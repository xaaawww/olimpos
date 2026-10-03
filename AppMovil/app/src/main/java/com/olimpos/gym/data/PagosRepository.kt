package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.auth.auth
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
 * en la base cuando Mercado Pago le confirma el pago al Worker (webhook,
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

/** Historial de pagos reales del socio (los que registró el webhook de
 *  Mercado Pago al confirmarse cada uno, tabla "pagos"). Vacío mientras
 *  nunca pagó nada todavía. La API ya lo entrega del más nuevo al más viejo. */
suspend fun cargarHistorialPagos(): List<PagoHistorial> {
    return try {
        Api.get("/v1/pagos").optJSONArray("pagos")?.objetos().orEmpty().mapNotNull { j ->
            val plan = j.textoONull("plan") ?: return@mapNotNull null
            val monto = j.numeroONull("monto")?.toLong() ?: return@mapNotNull null
            val fechaMs = j.numeroONull("fecha_ms")?.toLong() ?: return@mapNotNull null
            PagoHistorial("Plan $plan — ${fechaLegible(fechaMs)}", "$$monto", j.optString("estado", ""))
        }
    } catch (e: Exception) {
        emptyList()
    }
}
