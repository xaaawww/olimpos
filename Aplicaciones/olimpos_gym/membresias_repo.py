# OLIMPOS GYM — Repositorio de membresías asignadas (Dueño / Administrador /
# Recepcionista)
#
# La membresía de un socio la asigna un empleado acá, con fecha de inicio
# real — el socio solo la ve y puede "pedir" un cambio de plan (o pagarla
# con Mercado Pago desde la app). En la base es una fila de "sociomembresia"
# (socio + plan del catálogo "membresias" + fechas + estado). Cambiar o
# quitar un plan NO borra nada: la fila anterior queda como 'cancelada', así
# se conserva el historial.
#
# La pantalla la maneja como un diccionario por socio:
# {
#   "socio_id": "uid123", "plan": "Oro", "fecha_inicio_ms": 1737000000000,
#   "asignado_por": "Carlos García — Dueño"
# }

from datetime import date, datetime, timedelta

import neon_db

# Mismos 3 planes que el catálogo "membresias" de la base y que PLANES_MEMBRESIA
# en la app móvil (precio/beneficios viven en la base).
PLANES = ["Bronce", "Oro", "Platino"]

# Argos (el asistente de IA de la app móvil) es un beneficio de pago: solo lo
# tienen los socios con uno de estos planes (columna membresias.incluye_argos;
# el Worker de Argos lo verifica del lado del servidor).
PLANES_CON_ARGOS = ("Oro", "Platino")

_cache_membresias: dict[str, dict] | None = None


def cargar_membresias(forzar: bool = False) -> dict[str, dict]:
    global _cache_membresias
    if _cache_membresias is None or forzar:
        filas = neon_db.consulta(
            "SELECT s.firebase_uid, m.nombre AS plan, sm.fecha_inicio, sm.asignado_por"
            " FROM sociomembresia sm JOIN socios s USING (id_socio) JOIN membresias m USING (id_membresia)"
            " WHERE sm.estado = 'activa' AND s.firebase_uid IS NOT NULL"
        )
        _cache_membresias = {
            f["firebase_uid"]: {
                "socio_id": f["firebase_uid"], "plan": f["plan"],
                "fecha_inicio_ms": int(datetime.combine(f["fecha_inicio"], datetime.min.time()).timestamp() * 1000),
                "asignado_por": f["asignado_por"] or "",
            }
            for f in filas
        }
    return _cache_membresias


def obtener_membresia(socio_id: str) -> dict | None:
    return cargar_membresias().get(socio_id)


def nueva_fecha_hoy_ms() -> int:
    return int(datetime.now().timestamp() * 1000)


def fecha_legible(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%d/%m/%Y")


def parsear_fecha(texto: str) -> int | None:
    try:
        return int(datetime.strptime(texto.strip(), "%d/%m/%Y").timestamp() * 1000)
    except ValueError:
        return None


def asignar_membresia(socio_id: str, plan: str, fecha_inicio_ms: int, asignado_por: str) -> dict[str, dict]:
    global _cache_membresias
    inicio = datetime.fromtimestamp(fecha_inicio_ms / 1000).date()
    with neon_db.transaccion() as cur:
        cur.execute("SELECT id_socio FROM socios WHERE firebase_uid = %s", (socio_id,))
        id_socio = cur.fetchone()["id_socio"]
        cur.execute("SELECT id_membresia, duracion_dias FROM membresias WHERE nombre = %s", (plan,))
        m = cur.fetchone()
        cur.execute("UPDATE sociomembresia SET estado = 'cancelada', fecha_cancelacion = %s WHERE id_socio = %s AND estado = 'activa'",
                    (date.today(), id_socio))
        cur.execute(
            "INSERT INTO sociomembresia (id_socio, id_membresia, fecha_inicio, fecha_vencimiento, estado, asignado_por)"
            " VALUES (%s,%s,%s,%s,'activa',%s)",
            (id_socio, m["id_membresia"], inicio, inicio + timedelta(days=m["duracion_dias"]), asignado_por),
        )
    cache = cargar_membresias(forzar=True)
    return cache


def quitar_membresia(socio_id: str) -> dict[str, dict]:
    neon_db.ejecutar(
        "UPDATE sociomembresia SET estado = 'cancelada', fecha_cancelacion = %s"
        " WHERE estado = 'activa' AND id_socio = (SELECT id_socio FROM socios WHERE firebase_uid = %s)",
        (date.today(), socio_id),
    )
    return cargar_membresias(forzar=True)
