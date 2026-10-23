package com.olimpos.gym.data

import org.json.JSONObject

/**
 * Ingresos al gimnasio (tabla "accesos"). No hay torniquete ni lector físico:
 * la entrada la registra el propio socio al tocar "Mostrar carnet de acceso"
 * en Inicio (o "Marcar mi ingreso de hoy" en Accesos). La API no duplica la
 * entrada si el socio ya entró hace menos de 90 minutos. De acá salen la
 * ocupación en vivo, la racha de días y las visitas del mes en Perfil, y
 * varios Logros — ninguno inventado.
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
