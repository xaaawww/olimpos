package com.olimpos.gym.data

import org.json.JSONObject

/**
 * Compañeros de entrenamiento (tabla "companeros", un par de socios por fila).
 * Es unidireccional a propósito (lo agrega quien lo ve en Clasificación, sin
 * necesitar que el otro socio "acepte" nada): mismo dato que ya es público ahí
 * mismo (nombre, rango), solo que guardado en una lista propia. Alcanza para
 * los logros "Mentor" y "Espíritu de equipo" sin inventar un sistema de
 * solicitudes completo.
 */
data class Companero(val socioId: String, val nombre: String)

suspend fun agregarCompanero(companeroId: String, companeroNombre: String): Boolean {
    if (companeroId == socioActualId()) return false
    return try {
        Api.post("/v1/companeros", JSONObject().put("companero_id", companeroId))
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun eliminarCompanero(companeroId: String): Boolean {
    return try {
        Api.delete("/v1/companeros/$companeroId")
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarCompanerosDesdeFirebase(): List<Companero>? {
    return try {
        Api.get("/v1/companeros").optJSONArray("companeros")?.objetos()?.map {
            Companero(it.optString("socio_id"), it.optString("nombre"))
        } ?: emptyList()
    } catch (e: Exception) {
        null
    }
}

/** Cuántos días distintos el socio entrenó (cargó una marca en la
 *  Calculadora) el mismo día que al menos uno de sus compañeros — para el
 *  logro "Espíritu de equipo". La cuenta la hace la base (cruce de los días
 *  de sus marcas con los de sus compañeros). */
suspend fun contarDiasEntrenadosConCompaneros(): Int {
    return try {
        Api.get("/v1/companeros/dias-juntos").optInt("dias", 0)
    } catch (e: Exception) {
        0
    }
}
