package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.eliminarCompanero
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

/** Lista de compañeros de entrenamiento agregados desde Clasificación (ver
 *  DetallePerfilSocio) — para los logros "Mentor" y "Espíritu de equipo".
 *  Sin sistema de solicitudes: agregar a alguien es unidireccional, no
 *  hace falta que el otro socio acepte nada (mismo dato que ya es público
 *  en Clasificación). */
@Composable
fun CompanerosScreen(onVolver: () -> Unit) {
    val scope = rememberCoroutineScope()
    val companeros = DatosRemotos.companeros ?: emptyList()
    val dias = DatosRemotos.diasEntrenadosConCompaneros

    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver("Mis compañeros", "${companeros.size} agregados", onVolver)

        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
            TarjetaOro(Modifier.fillMaxWidth().padding(bottom = 16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconoCuadrado("👥")
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text("Días entrenados junto a un compañero", fontWeight = FontWeight.ExtraBold, fontSize = 13.sp, color = Olimpos.Cream)
                        Text(
                            "$dias de 5 para el logro \"Espíritu de equipo\" — cuenta un día si vos y alguno de tus compañeros cargaron una marca ese mismo día.",
                            fontSize = 11.sp, color = Olimpos.Muted
                        )
                    }
                }
            }

            SeccionLabel("Agregados")
            if (companeros.isEmpty()) {
                Text(
                    "Todavía no agregaste a nadie. Buscá a un socio en Clasificación y agregalo desde su perfil.",
                    fontSize = 12.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 12.dp)
                )
            } else {
                companeros.forEach { c ->
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
                        IconoCuadrado("🤝")
                        Spacer(Modifier.width(12.dp))
                        Text(c.nombre, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = Olimpos.Cream, modifier = Modifier.weight(1f))
                        Text(
                            "Quitar", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Olimpos.Red,
                            modifier = Modifier
                                .clip(RoundedCornerShape(10.dp))
                                .clickable {
                                    scope.launch {
                                        eliminarCompanero(c.socioId)
                                        DatosRemotos.recargarCompaneros()
                                    }
                                }
                                .padding(6.dp)
                        )
                    }
                }
            }
        }
    }
}
