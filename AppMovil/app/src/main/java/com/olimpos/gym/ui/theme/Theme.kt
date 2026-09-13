package com.olimpos.gym.ui.theme

import android.content.Context
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/** Modo de tema seleccionable por el usuario desde Configuración. */
enum class ThemeMode(val etiqueta: String) {
    CLARO("Claro"),
    OSCURO("Oscuro"),
    AUTOMATICO("Automático (sistema)")
}

private const val PREFS = "olimpos_prefs"
private const val KEY_THEME = "theme_mode"

fun leerThemeMode(context: Context): ThemeMode {
    val guardado = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY_THEME, null)
    return ThemeMode.entries.firstOrNull { it.name == guardado } ?: ThemeMode.CLARO
}

fun guardarThemeMode(context: Context, modo: ThemeMode) {
    context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
        .putString(KEY_THEME, modo.name)
        .apply()
}

/* ─────────────────────────────────────────────
   Paleta OlimpΩs — misma identidad en los dos modos.
   Claro: inspirado en el sistema de empleados (theme.py).
   Oscuro: el look premium dorado-sobre-negro original.
   Los `var ... by mutableStateOf` hacen que TODA la app
   reaccione al cambio de tema sin tocar cada pantalla:
   cada `Olimpos.Xxx` leído en un composable se suscribe
   igual que un State normal.
   ───────────────────────────────────────────── */
object Olimpos {
    // Identidad de marca — igual en ambos modos
    var Gold by mutableStateOf(Color(0xFFC9A227)); private set
    var GoldLight by mutableStateOf(Color(0xFFF0D060)); private set
    var GoldDark by mutableStateOf(Color(0xFFA07820)); private set
    var GoldBg by mutableStateOf(Color(0xFFFFFDE8)); private set
    var Green by mutableStateOf(Color(0xFF22C55E)); private set
    var Red by mutableStateOf(Color(0xFFEF4444)); private set
    var Dark by mutableStateOf(Color(0xFF0D0B00)); private set // tinta siempre oscura (texto sobre dorado, pills)

    // Dependientes del modo claro/oscuro
    var Cream by mutableStateOf(Color(0xFFFAFAF0)); private set        // texto principal
    var Muted by mutableStateOf(Color(0xFF888570)); private set        // texto secundario
    var GrayLight by mutableStateOf(Color(0xFFE8E5D8)); private set
    var Card by mutableStateOf(Color(0x09FFFFFF)); private set         // superficie de tarjetas
    var Superficie2 by mutableStateOf(Color(0xFF1A1500)); private set  // superficie elevada secundaria
    var Line by mutableStateOf(Color(0x29C9A227)); private set         // borde de tarjetas
    var GoldSoft by mutableStateOf(Color(0x1FC9A227)); private set     // chip/fondo dorado tenue
    var FondoA by mutableStateOf(Color(0xFF0D0B00)); private set       // gradiente de fondo, 3 paradas
    var FondoB by mutableStateOf(Color(0xFF1A1500)); private set
    var FondoC by mutableStateOf(Color(0xFF252100)); private set
    var EsOscuro by mutableStateOf(true); private set

    fun aplicar(oscuro: Boolean) {
        EsOscuro = oscuro
        if (oscuro) {
            Cream = Color(0xFFFAFAF0)
            Muted = Color(0xFF888570)
            GrayLight = Color(0xFFE8E5D8)
            Card = Color(0x09FFFFFF)
            Superficie2 = Color(0xFF1A1500)
            Line = Color(0x29C9A227)
            GoldSoft = Color(0x1FC9A227)
            FondoA = Color(0xFF0D0B00)
            FondoB = Color(0xFF1A1500)
            FondoC = Color(0xFF252100)
        } else {
            Cream = Color(0xFF221B02)
            Muted = Color(0xFF8A7F60)
            GrayLight = Color(0xFFE8E5D8)
            Card = Color(0xFFFFFFFF)
            Superficie2 = Color(0xFFF1EEE3)
            Line = Color(0x33C9A227)
            GoldSoft = Color(0xFFFCF3CE)
            FondoA = Color(0xFFFFFDF6)
            FondoB = Color(0xFFFAF6EC)
            FondoC = Color(0xFFF2ECDB)
        }
    }
}

/* Tipografía: pesos fuertes tipo Poppins/Nunito del sitio.
   Para usar las fuentes exactas: agregar poppins_*.ttf y nunito_*.ttf
   en res/font/ y reemplazar FontFamily.SansSerif por ellas. */
val OlimposType = Typography(
    displaySmall = TextStyle(
        fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.Black,
        fontSize = 26.sp, letterSpacing = (-0.5).sp
    ),
    titleLarge = TextStyle(
        fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.ExtraBold,
        fontSize = 18.sp
    ),
    titleMedium = TextStyle(
        fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.ExtraBold,
        fontSize = 15.sp
    ),
    bodyMedium = TextStyle(
        fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.Medium,
        fontSize = 13.5.sp, lineHeight = 20.sp
    ),
    bodySmall = TextStyle(
        fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.SemiBold,
        fontSize = 12.sp, lineHeight = 17.sp
    ),
    labelSmall = TextStyle(
        fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.ExtraBold,
        fontSize = 10.sp, letterSpacing = 1.8.sp
    )
)

@Composable
fun OlimposTheme(modo: ThemeMode = ThemeMode.CLARO, content: @Composable () -> Unit) {
    val oscuro = when (modo) {
        ThemeMode.CLARO -> false
        ThemeMode.OSCURO -> true
        ThemeMode.AUTOMATICO -> isSystemInDarkTheme()
    }
    SideEffect { Olimpos.aplicar(oscuro) }

    val scheme = if (oscuro) {
        darkColorScheme(
            primary = Olimpos.Gold, onPrimary = Olimpos.Dark,
            secondary = Olimpos.GoldLight, onSecondary = Olimpos.Dark,
            background = Olimpos.FondoA, onBackground = Olimpos.Cream,
            surface = Olimpos.FondoB, onSurface = Olimpos.Cream,
            surfaceVariant = Olimpos.FondoC, onSurfaceVariant = Olimpos.Muted,
            outline = Olimpos.Line, error = Olimpos.Red
        )
    } else {
        lightColorScheme(
            primary = Olimpos.Gold, onPrimary = Color.White,
            secondary = Olimpos.GoldDark, onSecondary = Color.White,
            background = Olimpos.FondoA, onBackground = Olimpos.Cream,
            surface = Color.White, onSurface = Olimpos.Cream,
            surfaceVariant = Olimpos.Superficie2, onSurfaceVariant = Olimpos.Muted,
            outline = Olimpos.Line, error = Olimpos.Red
        )
    }

    MaterialTheme(
        colorScheme = scheme,
        typography = OlimposType,
        content = content
    )
}
