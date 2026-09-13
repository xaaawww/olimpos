package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Reservas de clases grupales (colección "reservas_clase") — antes tocar
 * "Reservar" en una tarjeta de Inicio solo cambiaba un estado local (se
 * perdía al salir de la pantalla, y "Clases sem." en Perfil era un 0 fijo
 * porque no había ninguna reserva real de dónde sacarlo). Ahora cada
 * reserva se guarda de verdad, con la semana calendario en la que se
 * hizo — así "reservaste esta semana" se resetea sola la semana
 * siguiente, en vez de quedar marcado para siempre.
 */
data class ReservaClase(val claseId: String, val timestamp: Long)

private const val COLECCION_RESERVAS_CLASE = "reservas_clase"

suspend fun guardarReservaClaseEnFirebase(claseId: String): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_RESERVAS_CLASE).document().set(
            mapOf(
                "socio_id" to socioActualId(),
                "clase_id" to claseId,
                "timestamp" to System.currentTimeMillis()
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarReservasClaseDesdeFirebase(): List<ReservaClase>? {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_RESERVAS_CLASE)
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()
        snapshot.documents.mapNotNull { doc ->
            val claseId = doc.getString("clase_id") ?: return@mapNotNull null
            val timestamp = doc.getLong("timestamp") ?: return@mapNotNull null
            ReservaClase(claseId, timestamp)
        }
    } catch (e: Exception) {
        null
    }
}

/** Año+semana calendario (lunes a lunes) de un timestamp — para agrupar
 *  reservas "de esta semana" sin depender del locale del dispositivo. */
private fun semanaDe(timestampMs: Long): Pair<Int, Int> {
    val cal = java.util.Calendar.getInstance().apply {
        firstDayOfWeek = java.util.Calendar.MONDAY
        timeInMillis = timestampMs
    }
    return cal.get(java.util.Calendar.YEAR) to cal.get(java.util.Calendar.WEEK_OF_YEAR)
}

/** `true` si ya se reservó esta clase en la semana calendario actual —
 *  para no dejar reservar la misma clase dos veces la misma semana. */
fun yaReservadaEstaSemana(reservas: List<ReservaClase>, claseId: String): Boolean {
    val hoy = semanaDe(System.currentTimeMillis())
    return reservas.any { it.claseId == claseId && semanaDe(it.timestamp) == hoy }
}

/** Clases distintas reservadas esta semana — el "Clases sem." real de Perfil. */
fun clasesReservadasEstaSemana(reservas: List<ReservaClase>): Int {
    val hoy = semanaDe(System.currentTimeMillis())
    return reservas.filter { semanaDe(it.timestamp) == hoy }.map { it.claseId }.distinct().size
}
