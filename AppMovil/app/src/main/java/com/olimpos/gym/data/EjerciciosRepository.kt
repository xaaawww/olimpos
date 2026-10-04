package com.olimpos.gym.data

/**
 * Trae los ejercicios publicados desde el editor de empleados (tabla
 * "ejercicios" y sus hijas, vía la API). Devuelve `null` si la consulta
 * falla por cualquier motivo — quien llama decide en ese caso mostrar el
 * catálogo de ejemplo ([EJERCICIOS_CATALOGO_EJEMPLO]) en su lugar.
 *
 * No hay foto propia por ejercicio: cada punto guarda directamente la
 * [ZonaMuscular] elegida en el editor (sobre el mismo cuerpo compartido
 * que dibuja el Bodygraph), no coordenadas x/y.
 */
suspend fun cargarEjerciciosDesdeFirebase(): List<EjercicioCatalogo>? {
    return try {
        Api.get("/v1/ejercicios").optJSONArray("ejercicios")?.objetos()?.mapNotNull { j ->
            val nombre = j.optString("nombre").takeIf { it.isNotEmpty() } ?: return@mapNotNull null
            val puntos = j.optJSONArray("puntos")?.objetos()?.mapNotNull { p ->
                val zona = ZonaMuscular.entries.firstOrNull { it.name == p.optString("zona") } ?: return@mapNotNull null
                PuntoMuscular(
                    id = p.optString("id"), zona = zona,
                    nombre = p.optString("nombre").ifEmpty { zona.etiqueta },
                    descripcion = p.optString("descripcion", ""),
                    tags = p.optJSONArray("tags")?.textos()?.take(3) ?: emptyList()
                )
            } ?: emptyList()
            EjercicioCatalogo(
                id = j.optString("id"), nombre = nombre, descripcion = j.optString("descripcion", ""),
                tags = j.optJSONArray("tags")?.textos()?.take(3) ?: emptyList(), puntos = puntos
            )
        } ?: emptyList()
    } catch (e: Exception) {
        null
    }
}
