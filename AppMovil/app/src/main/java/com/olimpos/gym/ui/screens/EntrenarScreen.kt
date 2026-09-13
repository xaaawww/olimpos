package com.olimpos.gym.ui.screens

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
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
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
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DETALLES_EJERCICIOS
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.DetalleEjercicio
import com.olimpos.gym.data.EjercicioRutina
import com.olimpos.gym.data.SerieEntrenamiento
import com.olimpos.gym.data.SerieHecha
import com.olimpos.gym.data.ghostModeDeEjercicio
import com.olimpos.gym.data.guardarSerieEnFirebase
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private const val PASO_KG = 2.5f

private fun formatoKg(kg: Float): String = "%.1f".format(kg).replace('.', ',')

/** Reps sugeridas para arrancar el campo editable de una serie: el primer
 *  número del rango prescrito por el entrenador (ej. "8-10" → 8). Es solo
 *  un punto de partida — el socio ajusta a lo que realmente hizo antes de
 *  tocar "Registrar serie". */
private fun repsSugeridas(detalle: DetalleEjercicio?): Int =
    detalle?.reps?.let { Regex("\\d+").find(it)?.value?.toIntOrNull() } ?: 8

@Composable
fun EntrenarScreen() {
    var detalleEjercicio by remember { mutableStateOf<EjercicioRutina?>(null) }
    var mostrarEntrenador by remember { mutableStateOf(false) }

    detalleEjercicio?.let { ej ->
        DetalleTecnicaRutina(ej, onVolver = { detalleEjercicio = null })
        return
    }
    if (mostrarEntrenador) {
        EntrenadorScreen(onVolver = { mostrarEntrenador = false })
        return
    }

    val scope = rememberCoroutineScope()
    val rutina = DatosRemotos.rutinaAsignada
    if (rutina == null) {
        SinRutinaAsignada(onActualizar = { scope.launch { DatosRemotos.recargarRutinaAsignada() } })
        return
    }

    // Peso y reps de trabajo actual por ejercicio (ajustables) y las series
    // ya registradas (con el peso/reps que tenían en el momento de
    // registrarlas) — en memoria mientras dura la sesión, pero cada serie
    // se guarda en Firestore al tocar "Registrar serie" (ver
    // guardarSerieEnFirebase), así el Ghost Mode y "kg movidos este mes"
    // de Inicio la ven sin esperar a que termine la sesión.
    val pesos = remember { mutableStateListOf(*rutina.ejercicios.map { it.pesoBaseKg }.toTypedArray()) }
    val reps = remember { mutableStateListOf(*rutina.ejercicios.map { repsSugeridas(DETALLES_EJERCICIOS[it.nombre]) }.toTypedArray()) }
    val seriesHechas = remember { rutina.ejercicios.map { mutableStateListOf<SerieHecha>() } }
    val totalObjetivo = remember { rutina.ejercicios.sumOf { it.seriesObjetivo } }
    val totalHechas = seriesHechas.sumOf { it.size }
    val historialSeries = DatosRemotos.seriesEntrenamiento ?: emptyList()

    // Column + verticalScroll a propósito, NO LazyColumn: son pocas tarjetas
    // y cada una tiene un campo de texto (el peso editable). En una lista
    // lazy esos campos se destruyen y se recrean cada vez que salen y
    // vuelven a entrar en pantalla, y un TextField es de lo más caro de
    // componer — el scroll terminaba peor que con todo compuesto una vez.
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .statusBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(top = 14.dp, bottom = 26.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Eyebrow("Gestión en curso")
            Spacer(Modifier.weight(1f))
            CronometroSesion()
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                rutina.nombre, fontSize = 24.sp, fontWeight = FontWeight.Black,
                color = Olimpos.Cream, modifier = Modifier.weight(1f)
            )
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("$totalHechas/$totalObjetivo", fontSize = 17.sp, fontWeight = FontWeight.Black, color = Olimpos.Gold)
                Text(
                    "SERIES", fontSize = 9.sp, fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 1.sp, color = Olimpos.Muted
                )
            }
        }
        Text("Rutina creada por ${rutina.creadaPor}", fontSize = 12.5.sp, color = Olimpos.Muted)

        SeccionLabel("Ejercicios")
        rutina.ejercicios.forEachIndexed { i, ej ->
            TarjetaEjercicioRutina(
                ejercicio = ej,
                pesoActual = pesos[i],
                onPeso = { pesos[i] = it.coerceAtLeast(0f) },
                repsActual = reps[i],
                onReps = { reps[i] = it.coerceAtLeast(1) },
                seriesHechas = seriesHechas[i],
                onRegistrarSerie = {
                    val serie = SerieHecha(pesoKg = pesos[i], reps = reps[i])
                    seriesHechas[i].add(serie)
                    scope.launch {
                        guardarSerieEnFirebase(ej.nombre, serie.pesoKg, serie.reps, System.currentTimeMillis(), ej.esPesoCorporal)
                        DatosRemotos.recargarSeriesEntrenamiento()
                    }
                },
                onTecnica = { detalleEjercicio = ej },
                modifier = Modifier.padding(bottom = 10.dp)
            )
        }

        SeccionLabel("Ghost Mode")
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            rutina.ejercicios.forEachIndexed { i, ej ->
                TarjetaGhostMode(ej.nombre, seriesHechas[i], historialSeries)
            }
        }

        Spacer(Modifier.height(6.dp))
        BotonPrincipal("Terminar y enviar a validación") {
            // Cada serie ya se guarda en Firestore al instante al tocar
            // "Registrar serie" (ver guardarSerieEnFirebase más arriba) —
            // este botón es el cierre visual de la sesión, no dispara un
            // envío aparte.
        }
        Text(
            "Cada serie queda registrada al instante en tu historial de entrenamiento.",
            fontSize = 10.5.sp, color = Olimpos.Muted, lineHeight = 14.sp,
            modifier = Modifier.padding(top = 8.dp)
        )

        SeccionLabel("Tu entrenador")
        TarjetaOro(
            Modifier
                .fillMaxWidth()
                .clickable { mostrarEntrenador = true }
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconoCuadrado("🧑‍🏫")
                Spacer(Modifier.width(13.dp))
                Column(Modifier.weight(1f)) {
                    Text("Contactar y reservar sesión", fontWeight = FontWeight.ExtraBold, fontSize = 14.sp, color = Olimpos.Cream)
                    Text("Pedí una rutina nueva o una sesión 1 a 1", fontSize = 12.sp, color = Olimpos.Muted)
                }
                Text("→", color = Olimpos.Gold, fontWeight = FontWeight.Black, fontSize = 18.sp)
            }
        }
    }
}

/** Estado vacío de Entrenar: todavía ningún entrenador armó una rutina real
 *  para este socio (antes acá se mostraba siempre la misma rutina fija,
 *  "Empuje pesado", para cualquiera que abriera la app — ver
 *  cargarRutinaAsignada). */
@Composable
private fun SinRutinaAsignada(onActualizar: () -> Unit) {
    var mostrarEntrenador by remember { mutableStateOf(false) }
    if (mostrarEntrenador) {
        EntrenadorScreen(onVolver = { mostrarEntrenador = false })
        return
    }

    Column(
        Modifier
            .fillMaxSize()
            .statusBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(top = 14.dp, bottom = 26.dp)
    ) {
        Eyebrow("Entrenar")
        Spacer(Modifier.height(30.dp))
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
            Text("🏋️", fontSize = 44.sp)
            Spacer(Modifier.height(14.dp))
            Text(
                "Todavía no tenés una rutina asignada", fontSize = 17.sp, fontWeight = FontWeight.Black,
                color = Olimpos.Cream, textAlign = TextAlign.Center
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "Pedile a tu entrenador que te arme una desde el sistema del gimnasio — en cuanto la guarde, la vas a ver acá.",
                fontSize = 12.5.sp, color = Olimpos.Muted, textAlign = TextAlign.Center, lineHeight = 17.sp
            )
        }
        Spacer(Modifier.height(24.dp))
        BotonSecundario("🔄 Ya me la asignaron, actualizar") { onActualizar() }
        Spacer(Modifier.height(20.dp))
        TarjetaOro(
            Modifier
                .fillMaxWidth()
                .clickable { mostrarEntrenador = true }
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconoCuadrado("🧑‍🏫")
                Spacer(Modifier.width(13.dp))
                Column(Modifier.weight(1f)) {
                    Text("Contactar y reservar sesión", fontWeight = FontWeight.ExtraBold, fontSize = 14.sp, color = Olimpos.Cream)
                    Text("Pedí tu rutina o una sesión 1 a 1", fontSize = 12.sp, color = Olimpos.Muted)
                }
                Text("→", color = Olimpos.Gold, fontWeight = FontWeight.Black, fontSize = 18.sp)
            }
        }
    }
}

/** Botón "Técnica" de un ejercicio de la rutina: busca el ejercicio real en
 *  el catálogo (por id, o por nombre si viene de una rutina vieja sin id
 *  guardado) y reusa la misma pantalla de detalle que la Galería —
 *  descripción y zonas musculares reales, nunca algo que el entrenador
 *  tenga que tipear a mano. Antes esto leía de DETALLES_EJERCICIOS, un
 *  mapa fijo con 6 ejercicios de ejemplo que no tenía forma de conocer un
 *  ejercicio real armado desde Asignación de Rutinas. */
@Composable
private fun DetalleTecnicaRutina(ejercicio: EjercicioRutina, onVolver: () -> Unit) {
    val catalogo = DatosRemotos.ejercicios ?: emptyList()
    val real = catalogo.firstOrNull { it.id == ejercicio.ejercicioId }
        ?: catalogo.firstOrNull { it.nombre == ejercicio.nombre }

    if (real != null) {
        EjercicioCatalogoDetalleScreen(real, onVolver)
        return
    }
    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver(ejercicio.nombre, "Técnica y detalle del ejercicio", onVolver)
        Text(
            "Todavía no hay detalle cargado para este ejercicio en la Galería.",
            fontSize = 13.sp, color = Olimpos.Muted, modifier = Modifier.padding(horizontal = 20.dp)
        )
    }
}

/** El cronómetro vive en su propio composable a propósito: es el único que
 *  lee el contador de segundos, así el tick de cada segundo recompone este
 *  Text y nada más. Antes el valor se leía en el cuerpo de [EntrenarScreen],
 *  y eso hacía que TODA la pantalla (las 6 tarjetas, el Ghost Mode, los
 *  botones) se recompusiera una vez por segundo, peleándole frames al scroll. */
@Composable
private fun CronometroSesion() {
    var segundos by remember { mutableIntStateOf(0) }
    LaunchedEffect(Unit) {
        while (true) {
            delay(1000)
            segundos++
        }
    }
    Text(
        "%02d:%02d:%02d".format(segundos / 3600, (segundos / 60) % 60, segundos % 60),
        fontSize = 12.5.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.GoldLight
    )
}

@Composable
private fun TarjetaEjercicioRutina(
    ejercicio: EjercicioRutina,
    pesoActual: Float,
    onPeso: (Float) -> Unit,
    repsActual: Int,
    onReps: (Int) -> Unit,
    seriesHechas: List<SerieHecha>,
    onRegistrarSerie: () -> Unit,
    onTecnica: () -> Unit,
    modifier: Modifier = Modifier
) {
    val detalle = DETALLES_EJERCICIOS[ejercicio.nombre]
    val completo = seriesHechas.size >= ejercicio.seriesObjetivo

    TarjetaOro(modifier.fillMaxWidth()) {
        Text(ejercicio.nombre, fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, color = Olimpos.Cream)
        Text(
            "${ejercicio.seriesObjetivo} x ${detalle?.reps ?: "-"}" +
                (detalle?.let { " · descanso ${Math.round(it.descansoSeg / 60f).coerceAtLeast(1)}min" } ?: ""),
            fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted
        )

        Spacer(Modifier.height(10.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Peso", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted)
            Spacer(Modifier.weight(1f))
            BotonPasoPeso("－", habilitado = pesoActual > 0f, onClick = { onPeso((pesoActual - PASO_KG).coerceAtLeast(0f)) })
            CampoPesoCompacto(
                valor = pesoActual, onValor = onPeso, prefijoMas = ejercicio.esPesoCorporal,
                modifier = Modifier.padding(horizontal = 6.dp)
            )
            BotonPasoPeso("＋", habilitado = true, onClick = { onPeso(pesoActual + PASO_KG) })
        }
        Spacer(Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Repeticiones", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted)
            Spacer(Modifier.weight(1f))
            BotonPasoPeso("－", habilitado = repsActual > 1, onClick = { onReps((repsActual - 1).coerceAtLeast(1)) })
            CampoRepsCompacto(valor = repsActual, onValor = onReps, modifier = Modifier.padding(horizontal = 6.dp))
            BotonPasoPeso("＋", habilitado = true, onClick = { onReps(repsActual + 1) })
        }

        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            repeat(ejercicio.seriesObjetivo) { i ->
                val hecha = i < seriesHechas.size
                Box(
                    Modifier
                        .weight(1f)
                        .height(38.dp)
                        .clip(RoundedCornerShape(10.dp))
                        .background(if (hecha) Olimpos.Gold.copy(alpha = 0.16f) else Olimpos.Card)
                        .border(
                            1.5.dp,
                            if (hecha) Olimpos.Gold else Olimpos.Line,
                            RoundedCornerShape(10.dp)
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        if (hecha) "${formatoKg(seriesHechas[i].pesoKg)}×${seriesHechas[i].reps}" else "S${i + 1}",
                        fontSize = 10.sp, fontWeight = FontWeight.ExtraBold,
                        color = if (hecha) Olimpos.GoldLight else Olimpos.Muted
                    )
                }
            }
        }

        Spacer(Modifier.height(10.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            if (completo) {
                Box(
                    Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(16.dp))
                        .background(Olimpos.Green.copy(alpha = 0.14f))
                        .border(1.dp, Olimpos.Green.copy(alpha = 0.4f), RoundedCornerShape(16.dp))
                        .padding(vertical = 13.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text("✓ Series completas", fontSize = 13.sp, fontWeight = FontWeight.Black, color = Olimpos.Green)
                }
            } else {
                BotonPrincipal("Registrar serie ${seriesHechas.size + 1}", Modifier.weight(1f), onClick = onRegistrarSerie)
            }
            BotonSecundario("Técnica", Modifier.width(90.dp), onClick = onTecnica)
        }
    }
}

@Composable
private fun BotonPasoPeso(simbolo: String, habilitado: Boolean, onClick: () -> Unit) {
    Box(
        Modifier
            .size(30.dp)
            .clip(CircleShape)
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, CircleShape)
            .clickable(enabled = habilitado, onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text(
            simbolo, fontSize = 15.sp, fontWeight = FontWeight.Black,
            color = if (habilitado) Olimpos.GoldLight else Olimpos.Muted
        )
    }
}

/** Badge de peso que también es un campo editable: los botones +/- sirven
 *  para ajustes finos, pero si el peso de hoy es MUY distinto al sugerido
 *  (por ejemplo cambiaste de ejercicio o de plan), tocar el número y
 *  escribirlo directo es mucho más rápido que tocar +/- muchas veces. */
@Composable
private fun CampoPesoCompacto(
    valor: Float,
    onValor: (Float) -> Unit,
    prefijoMas: Boolean,
    modifier: Modifier = Modifier
) {
    var enfocado by remember { mutableStateOf(false) }
    var texto by remember { mutableStateOf(formatoKg(valor)) }
    LaunchedEffect(valor) {
        if (!enfocado) texto = formatoKg(valor)
    }

    Row(
        modifier
            .clip(RoundedCornerShape(10.dp))
            .background(Olimpos.GoldSoft)
            .border(1.dp, Olimpos.Gold.copy(alpha = if (enfocado) 0.7f else 0.3f), RoundedCornerShape(10.dp))
            .padding(horizontal = 10.dp, vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        if (prefijoMas) {
            Text("+", fontSize = 12.5.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldLight)
        }
        BasicTextField(
            value = texto,
            onValueChange = { nuevo ->
                texto = nuevo
                nuevo.replace(',', '.').toFloatOrNull()?.let { if (it >= 0f) onValor(it) }
            },
            modifier = Modifier
                .width(38.dp)
                .onFocusChanged { estado ->
                    enfocado = estado.isFocused
                    if (!estado.isFocused) texto = formatoKg(valor)
                },
            singleLine = true,
            textStyle = TextStyle(
                fontSize = 12.5.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldLight,
                textAlign = TextAlign.Center
            ),
            cursorBrush = SolidColor(Olimpos.Gold),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal)
        )
        Text(" kg", fontSize = 12.5.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldLight)
    }
}

/** Igual que [CampoPesoCompacto] pero para un entero (repeticiones) — sin
 *  decimales ni sufijo de unidad. */
@Composable
private fun CampoRepsCompacto(valor: Int, onValor: (Int) -> Unit, modifier: Modifier = Modifier) {
    var enfocado by remember { mutableStateOf(false) }
    var texto by remember { mutableStateOf(valor.toString()) }
    LaunchedEffect(valor) {
        if (!enfocado) texto = valor.toString()
    }

    Row(
        modifier
            .clip(RoundedCornerShape(10.dp))
            .background(Olimpos.GoldSoft)
            .border(1.dp, Olimpos.Gold.copy(alpha = if (enfocado) 0.7f else 0.3f), RoundedCornerShape(10.dp))
            .padding(horizontal = 10.dp, vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        BasicTextField(
            value = texto,
            onValueChange = { nuevo ->
                texto = nuevo
                nuevo.toIntOrNull()?.let { if (it >= 1) onValor(it) }
            },
            modifier = Modifier
                .width(24.dp)
                .onFocusChanged { estado ->
                    enfocado = estado.isFocused
                    if (!estado.isFocused) texto = valor.toString()
                },
            singleLine = true,
            textStyle = TextStyle(
                fontSize = 12.5.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldLight,
                textAlign = TextAlign.Center
            ),
            cursorBrush = SolidColor(Olimpos.Gold),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
        )
        Text(" reps", fontSize = 12.5.sp, fontWeight = FontWeight.Black, color = Olimpos.GoldLight)
    }
}

/** Ghost Mode real: compara la mejor serie de HOY (si ya se registró
 *  alguna de este ejercicio) contra la mejor serie de la sesión anterior
 *  en Firestore — ver [ghostModeDeEjercicio]. Antes esto comparaba contra
 *  un ejemplo fijo ("80kg × 8"), lo que producía mensajes contradictorios
 *  ("superaste" con una diferencia negativa); ahora, sin sesión anterior
 *  real con la que comparar, se avisa eso en vez de inventar un resultado. */
@Composable
private fun TarjetaGhostMode(ejercicio: String, seriesHoy: List<SerieHecha>, historial: List<SerieEntrenamiento>) {
    val comparacion = remember(seriesHoy.size, historial) { ghostModeDeEjercicio(ejercicio, seriesHoy, historial) }
    TarjetaOro(Modifier.fillMaxWidth()) {
        Text(
            "GHOST MODE · ${ejercicio.uppercase()}", fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold,
            letterSpacing = 1.sp, color = Olimpos.Muted
        )
        Spacer(Modifier.height(12.dp))
        if (comparacion == null) {
            Text(
                if (seriesHoy.isEmpty())
                    "Registrá una serie de $ejercicio para activar la comparación."
                else
                    "Todavía no tenés una sesión anterior de $ejercicio para comparar. La próxima vez que lo entrenes, vas a ver acá cuánto superás hoy.",
                fontSize = 12.sp, color = Olimpos.Muted, lineHeight = 16.sp
            )
            return@TarjetaOro
        }
        val color = if (comparacion.supera) Olimpos.Green else Olimpos.Red
        Text(
            "${if (comparacion.supera) "Superaste" else "Todavía no superaste"} tu sesión anterior " +
                "(${formatoKg(comparacion.pesoAnterior)}kg × ${comparacion.repsAnterior}) por " +
                "${formatoKg(kotlin.math.abs(comparacion.diferenciaKg))}kg de 1RM estimado, con " +
                "${formatoKg(comparacion.pesoHoy)}kg × ${comparacion.repsHoy} hoy.",
            fontSize = 12.sp, fontWeight = FontWeight.Bold, color = color, lineHeight = 16.sp
        )
    }
}
