package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DETALLES_EJERCICIOS
import com.olimpos.gym.ui.theme.Olimpos

@Composable
fun EjercicioDetalleScreen(nombre: String, onVolver: () -> Unit) {
    val detalle = DETALLES_EJERCICIOS[nombre]

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver(nombre, "Técnica y detalle del ejercicio", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            if (detalle == null) {
                Text("Todavía no hay detalle cargado para este ejercicio.", fontSize = 13.sp, color = Olimpos.Muted)
                return@Column
            }

            SeccionLabel("Músculos trabajados")
            Row(Modifier.fillMaxWidth()) {
                detalle.musculos.forEach { m ->
                    androidx.compose.foundation.layout.Box(Modifier.padding(end = 8.dp)) { ChipOro(m) }
                }
            }

            SeccionLabel("Técnica correcta")
            TarjetaOro(Modifier.fillMaxWidth()) {
                Text(detalle.tecnica, fontSize = 13.sp, color = Olimpos.Cream, lineHeight = 19.sp)
            }

            SeccionLabel("Series, repeticiones y descanso")
            Row(Modifier.fillMaxWidth()) {
                DatoRapido("${detalle.series}", "Series", Modifier.weight(1f))
                DatoRapido(detalle.reps, "Reps", Modifier.weight(1f))
                DatoRapido("${detalle.descansoSeg}s", "Descanso", Modifier.weight(1f))
            }

            SeccionLabel("Alternativa")
            TarjetaOro(Modifier.fillMaxWidth()) {
                Row {
                    Text("🔄", fontSize = 18.sp)
                    Spacer(Modifier.width(10.dp))
                    Text(detalle.alternativa, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Olimpos.Cream)
                }
            }
        }
    }
}

@Composable
private fun DatoRapido(valor: String, etiqueta: String, modifier: Modifier = Modifier) {
    Column(
        modifier
            .padding(4.dp)
            .clip(RoundedCornerShape(14.dp))
            .background(Olimpos.Card)
            .padding(vertical = 12.dp),
        horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally
    ) {
        Text(valor, fontSize = 17.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldLight)
        Text(etiqueta.uppercase(), fontSize = 9.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Muted)
    }
}
