package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.auth.auth
import com.google.firebase.firestore.firestore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Pago real de una membresía (Mercado Pago, modo prueba — no se cobra
 * plata real). Mismo patrón que Argos (ver ArgosRepository.kt): la app
 * nunca tiene el Access Token de Mercado Pago, le pide a este Worker que
 * arme el cobro (con el precio que el servidor conoce, no el que mande la
 * app) y este devuelve el link de pago de Mercado Pago.
 *
 * La membresía NO se activa acá ni al volver del navegador: se activa sola
 * en Firestore cuando Mercado Pago le confirma el pago al Worker (webhook,
 * ver PagosWorker/src/index.ts) — por eso, después de volver del pago, hay
 * que llamar a [DatosRemotos.recargarMembresia] para verla actualizada
 * (puede tardar unos segundos si el pago quedó "pendiente").
 *
 * Reemplazar PAGOS_WORKER_URL por la URL real una vez desplegado el Worker.
 */
private const val PAGOS_WORKER_URL = "https://pagos-olimpos.argosolimpo.workers.dev"

/** Devuelve el link de Mercado Pago para pagar [plan], o lanza una
 *  excepción con un mensaje ya listo para mostrar si algo falla. */
suspend fun crearPreferenciaDePago(plan: String): String {
    return withContext(Dispatchers.IO) {
        val idToken = Firebase.auth.currentUser?.getIdToken(false)?.await()?.token
            ?: throw Exception("Tu sesión no es válida — volvé a iniciar sesión.")

        val cuerpo = JSONObject().put("plan", plan)

        val conexion = (URL("$PAGOS_WORKER_URL/crear-preferencia").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            doOutput = true
            connectTimeout = 20_000
            readTimeout = 30_000
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
                throw Exception(json.optString("error", "No se pudo iniciar el pago (código $codigo)."))
            }
            json.getString("checkout_url")
        } finally {
            conexion.disconnect()
        }
    }
}

private const val COLECCION_PAGOS = "pagos_socios"

/** Historial de pagos reales del socio (los que escribió el webhook de
 *  Mercado Pago al confirmarse cada uno). Vacío mientras nunca pagó nada
 *  todavía. Se ordena en el celular, no en la consulta, para no necesitar
 *  un índice compuesto en Firestore por una lista que como mucho tiene
 *  unos pocos pagos por socio. */
suspend fun cargarHistorialPagos(): List<PagoHistorial> {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_PAGOS)
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()
        snapshot.documents
            .mapNotNull { doc ->
                val plan = doc.getString("plan") ?: return@mapNotNull null
                val monto = doc.getLong("monto") ?: return@mapNotNull null
                val estado = doc.getString("estado") ?: return@mapNotNull null
                val fechaMs = doc.getLong("fecha_ms") ?: return@mapNotNull null
                Triple(fechaMs, plan, monto) to estado
            }
            .sortedByDescending { it.first.first }
            .map { (datos, estado) ->
                val (fechaMs, plan, monto) = datos
                PagoHistorial("Plan $plan — ${fechaLegible(fechaMs)}", "$$monto", estado)
            }
    } catch (e: Exception) {
        emptyList()
    }
}
