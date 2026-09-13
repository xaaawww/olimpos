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
import com.olimpos.gym.data.ENTRENADORES
import com.olimpos.gym.data.Entrenador
import com.olimpos.gym.data.SESIONES_EJEMPLO
import com.olimpos.gym.ui.theme.Olimpos

@Composable
fun EntrenadorScreen(onVolver: () -> Unit) {
    var aviso by remember { mutableStateOf<String?>(null) }
    val sesiones = remember { mutableStateOf(SESIONES_EJEMPLO.toMutableList()) }
    var reprogramando by remember { mutableStateOf<Int?>(null) }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("Tu entrenador", "Contacto y sesiones personalizadas", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            SeccionLabel("Entrenadores disponibles")
            ENTRENADORES.forEach { e ->
                TarjetaEntrenador(e) { aviso = "Solicitud enviada a ${e.nombre}. Te va a responder a la brevedad." }
            }

            aviso?.let {
                Spacer(Modifier.height(4.dp))
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

            SeccionLabel("Tus sesiones reservadas")
            if (sesiones.value.isEmpty()) {
                Text("No tenés sesiones personalizadas reservadas.", fontSize = 12.5.sp, color = Olimpos.Muted)
            }
            sesiones.value.forEachIndexed { i, s ->
                TarjetaOro(Modifier.fillMaxWidth().padding(bottom = 10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(s.entrenador, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp, color = Olimpos.Cream)
                            Text("${s.fecha} · ${s.hora}", fontSize = 12.sp, color = Olimpos.Muted)
                        }
                        ChipOro(s.estado)
                    }
                    Spacer(Modifier.height(10.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        BotonSecundario("Reprogramar", Modifier.weight(1f)) {
                            reprogramando = i
                        }
                        BotonSecundario("Cancelar", Modifier.weight(1f)) {
                            sesiones.value = sesiones.value.toMutableList().also { it.removeAt(i) }
                        }
                    }
                    if (reprogramando == i) {
                        Spacer(Modifier.height(10.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            listOf("Lun 15/09", "Mié 17/09", "Vie 19/09").forEach { nuevaFecha ->
                                ChipSeleccionable(nuevaFecha, false) {
                                    sesiones.value = sesiones.value.toMutableList().also {
                                        it[i] = it[i].copy(fecha = nuevaFecha, estado = "Reprogramada")
                                    }
                                    reprogramando = null
                                }
                            }
                        }
                    }
                }
            }

            SeccionLabel("Reservar nueva sesión")
            BotonPrincipal("+ Reservar sesión personalizada") {
                sesiones.value = (sesiones.value + com.olimpos.gym.data.SesionEntrenador(
                    ENTRENADORES[0].nombre, "Vie 19/09", "17:00", "Confirmada"
                )).toMutableList()
            }
        }
    }
}

@Composable
private fun TarjetaEntrenador(e: Entrenador, onContactar: () -> Unit) {
    TarjetaOro(Modifier.fillMaxWidth().padding(bottom = 10.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            AvatarInicial(e.nombre.first().toString())
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(e.nombre, fontWeight = FontWeight.ExtraBold, fontSize = 14.5.sp, color = Olimpos.Cream)
                Text(e.especialidad, fontSize = 11.5.sp, color = Olimpos.Muted)
                Text(e.disponibilidad, fontSize = 10.5.sp, color = Olimpos.Muted)
            }
        }
        Spacer(Modifier.height(10.dp))
        BotonSecundario("Contactar") { onContactar() }
    }
}
