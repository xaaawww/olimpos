package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.HISTORIAL_PAGOS
import com.olimpos.gym.data.METODOS_PAGO
import com.olimpos.gym.data.PLANES_MEMBRESIA
import com.olimpos.gym.data.PlanMembresia
import com.olimpos.gym.ui.theme.Olimpos

@Composable
fun MembresiaScreen(onVolver: () -> Unit) {
    var planActual by remember { mutableStateOf("Oro") }
    var aviso by remember { mutableStateOf<String?>(null) }
    var mostrarCancelar by remember { mutableStateOf(false) }

    // LazyColumn en vez de Column+verticalScroll: planes, métodos de pago e
    // historial se van sumando, y así solo se arma lo que está en pantalla.
    LazyColumn(Modifier.fillMaxSize()) {
        item(key = "encabezado") {
            EncabezadoVolver("Mi membresía", "Plan, pagos y vencimientos", onVolver)
        }

        item(key = "plan-actual") {
            Column(Modifier.padding(horizontal = 20.dp)) {
                TarjetaOro(Modifier.fillMaxWidth()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("Plan $planActual", fontWeight = FontWeight.Black, fontSize = 18.sp, color = Olimpos.Cream)
                            Text("Próximo vencimiento: 05/10/2026", fontSize = 12.sp, color = Olimpos.Muted)
                        }
                        ChipOro("Vigente")
                    }
                }
                SeccionLabel("Planes disponibles")
            }
        }

        items(PLANES_MEMBRESIA, key = { it.nombre }) { p ->
            TarjetaPlan(
                plan = p,
                activo = p.nombre == planActual,
                modifier = Modifier.padding(horizontal = 20.dp)
            ) {
                if (p.nombre != planActual) {
                    planActual = p.nombre
                    aviso = "Cambiaste al plan ${p.nombre}. Se verá reflejado en tu próxima cuota."
                }
            }
        }

        item(key = "label-pagos") {
            Column(Modifier.padding(horizontal = 20.dp)) { SeccionLabel("Métodos de pago") }
        }

        items(METODOS_PAGO, key = { "${it.tipo}-${it.detalle}" }) { m ->
            Row(
                Modifier
                    .padding(horizontal = 20.dp)
                    .fillMaxWidth()
                    .padding(bottom = 9.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(Olimpos.Card)
                    .border(1.dp, Olimpos.Line, RoundedCornerShape(16.dp))
                    .padding(horizontal = 15.dp, vertical = 13.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(m.emoji, fontSize = 20.sp)
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text(m.tipo, fontWeight = FontWeight.ExtraBold, fontSize = 13.5.sp, color = Olimpos.Cream)
                    Text(m.detalle, fontSize = 11.5.sp, color = Olimpos.Muted)
                }
            }
        }

        item(key = "acciones") {
            Column(Modifier.padding(horizontal = 20.dp)) {
                BotonSecundario("+ Agregar método de pago") {
                    aviso = "Método de pago agregado correctamente."
                }
                Spacer(Modifier.height(6.dp))
                SeccionLabel("Pagar cuota de este mes")
                BotonPrincipal("Pagar $28.000 ahora") {
                    aviso = "Pago procesado ✓ Comprobante enviado a tu email."
                }
                SeccionLabel("Historial de pagos")
            }
        }

        items(HISTORIAL_PAGOS, key = { it.periodo }) { h ->
            Row(
                Modifier
                    .padding(horizontal = 20.dp)
                    .fillMaxWidth()
                    .padding(bottom = 9.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(Olimpos.Card)
                    .padding(horizontal = 15.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(Modifier.weight(1f)) {
                    Text(h.periodo, fontWeight = FontWeight.Bold, fontSize = 12.5.sp, color = Olimpos.Cream)
                    Text(h.monto, fontSize = 11.5.sp, color = Olimpos.Muted)
                }
                ChipOro(h.estado)
            }
        }

        item(key = "pie") {
            Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 26.dp)) {
                aviso?.let {
                    Spacer(Modifier.height(4.dp))
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(14.dp))
                            .background(Olimpos.GoldSoft)
                            .border(1.dp, Olimpos.Gold.copy(alpha = 0.35f), RoundedCornerShape(14.dp))
                            .padding(13.dp)
                    ) {
                        Text(it, fontSize = 12.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.GoldLight)
                    }
                }

                Spacer(Modifier.height(20.dp))
                if (!mostrarCancelar) {
                    Text(
                        "Cancelar membresía",
                        fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Olimpos.Red,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp)
                            .clickable(
                                interactionSource = remember { androidx.compose.foundation.interaction.MutableInteractionSource() },
                                indication = null
                            ) { mostrarCancelar = true }
                    )
                } else {
                    Text(
                        "Se canceló la solicitud de baja. Tu membresía sigue activa hasta 05/10/2026.",
                        fontSize = 12.sp, color = Olimpos.Muted
                    )
                }
            }
        }
    }
}

@Composable
private fun TarjetaPlan(plan: PlanMembresia, activo: Boolean, modifier: Modifier = Modifier, onElegir: () -> Unit) {
    TarjetaOro(modifier.fillMaxWidth().padding(bottom = 10.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(plan.nombre, fontWeight = FontWeight.Black, fontSize = 15.sp, color = Olimpos.Cream)
                Text(plan.precio, fontSize = 12.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.GoldLight)
            }
            if (plan.destacado) ChipOro("Popular")
        }
        Spacer(Modifier.height(10.dp))
        plan.beneficios.forEach { b ->
            Row(Modifier.padding(bottom = 4.dp)) {
                Text("✓ ", fontSize = 12.sp, color = Olimpos.Gold, fontWeight = FontWeight.Black)
                Text(b, fontSize = 12.sp, color = Olimpos.Muted)
            }
        }
        Spacer(Modifier.height(10.dp))
        if (activo) {
            ChipOro("Plan actual")
        } else {
            BotonSecundario("Elegir este plan") { onElegir() }
        }
    }
}
