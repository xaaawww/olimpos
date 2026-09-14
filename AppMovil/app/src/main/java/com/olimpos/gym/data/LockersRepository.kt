package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Reserva de locker (colección "lockers", un documento por socio — id =
 * su propio uid, así reservar uno nuevo reemplaza automáticamente el
 * anterior sin dejar basura). Antes esto vivía solo en memoria dentro de
 * LockersScreen (un `remember` local que se perdía al salir de la
 * pantalla) y el catálogo de ejemplo encima arrancaba con lockers ya
 * "ocupados" sin que ningún socio real los hubiese tomado.
 */
private const val COLECCION_LOCKERS = "lockers"

suspend fun reservarLockerEnFirebase(numero: Int): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_LOCKERS).document(socioActualId()).set(
            mapOf(
                "socio_id" to socioActualId(),
                "numero" to numero,
                "timestamp" to System.currentTimeMillis()
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun liberarLockerEnFirebase(): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_LOCKERS).document(socioActualId()).delete().await()
        true
    } catch (e: Exception) {
        false
    }
}

/** Número de locker -> uid del socio que lo tiene reservado, de TODOS los
 *  socios — hace falta para saber qué lockers están libres para
 *  cualquiera, no solo el propio. */
suspend fun cargarLockersDesdeFirebase(): Map<Int, String>? {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_LOCKERS).get().await()
        snapshot.documents.mapNotNull { doc ->
            val numero = doc.getLong("numero")?.toInt() ?: return@mapNotNull null
            numero to doc.id
        }.toMap()
    } catch (e: Exception) {
        null
    }
}
