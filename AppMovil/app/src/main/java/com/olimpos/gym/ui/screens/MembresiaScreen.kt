package com.olimpos.gym.ui.screens

import android.content.Intent
import android.net.Uri
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.PLANES_MEMBRESIA
import com.olimpos.gym.data.PlanMembresia
import com.olimpos.gym.data.crearPreferenciaDePago
import com.olimpos.gym.data.fechaLegible
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

@Composable
fun MembresiaScreen(onVolver: () -> Unit) {
    // Ya no se auto-asigna tocando un botón, ni queda como un "pedido" que
    // un empleado tiene que ir a activar a mano: el socio paga de verdad
    // (Mercado Pago, modo prueba — ver PagosRepository.kt) y la membresía
    // se activa sola cuando el pago se confirma.
    val membresia = DatosRemotos.membresia
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var aviso by remember { mutableStateOf<String?>(null) }
    var pagando by remember { mutableStateOf<String?>(null) }  // nombre del plan que se está por pagar
    var mostrarCancelar by remember { mutableStateOf(false) }

    fun pagarPlan(plan: String) {
        if (pagando != null) return
        pagando = plan
        aviso = null
        scope.launch {
            try {
                val url = crearPreferenciaDePago(plan)
                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                aviso = "Te llevamos a Mercado Pago para pagar el plan $plan. Cuando el pago se apruebe, la membresía se activa sola — volvé acá y actualizá."
            } catch (e: Exception) {
                aviso = e.message ?: "No se pudo iniciar el pago. Probá de nuevo."
            } finally {
                pagando = null
            }
        }
    }

    // LazyColumn en vez de Column+verticalScroll: planes e historial se van
    // sumando, y así solo se arma lo que está en pantalla.
    LazyColumn(Modifier.fillMaxSize()) {
        item(key = "encabezado") {
            EncabezadoVolver("Mi membresía", "Plan, pagos y vencimientos", onVolver)
        }

        item(key = "plan-actual") {
            Column(Modifier.padding(horizontal = 20.dp)) {
                TarjetaOro(Modifier.fillMaxWidth()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(
                                membresia?.let { "Plan ${it.plan}" } ?: "Sin plan asignado",
                                fontWeight = FontWeight.Black, fontSize = 18.sp, color = Olimpos.Cream
                            )
                            Text(
                                membresia?.let { "Socio desde ${fechaLegible(it.fechaInicioMs)}" }
                                    ?: "Elegí un plan más abajo para activarlo",
                                fontSize = 12.sp, color = Olimpos.Muted
                            )
                        }
                        if (membresia != null) ChipOro("Vigente")
                    }
                }
                BotonSecundario("¿Ya pagaste? Actualizar") {
                    scope.launch {
                        DatosRemotos.recargarMembresia()
                        DatosRemotos.recargarHistorialPagos()
                        aviso = null
                    }
                }
                SeccionLabel("Planes disponibles")
                Text(
                    "Elegí uno para pagarlo con Mercado Pago (modo prueba) — se activa solo apenas se confirma el pago.",
                    fontSize = 11.5.sp, color = Olimpos.Muted, modifier = Modifier.padding(bottom = 4.dp)
                )
            }
        }

        items(PLANES_MEMBRESIA, key = { it.nombre }) { p ->
            TarjetaPlan(
                plan = p,
                activo = p.nombre == membresia?.plan,
                pagando = pagando == p.nombre,
                modifier = Modifier.padding(horizontal = 20.dp)
            ) {
                pagarPlan(p.nombre)
            }
        }

        item(key = "label-historial") {
            Column(Modifier.padding(horizontal = 20.dp)) {
                SeccionLabel("Historial de pagos")
                if (DatosRemotos.historialPagos.isEmpty()) {
                    Text("Todavía no hay pagos registrados.", fontSize = 12.sp, color = Olimpos.Muted)
                }
            }
        }

        items(DatosRemotos.historialPagos, key = { it.periodo }) { h ->
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
                        "Se canceló la solicitud de baja. Tu membresía sigue activa.",
                        fontSize = 12.sp, color = Olimpos.Muted
                    )
                }
            }
        }
    }
}

@Composable
private fun TarjetaPlan(
    plan: PlanMembresia,
    activo: Boolean,
    pagando: Boolean = false,
    modifier: Modifier = Modifier,
    onElegir: () -> Unit
) {
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
            BotonSecundario(if (pagando) "Abriendo Mercado Pago…" else "Pagar este plan") {
                if (!pagando) onElegir()
            }
        }
    }
}
