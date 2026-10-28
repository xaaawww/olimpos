package com.olimpos.gym.data

import org.json.JSONArray
import org.json.JSONObject
import java.util.Base64

/**
 * Tienda del club (API: ApiWorker/src/rutas_tienda.ts). El dueño carga los
 * productos desde el sistema de empleados; el socio arma un pedido acá, queda
 * reservado (descuenta el stock) y lo paga y retira en la recepción.
 */
data class Producto(
    val id: String,
    val nombre: String,
    val descripcion: String,
    val precio: Double,
    val stock: Int,
    val imagen: ByteArray?,
    val etiquetas: List<String>
)

data class ItemPedido(val nombre: String, val cantidad: Int, val precio: Double)

data class PedidoTienda(
    val id: String,
    val estado: String,          // pendiente | entregado | cancelado
    val total: Double,
    val fechaMs: Long,
    val items: List<ItemPedido>
)

suspend fun cargarProductosTienda(): List<Producto>? = try {
    Api.get("/v1/tienda").optJSONArray("productos")?.objetos()?.map { j ->
        Producto(
            id = j.optString("id"),
            nombre = j.optString("nombre"),
            descripcion = j.optString("descripcion"),
            precio = j.optDouble("precio"),
            stock = j.optInt("stock"),
            imagen = j.optString("imagen").takeIf { it.isNotEmpty() && it != "null" }?.let {
                try { Base64.getDecoder().decode(it) } catch (e: IllegalArgumentException) { null }
            },
            etiquetas = j.optJSONArray("etiquetas")?.let { a -> (0 until a.length()).map { a.optString(it) } } ?: emptyList()
        )
    } ?: emptyList()
} catch (e: Exception) {
    null
}

private fun pedidoDesdeJson(j: JSONObject) = PedidoTienda(
    id = j.optString("id"),
    estado = j.optString("estado"),
    total = j.optDouble("total"),
    fechaMs = j.optLong("fecha_ms"),
    items = j.optJSONArray("items")?.objetos()?.map {
        ItemPedido(it.optString("nombre"), it.optInt("cantidad"), it.optDouble("precio"))
    } ?: emptyList()
)

suspend fun cargarPedidosTienda(): List<PedidoTienda>? = try {
    Api.get("/v1/tienda/pedidos").optJSONArray("pedidos")?.objetos()?.map(::pedidoDesdeJson) ?: emptyList()
} catch (e: Exception) {
    null
}

/** [carrito]: id del producto → cantidad. Devuelve el pedido creado o el
 *  mensaje de error listo para mostrar. */
suspend fun hacerPedidoTienda(carrito: Map<String, Int>): Result<PedidoTienda> = try {
    val items = JSONArray()
    carrito.filterValues { it > 0 }.forEach { (id, n) -> items.put(JSONObject().put("id", id).put("cantidad", n)) }
    Result.success(pedidoDesdeJson(Api.post("/v1/tienda/pedidos", JSONObject().put("items", items)).getJSONObject("pedido")))
} catch (e: Api.ErrorApi) {
    Result.failure(Exception(e.message))
} catch (e: Exception) {
    Result.failure(Exception("Sin conexión. Revisá internet y probá de nuevo."))
}

suspend fun cancelarPedidoTienda(id: String): String? = try {
    Api.delete("/v1/tienda/pedidos/$id")
    null
} catch (e: Api.ErrorApi) {
    e.message
} catch (e: Exception) {
    "Sin conexión. Revisá internet y probá de nuevo."
}

/** "$ 32.000" o "$ 1.250,50", como en el sistema de empleados. */
fun plata(v: Double): String {
    val entero = v % 1.0 == 0.0
    val texto = if (entero) "%,.0f".format(java.util.Locale.US, v) else "%,.2f".format(java.util.Locale.US, v)
    return "$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")
}
