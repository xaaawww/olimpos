package com.olimpos.gym.ui.screens

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.Remove
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.olimpos.gym.data.PedidoTienda
import com.olimpos.gym.data.Producto
import com.olimpos.gym.data.cancelarPedidoTienda
import com.olimpos.gym.data.cargarPedidosTienda
import com.olimpos.gym.data.cargarProductosTienda
import com.olimpos.gym.data.hacerPedidoTienda
import com.olimpos.gym.data.plata
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private enum class VistaTienda { CATALOGO, DETALLE, CARRITO }

/**
 * Tienda del club: catálogo por etiquetas, detalle del producto, carrito y
 * "Mis pedidos". El pedido se paga y retira en la recepción; mientras no se
 * retira, el socio lo puede cancelar.
 */
@Composable
fun TiendaScreen(onVolver: () -> Unit) {
    val scope = rememberCoroutineScope()
    var productos by remember { mutableStateOf<List<Producto>?>(null) }
    var pedidos by remember { mutableStateOf<List<PedidoTienda>>(emptyList()) }
    var sinConexion by remember { mutableStateOf(false) }
    val carrito = remember { mutableStateMapOf<String, Int>() }
    var vista by remember { mutableStateOf(VistaTienda.CATALOGO) }
    var elegido by remember { mutableStateOf<Producto?>(null) }
    var filtro by remember { mutableStateOf<String?>(null) }
    var aviso by remember { mutableStateOf<Pair<String, Boolean>?>(null) }   // texto, es error
    var enviando by remember { mutableStateOf(false) }

    suspend fun recargar() {
        val p = cargarProductosTienda()
        sinConexion = p == null
        if (p != null) productos = p
        cargarPedidosTienda()?.let { pedidos = it }
    }
    LaunchedEffect(Unit) { recargar() }

    val lista = productos.orEmpty()
    val cantidadCarrito = carrito.values.sum()
    val totalCarrito = carrito.entries.sumOf { (id, n) -> (lista.firstOrNull { it.id == id }?.precio ?: 0.0) * n }

    when (vista) {
        VistaTienda.DETALLE -> elegido?.let { p ->
            DetalleProducto(
                p, enCarrito = carrito[p.id] ?: 0,
                onVolver = { vista = VistaTienda.CATALOGO },
                onAgregar = { n ->
                    carrito[p.id] = n
                    aviso = "Agregado al pedido." to false
                    vista = VistaTienda.CATALOGO
                }
            )
            return
        }
        VistaTienda.CARRITO -> {
            Carrito(
                lista, carrito, totalCarrito, enviando,
                onVolver = { vista = VistaTienda.CATALOGO },
                onConfirmar = {
                    enviando = true
                    scope.launch {
                        hacerPedidoTienda(carrito.toMap())
                            .onSuccess {
                                carrito.clear()
                                aviso = "Pedido #${it.id} hecho. Pagalo y retiralo en la recepción." to false
                                vista = VistaTienda.CATALOGO
                            }
                            .onFailure { aviso = (it.message ?: "No se pudo hacer el pedido.") to true }
                        recargar()
                        enviando = false
                    }
                }
            )
            return
        }
        VistaTienda.CATALOGO -> Unit
    }

    Column(Modifier.fillMaxSize().background(CA.fondo)) {
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            EncabezadoArena("Tienda", "Pedí acá, pagá y retirá en la recepción.", onVolver)
            Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 24.dp)) {
                aviso?.let { (texto, error) -> Aviso(texto, error) }
                if (sinConexion && productos == null) {
                    Text("Sin conexión. Revisá internet para ver la tienda.", fontSize = 13.sp, color = CA.suave)
                }

                val pendientes = pedidos.filter { it.estado == "pendiente" }
                if (pendientes.isNotEmpty()) {
                    SeccionLabel("Para retirar en la recepción")
                    pendientes.forEach { pedido ->
                        TarjetaPedido(pedido) {
                            scope.launch {
                                val error = cancelarPedidoTienda(pedido.id)
                                aviso = (error ?: "Pedido #${pedido.id} cancelado.") to (error != null)
                                recargar()
                            }
                        }
                        Spacer(Modifier.height(10.dp))
                    }
                }

                val etiquetas = lista.flatMap { it.etiquetas }.distinctBy { it.lowercase() }.sortedBy { it.lowercase() }
                if (etiquetas.isNotEmpty()) {
                    Spacer(Modifier.height(6.dp))
                    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        ChipArena("Todo", filtro == null) { filtro = null }
                        etiquetas.forEach { e -> ChipArena(e, filtro.equals(e, true)) { filtro = e } }
                    }
                    Spacer(Modifier.height(14.dp))
                }

                val visibles = lista.filter { p -> filtro == null || p.etiquetas.any { it.equals(filtro, true) } }
                if (productos != null && visibles.isEmpty()) {
                    Text(
                        if (lista.isEmpty()) "Todavía no hay productos en la tienda." else "No hay productos con esa etiqueta.",
                        fontSize = 13.sp, color = CA.suave
                    )
                }
                visibles.chunked(2).forEach { fila ->
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        fila.forEach { p ->
                            TarjetaProducto(p, carrito[p.id] ?: 0, Modifier.weight(1f)) {
                                elegido = p
                                aviso = null
                                vista = VistaTienda.DETALLE
                            }
                        }
                        if (fila.size == 1) Spacer(Modifier.weight(1f))
                    }
                    Spacer(Modifier.height(12.dp))
                }

                val historial = pedidos.filter { it.estado != "pendiente" }.take(5)
                if (historial.isNotEmpty()) {
                    SeccionLabel("Pedidos anteriores")
                    historial.forEach { TarjetaPedido(it, onCancelar = null); Spacer(Modifier.height(10.dp)) }
                }
                Spacer(Modifier.height(if (cantidadCarrito > 0) 8.dp else 60.dp))
            }
        }
        if (cantidadCarrito > 0) {
            Row(
                Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 12.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(CA.amarillo)
                    .clickable { aviso = null; vista = VistaTienda.CARRITO }
                    .padding(horizontal = 18.dp, vertical = 14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Outlined.ShoppingBag, null, tint = CA.tinta, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(10.dp))
                Text("Ver mi pedido · $cantidadCarrito", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = CA.tinta,
                    modifier = Modifier.weight(1f))
                Text(plata(totalCarrito), fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = CA.tinta)
            }
        }
    }
}

@Composable
private fun Aviso(texto: String, error: Boolean) {
    Text(
        texto, fontSize = 12.5.sp, fontWeight = FontWeight.Medium,
        color = if (error) Olimpos.Red else Olimpos.Green,
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 10.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(if (error) Olimpos.Red.copy(alpha = 0.08f) else Olimpos.Green.copy(alpha = 0.1f))
            .padding(12.dp)
    )
}

@Composable
private fun FotoProducto(p: Producto, modifier: Modifier) {
    Box(modifier.clip(RoundedCornerShape(12.dp)).background(CA.amarilloSuave), contentAlignment = Alignment.Center) {
        if (p.imagen != null) {
            AsyncImage(model = p.imagen, contentDescription = p.nombre, contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize())
        } else {
            Icon(Icons.Outlined.ShoppingBag, null, tint = CA.acento, modifier = Modifier.size(34.dp))
        }
    }
}

@Composable
private fun TarjetaProducto(p: Producto, enCarrito: Int, modifier: Modifier, onClick: () -> Unit) {
    TarjetaLisa(modifier.clickable(onClick = onClick), padding = 10.dp) {
        Box {
            FotoProducto(p, Modifier.fillMaxWidth().aspectRatio(1f))
            if (enCarrito > 0) {
                Box(
                    Modifier.align(Alignment.TopEnd).padding(6.dp).size(24.dp).clip(CircleShape).background(CA.amarillo),
                    contentAlignment = Alignment.Center
                ) { Text("$enCarrito", fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = CA.tinta) }
            }
        }
        Spacer(Modifier.height(9.dp))
        Text(p.nombre, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, maxLines = 2,
            overflow = TextOverflow.Ellipsis, lineHeight = 17.sp, modifier = Modifier.height(34.dp))
        Spacer(Modifier.height(4.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(plata(p.precio), fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.weight(1f))
            if (p.stock == 0) Text("Sin stock", fontSize = 11.sp, color = Olimpos.Red)
        }
    }
}

@Composable
private fun DetalleProducto(p: Producto, enCarrito: Int, onVolver: () -> Unit, onAgregar: (Int) -> Unit) {
    var cantidad by remember { mutableStateOf(enCarrito.coerceAtLeast(1).coerceAtMost(p.stock.coerceAtLeast(1))) }
    val maximo = minOf(p.stock, 20)
    Column(Modifier.fillMaxSize().background(CA.fondo).verticalScroll(rememberScrollState())) {
        EncabezadoArena(p.nombre, p.etiquetas.joinToString(" · "), onVolver)
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 30.dp)) {
            FotoProducto(p, Modifier.fillMaxWidth().aspectRatio(1.2f))
            Spacer(Modifier.height(16.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(plata(p.precio), fontSize = 22.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.weight(1f))
                Text(
                    when { p.stock == 0 -> "Sin stock"; p.stock <= 5 -> "Quedan ${p.stock}"; else -> "En stock" },
                    fontSize = 12.5.sp, fontWeight = FontWeight.Medium,
                    color = if (p.stock == 0) Olimpos.Red else if (p.stock <= 5) Olimpos.GoldDark else Olimpos.Green
                )
            }
            if (p.etiquetas.isNotEmpty()) {
                Spacer(Modifier.height(10.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) { p.etiquetas.forEach { ChipSuave(it) } }
            }
            if (p.descripcion.isNotBlank()) {
                Spacer(Modifier.height(14.dp))
                Text(p.descripcion, fontSize = 13.5.sp, color = CA.suave, lineHeight = 20.sp)
            }
            Spacer(Modifier.height(22.dp))
            if (p.stock > 0) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Cantidad", fontSize = 13.5.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.weight(1f))
                    Contador(cantidad, 1, maximo) { cantidad = it }
                }
                Spacer(Modifier.height(16.dp))
                BotonPrincipal("Agregar al pedido · ${plata(p.precio * cantidad)}") { onAgregar(cantidad) }
                Spacer(Modifier.height(10.dp))
                Text("Lo pagás y lo retirás en la recepción.", fontSize = 11.5.sp, color = CA.suave)
            } else {
                Text("Por ahora no hay stock. Consultá en la recepción cuándo vuelve a entrar.", fontSize = 12.5.sp, color = CA.suave)
            }
        }
    }
}

@Composable
private fun Contador(valor: Int, minimo: Int, maximo: Int, onCambio: (Int) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        BotonRedondo(Icons.Outlined.Remove, valor > minimo) { onCambio(valor - 1) }
        Text("$valor", fontSize = 15.sp, fontWeight = FontWeight.SemiBold, color = CA.texto,
            modifier = Modifier.width(36.dp), textAlign = androidx.compose.ui.text.style.TextAlign.Center)
        BotonRedondo(Icons.Outlined.Add, valor < maximo) { onCambio(valor + 1) }
    }
}

@Composable
private fun BotonRedondo(icono: androidx.compose.ui.graphics.vector.ImageVector, habilitado: Boolean, onClick: () -> Unit) {
    Box(
        Modifier.size(32.dp).clip(CircleShape).border(1.dp, CA.borde, CircleShape)
            .clickable(enabled = habilitado, onClick = onClick),
        contentAlignment = Alignment.Center
    ) { Icon(icono, null, tint = if (habilitado) CA.texto else CA.suave.copy(alpha = 0.4f), modifier = Modifier.size(16.dp)) }
}

@Composable
private fun Carrito(
    productos: List<Producto>,
    carrito: MutableMap<String, Int>,
    total: Double,
    enviando: Boolean,
    onVolver: () -> Unit,
    onConfirmar: () -> Unit
) {
    BackHandler(onBack = onVolver)
    Column(Modifier.fillMaxSize().background(CA.fondo).verticalScroll(rememberScrollState())) {
        EncabezadoArena("Mi pedido", "Revisalo antes de confirmar", onVolver)
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 30.dp).navigationBarsPadding()) {
            TarjetaLisa(Modifier.fillMaxWidth(), padding = 0.dp) {
                carrito.entries.toList().forEachIndexed { i, (id, n) ->
                    val p = productos.firstOrNull { it.id == id } ?: return@forEachIndexed
                    if (i > 0) androidx.compose.material3.HorizontalDivider(color = CA.borde)
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        FotoProducto(p, Modifier.size(52.dp))
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text(p.nombre, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, maxLines = 2,
                                overflow = TextOverflow.Ellipsis)
                            Text(plata(p.precio * n), fontSize = 12.5.sp, color = CA.suave)
                        }
                        Contador(n, 0, minOf(p.stock, 20)) { nuevo -> if (nuevo == 0) carrito.remove(id) else carrito[id] = nuevo }
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
            Row {
                Text("Total a pagar en la recepción", fontSize = 13.5.sp, color = CA.suave, modifier = Modifier.weight(1f))
                Text(plata(total), fontSize = 17.sp, fontWeight = FontWeight.SemiBold, color = CA.texto)
            }
            Spacer(Modifier.height(18.dp))
            BotonPrincipal(if (enviando) "Enviando…" else "Confirmar pedido", habilitado = !enviando && carrito.isNotEmpty(),
                onClick = onConfirmar)
            Spacer(Modifier.height(10.dp))
            Text(
                "Al confirmar, los productos quedan reservados para vos. Los pagás y los retirás en la recepción; " +
                    "si cambiás de idea, podés cancelar el pedido desde la Tienda.",
                fontSize = 11.5.sp, color = CA.suave, lineHeight = 17.sp
            )
        }
    }
}

@Composable
private fun TarjetaPedido(pedido: PedidoTienda, onCancelar: (() -> Unit)?) {
    TarjetaLisa(Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Pedido #${pedido.id}", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.weight(1f))
            ChipSuave(
                when (pedido.estado) { "pendiente" -> "Listo para retirar"; "entregado" -> "Entregado"; else -> "Cancelado" },
                when (pedido.estado) { "pendiente" -> Pastel.AMARILLO; "entregado" -> Pastel.VERDE; else -> Pastel.NARANJA }
            )
        }
        Text(SimpleDateFormat("dd/MM HH:mm", Locale("es", "AR")).format(Date(pedido.fechaMs)), fontSize = 11.5.sp, color = CA.suave)
        Spacer(Modifier.height(8.dp))
        pedido.items.forEach {
            Text("${it.cantidad} × ${it.nombre}", fontSize = 12.5.sp, color = CA.texto, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        Spacer(Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(plata(pedido.total), fontSize = 14.5.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.weight(1f))
            if (onCancelar != null) {
                Text("Cancelar", fontSize = 12.5.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Red,
                    modifier = Modifier.clip(RoundedCornerShape(8.dp)).clickable(onClick = onCancelar).padding(6.dp))
            }
        }
    }
}
