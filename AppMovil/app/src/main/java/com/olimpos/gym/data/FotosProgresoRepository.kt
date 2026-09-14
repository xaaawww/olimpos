package com.olimpos.gym.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await
import java.io.ByteArrayOutputStream
import java.util.Base64

/**
 * Fotos de progreso del socio (colección "fotos_progreso") — para el
 * logro "Antes y después" y para poder comparar cómo cambió el cuerpo con
 * el tiempo. Igual que las fotos de los platos (ver DietasRepository.kt),
 * viajan como texto Base64 adentro del propio documento de Firestore —
 * este proyecto no tiene Firebase Storage configurado, así que en vez de
 * agregar esa pieza de infraestructura nueva se reutiliza el mismo
 * patrón que ya funciona para las dietas. Por eso hay que comprimir la
 * foto ANTES de subirla (ver [comprimirImagenABase64]): un documento de
 * Firestore no puede pesar más de 1MB.
 */
data class FotoProgreso(val id: String, val imagenBase64: String, val timestamp: Long)

private const val COLECCION_FOTOS_PROGRESO = "fotos_progreso"

suspend fun subirFotoProgresoEnFirebase(imagenBase64: String): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_FOTOS_PROGRESO).document().set(
            mapOf(
                "socio_id" to socioActualId(),
                "imagen" to imagenBase64,
                "timestamp" to System.currentTimeMillis()
            )
        ).await()
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun cargarFotosProgresoDesdeFirebase(): List<FotoProgreso>? {
    return try {
        val snapshot = Firebase.firestore.collection(COLECCION_FOTOS_PROGRESO)
            .whereEqualTo("socio_id", socioActualId())
            .get()
            .await()
        snapshot.documents.mapNotNull { doc ->
            val imagen = doc.getString("imagen") ?: return@mapNotNull null
            val timestamp = doc.getLong("timestamp") ?: return@mapNotNull null
            FotoProgreso(doc.id, imagen, timestamp)
        }
    } catch (e: Exception) {
        null
    }
}

suspend fun eliminarFotoProgresoEnFirebase(fotoId: String): Boolean {
    return try {
        Firebase.firestore.collection(COLECCION_FOTOS_PROGRESO).document(fotoId).delete().await()
        true
    } catch (e: Exception) {
        false
    }
}

/**
 * Achica y comprime la foto elegida en el picker ANTES de mandarla a
 * Firestore: una foto de celular sin tocar puede pesar varios MB, muy
 * por encima del límite de 1MB por documento. Primero mide el tamaño
 * real sin cargar todo el bitmap en memoria (`inJustDecodeBounds`), calcula
 * cuánto hace falta reducirlo, y recién ahí decodifica la versión chica.
 * `null` si la imagen no se pudo leer o no entra ni comprimida al máximo.
 */
fun comprimirImagenABase64(context: Context, uri: Uri, ladoMaximoPx: Int = 720): String? {
    return try {
        val resolver = context.contentResolver

        val limites = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, limites) }
            ?: return null

        var muestreo = 1
        while (limites.outWidth / muestreo > ladoMaximoPx * 2 || limites.outHeight / muestreo > ladoMaximoPx * 2) {
            muestreo *= 2
        }
        val opciones = BitmapFactory.Options().apply { inSampleSize = muestreo }
        val bitmapCrudo = resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, opciones) }
            ?: return null

        val escala = ladoMaximoPx.toFloat() / maxOf(bitmapCrudo.width, bitmapCrudo.height)
        val bitmapFinal = if (escala < 1f) {
            Bitmap.createScaledBitmap(
                bitmapCrudo,
                (bitmapCrudo.width * escala).toInt().coerceAtLeast(1),
                (bitmapCrudo.height * escala).toInt().coerceAtLeast(1),
                true
            )
        } else bitmapCrudo

        // Baja la calidad JPEG hasta que entre cómodo en un documento de
        // Firestore (dejando margen para el resto de los campos y el
        // ~33% extra que agrega codificar en Base64).
        var calidad = 80
        var bytes: ByteArray
        do {
            val salida = ByteArrayOutputStream()
            bitmapFinal.compress(Bitmap.CompressFormat.JPEG, calidad, salida)
            bytes = salida.toByteArray()
            calidad -= 15
        } while (bytes.size > 650_000 && calidad > 20)

        if (bytes.size > 700_000) return null
        Base64.getEncoder().encodeToString(bytes)
    } catch (e: Exception) {
        null
    }
}
