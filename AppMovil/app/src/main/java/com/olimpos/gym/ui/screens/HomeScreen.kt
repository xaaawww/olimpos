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
import com.olimpos.gym.data.Ocupacion
import com.olimpos.gym.data.ReservaClase
import com.olimpos.gym.data.ResultadoReserva
import com.olimpos.gym.data.cancelarReservaClaseEnFirebase
import com.olimpos.gym.data.cargarOcupacionDesdeFirebase
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

@Composable
fun HomeScreen(
    onAbrirPlano: () -> Unit,
    onIrEntrenar: () -> Unit,
    onIrDieta: () -> Unit,
    onAbrirTurnos: () -> Unit
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
                "OLIMPΩS", fontSize = 11.sp, fontWeight = FontWeight.SemiBold,
                letterSpacing = 2.sp, color = Olimpos.Muted
            )
        }
        Spacer(Modifier.height(10.dp))

        // ── Saludo ──
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Eyebrow(fechaDeHoyLegible())
                Text("Hola, $primerNombre", fontSize = 22.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
            }
            AvatarInicial(primerNombre.take(1).uppercase(), tamano = 42)
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

        // ── Clases: todo vive en Perfil → Mis turnos y reservas; acá el resumen ──
        SeccionLabel("Clases de la semana")
        val reservasClase = DatosRemotos.reservasClase ?: emptyList()
        val reservadas = CLASES_SEMANA.filter { c -> reservasClase.any { it.claseId == c.id } }
        TarjetaOro(Modifier.fillMaxWidth().clickable(onClick = onAbrirTurnos)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconoCuadrado("📅")
                Spacer(Modifier.width(13.dp))
                Column(Modifier.weight(1f)) {
                    Text("Mis turnos y reservas", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Olimpos.Cream)
                    Text(
                        if (reservadas.isEmpty()) "${CLASES_SEMANA.size} clases esta semana · todavía sin reservas"
                        else "${reservadas.size} reservada${if (reservadas.size == 1) "" else "s"}: " +
                            reservadas.joinToString(" · ") { "${it.nombre} ${it.hora}" },
                        fontSize = 12.sp, color = Olimpos.Muted, maxLines = 2
                    )
                }
                FlechaFila()
            }
        }

        // ── Equivalencia de carga movida ──
        SeccionLabel("Este mes levantaste el equivalente a…")
        EquivalenciaCarga()

        // ── Accesos rápidos ──
        SeccionLabel("Accesos rápidos")
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            AccesoRapido(
                "🏋️", "Mi rutina",
                DatosRemotos.rutinaActiva?.let { "${it.ejercicios.size} ejercicios hoy" } ?: "Todavía sin asignar",
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
                    Text("Plano del club", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Olimpos.Cream)
                    Text(
                        "Recorré los 2 pisos y encontrá cada sala",
                        fontSize = 12.sp, color = Olimpos.Muted
                    )
                }
                FlechaFila()
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
            .clip(RoundedCornerShape(18.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(18.dp))
            .padding(16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            // Anillo giratorio + núcleo dorado
            Box(Modifier.size(72.dp), contentAlignment = Alignment.Center) {
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
                        .size(52.dp)
                        .clip(CircleShape)
                        .background(Olimpos.GoldSoft),
                    contentAlignment = Alignment.Center
                ) {
                    Text("Ω", fontSize = 24.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.GoldLight)
                }
            }
            Spacer(Modifier.width(14.dp))
            Column {
                Text(socioActualNombre(), fontWeight = FontWeight.SemiBold, fontSize = 16.sp, color = Olimpos.Cream)
                Text("Carnet digital OlimpΩs", fontSize = 12.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 2.dp))
            }
        }
        Spacer(Modifier.height(14.dp))
        // La entrada se registra escaneando el QR de la recepción (ver EscanerIngreso.kt).
        IngresoConQr()
    }
}

/* ───────────────────── Ocupación en vivo ───────────────────── */
/** Número real: socios que escanearon el QR de entrada en el último rato (ver
 *  OcupacionRepository.kt). Se vuelve a pedir cada 30 segundos mientras la
 *  pantalla está abierta, y al instante cuando el propio socio escanea el
 *  QR (cambia DatosRemotos.ingresos y se reinicia el ciclo). */
@Composable
private fun OcupacionEnVivo() {
    var ocupacion by remember { mutableStateOf<Ocupacion?>(null) }
    LaunchedEffect(DatosRemotos.ingresos) {
        while (true) {
            cargarOcupacionDesdeFirebase()?.let { ocupacion = it }
            delay(30_000)
        }
    }
    val personas = ocupacion?.personas ?: 0
    val capacidad = ocupacion?.capacidadMaxima ?: 120
    val frac by animateFloatAsState(if (capacidad > 0) personas / capacidad.toFloat() else 0f, tween(1100), label = "occ")
    val parpadeo by rememberInfiniteTransition(label = "live").animateFloat(
        1f, 0.25f, infiniteRepeatable(tween(800), RepeatMode.Reverse), label = "dot"
    )

    TarjetaOro(Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Ocupación del gimnasio", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Olimpos.Cream, modifier = Modifier.weight(1f))
            Box(Modifier.size(7.dp).clip(CircleShape).background(Olimpos.Green.copy(alpha = parpadeo)))
            Spacer(Modifier.width(6.dp))
            Text("EN VIVO", fontSize = 10.sp, fontWeight = FontWeight.SemiBold, letterSpacing = 1.sp, color = Olimpos.Green)
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
                    .background(androidx.compose.ui.graphics.SolidColor(Olimpos.Gold))
            )
        }
        Spacer(Modifier.height(8.dp))
        Row {
            Text(
                if (ocupacion == null) "Conectando…" else if (personas == 1) "1 persona en el club" else "$personas personas en el club",
                fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted,
                modifier = Modifier.weight(1f)
            )
            Text("Capacidad $capacidad", fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted)
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
                    fontWeight = FontWeight.SemiBold, fontSize = 15.sp, color = Olimpos.Cream
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
fun TarjetaClase(clase: ClaseSemana, reservasClase: List<ReservaClase>, cuposClases: Map<String, Int>, capacidades: Map<String, Int>) {
    var expandida by remember { mutableStateOf(false) }
    var procesando by remember { mutableStateOf(false) }
    var aviso by remember { mutableStateOf<String?>(null) }
    val reservado = yaReservadaEstaSemana(reservasClase, clase.id)
    val ocupados = cuposClases[clase.id] ?: 0
    val cupo = capacidades[clase.id] ?: clase.cupo
    val completa = !reservado && ocupados >= cupo
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
                    .width(58.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(Olimpos.GoldSoft)
                    .padding(vertical = 9.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(clase.hora, fontWeight = FontWeight.SemiBold, fontSize = 15.sp, color = Olimpos.GoldLight)
                Text(clase.dia, fontSize = 9.5.sp, fontWeight = FontWeight.Medium, color = Olimpos.Muted)
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(clase.nombre, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Olimpos.Cream)
                Text(clase.lugar, fontSize = 11.5.sp, color = Olimpos.Muted, maxLines = 1)
                Text(
                    if (reservado) "✓ Reservado · $ocupados/$cupo" else "$ocupados/$cupo reservados",
                    fontSize = 11.sp, fontWeight = FontWeight.Medium,
                    color = when {
                        reservado -> Color(0xFF16A34A)
                        completa -> Olimpos.Red
                        else -> Olimpos.Muted
                    }
                )
            }
            Spacer(Modifier.width(8.dp))
            Box(
                Modifier
                    .width(88.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(if (reservado || completa) Olimpos.Superficie2 else Olimpos.Gold)
                    .clickable(
                        enabled = !procesando && !completa,
                        interactionSource = remember { androidx.compose.foundation.interaction.MutableInteractionSource() },
                        indication = null
                    ) {
                        procesando = true
                        aviso = null
                        scope.launch {
                            if (reservado) {
                                cancelarReservaClaseEnFirebase(clase.id)
                            } else {
                                when (guardarReservaClaseEnFirebase(clase.id)) {
                                    ResultadoReserva.CLASE_LLENA -> aviso = "Justo se llenó — probá con otra clase."
                                    ResultadoReserva.ERROR -> aviso = "No se pudo reservar. Probá de nuevo."
                                    else -> {}
                                }
                            }
                            DatosRemotos.recargarReservasClase()
                            procesando = false
                        }
                    }
                    .padding(vertical = 9.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    when {
                        procesando -> "…"
                        reservado -> "Cancelar"
                        completa -> "Completo"
                        else -> "Reservar"
                    },
                    fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
                    color = if (reservado || completa) Olimpos.Muted else Olimpos.Dark
                )
            }
        }
        androidx.compose.animation.AnimatedVisibility(visible = expandida) {
            Text(
                clase.descripcion, fontSize = 12.sp, color = Olimpos.Muted, lineHeight = 17.sp,
                modifier = Modifier.padding(top = 11.dp)
            )
        }
        aviso?.let {
            Text(it, fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Olimpos.Red,
                modifier = Modifier.padding(top = 6.dp))
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
        Text(titulo, fontWeight = FontWeight.SemiBold, fontSize = 13.5.sp, color = Olimpos.Cream)
        Text(sub, fontSize = 11.5.sp, color = Olimpos.Muted)
    }
}
