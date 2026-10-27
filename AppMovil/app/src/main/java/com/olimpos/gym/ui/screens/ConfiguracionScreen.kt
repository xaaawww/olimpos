package com.olimpos.gym.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
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
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.NIVELES_EXPERIENCIA
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.data.SocioAuth
import com.olimpos.gym.data.actualizarOcultoClasificacion
import com.olimpos.gym.data.guardarDatosFisicos
import com.olimpos.gym.data.guardarNotificacionesLogrosActivas
import com.olimpos.gym.data.socioActualNombre
import com.olimpos.gym.ui.theme.EscalaLetra
import com.olimpos.gym.ui.theme.Olimpos
import com.olimpos.gym.ui.theme.PreferenciasApp
import com.olimpos.gym.ui.theme.ThemeMode
import kotlinx.coroutines.launch

/** Configuración del socio: su cuenta (contraseña), sus datos físicos,
 *  objetivo, apariencia (tema y tamaño de letra), privacidad y avisos.
 *  Todo lo que se ve acá funciona de verdad: guarda en la base o en el celular. */
@Composable
fun ConfiguracionScreen(
    onVolver: () -> Unit,
    themeMode: ThemeMode,
    onThemeMode: (ThemeMode) -> Unit,
    objetivo: ObjetivoCompetencia?,
    onObjetivo: (ObjetivoCompetencia) -> Unit
) {
    val contexto = LocalContext.current
    val scope = rememberCoroutineScope()
    var notificacionesLogros by remember { mutableStateOf(LogrosToastState.notificacionesActivas) }
    var aviso by remember { mutableStateOf<Pair<String, Boolean>?>(null) }   // texto, es error
    var verPolitica by remember { mutableStateOf(false) }
    if (verPolitica) {
        PoliticaPrivacidadScreen(onVolver = { verPolitica = false })
        return
    }

    Column(Modifier.fillMaxSize().background(Olimpos.FondoA).verticalScroll(rememberScrollState())) {
        EncabezadoArena("Configuración", "Tu cuenta, tus datos y cómo se ve la app.", onVolver)

        Column(Modifier.padding(horizontal = 20.dp).padding(top = 4.dp, bottom = 26.dp)) {
            aviso?.let { (texto, esError) ->
                Text(
                    texto, fontSize = 12.5.sp, fontWeight = FontWeight.Medium,
                    color = if (esError) Olimpos.Red else Olimpos.Green,
                    modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp))
                        .background(if (esError) Olimpos.Red.copy(alpha = 0.08f) else Olimpos.Green.copy(alpha = 0.1f))
                        .padding(12.dp)
                )
                Spacer(Modifier.height(4.dp))
            }

            // ── Mi cuenta ──
            SeccionLabel("Mi cuenta")
            TarjetaLisa(Modifier.fillMaxWidth(), padding = 0.dp) {
                FilaDato("Nombre", socioActualNombre())
                Divisor()
                FilaDato("Email", SocioAuth.emailActual ?: "—")
                Divisor()
                CambiarPassword { texto, error -> aviso = texto to error }
            }

            // ── Mis datos físicos ──
            SeccionLabel("Mis datos")
            DatosFisicosEditables { texto, error -> aviso = texto to error }

            // ── Objetivo ──
            SeccionLabel("Mi objetivo")
            Text(
                "Adapta tus rankings, tu dieta y la racha de dieta.",
                fontSize = 12.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 10.dp)
            )
            FilaChips {
                ObjetivoCompetencia.entries.forEach { o ->
                    ChipArena("${o.emoji} ${o.etiqueta}", objetivo == o) { onObjetivo(o) }
                }
            }

            // ── Apariencia ──
            SeccionLabel("Apariencia")
            TarjetaLisa(Modifier.fillMaxWidth()) {
                Text("Tema", fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
                Spacer(Modifier.height(8.dp))
                PestanasPildora(
                    listOf("Claro", "Oscuro", "Automático"), ThemeMode.entries.indexOf(themeMode),
                    { onThemeMode(ThemeMode.entries[it]) }
                )
                Spacer(Modifier.height(14.dp))
                Text("Tamaño de letra", fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
                Spacer(Modifier.height(8.dp))
                PestanasPildora(
                    EscalaLetra.entries.map { it.etiqueta }, EscalaLetra.entries.indexOf(PreferenciasApp.escalaLetra),
                    { PreferenciasApp.guardarEscalaLetra(contexto, EscalaLetra.entries[it]) }
                )
                Spacer(Modifier.height(8.dp))
                Text("Se aplica en toda la app al instante.", fontSize = 11.sp, color = Olimpos.Muted)
            }

            // ── Privacidad y avisos ──
            SeccionLabel("Privacidad y avisos")
            TarjetaLisa(Modifier.fillMaxWidth(), padding = 0.dp) {
                val datos = DatosRemotos.datosFisicosPropios
                var visible by remember(datos) { mutableStateOf(!(datos?.ocultoClasificacion ?: false)) }
                FilaInterruptor(
                    "Aparecer en la Clasificación",
                    if (visible) "Otros socios te ven en la Escalera del Olimpo." else "Oculto: solo vos ves tu rango.",
                    visible, habilitado = datos != null
                ) { nuevo ->
                    visible = nuevo
                    scope.launch {
                        val ok = actualizarOcultoClasificacion(!nuevo)
                        DatosRemotos.recargarDatosFisicosPropios()
                        DatosRemotos.recargarRangosSocios()
                        if (!ok) aviso = "No se pudo guardar. Revisá tu conexión." to true
                    }
                }
                Divisor()
                FilaInterruptor(
                    "Aviso de logro desbloqueado", "Un cartel con sonido cuando conseguís un logro nuevo.",
                    notificacionesLogros
                ) { nuevo ->
                    notificacionesLogros = nuevo
                    LogrosToastState.notificacionesActivas = nuevo
                    guardarNotificacionesLogrosActivas(contexto, nuevo)
                }
            }

            // ── Datos y app ──
            SeccionLabel("Datos y app")
            TarjetaLisa(Modifier.fillMaxWidth(), padding = 0.dp) {
                var recargando by remember { mutableStateOf(false) }
                FilaAccion("Actualizar mis datos", if (recargando) "Actualizando…" else "Vuelve a traer membresía, marcas, rutina y dieta.") {
                    if (recargando) return@FilaAccion
                    recargando = true
                    scope.launch {
                        DatosRemotos.limpiar()
                        DatosRemotos.precargar()
                        recargando = false
                        aviso = "✓ Datos actualizados." to false
                    }
                }
                Divisor()
                FilaAccion("Política de privacidad", "Qué datos guardamos, para qué y tus derechos.") { verPolitica = true }
                Divisor()
                val version = remember {
                    try {
                        contexto.packageManager.getPackageInfo(contexto.packageName, 0).versionName
                    } catch (e: Exception) {
                        null
                    }
                }
                FilaDato("Versión de la app", version ?: "—")
            }
            Spacer(Modifier.height(72.dp))  // que el botón flotante de Argos no tape la última fila
        }
    }
}

@Composable
private fun Divisor() = HorizontalDivider(color = Olimpos.Line, thickness = 1.dp)

@Composable
private fun FilaDato(titulo: String, valor: String) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 13.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(titulo, fontSize = 13.sp, color = Olimpos.Muted, modifier = Modifier.weight(1f))
        Text(valor, fontSize = 13.5.sp, fontWeight = FontWeight.Medium, color = Olimpos.Cream, maxLines = 1)
    }
}

@Composable
private fun FilaAccion(titulo: String, sub: String, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onClick).padding(horizontal = 14.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.weight(1f)) {
            Text(titulo, fontSize = 13.5.sp, fontWeight = FontWeight.Medium, color = Olimpos.Cream)
            Text(sub, fontSize = 11.5.sp, color = Olimpos.Muted)
        }
        FlechaFila()
    }
}

@Composable
private fun FilaInterruptor(titulo: String, sub: String, activo: Boolean, habilitado: Boolean = true, onCambio: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(titulo, fontSize = 13.5.sp, fontWeight = FontWeight.Medium, color = Olimpos.Cream)
            Text(sub, fontSize = 11.5.sp, color = Olimpos.Muted)
        }
        Spacer(Modifier.width(10.dp))
        Switch(
            checked = activo, onCheckedChange = onCambio, enabled = habilitado,
            colors = SwitchDefaults.colors(
                checkedThumbColor = androidx.compose.ui.graphics.Color.White, checkedTrackColor = Olimpos.Gold,
                uncheckedThumbColor = Olimpos.Muted, uncheckedTrackColor = Olimpos.Superficie2,
                uncheckedBorderColor = Olimpos.Line
            )
        )
    }
}

/** Cambiar la contraseña: pide la actual (Firebase lo exige) y la nueva dos
 *  veces. También deja pedir el email de recuperación si no se acuerda. */
@Composable
private fun CambiarPassword(onAviso: (String, Boolean) -> Unit) {
    val scope = rememberCoroutineScope()
    var abierto by remember { mutableStateOf(false) }
    var actual by remember { mutableStateOf("") }
    var nueva by remember { mutableStateOf("") }
    var repetir by remember { mutableStateOf("") }
    var guardando by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    FilaAccion("Cambiar contraseña", "Elegí una nueva: 8 caracteres o más, con letras y números.") { abierto = !abierto; error = null }
    AnimatedVisibility(visible = abierto) {
        Column(Modifier.padding(horizontal = 14.dp).padding(bottom = 14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            CampoOro(actual, { actual = it; error = null }, "Contraseña actual", esPassword = true)
            CampoOro(nueva, { nueva = it; error = null }, "Contraseña nueva", esPassword = true)
            CampoOro(repetir, { repetir = it; error = null }, "Repetir la nueva", esPassword = true)
            error?.let { Text(it, fontSize = 12.sp, color = Olimpos.Red) }
            BotonPrincipal(if (guardando) "Guardando…" else "Guardar contraseña",
                habilitado = !guardando && actual.isNotBlank() && nueva.isNotBlank() && repetir.isNotBlank()) {
                if (nueva != repetir) {
                    error = "Las contraseñas nuevas no coinciden."
                    return@BotonPrincipal
                }
                guardando = true
                scope.launch {
                    val r = SocioAuth.cambiarPassword(actual, nueva)
                    guardando = false
                    if (r == null) {
                        actual = ""; nueva = ""; repetir = ""; abierto = false
                        onAviso("✓ Contraseña cambiada. La próxima vez entrá con la nueva.", false)
                    } else error = r
                }
            }
            Text(
                "¿No te acordás de la actual? Mandarme un email para restablecerla",
                fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.GoldLight,
                modifier = Modifier.clip(RoundedCornerShape(8.dp)).clickable {
                    scope.launch {
                        val r = SocioAuth.enviarEmailRecuperacion(SocioAuth.emailActual ?: "")
                        onAviso(r ?: "✓ Te mandamos un email a ${SocioAuth.emailActual} para elegir una contraseña nueva.", r != null)
                    }
                }.padding(vertical = 4.dp)
            )
        }
    }
}

/** Peso, edad, nivel y condición médica: los usan la Arena (rangos según tu
 *  peso), la dieta y el entrenador. */
@Composable
private fun DatosFisicosEditables(onAviso: (String, Boolean) -> Unit) {
    val datos = DatosRemotos.datosFisicosPropios
    val scope = rememberCoroutineScope()
    if (datos == null) {
        TarjetaLisa(Modifier.fillMaxWidth()) {
            Text("Cargando tus datos…", fontSize = 12.5.sp, color = Olimpos.Muted)
        }
        return
    }
    var peso by remember(datos) { mutableStateOf(datos.pesoKg.let { if (it % 1f == 0f) it.toInt().toString() else it.toString() }) }
    var edad by remember(datos) { mutableStateOf(datos.edad.toString()) }
    var nivel by remember(datos) { mutableStateOf(datos.experiencia) }
    var condicion by remember(datos) { mutableStateOf(datos.condicionMedica) }
    var guardando by remember { mutableStateOf(false) }

    TarjetaLisa(Modifier.fillMaxWidth()) {
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            CampoOro(peso, { peso = it.filter { c -> c.isDigit() || c == ',' || c == '.' }.take(5) }, "Peso (kg)",
                Modifier.weight(1f), teclado = KeyboardType.Decimal)
            CampoOro(edad, { edad = it.filter(Char::isDigit).take(3) }, "Edad", Modifier.weight(1f), teclado = KeyboardType.Number)
        }
        Spacer(Modifier.height(12.dp))
        Text("Nivel", fontSize = 12.5.sp, color = Olimpos.Muted)
        Spacer(Modifier.height(6.dp))
        PestanasPildora(NIVELES_EXPERIENCIA, NIVELES_EXPERIENCIA.indexOf(nivel).coerceAtLeast(0), { nivel = NIVELES_EXPERIENCIA[it] })
        Spacer(Modifier.height(12.dp))
        CampoOro(condicion, { condicion = it.take(200) }, "Lesión o condición médica (opcional)")
        Spacer(Modifier.height(12.dp))
        val pesoNum = peso.replace(",", ".").toFloatOrNull()
        val edadNum = edad.toIntOrNull()
        val error = when {
            pesoNum == null || pesoNum !in 20f..400f -> "El peso tiene que estar entre 20 y 400 kg."
            edadNum == null || edadNum !in 14..100 -> "La edad tiene que estar entre 14 y 100 años."
            else -> null
        }
        val cambio = pesoNum != datos.pesoKg || edadNum != datos.edad || nivel != datos.experiencia || condicion.trim() != datos.condicionMedica
        if (error != null && cambio) {
            Text(error, fontSize = 12.sp, color = Olimpos.Red)
            Spacer(Modifier.height(8.dp))
        }
        BotonPrincipal(if (guardando) "Guardando…" else "Guardar mis datos", habilitado = cambio && error == null && !guardando) {
            guardando = true
            scope.launch {
                val ok = guardarDatosFisicos(datos.copy(pesoKg = pesoNum!!, edad = edadNum!!, experiencia = nivel, condicionMedica = condicion.trim()))
                DatosRemotos.recargarDatosFisicosPropios()
                DatosRemotos.recargarRangosSocios()
                guardando = false
                onAviso(if (ok) "✓ Datos guardados. Tus rangos se recalculan con tu peso nuevo." else "No se pudo guardar. Revisá tu conexión.", !ok)
            }
        }
    }
}
