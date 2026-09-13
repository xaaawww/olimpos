package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Marcas personales del socio (colección "marcas" en Firestore). El socio
 * las carga desde la Calculadora/Mis marcas; el sistema de empleados las
 * lee para que un entrenador o el dueño las verifique (ver sección
 * "Verificación de Marcas"). Devuelve `null` si Firebase falla, para que
 * quien llama use [MIS_MARCAS] de ejemplo como respaldo.
 */
suspend fun cargarMarcasDesdeFirebase(): List<MarcaPersonal>? {
    return try {
        val snapshot = Firebase.firestore.collection("marcas")
            .whereEqualTo("socio_id", SOCIO_ACTUAL_ID)
            .get()
            .await()

        snapshot.documents.mapNotNull { doc ->
            val ejercicio = doc.getString("ejercicio") ?: return@mapNotNull null
            val peso = doc.getDouble("peso")?.toFloat() ?: return@mapNotNull null
            val reps = doc.getLong("repeticiones")?.toInt() ?: return@mapNotNull null
            MarcaPersonal(
                id = doc.id,
                ejercicio = ejercicio,
                pesoKg = peso,
                reps = reps,
                fecha = doc.getString("fecha") ?: "",
                timestamp = doc.getLong("timestamp") ?: 0L,
                verificado = doc.getBoolean("verificado") ?: false
            )
        }
    } catch (e: Exception) {
        null
    }
}

/** Rango general de un socio (promedio de sus 19 zonas), para la Escalera
 *  del Olimpo — quién más del club llegó a cada nivel. */
data class SocioRango(val socioId: String, val nombre: String, val nivel: NivelMuscular, val verificado: Boolean)

/** Trae el rango general de TODOS los socios con marcas cargadas (no solo
 *  el actual), agrupando por socio_id. Sin perfil de socios todavía no hay
 *  forma de saber el peso corporal real de cada uno, así que se usa una
 *  referencia fija de 80kg para este cálculo — mismo criterio que usa el
 *  sistema de empleados (marcas_repo.py) para su ranking general. */
suspend fun cargarRangosDeSocios(): List<SocioRango>? {
    return try {
        val snapshot = Firebase.firestore.collection("marcas").get().await()
        snapshot.documents
            .groupBy { it.getString("socio_id") ?: "?" }
            .mapNotNull { (socioId, docs) ->
                val nombre = docs.firstOrNull()?.getString("socio_nombre") ?: socioId
                val marcas = docs.mapNotNull { doc ->
                    val ejercicio = doc.getString("ejercicio") ?: return@mapNotNull null
                    val peso = doc.getDouble("peso")?.toFloat() ?: return@mapNotNull null
                    val reps = doc.getLong("repeticiones")?.toInt() ?: return@mapNotNull null
                    MarcaPersonal(
                        id = doc.id, ejercicio = ejercicio, pesoKg = peso, reps = reps,
                        fecha = doc.getString("fecha") ?: "", timestamp = doc.getLong("timestamp") ?: 0L,
                        verificado = doc.getBoolean("verificado") ?: false
                    )
                }
                val resumen = resumenMuscular(marcas, pesoCorporalKg = 80f)
                if (!resumen.tieneMarcas) return@mapNotNull null
                val promedio = ZonaMuscular.entries.sumOf { (resumen.puntajes[it] ?: 0f).toDouble() } / ZonaMuscular.entries.size
                SocioRango(socioId, nombre, nivelDesdePuntaje(promedio.toFloat()), resumen.verificado)
            }
    } catch (e: Exception) {
        null
    }
}

/** Guarda una marca nueva, siempre como pendiente de verificar. El
 *  [timestamp] es lo que decide, en [resumenMuscular], que esta marca
 *  reemplace a la anterior del mismo ejercicio en vez de acumularse. */
suspend fun guardarMarcaEnFirebase(ejercicio: String, pesoKg: Float, reps: Int, fecha: String, timestamp: Long): Boolean {
    return try {
        val doc = Firebase.firestore.collection("marcas").document()
        doc.set(
            mapOf(
                "socio_id" to SOCIO_ACTUAL_ID,
                "socio_nombre" to SOCIO_ACTUAL_NOMBRE,
                "ejercicio" to ejercicio,
                "peso" to pesoKg,
                "repeticiones" to reps,
                "fecha" to fecha,
                "timestamp" to timestamp,
                "verificado" to false
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}
