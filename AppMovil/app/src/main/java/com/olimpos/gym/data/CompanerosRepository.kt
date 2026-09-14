package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Compañeros de entrenamiento (colección "companeros", un documento por
 * par — id = "{miUid}_{companeroId}"). Es unidireccional a propósito (lo
 * agrega quien lo ve en Clasificación, sin necesitar que el otro socio
 * "acepte" nada): mismo dato que ya es público ahí mismo (nombre, rango),
 * solo que guardado en una lista propia. Alcanza para los logros "Mentor"
 * y "Espíritu de equipo" sin inventar un sistema de solicitudes completo.
 */
private const val COLECCION_COMPANEROS = "companeros"

data class Companero(val socioId: String, val nombre: String)

private fun idDocCompanero(companeroId: String) = "${socioActualId()}_$companeroId"

suspend fun agregarCompanero(companeroId: String, companeroNombre: String): Boolean {
    if (companeroId == socioActualId()) return false
    return try {
        Firebase.firestore.collection(COLECCION_COMPANEROS).document(idDocCompanero(companeroId)).set(
            mapOf(
                "socio_id" to socioActualId(),
                "companero_id" to companeroId,
                "companero_nombre" to companeroNombre,
                "timestamp" to System.currentTimeMillis()
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun eliminarCompanero(companeroId: String): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_COMPANEROS).document(idDocCompanero(companeroId)).delete().await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarCompanerosDesdeFirebase(): List<Companero>? {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_COMPANEROS)
            .whereEqualTo("socio_id", socioActualId())
            .get().await()
        snapshot.documents.mapNotNull { doc ->
            val id = doc.getString("companero_id") ?: return@mapNotNull null
            val nombre = doc.getString("companero_nombre") ?: return@mapNotNull null
            Companero(id, nombre)
        }
    } catch (e: Exception) {
        null
    }
}

private fun diasDeMarcas(documentos: List<com.google.firebase.firestore.DocumentSnapshot>): Set<Long> =
    documentos.mapNotNull { it.getLong("timestamp") }.map { it / 86_400_000L }.toSet()

/** Cuántos días distintos el socio entrenó (cargó una marca en la
 *  Calculadora) el mismo día que al menos uno de sus compañeros — para el
 *  logro "Espíritu de equipo". Usa "marcas" (no "series_entrenamiento",
 *  que es privada de cada socio) porque es la única colección de
 *  entrenamiento que ya es legible entre socios — ver firestore.rules. */
suspend fun contarDiasEntrenadosConCompaneros(companeroIds: List<String>): Int {
    if (companeroIds.isEmpty()) return 0
    return try {
        val misMarcas = Firebase.firestore.collection("marcas")
            .whereEqualTo("socio_id", socioActualId())
            .get().await()
        val misDias = diasDeMarcas(misMarcas.documents)
        if (misDias.isEmpty()) return 0

        val diasDeCompaneros = mutableSetOf<Long>()
        // whereIn admite hasta 10 valores — de sobra para una lista de
        // compañeros, que en la práctica va a ser corta.
        companeroIds.take(10).let { ids ->
            val snapshot = Firebase.firestore.collection("marcas").whereIn("socio_id", ids).get().await()
            diasDeCompaneros += diasDeMarcas(snapshot.documents)
        }
        (misDias intersect diasDeCompaneros).size
    } catch (e: Exception) {
        0
    }
}
