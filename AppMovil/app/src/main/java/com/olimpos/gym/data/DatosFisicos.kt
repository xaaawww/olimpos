package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.firestore.firestore
import kotlinx.coroutines.tasks.await

/**
 * Datos físicos del socio (colección "datos_fisicos" en Firestore, un
 * documento por uid). Los completa el propio socio en el onboarding
 * obligatorio del primer login (ver OnboardingScreen.kt) — a diferencia de
 * "socios_app" (que arma un empleado), esto lo escribe y actualiza el
 * socio sobre su propio documento únicamente (ver regla en
 * firestore.rules). Es la base real de la Escalera del Olimpo: sin peso
 * corporal real no hay forma de calcular cuántas veces su peso levanta.
 */
enum class SexoBiologico(val etiqueta: String) {
    MASCULINO("Masculino"),
    FEMENINO("Femenino"),
    PREFIERO_NO_DECIRLO("Prefiero no decirlo")
}

data class DatosFisicos(
    val pesoKg: Float,
    val edad: Int,
    val sexo: SexoBiologico,
    val experiencia: String,
    val condicionMedica: String = "",
    /** Si es true, este socio no aparece para el resto en la Escalera del
     *  Olimpo (ni en la búsqueda, ni en las listas de miembros, ni en el
     *  conteo de cada rango) — sigue viendo su PROPIO rango normalmente,
     *  ver ClasificacionScreen.kt. */
    val ocultoClasificacion: Boolean = false,
    /** Flags/contadores chicos de actividad, para Logros — se guardan acá
     *  en vez de crear una colección nueva por cada uno, ya total son solo
     *  un par de campos por socio (ver PlanoScreen/BodygraphScreen/
     *  ArenaScreen para dónde se actualiza cada uno). */
    val vioPlano: Boolean = false,
    val vistasBodygraph: Int = 0,
    val seccionesArenaVisitadas: Set<String> = emptySet()
)

private const val COLECCION_DATOS_FISICOS = "datos_fisicos"

suspend fun guardarDatosFisicos(datos: DatosFisicos): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_DATOS_FISICOS).document(socioActualId()).set(
            mapOf(
                "peso_kg" to datos.pesoKg,
                "edad" to datos.edad,
                "sexo" to datos.sexo.name,
                "experiencia" to datos.experiencia,
                "condicion_medica" to datos.condicionMedica,
                "oculto_clasificacion" to datos.ocultoClasificacion,
                "vio_plano" to datos.vioPlano,
                "vistas_bodygraph" to datos.vistasBodygraph,
                "secciones_arena_visitadas" to datos.seccionesArenaVisitadas.toList(),
                "actualizado_ms" to System.currentTimeMillis()
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

/** Solo cambia el "mostrar/ocultar" en Clasificación (update parcial, no
 *  pisa el resto del documento). */
suspend fun actualizarOcultoClasificacion(oculto: Boolean): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_DATOS_FISICOS).document(socioActualId())
            .update("oculto_clasificacion", oculto).await()
        true
    } catch (e: Exception) {
        false
    }
}

/** Las tres siguientes son para Logros — updates parciales chicos, cada
 *  una la dispara la pantalla correspondiente la primera vez que pasa lo
 *  que cuentan (ver PlanoScreen/BodygraphScreen/ArenaScreen). */
suspend fun marcarPlanoVisto(): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_DATOS_FISICOS).document(socioActualId())
            .update("vio_plano", true).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun incrementarVistaBodygraph(): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_DATOS_FISICOS).document(socioActualId())
            .update("vistas_bodygraph", com.google.firebase.firestore.FieldValue.increment(1)).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun marcarSeccionArenaVisitada(seccion: String): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_DATOS_FISICOS).document(socioActualId())
            .update("secciones_arena_visitadas", com.google.firebase.firestore.FieldValue.arrayUnion(seccion)).await()
        true
    } catch (e: Exception) {
        false
    }
}

private fun documentoADatosFisicos(doc: com.google.firebase.firestore.DocumentSnapshot): DatosFisicos? {
    val peso = doc.getDouble("peso_kg")?.toFloat() ?: return null
    return DatosFisicos(
        pesoKg = peso,
        edad = doc.getLong("edad")?.toInt() ?: 0,
        sexo = SexoBiologico.entries.firstOrNull { it.name == doc.getString("sexo") } ?: SexoBiologico.PREFIERO_NO_DECIRLO,
        experiencia = doc.getString("experiencia") ?: "",
        condicionMedica = doc.getString("condicion_medica") ?: "",
        ocultoClasificacion = doc.getBoolean("oculto_clasificacion") ?: false,
        vioPlano = doc.getBoolean("vio_plano") ?: false,
        vistasBodygraph = doc.getLong("vistas_bodygraph")?.toInt() ?: 0,
        seccionesArenaVisitadas = (doc.get("secciones_arena_visitadas") as? List<*>)
            ?.mapNotNull { it as? String }?.toSet() ?: emptySet()
    )
}

/** `null` = todavía no completó el onboarding (dispara la pantalla de
 *  datos físicos antes de dejarlo entrar a la app, ver MainActivity). */
suspend fun cargarDatosFisicosPropios(): DatosFisicos? {
    return try {
        val doc = Firebase.firestore.collection(COLECCION_DATOS_FISICOS).document(socioActualId()).get().await()
        if (doc.exists()) documentoADatosFisicos(doc) else null
    } catch (e: Exception) {
        null
    }
}

/** Para el ranking general: trae los datos físicos de TODOS los socios de
 *  una sola vez (una lectura, no N), para calcular el rango de cada uno
 *  contra su propio peso real en vez de una referencia fija compartida. */
suspend fun cargarDatosFisicosDeTodos(): Map<String, DatosFisicos> {
    return try {
        Firebase.firestore.collection(COLECCION_DATOS_FISICOS).get().await()
            .documents.mapNotNull { doc -> documentoADatosFisicos(doc)?.let { doc.id to it } }.toMap()
    } catch (e: Exception) {
        emptyMap()
    }
}
