package com.olimpos.gym.data

import org.json.JSONObject

/**
 * Platos que el socio marcó como "ya probé" (colección "platos_probados").
 * El id de cada documento es "{socio_id}_{plato_id}" — así marcarlo dos
 * veces no crea un duplicado, solo pisa el mismo documento. De acá sale
 * el logro "Sibarita" (probar 10 platos distintos del catálogo).
 */
suspend fun marcarPlatoProbadoEnFirebase(platoId: String): Boolean {
    return try {
        Api.post("/v1/platos-probados", JSONObject().put("plato_id", platoId))
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarPlatosProbadosDesdeFirebase(): Set<String>? {
    return try {
        Api.get("/v1/platos-probados").optJSONArray("plato_ids")?.textos()?.toSet() ?: emptySet()
    } catch (e: Exception) {
        null
    }
}
