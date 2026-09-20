package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.auth.auth
import com.google.firebase.firestore.firestore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Argos: el asistente de IA de texto de OlimpΩs, para los socios. La app
 * móvil NUNCA tiene la clave de Anthropic — no hay forma de esconder un
 * secreto adentro de un APK instalado, a diferencia de Firestore, que se
 * protege con reglas del lado del servidor. En cambio, le habla a un
 * Worker de Cloudflare (que sí puede guardar secretos) pasándole el ID
 * token de Firebase Auth del socio logueado, para probar que quien
 * pregunta es un socio real — ver ArgosWorker/src/index.ts.
 *
 * Reemplazar ARGOS_WORKER_URL por la URL real una vez desplegado el Worker
 * (ver instrucciones de despliegue).
 */
private const val ARGOS_WORKER_URL = "https://argos-olimpos.argosolimpo.workers.dev"

private const val COLECCION_CONFIG = "configuracion_app"
private const val DOC_ARGOS = "argos"

data class MensajeArgos(val rol: String, val texto: String) // rol: "user" | "assistant"

/** Base de conocimiento (horarios/precios/políticas reales) que carga el
 *  dueño/admin desde el sistema de empleados — mismo documento que usa el
 *  Worker, para que la respuesta sea consistente entre las dos apps. */
suspend fun cargarBaseConocimientoArgos(): String {
    return try {
        val doc = Firebase.firestore.collection(COLECCION_CONFIG).document(DOC_ARGOS).get().await()
        doc.getString("base_conocimiento") ?: ""
    } catch (e: Exception) {
        ""
    }
}

/** Resumen en texto plano de los datos propios del socio (membresía,
 *  racha, próximas clases reservadas) — así Argos puede responder
 *  preguntas personales ("¿cuándo vence mi membresía?") sin que el Worker
 *  tenga que leer Firestore por su cuenta con una cuenta de servicio. */
fun construirContextoPersonalArgos(): String {
    val partes = mutableListOf<String>()

    val membresia = DatosRemotos.membresia
    if (membresia != null) {
        partes.add("Tiene una membresía \"${membresia.plan}\" activa desde ${fechaLegible(membresia.fechaInicioMs)}.")
    } else {
        partes.add("Todavía no tiene ninguna membresía asignada.")
    }

    val ingresos = (DatosRemotos.ingresos ?: emptyList()).map { it.timestamp }
    partes.add("Racha actual: ${rachaActualDeDias(ingresos)} días seguidos yendo al gimnasio.")

    val reservas = DatosRemotos.reservasClase ?: emptyList()
    if (reservas.isNotEmpty()) {
        val nombres = reservas.mapNotNull { r ->
            CLASES_SEMANA.find { it.id == r.claseId }?.let { "${it.nombre} (${it.dia} ${it.hora})" }
        }
        if (nombres.isNotEmpty()) partes.add("Clases reservadas: " + nombres.joinToString(", ") + ".")
    }

    val locker = DatosRemotos.lockersOcupados?.entries?.find { it.value == socioActualId() }?.key
    if (locker != null) partes.add("Tiene reservado el locker Nº $locker.")

    return partes.joinToString(" ")
}

/** Llama al Worker de Argos (nunca directo a Anthropic). Lanza una
 *  excepción con un mensaje ya listo para mostrar si algo falla (sin
 *  sesión, cupo diario agotado del lado del Worker, error de red). */
suspend fun preguntarArgos(mensaje: String, historial: List<MensajeArgos>): String {
    if (!planIncluyeArgos(DatosRemotos.membresia?.plan)) {
        throw Exception("Argos es parte de los planes ${PLANES_CON_ARGOS.joinToString(" y ")}.")
    }
    return withContext(Dispatchers.IO) {
        val idToken = Firebase.auth.currentUser?.getIdToken(false)?.await()?.token
            ?: throw Exception("Tu sesión no es válida — volvé a iniciar sesión.")

        val baseConocimiento = cargarBaseConocimientoArgos()
        val contextoSocio = construirContextoPersonalArgos()

        val historialJson = JSONArray()
        historial.takeLast(20).forEach {
            historialJson.put(JSONObject().put("rol", it.rol).put("texto", it.texto))
        }

        val cuerpo = JSONObject()
            .put("mensaje", mensaje)
            .put("historial", historialJson)
            .put("contexto_socio", contextoSocio)
            .put("base_conocimiento", baseConocimiento)

        val conexion = (URL(ARGOS_WORKER_URL).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            doOutput = true
            connectTimeout = 20_000
            readTimeout = 60_000
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("Authorization", "Bearer $idToken")
        }

        try {
            conexion.outputStream.use { it.write(cuerpo.toString().toByteArray(Charsets.UTF_8)) }
            val codigo = conexion.responseCode
            val flujo = if (codigo in 200..299) conexion.inputStream else conexion.errorStream
            val texto = flujo?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            val json = if (texto.isNotBlank()) JSONObject(texto) else JSONObject()
            if (codigo !in 200..299) {
                throw Exception(json.optString("error", "Argos no pudo responder (código $codigo)."))
            }
            json.getString("respuesta")
        } finally {
            conexion.disconnect()
        }
    }
}
