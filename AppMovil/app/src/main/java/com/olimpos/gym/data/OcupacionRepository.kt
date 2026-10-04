package com.olimpos.gym.data

/**
 * Ocupación en vivo del gimnasio (tabla "aforo") — antes la tarjeta "Ocupación del gimnasio" de Inicio
 * mostraba un número inventado que cambiaba solo cada pocos segundos (ver
 * el viejo OcupacionEnVivo en HomeScreen.kt). Ahora es un dato real: lo
 * carga a mano el dueño desde el sistema de empleados (ver
 * ocupacion_repo.py) — no hay ningún lector de accesos conectado a
 * la base, así que no se puede calcular solo.
 */
data class Ocupacion(val personas: Int, val capacidadMaxima: Int, val actualizadoMs: Long)

private const val CAPACIDAD_MAXIMA = 120

/** `null` si todavía no se pudo leer (sin conexión, etc.) — a diferencia
 *  de cuando el dueño simplemente nunca cargó un valor (ahí la API
 *  devuelve 0 personas igual que hace ocupacion_repo.py). */
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
