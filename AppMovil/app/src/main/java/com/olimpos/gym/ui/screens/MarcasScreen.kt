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
import androidx.compose.foundation.layout.aspectRatio
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.EJERCICIOS_FUERZA
import com.olimpos.gym.data.EjercicioFuerza
import com.olimpos.gym.data.MIS_MARCAS
import com.olimpos.gym.data.MarcaPersonal
import com.olimpos.gym.data.calcular1RM
import com.olimpos.gym.data.cargarMarcasDesdeFirebase
import com.olimpos.gym.data.eliminarMarcaEnFirebase
import com.olimpos.gym.data.guardarMarcaEnFirebase
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

@Composable
fun MarcasScreen(onVolver: () -> Unit) {
    var ejercicio by remember { mutableStateOf(EJERCICIOS_FUERZA[0].nombre) }
    var peso by remember { mutableStateOf("") }
    var reps by remember { mutableStateOf("") }
    var aviso by remember { mutableStateOf<String?>(null) }
    var marcas by remember { mutableStateOf<List<MarcaPersonal>>(MIS_MARCAS) }
    var ejercicioViendo by remember { mutableStateOf<String?>(null) }
    var marcaAEliminar by remember { mutableStateOf<MarcaPersonal?>(null) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        cargarMarcasDesdeFirebase()?.takeIf { it.isNotEmpty() }?.let { marcas = it }
    }

    fun eliminarMarca(marca: MarcaPersonal) {
        marcas = marcas.filter { it.id != marca.id }
        scope.launch {
            eliminarMarcaEnFirebase(marca.id)
            // Sin esto, el Bodygraph y la Clasificación seguirían mostrando
            // el rango calculado con la marca ya borrada hasta reiniciar la app.
            DatosRemotos.recargarMarcas()
            DatosRemotos.recargarRangosSocios()
        }
        marcaAEliminar = null
    }

    val ejercicioActivo = ejercicioViendo
    Box(Modifier.fillMaxSize()) {
        if (ejercicioActivo != null) {
            MarcasDeEjercicioScreen(
                ejercicio = ejercicioActivo,
                marcas = marcas.filter { it.ejercicio == ejercicioActivo }.sortedByDescending { it.timestamp },
                onVolver = { ejercicioViendo = null },
                onEliminar = { marcaAEliminar = it }
            )
        } else {
            // Column + verticalScroll y NO LazyColumn: el formulario tiene campos de
            // texto, y en una lista lazy se destruyen/recrean al salir de pantalla
            // (un TextField es de lo más caro de componer). Con pocas filas de
            // historial conviene componer todo una vez.
            Column(
                Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
            ) {
                EncabezadoVolver("Mis marcas", "Registrá tu PR y seguí tu progreso", onVolver)

                Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
                    SeccionLabel("Registrar levantamiento")
                    TarjetaOro(Modifier.fillMaxWidth()) {
                        Text("Ejercicio", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted)
                        Spacer(Modifier.height(8.dp))
                        FilaChips {
                            EJERCICIOS_FUERZA.forEach { ej ->
                                ChipSeleccionable("${ej.emoji} ${ej.nombre}", ejercicio == ej.nombre) { ejercicio = ej.nombre }
                            }
                        }
                        Spacer(Modifier.height(14.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            CampoOro(peso, { peso = it }, "Peso (kg)", Modifier.weight(1f), teclado = KeyboardType.Number)
                            CampoOro(reps, { reps = it }, "Repeticiones", Modifier.weight(1f), teclado = KeyboardType.Number)
                        }
                        val pesoF = peso.toFloatOrNull()
                        val repsI = reps.toIntOrNull()
                        val anomalia = pesoF != null && pesoF > 150f
                        if (anomalia) {
                            Spacer(Modifier.height(10.dp))
                            Text(
                                "⚠️ Peso inusualmente alto respecto a tus marcas anteriores. Se marcará para revisión automática.",
                                fontSize = 11.5.sp, color = Olimpos.Red, fontWeight = FontWeight.Bold
                            )
                        }
                        Spacer(Modifier.height(14.dp))
                        BotonPrincipal("Registrar marca", habilitado = pesoF != null && repsI != null) {
                            val p = pesoF ?: 0f
                            val r = repsI ?: 0
                            val hoy = "hoy"
                            val ahora = System.currentTimeMillis()
                            marcas = marcas + MarcaPersonal(ejercicio = ejercicio, pesoKg = p, reps = r, fecha = hoy, timestamp = ahora, verificado = false)
                            scope.launch {
                                guardarMarcaEnFirebase(ejercicio, p, r, hoy, ahora)
                                // Bodygraph y Clasificación leen de este caché — sin
                                // esto se quedarían con la marca anterior hasta
                                // reiniciar la app.
                                DatosRemotos.recargarMarcas()
                                DatosRemotos.recargarRangosSocios()
                                // Reemplaza la marca optimista de arriba (sin id
                                // real todavía) por la lista real de Firestore,
                                // para poder borrarla ni bien se registra si hace falta.
                                cargarMarcasDesdeFirebase()?.let { marcas = it }
                            }
                            aviso = "Marca registrada — reemplaza tu marca anterior de este ejercicio en el ranking. Enviada al entrenador para verificar ✓"
                            peso = ""; reps = ""
                        }
                    }

                    aviso?.let {
                        Spacer(Modifier.height(12.dp))
                        Row(
                            Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(14.dp))
                                .background(Olimpos.GoldSoft)
                                .border(1.dp, Olimpos.Gold.copy(alpha = 0.35f), RoundedCornerShape(14.dp))
                                .padding(13.dp)
                        ) {
                            Text(it, fontSize = 12.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.GoldLight)
                        }
                    }

                    SeccionLabel("Tus marcas por ejercicio")
                    Text(
                        "Tocá un ejercicio para ver el historial completo con fechas.",
                        fontSize = 11.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 12.dp)
                    )
                    GrillaEjercicios(marcas, onSeleccionar = { ejercicioViendo = it })
                }
            }
        }

        AnimatedVisibility(visible = marcaAEliminar != null, enter = fadeIn(), exit = fadeOut()) {
            marcaAEliminar?.let { m ->
                ConfirmarEliminarMarca(
                    marca = m,
                    onCancelar = { marcaAEliminar = null },
                    onConfirmar = { eliminarMarca(m) }
                )
            }
        }
    }
}

/** Grilla de 2 columnas con los 8 ejercicios de la Calculadora — cada uno
 *  con la cantidad de marcas cargadas. Reemplaza el historial plano de
 *  antes: con muchas marcas encima era difícil encontrar las de un
 *  ejercicio puntual. */
@Composable
private fun GrillaEjercicios(marcas: List<MarcaPersonal>, onSeleccionar: (String) -> Unit) {
    val filas = EJERCICIOS_FUERZA.chunked(2)
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        filas.forEach { fila ->
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                fila.forEach { ej ->
                    TarjetaEjercicioMarcas(
                        ejercicio = ej,
                        cantidad = marcas.count { it.ejercicio == ej.nombre },
                        modifier = Modifier.weight(1f),
                        onClick = { onSeleccionar(ej.nombre) }
                    )
                }
                if (fila.size == 1) Spacer(Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun TarjetaEjercicioMarcas(ejercicio: EjercicioFuerza, cantidad: Int, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Column(
        modifier
            .aspectRatio(1.15f)
            .clip(RoundedCornerShape(18.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(18.dp))
            .clickable(onClick = onClick)
            .padding(14.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(ejercicio.emoji, fontSize = 30.sp)
        Spacer(Modifier.height(8.dp))
        Text(
            ejercicio.nombre, fontSize = 13.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center
        )
        Spacer(Modifier.height(4.dp))
        Text(
            if (cantidad == 0) "Sin marcas todavía" else "$cantidad marca${if (cantidad == 1) "" else "s"}",
            fontSize = 11.sp, color = Olimpos.Muted
        )
    }
}

/** Historial completo de un ejercicio puntual, con fecha de cada marca y
 *  un botón para borrarla. */
@Composable
private fun MarcasDeEjercicioScreen(
    ejercicio: String,
    marcas: List<MarcaPersonal>,
    onVolver: () -> Unit,
    onEliminar: (MarcaPersonal) -> Unit
) {
    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver(ejercicio, "${marcas.size} marca${if (marcas.size == 1) "" else "s"} registrada${if (marcas.size == 1) "" else "s"}", onVolver)
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(bottom = 26.dp)
        ) {
            if (marcas.isEmpty()) {
                Text(
                    "Todavía no cargaste ninguna marca de este ejercicio.",
                    fontSize = 12.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 20.dp)
                )
            } else {
                marcas.forEach { m ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .padding(bottom = 9.dp)
                            .clip(RoundedCornerShape(16.dp))
                            .background(Olimpos.Card)
                            .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
                            .padding(horizontal = 15.dp, vertical = 13.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text("${m.pesoKg.toInt()}kg × ${m.reps}", fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                            Text("${m.fecha} · 1RM est. ${"%.0f".format(calcular1RM(m.pesoKg, m.reps))}kg", fontSize = 11.5.sp, color = Olimpos.Muted)
                        }
                        ChipOro(if (m.verificado) "Verificada ✓" else "Pendiente")
                        Spacer(Modifier.width(8.dp))
                        Box(
                            Modifier
                                .clip(RoundedCornerShape(10.dp))
                                .clickable { onEliminar(m) }
                                .padding(8.dp)
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
            .background(Olimpos.Dark.copy(alpha = 0.72f))
            .clickable(onClick = onCancelar),
        contentAlignment = Alignment.Center
    ) {
        Column(
            Modifier
                .padding(horizontal = 36.dp)
                .clip(RoundedCornerShape(24.dp))
                .background(Olimpos.Card)
                .border(1.dp, Olimpos.Red.copy(alpha = 0.4f), RoundedCornerShape(24.dp))
                .clickable(enabled = false) {}
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("¿Eliminar esta marca?", fontSize = 16.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
            Spacer(Modifier.height(8.dp))
            Text(
                "${marca.ejercicio} · ${marca.pesoKg.toInt()}kg × ${marca.reps} (${marca.fecha}). Si era tu única marca de este ejercicio, tu rango general puede bajar.",
                fontSize = 12.5.sp, color = Olimpos.Muted, textAlign = androidx.compose.ui.text.style.TextAlign.Center
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
                ) { Text("Eliminar", fontSize = 13.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream) }
            }
        }
    }
}
