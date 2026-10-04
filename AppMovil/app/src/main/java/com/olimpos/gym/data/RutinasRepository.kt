package com.olimpos.gym.data

import org.json.JSONArray
import org.json.JSONObject

/**
 * Rutinas del socio (tablas "rutinas" y "rutinaejercicio" — ver rutinas_repo.py
 * en el sistema de empleados). Un socio puede tener varias: como mucho una con
 * "origen" = "entrenador" (armada desde el sistema de empleados) y cero o más
 * con "origen" = "socio" (armadas por él mismo desde "Mis rutinas", con
 * ejercicios del catálogo real o escritos a mano). El socio elige cuál sigue
 * en Entrenar marcando "activa" una sola a la vez. La API es quien aplica las
 * reglas (por ejemplo, no deja editar la rutina del entrenador).
 */
suspend fun cargarMisRutinas(): List<RutinaCompleta>? {
    return try {
        Api.get("/v1/rutinas").optJSONArray("rutinas")?.objetos()?.map { j ->
            RutinaCompleta(
                id = j.optString("id"), nombre = j.optString("nombre"), creadaPor = j.optString("creada_por", ""),
                origen = j.optString("origen", "entrenador"), activa = j.optBoolean("activa", false),
                ejercicios = j.optJSONArray("ejercicios")?.objetos()?.map { e ->
                    EjercicioRutina(
                        nombre = e.optString("nombre"), seriesObjetivo = e.optInt("series_objetivo", 3),
                        pesoBaseKg = e.optDouble("peso_base_kg", 0.0).toFloat(),
                        esPesoCorporal = e.optBoolean("es_peso_corporal", false),
                        ejercicioId = e.textoONull("ejercicio_id")
                    )
                } ?: emptyList()
            )
        } ?: emptyList()
    } catch (e: Exception) {
        null
    }
}

private fun cuerpoRutina(nombre: String, ejercicios: List<EjercicioRutina>): JSONObject {
    val lista = JSONArray()
    ejercicios.forEach {
        lista.put(
            JSONObject().put("nombre", it.nombre).put("series_objetivo", it.seriesObjetivo)
                .put("peso_base_kg", it.pesoBaseKg.toDouble()).put("es_peso_corporal", it.esPesoCorporal)
                .put("ejercicio_id", it.ejercicioId ?: JSONObject.NULL)
        )
    }
    return JSONObject().put("nombre", nombre).put("ejercicios", lista)
}

/** Marca [rutinaId] como la que sigue en Entrenar (la API apaga las demás).
 *  Vale para cualquiera de las rutinas del socio, incluida la del entrenador. */
suspend fun marcarRutinaActiva(rutinaId: String): Boolean {
    return try {
        Api.post("/v1/rutinas/$rutinaId/activar")
        true
    } catch (e: Exception) {
        false
    }
}

/** Crea una rutina propia nueva. Queda activa sola si es la primera que tiene
 *  el socio; si ya seguía otra, no se la cambia sin que él lo elija. */
suspend fun crearRutinaPropia(nombre: String, ejercicios: List<EjercicioRutina>): Boolean {
    return try {
        Api.post("/v1/rutinas", cuerpoRutina(nombre, ejercicios))
        true
    } catch (e: Exception) {
        false
    }
}

/** Edita una rutina propia ya existente (nunca una del entrenador). */
suspend fun editarRutinaPropia(rutinaId: String, nombre: String, ejercicios: List<EjercicioRutina>): Boolean {
    return try {
        Api.put("/v1/rutinas/$rutinaId", cuerpoRutina(nombre, ejercicios))
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun borrarRutinaPropia(rutinaId: String): Boolean {
    return try {
        Api.delete("/v1/rutinas/$rutinaId")
        true
    } catch (e: Exception) {
        false
    }
}
