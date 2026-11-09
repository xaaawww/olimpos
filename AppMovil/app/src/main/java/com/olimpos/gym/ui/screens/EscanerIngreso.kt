package com.olimpos.gym.ui.screens

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.QrCodeScanner
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.adentroDesde
import com.olimpos.gym.data.registrarIngresoConQr
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val VerdeFondo = Color(0xFFDCFCE7)
private val VerdeTexto = Color(0xFF16A34A)

/** "menos de un minuto", "25 min" o "1 h 10 min". */
private fun tiempoDesde(desde: Long, ahora: Long): String {
    val minutos = ((ahora - desde) / 60_000L).coerceAtLeast(0L)
    if (minutos < 1) return "menos de un minuto"
    val h = minutos / 60
    val m = minutos % 60
    return if (h > 0) "$h h $m min" else "$m min"
}

/**
 * Entrada al gimnasio: si el socio ya escaneó el QR de la recepción en el
 * último rato muestra "Estás en el gimnasio"; si no, el botón que abre la
 * cámara. El QR lo valida la API (ver IngresoRepository.kt).
 */
@Composable
fun IngresoConQr(modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope()
    var registrando by remember { mutableStateOf(false) }
    var aviso by remember { mutableStateOf<Pair<String, Boolean>?>(null) }   // texto, es error
    // Cada 30 s se mira el reloj (para "hace X min" y para dejar de contar como
    // adentro a los 90 minutos) y cada minuto se recargan los ingresos: así
    // también aparece la entrada que la recepción registra con el DNI.
    var ahora by remember { mutableLongStateOf(System.currentTimeMillis()) }
    LaunchedEffect(Unit) {
        var vuelta = 0
        while (true) {
            delay(30_000)
            if (++vuelta % 2 == 0) DatosRemotos.recargarIngresos()
            ahora = System.currentTimeMillis()
        }
    }
    val desde = adentroDesde(DatosRemotos.ingresos, ahora)

    val escaner = rememberLauncherForActivityResult(ScanContract()) { resultado ->
        val texto = resultado.contents ?: return@rememberLauncherForActivityResult   // canceló
        registrando = true
        aviso = null
        scope.launch {
            val r = registrarIngresoConQr(texto)
            if (r.ok) {
                DatosRemotos.recargarIngresos()
                ahora = System.currentTimeMillis()
                aviso = (if (r.nuevo) "Entrada registrada · ¡Bienvenido!" else "Ya estabas registrado adentro.") to false
            } else {
                aviso = (r.error ?: "No se pudo registrar la entrada.") to true
            }
            registrando = false
        }
    }

    Column(modifier) {
        if (desde != null) {
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(VerdeFondo)
                    .padding(horizontal = 14.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(Modifier.size(9.dp).clip(CircleShape).background(VerdeTexto))
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)) {
                    Text(
                        "En el gimnasio hace ${tiempoDesde(desde, ahora)}",
                        fontSize = 13.5.sp, fontWeight = FontWeight.SemiBold, color = VerdeTexto
                    )
                    Text(
                        "Entraste a las ${SimpleDateFormat("HH:mm", Locale("es", "AR")).format(Date(desde))}" +
                            if (DatosRemotos.ingresos?.maxByOrNull { it.timestamp }?.metodo == "qr") " con el QR" else " · registrado en recepción",
                        fontSize = 11.5.sp, color = VerdeTexto.copy(alpha = 0.8f)
                    )
                }
            }
        } else {
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(Olimpos.Gold)
                    .clickable(enabled = !registrando) {
                        escaner.launch(
                            ScanOptions()
                                .setDesiredBarcodeFormats(ScanOptions.QR_CODE)
                                .setPrompt("Apuntá al QR de la pantalla de la recepción")
                                .setBeepEnabled(false)
                                .setOrientationLocked(false)
                        )
                    }
                    .padding(vertical = 12.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Outlined.QrCodeScanner, null, tint = Olimpos.Dark, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text(
                    if (registrando) "Registrando tu entrada…" else "Escanear QR de entrada",
                    fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Dark
                )
            }
        }
        aviso?.let { (texto, error) ->
            Spacer(Modifier.height(8.dp))
            Text(
                texto, fontSize = 11.5.sp,
                color = if (error) Olimpos.Red else VerdeTexto,
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(10.dp))
                    .border(1.dp, (if (error) Olimpos.Red else VerdeTexto).copy(alpha = 0.3f), RoundedCornerShape(10.dp))
                    .padding(horizontal = 12.dp, vertical = 8.dp)
            )
        }
    }
}
