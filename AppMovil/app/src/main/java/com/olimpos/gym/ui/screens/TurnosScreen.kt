package com.olimpos.gym.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.background
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.CLASES_SEMANA
import com.olimpos.gym.data.ClaseSemana
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.ui.theme.Olimpos
import java.util.Calendar

private val DIAS = listOf("LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM")

/** 0 = lunes … 6 = domingo, para el día de hoy. */
private fun indiceHoy(): Int = (Calendar.getInstance().get(Calendar.DAY_OF_WEEK) + 5) % 7

/** Día de la semana de la clase (las que dicen "HOY" son las de hoy). */
private fun indiceDia(clase: ClaseSemana): Int =
    if (clase.dia == "HOY") indiceHoy() else DIAS.indexOf(clase.dia).takeIf { it >= 0 } ?: 7

/** Minutos que faltan para la clase dentro de la semana actual (negativo = ya pasó). */
private fun minutosHasta(clase: ClaseSemana): Int {
    val ahora = Calendar.getInstance()
    val (h, m) = clase.hora.split(":").let { (it.getOrNull(0)?.toIntOrNull() ?: 0) to (it.getOrNull(1)?.toIntOrNull() ?: 0) }
    val dias = indiceDia(clase) - indiceHoy()
    return dias * 1440 + (h * 60 + m) - (ahora.get(Calendar.HOUR_OF_DAY) * 60 + ahora.get(Calendar.MINUTE))
}

private fun nombreDia(clase: ClaseSemana): String = when (val i = indiceDia(clase)) {
    indiceHoy() -> "Hoy"
    (indiceHoy() + 1) % 7 -> "Mañana"
    else -> listOf("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo").getOrElse(i) { clase.dia }
}

/** Mis turnos y reservas: todo lo de las clases grupales de la semana —
 *  las que reservaste (con la próxima destacada), todas las clases para
 *  reservar o cancelar, y los lugares que quedan. Las reservas son de la
 *  semana en curso (la API las reinicia solas cada lunes). */
@Composable
fun TurnosScreen(onVolver: () -> Unit) {
    LaunchedEffect(Unit) { DatosRemotos.recargarReservasClase() }
    val reservas = DatosRemotos.reservasClase ?: emptyList()
    val cupos = DatosRemotos.cuposClases
    val capacidades = DatosRemotos.capacidadesClases
    val clases = remember { CLASES_SEMANA.sortedWith(compareBy({ indiceDia(it) }, { it.hora })) }
    val mias = clases.filter { c -> reservas.any { it.claseId == c.id } }
    val proxima = mias.filter { minutosHasta(it) > -60 }.minByOrNull { minutosHasta(it) }
    val libres = clases.sumOf { c -> ((capacidades[c.id] ?: c.cupo) - (cupos[c.id] ?: 0)).coerceAtLeast(0) }
    var filtro by remember { mutableStateOf<Int?>(null) }

    Column(Modifier.fillMaxSize().background(Olimpos.FondoA).verticalScroll(rememberScrollState())) {
        EncabezadoArena("Mis turnos y reservas", "Las clases grupales de esta semana.", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(top = 6.dp, bottom = 26.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Dato("${mias.size}", "Reservadas", Modifier.weight(1f))
                Dato("${clases.size}", "Clases", Modifier.weight(1f))
                Dato("$libres", "Lugares libres", Modifier.weight(1f))
            }

            // ── Próxima clase reservada ──
            Spacer(Modifier.height(14.dp))
            TarjetaLisa(Modifier.fillMaxWidth()) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconoCuadrado("📅")
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text("Tu próxima clase", fontSize = 11.5.sp, color = Olimpos.Muted)
                        if (proxima != null) {
                            Text(proxima.nombre, fontSize = 15.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
                            Text("${nombreDia(proxima)} · ${proxima.hora} · ${proxima.lugar}", fontSize = 12.sp, color = Olimpos.Muted)
                        } else {
                            Text("Sin clases reservadas por delante", fontSize = 14.sp, fontWeight = FontWeight.Medium, color = Olimpos.Cream)
                            Text("Reservá un lugar en alguna de las clases de abajo.", fontSize = 12.sp, color = Olimpos.Muted)
                        }
                    }
                }
            }

            // ── Todas las clases, filtrables por día ──
            SeccionLabel("Clases de la semana")
            val diasConClase = clases.map { indiceDia(it) }.distinct().filter { it < 7 }
            FilaChips {
                ChipArena("Todas", filtro == null) { filtro = null }
                diasConClase.forEach { d ->
                    val etiqueta = if (d == indiceHoy()) "Hoy" else DIAS[d].lowercase().replaceFirstChar { it.uppercase() }
                    ChipArena(etiqueta, filtro == d) { filtro = if (filtro == d) null else d }
                }
            }
            Spacer(Modifier.height(12.dp))
            val visibles = clases.filter { filtro == null || indiceDia(it) == filtro }
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                visibles.forEach { clase -> TarjetaClase(clase, reservas, cupos, capacidades) }
            }
            Spacer(Modifier.height(12.dp))
            Text(
                "Tocá una clase para ver de qué se trata. Las reservas valen para esta semana y las podés cancelar desde acá.",
                fontSize = 11.5.sp, color = Olimpos.Muted, lineHeight = 16.sp, textAlign = TextAlign.Start
            )
        }
    }
}

@Composable
private fun Dato(valor: String, etiqueta: String, modifier: Modifier) {
    TarjetaLisa(modifier, padding = 12.dp) {
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(valor, fontSize = 20.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
            Text(etiqueta, fontSize = 11.sp, color = Olimpos.Muted, maxLines = 1)
        }
    }
}
