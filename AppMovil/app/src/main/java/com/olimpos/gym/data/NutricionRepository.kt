package com.olimpos.gym.data

import org.json.JSONArray
import org.json.JSONObject

/**
 * Perfil nutricional del socio (colección "perfiles_nutricionales", un
 * documento por socio). Antes "Guardar preferencias" en NutricionScreen
 * solo mostraba un aviso de texto — las casillas tildadas se perdían apenas
 * se salía de la pantalla, nunca llegaban a guardarse en ningún lado.
 */
data class PerfilNutricional(val preferencias: Set<String>, val excluidos: Set<String>)

suspend fun guardarPerfilNutricionalEnFirebase(preferencias: Set<String>, excluidos: Set<String>): Boolean {
    return try {
        Api.put(
            "/v1/perfil-nutricional",
            JSONObject().put("preferencias", JSONArray(preferencias.toList())).put("excluidos", JSONArray(excluidos.toList()))
        )
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarPerfilNutricionalDesdeFirebase(): PerfilNutricional? {
    return try {
        val j = Api.get("/v1/perfil-nutricional")
        if (!j.optBoolean("existe", false)) return null
        PerfilNutricional(
            preferencias = j.optJSONArray("preferencias")?.textos()?.toSet() ?: emptySet(),
            excluidos = j.optJSONArray("excluidos")?.textos()?.toSet() ?: emptySet()
        )
    } catch (e: Exception) {
        null
    }
}
