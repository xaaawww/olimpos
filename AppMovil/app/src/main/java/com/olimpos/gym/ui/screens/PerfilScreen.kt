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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.data.SocioAuth
import com.olimpos.gym.data.clasesReservadasEstaSemana
import com.olimpos.gym.data.planIncluyeArgos
import com.olimpos.gym.data.rachaActualDeDias
import com.olimpos.gym.data.visitasEnElMesActual
import com.olimpos.gym.ui.theme.Olimpos
import com.olimpos.gym.ui.theme.ThemeMode

private enum class PerfilVista { HOME, MEMBRESIA, ACCESO, TURNOS, PROGRESO, COMPANEROS, ARGOS, CONFIGURACION }

@Composable
fun PerfilScreen(
    onAbrirPlano: () -> Unit,
    themeMode: ThemeMode,
    onThemeMode: (ThemeMode) -> Unit,
    objetivo: ObjetivoCompetencia?,
    onObjetivo: (ObjetivoCompetencia) -> Unit,
    /** Se pone en true desde afuera (ver el bloqueo de Argos) para abrir
     *  directo "Mi membresía"; [onMembresiaAbierta] apaga el pedido. */
    abrirMembresia: Boolean,
    onMembresiaAbierta: () -> Unit,
    /** Igual que [abrirMembresia], pero para "Mis turnos y reservas" (lo pide Inicio). */
    abrirTurnos: Boolean,
    onTurnosAbierto: () -> Unit,
    onCerrarSesion: () -> Unit
) {
    var vista by remember { mutableStateOf(PerfilVista.HOME) }
    LaunchedEffect(abrirMembresia) {
        if (abrirMembresia) {
            vista = PerfilVista.MEMBRESIA
            onMembresiaAbierta()
        }
    }
    LaunchedEffect(abrirTurnos) {
        if (abrirTurnos) {
            vista = PerfilVista.TURNOS
            onTurnosAbierto()
        }
    }

    when (vista) {
        PerfilVista.HOME -> PerfilHome(
            onAbrirPlano = onAbrirPlano,
            onMembresia = { vista = PerfilVista.MEMBRESIA },
            onAcceso = { vista = PerfilVista.ACCESO },
            onTurnos = { vista = PerfilVista.TURNOS },
            onProgreso = { vista = PerfilVista.PROGRESO },
            onCompaneros = { vista = PerfilVista.COMPANEROS },
            onArgos = { vista = PerfilVista.ARGOS },
            onConfiguracion = { vista = PerfilVista.CONFIGURACION },
            onCerrarSesion = onCerrarSesion
        )
        PerfilVista.MEMBRESIA -> MembresiaScreen(onVolver = { vista = PerfilVista.HOME })
        PerfilVista.ACCESO -> AccesoScreen(onVolver = { vista = PerfilVista.HOME })
        PerfilVista.TURNOS -> TurnosScreen(onVolver = { vista = PerfilVista.HOME })
        PerfilVista.PROGRESO -> ProgresoScreen(onVolver = { vista = PerfilVista.HOME })
        PerfilVista.COMPANEROS -> CompanerosScreen(onVolver = { vista = PerfilVista.HOME })
        PerfilVista.ARGOS -> ArgosScreen(
            onVolver = { vista = PerfilVista.HOME },
            onVerPlanes = { vista = PerfilVista.MEMBRESIA }
        )
        PerfilVista.CONFIGURACION -> ConfiguracionScreen(
            onVolver = { vista = PerfilVista.HOME },
            themeMode = themeMode,
            onThemeMode = onThemeMode,
            objetivo = objetivo,
            onObjetivo = onObjetivo
        )
    }
}

@Composable
private fun PerfilHome(
    onAbrirPlano: () -> Unit,
    onMembresia: () -> Unit,
    onAcceso: () -> Unit,
    onTurnos: () -> Unit,
    onProgreso: () -> Unit,
    onCompaneros: () -> Unit,
    onArgos: () -> Unit,
    onConfiguracion: () -> Unit,
    onCerrarSesion: () -> Unit
) {
    var aviso by remember { mutableStateOf<String?>(null) }
    val nombre = SocioAuth.nombreActual ?: "Socio"

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .statusBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(top = 14.dp, bottom = 26.dp)
    ) {
        // ── Cabecera ──
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
            AvatarInicial(nombre.take(1).uppercase(), tamano = 64)
            Spacer(Modifier.height(10.dp))
            Text(nombre, fontSize = 18.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
            Spacer(Modifier.height(8.dp))
            ChipOro("Ω  Socio OlimpΩs")
        }

        Spacer(Modifier.height(18.dp))

        // ── Estadísticas ──
        // Las tres salen de datos reales: ingresos marcados en Accesos
        // (racha/visitas) y reservas de clase guardadas de verdad desde
        // Inicio (antes "Reservar" solo cambiaba un estado local que se
        // perdía al salir de la pantalla).
        val timestampsIngreso = (DatosRemotos.ingresos ?: emptyList()).map { it.timestamp }
        val reservasClase = DatosRemotos.reservasClase ?: emptyList()
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Estadistica("${rachaActualDeDias(timestampsIngreso)}", "Días racha", Modifier.weight(1f))
            Estadistica("${visitasEnElMesActual(timestampsIngreso)}", "Visitas mes", Modifier.weight(1f))
            Estadistica("${clasesReservadasEstaSemana(reservasClase)}", "Clases sem.", Modifier.weight(1f))
        }

        SeccionLabel("Mi club")
        // ── El plano vive acá: sector aparte, no principal ──
        ItemMenu("🗺️", "Plano interactivo del club") { onAbrirPlano() }
        ItemMenu("💳", "Mi membresía y pagos") { onMembresia() }
        ItemMenu("🔐", "Accesos y seguridad") { onAcceso() }
        ItemMenu("📈", "Mi progreso") { onProgreso() }
        ItemMenu("🤝", "Mis compañeros de entrenamiento") { onCompaneros() }
        ItemMenu(
            "🐕",
            if (planIncluyeArgos(DatosRemotos.membresia?.plan)) "Argos, asistente de IA"
            else "Argos (Plan Oro)"
        ) { onArgos() }
        ItemMenu("📅", "Mis turnos y reservas") { onTurnos() }

        SeccionLabel("Cuenta")
        ItemMenu("⚙️", "Configuración") { onConfiguracion() }
        ItemMenu("ℹ️", "Acerca de OlimpΩs") { aviso = "OlimpΩs App · v1.0 · Proyecto Olimpos" }
        ItemMenu("🚪", "Cerrar sesión") { onCerrarSesion() }

        aviso?.let {
            Spacer(Modifier.height(14.dp))
            Box(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .background(Olimpos.GoldSoft)
                    .border(1.dp, Olimpos.Gold.copy(alpha = 0.35f), RoundedCornerShape(14.dp))
                    .padding(13.dp)
            ) {
                Text(it, fontSize = 12.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.GoldLight)
            }
        }
    }
}

@Composable
private fun Estadistica(valor: String, etiqueta: String, modifier: Modifier = Modifier) {
    Column(
        modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
            .padding(vertical = 13.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(valor, fontSize = 20.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
        Text(etiqueta, fontSize = 11.sp, color = Olimpos.Muted)
    }
}

@Composable
private fun ItemMenu(emoji: String, texto: String, onClick: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .padding(bottom = 8.dp)
            .clip(RoundedCornerShape(14.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 11.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconoCuadrado(emoji)
        Spacer(Modifier.width(13.dp))
        Text(texto, fontSize = 14.sp, fontWeight = FontWeight.Medium, color = Olimpos.Cream, modifier = Modifier.weight(1f))
        FlechaFila()
    }
}
