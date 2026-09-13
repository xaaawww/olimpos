package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
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
import com.olimpos.gym.data.ALIMENTOS_EXCLUIBLES
import com.olimpos.gym.data.HISTORIAL_ALIMENTARIO
import com.olimpos.gym.data.PREFERENCIAS_ALIMENTARIAS
import com.olimpos.gym.data.RECOMENDACIONES_NUTRICIONALES
import com.olimpos.gym.ui.theme.Olimpos

@Composable
fun NutricionScreen(onVolver: () -> Unit) {
    var preferencias by remember { mutableStateOf(setOf<String>()) }
    var excluidos by remember { mutableStateOf(setOf<String>()) }
    var aviso by remember { mutableStateOf<String?>(null) }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("Mi nutrición", "Preferencias, plan y seguimiento", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            SeccionLabel("Preferencias alimentarias")
            FlowChips(PREFERENCIAS_ALIMENTARIAS, preferencias) { item ->
                preferencias = if (item in preferencias) preferencias - item else preferencias + item
            }

            SeccionLabel("Alimentos que preferís evitar")
            FlowChips(ALIMENTOS_EXCLUIBLES, excluidos) { item ->
                excluidos = if (item in excluidos) excluidos - item else excluidos + item
            }

            Spacer(Modifier.height(14.dp))
            BotonPrincipal("Guardar preferencias") {
                aviso = "Preferencias guardadas. Tu nutricionista las va a tener en cuenta en tu próximo plan."
            }
            aviso?.let {
                Spacer(Modifier.height(12.dp))
                Row(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(14.dp))
                        .background(Olimpos.GoldSoft)
                        .border(1.dp, Olimpos.Gold.copy(alpha = 0.35f), RoundedCornerShape(14.dp))
                        .padding(13.dp)
                ) {
                    Text(it, fontSize = 12.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.GoldLight)
                }
            }

            SeccionLabel("Recomendaciones para vos")
            RECOMENDACIONES_NUTRICIONALES.forEach { r ->
                TarjetaOro(Modifier.fillMaxWidth().padding(bottom = 10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(r.emoji, fontSize = 22.sp)
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text(r.titulo, fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                            Text(r.detalle, fontSize = 11.5.sp, color = Olimpos.Muted, lineHeight = 16.sp)
                        }
                    }
                }
            }

            SeccionLabel("Historial y progreso nutricional")
            HISTORIAL_ALIMENTARIO.forEach { h ->
                Row(
                    Modifier
                        .fillMaxWidth()
                        .padding(bottom = 9.dp)
                        .clip(RoundedCornerShape(14.dp))
                        .background(Olimpos.Card)
                        .padding(horizontal = 15.dp, vertical = 12.dp)
                ) {
                    Text(h.fecha, fontSize = 12.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldLight)
                    Spacer(Modifier.width(10.dp))
                    Text(h.resumen, fontSize = 12.sp, color = Olimpos.Muted)
                }
            }

            SeccionLabel("¿Necesitás ajustar tu plan?")
            BotonSecundario("Solicitar asesoramiento nutricional") {
                aviso = "Solicitud enviada a tu nutricionista. Te va a contactar dentro de las 48hs."
            }
        }
    }
}

@Composable
private fun FlowChips(opciones: List<String>, seleccionados: Set<String>, onToggle: (String) -> Unit) {
    val filas = opciones.chunked(3)
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        filas.forEach { fila ->
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                fila.forEach { item ->
                    ChipSeleccionable(item, item in seleccionados) { onToggle(item) }
                }
            }
        }
    }
}
