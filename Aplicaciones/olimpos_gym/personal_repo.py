# OLIMPOS GYM — Personal (Dueño / Administrador)
#
# Empleados del sistema ("empleados" + su rol), sus sueldos y lo que hacen:
#   - alta: crea el usuario con una contraseña generada (se muestra una sola vez)
#   - baja: NO borra nada; estado = 'inactivo' + fecha y motivo (el login ya
#     rechaza a los inactivos). Se puede reactivar.
#   - sueldo: el mensual vive en empleados.sueldo; cada cambio queda en
#     "historialsueldo" y cada pago (sueldo del mes, adelanto o bono) en
#     "liquidacionessueldo" (anular un pago no lo borra: queda 'anulado').
#   - actividad: ingresos al sistema y lo que hizo según su rol (rutinas,
#     dietas, marcas verificadas, membresías asignadas, mensajes a Argos).

import secrets
import string
from datetime import date, datetime

import neon_db

ROLES = {
    "dueno": "Dueño", "admin": "Administrador", "entrenador": "Entrenador",
    "nutricionista": "Nutricionista", "seguridad": "Seguridad", "recepcionista": "Recepcionista",
}
TURNOS = ["Mañana", "Tarde", "Noche", "Mañana y tarde", "Rotativo"]
MEDIOS = ["Transferencia", "Efectivo"]
CONCEPTOS = ["Sueldo", "Adelanto", "Bono"]
CON_ESPECIALIDAD = ("entrenador", "nutricionista")


def hoy() -> date:
    return date.today()


def numero(valor) -> float:
    """Lee un monto como lo escribe la gente: "650.000", "650000", "650000,50"
    o "1.250.000,5" (punto de miles, coma decimal). Un número ya numérico
    pasa tal cual. Lanza ValueError si no es un número."""
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor or "").strip().replace("$", "").replace(" ", "")
    if not texto:
        raise ValueError
    import re
    if "," in texto:                                  # coma decimal: los puntos son de miles
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):   # 650.000 / 1.250.000
        texto = texto.replace(".", "")
    return float(texto)


def mes_actual() -> date:
    h = hoy()
    return date(h.year, h.month, 1)


# ── lectura ──
def empleados() -> list[dict]:
    """Todos los empleados (activos y de baja) con lo que muestra la tabla:
    rol, turno, sueldo, si cobró el sueldo de este mes y su último ingreso."""
    filas = neon_db.consulta(
        "SELECT e.id_empleado, e.usuario, e.nombre, e.apellido, e.dni, e.email, e.telefono, e.direccion,"
        " e.estado, e.fecha_ingreso::date AS ingreso, e.sueldo, e.turno, e.especialidad, e.fecha_baja, e.motivo_baja,"
        " r.nombre AS rol,"
        " (SELECT max(fecha) FROM intentosacceso i WHERE i.id_empleado = e.id_empleado AND i.resultado = 'exitoso') AS ultimo_ingreso,"
        " EXISTS (SELECT 1 FROM liquidacionessueldo l WHERE l.id_empleado = e.id_empleado AND l.concepto = 'Sueldo'"
        "   AND l.estado = 'pagado' AND l.periodo = date_trunc('month', current_date)::date) AS cobro_mes"
        " FROM empleados e JOIN rol r ON r.id_rol = e.rol ORDER BY e.estado, r.id_rol, e.nombre")
    for f in filas:
        f["sueldo"] = float(f["sueldo"]) if f["sueldo"] is not None else None
        f["nombre_completo"] = f"{f['nombre']} {f['apellido']}".strip()
    return filas


def resumen(lista: list[dict]) -> dict:
    activos = [e for e in lista if e["estado"] == "activo"]
    con_sueldo = [e for e in activos if e["sueldo"]]
    pagados = [e for e in con_sueldo if e["cobro_mes"]]
    total_mes = neon_db.una_fila(
        "SELECT COALESCE(sum(monto), 0) AS t FROM liquidacionessueldo WHERE estado = 'pagado'"
        " AND periodo = date_trunc('month', current_date)::date")["t"]
    return {
        "activos": len(activos), "de_baja": len(lista) - len(activos),
        "masa_salarial": sum(e["sueldo"] for e in con_sueldo),
        "pagados": len(pagados), "a_pagar": len(con_sueldo),
        "pendiente": sum(e["sueldo"] for e in con_sueldo if not e["cobro_mes"]),
        "pagado_mes": float(total_mes), "sin_sueldo": len(activos) - len(con_sueldo),
    }


def pagos(id_empleado: int) -> list[dict]:
    filas = neon_db.consulta(
        "SELECT id_liquidacion, periodo, concepto, monto, medio, fecha_pago, nota, registrado_por, estado"
        " FROM liquidacionessueldo WHERE id_empleado = %s ORDER BY periodo DESC, fecha_pago DESC", (id_empleado,))
    for f in filas:
        f["monto"] = float(f["monto"])
    return filas


def historial_sueldo(id_empleado: int) -> list[dict]:
    filas = neon_db.consulta(
        "SELECT sueldo_anterior, sueldo_nuevo, fecha, registrado_por FROM historialsueldo"
        " WHERE id_empleado = %s ORDER BY fecha DESC, id_historial DESC", (id_empleado,))
    for f in filas:
        f["sueldo_anterior"] = float(f["sueldo_anterior"]) if f["sueldo_anterior"] is not None else None
        f["sueldo_nuevo"] = float(f["sueldo_nuevo"])
    return filas


def actividad(emp: dict) -> dict:
    """Lo útil de su actividad: ingresos al sistema y lo que hizo según su rol."""
    i = emp["id_empleado"]
    accesos = neon_db.una_fila(
        "SELECT count(*) FILTER (WHERE resultado = 'exitoso' AND fecha > now() - interval '30 days') AS ingresos_30,"
        " count(*) FILTER (WHERE resultado = 'fallido' AND fecha > now() - interval '30 days') AS fallidos_30,"
        " count(DISTINCT fecha::date) FILTER (WHERE resultado = 'exitoso' AND fecha > now() - interval '30 days') AS dias_30,"
        " max(fecha) FILTER (WHERE resultado = 'exitoso') AS ultimo"
        " FROM intentosacceso WHERE id_empleado = %s", (i,))
    firma = f"%{emp['nombre_completo']} —%"
    hechos = neon_db.una_fila(
        "SELECT (SELECT count(*) FROM rutinas WHERE id_empleado = %s) AS rutinas,"
        " (SELECT count(DISTINCT id_socio) FROM rutinas WHERE id_empleado = %s AND estado = 'vigente') AS socios_rutina,"
        " (SELECT count(*) FROM dietas WHERE id_empleado = %s) AS dietas,"
        " (SELECT count(*) FROM marcaspersonales WHERE id_empleado_verificador = %s AND estado = 'verificada') AS marcas,"
        " (SELECT count(*) FROM marcaspersonales WHERE id_empleado_verificador = %s AND estado = 'rechazada') AS marcas_rechazadas,"
        " (SELECT count(*) FROM sociomembresia WHERE asignado_por LIKE %s) AS membresias,"
        " (SELECT COALESCE(sum(mensajes_enviados), 0) FROM argoscupodiario WHERE id_empleado = %s"
        "   AND fecha > current_date - 30) AS argos_30",
        (i, i, i, i, i, firma, i))
    return {**{k: (int(v) if isinstance(v, int) else v) for k, v in accesos.items()}, **{k: int(v) for k, v in hechos.items()}}


# ── validaciones ──
def _limpiar(datos: dict) -> dict:
    d = {k: (v.strip() if isinstance(v, str) else v) for k, v in datos.items()}
    if not d.get("nombre"):
        raise ValueError("Poné el nombre.")
    if not d.get("apellido"):
        raise ValueError("Poné el apellido.")
    if not d.get("email") or "@" not in d["email"] or "." not in d["email"].split("@")[-1]:
        raise ValueError("Revisá el email.")
    if d.get("dni") and not (d["dni"].isdigit() and 6 <= len(d["dni"]) <= 10):
        raise ValueError("El DNI tiene que tener entre 6 y 10 números, sin puntos.")
    if d.get("rol") not in ROLES:
        raise ValueError("Elegí el rol.")
    if d.get("sueldo") not in (None, ""):
        try:
            d["sueldo"] = numero(d["sueldo"])
        except ValueError:
            raise ValueError("El sueldo tiene que ser un número.")
        if d["sueldo"] < 0:
            raise ValueError("El sueldo no puede ser negativo.")
    else:
        d["sueldo"] = None
    for campo in ("dni", "telefono", "direccion", "turno", "especialidad"):
        d[campo] = d.get(campo) or None
    d["ingreso"] = d.get("ingreso") or hoy()
    if d["ingreso"] > hoy():
        raise ValueError("La fecha de ingreso no puede ser futura.")
    if d["rol"] not in CON_ESPECIALIDAD:
        d["especialidad"] = None
    return d


def _error_unico(ex: Exception) -> ValueError:
    texto = str(ex)
    for campo, aviso in (("dni", "Ya hay un empleado con ese DNI."), ("email", "Ya hay un empleado con ese email."),
                         ("usuario", "Ese usuario ya existe: elegí otro.")):
        if f"empleados_{campo}_key" in texto:
            return ValueError(aviso)
    return ValueError(f"No se pudo guardar: {texto.splitlines()[0]}")


def generar_password() -> str:
    """10 caracteres fáciles de dictar (sin 0/O ni 1/l) + un símbolo y un número."""
    letras = "".join(c for c in string.ascii_letters if c not in "OlI")
    base = "".join(secrets.choice(letras) for _ in range(7))
    return base[0].upper() + base[1:] + secrets.choice("#$%&") + "".join(secrets.choice("23456789") for _ in range(2))


def sugerir_usuario(nombre: str, apellido: str) -> str:
    import unicodedata
    texto = f"{nombre[:1]}{apellido}".lower()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if c.isalnum() and ord(c) < 128)
    base, n = texto or "empleado", 1
    candidato = base
    while neon_db.una_fila("SELECT 1 AS x FROM empleados WHERE usuario = %s", (candidato,)):
        n += 1
        candidato = f"{base}{n}"
    return candidato


# ── acciones ──
def crear(datos: dict, usuario: str, firma: str) -> tuple[int, str]:
    """Da de alta al empleado. Devuelve (id, contraseña inicial)."""
    d = _limpiar(datos)
    usuario = (usuario or "").strip().lower()
    if not usuario or not all(c.isalnum() or c in "._" for c in usuario):
        raise ValueError("El usuario solo puede tener letras, números, punto y guion bajo.")
    password = generar_password()
    ingreso = d["ingreso"]
    try:
        with neon_db.transaccion() as cur:
            cur.execute("SELECT id_rol FROM rol WHERE nombre = %s", (d["rol"],))
            id_rol = cur.fetchone()["id_rol"]
            cur.execute(
                "INSERT INTO empleados (dni, nombre, apellido, rol, email, contraseña, direccion, telefono, estado,"
                " fecha_ingreso, usuario, sueldo, turno, especialidad)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'activo',%s,%s,%s,%s,%s) RETURNING id_empleado",
                (d["dni"], d["nombre"], d["apellido"], id_rol, d["email"].lower(), neon_db.hash_password(password),
                 d["direccion"], d["telefono"], datetime.combine(ingreso, datetime.min.time()).astimezone(),
                 usuario, d["sueldo"], d["turno"], d["especialidad"]))
            nuevo = cur.fetchone()["id_empleado"]
            if d["sueldo"]:
                cur.execute("INSERT INTO historialsueldo (id_empleado, sueldo_anterior, sueldo_nuevo, registrado_por)"
                            " VALUES (%s, NULL, %s, %s)", (nuevo, d["sueldo"], firma))
    except ValueError:
        raise
    except Exception as ex:
        raise _error_unico(ex)
    return nuevo, password


def actualizar(id_empleado: int, datos: dict, firma: str) -> None:
    d = _limpiar(datos)
    try:
        with neon_db.transaccion() as cur:
            cur.execute("SELECT sueldo FROM empleados WHERE id_empleado = %s", (id_empleado,))
            anterior = cur.fetchone()["sueldo"]
            cur.execute("SELECT id_rol FROM rol WHERE nombre = %s", (d["rol"],))
            id_rol = cur.fetchone()["id_rol"]
            cur.execute(
                "UPDATE empleados SET nombre=%s, apellido=%s, dni=%s, email=%s, telefono=%s, direccion=%s, rol=%s,"
                " turno=%s, especialidad=%s, sueldo=%s, fecha_ingreso=%s WHERE id_empleado=%s",
                (d["nombre"], d["apellido"], d["dni"], d["email"].lower(), d["telefono"], d["direccion"], id_rol,
                 d["turno"], d["especialidad"], d["sueldo"],
                 datetime.combine(d["ingreso"], datetime.min.time()).astimezone(), id_empleado))
            if (float(anterior) if anterior is not None else None) != d["sueldo"] and d["sueldo"] is not None:
                cur.execute("INSERT INTO historialsueldo (id_empleado, sueldo_anterior, sueldo_nuevo, registrado_por)"
                            " VALUES (%s, %s, %s, %s)", (id_empleado, anterior, d["sueldo"], firma))
    except ValueError:
        raise
    except Exception as ex:
        raise _error_unico(ex)


def dar_de_baja(id_empleado: int, fecha: date, motivo: str) -> None:
    if not (motivo or "").strip():
        raise ValueError("Escribí el motivo de la baja.")
    neon_db.ejecutar("UPDATE empleados SET estado = 'inactivo', fecha_baja = %s, motivo_baja = %s WHERE id_empleado = %s",
                     (fecha, motivo.strip()[:255], id_empleado))


def reactivar(id_empleado: int) -> None:
    neon_db.ejecutar("UPDATE empleados SET estado = 'activo', fecha_baja = NULL, motivo_baja = NULL WHERE id_empleado = %s",
                     (id_empleado,))


def restablecer_password(id_empleado: int) -> str:
    password = generar_password()
    neon_db.ejecutar("UPDATE empleados SET contraseña = %s WHERE id_empleado = %s",
                     (neon_db.hash_password(password), id_empleado))
    return password


def registrar_pago(id_empleado: int, periodo: date, concepto: str, monto: float, medio: str,
                   nota: str, firma: str) -> int:
    if concepto not in CONCEPTOS:
        raise ValueError("Elegí el concepto.")
    if medio not in MEDIOS:
        raise ValueError("Elegí cómo se pagó.")
    if not monto or monto <= 0:
        raise ValueError("El monto tiene que ser mayor a cero.")
    periodo = date(periodo.year, periodo.month, 1)
    if concepto == "Sueldo" and neon_db.una_fila(
            "SELECT 1 AS x FROM liquidacionessueldo WHERE id_empleado = %s AND periodo = %s AND concepto = 'Sueldo'"
            " AND estado = 'pagado'", (id_empleado, periodo)):
        raise ValueError(f"El sueldo de {periodo:%m/%Y} ya está pagado. Si es un extra, cargalo como Bono o Adelanto.")
    with neon_db.transaccion() as cur:
        cur.execute(
            "INSERT INTO liquidacionessueldo (id_empleado, periodo, concepto, monto, medio, nota, registrado_por)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id_liquidacion",
            (id_empleado, periodo, concepto, monto, medio, (nota or "").strip()[:255] or None, firma[:255]))
        return cur.fetchone()["id_liquidacion"]


def anular_pago(id_liquidacion: int) -> None:
    neon_db.ejecutar("UPDATE liquidacionessueldo SET estado = 'anulado' WHERE id_liquidacion = %s AND estado = 'pagado'",
                     (id_liquidacion,))
