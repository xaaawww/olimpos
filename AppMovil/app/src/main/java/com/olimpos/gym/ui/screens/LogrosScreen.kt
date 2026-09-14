package com.olimpos.gym.ui.screens

import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.Logro
import com.olimpos.gym.data.calcularLogros
import com.olimpos.gym.data.construirContextoLogros
import com.olimpos.gym.ui.theme.Olimpos

/** Logros: grilla de 5 columnas solo con el ícono — tocar uno abre el
 *  detalle (título, descripción y barra de progreso) en una tarjeta
 *  superpuesta. Los secretos no aparecen en la grilla ni en el total hasta
 *  que se desbloquean — son un bonus raro, no parte del 100% normal. */
@Composable
fun LogrosScreen(onVolver: () -> Unit) {
    // remember con estas claves: los logros se recalculan si cambia
    // alguna de las fuentes reales detrás (una marca nueva, una serie
    // registrada, un ingreso marcado, etc.), pero no en cada recomposición
    // suelta (por ejemplo, al abrir o cerrar el detalle de una medalla).
    val contexto = LocalContext.current
    val ctxLogros = construirContextoLogros(contexto)
    val logros = remember(ctxLogros) { calcularLogros(ctxLogros) }
    val publicos = remember(logros) { logros.filter { !it.secreto } }
    val desbloqueados = remember(logros) { publicos.count { it.desbloqueado } }
    val visibles = remember(logros) { logros.filter { !it.secreto || it.desbloqueado } }
    var seleccionado by remember { mutableStateOf<Logro?>(null) }

    Box(Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxSize()) {
            EncabezadoVolver("Logros", "$desbloqueados de ${publicos.size} medallas desbloqueadas", onVolver)

            Column(Modifier.padding(horizontal = 20.dp, vertical = 6.dp)) {
                BarraProgreso(desbloqueados / publicos.size.toFloat())
            }

            LazyVerticalGrid(
                columns = GridCells.Fixed(5),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(20.dp),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
                modifier = Modifier.weight(1f)
            ) {
                items(visibles, key = { it.nombre }) { logro ->
                    IconoLogro(logro) { seleccionado = logro }
                }
            }
        }

        androidx.compose.animation.AnimatedVisibility(
            visible = seleccionado != null,
            enter = fadeIn(), exit = fadeOut()
        ) {
            seleccionado?.let { logro ->
                DetalleLogro(logro, onCerrar = { seleccionado = null })
            }
        }
    }
}

@Composable
private fun IconoLogro(logro: Logro, onClick: () -> Unit) {
    Box(
        Modifier
            .aspectRatio(1f)
            .clip(RoundedCornerShape(16.dp))
            .background(if (logro.desbloqueado) Olimpos.GoldSoft else Olimpos.Card)
            .border(
                1.dp,
                if (logro.desbloqueado) Olimpos.Gold.copy(alpha = 0.4f) else Olimpos.Line,
                RoundedCornerShape(16.dp)
            )
            .clickable(onClick = onClick)
            .alpha(if (logro.desbloqueado) 1f else 0.55f),
        contentAlignment = Alignment.Center
    ) {
        Text(logro.emoji, fontSize = 24.sp)
        if (logro.desbloqueado) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.TopEnd) {
                Text(
                    "✓", color = Olimpos.Green, fontWeight = FontWeight.Black, fontSize = 12.sp,
                    modifier = Modifier.padding(4.dp)
                )
            }
        }
    }
}

@Composable
private fun DetalleLogro(logro: Logro, onCerrar: () -> Unit) {
    Box(
        Modifier
            .fillMaxSize()
            .background(Olimpos.Dark.copy(alpha = 0.72f))
            .clickable(onClick = onCerrar),
        contentAlignment = Alignment.Center
    ) {
        Column(
            Modifier
                .padding(horizontal = 36.dp)
                .clip(RoundedCornerShape(24.dp))
                .background(Olimpos.Card)
                .border(1.dp, Olimpos.Gold.copy(alpha = 0.4f), RoundedCornerShape(24.dp))
                .clickable(enabled = false) {}
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                Modifier
                    .padding(bottom = 14.dp)
                    .clip(RoundedCornerShape(18.dp))
                    .background(if (logro.desbloqueado) Olimpos.Gold.copy(alpha = 0.25f) else Olimpos.Superficie2)
                    .padding(18.dp)
            ) { Text(logro.emoji, fontSize = 36.sp) }

            Text(logro.nombre, fontSize = 17.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
            Spacer(Modifier.height(6.dp))
            Text(
                logro.descripcion, fontSize = 12.5.sp, color = Olimpos.Muted,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            if (logro.desbloqueado) {
                ChipOro("✓ Desbloqueado")
            } else {
                BarraProgreso(logro.progreso, modifier = Modifier.fillMaxWidth())
                Spacer(Modifier.height(6.dp))
                Text(
                    "${(logro.progreso * 100).toInt()}% completado",
                    fontSize = 11.sp, color = Olimpos.Muted
                )
            }
        }
    }
}
