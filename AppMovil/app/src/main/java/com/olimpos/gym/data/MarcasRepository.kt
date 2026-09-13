package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Marcas personales del socio (colección "marcas" en Firestore). El socio
 * las carga desde la Calculadora/Mis marcas; el sistema de empleados las
 * lee para que un entrenador o el dueño las verifique (ver sección
 * "Verificación de Marcas"). Devuelve `null` si Firebase falla, para que
 * quien llama use [MIS_MARCAS] de ejemplo como respaldo.
 */
suspend fun cargarMarcasDesdeFirebase(): List<MarcaPersonal>? {
    return try {
        val snapshot = Firebase.firestore.collection("marcas")
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()

        snapshot.documents.mapNotNull { doc ->
            val ejercicio = doc.getString("ejercicio") ?: return@mapNotNull null
            val peso = doc.getDouble("peso")?.toFloat() ?: return@mapNotNull null
            val reps = doc.getLong("repeticiones")?.toInt() ?: return@mapNotNull null
            MarcaPersonal(
                id = doc.id,
                ejercicio = ejercicio,
                pesoKg = peso,
                reps = reps,
                fecha = doc.getString("fecha") ?: "",
                timestamp = doc.getLong("timestamp") ?: 0L,
                verificado = doc.getBoolean("verificado") ?: false
            )
        }
    } catch (e: Exception) {
        null
    }
}

/** Rango general de un socio (promedio de sus 19 zonas), para la Escalera
 *  del Olimpo — quién más del club llegó a cada nivel. [creadoMs] sale del
 *  alta de su acceso a la app (colección "socios_app", ver auth_repo.py) —
 *  es la única fecha real que existe por socio hoy. */
data class SocioRango(
    val socioId: String,
    val nombre: String,
    val nivel: NivelMuscular,
    val verificado: Boolean,
    val kgTotales: Float,
    val creadoMs: Long? = null
)

private const val PESO_CORPORAL_REFERENCIA = 80f

/** Trae el rango general de TODOS los socios con marcas cargadas (no solo
 *  el actual), agrupando por socio_id. Sin perfil de socios todavía no hay
 *  forma de saber el peso corporal real de cada uno, así que se usa una
 *  referencia fija de 80kg para este cálculo — mismo criterio que usa el
 *  sistema de empleados (marcas_repo.py) para su ranking general. */
suspend fun cargarRangosDeSocios(): List<SocioRango>? {
    return try {
        val snapshotMarcas = Firebase.firestore.collection("marcas").get().await()
        // "socios_app": lo crea un empleado al darle acceso al socio (ver
        // auth_repo.py) — de ahí sale cuándo se unió cada uno.
        val creadoPorUid = try {
            Firebase.firestore.collection("socios_app").get().await()
                .documents.associate { it.id to it.getLong("creado_ms") }
        } catch (e: Exception) {
            emptyMap()
        }

        snapshotMarcas.documents
            .groupBy { it.getString("socio_id") ?: "?" }
            .mapNotNull { (socioId, docs) ->
                val nombre = docs.firstOrNull()?.getString("socio_nombre") ?: socioId
                val marcas = docs.mapNotNull { doc ->
                    val ejercicio = doc.getString("ejercicio") ?: return@mapNotNull null
                    val peso = doc.getDouble("peso")?.toFloat() ?: return@mapNotNull null
                    val reps = doc.getLong("repeticiones")?.toInt() ?: return@mapNotNull null
                    MarcaPersonal(
                        id = doc.id, ejercicio = ejercicio, pesoKg = peso, reps = reps,
                        fecha = doc.getString("fecha") ?: "", timestamp = doc.getLong("timestamp") ?: 0L,
                        verificado = doc.getBoolean("verificado") ?: false
                    )
                }
                val resumen = resumenMuscular(marcas, pesoCorporalKg = PESO_CORPORAL_REFERENCIA)
                if (!resumen.tieneMarcas) return@mapNotNull null
                val promedio = ZonaMuscular.entries.sumOf { (resumen.puntajes[it] ?: 0f).toDouble() } / ZonaMuscular.entries.size
                SocioRango(
                    socioId = socioId,
                    nombre = nombre,
                    nivel = nivelDesdePuntaje(promedio.toFloat()),
                    verificado = resumen.verificado,
                    kgTotales = kgTotalesVigentes(marcas, PESO_CORPORAL_REFERENCIA),
                    creadoMs = creadoPorUid[socioId]
                )
            }
    } catch (e: Exception) {
        null
    }
}

/** Guarda una marca nueva, siempre como pendiente de verificar. El
 *  [timestamp] es lo que decide, en [resumenMuscular], que esta marca
 *  reemplace a la anterior del mismo ejercicio en vez de acumularse. */
suspend fun guardarMarcaEnFirebase(ejercicio: String, pesoKg: Float, reps: Int, fecha: String, timestamp: Long): Boolean {
    return try {
        val doc = Firebase.firestore.collection("marcas").document()
        doc.set(
            mapOf(
                "socio_id" to socioActualId(),
                "socio_nombre" to socioActualNombre(),
                "ejercicio" to ejercicio,
                "peso" to pesoKg,
                "repeticiones" to reps,
                "fecha" to fecha,
                "timestamp" to timestamp,
                "verificado" to false
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}
