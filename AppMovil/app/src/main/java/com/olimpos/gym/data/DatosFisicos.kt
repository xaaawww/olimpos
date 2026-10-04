package com.olimpos.gym.data

import org.json.JSONArray
import org.json.JSONObject

/**
 * Datos físicos del socio. Los completa el propio socio en el onboarding
 * obligatorio del primer login (ver OnboardingScreen.kt) — a diferencia de
 * la ficha del socio (que arma un empleado), esto lo escribe y actualiza el
 * socio sobre sí mismo únicamente. Es la base real de la Escalera del
 * Olimpo: sin peso corporal real no hay forma de calcular cuántas veces su
 * peso levanta.
 *
 * En la base de datos se reparten en varias tablas (socios, perfilapp,
 * progresopeso, objetivos, salud...), pero la API los entrega y recibe como
 * un solo objeto — ver ApiWorker/src/rutas_socio.ts.
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
    /** Flags/contadores chicos de actividad, para Logros (ver PlanoScreen/
     *  BodygraphScreen/ArenaScreen para dónde se actualiza cada uno). */
    val vioPlano: Boolean = false,
    val vistasBodygraph: Int = 0,
    val seccionesArenaVisitadas: Set<String> = emptySet(),
    /** El objetivo que eligió al iniciar (o cambió después en Configuración).
     *  Vive en la base además de en el celular para que el nutricionista lo
     *  vea al armar la dieta y para no volver a pedirlo si entra desde otro
     *  dispositivo. `null` = todavía no eligió. */
    val objetivo: ObjetivoCompetencia? = null
)

suspend fun guardarDatosFisicos(datos: DatosFisicos): Boolean {
    return try {
        val cuerpo = JSONObject()
            .put("peso_kg", datos.pesoKg.toDouble())
            .put("edad", datos.edad)
            .put("sexo", datos.sexo.name)
            .put("experiencia", datos.experiencia)
            .put("condicion_medica", datos.condicionMedica)
            .put("oculto_clasificacion", datos.ocultoClasificacion)
            .put("vio_plano", datos.vioPlano)
            .put("vistas_bodygraph", datos.vistasBodygraph)
            .put("secciones_arena_visitadas", JSONArray(datos.seccionesArenaVisitadas.toList()))
        datos.objetivo?.let { cuerpo.put("objetivo", it.name) }
        Api.put("/v1/datos-fisicos", cuerpo)
        true
    } catch (e: Exception) {
        false
    }
}

private suspend fun actualizarParcial(cuerpo: JSONObject): Boolean {
    return try {
        Api.post("/v1/datos-fisicos/parcial", cuerpo)
        true
    } catch (e: Exception) {
        false
    }
}

/** Guarda el objetivo sin tocar el resto — para cuando lo elige por primera
 *  vez (cuentas que ya habían hecho el onboarding) o lo cambia en
 *  Configuración. */
suspend fun guardarObjetivoEnFirebase(objetivo: ObjetivoCompetencia): Boolean =
    actualizarParcial(JSONObject().put("objetivo", objetivo.name))

/** Solo cambia el "mostrar/ocultar" en Clasificación. */
suspend fun actualizarOcultoClasificacion(oculto: Boolean): Boolean =
    actualizarParcial(JSONObject().put("oculto_clasificacion", oculto))

/** Las tres siguientes son para Logros — updates chicos, cada una la dispara
 *  la pantalla correspondiente la primera vez que pasa lo que cuentan (ver
 *  PlanoScreen/BodygraphScreen/ArenaScreen). */
suspend fun marcarPlanoVisto(): Boolean = actualizarParcial(JSONObject().put("vio_plano", true))

suspend fun incrementarVistaBodygraph(): Boolean = actualizarParcial(JSONObject().put("incrementar_vista_bodygraph", true))

suspend fun marcarSeccionArenaVisitada(seccion: String): Boolean = actualizarParcial(JSONObject().put("seccion_arena", seccion))

internal fun jsonADatosFisicos(j: JSONObject): DatosFisicos? {
    val peso = j.numeroONull("peso_kg")?.toFloat() ?: return null
    return DatosFisicos(
        pesoKg = peso,
        edad = j.optInt("edad", 0),
        sexo = SexoBiologico.entries.firstOrNull { it.name == j.optString("sexo") } ?: SexoBiologico.PREFIERO_NO_DECIRLO,
        experiencia = j.optString("experiencia", ""),
        condicionMedica = j.optString("condicion_medica", ""),
        ocultoClasificacion = j.optBoolean("oculto_clasificacion", false),
        vioPlano = j.optBoolean("vio_plano", false),
        vistasBodygraph = j.optInt("vistas_bodygraph", 0),
        seccionesArenaVisitadas = j.optJSONArray("secciones_arena_visitadas")?.textos()?.toSet() ?: emptySet(),
        objetivo = ObjetivoCompetencia.entries.firstOrNull { it.name == j.textoONull("objetivo") }
    )
}

/** `null` = todavía no completó el onboarding (dispara la pantalla de
 *  datos físicos antes de dejarlo entrar a la app, ver MainActivity). */
suspend fun cargarDatosFisicosPropios(): DatosFisicos? {
    return try {
        val j = Api.get("/v1/datos-fisicos")
        if (j.optBoolean("existe", false)) jsonADatosFisicos(j) else null
    } catch (e: Exception) {
        null
    }
}
