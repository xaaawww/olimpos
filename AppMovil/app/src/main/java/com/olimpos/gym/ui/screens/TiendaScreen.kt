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
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.Backpack
import androidx.compose.material.icons.outlined.Blender
import androidx.compose.material.icons.outlined.Bolt
import androidx.compose.material.icons.outlined.Checkroom
import androidx.compose.material.icons.outlined.Cookie
import androidx.compose.material.icons.outlined.DeleteOutline
import androidx.compose.material.icons.outlined.FitnessCenter
import androidx.compose.material.icons.outlined.LocalDrink
import androidx.compose.material.icons.outlined.LocalFireDepartment
import androidx.compose.material.icons.outlined.Medication
import androidx.compose.material.icons.outlined.Remove
import androidx.compose.material.icons.outlined.Science
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material.icons.outlined.ShoppingCart
import androidx.compose.material.icons.outlined.Storefront
import androidx.compose.material3.HorizontalDivider
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
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
import java.text.Normalizer
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private enum class VistaTienda { INICIO, CATEGORIA, DETALLE, CARRITO }

/** Más o menos unidades que esto = "Stock bajo" (igual que el sistema de empleados). */
private const val STOCK_BAJO = 5

private val VerdeFondo = Color(0xFFDCFCE7)
private val VerdeTexto = Color(0xFF16A34A)
private val NaranjaFondo = Color(0xFFFEF3C7)
private val NaranjaTexto = Color(0xFFD97706)
private val RojoFondo = Color(0xFFFEE2E2)
private val RojoTexto = Color(0xFFDC2626)

private fun clave(t: String) = Normalizer.normalize(t.lowercase().trim(), Normalizer.Form.NFD).replace(Regex("\\p{Mn}"), "")

/** Ícono de línea para cada categoría (las etiquetas que carga el dueño). */
private fun iconoCategoria(nombre: String): ImageVector = when (clave(nombre)) {
    "proteinas", "proteina" -> Icons.Outlined.FitnessCenter
    "creatina" -> Icons.Outlined.Bolt
    "pre-entreno", "preentreno" -> Icons.Outlined.LocalFireDepartment
    "aminoacidos", "bcaa" -> Icons.Outlined.Science
    "vitaminas" -> Icons.Outlined.Medication
    "snacks", "barras" -> Icons.Outlined.Cookie
    "bebidas" -> Icons.Outlined.LocalDrink
    "accesorios" -> Icons.Outlined.Backpack
    "shakers" -> Icons.Outlined.Blender
    "indumentaria", "ropa" -> Icons.Outlined.Checkroom
    else -> Icons.Outlined.ShoppingBag
}

/**
 * NutriStore, la tienda del club: inicio (buscador, banner y categorías),
 * productos por categoría, detalle, carrito y los pedidos del socio. El pedido
 * se paga y retira en la recepción; mientras no se retira, se puede cancelar.
 */
@Composable
fun TiendaScreen(onVolver: () -> Unit) {
    val scope = rememberCoroutineScope()
    var productos by remember { mutableStateOf<List<Producto>?>(null) }
    var pedidos by remember { mutableStateOf<List<PedidoTienda>>(emptyList()) }
    var sinConexion by remember { mutableStateOf(false) }
    val carrito = remember { mutableStateMapOf<String, Int>() }
    var vista by remember { mutableStateOf(VistaTienda.INICIO) }
    var categoria by remember { mutableStateOf<String?>(null) }   // null = todos los productos
    var elegido by remember { mutableStateOf<Producto?>(null) }
    var desde by remember { mutableStateOf(VistaTienda.INICIO) }   // a dónde vuelve el detalle
    var busqueda by remember { mutableStateOf("") }
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
    val categorias = lista.flatMap { it.etiquetas.take(1) }.distinctBy(::clave).sortedBy(::clave)
    val enCarrito = carrito.values.sum()
    val totalCarrito = carrito.entries.sumOf { (id, n) -> (lista.firstOrNull { it.id == id }?.precio ?: 0.0) * n }
    val abrirProducto: (Producto) -> Unit = { p -> elegido = p; desde = vista; aviso = null; vista = VistaTienda.DETALLE }
    val abrirCarrito = { aviso = null; vista = VistaTienda.CARRITO }
    val iconoCarrito: @Composable () -> Unit = { BotonCarrito(enCarrito, abrirCarrito) }

    when (vista) {
        VistaTienda.DETALLE -> {
            val p = elegido ?: return
            DetalleProducto(
                p, enCarrito = carrito[p.id] ?: 0, carrito = iconoCarrito,
                onVolver = { vista = desde },
                onAgregar = { n ->
                    carrito[p.id] = n
                    aviso = "Agregado al carrito." to false
                    vista = desde
                }
            )
        }
        VistaTienda.CARRITO -> Carrito(
            lista, carrito, totalCarrito, enviando,
            onVolver = { vista = VistaTienda.INICIO },
            onConfirmar = {
                enviando = true
                scope.launch {
                    hacerPedidoTienda(carrito.toMap())
                        .onSuccess {
                            carrito.clear()
                            aviso = "Pedido #${it.id} confirmado. Pagalo y retiralo en la recepción." to false
                            vista = VistaTienda.INICIO
                        }
                        .onFailure { aviso = (it.message ?: "No se pudo hacer el pedido.") to true }
                    recargar()
                    enviando = false
                }
            }
        )
        VistaTienda.CATEGORIA -> Categoria(
            lista, categorias, categoria, carrito,
            onCategoria = { categoria = it },
            onProducto = abrirProducto,
            carritoIcono = iconoCarrito,
            onVolver = { vista = VistaTienda.INICIO }
        )
        VistaTienda.INICIO -> InicioTienda(
            productos = productos, sinConexion = sinConexion, categorias = categorias, pedidos = pedidos,
            carrito = carrito, busqueda = busqueda, onBusqueda = { busqueda = it }, aviso = aviso,
            carritoIcono = iconoCarrito, onVolver = onVolver, onProducto = abrirProducto,
            onCategoria = { categoria = it; aviso = null; vista = VistaTienda.CATEGORIA },
            onCancelarPedido = { pedido ->
                scope.launch {
                    val error = cancelarPedidoTienda(pedido.id)
                    aviso = (error ?: "Pedido #${pedido.id} cancelado.") to (error != null)
                    recargar()
                }
            }
        )
    }
}

/* ═══════════════════════ INICIO DE LA TIENDA ═══════════════════════ */

@Composable
private fun InicioTienda(
    productos: List<Producto>?,
    sinConexion: Boolean,
    categorias: List<String>,
    pedidos: List<PedidoTienda>,
    carrito: Map<String, Int>,
    busqueda: String,
    onBusqueda: (String) -> Unit,
    aviso: Pair<String, Boolean>?,
    carritoIcono: @Composable () -> Unit,
    onVolver: () -> Unit,
    onProducto: (Producto) -> Unit,
    onCategoria: (String?) -> Unit,
    onCancelarPedido: (PedidoTienda) -> Unit
) {
    val lista = productos.orEmpty()
    Column(Modifier.fillMaxSize().background(CA.fondo).verticalScroll(rememberScrollState())) {
        EncabezadoArena("NutriStore", "Pedí acá, pagá y retirá en la recepción.", onVolver, derecha = carritoIcono)
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp)) {
            CampoBusqueda(busqueda, onBusqueda, "Buscar productos…")
            Spacer(Modifier.height(14.dp))
            aviso?.let { (texto, error) -> Aviso(texto, error) }
            if (sinConexion && productos == null) {
                Text("Sin conexión. Revisá internet para ver la NutriStore.", fontSize = 13.sp, color = CA.suave)
            }

            val q = clave(busqueda)
            if (q.isNotEmpty()) {
                val encontrados = lista.filter { p -> clave(p.nombre).contains(q) || p.etiquetas.any { clave(it).contains(q) } }
                SeccionLabel("Resultados (${encontrados.size})")
                if (encontrados.isEmpty()) Text("No encontramos productos con \"$busqueda\".", fontSize = 13.sp, color = CA.suave)
                GrillaProductos(encontrados, carrito, onProducto)
                return@Column
            }

            Banner(lista.firstOrNull { it.imagen != null && it.stock > 0 }) { onCategoria(null) }

            val pendientes = pedidos.filter { it.estado == "pendiente" }
            if (pendientes.isNotEmpty()) {
                SeccionLabel("Para retirar en la recepción")
                pendientes.forEach { TarjetaPedido(it) { onCancelarPedido(it) }; Spacer(Modifier.height(10.dp)) }
            }

            if (categorias.isNotEmpty()) {
                Row(Modifier.padding(top = 22.dp, bottom = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text("Categorías", fontSize = 15.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.weight(1f))
                    Text("Ver todo ›", fontSize = 12.sp, color = CA.suave, modifier = Modifier.clickable { onCategoria(null) })
                }
                categorias.chunked(3).forEach { fila ->
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        fila.forEach { c -> TarjetaCategoria(c, Modifier.weight(1f)) { onCategoria(c) } }
                        repeat(3 - fila.size) { Spacer(Modifier.weight(1f)) }
                    }
                    Spacer(Modifier.height(12.dp))
                }
            }

            if (lista.isNotEmpty()) {
                Row(Modifier.padding(top = 10.dp, bottom = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text("Recomendados", fontSize = 15.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.weight(1f))
                    Text("Ver todo ›", fontSize = 12.sp, color = CA.suave, modifier = Modifier.clickable { onCategoria(null) })
                }
                GrillaProductos(lista.filter { it.stock > 0 }.take(4), carrito, onProducto)
            } else if (productos != null) {
                Text("Todavía no hay productos en la NutriStore.", fontSize = 13.sp, color = CA.suave)
            }

            val historial = pedidos.filter { it.estado != "pendiente" }.take(5)
            if (historial.isNotEmpty()) {
                SeccionLabel("Mis pedidos anteriores")
                historial.forEach { TarjetaPedido(it, onCancelar = null); Spacer(Modifier.height(10.dp)) }
            }
        }
    }
}

@Composable
private fun Banner(destacado: Producto?, onVer: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .height(150.dp)
            .clip(RoundedCornerShape(18.dp))
            .background(Brush.linearGradient(listOf(Color(0xFF2A2310), Color(0xFF6B5418), Color(0xFFC9A227))))
            .padding(start = 18.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.weight(1f)) {
            Text("Recargá tu\nentrenamiento", fontSize = 19.sp, lineHeight = 23.sp, fontWeight = FontWeight.SemiBold, color = Color.White)
            Spacer(Modifier.height(4.dp))
            Text("Suplementos, snacks y accesorios", fontSize = 11.5.sp, color = Color.White.copy(alpha = 0.78f))
            Spacer(Modifier.height(12.dp))
            Box(
                Modifier.clip(RoundedCornerShape(20.dp)).background(Olimpos.Gold).clickable(onClick = onVer)
                    .padding(horizontal = 14.dp, vertical = 7.dp)
            ) { Text("Ver productos", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = CA.tinta) }
        }
        if (destacado?.imagen != null) {
            AsyncImage(
                model = destacado.imagen, contentDescription = destacado.nombre, contentScale = ContentScale.Crop,
                modifier = Modifier.size(150.dp).clip(RoundedCornerShape(topEnd = 18.dp, bottomEnd = 18.dp))
            )
        }
    }
}

@Composable
private fun TarjetaCategoria(nombre: String, modifier: Modifier, onClick: () -> Unit) {
    Column(
        modifier.clip(RoundedCornerShape(14.dp)).clickable(onClick = onClick).padding(vertical = 6.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(Modifier.size(58.dp).clip(RoundedCornerShape(18.dp)).background(CA.amarilloSuave), contentAlignment = Alignment.Center) {
            Icon(iconoCategoria(nombre), null, tint = CA.acento, modifier = Modifier.size(26.dp))
        }
        Spacer(Modifier.height(6.dp))
        Text(nombre, fontSize = 11.5.sp, color = CA.texto, maxLines = 1, overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Center)
    }
}

@Composable
private fun BotonCarrito(cantidad: Int, onClick: () -> Unit) {
    Box(Modifier.size(38.dp).clip(CircleShape).clickable(onClick = onClick), contentAlignment = Alignment.Center) {
        Icon(Icons.Outlined.ShoppingCart, "Carrito", tint = CA.texto, modifier = Modifier.size(22.dp))
        if (cantidad > 0) {
            Box(
                Modifier.align(Alignment.TopEnd).offset(x = (-2).dp, y = 2.dp).size(17.dp).clip(CircleShape).background(Olimpos.Gold),
                contentAlignment = Alignment.Center
            ) { Text("$cantidad", fontSize = 9.5.sp, fontWeight = FontWeight.Bold, color = CA.tinta) }
        }
    }
}

/* ═══════════════════════ CATEGORÍA (grilla) ═══════════════════════ */

@Composable
private fun Categoria(
    productos: List<Producto>,
    categorias: List<String>,
    elegida: String?,
    carrito: Map<String, Int>,
    onCategoria: (String?) -> Unit,
    onProducto: (Producto) -> Unit,
    carritoIcono: @Composable () -> Unit,
    onVolver: () -> Unit
) {
    val visibles = productos.filter { p -> elegida == null || p.etiquetas.any { clave(it) == clave(elegida) } }
    Column(Modifier.fillMaxSize().background(CA.fondo).verticalScroll(rememberScrollState())) {
        EncabezadoArena(elegida ?: "Todos los productos", "${visibles.size} productos", onVolver, derecha = carritoIcono)
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp)) {
            Row(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(CA.tarjeta).border(1.dp, CA.borde, RoundedCornerShape(14.dp))
                    .horizontalScroll(rememberScrollState()).padding(4.dp),
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                PildoraCategoria("Todo", elegida == null) { onCategoria(null) }
                categorias.forEach { c -> PildoraCategoria(c, elegida != null && clave(c) == clave(elegida)) { onCategoria(c) } }
            }
            Spacer(Modifier.height(16.dp))
            if (visibles.isEmpty()) Text("No hay productos en esta categoría.", fontSize = 13.sp, color = CA.suave)
            GrillaProductos(visibles, carrito, onProducto)
        }
    }
}

@Composable
private fun PildoraCategoria(texto: String, activa: Boolean, onClick: () -> Unit) {
    Box(
        Modifier.clip(RoundedCornerShape(10.dp)).background(if (activa) CA.amarillo else Color.Transparent)
            .clickable(onClick = onClick).padding(horizontal = 16.dp, vertical = 9.dp)
    ) {
        Text(texto, fontSize = 12.5.sp, fontWeight = if (activa) FontWeight.SemiBold else FontWeight.Normal,
            color = if (activa) CA.tinta else CA.suave)
    }
}

@Composable
private fun GrillaProductos(lista: List<Producto>, carrito: Map<String, Int>, onProducto: (Producto) -> Unit) {
    lista.chunked(2).forEach { fila ->
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            fila.forEach { p -> TarjetaProducto(p, carrito[p.id] ?: 0, Modifier.weight(1f)) { onProducto(p) } }
            if (fila.size == 1) Spacer(Modifier.weight(1f))
        }
        Spacer(Modifier.height(12.dp))
    }
}

@Composable
private fun EstadoStock(stock: Int) {
    val (texto, fondo, color) = when {
        stock == 0 -> Triple("Sin stock", RojoFondo, RojoTexto)
        stock <= STOCK_BAJO -> Triple("Stock bajo", NaranjaFondo, NaranjaTexto)
        else -> Triple("En stock", VerdeFondo, VerdeTexto)
    }
    Row(
        Modifier.clip(RoundedCornerShape(20.dp)).background(fondo).padding(horizontal = 8.dp, vertical = 3.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(Modifier.size(6.dp).clip(CircleShape).background(color))
        Spacer(Modifier.width(5.dp))
        Text(texto, fontSize = 10.5.sp, fontWeight = FontWeight.Medium, color = color)
    }
}

@Composable
private fun Aviso(texto: String, error: Boolean) {
    Text(
        texto, fontSize = 12.5.sp, fontWeight = FontWeight.Medium,
        color = if (error) Olimpos.Red else Olimpos.Green,
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 12.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(if (error) Olimpos.Red.copy(alpha = 0.08f) else Olimpos.Green.copy(alpha = 0.1f))
            .padding(12.dp)
    )
}

@Composable
private fun FotoProducto(p: Producto, modifier: Modifier, radio: Int = 12) {
    Box(modifier.clip(RoundedCornerShape(radio.dp)).background(CA.amarilloSuave), contentAlignment = Alignment.Center) {
        if (p.imagen != null) {
            AsyncImage(model = p.imagen, contentDescription = p.nombre, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
        } else {
            Icon(Icons.Outlined.Storefront, null, tint = CA.acento, modifier = Modifier.size(34.dp))
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
        Text(p.nombre, fontSize = 13.sp, fontWeight = FontWeight.Medium, color = CA.texto, maxLines = 2,
            overflow = TextOverflow.Ellipsis, lineHeight = 17.sp, modifier = Modifier.height(34.dp))
        Spacer(Modifier.height(3.dp))
        Text(plata(p.precio), fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = CA.texto)
        Spacer(Modifier.height(6.dp))
        EstadoStock(p.stock)
    }
}

/* ═══════════════════════ DETALLE ═══════════════════════ */

@Composable
private fun DetalleProducto(p: Producto, enCarrito: Int, carrito: @Composable () -> Unit, onVolver: () -> Unit, onAgregar: (Int) -> Unit) {
    BackHandler(onBack = onVolver)
    var cantidad by remember { mutableStateOf(enCarrito.coerceIn(1, p.stock.coerceAtLeast(1))) }
    val maximo = minOf(p.stock, 20)
    Column(Modifier.fillMaxSize().background(CA.fondo).verticalScroll(rememberScrollState())) {
        Box(Modifier.statusBarsPadding().padding(horizontal = 20.dp).padding(top = 10.dp)) {
            FotoProducto(p, Modifier.fillMaxWidth().aspectRatio(1.05f), radio = 22)
            Box(
                Modifier.padding(10.dp).size(38.dp).clip(CircleShape).background(Color.White.copy(alpha = 0.9f)).clickable(onClick = onVolver),
                contentAlignment = Alignment.Center
            ) { IconoVolver(Color(0xFF1F1D16)) }
            Box(Modifier.align(Alignment.TopEnd).padding(10.dp).clip(CircleShape).background(Color.White.copy(alpha = 0.9f))) { carrito() }
        }
        Column(Modifier.padding(horizontal = 20.dp).padding(top = 18.dp, bottom = 30.dp)) {
            if (p.etiquetas.isNotEmpty()) {
                Text(p.etiquetas.joinToString(" · ").uppercase(), fontSize = 10.5.sp, fontWeight = FontWeight.SemiBold,
                    color = CA.acento, letterSpacing = 1.2.sp)
                Spacer(Modifier.height(4.dp))
            }
            Text(p.nombre, fontSize = 20.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, lineHeight = 25.sp)
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(plata(p.precio), fontSize = 24.sp, fontWeight = FontWeight.Bold, color = CA.texto, modifier = Modifier.weight(1f))
                EstadoStock(p.stock)
            }
            if (p.descripcion.isNotBlank()) {
                Spacer(Modifier.height(12.dp))
                Text(p.descripcion, fontSize = 13.5.sp, color = CA.suave, lineHeight = 20.sp)
            }
            Spacer(Modifier.height(22.dp))
            if (p.stock > 0) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Cantidad", fontSize = 13.5.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.weight(1f))
                    if (p.stock <= STOCK_BAJO) {
                        Text("Quedan ${p.stock}", fontSize = 11.5.sp, color = NaranjaTexto)
                        Spacer(Modifier.width(10.dp))
                    }
                    Contador(cantidad, 1, maximo) { cantidad = it }
                }
                Spacer(Modifier.height(18.dp))
                BotonPrincipal("Agregar al carrito · ${plata(p.precio * cantidad)}") { onAgregar(cantidad) }
                Spacer(Modifier.height(10.dp))
                Text("Lo pagás y lo retirás en la recepción del club.", fontSize = 11.5.sp, color = CA.suave,
                    modifier = Modifier.fillMaxWidth(), textAlign = TextAlign.Center)
            } else {
                Text("Por ahora no hay stock. Consultá en la recepción cuándo vuelve a entrar.", fontSize = 12.5.sp, color = CA.suave)
            }
        }
    }
}

@Composable
private fun Contador(valor: Int, minimo: Int, maximo: Int, onCambio: (Int) -> Unit) {
    Row(
        Modifier.clip(RoundedCornerShape(10.dp)).border(1.dp, CA.borde, RoundedCornerShape(10.dp)),
        verticalAlignment = Alignment.CenterVertically
    ) {
        BotonContador(Icons.Outlined.Remove, valor > minimo) { onCambio(valor - 1) }
        Text("$valor", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = CA.texto,
            modifier = Modifier.width(30.dp), textAlign = TextAlign.Center)
        BotonContador(Icons.Outlined.Add, valor < maximo) { onCambio(valor + 1) }
    }
}

@Composable
private fun BotonContador(icono: ImageVector, habilitado: Boolean, onClick: () -> Unit) {
    Box(Modifier.size(32.dp).clickable(enabled = habilitado, onClick = onClick), contentAlignment = Alignment.Center) {
        Icon(icono, null, tint = if (habilitado) CA.texto else CA.suave.copy(alpha = 0.4f), modifier = Modifier.size(15.dp))
    }
}

/* ═══════════════════════ CARRITO ═══════════════════════ */

@Composable
private fun Carrito(
    productos: List<Producto>,
    carrito: MutableMap<String, Int>,
    total: Double,
    enviando: Boolean,
    onVolver: () -> Unit,
    onConfirmar: () -> Unit
) {
    val unidades = carrito.values.sum()
    Column(Modifier.fillMaxSize().background(CA.fondo).verticalScroll(rememberScrollState())) {
        EncabezadoArena("Carrito ($unidades)", "Revisalo antes de confirmar", onVolver)
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 30.dp)) {
            if (carrito.isEmpty()) {
                Text("Tu carrito está vacío. Agregá productos desde la NutriStore.", fontSize = 13.sp, color = CA.suave)
                return@Column
            }
            carrito.entries.toList().forEach { (id, n) ->
                val p = productos.firstOrNull { it.id == id } ?: return@forEach
                TarjetaLisa(Modifier.fillMaxWidth().padding(bottom = 10.dp), padding = 10.dp) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        FotoProducto(p, Modifier.size(74.dp))
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text(p.nombre, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, maxLines = 2,
                                overflow = TextOverflow.Ellipsis)
                            p.etiquetas.firstOrNull()?.let { Text(it, fontSize = 11.sp, color = CA.suave) }
                            Spacer(Modifier.height(4.dp))
                            Text(plata(p.precio), fontSize = 13.5.sp, fontWeight = FontWeight.SemiBold, color = CA.texto)
                            Spacer(Modifier.height(6.dp))
                            Contador(n, 1, minOf(p.stock, 20).coerceAtLeast(1)) { carrito[id] = it }
                        }
                        Box(Modifier.size(34.dp).clip(CircleShape).clickable { carrito.remove(id) }, contentAlignment = Alignment.Center) {
                            Icon(Icons.Outlined.DeleteOutline, "Quitar", tint = CA.suave, modifier = Modifier.size(19.dp))
                        }
                    }
                }
            }
            Spacer(Modifier.height(8.dp))
            FilaTotal("Subtotal", plata(total))
            FilaTotal("Retiro en la recepción", "Gratis")
            HorizontalDivider(color = CA.borde, modifier = Modifier.padding(vertical = 10.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Total", fontSize = 15.sp, fontWeight = FontWeight.SemiBold, color = CA.texto, modifier = Modifier.weight(1f))
                Text(plata(total), fontSize = 18.sp, fontWeight = FontWeight.Bold, color = CA.texto)
            }
            Spacer(Modifier.height(18.dp))
            BotonPrincipal(if (enviando) "Enviando…" else "Confirmar pedido", habilitado = !enviando, onClick = onConfirmar)
            Spacer(Modifier.height(10.dp))
            Text(
                "Al confirmar, los productos quedan reservados para vos. Los pagás y los retirás en la recepción; " +
                    "si cambiás de idea, podés cancelar el pedido desde la NutriStore.",
                fontSize = 11.5.sp, color = CA.suave, lineHeight = 17.sp, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@Composable
private fun FilaTotal(titulo: String, valor: String) {
    Row(Modifier.padding(vertical = 3.dp)) {
        Text(titulo, fontSize = 13.sp, color = CA.suave, modifier = Modifier.weight(1f))
        Text(valor, fontSize = 13.sp, color = CA.texto)
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
