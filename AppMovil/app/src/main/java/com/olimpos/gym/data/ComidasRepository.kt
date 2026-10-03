package com.olimpos.gym.data

import org.json.JSONArray
import org.json.JSONObject
import java.util.Base64

/**
 * Comidas que el socio registra con una foto. En la base viven en tablas
 * separadas a propósito:
 *  - "comidasdia" + "comidasregistradas" (+ "comidaregistradaplatos"): un día
 *    con los macros de cada horario y un resumen de la meta de ese día. Pesa
 *    muy poco, así que se trae TODO el historial de una vez — hace falta para
 *    calcular la racha.
 *  - "fotoscomidas": una foto por horario, en Base64. Se pide de a una, solo
 *    cuando hay que mostrarla.
 */
data class ComidaRegistrada(
    val momento: MomentoComida,
    val macros: Macros,
    /** Ids de los platos asignados que dijo haber comido (vacío = otra comida). */
    val platoIds: List<String>,
    val nota: String,
    val horaMs: Long
)

data class DiaComidas(
    val fecha: String,
    val comidas: Map<MomentoComida, ComidaRegistrada>,
    /** Meta vigente la última vez que se registró algo ese día — así un día
     *  pasado no cambia si después el nutricionista cambia la dieta. */
    val meta: MetaDia?,
    val objetivo: ObjetivoCompetencia?
) {
    val totales: Macros get() = comidas.values.fold(Macros()) { acc, c -> acc + c.macros }
}

private fun jsonDeMacros(m: Macros) = JSONObject()
    .put("kcal", m.kcal).put("proteinas", m.proteinas).put("carbs", m.carbs).put("grasas", m.grasas)

suspend fun cargarDiasComidasDesdeFirebase(): List<DiaComidas>? {
    return try {
        Api.get("/v1/comidas").optJSONArray("dias")?.objetos()?.mapNotNull { dia ->
            val fecha = dia.optString("fecha").takeIf { it.isNotEmpty() } ?: return@mapNotNull null
            val mapa = dia.optJSONObject("comidas") ?: JSONObject()
            val comidas = MomentoComida.entries.mapNotNull { m ->
                val c = mapa.optJSONObject(m.clave) ?: return@mapNotNull null
                m to ComidaRegistrada(
                    momento = m, macros = macrosDeJson(c),
                    platoIds = c.optJSONArray("plato_ids")?.textos().orEmpty(),
                    nota = c.optString("nota", ""), horaMs = c.optLong("hora_ms", 0L)
                )
            }.toMap()
            val meta = dia.optJSONObject("meta")?.let { mm ->
                val momentos = mm.optJSONArray("momentos")?.textos().orEmpty()
                    .mapNotNull { clave -> MomentoComida.entries.firstOrNull { it.clave == clave } }.toSet()
                MetaDia(macrosDeJson(mm), momentos)
            }
            DiaComidas(
                fecha = fecha, comidas = comidas, meta = meta,
                objetivo = ObjetivoCompetencia.entries.firstOrNull { it.name == dia.textoONull("objetivo") }
            )
        } ?: emptyList()
    } catch (e: Exception) {
        null
    }
}

/** Guarda (o reemplaza) la comida de hoy en [momento]: la foto y los macros. */
suspend fun registrarComidaEnFirebase(
    momento: MomentoComida,
    macros: Macros,
    platoIds: List<String>,
    nota: String,
    imagenBase64: String,
    meta: MetaDia?,
    objetivo: ObjetivoCompetencia?
): Boolean {
    return try {
        val cuerpo = jsonDeMacros(macros)
            .put("fecha", fechaClave())
            .put("momento", momento.clave)
            .put("plato_ids", JSONArray(platoIds))
            .put("nota", nota)
            .put("imagen", imagenBase64)
        if (meta != null) cuerpo.put("meta", jsonDeMacros(meta.macros).put("momentos", JSONArray(meta.momentos.map { it.clave })))
        if (objetivo != null) cuerpo.put("objetivo", objetivo.name)
        Api.put("/v1/comidas", cuerpo)
        true
    } catch (e: Exception) {
        false
    }
}

/** Borra la comida ya registrada de [fecha] en [momento] (por si se cargó mal). */
suspend fun borrarComidaEnFirebase(fecha: String, momento: MomentoComida): Boolean {
    return try {
        Api.delete("/v1/comidas/$fecha/${momento.clave}")
        true
    } catch (e: Exception) {
        false
    }
}

/** La foto de una comida ya registrada, lista para Coil; `null` si no hay. */
suspend fun cargarFotoComida(fecha: String, momento: MomentoComida): ByteArray? {
    return try {
        Api.get("/v1/comidas/$fecha/${momento.clave}/foto").textoONull("imagen")?.let { Base64.getDecoder().decode(it) }
    } catch (e: Exception) {
        null
    }
}
