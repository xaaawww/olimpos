package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Perfil nutricional del socio (colección "perfiles_nutricionales", un
 * documento por socio). Antes "Guardar preferencias" en NutricionScreen
 * solo mostraba un aviso de texto — las casillas tildadas se perdían apenas
 * se salía de la pantalla, nunca llegaban a guardarse en ningún lado.
 */
data class PerfilNutricional(val preferencias: Set<String>, val excluidos: Set<String>)

private const val COLECCION_PERFILES_NUTRICIONALES = "perfiles_nutricionales"

suspend fun guardarPerfilNutricionalEnFirebase(preferencias: Set<String>, excluidos: Set<String>): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_PERFILES_NUTRICIONALES).document(socioActualId()).set(
            mapOf(
                "preferencias" to preferencias.toList(),
                "excluidos" to excluidos.toList()
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarPerfilNutricionalDesdeFirebase(): PerfilNutricional? {
    return try {
        val doc = Firebase.firestore.collection(COLECCION_PERFILES_NUTRICIONALES).document(socioActualId()).get().await()
        if (!doc.exists()) return null
        @Suppress("UNCHECKED_CAST")
        val preferencias = (doc.get("preferencias") as? List<String>)?.toSet() ?: emptySet()
        @Suppress("UNCHECKED_CAST")
        val excluidos = (doc.get("excluidos") as? List<String>)?.toSet() ?: emptySet()
        PerfilNutricional(preferencias, excluidos)
    } catch (e: Exception) {
        null
    }
}
