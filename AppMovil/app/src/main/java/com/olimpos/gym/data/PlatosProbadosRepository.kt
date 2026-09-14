package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Platos que el socio marcó como "ya probé" (colección "platos_probados").
 * El id de cada documento es "{socio_id}_{plato_id}" — así marcarlo dos
 * veces no crea un duplicado, solo pisa el mismo documento. De acá sale
 * el logro "Sibarita" (probar 10 platos distintos del catálogo).
 */
private const val COLECCION_PLATOS_PROBADOS = "platos_probados"

suspend fun marcarPlatoProbadoEnFirebase(platoId: String): Boolean {
    return try {
        val docId = "${socioActualId()}_$platoId"
        Firebase.firestore.collection(COLECCION_PLATOS_PROBADOS).document(docId).set(
            mapOf(
                "socio_id" to socioActualId(),
                "plato_id" to platoId,
                "timestamp" to System.currentTimeMillis()
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarPlatosProbadosDesdeFirebase(): Set<String>? {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_PLATOS_PROBADOS)
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()
        snapshot.documents.mapNotNull { it.getString("plato_id") }.toSet()
    } catch (e: Exception) {
        null
    }
}
