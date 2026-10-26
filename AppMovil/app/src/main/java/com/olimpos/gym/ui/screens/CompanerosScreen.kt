package com.olimpos.gym.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Image
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.Companero
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.NivelMuscular
import com.olimpos.gym.data.SocioRango
import com.olimpos.gym.data.agregarCompanero
import com.olimpos.gym.data.eliminarCompanero
import com.olimpos.gym.data.formatearAntiguedad
import com.olimpos.gym.data.socioActualId
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch
import kotlin.math.roundToInt

/** Días juntos que pide el logro "Espíritu de equipo". */
private const val DIAS_LOGRO_EQUIPO = 5

/** Posición del nivel en la Escalera del Olimpo (para comparar dos socios). */
private fun orden(n: NivelMuscular): Int = n.rango.ordinal * 3 + (n.nivel - 1)

private fun comparacion(suyo: NivelMuscular?, mio: NivelMuscular?): Pair<String, Pastel>? {
    if (suyo == null || mio == null) return null
    val dif = orden(suyo) - orden(mio)
    return when {
        dif == 0 -> "Mismo nivel que vos" to Pastel.AZUL
        dif > 0 -> "$dif nivel${if (dif == 1) "" else "es"} arriba tuyo" to Pastel.NARANJA
        else -> "${-dif} nivel${if (dif == -1) "" else "es"} abajo tuyo" to Pastel.VERDE
    }
}

/** Mis compañeros: con quién entrenás. Se agregan desde acá (o desde un
 *  perfil de Clasificación) sin que el otro tenga que aceptar — solo se
 *  muestra lo que ya es público en Clasificación. Cada compañero se compara
 *  con vos (rango, kilos, mapa corporal) y hay un ranking entre ustedes. */
@Composable
fun CompanerosScreen(onVolver: () -> Unit) {
    val scope = rememberCoroutineScope()
    val companeros = DatosRemotos.companeros ?: emptyList()
    val rangos = DatosRemotos.rangosSocios ?: emptyList()
    val miId = socioActualId()
    val yo = rangos.firstOrNull { it.socioId == miId }
    val dias = DatosRemotos.diasEntrenadosConCompaneros
    var pestana by remember { mutableIntStateOf(0) }
    var agregando by remember { mutableStateOf(false) }
    var viendo by remember { mutableStateOf<Companero?>(null) }
    var aQuitar by remember { mutableStateOf<Companero?>(null) }

    fun rangoDe(c: Companero): SocioRango? = rangos.firstOrNull { it.socioId == c.socioId }

    val enDetalle = viendo
    Box(Modifier.fillMaxSize().background(Olimpos.FondoA)) {
        when {
            agregando -> AgregarCompaneroScreen(
                candidatos = rangos.filter { r -> r.socioId != miId && companeros.none { it.socioId == r.socioId } },
                onVolver = { agregando = false },
                onAgregar = { r ->
                    scope.launch {
                        agregarCompanero(r.socioId, r.nombre)
                        DatosRemotos.recargarCompaneros()
                    }
                }
            )
            enDetalle != null -> DetalleCompanero(
                companero = enDetalle, suyo = rangoDe(enDetalle), yo = yo,
                onVolver = { viendo = null },
                onQuitar = { aQuitar = enDetalle }
            )
            else -> Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
                EncabezadoArena(
                    "Mis compañeros", "Entrená acompañado y compará tu progreso.", onVolver,
                    derecha = { BotonChico("+ Agregar") { agregando = true } }
                )
                Column(Modifier.padding(horizontal = 20.dp).padding(top = 6.dp, bottom = 26.dp)) {
                    // ── Resumen ──
                    val mejor = companeros.mapNotNull { rangoDe(it)?.nivel }.maxByOrNull { orden(it) }
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        DatoChico("${companeros.size}", "Compañeros", Modifier.weight(1f))
                        DatoChico("$dias", "Días juntos", Modifier.weight(1f))
                        DatoChico(mejor?.etiquetaCompleta ?: "—", "Mejor rango", Modifier.weight(1f))
                    }

                    // ── Logro "Espíritu de equipo" ──
                    Spacer(Modifier.height(12.dp))
                    TarjetaLisa(Modifier.fillMaxWidth()) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            IconoCuadrado("👥")
                            Spacer(Modifier.width(12.dp))
                            Column(Modifier.weight(1f)) {
                                Text("Espíritu de equipo", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
                                Text(
                                    if (dias >= DIAS_LOGRO_EQUIPO) "¡Logro conseguido! Entrenaron juntos $dias días."
                                    else "${minOf(dias, DIAS_LOGRO_EQUIPO)} de $DIAS_LOGRO_EQUIPO días: cuenta cuando vos y un compañero cargan una marca el mismo día.",
                                    fontSize = 11.5.sp, color = Olimpos.Muted, lineHeight = 15.sp
                                )
                            }
                        }
                        Spacer(Modifier.height(10.dp))
                        BarraArena(dias / DIAS_LOGRO_EQUIPO.toFloat())
                    }

                    Spacer(Modifier.height(14.dp))
                    PestanasPildora(listOf("Compañeros", "Ranking"), pestana, { pestana = it })
                    Spacer(Modifier.height(12.dp))

                    if (companeros.isEmpty()) {
                        TarjetaLisa(Modifier.fillMaxWidth()) {
                            Text(
                                "Todavía no agregaste a nadie. Tocá \"+ Agregar\" para buscar a un socio del club.",
                                fontSize = 12.5.sp, color = Olimpos.Muted, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth()
                            )
                        }
                    } else if (pestana == 0) {
                        Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
                            companeros.forEach { c -> FilaCompanero(c, rangoDe(c), yo) { viendo = c } }
                        }
                    } else {
                        RankingGrupo(companeros.map { it to rangoDe(it) }, yo)
                    }
                }
            }
        }

        AnimatedVisibility(visible = aQuitar != null, enter = fadeIn(), exit = fadeOut()) {
            aQuitar?.let { c ->
                ConfirmarQuitar(
                    nombre = c.nombre,
                    onCancelar = { aQuitar = null },
                    onConfirmar = {
                        aQuitar = null
                        viendo = null
                        scope.launch {
                            eliminarCompanero(c.socioId)
                            DatosRemotos.recargarCompaneros()
                        }
                    }
                )
            }
        }
    }
}

@Composable
private fun BotonChico(texto: String, onClick: () -> Unit) {
    Box(
        Modifier
            .padding(top = 2.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(Olimpos.Gold)
            .clickable(onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) { Text(texto, fontSize = 12.5.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Dark) }
}

@Composable
private fun DatoChico(valor: String, etiqueta: String, modifier: Modifier) {
    TarjetaLisa(modifier, padding = 10.dp) {
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(valor, fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(etiqueta, fontSize = 11.sp, color = Olimpos.Muted, maxLines = 1)
        }
    }
}

@Composable
private fun InsigniaRango(nivel: NivelMuscular?, tamano: Int = 30) {
    if (nivel != null) {
        Image(painterResource(iconoDeRango(nivel)), contentDescription = nivel.etiquetaCompleta, modifier = Modifier.size(tamano.dp))
    }
}

@Composable
private fun FilaCompanero(c: Companero, r: SocioRango?, yo: SocioRango?, onClick: () -> Unit) {
    TarjetaLisa(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).clickable(onClick = onClick), padding = 12.dp) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            AvatarInicial(c.nombre.take(1).uppercase(), tamano = 40)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(c.nombre, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(
                    r?.let { "${it.nivel.etiquetaCompleta} · ${it.kgTotales.roundToInt()} kg en total" } ?: "Sin marcas en la clasificación",
                    fontSize = 11.5.sp, color = Olimpos.Muted, maxLines = 1
                )
                comparacion(r?.nivel, yo?.nivel)?.let { (texto, pastel) ->
                    Spacer(Modifier.height(5.dp))
                    ChipSuave(texto, pastel)
                }
            }
            InsigniaRango(r?.nivel)
            Spacer(Modifier.width(4.dp))
            FlechaFila()
        }
    }
}

private data class FilaRanking(val nombre: String, val r: SocioRango?, val esYo: Boolean)

/** Ranking entre vos y tus compañeros, por rango general. */
@Composable
private fun RankingGrupo(lista: List<Pair<Companero, SocioRango?>>, yo: SocioRango?) {
    val filas = (lista.map { FilaRanking(it.first.nombre, it.second, false) } +
        listOfNotNull(yo?.let { FilaRanking("Vos", it, true) }))
        .sortedWith(compareByDescending<FilaRanking> { it.r?.nivel?.let(::orden) ?: -1 }.thenByDescending { it.r?.kgTotales ?: 0f })
    TarjetaLisa(Modifier.fillMaxWidth(), padding = 6.dp) {
        filas.forEachIndexed { i, f ->
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(10.dp))
                    .background(if (f.esYo) Olimpos.GoldSoft else androidx.compose.ui.graphics.Color.Transparent)
                    .padding(horizontal = 10.dp, vertical = 9.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("${i + 1}", fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Muted, modifier = Modifier.width(24.dp))
                AvatarInicial(f.nombre.take(1).uppercase(), tamano = 30)
                Spacer(Modifier.width(10.dp))
                Text(f.nombre, fontSize = 13.5.sp, fontWeight = if (f.esYo) FontWeight.SemiBold else FontWeight.Medium, color = Olimpos.Cream, modifier = Modifier.weight(1f), maxLines = 1)
                Text(f.r?.nivel?.etiquetaCompleta ?: "Sin marcas", fontSize = 12.sp, color = if (f.r != null) Olimpos.GoldLight else Olimpos.Muted)
                Spacer(Modifier.width(8.dp))
                InsigniaRango(f.r?.nivel, 24)
            }
        }
    }
    if (yo == null) {
        Text("Cargá marcas en 3 ejercicios para aparecer vos también en el ranking.", fontSize = 11.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 8.dp))
    }
}

/** Perfil de un compañero comparado con el tuyo. */
@Composable
private fun DetalleCompanero(companero: Companero, suyo: SocioRango?, yo: SocioRango?, onVolver: () -> Unit, onQuitar: () -> Unit) {
    val corto = companero.nombre.substringBefore(" ")
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        EncabezadoArena(companero.nombre, suyo?.let { formatearAntiguedad(it.creadoMs) } ?: "Compañero de entrenamiento", onVolver)
        Column(Modifier.padding(horizontal = 20.dp).padding(top = 6.dp, bottom = 26.dp)) {
            comparacion(suyo?.nivel, yo?.nivel)?.let { (texto, pastel) ->
                ChipSuave(texto, pastel)
                Spacer(Modifier.height(12.dp))
            }

            // ── Los dos mapas corporales lado a lado ──
            TarjetaLisa(Modifier.fillMaxWidth()) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                    listOf(corto to suyo, "Vos" to yo).forEach { (nombre, r) ->
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CuerpoMuscularRangosMini(rangoPorZona = r?.rangoPorZona ?: emptyMap(), tamano = 104.dp)
                            Spacer(Modifier.height(6.dp))
                            Text(nombre, fontSize = 12.5.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
                            Text(r?.nivel?.etiquetaCompleta ?: "Sin marcas", fontSize = 11.sp, color = Olimpos.Muted)
                        }
                    }
                }
            }

            // ── Comparación en números ──
            Spacer(Modifier.height(12.dp))
            TarjetaLisa(Modifier.fillMaxWidth(), padding = 0.dp) {
                FilaComparacion("", corto, "Vos", encabezado = true)
                FilaComparacion("Rango general", suyo?.nivel?.etiquetaCompleta ?: "—", yo?.nivel?.etiquetaCompleta ?: "—")
                FilaComparacion("Kilos en total", suyo?.let { "${it.kgTotales.roundToInt()} kg" } ?: "—", yo?.let { "${it.kgTotales.roundToInt()} kg" } ?: "—")
                FilaComparacion(
                    "Mejor levantamiento",
                    suyo?.mejorLevantamiento?.let { "${"%.1f".format(it.vecesPesoCorporal)}× su peso · ${it.ejercicio}" } ?: "—",
                    yo?.mejorLevantamiento?.let { "${"%.1f".format(it.vecesPesoCorporal)}× tu peso · ${it.ejercicio}" } ?: "—"
                )
                FilaComparacion(
                    "Marcas verificadas",
                    suyo?.let { if (it.verificado) "Sí ✓" else "Pendientes" } ?: "—",
                    yo?.let { if (it.verificado) "Sí ✓" else "Pendientes" } ?: "—"
                )
            }
            if (suyo == null) {
                Text(
                    "$corto todavía no tiene marcas en la clasificación (o eligió no aparecer).",
                    fontSize = 11.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 8.dp)
                )
            }

            Spacer(Modifier.height(18.dp))
            Box(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .border(1.dp, Olimpos.Red.copy(alpha = 0.45f), RoundedCornerShape(12.dp))
                    .clickable(onClick = onQuitar)
                    .padding(vertical = 12.dp),
                contentAlignment = Alignment.Center
            ) { Text("Quitar de mis compañeros", fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Red) }
        }
    }
}

@Composable
private fun FilaComparacion(dato: String, suyo: String, mio: String, encabezado: Boolean = false) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(dato, fontSize = 12.sp, color = Olimpos.Muted, modifier = Modifier.weight(1f))
        listOf(suyo, mio).forEach {
            Text(
                it, fontSize = if (encabezado) 12.sp else 12.5.sp, textAlign = TextAlign.End, maxLines = 2,
                fontWeight = if (encabezado) FontWeight.SemiBold else FontWeight.Medium,
                color = if (encabezado) Olimpos.Muted else Olimpos.Cream,
                modifier = Modifier.weight(1f)
            )
        }
    }
}

/** Buscar socios del club (los que aparecen en Clasificación) para agregar. */
@Composable
private fun AgregarCompaneroScreen(candidatos: List<SocioRango>, onVolver: () -> Unit, onAgregar: (SocioRango) -> Unit) {
    var busqueda by remember { mutableStateOf("") }
    var agregados by remember { mutableStateOf(setOf<String>()) }
    val q = busqueda.trim().lowercase()
    val filtrados = candidatos.filter { q.isEmpty() || it.nombre.lowercase().contains(q) }
        .sortedByDescending { orden(it.nivel) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        EncabezadoArena("Agregar compañero", "Socios del club que aparecen en la clasificación.", onVolver)
        Column(Modifier.padding(horizontal = 20.dp).padding(top = 6.dp, bottom = 26.dp)) {
            CampoBusqueda(busqueda, { busqueda = it }, "Buscar por nombre…")
            Spacer(Modifier.height(12.dp))
            if (filtrados.isEmpty()) {
                Text(
                    if (candidatos.isEmpty()) "No hay más socios para agregar por ahora." else "Nadie se llama así.",
                    fontSize = 12.5.sp, color = Olimpos.Muted
                )
            }
            Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
                filtrados.forEach { r ->
                    val listo = r.socioId in agregados
                    TarjetaLisa(Modifier.fillMaxWidth(), padding = 12.dp) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            AvatarInicial(r.nombre.take(1).uppercase(), tamano = 38)
                            Spacer(Modifier.width(12.dp))
                            Column(Modifier.weight(1f)) {
                                Text(r.nombre, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream, maxLines = 1)
                                Text(r.nivel.etiquetaCompleta, fontSize = 11.5.sp, color = Olimpos.Muted)
                            }
                            Box(
                                Modifier
                                    .width(88.dp)
                                    .clip(RoundedCornerShape(10.dp))
                                    .background(if (listo) Olimpos.Superficie2 else Olimpos.Gold)
                                    .clickable(enabled = !listo) { agregados = agregados + r.socioId; onAgregar(r) }
                                    .padding(vertical = 8.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    if (listo) "Agregado ✓" else "Agregar", fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
                                    color = if (listo) Olimpos.Muted else Olimpos.Dark
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ConfirmarQuitar(nombre: String, onCancelar: () -> Unit, onConfirmar: () -> Unit) {
    Box(
        Modifier.fillMaxSize().background(Olimpos.Dark.copy(alpha = 0.5f)).clickable(onClick = onCancelar),
        contentAlignment = Alignment.Center
    ) {
        Column(
            Modifier
                .padding(horizontal = 36.dp)
                .clip(RoundedCornerShape(20.dp))
                .background(Olimpos.Card)
                .clickable(enabled = false) {}
                .padding(22.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("¿Quitar a $nombre?", fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream, textAlign = TextAlign.Center)
            Spacer(Modifier.height(6.dp))
            Text(
                "Deja de aparecer en tu lista y en tu ranking. Lo podés volver a agregar cuando quieras.",
                fontSize = 12.5.sp, color = Olimpos.Muted, textAlign = TextAlign.Center
            )
            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                BotonSecundario("Cancelar", Modifier.width(118.dp)) { onCancelar() }
                Box(
                    Modifier.width(118.dp).clip(RoundedCornerShape(16.dp)).background(Olimpos.Red).clickable(onClick = onConfirmar).padding(vertical = 14.dp),
                    contentAlignment = Alignment.Center
                ) { Text("Quitar", fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.TintaClara) }
            }
        }
    }
}
