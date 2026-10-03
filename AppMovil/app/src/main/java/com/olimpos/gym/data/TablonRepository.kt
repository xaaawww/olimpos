package com.olimpos.gym.data

/**
 * Tablón del club: avisos, eventos y promociones que publica SOLO el dueño
 * desde el sistema de empleados (ver tablon_repo.py). La app únicamente lo
 * lee — las API no le deja a ningún socio escribir nada, y solo
 * entrega lo que está publicado (tabla "tablonpublicaciones").
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
 *  la API falló (se conserva lo que ya se había cargado). */
suspend fun cargarTablonDesdeFirebase(): List<PublicacionTablon>? {
    return try {
        Api.get("/v1/tablon").optJSONArray("publicaciones")?.objetos().orEmpty().mapNotNull { j ->
            val titulo = j.textoONull("titulo") ?: return@mapNotNull null
            PublicacionTablon(
                id = j.optString("id"),
                titulo = titulo,
                mensaje = j.optString("mensaje", ""),
                categoria = CategoriaTablon.entries.firstOrNull { it.etiqueta == j.optString("categoria") }
                    ?: CategoriaTablon.AVISO,
                fijado = j.optBoolean("fijado", false),
                creadoMs = j.optLong("creado_ms", 0L),
                autor = j.optString("autor", "")
            )
        }.sortedWith(compareByDescending<PublicacionTablon> { it.fijado }.thenByDescending { it.creadoMs })
    } catch (e: Exception) {
        null
    }
}
