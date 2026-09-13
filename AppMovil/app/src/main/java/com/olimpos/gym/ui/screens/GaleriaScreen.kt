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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.EJERCICIOS_CATALOGO_EJEMPLO
import com.olimpos.gym.data.EjercicioCatalogo
import com.olimpos.gym.ui.theme.Olimpos

/** Galería de ejercicios: catálogo curado por el Dueño/Entrenador desde el
 *  sistema de empleados (igual patrón que el catálogo de dietas). Buscador
 *  arriba + grilla de 3 columnas; tocar un ejercicio abre su detalle. */
@Composable
fun GaleriaScreen(onVolver: () -> Unit) {
    // Precargado desde que se entró a la app (ver DatosRemotos/MainActivity)
    // — nada de mostrar el catálogo de ejemplo para reemplazarlo un instante después.
    val ejercicios = DatosRemotos.ejercicios?.takeIf { it.isNotEmpty() } ?: EJERCICIOS_CATALOGO_EJEMPLO

    var seleccionado by remember { mutableStateOf<EjercicioCatalogo?>(null) }
    seleccionado?.let {
        EjercicioCatalogoDetalleScreen(it, onVolver = { seleccionado = null })
        return
    }

    var busqueda by remember { mutableStateOf("") }
    val query = busqueda.trim().lowercase()

    // Etiquetas de todos los ejercicios (Empuje, Piernas, Fuerza, etc.) para
    // filtrar con un toque en vez de tener que escribir — se arman solas a
    // partir del catálogo real, no hay una lista fija que mantener aparte.
    val tagsDisponibles = remember(ejercicios) { ejercicios.flatMap { it.tags }.distinct().sorted() }
    var tagSeleccionado by remember { mutableStateOf<String?>(null) }

    val filtrados = ejercicios.filter { ej ->
        val coincideTexto = query.isEmpty() ||
            ej.nombre.lowercase().contains(query) ||
            ej.tags.any { it.lowercase().contains(query) }
        val coincideTag = tagSeleccionado == null || ej.tags.contains(tagSeleccionado)
        coincideTexto && coincideTag
    }

    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver("Galería", "Ejercicios cargados por tu entrenador", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 4.dp)) {
            CampoBusqueda(busqueda, { busqueda = it }, "Buscar ejercicio u objetivo…")
            if (tagsDisponibles.isNotEmpty()) {
                Spacer(Modifier.height(10.dp))
                FilaChips {
                    ChipSeleccionable("Todos", tagSeleccionado == null) { tagSeleccionado = null }
                    tagsDisponibles.forEach { tag ->
                        ChipSeleccionable(tag, tagSeleccionado == tag) {
                            tagSeleccionado = if (tagSeleccionado == tag) null else tag
                        }
                    }
                }
            }
        }

        Column(
            Modifier
                .weight(1f)
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(top = 12.dp, bottom = 26.dp)
        ) {
            if (filtrados.isEmpty()) {
                EstadoVacioGaleria(
                    when {
                        ejercicios.isEmpty() -> "Todavía no hay ejercicios publicados."
                        query.isNotEmpty() && tagSeleccionado != null -> "Sin resultados para \"$busqueda\" en $tagSeleccionado."
                        query.isNotEmpty() -> "Sin resultados para \"$busqueda\"."
                        else -> "Ningún ejercicio tiene la etiqueta \"$tagSeleccionado\"."
                    }
                )
            } else {
                GridEjercicios(filtrados) { seleccionado = it }
            }
        }
    }
}

@Composable
private fun GridEjercicios(items: List<EjercicioCatalogo>, onVer: (EjercicioCatalogo) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        items.chunked(3).forEach { fila ->
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                fila.forEach { ej -> TarjetaEjercicio(ej, Modifier.weight(1f)) { onVer(ej) } }
                repeat(3 - fila.size) { Spacer(Modifier.weight(1f)) }
            }
        }
    }
}

@Composable
private fun TarjetaEjercicio(ejercicio: EjercicioCatalogo, modifier: Modifier, onClick: () -> Unit) {
    Column(
        modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
    ) {
        Box(
            Modifier
                .fillMaxWidth()
                .height(90.dp)
                .clip(RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp))
                .background(Olimpos.GoldSoft),
            contentAlignment = Alignment.Center
        ) {
            CuerpoMuscularMini(zonasActivas = ejercicio.puntos.map { it.zona }.toSet(), tamano = 42.dp)
        }
        Column(Modifier.padding(9.dp)) {
            Text(
                ejercicio.nombre, fontSize = 11.5.sp, fontWeight = FontWeight.ExtraBold,
                color = Olimpos.Cream, maxLines = 1, overflow = TextOverflow.Ellipsis
            )
            if (ejercicio.descripcion.isNotBlank()) {
                Spacer(Modifier.height(3.dp))
                Text(
                    ejercicio.descripcion, fontSize = 9.5.sp, lineHeight = 12.sp, color = Olimpos.Muted,
                    maxLines = 2, overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}

@Composable
private fun EstadoVacioGaleria(mensaje: String) {
    Box(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
            .padding(18.dp)
    ) {
        Text(
            mensaje, fontSize = 12.sp, color = Olimpos.Muted,
            textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth()
        )
    }
}
