# OLIMPOS GYM — Repositorio de membresías asignadas (Dueño / Administrador /
# Recepcionista)
#
# Antes "Mi membresía" en la app móvil dejaba que el propio socio se
# activara un plan tocando un botón — nadie del gimnasio se enteraba, y no
# quedaba ninguna fecha de inicio real (el logro "Cliente fiel: 6 meses de
# membresía activa" no tenía de dónde salir, y el texto de la app mostraba
# un vencimiento inventado). Ahora la asigna un empleado acá, con fecha de
# inicio real — el socio solo la ve y puede "pedir" un cambio de plan.
#
# Forma en Firestore (colección "membresias", un documento por socio):
# {
#   "socio_id": "uid123", "plan": "Oro", "fecha_inicio_ms": 1737000000000,
#   "asignado_por": "Carlos García — Dueño"
# }

from datetime import datetime

from dietas_repo import _db

COLECCION = "membresias"

# Mismos 3 planes que PLANES_MEMBRESIA en la app móvil (AppData.kt) — solo
# el nombre hace falta acá, precio/beneficios son catálogo fijo del lado
# de la app.
PLANES = ["Bronce", "Oro", "Platino"]

# Argos (el asistente de IA de la app móvil) es un beneficio de pago: solo lo
# tienen los socios con uno de estos planes (mismo criterio que
# PLANES_CON_ARGOS en la app móvil y que el Worker de Argos, que lo verifica
# del lado del servidor leyendo este mismo documento "membresias").
PLANES_CON_ARGOS = ("Oro", "Platino")

_cache_membresias: dict[str, dict] | None = None


def cargar_membresias(forzar: bool = False) -> dict[str, dict]:
    global _cache_membresias
    if _cache_membresias is None or forzar:
        docs = _db().collection(COLECCION).stream()
        _cache_membresias = {d.id: d.to_dict() for d in docs}
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
    doc = {
        "socio_id": socio_id,
        "plan": plan,
        "fecha_inicio_ms": fecha_inicio_ms,
        "asignado_por": asignado_por,
    }
    _db().collection(COLECCION).document(socio_id).set(doc)
    cache = cargar_membresias()
    cache[socio_id] = doc
    return cache


def quitar_membresia(socio_id: str) -> dict[str, dict]:
    global _cache_membresias
    _db().collection(COLECCION).document(socio_id).delete()
    cache = cargar_membresias()
    cache.pop(socio_id, None)
    return cache
