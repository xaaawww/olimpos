package com.olimpos.gym.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import coil.compose.AsyncImage
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.EVOLUCION_PESO
import com.olimpos.gym.data.FotoProgreso
import com.olimpos.gym.data.HISTORIAL_ENTRENAMIENTOS
import com.olimpos.gym.data.PuntoEvolucion
import com.olimpos.gym.data.comprimirImagenABase64
import com.olimpos.gym.data.eliminarFotoProgresoEnFirebase
import com.olimpos.gym.data.evolucionDeFuerza
import com.olimpos.gym.data.fechaLegible
import com.olimpos.gym.data.subirFotoProgresoEnFirebase
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

@Composable
fun ProgresoScreen(onVolver: () -> Unit) {
    val marcas = DatosRemotos.marcas ?: emptyList()
    val evolucionFuerza = remember(marcas) { evolucionDeFuerza(marcas) }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("Mi progreso", "Historial y evolución", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            SeccionLabel("Fotos de progreso")
            SeccionFotosProgreso()

            SeccionLabel(
                if (evolucionFuerza != null) "Evolución de fuerza (${evolucionFuerza.ejercicio}, 1RM est. en kg)"
                else "Evolución de fuerza"
            )
            TarjetaOro(Modifier.fillMaxWidth()) {
                GraficoLinea(evolucionFuerza?.puntos ?: emptyList(), Olimpos.Gold)
            }

            SeccionLabel("Evolución de peso corporal (kg)")
            TarjetaOro(Modifier.fillMaxWidth()) {
                GraficoLinea(EVOLUCION_PESO, Olimpos.Green)
            }

            SeccionLabel("Historial de entrenamientos")
            if (HISTORIAL_ENTRENAMIENTOS.isEmpty()) {
                Text(
                    "Todavía no tenés sesiones registradas.",
                    fontSize = 12.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 12.dp)
                )
            }
            HISTORIAL_ENTRENAMIENTOS.forEach { s ->
                Row(
                    Modifier
                        .fillMaxWidth()
                        .padding(bottom = 9.dp)
                        .clip(RoundedCornerShape(16.dp))
                        .background(Olimpos.Card)
                        .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
                        .padding(horizontal = 15.dp, vertical = 13.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(Modifier.weight(1f)) {
                        Text("${s.fecha} · ${s.tipo}", fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                        Text("${s.duracion} · ${s.volumenKg}kg movidos", fontSize = 11.5.sp, color = Olimpos.Muted)
                    }
                }
            }
        }
    }
}

/** Fotos de progreso: una fila horizontal con lo ya subido + un tile para
 *  agregar una nueva. Se suben comprimidas (ver comprimirImagenABase64)
 *  porque este proyecto guarda las imágenes como texto adentro del propio
 *  documento de Firestore (no hay Firebase Storage configurado — mismo
 *  patrón que ya usan las fotos de los platos de Dieta), y un documento no
 *  puede pesar más de 1MB. */
@Composable
private fun SeccionFotosProgreso() {
    val contexto = LocalContext.current
    val scope = rememberCoroutineScope()
    val fotos = (DatosRemotos.fotosProgreso ?: emptyList()).sortedByDescending { it.timestamp }
    var subiendo by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    val selectorImagen = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia()
    ) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        subiendo = true
        error = null
        scope.launch {
            val base64 = comprimirImagenABase64(contexto, uri)
            if (base64 == null) {
                error = "No se pudo procesar esa imagen — probá con otra."
            } else {
                subirFotoProgresoEnFirebase(base64)
                DatosRemotos.recargarFotosProgreso()
            }
            subiendo = false
        }
    }

    Row(
        Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        fotos.forEach { foto ->
            TarjetaFotoProgreso(foto) {
                scope.launch {
                    eliminarFotoProgresoEnFirebase(foto.id)
                    DatosRemotos.recargarFotosProgreso()
                }
            }
        }
        TarjetaAgregarFoto(subiendo = subiendo) {
            selectorImagen.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly))
        }
    }
    if (fotos.isEmpty() && !subiendo) {
        Text(
            "Todavía no subiste ninguna foto de progreso.",
            fontSize = 12.sp, color = Olimpos.Muted,
            modifier = Modifier.padding(top = 8.dp, bottom = 4.dp)
        )
    }
    error?.let {
        Text(it, fontSize = 11.5.sp, color = Olimpos.Red, modifier = Modifier.padding(top = 6.dp))
    }
    Spacer(Modifier.height(6.dp))
}

@Composable
private fun TarjetaFotoProgreso(foto: FotoProgreso, onEliminar: () -> Unit) {
    val bytes = remember(foto.id) {
        try {
            java.util.Base64.getDecoder().decode(foto.imagenBase64)
        } catch (e: Exception) {
            null
        }
    }
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(Modifier.size(110.dp)) {
            AsyncImage(
                model = bytes,
                contentDescription = "Foto de progreso",
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxSize()
                    .clip(RoundedCornerShape(14.dp))
                    .border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp))
            )
            Box(
                Modifier
                    .padding(4.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(Olimpos.Dark.copy(alpha = 0.55f))
                    .clickable(onClick = onEliminar)
                    .padding(5.dp)
                    .align(Alignment.TopEnd)
            ) { Text("🗑️", fontSize = 11.sp) }
        }
        Spacer(Modifier.height(4.dp))
        Text(fechaLegible(foto.timestamp), fontSize = 9.5.sp, color = Olimpos.Muted)
    }
}

@Composable
private fun TarjetaAgregarFoto(subiendo: Boolean, onClick: () -> Unit) {
    Column(
        Modifier
            .size(110.dp)
            .clip(RoundedCornerShape(14.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp))
            .clickable(enabled = !subiendo, onClick = onClick),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(if (subiendo) "…" else "+", fontSize = 26.sp, fontWeight = FontWeight.Black, color = Olimpos.Gold)
        Text(
            if (subiendo) "Subiendo" else "Agregar foto",
            fontSize = 10.sp, color = Olimpos.Muted, modifier = Modifier.padding(horizontal = 6.dp)
        )
    }
}

@Composable
private fun GraficoLinea(datos: List<PuntoEvolucion>, color: androidx.compose.ui.graphics.Color) {
    if (datos.isEmpty()) {
        Text(
            "Todavía no hay suficientes datos para graficar.",
            fontSize = 12.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(vertical = 30.dp)
        )
        return
    }
    val maxV = datos.maxOf { it.valor }
    val minV = datos.minOf { it.valor }
    val rango = (maxV - minV).let { if (it == 0f) 1f else it }

    Canvas(
        Modifier
            .fillMaxWidth()
            .height(120.dp)
    ) {
        val pasoX = size.width / (datos.size - 1).coerceAtLeast(1)
        val puntos = datos.mapIndexed { i, p ->
            val x = i * pasoX
            val y = size.height - ((p.valor - minV) / rango) * size.height
            Offset(x, y)
        }
        for (i in 0 until puntos.size - 1) {
            drawLine(color, puntos[i], puntos[i + 1], strokeWidth = 3.dp.toPx())
        }
        puntos.forEach { p ->
            drawCircle(color, radius = 5.dp.toPx(), center = p)
            drawCircle(androidx.compose.ui.graphics.Color(0xFF120F00), radius = 2.dp.toPx(), center = p)
        }
    }
    Spacer(Modifier.height(8.dp))
    Row(Modifier.fillMaxWidth()) {
        datos.forEach { p ->
            Text(
                p.etiqueta, fontSize = 10.sp, color = Olimpos.Muted, fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f), textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
        }
    }
}
