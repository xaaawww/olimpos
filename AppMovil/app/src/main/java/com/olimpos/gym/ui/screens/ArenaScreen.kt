package com.olimpos.gym.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.ui.theme.Olimpos

private enum class ArenaVista { GRID, BODYGRAPH, CALCULADORA, GALERIA, MARCAS, LOGROS, CLASIFICACION }

@Composable
fun ArenaScreen(objetivo: ObjetivoCompetencia?, onObjetivo: (ObjetivoCompetencia) -> Unit) {
    var vista by remember { mutableStateOf(ArenaVista.GRID) }
    var mostrarSelector by remember { mutableStateOf(false) }

    // Primera vez que entra a Arena (objetivo == null) o tocó la insignia
    // para cambiarlo: pantalla completa de selección, antes que la grilla.
    if (objetivo == null || mostrarSelector) {
        ObjetivoScreen(objetivoActual = objetivo) { elegido ->
            onObjetivo(elegido)
            mostrarSelector = false
        }
        return
    }

    when (vista) {
        ArenaVista.GRID -> ArenaGrid(
            objetivo = objetivo,
            onCambiarObjetivo = { mostrarSelector = true },
            onBodygraph = { vista = ArenaVista.BODYGRAPH },
            onCalculadora = { vista = ArenaVista.CALCULADORA },
            onGaleria = { vista = ArenaVista.GALERIA },
            onLogros = { vista = ArenaVista.LOGROS },
            onMarcas = { vista = ArenaVista.MARCAS },
            onClasificacion = { vista = ArenaVista.CLASIFICACION }
        )
        ArenaVista.BODYGRAPH -> BodygraphScreen(onVolver = { vista = ArenaVista.GRID })
        ArenaVista.CALCULADORA -> CalculadoraScreen(onVolver = { vista = ArenaVista.GRID })
        ArenaVista.GALERIA -> GaleriaScreen(onVolver = { vista = ArenaVista.GRID })
        ArenaVista.MARCAS -> MarcasScreen(onVolver = { vista = ArenaVista.GRID })
        ArenaVista.LOGROS -> LogrosScreen(onVolver = { vista = ArenaVista.GRID })
        ArenaVista.CLASIFICACION -> ClasificacionScreen(onVolver = { vista = ArenaVista.GRID })
    }
}

@Composable
private fun ArenaGrid(
    objetivo: ObjetivoCompetencia,
    onCambiarObjetivo: () -> Unit,
    onBodygraph: () -> Unit,
    onCalculadora: () -> Unit,
    onGaleria: () -> Unit,
    onLogros: () -> Unit,
    onMarcas: () -> Unit,
    onClasificacion: () -> Unit
) {
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .statusBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(top = 14.dp, bottom = 26.dp)
    ) {
        BadgeObjetivo(objetivo, onClick = onCambiarObjetivo)
        Spacer(Modifier.height(12.dp))
        Eyebrow("Arena")
        Row {
            Text("Competí y ", fontSize = 26.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
            Text("superate", fontSize = 26.sp, fontWeight = FontWeight.Black, color = Olimpos.Gold)
        }
        Text("Tu mapa muscular, tu rango y tus marcas personales", fontSize = 13.sp, color = Olimpos.Muted)

        Spacer(Modifier.height(18.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            TarjetaArena("🧍", "Bodygraph", "Mapa muscular de hoy", Modifier.weight(1f), onBodygraph)
            TarjetaArena("🧮", "Calculadora", "Estimá tu 1RM", Modifier.weight(1f), onCalculadora)
        }
        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            TarjetaArena("🏅", "Galería", "Tu rango por ejercicio", Modifier.weight(1f), onGaleria)
            TarjetaArena("🎖️", "Logros y medallas", "Tu vitrina de insignias", Modifier.weight(1f), onLogros)
        }
        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            TarjetaArena("🥇", "Mis marcas", "PRs y validación", Modifier.weight(1f), onMarcas)
            TarjetaArena("📊", "Clasificación", "La Escalera del Olimpo", Modifier.weight(1f), onClasificacion)
        }
    }
}

@Composable
private fun TarjetaArena(icono: String, titulo: String, sub: String, modifier: Modifier, onClick: () -> Unit) {
    TarjetaOro(modifier.clickable(onClick = onClick)) {
        IconoCuadrado(icono)
        Spacer(Modifier.height(10.dp))
        Text(titulo, fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
        Text(sub, fontSize = 11.sp, color = Olimpos.Muted)
    }
}
