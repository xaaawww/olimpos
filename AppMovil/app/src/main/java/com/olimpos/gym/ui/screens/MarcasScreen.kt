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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
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
import com.olimpos.gym.data.MIS_MARCAS
import com.olimpos.gym.data.MarcaPersonal
import com.olimpos.gym.data.calcular1RM
import com.olimpos.gym.data.cargarMarcasDesdeFirebase
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
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        cargarMarcasDesdeFirebase()?.takeIf { it.isNotEmpty() }?.let { marcas = it }
    }

    val pesoF = peso.toFloatOrNull()
    val repsI = reps.toIntOrNull()
    val anomalia = pesoF != null && pesoF > 150f

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

            SeccionLabel("Historial de marcas")
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
                        Text("${m.ejercicio} · ${m.pesoKg.toInt()}kg × ${m.reps}", fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                        Text("${m.fecha} · 1RM est. ${"%.0f".format(calcular1RM(m.pesoKg, m.reps))}kg", fontSize = 11.5.sp, color = Olimpos.Muted)
                    }
                    ChipOro(if (m.verificado) "Verificada ✓" else "Pendiente")
                }
            }
        }
    }
}
