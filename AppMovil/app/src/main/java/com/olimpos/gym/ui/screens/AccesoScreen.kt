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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.fechaLegible
import com.olimpos.gym.data.registrarIngresoEnFirebase
import com.olimpos.gym.data.yaIngresoHoy
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

@Composable
fun AccesoScreen(onVolver: () -> Unit) {
    var qrActivo by remember { mutableStateOf(true) }
    var biometricoActivo by remember { mutableStateOf(false) }
    var relojVinculado by remember { mutableStateOf(false) }
    var aviso by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    val ingresos = DatosRemotos.ingresos ?: emptyList()
    val yaMarcado = yaIngresoHoy(ingresos)

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("Accesos y seguridad", "QR, biométrico y dispositivos", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            TarjetaOro(Modifier.fillMaxWidth()) {
                Text("Aforo actual", fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                Spacer(Modifier.height(10.dp))
                BarraProgreso(0.58f)
                Spacer(Modifier.height(6.dp))
                Text("70 de 120 personas en el club", fontSize = 11.5.sp, color = Olimpos.Muted)
            }

            SeccionLabel("Marcar ingreso")
            TarjetaOro(Modifier.fillMaxWidth().padding(bottom = 16.dp)) {
                Text(
                    if (yaMarcado) "Ya marcaste tu ingreso de hoy ✓" else "¿Llegaste al club? Marcalo acá.",
                    fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    "Todavía no hay lector conectado a la app — este botón es tu propio registro de asistencia, la base de tu racha y tus visitas del mes.",
                    fontSize = 11.sp, color = Olimpos.Muted
                )
                Spacer(Modifier.height(12.dp))
                BotonPrincipal(
                    if (yaMarcado) "Ingreso de hoy ya registrado" else "✅ Marcar mi ingreso de hoy",
                    habilitado = !yaMarcado
                ) {
                    scope.launch {
                        registrarIngresoEnFirebase()
                        DatosRemotos.recargarIngresos()
                    }
                }
            }

            SeccionLabel("Métodos de acceso")
            OpcionAcceso("🔳", "Código QR", "Mostrá el QR en el lector de entrada", qrActivo) {
                qrActivo = it
            }
            OpcionAcceso("🖐️", "Acceso biométrico", "Huella o reconocimiento facial", biometricoActivo) {
                biometricoActivo = it
                aviso = if (it) "Datos biométricos registrados ✓" else null
            }
            OpcionAcceso("⌚", "Reloj deportivo", "Vinculá tu reloj para ingresar sin el celular", relojVinculado) {
                relojVinculado = it
                aviso = if (it) "Reloj vinculado correctamente ✓" else null
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

            SeccionLabel("Historial de ingresos")
            if (ingresos.isEmpty()) {
                Text("Todavía no hay ingresos registrados.", fontSize = 12.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 12.dp))
            }
            ingresos.sortedDescending().forEach { timestamp ->
                Row(
                    Modifier
                        .fillMaxWidth()
                        .padding(bottom = 9.dp)
                        .clip(RoundedCornerShape(14.dp))
                        .background(Olimpos.Card)
                        .padding(horizontal = 15.dp, vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(fechaLegible(timestamp), fontWeight = FontWeight.Bold, fontSize = 12.5.sp, color = Olimpos.Cream)
                        Text("Ingreso registrado", fontSize = 11.sp, color = Olimpos.Muted)
                    }
                }
            }

            SeccionLabel("¿Problemas para ingresar?")
            BotonSecundario("Reportar problema de acceso") {
                aviso = "Reporte enviado. El equipo de seguridad lo va a revisar."
            }
        }
    }
}

@Composable
private fun OpcionAcceso(emoji: String, titulo: String, sub: String, activo: Boolean, onCambio: (Boolean) -> Unit) {
    TarjetaOro(Modifier.fillMaxWidth().padding(bottom = 10.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconoCuadrado(emoji)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(titulo, fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                Text(sub, fontSize = 11.sp, color = Olimpos.Muted)
            }
            androidx.compose.material3.Switch(
                checked = activo,
                onCheckedChange = onCambio,
                colors = androidx.compose.material3.SwitchDefaults.colors(
                    checkedThumbColor = Olimpos.Dark,
                    checkedTrackColor = Olimpos.Gold,
                    uncheckedThumbColor = Olimpos.Muted,
                    uncheckedTrackColor = Olimpos.Card,
                    uncheckedBorderColor = Olimpos.Line
                )
            )
        }
    }
}
