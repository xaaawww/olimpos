package com.olimpos.gym.ui.screens

import androidx.activity.compose.BackHandler
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.R
import com.olimpos.gym.data.GrupoMuscular
import com.olimpos.gym.data.ZonaMuscular
import com.olimpos.gym.data.socioActualNombre
import com.olimpos.gym.ui.theme.Olimpos

/* ═══════════════════════════════════════════════════════
   Piezas comunes de las secciones de la Arena (Mapa corporal,
   Calculadora, Ejercicios, Logros, Mis marcas), con la paleta
   del mockup: amarillo vivo, fondo crema, tarjetas blancas y
   un color pastel por grupo muscular. En modo oscuro se usan
   las superficies oscuras de OlimpΩs con los mismos acentos.
   ═══════════════════════════════════════════════════════ */

object CA {
    val amarillo = Color(0xFFF6C744)
    /** Texto sobre amarillo (pestaña elegida, botón). */
    val tinta = Color(0xFF1F1F1F)
    val amarilloSuave: Color @Composable get() = if (Olimpos.EsOscuro) Color(0x33F6C744) else Color(0xFFFDF3D3)
    val fondo: Color @Composable get() = if (Olimpos.EsOscuro) Olimpos.FondoA else Color(0xFFFAF8F3)
    val tarjeta: Color @Composable get() = if (Olimpos.EsOscuro) Olimpos.Superficie2 else Color.White
    val borde: Color @Composable get() = if (Olimpos.EsOscuro) Olimpos.Line else Color(0xFFEFEBE2)
    val texto: Color @Composable get() = if (Olimpos.EsOscuro) Olimpos.Cream else Color(0xFF1F1F1F)
    val suave: Color @Composable get() = if (Olimpos.EsOscuro) Olimpos.Muted else Color(0xFF8E8E8E)
    val gris: Color @Composable get() = if (Olimpos.EsOscuro) Color(0x14FFFFFF) else Color(0xFFF2F1EE)
    /** Amarillo legible como texto sobre blanco. */
    val acento: Color @Composable get() = if (Olimpos.EsOscuro) amarillo else Color(0xFF9A7200)
}

/** Color pastel de chip/ícono: fondo suave + texto del mismo tono. */
enum class Pastel(private val fondoClaro: Color, val tono: Color) {
    AMARILLO(Color(0xFFFDF1CC), Color(0xFFA57A00)),
    AZUL(Color(0xFFDDEBFA), Color(0xFF2F6FB5)),
    NARANJA(Color(0xFFFDE7D3), Color(0xFFD2691E)),
    VERDE(Color(0xFFDDF2E3), Color(0xFF2E8B57)),
    TURQUESA(Color(0xFFD8F1EF), Color(0xFF1F8A80)),
    VIOLETA(Color(0xFFECE4FA), Color(0xFF7650C2)),
    ROSA(Color(0xFFFCE2E7), Color(0xFFC9405F)),
    GRIS(Color(0xFFEFEFEF), Color(0xFF777777));

    val fondo: Color @Composable get() = if (Olimpos.EsOscuro) tono.copy(alpha = 0.22f) else fondoClaro
}

fun pastelDeGrupo(grupo: GrupoMuscular): Pastel = when (grupo) {
    GrupoMuscular.PECHO -> Pastel.AMARILLO
    GrupoMuscular.ESPALDA -> Pastel.AZUL
    GrupoMuscular.HOMBROS -> Pastel.NARANJA
    GrupoMuscular.BRAZOS -> Pastel.VERDE
    GrupoMuscular.ABDOMINALES -> Pastel.TURQUESA
    GrupoMuscular.PIERNAS -> Pastel.VIOLETA
}

fun pastelDeZona(zona: ZonaMuscular): Pastel =
    if (zona == ZonaMuscular.GLUTEOS) Pastel.ROSA
    else GrupoMuscular.entries.firstOrNull { zona in it.zonas }?.let(::pastelDeGrupo) ?: Pastel.GRIS

fun pastelDeCategoria(categoria: String): Pastel = when (categoria) {
    "Fuerza" -> Pastel.AZUL
    "Corporal" -> Pastel.ROSA
    else -> Pastel.VERDE
}

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
            Text("OlimpΩs", fontSize = 17.sp, fontWeight = FontWeight.Black, color = CA.texto, modifier = Modifier.weight(1f))
            Box(
                Modifier.size(32.dp).clip(CircleShape).background(CA.amarillo),
                contentAlignment = Alignment.Center
            ) {
                Text(socioActualNombre().take(1).uppercase().ifEmpty { "?" }, fontWeight = FontWeight.Black, fontSize = 13.sp, color = CA.tinta)
            }
        }
        Spacer(Modifier.height(16.dp))
        Row(verticalAlignment = Alignment.Top) {
            Box(
                Modifier
                    .padding(top = 1.dp)
                    .size(32.dp)
                    .clip(CircleShape)
                    .clickable(
                        interactionSource = remember { MutableInteractionSource() },
                        indication = null,
                        onClick = onVolver
                    ),
                contentAlignment = Alignment.CenterStart
            ) { Text("←", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = CA.texto) }
            Spacer(Modifier.width(8.dp))
            Column(Modifier.weight(1f)) {
                Text(titulo, fontSize = 22.sp, lineHeight = 26.sp, fontWeight = FontWeight.Black, color = CA.texto)
                Text(subtitulo, fontSize = 12.5.sp, color = CA.suave, lineHeight = 16.sp)
            }
            if (derecha != null) {
                Spacer(Modifier.width(8.dp))
                derecha()
            }
        }
    }
}

/** Pestañas tipo píldora de ancho parejo: la elegida en amarillo lleno. */
@Composable
fun PestanasPildora(opciones: List<String>, elegida: Int, onElegir: (Int) -> Unit, modifier: Modifier = Modifier) {
    Row(modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        opciones.forEachIndexed { i, texto ->
            val activa = i == elegida
            Box(
                Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(12.dp))
                    .background(if (activa) CA.amarillo else CA.tarjeta)
                    .border(1.dp, if (activa) CA.amarillo else CA.borde, RoundedCornerShape(12.dp))
                    .clickable { onElegir(i) }
                    .padding(vertical = 11.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    texto, fontSize = 12.5.sp, maxLines = 1, textAlign = TextAlign.Center,
                    fontWeight = if (activa) FontWeight.ExtraBold else FontWeight.SemiBold,
                    color = if (activa) CA.tinta else CA.texto
                )
            }
        }
    }
}

/** Chip de filtro (redondo): el elegido en amarillo. */
@Composable
fun ChipArena(texto: String, elegido: Boolean, onClick: () -> Unit) {
    Box(
        Modifier
            .clip(RoundedCornerShape(100.dp))
            .background(if (elegido) CA.amarillo else CA.tarjeta)
            .border(1.dp, if (elegido) CA.amarillo else CA.borde, RoundedCornerShape(100.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 15.dp, vertical = 9.dp)
    ) {
        Text(
            texto, fontSize = 12.5.sp, fontWeight = if (elegido) FontWeight.ExtraBold else FontWeight.SemiBold,
            color = if (elegido) CA.tinta else CA.texto
        )
    }
}

/** Tarjeta blanca de las secciones de la Arena. */
@Composable
fun TarjetaLisa(
    modifier: Modifier = Modifier,
    padding: Dp = 14.dp,
    contenido: @Composable ColumnScope.() -> Unit
) {
    Column(
        modifier
            .clip(RoundedCornerShape(16.dp))
            .background(CA.tarjeta)
            .border(1.dp, CA.borde, RoundedCornerShape(16.dp))
            .padding(padding),
        content = contenido
    )
}

/** Chip chico de texto en un color pastel (músculo, categoría, nivel). */
@Composable
fun ChipSuave(texto: String, pastel: Pastel = Pastel.AMARILLO) {
    Box(
        Modifier
            .clip(RoundedCornerShape(8.dp))
            .background(pastel.fondo)
            .padding(horizontal = 9.dp, vertical = 4.dp)
    ) {
        Text(texto, fontSize = 10.5.sp, fontWeight = FontWeight.Bold, maxLines = 1, color = pastel.tono)
    }
}

/** Barra de progreso amarilla sobre un riel gris claro. */
@Composable
fun BarraArena(fraccion: Float, modifier: Modifier = Modifier, alto: Dp = 6.dp) {
    val frac by animateFloatAsState(fraccion.coerceIn(0f, 1f), tween(700), label = "barra")
    Box(modifier.fillMaxWidth().height(alto).clip(RoundedCornerShape(100.dp)).background(CA.gris)) {
        Box(Modifier.fillMaxWidth(frac).height(alto).clip(RoundedCornerShape(100.dp)).background(CA.amarillo))
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
            .background(if (dibujo != null) Color(0xFFF7F6F2) else CA.amarilloSuave),
        contentAlignment = Alignment.Center
    ) {
        if (dibujo != null) {
            Image(painterResource(dibujo), contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.size(tamano))
        } else {
            CuerpoMuscularMini(zonasActivas = zonas, tamano = tamano * 0.42f)
        }
    }
}

/** Ícono redondo de color pastel con un emoji — los íconos de las filas. */
@Composable
fun IconoRedondo(emoji: String, tamano: Dp = 40.dp, pastel: Pastel = Pastel.AMARILLO, apagado: Boolean = false) {
    Box(
        Modifier
            .size(tamano)
            .clip(CircleShape)
            .background(if (apagado) CA.gris else pastel.fondo),
        contentAlignment = Alignment.Center
    ) { Text(emoji, fontSize = (tamano.value * 0.45f).sp) }
}

@Composable
fun Chevron() {
    Text("›", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = CA.suave)
}
