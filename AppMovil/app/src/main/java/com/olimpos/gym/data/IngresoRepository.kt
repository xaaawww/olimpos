package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Ingresos al gimnasio (colección "ingresos"). Hoy no hay ningún torniquete
 * ni lector físico conectado a Firestore — el "acceso QR/biométrico/reloj"
 * de AccesoScreen son solo preferencias locales del socio, no eventos
 * reales — así que el ingreso lo marca el propio socio, una vez por día,
 * con un botón explícito ("Marcar mi ingreso de hoy"). De acá salen la
 * racha de días y las visitas del mes en Perfil, y varios Logros —
 * ninguno inventado.
 */
private const val COLECCION_INGRESOS = "ingresos"

suspend fun registrarIngresoEnFirebase(): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_INGRESOS).document().set(
            mapOf(
                "socio_id" to socioActualId(),
                "timestamp" to System.currentTimeMillis()
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

/** Devuelve solo los timestamps (no hace falta más para racha/visitas). */
suspend fun cargarIngresosDesdeFirebase(): List<Long>? {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_INGRESOS)
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()
        snapshot.documents.mapNotNull { it.getLong("timestamp") }
    } catch (e: Exception) {
        null
    }
}

/** `true` si ya hay un ingreso marcado en el día calendario de hoy — para
 *  deshabilitar el botón y no permitir marcar dos veces el mismo día. */
fun yaIngresoHoy(ingresos: List<Long>): Boolean {
    val hoy = java.util.Calendar.getInstance()
    return ingresos.any { ts ->
        val cal = java.util.Calendar.getInstance().apply { timeInMillis = ts }
        cal.get(java.util.Calendar.DAY_OF_YEAR) == hoy.get(java.util.Calendar.DAY_OF_YEAR) &&
            cal.get(java.util.Calendar.YEAR) == hoy.get(java.util.Calendar.YEAR)
    }
}
