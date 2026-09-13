package com.olimpos.gym.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.drawscope.translate
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.R
import com.olimpos.gym.data.NivelMuscular
import com.olimpos.gym.data.RangoMuscular
import com.olimpos.gym.data.ZonaMuscular
import com.olimpos.gym.ui.theme.Olimpos

/** Vista del cuerpo a dibujar. */
enum class VistaCuerpo { FRENTE, ESPALDA }

// Dimensiones del viewBox original (ver CuerpoPaths.kt): frente 0..724 / 0..1448,
// espalda originalmente corrida +724 en x — se corrige con un translate al dibujar.
private const val ANCHO_ORIGINAL = 724f
private const val ALTO_ORIGINAL = 1448f
private const val OFFSET_ESPALDA = 724f

/**
 * Ilustración real del cuerpo (frente + espalda), a partir de anatomía de
 * verdad (no formas dibujadas a mano) — ver [CuerpoPaths] para el origen y
 * la licencia de los datos. Cada grupo muscular se colorea según si está en
 * [zonasActivas] o no. Reutilizable entre el Bodygraph y la Galería de
 * ejercicios (como imagen de "músculos trabajados" cuando el ejercicio
 * todavía no tiene foto propia) — un solo dibujo, varios usos.
 */
@Composable
fun CuerpoMuscular(
    zonasActivas: Set<ZonaMuscular>,
    modifier: Modifier = Modifier,
    tamano: Dp = 150.dp
) {
    val colorDeZona: @Composable (ZonaMuscular) -> Color = { zona ->
        if (zona in zonasActivas) Olimpos.Gold else Olimpos.Muted
    }
    Row(modifier, horizontalArrangement = Arrangement.spacedBy(18.dp)) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            SiluetaReal(VistaCuerpo.FRENTE, tamano, colorDeZona)
            Spacer(Modifier.height(6.dp))
            EtiquetaVista("Frente")
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            SiluetaReal(VistaCuerpo.ESPALDA, tamano, colorDeZona)
            Spacer(Modifier.height(6.dp))
            EtiquetaVista("Espalda")
        }
    }
}

/** Variante compacta (solo de frente, sin etiqueta) para usar como miniatura
 *  en tarjetas — por ejemplo, en la Galería de ejercicios. */
@Composable
fun CuerpoMuscularMini(zonasActivas: Set<ZonaMuscular>, modifier: Modifier = Modifier, tamano: Dp = 60.dp) {
    Box(modifier) {
        SiluetaReal(VistaCuerpo.FRENTE, tamano) { zona ->
            if (zona in zonasActivas) Olimpos.Gold else Olimpos.Muted
        }
    }
}

/** Variante del Bodygraph: cada zona se pinta según su [RangoMuscular]
 *  actual (o gris si todavía no hay marcas para esa zona) en vez de un
 *  simple activo/inactivo — así el cuerpo entero se ve como un mosaico de
 *  colores de progreso, no una silueta de un solo tono. */
@Composable
fun CuerpoMuscularRangos(
    rangoPorZona: Map<ZonaMuscular, RangoMuscular?>,
    modifier: Modifier = Modifier,
    tamano: Dp = 150.dp
) {
    val colorDeZona: @Composable (ZonaMuscular) -> Color = { zona ->
        // Sin marcas todavía = un gris claro "sin rango", no el mismo tono
        // apagado que Muted (que se ve sucio/oscuro sobre el fondo).
        rangoPorZona[zona]?.let { colorDeRango(it) } ?: Olimpos.GrayLight
    }
    Row(modifier, horizontalArrangement = Arrangement.spacedBy(18.dp)) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            SiluetaReal(VistaCuerpo.FRENTE, tamano, colorDeZona)
            Spacer(Modifier.height(6.dp))
            EtiquetaVista("Frente")
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            SiluetaReal(VistaCuerpo.ESPALDA, tamano, colorDeZona)
            Spacer(Modifier.height(6.dp))
            EtiquetaVista("Espalda")
        }
    }
}

/** Color fijo por rango — de apagado (Mortal) a brillante (Dios), para que
 *  de un vistazo se note qué tan avanzado está cada músculo. */
fun colorDeRango(rango: RangoMuscular): Color = when (rango) {
    RangoMuscular.MORTAL -> Color(0xFF8A8578)
    RangoMuscular.ESPARTANO -> Color(0xFFB5651D)
    RangoMuscular.HOPLITA -> Color(0xFFC7C9D1)
    RangoMuscular.HEROE -> Color(0xFFD4AF37)
    RangoMuscular.SEMIDIOS -> Color(0xFF45D6C6)
    RangoMuscular.TITAN -> Color(0xFF3D6BE0)
    RangoMuscular.COLOSO -> Color(0xFF9B4FE0)
    RangoMuscular.OLIMPICO -> Color(0xFFE0334F)
    RangoMuscular.DIOS -> Color(0xFFFFF3C4)
}

/** Ícono de bandera/escudo por rango + nivel (arte provisto por el
 *  usuario). Dios tiene un solo nivel, así que usa siempre la misma
 *  imagen (la más decorada de esa fila). */
fun iconoDeRango(nivel: NivelMuscular): Int = when (nivel.rango) {
    RangoMuscular.MORTAL -> when (nivel.nivel) { 1 -> R.drawable.rango_mortal_1; 2 -> R.drawable.rango_mortal_2; else -> R.drawable.rango_mortal_3 }
    RangoMuscular.ESPARTANO -> when (nivel.nivel) { 1 -> R.drawable.rango_espartano_1; 2 -> R.drawable.rango_espartano_2; else -> R.drawable.rango_espartano_3 }
    RangoMuscular.HOPLITA -> when (nivel.nivel) { 1 -> R.drawable.rango_hoplita_1; 2 -> R.drawable.rango_hoplita_2; else -> R.drawable.rango_hoplita_3 }
    RangoMuscular.HEROE -> when (nivel.nivel) { 1 -> R.drawable.rango_heroe_1; 2 -> R.drawable.rango_heroe_2; else -> R.drawable.rango_heroe_3 }
    RangoMuscular.SEMIDIOS -> when (nivel.nivel) { 1 -> R.drawable.rango_semidios_1; 2 -> R.drawable.rango_semidios_2; else -> R.drawable.rango_semidios_3 }
    RangoMuscular.TITAN -> when (nivel.nivel) { 1 -> R.drawable.rango_titan_1; 2 -> R.drawable.rango_titan_2; else -> R.drawable.rango_titan_3 }
    RangoMuscular.COLOSO -> when (nivel.nivel) { 1 -> R.drawable.rango_coloso_1; 2 -> R.drawable.rango_coloso_2; else -> R.drawable.rango_coloso_3 }
    RangoMuscular.OLIMPICO -> when (nivel.nivel) { 1 -> R.drawable.rango_olimpico_1; 2 -> R.drawable.rango_olimpico_2; else -> R.drawable.rango_olimpico_3 }
    RangoMuscular.DIOS -> R.drawable.rango_dios
}

@Composable
private fun EtiquetaVista(texto: String) {
    Text(
        texto.uppercase(), fontSize = 9.5.sp, fontWeight = FontWeight.ExtraBold,
        letterSpacing = 1.2.sp, color = Olimpos.Muted
    )
}

private fun pathDe(d: String): Path = PathParser().parsePathString(d).toPath()

@Composable
private fun SiluetaReal(vista: VistaCuerpo, tamano: Dp, colorDeZona: @Composable (ZonaMuscular) -> Color) {
    // Colores sólidos (no semitransparentes): el pelo, las orejas y otras
    // piezas se superponen a propósito (igual que en el dato original), y
    // con alpha < 1 esa superposición se nota como un parche de otro tono
    // (el "músculo corrido" que se veía cerca de la cabeza).
    // Cabeza, manos y pies no son zonas puntuables — siempre van en gris
    // claro, nunca en el tono oscuro/verdoso de Muted (se veía sucio).
    val colorNeutro = Olimpos.GrayLight
    val colorContorno = Olimpos.Muted.copy(alpha = 0.55f)
    val coloresPorZona = ZonaMuscular.entries.associateWith { colorDeZona(it) }

    // Parsear los paths SVG a Path real de Compose es lo único "pesado" acá;
    // remember evita rehacerlo en cada recomposición de la pantalla.
    val contorno = remember(vista) {
        pathDe(if (vista == VistaCuerpo.FRENTE) CuerpoPaths.contornoFrente else CuerpoPaths.contornoEspalda)
    }
    val neutros = remember(vista) {
        (if (vista == VistaCuerpo.FRENTE) CuerpoPaths.neutroFrente else CuerpoPaths.neutroEspalda).map(::pathDe)
    }
    val zonasPaths = remember(vista) {
        (if (vista == VistaCuerpo.FRENTE) CuerpoPaths.zonasFrente else CuerpoPaths.zonasEspalda)
            .mapValues { (_, ds) -> ds.map(::pathDe) }
    }

    Canvas(Modifier.size(tamano, tamano * (ALTO_ORIGINAL / ANCHO_ORIGINAL))) {
        val factor = size.width / ANCHO_ORIGINAL
        scale(factor, factor, pivot = Offset.Zero) {
            val dibujar: DrawScope.() -> Unit = {
                drawPath(contorno, color = colorContorno, style = androidx.compose.ui.graphics.drawscope.Stroke(width = 2f))
                neutros.forEach { drawPath(it, color = colorNeutro) }
                ZonaMuscular.entries.forEach { zona ->
                    zonasPaths[zona]?.forEach { p ->
                        drawPath(p, color = coloresPorZona[zona] ?: colorNeutro)
                    }
                }
            }
            if (vista == VistaCuerpo.ESPALDA) {
                translate(left = -OFFSET_ESPALDA) { dibujar() }
            } else {
                dibujar()
            }
        }
    }
}
