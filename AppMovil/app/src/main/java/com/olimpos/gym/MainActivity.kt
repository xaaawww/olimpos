package com.olimpos.gym

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
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
import androidx.compose.foundation.layout.size
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
import androidx.compose.runtime.rememberCoroutineScope
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
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.data.SocioAuth
import com.olimpos.gym.data.cargarDatosFisicosPropios
import com.olimpos.gym.data.guardarObjetivoArena
import com.olimpos.gym.data.guardarObjetivoEnFirebase
import com.olimpos.gym.data.leerObjetivoArena
import com.olimpos.gym.data.planIncluyeArgos
import com.olimpos.gym.data.resolverObjetivo
import com.olimpos.gym.ui.screens.ArenaScreen
import com.olimpos.gym.ui.screens.NutricionTab
import com.olimpos.gym.ui.screens.NutricionVista
import com.olimpos.gym.ui.screens.ArgosBurbujaMovil
import com.olimpos.gym.ui.screens.ArgosScreen
import com.olimpos.gym.ui.screens.CambiarPasswordScreen
import com.olimpos.gym.ui.screens.EntrenarScreen
import com.olimpos.gym.ui.screens.HomeScreen
import com.olimpos.gym.ui.screens.LoginScreen
import com.olimpos.gym.ui.screens.ObjetivoScreen
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
import kotlinx.coroutines.launch

enum class Tab(val label: String, val icon: String) {
    INICIO("Inicio", "🏛️"),
    ENTRENAR("Entrenar", "🏋️"),
    ARENA("Arena", "⚔️"),
    DIETA("NutriStore", "🥗"),   // Nutri (dieta) + Store (tienda), ver NutricionTab
    PERFIL("Perfil", "👤")
}

/** Etapa general de la app: verificación (arranque/post-login) →
 *  autenticación → cambio de contraseña obligatorio (solo en el primer
 *  login, ver [SocioAuth.debeCambiarPassword]) → onboarding obligatorio
 *  (solo si todavía no cargó sus datos físicos, ver
 *  [cargarDatosFisicosPropios]) → elegir objetivo (solo si todavía no tiene
 *  uno, ver [resolverObjetivo]) → app principal. */
private enum class Etapa { VERIFICANDO, LOGIN, CAMBIAR_PASSWORD, ONBOARDING, OBJETIVO, APP }

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val contexto = LocalContext.current
            var themeMode by remember { mutableStateOf(leerThemeMode(contexto)) }
            OlimposTheme(modo = themeMode) {
                // Letra un 8% más chica en toda la app (respetando el tamaño
                // que el socio eligió en su celular): más liviana, como el
                // sistema de empleados.
                val densidad = androidx.compose.ui.platform.LocalDensity.current
                remember { com.olimpos.gym.ui.theme.PreferenciasApp.cargar(contexto) }
                androidx.compose.runtime.CompositionLocalProvider(
                    androidx.compose.ui.platform.LocalDensity provides androidx.compose.ui.unit.Density(
                        densidad.density,
                        densidad.fontScale * com.olimpos.gym.ui.theme.PreferenciasApp.escalaLetra.factor
                    )
                ) {
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
    val contexto = LocalContext.current
    val scope = rememberCoroutineScope()

    LaunchedEffect(verificacion) {
        etapa = when {
            Firebase.auth.currentUser == null -> Etapa.LOGIN
            !SocioAuth.cuentaSigueActiva() -> {
                SocioAuth.cerrarSesion()
                DatosRemotos.limpiar()
                Etapa.LOGIN
            }
            // Contraseña temporal generada por el empleado, todavía no
            // reemplazada por el propio socio (ver auth_repo.py).
            SocioAuth.debeCambiarPassword() -> Etapa.CAMBIAR_PASSWORD
            else -> {
                val datos = cargarDatosFisicosPropios()
                when {
                    // Sin datos físicos todavía (cuenta recién creada por un
                    // empleado) → onboarding obligatorio antes de dejarlo entrar.
                    datos == null -> Etapa.ONBOARDING
                    // Sin objetivo (cuenta que hizo el onboarding antes de que
                    // el objetivo se guardara): se le pide una sola vez.
                    resolverObjetivo(contexto, datos) == null -> Etapa.OBJETIVO
                    else -> Etapa.APP
                }
            }
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
                Etapa.CAMBIAR_PASSWORD -> CambiarPasswordScreen(onListo = { verificacion++ })
                Etapa.ONBOARDING -> OnboardingScreen(onFinalizar = { verificacion++ })
                Etapa.OBJETIVO -> ObjetivoScreen(objetivoActual = null) { elegido ->
                    guardarObjetivoArena(contexto, elegido)
                    scope.launch {
                        guardarObjetivoEnFirebase(elegido)
                        verificacion++
                    }
                }
                Etapa.APP -> OlimposAppPrincipal(
                    themeMode = themeMode,
                    onThemeMode = onThemeMode,
                    onCerrarSesion = {
                        SocioAuth.cerrarSesion()
                        // Sin esto, la próxima cuenta que inicie sesión en este
                        // mismo celular vería la membresía, marcas y comidas de la anterior.
                        DatosRemotos.limpiar()
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
    var vistaNutricion by remember { mutableStateOf(NutricionVista.MENU) }
    // El plano vive fuera de la navegación principal: sector aparte
    var mostrarPlano by remember { mutableStateOf(false) }
    // Argos también: burbuja flotante sobre cualquier pestaña, en vez de
    // que haga falta ir hasta Perfil para preguntarle algo.
    var mostrarArgos by remember { mutableStateOf(false) }
    // Pantallas con botones abajo (registrar una comida) le piden esconderse.
    var ocultarBurbujaArgos by remember { mutableStateOf(false) }

    val contexto = LocalContext.current
    val scope = rememberCoroutineScope()
    var objetivoArena by remember { mutableStateOf(leerObjetivoArena(contexto)) }
    // Lo pide el bloqueo de Argos para llevar directo a "Mi membresía".
    var abrirMembresia by remember { mutableStateOf(false) }
    // Lo pide Inicio (tarjeta de clases) para llevar directo a "Mis turnos y reservas".
    var abrirTurnos by remember { mutableStateOf(false) }

    // El objetivo se elige al iniciar la app y se cambia solo desde
    // Configuración — la Arena ya no lo cambia.
    val cambiarObjetivo: (ObjetivoCompetencia) -> Unit = { nuevo ->
        objetivoArena = nuevo
        guardarObjetivoArena(contexto, nuevo)
        scope.launch { guardarObjetivoEnFirebase(nuevo) }
    }

    // Precarga marcas/platos/ejercicios/ranking apenas se entra a la app,
    // para que Bodygraph, Dieta y Galería ya tengan los datos reales listos
    // en vez de mostrar el catálogo de ejemplo un instante y reemplazarlo.
    LaunchedEffect(Unit) { DatosRemotos.precargar() }

    // Atrás del celular desde otra pestaña vuelve a Inicio; recién desde
    // Inicio sale de la app. Las sub-pantallas (EncabezadoVolver), el Plano y
    // Argos se componen después, así que su propio Atrás tiene prioridad.
    BackHandler(enabled = tab != Tab.INICIO) { tab = Tab.INICIO }

    // Vigila en segundo plano si se desbloqueó un logro nuevo, toda la
    // sesión — no solo cuando la pantalla de Logros está abierta.
    ObservadorDeLogros()

    Box(Modifier.fillMaxSize()) {
        Scaffold(
            containerColor = androidx.compose.ui.graphics.Color.Transparent,
            contentWindowInsets = WindowInsets(0),
            // Tocar "NutriStore" en la barra siempre lleva a su menú (Nutri / Store)
            bottomBar = { BarraInferior(tab) { if (it == Tab.DIETA) vistaNutricion = NutricionVista.MENU; tab = it } }
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
                        onIrDieta = { vistaNutricion = NutricionVista.DIETA; tab = Tab.DIETA },
                        onIrTienda = { vistaNutricion = NutricionVista.TIENDA; tab = Tab.DIETA },
                        onAbrirTurnos = { tab = Tab.PERFIL; abrirTurnos = true }
                    )
                    Tab.ENTRENAR -> EntrenarScreen()
                    Tab.ARENA -> ArenaScreen(objetivo = objetivoArena)
                    Tab.DIETA -> NutricionTab(
                        vista = vistaNutricion,
                        onVista = { vistaNutricion = it },
                        objetivo = objetivoArena,
                        onOcultarBurbujaArgos = { ocultarBurbujaArgos = it }
                    )
                    Tab.PERFIL -> PerfilScreen(
                        onAbrirPlano = { mostrarPlano = true },
                        themeMode = themeMode,
                        onThemeMode = onThemeMode,
                        objetivo = objetivoArena,
                        onObjetivo = cambiarObjetivo,
                        abrirMembresia = abrirMembresia,
                        onMembresiaAbierta = { abrirMembresia = false },
                        abrirTurnos = abrirTurnos,
                        onTurnosAbierto = { abrirTurnos = false },
                        onCerrarSesion = onCerrarSesion
                    )
                }
            }
        }

        // ── Burbuja flotante de Argos: se tapa sola en cuanto se abre el
        // Plano o el propio chat, por estar antes que esos dos en el Stack.
        // Se puede arrastrar por la pantalla (ver ArgosBurbujaMovil, que
        // también se ocupa de respetar la barra de navegación del sistema para
        // no arrancar tapando el botón "Perfil"). ──
        ArgosBurbujaMovil(
            visible = !mostrarPlano && !mostrarArgos && !ocultarBurbujaArgos,
            bloqueado = !planIncluyeArgos(DatosRemotos.membresia?.plan),
            onClick = { mostrarArgos = true }
        )

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
            ArgosScreen(
                onVolver = { mostrarArgos = false },
                onVerPlanes = {
                    mostrarArgos = false
                    tab = Tab.PERFIL
                    abrirMembresia = true
                }
            )
        }

        // ── Toast de logro desbloqueado: por encima de todo, incluido el Plano ──
        ToastLogroOverlay()
    }
}

/** Barra de pestañas clara, como el menú lateral del sistema de empleados:
 *  ícono de línea + nombre; la elegida en dorado sobre fondo suave. */
@Composable
private fun BarraInferior(actual: Tab, onTab: (Tab) -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .background(if (Olimpos.EsOscuro) Olimpos.Dark else Olimpos.Card)
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
                .height(62.dp)
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
                            .width(52.dp)
                            .height(28.dp)
                            .clip(RoundedCornerShape(100.dp))
                            .background(if (activo) Olimpos.GoldSoft else androidx.compose.ui.graphics.Color.Transparent),
                        contentAlignment = Alignment.Center
                    ) {
                        com.olimpos.gym.ui.theme.ICONO_DE_EMOJI[t.icon]?.let {
                            androidx.compose.material3.Icon(
                                it, contentDescription = t.label, modifier = Modifier.size(20.dp),
                                tint = if (activo) Olimpos.GoldLight else Olimpos.Muted
                            )
                        }
                    }
                    Text(
                        t.label,
                        fontSize = 10.5.sp,
                        fontWeight = if (activo) FontWeight.SemiBold else FontWeight.Medium,
                        color = if (activo) Olimpos.Cream else Olimpos.Muted,
                        modifier = Modifier.padding(top = 2.dp)
                    )
                }
            }
        }
    }
}
