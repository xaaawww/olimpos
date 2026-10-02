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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.EjercicioRutina
import com.olimpos.gym.data.RutinaCompleta
import com.olimpos.gym.data.borrarRutinaPropia
import com.olimpos.gym.data.crearRutinaPropia
import com.olimpos.gym.data.editarRutinaPropia
import com.olimpos.gym.data.marcarRutinaActiva
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

/** Lista de todas las rutinas del socio (la del entrenador, si tiene, y las
 *  que armó él mismo) — elegir cuál seguir en Entrenar, o armar/editar/
 *  borrar las propias. Antes "Entrenar" solo podía mostrar la única rutina
 *  que un entrenador hubiera asignado; esta pantalla es la que permite que
 *  el socio arme la suya (ver RutinasRepository.kt). */
@Composable
fun MisRutinasScreen(onVolver: () -> Unit) {
    var editando by remember { mutableStateOf<RutinaCompleta?>(null) }
    var creandoNueva by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    if (creandoNueva || editando != null) {
        EditorRutinaScreen(
            rutinaExistente = editando,
            onGuardado = { creandoNueva = false; editando = null },
            onVolver = { creandoNueva = false; editando = null },
        )
        return
    }

    // Siempre refresca al entrar (no solo si todavía no cargó nada): por si
    // el entrenador asignó una rutina nueva, o el socio eligió/editó una
    // desde otro dispositivo, mientras esta pantalla no estaba abierta.
    LaunchedEffect(Unit) { DatosRemotos.recargarMisRutinas() }
    val rutinas = DatosRemotos.misRutinas ?: emptyList()

    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver("Mis rutinas", "Elegí cuál seguir en Entrenar", onVolver)
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(top = 10.dp, bottom = 26.dp)
        ) {
            if (rutinas.isEmpty()) {
                Text(
                    "Todavía no tenés ninguna rutina. Armate la tuya con \"+ Nueva rutina\" de abajo, o pedile una a tu entrenador.",
                    fontSize = 12.5.sp, color = Olimpos.Muted, lineHeight = 17.sp
                )
                Spacer(Modifier.height(18.dp))
            }
            rutinas.forEach { r ->
                TarjetaRutina(
                    rutina = r,
                    onSeguir = { scope.launch { if (marcarRutinaActiva(r.id, rutinas)) DatosRemotos.recargarMisRutinas() } },
                    onEditar = { editando = r },
                    onBorrar = { scope.launch { if (borrarRutinaPropia(r.id)) DatosRemotos.recargarMisRutinas() } },
                )
                Spacer(Modifier.height(10.dp))
            }
            Spacer(Modifier.height(8.dp))
            BotonPrincipal("+ Nueva rutina propia") { creandoNueva = true }
        }
    }
}

@Composable
private fun TarjetaRutina(
    rutina: RutinaCompleta,
    onSeguir: () -> Unit,
    onEditar: () -> Unit,
    onBorrar: () -> Unit,
) {
    TarjetaOro(Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(rutina.nombre, fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, color = Olimpos.Cream)
                Text(
                    if (rutina.origen == "socio") "Hecha por vos" else "Armada por tu entrenador",
                    fontSize = 11.sp, color = Olimpos.Muted
                )
            }
            if (rutina.activa) ChipOro("✓ Activa")
        }
        Spacer(Modifier.height(6.dp))
        Text(
            rutina.ejercicios.joinToString(" · ") { it.nombre }.ifEmpty { "Sin ejercicios todavía" },
            fontSize = 11.5.sp, color = Olimpos.Muted
        )
        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            if (!rutina.activa) {
                BotonPrincipal("Seguir esta", Modifier.weight(1f), onClick = onSeguir)
            }
            if (rutina.origen == "socio") {
                BotonSecundario("Editar", Modifier.width(if (rutina.activa) 110.dp else 90.dp), onClick = onEditar)
                BotonSecundario("Borrar", Modifier.width(90.dp), onClick = onBorrar)
            }
        }
    }
}

/** Armar o editar una rutina propia: nombre + lista de ejercicios, cada uno
 *  elegido del catálogo real (hereda ficha de técnica) o escrito a mano
 *  (sin ficha, solo nombre/series/peso — ver EjercicioRutina.ejercicioId). */
@Composable
private fun EditorRutinaScreen(rutinaExistente: RutinaCompleta?, onGuardado: () -> Unit, onVolver: () -> Unit) {
    var nombre by remember { mutableStateOf(rutinaExistente?.nombre ?: "") }
    val filas = remember { mutableStateListOf(*(rutinaExistente?.ejercicios ?: emptyList()).toTypedArray()) }
    var mostrarCatalogo by remember { mutableStateOf(false) }
    var textoLibre by remember { mutableStateOf("") }
    var aviso by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver(
            if (rutinaExistente == null) "Nueva rutina" else "Editar rutina",
            "Elegí ejercicios del catálogo o escribí uno a mano", onVolver
        )
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(top = 10.dp, bottom = 26.dp)
        ) {
            CampoOro(nombre, { nombre = it }, "Nombre de la rutina")
            Spacer(Modifier.height(16.dp))
            SeccionLabel("Ejercicios")

            filas.forEachIndexed { i, ej ->
                FilaEjercicioEditor(
                    ejercicio = ej,
                    onCambiar = { filas[i] = it },
                    onQuitar = { filas.removeAt(i) },
                )
                Spacer(Modifier.height(8.dp))
            }
            if (filas.isEmpty()) {
                Text("Todavía no agregaste ningún ejercicio.", fontSize = 12.5.sp, color = Olimpos.Muted)
                Spacer(Modifier.height(10.dp))
            }

            Spacer(Modifier.height(6.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                BotonSecundario("📋 Del catálogo", Modifier.weight(1f)) { mostrarCatalogo = !mostrarCatalogo }
            }
            if (mostrarCatalogo) {
                Spacer(Modifier.height(8.dp))
                val catalogo = DatosRemotos.ejercicios ?: emptyList()
                if (catalogo.isEmpty()) {
                    Text("Todavía no hay ejercicios publicados en el catálogo.", fontSize = 12.sp, color = Olimpos.Muted)
                } else {
                    FilaChips {
                        catalogo.forEach { ce ->
                            ChipSeleccionable(ce.nombre, seleccionado = false) {
                                filas.add(EjercicioRutina(ce.nombre, 3, 0f, false, ce.id))
                                mostrarCatalogo = false
                            }
                        }
                    }
                }
            }
            Spacer(Modifier.height(10.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                CampoOro(textoLibre, { textoLibre = it }, "Escribir un ejercicio...", modifier = Modifier.weight(1f))
                Spacer(Modifier.width(8.dp))
                Box(
                    Modifier
                        .size(48.dp)
                        .clip(RoundedCornerShape(14.dp))
                        .background(Olimpos.Card)
                        .border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp))
                        .clickable {
                            val n = textoLibre.trim()
                            if (n.isNotEmpty()) {
                                filas.add(EjercicioRutina(n, 3, 0f, false, null))
                                textoLibre = ""
                            }
                        },
                    contentAlignment = Alignment.Center
                ) { Text("+", color = Olimpos.GoldLight, fontWeight = FontWeight.Black, fontSize = 20.sp) }
            }

            aviso?.let {
                Spacer(Modifier.height(14.dp))
                Text(it, fontSize = 12.sp, color = Olimpos.Gold, fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.height(20.dp))
            BotonPrincipal("💾 Guardar rutina") {
                if (nombre.isBlank() || filas.isEmpty()) {
                    aviso = "Poné un nombre y agregá al menos un ejercicio."
                    return@BotonPrincipal
                }
                scope.launch {
                    val ok = if (rutinaExistente == null) {
                        crearRutinaPropia(nombre.trim(), filas.toList(), yaTeniaAlguna = !DatosRemotos.misRutinas.isNullOrEmpty())
                    } else {
                        editarRutinaPropia(rutinaExistente.id, nombre.trim(), filas.toList())
                    }
                    if (ok) {
                        DatosRemotos.recargarMisRutinas()
                        onGuardado()
                    } else {
                        aviso = "No se pudo guardar — revisá tu conexión e intentá de nuevo."
                    }
                }
            }
        }
    }
}

@Composable
private fun FilaEjercicioEditor(ejercicio: EjercicioRutina, onCambiar: (EjercicioRutina) -> Unit, onQuitar: () -> Unit) {
    TarjetaOro(Modifier.fillMaxWidth(), radio = 14) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(ejercicio.nombre, fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                if (ejercicio.ejercicioId == null) {
                    Text("Escrito a mano — sin ficha de técnica", fontSize = 10.5.sp, color = Olimpos.Muted)
                }
            }
            Text("✕", color = Olimpos.Muted, fontWeight = FontWeight.Black, modifier = Modifier.clickable { onQuitar() })
        }
        Spacer(Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Series", fontSize = 10.sp, color = Olimpos.Muted, modifier = Modifier.weight(1f))
            PasoChico("－") { if (ejercicio.seriesObjetivo > 1) onCambiar(ejercicio.copy(seriesObjetivo = ejercicio.seriesObjetivo - 1)) }
            Text(
                "${ejercicio.seriesObjetivo}", fontSize = 13.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream,
                modifier = Modifier.width(28.dp), textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
            PasoChico("＋") { onCambiar(ejercicio.copy(seriesObjetivo = ejercicio.seriesObjetivo + 1)) }
        }
        Spacer(Modifier.height(6.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Peso de partida", fontSize = 10.sp, color = Olimpos.Muted, modifier = Modifier.weight(1f))
            PasoChico("－") { onCambiar(ejercicio.copy(pesoBaseKg = (ejercicio.pesoBaseKg - 2.5f).coerceAtLeast(0f))) }
            Text(
                "%.1f".format(ejercicio.pesoBaseKg).replace('.', ',') + "kg", fontSize = 13.sp, fontWeight = FontWeight.Black,
                color = Olimpos.Cream, modifier = Modifier.width(60.dp), textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
            PasoChico("＋") { onCambiar(ejercicio.copy(pesoBaseKg = ejercicio.pesoBaseKg + 2.5f)) }
        }
    }
}

@Composable
private fun PasoChico(simbolo: String, onClick: () -> Unit) {
    Box(
        Modifier
            .size(30.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(Olimpos.Card)
            .border(1.dp, Olimpos.Line, RoundedCornerShape(10.dp))
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) { Text(simbolo, color = Olimpos.GoldLight, fontWeight = FontWeight.Black, fontSize = 15.sp) }
}
