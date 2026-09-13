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
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DIAS_SEMANA
import com.olimpos.gym.data.FRANJAS_HORARIAS
import com.olimpos.gym.data.NIVELES_EXPERIENCIA
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.ui.theme.Olimpos

private const val TOTAL_PASOS = 4

@Composable
fun OnboardingScreen(onFinalizar: () -> Unit) {
    var paso by remember { mutableIntStateOf(0) }

    // Paso 1: datos físicos
    var peso by remember { mutableStateOf("") }
    var altura by remember { mutableStateOf("") }
    var edad by remember { mutableStateOf("") }
    var condicion by remember { mutableStateOf("") }

    // Paso 2: objetivo
    var objetivo by remember { mutableStateOf<ObjetivoCompetencia?>(null) }

    // Paso 3: experiencia
    var experiencia by remember { mutableStateOf<String?>(null) }

    // Paso 4: disponibilidad
    var diasElegidos by remember { mutableStateOf(setOf<String>()) }
    var franja by remember { mutableStateOf<String?>(null) }

    val puedeContinuar = when (paso) {
        0 -> peso.isNotBlank() && altura.isNotBlank() && edad.isNotBlank()
        1 -> objetivo != null
        2 -> experiencia != null
        3 -> diasElegidos.isNotEmpty() && franja != null
        else -> true
    }

    Column(
        Modifier
            .fillMaxSize()
            .background(Brush.linearGradient(listOf(Olimpos.FondoA, Olimpos.FondoB, Olimpos.FondoC)))
            .statusBarsPadding()
    ) {
        Column(Modifier.padding(horizontal = 24.dp, vertical = 18.dp)) {
            Eyebrow("Paso ${paso + 1} de $TOTAL_PASOS")
            Spacer(Modifier.height(10.dp))
            PuntosPaso(TOTAL_PASOS, paso)
        }

        Column(
            Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp)
        ) {
            when (paso) {
                0 -> PasoFisico(peso, { peso = it }, altura, { altura = it }, edad, { edad = it }, condicion, { condicion = it })
                1 -> PasoObjetivo(objetivo) { objetivo = it }
                2 -> PasoExperiencia(experiencia) { experiencia = it }
                3 -> PasoDisponibilidad(diasElegidos, { diasElegidos = it }, franja) { franja = it }
            }
            Spacer(Modifier.height(24.dp))
        }

        Row(
            Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 18.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            if (paso > 0) {
                BotonSecundario("Atrás", Modifier.weight(1f)) { paso-- }
            }
            BotonPrincipal(
                if (paso == TOTAL_PASOS - 1) "Finalizar" else "Continuar",
                Modifier.weight(1f),
                habilitado = puedeContinuar
            ) {
                if (paso == TOTAL_PASOS - 1) onFinalizar() else paso++
            }
        }
    }
}

@Composable
private fun PasoFisico(
    peso: String, onPeso: (String) -> Unit,
    altura: String, onAltura: (String) -> Unit,
    edad: String, onEdad: (String) -> Unit,
    condicion: String, onCondicion: (String) -> Unit
) {
    Text("Contanos de tu cuerpo", fontSize = 24.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
    Text(
        "Con estos datos calculamos tus estándares de fuerza y tu plan inicial.",
        fontSize = 13.sp, color = Olimpos.Muted,
        modifier = Modifier.padding(top = 4.dp, bottom = 22.dp)
    )
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        CampoOro(peso, onPeso, "Peso (kg)", Modifier.weight(1f), teclado = KeyboardType.Number)
        CampoOro(altura, onAltura, "Altura (cm)", Modifier.weight(1f), teclado = KeyboardType.Number)
    }
    Spacer(Modifier.height(12.dp))
    CampoOro(edad, onEdad, "Edad", teclado = KeyboardType.Number)
    Spacer(Modifier.height(12.dp))
    CampoOro(condicion, onCondicion, "Condición médica (opcional)")
}

@Composable
private fun PasoObjetivo(seleccionado: ObjetivoCompetencia?, onSeleccion: (ObjetivoCompetencia) -> Unit) {
    Text("¿Cuál es tu objetivo?", fontSize = 24.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
    Text(
        "Vamos a adaptar tu rutina, tu perfil de competencia y tus rankings.",
        fontSize = 13.sp, color = Olimpos.Muted,
        modifier = Modifier.padding(top = 4.dp, bottom = 22.dp)
    )
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        ObjetivoCompetencia.entries.forEach { obj ->
            OpcionGrande(obj.emoji, obj.etiqueta, seleccionado == obj) { onSeleccion(obj) }
        }
    }
}

@Composable
private fun PasoExperiencia(seleccionado: String?, onSeleccion: (String) -> Unit) {
    Text("¿Cuál es tu nivel?", fontSize = 24.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
    Text(
        "Así ajustamos la dificultad y el peso sugerido en tus ejercicios.",
        fontSize = 13.sp, color = Olimpos.Muted,
        modifier = Modifier.padding(top = 4.dp, bottom = 22.dp)
    )
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        NIVELES_EXPERIENCIA.forEach { nivel ->
            OpcionGrande("💪", nivel, seleccionado == nivel) { onSeleccion(nivel) }
        }
    }
}

@Composable
private fun PasoDisponibilidad(
    diasElegidos: Set<String>, onDias: (Set<String>) -> Unit,
    franja: String?, onFranja: (String) -> Unit
) {
    Text("Tu disponibilidad", fontSize = 24.sp, fontWeight = FontWeight.Black, color = Olimpos.Cream)
    Text(
        "Elegí los días y el horario en que solés entrenar.",
        fontSize = 13.sp, color = Olimpos.Muted,
        modifier = Modifier.padding(top = 4.dp, bottom = 22.dp)
    )
    SeccionLabel("Días")
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        DIAS_SEMANA.take(4).forEach { dia ->
            ChipSeleccionable(dia, dia in diasElegidos, Modifier.wrapContentWidth()) {
                onDias(if (dia in diasElegidos) diasElegidos - dia else diasElegidos + dia)
            }
        }
    }
    Spacer(Modifier.height(8.dp))
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        DIAS_SEMANA.drop(4).forEach { dia ->
            ChipSeleccionable(dia, dia in diasElegidos, Modifier.wrapContentWidth()) {
                onDias(if (dia in diasElegidos) diasElegidos - dia else diasElegidos + dia)
            }
        }
    }
    SeccionLabel("Franja horaria")
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        FRANJAS_HORARIAS.forEach { f ->
            OpcionGrande("🕐", f, franja == f) { onFranja(f) }
        }
    }
}

