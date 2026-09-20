package com.olimpos.gym.ui.screens

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import coil.compose.AsyncImage
import com.olimpos.gym.data.ComidaRegistrada
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.Macros
import com.olimpos.gym.data.MetaDia
import com.olimpos.gym.data.MomentoComida
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.data.Plato
import com.olimpos.gym.data.borrarComidaEnFirebase
import com.olimpos.gym.data.cargarFotoComida
import com.olimpos.gym.data.comprimirImagenABase64
import com.olimpos.gym.data.diaCumplido
import com.olimpos.gym.data.fechaClave
import com.olimpos.gym.data.metaDelDia
import com.olimpos.gym.data.rachaDietaActual
import com.olimpos.gym.data.reglaDe
import com.olimpos.gym.data.registrarComidaEnFirebase
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/* ═══════════════════════ "Mi día" (dentro de Dieta) ═══════════════════════ */

/** Qué le toca comer hoy según su nutricionista (desayuno/almuerzo/cena), cómo
 *  va con las kcal y los macros de la meta, y la racha de dieta. */
@Composable
fun SeccionMiDia(objetivo: ObjetivoCompetencia?, platos: List<Plato>, onRegistrar: (MomentoComida) -> Unit) {
    val dieta = DatosRemotos.dietaAsignada
    val dias = DatosRemotos.diasComidas ?: emptyList()
    val meta = metaDelDia(dieta, platos)
    val hoy = dias.firstOrNull { it.fecha == fechaClave() }
    val objetivoEfectivo = objetivo ?: ObjetivoCompetencia.SALUD
    val racha = rachaDietaActual(dias, objetivoEfectivo, meta)
    val hoyCumplido = hoy != null && diaCumplido(hoy, objetivoEfectivo, meta)

    SeccionLabel("Mi día")
    TarjetaRachaDieta(racha, objetivoEfectivo, meta, hoyCumplido)
    Spacer(Modifier.height(12.dp))
    TarjetaMacrosHoy(hoy?.totales ?: Macros(), meta?.macros)
    Spacer(Modifier.height(12.dp))
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        MomentoComida.entries.forEach { momento ->
            TarjetaMomento(
                momento = momento,
                asignados = dieta?.platosDe(momento, platos).orEmpty(),
                registrada = hoy?.comidas?.get(momento),
                fecha = fechaClave(),
                onRegistrar = { onRegistrar(momento) }
            )
        }
    }
}

@Composable
private fun TarjetaRachaDieta(racha: Int, objetivo: ObjetivoCompetencia, meta: MetaDia?, hoyCumplido: Boolean) {
    TarjetaOro(Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconoCuadrado("🔥")
            Spacer(Modifier.width(13.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    "Racha de dieta: $racha ${if (racha == 1) "día" else "días"}",
                    fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, color = Olimpos.Cream
                )
                Text(
                    when {
                        meta == null ->
                            "Tu nutricionista todavía no te asignó una dieta. La racha arranca cuando la tengas."
                        hoyCumplido -> "¡Hoy ya cumpliste tu dieta! 🎉"
                        else ->
                            "Para sumar hoy: registrá tus comidas y quedá ${reglaDe(objetivo).descripcion}."
                    },
                    fontSize = 11.5.sp, lineHeight = 15.sp, color = Olimpos.Muted
                )
            }
        }
    }
}

@Composable
private fun TarjetaMacrosHoy(actual: Macros, meta: Macros?) {
    TarjetaOro(Modifier.fillMaxWidth()) {
        Text("Hoy llevás", fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
        Spacer(Modifier.height(10.dp))
        FilaMacro("Calorías", actual.kcal, meta?.kcal, " kcal", Olimpos.Gold)
        Spacer(Modifier.height(9.dp))
        FilaMacro("Proteínas", actual.proteinas, meta?.proteinas, " g", Color(0xFFEF7B6B))
        Spacer(Modifier.height(9.dp))
        FilaMacro("Carbohidratos", actual.carbs, meta?.carbs, " g", Color(0xFF6BA8EF))
        Spacer(Modifier.height(9.dp))
        FilaMacro("Grasas", actual.grasas, meta?.grasas, " g", Color(0xFF7BD389))
        if (meta == null || meta.kcal == 0) {
            Spacer(Modifier.height(8.dp))
            Text(
                if (meta == null) "Sin dieta asignada todavía: se muestra solo lo que registrás."
                else "Los platos de tu dieta todavía no tienen valores nutricionales cargados.",
                fontSize = 10.5.sp, color = Olimpos.Muted
            )
        }
    }
}

@Composable
private fun FilaMacro(etiqueta: String, actual: Int, meta: Int?, unidad: String, color: Color) {
    val hayMeta = meta != null && meta > 0
    Column {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(etiqueta, fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted, modifier = Modifier.weight(1f))
            Text(
                if (hayMeta) "$actual / $meta$unidad" else "$actual$unidad",
                fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream
            )
        }
        Spacer(Modifier.height(4.dp))
        Box(
            Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp))
                .background(Olimpos.Line)
        ) {
            if (hayMeta) {
                Box(
                    Modifier
                        .fillMaxWidth((actual.toFloat() / meta!!).coerceIn(0f, 1f))
                        .height(6.dp)
                        .clip(RoundedCornerShape(3.dp))
                        .background(color)
                )
            }
        }
    }
}

@Composable
private fun TarjetaMomento(
    momento: MomentoComida,
    asignados: List<Plato>,
    registrada: ComidaRegistrada?,
    fecha: String,
    onRegistrar: () -> Unit
) {
    val scope = rememberCoroutineScope()
    val foto by produceState<ByteArray?>(null, fecha, momento, registrada?.horaMs) {
        value = if (registrada != null) cargarFotoComida(fecha, momento) else null
    }
    val macrosAsignados = asignados.fold(Macros()) { acc, p -> acc + (p.macros ?: Macros()) }

    TarjetaOro(Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier
                    .size(64.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(Olimpos.GoldSoft)
                    .border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp)),
                contentAlignment = Alignment.Center
            ) {
                if (foto != null) {
                    AsyncImage(
                        model = foto, contentDescription = "Foto de ${momento.etiqueta}",
                        contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize()
                    )
                } else {
                    Text(momento.emoji, fontSize = 26.sp)
                }
            }
            Spacer(Modifier.width(13.dp))
            Column(Modifier.weight(1f)) {
                Text("${momento.emoji} ${momento.etiqueta}", fontWeight = FontWeight.ExtraBold, fontSize = 14.sp, color = Olimpos.Cream)
                Text(
                    if (asignados.isEmpty()) "Sin plato asignado en este horario"
                    else "Asignado: " + asignados.joinToString(" + ") { it.nombre } +
                        if (macrosAsignados.kcal > 0) " · ${macrosAsignados.kcal} kcal" else "",
                    fontSize = 11.sp, lineHeight = 14.sp, color = Olimpos.Muted
                )
                if (registrada != null) {
                    Text(
                        "✓ Registrado a las ${horaLegible(registrada.horaMs)} · ${registrada.macros.kcal} kcal · " +
                            "P ${registrada.macros.proteinas} · C ${registrada.macros.carbs} · G ${registrada.macros.grasas}",
                        fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Olimpos.GoldLight,
                        modifier = Modifier.padding(top = 3.dp)
                    )
                } else {
                    Text("Pendiente", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Olimpos.Muted, modifier = Modifier.padding(top = 3.dp))
                }
            }
        }
        Spacer(Modifier.height(10.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            BotonSecundario(
                if (registrada != null) "📸 Cambiar" else "📸 Registrar comida",
                Modifier.weight(1f), onClick = onRegistrar
            )
            if (registrada != null) {
                Text(
                    "🗑️ Borrar", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Olimpos.Red,
                    modifier = Modifier
                        .clickable {
                            scope.launch {
                                borrarComidaEnFirebase(fecha, momento)
                                DatosRemotos.recargarComidas()
                            }
                        }
                        .padding(horizontal = 8.dp, vertical = 10.dp)
                )
            }
        }
    }
}

private fun horaLegible(ms: Long): String = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(ms))

/* ═══════════════════════ Registrar una comida (foto + macros) ═══════════════════════ */

@Composable
fun RegistrarComidaScreen(
    momento: MomentoComida,
    objetivo: ObjetivoCompetencia?,
    platos: List<Plato>,
    onVolver: () -> Unit
) {
    val contexto = LocalContext.current
    val scope = rememberCoroutineScope()
    val dieta = DatosRemotos.dietaAsignada
    val asignados = dieta?.platosDe(momento, platos).orEmpty()
    val macrosAsignados = asignados.fold(Macros()) { acc, p -> acc + (p.macros ?: Macros()) }

    var uriFoto by remember { mutableStateOf<Uri?>(null) }
    var uriCamara by remember { mutableStateOf<Uri?>(null) }
    var comioAsignado by remember { mutableStateOf(asignados.isNotEmpty()) }
    var kcal by remember { mutableStateOf(if (asignados.isNotEmpty() && macrosAsignados.kcal > 0) macrosAsignados.kcal.toString() else "") }
    var proteinas by remember { mutableStateOf(if (asignados.isNotEmpty() && macrosAsignados.proteinas > 0) macrosAsignados.proteinas.toString() else "") }
    var carbs by remember { mutableStateOf(if (asignados.isNotEmpty() && macrosAsignados.carbs > 0) macrosAsignados.carbs.toString() else "") }
    var grasas by remember { mutableStateOf(if (asignados.isNotEmpty() && macrosAsignados.grasas > 0) macrosAsignados.grasas.toString() else "") }
    var nota by remember { mutableStateOf("") }
    var guardando by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    val camara = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { exito ->
        if (exito) uriFoto = uriCamara
    }
    val galeria = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null) uriFoto = uri
    }

    fun sacarFoto() {
        val carpeta = File(contexto.cacheDir, "fotos_comidas").apply { mkdirs() }
        val archivo = File.createTempFile("comida_", ".jpg", carpeta)
        val uri = FileProvider.getUriForFile(contexto, "${contexto.packageName}.fileprovider", archivo)
        uriCamara = uri
        camara.launch(uri)
    }

    fun elegirAsignado(elegido: Boolean) {
        comioAsignado = elegido
        if (elegido) {
            kcal = if (macrosAsignados.kcal > 0) macrosAsignados.kcal.toString() else ""
            proteinas = if (macrosAsignados.proteinas > 0) macrosAsignados.proteinas.toString() else ""
            carbs = if (macrosAsignados.carbs > 0) macrosAsignados.carbs.toString() else ""
            grasas = if (macrosAsignados.grasas > 0) macrosAsignados.grasas.toString() else ""
        } else {
            kcal = ""; proteinas = ""; carbs = ""; grasas = ""
        }
    }

    val puedeGuardar = uriFoto != null && (kcal.toIntOrNull() ?: 0) > 0 && !guardando

    fun guardar() {
        val foto = uriFoto ?: return
        guardando = true
        error = null
        scope.launch {
            val base64 = withContext(Dispatchers.IO) { comprimirImagenABase64(contexto, foto, 640) }
            if (base64 == null) {
                error = "No se pudo procesar esa foto — probá con otra."
                guardando = false
                return@launch
            }
            val ok = registrarComidaEnFirebase(
                momento = momento,
                macros = Macros(
                    kcal = kcal.toIntOrNull() ?: 0,
                    proteinas = proteinas.toIntOrNull() ?: 0,
                    carbs = carbs.toIntOrNull() ?: 0,
                    grasas = grasas.toIntOrNull() ?: 0
                ),
                platoIds = if (comioAsignado) asignados.map { it.id } else emptyList(),
                nota = nota.trim(),
                imagenBase64 = base64,
                meta = metaDelDia(dieta, platos),
                objetivo = objetivo
            )
            if (ok) {
                DatosRemotos.recargarComidas()
                onVolver()
            } else {
                error = "No se pudo guardar. Revisá tu conexión e intentá de nuevo."
                guardando = false
            }
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .imePadding()
            .verticalScroll(rememberScrollState())
    ) {
        EncabezadoVolver("${momento.emoji} ${momento.etiqueta}", "Registrá lo que comiste con una foto", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            SeccionLabel("Foto de tu comida")
            Box(
                Modifier
                    .fillMaxWidth()
                    .height(210.dp)
                    .clip(RoundedCornerShape(18.dp))
                    .background(Olimpos.Card)
                    .border(1.dp, Olimpos.Line, RoundedCornerShape(18.dp)),
                contentAlignment = Alignment.Center
            ) {
                if (uriFoto != null) {
                    AsyncImage(
                        model = uriFoto, contentDescription = "Tu comida",
                        contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize()
                    )
                } else {
                    Text("La foto es obligatoria: es tu comprobante", fontSize = 12.sp, color = Olimpos.Muted)
                }
            }
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                BotonSecundario("📷 Sacar foto", Modifier.weight(1f)) { sacarFoto() }
                BotonSecundario("🖼️ De la galería", Modifier.weight(1f)) {
                    galeria.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly))
                }
            }

            SeccionLabel("¿Qué comiste?")
            if (asignados.isNotEmpty()) {
                OpcionGrande(
                    "✅",
                    "Lo asignado: " + asignados.joinToString(" + ") { it.nombre },
                    comioAsignado
                ) { elegirAsignado(true) }
                Spacer(Modifier.height(10.dp))
                OpcionGrande("🍽️", "Comí otra cosa", !comioAsignado) { elegirAsignado(false) }
            } else {
                Text(
                    "No tenés ningún plato asignado en este horario — cargá los valores de lo que comiste.",
                    fontSize = 12.sp, color = Olimpos.Muted
                )
            }

            SeccionLabel("Valores de esta comida")
            if (comioAsignado && asignados.isNotEmpty() && macrosAsignados.esVacio) {
                Text(
                    "Tu nutricionista todavía no cargó los valores de estos platos: completalos vos.",
                    fontSize = 11.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 8.dp)
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                CampoOro(kcal, { kcal = it.filter(Char::isDigit); error = null }, "Calorías (kcal)", Modifier.weight(1f), teclado = KeyboardType.Number)
                CampoOro(proteinas, { proteinas = it.filter(Char::isDigit) }, "Proteínas (g)", Modifier.weight(1f), teclado = KeyboardType.Number)
            }
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                CampoOro(carbs, { carbs = it.filter(Char::isDigit) }, "Carbohidratos (g)", Modifier.weight(1f), teclado = KeyboardType.Number)
                CampoOro(grasas, { grasas = it.filter(Char::isDigit) }, "Grasas (g)", Modifier.weight(1f), teclado = KeyboardType.Number)
            }
            Spacer(Modifier.height(10.dp))
            CampoOro(nota, { nota = it }, "Nota (opcional)")

            error?.let {
                Spacer(Modifier.height(12.dp))
                Text(it, fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Olimpos.Red)
            }

            Spacer(Modifier.height(20.dp))
            if (guardando) {
                Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = Olimpos.Gold)
                }
            } else {
                BotonPrincipal("Guardar comida", habilitado = puedeGuardar) { guardar() }
                if (!puedeGuardar) {
                    Text(
                        "Falta la foto y al menos las calorías para guardar.",
                        fontSize = 11.sp, color = Olimpos.Muted, modifier = Modifier.padding(top = 8.dp)
                    )
                }
            }
        }
    }
}
