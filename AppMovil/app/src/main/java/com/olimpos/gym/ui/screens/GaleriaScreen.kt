package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
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
import com.olimpos.gym.data.imagenDeEjercicio
import com.olimpos.gym.ui.theme.Olimpos

/** Ejercicios: el catálogo que publican el Dueño/Entrenador desde el sistema
 *  de empleados, con los mismos dibujos. Buscador + filtros por etiqueta y
 *  una fila por ejercicio con sus músculos; tocar uno abre su detalle. */
@Composable
fun GaleriaScreen(onVolver: () -> Unit) {
    val ejercicios = DatosRemotos.ejercicios?.takeIf { it.isNotEmpty() } ?: EJERCICIOS_CATALOGO_EJEMPLO

    var seleccionado by remember { mutableStateOf<EjercicioCatalogo?>(null) }
    seleccionado?.let {
        EjercicioCatalogoDetalleScreen(it, onVolver = { seleccionado = null })
        return
    }

    var busqueda by remember { mutableStateOf("") }
    val query = busqueda.trim().lowercase()
    // Los filtros salen solos de las etiquetas reales del catálogo.
    val tags = remember(ejercicios) { ejercicios.flatMap { it.tags }.distinct().sorted() }
    var tag by remember { mutableStateOf<String?>(null) }

    val filtrados = ejercicios.filter { ej ->
        (query.isEmpty() || ej.nombre.lowercase().contains(query) ||
            ej.tags.any { it.lowercase().contains(query) } ||
            ej.puntos.any { it.nombre.lowercase().contains(query) }) &&
            (tag == null || tag in ej.tags)
    }

    Column(Modifier.fillMaxSize().background(CA.fondo)) {
        EncabezadoArena("Ejercicios", "Explorá todos los ejercicios disponibles.", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(top = 4.dp)) {
            CampoBusqueda(busqueda, { busqueda = it }, "Buscar ejercicio…")
            if (tags.isNotEmpty()) {
                Spacer(Modifier.height(10.dp))
                FilaChips {
                    ChipArena("Todos", tag == null) { tag = null }
                    tags.forEach { t -> ChipArena(t, tag == t) { tag = if (tag == t) null else t } }
                }
            }
        }

        LazyColumn(
            Modifier.weight(1f).fillMaxWidth(),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(start = 20.dp, end = 20.dp, top = 12.dp, bottom = 26.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            if (filtrados.isEmpty()) {
                item {
                    TarjetaLisa(Modifier.fillMaxWidth()) {
                        Text(
                            if (query.isNotEmpty()) "Sin resultados para \"$busqueda\"." else "Ningún ejercicio con la etiqueta \"$tag\".",
                            fontSize = 12.sp, color = CA.suave, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }
            items(filtrados, key = { it.id }) { ej -> FilaEjercicio(ej) { seleccionado = ej } }
        }
    }
}

@Composable
private fun FilaEjercicio(ej: EjercicioCatalogo, onClick: () -> Unit) {
    TarjetaLisa(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).clickable(onClick = onClick),
        padding = 8.dp
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            ImagenEjercicio(imagenDeEjercicio(ej.id, ej.nombre), 64.dp, ej.puntos.map { it.zona }.toSet())
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(ej.nombre, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Spacer(Modifier.height(6.dp))
                // Músculos trabajados: el primero (el protagonista) resaltado.
                val musculos = ej.puntos.distinctBy { it.nombre }
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    musculos.take(2).forEach { p -> ChipSuave(p.nombre, pastelDeZona(p.zona)) }
                    if (musculos.size > 2) ChipSuave("+${musculos.size - 2}", Pastel.GRIS)
                }
            }
            Chevron()
            Spacer(Modifier.width(6.dp))
        }
    }
}
