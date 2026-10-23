# OLIMPOS GYM — Notificaciones del sistema de empleados
#
# Los avisos NO se cargan a mano: se calculan en el momento con los datos
# reales (membresías, marcas, accesos, ingresos al sistema...). Cada rol ve
# solo los tipos que le corresponden (TIPOS[..]["roles"]): la nutricionista
# no ve pagos ni intentos de acceso, seguridad no ve dietas, etc.
#
# Cada aviso tiene una "clave" estable (ej. "marca_pendiente:13"). Cuando un
# empleado lo marca como leído se guarda en la tabla "notificaciones" con su
# id_empleado: lo leído es de cada uno, y si el dato cambia (otra marca, un
# intento fallido más) la clave cambia y el aviso vuelve como nuevo.

from datetime import date, datetime, timedelta, timezone

import neon_db
import configuracion_repo

TODOS = {"dueno", "admin", "entrenador", "nutricionista", "seguridad", "recepcionista"}

# tipo → cómo se muestra, quién lo ve y a qué sección lleva "Ver"
TIPOS = {
    "membresia_vencida":    {"nombre": "Membresías vencidas", "icono": "EVENT_BUSY", "color": "rojo",
                             "roles": {"dueno", "admin", "recepcionista"}, "seccion": "membresias"},
    "membresia_por_vencer": {"nombre": "Membresías por vencer", "icono": "SCHEDULE", "color": "naranja",
                             "roles": {"dueno", "admin", "recepcionista"}, "seccion": "membresias"},
    "sin_membresia":        {"nombre": "Socios sin plan", "icono": "PERSON_OFF_OUTLINED", "color": "naranja",
                             "roles": {"dueno", "admin", "recepcionista"}, "seccion": "membresias"},
    "socio_nuevo":          {"nombre": "Socios nuevos", "icono": "PERSON_ADD_ALT", "color": "verde",
                             "roles": {"dueno", "admin", "recepcionista", "entrenador", "nutricionista"}, "seccion": "socios"},
    "pago_recibido":        {"nombre": "Pagos recibidos", "icono": "PAYMENTS_OUTLINED", "color": "verde",
                             "roles": {"dueno", "admin"}, "seccion": "pagos"},
    "contacto_web":         {"nombre": "Mensajes de la web", "icono": "MAIL_OUTLINE", "color": "azul",
                             "roles": {"dueno", "admin", "recepcionista"}, "seccion": None},
    "marca_pendiente":      {"nombre": "Marcas por verificar", "icono": "EMOJI_EVENTS_OUTLINED", "color": "acento",
                             "roles": {"dueno", "entrenador"}, "seccion": "verificacion-marcas"},
    "sin_rutina":           {"nombre": "Socios sin rutina", "icono": "FORMAT_LIST_BULLETED", "color": "azul",
                             "roles": {"dueno", "entrenador"}, "seccion": "rutinas"},
    "sin_dieta":            {"nombre": "Socios sin dieta", "icono": "RESTAURANT", "color": "verde",
                             "roles": {"dueno", "nutricionista"}, "seccion": "asignar-dietas"},
    "peso_registrado":      {"nombre": "Nuevos registros de peso", "icono": "MONITOR_WEIGHT_OUTLINED", "color": "azul",
                             "roles": {"dueno", "entrenador", "nutricionista"}, "seccion": "progreso"},
    "ocupacion_alta":       {"nombre": "Club casi lleno", "icono": "GROUPS_OUTLINED", "color": "rojo",
                             "roles": {"dueno", "seguridad", "recepcionista"}, "seccion": "asistencia"},
    "acceso_denegado":      {"nombre": "Accesos denegados", "icono": "DO_NOT_DISTURB_ON_OUTLINED", "color": "rojo",
                             "roles": {"dueno", "seguridad"}, "seccion": "asistencia"},
    "intentos_fallidos":    {"nombre": "Ingresos fallidos al sistema", "icono": "GPP_MAYBE_OUTLINED", "color": "rojo",
                             "roles": {"dueno", "seguridad"}, "seccion": None},
    "mi_cuenta":            {"nombre": "Seguridad de mi cuenta", "icono": "LOCK_OUTLINE", "color": "rojo",
                             "roles": TODOS, "seccion": None},
}


def tipos_de_rol(rol: str) -> list[str]:
    return [t for t, info in TIPOS.items() if rol in info["roles"]]


def _aviso(tipo, clave, titulo, detalle, fecha) -> dict:
    if isinstance(fecha, date) and not isinstance(fecha, datetime):
        fecha = datetime(fecha.year, fecha.month, fecha.day, tzinfo=timezone.utc)
    return {"tipo": tipo, "clave": f"{tipo}:{clave}", "titulo": titulo, "detalle": detalle, "fecha": fecha}


def _plural(n: int, uno: str, varios: str) -> str:
    return uno if n == 1 else varios


# ── un generador por tipo: devuelven la lista de avisos con datos reales ──
def _membresias(tipos, prefs, club):
    avisos = []
    hoy = date.today()
    dias = int(prefs.get("dias_aviso_vencimiento") or 7)
    filas = neon_db.consulta(
        "SELECT sm.id_socio_membresia, sm.fecha_vencimiento, m.nombre AS plan, trim(s.nombre || ' ' || s.apellido) AS socio"
        " FROM sociomembresia sm JOIN socios s USING (id_socio) JOIN membresias m USING (id_membresia)"
        " WHERE sm.estado = 'activa' AND s.estado = 'activo' AND sm.fecha_vencimiento <= %s",
        (hoy + timedelta(days=dias),))
    for f in filas:
        venc = f["fecha_vencimiento"]
        if venc < hoy and "membresia_vencida" in tipos:
            d = (hoy - venc).days
            avisos.append(_aviso("membresia_vencida", f["id_socio_membresia"], f"{f['socio']} tiene la membresía vencida",
                                 f"Plan {f['plan']} · venció hace {d} {_plural(d, 'día', 'días')} ({venc:%d/%m})", venc))
        elif venc >= hoy and "membresia_por_vencer" in tipos:
            d = (venc - hoy).days
            cuando = "hoy" if d == 0 else ("mañana" if d == 1 else f"en {d} días")
            avisos.append(_aviso("membresia_por_vencer", f"{f['id_socio_membresia']}:{venc}",
                                 f"La membresía de {f['socio']} vence {cuando}",
                                 f"Plan {f['plan']} · vence el {venc:%d/%m}", datetime.now(timezone.utc) - timedelta(minutes=d)))
    if "sin_membresia" in tipos:
        for f in neon_db.consulta(
                "SELECT s.id_socio, trim(s.nombre || ' ' || s.apellido) AS socio, s.fecha_registro FROM socios s"
                " WHERE s.estado = 'activo' AND NOT EXISTS (SELECT 1 FROM sociomembresia sm"
                "   WHERE sm.id_socio = s.id_socio AND sm.estado = 'activa')"):
            avisos.append(_aviso("sin_membresia", f["id_socio"], f"{f['socio']} no tiene un plan asignado",
                                 "Asignale una membresía para que pueda entrar al club", f["fecha_registro"]))
    return avisos


def _socios_nuevos(tipos, prefs, club):
    dias = int(club.get("dias_socio_nuevo") or 30)
    return [_aviso("socio_nuevo", f["id_socio"], f"Nuevo socio: {f['socio']}",
                   f"Se registró el {f['fecha_registro']:%d/%m}" + (f" · {f['nivel']}" if f["nivel"] else ""),
                   f["fecha_registro"])
            for f in neon_db.consulta(
                "SELECT id_socio, trim(nombre || ' ' || apellido) AS socio, fecha_registro, nivel_experiencia AS nivel"
                " FROM socios WHERE fecha_registro > now() - make_interval(days => %s) ORDER BY fecha_registro DESC",
                (dias,))]


def _pagos(tipos, prefs, club):
    return [_aviso("pago_recibido", f["id_pago"], f"{f['socio']} pagó ${f['monto']:,.0f}".replace(",", "."),
                   f"Plan {f['plan']}" + (f" · comprobante {f['numero_comprobante']}" if f["numero_comprobante"] else ""),
                   f["fecha_pago"])
            for f in neon_db.consulta(
                "SELECT p.id_pago, p.monto, p.fecha_pago, p.numero_comprobante, m.nombre AS plan,"
                " trim(s.nombre || ' ' || s.apellido) AS socio FROM pagos p JOIN socios s USING (id_socio)"
                " JOIN membresias m USING (id_membresia) WHERE p.fecha_pago > now() - interval '7 days'"
                " ORDER BY p.fecha_pago DESC")]


def _contactos(tipos, prefs, club):
    return [_aviso("contacto_web", f["id_contacto"], f"Mensaje de {f['nombre']} desde la página web",
                   ((f["mensaje"] or "").strip()[:90] or "(sin mensaje)") + f" · {f['email']}", f["fecha"])
            for f in neon_db.consulta("SELECT id_contacto, nombre, email, mensaje, fecha FROM contactosweb"
                                      " WHERE estado = 'nuevo' ORDER BY fecha DESC")]


def _marcas(tipos, prefs, club):
    return [_aviso("marca_pendiente", f["id_marca"], f"{f['socio']} cargó una marca para verificar",
                   f"{f['ejercicio']}: {f['peso']:g} kg x {f['repeticiones']}", f["fecha"])
            for f in neon_db.consulta(
                "SELECT mp.id_marca, mp.peso, mp.repeticiones, mp.fecha, e.nombre AS ejercicio,"
                " trim(s.nombre || ' ' || s.apellido) AS socio FROM marcaspersonales mp"
                " JOIN socios s USING (id_socio) JOIN ejerciciosmarca em ON em.id_ejercicio_marca = mp.id_ejercicio_marca"
                " JOIN ejercicios e ON e.id_ejercicio = em.id_ejercicio"
                " WHERE mp.estado NOT IN ('verificada', 'rechazada') AND s.firebase_uid IS NOT NULL ORDER BY mp.fecha DESC")]


def _sin_plan_de(tabla: str, tipo: str, que: str):
    def generar(tipos, prefs, club):
        return [_aviso(tipo, f["id_socio"], f"{f['socio']} no tiene {que}",
                       f"Socio activo desde el {f['fecha_registro']:%d/%m}", f["fecha_registro"])
                for f in neon_db.consulta(
                    f"SELECT s.id_socio, trim(s.nombre || ' ' || s.apellido) AS socio, s.fecha_registro FROM socios s"
                    f" WHERE s.estado = 'activo' AND NOT EXISTS (SELECT 1 FROM {tabla} x"
                    f"   WHERE x.id_socio = s.id_socio AND x.estado = 'vigente') ORDER BY s.fecha_registro DESC")]
    return generar


def _pesos(tipos, prefs, club):
    return [_aviso("peso_registrado", f["id_progreso_peso"], f"{f['socio']} registró su peso",
                   f"{f['peso']:g} kg" + (f" ({f['peso'] - f['anterior']:+g} kg)" if f["anterior"] is not None else ""),
                   f["fecha"])
            for f in neon_db.consulta(
                "SELECT pp.id_progreso_peso, pp.peso, pp.fecha, trim(s.nombre || ' ' || s.apellido) AS socio,"
                " (SELECT p2.peso FROM progresopeso p2 WHERE p2.id_socio = pp.id_socio AND p2.fecha < pp.fecha"
                "  ORDER BY p2.fecha DESC LIMIT 1) AS anterior"
                " FROM progresopeso pp JOIN socios s USING (id_socio)"
                " WHERE pp.fecha > current_date - 7 ORDER BY pp.fecha DESC")]


def _ocupacion(tipos, prefs, club):
    import ocupacion_repo
    personas = ocupacion_repo.obtener_ocupacion()["personas"]
    capacidad = int(club.get("capacidad_maxima") or 120)
    limite = int(club.get("porcentaje_lleno") or 80)
    porcentaje = round(personas * 100 / capacidad) if capacidad else 0
    if porcentaje < limite:
        return []
    hora = datetime.now().strftime("%Y-%m-%dT%H")   # como mucho un aviso por hora
    return [_aviso("ocupacion_alta", hora, f"El club está al {porcentaje}% de su capacidad",
                   f"{personas} de {capacidad} personas adentro (avisa desde el {limite}%)", datetime.now(timezone.utc))]


def _accesos_denegados(tipos, prefs, club):
    return [_aviso("acceso_denegado", f["id_acceso"], f"Se le negó la entrada a {f['socio']}",
                   f"{f['resultado'].capitalize()} · {f['metodo']}" + (f" · {f['dispositivo']}" if f["dispositivo"] else ""),
                   f["fecha"])
            for f in neon_db.consulta(
                "SELECT a.id_acceso, a.fecha, a.metodo, a.resultado, a.dispositivo, trim(s.nombre || ' ' || s.apellido) AS socio"
                " FROM accesos a JOIN socios s USING (id_socio)"
                " WHERE a.resultado <> 'permitido' AND a.fecha > now() - interval '2 days' ORDER BY a.fecha DESC")]


def _intentos(tipos, prefs, club, id_empleado):
    avisos = []
    # agrupados por día: uno solo aunque haya muchos intentos
    if "intentos_fallidos" in tipos:
        for f in neon_db.consulta(
                "SELECT (fecha AT TIME ZONE 'America/Argentina/Buenos_Aires')::date AS dia, count(*) AS n,"
                " max(fecha) AS ultimo, string_agg(DISTINCT COALESCE(motivo, ''), ', ') AS motivos"
                " FROM intentosacceso WHERE tipo_usuario = 'empleado' AND resultado = 'fallido'"
                " AND fecha > now() - interval '7 days' GROUP BY 1 ORDER BY 1 DESC"):
            n = f["n"]
            avisos.append(_aviso("intentos_fallidos", f"{f['dia']}:{n}",
                                 f"{n} {_plural(n, 'intento fallido', 'intentos fallidos')} de entrar al sistema",
                                 f"{f['dia']:%d/%m} · {(f['motivos'] or '').strip(', ')[:100]}", f["ultimo"]))
    if "mi_cuenta" in tipos and id_empleado:
        f = neon_db.una_fila(
            "SELECT count(*) AS n, max(fecha) AS ultimo FROM intentosacceso"
            " WHERE id_empleado = %s AND resultado = 'fallido' AND fecha > now() - interval '7 days'", (id_empleado,))
        if f and f["n"]:
            n = f["n"]
            avisos.append(_aviso("mi_cuenta", f"{id_empleado}:{f['ultimo']:%Y%m%d%H%M%S}",
                                 f"Alguien escribió mal tu contraseña {n} {_plural(n, 'vez', 'veces')}",
                                 f"El último intento fue el {f['ultimo'].astimezone():%d/%m a las %H:%M}. "
                                 "Si no fuiste vos, avisale al dueño.", f["ultimo"]))
    return avisos


_GENERADORES = [
    ({"membresia_vencida", "membresia_por_vencer", "sin_membresia"}, _membresias),
    ({"socio_nuevo"}, _socios_nuevos),
    ({"pago_recibido"}, _pagos),
    ({"contacto_web"}, _contactos),
    ({"marca_pendiente"}, _marcas),
    ({"sin_rutina"}, _sin_plan_de("rutinas", "sin_rutina", "una rutina asignada")),
    ({"sin_dieta"}, _sin_plan_de("dietas", "sin_dieta", "una dieta asignada")),
    ({"peso_registrado"}, _pesos),
    ({"ocupacion_alta"}, _ocupacion),
    ({"acceso_denegado"}, _accesos_denegados),
]


def avisos_de(rol: str, id_empleado: int | None) -> list[dict]:
    """Los avisos que le tocan a este empleado (según su rol y los tipos que
    no apagó en Configuración), el más reciente primero, con "leido"."""
    prefs = configuracion_repo.preferencias()
    club = configuracion_repo.club()
    tipos = set(tipos_de_rol(rol)) - set(prefs.get("avisos_apagados") or [])
    avisos = []
    for de_tipo, generar in _GENERADORES:
        if de_tipo & tipos:
            try:
                avisos += generar(tipos, prefs, club)
            except Exception:
                neon_db._conexion = None   # una consulta que falla no deja sin los demás avisos
    if {"intentos_fallidos", "mi_cuenta"} & tipos:
        try:
            avisos += _intentos(tipos, prefs, club, id_empleado)
        except Exception:
            neon_db._conexion = None
    avisos = [a for a in avisos if a["tipo"] in tipos]
    leidos = leidas(id_empleado)
    for a in avisos:
        a["leido"] = a["clave"] in leidos
    avisos.sort(key=lambda a: a["fecha"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return avisos


def sin_leer(rol: str, id_empleado: int | None) -> int:
    try:
        return sum(1 for a in avisos_de(rol, id_empleado) if not a["leido"])
    except Exception:
        return 0


def leidas(id_empleado: int | None) -> set[str]:
    if not id_empleado:
        return set()
    return {f["clave"] for f in neon_db.consulta(
        "SELECT clave FROM notificaciones WHERE id_empleado = %s AND clave IS NOT NULL", (id_empleado,))}


def marcar_leidas(id_empleado: int, avisos: list[dict]) -> None:
    if not avisos:
        return
    with neon_db.transaccion() as cur:
        for a in avisos:
            cur.execute(
                "INSERT INTO notificaciones (id_empleado, tipo, mensaje, fecha, estado, clave)"
                " VALUES (%s, %s, %s, now(), 'leida', %s) ON CONFLICT (id_empleado, clave) DO NOTHING",
                (id_empleado, a["tipo"], a["titulo"][:255], a["clave"][:120]))


def marcar_no_leida(id_empleado: int, aviso: dict) -> None:
    neon_db.ejecutar("DELETE FROM notificaciones WHERE id_empleado = %s AND clave = %s", (id_empleado, aviso["clave"]))
