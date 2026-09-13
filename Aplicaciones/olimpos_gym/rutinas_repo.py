# OLIMPOS GYM — Repositorio de rutinas asignadas (Dueño / Entrenador)
#
# Antes, la pestaña "Entrenar" de la app móvil mostraba SIEMPRE la misma
# rutina fija ("Empuje pesado", atribuida a un entrenador inventado) para
# cualquier socio que abriera la app — no existía ninguna asignación real.
# Acá un entrenador/dueño arma y guarda la rutina de CADA socio; la app
# móvil la lee por su propio uid (ver EntrenamientoRepository.kt).
#
# Forma de una "rutina asignada" en Firestore (coincide 1:1 con
# RutinaDelDia/EjercicioRutina de la app móvil), un documento por socio:
# {
#   "socio_id": "uid123",
#   "nombre": "Empuje pesado",
#   "creada_por": "Diego A. — entrenador",
#   "actualizado": "2026-09-13T10:00:00",
#   "ejercicios": [
#       {"nombre": "Press de banca", "series_objetivo": 4, "peso_base_kg": 60.0, "es_peso_corporal": False},
#       ...
#   ]
# }

from datetime import datetime

from dietas_repo import _db

COLECCION = "rutinas_asignadas"

# Caché en memoria, igual que ejercicios_repo/dietas_repo: uid -> rutina.
_cache_rutinas: dict[str, dict] | None = None


def cargar_rutinas(forzar: bool = False) -> dict[str, dict]:
    """Trae la rutina asignada de TODOS los socios (uid -> rutina) — para
    saber en el listado quién ya tiene una y quién no."""
    global _cache_rutinas
    if _cache_rutinas is None or forzar:
        docs = _db().collection(COLECCION).stream()
        _cache_rutinas = {d.id: d.to_dict() for d in docs}
    return _cache_rutinas


def obtener_rutina(socio_id: str) -> dict | None:
    return cargar_rutinas().get(socio_id)


def nueva_rutina(socio_id: str, creada_por: str) -> dict:
    return {
        "socio_id": socio_id,
        "nombre": "Nueva rutina",
        "creada_por": creada_por,
        "actualizado": datetime.now().isoformat(timespec="seconds"),
        "ejercicios": [],
    }


def nuevo_ejercicio_rutina() -> dict:
    # "ejercicio_id" es None hasta que el entrenador elige uno real del
    # catálogo (ver editor_rutinas.py) — no se permite un nombre suelto sin
    # referencia, así la rutina siempre usa ejercicios que ya existen (con
    # su técnica y zonas musculares reales), nunca uno inventado al vuelo.
    return {"ejercicio_id": None, "nombre": "", "series_objetivo": 3, "peso_base_kg": 0.0, "es_peso_corporal": False}


def guardar_rutina(rutina: dict) -> dict[str, dict]:
    global _cache_rutinas
    rutina["actualizado"] = datetime.now().isoformat(timespec="seconds")
    _db().collection(COLECCION).document(rutina["socio_id"]).set(rutina)
    cache = cargar_rutinas()
    cache[rutina["socio_id"]] = rutina
    return cache


def eliminar_rutina(socio_id: str) -> dict[str, dict]:
    global _cache_rutinas
    _db().collection(COLECCION).document(socio_id).delete()
    cache = cargar_rutinas()
    cache.pop(socio_id, None)
    return cache
