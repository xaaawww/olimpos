package com.olimpos.gym.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.EVOLUCION_FUERZA
import com.olimpos.gym.data.EVOLUCION_PESO
import com.olimpos.gym.data.HISTORIAL_ENTRENAMIENTOS
import com.olimpos.gym.data.PuntoEvolucion
import com.olimpos.gym.ui.theme.Olimpos

@Composable
fun ProgresoScreen(onVolver: () -> Unit) {
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("Mi progreso", "Historial y evolución", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            SeccionLabel("Evolución de fuerza (sentadilla, kg)")
            TarjetaOro(Modifier.fillMaxWidth()) {
                GraficoLinea(EVOLUCION_FUERZA, Olimpos.Gold)
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
