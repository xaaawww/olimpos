package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.firestore.FieldValue
import com.google.firebase.firestore.SetOptions
import com.google.firebase.firestore.firestore
import kotlinx.coroutines.tasks.await
import java.util.Base64

/**
 * Comidas que el socio registra con una foto. Se guardan en DOS colecciones
 * a propósito:
 *  - "comidas_dia": un documento por día (id = "{uid}_{aaaammdd}") con los
 *    macros de cada horario y un resumen de la meta de ese día. Pesa muy
 *    poco, así que se trae TODO el historial de una vez — hace falta para
 *    calcular la racha.
 *  - "fotos_comidas": una foto por documento (id = "{uid}_{aaaammdd}_{horario}"),
 *    en Base64 como las fotos de progreso (no hay Firebase Storage). Se pide
 *    de a una, solo cuando hay que mostrarla.
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

private const val COLECCION_DIAS = "comidas_dia"
private const val COLECCION_FOTOS = "fotos_comidas"

private fun mapaDeMacros(m: Macros) = mapOf(
    "kcal" to m.kcal, "proteinas" to m.proteinas, "carbs" to m.carbs, "grasas" to m.grasas
)

suspend fun cargarDiasComidasDesdeFirebase(): List<DiaComidas>? {
    return try {
        Firebase.firestore.collection(COLECCION_DIAS)
            .whereEqualTo("socio_id", socioActualId())
            .get().await()
            .documents.mapNotNull { doc ->
                val fecha = doc.getString("fecha") ?: return@mapNotNull null
                val mapaComidas = doc.get("comidas") as? Map<*, *> ?: emptyMap<Any, Any>()
                val comidas = MomentoComida.entries.mapNotNull { m ->
                    val c = mapaComidas[m.clave] as? Map<*, *> ?: return@mapNotNull null
                    m to ComidaRegistrada(
                        momento = m,
                        macros = macrosDeMapa(c),
                        platoIds = (c["plato_ids"] as? List<*>)?.mapNotNull { it as? String }.orEmpty(),
                        nota = c["nota"] as? String ?: "",
                        horaMs = (c["hora_ms"] as? Number)?.toLong() ?: 0L
                    )
                }.toMap()
                val metaMapa = doc.get("meta") as? Map<*, *>
                val meta = metaMapa?.let { mm ->
                    val momentos = (mm["momentos"] as? List<*>).orEmpty()
                        .mapNotNull { clave -> MomentoComida.entries.firstOrNull { it.clave == clave } }
                        .toSet()
                    MetaDia(macrosDeMapa(mm), momentos)
                }
                DiaComidas(
                    fecha = fecha,
                    comidas = comidas,
                    meta = meta,
                    objetivo = ObjetivoCompetencia.entries.firstOrNull { it.name == doc.getString("objetivo") }
                )
            }
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
    val uid = socioActualId()
    val fecha = fechaClave()
    val ahora = System.currentTimeMillis()
    return try {
        val db = Firebase.firestore
        db.collection(COLECCION_FOTOS).document("${uid}_${fecha}_${momento.clave}").set(
            mapOf(
                "socio_id" to uid,
                "fecha" to fecha,
                "momento" to momento.clave,
                "imagen" to imagenBase64,
                "timestamp" to ahora
            )
        ).await()

        val dia = mutableMapOf<String, Any>(
            "socio_id" to uid,
            "fecha" to fecha,
            "actualizado_ms" to ahora,
            "comidas" to mapOf(
                momento.clave to (mapaDeMacros(macros) + mapOf(
                    "plato_ids" to platoIds, "nota" to nota, "hora_ms" to ahora
                ))
            )
        )
        if (meta != null) {
            dia["meta"] = mapaDeMacros(meta.macros) + mapOf("momentos" to meta.momentos.map { it.clave })
        }
        if (objetivo != null) dia["objetivo"] = objetivo.name
        // merge: no pisa las comidas de los otros horarios del mismo día.
        db.collection(COLECCION_DIAS).document("${uid}_$fecha").set(dia, SetOptions.merge()).await()
        true
    } catch (e: Exception) {
        false
    }
}

/** Borra la comida ya registrada de [fecha] en [momento] (por si se cargó mal). */
suspend fun borrarComidaEnFirebase(fecha: String, momento: MomentoComida): Boolean {
    val uid = socioActualId()
    return try {
        val db = Firebase.firestore
        db.collection(COLECCION_DIAS).document("${uid}_$fecha")
            .update("comidas.${momento.clave}", FieldValue.delete()).await()
        db.collection(COLECCION_FOTOS).document("${uid}_${fecha}_${momento.clave}").delete().await()
        true
    } catch (e: Exception) {
        false
    }
}

/** La foto de una comida ya registrada, lista para Coil; `null` si no hay. */
suspend fun cargarFotoComida(fecha: String, momento: MomentoComida): ByteArray? {
    return try {
        val doc = Firebase.firestore.collection(COLECCION_FOTOS)
            .document("${socioActualId()}_${fecha}_${momento.clave}").get().await()
        doc.getString("imagen")?.let { Base64.getDecoder().decode(it) }
    } catch (e: Exception) {
        null
    }
}
