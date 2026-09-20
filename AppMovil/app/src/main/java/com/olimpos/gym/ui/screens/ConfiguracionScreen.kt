package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.data.guardarNotificacionesLogrosActivas
import com.olimpos.gym.ui.theme.Olimpos
import com.olimpos.gym.ui.theme.ThemeMode

@Composable
fun ConfiguracionScreen(
    onVolver: () -> Unit,
    themeMode: ThemeMode,
    onThemeMode: (ThemeMode) -> Unit,
    objetivo: ObjetivoCompetencia?,
    onObjetivo: (ObjetivoCompetencia) -> Unit
) {
    val contexto = LocalContext.current
    var notificacionesLogros by remember { mutableStateOf(LogrosToastState.notificacionesActivas) }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("Configuración", "Objetivo, apariencia y preferencias", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            SeccionLabel("Mi objetivo")
            Text(
                "Adapta tus rankings, tu dieta y la racha de dieta. Lo elegiste al empezar y lo podés cambiar cuando quieras.",
                fontSize = 12.5.sp, color = Olimpos.Muted,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            ObjetivoCompetencia.entries.forEach { opcion ->
                OpcionGrande(opcion.emoji, opcion.etiqueta, objetivo == opcion) { onObjetivo(opcion) }
                Spacer(Modifier.height(10.dp))
            }

            SeccionLabel("Apariencia")
            Text(
                "Elegí cómo se ve OlimpΩs en tu celular.",
                fontSize = 12.5.sp, color = Olimpos.Muted,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            ThemeMode.entries.forEach { modo ->
                OpcionTema(modo, themeMode == modo) { onThemeMode(modo) }
                Spacer(Modifier.height(10.dp))
            }

            SeccionLabel("Logros")
            FilaSwitch(
                emoji = "🏆",
                titulo = "Notificación de logro desbloqueado",
                sub = "Aviso rápido con sonido cuando conseguís uno nuevo",
                activo = notificacionesLogros,
                onCambio = { nuevo ->
                    notificacionesLogros = nuevo
                    LogrosToastState.notificacionesActivas = nuevo
                    guardarNotificacionesLogrosActivas(contexto, nuevo)
                }
            )
        }
    }
}

@Composable
private fun FilaSwitch(emoji: String, titulo: String, sub: String, activo: Boolean, onCambio: (Boolean) -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconoCuadrado(emoji)
        Spacer(Modifier.width(13.dp))
        Column(Modifier.weight(1f)) {
            Text(titulo, fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
            Text(sub, fontSize = 11.sp, color = Olimpos.Muted)
        }
        Switch(
            checked = activo,
            onCheckedChange = onCambio,
            colors = SwitchDefaults.colors(
                checkedThumbColor = Olimpos.Dark,
                checkedTrackColor = Olimpos.Gold,
                uncheckedThumbColor = Olimpos.Muted,
                uncheckedTrackColor = Olimpos.Card,
                uncheckedBorderColor = Olimpos.Line
            )
        )
    }
}

@Composable
private fun OpcionTema(modo: ThemeMode, seleccionado: Boolean, onClick: () -> Unit) {
    val emoji = when (modo) {
        ThemeMode.CLARO -> "☀️"
        ThemeMode.OSCURO -> "🌙"
        ThemeMode.AUTOMATICO -> "🔄"
    }
    val descripcion = when (modo) {
        ThemeMode.CLARO -> "Interfaz clara, ideal de día"
        ThemeMode.OSCURO -> "Look premium dorado sobre negro"
        ThemeMode.AUTOMATICO -> "Sigue la configuración del sistema"
    }
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(if (seleccionado) Olimpos.GoldSoft else Olimpos.Card)
            .border(1.dp, if (seleccionado) Olimpos.Gold else Olimpos.Line, RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 15.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconoCuadrado(emoji)
        Spacer(Modifier.width(13.dp))
        Column(Modifier.weight(1f)) {
            Text(modo.etiqueta, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp, color = Olimpos.Cream)
            Text(descripcion, fontSize = 11.5.sp, color = Olimpos.Muted)
        }
        Box(
            Modifier
                .size(24.dp)
                .clip(CircleShape)
                .background(if (seleccionado) Olimpos.Gold else androidx.compose.ui.graphics.Color.Transparent)
                .border(1.5.dp, if (seleccionado) Olimpos.Gold else Olimpos.Line, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            if (seleccionado) Text("✓", fontWeight = FontWeight.Black, fontSize = 12.sp, color = Olimpos.Dark)
        }
    }
}
