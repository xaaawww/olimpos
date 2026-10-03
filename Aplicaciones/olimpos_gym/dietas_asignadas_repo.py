# OLIMPOS GYM — Repositorio de dietas asignadas por horario (Nutricionista / Dueño)
#
# Acá el nutricionista/dueño elige, para CADA socio, qué platos le tocan en
# cada horario del día: Desayuno, Almuerzo y Cena. En la base es una "dieta"
# vigente del socio, con su plan alimentario y los platos por momento
# (tablas dietas -> planalimentario -> planplato). La app móvil la lee por su
# propio usuario y de ahí salen "Mi día" (qué comer y cuándo), las metas
# diarias de kcal/macros y la racha de dieta.
#
# La pantalla la maneja como un diccionario por socio:
# {
#   "socio_id": "uid123",
#   "asignada_por": "Sandra Villar — Nutricionista",
#   "actualizado": "2026-09-19T10:00:00",
#   "comidas": {
#       "desayuno": ["12", "15"],
#       "almuerzo": ["7"],
#       "cena": []
#   }
# }
# Los ids son los de los platos (ver dietas_repo.py) — tienen que estar
# publicados para que el socio pueda verlos.

from datetime import date, datetime

import neon_db
from empleados_credenciales import id_empleado_actual

# clave en la base, etiqueta visible, emoji — mismo orden que MomentoComida
# en la app móvil (ComidasRepository.kt).
MOMENTOS = [
    ("desayuno", "Desayuno", "🌅"),
    ("almuerzo", "Almuerzo", "☀️"),
    ("cena", "Cena", "🌙"),
]
CLAVES_MOMENTOS = [m[0] for m in MOMENTOS]

MACROS_VACIOS = {"kcal": 0, "proteinas": 0, "carbs": 0, "grasas": 0}

# Caché en memoria, igual que rutinas_repo/membresias_repo: uid -> asignación.
_cache_asignaciones: dict[str, dict] | None = None


def cargar_asignaciones(forzar: bool = False) -> dict[str, dict]:
    global _cache_asignaciones
    if _cache_asignaciones is None or forzar:
        dietas = neon_db.consulta(
            "SELECT d.cod_dieta, s.firebase_uid, d.fecha_actualizacion, pa.id_plan_alimentario,"
            " trim(e.nombre || ' ' || e.apellido) || ' — ' || r.descripcion AS asignada_por"
            " FROM dietas d JOIN socios s USING (id_socio) JOIN planalimentario pa USING (cod_dieta)"
            " JOIN empleados e ON e.id_empleado = d.id_empleado JOIN rol r ON r.id_rol = e.rol"
            " WHERE d.estado = 'vigente' AND pa.estado = 'vigente' AND s.firebase_uid IS NOT NULL"
        )
        platos = neon_db.consulta(
            "SELECT id_plan_alimentario, momento, id_plato FROM planplato ORDER BY id_plan_alimentario, momento, orden"
        )
        por_plan: dict[int, dict[str, list[str]]] = {}
        for p in platos:
            por_plan.setdefault(p["id_plan_alimentario"], {c: [] for c in CLAVES_MOMENTOS})[p["momento"]].append(str(p["id_plato"]))
        _cache_asignaciones = {
            d["firebase_uid"]: {
                "socio_id": d["firebase_uid"], "asignada_por": d["asignada_por"],
                "actualizado": d["fecha_actualizacion"].replace(tzinfo=None).isoformat(timespec="seconds"),
                "comidas": por_plan.get(d["id_plan_alimentario"], {c: [] for c in CLAVES_MOMENTOS}),
            }
            for d in dietas
        }
    return _cache_asignaciones


def obtener_asignacion(socio_id: str) -> dict | None:
    return cargar_asignaciones().get(socio_id)


def nueva_asignacion(socio_id: str, asignada_por: str) -> dict:
    return {
        "socio_id": socio_id,
        "asignada_por": asignada_por,
        "actualizado": datetime.now().isoformat(timespec="seconds"),
        "comidas": {clave: [] for clave in CLAVES_MOMENTOS},
    }


def cantidad_platos(asignacion: dict | None) -> int:
    if not asignacion:
        return 0
    return sum(len(asignacion.get("comidas", {}).get(c, [])) for c in CLAVES_MOMENTOS)


def horarios_con_platos(asignacion: dict | None) -> int:
    if not asignacion:
        return 0
    return sum(1 for c in CLAVES_MOMENTOS if asignacion.get("comidas", {}).get(c))


def guardar_asignacion(asignacion: dict) -> dict[str, dict]:
    asignacion["actualizado"] = datetime.now().isoformat(timespec="seconds")
    with neon_db.transaccion() as cur:
        cur.execute("SELECT id_socio FROM socios WHERE firebase_uid = %s", (asignacion["socio_id"],))
        id_socio = cur.fetchone()["id_socio"]
        cur.execute(
            "SELECT d.cod_dieta, pa.id_plan_alimentario FROM dietas d JOIN planalimentario pa USING (cod_dieta)"
            " WHERE d.id_socio = %s AND d.estado = 'vigente' AND pa.estado = 'vigente'", (id_socio,))
        existente = cur.fetchone()
        if existente:
            plan = existente["id_plan_alimentario"]
            cur.execute("UPDATE dietas SET id_empleado = COALESCE(%s, id_empleado), fecha_actualizacion = now() WHERE cod_dieta = %s",
                        (id_empleado_actual(), existente["cod_dieta"]))
            cur.execute("DELETE FROM planplato WHERE id_plan_alimentario = %s", (plan,))
        else:
            cur.execute("INSERT INTO dietas (id_socio, id_empleado, nombre, estado) VALUES (%s,%s,'Dieta asignada','vigente')"
                        " RETURNING cod_dieta", (id_socio, id_empleado_actual()))
            cod = cur.fetchone()["cod_dieta"]
            cur.execute("INSERT INTO planalimentario (cod_dieta, nombre, fecha_inicio, estado) VALUES (%s,'Plan diario',%s,'vigente')"
                        " RETURNING id_plan_alimentario", (cod, date.today()))
            plan = cur.fetchone()["id_plan_alimentario"]
        for momento in CLAVES_MOMENTOS:
            for i, plato_id in enumerate(dict.fromkeys(asignacion["comidas"].get(momento, []))):
                cur.execute("INSERT INTO planplato (id_plan_alimentario, id_plato, momento, orden) VALUES (%s,%s,%s,%s)",
                            (plan, int(plato_id), momento, i))
    return cargar_asignaciones(forzar=True)


def eliminar_asignacion(socio_id: str) -> dict[str, dict]:
    neon_db.ejecutar(
        "DELETE FROM dietas WHERE estado = 'vigente' AND id_socio = (SELECT id_socio FROM socios WHERE firebase_uid = %s)",
        (socio_id,),
    )
    return cargar_asignaciones(forzar=True)


# ══════════════ Macros ══════════════

def macros_de_plato(plato: dict | None) -> dict:
    """Macros por porción del plato completo (los carga el nutricionista en
    el Editor Visual de Dietas). Si el plato es viejo y no los tiene, todo
    en cero — no se inventa nada."""
    macros = (plato or {}).get("macros") or {}
    return {k: int(macros.get(k) or 0) for k in MACROS_VACIOS}


def sumar_macros(platos: list[dict]) -> dict:
    total = dict(MACROS_VACIOS)
    for plato in platos:
        for k, v in macros_de_plato(plato).items():
            total[k] += v
    return total


# ══════════════ Objetivo y peso de cada socio (los carga el propio socio) ══════════════

def cargar_perfiles_fisicos() -> dict[str, dict]:
    """uid -> {"objetivo": "HIPERTROFIA"|..., "peso_kg": 80.0}: el objetivo
    activo (tabla objetivos) y el último peso (tabla progresopeso), que carga
    el socio en el onboarding/Configuración de la app móvil. Solo para que el
    nutricionista vea con qué objetivo está armando la dieta."""
    filas = neon_db.consulta(
        "SELECT s.firebase_uid, o.tipo AS objetivo,"
        " (SELECT pp.peso FROM progresopeso pp WHERE pp.id_socio = s.id_socio"
        "  ORDER BY pp.fecha DESC, pp.id_progreso_peso DESC LIMIT 1) AS peso_kg"
        " FROM socios s LEFT JOIN objetivos o ON o.id_socio = s.id_socio AND o.estado = 'activo'"
        " WHERE s.firebase_uid IS NOT NULL"
    )
    return {f["firebase_uid"]: {"objetivo": f["objetivo"], "peso_kg": float(f["peso_kg"]) if f["peso_kg"] is not None else None}
            for f in filas}
