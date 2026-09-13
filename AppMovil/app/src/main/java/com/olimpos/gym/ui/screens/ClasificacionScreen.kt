package com.olimpos.gym.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import androidx.compose.runtime.rememberCoroutineScope
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DESCRIPCION_RANGO
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.MINIMO_EJERCICIOS_PARA_CLASIFICACION
import com.olimpos.gym.data.NivelMuscular
import com.olimpos.gym.data.RangoMuscular
import com.olimpos.gym.data.SexoBiologico
import com.olimpos.gym.data.SocioRango
import com.olimpos.gym.data.actualizarOcultoClasificacion
import com.olimpos.gym.data.cantidadEjerciciosVigentes
import com.olimpos.gym.data.formatearAntiguedad
import com.olimpos.gym.data.nivelDesdePuntaje
import com.olimpos.gym.data.puntajeGeneralDeSocio
import com.olimpos.gym.data.socioActualId
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

/** Clasificación: la Escalera del Olimpo — los 25 niveles del Bodygraph
 *  desde Mortal (al pie) hasta Dios (en la cima). Los estandartes flotan
 *  centrados sobre la montaña, sin nombre a la vista — tocar uno lo
 *  despliega con su título, descripción y un botón para ver a todos los
 *  socios de ese rango exacto en otra pantalla (con muchos socios usando
 *  la app a la vez, listarlos ahí adentro es mucho más cómodo que una
 *  lista larga metida en el medio de la montaña). También hay un buscador
 *  por nombre arriba de todo, para encontrar a alguien sin tener que bajar
 *  escalón por escalón. */
@Composable
fun ClasificacionScreen(onVolver: () -> Unit) {
    val rangosSocios = DatosRemotos.rangosSocios ?: emptyList()
    var nivelMiembros by remember { mutableStateOf<NivelMuscular?>(null) }
    var perfilSeleccionado by remember { mutableStateOf<SocioRango?>(null) }

    Box(Modifier.fillMaxSize()) {
        val nivelActivo = nivelMiembros
        if (nivelActivo != null) {
            MiembrosRangoScreen(
                nivel = nivelActivo,
                socios = remember(rangosSocios, nivelActivo) {
                    rangosSocios.filter { it.nivel == nivelActivo && it.verificado }
                        .sortedByDescending { it.kgTotales }
                },
                onVolver = { nivelMiembros = null },
                onSeleccionar = { perfilSeleccionado = it }
            )
        } else {
            Column(Modifier.fillMaxSize()) {
                EncabezadoVolver("Clasificación", "La Escalera del Olimpo: quién llegó a cada rango", onVolver)
                Column(
                    Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(horizontal = 20.dp)
                        .padding(bottom = 26.dp)
                ) {
                    ToggleVisibilidadPropia()
                    BuscadorSocios(rangosSocios, onSeleccionar = { perfilSeleccionado = it })
                    EscaleraDelOlimpo(onVerMiembros = { nivelMiembros = it })
                }
            }
        }

        AnimatedVisibility(visible = perfilSeleccionado != null, enter = fadeIn(), exit = fadeOut()) {
            perfilSeleccionado?.let { DetallePerfilSocio(it, onCerrar = { perfilSeleccionado = null }) }
        }
    }
}

/** Botón para que un socio deje de aparecer para los DEMÁS en la Escalera
 *  del Olimpo (búsqueda, listas de miembros, conteo por rango) — sigue
 *  viendo su propio rango normalmente, ese cálculo no depende de esta
 *  lista compartida. Algunos socios prefieren no exponer su posición. */
@Composable
private fun ToggleVisibilidadPropia() {
    val datosFisicos = DatosRemotos.datosFisicosPropios
    var oculto by remember(datosFisicos) { mutableStateOf(datosFisicos?.ocultoClasificacion ?: false) }
    val scope = rememberCoroutineScope()

    TarjetaOro(Modifier.fillMaxWidth().padding(bottom = 16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconoCuadrado(if (oculto) "🙈" else "🏆")
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text("Mostrarme en la Escalera del Olimpo", fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                Text(
                    if (oculto) "Oculto: nadie más te ve en la búsqueda ni en las listas de miembros."
                    else "Otros socios pueden verte en la búsqueda y en la lista de tu rango.",
                    fontSize = 11.sp, color = Olimpos.Muted
                )
            }
            Switch(
                checked = !oculto,
                onCheckedChange = { visible ->
                    oculto = !visible
                    scope.launch {
                        actualizarOcultoClasificacion(!visible)
                        DatosRemotos.recargarDatosFisicosPropios()
                        DatosRemotos.recargarRangosSocios()
                    }
                },
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
}

/** Buscador por nombre: no navega solo — muestra hasta 8 coincidencias con
 *  su rango, y tocar una abre directo el mismo detalle de perfil que se ve
 *  desde la lista de miembros de un rango (no hace falta pasar por ahí). */
@Composable
private fun BuscadorSocios(rangosSocios: List<SocioRango>, onSeleccionar: (SocioRango) -> Unit) {
    var busqueda by remember { mutableStateOf("") }

    Column(Modifier.padding(bottom = 16.dp)) {
        CampoBusqueda(busqueda, { busqueda = it }, "Buscar a un socio por nombre…")

        if (busqueda.isNotBlank()) {
            val resultados = remember(busqueda, rangosSocios) {
                rangosSocios.filter { it.nombre.contains(busqueda, ignoreCase = true) }
                    .sortedBy { it.nombre }
                    .take(8)
            }
            Spacer(Modifier.height(8.dp))
            if (resultados.isEmpty()) {
                Text(
                    "Nadie con ese nombre todavía.",
                    fontSize = 12.sp, color = Olimpos.Muted, modifier = Modifier.padding(vertical = 4.dp)
                )
            } else {
                Column(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(14.dp))
                        .background(Olimpos.Card)
                        .border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp))
                ) {
                    resultados.forEachIndexed { i, s ->
                        Row(
                            Modifier
                                .fillMaxWidth()
                                .clickable { onSeleccionar(s) }
                                .padding(horizontal = 14.dp, vertical = 11.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(Modifier.weight(1f)) {
                                Text(s.nombre, fontSize = 13.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Cream)
                                Text(s.nivel.etiquetaCompleta, fontSize = 11.sp, color = Olimpos.Gold)
                            }
                            Text("→", color = Olimpos.Muted, fontWeight = FontWeight.Black)
                        }
                        if (i < resultados.lastIndex) {
                            Box(Modifier.fillMaxWidth().height(1.dp).background(Olimpos.Line))
                        }
                    }
                }
            }
        }
    }
}

/* ── Escalera del Olimpo: los 25 niveles del Bodygraph (ver
   RangoMuscular/NivelMuscular en GamificacionData.kt), de Mortal al pie de
   la montaña a Dios en la cima — mismos estandartes que ya se usan en el
   Bodygraph, sin personas ni fotos dibujadas (la gente aparece en la
   pantalla de miembros, al tocar "ver miembros" de un escalón). ── */
private val ALTO_ESCALON = 108.dp

@Composable
private fun EscaleraDelOlimpo(onVerMiembros: (NivelMuscular) -> Unit) {
    // Precargado desde que se entró a la app (ver DatosRemotos/MainActivity).
    // Sin datos de ejemplo de respaldo a propósito: un socio nuevo debe
    // empezar en cero, no ver marcas que nunca cargó.
    val marcas = DatosRemotos.marcas ?: emptyList()
    val rangosSocios = DatosRemotos.rangosSocios ?: emptyList()
    val datosFisicos = DatosRemotos.datosFisicosPropios
    val pesoCorporal = datosFisicos?.pesoKg ?: 80f
    val rangoActual = remember(marcas, datosFisicos) {
        puntajeGeneralDeSocio(marcas, pesoCorporal, datosFisicos?.sexo)?.let { nivelDesdePuntaje(it) }
    }
    val ejerciciosRegistrados = remember(marcas) { cantidadEjerciciosVigentes(marcas) }
    val escalones = remember {
        RangoMuscular.entries.reversed().flatMap { rango -> (rango.nivelesMax downTo 1).map { NivelMuscular(rango, it) } }
    }
    var expandido by remember { mutableStateOf<NivelMuscular?>(null) }

    Text(
        "La Escalera del Olimpo", fontSize = 18.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream,
        modifier = Modifier.padding(top = 4.dp, bottom = 2.dp)
    )
    Text(
        "De Mortal, al pie de la montaña, a Dios en la cima. Tocá un escalón para ver quién llegó ahí.",
        fontSize = 12.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 14.dp)
    )

    if (rangoActual == null) {
        val faltan = (MINIMO_EJERCICIOS_PARA_CLASIFICACION - ejerciciosRegistrados).coerceAtLeast(0)
        Box(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp))
                .background(Olimpos.Card)
                .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
                .padding(14.dp)
        ) {
            Text(
                if (faltan > 0)
                    "Todavía no aparecés en la Escalera del Olimpo: cargá marcas en $faltan ejercicio${if (faltan == 1) "" else "s"} más de la Calculadora (mínimo $MINIMO_EJERCICIOS_PARA_CLASIFICACION en total) para entrar al ranking."
                else
                    "Todavía no aparecés en la Escalera del Olimpo: te faltan datos personales (peso) para calcular tu rango.",
                fontSize = 12.sp, color = Olimpos.Muted
            )
        }
        Spacer(Modifier.height(16.dp))
    }

    Box(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(24.dp))
            .background(Brush.verticalGradient(listOf(Olimpos.FondoC, Olimpos.FondoB, Olimpos.FondoA)))
            .montanaFondo()
    ) {
        Column {
            escalones.forEach { esc ->
                val cantidad = remember(rangosSocios, esc) {
                    rangosSocios.count { it.nivel == esc && it.verificado }
                }
                FilaEscalon(
                    nivel = esc,
                    esActual = esc == rangoActual,
                    cantidadEnRango = cantidad,
                    expandido = expandido == esc,
                    onToggle = { expandido = if (expandido == esc) null else esc },
                    onVerMiembros = { onVerMiembros(esc) }
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
    cantidadEnRango: Int,
    expandido: Boolean,
    onToggle: () -> Unit,
    onVerMiembros: () -> Unit
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
        AnimatedVisibility(visible = expandido) {
            DetalleEscalon(nivel, esActual, cantidadEnRango, onVerMiembros)
        }
    }
}

@Composable
private fun DetalleEscalon(nivel: NivelMuscular, esActual: Boolean, cantidadEnRango: Int, onVerMiembros: () -> Unit) {
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
        Spacer(Modifier.height(14.dp))
        if (cantidadEnRango > 0) {
            BotonSecundario("Ver ${if (cantidadEnRango == 1) "el socio" else "los $cantidadEnRango socios"} en este rango") {
                onVerMiembros()
            }
        } else {
            Text(
                "Todavía nadie llegó a este rango (verificado).",
                fontSize = 11.5.sp, color = Olimpos.Muted
            )
        }
        Spacer(Modifier.height(10.dp))
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

/* ── Pantalla de miembros de un rango: se abre desde el botón "Ver
   miembros" de un escalón, o desde el buscador de arriba. Lista completa
   (te incluye a vos, marcado "Vos") en vez de un preview corto — pensada
   para rangos con muchos socios adentro. ── */
@Composable
private fun MiembrosRangoScreen(
    nivel: NivelMuscular,
    socios: List<SocioRango>,
    onVolver: () -> Unit,
    onSeleccionar: (SocioRango) -> Unit
) {
    val desc = DESCRIPCION_RANGO[nivel]
    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver(
            nivel.etiquetaCompleta,
            desc?.apodo?.let { "$it · ${socios.size} en el club" } ?: "${socios.size} en el club",
            onVolver
        )
        if (socios.isEmpty()) {
            Column(
                Modifier.fillMaxSize().padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Spacer(Modifier.height(50.dp))
                Text(
                    "Todavía nadie llegó a este rango.",
                    fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Olimpos.Cream
                )
            }
        } else {
            LazyColumn(
                Modifier.fillMaxSize(),
                contentPadding = PaddingValues(horizontal = 20.dp, vertical = 14.dp),
                verticalArrangement = Arrangement.spacedBy(9.dp)
            ) {
                items(socios, key = { it.socioId }) { s ->
                    FilaMiembro(s, esYo = s.socioId == socioActualId()) { onSeleccionar(s) }
                }
            }
        }
    }
}

@Composable
private fun FilaMiembro(socio: SocioRango, esYo: Boolean, onClick: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Olimpos.Card)
            .border(1.dp, if (esYo) Olimpos.Gold.copy(alpha = 0.5f) else Olimpos.Line, RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 15.dp, vertical = 13.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(socio.nombre, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream)
                if (esYo) {
                    Spacer(Modifier.width(6.dp))
                    ChipOro("Vos")
                }
            }
            Text(
                "${socio.kgTotales.toInt()} kg totales · ${formatearAntiguedad(socio.creadoMs)}",
                fontSize = 11.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 2.dp)
            )
        }
        Text("→", color = Olimpos.Gold, fontWeight = FontWeight.Black)
    }
}

/** Detalle de un perfil: nombre como título grande, datos personales (los
 *  rangos se calculan contra el peso de cada uno, así que se muestran acá),
 *  la frase de cuántas veces su peso levanta y un recuadro al costado
 *  reservado para su Bodygraph personal — todavía no se puede ver el de
 *  otro socio (hoy el Bodygraph solo calcula el propio a partir de las
 *  marcas ya precargadas), así que por ahora queda como adelanto. Se abre
 *  tanto desde la lista de miembros de un rango como directo desde el
 *  buscador. */
@Composable
private fun DetallePerfilSocio(socio: SocioRango, onCerrar: () -> Unit) {
    Box(
        Modifier
            .fillMaxSize()
            .background(Olimpos.Dark.copy(alpha = 0.72f))
            .clickable(onClick = onCerrar),
        contentAlignment = Alignment.Center
    ) {
        Column(
            Modifier
                .padding(horizontal = 30.dp)
                .clip(RoundedCornerShape(24.dp))
                .background(Olimpos.Card)
                .border(1.dp, Olimpos.Gold.copy(alpha = 0.4f), RoundedCornerShape(24.dp))
                .clickable(enabled = false) {}
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Image(
                painter = painterResource(iconoDeRango(socio.nivel)),
                contentDescription = socio.nivel.etiquetaCompleta,
                modifier = Modifier.size(60.dp)
            )
            Spacer(Modifier.height(12.dp))
            Text(
                socio.nombre, fontSize = 18.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream,
                textAlign = TextAlign.Center
            )
            Spacer(Modifier.height(8.dp))
            ChipOro(socio.nivel.etiquetaCompleta)

            Spacer(Modifier.height(10.dp))
            Text(
                listOfNotNull(
                    "${socio.pesoKg.toInt()} kg",
                    socio.edad?.let { "$it años" },
                    socio.sexo?.takeIf { it != SexoBiologico.PREFIERO_NO_DECIRLO }?.etiqueta
                ).joinToString(" · "),
                fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Gold
            )

            Spacer(Modifier.height(14.dp))
            Row(verticalAlignment = Alignment.Top, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                Column(Modifier.weight(1f)) {
                    Text(
                        buildString {
                            socio.mejorLevantamiento?.let { m ->
                                append("${socio.nombre} levanta ${"%.1f".format(m.vecesPesoCorporal)} veces su peso corporal (en ${m.ejercicio}). ")
                            }
                            append("Lleva un total estimado de ${socio.kgTotales.toInt()} kg levantados en sus marcas")
                            append(if (socio.verificado) " verificadas" else " (todavía sin verificar)")
                            append(", y forma parte de OlimpΩs desde hace ")
                            append(formatearAntiguedad(socio.creadoMs).removePrefix("Socio hace ").removePrefix("Se unió "))
                            append(".")
                        },
                        fontSize = 12.5.sp, color = Olimpos.Muted
                    )
                }
                // Recuadro reservado para el Bodygraph personal de este socio
                // — el detalle por músculo llega en una próxima entrega.
                Column(
                    Modifier
                        .size(64.dp)
                        .clip(RoundedCornerShape(14.dp))
                        .background(Olimpos.Superficie2)
                        .border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp))
                        .padding(6.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Text("🫁", fontSize = 18.sp)
                    Text(
                        "Bodygraph\npróx.", fontSize = 8.sp, color = Olimpos.Muted,
                        textAlign = TextAlign.Center, lineHeight = 9.sp
                    )
                }
            }
        }
    }
}
