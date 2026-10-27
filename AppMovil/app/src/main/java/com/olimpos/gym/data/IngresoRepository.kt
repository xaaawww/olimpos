package com.olimpos.gym.data

import org.json.JSONObject

/**
 * Ingresos al gimnasio (tabla "accesos"). La recepción muestra en su
 * computadora un QR que cambia cada 30 segundos (sistema de empleados →
 * "QR de entrada"); el socio lo escanea con la app y la API comprueba que el
 * código sea el de ese momento antes de registrar la entrada. Así el ingreso
 * lo confirma el club, no el propio socio. La API no duplica la entrada si
 * el socio ya entró hace menos de [MINUTOS_EN_EL_CLUB] minutos. De acá salen
 * la ocupación en vivo, la racha de días, las visitas del mes y varios Logros.
 */
data class IngresoRegistro(val timestamp: Long, val metodo: String)

/** Mismo valor que la API (ApiWorker/src/util.ts): ese rato después de
 *  escanear cuenta como "adentro". */
const val MINUTOS_EN_EL_CLUB = 90

/** Resultado de escanear: [error] es un mensaje listo para mostrar. */
data class ResultadoIngreso(val ok: Boolean, val nuevo: Boolean = false, val error: String? = null)

suspend fun registrarIngresoConQr(contenidoQr: String): ResultadoIngreso {
    return try {
        val r = Api.post("/v1/ingresos", JSONObject().put("qr", contenidoQr.trim()))
        ResultadoIngreso(ok = true, nuevo = r.optBoolean("nuevo"))
    } catch (e: Api.ErrorApi) {
        ResultadoIngreso(ok = false, error = e.message)
    } catch (e: Exception) {
        ResultadoIngreso(ok = false, error = "Sin conexión. Revisá internet y volvé a escanear.")
    }
}

/** Desde cuándo está adentro (el último ingreso, si fue hace menos de
 *  [MINUTOS_EN_EL_CLUB] minutos), o null si no está en el gimnasio. */
fun adentroDesde(ingresos: List<IngresoRegistro>?, ahora: Long = System.currentTimeMillis()): Long? =
    ingresos?.maxOfOrNull { it.timestamp }?.takeIf { ahora - it < MINUTOS_EN_EL_CLUB * 60_000L }

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
