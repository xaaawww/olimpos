package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Rutinas asignadas (colección "rutinas_asignadas" en Firestore — ver
 * rutinas_repo.py). Antes había como mucho UN documento por socio (id = su
 * uid), armado solo por un entrenador desde el sistema de empleados. Ahora
 * puede haber varios documentos por socio (id autogenerado, con el campo
 * "socio_id"): como mucho uno con "origen" = "entrenador", y cero o más con
 * "origen" = "socio" (armadas por el propio socio desde "Mis rutinas", con
 * ejercicios del catálogo real o escritos a mano). El socio elige cuál
 * sigue en Entrenar marcando "activa" en una sola a la vez.
 */
private const val COLECCION_RUTINAS = "rutinas_asignadas"

suspend fun cargarMisRutinas(): List<RutinaCompleta>? {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_RUTINAS)
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()
        snapshot.documents.mapNotNull { doc -> docARutina(doc.id, doc.data ?: return@mapNotNull null) }
    } catch (e: Exception) {
        null
    }
}

private fun docARutina(id: String, m: Map<String, Any?>): RutinaCompleta? {
    val nombre = m["nombre"] as? String ?: return null
    val creadaPor = m["creada_por"] as? String ?: ""
    val origen = m["origen"] as? String ?: "entrenador"
    val activa = m["activa"] as? Boolean ?: false
    @Suppress("UNCHECKED_CAST")
    val ejerciciosRaw = m["ejercicios"] as? List<Map<String, Any?>> ?: emptyList()
    val ejercicios = ejerciciosRaw.mapNotNull { e ->
        val nombreEj = e["nombre"] as? String ?: return@mapNotNull null
        val series = (e["series_objetivo"] as? Long)?.toInt() ?: (e["series_objetivo"] as? Double)?.toInt() ?: 3
        val peso = (e["peso_base_kg"] as? Double)?.toFloat() ?: (e["peso_base_kg"] as? Long)?.toFloat() ?: 0f
        val esPesoCorporal = e["es_peso_corporal"] as? Boolean ?: false
        val ejercicioId = e["ejercicio_id"] as? String
        EjercicioRutina(nombreEj, series, peso, esPesoCorporal, ejercicioId)
    }
    return RutinaCompleta(id, nombre, creadaPor, origen, activa, ejercicios)
}

private fun ejerciciosAMapa(ejercicios: List<EjercicioRutina>): List<Map<String, Any?>> = ejercicios.map {
    mapOf(
        "nombre" to it.nombre, "series_objetivo" to it.seriesObjetivo,
        "peso_base_kg" to it.pesoBaseKg, "es_peso_corporal" to it.esPesoCorporal,
        "ejercicio_id" to it.ejercicioId
    )
}

/** Marca [rutinaId] como la única activa entre [todasLasPropias] (el resto
 *  de las mismas pasan a `false`) — puede tocar este campo en cualquiera de
 *  las suyas, incluida una armada por el entrenador (ver firestore.rules). */
suspend fun marcarRutinaActiva(rutinaId: String, todasLasPropias: List<RutinaCompleta>): Boolean {
    return try {
        val db = Firebase.firestore
        val batch = db.batch()
        for (r in todasLasPropias) {
            batch.update(db.collection(COLECCION_RUTINAS).document(r.id), "activa", r.id == rutinaId)
        }
        batch.commit().await()
        true
    } catch (e: Exception) {
        false
    }
}

/** Crea una rutina propia nueva — [activa] en `true` solo si es la primera
 *  rutina que tiene este socio de cualquier origen (si ya seguía alguna,
 *  no se la cambia sin que él lo elija desde "Mis rutinas"). */
suspend fun crearRutinaPropia(nombre: String, ejercicios: List<EjercicioRutina>, yaTeniaAlguna: Boolean): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_RUTINAS).document().set(
            mapOf(
                "socio_id" to socioActualId(), "origen" to "socio", "activa" to !yaTeniaAlguna,
                "nombre" to nombre, "creada_por" to "Vos mismo", "ejercicios" to ejerciciosAMapa(ejercicios)
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

/** Edita una rutina propia ya existente (nunca una del entrenador — eso lo
 *  frena también firestore.rules, esto es solo para no ofrecer el botón). */
suspend fun editarRutinaPropia(rutinaId: String, nombre: String, ejercicios: List<EjercicioRutina>): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_RUTINAS).document(rutinaId).set(
            mapOf(
                "socio_id" to socioActualId(), "origen" to "socio",
                "nombre" to nombre, "creada_por" to "Vos mismo", "ejercicios" to ejerciciosAMapa(ejercicios)
            ), com.google.firebase.firestore.SetOptions.merge()
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun borrarRutinaPropia(rutinaId: String): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_RUTINAS).document(rutinaId).delete().await()
        true
    } catch (e: Exception) {
        false
    }
}
