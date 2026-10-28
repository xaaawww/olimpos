# OLIMPOS GYM — Tienda del club (suplementos, accesorios, ropa…)
#
# Tablas: productos, productoetiquetas, pedidostienda, pedidotiendaitems
# (ver neon/tienda.sql). La gestiona solo el dueño desde la sección Tienda.
#
# Los socios ven en la app los productos PUBLICADOS y arman un pedido: queda
# reservado (descuenta el stock) y lo pagan y retiran en la recepción, donde
# el dueño lo marca como entregado. Si se cancela, el stock vuelve.
#
# Un producto (dict):
#   {"id": "12" | None, "nombre": str, "descripcion": str, "precio": float,
#    "stock": int, "etiquetas": [str], "imagen": "<Base64 JPEG>" | None,
#    "publicado": bool, "actualizado": "2026-10-27T18:00:00"}

import neon_db
import validaciones

MAX_ETIQUETAS = 4
MAX_DESCRIPCION = 1000
# Para arrancar rápido en el editor; se puede escribir cualquier otra.
ETIQUETAS_SUGERIDAS = ["Proteínas", "Creatina", "Pre-entreno", "Vitaminas", "Snacks", "Bebidas",
                       "Accesorios", "Ropa", "Shakers"]

_cache: list[dict] | None = None


def nuevo_producto() -> dict:
    return {"id": None, "nombre": "", "descripcion": "", "precio": None, "stock": 0, "etiquetas": [],
            "imagen": None, "publicado": False, "actualizado": ""}


def cargar_productos(forzar: bool = False) -> list[dict]:
    global _cache
    if _cache is None or forzar:
        filas = neon_db.consulta(
            "SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.stock, p.imagen, p.publicado,"
            " to_char(p.fecha_actualizacion, 'YYYY-MM-DD\"T\"HH24:MI:SS') AS actualizado,"
            " COALESCE((SELECT array_agg(e.etiqueta ORDER BY e.orden) FROM productoetiquetas e"
            "           WHERE e.id_producto = p.id_producto), '{}') AS etiquetas"
            " FROM productos p ORDER BY lower(p.nombre)")
        _cache = [{"id": str(f["id_producto"]), "nombre": f["nombre"], "descripcion": f["descripcion"] or "",
                   "precio": float(f["precio"]), "stock": int(f["stock"]), "imagen": f["imagen"],
                   "publicado": bool(f["publicado"]), "actualizado": f["actualizado"],
                   "etiquetas": list(f["etiquetas"] or [])} for f in filas]
    return _cache


def todas_las_etiquetas(productos: list[dict]) -> list[str]:
    """Las que ya usa algún producto (para los filtros), sin repetir."""
    vistas = {}
    for p in productos:
        for e in p["etiquetas"]:
            vistas.setdefault(validaciones.normalizar(e), e)
    return sorted(vistas.values(), key=validaciones.normalizar)


def validar(p: dict) -> None:
    """Revisa y limpia el producto antes de guardarlo (ValueError con el primer problema)."""
    p["nombre"] = validaciones.texto(p.get("nombre"), "el nombre del producto", maximo=80, minimo=3)
    excluir = ("id_producto", int(p["id"])) if p.get("id") else None
    if validaciones.ya_existe("productos", "nombre", p["nombre"], excluir, sin_mayusculas=True):
        raise ValueError(f"Ya hay un producto llamado \"{p['nombre']}\".")
    p["descripcion"] = validaciones.texto(p.get("descripcion"), "la descripción", maximo=MAX_DESCRIPCION,
                                          obligatorio=False, multilinea=True) or ""
    p["precio"] = validaciones.monto(p.get("precio"), "el precio", maximo=10_000_000)
    p["stock"] = validaciones.entero(p.get("stock"), "el stock", minimo=0, maximo=100_000)
    p["etiquetas"] = validaciones.etiquetas(p.get("etiquetas"), maximo_items=MAX_ETIQUETAS, maximo_largo=30)
    if p.get("publicado") and not p["etiquetas"]:
        raise ValueError("Poné al menos una etiqueta antes de publicarlo: así se ordena en la app.")


def guardar(p: dict) -> dict:
    """Crea o actualiza el producto (con sus etiquetas) y devuelve la lista nueva."""
    validar(p)
    with neon_db.transaccion() as cur:
        if p.get("id"):
            cur.execute(
                "UPDATE productos SET nombre = %s, descripcion = %s, precio = %s, stock = %s, imagen = %s,"
                " publicado = %s, fecha_actualizacion = now() WHERE id_producto = %s",
                (p["nombre"], p["descripcion"] or None, p["precio"], p["stock"], p.get("imagen"),
                 bool(p.get("publicado")), int(p["id"])))
            cur.execute("DELETE FROM productoetiquetas WHERE id_producto = %s", (int(p["id"]),))
            id_producto = int(p["id"])
        else:
            cur.execute(
                "INSERT INTO productos (nombre, descripcion, precio, stock, imagen, publicado)"
                " VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_producto",
                (p["nombre"], p["descripcion"] or None, p["precio"], p["stock"], p.get("imagen"),
                 bool(p.get("publicado"))))
            id_producto = cur.fetchone()["id_producto"]
        for i, etiqueta in enumerate(p["etiquetas"]):
            cur.execute("INSERT INTO productoetiquetas (id_producto, etiqueta, orden) VALUES (%s, %s, %s)",
                        (id_producto, etiqueta, i))
    p["id"] = str(id_producto)
    return cargar_productos(forzar=True)


def eliminar(id_producto: str) -> tuple[list[dict], str]:
    """Si el producto ya está en algún pedido no se puede borrar (el pedido
    tiene que seguir diciendo qué se vendió): se despublica. Devuelve la lista
    nueva y un mensaje de lo que pasó."""
    usado = neon_db.una_fila("SELECT 1 AS x FROM pedidotiendaitems WHERE id_producto = %s LIMIT 1", (int(id_producto),))
    if usado:
        neon_db.ejecutar("UPDATE productos SET publicado = FALSE, fecha_actualizacion = now() WHERE id_producto = %s",
                         (int(id_producto),))
        mensaje = "Ya tiene pedidos, así que no se borra: quedó como borrador y no se ve en la app."
    else:
        neon_db.ejecutar("DELETE FROM productos WHERE id_producto = %s", (int(id_producto),))
        mensaje = "Producto eliminado."
    return cargar_productos(forzar=True), mensaje


# ── pedidos ──
def pedidos(estado: str | None = "pendiente") -> list[dict]:
    """Pedidos (los pendientes primero por fecha) con el socio y sus productos."""
    filas = neon_db.consulta(
        "SELECT p.id_pedido, p.estado, p.total, p.fecha, trim(s.nombre || ' ' || s.apellido) AS socio,"
        " s.telefono, COALESCE((SELECT json_agg(json_build_object('nombre', i.nombre, 'cantidad', i.cantidad,"
        "   'precio', i.precio_unitario) ORDER BY i.nombre) FROM pedidotiendaitems i WHERE i.id_pedido = p.id_pedido),"
        "   '[]') AS items"
        " FROM pedidostienda p JOIN socios s USING (id_socio)"
        + (" WHERE p.estado = %s" if estado else "") + " ORDER BY p.fecha" + ("" if estado == "pendiente" else " DESC")
        + " LIMIT 200", (estado,) if estado else ())
    return [{"id": f["id_pedido"], "estado": f["estado"], "total": float(f["total"]), "fecha": f["fecha"],
             "socio": f["socio"], "telefono": f["telefono"], "items": f["items"]} for f in filas]


def cerrar_pedido(id_pedido: int, estado: str, id_empleado: int | None) -> None:
    """Marca un pedido pendiente como entregado o cancelado. Al cancelar, el
    stock reservado vuelve a los productos."""
    if estado not in ("entregado", "cancelado"):
        raise ValueError("Estado inválido")
    with neon_db.transaccion() as cur:
        cur.execute("UPDATE pedidostienda SET estado = %s, fecha_cierre = now(), id_empleado_cierre = %s"
                    " WHERE id_pedido = %s AND estado = 'pendiente' RETURNING id_pedido", (estado, id_empleado, id_pedido))
        if not cur.fetchone():
            raise ValueError("Ese pedido ya no está pendiente.")
        if estado == "cancelado":
            cur.execute("UPDATE productos p SET stock = p.stock + i.cantidad FROM pedidotiendaitems i"
                        " WHERE i.id_pedido = %s AND i.id_producto = p.id_producto", (id_pedido,))
    cargar_productos(forzar=True)
