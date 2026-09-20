package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.firestore.firestore
import kotlinx.coroutines.tasks.await

/**
 * Tablón del club: avisos, eventos y promociones que publica SOLO el dueño
 * desde el sistema de empleados (ver tablon_repo.py). La app únicamente lo
 * lee — las reglas de Firestore no le dejan a ningún socio escribir nada, y
 * solo dejan leer lo que está publicado.
 */
enum class CategoriaTablon(val etiqueta: String, val emoji: String) {
    AVISO("Aviso", "📢"),
    EVENTO("Evento", "🎉"),
    PROMOCION("Promoción", "🏷️"),
    IMPORTANTE("Importante", "⚠️")
}

data class PublicacionTablon(
    val id: String,
    val titulo: String,
    val mensaje: String,
    val categoria: CategoriaTablon,
    val fijado: Boolean,
    val creadoMs: Long,
    val autor: String
)

/** Fijadas primero; dentro de cada grupo, la más reciente arriba. `null` si
 *  Firebase falló (se conserva lo que ya se había cargado). */
suspend fun cargarTablonDesdeFirebase(): List<PublicacionTablon>? {
    return try {
        Firebase.firestore.collection("tablon")
            .whereEqualTo("publicado", true)
            .get().await()
            .documents.mapNotNull { doc ->
                val titulo = doc.getString("titulo") ?: return@mapNotNull null
                PublicacionTablon(
                    id = doc.id,
                    titulo = titulo,
                    mensaje = doc.getString("mensaje") ?: "",
                    categoria = CategoriaTablon.entries.firstOrNull { it.etiqueta == doc.getString("categoria") }
                        ?: CategoriaTablon.AVISO,
                    fijado = doc.getBoolean("fijado") ?: false,
                    creadoMs = doc.getLong("creado_ms") ?: 0L,
                    autor = doc.getString("autor") ?: ""
                )
            }
            .sortedWith(compareByDescending<PublicacionTablon> { it.fijado }.thenByDescending { it.creadoMs })
    } catch (e: Exception) {
        null
    }
}
