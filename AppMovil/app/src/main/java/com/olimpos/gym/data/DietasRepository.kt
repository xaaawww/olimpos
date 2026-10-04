package com.olimpos.gym.data

import java.util.Base64
import kotlin.math.atan2
import kotlin.math.min
import kotlin.math.sqrt

/**
 * Trae los platos publicados desde el editor de empleados (tabla "platos" y
 * sus hijas, vía la API). Devuelve `null` si la consulta falla por cualquier
 * motivo — quien llama decide en ese caso mostrar el catálogo de ejemplo
 * ([PLATOS]) en su lugar, para que la pantalla nunca se rompa.
 *
 * Las imágenes viajan como texto Base64 adentro de cada plato. Acá se
 * decodifican a ByteArray, que Coil sabe renderizar directamente.
 *
 * El editor guarda cada punto como coordenadas x/y en % (igual que el
 * plano del gimnasio), no como ángulo/radio sobre un plato giratorio.
 * [xyAPolar] hace esa conversión acá, así el resto de DietaScreen (la
 * animación de rotación) no necesita cambios.
 */
suspend fun cargarPlatosDesdeFirebase(): List<Plato>? {
    return try {
        Api.get("/v1/platos").optJSONArray("platos")?.objetos()?.mapNotNull { j ->
            val nombre = j.optString("nombre").takeIf { it.isNotEmpty() } ?: return@mapNotNull null
            val imagen = try {
                Base64.getDecoder().decode(j.optString("imagen").takeIf { it.isNotEmpty() } ?: return@mapNotNull null)
            } catch (e: IllegalArgumentException) {
                return@mapNotNull null
            }
            val macros = macrosDeJson(j.optJSONObject("macros")).takeUnless { it.esVacio }
            val items = j.optJSONArray("puntos")?.objetos()?.mapNotNull { p ->
                val x = p.numeroONull("x")?.toFloat() ?: return@mapNotNull null
                val y = p.numeroONull("y")?.toFloat() ?: return@mapNotNull null
                val (angulo, radio) = xyAPolar(x, y)
                Ingrediente(
                    emoji = "🍽️",
                    nombre = p.optString("nombre").ifEmpty { "Ingrediente" },
                    categoria = p.optString("categoria", ""),
                    angulo = angulo,
                    radio = radio,
                    kcal = p.optString("kcal", ""),
                    tags = p.optJSONArray("tags")?.textos() ?: emptyList(),
                    aporte = p.optString("aporte", ""),
                    beneficios = p.optJSONArray("beneficios")?.textos() ?: emptyList()
                )
            } ?: emptyList()
            if (items.isEmpty()) return@mapNotNull null
            Plato(
                id = j.optString("id"), nombre = nombre, emoji = "🍽️", imagen = imagen,
                descripcion = j.optString("descripcion", ""), tags = j.optJSONArray("tags")?.textos()?.take(3) ?: emptyList(),
                asignada = j.optBoolean("asignada", false), macros = macros, items = items
            )
        } ?: emptyList()
    } catch (e: Exception) {
        null
    }
}

/** Convierte una posición en % (0..100, con 50/50 = centro) a ángulo/radio
 *  sobre el plato giratorio (radio normalizado 0..100, igual escala que
 *  usan los ingredientes de ejemplo). */
private fun xyAPolar(xPct: Float, yPct: Float): Pair<Float, Float> {
    val dx = xPct - 50f
    val dy = yPct - 50f
    val distancia = sqrt(dx * dx + dy * dy)
    val radio = min(distancia * 2f, 100f)
    var angulo = Math.toDegrees(atan2(dy.toDouble(), dx.toDouble())).toFloat()
    if (angulo < 0f) angulo += 360f
    return angulo to radio
}
