package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import android.content.Context
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.IntOffset
import kotlin.math.roundToInt
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.OutlinedTextFieldDefaults
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
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.MensajeArgos
import com.olimpos.gym.data.PLANES_CON_ARGOS
import com.olimpos.gym.data.planIncluyeArgos
import com.olimpos.gym.data.preguntarArgos
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

/** Chat simple con Argos — el historial vive solo en memoria de esta
 *  pantalla (se pierde al volver), a propósito: es una charla puntual, no
 *  algo que haga falta guardar. Nunca ejecuta ninguna acción, solo
 *  responde texto (ver ArgosRepository.kt/ArgosWorker).
 *
 *  Argos es un beneficio de pago (planes Oro y Platino, ver
 *  [planIncluyeArgos]): sin uno de esos planes se muestra el bloqueo en vez
 *  del chat. [onVerPlanes] lleva a "Mi membresía". */
@Composable
fun ArgosScreen(onVolver: () -> Unit, onVerPlanes: () -> Unit) {
    val membresia = DatosRemotos.membresia
    var actualizandoPlan by remember { mutableStateOf(true) }
    val scopePlan = rememberCoroutineScope()
    // Al abrir Argos se vuelve a pedir la membresía: si recepción acaba de
    // activarle el plan con la app abierta, se desbloquea solo.
    LaunchedEffect(Unit) {
        DatosRemotos.recargarMembresia()
        actualizandoPlan = false
    }
    if (!planIncluyeArgos(membresia?.plan)) {
        ArgosBloqueado(
            planActual = membresia?.plan,
            actualizando = actualizandoPlan,
            onVolver = onVolver,
            onVerPlanes = onVerPlanes,
            onActualizar = {
                actualizandoPlan = true
                scopePlan.launch {
                    DatosRemotos.recargarMembresia()
                    actualizandoPlan = false
                }
            }
        )
        return
    }

    val scope = rememberCoroutineScope()
    var mensajes by remember { mutableStateOf(listOf<MensajeArgos>()) }
    var textoActual by remember { mutableStateOf("") }
    var enviando by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val estadoLista = rememberLazyListState()

    fun enviar() {
        val pregunta = textoActual.trim()
        if (pregunta.isEmpty() || enviando) return
        val historialPrevio = mensajes
        mensajes = mensajes + MensajeArgos("user", pregunta)
        textoActual = ""
        error = null
        enviando = true
        scope.launch {
            try {
                val respuesta = preguntarArgos(pregunta, historialPrevio)
                mensajes = mensajes + MensajeArgos("assistant", respuesta)
            } catch (e: Exception) {
                error = e.message ?: "No se pudo conectar con Argos."
            }
            enviando = false
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .background(Brush.linearGradient(listOf(Olimpos.FondoA, Olimpos.FondoB, Olimpos.FondoC)))
            // Consume cualquier toque en las zonas "vacías" de esta pantalla
            // — sin esto, un toque ahí pasaba de largo hacia la pestaña de
            // abajo (Inicio/Entrenar/...) que sigue compuesta debajo, aunque
            // tapada visualmente por este overlay de pantalla completa.
            .clickable(interactionSource = remember { MutableInteractionSource() }, indication = null) {}
    ) {
        EncabezadoVolver("🐕 Argos", "Tu asistente de IA en OlimpΩs", onVolver)

        LazyColumn(
            state = estadoLista,
            modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 12.dp)
        ) {
            if (mensajes.isEmpty()) {
                item {
                    Text(
                        "Preguntale a Argos sobre horarios, membresías, clases, máquinas, el catálogo de " +
                            "comidas, tu propio progreso o consejos generales de entrenamiento.",
                        fontSize = 12.5.sp, color = Olimpos.Muted
                    )
                }
            }
            items(mensajes) { m -> BurbujaArgos(m) }
            if (enviando) item { BurbujaArgos(MensajeArgos("assistant", "Escribiendo…"), atenuado = true) }
        }

        error?.let {
            Text(
                it, fontSize = 11.5.sp, color = Olimpos.Red,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
            )
        }

        Row(
            Modifier
                .fillMaxWidth()
                .imePadding()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            androidx.compose.material3.OutlinedTextField(
                value = textoActual,
                onValueChange = { textoActual = it },
                placeholder = { Text("Preguntale algo a Argos...", color = Olimpos.Muted, fontSize = 13.sp) },
                singleLine = false,
                maxLines = 4,
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(16.dp),
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 13.5.sp, color = Olimpos.Cream),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Olimpos.Cream, unfocusedTextColor = Olimpos.Cream,
                    focusedBorderColor = Olimpos.Gold, unfocusedBorderColor = Olimpos.Line,
                    cursorColor = Olimpos.Gold,
                    focusedContainerColor = Olimpos.Card, unfocusedContainerColor = Olimpos.Card
                )
            )
            Box(
                Modifier
                    .clip(RoundedCornerShape(14.dp))
                    .background(Olimpos.Gold)
                    .clickable(enabled = !enviando) { enviar() }
                    .padding(horizontal = 16.dp, vertical = 14.dp)
            ) {
                Text(if (enviando) "…" else "➤", fontWeight = FontWeight.Black, fontSize = 15.sp, color = Olimpos.Dark)
            }
        }
    }
}

@Composable
private fun BurbujaArgos(m: MensajeArgos, atenuado: Boolean = false) {
    val esUsuario = m.rol == "user"
    val color = if (esUsuario) Olimpos.Dark else Olimpos.Cream
    Row(
        Modifier.fillMaxWidth().alpha(if (atenuado) 0.6f else 1f),
        horizontalArrangement = if (esUsuario) Arrangement.End else Arrangement.Start
    ) {
        Box(
            Modifier
                .widthIn(max = 280.dp)
                .clip(RoundedCornerShape(14.dp))
                .background(if (esUsuario) Olimpos.Gold else Olimpos.Card)
                .let { if (!esUsuario) it.border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp)) else it }
                .padding(horizontal = 13.dp, vertical = 10.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
                // Argos suele escribir con **negrita** y listas con "- " —
                // esto lo interpreta en vez de mostrar los asteriscos
                // sueltos, para que la burbuja no se vea rara.
                m.texto.split("\n").forEach { linea ->
                    val recortada = linea.trimStart()
                    val esBullet = recortada.startsWith("- ") || recortada.startsWith("* ")
                    val contenido = if (esBullet) recortada.removePrefix("- ").removePrefix("* ") else linea
                    Row {
                        if (esBullet) {
                            Text("•  ", fontSize = 13.sp, fontWeight = FontWeight.Black, color = color)
                        }
                        Text(
                            aTextoConNegrita(contenido, color), fontSize = 13.sp,
                            fontWeight = FontWeight.Medium, color = color
                        )
                    }
                }
            }
        }
    }
}

/** Convierte "**palabra**" en negrita real (Compose no interpreta markdown
 *  solo) — Argos, el modelo de lenguaje, escribe así seguido. */
private fun aTextoConNegrita(texto: String, color: androidx.compose.ui.graphics.Color) = buildAnnotatedString {
    val regex = Regex("\\*\\*(.+?)\\*\\*")
    var ultimo = 0
    for (match in regex.findAll(texto)) {
        append(texto.substring(ultimo, match.range.first))
        pushStyle(SpanStyle(fontWeight = FontWeight.Black, color = color))
        append(match.groupValues[1])
        pop()
        ultimo = match.range.last + 1
    }
    append(texto.substring(ultimo))
}

/** Pantalla que reemplaza al chat cuando el plan del socio no incluye Argos. */
@Composable
private fun ArgosBloqueado(
    planActual: String?,
    actualizando: Boolean,
    onVolver: () -> Unit,
    onVerPlanes: () -> Unit,
    onActualizar: () -> Unit
) {
    Column(
        Modifier
            .fillMaxSize()
            .background(Brush.linearGradient(listOf(Olimpos.FondoA, Olimpos.FondoB, Olimpos.FondoC)))
            // Mismo motivo que en el chat: no dejar pasar toques a la pestaña de abajo.
            .clickable(interactionSource = remember { MutableInteractionSource() }, indication = null) {}
    ) {
        EncabezadoVolver("🐕 Argos", "Tu asistente de IA en OlimpΩs", onVolver)

        Column(
            Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(top = 12.dp, bottom = 26.dp)
        ) {
            TarjetaOro(Modifier.fillMaxWidth()) {
                Text("🔒", fontSize = 34.sp)
                Spacer(Modifier.height(8.dp))
                Text(
                    "Argos es parte del plan ${PLANES_CON_ARGOS.first()}",
                    fontSize = 19.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream
                )
                Text(
                    "Incluido en los planes ${PLANES_CON_ARGOS.joinToString(" y ")}.",
                    fontSize = 12.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 4.dp, bottom = 14.dp)
                )
                listOf(
                    "Respuestas sobre horarios, clases, membresías y el catálogo de comidas",
                    "Datos de tu propio progreso, tu racha y tus reservas",
                    "Consejos de entrenamiento y hábitos saludables, 24/7"
                ).forEach { beneficio ->
                    Row(Modifier.padding(bottom = 6.dp)) {
                        Text("✓ ", fontSize = 12.5.sp, color = Olimpos.Gold, fontWeight = FontWeight.Black)
                        Text(beneficio, fontSize = 12.5.sp, color = Olimpos.Muted)
                    }
                }
            }

            Spacer(Modifier.height(14.dp))
            Text(
                if (planActual != null) "Tu plan actual es $planActual y no incluye a Argos."
                else "Todavía no tenés ningún plan asignado.",
                fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Olimpos.GoldLight
            )
            Text(
                "Pedile a recepción que te active el plan ${PLANES_CON_ARGOS.first()} (o Platino) y Argos se desbloquea acá mismo.",
                fontSize = 11.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 4.dp)
            )

            Spacer(Modifier.height(20.dp))
            BotonPrincipal("Ver planes de membresía") { onVerPlanes() }
            Spacer(Modifier.height(10.dp))
            BotonSecundario(if (actualizando) "Actualizando…" else "Ya me lo activaron — actualizar") {
                if (!actualizando) onActualizar()
            }
        }
    }
}

/** La burbuja de Argos, arrastrable: se puede llevar a cualquier lugar de la
 *  pantalla para que no tape información (un botón, un número, una comida).
 *  Arranca en su esquina de siempre (abajo a la derecha, por encima de la
 *  barra de pestañas) y de ahí se mide cuánto se corrió — así, si la pantalla
 *  cambia de tamaño (rotación), la burbuja queda en un lugar razonable. Los
 *  límites la mantienen siempre entera adentro de la pantalla: no se puede
 *  "perder" fuera del borde. Un toque corto sigue abriendo el chat; solo un
 *  arrastre la mueve. Ocupa toda la pantalla pero no intercepta toques:
 *  solo la burbuja en sí reacciona.
 *
 *  La posición se guarda en SharedPreferences (ver [leerCorrimientoGuardado]/
 *  [guardarCorrimiento]) al soltar el dedo, no en cada píxel arrastrado, así
 *  que sobrevive a cerrar la app del todo y no solo a girar el celular (eso
 *  ya lo cubre rememberSaveable por su cuenta). Es una preferencia del
 *  dispositivo, no de la cuenta — no hace falta distinguir por socio. */
@Composable
fun ArgosBurbujaMovil(visible: Boolean, bloqueado: Boolean, onClick: () -> Unit) {
    val density = LocalDensity.current
    val context = LocalContext.current
    // Corrimiento respecto de la esquina inferior derecha, en píxeles
    // (negativo = hacia la izquierda / hacia arriba). rememberSaveable para
    // que sobreviva a girar el celular; el valor inicial sale de la última
    // posición guardada (si la había) en vez de siempre 0.
    var corrimientoX by rememberSaveable { mutableStateOf(leerCorrimientoGuardado(context).first) }
    var corrimientoY by rememberSaveable { mutableStateOf(leerCorrimientoGuardado(context).second) }

    // statusBarsPadding + navigationBarsPadding: los límites se calculan sobre
    // la zona realmente usable, sin la barra de estado ni la de navegación.
    BoxWithConstraints(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()) {
        val tamano = with(density) { TAMANO_BURBUJA.toPx() }
        val margenDerecho = with(density) { MARGEN_DERECHO_BURBUJA.toPx() }
        val margenInferior = with(density) { MARGEN_INFERIOR_BURBUJA.toPx() }
        val respiro = with(density) { 6.dp.toPx() }  // separación mínima con el borde

        // Cuánto puede correrse hacia cada lado a partir de la posición inicial.
        val minX = -(constraints.maxWidth - tamano - margenDerecho - respiro)
        val maxX = margenDerecho - respiro
        val minY = -(constraints.maxHeight - tamano - margenInferior - respiro)
        val maxY = margenInferior - respiro

        androidx.compose.animation.AnimatedVisibility(
            visible = visible,
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(end = MARGEN_DERECHO_BURBUJA, bottom = MARGEN_INFERIOR_BURBUJA),
            enter = fadeIn(), exit = fadeOut()
        ) {
            ArgosBurbujaFlotante(
                bloqueado = bloqueado,
                onClick = onClick,
                modifier = Modifier
                    .offset { IntOffset(corrimientoX.roundToInt(), corrimientoY.roundToInt()) }
                    .pointerInput(minX, maxX, minY, maxY) {
                        detectDragGestures(
                            onDragEnd = { guardarCorrimiento(context, corrimientoX, corrimientoY) }
                        ) { cambio, arrastre ->
                            cambio.consume()
                            corrimientoX = (corrimientoX + arrastre.x).coerceIn(minX, maxX)
                            corrimientoY = (corrimientoY + arrastre.y).coerceIn(minY, maxY)
                        }
                    }
            )
        }
    }
}

// Mismo archivo de SharedPreferences que usa el objetivo de Arena/Configuración
// (ver PREFS_ARENA en GamificacionData.kt) — no hace falta uno propio para
// dos claves sueltas.
private const val PREFS_BURBUJA = "olimpos_prefs"
private const val KEY_BURBUJA_X = "burbuja_argos_x"
private const val KEY_BURBUJA_Y = "burbuja_argos_y"

private fun leerCorrimientoGuardado(context: Context): Pair<Float, Float> {
    val prefs = context.getSharedPreferences(PREFS_BURBUJA, Context.MODE_PRIVATE)
    return prefs.getFloat(KEY_BURBUJA_X, 0f) to prefs.getFloat(KEY_BURBUJA_Y, 0f)
}

private fun guardarCorrimiento(context: Context, x: Float, y: Float) {
    context.getSharedPreferences(PREFS_BURBUJA, Context.MODE_PRIVATE).edit()
        .putFloat(KEY_BURBUJA_X, x)
        .putFloat(KEY_BURBUJA_Y, y)
        .apply()
}

private val TAMANO_BURBUJA = 58.dp
private val MARGEN_DERECHO_BURBUJA = 16.dp
// Alto de la barra de pestañas (66.dp) + aire, para no tapar "Perfil" de arranque.
private val MARGEN_INFERIOR_BURBUJA = 82.dp

/** Burbuja flotante siempre visible (cualquier pestaña) para abrir el chat
 *  de Argos sin tener que ir hasta Perfil. Si el plan del socio no lo
 *  incluye, lleva un candado y al tocarla se ve el bloqueo. Para poder
 *  moverla ver [ArgosBurbujaMovil], que la envuelve. */
@Composable
fun ArgosBurbujaFlotante(bloqueado: Boolean = false, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Box(
        modifier
            .size(TAMANO_BURBUJA)
            .shadow(8.dp, CircleShape)
            .clip(CircleShape)
            .background(Brush.linearGradient(listOf(Olimpos.GoldLight, Olimpos.GoldDark)))
            .border(1.5.dp, Olimpos.Gold, CircleShape)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text("🐕", fontSize = 26.sp)
        if (bloqueado) {
            Text("🔒", fontSize = 13.sp, modifier = Modifier.align(Alignment.TopEnd).padding(top = 7.dp, end = 7.dp))
        }
    }
}
