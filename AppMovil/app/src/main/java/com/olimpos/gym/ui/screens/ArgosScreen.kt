package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.MensajeArgos
import com.olimpos.gym.data.preguntarArgos
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

/** Chat simple con Argos — el historial vive solo en memoria de esta
 *  pantalla (se pierde al volver), a propósito: es una charla puntual, no
 *  algo que haga falta guardar. Nunca ejecuta ninguna acción, solo
 *  responde texto (ver ArgosRepository.kt/ArgosWorker). */
@Composable
fun ArgosScreen(onVolver: () -> Unit) {
    val scope = rememberCoroutineScope()
    var mensajes by remember { mutableStateOf(listOf<MensajeArgos>()) }
    var textoActual by remember { mutableStateOf("") }
    var enviando by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val estadoLista = rememberLazyListState()

    fun enviar() {
        val pregunta = textoActual.trim()
        if (pregunta.isEmpty() || enviando) return
        val historialPrevio = mensajes
        mensajes = mensajes + MensajeArgos("user", pregunta)
        textoActual = ""
        error = null
        enviando = true
        scope.launch {
            try {
                val respuesta = preguntarArgos(pregunta, historialPrevio)
                mensajes = mensajes + MensajeArgos("assistant", respuesta)
            } catch (e: Exception) {
                error = e.message ?: "No se pudo conectar con Argos."
            }
            enviando = false
        }
    }

    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver("🐕 Argos", "Tu asistente de IA en OlimpΩs", onVolver)

        LazyColumn(
            state = estadoLista,
            modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 12.dp)
        ) {
            if (mensajes.isEmpty()) {
                item {
                    Text(
                        "Preguntale a Argos sobre horarios, membresías, clases, máquinas, el catálogo de " +
                            "comidas, tu propio progreso o consejos generales de entrenamiento.",
                        fontSize = 12.5.sp, color = Olimpos.Muted
                    )
                }
            }
            items(mensajes) { m -> BurbujaArgos(m) }
            if (enviando) item { BurbujaArgos(MensajeArgos("assistant", "Escribiendo…"), atenuado = true) }
        }

        error?.let {
            Text(
                it, fontSize = 11.5.sp, color = Olimpos.Red,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
            )
        }

        Row(
            Modifier
                .fillMaxWidth()
                .imePadding()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            androidx.compose.material3.OutlinedTextField(
                value = textoActual,
                onValueChange = { textoActual = it },
                placeholder = { Text("Preguntale algo a Argos...", color = Olimpos.Muted, fontSize = 13.sp) },
                singleLine = false,
                maxLines = 4,
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(16.dp),
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 13.5.sp, color = Olimpos.Cream),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Olimpos.Cream, unfocusedTextColor = Olimpos.Cream,
                    focusedBorderColor = Olimpos.Gold, unfocusedBorderColor = Olimpos.Line,
                    cursorColor = Olimpos.Gold,
                    focusedContainerColor = Olimpos.Card, unfocusedContainerColor = Olimpos.Card
                )
            )
            Box(
                Modifier
                    .clip(RoundedCornerShape(14.dp))
                    .background(Olimpos.Gold)
                    .clickable(enabled = !enviando) { enviar() }
                    .padding(horizontal = 16.dp, vertical = 14.dp)
            ) {
                Text(if (enviando) "…" else "➤", fontWeight = FontWeight.Black, fontSize = 15.sp, color = Olimpos.Dark)
            }
        }
    }
}

@Composable
private fun BurbujaArgos(m: MensajeArgos, atenuado: Boolean = false) {
    val esUsuario = m.rol == "user"
    val color = if (esUsuario) Olimpos.Dark else Olimpos.Cream
    Row(
        Modifier.fillMaxWidth().alpha(if (atenuado) 0.6f else 1f),
        horizontalArrangement = if (esUsuario) Arrangement.End else Arrangement.Start
    ) {
        Box(
            Modifier
                .widthIn(max = 280.dp)
                .clip(RoundedCornerShape(14.dp))
                .background(if (esUsuario) Olimpos.Gold else Olimpos.Card)
                .let { if (!esUsuario) it.border(1.dp, Olimpos.Line, RoundedCornerShape(14.dp)) else it }
                .padding(horizontal = 13.dp, vertical = 10.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
                // Argos suele escribir con **negrita** y listas con "- " —
                // esto lo interpreta en vez de mostrar los asteriscos
                // sueltos, para que la burbuja no se vea rara.
                m.texto.split("\n").forEach { linea ->
                    val recortada = linea.trimStart()
                    val esBullet = recortada.startsWith("- ") || recortada.startsWith("* ")
                    val contenido = if (esBullet) recortada.removePrefix("- ").removePrefix("* ") else linea
                    Row {
                        if (esBullet) {
                            Text("•  ", fontSize = 13.sp, fontWeight = FontWeight.Black, color = color)
                        }
                        Text(
                            aTextoConNegrita(contenido, color), fontSize = 13.sp,
                            fontWeight = FontWeight.Medium, color = color
                        )
                    }
                }
            }
        }
    }
}

/** Convierte "**palabra**" en negrita real (Compose no interpreta markdown
 *  solo) — Argos, el modelo de lenguaje, escribe así seguido. */
private fun aTextoConNegrita(texto: String, color: androidx.compose.ui.graphics.Color) = buildAnnotatedString {
    val regex = Regex("\\*\\*(.+?)\\*\\*")
    var ultimo = 0
    for (match in regex.findAll(texto)) {
        append(texto.substring(ultimo, match.range.first))
        pushStyle(SpanStyle(fontWeight = FontWeight.Black, color = color))
        append(match.groupValues[1])
        pop()
        ultimo = match.range.last + 1
    }
    append(texto.substring(ultimo))
}

/** Burbuja flotante siempre visible (cualquier pestaña) para abrir el chat
 *  de Argos sin tener que ir hasta Perfil. */
@Composable
fun ArgosBurbujaFlotante(onClick: () -> Unit) {
    Box(
        Modifier
            .size(58.dp)
            .shadow(8.dp, CircleShape)
            .clip(CircleShape)
            .background(Brush.linearGradient(listOf(Olimpos.GoldLight, Olimpos.GoldDark)))
            .border(1.5.dp, Olimpos.Gold, CircleShape)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text("🐕", fontSize = 26.sp)
    }
}
