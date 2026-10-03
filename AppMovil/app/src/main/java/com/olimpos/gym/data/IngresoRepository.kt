package com.olimpos.gym.data

import org.json.JSONObject

/**
 * Ingresos al gimnasio (colección "ingresos"). Hoy no hay ningún torniquete
 * ni lector físico conectado a Firestore — el "acceso QR/biométrico/reloj"
 * de AccesoScreen son solo preferencias locales del socio, no eventos
 * reales — así que el ingreso lo marca el propio socio, una vez por día,
 * con un botón explícito ("Marcar mi ingreso de hoy"). De acá salen la
 * racha de días y las visitas del mes en Perfil, y varios Logros —
 * ninguno inventado.
 */
data class IngresoRegistro(val timestamp: Long, val metodo: String)

/** Cada ingreso es una fila de la tabla "accesos" del club. */
suspend fun registrarIngresoEnFirebase(metodo: String): Boolean {
    return try {
        Api.post("/v1/ingresos", JSONObject().put("metodo", metodo))
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarIngresosDesdeFirebase(): List<IngresoRegistro>? {
    return try {
        Api.get("/v1/ingresos").optJSONArray("ingresos")?.objetos()?.map {
            IngresoRegistro(it.optLong("timestamp"), it.optString("metodo", "manual"))
        } ?: emptyList()
    } catch (e: Exception) {
        null
    }
}

fun yaIngresoHoy(ingresos: List<IngresoRegistro>): Boolean {
    val hoy = java.util.Calendar.getInstance()
    return ingresos.any { ingreso ->
        val cal = java.util.Calendar.getInstance().apply { timeInMillis = ingreso.timestamp }
        cal.get(java.util.Calendar.DAY_OF_YEAR) == hoy.get(java.util.Calendar.DAY_OF_YEAR) &&
            cal.get(java.util.Calendar.YEAR) == hoy.get(java.util.Calendar.YEAR)
    }
}
