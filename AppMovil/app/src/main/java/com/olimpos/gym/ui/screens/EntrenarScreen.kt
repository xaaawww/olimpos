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
import com.olimpos.gym.data.EjercicioRutina
import com.olimpos.gym.data.GHOST_MODE_EJEMPLO
import com.olimpos.gym.data.RUTINA_HOY
import com.olimpos.gym.data.RutinaDelDia
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.delay

private const val PASO_KG = 2.5f

private fun formatoKg(kg: Float): String = "%.1f".format(kg).replace('.', ',')

@Composable
fun EntrenarScreen() {
    var detalleEjercicio by remember { mutableStateOf<String?>(null) }
    var mostrarEntrenador by remember { mutableStateOf(false) }

    if (detalleEjercicio != null) {
        EjercicioDetalleScreen(detalleEjercicio!!, onVolver = { detalleEjercicio = null })
        return
    }
    if (mostrarEntrenador) {
        EntrenadorScreen(onVolver = { mostrarEntrenador = false })
        return
    }

    val rutina = RUTINA_HOY

    // Peso de trabajo actual por ejercicio (ajustable con +/-) y las series
    // ya registradas (con el peso que tenían en el momento de registrarlas)
    // — todo en memoria mientras dura la sesión, ver aviso al pie.
    val pesos = remember { mutableStateListOf(*rutina.ejercicios.map { it.pesoBaseKg }.toTypedArray()) }
    val seriesHechas = remember { rutina.ejercicios.map { mutableStateListOf<Float>() } }
    val totalObjetivo = remember { rutina.ejercicios.sumOf { it.seriesObjetivo } }
    val totalHechas = seriesHechas.sumOf { it.size }

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
                seriesHechas = seriesHechas[i],
                onRegistrarSerie = { seriesHechas[i].add(pesos[i]) },
                onTecnica = { detalleEjercicio = ej.nombre },
                modifier = Modifier.padding(bottom = 10.dp)
            )
        }

        SeccionLabel("Ghost Mode")
        TarjetaGhostMode(pesos, rutina)

        Spacer(Modifier.height(6.dp))
        BotonPrincipal("Terminar y enviar a validación") {
            // Sin backend de sesiones todavía: cada serie ya se guarda en
            // Firestore individualmente al tocar "Registrar serie" (ver
            // guardarMarcaEnFirebase en MarcasScreen) — este botón es el
            // cierre visual de la sesión, no dispara un envío aparte.
        }
        Text(
            "Las series quedan registradas al instante; tu entrenador valida la marca cuando termine la sesión.",
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
    seriesHechas: List<Float>,
    onRegistrarSerie: () -> Unit,
    onTecnica: () -> Unit,
    modifier: Modifier = Modifier
) {
    val detalle = DETALLES_EJERCICIOS[ejercicio.nombre]
    val completo = seriesHechas.size >= ejercicio.seriesObjetivo

    TarjetaOro(modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(ejercicio.nombre, fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, color = Olimpos.Cream)
                Text(
                    "${ejercicio.seriesObjetivo} x ${detalle?.reps ?: "-"}" +
                        (detalle?.let { " · descanso ${Math.round(it.descansoSeg / 60f).coerceAtLeast(1)}min" } ?: ""),
                    fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted
                )
            }
            BotonPasoPeso("－", habilitado = pesoActual > 0f, onClick = { onPeso((pesoActual - PASO_KG).coerceAtLeast(0f)) })
            CampoPesoCompacto(
                valor = pesoActual, onValor = onPeso, prefijoMas = ejercicio.esPesoCorporal,
                modifier = Modifier.padding(horizontal = 6.dp)
            )
            BotonPasoPeso("＋", habilitado = true, onClick = { onPeso(pesoActual + PASO_KG) })
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
                        if (hecha) formatoKg(seriesHechas[i]) else "S${i + 1}",
                        fontSize = 11.sp, fontWeight = FontWeight.ExtraBold,
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

/** Ghost Mode: compara la última marca validada de un ejercicio contra el
 *  peso que se está cargando hoy en la rutina — antes vivía en "Mis
 *  marcas", ahora está acá para verlo mientras se entrena, no después. El
 *  peso de "Hoy" es real (el mismo que ajustan los botones +/- de la
 *  tarjeta); las repeticiones siguen siendo el dato de ejemplo de
 *  [GHOST_MODE_EJEMPLO], porque una serie acá solo guarda el peso usado. */
@Composable
private fun TarjetaGhostMode(pesos: List<Float>, rutina: RutinaDelDia) {
    val g = GHOST_MODE_EJEMPLO
    val indice = rutina.ejercicios.indexOfFirst { it.nombre == g.ejercicio }
    val pesoHoy = if (indice >= 0) pesos[indice] else g.pesoActual
    val repsHoy = g.repsActual

    val volumenAnterior = g.pesoAnterior * g.repsAnterior
    val volumenHoy = pesoHoy * repsHoy
    val diferenciaKg = pesoHoy - g.pesoAnterior
    val supera = volumenHoy > volumenAnterior

    // Misma escala para las dos barras (con un 15% de margen arriba del
    // mayor volumen) para que el largo de cada una sea comparable a ojo.
    val escala = maxOf(volumenAnterior, volumenHoy) * 1.15f

    TarjetaOro(Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                "GHOST MODE · ${g.ejercicio.uppercase()}", fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold,
                letterSpacing = 1.sp, color = Olimpos.Muted, modifier = Modifier.weight(1f)
            )
            ChipOro("ACTIVO")
        }
        Spacer(Modifier.height(12.dp))
        Text("Última marca validada", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted)
        Spacer(Modifier.height(4.dp))
        BarraProgreso(
            fraccion = volumenAnterior / escala, alto = 10, divisiones = 5,
            colores = listOf(Olimpos.Muted.copy(alpha = 0.55f), Olimpos.Muted, Olimpos.GrayLight)
        )
        Text(
            "${formatoKg(g.pesoAnterior)}kg × ${g.repsAnterior}", fontSize = 11.5.sp,
            fontWeight = FontWeight.Bold, color = Olimpos.Cream, modifier = Modifier.padding(top = 3.dp)
        )
        Spacer(Modifier.height(10.dp))
        Text("Hoy", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted)
        Spacer(Modifier.height(4.dp))
        BarraProgreso(fraccion = volumenHoy / escala, alto = 10, divisiones = 5)
        Text(
            "${formatoKg(pesoHoy)}kg × $repsHoy", fontSize = 11.5.sp,
            fontWeight = FontWeight.Bold, color = Olimpos.GoldLight, modifier = Modifier.padding(top = 3.dp)
        )
        Spacer(Modifier.height(10.dp))
        Text(
            if (supera) "Superaste a tu fantasma por ${formatoKg(diferenciaKg)}kg 🔥 — quedará a revisión de tu entrenador cuando valide el PR."
            else "Todavía no superaste tu marca anterior — te faltan ${formatoKg(-diferenciaKg)}kg para empatarla.",
            fontSize = 11.5.sp, fontWeight = FontWeight.Bold,
            color = if (supera) Olimpos.Green else Olimpos.Muted, lineHeight = 15.sp
        )
    }
}
