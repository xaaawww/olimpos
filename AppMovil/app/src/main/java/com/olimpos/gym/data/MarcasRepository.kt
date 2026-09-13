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
            .whereEqualTo("socio_id", socioActualId())
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

/** Rango general de un socio (promedio calibrado por ejercicio — ver
 *  [puntajeGeneralDeSocio]), para la Escalera del Olimpo — quién más del
 *  club llegó a cada nivel. [creadoMs] sale del alta de su acceso a la app
 *  (colección "socios_app", ver auth_repo.py); [pesoKg]/[sexo]/[edad] del
 *  onboarding (colección "datos_fisicos") — es la base real del cálculo,
 *  ya no una referencia fija compartida por todos. */
data class SocioRango(
    val socioId: String,
    val nombre: String,
    val nivel: NivelMuscular,
    val verificado: Boolean,
    val kgTotales: Float,
    val pesoKg: Float,
    val edad: Int?,
    val sexo: SexoBiologico?,
    val mejorLevantamiento: MejorLevantamiento?,
    val creadoMs: Long? = null
)

/** Referencia SOLO para el caso borde de una cuenta sin datos físicos
 *  todavía (no debería pasar: el onboarding es obligatorio desde el primer
 *  login — ver MainActivity — pero una cuenta de prueba vieja podría no
 *  tenerlos). */
private const val PESO_CORPORAL_REFERENCIA = 80f

/** Trae el rango general de TODOS los socios con marcas cargadas (no solo
 *  el actual), agrupando por socio_id, y cruzando contra sus datos físicos
 *  reales. Solo entran a la Escalera del Olimpo los que tengan marcas en
 *  al menos [MINIMO_EJERCICIOS_PARA_CLASIFICACION] ejercicios distintos —
 *  ver [puntajeGeneralDeSocio]. */
suspend fun cargarRangosDeSocios(): List<SocioRango>? {
    return try {
        val snapshotMarcas = Firebase.firestore.collection("marcas").get().await()
        // "socios_app": lo crea un empleado al darle acceso al socio (ver
        // auth_repo.py) — de ahí sale cuándo se unió cada uno.
        val creadoPorUid = try {
            Firebase.firestore.collection("socios_app").get().await()
                .documents.associate { it.id to it.getLong("creado_ms") }
        } catch (e: Exception) {
            emptyMap()
        }
        val datosFisicosPorUid = cargarDatosFisicosDeTodos()

        snapshotMarcas.documents
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
                val datosFisicos = datosFisicosPorUid[socioId]
                // El socio pidió no aparecer para los demás (botón en
                // Clasificación) — su propio rango sigue viéndolo él, ya
                // que eso se calcula aparte con sus propias marcas, no con
                // esta lista compartida.
                if (datosFisicos?.ocultoClasificacion == true) return@mapNotNull null
                val pesoCorporal = datosFisicos?.pesoKg ?: PESO_CORPORAL_REFERENCIA
                val puntajeGeneral = puntajeGeneralDeSocio(marcas, pesoCorporal, datosFisicos?.sexo) ?: return@mapNotNull null
                val resumen = resumenMuscular(marcas, pesoCorporal, datosFisicos?.sexo)
                SocioRango(
                    socioId = socioId,
                    nombre = nombre,
                    nivel = nivelDesdePuntaje(puntajeGeneral),
                    verificado = resumen.verificado,
                    kgTotales = kgTotalesVigentes(marcas, pesoCorporal),
                    pesoKg = pesoCorporal,
                    edad = datosFisicos?.edad,
                    sexo = datosFisicos?.sexo,
                    mejorLevantamiento = mejorLevantamientoVigente(marcas, pesoCorporal),
                    creadoMs = creadoPorUid[socioId]
                )
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
                "socio_id" to socioActualId(),
                "socio_nombre" to socioActualNombre(),
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

/** Borra una marca ya cargada. El Bodygraph y la Clasificación se
 *  recalculan a partir de lo que quede en Firestore (ver [resumenMuscular]/
 *  [puntajeGeneralDeSocio]), así que borrar la única marca de un ejercicio
 *  puede hacer bajar el rango — quien llama debe recargar [DatosRemotos]
 *  después de esto para que se note sin reiniciar la app. */
suspend fun eliminarMarcaEnFirebase(marcaId: String): Boolean {
    if (marcaId.isBlank()) return false
    return try {
        Firebase.firestore.collection("marcas").document(marcaId).delete().await()
        true
    } catch (e: Exception) {
        false
    }
}
