package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.ObjetivoCompetencia

/** Fondo siempre oscuro para este momento (deliberado, sin importar el
 *  tema claro/oscuro elegido en Configuración): es una pantalla ritual,
 *  no una sección más de la app. */
private val NEGRO_A = Color(0xFF0B0900)
private val NEGRO_B = Color(0xFF000000)

/**
 * Pantalla a pantalla completa para elegir el objetivo. Se muestra al
 * iniciar la app cuando el socio todavía no tiene uno guardado (cuentas que
 * ya habían hecho el onboarding antes de que el objetivo se guardara — las
 * nuevas lo eligen en el paso 2 del onboarding). Después se cambia desde
 * Configuración, nunca desde la Arena.
 */
@Composable
fun ObjetivoScreen(objetivoActual: ObjetivoCompetencia?, onElegido: (ObjetivoCompetencia) -> Unit) {
    var seleccionado by remember { mutableStateOf(objetivoActual) }

    Column(
        Modifier
            .fillMaxSize()
            .background(Brush.verticalGradient(listOf(NEGRO_A, NEGRO_B)))
            .statusBarsPadding()
            .padding(horizontal = 24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text("🎯", fontSize = 40.sp)
        Spacer(Modifier.height(14.dp))
        Text(
            "¿Cuál es tu\nobjetivo?",
            fontSize = 27.sp, fontWeight = FontWeight.Black, color = Color(0xFFFAFAF0), lineHeight = 33.sp
        )
        Text(
            "Vamos a adaptar tus rankings, tu dieta, tu racha y tus metas de competencia. " +
                "Lo podés cambiar cuando quieras desde Configuración.",
            fontSize = 13.sp, color = Color(0xFF9C9880),
            modifier = Modifier.padding(top = 8.dp, bottom = 26.dp)
        )
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            ObjetivoCompetencia.entries.forEach { obj ->
                OpcionGrande(obj.emoji, obj.etiqueta, seleccionado == obj) { seleccionado = obj }
            }
        }
        Spacer(Modifier.height(22.dp))
        BotonPrincipal(
            "Confirmar objetivo",
            Modifier.fillMaxWidth(),
            habilitado = seleccionado != null
        ) { seleccionado?.let(onElegido) }
        Spacer(Modifier.height(18.dp))
    }
}
