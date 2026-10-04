package com.olimpos.gym.data

import org.json.JSONObject

/**
 * Series de entrenamiento registradas desde una rutina (colección
 * "seriesentrenamiento" en la base de datos) — a diferencia de "marcas" (que son
 * intentos de PR que un entrenador tiene que verificar para el ranking de
 * Clasificación), esto es simplemente el registro de qué se entrenó en
 * cada sesión de rutina. Alimenta dos cosas que antes no tenían datos
 * reales detrás: "kg movidos este mes" en Inicio y el Ghost Mode de
 * Entrenar (comparar hoy contra la sesión anterior de este mismo
 * ejercicio) — ver EntrenarScreen.kt.
 */
data class SerieEntrenamiento(
    val id: String = "",
    val ejercicio: String,
    val pesoKg: Float,
    val reps: Int,
    val timestamp: Long,
    /** Igual que EjercicioRutina.esPesoCorporal: [pesoKg] es lo AGREGADO al
     *  peso corporal, no el total — hace falta guardarlo por serie porque
     *  distintas rutinas pueden nombrar el mismo movimiento distinto
     *  (ej. "Dominadas asistidas" acá vs. "Dominadas" en la Calculadora),
     *  así que no alcanza con una lista fija de nombres. */
    val esPesoCorporal: Boolean = false
)

suspend fun guardarSerieEnFirebase(ejercicio: String, pesoKg: Float, reps: Int, timestamp: Long, esPesoCorporal: Boolean): Boolean {
    return try {
        Api.post(
            "/v1/series",
            JSONObject().put("ejercicio", ejercicio).put("peso", pesoKg.toDouble()).put("repeticiones", reps)
                .put("timestamp", timestamp).put("es_peso_corporal", esPesoCorporal)
        )
        true
    } catch (e: Exception) {
        false
    }
}

/** Trae TODAS las series propias ya registradas, de cualquier sesión
 *  pasada — se usa tanto para "kg movidos este mes" (todas) como para el
 *  Ghost Mode (la mejor de una sesión anterior, por ejercicio). */
suspend fun cargarSeriesDesdeFirebase(): List<SerieEntrenamiento>? {
    return try {
        Api.get("/v1/series").optJSONArray("series")?.objetos()?.map { j ->
            SerieEntrenamiento(
                id = j.optString("id"), ejercicio = j.optString("ejercicio"),
                pesoKg = j.optDouble("peso", 0.0).toFloat(), reps = j.optInt("repeticiones", 1),
                timestamp = j.optLong("timestamp", 0L), esPesoCorporal = j.optBoolean("es_peso_corporal", false)
            )
        } ?: emptyList()
    } catch (e: Exception) {
        null
    }
}
