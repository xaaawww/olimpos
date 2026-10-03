"""
OLIMPOS GYM - Migracion de datos: Firestore -> PostgreSQL (Neon)

Uso:
    python neon/migrar_firestore_a_neon.py [--url postgresql://...] [--limpiar]

  --url      cadena de conexion. Si se omite, se lee de
             Aplicaciones/olimpos_gym/neon_credentials.json  {"database_url": "..."}
  --limpiar  vacia primero los datos migrados (no los catalogos iniciales) para
             poder repetir la migracion sin duplicar nada.

Antes hay que haber aplicado neon/esquema.sql en la base de destino.

Las claves foraneas dejan al descubierto datos inconsistentes que Firestore
aceptaba sin chistar (filas de cuentas de prueba ya borradas, valores fuera de
catalogo...). Esas filas NO se migran y quedan listadas en el reporte final.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone

import firebase_admin
import psycopg
from firebase_admin import credentials, firestore

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_EMPLEADOS = os.path.join(RAIZ, "Aplicaciones", "olimpos_gym")
sys.path.insert(0, CARPETA_EMPLEADOS)
sys.stdout.reconfigure(encoding="utf-8")

import neon_db  # noqa: E402  (hash de contraseñas)
from theme import ROLES  # noqa: E402

# Los 6 usuarios que antes estaban escritos a mano en empleados_credenciales.py:
# se cargan una sola vez en la tabla "empleados" (con la contraseña cifrada).
CREDENCIALES = {
    "cgarcia":    {"password": "Garcia2026",    "role": "dueno"},
    "sramirez":   {"password": "Ramirez2026",   "role": "admin"},
    "crodriguez": {"password": "Rodriguez2026", "role": "entrenador"},
    "svillar":    {"password": "Villar2026",    "role": "nutricionista"},
    "rflores":    {"password": "Flores2026",    "role": "seguridad"},
    "pacosta":    {"password": "Acosta2026",    "role": "recepcionista"},
}

HORARIOS = ("desayuno", "almuerzo", "cena")
AHORA = lambda: datetime.now(timezone.utc)  # noqa: E731


class Reporte:
    def __init__(self):
        self.insertadas: dict[str, int] = {}
        self.descartadas: list[str] = []

    def ok(self, tabla: str, n: int = 1):
        self.insertadas[tabla] = self.insertadas.get(tabla, 0) + n

    def descarta(self, tabla: str, motivo: str):
        self.descartadas.append(f"{tabla}: {motivo}")


def ms(valor) -> datetime | None:
    if valor in (None, ""):
        return None
    return datetime.fromtimestamp(float(valor) / 1000, tz=timezone.utc)


def iso(valor) -> datetime | None:
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)
    try:
        d = datetime.fromisoformat(str(valor))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def fecha(valor) -> date | None:
    if not valor:
        return None
    try:
        return datetime.strptime(str(valor).replace("-", "")[:8], "%Y%m%d").date()
    except ValueError:
        return None


def semana_de(ts_ms) -> str:
    anio, semana, _ = (ms(ts_ms) or AHORA()).isocalendar()
    return f"{anio}-W{semana}"


def vacio_a_none(v):
    return None if v in (None, "") else v


def normalizar(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()


def dividir_nombre(completo: str) -> tuple[str, str]:
    partes = (completo or "").split()
    if len(partes) <= 1:
        return (partes[0] if partes else "-"), ""
    return " ".join(partes[:-1]), partes[-1]


def leer(db, coleccion):
    return [(d.id, d.to_dict()) for d in db.collection(coleccion).stream()]


def migrar(db, cx: psycopg.Connection, rep: Reporte):
    cur = cx.cursor()

    def uno(sql, params=()):
        cur.execute(sql, params)
        r = cur.fetchone()
        return r[0] if r else None

    # ===================== EMPLEADOS (antes fijos en el codigo) =====================
    rol_id = dict((n, i) for i, n in (cur.execute("SELECT id_rol, nombre FROM rol") or cur).fetchall())
    empleados = []  # (id_empleado, nombre_normalizado, rol)
    por_rol = {}
    for usuario, cuenta in CREDENCIALES.items():
        nombre_completo = ROLES[cuenta["role"]]["name"]
        nombre, apellido = dividir_nombre(nombre_completo)
        eid = uno(
            "INSERT INTO empleados (usuario, nombre, apellido, rol, email, contraseña, estado, fecha_ingreso)"
            " VALUES (%s,%s,%s,%s,%s,%s,'activo',%s) RETURNING id_empleado",
            (usuario, nombre, apellido, rol_id[cuenta["role"]], f"{usuario}@olimpos.com",
             neon_db.hash_password(cuenta["password"]), AHORA()),
        )
        empleados.append((eid, normalizar(nombre_completo), cuenta["role"]))
        por_rol[cuenta["role"]] = eid
        rep.ok("empleados")

    def empleado_de(texto: str) -> int:
        """Empleado al que se refiere un texto como 'Carlos García — Dueño' (si no, el dueño)."""
        t = normalizar(texto)
        for eid, nombre, _ in empleados:
            if nombre and nombre in t:
                return eid
        for palabra, rol in (("entrenador", "entrenador"), ("nutricionista", "nutricionista"), ("admin", "admin"),
                             ("dueno", "dueno"), ("recepcion", "recepcionista"), ("seguridad", "seguridad")):
            if palabra in t:
                return por_rol[rol]
        return por_rol["dueno"]

    dueno = por_rol["dueno"]

    # ===================== SOCIOS =====================
    dnis = {i: d.get("dni") for i, d in leer(db, "socios_privado")}
    socio = {}  # firebase_uid -> id_socio
    for uid, d in leer(db, "socios_app"):
        uid = d.get("uid") or uid
        nombre, apellido = dividir_nombre(d.get("nombre", ""))
        dni = vacio_a_none(dnis.get(uid))
        if dni is not None and not re.fullmatch(r"[0-9]{6,10}", str(dni)):
            rep.descarta("socios", f"DNI no numerico ({dni}) de {d.get('nombre')}: queda sin DNI")
            dni = None
        id_socio = uno(
            "INSERT INTO socios (firebase_uid, dni, nombre, apellido, email, estado, fecha_registro)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id_socio",
            (uid, dni, nombre, apellido, d.get("email", ""), "activo" if d.get("activo", True) else "inactivo",
             ms(d.get("creado_ms")) or AHORA()),
        )
        socio[uid] = id_socio
        cur.execute("INSERT INTO perfilapp (id_socio, debe_cambiar_password) VALUES (%s,%s)",
                    (id_socio, d.get("debe_cambiar_password", False)))
        rep.ok("socios")
        rep.ok("perfilapp")
    for uid in set(dnis) - set(socio):
        rep.descarta("socios_privado", f"DNI de una cuenta que ya no existe ({uid[:8]}...)")

    # ===================== DATOS FISICOS -> socios + perfilapp + progresopeso + objetivos + salud =====================
    peso_actual = {}
    for uid, d in leer(db, "datos_fisicos"):
        if uid not in socio:
            rep.descarta("datos_fisicos", f"socio inexistente ({uid[:8]}...)")
            continue
        sid = socio[uid]
        sexo = d.get("sexo") if d.get("sexo") in ("MASCULINO", "FEMENINO", "PREFIERO_NO_DECIRLO") else None
        nivel = d.get("experiencia") if d.get("experiencia") in ("Principiante", "Intermedio", "Avanzado") else None
        cur.execute("UPDATE socios SET sexo=%s, nivel_experiencia=%s WHERE id_socio=%s", (sexo, nivel, sid))
        f = ms(d.get("actualizado_ms")) or AHORA()
        cur.execute(
            "UPDATE perfilapp SET edad=%s, oculto_clasificacion=%s, vio_plano=%s, vistas_bodygraph=%s, fecha_actualizacion=%s"
            " WHERE id_socio=%s",
            (d.get("edad"), d.get("oculto_clasificacion", False), d.get("vio_plano", False),
             d.get("vistas_bodygraph", 0), f, sid),
        )
        if d.get("peso_kg"):
            peso_actual[sid] = float(d["peso_kg"])
            cur.execute("INSERT INTO progresopeso (id_socio, fecha, peso) VALUES (%s,%s,%s)", (sid, f.date(), d["peso_kg"]))
            rep.ok("progresopeso")
        if d.get("objetivo") in ("FUERZA", "HIPERTROFIA", "SALUD"):
            cur.execute("INSERT INTO objetivos (id_socio, tipo, prioridad, fecha_registro, estado)"
                        " VALUES (%s,%s,'principal',%s,'activo')", (sid, d["objetivo"], f))
            rep.ok("objetivos")
        if vacio_a_none(d.get("condicion_medica")):
            cur.execute("INSERT INTO salud (id_socio, fecha, observaciones) VALUES (%s,%s,%s)",
                        (sid, f, d["condicion_medica"]))
            rep.ok("salud")
        for sec in dict.fromkeys(d.get("secciones_arena_visitadas", [])):
            cur.execute("INSERT INTO perfilappsecciones (id_socio, seccion) VALUES (%s,%s)", (sid, sec))
            rep.ok("perfilappsecciones")
        rep.ok("datos_fisicos (repartidos en 6 tablas)")

    # ===================== MEMBRESIAS Y PAGOS =====================
    planes = {n: (i, dias) for i, n, dias in (cur.execute("SELECT id_membresia, nombre, duracion_dias FROM membresias") or cur).fetchall()}
    for uid, d in leer(db, "membresias"):
        if uid not in socio or d.get("plan") not in planes:
            rep.descarta("sociomembresia", f"socio o plan invalido ({uid[:8]}..., {d.get('plan')})")
            continue
        inicio = (ms(d.get("fecha_inicio_ms")) or AHORA()).date()
        idm, dias = planes[d["plan"]]
        cur.execute(
            "INSERT INTO sociomembresia (id_socio, id_membresia, fecha_inicio, fecha_vencimiento, estado, asignado_por)"
            " VALUES (%s,%s,%s,%s,'activa',%s)",
            (socio[uid], idm, inicio, inicio + timedelta(days=dias), d.get("asignado_por", "")),
        )
        rep.ok("sociomembresia")
    plan_pago = uno("SELECT id_plan_pago FROM planespago WHERE nombre='Pago único'")
    for pid, d in leer(db, "pagos_socios"):
        uid = d.get("socio_id")
        if uid not in socio or d.get("plan") not in planes:
            rep.descarta("pagos", f"socio o plan invalido ({pid})")
            continue
        cur.execute("INSERT INTO mediospago (id_socio, tipo, proveedor, estado) VALUES (%s,'Mercado Pago','Mercado Pago','activo')"
                    " ON CONFLICT (id_socio, tipo, proveedor) DO NOTHING", (socio[uid],))
        medio = uno("SELECT id_medio_pago FROM mediospago WHERE id_socio=%s AND tipo='Mercado Pago'", (socio[uid],))
        pagado = ms(d.get("fecha_ms")) or AHORA()
        idm, dias = planes[d["plan"]]
        cur.execute(
            "INSERT INTO pagos (id_socio, id_membresia, id_plan_pago, id_medio_pago, monto, fecha_pago, fecha_vencimiento,"
            " numero_comprobante, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (socio[uid], idm, plan_pago, medio, d.get("monto", 1), pagado, (pagado + timedelta(days=dias)).date(),
             d.get("mp_payment_id") or pid, d.get("estado", "Aprobado")),
        )
        rep.ok("pagos")

    # ===================== PERFIL NUTRICIONAL =====================
    for uid, d in leer(db, "perfiles_nutricionales"):
        if uid not in socio:
            rep.descarta("perfiles_nutricionales", f"socio inexistente ({uid[:8]}...)")
            continue
        for p in dict.fromkeys(d.get("preferencias", [])):
            cur.execute("INSERT INTO preferenciasalimentarias (id_socio, tipo) VALUES (%s,%s)", (socio[uid], p))
            rep.ok("preferenciasalimentarias")
        for a in dict.fromkeys(d.get("excluidos", [])):
            cur.execute("INSERT INTO alimentosexcluidos (id_socio, alimento) VALUES (%s,%s)", (socio[uid], a))
            rep.ok("alimentosexcluidos")

    # ===================== CATALOGO DE EJERCICIOS =====================
    zonas = {r[0]: r[1] for r in (cur.execute("SELECT zona, etiqueta FROM zonasmusculares") or cur).fetchall()}
    ejercicio = {}  # slug de Firestore -> id_ejercicio
    for slug, d in leer(db, "ejercicios"):
        slug = d.get("id") or slug
        puntos_ok = [p for p in d.get("puntos", []) if p.get("zona") in zonas]
        musculos = ", ".join(dict.fromkeys(zonas[p["zona"]] for p in puntos_ok))[:255]
        eid = uno(
            "INSERT INTO ejercicios (nombre, descripcion, musculos_trabajados, estado, fecha_actualizacion)"
            " VALUES (%s,%s,%s,%s,%s) RETURNING id_ejercicio",
            (d.get("nombre", slug), (d.get("descripcion") or "")[:255], musculos or None,
             "publicado" if d.get("publicado") else "borrador", iso(d.get("actualizado")) or AHORA()),
        )
        ejercicio[slug] = eid
        rep.ok("ejercicios")
        for i, t in enumerate(dict.fromkeys(d.get("tags", []))):
            cur.execute("INSERT INTO ejercicioetiquetas (id_ejercicio, etiqueta, orden) VALUES (%s,%s,%s)", (eid, t, i))
            rep.ok("ejercicioetiquetas")
        vistos = set()
        for i, p in enumerate(d.get("puntos", [])):
            pid = p.get("id") or f"p{i}"
            if pid in vistos or p.get("zona") not in zonas:
                rep.descarta("ejerciciopuntos", f"punto repetido o zona invalida ({slug}/{pid})")
                continue
            vistos.add(pid)
            cur.execute("INSERT INTO ejerciciopuntos (id_ejercicio, punto_id, zona, nombre, descripcion, orden)"
                        " VALUES (%s,%s,%s,%s,%s,%s)",
                        (eid, pid, p["zona"], p.get("nombre", ""), p.get("descripcion", ""), i))
            rep.ok("ejerciciopuntos")
            for j, t in enumerate(dict.fromkeys(p.get("tags", []))):
                cur.execute("INSERT INTO puntoetiquetas (id_ejercicio, punto_id, etiqueta, orden) VALUES (%s,%s,%s,%s)",
                            (eid, pid, t, j))
                rep.ok("puntoetiquetas")

    # ===================== PLATOS =====================
    plato = {}  # slug -> id_plato
    for slug, d in leer(db, "dietas"):
        slug = d.get("id") or slug
        m = d.get("macros") or {}
        pid = uno(
            "INSERT INTO platos (nombre, descripcion, imagen, imagen_generada_ia, estado, kcal, proteinas, carbs, grasas,"
            " crop_x, crop_y, fecha_actualizacion) VALUES (%s,%s,%s,FALSE,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_plato",
            (d.get("nombre", slug), (d.get("descripcion") or "")[:255], vacio_a_none(d.get("imagen")),
             "publicado" if d.get("publicado") else "borrador", m.get("kcal"), m.get("proteinas"), m.get("carbs"),
             m.get("grasas"), d.get("crop_x"), d.get("crop_y"), iso(d.get("actualizado")) or AHORA()),
        )
        plato[slug] = pid
        rep.ok("platos")
        for i, t in enumerate(dict.fromkeys(d.get("tags", []))):
            cur.execute("INSERT INTO platoetiquetas (id_plato, etiqueta, orden) VALUES (%s,%s,%s)", (pid, t, i))
            rep.ok("platoetiquetas")
        vistos = set()
        for i, p in enumerate(d.get("puntos", [])):
            iid = p.get("id") or f"i{i}"
            if iid in vistos:
                iid = f"{iid}_{i}"
            vistos.add(iid)
            cur.execute(
                "INSERT INTO platoingredientes (id_plato, ingrediente_id, nombre, categoria, aporte, kcal_texto, x, y, orden)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (pid, iid, p.get("nombre", ""), p.get("categoria", "Proteína"), (p.get("aporte") or "")[:500],
                 p.get("kcal", ""), p.get("x"), p.get("y"), i),
            )
            rep.ok("platoingredientes")
            for j, t in enumerate(dict.fromkeys(p.get("tags", []))):
                cur.execute("INSERT INTO ingredienteetiquetas (id_plato, ingrediente_id, etiqueta, orden) VALUES (%s,%s,%s,%s)",
                            (pid, iid, t, j))
                rep.ok("ingredienteetiquetas")
            for j, b in enumerate(dict.fromkeys(p.get("beneficios", []))):
                cur.execute("INSERT INTO ingredientebeneficios (id_plato, ingrediente_id, beneficio, orden) VALUES (%s,%s,%s,%s)",
                            (pid, iid, b[:500], j))
                rep.ok("ingredientebeneficios")

    # ===================== TABLON =====================
    for _, d in leer(db, "tablon"):
        cur.execute(
            "INSERT INTO tablonpublicaciones (titulo, mensaje, categoria, autor, fijado, publicado, fecha_creacion,"
            " fecha_actualizacion) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (d.get("titulo", ""), d.get("mensaje", ""), d.get("categoria", "Aviso"), d.get("autor", ""),
             d.get("fijado", False), d.get("publicado", False), ms(d.get("creado_ms")) or AHORA(),
             ms(d.get("actualizado_ms")) or AHORA()),
        )
        rep.ok("tablonpublicaciones")

    # ===================== DIETA ASIGNADA: dietas -> planalimentario -> planplato =====================
    for uid, d in leer(db, "dietas_asignadas"):
        if uid not in socio:
            rep.descarta("dietas", f"socio inexistente ({uid[:8]}...)")
            continue
        f = iso(d.get("actualizado")) or AHORA()
        cod = uno(
            "INSERT INTO dietas (id_socio, id_empleado, nombre, fecha_creacion, fecha_actualizacion, estado)"
            " VALUES (%s,%s,'Dieta asignada',%s,%s,'vigente') RETURNING cod_dieta",
            (socio[uid], empleado_de(d.get("asignada_por", "")), f, f),
        )
        plan = uno("INSERT INTO planalimentario (cod_dieta, nombre, fecha_inicio, estado) VALUES (%s,'Plan diario',%s,'vigente')"
                   " RETURNING id_plan_alimentario", (cod, f.date()))
        rep.ok("dietas")
        rep.ok("planalimentario")
        for momento, lista in (d.get("comidas") or {}).items():
            if momento not in HORARIOS:
                continue
            for i, slug in enumerate(dict.fromkeys(lista)):
                if slug not in plato:
                    rep.descarta("planplato", f"plato inexistente: {slug}")
                    continue
                cur.execute("INSERT INTO planplato (id_plan_alimentario, id_plato, momento, orden) VALUES (%s,%s,%s,%s)",
                            (plan, plato[slug], momento, i))
                rep.ok("planplato")

    # ===================== PLATOS PROBADOS / AGUA =====================
    for _id, d in leer(db, "platos_probados"):
        if d.get("socio_id") not in socio or d.get("plato_id") not in plato:
            rep.descarta("platosprobados", f"socio o plato inexistente ({_id[:20]})")
            continue
        cur.execute("INSERT INTO platosprobados (id_socio, id_plato, fecha_probado) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                    (socio[d["socio_id"]], plato[d["plato_id"]], ms(d.get("timestamp")) or AHORA()))
        rep.ok("platosprobados")
    for _id, d in leer(db, "registros_agua"):
        if d.get("socio_id") not in socio:
            rep.descarta("registroagua", "socio inexistente")
            continue
        cur.execute("INSERT INTO registroagua (id_socio, fecha) VALUES (%s,%s)",
                    (socio[d["socio_id"]], ms(d.get("timestamp")) or AHORA()))
        rep.ok("registroagua")

    # ===================== COMIDAS REGISTRADAS =====================
    for _id, d in leer(db, "comidas_dia"):
        uid, f = d.get("socio_id"), fecha(d.get("fecha"))
        if uid not in socio or f is None:
            rep.descarta("comidasdia", f"socio inexistente o fecha invalida ({_id[:24]})")
            continue
        obj = d.get("objetivo") if d.get("objetivo") in ("FUERZA", "HIPERTROFIA", "SALUD") else None
        meta = d.get("meta") or {}
        cur.execute("INSERT INTO comidasdia (id_socio, fecha, objetivo, meta_kcal, meta_proteinas, meta_carbs, meta_grasas,"
                    " fecha_actualizacion) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (socio[uid], f, obj, meta.get("kcal"), meta.get("proteinas"), meta.get("carbs"), meta.get("grasas"),
                     ms(d.get("actualizado_ms")) or AHORA()))
        rep.ok("comidasdia")
        for mom in dict.fromkeys(meta.get("momentos", [])):
            if mom in HORARIOS:
                cur.execute("INSERT INTO comidasdiametamomentos (id_socio, fecha, momento) VALUES (%s,%s,%s)", (socio[uid], f, mom))
                rep.ok("comidasdiametamomentos")
        for momento, c in (d.get("comidas") or {}).items():
            if momento not in HORARIOS:
                continue
            cur.execute(
                "INSERT INTO comidasregistradas (id_socio, fecha, momento, hora, kcal, proteinas, carbs, grasas, nota)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (socio[uid], f, momento, ms(c.get("hora_ms")) or AHORA(), c.get("kcal", 0), c.get("proteinas", 0),
                 c.get("carbs", 0), c.get("grasas", 0), c.get("nota", "")),
            )
            rep.ok("comidasregistradas")
            for slug in dict.fromkeys(c.get("plato_ids", [])):
                if slug in plato:
                    cur.execute("INSERT INTO comidaregistradaplatos (id_socio, fecha, momento, id_plato) VALUES (%s,%s,%s,%s)",
                                (socio[uid], f, momento, plato[slug]))
                    rep.ok("comidaregistradaplatos")
                else:
                    rep.descarta("comidaregistradaplatos", f"plato inexistente: {slug}")
    for _id, d in leer(db, "fotos_comidas"):
        f = fecha(d.get("fecha"))
        if d.get("socio_id") not in socio or f is None or d.get("momento") not in HORARIOS:
            rep.descarta("fotoscomidas", f"socio/fecha/momento invalido ({_id[:24]})")
            continue
        cur.execute("INSERT INTO fotoscomidas (id_socio, fecha, momento, imagen, fecha_foto) VALUES (%s,%s,%s,%s,%s)"
                    " ON CONFLICT DO NOTHING",
                    (socio[d["socio_id"]], f, d["momento"], d.get("imagen", ""), ms(d.get("timestamp")) or AHORA()))
        rep.ok("fotoscomidas")

    # ===================== ARENA: marcas personales =====================
    marca_de = {n: i for i, n in (cur.execute(
        "SELECT em.id_ejercicio_marca, e.nombre FROM ejerciciosmarca em JOIN ejercicios e USING (id_ejercicio)") or cur).fetchall()}
    for _id, d in leer(db, "marcas"):
        uid = d.get("socio_id")
        if uid not in socio:
            rep.descarta("marcaspersonales", f"socio inexistente ({uid})")
            continue
        if d.get("ejercicio") not in marca_de:
            rep.descarta("marcaspersonales", f"ejercicio fuera de catalogo: {d.get('ejercicio')}")
            continue
        ts = ms(d.get("timestamp")) or AHORA()
        peso, reps = float(d.get("peso", 0)), max(1, int(d.get("repeticiones", 1)))
        verificada = bool(d.get("verificado"))
        cur.execute(
            "INSERT INTO marcaspersonales (id_socio, id_ejercicio_marca, peso, repeticiones, uno_rm_estimado, peso_corporal,"
            " fecha, estado, id_empleado_verificador, fecha_verificacion, verificado_por)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (socio[uid], marca_de[d["ejercicio"]], peso, reps, round(peso * (1 + reps / 30), 2), peso_actual.get(socio[uid]),
             ts, "verificada" if verificada else "pendiente",
             empleado_de(d.get("verificado_por", "")) if verificada else None, ts if verificada else None,
             d.get("verificado_por") if verificada else None),
        )
        rep.ok("marcaspersonales")

    # ===================== SERIES DE ENTRENAMIENTO =====================
    series = []
    for _id, d in leer(db, "series_entrenamiento"):
        if d.get("socio_id") not in socio:
            rep.descarta("seriesentrenamiento", "socio inexistente")
            continue
        series.append(d)
    series.sort(key=lambda d: d.get("timestamp", 0))
    contador = {}
    for d in series:
        ts = ms(d.get("timestamp")) or AHORA()
        clave = (d["socio_id"], d.get("ejercicio", ""), ts.date())
        contador[clave] = contador.get(clave, 0) + 1
        cur.execute(
            "INSERT INTO seriesentrenamiento (id_socio, ejercicio, numero_serie, peso, repeticiones, es_peso_corporal, fecha)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (socio[d["socio_id"]], d.get("ejercicio", ""), contador[clave], d.get("peso", 0),
             max(1, int(d.get("repeticiones", 1))), d.get("es_peso_corporal", False), ts),
        )
        rep.ok("seriesentrenamiento")

    # ===================== RUTINAS =====================
    activa_de, entrenador_de = set(), set()
    for _id, d in leer(db, "rutinas_asignadas"):
        uid = d.get("socio_id")
        if uid not in socio:
            rep.descarta("rutinas", f"socio inexistente ({uid})")
            continue
        origen = d.get("origen", "entrenador")
        activa = bool(d.get("activa", True))
        if activa and uid in activa_de:
            activa = False
            rep.descarta("rutinas", f"{uid[:8]}... tenia 2 rutinas activas; se dejo una sola")
        if origen == "entrenador" and uid in entrenador_de:
            rep.descarta("rutinas", f"{uid[:8]}... tenia 2 rutinas del entrenador; se migro solo la primera")
            continue
        if activa:
            activa_de.add(uid)
        if origen == "entrenador":
            entrenador_de.add(uid)
        f = iso(d.get("actualizado")) or AHORA()
        cod = uno(
            "INSERT INTO rutinas (id_socio, id_empleado, nombre, fecha_creacion, fecha_actualizacion, estado, origen, activa,"
            " creada_por) VALUES (%s,%s,%s,%s,%s,'vigente',%s,%s,%s) RETURNING cod_rutina",
            (socio[uid], empleado_de(d.get("creada_por", "")) if origen == "entrenador" else None, d.get("nombre", "Rutina"),
             f, f, origen, activa, d.get("creada_por", "")),
        )
        rep.ok("rutinas")
        for pos, e in enumerate(d.get("ejercicios", [])):
            eid = ejercicio.get(e.get("ejercicio_id"))
            if e.get("ejercicio_id") and eid is None:
                rep.descarta("rutinaejercicio", f"ejercicio_id inexistente ({e.get('ejercicio_id')}); queda escrito a mano")
            cur.execute(
                "INSERT INTO rutinaejercicio (cod_rutina, id_ejercicio, orden, nombre, series, peso, es_peso_corporal)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (cod, eid, pos, e.get("nombre", ""), max(1, int(e.get("series_objetivo", 3))), e.get("peso_base_kg", 0),
                 e.get("es_peso_corporal", False)),
            )
            rep.ok("rutinaejercicio")

    # ===================== CLASES, ACCESOS, LOCKERS, COMPAÑEROS, FOTOS =====================
    clase = {c: i for i, c in (cur.execute("SELECT id_clase, codigo FROM clases") or cur).fetchall()}
    for _id, d in leer(db, "reservas_clase"):
        if d.get("socio_id") not in socio or d.get("clase_id") not in clase:
            rep.descarta("reservasclase", f"socio o clase inexistente ({_id[:20]})")
            continue
        cur.execute(
            "INSERT INTO reservasclase (id_clase, id_socio, fecha_reserva, estado, semana) VALUES (%s,%s,%s,'confirmada',%s)"
            " ON CONFLICT DO NOTHING",
            (clase[d["clase_id"]], socio[d["socio_id"]], ms(d.get("timestamp")) or AHORA(),
             d.get("semana") or semana_de(d.get("timestamp"))),
        )
        rep.ok("reservasclase")
    for _id, d in leer(db, "ingresos"):
        if d.get("socio_id") not in socio:
            rep.descarta("accesos", "socio inexistente")
            continue
        metodo = d.get("metodo") if d.get("metodo") in ("qr", "biometrico", "manual") else "manual"
        cur.execute("INSERT INTO accesos (id_socio, fecha, metodo, resultado) VALUES (%s,%s,%s,'permitido')",
                    (socio[d["socio_id"]], ms(d.get("timestamp")) or AHORA(), metodo))
        rep.ok("accesos")
    locker = {n: i for i, n in (cur.execute("SELECT id_locker, numero FROM lockers") or cur).fetchall()}
    for uid_doc, d in leer(db, "lockers"):
        uid, num = d.get("socio_id") or uid_doc, str(d.get("numero"))
        if uid not in socio or num not in locker:
            rep.descarta("reservaslocker", f"socio inexistente o locker invalido ({num})")
            continue
        try:
            cur.execute("SAVEPOINT sp")
            cur.execute("INSERT INTO reservaslocker (id_locker, id_socio, fecha_inicio, estado) VALUES (%s,%s,%s,'activa')",
                        (locker[num], socio[uid], ms(d.get("timestamp")) or AHORA()))
            rep.ok("reservaslocker")
        except psycopg.errors.UniqueViolation:
            cur.execute("ROLLBACK TO SAVEPOINT sp")
            rep.descarta("reservaslocker", f"locker {num} ya estaba ocupado por otro socio")
    for _id, d in leer(db, "companeros"):
        a, b = d.get("socio_id"), d.get("companero_id")
        if a not in socio or b not in socio or a == b:
            rep.descarta("companeros", f"socio inexistente o autocompañero ({_id[:20]})")
            continue
        cur.execute("INSERT INTO companeros (id_socio, id_companero, fecha_agregado) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                    (socio[a], socio[b], ms(d.get("timestamp")) or AHORA()))
        rep.ok("companeros")
    for _id, d in leer(db, "fotos_progreso"):
        if d.get("socio_id") not in socio:
            rep.descarta("fotosprogreso", "socio inexistente")
            continue
        cur.execute("INSERT INTO fotosprogreso (id_socio, fecha, imagen) VALUES (%s,%s,%s)",
                    (socio[d["socio_id"]], ms(d.get("timestamp")) or AHORA(), d.get("imagen", "")))
        rep.ok("fotosprogreso")

    # ===================== OPERACION =====================
    for did, d in leer(db, "configuracion_app"):
        if did == "ocupacion":
            cur.execute("INSERT INTO aforo (fecha, cantidad_personas, capacidad_maxima, estado) VALUES (%s,%s,120,'vigente')",
                        (ms(d.get("actualizado_ms")) or AHORA(), max(0, int(d.get("personas", 0)))))
            rep.ok("aforo")
        elif did == "argos" and d.get("base_conocimiento"):
            cur.execute("INSERT INTO argosbaseconocimiento (id_empleado, titulo, contenido) VALUES (%s,'Base de conocimiento',%s)",
                        (dueno, d["base_conocimiento"]))
            rep.ok("argosbaseconocimiento")
    for did, d in leer(db, "argos_uso_diario"):
        f = fecha(d.get("fecha") or did)
        if f:
            cur.execute("INSERT INTO argoscupodiario (id_empleado, fecha, mensajes_enviados, limite_diario)"
                        " VALUES (%s,%s,%s,300) ON CONFLICT DO NOTHING", (dueno, f, max(0, int(d.get("cantidad", 0)))))
            rep.ok("argoscupodiario")
    for did, d in leer(db, "generaciones_imagenes_ia"):
        f = fecha(d.get("fecha") or did)
        if f:
            cur.execute("INSERT INTO consumoimagenesia (fecha, cantidad) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                        (f, max(0, int(d.get("cantidad", 0)))))
            rep.ok("consumoimagenesia")
    for _id, d in leer(db, "contactos_web"):
        contacto = (d.get("contacto") or "").strip()
        cur.execute(
            "INSERT INTO contactosweb (nombre, email, telefono, mensaje, fecha, estado) VALUES (%s,%s,%s,%s,%s,'nuevo')",
            ((d.get("nombre") or "-")[:100], contacto if "@" in contacto else None, None if "@" in contacto else (contacto or "-"),
             (d.get("mensaje") or "")[:999], d.get("creado") or AHORA()),
        )
        rep.ok("contactosweb")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--limpiar", action="store_true")
    args = ap.parse_args()

    url = args.url
    if not url:
        ruta = os.path.join(CARPETA_EMPLEADOS, "neon_credentials.json")
        if not os.path.exists(ruta):
            sys.exit(f"Falta {ruta} con {{\"database_url\": \"postgresql://...\"}} (o pasar --url).")
        url = json.load(open(ruta))["database_url"]

    firebase_admin.initialize_app(credentials.Certificate(os.path.join(CARPETA_EMPLEADOS, "firebase_credentials.json")))
    db = firestore.client()

    rep = Reporte()
    with psycopg.connect(url, prepare_threshold=None) as cx:
        if args.limpiar:
            cx.execute("TRUNCATE socios, empleados, platos, tablonpublicaciones, contactosweb, consumoimagenesia,"
                       " argosbaseconocimiento RESTART IDENTITY CASCADE")
            cx.execute("DELETE FROM ejercicios WHERE estado <> 'competencia'")
            cx.execute("DELETE FROM aforo WHERE id_aforo <> (SELECT min(id_aforo) FROM aforo)")
        migrar(db, cx, rep)
        cx.commit()

    print("\n=== FILAS MIGRADAS ===")
    for t, n in sorted(rep.insertadas.items()):
        print(f"  {t:42s} {n}")
    print(f"  {'TOTAL':42s} {sum(rep.insertadas.values())}")
    if rep.descartadas:
        print(f"\n=== FILAS DESCARTADAS POR NO CUMPLIR LAS CLAVES FORANEAS / CATALOGOS ({len(rep.descartadas)}) ===")
        resumen: dict[str, int] = {}
        for linea in rep.descartadas:
            resumen[linea] = resumen.get(linea, 0) + 1
        for linea, n in sorted(resumen.items()):
            print(f"  {linea}" + (f"  (x{n})" if n > 1 else ""))


if __name__ == "__main__":
    main()
