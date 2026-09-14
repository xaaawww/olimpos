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

/** [metodo]: "qr" | "biometrico" | "manual" — el que el socio tenía
 *  activado al tocar el botón (ver AccesoScreen), no un dato leído de un
 *  lector real. Sirve para los logros "Puntualidad"/"Biométrico". */
data class IngresoRegistro(val timestamp: Long, val metodo: String)

suspend fun registrarIngresoEnFirebase(metodo: String): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_INGRESOS).document().set(
            mapOf(
                "socio_id" to socioActualId(),
                "timestamp" to System.currentTimeMillis(),
                "metodo" to metodo
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarIngresosDesdeFirebase(): List<IngresoRegistro>? {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_INGRESOS)
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()
        snapshot.documents.mapNotNull { doc ->
            val ts = doc.getLong("timestamp") ?: return@mapNotNull null
            IngresoRegistro(ts, doc.getString("metodo") ?: "manual")
        }
    } catch (e: Exception) {
        null
    }
}

/** `true` si ya hay un ingreso marcado en el día calendario de hoy — para
 *  deshabilitar el botón y no permitir marcar dos veces el mismo día. */
fun yaIngresoHoy(ingresos: List<IngresoRegistro>): Boolean {
    val hoy = java.util.Calendar.getInstance()
    return ingresos.any { ingreso ->
        val cal = java.util.Calendar.getInstance().apply { timeInMillis = ingreso.timestamp }
        cal.get(java.util.Calendar.DAY_OF_YEAR) == hoy.get(java.util.Calendar.DAY_OF_YEAR) &&
            cal.get(java.util.Calendar.YEAR) == hoy.get(java.util.Calendar.YEAR)
    }
}
