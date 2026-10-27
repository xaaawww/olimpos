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
import androidx.compose.runtime.LaunchedEffect
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
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.Ocupacion
import com.olimpos.gym.data.cargarOcupacionDesdeFirebase
import com.olimpos.gym.data.fechaLegible
import com.olimpos.gym.ui.theme.Olimpos

@Composable
fun AccesoScreen(onVolver: () -> Unit) {
    val ingresos = DatosRemotos.ingresos ?: emptyList()
    // Mismo dato que la tarjeta "Ocupación del gimnasio" de Inicio; se vuelve
    // a pedir cuando cambian los ingresos (al escanear el QR acá abajo).
    var ocupacion by remember { mutableStateOf<Ocupacion?>(null) }
    LaunchedEffect(DatosRemotos.ingresos) {
        cargarOcupacionDesdeFirebase()?.let { ocupacion = it }
    }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("Accesos y seguridad", "Entrada con QR e historial", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            TarjetaOro(Modifier.fillMaxWidth()) {
                Text("Aforo actual", fontWeight = FontWeight.SemiBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                Spacer(Modifier.height(10.dp))
                val capacidad = ocupacion?.capacidadMaxima ?: 120
                BarraProgreso(if (capacidad > 0) (ocupacion?.personas ?: 0) / capacidad.toFloat() else 0f)
                Spacer(Modifier.height(6.dp))
                Text(
                    ocupacion?.let { "${it.personas} de ${it.capacidadMaxima} personas en el club" } ?: "Conectando…",
                    fontSize = 11.5.sp, color = Olimpos.Muted
                )
            }

            SeccionLabel("Entrada al gimnasio")
            TarjetaOro(Modifier.fillMaxWidth().padding(bottom = 16.dp)) {
                Text("Escaneá el QR de la recepción", fontWeight = FontWeight.SemiBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                Spacer(Modifier.height(4.dp))
                Text(
                    "Está en la pantalla del mostrador y cambia cada 30 segundos. Al escanearlo queda registrado que estás adentro: " +
                        "es la base de tu racha, tus visitas del mes y la ocupación del club.",
                    fontSize = 11.sp, color = Olimpos.Muted
                )
                Spacer(Modifier.height(12.dp))
                IngresoConQr()
            }

            SeccionLabel("Historial de ingresos")
            if (ingresos.isEmpty()) {
                Text("Todavía no hay ingresos registrados.", fontSize = 12.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 12.dp))
            }
            ingresos.sortedByDescending { it.timestamp }.forEach { ingreso ->
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
                        Text(fechaLegible(ingreso.timestamp), fontWeight = FontWeight.Bold, fontSize = 12.5.sp, color = Olimpos.Cream)
                        Text(
                            "Ingreso registrado · ${
                                when (ingreso.metodo) { "qr" -> "QR"; "biometrico" -> "Biométrico"; else -> "Manual" }
                            }",
                            fontSize = 11.sp, color = Olimpos.Muted
                        )
                    }
                }
            }

            SeccionLabel("¿Problemas para ingresar?")
            Text(
                "Si el QR no se lee o te dice que venció, esperá a que cambie en la pantalla y volvé a escanear. " +
                    "Si sigue sin funcionar, avisale a recepción.",
                fontSize = 11.5.sp, color = Olimpos.Muted
            )
        }
    }
}
