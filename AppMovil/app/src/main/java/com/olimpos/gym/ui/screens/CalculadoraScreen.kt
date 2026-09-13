package com.olimpos.gym.ui.screens

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
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.EJERCICIOS_FUERZA
import com.olimpos.gym.data.calcular1RM
import com.olimpos.gym.ui.theme.Olimpos

/** Calculadora de 1RM: elegís ejercicio, deslizás peso y repeticiones, y ves
 *  la estimación en vivo. Reemplaza al cálculo que antes vivía embebido en
 *  "Mis marcas" — ahora es su propia herramienta dentro de la Arena. */
@Composable
fun CalculadoraScreen(onVolver: () -> Unit) {
    var ejercicio by remember { mutableStateOf(EJERCICIOS_FUERZA[0]) }
    var peso by remember { mutableFloatStateOf(60f) }
    var reps by remember { mutableFloatStateOf(8f) }
    val oneRM = calcular1RM(peso, reps.toInt())

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("Calculadora", "Estimá tu 1RM por ejercicio", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            SeccionLabel("Ejercicio")
            FilaChips {
                EJERCICIOS_FUERZA.forEach { ej ->
                    ChipSeleccionable("${ej.emoji} ${ej.nombre}", ejercicio == ej) { ejercicio = ej }
                }
            }

            Spacer(Modifier.height(18.dp))

            TarjetaOro(Modifier.fillMaxWidth()) {
                Column(
                    Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        "1RM ESTIMADO · ${ejercicio.nombre.uppercase()}",
                        fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold,
                        letterSpacing = 1.2.sp, color = Olimpos.Muted
                    )
                    Spacer(Modifier.height(4.dp))
                    Row(verticalAlignment = Alignment.Bottom) {
                        Text(
                            "%.1f".format(oneRM),
                            fontSize = 46.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldLight
                        )
                        Text(
                            " kg", fontSize = 18.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Muted,
                            modifier = Modifier.padding(bottom = 8.dp)
                        )
                    }
                }

                Spacer(Modifier.height(22.dp))
                ControlDeslizante("PESO", "${peso.toInt()} kg", peso, 20f..250f) { peso = it }
                Spacer(Modifier.height(18.dp))
                ControlDeslizante("REPETICIONES", "${reps.toInt()}", reps, 1f..20f, pasos = 18) { reps = it }
            }

            SeccionLabel("Cómo se calcula")
            Text(
                "Estimación con la fórmula de Epley: peso × (1 + repeticiones ÷ 30). Es una referencia — " +
                    "tu 1RM real puede variar según técnica, descanso y estado del día.",
                fontSize = 12.5.sp, lineHeight = 18.sp, color = Olimpos.Muted
            )
        }
    }
}

@Composable
private fun ControlDeslizante(
    etiqueta: String, valorTexto: String, valor: Float, rango: ClosedFloatingPointRange<Float>,
    pasos: Int = 0, onValor: (Float) -> Unit
) {
    Column {
        Row(Modifier.fillMaxWidth()) {
            Text(etiqueta, fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp, color = Olimpos.Muted, modifier = Modifier.weight(1f))
            Text(valorTexto, fontSize = 13.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
        }
        Slider(
            value = valor,
            onValueChange = onValor,
            valueRange = rango,
            steps = pasos,
            colors = SliderDefaults.colors(
                thumbColor = Olimpos.Gold,
                activeTrackColor = Olimpos.Gold,
                inactiveTrackColor = Olimpos.Line
            )
        )
    }
}
