package com.olimpos.gym.ui.screens

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.ui.theme.Olimpos

/** Tarjeta base estilo sitio: fondo sutil + borde dorado tenue */
@Composable
fun TarjetaOro(
    modifier: Modifier = Modifier,
    radio: Int = 22,
    contenido: @Composable ColumnScope.() -> Unit
) {
    Column(
        modifier
            .clip(RoundedCornerShape(radio.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(radio.dp))
            .padding(16.dp),
        content = contenido
    )
}

/** Eyebrow: etiqueta pequeña dorada con guion, como en la landing */
@Composable
fun Eyebrow(texto: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            Modifier
                .width(14.dp)
                .height(2.dp)
                .background(Olimpos.Gold, RoundedCornerShape(2.dp))
        )
        Spacer(Modifier.width(8.dp))
        Text(
            texto.uppercase(),
            fontSize = 10.sp,
            fontWeight = FontWeight.ExtraBold,
            letterSpacing = 2.2.sp,
            color = Olimpos.Gold
        )
    }
}

/** Título de sección en mayúsculas apagadas */
@Composable
fun SeccionLabel(texto: String, modifier: Modifier = Modifier) {
    Text(
        texto.uppercase(),
        fontSize = 11.sp,
        fontWeight = FontWeight.ExtraBold,
        letterSpacing = 1.8.sp,
        color = Olimpos.Muted,
        modifier = modifier.padding(top = 24.dp, bottom = 11.dp)
    )
}

/** Chip dorado pequeño */
@Composable
fun ChipOro(texto: String) {
    Box(
        Modifier
            .clip(RoundedCornerShape(100.dp))
            .background(Olimpos.GoldSoft)
            .border(1.dp, Olimpos.Gold.copy(alpha = 0.35f), RoundedCornerShape(100.dp))
            .padding(horizontal = 11.dp, vertical = 5.dp)
    ) {
        Text(
            texto,
            fontSize = 11.sp,
            fontWeight = FontWeight.ExtraBold,
            color = Olimpos.GoldLight
        )
    }
}

/** Círculo con un tilde dibujado a mano (no el carácter "✓" de la fuente):
 *  el glifo Unicode de tilde no queda centrado dentro de su propio recuadro
 *  en la mayoría de las tipografías (le sobra aire arriba), así que por más
 *  que el Box lo centre, se ve corrido — dibujarlo como dos trazos en un
 *  Canvas lo deja siempre perfectamente centrado. */
@Composable
fun IconoCheck(tamano: androidx.compose.ui.unit.Dp = 16.dp, fondo: Color = Olimpos.Gold, trazo: Color = Color.White) {
    androidx.compose.foundation.Canvas(Modifier.size(tamano)) {
        drawCircle(color = fondo)
        val w = size.width
        val h = size.height
        val camino = androidx.compose.ui.graphics.Path().apply {
            moveTo(w * 0.26f, h * 0.52f)
            lineTo(w * 0.43f, h * 0.68f)
            lineTo(w * 0.76f, h * 0.32f)
        }
        drawPath(
            camino, color = trazo,
            style = androidx.compose.ui.graphics.drawscope.Stroke(
                width = w * 0.13f,
                cap = androidx.compose.ui.graphics.StrokeCap.Round,
                join = androidx.compose.ui.graphics.StrokeJoin.Round
            )
        )
    }
}

/** Encabezado estándar de sub-pantalla: flecha de volver + título */
@Composable
fun EncabezadoVolver(titulo: String, subtitulo: String? = null, onVolver: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(top = 14.dp, bottom = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            Modifier
                .size(38.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(Olimpos.Card)
                .border(1.dp, Olimpos.Line, RoundedCornerShape(12.dp))
                .clickable(
                    interactionSource = remember { MutableInteractionSource() },
                    indication = null,
                    onClick = onVolver
                ),
            contentAlignment = Alignment.Center
        ) { Text("←", color = Olimpos.GoldLight, fontWeight = FontWeight.Black, fontSize = 17.sp) }
        Spacer(Modifier.width(13.dp))
        Column {
            Text(titulo, fontSize = 18.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
            subtitulo?.let { Text(it, fontSize = 12.sp, color = Olimpos.Muted) }
        }
    }
}

/** Botón sólido dorado, ancho completo */
@Composable
fun BotonPrincipal(texto: String, modifier: Modifier = Modifier, habilitado: Boolean = true, onClick: () -> Unit) {
    val (padV, fuente) = tamanoBoton()
    Box(
        modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(
                if (habilitado) Brush.linearGradient(listOf(Olimpos.GoldLight, Olimpos.Gold, Olimpos.GoldDark))
                else Brush.linearGradient(listOf(Olimpos.Muted, Olimpos.Muted))
            )
            .alpha(if (habilitado) 1f else 0.5f)
            .clickable(enabled = habilitado, onClick = onClick)
            .padding(vertical = padV),
        contentAlignment = Alignment.Center
    ) {
        Text(texto, fontSize = fuente.sp, fontWeight = FontWeight.Black, letterSpacing = 0.5.sp, color = Olimpos.Dark)
    }
}

/** Botón fantasma con borde dorado */
@Composable
fun BotonSecundario(texto: String, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val (padV, fuente) = tamanoBoton()
    Box(
        modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
            .padding(vertical = padV),
        contentAlignment = Alignment.Center
    ) {
        Text(texto, fontSize = fuente.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldLight)
    }
}

/** Tamaño de botón adaptado al ancho real de pantalla (no una reducción
 *  proporcional de toda la UI): celulares angostos usan menos padding y
 *  una fuente levemente menor; celulares grandes, un poco más de aire. */
@Composable
private fun tamanoBoton(): Pair<androidx.compose.ui.unit.Dp, Float> {
    val anchoPantalla = androidx.compose.ui.platform.LocalConfiguration.current.screenWidthDp
    return when {
        anchoPantalla < 360 -> 12.dp to 12.5f
        anchoPantalla > 420 -> 16.dp to 14.5f
        else -> 15.dp to 14f
    }
}

/** Campo de texto estilo OlimpΩs */
@Composable
fun CampoOro(
    valor: String,
    onValor: (String) -> Unit,
    etiqueta: String,
    modifier: Modifier = Modifier,
    esPassword: Boolean = false,
    teclado: KeyboardType = KeyboardType.Text
) {
    OutlinedTextField(
        value = valor,
        onValueChange = onValor,
        label = { Text(etiqueta, color = Olimpos.Muted) },
        singleLine = true,
        visualTransformation = if (esPassword) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = KeyboardOptions(keyboardType = teclado),
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = Olimpos.Cream,
            unfocusedTextColor = Olimpos.Cream,
            focusedBorderColor = Olimpos.Gold,
            unfocusedBorderColor = Olimpos.Line,
            cursorColor = Olimpos.Gold,
            focusedLabelColor = Olimpos.GoldLight,
            unfocusedLabelColor = Olimpos.Muted,
            focusedContainerColor = Olimpos.Card,
            unfocusedContainerColor = Olimpos.Card
        )
    )
}

/** Campo de búsqueda compacto (pill redondeada, ícono de lupa + botón de limpiar) */
@Composable
fun CampoBusqueda(
    valor: String,
    onValor: (String) -> Unit,
    placeholder: String,
    modifier: Modifier = Modifier
) {
    OutlinedTextField(
        value = valor,
        onValueChange = onValor,
        placeholder = { Text(placeholder, color = Olimpos.Muted, fontSize = 13.sp) },
        leadingIcon = { Text("🔍", fontSize = 13.sp) },
        trailingIcon = {
            if (valor.isNotEmpty()) {
                Box(
                    Modifier
                        .clip(CircleShape)
                        .clickable(
                            interactionSource = remember { MutableInteractionSource() },
                            indication = null
                        ) { onValor("") }
                        .padding(6.dp)
                ) { Text("✕", color = Olimpos.Muted, fontSize = 12.sp) }
            }
        },
        singleLine = true,
        textStyle = androidx.compose.ui.text.TextStyle(fontSize = 13.5.sp, color = Olimpos.Cream),
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(100.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = Olimpos.Cream,
            unfocusedTextColor = Olimpos.Cream,
            focusedBorderColor = Olimpos.Gold,
            unfocusedBorderColor = Olimpos.Line,
            cursorColor = Olimpos.Gold,
            focusedContainerColor = Olimpos.Card,
            unfocusedContainerColor = Olimpos.Card
        )
    )
}

/** Chip seleccionable (para elegir objetivo, experiencia, días, etc.) */
@Composable
fun ChipSeleccionable(texto: String, seleccionado: Boolean, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Box(
        modifier
            .clip(RoundedCornerShape(100.dp))
            .background(if (seleccionado) Olimpos.Gold else Olimpos.Card)
            .border(1.dp, if (seleccionado) Olimpos.Gold else Olimpos.Line, RoundedCornerShape(100.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 15.dp, vertical = 10.dp)
    ) {
        Text(
            texto,
            fontSize = 12.5.sp,
            fontWeight = FontWeight.ExtraBold,
            color = if (seleccionado) Olimpos.Dark else Olimpos.Cream
        )
    }
}

/** Barra de progreso lineal reutilizable (0f..1f). [colores] permite usar un
 *  degradé distinto al dorado por defecto (por ejemplo, para que dos barras
 *  una debajo de la otra se distingan sin tener que fijarse de cerca).
 *  [divisiones] dibuja esa cantidad de líneas finas repartidas en la barra,
 *  a modo de escala — también opcional, 0 = sin líneas (el default de
 *  siempre). */
@Composable
fun BarraProgreso(
    fraccion: Float,
    modifier: Modifier = Modifier,
    alto: Int = 10,
    colores: List<Color> = listOf(Olimpos.GoldDark, Olimpos.Gold, Olimpos.GoldLight),
    divisiones: Int = 0
) {
    val frac by animateFloatAsState(fraccion.coerceIn(0f, 1f), tween(700), label = "barra")
    Box(
        modifier
            .fillMaxWidth()
            .height(alto.dp)
            .clip(RoundedCornerShape(100.dp))
            .background(Color.White.copy(alpha = 0.07f))
    ) {
        Box(
            Modifier
                .fillMaxWidth(frac)
                .height(alto.dp)
                .clip(RoundedCornerShape(100.dp))
                .background(Brush.linearGradient(colores))
        )
        if (divisiones > 0) {
            androidx.compose.foundation.Canvas(Modifier.fillMaxSize()) {
                val paso = size.width / divisiones
                for (i in 1 until divisiones) {
                    val x = paso * i
                    drawLine(
                        color = Color.Black.copy(alpha = 0.18f),
                        start = androidx.compose.ui.geometry.Offset(x, 0f),
                        end = androidx.compose.ui.geometry.Offset(x, size.height),
                        strokeWidth = 1.5.dp.toPx()
                    )
                }
            }
        }
    }
}

/** Punto/paso de un wizard (onboarding) */
@Composable
fun PuntosPaso(total: Int, actual: Int, modifier: Modifier = Modifier) {
    Row(modifier, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        repeat(total) { i ->
            Box(
                Modifier
                    .height(5.dp)
                    .width(if (i == actual) 22.dp else 14.dp)
                    .clip(RoundedCornerShape(100.dp))
                    .background(if (i <= actual) Olimpos.Gold else Olimpos.Line)
            )
        }
    }
}

/** Fila de chips que SIEMPRE desplaza en vez de comprimirse: usar esto (no
 *  un Row a secas) para cualquier selector de chips que pueda no entrar
 *  en una sola línea (ejercicios, días, objetivos, etc.) — evita que un
 *  chip termine con ancho forzado y el texto partido letra por letra. */
@Composable
fun FilaChips(modifier: Modifier = Modifier, contenido: @Composable RowScope.() -> Unit) {
    Row(
        modifier.horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        content = contenido
    )
}

/** Fila seleccionable grande: emoji + texto + check. Usada en pasos de
 *  onboarding y en selectores de una sola opción a pantalla completa. */
@Composable
fun OpcionGrande(emoji: String, texto: String, seleccionado: Boolean, onClick: () -> Unit) {
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
        Text(texto, fontSize = 14.5.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream, modifier = Modifier.weight(1f))
        Box(
            Modifier
                .size(24.dp)
                .clip(CircleShape)
                .background(if (seleccionado) Olimpos.Gold else Color.Transparent)
                .border(1.5.dp, if (seleccionado) Olimpos.Gold else Olimpos.Line, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            if (seleccionado) Text("✓", fontWeight = FontWeight.Black, fontSize = 12.sp, color = Olimpos.Dark)
        }
    }
}

/** Insignia compacta con el objetivo del socio. Se muestra arriba a la
 *  izquierda tanto en Arena como en Dieta. El objetivo se cambia desde
 *  Configuración, no desde la insignia (por eso [onClick] es opcional y hoy
 *  nadie lo usa). */
@Composable
fun BadgeObjetivo(objetivo: ObjetivoCompetencia, modifier: Modifier = Modifier, onClick: (() -> Unit)? = null) {
    Box(
        modifier
            .clip(RoundedCornerShape(100.dp))
            .background(Olimpos.GoldSoft)
            .border(1.dp, Olimpos.Gold.copy(alpha = 0.3f), RoundedCornerShape(100.dp))
            .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier)
            .padding(horizontal = 10.dp, vertical = 5.dp)
    ) {
        Text(
            "${objetivo.emoji} ${objetivo.etiqueta}",
            fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.GoldLight
        )
    }
}

/** Avatar circular con inicial */
@Composable
fun AvatarInicial(inicial: String, tamano: Int = 44) {
    Box(
        Modifier
            .size(tamano.dp)
            .clip(CircleShape)
            .background(Brush.linearGradient(listOf(Olimpos.GoldLight, Olimpos.GoldDark))),
        contentAlignment = Alignment.Center
    ) { Text(inicial, fontWeight = FontWeight.Black, color = Olimpos.Dark, fontSize = (tamano * 0.38f).sp) }
}
