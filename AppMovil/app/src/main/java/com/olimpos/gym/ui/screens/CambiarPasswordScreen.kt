package com.olimpos.gym.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.R
import com.olimpos.gym.data.SocioAuth
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

/**
 * Se muestra una única vez, en el primer login: el empleado le crea al
 * socio una contraseña generada al azar (ver auth_repo.py), y acá el
 * propio socio la reemplaza por una que le resulte cómoda. Es obligatoria
 * (no hay forma de saltearla) — mismo criterio que [OnboardingScreen].
 */
@Composable
fun CambiarPasswordScreen(onListo: () -> Unit) {
    var nueva by remember { mutableStateOf("") }
    var confirmar by remember { mutableStateOf("") }
    var cargando by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    fun confirmarCambio() {
        if (cargando) return
        if (nueva.length < 6) {
            error = "La contraseña tiene que tener al menos 6 caracteres."
            return
        }
        if (nueva != confirmar) {
            error = "Las contraseñas no coinciden."
            return
        }
        cargando = true
        error = null
        scope.launch {
            val mensaje = SocioAuth.actualizarPassword(nueva)
            cargando = false
            if (mensaje == null) onListo() else error = mensaje
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .background(Brush.linearGradient(listOf(Olimpos.FondoA, Olimpos.FondoB, Olimpos.FondoC)))
            .statusBarsPadding()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 26.dp)
    ) {
        Spacer(Modifier.height(56.dp))

        Image(
            painter = painterResource(R.drawable.logo_olimpos),
            contentDescription = "OlimpΩs",
            contentScale = ContentScale.Fit,
            modifier = Modifier
                .size(88.dp)
                .align(Alignment.CenterHorizontally)
        )

        Spacer(Modifier.height(18.dp))
        Text(
            "Elegí tu contraseña", fontSize = 24.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream,
            modifier = Modifier.align(Alignment.CenterHorizontally)
        )
        Text(
            "Es tu primer ingreso — cambiá la contraseña temporal por una que te resulte cómoda.",
            fontSize = 13.sp, color = Olimpos.Muted,
            modifier = Modifier
                .align(Alignment.CenterHorizontally)
                .padding(top = 6.dp, bottom = 34.dp)
        )

        TarjetaOro(Modifier.fillMaxWidth()) {
            Text("Nueva contraseña", fontWeight = FontWeight.ExtraBold, fontSize = 16.sp, color = Olimpos.Cream)
            Spacer(Modifier.height(14.dp))
            CampoOro(nueva, { nueva = it; error = null }, "Contraseña nueva", esPassword = true)
            Spacer(Modifier.height(12.dp))
            CampoOro(confirmar, { confirmar = it; error = null }, "Confirmar contraseña", esPassword = true)

            error?.let {
                Spacer(Modifier.height(12.dp))
                Text(it, fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Olimpos.Red)
            }
        }

        Spacer(Modifier.height(20.dp))
        if (cargando) {
            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = Olimpos.Gold)
            }
        } else {
            BotonPrincipal(
                "Confirmar cambio",
                habilitado = nueva.isNotBlank() && confirmar.isNotBlank()
            ) { confirmarCambio() }
        }

        Spacer(Modifier.height(20.dp))
        Box(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(Olimpos.Card)
                .padding(14.dp)
        ) {
            Text(
                "Este paso solo aparece la primera vez que entrás a la app.",
                fontSize = 11.5.sp, color = Olimpos.Muted
            )
        }

        Spacer(Modifier.height(30.dp))
    }
}
