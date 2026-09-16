package com.olimpos.gym

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.firebase.Firebase
import com.google.firebase.auth.auth
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.SocioAuth
import com.olimpos.gym.data.cargarDatosFisicosPropios
import com.olimpos.gym.data.leerObjetivoArena
import com.olimpos.gym.data.guardarObjetivoArena
import com.olimpos.gym.ui.screens.ArenaScreen
import com.olimpos.gym.ui.screens.ArgosBurbujaFlotante
import com.olimpos.gym.ui.screens.ArgosScreen
import com.olimpos.gym.ui.screens.DietaScreen
import com.olimpos.gym.ui.screens.EntrenarScreen
import com.olimpos.gym.ui.screens.HomeScreen
import com.olimpos.gym.ui.screens.LoginScreen
import com.olimpos.gym.ui.screens.ObservadorDeLogros
import com.olimpos.gym.ui.screens.ToastLogroOverlay
import com.olimpos.gym.ui.screens.OnboardingScreen
import com.olimpos.gym.ui.screens.PerfilScreen
import com.olimpos.gym.ui.screens.PlanoScreen
import com.olimpos.gym.ui.theme.Olimpos
import com.olimpos.gym.ui.theme.OlimposTheme
import com.olimpos.gym.ui.theme.ThemeMode
import com.olimpos.gym.ui.theme.guardarThemeMode
import com.olimpos.gym.ui.theme.leerThemeMode

enum class Tab(val label: String, val icon: String) {
    INICIO("Inicio", "🏛️"),
    ENTRENAR("Entrenar", "🏋️"),
    ARENA("Arena", "⚔️"),
    DIETA("Dieta", "🥗"),
    PERFIL("Perfil", "👤")
}

/** Etapa general de la app: verificación (arranque/post-login) →
 *  autenticación → onboarding obligatorio (solo si todavía no cargó sus
 *  datos físicos, ver [cargarDatosFisicosPropios]) → app principal. */
private enum class Etapa { VERIFICANDO, LOGIN, ONBOARDING, APP }

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val contexto = LocalContext.current
            var themeMode by remember { mutableStateOf(leerThemeMode(contexto)) }
            OlimposTheme(modo = themeMode) {
                OlimposApp(
                    themeMode = themeMode,
                    onThemeMode = { nuevo ->
                        themeMode = nuevo
                        guardarThemeMode(contexto, nuevo)
                    }
                )
            }
        }
    }
}

/** Ancho máximo del contenido: en celulares no cambia nada (siempre son más
 *  angostos), pero evita que tarjetas y botones se estiren desproporcionados
 *  en pantallas grandes/tablets — layout adaptativo, no un escalado uniforme. */
private val ANCHO_CONTENIDO_MAX = 480.dp

@Composable
fun OlimposApp(themeMode: ThemeMode, onThemeMode: (ThemeMode) -> Unit) {
    var etapa by remember { mutableStateOf(Etapa.VERIFICANDO) }
    // Se incrementa para forzar una nueva verificación (arranque de la app
    // y cada login exitoso) sin duplicar la lógica en dos lados.
    var verificacion by remember { mutableIntStateOf(0) }

    LaunchedEffect(verificacion) {
        etapa = when {
            Firebase.auth.currentUser == null -> Etapa.LOGIN
            // Sin datos físicos todavía (cuenta recién creada por un
            // empleado) → onboarding obligatorio antes de dejarlo entrar.
            cargarDatosFisicosPropios() == null -> Etapa.ONBOARDING
            else -> Etapa.APP
        }
    }

    Box(
        Modifier
            .fillMaxSize()
            .background(Brush.linearGradient(listOf(Olimpos.FondoA, Olimpos.FondoB, Olimpos.FondoC))),
        contentAlignment = Alignment.TopCenter
    ) {
        Box(Modifier.fillMaxHeight().widthIn(max = ANCHO_CONTENIDO_MAX)) {
            when (etapa) {
                Etapa.VERIFICANDO -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = Olimpos.Gold)
                }
                Etapa.LOGIN -> LoginScreen(onIngresar = { verificacion++ })
                Etapa.ONBOARDING -> OnboardingScreen(onFinalizar = { etapa = Etapa.APP })
                Etapa.APP -> OlimposAppPrincipal(
                    themeMode = themeMode,
                    onThemeMode = onThemeMode,
                    onCerrarSesion = {
                        SocioAuth.cerrarSesion()
                        etapa = Etapa.LOGIN
                    }
                )
            }
        }
    }
}

@Composable
private fun OlimposAppPrincipal(themeMode: ThemeMode, onThemeMode: (ThemeMode) -> Unit, onCerrarSesion: () -> Unit) {
    var tab by remember { mutableStateOf(Tab.INICIO) }
    // El plano vive fuera de la navegación principal: sector aparte
    var mostrarPlano by remember { mutableStateOf(false) }
    // Argos también: burbuja flotante sobre cualquier pestaña, en vez de
    // que haga falta ir hasta Perfil para preguntarle algo.
    var mostrarArgos by remember { mutableStateOf(false) }

    val contexto = LocalContext.current
    var objetivoArena by remember { mutableStateOf(leerObjetivoArena(contexto)) }

    // Precarga marcas/platos/ejercicios/ranking apenas se entra a la app,
    // para que Bodygraph, Dieta y Galería ya tengan los datos reales listos
    // en vez de mostrar el catálogo de ejemplo un instante y reemplazarlo.
    LaunchedEffect(Unit) { DatosRemotos.precargar() }

    // Vigila en segundo plano si se desbloqueó un logro nuevo, toda la
    // sesión — no solo cuando la pantalla de Logros está abierta.
    ObservadorDeLogros()

    Box(Modifier.fillMaxSize()) {
        Scaffold(
            containerColor = androidx.compose.ui.graphics.Color.Transparent,
            contentWindowInsets = WindowInsets(0),
            bottomBar = { BarraInferior(tab) { tab = it } }
        ) { pad ->
            AnimatedContent(
                targetState = tab,
                modifier = Modifier.padding(pad),
                transitionSpec = {
                    (fadeIn() + slideInVertically { it / 30 })
                        .togetherWith(fadeOut())
                },
                label = "tabs"
            ) { t ->
                when (t) {
                    Tab.INICIO -> HomeScreen(
                        onAbrirPlano = { mostrarPlano = true },
                        onIrEntrenar = { tab = Tab.ENTRENAR },
                        onIrDieta = { tab = Tab.DIETA }
                    )
                    Tab.ENTRENAR -> EntrenarScreen()
                    Tab.ARENA -> ArenaScreen(
                        objetivo = objetivoArena,
                        onObjetivo = { nuevo ->
                            objetivoArena = nuevo
                            guardarObjetivoArena(contexto, nuevo)
                        }
                    )
                    Tab.DIETA -> DietaScreen(objetivo = objetivoArena)
                    Tab.PERFIL -> PerfilScreen(
                        onAbrirPlano = { mostrarPlano = true },
                        themeMode = themeMode,
                        onThemeMode = onThemeMode,
                        onCerrarSesion = onCerrarSesion
                    )
                }
            }
        }

        // ── Burbuja flotante de Argos: se tapa sola en cuanto se abre el
        // Plano o el propio chat, por estar antes que esos dos en el Stack ──
        androidx.compose.animation.AnimatedVisibility(
            visible = !mostrarPlano && !mostrarArgos,
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(end = 16.dp, bottom = 84.dp),
            enter = fadeIn(), exit = fadeOut()
        ) {
            ArgosBurbujaFlotante(onClick = { mostrarArgos = true })
        }

        // ── Plano interactivo: pantalla completa aparte ──
        androidx.compose.animation.AnimatedVisibility(
            visible = mostrarPlano,
            enter = slideInVertically { it } + fadeIn(),
            exit = slideOutVertically { it } + fadeOut()
        ) {
            PlanoScreen(onVolver = { mostrarPlano = false })
        }

        // ── Chat de Argos: pantalla completa aparte, igual que el Plano ──
        androidx.compose.animation.AnimatedVisibility(
            visible = mostrarArgos,
            enter = slideInVertically { it } + fadeIn(),
            exit = slideOutVertically { it } + fadeOut()
        ) {
            ArgosScreen(onVolver = { mostrarArgos = false })
        }

        // ── Toast de logro desbloqueado: por encima de todo, incluido el Plano ──
        ToastLogroOverlay()
    }
}

@Composable
private fun BarraInferior(actual: Tab, onTab: (Tab) -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .background(Olimpos.Dark.copy(alpha = 0.96f))
    ) {
        Box(
            Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(Olimpos.Line)
        )
        Row(
            Modifier
                .fillMaxWidth()
                .navigationBarsPadding()
                .height(66.dp)
        ) {
            Tab.entries.forEach { t ->
                val activo = t == actual
                Column(
                    Modifier
                        .weight(1f)
                        .fillMaxSize()
                        .clickable(
                            interactionSource = remember { MutableInteractionSource() },
                            indication = null
                        ) { onTab(t) },
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Box(
                        Modifier
                            .width(22.dp)
                            .height(3.dp)
                            .clip(RoundedCornerShape(bottomStart = 4.dp, bottomEnd = 4.dp))
                            .background(if (activo) Olimpos.Gold else androidx.compose.ui.graphics.Color.Transparent)
                    )
                    Text(t.icon, fontSize = if (activo) 19.sp else 17.sp, modifier = Modifier.padding(top = 5.dp))
                    Text(
                        t.label.uppercase(),
                        fontSize = 8.sp,
                        fontWeight = FontWeight.ExtraBold,
                        letterSpacing = 0.8.sp,
                        color = if (activo) Olimpos.GoldLight else Olimpos.Muted
                    )
                }
            }
        }
    }
}
