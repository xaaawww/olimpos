package com.olimpos.gym.ui.screens

import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.Ingrediente
import com.olimpos.gym.data.MomentoComida
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.data.PLATOS
import com.olimpos.gym.data.Plato
import com.olimpos.gym.data.marcarPlatoProbadoEnFirebase
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.math.cos
import kotlin.math.roundToInt
import kotlin.math.sin

private val EASE = CubicBezierEasing(0.22f, 0.61f, 0.36f, 1f)

/** Ángulo (en grados, convención de pantalla: 0=derecha, 90=abajo, 180=
 *  izquierda, 270=arriba) al que el plato rota el ingrediente activo. Antes
 *  era 270 (arriba), pero esa zona queda muy cerca del borde superior del
 *  stage; corrido más a la izquierda deja el ingrediente activo bien
 *  centrado en la mitad visible del plato (la que no tapa el panel). */
private const val ANGULO_OBJETIVO_GRADOS = 200f

private enum class PantallaDieta { CATALOGO, DETALLE }

@Composable
fun DietaScreen(objetivo: ObjetivoCompetencia? = null, onOcultarBurbujaArgos: (Boolean) -> Unit = {}) {
    var mostrarNutricion by remember { mutableStateOf(false) }
    if (mostrarNutricion) {
        NutricionScreen(onVolver = { mostrarNutricion = false })
        return
    }

    // Dietas publicadas desde el editor de empleados (Firebase), precargadas
    // desde que se entró a la app (ver DatosRemotos/MainActivity) — si
    // todavía no hay nada publicado, o Firebase no está configurado en el
    // celular, se queda con el catálogo de ejemplo.
    val platos = DatosRemotos.platos?.takeIf { it.isNotEmpty() } ?: PLATOS

    // Cada vez que se abre Dieta: por si el nutricionista asignó o cambió la
    // dieta (o el socio registró algo desde otro celular) con la app abierta.
    LaunchedEffect(Unit) {
        DatosRemotos.recargarDietaAsignada()
        DatosRemotos.recargarComidas()
    }

    var registrando by remember { mutableStateOf<MomentoComida?>(null) }
    // La burbuja flotante de Argos tapaba el botón "Guardar comida": se
    // esconde mientras se registra una comida y vuelve al salir de Dieta.
    LaunchedEffect(registrando) { onOcultarBurbujaArgos(registrando != null) }
    androidx.compose.runtime.DisposableEffect(Unit) { onDispose { onOcultarBurbujaArgos(false) } }
    val momentoRegistrando = registrando
    if (momentoRegistrando != null) {
        RegistrarComidaScreen(momentoRegistrando, objetivo, platos, onVolver = { registrando = null })
        return
    }

    var pantalla by remember { mutableStateOf(PantallaDieta.CATALOGO) }
    var platoActivo by remember { mutableIntStateOf(0) }
    var busqueda by remember { mutableStateOf("") }
    val expandidos = remember { mutableStateListOf<String>() }

    when (pantalla) {
        PantallaDieta.CATALOGO -> CatalogoDietas(
            platos = platos,
            objetivo = objetivo,
            busqueda = busqueda,
            onBusqueda = { busqueda = it },
            expandidos = expandidos,
            onToggleExpandir = { id -> if (id in expandidos) expandidos.remove(id) else expandidos.add(id) },
            onNutricion = { mostrarNutricion = true },
            onRegistrar = { registrando = it },
            onVer = { idx -> platoActivo = idx; pantalla = PantallaDieta.DETALLE }
        )
        PantallaDieta.DETALLE -> DetalleDieta(
            plato = platos[platoActivo.coerceIn(platos.indices)],
            onVolver = { pantalla = PantallaDieta.CATALOGO }
        )
    }
}

/* ═══════════════════════ CATÁLOGO (grilla 2×N) ═══════════════════════ */

@Composable
private fun CatalogoDietas(
    platos: List<Plato>,
    objetivo: ObjetivoCompetencia?,
    busqueda: String,
    onBusqueda: (String) -> Unit,
    expandidos: List<String>,
    onToggleExpandir: (String) -> Unit,
    onNutricion: () -> Unit,
    onRegistrar: (MomentoComida) -> Unit,
    onVer: (Int) -> Unit
) {
    val query = busqueda.trim().lowercase()
    fun coincide(p: Plato) = query.isEmpty() ||
        p.nombre.lowercase().contains(query) ||
        p.tags.any { it.lowercase().contains(query) }

    // "Asignadas" = los platos de la dieta que le armó SU nutricionista
    // (por horario, ver DietaAsignada) — ya no un tilde global en el plato.
    val idsAsignados = DatosRemotos.dietaAsignada?.platoIds.orEmpty()
    val indexados = platos.withIndex().toList()
    val asignadasBase = indexados.filter { it.value.id in idsAsignados }
    val catalogoBase = indexados.filter { it.value.id !in idsAsignados }
    val catalogo = catalogoBase.filter { coincide(it.value) }
    val asignadas = asignadasBase.filter { coincide(it.value) }

    Column(Modifier.fillMaxSize()) {
        Column(
            Modifier
                .statusBarsPadding()
                .padding(horizontal = 20.dp)
                .padding(top = 14.dp)
        ) {
            if (objetivo != null) {
                BadgeObjetivo(objetivo)
                Spacer(Modifier.height(10.dp))
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Eyebrow("Mi dieta")
                    Row {
                        Text("Plato ", fontSize = 26.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
                        Text("saludable", fontSize = 26.sp, fontWeight = FontWeight.Black, color = Olimpos.Gold)
                    }
                }
                Box(
                    Modifier
                        .clip(RoundedCornerShape(14.dp))
                        .background(Olimpos.GoldSoft)
                        .border(1.dp, Olimpos.Gold.copy(alpha = 0.3f), RoundedCornerShape(14.dp))
                        .clickable { onNutricion() }
                        .padding(horizontal = 12.dp, vertical = 10.dp)
                ) {
                    Text("🥗 Mi nutrición", fontSize = 11.5.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.GoldLight)
                }
            }
            Spacer(Modifier.height(13.dp))
            CampoBusqueda(busqueda, onBusqueda, "Buscar por nombre u objetivo…")
        }

        Column(
            Modifier
                .weight(1f)
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
        ) {
            SeccionMiDia(objetivo, platos, onRegistrar)

            SeccionLabel("Catálogo")
            if (catalogo.isEmpty()) {
                EstadoVacioDietas(
                    if (query.isEmpty()) "Todavía no hay dietas publicadas."
                    else "Sin resultados para \"$busqueda\"."
                )
            } else {
                GridDietas(catalogo, expandidos, onToggleExpandir, onVer)
            }

            SeccionLabel("Asignadas por tu nutricionista")
            when {
                asignadasBase.isEmpty() -> EstadoVacioDietas(
                    "Tu nutricionista o entrenador todavía no te asignó una dieta personalizada."
                )
                asignadas.isEmpty() -> EstadoVacioDietas("Sin resultados para \"$busqueda\".")
                else -> GridDietas(asignadas, expandidos, onToggleExpandir, onVer)
            }
            Spacer(Modifier.height(20.dp))
        }
    }
}

@Composable
private fun GridDietas(
    items: List<IndexedValue<Plato>>,
    expandidos: List<String>,
    onToggleExpandir: (String) -> Unit,
    onVer: (Int) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        items.chunked(2).forEach { fila ->
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                fila.forEach { (idx, p) ->
                    TarjetaDieta(
                        plato = p,
                        expandido = p.id in expandidos,
                        onToggleExpandir = { onToggleExpandir(p.id) },
                        onVer = { onVer(idx) },
                        modifier = Modifier.weight(1f)
                    )
                }
                if (fila.size == 1) Spacer(Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun TarjetaDieta(
    plato: Plato,
    expandido: Boolean,
    onToggleExpandir: () -> Unit,
    onVer: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier
            .clip(RoundedCornerShape(18.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(18.dp))
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null,
                onClick = onToggleExpandir
            )
    ) {
        AsyncImage(
            model = plato.imagen,
            contentDescription = plato.nombre,
            contentScale = ContentScale.Crop,
            modifier = Modifier
                .fillMaxWidth()
                .height(96.dp)
                .clip(RoundedCornerShape(topStart = 18.dp, topEnd = 18.dp))
        )
        Column(Modifier.padding(12.dp)) {
            Text(
                plato.nombre, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold,
                color = Olimpos.Cream, maxLines = 1
            )
            if (plato.tags.isNotEmpty()) {
                Spacer(Modifier.height(6.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                    plato.tags.take(3).forEach { EtiquetaMini(it) }
                }
            }
            androidx.compose.animation.AnimatedVisibility(
                visible = expandido,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically()
            ) {
                Column {
                    Spacer(Modifier.height(8.dp))
                    Text(
                        plato.descripcion.ifBlank { "Sin descripción todavía." },
                        fontSize = 11.5.sp, lineHeight = 15.sp, color = Olimpos.Muted
                    )
                }
            }
            Spacer(Modifier.height(10.dp))
            Box(
                Modifier
                    .align(Alignment.End)
                    .clip(RoundedCornerShape(100.dp))
                    .background(Brush.linearGradient(listOf(Olimpos.Gold, Olimpos.GoldDark)))
                    .clickable(onClick = onVer)
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            ) {
                Text("Ver ▸", fontSize = 11.5.sp, fontWeight = FontWeight.ExtraBold, color = Color.White)
            }
        }
    }
}

@Composable
private fun EtiquetaMini(texto: String) {
    Box(
        Modifier
            .clip(RoundedCornerShape(100.dp))
            .background(Olimpos.GoldSoft)
            .padding(horizontal = 8.dp, vertical = 3.dp)
    ) {
        Text(texto, fontSize = 9.5.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.GoldLight, maxLines = 1)
    }
}

@Composable
private fun EstadoVacioDietas(mensaje: String) {
    Box(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
            .padding(18.dp)
    ) {
        Text(
            mensaje, fontSize = 12.sp, color = Olimpos.Muted,
            textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth()
        )
    }
}

/* ═══════════════════ DETALLE: plato giratorio + panel lateral ═══════════════════ */

@Composable
private fun DetalleDieta(plato: Plato, onVolver: () -> Unit) {
    var activo by remember { mutableStateOf<Int?>(null) }
    var rotObjetivo by remember { mutableStateOf(0f) }
    var reproduciendo by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    // Para el logro "Sibarita" (probar 10 platos distintos) — nunca se
    // marca solo, es el propio socio el que dice "ya lo probé".
    val yaProbado = plato.id in (DatosRemotos.platosProbados ?: emptySet())

    val items = plato.items
    val enfocado = activo != null

    fun activar(i: Int) {
        val ing = items[i]
        if (ing.radio > 0f) {
            val deseado = ANGULO_OBJETIVO_GRADOS - ing.angulo
            val actual = ((rotObjetivo % 360f) + 360f) % 360f
            var delta = ((deseado - actual) % 360f + 360f) % 360f
            if (delta > 180f) delta -= 360f
            rotObjetivo += delta
        }
        activo = i
    }

    LaunchedEffect(reproduciendo) {
        while (reproduciendo) {
            delay(3400)
            activar(((activo ?: -1) + 1) % items.size)
        }
    }

    val rot by animateFloatAsState(rotObjetivo, tween(1050, easing = EASE), label = "rot")

    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver(plato.nombre, "Tocá un ingrediente o iniciá el recorrido", onVolver)

        Row(
            Modifier
                .padding(horizontal = 20.dp)
                .padding(bottom = 4.dp)
        ) {
            Box(
                Modifier
                    .clip(RoundedCornerShape(100.dp))
                    .background(if (yaProbado) Olimpos.Card else Olimpos.GoldSoft)
                    .border(
                        1.dp,
                        if (yaProbado) Olimpos.Line else Olimpos.Gold.copy(alpha = 0.35f),
                        RoundedCornerShape(100.dp)
                    )
                    .clickable(enabled = !yaProbado) {
                        scope.launch {
                            marcarPlatoProbadoEnFirebase(plato.id)
                            DatosRemotos.recargarPlatosProbados()
                        }
                    }
                    .padding(horizontal = 14.dp, vertical = 8.dp)
            ) {
                Text(
                    if (yaProbado) "✓ Ya probaste este plato" else "🍽️ Marcar como probado",
                    fontSize = 11.5.sp, fontWeight = FontWeight.ExtraBold,
                    color = if (yaProbado) Olimpos.Muted else Olimpos.GoldLight
                )
            }
        }

        BoxWithConstraints(Modifier.weight(1f).fillMaxWidth()) {
            val anchoStage = maxWidth
            val altoStage = maxHeight
            val anchoPanel = (anchoStage * 0.62f).coerceIn(200.dp, 300.dp)
            val diametroPlato = (minOf(anchoStage, altoStage) * 0.82f).coerceAtMost(320.dp)

            // Al enfocar un ingrediente, el plato (con sus puntos) se corre
            // como UN SOLO bloque rígido hacia el espacio libre a la
            // izquierda del panel — nunca se agranda (antes escalaba 1.7x,
            // y como los puntos compartían ese escalado, saltaban de
            // tamaño y de posición junto con el plato). Sin zoom, los
            // puntos quedan siempre exactamente donde estaban.
            val desplX by animateFloatAsState(
                if (enfocado) -(anchoPanel.value / 2f) else 0f,
                tween(1050, easing = EASE), label = "tx"
            )

            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Box(
                    Modifier
                        .size(diametroPlato * 1.15f)
                        .graphicsLayer { translationX = desplX }
                        .background(
                            Brush.radialGradient(listOf(Olimpos.GoldLight.copy(alpha = 0.12f), Color.Transparent)),
                            CircleShape
                        )
                )

                Box(
                    Modifier
                        .size(diametroPlato)
                        .graphicsLayer { translationX = desplX }
                ) {
                    Box(
                        Modifier
                            .fillMaxSize()
                            .clip(CircleShape)
                            .border(2.5.dp, Olimpos.Gold.copy(alpha = 0.8f), CircleShape)
                            .graphicsLayer { rotationZ = rot }
                    ) {
                        AsyncImage(
                            model = plato.imagen,
                            contentDescription = plato.nombre,
                            contentScale = ContentScale.Crop,
                            modifier = Modifier
                                .fillMaxSize()
                                .graphicsLayer { scaleX = 1.12f; scaleY = 1.12f }
                        )
                    }

                    items.forEachIndexed { i, ing ->
                        val radioPx = with(androidx.compose.ui.platform.LocalDensity.current) { (diametroPlato / 2).toPx() * (ing.radio / 100f) }
                        val rad = Math.toRadians(ing.angulo.toDouble())
                        // Al enfocar un ingrediente (a mano o durante el
                        // recorrido) TODOS los puntos desaparecen, incluido
                        // el activo — la comida ya se identifica con el
                        // panel de la derecha, el puntito solo estorbaba.
                        val oculto = enfocado
                        val alfa by animateFloatAsState(if (oculto) 0f else 1f, tween(400), label = "d$i")
                        Box(
                            Modifier
                                .align(Alignment.Center)
                                .graphicsLayer {
                                    translationX = cos(rad).toFloat() * radioPx
                                    translationY = sin(rad).toFloat() * radioPx
                                    rotationZ = -rot
                                    alpha = alfa
                                    val esc = if (oculto) 0.4f else 1f
                                    scaleX = esc; scaleY = esc
                                }
                                .size(26.dp)
                                .clip(CircleShape)
                                .background(Color.White.copy(alpha = 0.94f))
                                .border(2.dp, Olimpos.GoldDark, CircleShape)
                                .clickable(enabled = !oculto) { reproduciendo = false; activar(i) },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                "${i + 1}", fontSize = 12.sp, fontWeight = FontWeight.Black,
                                color = Olimpos.GoldDark
                            )
                        }
                    }
                }

                androidx.compose.animation.AnimatedVisibility(
                    visible = !enfocado,
                    modifier = Modifier.align(Alignment.BottomCenter),
                    enter = fadeIn(), exit = fadeOut()
                ) {
                    Column(
                        Modifier.padding(bottom = 18.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Box(
                            Modifier
                                .clip(RoundedCornerShape(100.dp))
                                .background(Olimpos.Card)
                                .border(1.dp, Olimpos.Line, RoundedCornerShape(100.dp))
                                .padding(horizontal = 14.dp, vertical = 6.dp)
                        ) {
                            Text(
                                "Tocá un ingrediente o iniciá el recorrido",
                                fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted
                            )
                        }
                        Spacer(Modifier.height(11.dp))
                        Box(
                            Modifier
                                .clip(RoundedCornerShape(100.dp))
                                .background(Brush.linearGradient(listOf(Olimpos.Gold, Olimpos.GoldDark)))
                                .clickable { activar(0); reproduciendo = true }
                                .padding(horizontal = 26.dp, vertical = 13.dp)
                        ) {
                            Text("▶  Iniciar recorrido", fontSize = 13.5.sp, fontWeight = FontWeight.ExtraBold, color = Color.White)
                        }
                    }
                }
            }

            androidx.compose.animation.AnimatedVisibility(
                visible = enfocado,
                modifier = Modifier.align(Alignment.CenterEnd).fillMaxHeight(),
                enter = slideInHorizontally(tween(550, easing = EASE)) { it } + fadeIn(),
                exit = slideOutHorizontally(tween(400)) { it } + fadeOut()
            ) {
                val ing = items[(activo ?: 0).coerceIn(items.indices)]
                PanelIngrediente(
                    plato = plato,
                    ing = ing,
                    indice = (activo ?: 0),
                    total = items.size,
                    ancho = anchoPanel,
                    reproduciendo = reproduciendo,
                    onCerrar = {
                        reproduciendo = false; activo = null
                        rotObjetivo = (rotObjetivo / 360f).roundToInt() * 360f
                    },
                    onSeleccionar = { reproduciendo = false; activar(it) },
                    onTogglePlay = {
                        if (!reproduciendo && activo == null) activar(0)
                        reproduciendo = !reproduciendo
                    },
                    onPrev = { reproduciendo = false; activar(((activo ?: 0) - 1 + items.size) % items.size) },
                    onNext = { reproduciendo = false; activar(((activo ?: -1) + 1) % items.size) }
                )
            }
        }
    }
}

/** Recorte circular del ingrediente activo, para el encabezado del panel —
 *  vive adentro del panel (nunca flota sobre el plato ni lo tapa). El
 *  desplazamiento usa el radio real de la caja según su tamaño en pantalla
 *  y compensa el zoom aplicado (antes usaba un offset fijo en píxeles sin
 *  escalar por ninguno de los dos, así que el recorte casi no cambiaba
 *  entre ingredientes y terminaba mostrando siempre más o menos el centro
 *  del plato en vez del ingrediente real). */
@Composable
private fun RecorteIngrediente(plato: Plato, ing: Ingrediente, tamano: androidx.compose.ui.unit.Dp) {
    Box(
        Modifier
            .size(tamano)
            .clip(CircleShape)
            .border(2.dp, Olimpos.Gold, CircleShape)
    ) {
        val zoom = 1.8f
        val rad = Math.toRadians(ing.angulo.toDouble())
        val radioCajaPx = with(androidx.compose.ui.platform.LocalDensity.current) { (tamano / 2).toPx() }
        val d = radioCajaPx * (ing.radio / 100f)
        val fx = if (ing.radio > 0f) cos(rad).toFloat() * d * zoom else 0f
        val fy = if (ing.radio > 0f) sin(rad).toFloat() * d * zoom else 0f
        AsyncImage(
            model = plato.imagen,
            contentDescription = ing.nombre,
            contentScale = ContentScale.Crop,
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer {
                    scaleX = zoom; scaleY = zoom
                    translationX = -fx; translationY = -fy
                }
        )
    }
}

@Composable
private fun PanelIngrediente(
    plato: Plato,
    ing: Ingrediente,
    indice: Int,
    total: Int,
    ancho: androidx.compose.ui.unit.Dp,
    reproduciendo: Boolean,
    onCerrar: () -> Unit,
    onSeleccionar: (Int) -> Unit,
    onTogglePlay: () -> Unit,
    onPrev: () -> Unit,
    onNext: () -> Unit
) {
    Column(
        Modifier
            .width(ancho)
            .fillMaxHeight()
            .clip(RoundedCornerShape(topStart = 26.dp, bottomStart = 26.dp))
            // Superficie2 (no Card): este panel se superpone a la foto del
            // plato, no al fondo liso de la pantalla — Card es semitransparente
            // a propósito en modo oscuro (pensada para ir sobre el degradé de
            // fondo), así que acá dejaba traslucir la foto y el texto se
            // volvía ilegible. Superficie2 es opaca en los dos modos.
            .background(Olimpos.Superficie2)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(topStart = 26.dp, bottomStart = 26.dp))
    ) {
        Column(
            Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(18.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                ChipOro(ing.categoria.uppercase())
                Spacer(Modifier.weight(1f))
                Box(
                    Modifier
                        .size(28.dp)
                        .clip(CircleShape)
                        .background(Olimpos.GoldSoft)
                        .clickable(
                            interactionSource = remember { MutableInteractionSource() },
                            indication = null,
                            onClick = onCerrar
                        ),
                    contentAlignment = Alignment.Center
                ) { Text("✕", fontSize = 12.sp, color = Olimpos.Muted) }
            }
            Spacer(Modifier.height(11.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                RecorteIngrediente(plato, ing, tamano = 58.dp)
                Spacer(Modifier.width(12.dp))
                Column {
                    Text(
                        "INGREDIENTE ${indice + 1} DE $total",
                        fontSize = 9.5.sp, fontWeight = FontWeight.ExtraBold,
                        letterSpacing = 1.sp, color = Olimpos.Muted
                    )
                    Text(ing.nombre, fontSize = 17.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream)
                }
            }
            Spacer(Modifier.height(12.dp))
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .background(Olimpos.GoldSoft)
                    .border(1.dp, Olimpos.Gold.copy(alpha = 0.25f), RoundedCornerShape(14.dp))
                    .padding(horizontal = 13.dp, vertical = 9.dp),
                verticalAlignment = Alignment.Bottom
            ) {
                Text(ing.kcal, fontSize = 19.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldDark)
                Spacer(Modifier.width(6.dp))
                Text("por porción", fontSize = 10.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 2.dp))
            }
            Spacer(Modifier.height(10.dp))
            Text(ing.aporte, fontSize = 12.5.sp, lineHeight = 18.sp, color = Olimpos.Muted)
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                ing.tags.take(2).forEach { t -> ChipOro(t) }
            }
            Spacer(Modifier.height(14.dp))
            Text(
                "APORTE SALUDABLE", fontSize = 9.5.sp, fontWeight = FontWeight.ExtraBold,
                letterSpacing = 1.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 9.dp)
            )
            ing.beneficios.forEach { b ->
                Row(Modifier.padding(bottom = 7.dp), verticalAlignment = Alignment.Top) {
                    IconoCheck()
                    Spacer(Modifier.width(8.dp))
                    Text(b, fontSize = 11.5.sp, lineHeight = 15.sp, color = Olimpos.Muted)
                }
            }
        }

        Column(
            Modifier
                .fillMaxWidth()
                .background(Olimpos.Superficie2)
                .padding(horizontal = 16.dp, vertical = 12.dp)
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                (0 until total).forEach { idx ->
                    Box(
                        Modifier
                            .weight(1f)
                            .height(4.dp)
                            .clip(RoundedCornerShape(3.dp))
                            .background(if (idx <= indice) Olimpos.Gold else Olimpos.Line)
                            .clickable(
                                interactionSource = remember { MutableInteractionSource() },
                                indication = null
                            ) { onSeleccionar(idx) }
                    )
                }
            }
            Spacer(Modifier.height(10.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                ControlRedondo("‹", onPrev)
                Box(
                    Modifier
                        .size(50.dp)
                        .clip(CircleShape)
                        .background(Brush.linearGradient(listOf(Olimpos.Gold, Olimpos.GoldDark)))
                        .clickable(onClick = onTogglePlay),
                    contentAlignment = Alignment.Center
                ) {
                    Text(if (reproduciendo) "❚❚" else "▶", fontSize = 15.sp, fontWeight = FontWeight.Black, color = Color.White)
                }
                ControlRedondo("›", onNext)
            }
        }
    }
}

@Composable
private fun ControlRedondo(simbolo: String, onClick: () -> Unit) {
    Box(
        Modifier
            .size(38.dp)
            .clip(CircleShape)
            .background(Olimpos.GoldSoft)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) { Text(simbolo, fontSize = 17.sp, color = Olimpos.Muted) }
}
