package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Trae los ejercicios publicados desde el editor de empleados (Firestore,
 * colección "ejercicios"). Devuelve `null` si Firebase todavía no está
 * configurado o si la consulta falla por cualquier motivo — quien llama
 * decide en ese caso mostrar el catálogo de ejemplo
 * ([EJERCICIOS_CATALOGO_EJEMPLO]) en su lugar.
 *
 * No hay foto propia por ejercicio: cada punto guarda directamente la
 * [ZonaMuscular] elegida en el editor (sobre el mismo cuerpo compartido
 * que dibuja el Bodygraph), no coordenadas x/y.
 */
suspend fun cargarEjerciciosDesdeFirebase(): List<EjercicioCatalogo>? {
    return try {
        val snapshot = Firebase.firestore.collection("ejercicios")
            .whereEqualTo("publicado", true)
            .get()
            .await()

        snapshot.documents.mapNotNull { doc ->
            val nombre = doc.getString("nombre") ?: return@mapNotNull null
            val descripcion = doc.getString("descripcion") ?: ""
            @Suppress("UNCHECKED_CAST")
            val tags = (doc.get("tags") as? List<String>)?.take(3) ?: emptyList()

            @Suppress("UNCHECKED_CAST")
            val puntosRaw = doc.get("puntos") as? List<Map<String, Any?>> ?: emptyList()
            val puntos = puntosRaw.mapNotNull { p ->
                val zonaStr = p["zona"] as? String ?: return@mapNotNull null
                val zona = ZonaMuscular.entries.firstOrNull { it.name == zonaStr } ?: return@mapNotNull null
                PuntoMuscular(
                    id = p["id"] as? String ?: "",
                    zona = zona,
                    nombre = p["nombre"] as? String ?: zona.etiqueta,
                    descripcion = p["descripcion"] as? String ?: "",
                    tags = (p["tags"] as? List<String>)?.take(3) ?: emptyList()
                )
            }

            EjercicioCatalogo(
                id = doc.id, nombre = nombre,
                descripcion = descripcion, tags = tags, puntos = puntos
            )
        }
    } catch (e: Exception) {
        null
    }
}
