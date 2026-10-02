# OLIMPOS GYM — Repositorio de rutinas asignadas (Dueño / Entrenador)
#
# Antes, la pestaña "Entrenar" de la app móvil mostraba SIEMPRE la misma
# rutina fija ("Empuje pesado", atribuida a un entrenador inventado) para
# cualquier socio que abriera la app — no existía ninguna asignación real.
# Acá un entrenador/dueño arma y guarda LA rutina de cada socio (la de
# "origen" = "entrenador"); la app móvil la lee por su propio uid (ver
# EntrenamientoRepository.kt / RutinasRepository.kt).
#
# Desde que el socio puede armarse rutinas propias desde la app (ver
# RutinasRepository.kt, crearRutinaPropia), "rutinas_asignadas" dejó de
# ser un documento por socio para pasar a ser VARIOS documentos por socio
# (id autogenerado, con un campo "socio_id"): como mucho uno con
# "origen" = "entrenador" (el que este módulo edita) y cero o más con
# "origen" = "socio" (de solo lectura acá, ver _vista_editor). El socio
# elige en la app cuál de todas sigue en Entrenar marcando "activa".
#
# Forma de una rutina en Firestore (coincide 1:1 con RutinaCompleta/
# EjercicioRutina de la app móvil):
# {
#   "socio_id": "uid123",
#   "origen": "entrenador",          # o "socio"
#   "activa": True,
#   "nombre": "Empuje pesado",
#   "creada_por": "Diego A. — entrenador",
#   "actualizado": "2026-09-13T10:00:00",
#   "ejercicios": [
#       {"nombre": "Press de banca", "series_objetivo": 4, "peso_base_kg": 60.0, "es_peso_corporal": False, "ejercicio_id": "abc"},
#       ...
#   ]
# }

from datetime import datetime

from dietas_repo import _db

COLECCION = "rutinas_asignadas"

# Caché en memoria, igual que ejercicios_repo/dietas_repo: uid -> lista de
# TODAS sus rutinas (de cualquier origen).
_cache_rutinas: dict[str, list[dict]] | None = None


def cargar_rutinas(forzar: bool = False) -> dict[str, list[dict]]:
    """Trae TODAS las rutinas de TODOS los socios (uid -> lista) — para
    saber en el listado quién ya tiene una del entrenador y quién no."""
    global _cache_rutinas
    if _cache_rutinas is None or forzar:
        agrupadas: dict[str, list[dict]] = {}
        for d in _db().collection(COLECCION).stream():
            rutina = d.to_dict()
            rutina["id"] = d.id
            socio_id = rutina.get("socio_id")
            if not socio_id:
                continue
            agrupadas.setdefault(socio_id, []).append(rutina)
        _cache_rutinas = agrupadas
    return _cache_rutinas


def obtener_rutina_entrenador(socio_id: str) -> dict | None:
    """La única rutina de "origen" = "entrenador" de ese socio (la que edita
    esta pantalla) — ignora las que el socio se haya armado por su cuenta."""
    return next((r for r in cargar_rutinas().get(socio_id, []) if r.get("origen", "entrenador") == "entrenador"), None)


def obtener_rutinas_propias(socio_id: str) -> list[dict]:
    """Las rutinas que el socio armó por su cuenta desde la app — de solo
    lectura acá, ver _vista_editor."""
    return [r for r in cargar_rutinas().get(socio_id, []) if r.get("origen") == "socio"]


def nueva_rutina(socio_id: str, creada_por: str) -> dict:
    # "activa" solo se prende sola si es la primera rutina que tiene ese
    # socio de cualquier origen — si ya seguía alguna (propia o de un
    # entrenador anterior), asignarle una nueva no le cambia qué sigue en
    # Entrenar sin que él lo elija (ver guardar_rutina).
    ya_tiene_alguna = len(cargar_rutinas().get(socio_id, [])) > 0
    return {
        "socio_id": socio_id,
        "origen": "entrenador",
        "activa": not ya_tiene_alguna,
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
    # (El socio sí puede escribir uno libre en las suyas propias, armadas
    # desde la app — eso vive del lado de RutinasRepository.kt, no acá.)
    return {"ejercicio_id": None, "nombre": "", "series_objetivo": 3, "peso_base_kg": 0.0, "es_peso_corporal": False}


def guardar_rutina(rutina: dict) -> dict[str, list[dict]]:
    global _cache_rutinas
    rutina["actualizado"] = datetime.now().isoformat(timespec="seconds")
    rutina.setdefault("origen", "entrenador")
    rutina.setdefault("activa", False)
    rutina_id = rutina.get("id")
    if rutina_id:
        _db().collection(COLECCION).document(rutina_id).set({k: v for k, v in rutina.items() if k != "id"})
    else:
        ref = _db().collection(COLECCION).document()
        rutina["id"] = ref.id
        ref.set({k: v for k, v in rutina.items() if k != "id"})

    cache = cargar_rutinas()
    lista = cache.setdefault(rutina["socio_id"], [])
    lista[:] = [r for r in lista if r.get("id") != rutina["id"]] + [rutina]
    return cache


def eliminar_rutina(rutina_id: str, socio_id: str) -> dict[str, list[dict]]:
    global _cache_rutinas
    _db().collection(COLECCION).document(rutina_id).delete()
    cache = cargar_rutinas()
    if socio_id in cache:
        cache[socio_id] = [r for r in cache[socio_id] if r.get("id") != rutina_id]
    return cache
