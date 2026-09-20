# OLIMPOS GYM — Repositorio del tablón del club (SOLO el Dueño lo modifica)
#
# El tablón son los avisos, eventos y promociones que ven los socios al abrir
# la app móvil (Inicio > "Tablón del club"). Lo publica y edita únicamente el
# dueño desde el sistema de empleados; la app móvil solo lo lee — las reglas
# de Firestore no le dejan a ningún socio crear, editar ni borrar nada (ver
# firestore.rules). Que solo el dueño pueda editarlo desde ACÁ lo garantiza
# la pantalla (views/tablon.py), ya que el sistema de empleados no usa
# Firebase Auth sino su propio login local por rol.
#
# Forma en Firestore (colección "tablon", un documento por publicación):
# {
#   "id": "pub_xxxxxxxx", "titulo": "Cerrado el 25/12",
#   "mensaje": "El club abre de nuevo el 26 desde las 8:00.",
#   "categoria": "Aviso",        # Aviso | Evento | Promoción | Importante
#   "fijado": False,             # True = aparece arriba de todo
#   "publicado": True,           # False = borrador, no lo ve ningún socio
#   "creado_ms": 1758000000000, "actualizado_ms": 1758000000000,
#   "autor": "Carlos García — Dueño"
# }

import time
import uuid

from dietas_repo import _db

COLECCION = "tablon"

# Mismas categorías que reconoce la app móvil (TablonRepository.kt) para
# elegir el ícono y el color de cada publicación.
CATEGORIAS = ["Aviso", "Evento", "Promoción", "Importante"]
EMOJI_CATEGORIA = {"Aviso": "📢", "Evento": "🎉", "Promoción": "🏷️", "Importante": "⚠️"}

MAX_TITULO = 80
MAX_MENSAJE = 600

_cache_publicaciones: list[dict] | None = None


def _ordenar(publicaciones: list[dict]) -> list[dict]:
    """Fijadas primero, y dentro de cada grupo la más reciente arriba."""
    return sorted(publicaciones, key=lambda p: (not p.get("fijado", False), -p.get("creado_ms", 0)))


def cargar_publicaciones(forzar: bool = False) -> list[dict]:
    global _cache_publicaciones
    if _cache_publicaciones is None or forzar:
        _cache_publicaciones = _ordenar([d.to_dict() for d in _db().collection(COLECCION).stream()])
    return _cache_publicaciones


def obtener_publicacion(publicaciones: list[dict], pub_id: str) -> dict | None:
    return next((p for p in publicaciones if p["id"] == pub_id), None)


def nueva_publicacion(autor: str) -> dict:
    ahora = int(time.time() * 1000)
    return {
        "id": f"pub_{uuid.uuid4().hex[:10]}",
        "titulo": "",
        "mensaje": "",
        "categoria": CATEGORIAS[0],
        "fijado": False,
        "publicado": False,
        "creado_ms": ahora,
        "actualizado_ms": ahora,
        "autor": autor,
    }


def guardar_publicacion(publicaciones: list[dict], pub: dict) -> list[dict]:
    global _cache_publicaciones
    pub["actualizado_ms"] = int(time.time() * 1000)
    _db().collection(COLECCION).document(pub["id"]).set(pub)
    resto = [p for p in publicaciones if p["id"] != pub["id"]]
    _cache_publicaciones = _ordenar(resto + [pub])
    return _cache_publicaciones


def eliminar_publicacion(publicaciones: list[dict], pub_id: str) -> list[dict]:
    global _cache_publicaciones
    _db().collection(COLECCION).document(pub_id).delete()
    _cache_publicaciones = [p for p in publicaciones if p["id"] != pub_id]
    return _cache_publicaciones
