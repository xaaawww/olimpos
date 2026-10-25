package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
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
import com.olimpos.gym.data.EJERCICIOS_FUERZA
import com.olimpos.gym.data.MarcaPersonal
import com.olimpos.gym.data.RangoMuscular
import com.olimpos.gym.data.calcular1RM
import com.olimpos.gym.data.calcular1RMBrzycki
import com.olimpos.gym.data.cargaParaEntrarEnRango
import com.olimpos.gym.data.esEjercicioPesoCorporal
import com.olimpos.gym.data.imagenDeEjercicio
import com.olimpos.gym.data.nivelDesdePuntaje
import com.olimpos.gym.data.pesoParaRepeticiones
import com.olimpos.gym.data.puntajeDeMarca
import com.olimpos.gym.data.repeticionesConPeso
import com.olimpos.gym.ui.theme.Olimpos
import kotlin.math.roundToInt

/** Calculadora: con una serie (peso × repeticiones) estima el 1RM y dice en
 *  qué rango del Olimpo cae; "Peso ideal" da el peso para cada cantidad de
 *  repeticiones y "Repeticiones" cuántas salen con un peso dado. La tabla de
 *  referencia es la de los rangos reales (la inversa de puntajeDeMarca), con
 *  el peso corporal y el sexo del socio. Arranca con su última marca. */
@Composable
fun CalculadoraScreen(onVolver: () -> Unit) {
    var ejercicio by remember { mutableStateOf(EJERCICIOS_FUERZA[0].nombre) }
    var pestana by remember { mutableIntStateOf(0) }
    var peso by remember { mutableFloatStateOf(60f) }
    var reps by remember { mutableFloatStateOf(8f) }
    var pesoPrueba by remember { mutableFloatStateOf(50f) }

    val datos = DatosRemotos.datosFisicosPropios
    val pesoCorporal = datos?.pesoKg ?: 0f
    val corporal = esEjercicioPesoCorporal(ejercicio)
    val marcas = DatosRemotos.marcas ?: emptyList()

    // Al cambiar de ejercicio arranca con la última marca cargada de ese ejercicio.
    LaunchedEffect(ejercicio) {
        val ultima = marcas.filter { it.ejercicio == ejercicio }.maxByOrNull { it.timestamp }
        peso = ultima?.pesoKg ?: if (corporal) 0f else 40f
        reps = (ultima?.reps ?: 8).toFloat().coerceIn(1f, 20f)
    }

    // En dominadas/flexiones el peso del slider es el lastre: la carga real suma el cuerpo.
    val carga = if (corporal) pesoCorporal + peso else peso
    val r = reps.roundToInt()
    val oneRM = calcular1RM(carga, r)
    val oneRMBrzycki = calcular1RMBrzycki(carga, r)
    val nivel = if (pesoCorporal > 0f) {
        nivelDesdePuntaje(puntajeDeMarca(MarcaPersonal(ejercicio = ejercicio, pesoKg = peso, reps = r, fecha = "", verificado = false), pesoCorporal, datos?.sexo))
    } else null

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        EncabezadoArena("Calculadora", "Descubrí cuánto podés levantar según tu nivel.", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(top = 6.dp, bottom = 26.dp)) {
            PestanasPildora(listOf("1RM", "Peso ideal", "Repeticiones"), pestana, { pestana = it })

            Etiqueta("Elegí un ejercicio")
            SelectorEjercicio(ejercicio) { ejercicio = it }

            Etiqueta("Tu serie")
            TarjetaLisa(Modifier.fillMaxWidth()) {
                Deslizador(
                    if (corporal) "PESO AGREGADO" else "PESO",
                    if (corporal && peso == 0f) "Sin lastre" else "${peso.roundToInt()} kg",
                    peso, if (corporal) 0f..80f else 5f..300f
                ) { peso = it.roundToInt().toFloat() }
                Spacer(Modifier.height(10.dp))
                Deslizador("REPETICIONES", "$r", reps, 1f..20f, pasos = 18) { reps = it }
                if (corporal) {
                    Text(
                        if (pesoCorporal > 0f) "Se suma tu peso corporal (${pesoCorporal.roundToInt()} kg)."
                        else "Cargá tu peso en Perfil para calcular este ejercicio.",
                        fontSize = 11.sp, color = Olimpos.Muted
                    )
                }
            }

            when {
                pestana != 0 && oneRM < 1f -> {
                    Spacer(Modifier.height(14.dp))
                    TarjetaLisa(Modifier.fillMaxWidth()) {
                        Text("Elegí un peso y repeticiones para calcular.", fontSize = 12.sp, color = Olimpos.Muted)
                    }
                }
                pestana == 0 -> {
                    Etiqueta("Tu resultado estimado")
                    Resultado1RM(oneRM, minOf(oneRM, oneRMBrzycki), maxOf(oneRM, oneRMBrzycki), r, nivel?.etiquetaCompleta)
                    Etiqueta("Tabla de referencia")
                    TablaRangos(ejercicio, pesoCorporal, datos?.sexo, nivel?.rango, corporal)
                }
                pestana == 1 -> {
                    Etiqueta("Peso para cada cantidad de repeticiones")
                    TablaPesoIdeal(oneRM, corporal, pesoCorporal)
                }
                else -> {
                    // Por debajo del 50% del máximo Epley ya no es confiable (daría 30+ reps).
                    val minimo = (oneRM * 0.5f).roundToInt().toFloat()
                    LaunchedEffect(oneRM) { pesoPrueba = pesoPrueba.coerceIn(minimo, oneRM) }
                    Etiqueta("¿Cuántas repeticiones te salen?")
                    TarjetaLisa(Modifier.fillMaxWidth()) {
                        Deslizador("PESO", "${pesoPrueba.roundToInt()} kg", pesoPrueba, minimo..maxOf(oneRM, minimo + 1f)) {
                            pesoPrueba = it.roundToInt().toFloat()
                        }
                        val estimadas = repeticionesConPeso(oneRM, pesoPrueba)
                        Spacer(Modifier.height(6.dp))
                        Row(verticalAlignment = Alignment.Bottom) {
                            Text("$estimadas", fontSize = 40.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
                            Text(
                                " repeticiones", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted,
                                modifier = Modifier.padding(bottom = 8.dp)
                            )
                        }
                        Text(
                            "Con tu 1RM estimado de ${oneRM.roundToInt()} kg (${(pesoPrueba / oneRM * 100).roundToInt()}% del máximo).",
                            fontSize = 11.5.sp, color = Olimpos.Muted
                        )
                    }
                }
            }

            Spacer(Modifier.height(14.dp))
            Text(
                "Estimación con la fórmula de Epley; el rango la compara con la de Brzycki. " +
                    "Tu máximo real puede variar según técnica, descanso y el día.",
                fontSize = 11.sp, lineHeight = 15.sp, color = Olimpos.Muted
            )
        }
    }
}

@Composable
private fun Etiqueta(texto: String) {
    Text(
        texto, fontSize = 13.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream,
        modifier = Modifier.padding(top = 18.dp, bottom = 9.dp)
    )
}

@Composable
private fun SelectorEjercicio(elegido: String, onElegir: (String) -> Unit) {
    var abierto by remember { mutableStateOf(false) }
    Box {
        Row(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(Olimpos.Card)
                .border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp))
                .clickable { abierto = true }
                .padding(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            ImagenEjercicio(imagenDeEjercicio(nombre = elegido), 38.dp, radio = 9.dp)
            Spacer(Modifier.width(12.dp))
            Text(elegido, fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Olimpos.Cream, modifier = Modifier.weight(1f))
            Text("▾", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted, modifier = Modifier.padding(end = 6.dp))
        }
        DropdownMenu(expanded = abierto, onDismissRequest = { abierto = false }) {
            EJERCICIOS_FUERZA.forEach { ej ->
                DropdownMenuItem(
                    text = { Text(ej.nombre, fontSize = 14.sp, fontWeight = if (ej.nombre == elegido) FontWeight.ExtraBold else FontWeight.Normal) },
                    leadingIcon = { ImagenEjercicio(imagenDeEjercicio(nombre = ej.nombre), 32.dp, radio = 8.dp) },
                    onClick = { onElegir(ej.nombre); abierto = false }
                )
            }
        }
    }
}

@Composable
private fun Deslizador(
    etiqueta: String, valorTexto: String, valor: Float, rango: ClosedFloatingPointRange<Float>,
    pasos: Int = 0, onValor: (Float) -> Unit
) {
    Column {
        Row(Modifier.fillMaxWidth()) {
            Text(etiqueta, fontSize = 10.5.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp, color = Olimpos.Muted, modifier = Modifier.weight(1f))
            Text(valorTexto, fontSize = 13.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
        }
        Slider(
            value = valor.coerceIn(rango), onValueChange = onValor, valueRange = rango, steps = pasos,
            colors = SliderDefaults.colors(thumbColor = Olimpos.Gold, activeTrackColor = Olimpos.Gold, inactiveTrackColor = Olimpos.Line)
        )
    }
}

@Composable
private fun Resultado1RM(oneRM: Float, minimo: Float, maximo: Float, reps: Int, nivel: String?) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Olimpos.GoldSoft)
            .border(1.dp, Olimpos.Gold.copy(alpha = 0.3f), RoundedCornerShape(16.dp))
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            Modifier.size(50.dp).clip(CircleShape).background(Olimpos.Gold.copy(alpha = 0.25f)),
            contentAlignment = Alignment.Center
        ) { Text("🏋️", fontSize = 22.sp) }
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text("1RM estimado", fontSize = 11.5.sp, color = Olimpos.Muted)
            Text("${oneRM.roundToInt()} kg", fontSize = 30.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
            Text(
                if (reps == 1) "Es tu máximo de una repetición" else "Entre ${minimo.roundToInt()} y ${maximo.roundToInt()} kg según la fórmula",
                fontSize = 10.5.sp, color = Olimpos.Muted
            )
        }
        if (nivel != null) {
            Column(
                Modifier
                    .clip(RoundedCornerShape(12.dp))
                    .background(Olimpos.Card)
                    .border(1.dp, Olimpos.Line, RoundedCornerShape(12.dp))
                    .padding(horizontal = 10.dp, vertical = 7.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text("Nivel", fontSize = 9.5.sp, color = Olimpos.Muted)
                Text(nivel, fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = acentoTexto)
            }
        }
    }
}

/** Los 9 rangos con el peso desde el que se entra a cada uno en este
 *  ejercicio — la fila del rango de la serie actual va resaltada. */
@Composable
private fun TablaRangos(ejercicio: String, pesoCorporal: Float, sexo: com.olimpos.gym.data.SexoBiologico?, actual: RangoMuscular?, corporal: Boolean) {
    if (pesoCorporal <= 0f) {
        TarjetaLisa(Modifier.fillMaxWidth()) {
            Text("Cargá tu peso corporal en Perfil para ver la tabla: los rangos dependen de tu peso.", fontSize = 12.sp, color = Olimpos.Muted)
        }
        return
    }
    val desde = RangoMuscular.entries.map { cargaParaEntrarEnRango(ejercicio, it, pesoCorporal, sexo) ?: 0f }
    TarjetaLisa(Modifier.fillMaxWidth(), padding = 0.dp) {
        FilaTabla("Nivel", if (corporal) "Carga total" else "Peso", encabezado = true)
        RangoMuscular.entries.forEachIndexed { i, rango ->
            val texto = if (i == RangoMuscular.entries.lastIndex) "${desde[i].roundToInt()}+ kg"
            else "${desde[i].roundToInt()} – ${desde[i + 1].roundToInt()} kg"
            FilaTabla(rango.etiqueta, texto, color = colorDeRango(rango), resaltada = rango == actual)
        }
    }
    if (corporal) {
        Text("Incluye tu peso corporal (${pesoCorporal.roundToInt()} kg).", fontSize = 10.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 6.dp))
    }
}

@Composable
private fun FilaTabla(izq: String, der: String, encabezado: Boolean = false, color: androidx.compose.ui.graphics.Color? = null, resaltada: Boolean = false) {
    Row(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 6.dp, vertical = 2.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(if (resaltada) Olimpos.GoldSoft else androidx.compose.ui.graphics.Color.Transparent)
            .padding(horizontal = 10.dp, vertical = if (encabezado) 10.dp else 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        if (color != null) {
            Box(Modifier.size(10.dp).clip(CircleShape).background(color))
            Spacer(Modifier.width(10.dp))
        }
        Text(
            izq, fontSize = if (encabezado) 11.sp else 12.5.sp, modifier = Modifier.weight(1f),
            fontWeight = if (resaltada) FontWeight.ExtraBold else FontWeight.Normal,
            color = if (encabezado) Olimpos.Muted else Olimpos.Cream
        )
        Text(
            der, fontSize = if (encabezado) 11.sp else 12.5.sp, modifier = Modifier.weight(0.8f),
            fontWeight = if (resaltada) FontWeight.ExtraBold else FontWeight.Normal,
            color = if (encabezado) Olimpos.Muted else Olimpos.Cream
        )
    }
}

@Composable
private fun TablaPesoIdeal(oneRM: Float, corporal: Boolean, pesoCorporal: Float) {
    TarjetaLisa(Modifier.fillMaxWidth(), padding = 0.dp) {
        FilaTabla("Repeticiones", if (corporal) "Lastre" else "Peso", encabezado = true)
        listOf(1, 2, 3, 4, 5, 6, 8, 10, 12, 15).forEach { n ->
            val total = if (n == 1) oneRM else pesoParaRepeticiones(oneRM, n)
            val texto = if (corporal) {
                val lastre = total - pesoCorporal
                if (lastre <= 0.5f) "Sin lastre" else "+${lastre.roundToInt()} kg"
            } else "${total.roundToInt()} kg"
            FilaTabla(
                "$n rep · ${(total / oneRM * 100).roundToInt()}%", texto,
                color = when {
                    n <= 5 -> Olimpos.Gold
                    n <= 12 -> Olimpos.GoldLight
                    else -> Olimpos.Muted
                }
            )
        }
    }
    Text(
        "1 a 5 repeticiones: fuerza · 6 a 12: hipertrofia · 15: resistencia.",
        fontSize = 10.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 6.dp)
    )
}
