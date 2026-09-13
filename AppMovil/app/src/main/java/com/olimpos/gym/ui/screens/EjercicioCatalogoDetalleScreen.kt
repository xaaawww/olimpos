package com.olimpos.gym.ui.screens

import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.EjercicioCatalogo
import com.olimpos.gym.data.PuntoMuscular
import com.olimpos.gym.ui.theme.Olimpos

/** Detalle de un ejercicio de la Galería: dos cuadros — el cuerpo
 *  (frente/espalda, compartido con el Bodygraph) mostrando las zonas
 *  musculares trabajadas, y debajo la descripción del ejercicio. Cada
 *  zona, igual que en Dieta, muestra su propia descripción y etiquetas
 *  de cómo se fortalece con este ejercicio. */
@Composable
fun EjercicioCatalogoDetalleScreen(ejercicio: EjercicioCatalogo, onVolver: () -> Unit) {
    var activo by remember { mutableStateOf<PuntoMuscular?>(ejercicio.puntos.firstOrNull()) }
    val zonasActivas = remember(ejercicio) { ejercicio.puntos.map { it.zona }.toSet() }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver(ejercicio.nombre, "Músculos trabajados y técnica", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            // ── Frame 1: cuerpo con las zonas trabajadas ──
            SeccionLabel("Músculos trabajados")
            TarjetaOro(Modifier.fillMaxWidth()) {
                Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    CuerpoMuscular(zonasActivas = zonasActivas, tamano = 128.dp)
                }
            }

            if (ejercicio.puntos.isEmpty()) {
                Spacer(Modifier.height(10.dp))
                Text(
                    "Todavía no hay zonas musculares cargadas para este ejercicio.",
                    fontSize = 12.sp, color = Olimpos.Muted
                )
            } else {
                androidx.compose.animation.AnimatedVisibility(visible = activo != null, enter = fadeIn(), exit = fadeOut()) {
                    activo?.let { p ->
                        Column {
                            Spacer(Modifier.height(12.dp))
                            TarjetaPuntoMuscular(p)
                        }
                    }
                }

                if (ejercicio.puntos.size > 1) {
                    Spacer(Modifier.height(14.dp))
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        ejercicio.puntos.forEach { p ->
                            FilaPuntoMuscular(p, activa = activo?.id == p.id) { activo = p }
                        }
                    }
                }
            }

            // ── Frame 2: descripción del ejercicio ──
            SeccionLabel("Descripción del ejercicio")
            TarjetaOro(Modifier.fillMaxWidth()) {
                Text(
                    ejercicio.descripcion.ifBlank { "Sin descripción todavía." },
                    fontSize = 13.sp, lineHeight = 19.sp, color = Olimpos.Cream
                )
                if (ejercicio.tags.isNotEmpty()) {
                    Spacer(Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        ejercicio.tags.forEach { ChipOro(it) }
                    }
                }
            }
        }
    }
}

@Composable
private fun TarjetaPuntoMuscular(p: PuntoMuscular) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(18.dp))
            .background(Olimpos.GoldSoft)
            .border(1.dp, Olimpos.Gold.copy(alpha = 0.3f), RoundedCornerShape(18.dp))
            .padding(16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(p.zona.emoji, fontSize = 16.sp)
            Spacer(Modifier.width(8.dp))
            Text(p.nombre, fontSize = 15.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream)
        }
        Spacer(Modifier.height(6.dp))
        Text(
            p.descripcion.ifBlank { "Sin descripción todavía." },
            fontSize = 12.5.sp, lineHeight = 18.sp, color = Olimpos.Cream.copy(alpha = 0.78f)
        )
        if (p.tags.isNotEmpty()) {
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                p.tags.forEach { ChipOro(it) }
            }
        }
    }
}

@Composable
private fun FilaPuntoMuscular(p: PuntoMuscular, activa: Boolean, onClick: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(13.dp))
            .background(if (activa) Olimpos.GoldSoft else androidx.compose.ui.graphics.Color.Transparent)
            .clickable(onClick = onClick)
            .padding(horizontal = 11.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            Modifier
                .size(24.dp)
                .clip(CircleShape)
                .background(if (activa) Olimpos.Gold else Olimpos.GoldSoft),
            contentAlignment = Alignment.Center
        ) { Text(p.zona.emoji, fontSize = 11.sp) }
        Spacer(Modifier.width(11.dp))
        Text(p.nombre, fontSize = 13.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Cream)
    }
}
