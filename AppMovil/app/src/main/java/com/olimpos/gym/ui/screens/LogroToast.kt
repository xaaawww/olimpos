package com.olimpos.gym.ui.screens

import android.content.Context
import android.media.AudioManager
import android.media.ToneGenerator
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.Logro
import com.olimpos.gym.data.calcularLogros
import com.olimpos.gym.data.construirContextoLogros
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.leerNotificacionesLogrosActivas
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.delay

/** Cola de logros recién desbloqueados esperando a mostrarse como toast, uno
 *  a la vez — igual patrón que [DatosRemotos]: un objeto con estado
 *  reactivo, sin necesitar un ViewModel para algo tan chico. */
object LogrosToastState {
    var notificacionesActivas by mutableStateOf(true)
    private val cola = mutableStateListOf<Logro>()
    var actual by mutableStateOf<Logro?>(null); private set

    fun encolar(logro: Logro) {
        if (!notificacionesActivas) return
        if (actual?.nombre == logro.nombre || cola.any { it.nombre == logro.nombre }) return
        if (actual == null) actual = logro else cola.add(logro)
    }

    /** Descarta el toast actual, pero solo si [nombre] sigue siendo el que
     *  está mostrándose — el auto-dismiss y el swipe pueden llegar a
     *  dispararse los dos para el mismo toast, y sin esta guarda el segundo
     *  saltearía de más el siguiente de la cola. */
    fun descartar(nombre: String) {
        if (actual?.nombre == nombre) {
            actual = cola.removeFirstOrNull()
        }
    }
}

/** Sin sonido propio (este proyecto no tiene ningún asset de audio ni
 *  Storage para bajarlo) — un ToneGenerator arma un "ding-ding" ascendente
 *  corto con los tonos del sistema, sin necesitar ningún archivo. Respeta
 *  silencio/vibrador: no sea que suene si el socio puso el celular en
 *  silencio. */
private suspend fun sonarLogroDesbloqueado(contexto: Context) {
    try {
        val audioManager = contexto.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
        if (audioManager?.ringerMode != AudioManager.RINGER_MODE_NORMAL) return
        val tono = ToneGenerator(AudioManager.STREAM_NOTIFICATION, 85)
        tono.startTone(ToneGenerator.TONE_PROP_BEEP2, 90)
        delay(100)
        tono.startTone(ToneGenerator.TONE_PROP_ACK, 140)
        delay(160)
        tono.release()
    } catch (e: Exception) {
        // Sin audio disponible (celular sin salida de sonido, etc.) — el
        // toast visual ya cumple igual, no hace falta más que ignorarlo.
    }
}

/** Vive montado toda la sesión (ver MainActivity) y vigila en segundo plano
 *  si algún logro pasó de bloqueado a desbloqueado, para encolar su toast.
 *  Espera a [DatosRemotos.listo] antes de tomar la primera "foto" de qué ya
 *  estaba desbloqueado — si no, los logros que ya tenía de antes irían
 *  apareciendo como "recién conseguidos" a medida que cada carga de
 *  Firestore fuera llegando de a una al abrir la app. */
@Composable
fun ObservadorDeLogros() {
    val contexto = LocalContext.current
    LaunchedEffect(Unit) {
        LogrosToastState.notificacionesActivas = leerNotificacionesLogrosActivas(contexto)
    }

    val ctxLogros = construirContextoLogros(contexto)
    val logros = remember(ctxLogros) { calcularLogros(ctxLogros) }
    var vistos by remember { mutableStateOf<Set<String>?>(null) }

    LaunchedEffect(logros) {
        if (!DatosRemotos.listo) return@LaunchedEffect
        val desbloqueadosAhora = logros.filter { it.desbloqueado }.map { it.nombre }.toSet()
        val anterior = vistos
        if (anterior == null) {
            // Primera vez con datos completos: establece la base sin avisar.
            vistos = desbloqueadosAhora
        } else {
            val nuevos = desbloqueadosAhora - anterior
            logros.filter { it.nombre in nuevos }.forEach { LogrosToastState.encolar(it) }
            vistos = desbloqueadosAhora
        }
    }
}

/** El toast en sí — se monta una sola vez en la raíz de la app (ver
 *  MainActivity) para que aparezca por encima de cualquier pantalla. */
@Composable
fun ToastLogroOverlay() {
    Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
        AnimatedContent(
            targetState = LogrosToastState.actual,
            transitionSpec = {
                (slideInVertically { -it } + fadeIn()) togetherWith (slideOutVertically { -it } + fadeOut())
            },
            label = "toast_logro"
        ) { logro ->
            if (logro != null) TarjetaToastLogro(logro)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TarjetaToastLogro(logro: Logro) {
    val contexto = LocalContext.current
    val estadoSwipe = rememberSwipeToDismissBoxState()

    LaunchedEffect(logro.nombre) {
        sonarLogroDesbloqueado(contexto)
        delay(3200)
        LogrosToastState.descartar(logro.nombre)
    }
    LaunchedEffect(estadoSwipe.currentValue) {
        if (estadoSwipe.currentValue != SwipeToDismissBoxValue.Settled) {
            LogrosToastState.descartar(logro.nombre)
        }
    }

    SwipeToDismissBox(
        state = estadoSwipe,
        backgroundContent = {},
        modifier = Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(horizontal = 14.dp, vertical = 6.dp)
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp))
                // Card/Line (no Dark/Gold fijos) porque son los que cambian
                // junto con Cream/Muted según el tema — con un fondo fijo
                // oscuro y texto que se vuelve oscuro en modo claro quedaba
                // ilegible (letra y marco casi del mismo color).
                .background(Olimpos.Card)
                .border(1.dp, Olimpos.Gold.copy(alpha = 0.45f), RoundedCornerShape(16.dp))
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                Modifier
                    .size(42.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(Olimpos.GoldSoft),
                contentAlignment = Alignment.Center
            ) { Text(logro.emoji, fontSize = 21.sp) }
            Spacer(Modifier.width(11.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    "¡Logro desbloqueado!",
                    fontSize = 10.sp, fontWeight = FontWeight.ExtraBold,
                    color = Olimpos.GoldDark, letterSpacing = 0.6.sp
                )
                Text(logro.nombre, fontSize = 13.5.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
                Text(logro.descripcion, fontSize = 11.sp, color = Olimpos.Muted)
            }
        }
    }
}
