package com.olimpos.gym.data


/**
 * Registro de consumo de agua (colección "registros_agua") — un marcado
 * propio de "hoy tomé agua" (no litros exactos), una vez por día. De acá
 * sale el logro "Hidratado" (7 días seguidos). Mismo patrón que los
 * ingresos al gimnasio (IngresoRepository.kt).
 */
suspend fun registrarAguaEnFirebase(): Boolean {
    return try {
        Api.post("/v1/agua")
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarRegistrosAguaDesdeFirebase(): List<Long>? {
    return try {
        val a = Api.get("/v1/agua").optJSONArray("registros")
        if (a == null) emptyList() else (0 until a.length()).map { a.optLong(it) }
    } catch (e: Exception) {
        null
    }
}

fun yaRegistroAguaHoy(registros: List<Long>): Boolean {
    val hoy = java.util.Calendar.getInstance()
    return registros.any { ts ->
        val cal = java.util.Calendar.getInstance().apply { timeInMillis = ts }
        cal.get(java.util.Calendar.DAY_OF_YEAR) == hoy.get(java.util.Calendar.DAY_OF_YEAR) &&
            cal.get(java.util.Calendar.YEAR) == hoy.get(java.util.Calendar.YEAR)
    }
}
