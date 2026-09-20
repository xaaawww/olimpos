package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await
import java.util.Base64
import kotlin.math.atan2
import kotlin.math.min
import kotlin.math.sqrt

/**
 * Trae los platos publicados desde el editor de empleados (Firestore,
 * colección "dietas"). Devuelve `null` si Firebase todavía no está
 * configurado en este dispositivo (falta google-services.json) o si la
 * consulta falla por cualquier motivo — quien llama decide en ese caso
 * mostrar el catálogo de ejemplo ([PLATOS]) en su lugar, para que la
 * pantalla nunca se rompa mientras se termina de configurar Firebase.
 *
 * Las imágenes viajan como texto Base64 adentro del propio documento
 * (no en Firebase Storage: ese servicio pasó a requerir el plan pago
 * Blaze, y el proyecto se armó para no depender de una tarjeta). Acá se
 * decodifican a ByteArray, que Coil sabe renderizar directamente.
 *
 * El editor guarda cada punto como coordenadas x/y en % (igual que el
 * plano del gimnasio), no como ángulo/radio sobre un plato giratorio.
 * [xyAPolar] hace esa conversión acá, así el resto de DietaScreen (la
 * animación de rotación, ya construida en la Fase 1) no necesita cambios.
 */
suspend fun cargarPlatosDesdeFirebase(): List<Plato>? {
    return try {
        val snapshot = Firebase.firestore.collection("dietas")
            .whereEqualTo("publicado", true)
            .get()
            .await()

        val platos = snapshot.documents.mapNotNull { doc ->
            val nombre = doc.getString("nombre") ?: return@mapNotNull null
            val imagenB64 = doc.getString("imagen") ?: return@mapNotNull null
            val imagen = try {
                Base64.getDecoder().decode(imagenB64)
            } catch (e: IllegalArgumentException) {
                return@mapNotNull null
            }
            val descripcion = doc.getString("descripcion") ?: ""
            @Suppress("UNCHECKED_CAST")
            val tags = (doc.get("tags") as? List<String>)?.take(3) ?: emptyList()
            val asignada = doc.getBoolean("asignada") ?: false
            val macros = macrosDeMapa(doc.get("macros") as? Map<*, *>).takeUnless { it.esVacio }

            @Suppress("UNCHECKED_CAST")
            val puntosRaw = doc.get("puntos") as? List<Map<String, Any?>> ?: emptyList()
            val items = puntosRaw.mapNotNull { p ->
                val x = (p["x"] as? Number)?.toFloat() ?: return@mapNotNull null
                val y = (p["y"] as? Number)?.toFloat() ?: return@mapNotNull null
                val (angulo, radio) = xyAPolar(x, y)
                @Suppress("UNCHECKED_CAST")
                Ingrediente(
                    emoji = "🍽️",
                    nombre = p["nombre"] as? String ?: "Ingrediente",
                    categoria = p["categoria"] as? String ?: "",
                    angulo = angulo,
                    radio = radio,
                    kcal = p["kcal"] as? String ?: "",
                    tags = (p["tags"] as? List<String>) ?: emptyList(),
                    aporte = p["aporte"] as? String ?: "",
                    beneficios = (p["beneficios"] as? List<String>) ?: emptyList()
                )
            }
            if (items.isEmpty()) return@mapNotNull null
            Plato(
                id = doc.id, nombre = nombre, emoji = "🍽️", imagen = imagen,
                descripcion = descripcion, tags = tags, asignada = asignada, macros = macros, items = items
            )
        }
        platos
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
