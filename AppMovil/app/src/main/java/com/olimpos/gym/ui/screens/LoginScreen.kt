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
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.R
import com.olimpos.gym.data.SocioAuth
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

/**
 * Login real contra Firebase Auth — sin opción de "crear cuenta": el socio
 * nunca se registra solo, un empleado le crea el usuario desde el sistema
 * de gestión (ver auth_repo.py) y le pasa el email/contraseña acá.
 */
@Composable
fun LoginScreen(onIngresar: () -> Unit) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var cargando by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    fun intentarIngresar() {
        if (email.isBlank() || password.isBlank() || cargando) return
        cargando = true
        error = null
        scope.launch {
            val mensaje = SocioAuth.iniciarSesion(email, password)
            cargando = false
            if (mensaje == null) onIngresar() else error = mensaje
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

        // Logo oficial de OlimpΩs — elemento principal de marca en el login
        Image(
            painter = painterResource(R.drawable.logo_olimpos),
            contentDescription = "OlimpΩs",
            contentScale = ContentScale.Fit,
            modifier = Modifier
                .size(108.dp)
                .align(Alignment.CenterHorizontally)
        )

        Spacer(Modifier.height(14.dp))
        Text(
            "OlimpΩs", fontSize = 30.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream,
            modifier = Modifier.align(Alignment.CenterHorizontally)
        )
        Text(
            "Despertá al dios que llevás dentro",
            fontSize = 13.sp, color = Olimpos.Muted,
            modifier = Modifier
                .align(Alignment.CenterHorizontally)
                .padding(top = 2.dp, bottom = 34.dp)
        )

        TarjetaOro(Modifier.fillMaxWidth()) {
            Text("Iniciá sesión", fontWeight = FontWeight.ExtraBold, fontSize = 16.sp, color = Olimpos.Cream)
            Spacer(Modifier.height(14.dp))
            CampoOro(email, { email = it; error = null }, "Email", teclado = KeyboardType.Email)
            Spacer(Modifier.height(12.dp))
            CampoOro(password, { password = it; error = null }, "Contraseña", esPassword = true)

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
            BotonPrincipal("Ingresar", habilitado = email.isNotBlank() && password.isNotBlank()) {
                intentarIngresar()
            }
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
                "¿Todavía no tenés cuenta? Pedísela a tu entrenador o a recepción — el acceso a la app te lo crea el gimnasio.",
                fontSize = 11.5.sp, color = Olimpos.Muted
            )
        }

        Spacer(Modifier.height(24.dp))
        Text(
            "Al continuar aceptás los Términos y la Política de Privacidad de OlimpΩs.",
            fontSize = 10.5.sp, color = Olimpos.Muted,
            modifier = Modifier.padding(bottom = 30.dp)
        )
    }
}
