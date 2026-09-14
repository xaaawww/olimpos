package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Registro de consumo de agua (colección "registros_agua") — un marcado
 * propio de "hoy tomé agua" (no litros exactos), una vez por día. De acá
 * sale el logro "Hidratado" (7 días seguidos). Mismo patrón que los
 * ingresos al gimnasio (IngresoRepository.kt).
 */
private const val COLECCION_AGUA = "registros_agua"

suspend fun registrarAguaEnFirebase(): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_AGUA).document().set(
            mapOf(
                "socio_id" to socioActualId(),
                "timestamp" to System.currentTimeMillis()
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarRegistrosAguaDesdeFirebase(): List<Long>? {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_AGUA)
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()
        snapshot.documents.mapNotNull { it.getLong("timestamp") }
    } catch (e: Exception) {
        null
    }
}

/** `true` si ya hay un registro de agua en el día calendario de hoy. */
fun yaRegistroAguaHoy(registros: List<Long>): Boolean {
    val hoy = java.util.Calendar.getInstance()
    return registros.any { ts ->
        val cal = java.util.Calendar.getInstance().apply { timeInMillis = ts }
        cal.get(java.util.Calendar.DAY_OF_YEAR) == hoy.get(java.util.Calendar.DAY_OF_YEAR) &&
            cal.get(java.util.Calendar.YEAR) == hoy.get(java.util.Calendar.YEAR)
    }
}
