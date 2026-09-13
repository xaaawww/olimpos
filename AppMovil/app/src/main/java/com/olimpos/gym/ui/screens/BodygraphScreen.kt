package com.olimpos.gym.ui.screens

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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.ui.res.painterResource
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.EVOLUCION_PESO
import com.olimpos.gym.data.GrupoMuscular
import com.olimpos.gym.data.MIS_MARCAS
import com.olimpos.gym.data.NivelMuscular
import com.olimpos.gym.data.ZonaMuscular
import com.olimpos.gym.data.nivelDesdePuntaje
import com.olimpos.gym.data.resumenMuscular
import com.olimpos.gym.ui.theme.Olimpos

/** Bodygraph: el rango/nivel de cada músculo (no "qué trabajaste hoy"), a
 *  partir de las marcas cargadas en la Calculadora — ver [resumenMuscular].
 *  La insignia de la esquina indica si esas marcas ya fueron verificadas
 *  por un entrenador o el dueño (sistema de empleados), para que no se
 *  pueda "hacer trampa" cargando pesos falsos sin que nadie lo note. */
@Composable
fun BodygraphScreen(onVolver: () -> Unit) {
    // DatosRemotos ya arrancó la carga apenas se entró a la app (ver
    // MainActivity) — acá solo se lee lo que haya, sin volver a pedirlo ni
    // mostrar primero el catálogo de ejemplo para reemplazarlo después.
    val marcas = DatosRemotos.marcas?.takeIf { it.isNotEmpty() } ?: MIS_MARCAS

    val pesoCorporal = EVOLUCION_PESO.lastOrNull()?.valor ?: 80f
    val resumen = remember(marcas) { resumenMuscular(marcas, pesoCorporal) }
    val nivelesPorZona = remember(resumen) {
        ZonaMuscular.entries.associateWith { zona -> resumen.puntajes[zona]?.let(::nivelDesdePuntaje) }
    }
    // Rango general = promedio del puntaje de las 19 zonas (las que todavía
    // no tienen marcas suman 0, como corresponde a "no entrenado aún").
    val nivelGeneral = remember(resumen) {
        val promedio = ZonaMuscular.entries.sumOf { (resumen.puntajes[it] ?: 0f).toDouble() } / ZonaMuscular.entries.size
        nivelDesdePuntaje(promedio.toFloat())
    }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("Bodygraph", "El nivel de cada músculo, según tus marcas", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            TarjetaOro(Modifier.fillMaxWidth()) {
                Box(Modifier.fillMaxWidth()) {
                    Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                        InsigniaRangoGeneral(nivelGeneral)
                        Spacer(Modifier.height(14.dp))
                        CuerpoMuscularRangos(rangoPorZona = nivelesPorZona.mapValues { it.value?.rango })
                    }
                    InsigniaVerificado(
                        tieneMarcas = resumen.tieneMarcas,
                        verificado = resumen.verificado,
                        modifier = Modifier.align(Alignment.TopEnd)
                    )
                }
            }

            SeccionLabel("Rankings de músculo")
            var expandidos by remember { mutableStateOf(setOf<GrupoMuscular>()) }
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                GrupoMuscular.entries.forEach { grupo ->
                    FilaGrupoMuscular(
                        grupo = grupo,
                        nivelesPorZona = nivelesPorZona,
                        expandido = grupo in expandidos,
                        onToggle = {
                            expandidos = if (grupo in expandidos) expandidos - grupo else expandidos + grupo
                        }
                    )
                }
            }
        }
    }
}

@Composable
private fun FilaGrupoMuscular(
    grupo: GrupoMuscular,
    nivelesPorZona: Map<ZonaMuscular, NivelMuscular?>,
    expandido: Boolean,
    onToggle: () -> Unit
) {
    val completados = grupo.zonas.count { nivelesPorZona[it] != null }
    Column {
        Row(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(if (expandido) Olimpos.GoldSoft else Olimpos.Card)
                .border(1.dp, if (expandido) Olimpos.Gold.copy(alpha = 0.35f) else Olimpos.Line, RoundedCornerShape(14.dp))
                .clickable(onClick = onToggle)
                .padding(horizontal = 14.dp, vertical = 13.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                Modifier
                    .size(38.dp)
                    .clip(RoundedCornerShape(11.dp))
                    .background(Olimpos.Superficie2),
                contentAlignment = Alignment.Center
            ) { Text(grupo.emoji, fontSize = 17.sp) }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(grupo.etiqueta, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream)
                Text(
                    "$completados/${grupo.zonas.size} completado" + if (completados == 1) "" else "s",
                    fontSize = 11.sp, color = Olimpos.Muted
                )
            }
            Text(
                if (expandido) "⌃" else "⌄",
                fontSize = 16.sp, fontWeight = FontWeight.Black, color = Olimpos.Muted
            )
        }
        androidx.compose.animation.AnimatedVisibility(visible = expandido) {
            Column(
                Modifier.padding(top = 8.dp, start = 10.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                grupo.zonas.forEach { zona -> FilaNivelMuscular(zona, nivelesPorZona[zona]) }
            }
        }
    }
}

@Composable
private fun InsigniaRangoGeneral(nivel: NivelMuscular) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Image(
            painter = painterResource(iconoDeRango(nivel)),
            contentDescription = nivel.etiquetaCompleta,
            modifier = Modifier.height(84.dp)
        )
        Spacer(Modifier.height(4.dp))
        Text(
            "RANGO GENERAL", fontSize = 9.5.sp, fontWeight = FontWeight.ExtraBold,
            letterSpacing = 1.2.sp, color = Olimpos.Muted
        )
        Text(
            nivel.etiquetaCompleta, fontSize = 15.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream
        )
    }
}

@Composable
private fun InsigniaVerificado(tieneMarcas: Boolean, verificado: Boolean, modifier: Modifier = Modifier) {
    if (!tieneMarcas) return
    val (texto, color) = if (verificado) "Verificado ✓" to Olimpos.Green else "No verificado" to Olimpos.Red
    Row(
        modifier
            .clip(RoundedCornerShape(20.dp))
            .background(color.copy(alpha = 0.16f))
            .border(1.dp, color.copy(alpha = 0.4f), RoundedCornerShape(20.dp))
            .padding(horizontal = 10.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(texto, fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold, color = color)
    }
}

@Composable
private fun FilaNivelMuscular(zona: ZonaMuscular, nivel: NivelMuscular?) {
    val activa = nivel != null
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(if (activa) Olimpos.GoldSoft else Olimpos.Card)
            .border(1.dp, if (activa) Olimpos.Gold.copy(alpha = 0.35f) else Olimpos.Line, RoundedCornerShape(14.dp))
            .padding(horizontal = 14.dp, vertical = 11.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        if (nivel != null) {
            Image(painter = painterResource(iconoDeRango(nivel)), contentDescription = nivel.etiquetaCompleta, modifier = Modifier.size(26.dp))
        } else {
            Box(Modifier.size(10.dp).clip(CircleShape).background(Olimpos.Muted.copy(alpha = 0.4f)))
        }
        Spacer(Modifier.width(11.dp))
        Text(zona.emoji, fontSize = 15.sp)
        Spacer(Modifier.width(9.dp))
        Text(
            zona.etiqueta, fontSize = 13.5.sp, fontWeight = FontWeight.ExtraBold,
            color = if (activa) Olimpos.Cream else Olimpos.Muted, modifier = Modifier.weight(1f)
        )
        Text(
            nivel?.etiquetaCompleta ?: "Sin marcas",
            fontSize = 10.5.sp, fontWeight = FontWeight.Bold,
            color = if (activa) Olimpos.GoldLight else Olimpos.Muted
        )
    }
}
