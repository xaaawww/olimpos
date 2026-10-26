package com.olimpos.gym.ui.screens

import androidx.compose.animation.AnimatedVisibility
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
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.CATEGORIAS_EJERCICIO
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.EJERCICIOS_FUERZA
import com.olimpos.gym.data.MarcaPersonal
import com.olimpos.gym.data.calcular1RM
import com.olimpos.gym.data.cargaEfectivaDeMarca
import com.olimpos.gym.data.cargarMarcasDesdeFirebase
import com.olimpos.gym.data.categoriaDeEjercicio
import com.olimpos.gym.data.eliminarMarcaEnFirebase
import com.olimpos.gym.data.esEjercicioPesoCorporal
import com.olimpos.gym.data.fechaLegible
import com.olimpos.gym.data.guardarMarcaEnFirebase
import com.olimpos.gym.data.imagenDeEjercicio
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

/** Mis marcas: la marca vigente (la más reciente) de cada ejercicio de la
 *  Calculadora, filtrable por familia. Tocar uno abre su historial completo;
 *  "+ Registrar" carga una marca nueva (que reemplaza la anterior en el
 *  ranking y queda pendiente de verificación por un entrenador). */
@Composable
fun MarcasScreen(onVolver: () -> Unit) {
    // Sin datos de ejemplo a propósito: un socio nuevo empieza en cero.
    var marcas by remember { mutableStateOf<List<MarcaPersonal>>(emptyList()) }
    var cargando by remember { mutableStateOf(true) }
    var ejercicioViendo by remember { mutableStateOf<String?>(null) }
    var registrando by remember { mutableStateOf<String?>(null) }
    var marcaAEliminar by remember { mutableStateOf<MarcaPersonal?>(null) }
    var aviso by remember { mutableStateOf<String?>(null) }
    var filtro by remember { mutableIntStateOf(0) }
    val scope = rememberCoroutineScope()
    val pesoCorporalKg = DatosRemotos.datosFisicosPropios?.pesoKg ?: 80f

    LaunchedEffect(Unit) {
        cargarMarcasDesdeFirebase()?.let { marcas = it }
        cargando = false
    }

    fun eliminarMarca(marca: MarcaPersonal) {
        marcas = marcas.filter { it.id != marca.id }
        scope.launch {
            eliminarMarcaEnFirebase(marca.id)
            // Sin esto el Bodygraph y la Clasificación seguirían con la marca borrada.
            DatosRemotos.recargarMarcas()
            DatosRemotos.recargarRangosSocios()
        }
        marcaAEliminar = null
    }

    val enRegistro = registrando
    val enHistorial = ejercicioViendo
    Box(Modifier.fillMaxSize().background(CA.fondo)) {
        when {
            enRegistro != null -> RegistrarMarcaScreen(
                ejercicioInicial = enRegistro,
                onVolver = { registrando = null },
                onRegistrar = { ejercicio, p, r ->
                    val ahora = System.currentTimeMillis()
                    val fechaTexto = fechaLegible(ahora)
                    marcas = marcas + MarcaPersonal(ejercicio = ejercicio, pesoKg = p, reps = r, fecha = fechaTexto, timestamp = ahora, verificado = false)
                    scope.launch {
                        guardarMarcaEnFirebase(ejercicio, p, r, fechaTexto, ahora)
                        // Bodygraph y Clasificación leen de este caché.
                        DatosRemotos.recargarMarcas()
                        DatosRemotos.recargarRangosSocios()
                        // Reemplaza la marca optimista (sin id real) por la lista real.
                        cargarMarcasDesdeFirebase()?.let { marcas = it }
                    }
                    aviso = "Marca de $ejercicio registrada: reemplaza la anterior en el ranking y quedó enviada al entrenador para verificar."
                    registrando = null
                }
            )
            enHistorial != null -> MarcasDeEjercicioScreen(
                ejercicio = enHistorial,
                marcas = marcas.filter { it.ejercicio == enHistorial }.sortedByDescending { it.timestamp },
                pesoCorporalKg = pesoCorporalKg,
                onVolver = { ejercicioViendo = null },
                onEliminar = { marcaAEliminar = it },
                onRegistrar = { registrando = enHistorial }
            )
            else -> Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
                EncabezadoArena(
                    "Mis marcas", "Tus mejores resultados en cada ejercicio.", onVolver,
                    derecha = { BotonRegistrar { registrando = EJERCICIOS_FUERZA[0].nombre } }
                )
                Column(Modifier.padding(horizontal = 20.dp).padding(top = 6.dp, bottom = 26.dp)) {
                    PestanasPildora(listOf("Todos") + CATEGORIAS_EJERCICIO, filtro, { filtro = it })
                    aviso?.let {
                        Spacer(Modifier.height(12.dp))
                        Text(
                            it, fontSize = 12.sp, fontWeight = FontWeight.Bold, color = CA.acento,
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(14.dp))
                                .background(CA.amarilloSuave)
                                .padding(12.dp)
                        )
                    }
                    Spacer(Modifier.height(12.dp))
                    val visibles = EJERCICIOS_FUERZA.filter { filtro == 0 || categoriaDeEjercicio(it.nombre) == CATEGORIAS_EJERCICIO[filtro - 1] }
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        visibles.forEach { ej ->
                            val vigente = marcas.filter { it.ejercicio == ej.nombre }.maxByOrNull { it.timestamp }
                            FilaMarca(ej.nombre, vigente, cargando) {
                                if (vigente == null) registrando = ej.nombre else ejercicioViendo = ej.nombre
                            }
                        }
                    }
                }
            }
        }

        AnimatedVisibility(visible = marcaAEliminar != null, enter = fadeIn(), exit = fadeOut()) {
            marcaAEliminar?.let { m ->
                ConfirmarEliminarMarca(marca = m, onCancelar = { marcaAEliminar = null }, onConfirmar = { eliminarMarca(m) })
            }
        }
    }
}

@Composable
private fun BotonRegistrar(onClick: () -> Unit) {
    Text(
        "+ Registrar", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = CA.tinta,
        modifier = Modifier
            .padding(top = 4.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(CA.amarillo)
            .clickable(onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 9.dp)
    )
}

private fun textoMarca(m: MarcaPersonal): String =
    if (esEjercicioPesoCorporal(m.ejercicio)) {
        if (m.pesoKg > 0f) "Corporal +${m.pesoKg.toInt()} kg × ${m.reps} rep" else "${m.reps} rep"
    } else "${m.pesoKg.toInt()} kg × ${m.reps} rep"

private fun fechaDe(m: MarcaPersonal): String =
    if (m.timestamp > 0) java.text.SimpleDateFormat("dd/MM/yyyy", java.util.Locale("es", "AR")).format(java.util.Date(m.timestamp)) else m.fecha

@Composable
private fun FilaMarca(ejercicio: String, vigente: MarcaPersonal?, cargando: Boolean, onClick: () -> Unit) {
    TarjetaLisa(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).clickable(onClick = onClick), padding = 8.dp) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            ImagenEjercicio(imagenDeEjercicio(nombre = ejercicio), 64.dp)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(ejercicio, fontSize = 12.sp, color = CA.suave)
                if (vigente != null) {
                    Text(textoMarca(vigente), fontSize = 16.sp, fontWeight = FontWeight.Bold, color = CA.texto)
                    Text(
                        fechaDe(vigente) + if (vigente.verificado) " · Verificada ✓" else " · Pendiente",
                        fontSize = 10.5.sp, color = if (vigente.verificado) Olimpos.Green else CA.suave
                    )
                } else {
                    Text(if (cargando) "Cargando…" else "Sin marcas todavía", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = CA.suave)
                    if (!cargando) Text("Tocá para registrar la primera", fontSize = 10.5.sp, color = CA.suave)
                }
            }
            ChipSuave(categoriaDeEjercicio(ejercicio), if (vigente != null) pastelDeCategoria(categoriaDeEjercicio(ejercicio)) else Pastel.GRIS)
            Spacer(Modifier.width(4.dp))
            Chevron()
            Spacer(Modifier.width(4.dp))
        }
    }
}

/** Formulario para cargar una marca nueva. */
@Composable
private fun RegistrarMarcaScreen(ejercicioInicial: String, onVolver: () -> Unit, onRegistrar: (String, Float, Int) -> Unit) {
    var ejercicio by remember { mutableStateOf(ejercicioInicial) }
    var peso by remember { mutableStateOf("") }
    var reps by remember { mutableStateOf("") }
    val esPesoCorporal = esEjercicioPesoCorporal(ejercicio)
    // En peso corporal un campo vacío es "sin lastre" (0 kg), no un dato faltante.
    val pesoF = if (esPesoCorporal) (peso.toFloatOrNull() ?: 0f) else peso.toFloatOrNull()
    val repsI = reps.toIntOrNull()?.takeIf { it > 0 }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        EncabezadoArena("Registrar marca", "Cargá tu levantamiento: lo verifica un entrenador.", onVolver)
        Column(Modifier.padding(horizontal = 20.dp).padding(top = 6.dp, bottom = 26.dp)) {
            Text("Ejercicio", fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.padding(bottom = 9.dp))
            FilaChips {
                EJERCICIOS_FUERZA.forEach { ej -> ChipArena(ej.nombre, ejercicio == ej.nombre) { ejercicio = ej.nombre } }
            }
            Spacer(Modifier.height(14.dp))
            TarjetaLisa(Modifier.fillMaxWidth()) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ImagenEjercicio(imagenDeEjercicio(nombre = ejercicio), 56.dp)
                    Spacer(Modifier.width(12.dp))
                    Text(ejercicio, fontSize = 15.sp, fontWeight = FontWeight.SemiBold, color = CA.texto)
                }
                Spacer(Modifier.height(14.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    CampoOro(
                        peso, { peso = it }, if (esPesoCorporal) "Lastre (kg, opcional)" else "Peso (kg)",
                        Modifier.weight(1f), teclado = KeyboardType.Number
                    )
                    CampoOro(reps, { reps = it }, "Repeticiones", Modifier.weight(1f), teclado = KeyboardType.Number)
                }
                if (esPesoCorporal) {
                    Spacer(Modifier.height(8.dp))
                    Text("Cuenta tu peso corporal: dejá el peso vacío si no sumaste lastre.", fontSize = 11.sp, color = CA.suave)
                }
                if (pesoF != null && pesoF > 150f) {
                    Spacer(Modifier.height(10.dp))
                    Text(
                        "⚠️ Peso inusualmente alto: se marcará para revisión.",
                        fontSize = 11.5.sp, color = Olimpos.Red, fontWeight = FontWeight.Bold
                    )
                }
                Spacer(Modifier.height(14.dp))
                BotonPrincipal("Registrar marca", habilitado = pesoF != null && repsI != null) {
                    onRegistrar(ejercicio, pesoF ?: 0f, repsI ?: 0)
                }
            }
        }
    }
}

/** Historial completo de un ejercicio, con fecha y estado de cada marca. */
@Composable
private fun MarcasDeEjercicioScreen(
    ejercicio: String,
    marcas: List<MarcaPersonal>,
    pesoCorporalKg: Float,
    onVolver: () -> Unit,
    onEliminar: (MarcaPersonal) -> Unit,
    onRegistrar: () -> Unit
) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        EncabezadoArena(
            ejercicio, "${marcas.size} marca${if (marcas.size == 1) "" else "s"} registrada${if (marcas.size == 1) "" else "s"}", onVolver,
            derecha = { BotonRegistrar(onRegistrar) }
        )
        Column(Modifier.padding(horizontal = 20.dp).padding(top = 6.dp, bottom = 26.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
            if (marcas.isEmpty()) {
                Text("Todavía no cargaste ninguna marca de este ejercicio.", fontSize = 12.5.sp, color = CA.suave)
            }
            marcas.forEachIndexed { i, m ->
                TarjetaLisa(Modifier.fillMaxWidth()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(textoMarca(m), fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = CA.texto)
                            Text(
                                "${fechaDe(m)} · 1RM est. ${"%.0f".format(calcular1RM(cargaEfectivaDeMarca(m, pesoCorporalKg), m.reps))} kg" +
                                    if (i == 0) " · vigente" else "",
                                fontSize = 11.sp, color = CA.suave
                            )
                        }
                        ChipSuave(if (m.verificado) "Verificada ✓" else "Pendiente", if (m.verificado) Pastel.VERDE else Pastel.GRIS)
                        Box(
                            Modifier.clip(RoundedCornerShape(10.dp)).clickable { onEliminar(m) }.padding(8.dp)
                        ) { Text("🗑️", fontSize = 16.sp) }
                    }
                }
            }
        }
    }
}

@Composable
private fun ConfirmarEliminarMarca(marca: MarcaPersonal, onCancelar: () -> Unit, onConfirmar: () -> Unit) {
    Box(
        Modifier
            .fillMaxSize()
            .background(CA.tinta.copy(alpha = 0.72f))
            .clickable(onClick = onCancelar),
        contentAlignment = Alignment.Center
    ) {
        Column(
            Modifier
                .padding(horizontal = 36.dp)
                .clip(RoundedCornerShape(24.dp))
                .background(CA.tarjeta)
                .border(1.dp, Olimpos.Red.copy(alpha = 0.4f), RoundedCornerShape(24.dp))
                .clickable(enabled = false) {}
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("¿Eliminar esta marca?", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = CA.texto)
            Spacer(Modifier.height(8.dp))
            Text(
                "${marca.ejercicio} · ${textoMarca(marca)} (${fechaDe(marca)}). Si era tu única marca de este ejercicio, tu rango general puede bajar.",
                fontSize = 12.5.sp, color = CA.suave, textAlign = TextAlign.Center
            )
            Spacer(Modifier.height(18.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                BotonSecundario("Cancelar", Modifier.width(120.dp)) { onCancelar() }
                Box(
                    Modifier
                        .width(120.dp)
                        .clip(RoundedCornerShape(16.dp))
                        .background(Olimpos.Red)
                        .clickable { onConfirmar() }
                        .padding(vertical = 13.dp),
                    contentAlignment = Alignment.Center
                ) { Text("Eliminar", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Olimpos.TintaClara) }
            }
        }
    }
}
