package com.olimpos.gym.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import com.olimpos.gym.R
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.runtime.LaunchedEffect
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.PISOS
import com.olimpos.gym.data.PuntoPlano
import com.olimpos.gym.data.marcarPlanoVisto
import com.olimpos.gym.ui.theme.Olimpos
import kotlin.math.roundToInt

private val EASE = CubicBezierEasing(0.6f, 0f, 0.2f, 1f)
private const val ZOOM = 2.3f

@Composable
fun PlanoScreen(onVolver: () -> Unit) {
    var piso by remember { mutableIntStateOf(0) }
    var activo by remember { mutableStateOf<PuntoPlano?>(null) }
    val datos = PISOS[piso]

    // Para el logro "Cartógrafo" — se marca una sola vez, la primera vez
    // que el socio abre el Plano (el `if` evita reescribir el mismo true
    // cada vez que vuelve a entrar).
    LaunchedEffect(Unit) {
        if (DatosRemotos.datosFisicosPropios?.vioPlano != true) {
            marcarPlanoVisto()
            DatosRemotos.recargarDatosFisicosPropios()
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .background(Brush.linearGradient(listOf(Olimpos.FondoA, Olimpos.FondoB, Olimpos.FondoC)))
            .statusBarsPadding()
    ) {
        // ── Encabezado con volver ──
        Row(
            Modifier.padding(horizontal = 20.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(13.dp))
                    .background(Olimpos.Card)
                    .border(1.dp, Olimpos.Line, RoundedCornerShape(13.dp))
                    .clickable(onClick = onVolver),
                contentAlignment = Alignment.Center
            ) { Text("←", fontSize = 17.sp, color = Olimpos.GoldLight) }
            Spacer(Modifier.width(12.dp))
            Column {
                Text("Plano del club", fontSize = 17.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
                Text(
                    "RECORRIDO INTERACTIVO",
                    fontSize = 10.sp, fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 1.6.sp, color = Olimpos.Muted
                )
            }
        }

        // ── Selector de piso con deslizador ──
        BoxWithConstraints(
            Modifier
                .padding(horizontal = 20.dp)
                .fillMaxWidth()
                .clip(RoundedCornerShape(100.dp))
                .background(Olimpos.Card)
                .border(1.dp, Olimpos.Line, RoundedCornerShape(100.dp))
                .padding(4.dp)
        ) {
            val mitad = maxWidth / 2 - 4.dp
            val despl by animateFloatAsState(if (piso == 0) 0f else 1f, tween(400), label = "sw")
            Box(
                Modifier
                    .offset(x = (mitad + 4.dp) * despl)
                    .width(mitad + 4.dp)
                    .height(38.dp)
                    .clip(RoundedCornerShape(100.dp))
                    .background(Brush.linearGradient(listOf(Olimpos.Gold, Olimpos.GoldDark)))
            )
            Row {
                PISOS.forEachIndexed { i, p ->
                    Box(
                        Modifier
                            .weight(1f)
                            .height(38.dp)
                            .clip(RoundedCornerShape(100.dp))
                            .clickable { if (i != piso) { piso = i; activo = null } },
                        contentAlignment = Alignment.Center
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                if (i == 0) "Piso 1" else "Piso 2",
                                fontSize = 12.5.sp, fontWeight = FontWeight.ExtraBold,
                                color = if (i == piso) Olimpos.Dark else Olimpos.Muted
                            )
                            Spacer(Modifier.width(5.dp))
                            Text(
                                p.nivel.replace(" ", ""),
                                fontSize = 9.sp, fontWeight = FontWeight.Bold,
                                color = (if (i == piso) Olimpos.Dark else Olimpos.Muted).copy(alpha = 0.7f)
                            )
                        }
                    }
                }
            }
        }

        Spacer(Modifier.height(12.dp))

        // ═══════════ MAPA ═══════════
        // Relación de aspecto fija (1100:850, la del plano real) para que los puntos
        // en % coincidan siempre con el lugar correcto de la imagen, sea cual sea el
        // ancho de pantalla.
        BoxWithConstraints(
            Modifier
                .padding(horizontal = 20.dp)
                .fillMaxWidth()
                .aspectRatio(1100f / 850f)
                .clip(RoundedCornerShape(20.dp))
                .background(Color(0xFF0A0800))
                .border(1.dp, Olimpos.Line, RoundedCornerShape(20.dp))
        ) {
            val density = LocalDensity.current
            val wPx = with(density) { maxWidth.toPx() }
            val hPx = with(density) { maxHeight.toPx() }

            val enfocado = activo != null
            val escala by animateFloatAsState(if (enfocado) ZOOM else 1f, tween(650, easing = EASE), label = "mz")
            val tx by animateFloatAsState(
                if (enfocado) wPx * (0.5f - (activo!!.x / 100f) * ZOOM) else 0f,
                tween(650, easing = EASE), label = "mx"
            )
            val ty by animateFloatAsState(
                if (enfocado) hPx * (0.5f - (activo!!.y / 100f) * ZOOM) else 0f,
                tween(650, easing = EASE), label = "my"
            )

            // Capa transformable: plano + marcadores
            Box(
                Modifier
                    .fillMaxSize()
                    .graphicsLayer {
                        transformOrigin = TransformOrigin(0f, 0f)
                        scaleX = escala; scaleY = escala
                        translationX = tx; translationY = ty
                    }
            ) {
                // Imagen real del plano del piso (fondo/mapa visual)
                Image(
                    painter = painterResource(
                        if (piso == 0) R.drawable.plano_piso1 else R.drawable.plano_piso2
                    ),
                    contentDescription = "Plano ${datos.titulo}",
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color(0xFFEDE9DC)),
                    contentScale = ContentScale.Crop
                )

                // Marcadores (contra-escalados para mantener tamaño)
                datos.puntos.forEach { p ->
                    val esActivo = activo?.n == p.n
                    val atenuado = enfocado && !esActivo
                    val pulso by rememberInfiniteTransition(label = "pg${p.n}").animateFloat(
                        1f, 1.9f, infiniteRepeatable(tween(2400), RepeatMode.Restart), label = "pp${p.n}"
                    )
                    Box(
                        Modifier
                            .offset {
                                IntOffset(
                                    (wPx * p.x / 100f).roundToInt(),
                                    (hPx * p.y / 100f).roundToInt()
                                )
                            }
                            .graphicsLayer {
                                // "this.density" fuerza el Float del GraphicsLayerScope (evita el Density externo)
                                translationX = -14.5f * this.density
                                translationY = -14.5f * this.density
                                val inv = 1f / escala
                                scaleX = inv; scaleY = inv
                            }
                            .alpha(if (atenuado) 0.28f else 1f)
                    ) {
                        // onda de radar
                        if (!enfocado) {
                            Box(
                                Modifier
                                    .size(29.dp)
                                    .graphicsLayer {
                                        scaleX = pulso; scaleY = pulso
                                        alpha = (1.9f - pulso).coerceIn(0f, 0.6f)
                                    }
                                    .border(2.dp, Olimpos.Gold, CircleShape)
                            )
                        }
                        Box(
                            Modifier
                                .size(29.dp)
                                .clip(CircleShape)
                                .background(if (esActivo) Olimpos.GoldLight else Olimpos.Gold)
                                .border(2.dp, Color(0xFFFFF2C8), CircleShape)
                                .clickable { activo = p },
                            contentAlignment = Alignment.Center
                        ) {
                            Text("${p.n}", fontSize = 12.sp, fontWeight = FontWeight.Black, color = Olimpos.Dark)
                        }
                    }
                }
            }

            // Etiqueta del piso
            Box(
                Modifier
                    .padding(12.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(Olimpos.Dark.copy(alpha = 0.85f))
                    .border(1.dp, Olimpos.Line, RoundedCornerShape(10.dp))
                    .padding(horizontal = 13.dp, vertical = 8.dp)
            ) {
                Row {
                    Text("PISO ", fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp, color = Olimpos.Cream)
                    Text("${piso + 1}", fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp, color = Olimpos.GoldLight)
                    Text(" · ${datos.tag}", fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp, color = Olimpos.Cream)
                }
            }

            // Botón vista general
            androidx.compose.animation.AnimatedVisibility(
                visible = enfocado,
                modifier = Modifier
                    .align(Alignment.BottomStart)
                    .padding(12.dp),
                enter = fadeIn(), exit = fadeOut()
            ) {
                Box(
                    Modifier
                        .clip(RoundedCornerShape(100.dp))
                        .background(Olimpos.Dark.copy(alpha = 0.85f))
                        .border(1.dp, Olimpos.Line, RoundedCornerShape(100.dp))
                        .clickable { activo = null }
                        .padding(horizontal = 14.dp, vertical = 9.dp)
                ) {
                    Text(
                        "VISTA GENERAL",
                        fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold,
                        letterSpacing = 1.sp, color = Olimpos.GoldLight
                    )
                }
            }
        }

        // ═══════════ DETALLE + LEYENDA ═══════════
        Column(
            Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(top = 14.dp)
                .navigationBarsPadding()
        ) {
            androidx.compose.animation.AnimatedVisibility(visible = activo != null, enter = fadeIn(), exit = fadeOut()) {
                Column {
                    activo?.let { p ->
                        Column(
                        Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(18.dp))
                            .background(
                                Brush.linearGradient(
                                    listOf(Olimpos.Gold.copy(alpha = 0.13f), Olimpos.Gold.copy(alpha = 0.03f))
                                )
                            )
                            .border(1.dp, Olimpos.Gold.copy(alpha = 0.3f), RoundedCornerShape(18.dp))
                            .padding(16.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                Modifier.size(30.dp).clip(CircleShape).background(Olimpos.Gold),
                                contentAlignment = Alignment.Center
                            ) { Text("${p.n}", fontWeight = FontWeight.Black, fontSize = 13.sp, color = Olimpos.Dark) }
                            Spacer(Modifier.width(11.dp))
                            Text(p.titulo, fontSize = 16.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream)
                        }
                        Spacer(Modifier.height(8.dp))
                        Text(p.desc, fontSize = 12.5.sp, lineHeight = 19.sp, color = Olimpos.Cream.copy(alpha = 0.78f))
                    }
                    Spacer(Modifier.height(14.dp))
                }
                }
            }

            Text(
                "ÁREAS DEL PISO — ${datos.titulo.uppercase()}",
                fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold,
                letterSpacing = 1.6.sp, color = Olimpos.Muted,
                modifier = Modifier.padding(bottom = 9.dp)
            )
            datos.puntos.forEach { p ->
                val on = activo?.n == p.n
                Row(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(13.dp))
                        .background(if (on) Olimpos.GoldSoft else Color.Transparent)
                        .clickable { activo = p }
                        .padding(horizontal = 11.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        Modifier
                            .size(26.dp)
                            .clip(CircleShape)
                            .background(if (on) Olimpos.Gold else Color.Transparent)
                            .border(1.5.dp, if (on) Olimpos.Gold else Olimpos.GoldDark, CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "${p.n}", fontSize = 11.5.sp, fontWeight = FontWeight.ExtraBold,
                            color = if (on) Olimpos.Dark else Olimpos.GoldLight
                        )
                    }
                    Spacer(Modifier.width(12.dp))
                    Text(p.titulo, fontSize = 13.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Cream)
                }
            }
            Spacer(Modifier.height(20.dp))
        }
    }
}
