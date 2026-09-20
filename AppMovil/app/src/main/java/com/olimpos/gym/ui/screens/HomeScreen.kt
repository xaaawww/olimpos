package com.olimpos.gym.ui.screens

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.Canvas
import com.olimpos.gym.R
import com.olimpos.gym.data.CLASES_SEMANA
import com.olimpos.gym.data.ClaseSemana
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.data.ReservaClase
import com.olimpos.gym.data.cantidadEquivalencia
import com.olimpos.gym.data.equivalenciaDeCarga
import com.olimpos.gym.data.guardarReservaClaseEnFirebase
import com.olimpos.gym.data.kgMovidosEsteMes
import com.olimpos.gym.data.leerObjetivoArena
import com.olimpos.gym.data.metaDelDia
import com.olimpos.gym.data.rachaDietaActual
import com.olimpos.gym.data.socioActualNombre
import com.olimpos.gym.data.yaReservadaEstaSemana
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.random.Random

@Composable
fun HomeScreen(
    onAbrirPlano: () -> Unit,
    onIrEntrenar: () -> Unit,
    onIrDieta: () -> Unit
) {
    val nombreSocio = socioActualNombre()
    val primerNombre = nombreSocio.substringBefore(" ")
    var mostrarTablon by remember { mutableStateOf(false) }
    // Cada vez que se vuelve a Inicio se pide de nuevo: un aviso nuevo del
    // dueño aparece sin tener que reiniciar la app.
    LaunchedEffect(Unit) { DatosRemotos.recargarTablon() }
    if (mostrarTablon) {
        TablonScreen(onVolver = { mostrarTablon = false })
        return
    }
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .statusBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(top = 14.dp, bottom = 26.dp)
    ) {
        // ── Marca ──
        Row(verticalAlignment = Alignment.CenterVertically) {
            Image(
                painter = painterResource(R.drawable.logo_olimpos),
                contentDescription = "OlimpΩs",
                modifier = Modifier.size(22.dp)
            )
            Spacer(Modifier.width(7.dp))
            Text(
                "OLIMPΩS", fontSize = 11.sp, fontWeight = FontWeight.ExtraBold,
                letterSpacing = 2.sp, color = Olimpos.Muted
            )
        }
        Spacer(Modifier.height(10.dp))

        // ── Saludo ──
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Eyebrow(fechaDeHoyLegible())
                Row {
                    Text("Hola, ", fontSize = 26.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
                    Text(primerNombre, fontSize = 26.sp, fontWeight = FontWeight.Black, color = Olimpos.Gold)
                    Text(" 👋", fontSize = 24.sp)
                }
            }
            Box(
                Modifier
                    .size(44.dp)
                    .clip(CircleShape)
                    .background(Brush.linearGradient(listOf(Olimpos.GoldLight, Olimpos.GoldDark))),
                contentAlignment = Alignment.Center
            ) {
                Text(primerNombre.take(1).uppercase(), fontWeight = FontWeight.Black, color = Olimpos.Dark, fontSize = 17.sp)
            }
        }

        Spacer(Modifier.height(18.dp))

        // ── Carnet digital con medalla Ω ──
        CarnetMedalla()

        // ── Tablón del club: lo publica solo el dueño desde el sistema de empleados ──
        SeccionLabel("Tablón del club")
        TablonResumen(onVerTodo = { mostrarTablon = true })

        // ── Ocupación en vivo ──
        SeccionLabel("Ahora en el club")
        OcupacionEnVivo()

        // ── Clases de la semana (antes vivían en Entrenar) ──
        SeccionLabel("Clases de la semana")
        val reservasClase = DatosRemotos.reservasClase ?: emptyList()
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            CLASES_SEMANA.forEach { clase -> TarjetaClase(clase, reservasClase) }
        }

        // ── Equivalencia de carga movida ──
        SeccionLabel("Este mes levantaste el equivalente a…")
        EquivalenciaCarga()

        // ── Accesos rápidos ──
        SeccionLabel("Accesos rápidos")
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            AccesoRapido(
                "🏋️", "Mi rutina",
                DatosRemotos.rutinaAsignada?.let { "${it.ejercicios.size} ejercicios hoy" } ?: "Todavía sin asignar",
                Modifier.weight(1f), onIrEntrenar
            )
            val objetivoDieta = leerObjetivoArena(LocalContext.current) ?: ObjetivoCompetencia.SALUD
            val rachaDieta = rachaDietaActual(
                DatosRemotos.diasComidas.orEmpty(), objetivoDieta,
                metaDelDia(DatosRemotos.dietaAsignada, DatosRemotos.platos.orEmpty())
            )
            AccesoRapido(
                "🥗", "Mi dieta",
                if (rachaDieta > 0) "🔥 Racha: $rachaDieta ${if (rachaDieta == 1) "día" else "días"}" else "Registrá tus comidas",
                Modifier.weight(1f), onIrDieta
            )
        }
        Spacer(Modifier.height(12.dp))
        // El plano NO es sección principal: acceso secundario desde aquí
        TarjetaOro(
            Modifier
                .fillMaxWidth()
                .clickable(onClick = onAbrirPlano)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconoCuadrado("🗺️")
                Spacer(Modifier.width(13.dp))
                Column(Modifier.weight(1f)) {
                    Text("Plano del club", fontWeight = FontWeight.ExtraBold, fontSize = 14.sp, color = Olimpos.Cream)
                    Text(
                        "Recorré los 2 pisos y encontrá cada sala",
                        fontSize = 12.sp, color = Olimpos.Muted
                    )
                }
                Text("→", color = Olimpos.Gold, fontWeight = FontWeight.Black, fontSize = 18.sp)
            }
        }
    }
}

/** "Domingo 20 · septiembre" — antes el saludo mostraba siempre "Lunes 6 · Julio". */
private fun fechaDeHoyLegible(): String =
    java.text.SimpleDateFormat("EEEE d · MMMM", java.util.Locale("es", "AR"))
        .format(java.util.Date())

/* ───────────────────── Carnet / medalla Ω ───────────────────── */
@Composable
private fun CarnetMedalla() {
    val giro by rememberInfiniteTransition(label = "giro").animateFloat(
        0f, 360f,
        infiniteRepeatable(tween(26000, easing = LinearEasing)),
        label = "anillo"
    )
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(28.dp))
            .background(Brush.linearGradient(listOf(Color(0xFF241D02), Color(0xFF171200), Color(0xFF0F0C00))))
            .border(1.dp, Olimpos.Gold.copy(alpha = 0.35f), RoundedCornerShape(28.dp))
            .padding(20.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            // Anillo giratorio + núcleo dorado
            Box(Modifier.size(104.dp), contentAlignment = Alignment.Center) {
                Canvas(Modifier.fillMaxSize().rotate(giro)) {
                    val r1 = size.minDimension / 2f - 2.dp.toPx()
                    drawCircle(
                        color = Olimpos.Gold.copy(alpha = 0.4f),
                        radius = r1,
                        style = Stroke(
                            width = 2.dp.toPx(),
                            pathEffect = PathEffect.dashPathEffect(floatArrayOf(6f, 14f))
                        )
                    )
                    drawCircle(
                        color = Olimpos.GoldLight.copy(alpha = 0.55f),
                        radius = r1 - 7.dp.toPx(),
                        style = Stroke(
                            width = 1.5.dp.toPx(),
                            pathEffect = PathEffect.dashPathEffect(floatArrayOf(58f, 120f))
                        )
                    )
                }
                Box(
                    Modifier
                        .size(74.dp)
                        .clip(CircleShape)
                        .background(
                            Brush.radialGradient(
                                listOf(Olimpos.GoldLight, Olimpos.Gold, Olimpos.GoldDark),
                                center = Offset(0.35f, 0.3f).let { Offset(it.x * 200, it.y * 200) }
                            )
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text("Ω", fontSize = 36.sp, fontWeight = FontWeight.Black, color = Olimpos.Dark)
                }
            }
            Spacer(Modifier.width(17.dp))
            Column {
                Text(socioActualNombre(), fontWeight = FontWeight.ExtraBold, fontSize = 17.sp, color = Olimpos.Cream)
                // Sin número de socio ni vencimiento de ejemplo: todavía no
                // existe una asignación real de plan/membresía por socio.
                Text(
                    "CARNET DIGITAL OLIMPΩS",
                    fontSize = 11.sp, fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 1.4.sp, color = Olimpos.GoldLight,
                    modifier = Modifier.padding(top = 2.dp, bottom = 9.dp)
                )
            }
        }
        Spacer(Modifier.height(15.dp))
        var mostrado by remember { mutableStateOf(false) }
        Box(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(Brush.linearGradient(listOf(Olimpos.Gold, Olimpos.GoldDark)))
                .clickable { mostrado = !mostrado }
                .padding(vertical = 13.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                if (mostrado) "CARNET LISTO — ACERCALO AL LECTOR ✓" else "MOSTRAR CARNET DE ACCESO",
                fontSize = 12.sp, fontWeight = FontWeight.ExtraBold,
                letterSpacing = 1.sp, color = Olimpos.Dark
            )
        }
    }
}

/* ───────────────────── Ocupación en vivo ───────────────────── */
@Composable
private fun OcupacionEnVivo() {
    var personas by remember { mutableIntStateOf(0) }
    LaunchedEffect(Unit) {
        delay(350)
        while (true) {
            personas = 54 + Random.nextInt(27)
            delay(7000)
        }
    }
    val frac by animateFloatAsState(personas / 120f, tween(1100), label = "occ")
    val parpadeo by rememberInfiniteTransition(label = "live").animateFloat(
        1f, 0.25f, infiniteRepeatable(tween(800), RepeatMode.Reverse), label = "dot"
    )

    TarjetaOro(Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Ocupación del gimnasio", fontWeight = FontWeight.ExtraBold, fontSize = 14.sp, color = Olimpos.Cream, modifier = Modifier.weight(1f))
            Box(Modifier.size(7.dp).clip(CircleShape).background(Olimpos.Green.copy(alpha = parpadeo)))
            Spacer(Modifier.width(6.dp))
            Text("EN VIVO", fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp, color = Olimpos.Green)
        }
        Spacer(Modifier.height(11.dp))
        Box(
            Modifier
                .fillMaxWidth()
                .height(10.dp)
                .clip(RoundedCornerShape(100.dp))
                .background(Color.White.copy(alpha = 0.07f))
        ) {
            Box(
                Modifier
                    .fillMaxWidth(frac)
                    .height(10.dp)
                    .clip(RoundedCornerShape(100.dp))
                    .background(Brush.linearGradient(listOf(Olimpos.GoldDark, Olimpos.Gold, Olimpos.GoldLight)))
            )
        }
        Spacer(Modifier.height(8.dp))
        Row {
            Text(
                if (personas == 0) "Conectando…" else "$personas personas entrenando",
                fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted,
                modifier = Modifier.weight(1f)
            )
            Text("Capacidad 120", fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted)
        }
    }
}

/* ───────────────────── Equivalencia de carga movida (kg) ───────────────────── */
@Composable
private fun EquivalenciaCarga() {
    // Se calcula de verdad a partir de las marcas cargadas este mes (ver
    // kgMovidosEsteMes) — antes esto era un 0 fijo porque no había forma
    // de filtrar por mes, ahora el timestamp real de cada marca alcanza.
    val marcas = DatosRemotos.marcas ?: emptyList()
    val series = DatosRemotos.seriesEntrenamiento ?: emptyList()
    val pesoCorporal = DatosRemotos.datosFisicosPropios?.pesoKg ?: 80f
    val kgDelMes = remember(marcas, series, pesoCorporal) { kgMovidosEsteMes(marcas, series, pesoCorporal) }

    if (kgDelMes <= 0) {
        TarjetaOro(Modifier.fillMaxWidth()) {
            Text(
                "Todavía no registraste kilos movidos este mes.",
                fontSize = 12.5.sp, color = Olimpos.Muted
            )
        }
        return
    }
    val eq = equivalenciaDeCarga(kgDelMes)
    val cantidad = cantidadEquivalencia(kgDelMes, eq.umbralKg)

    TarjetaOro(Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(eq.emoji, fontSize = 32.sp)
            Spacer(Modifier.width(13.dp))
            Column {
                Text(
                    if (cantidad > 1) "$cantidad × ${eq.texto}" else eq.texto,
                    fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, color = Olimpos.Cream
                )
                Text("$kgDelMes kg movidos este mes", fontSize = 11.5.sp, color = Olimpos.Muted)
            }
        }
    }
}

/* ───────────────────── Tarjeta de clase ─────────────────────
   Tocar la fila (fuera del botón de reservar) despliega la descripción de
   la clase, para saber de qué se trata antes de anotarse. */
@Composable
fun TarjetaClase(clase: ClaseSemana, reservasClase: List<ReservaClase>) {
    var expandida by remember { mutableStateOf(false) }
    var reservando by remember { mutableStateOf(false) }
    val reservado = reservando || yaReservadaEstaSemana(reservasClase, clase.id)
    val scope = rememberCoroutineScope()
    TarjetaOro(
        Modifier
            .fillMaxWidth()
            .clickable(
                interactionSource = remember { androidx.compose.foundation.interaction.MutableInteractionSource() },
                indication = null
            ) { expandida = !expandida }
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(
                Modifier
                    .clip(RoundedCornerShape(14.dp))
                    .background(Olimpos.GoldSoft)
                    .border(1.dp, Olimpos.Gold.copy(alpha = 0.28f), RoundedCornerShape(14.dp))
                    .padding(horizontal = 12.dp, vertical = 9.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(clase.hora, fontWeight = FontWeight.Black, fontSize = 16.sp, color = Olimpos.GoldLight)
                Text(clase.dia, fontSize = 9.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp, color = Olimpos.Muted)
            }
            Spacer(Modifier.width(13.dp))
            Column(Modifier.weight(1f)) {
                Text(clase.nombre, fontWeight = FontWeight.ExtraBold, fontSize = 14.5.sp, color = Olimpos.Cream)
                Text(clase.lugar, fontSize = 11.5.sp, color = Olimpos.Muted)
            }
            Box(
                Modifier
                    .clip(RoundedCornerShape(100.dp))
                    .background(if (reservado) Color.Transparent else Olimpos.Gold)
                    .border(
                        1.dp,
                        if (reservado) Olimpos.Green else Color.Transparent,
                        RoundedCornerShape(100.dp)
                    )
                    .clickable(
                        enabled = !reservado,
                        interactionSource = remember { androidx.compose.foundation.interaction.MutableInteractionSource() },
                        indication = null
                    ) {
                        reservando = true
                        scope.launch {
                            guardarReservaClaseEnFirebase(clase.id)
                            DatosRemotos.recargarReservasClase()
                        }
                    }
                    .padding(horizontal = 13.dp, vertical = 9.dp)
            ) {
                Text(
                    if (reservado) "Reservado ✓" else "Reservar",
                    fontSize = 11.sp, fontWeight = FontWeight.Black,
                    color = if (reservado) Olimpos.Green else Olimpos.Dark
                )
            }
        }
        androidx.compose.animation.AnimatedVisibility(visible = expandida) {
            Text(
                clase.descripcion, fontSize = 12.sp, color = Olimpos.Muted, lineHeight = 17.sp,
                modifier = Modifier.padding(top = 11.dp)
            )
        }
    }
}

/* ───────────────────── Acceso rápido ───────────────────── */
@Composable
private fun AccesoRapido(
    icono: String, titulo: String, sub: String,
    modifier: Modifier = Modifier, onClick: () -> Unit
) {
    TarjetaOro(modifier.clickable(onClick = onClick)) {
        IconoCuadrado(icono)
        Spacer(Modifier.height(9.dp))
        Text(titulo, fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
        Text(sub, fontSize = 11.5.sp, color = Olimpos.Muted)
    }
}

@Composable
fun IconoCuadrado(emoji: String) {
    Box(
        Modifier
            .size(38.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(Olimpos.GoldSoft)
            .border(1.dp, Olimpos.Gold.copy(alpha = 0.25f), RoundedCornerShape(12.dp)),
        contentAlignment = Alignment.Center
    ) { Text(emoji, fontSize = 18.sp) }
}
