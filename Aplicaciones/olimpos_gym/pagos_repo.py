# OLIMPOS GYM — Pagos y cuotas (Dueño / Administrador / Recepcionista)
#
# Un pago es una fila de "pagos" (socio, plan, medio de pago, monto, fecha y
# hasta cuándo cubre). Llegan de dos lados:
#   - Mercado Pago, desde la app (lo registra el PagosWorker)
#   - el mostrador, desde esta pantalla (efectivo, transferencia, tarjeta...)
# Registrar un pago puede renovar la membresía en el mismo paso: si todavía
# estaba vigente, el período nuevo arranca cuando termina el actual (no se
# pierden días); si ya venció, arranca el día del pago.
# Anular un pago no lo borra: queda con estado 'Anulado' como historial.

import csv
from datetime import date, datetime, timedelta

import neon_db

METODOS = ["Efectivo", "Transferencia", "Tarjeta de débito", "Tarjeta de crédito", "Mercado Pago"]
ZONA = "America/Argentina/Buenos_Aires"
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
         "Noviembre", "Diciembre"]
MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def hoy() -> date:
    return date.today()


def mes_anterior(anio: int, mes: int) -> tuple[int, int]:
    return (anio - 1, 12) if mes == 1 else (anio, mes - 1)


def nombre_mes(anio: int, mes: int) -> str:
    return f"{MESES[mes - 1]} {anio}"


def planes() -> list[dict]:
    return [{**p, "precio": float(p["precio"])} for p in neon_db.consulta(
        "SELECT id_membresia, nombre, precio, duracion_dias, estado FROM membresias ORDER BY precio")]


def socios() -> list[dict]:
    """Socios activos con su plan vigente (si tienen) para el formulario."""
    return neon_db.consulta(
        "SELECT s.id_socio, trim(s.nombre || ' ' || s.apellido) AS nombre, s.email, m.nombre AS plan,"
        " sm.fecha_vencimiento AS vencimiento FROM socios s"
        " LEFT JOIN sociomembresia sm ON sm.id_socio = s.id_socio AND sm.estado = 'activa'"
        " LEFT JOIN membresias m ON m.id_membresia = sm.id_membresia"
        " WHERE s.estado = 'activo' ORDER BY nombre")


# ── tablero ──
def resumen(anio: int, mes: int) -> dict:
    """Las cuatro tarjetas de arriba (con sus mini gráficos)."""
    pa, pm = mes_anterior(anio, mes)
    ingresos = _ingresos_mes(anio, mes)
    anterior = _ingresos_mes(pa, pm)
    por_dia = {f["dia"]: f for f in neon_db.consulta(
        f"SELECT (fecha_pago AT TIME ZONE '{ZONA}')::date AS dia, count(*) AS n, sum(monto) AS total FROM pagos"
        f" WHERE estado = 'Aprobado' AND fecha_pago > now() - interval '15 days' GROUP BY 1")}
    h = hoy()
    dias = [h - timedelta(days=i) for i in range(13, -1, -1)]
    pagos_dias = [int(por_dia[d]["n"]) if d in por_dia else 0 for d in dias]
    estados = neon_db.una_fila(
        "SELECT count(*) AS activos,"
        " count(*) FILTER (WHERE sm.fecha_vencimiento >= current_date) AS al_dia,"
        " count(*) FILTER (WHERE sm.fecha_vencimiento < current_date) AS vencidos,"
        " count(*) FILTER (WHERE sm.id_socio IS NULL) AS sin_plan"
        " FROM socios s LEFT JOIN sociomembresia sm ON sm.id_socio = s.id_socio AND sm.estado = 'activa'"
        " WHERE s.estado = 'activo'")
    meses = ultimos_meses(anio, mes, 6)
    return {
        "ingresos": ingresos, "ingresos_cambio": ((ingresos - anterior) / anterior * 100) if anterior else None,
        "ingresos_meses": [m["total"] for m in meses],
        "pagos_hoy": pagos_dias[-1], "pagos_ayer": pagos_dias[-2], "pagos_dias": pagos_dias,
        "activos": int(estados["activos"]), "al_dia": int(estados["al_dia"]),
        "vencidos": int(estados["vencidos"]), "sin_plan": int(estados["sin_plan"]),
    }


def _ingresos_mes(anio: int, mes: int) -> float:
    fila = neon_db.una_fila(
        f"SELECT COALESCE(sum(monto), 0) AS total FROM pagos WHERE estado = 'Aprobado'"
        f" AND date_trunc('month', fecha_pago AT TIME ZONE '{ZONA}') = make_date(%s, %s, 1)", (anio, mes))
    return float(fila["total"])


def ultimos_meses(anio: int, mes: int, cantidad: int) -> list[dict]:
    """[{"anio", "mes", "etiqueta", "total", "pagos"}] de los últimos N meses hasta (anio, mes)."""
    lista = []
    a, m = anio, mes
    for _ in range(cantidad):
        lista.append((a, m))
        a, m = mes_anterior(a, m)
    lista.reverse()
    filas = {(int(f["anio"]), int(f["mes"])): f for f in neon_db.consulta(
        f"SELECT extract(year FROM fecha_pago AT TIME ZONE '{ZONA}') AS anio,"
        f" extract(month FROM fecha_pago AT TIME ZONE '{ZONA}') AS mes, sum(monto) AS total, count(*) AS pagos"
        f" FROM pagos WHERE estado = 'Aprobado' AND fecha_pago >= make_date(%s, %s, 1) GROUP BY 1, 2",
        lista[0])}
    return [{"anio": a, "mes": m, "etiqueta": MESES_CORTOS[m - 1],
             "total": float(filas[(a, m)]["total"]) if (a, m) in filas else 0.0,
             "pagos": int(filas[(a, m)]["pagos"]) if (a, m) in filas else 0} for a, m in lista]


def por_plan(anio: int, mes: int) -> list[dict]:
    filas = neon_db.consulta(
        f"SELECT m.nombre AS plan, sum(p.monto) AS total, count(*) AS pagos FROM pagos p"
        f" JOIN membresias m USING (id_membresia) WHERE p.estado = 'Aprobado'"
        f" AND date_trunc('month', p.fecha_pago AT TIME ZONE '{ZONA}') = make_date(%s, %s, 1)"
        f" GROUP BY 1 ORDER BY 2 DESC", (anio, mes))
    total = sum(float(f["total"]) for f in filas) or 1
    return [{"plan": f["plan"], "total": float(f["total"]), "pagos": int(f["pagos"]),
             "porcentaje": float(f["total"]) / total * 100} for f in filas]


def pagos_del_mes(anio: int, mes: int, plan: str | None = None) -> list[dict]:
    filas = neon_db.consulta(
        f"SELECT p.id_pago, p.monto, p.fecha_pago, p.fecha_vencimiento, p.numero_comprobante, p.estado,"
        f" m.nombre AS plan, mp.tipo AS metodo, mp.proveedor, trim(s.nombre || ' ' || s.apellido) AS socio, s.id_socio"
        f" FROM pagos p JOIN socios s USING (id_socio) JOIN membresias m USING (id_membresia)"
        f" JOIN mediospago mp USING (id_medio_pago)"
        f" WHERE date_trunc('month', p.fecha_pago AT TIME ZONE '{ZONA}') = make_date(%s, %s, 1)"
        f" AND (%s::text IS NULL OR m.nombre = %s) ORDER BY p.fecha_pago DESC", (anio, mes, plan, plan))
    for f in filas:
        f["monto"] = float(f["monto"])
    return filas


def vencimientos(dias: int = 15) -> list[dict]:
    """Membresías vencidas (todavía 'activa' en la base, sin renovar) y las que
    vencen en los próximos N días, la más urgente primero."""
    filas = neon_db.consulta(
        "SELECT s.id_socio, trim(s.nombre || ' ' || s.apellido) AS socio, s.telefono, s.email, m.nombre AS plan,"
        " m.precio, sm.fecha_vencimiento AS vencimiento, sm.fecha_vencimiento - current_date AS dias"
        " FROM sociomembresia sm JOIN socios s USING (id_socio) JOIN membresias m USING (id_membresia)"
        " WHERE sm.estado = 'activa' AND s.estado = 'activo' AND sm.fecha_vencimiento <= current_date + %s"
        " ORDER BY sm.fecha_vencimiento", (dias,))
    for f in filas:
        f["precio"] = float(f["precio"])
        f["dias"] = int(f["dias"])
    return filas


def meses_disponibles() -> list[tuple[int, int]]:
    """Los últimos 12 meses (el actual primero) para el selector."""
    h = hoy()
    a, m = h.year, h.month
    lista = []
    for _ in range(12):
        lista.append((a, m))
        a, m = mes_anterior(a, m)
    return lista


# ── acciones ──
def registrar_pago(id_socio: int, plan: str, monto: float, metodo: str, fecha: date,
                   comprobante: str | None, renovar: bool, registrado_por: str) -> dict:
    """Guarda el pago (y renueva la membresía si se pidió), todo junto."""
    if monto <= 0:
        raise ValueError("El monto tiene que ser mayor a cero.")
    if metodo not in METODOS:
        raise ValueError("Elegí un medio de pago.")
    comprobante = (comprobante or "").strip() or None
    with neon_db.transaccion() as cur:
        cur.execute("SELECT id_membresia, duracion_dias FROM membresias WHERE nombre = %s", (plan,))
        m = cur.fetchone()
        if not m:
            raise ValueError("Ese plan no existe.")
        if comprobante:
            cur.execute("SELECT 1 FROM pagos WHERE numero_comprobante = %s", (comprobante,))
            if cur.fetchone():
                raise ValueError(f"Ya hay un pago con el comprobante {comprobante}.")
        cur.execute("SELECT id_plan_pago FROM planespago WHERE nombre = 'Pago único'")
        plan_pago = cur.fetchone()["id_plan_pago"]
        proveedor = "Mercado Pago" if metodo == "Mercado Pago" else "Mostrador"
        cur.execute("INSERT INTO mediospago (id_socio, tipo, proveedor, estado) VALUES (%s, %s, %s, 'activo')"
                    " ON CONFLICT (id_socio, tipo, proveedor) DO NOTHING", (id_socio, metodo, proveedor))
        cur.execute("SELECT id_medio_pago FROM mediospago WHERE id_socio = %s AND tipo = %s AND proveedor = %s",
                    (id_socio, metodo, proveedor))
        id_medio = cur.fetchone()["id_medio_pago"]

        vence = None
        if renovar:
            cur.execute("SELECT id_membresia, fecha_vencimiento FROM sociomembresia"
                        " WHERE id_socio = %s AND estado = 'activa'", (id_socio,))
            actual = cur.fetchone()
            # sigue vigente y es el mismo plan: el período nuevo arranca cuando termina el actual
            if actual and actual["fecha_vencimiento"] >= fecha and actual["id_membresia"] == m["id_membresia"]:
                inicio = actual["fecha_vencimiento"]
            else:
                inicio = fecha
            vence = inicio + timedelta(days=m["duracion_dias"])
            cur.execute("UPDATE sociomembresia SET estado = 'cancelada', fecha_cancelacion = %s"
                        " WHERE id_socio = %s AND estado = 'activa'", (fecha, id_socio))
            cur.execute("INSERT INTO sociomembresia (id_socio, id_membresia, fecha_inicio, fecha_vencimiento, estado,"
                        " asignado_por) VALUES (%s, %s, %s, %s, 'activa', %s)",
                        (id_socio, m["id_membresia"], inicio, vence, f"Pago en mostrador — {registrado_por}"[:255]))
        momento = datetime.now() if fecha == hoy() else datetime(fecha.year, fecha.month, fecha.day, 12)
        cur.execute("INSERT INTO pagos (id_socio, id_membresia, id_plan_pago, id_medio_pago, monto, fecha_pago,"
                    " fecha_vencimiento, numero_comprobante, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Aprobado')"
                    " RETURNING id_pago",
                    (id_socio, m["id_membresia"], plan_pago, id_medio, monto, momento.astimezone(), vence, comprobante))
        id_pago = cur.fetchone()["id_pago"]
    try:
        import membresias_repo
        membresias_repo.cargar_membresias(forzar=True)   # la pantalla de Membresías ve el cambio
    except Exception:
        pass
    return {"id_pago": id_pago, "vence": vence}


def anular_pago(id_pago: int) -> None:
    neon_db.ejecutar("UPDATE pagos SET estado = 'Anulado' WHERE id_pago = %s AND estado = 'Aprobado'", (id_pago,))


def actualizar_plan(id_membresia: int, precio: float, duracion_dias: int) -> None:
    """Cambia el precio y la duración de un plan. Es el mismo catálogo que usa
    la app (Mercado Pago cobra este precio)."""
    if precio <= 0 or duracion_dias <= 0:
        raise ValueError("El precio y la duración tienen que ser mayores a cero.")
    neon_db.ejecutar("UPDATE membresias SET precio = %s, duracion_dias = %s WHERE id_membresia = %s",
                     (precio, duracion_dias, id_membresia))


def exportar_csv(ruta: str, anio: int, mes: int) -> int:
    """Guarda los pagos del mes en un CSV (se abre con Excel). Devuelve cuántos."""
    filas = pagos_del_mes(anio, mes)
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Fecha", "Socio", "Plan", "Monto", "Medio de pago", "Comprobante", "Cubre hasta", "Estado"])
        for p in filas:
            w.writerow([p["fecha_pago"].astimezone().strftime("%d/%m/%Y %H:%M"), p["socio"], p["plan"],
                        f"{p['monto']:.2f}".replace(".", ","), p["metodo"], p["numero_comprobante"] or "",
                        p["fecha_vencimiento"].strftime("%d/%m/%Y") if p["fecha_vencimiento"] else "",
                        "Pagado" if p["estado"] == "Aprobado" else p["estado"]])
        total = sum(p["monto"] for p in filas if p["estado"] == "Aprobado")
        w.writerow([])
        w.writerow(["", "", "Total cobrado", f"{total:.2f}".replace(".", ",")])
    return len(filas)
