package com.olimpos.gym.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
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
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
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
import com.olimpos.gym.ui.theme.Olimpos

@Composable
fun LoginScreen(onIngresar: () -> Unit, onRegistrarse: () -> Unit) {
    var esRegistro by remember { mutableStateOf(false) }
    var nombre by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }

    Column(
        Modifier
            .fillMaxSize()
            .background(Brush.linearGradient(listOf(Olimpos.FondoA, Olimpos.FondoB, Olimpos.FondoC)))
            .statusBarsPadding()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 26.dp)
    ) {
        Spacer(Modifier.height(40.dp))

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

        // ── Selector Ingresar / Crear cuenta ──
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            if (esRegistro) {
                BotonSecundario("Ingresar", Modifier.weight(1f)) { esRegistro = false }
                BotonPrincipal("Crear cuenta", Modifier.weight(1f)) { esRegistro = true }
            } else {
                BotonPrincipal("Ingresar", Modifier.weight(1f)) { esRegistro = false }
                BotonSecundario("Crear cuenta", Modifier.weight(1f)) { esRegistro = true }
            }
        }

        Spacer(Modifier.height(22.dp))

        TarjetaOro(Modifier.fillMaxWidth()) {
            if (esRegistro) {
                Text("Creá tu cuenta", fontWeight = FontWeight.ExtraBold, fontSize = 16.sp, color = Olimpos.Cream)
                Spacer(Modifier.height(14.dp))
                CampoOro(nombre, { nombre = it }, "Nombre y apellido")
                Spacer(Modifier.height(12.dp))
            } else {
                Text("Iniciá sesión", fontWeight = FontWeight.ExtraBold, fontSize = 16.sp, color = Olimpos.Cream)
                Spacer(Modifier.height(14.dp))
            }
            CampoOro(email, { email = it }, "Email", teclado = KeyboardType.Email)
            Spacer(Modifier.height(12.dp))
            CampoOro(password, { password = it }, "Contraseña", esPassword = true)
            if (!esRegistro) {
                Text(
                    "¿Olvidaste tu contraseña?",
                    fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Olimpos.GoldLight,
                    modifier = Modifier.padding(top = 12.dp)
                )
            }
        }

        Spacer(Modifier.height(20.dp))
        BotonPrincipal(if (esRegistro) "Crear cuenta y continuar" else "Ingresar") {
            if (esRegistro) onRegistrarse() else onIngresar()
        }

        Spacer(Modifier.height(24.dp))
        Text(
            "Al continuar aceptás los Términos y la Política de Privacidad de OlimpΩs.",
            fontSize = 10.5.sp, color = Olimpos.Muted,
            modifier = Modifier.padding(bottom = 30.dp)
        )
    }
}
