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
 *
 * El id de cada reserva es "{uid}_{clase_id}_{semana}" (no uno al azar):
 * así, reservar la misma clase dos veces la misma semana es un "set" sobre
 * el mismo documento (no crea un duplicado), y cancelar es simplemente
 * borrar ese id conocido, sin tener que buscarlo primero.
 */
data class ReservaClase(val claseId: String, val timestamp: Long)

enum class ResultadoReserva { OK, YA_RESERVADA, CLASE_LLENA, ERROR }

private const val COLECCION_RESERVAS_CLASE = "reservas_clase"
private const val COLECCION_CUPOS = "clases_cupos"

/** Año+semana calendario (lunes a lunes) de un timestamp, como texto
 *  ("2026-W40") — para agrupar reservas "de esta semana" sin depender del
 *  locale del dispositivo, y para usarlo en los ids de documento. */
private fun claveSemanaDe(timestampMs: Long): String {
    val cal = java.util.Calendar.getInstance().apply {
        firstDayOfWeek = java.util.Calendar.MONDAY
        timeInMillis = timestampMs
    }
    return "${cal.get(java.util.Calendar.YEAR)}-W${cal.get(java.util.Calendar.WEEK_OF_YEAR)}"
}

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

/** Reserva [claseId] para el socio actual, respetando [cupoMaximo] — ver
 *  "clases_cupos" en firestore.rules para qué parte de esto cuida también
 *  el servidor. El cupo máximo en sí es un dato fijo en el código de la
 *  app (ClaseSemana.cupo), no algo guardado en Firestore, así que esta
 *  función es la única barrera real contra pasarse del cupo — no hay una
 *  regla de seguridad que la reemplace (a diferencia de Argos o los pagos,
 *  acá no hay plata de por medio, es una limitación aceptada a propósito). */
suspend fun guardarReservaClaseEnFirebase(claseId: String, cupoMaximo: Int): ResultadoReserva {
    val uid = socioActualId()
    val ahora = System.currentTimeMillis()
    val semana = claveSemanaDe(ahora)
    val db = Firebase.firestore
    val refReserva = db.collection(COLECCION_RESERVAS_CLASE).document("${uid}_${claseId}_${semana}")
    val refCupo = db.collection(COLECCION_CUPOS).document("${claseId}_${semana}")

    return try {
        db.runTransaction { tx ->
            if (tx.get(refReserva).exists()) return@runTransaction ResultadoReserva.YA_RESERVADA

            val cupoActual = (tx.get(refCupo).getLong("reservados") ?: 0L).toInt()
            if (cupoActual >= cupoMaximo) return@runTransaction ResultadoReserva.CLASE_LLENA

            tx.set(refReserva, mapOf(
                "socio_id" to uid, "clase_id" to claseId, "semana" to semana, "timestamp" to ahora
            ))
            tx.set(refCupo, mapOf(
                "clase_id" to claseId, "semana" to semana, "reservados" to (cupoActual + 1)
            ))
            ResultadoReserva.OK
        }.await()
    } catch (e: Exception) {
        ResultadoReserva.ERROR
    }
}

/** Cancela la reserva de [claseId] de esta semana, si existe — baja el
 *  cupo real en el mismo movimiento. */
suspend fun cancelarReservaClaseEnFirebase(claseId: String): Boolean {
    val uid = socioActualId()
    val semana = claveSemanaDe(System.currentTimeMillis())
    val db = Firebase.firestore
    val refReserva = db.collection(COLECCION_RESERVAS_CLASE).document("${uid}_${claseId}_${semana}")
    val refCupo = db.collection(COLECCION_CUPOS).document("${claseId}_${semana}")

    return try {
        db.runTransaction { tx ->
            if (!tx.get(refReserva).exists()) return@runTransaction Unit
            val cupoActual = (tx.get(refCupo).getLong("reservados") ?: 0L).toInt()
            tx.delete(refReserva)
            if (cupoActual > 0) {
                tx.set(refCupo, mapOf(
                    "clase_id" to claseId, "semana" to semana, "reservados" to (cupoActual - 1)
                ))
            }
        }.await()
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

/** Cuántos socios (de cualquiera) tienen reservada cada clase esta semana
 *  — para mostrar "X/cupo" de verdad en Inicio. Una lectura por clase
 *  (son solo 3, CLASES_SEMANA): no vale la pena una consulta más compleja
 *  para esta escala. */
suspend fun cargarCuposClasesDesdeFirebase(): Map<String, Int> {
    val semana = claveSemanaDe(System.currentTimeMillis())
    val db = Firebase.firestore
    val resultado = mutableMapOf<String, Int>()
    for (clase in CLASES_SEMANA) {
        try {
            val doc = db.collection(COLECCION_CUPOS).document("${clase.id}_${semana}").get().await()
            resultado[clase.id] = (doc.getLong("reservados") ?: 0L).toInt()
        } catch (e: Exception) {
            // Si una falla (sin conexión, etc.) se deja en 0 — mejor mostrar
            // "0/cupo" que trabar toda la pantalla de Inicio por una clase.
        }
    }
    return resultado
}
