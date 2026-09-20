package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.CategoriaTablon
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.PublicacionTablon
import com.olimpos.gym.data.fechaLegible
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

/** Cuántas publicaciones se muestran en el resumen de Inicio (el resto, en "Ver todo"). */
private const val MAX_EN_INICIO = 2

/** Resumen del tablón para Inicio: las publicaciones más importantes (las
 *  fijadas primero) y el acceso a la lista completa. */
@Composable
fun TablonResumen(onVerTodo: () -> Unit) {
    val publicaciones = DatosRemotos.tablon ?: emptyList()
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        if (publicaciones.isEmpty()) {
            TarjetaOro(Modifier.fillMaxWidth()) {
                Text(
                    "No hay avisos por ahora. Cuando el club publique algo importante lo vas a ver acá.",
                    fontSize = 12.sp, color = Olimpos.Muted
                )
            }
        } else {
            publicaciones.take(MAX_EN_INICIO).forEach { TarjetaPublicacion(it, compacta = true, onClick = onVerTodo) }
            if (publicaciones.size > MAX_EN_INICIO) {
                Text(
                    "Ver todo el tablón (${publicaciones.size}) →",
                    fontSize = 12.5.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Gold,
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable(onClick = onVerTodo)
                        .padding(vertical = 4.dp)
                )
            }
        }
    }
}

@Composable
fun TablonScreen(onVolver: () -> Unit) {
    val scope = rememberCoroutineScope()
    var actualizando by remember { mutableStateOf(false) }
    val publicaciones = DatosRemotos.tablon ?: emptyList()

    LaunchedEffect(Unit) { DatosRemotos.recargarTablon() }

    LazyColumn(Modifier.fillMaxSize()) {
        item(key = "encabezado") {
            EncabezadoVolver("📌 Tablón del club", "Avisos, eventos y promociones", onVolver)
        }
        item(key = "actualizar") {
            Column(Modifier.padding(horizontal = 20.dp)) {
                BotonSecundario(if (actualizando) "Actualizando…" else "🔄 Actualizar") {
                    if (!actualizando) {
                        actualizando = true
                        scope.launch {
                            DatosRemotos.recargarTablon()
                            actualizando = false
                        }
                    }
                }
                Spacer(Modifier.height(14.dp))
            }
        }
        if (publicaciones.isEmpty()) {
            item(key = "vacio") {
                Column(Modifier.padding(horizontal = 20.dp)) {
                    TarjetaOro(Modifier.fillMaxWidth()) {
                        Text(
                            "Todavía no hay publicaciones en el tablón.",
                            fontSize = 12.5.sp, color = Olimpos.Muted
                        )
                    }
                }
            }
        }
        items(publicaciones, key = { it.id }) { p ->
            Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 10.dp)) {
                TarjetaPublicacion(p, compacta = false, onClick = null)
            }
        }
        item(key = "pie") { Spacer(Modifier.height(24.dp)) }
    }
}

@Composable
private fun TarjetaPublicacion(p: PublicacionTablon, compacta: Boolean, onClick: (() -> Unit)?) {
    val esImportante = p.categoria == CategoriaTablon.IMPORTANTE
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(18.dp))
            .background(if (esImportante) Olimpos.GoldSoft else Olimpos.Card)
            .border(1.dp, if (esImportante) Olimpos.Gold.copy(alpha = 0.45f) else Olimpos.Line, RoundedCornerShape(18.dp))
            .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier)
            .padding(15.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            ChipOro("${p.categoria.emoji} ${p.categoria.etiqueta}")
            if (p.fijado) {
                Spacer(Modifier.width(8.dp))
                Text("📌 Fijado", fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Muted)
            }
            Spacer(Modifier.weight(1f))
            if (p.creadoMs > 0) Text(fechaLegible(p.creadoMs), fontSize = 10.sp, color = Olimpos.Muted)
        }
        Spacer(Modifier.height(9.dp))
        Text(p.titulo, fontSize = 15.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
        Spacer(Modifier.height(4.dp))
        Text(
            p.mensaje, fontSize = 12.5.sp, lineHeight = 17.sp, color = Olimpos.Muted,
            maxLines = if (compacta) 2 else Int.MAX_VALUE,
            overflow = TextOverflow.Ellipsis
        )
        if (!compacta && p.autor.isNotBlank()) {
            Spacer(Modifier.height(8.dp))
            Text("— ${p.autor}", fontSize = 10.5.sp, color = Olimpos.Muted)
        }
    }
}
