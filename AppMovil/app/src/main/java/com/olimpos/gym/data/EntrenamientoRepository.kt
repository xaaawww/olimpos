package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Series de entrenamiento registradas desde una rutina (colección
 * "series_entrenamiento" en Firestore) — a diferencia de "marcas" (que son
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

private const val COLECCION_SERIES = "series_entrenamiento"

suspend fun guardarSerieEnFirebase(ejercicio: String, pesoKg: Float, reps: Int, timestamp: Long, esPesoCorporal: Boolean): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_SERIES).document().set(
            mapOf(
                "socio_id" to socioActualId(),
                "ejercicio" to ejercicio,
                "peso" to pesoKg,
                "repeticiones" to reps,
                "timestamp" to timestamp,
                "es_peso_corporal" to esPesoCorporal
            )
        ).await()
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
        val snapshot = Firebase.firestore.collection(COLECCION_SERIES)
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()
        snapshot.documents.mapNotNull { doc ->
            val ejercicio = doc.getString("ejercicio") ?: return@mapNotNull null
            val peso = doc.getDouble("peso")?.toFloat() ?: return@mapNotNull null
            val reps = doc.getLong("repeticiones")?.toInt() ?: return@mapNotNull null
            SerieEntrenamiento(
                id = doc.id, ejercicio = ejercicio, pesoKg = peso, reps = reps,
                timestamp = doc.getLong("timestamp") ?: 0L,
                esPesoCorporal = doc.getBoolean("es_peso_corporal") ?: false
            )
        }
    } catch (e: Exception) {
        null
    }
}
