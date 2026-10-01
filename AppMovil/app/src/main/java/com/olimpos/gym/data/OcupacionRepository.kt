package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.firestore.firestore
import kotlinx.coroutines.tasks.await

/**
 * Ocupación en vivo del gimnasio (colección "configuracion_app", documento
 * "ocupacion") — antes la tarjeta "Ocupación del gimnasio" de Inicio
 * mostraba un número inventado que cambiaba solo cada pocos segundos (ver
 * el viejo OcupacionEnVivo en HomeScreen.kt). Ahora es un dato real: lo
 * carga a mano el dueño desde el sistema de empleados (ver
 * ocupacion_repo.py) — no hay ningún lector de accesos conectado a
 * Firestore, así que no se puede calcular solo.
 */
data class Ocupacion(val personas: Int, val capacidadMaxima: Int, val actualizadoMs: Long)

private const val COLECCION_CONFIG = "configuracion_app"
private const val DOC_OCUPACION = "ocupacion"
private const val CAPACIDAD_MAXIMA = 120

/** `null` si todavía no se pudo leer (sin conexión, etc.) — a diferencia
 *  de cuando el dueño simplemente nunca cargó un valor (ahí el documento
 *  no existe, y se devuelve 0 personas igual que hace ocupacion_repo.py). */
suspend fun cargarOcupacionDesdeFirebase(): Ocupacion? {
    return try {
        val doc = Firebase.firestore.collection(COLECCION_CONFIG).document(DOC_OCUPACION).get().await()
        Ocupacion(
            personas = (doc.getLong("personas") ?: 0L).toInt(),
            capacidadMaxima = CAPACIDAD_MAXIMA,
            actualizadoMs = doc.getLong("actualizado_ms") ?: 0L
        )
    } catch (e: Exception) {
        null
    }
}
