// Rutas de la tienda del club: el catálogo publicado, los pedidos del socio,
// hacer un pedido y cancelarlo. El dueño carga los productos desde el sistema
// de empleados (tienda_repo.py) y entrega los pedidos en la recepción, donde
// se pagan. Ver neon/tienda.sql.

import { entero, ErrorApi, Fila, idNumerico, MS, Ruta } from "./util.js";

/** Pedidos sin retirar que puede tener un socio a la vez (para que nadie
 *  reserve todo el stock y no lo venga a buscar). */
const MAX_PEDIDOS_PENDIENTES = 3;
const MAX_PRODUCTOS_POR_PEDIDO = 10;

const catalogo: Ruta = {
  metodo: "GET", patron: /^\/v1\/tienda$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.stock, p.imagen,
              COALESCE((SELECT array_agg(e.etiqueta ORDER BY e.orden) FROM productoetiquetas e
                        WHERE e.id_producto = p.id_producto), '{}') AS etiquetas
       FROM productos p WHERE p.publicado ORDER BY lower(p.nombre)`);
    return {
      productos: r.rows.map((f) => ({
        id: String(f.id_producto), nombre: f.nombre, descripcion: f.descripcion ?? "", precio: Number(f.precio),
        stock: f.stock, imagen: f.imagen, etiquetas: f.etiquetas,
      })),
    };
  },
};

function pedidoJson(f: Fila) {
  return {
    id: String(f.id_pedido), estado: f.estado, total: Number(f.total), fecha_ms: f.fecha_ms,
    items: (f.items ?? []).map((i: Fila) => ({ nombre: i.nombre, cantidad: i.cantidad, precio: Number(i.precio) })),
  };
}

const SQL_PEDIDOS = `
  SELECT p.id_pedido, p.estado, p.total, ${MS("p.fecha")} AS fecha_ms,
         (SELECT json_agg(json_build_object('nombre', i.nombre, 'cantidad', i.cantidad, 'precio', i.precio_unitario)
                 ORDER BY i.nombre) FROM pedidotiendaitems i WHERE i.id_pedido = p.id_pedido) AS items
  FROM pedidostienda p WHERE p.id_socio = $1`;

const misPedidos: Ruta = {
  metodo: "GET", patron: /^\/v1\/tienda\/pedidos$/,
  async manejador(c) {
    const r = await c.db.query(`${SQL_PEDIDOS} ORDER BY p.fecha DESC LIMIT 30`, [c.idSocio]);
    return { pedidos: r.rows.map(pedidoJson) };
  },
};

// Hace el pedido en UNA transacción: bloquea los productos (FOR UPDATE) para
// que dos socios no se lleven la última unidad, comprueba stock y que estén
// publicados, copia nombre y precio actuales (el precio lo pone la base, nunca
// la app) y descuenta el stock.
const hacerPedido: Ruta = {
  metodo: "POST", patron: /^\/v1\/tienda\/pedidos$/,
  async manejador(c) {
    const crudo = c.body.items;
    if (!Array.isArray(crudo) || crudo.length < 1) throw new ErrorApi(400, "El pedido está vacío.");
    if (crudo.length > MAX_PRODUCTOS_POR_PEDIDO) throw new ErrorApi(400, `Un pedido puede tener hasta ${MAX_PRODUCTOS_POR_PEDIDO} productos distintos.`);
    const cantidades = new Map<number, number>();
    for (const it of crudo) {
      const id = idNumerico(String(it?.id ?? ""), "producto");
      cantidades.set(id, (cantidades.get(id) ?? 0) + entero(it?.cantidad, "cantidad", 1, 20));
    }
    for (const n of cantidades.values()) if (n > 20) throw new ErrorApi(400, "Podés pedir hasta 20 unidades de cada producto.");

    return c.db.tx(async (db) => {
      const pendientes = await db.query("SELECT count(*)::int AS n FROM pedidostienda WHERE id_socio = $1 AND estado = 'pendiente'", [c.idSocio]);
      if (pendientes.rows[0].n >= MAX_PEDIDOS_PENDIENTES) {
        throw new ErrorApi(409, `Ya tenés ${MAX_PEDIDOS_PENDIENTES} pedidos sin retirar. Pasá a buscarlos por la recepción antes de hacer otro.`);
      }
      const ids = [...cantidades.keys()];
      const prods = await db.query(
        "SELECT id_producto, nombre, precio, stock, publicado FROM productos WHERE id_producto = ANY($1::int[]) ORDER BY id_producto FOR UPDATE",
        [ids]);
      if (prods.rows.length !== ids.length || prods.rows.some((p) => !p.publicado)) {
        throw new ErrorApi(409, "Algún producto ya no está en la tienda. Actualizá el catálogo y probá de nuevo.");
      }
      for (const p of prods.rows) {
        const pide = cantidades.get(p.id_producto)!;
        if (p.stock < pide) {
          throw new ErrorApi(409, p.stock === 0 ? `"${p.nombre}" se quedó sin stock.` : `De "${p.nombre}" quedan solo ${p.stock}.`);
        }
      }
      const total = prods.rows.reduce((s, p) => s + Number(p.precio) * cantidades.get(p.id_producto)!, 0);
      const ped = await db.query("INSERT INTO pedidostienda (id_socio, total) VALUES ($1, $2) RETURNING id_pedido", [c.idSocio, total]);
      const idPedido = ped.rows[0].id_pedido;
      for (const p of prods.rows) {
        const n = cantidades.get(p.id_producto)!;
        await db.query(
          "INSERT INTO pedidotiendaitems (id_pedido, id_producto, nombre, precio_unitario, cantidad) VALUES ($1, $2, $3, $4, $5)",
          [idPedido, p.id_producto, p.nombre, p.precio, n]);
        await db.query("UPDATE productos SET stock = stock - $1 WHERE id_producto = $2", [n, p.id_producto]);
      }
      const r = await db.query(`${SQL_PEDIDOS} AND p.id_pedido = $2`, [c.idSocio, idPedido]);
      return { pedido: pedidoJson(r.rows[0]) };
    });
  },
};

// El socio puede cancelar un pedido mientras no lo retiró: el stock vuelve.
const cancelarPedido: Ruta = {
  metodo: "DELETE", patron: /^\/v1\/tienda\/pedidos\/([0-9]+)$/,
  async manejador(c) {
    const id = idNumerico(c.params[0], "pedido");
    return c.db.tx(async (db) => {
      const r = await db.query(
        `UPDATE pedidostienda SET estado = 'cancelado', fecha_cierre = now()
         WHERE id_pedido = $1 AND id_socio = $2 AND estado = 'pendiente' RETURNING id_pedido`, [id, c.idSocio]);
      if (!r.rows.length) throw new ErrorApi(404, "Ese pedido no existe o ya no se puede cancelar.");
      await db.query(
        `UPDATE productos p SET stock = p.stock + i.cantidad FROM pedidotiendaitems i
         WHERE i.id_pedido = $1 AND i.id_producto = p.id_producto`, [id]);
      return { ok: true };
    });
  },
};

export const rutasTienda: Ruta[] = [catalogo, misPedidos, hacerPedido, cancelarPedido];
