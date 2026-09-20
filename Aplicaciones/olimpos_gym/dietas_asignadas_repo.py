# OLIMPOS GYM — Repositorio de dietas asignadas por horario (Nutricionista / Dueño)
#
# Hasta ahora "asignada" era un tilde suelto en cada plato (igual para todos
# los socios) — nadie le asignaba de verdad una dieta a un socio puntual.
# Acá el nutricionista/dueño elige, para CADA socio, qué platos le tocan en
# cada horario del día: Desayuno, Almuerzo y Cena. La app móvil lee este
# documento por su propio uid (ver AsignacionDietaRepository.kt) y de ahí
# salen "Mi día" (qué comer y cuándo), las metas diarias de kcal/macros y la
# racha de dieta.
#
# Forma en Firestore (colección "dietas_asignadas", un documento por socio):
# {
#   "socio_id": "uid123",
#   "asignada_por": "Sandra Villar — Nutricionista",
#   "actualizado": "2026-09-19T10:00:00",
#   "comidas": {
#       "desayuno": ["plato_abc", "plato_def"],
#       "almuerzo": ["plato_xyz"],
#       "cena": []
#   }
# }
# Los ids son los de los platos de "dietas" (ver dietas_repo.py) — tienen
# que estar publicados para que el socio pueda verlos (ver firestore.rules).

from datetime import datetime

from dietas_repo import _db

COLECCION = "dietas_asignadas"

# clave en Firestore, etiqueta visible, emoji — mismo orden que MomentoComida
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
        docs = _db().collection(COLECCION).stream()
        _cache_asignaciones = {d.id: d.to_dict() for d in docs}
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
    global _cache_asignaciones
    asignacion["actualizado"] = datetime.now().isoformat(timespec="seconds")
    _db().collection(COLECCION).document(asignacion["socio_id"]).set(asignacion)
    cache = cargar_asignaciones()
    cache[asignacion["socio_id"]] = asignacion
    return cache


def eliminar_asignacion(socio_id: str) -> dict[str, dict]:
    global _cache_asignaciones
    _db().collection(COLECCION).document(socio_id).delete()
    cache = cargar_asignaciones()
    cache.pop(socio_id, None)
    return cache


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
    """uid -> {"objetivo": "HIPERTROFIA"|..., "peso_kg": 80.0} leído de
    "datos_fisicos" (lo escribe el socio en el onboarding/Configuración de la
    app móvil). Solo para que el nutricionista vea con qué objetivo está
    armando la dieta — el Admin SDK no pasa por las reglas de Firestore."""
    perfiles = {}
    for d in _db().collection("datos_fisicos").stream():
        datos = d.to_dict() or {}
        perfiles[d.id] = {"objetivo": datos.get("objetivo"), "peso_kg": datos.get("peso_kg")}
    return perfiles
