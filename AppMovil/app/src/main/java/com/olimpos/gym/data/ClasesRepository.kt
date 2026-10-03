package com.olimpos.gym.data

import org.json.JSONObject

/**
 * Reservas de clases grupales (tabla "reservasclase"). Cada reserva es de una
 * semana calendario concreta, así que "reservaste esta semana" se resetea sola
 * la semana siguiente. Quien manda en TODO lo importante es la API, no el
 * celular: ella decide qué semana es, cuenta cuántos lugares quedan dentro de
 * una transacción con bloqueo (dos socios que reservan la última plaza a la
 * vez no pueden pasarse del cupo) y evita reservar la misma clase dos veces.
 * Cancelar no borra la reserva: queda como 'cancelada' en el historial.
 */
data class ReservaClase(val claseId: String, val timestamp: Long)

enum class ResultadoReserva { OK, YA_RESERVADA, CLASE_LLENA, ERROR }

/** Lo que la API informa de las clases: las reservas del socio EN LA SEMANA
 *  ACTUAL, cuántos lugares hay ocupados en cada clase y cuál es su cupo. */
data class EstadoClases(
    val reservas: List<ReservaClase>,
    val reservados: Map<String, Int>,
    val capacidades: Map<String, Int>
)

/** `true` si ya se reservó esta clase en la semana actual (la API solo
 *  informa reservas de la semana en curso). */
fun yaReservadaEstaSemana(reservas: List<ReservaClase>, claseId: String): Boolean =
    reservas.any { it.claseId == claseId }

/** Clases distintas reservadas esta semana — el "Clases sem." real de Perfil. */
fun clasesReservadasEstaSemana(reservas: List<ReservaClase>): Int = reservas.map { it.claseId }.distinct().size

suspend fun cargarEstadoClases(): EstadoClases? {
    return try {
        val j = Api.get("/v1/clases")
        val clases = j.optJSONArray("clases")?.objetos().orEmpty()
        EstadoClases(
            reservas = j.optJSONArray("mis_reservas")?.objetos()?.map { ReservaClase(it.optString("clase_id"), it.optLong("timestamp")) }.orEmpty(),
            reservados = clases.associate { it.optString("id") to it.optInt("reservados", 0) },
            capacidades = clases.associate { it.optString("id") to it.optInt("cupo", 0) }
        )
    } catch (e: Exception) {
        null
    }
}

suspend fun guardarReservaClaseEnFirebase(claseId: String): ResultadoReserva {
    return try {
        when (Api.post("/v1/clases/$claseId/reservar").optString("resultado")) {
            "OK" -> ResultadoReserva.OK
            "YA_RESERVADA" -> ResultadoReserva.YA_RESERVADA
            "CLASE_LLENA" -> ResultadoReserva.CLASE_LLENA
            else -> ResultadoReserva.ERROR
        }
    } catch (e: Exception) {
        ResultadoReserva.ERROR
    }
}

/** Cancela la reserva de [claseId] de esta semana, si existe. */
suspend fun cancelarReservaClaseEnFirebase(claseId: String): Boolean {
    return try {
        Api.delete("/v1/clases/$claseId/reserva")
        true
    } catch (e: Exception) {
        false
    }
}
