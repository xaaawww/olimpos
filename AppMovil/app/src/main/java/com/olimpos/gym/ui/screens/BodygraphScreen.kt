package com.olimpos.gym.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
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
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.GrupoMuscular
import com.olimpos.gym.data.MINIMO_EJERCICIOS_PARA_CLASIFICACION
import com.olimpos.gym.data.NivelMuscular
import com.olimpos.gym.data.ZonaMuscular
import com.olimpos.gym.data.cantidadEjerciciosVigentes
import com.olimpos.gym.data.incrementarVistaBodygraph
import com.olimpos.gym.data.nivelDesdePuntaje
import com.olimpos.gym.data.porcentajeDePuntaje
import com.olimpos.gym.data.puntajeGeneralDeSocio
import com.olimpos.gym.data.resumenMuscular
import com.olimpos.gym.ui.theme.Olimpos

/** Mapa corporal (el Bodygraph): el rango de cada músculo a partir de las
 *  marcas cargadas en Mis marcas — ver [resumenMuscular]. El cuerpo es el
 *  mismo de siempre; tocarlo lo da vuelta (frente/espalda). Cada grupo
 *  muestra su % (qué tan cerca está de Dios) y su rango; tocar un grupo
 *  abre el detalle de sus músculos. */
@Composable
fun BodygraphScreen(onVolver: () -> Unit) {
    // Sin datos de ejemplo de respaldo a propósito: un socio nuevo debe ver
    // el cuerpo en gris, no rangos que nunca ganó.
    val marcas = DatosRemotos.marcas ?: emptyList()
    val datosFisicos = DatosRemotos.datosFisicosPropios
    val pesoCorporal = datosFisicos?.pesoKg ?: 80f
    val resumen = remember(marcas, datosFisicos) { resumenMuscular(marcas, pesoCorporal, datosFisicos?.sexo) }
    val nivelesPorZona = remember(resumen) {
        ZonaMuscular.entries.associateWith { zona -> resumen.puntajes[zona]?.let(::nivelDesdePuntaje) }
    }
    // Mismo cálculo que la Escalera del Olimpo en Clasificación (promedio por
    // ejercicio), para que nunca se vea un rango distinto acá que allá.
    val puntajeGeneral = remember(marcas, datosFisicos) { puntajeGeneralDeSocio(marcas, pesoCorporal, datosFisicos?.sexo) }
    val ejerciciosRegistrados = remember(marcas) { cantidadEjerciciosVigentes(marcas) }
    val ultimaMarca = marcas.maxOfOrNull { it.timestamp }?.takeIf { it > 0 }

    var vista by remember { mutableStateOf(VistaCuerpo.FRENTE) }
    var grupoAbierto by remember { mutableStateOf<GrupoMuscular?>(null) }

    // Para el logro "Ojo en el progreso" (revisar el Bodygraph 20 veces).
    LaunchedEffect(Unit) {
        incrementarVistaBodygraph()
        DatosRemotos.recargarDatosFisicosPropios()
    }

    Column(Modifier.fillMaxSize().background(CA.fondo).verticalScroll(rememberScrollState())) {
        EncabezadoArena(
            "Mapa corporal", "Tu progreso muscular en cada grupo.", onVolver,
            derecha = ultimaMarca?.let { ts -> { PildoraFecha(ts) } }
        )

        Column(Modifier.padding(horizontal = 16.dp).padding(top = 8.dp, bottom = 26.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                // ── Cuerpo: el mismo de siempre, ocupa media pantalla y se da
                // vuelta al tocarlo ──
                BoxWithConstraints(
                    Modifier
                        .weight(0.54f)
                        .clickable {
                            vista = if (vista == VistaCuerpo.FRENTE) VistaCuerpo.ESPALDA else VistaCuerpo.FRENTE
                        }
                ) {
                    val ancho = maxWidth
                    Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                    CuerpoMuscularRangosMini(
                        rangoPorZona = nivelesPorZona.mapValues { it.value?.rango },
                        tamano = ancho,
                        vista = vista
                    )
                    Spacer(Modifier.height(6.dp))
                    Text(
                        (if (vista == VistaCuerpo.FRENTE) "Frente" else "Espalda") + "  ⇄",
                        fontSize = 10.5.sp, fontWeight = FontWeight.Bold, color = CA.suave
                    )
                    }
                }
                Spacer(Modifier.width(8.dp))
                // ── Los 6 grupos ──
                Column(Modifier.weight(0.46f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    GrupoMuscular.entries.forEach { grupo ->
                        val puntajes = grupo.zonas.map { resumen.puntajes[it] ?: 0f }
                        val promedio = puntajes.average().toFloat()
                        FilaGrupo(
                            grupo = grupo,
                            porcentaje = porcentajeDePuntaje(promedio),
                            nivel = if (puntajes.any { it > 0f }) nivelDesdePuntaje(promedio) else null,
                            abierto = grupo == grupoAbierto,
                            onClick = { grupoAbierto = if (grupoAbierto == grupo) null else grupo }
                        )
                    }
                }
            }

            // ── Detalle del grupo tocado: cada músculo con su rango ──
            AnimatedVisibility(visible = grupoAbierto != null) {
                grupoAbierto?.let { grupo ->
                    TarjetaLisa(Modifier.fillMaxWidth().padding(top = 14.dp)) {
                        Text(grupo.etiqueta, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = CA.texto)
                        Spacer(Modifier.height(8.dp))
                        grupo.zonas.forEach { zona ->
                            FilaMusculo(zona, nivelesPorZona[zona], resumen.puntajes[zona])
                        }
                    }
                }
            }

            Spacer(Modifier.height(14.dp))
            TarjetaPuntuacion(
                puntajeGeneral = puntajeGeneral,
                faltan = (MINIMO_EJERCICIOS_PARA_CLASIFICACION - ejerciciosRegistrados).coerceAtLeast(0),
                tieneMarcas = resumen.tieneMarcas,
                verificado = resumen.verificado
            )
        }
    }
}

@Composable
private fun PildoraFecha(timestamp: Long) {
    Column(
        Modifier
            .clip(RoundedCornerShape(10.dp))
            .background(CA.tarjeta)
            .border(1.dp, CA.borde, RoundedCornerShape(10.dp))
            .padding(horizontal = 10.dp, vertical = 6.dp)
    ) {
        Text("Actualizado", fontSize = 9.sp, color = CA.suave)
        Text(
            java.text.SimpleDateFormat("dd/MM/yyyy", java.util.Locale("es", "AR")).format(java.util.Date(timestamp)),
            fontSize = 10.5.sp, fontWeight = FontWeight.Bold, color = CA.texto
        )
    }
}

@Composable
private fun FilaGrupo(grupo: GrupoMuscular, porcentaje: Float, nivel: NivelMuscular?, abierto: Boolean, onClick: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(if (abierto) CA.amarilloSuave else CA.tarjeta)
            .border(1.dp, if (abierto) CA.amarillo.copy(alpha = 0.45f) else CA.borde, RoundedCornerShape(14.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 8.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconoRedondo(grupo.emoji, tamano = 30.dp, pastel = pastelDeGrupo(grupo), apagado = nivel == null)
        Spacer(Modifier.width(8.dp))
        Column(Modifier.weight(1f)) {
            Text(nombreCorto(grupo), fontSize = 12.5.sp, fontWeight = FontWeight.ExtraBold, color = CA.texto, maxLines = 1)
            Text(nivel?.etiquetaCompleta ?: "Sin marcas", fontSize = 10.sp, color = CA.suave, maxLines = 1)
        }
        val pastel = pastelDeGrupo(grupo)
        Text(
            "${(porcentaje * 100).toInt()}%",
            fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold, color = pastel.tono,
            modifier = Modifier
                .clip(RoundedCornerShape(8.dp))
                .background(pastel.fondo)
                .padding(horizontal = 6.dp, vertical = 3.dp)
        )
    }
}

/** "Abdomen" en vez de "Abdominales" (como en el diseño): entra en la tarjeta. */
private fun nombreCorto(grupo: GrupoMuscular): String =
    if (grupo == GrupoMuscular.ABDOMINALES) "Abdomen" else grupo.etiqueta

@Composable
private fun FilaMusculo(zona: ZonaMuscular, nivel: NivelMuscular?, puntaje: Float?) {
    Row(Modifier.fillMaxWidth().padding(vertical = 5.dp), verticalAlignment = Alignment.CenterVertically) {
        if (nivel != null) {
            Image(painterResource(iconoDeRango(nivel)), contentDescription = nivel.etiquetaCompleta, modifier = Modifier.size(24.dp))
        } else {
            Box(Modifier.size(24.dp), contentAlignment = Alignment.Center) {
                Box(Modifier.size(9.dp).clip(CircleShape).background(CA.suave.copy(alpha = 0.4f)))
            }
        }
        Spacer(Modifier.width(10.dp))
        Column(Modifier.weight(1f)) {
            Text(zona.etiqueta, fontSize = 12.5.sp, fontWeight = FontWeight.Bold, color = if (nivel != null) CA.texto else CA.suave)
            if (nivel != null && puntaje != null) {
                Spacer(Modifier.height(4.dp))
                BarraArena(nivel.progreso(puntaje), alto = 5.dp)
            }
        }
        Spacer(Modifier.width(10.dp))
        Text(nivel?.etiquetaCompleta ?: "Sin marcas", fontSize = 10.5.sp, fontWeight = FontWeight.Bold, color = if (nivel != null) CA.acento else CA.suave)
    }
}

@Composable
private fun TarjetaPuntuacion(puntajeGeneral: Float?, faltan: Int, tieneMarcas: Boolean, verificado: Boolean) {
    val nivel = puntajeGeneral?.let(::nivelDesdePuntaje)
    TarjetaLisa(Modifier.fillMaxWidth(), padding = 16.dp) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (nivel != null) {
                Image(painterResource(iconoDeRango(nivel)), contentDescription = nivel.etiquetaCompleta, modifier = Modifier.size(46.dp))
            } else {
                IconoRedondo("📊", tamano = 46.dp, apagado = true)
            }
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1.1f)) {
                Text("Puntuación general", fontSize = 11.sp, color = CA.suave, maxLines = 1)
                if (puntajeGeneral != null && nivel != null) {
                    Text("${(porcentajeDePuntaje(puntajeGeneral) * 100).toInt()}%", fontSize = 28.sp, fontWeight = FontWeight.Black, color = CA.texto)
                    ChipSuave(nivel.etiquetaCompleta, Pastel.AZUL)
                } else {
                    Text("Sin clasificar", fontSize = 18.sp, fontWeight = FontWeight.Black, color = CA.texto)
                }
            }
            Box(Modifier.width(1.dp).height(54.dp).background(CA.borde))
            Spacer(Modifier.width(12.dp))
            Text(
                when {
                    !tieneMarcas -> "Cargá tus marcas en Mis marcas para empezar a ver tu progreso."
                    puntajeGeneral == null -> "Cargá marcas en $faltan ejercicio${if (faltan == 1) "" else "s"} más para entrar en la clasificación."
                    !verificado -> "Algunas marcas todavía no las verificó un entrenador."
                    else -> "¡Vas por buen camino! Mantené la constancia para seguir subiendo."
                },
                fontSize = 10.5.sp, lineHeight = 14.sp, color = CA.suave,
                modifier = Modifier.weight(0.9f)
            )
        }
    }
}
