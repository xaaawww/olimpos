package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.auth.auth
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Cliente de la API del club (Worker "api-olimpos" + base de datos en Neon).
 *
 * La app NO habla directo con la base: dentro de un APK no se puede esconder
 * una contraseña de base de datos. En cambio, cada pedido lleva el ID token
 * de Firebase Authentication del socio logueado (el login sigue en Firebase)
 * y la API decide qué puede ver y tocar ese socio — ver ApiWorker/src.
 *
 * Todas las respuestas son un objeto JSON. Si la API contesta con error, se
 * lanza [ErrorApi] con un mensaje que ya se puede mostrar tal cual.
 */
object Api {
    const val URL_BASE = "https://api-olimpos.argosolimpo.workers.dev"

    class ErrorApi(val codigo: Int, mensaje: String) : Exception(mensaje)

    private suspend fun llamar(metodo: String, ruta: String, cuerpo: JSONObject?): JSONObject {
        val token = Firebase.auth.currentUser?.getIdToken(false)?.await()?.token
            ?: throw ErrorApi(401, "Tu sesión no es válida — volvé a iniciar sesión.")
        return withContext(Dispatchers.IO) {
            val conexion = (URL(URL_BASE + ruta).openConnection() as HttpURLConnection).apply {
                requestMethod = metodo
                connectTimeout = 20_000
                readTimeout = 30_000
                setRequestProperty("Authorization", "Bearer $token")
                setRequestProperty("Accept", "application/json")
                if (cuerpo != null) {
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json; charset=utf-8")
                }
            }
            try {
                if (cuerpo != null) conexion.outputStream.use { it.write(cuerpo.toString().toByteArray(Charsets.UTF_8)) }
                val codigo = conexion.responseCode
                val flujo = if (codigo in 200..299) conexion.inputStream else conexion.errorStream
                val texto = flujo?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
                val json = if (texto.isNotBlank()) try { JSONObject(texto) } catch (e: Exception) { JSONObject() } else JSONObject()
                if (codigo !in 200..299) throw ErrorApi(codigo, json.optString("error", "No se pudo completar la operación (código $codigo)."))
                json
            } finally {
                conexion.disconnect()
            }
        }
    }

    suspend fun get(ruta: String): JSONObject = llamar("GET", ruta, null)
    suspend fun post(ruta: String, cuerpo: JSONObject = JSONObject()): JSONObject = llamar("POST", ruta, cuerpo)
    suspend fun put(ruta: String, cuerpo: JSONObject): JSONObject = llamar("PUT", ruta, cuerpo)
    suspend fun delete(ruta: String): JSONObject = llamar("DELETE", ruta, null)
}

/** Recorre un JSONArray como lista de objetos (ignora lo que no sea objeto). */
fun JSONArray.objetos(): List<JSONObject> = (0 until length()).mapNotNull { optJSONObject(it) }

/** Recorre un JSONArray de textos. */
fun JSONArray.textos(): List<String> = (0 until length()).mapNotNull { i -> optString(i).takeIf { it.isNotEmpty() } }

/** Número o `null` (org.json devuelve 0 si falta, y a veces 0 es un valor real). */
fun JSONObject.numeroONull(clave: String): Double? = if (has(clave) && !isNull(clave)) optDouble(clave) else null

fun JSONObject.textoONull(clave: String): String? = if (has(clave) && !isNull(clave)) optString(clave) else null
