package com.olimpos.gym.data

/**
 * Ocupación en vivo del gimnasio. La calcula la API con las entradas reales
 * (tabla "accesos"): cada socio que tocó "Mostrar carnet de acceso" en
 * Inicio cuenta como adentro durante un rato (90 minutos, ver
 * MINUTOS_EN_EL_CLUB en ApiWorker/src/util.ts), porque no hay registro de
 * salida. El sistema de empleados muestra el mismo número (ocupacion_repo.py).
 */
data class Ocupacion(val personas: Int, val capacidadMaxima: Int, val actualizadoMs: Long)

private const val CAPACIDAD_MAXIMA = 120

/** `null` si todavía no se pudo leer (sin conexión, etc.); 0 personas si
 *  nadie mostró el carnet en el último rato. */
suspend fun cargarOcupacionDesdeFirebase(): Ocupacion? {
    return try {
        val j = Api.get("/v1/ocupacion")
        Ocupacion(
            personas = j.optInt("personas", 0),
            capacidadMaxima = j.optInt("capacidad_maxima", CAPACIDAD_MAXIMA),
            actualizadoMs = j.optLong("actualizado_ms", 0L)
        )
    } catch (e: Exception) {
        null
    }
}
