package com.olimpos.gym.ui.screens

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DESCRIPCION_RANGO
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.EVOLUCION_PESO
import com.olimpos.gym.data.MIS_MARCAS
import com.olimpos.gym.data.NivelMuscular
import com.olimpos.gym.data.RangoMuscular
import com.olimpos.gym.data.socioActualId
import com.olimpos.gym.data.SocioRango
import com.olimpos.gym.data.ZonaMuscular
import com.olimpos.gym.data.nivelDesdePuntaje
import com.olimpos.gym.data.resumenMuscular
import com.olimpos.gym.ui.theme.Olimpos

/** Clasificación: la Escalera del Olimpo — los 25 niveles del Bodygraph
 *  desde Mortal (al pie) hasta Dios (en la cima). Los estandartes flotan
 *  centrados sobre la montaña, sin nombre a la vista — tocar uno lo
 *  despliega con su nombre, su mini-descripción y quién más del club
 *  (solo verificados) llegó a ese rango exacto. */
@Composable
fun ClasificacionScreen(onVolver: () -> Unit) {
    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver("Clasificación", "La Escalera del Olimpo: quién llegó a cada rango", onVolver)
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(bottom = 26.dp)
        ) {
            EscaleraDelOlimpo()
        }
    }
}

/* ── Escalera del Olimpo: los 25 niveles del Bodygraph (ver
   RangoMuscular/NivelMuscular en GamificacionData.kt), de Mortal al pie de
   la montaña a Dios en la cima — mismos estandartes que ya se usan en el
   Bodygraph, sin personas ni fotos dibujadas (la gente aparece como lista
   de texto al tocar un escalón). ── */
private val ALTO_ESCALON = 108.dp

@Composable
private fun EscaleraDelOlimpo() {
    // Precargado desde que se entró a la app (ver DatosRemotos/MainActivity).
    val marcas = DatosRemotos.marcas?.takeIf { it.isNotEmpty() } ?: MIS_MARCAS
    val rangosSocios = DatosRemotos.rangosSocios ?: emptyList()
    val pesoCorporal = EVOLUCION_PESO.lastOrNull()?.valor ?: 80f
    val rangoActual = remember(marcas) {
        val resumen = resumenMuscular(marcas, pesoCorporal)
        if (!resumen.tieneMarcas) null else {
            val promedio = ZonaMuscular.entries.sumOf { (resumen.puntajes[it] ?: 0f).toDouble() } / ZonaMuscular.entries.size
            nivelDesdePuntaje(promedio.toFloat())
        }
    }
    val escalones = remember {
        RangoMuscular.entries.reversed().flatMap { rango -> (rango.nivelesMax downTo 1).map { NivelMuscular(rango, it) } }
    }
    var expandido by remember { mutableStateOf<NivelMuscular?>(null) }

    Text(
        "La Escalera del Olimpo", fontSize = 18.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream,
        modifier = Modifier.padding(top = 4.dp, bottom = 2.dp)
    )
    Text(
        "De Mortal, al pie de la montaña, a Dios en la cima. Tocá un escalón para ver quién más del club llegó ahí.",
        fontSize = 12.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 14.dp)
    )

    Box(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(24.dp))
            .background(Brush.verticalGradient(listOf(Olimpos.FondoC, Olimpos.FondoB, Olimpos.FondoA)))
            .montanaFondo()
    ) {
        Column {
            escalones.forEach { esc ->
                val otros = remember(rangosSocios, esc) {
                    rangosSocios.filter { it.nivel == esc && it.verificado && it.socioId != socioActualId() }
                }
                FilaEscalon(
                    nivel = esc,
                    esActual = esc == rangoActual,
                    otrosSocios = otros,
                    expandido = expandido == esc,
                    onToggle = { expandido = if (expandido == esc) null else esc }
                )
            }
        }
    }
}

/** Silueta de una cadena montañosa lejana: una lista de (fracción de ancho,
 *  fracción de alto) que arranca y termina en la base (fy=1) para rellenarse
 *  contra el piso del fondo. */
private fun crestaContraBase(size: androidx.compose.ui.geometry.Size, puntos: List<Pair<Float, Float>>): Path {
    val w = size.width
    val h = size.height
    return Path().apply {
        moveTo(w * puntos.first().first, h)
        puntos.forEach { (fx, fy) -> lineTo(w * fx, h * fy) }
        lineTo(w * puntos.last().first, h)
        close()
    }
}

/** Polígono que se cierra contra su propio primer punto (para el pico
 *  central y la nieve de la cumbre, que no llegan hasta la base). */
private fun poligonoCerrado(size: androidx.compose.ui.geometry.Size, puntos: List<Pair<Float, Float>>): Path {
    val w = size.width
    val h = size.height
    return Path().apply {
        moveTo(w * puntos.first().first, h * puntos.first().second)
        puntos.drop(1).forEach { (fx, fy) -> lineTo(w * fx, h * fy) }
        close()
    }
}

/** Ladera izquierda del pico central (rocosa, con jags hacia afuera) — la
 *  ladera derecha es su espejo, así el pico queda simétrico y sin que sus
 *  bordes se crucen entre sí. */
private val LADERA_IZQUIERDA = listOf(
    0.05f to 1f, 0.13f to 0.87f, 0.10f to 0.80f, 0.19f to 0.68f, 0.16f to 0.60f,
    0.25f to 0.49f, 0.22f to 0.41f, 0.31f to 0.29f, 0.28f to 0.22f, 0.39f to 0.10f,
    0.5f to 0f
)
private val PICO_CENTRAL = LADERA_IZQUIERDA + LADERA_IZQUIERDA.dropLast(1).reversed().map { (fx, fy) -> 1f - fx to fy }

private val NUBE_REDONDEADA = listOf(0f to 1f, -0.7f to 0.55f, 0.75f to 0.6f, -1.3f to 0.8f, 1.35f to 0.85f)
private val NUBE_ALARGADA = listOf(0f to 1f, -1.1f to 0.7f, 1.15f to 0.72f, -1.9f to 0.9f, 1.95f to 0.92f)

private fun androidx.compose.ui.graphics.drawscope.DrawScope.dibujarNube(
    cx: Float, cy: Float, radioBase: Float, alpha: Float,
    forma: List<Pair<Float, Float>> = NUBE_REDONDEADA
) {
    forma.forEach { (dfx, dfr) ->
        drawCircle(
            brush = Brush.radialGradient(
                listOf(Olimpos.Cream.copy(alpha = alpha), Olimpos.Cream.copy(alpha = 0f)),
                center = androidx.compose.ui.geometry.Offset(cx + dfx * radioBase, cy),
                radius = radioBase * dfr * 1.4f
            ),
            radius = radioBase * dfr,
            center = androidx.compose.ui.geometry.Offset(cx + dfx * radioBase, cy)
        )
    }
}

/** Fondo de "El Olimpo": cadenas montañosas lejanas (jalonadas, con poca
 *  opacidad para dar profundidad), un pico central que va de ancho en la
 *  base (Mortal) a angosto en la cima (Dios), una capa de nieve en la
 *  cumbre y nubes flotando a distintas alturas — todo dibujado, sin
 *  fotos ni personas, como pidió el usuario. */
private fun Modifier.montanaFondo(): Modifier = this.drawBehind {
    val w = size.width
    val h = size.height

    // Cadenas lejanas, alturas irregulares (no parejas, para que no se vean
    // como una sierra de dientes sino como montañas distintas de fondo).
    drawPath(
        crestaContraBase(size, listOf(
            0f to 0.75f, 0.1f to 0.55f, 0.22f to 0.68f, 0.36f to 0.42f, 0.5f to 0.6f,
            0.64f to 0.5f, 0.78f to 0.66f, 0.9f to 0.48f, 1f to 0.7f
        )),
        color = Olimpos.Gold.copy(alpha = 0.04f)
    )
    drawPath(
        crestaContraBase(size, listOf(
            0f to 0.85f, 0.14f to 0.62f, 0.28f to 0.78f, 0.42f to 0.56f, 0.55f to 0.72f,
            0.7f to 0.58f, 0.85f to 0.74f, 1f to 0.6f
        )),
        color = Olimpos.Gold.copy(alpha = 0.07f)
    )
    // Pico central: rocoso y ancho en la base (Mortal), filoso en la cumbre (Dios)
    drawPath(
        poligonoCerrado(size, PICO_CENTRAL),
        brush = Brush.verticalGradient(
            listOf(Olimpos.GoldLight.copy(alpha = 0.2f), Olimpos.Gold.copy(alpha = 0.03f)),
            startY = 0f, endY = h * 0.5f
        )
    )
    // Nieve brillando en la cumbre
    drawPath(
        poligonoCerrado(size, listOf(
            0.42f to 0.12f, 0.46f to 0.055f, 0.5f to 0f, 0.54f to 0.055f, 0.58f to 0.12f,
            0.5f to 0.045f
        )),
        color = Olimpos.GoldLight.copy(alpha = 0.28f)
    )

    // Nubes a la izquierda del pico
    dibujarNube(w * 0.16f, h * 0.2f, w * 0.14f, 0.12f)
    dibujarNube(w * 0.22f, h * 0.5f, w * 0.15f, 0.09f, NUBE_ALARGADA)
    dibujarNube(w * 0.14f, h * 0.8f, w * 0.16f, 0.07f)

    // Nubes a la derecha del pico — varias, a distintas alturas y formas,
    // para que ese lado no quede vacío ahora que el estandarte va centrado.
    dibujarNube(w * 0.85f, h * 0.12f, w * 0.1f, 0.09f, NUBE_ALARGADA)
    dibujarNube(w * 0.88f, h * 0.3f, w * 0.11f, 0.1f)
    dibujarNube(w * 0.82f, h * 0.46f, w * 0.13f, 0.08f, NUBE_ALARGADA)
    dibujarNube(w * 0.87f, h * 0.64f, w * 0.12f, 0.09f)
    dibujarNube(w * 0.83f, h * 0.8f, w * 0.15f, 0.07f, NUBE_ALARGADA)
    dibujarNube(w * 0.9f, h * 0.94f, w * 0.1f, 0.06f)
}

@Composable
private fun FilaEscalon(
    nivel: NivelMuscular,
    esActual: Boolean,
    otrosSocios: List<SocioRango>,
    expandido: Boolean,
    onToggle: () -> Unit
) {
    Column {
        Box(
            Modifier
                .fillMaxWidth()
                .height(ALTO_ESCALON)
                .clickable(onClick = onToggle),
            contentAlignment = Alignment.Center
        ) {
            if (esActual) IconoConBrillo(nivel) else {
                Image(
                    painter = painterResource(iconoDeRango(nivel)),
                    contentDescription = nivel.etiquetaCompleta,
                    modifier = Modifier.size(50.dp)
                )
            }
        }
        androidx.compose.animation.AnimatedVisibility(visible = expandido) {
            DetalleEscalon(nivel, esActual, otrosSocios)
        }
    }
}

@Composable
private fun DetalleEscalon(nivel: NivelMuscular, esActual: Boolean, otrosSocios: List<SocioRango>) {
    val desc = DESCRIPCION_RANGO[nivel]
    Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 6.dp)) {
        if (esActual) {
            Text(
                "TU RANGO ACTUAL", fontSize = 9.sp, fontWeight = FontWeight.ExtraBold,
                letterSpacing = 1.sp, color = Olimpos.Gold
            )
            Spacer(Modifier.height(2.dp))
        }
        Text(
            nivel.etiquetaCompleta.uppercase(), fontSize = 16.sp, fontWeight = FontWeight.Black,
            color = if (esActual) Olimpos.GoldLight else Olimpos.Cream
        )
        if (desc != null) {
            Text(
                desc.apodo, fontSize = 12.5.sp, fontWeight = FontWeight.Bold,
                color = Olimpos.Gold, modifier = Modifier.padding(top = 2.dp)
            )
            Text(
                desc.texto, fontSize = 12.sp, color = Olimpos.Cream.copy(alpha = 0.78f),
                modifier = Modifier.padding(top = 6.dp)
            )
        }
        Spacer(Modifier.height(12.dp))
        ListaSociosDeRango(otrosSocios)
    }
}

/** Ícono del rango actual del socio: halo dorado grande + anillo de borde
 *  + un pulso de escala, para que salte a la vista entre los demás
 *  escalones apagados de la montaña sin necesidad de leer el texto. */
@Composable
private fun IconoConBrillo(nivel: NivelMuscular) {
    val transition = rememberInfiniteTransition(label = "brillo")
    val pulso by transition.animateFloat(
        initialValue = 0.45f, targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(900), RepeatMode.Reverse),
        label = "pulso"
    )
    val escala by transition.animateFloat(
        initialValue = 1f, targetValue = 1.08f,
        animationSpec = infiniteRepeatable(tween(900), RepeatMode.Reverse),
        label = "escala"
    )
    Box(contentAlignment = Alignment.Center) {
        // Halo amplio y difuso: da el "brillo" desde lejos
        Box(
            Modifier
                .size(150.dp)
                .clip(CircleShape)
                .background(Brush.radialGradient(listOf(Olimpos.GoldLight.copy(alpha = pulso * 0.55f), Olimpos.Gold.copy(alpha = 0f))))
        )
        // Núcleo más chico y más intenso, para que el centro no se vea lavado
        Box(
            Modifier
                .size(92.dp)
                .clip(CircleShape)
                .background(Brush.radialGradient(listOf(Olimpos.GoldLight.copy(alpha = pulso), Olimpos.Gold.copy(alpha = pulso * 0.35f), Olimpos.Gold.copy(alpha = 0f))))
        )
        // Anillo definido: marca el contorno incluso cuando el pulso está bajo
        Box(
            Modifier
                .size(74.dp)
                .clip(CircleShape)
                .border(2.5.dp, Olimpos.GoldLight.copy(alpha = 0.4f + pulso * 0.6f), CircleShape)
        )
        Image(
            painter = painterResource(iconoDeRango(nivel)),
            contentDescription = nivel.etiquetaCompleta,
            modifier = Modifier
                .size(64.dp)
                .graphicsLayer(scaleX = escala, scaleY = escala)
        )
    }
}

@Composable
private fun ListaSociosDeRango(socios: List<SocioRango>) {
    Column(Modifier.fillMaxWidth().padding(bottom = 14.dp)) {
        if (socios.isEmpty()) {
            Text(
                "Todavía nadie más del club llegó a este rango (verificado).",
                fontSize = 11.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(vertical = 8.dp)
            )
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                socios.forEach { s ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(Olimpos.Card)
                            .border(1.dp, Olimpos.Line, RoundedCornerShape(12.dp))
                            .padding(horizontal = 12.dp, vertical = 9.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("✓", color = Olimpos.Green, fontWeight = FontWeight.Black, fontSize = 12.sp)
                        Spacer(Modifier.width(8.dp))
                        Text(s.nombre, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Olimpos.Cream)
                    }
                }
            }
        }
    }
}
