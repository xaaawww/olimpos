package com.olimpos.gym.ui.screens

import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.Logro
import com.olimpos.gym.data.calcularLogros
import com.olimpos.gym.data.construirContextoLogros
import com.olimpos.gym.ui.theme.Olimpos

/** Logros y medallas. "Logros" = los que faltan, ordenados por lo cerca que
 *  estás, con su barra; "Medallas" = la vitrina de los ya ganados. Tocar
 *  cualquiera abre su detalle. Los secretos no aparecen ni cuentan para el
 *  total hasta que se desbloquean. */
@Composable
fun LogrosScreen(onVolver: () -> Unit) {
    // Se recalculan si cambia alguna fuente real (marca, serie, ingreso…),
    // no en cada recomposición suelta.
    val contexto = LocalContext.current
    val ctxLogros = construirContextoLogros(contexto)
    val logros = remember(ctxLogros) { calcularLogros(ctxLogros) }
    val publicos = remember(logros) { logros.filter { !it.secreto } }
    val ganados = remember(logros) { logros.filter { it.desbloqueado } }
    val pendientes = remember(logros) { publicos.filter { !it.desbloqueado }.sortedByDescending { it.progreso } }
    var pestana by remember { mutableIntStateOf(0) }
    var seleccionado by remember { mutableStateOf<Logro?>(null) }

    Box(Modifier.fillMaxSize().background(CA.fondo)) {
        LazyVerticalGrid(
            columns = GridCells.Fixed(3),
            modifier = Modifier.fillMaxSize(),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(bottom = 26.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            item(span = { GridItemSpan(3) }) {
                Column {
                    EncabezadoArena(
                        "Logros y medallas", "Completá desafíos, ganá medallas y demostrá tu progreso.", onVolver,
                        derecha = { ContadorLogros(publicos.count { it.desbloqueado }, publicos.size) }
                    )
                    PestanasPildora(
                        listOf("Logros", "Medallas"), pestana, { pestana = it },
                        Modifier.padding(horizontal = 20.dp).padding(top = 6.dp, bottom = 4.dp)
                    )
                }
            }
            if (pestana == 0) {
                if (pendientes.isEmpty()) {
                    item(span = { GridItemSpan(3) }) { Vacio("¡Completaste todos los logros! Mirá tus medallas.") }
                }
                items(pendientes, key = { it.nombre }, span = { GridItemSpan(3) }) { logro ->
                    FilaLogro(logro, Modifier.padding(horizontal = 20.dp)) { seleccionado = logro }
                }
            } else {
                if (ganados.isEmpty()) {
                    item(span = { GridItemSpan(3) }) { Vacio("Todavía no ganaste medallas. Empezá por el logro que tengas más cerca.") }
                }
                items(ganados, key = { it.nombre }) { logro ->
                    val i = ganados.indexOf(logro) % 3
                    Medalla(
                        logro,
                        Modifier.padding(start = if (i == 0) 20.dp else 0.dp, end = if (i == 2) 20.dp else 0.dp)
                    ) { seleccionado = logro }
                }
            }
        }

        androidx.compose.animation.AnimatedVisibility(visible = seleccionado != null, enter = fadeIn(), exit = fadeOut()) {
            seleccionado?.let { logro -> DetalleLogro(logro, onCerrar = { seleccionado = null }) }
        }
    }
}

@Composable
private fun ContadorLogros(ganados: Int, total: Int) {
    Row(
        Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(CA.tarjeta)
            .border(1.dp, CA.borde, RoundedCornerShape(12.dp))
            .padding(horizontal = 10.dp, vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text("🏆", fontSize = 18.sp)
        Spacer(Modifier.width(6.dp))
        Column {
            Text("$ganados/$total", fontSize = 13.sp, fontWeight = FontWeight.Black, color = CA.texto)
            Text("logros", fontSize = 9.sp, color = CA.suave)
        }
    }
}

@Composable
private fun FilaLogro(logro: Logro, modifier: Modifier, onClick: () -> Unit) {
    TarjetaLisa(modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).clickable(onClick = onClick)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconoRedondo(logro.emoji, tamano = 48.dp, apagado = logro.progreso <= 0f)
            Spacer(Modifier.width(13.dp))
            Column(Modifier.weight(1f)) {
                Text(logro.nombre, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = CA.texto)
                Text(logro.descripcion, fontSize = 11.5.sp, color = CA.suave, maxLines = 2, overflow = TextOverflow.Ellipsis)
                Spacer(Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    BarraArena(logro.progreso, Modifier.weight(1f))
                    Spacer(Modifier.width(10.dp))
                    Text("${(logro.progreso * 100).toInt()}%", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = CA.suave)
                }
            }
            Spacer(Modifier.width(8.dp))
            Chevron()
        }
    }
}

@Composable
private fun Medalla(logro: Logro, modifier: Modifier, onClick: () -> Unit) {
    Column(
        modifier
            .clip(RoundedCornerShape(16.dp))
            .background(CA.tarjeta)
            .border(1.dp, CA.amarillo.copy(alpha = 0.35f), RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
            .padding(vertical = 14.dp, horizontal = 6.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        IconoRedondo(logro.emoji, tamano = 52.dp, pastel = Pastel.NARANJA)
        Spacer(Modifier.height(8.dp))
        Text(
            logro.nombre, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, color = CA.texto,
            textAlign = TextAlign.Center, maxLines = 2, overflow = TextOverflow.Ellipsis, lineHeight = 13.sp
        )
    }
}

@Composable
private fun Vacio(texto: String) {
    TarjetaLisa(Modifier.fillMaxWidth().padding(horizontal = 20.dp)) {
        Text(texto, fontSize = 12.sp, color = CA.suave, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth())
    }
}

@Composable
private fun DetalleLogro(logro: Logro, onCerrar: () -> Unit) {
    Box(
        Modifier
            .fillMaxSize()
            .background(CA.tinta.copy(alpha = 0.72f))
            .clickable(onClick = onCerrar),
        contentAlignment = Alignment.Center
    ) {
        Column(
            Modifier
                .padding(horizontal = 36.dp)
                .clip(RoundedCornerShape(24.dp))
                .background(CA.tarjeta)
                .border(1.dp, CA.amarillo.copy(alpha = 0.4f), RoundedCornerShape(24.dp))
                .clickable(enabled = false) {}
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            IconoRedondo(logro.emoji, tamano = 72.dp, apagado = !logro.desbloqueado)
            Spacer(Modifier.height(14.dp))
            Text(logro.nombre, fontSize = 17.sp, fontWeight = FontWeight.Black, color = CA.texto)
            Spacer(Modifier.height(6.dp))
            Text(
                logro.descripcion, fontSize = 12.5.sp, color = CA.suave, textAlign = TextAlign.Center,
                modifier = Modifier.padding(bottom = 16.dp)
            )
            if (logro.desbloqueado) {
                ChipSuave("✓ Medalla ganada", Pastel.VERDE)
            } else {
                BarraArena(logro.progreso, alto = 8.dp)
                Spacer(Modifier.height(6.dp))
                Text("${(logro.progreso * 100).toInt()}% completado", fontSize = 11.sp, color = CA.suave)
            }
        }
    }
}
