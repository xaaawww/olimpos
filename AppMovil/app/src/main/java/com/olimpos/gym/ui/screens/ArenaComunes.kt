package com.olimpos.gym.ui.screens

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.R
import com.olimpos.gym.data.ZonaMuscular
import com.olimpos.gym.data.socioActualNombre
import com.olimpos.gym.ui.theme.Olimpos

/* ═══════════════════════════════════════════════════════
   Piezas comunes de las secciones de la Arena (Mapa corporal,
   Calculadora, Ejercicios, Logros, Mis marcas): encabezado con
   la marca, pestañas tipo píldora, tarjetas blancas y chips.
   ═══════════════════════════════════════════════════════ */

/** Dorado legible para texto: el GoldLight se pierde sobre fondo claro. */
val acentoTexto: Color @Composable get() = if (Olimpos.EsOscuro) Olimpos.GoldLight else Olimpos.GoldDark

/** Marca + avatar arriba, y debajo flecha de volver, título grande y
 *  subtítulo; [derecha] ocupa la esquina (fecha, contador de logros…).
 *  También engancha el Atrás del celular a [onVolver]. */
@Composable
fun EncabezadoArena(
    titulo: String,
    subtitulo: String,
    onVolver: () -> Unit,
    derecha: (@Composable () -> Unit)? = null
) {
    BackHandler(onBack = onVolver)
    Column(
        Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(top = 12.dp, bottom = 8.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Image(painterResource(R.drawable.logo_olimpos), contentDescription = "OlimpΩs", modifier = Modifier.size(26.dp))
            Spacer(Modifier.width(8.dp))
            Text("OlimpΩs", fontSize = 17.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream, modifier = Modifier.weight(1f))
            AvatarInicial(socioActualNombre().take(1).uppercase().ifEmpty { "?" }, tamano = 32)
        }
        Spacer(Modifier.height(16.dp))
        Row(verticalAlignment = Alignment.Top) {
            Box(
                Modifier
                    .padding(top = 2.dp)
                    .size(34.dp)
                    .clip(CircleShape)
                    .clickable(
                        interactionSource = remember { MutableInteractionSource() },
                        indication = null,
                        onClick = onVolver
                    ),
                contentAlignment = Alignment.CenterStart
            ) { Text("←", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Olimpos.Cream) }
            Spacer(Modifier.width(8.dp))
            Column(Modifier.weight(1f)) {
                Text(titulo, fontSize = 22.sp, lineHeight = 26.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
                Text(subtitulo, fontSize = 12.5.sp, color = Olimpos.Muted, lineHeight = 16.sp)
            }
            if (derecha != null) {
                Spacer(Modifier.width(8.dp))
                derecha()
            }
        }
    }
}

/** Pestañas tipo píldora de ancho parejo: la elegida en dorado lleno. */
@Composable
fun PestanasPildora(opciones: List<String>, elegida: Int, onElegir: (Int) -> Unit, modifier: Modifier = Modifier) {
    Row(modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        opciones.forEachIndexed { i, texto ->
            val activa = i == elegida
            Box(
                Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(12.dp))
                    .background(if (activa) Olimpos.Gold else Olimpos.Card)
                    .border(1.dp, if (activa) Olimpos.Gold else Olimpos.Line, RoundedCornerShape(12.dp))
                    .clickable { onElegir(i) }
                    .padding(vertical = 11.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    texto, fontSize = 12.5.sp, maxLines = 1, textAlign = TextAlign.Center,
                    fontWeight = if (activa) FontWeight.ExtraBold else FontWeight.SemiBold,
                    color = if (activa) Olimpos.Dark else Olimpos.Cream
                )
            }
        }
    }
}

/** Tarjeta lisa de las secciones de la Arena (más sobria que TarjetaOro). */
@Composable
fun TarjetaLisa(
    modifier: Modifier = Modifier,
    padding: Dp = 14.dp,
    contenido: @Composable ColumnScope.() -> Unit
) {
    Column(
        modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
            .padding(padding),
        content = contenido
    )
}

/** Chip chico de texto (músculo, categoría, nivel). [fuerte] = dorado. */
@Composable
fun ChipSuave(texto: String, fuerte: Boolean = true) {
    Box(
        Modifier
            .clip(RoundedCornerShape(8.dp))
            .background(if (fuerte) Olimpos.GoldSoft else Olimpos.Superficie2)
            .padding(horizontal = 9.dp, vertical = 4.dp)
    ) {
        Text(
            texto, fontSize = 10.5.sp, fontWeight = FontWeight.Bold, maxLines = 1,
            color = if (fuerte) acentoTexto else Olimpos.Muted
        )
    }
}

/** Dibujo del ejercicio (los mismos del sistema de empleados) en un cuadrado
 *  redondeado; si no tiene, el cuerpo con los músculos que trabaja. */
@Composable
fun ImagenEjercicio(dibujo: Int?, tamano: Dp, zonas: Set<ZonaMuscular> = emptySet(), radio: Dp = 12.dp) {
    Box(
        Modifier
            .size(tamano)
            .clip(RoundedCornerShape(radio))
            .background(if (dibujo != null) Color(0xFFF7F6F2) else Olimpos.GoldSoft),
        contentAlignment = Alignment.Center
    ) {
        if (dibujo != null) {
            Image(painterResource(dibujo), contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.size(tamano))
        } else {
            CuerpoMuscularMini(zonasActivas = zonas, tamano = tamano * 0.42f)
        }
    }
}

/** Ícono redondo de color suave con un emoji — los íconos de las filas. */
@Composable
fun IconoRedondo(emoji: String, tamano: Dp = 40.dp, apagado: Boolean = false) {
    Box(
        Modifier
            .size(tamano)
            .clip(CircleShape)
            .background(
                if (apagado) Brush.linearGradient(listOf(Olimpos.Superficie2, Olimpos.Superficie2))
                else Brush.linearGradient(listOf(Olimpos.GoldSoft, Olimpos.Gold.copy(alpha = 0.28f)))
            ),
        contentAlignment = Alignment.Center
    ) { Text(emoji, fontSize = (tamano.value * 0.45f).sp) }
}

@Composable
fun Chevron() {
    Text("›", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted)
}
