package com.olimpos.gym.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.ObjetivoCompetencia
import com.olimpos.gym.data.PedidoTienda
import com.olimpos.gym.data.cargarPedidosTienda
import com.olimpos.gym.data.plata
import com.olimpos.gym.ui.theme.Olimpos

/** Qué se ve en la pestaña Nutrición: el menú con los dos accesos, o una de las secciones. */
enum class NutricionVista { MENU, DIETA, TIENDA }

/**
 * Pestaña Nutrición: dos tarjetas como en la Arena, "Mi dieta" (el plan del
 * nutricionista y el registro de comidas) y "Tienda" (suplementos y demás).
 * [vista] la maneja MainActivity para que los accesos rápidos de Inicio
 * puedan abrir directo una de las dos.
 */
@Composable
fun NutricionTab(
    vista: NutricionVista,
    onVista: (NutricionVista) -> Unit,
    objetivo: ObjetivoCompetencia?,
    onOcultarBurbujaArgos: (Boolean) -> Unit
) {
    when (vista) {
        NutricionVista.DIETA -> DietaScreen(objetivo, onOcultarBurbujaArgos, onVolver = { onVista(NutricionVista.MENU) })
        NutricionVista.TIENDA -> TiendaScreen(onVolver = { onVista(NutricionVista.MENU) })
        NutricionVista.MENU -> MenuNutricion(objetivo, onVista)
    }
}

@Composable
private fun MenuNutricion(objetivo: ObjetivoCompetencia?, onVista: (NutricionVista) -> Unit) {
    var pendientes by remember { mutableStateOf<List<PedidoTienda>>(emptyList()) }
    LaunchedEffect(Unit) { cargarPedidosTienda()?.let { l -> pendientes = l.filter { it.estado == "pendiente" } } }
    val platosDieta = DatosRemotos.dietaAsignada?.platoIds?.size ?: 0

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .statusBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(top = 14.dp, bottom = 26.dp)
    ) {
        if (objetivo != null) {
            BadgeObjetivo(objetivo)
            Spacer(Modifier.height(12.dp))
        }
        Eyebrow("Nutrición")
        Text("Comé bien y recargá", fontSize = 22.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
        Text("Tu plan de comidas y la NutriStore", fontSize = 13.sp, color = Olimpos.Muted)

        Spacer(Modifier.height(18.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            TarjetaNutricion("🥗", "Mi dieta",
                if (platosDieta > 0) "Tu plan y tus comidas" else "Registrá tus comidas",
                Modifier.weight(1f)) { onVista(NutricionVista.DIETA) }
            TarjetaNutricion("🛍️", "NutriStore", "Suplementos y más", Modifier.weight(1f)) { onVista(NutricionVista.TIENDA) }
        }

        if (pendientes.isNotEmpty()) {
            Spacer(Modifier.height(18.dp))
            SeccionLabel("Para retirar")
            TarjetaOro(Modifier.fillMaxWidth().clickable { onVista(NutricionVista.TIENDA) }) {
                Text(
                    if (pendientes.size == 1) "Tenés el pedido #${pendientes[0].id} listo para retirar"
                    else "Tenés ${pendientes.size} pedidos listos para retirar",
                    fontSize = 13.5.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream
                )
                Text("Pagalo en la recepción · ${plata(pendientes.sumOf { it.total })}", fontSize = 11.5.sp, color = Olimpos.Muted)
            }
        }
    }
}

@Composable
private fun TarjetaNutricion(icono: String, titulo: String, sub: String, modifier: Modifier, onClick: () -> Unit) {
    // Mismo alto y forma que las tarjetas de la Arena
    TarjetaOro(modifier.height(118.dp).clickable(onClick = onClick)) {
        IconoCuadrado(icono)
        Spacer(Modifier.weight(1f))
        Text(titulo, fontWeight = FontWeight.SemiBold, fontSize = 13.5.sp, color = Olimpos.Cream, maxLines = 1, overflow = TextOverflow.Ellipsis)
        Text(sub, fontSize = 11.sp, color = Olimpos.Muted, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}
