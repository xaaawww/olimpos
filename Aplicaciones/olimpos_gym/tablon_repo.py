# OLIMPOS GYM — Repositorio del tablón del club (SOLO el Dueño lo modifica)
#
# El tablón son los avisos, eventos y promociones que ven los socios al abrir
# la app móvil (Inicio > "Tablón del club"). Lo publica y edita únicamente el
# dueño desde el sistema de empleados; la app móvil solo lo lee (la API no
# expone ninguna forma de escribirlo). Que solo el dueño pueda editarlo desde
# ACÁ lo garantiza la pantalla (views/tablon.py).
#
# En la base es la tabla "tablonpublicaciones". La pantalla la maneja como:
# {
#   "id": "5", "titulo": "Cerrado el 25/12",       # id_publicacion (texto); "nueva_xxx" si no se guardó
#   "mensaje": "El club abre de nuevo el 26 desde las 8:00.",
#   "categoria": "Aviso",        # Aviso | Evento | Promoción | Importante
#   "fijado": False,             # True = aparece arriba de todo
#   "publicado": True,           # False = borrador, no lo ve ningún socio
#   "creado_ms": 1758000000000, "actualizado_ms": 1758000000000,
#   "autor": "Carlos García — Dueño"
# }

import time
import uuid

import neon_db

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
        filas = neon_db.consulta("SELECT * FROM tablonpublicaciones")
        _cache_publicaciones = _ordenar([{
            "id": str(f["id_publicacion"]), "titulo": f["titulo"], "mensaje": f["mensaje"], "categoria": f["categoria"],
            "fijado": f["fijado"], "publicado": f["publicado"], "autor": f["autor"],
            "creado_ms": int(f["fecha_creacion"].timestamp() * 1000),
            "actualizado_ms": int(f["fecha_actualizacion"].timestamp() * 1000),
        } for f in filas])
    return _cache_publicaciones


def obtener_publicacion(publicaciones: list[dict], pub_id: str) -> dict | None:
    return next((p for p in publicaciones if p["id"] == pub_id), None)


def nueva_publicacion(autor: str) -> dict:
    ahora = int(time.time() * 1000)
    return {
        "id": f"nueva_{uuid.uuid4().hex[:10]}",
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
    if str(pub["id"]).isdigit():
        neon_db.ejecutar(
            "UPDATE tablonpublicaciones SET titulo=%s, mensaje=%s, categoria=%s, autor=%s, fijado=%s, publicado=%s,"
            " fecha_actualizacion=now() WHERE id_publicacion=%s",
            (pub["titulo"], pub["mensaje"], pub["categoria"], pub["autor"], pub["fijado"], pub["publicado"], int(pub["id"])),
        )
    else:
        fila = neon_db.una_fila(
            "INSERT INTO tablonpublicaciones (titulo, mensaje, categoria, autor, fijado, publicado) VALUES (%s,%s,%s,%s,%s,%s)"
            " RETURNING id_publicacion",
            (pub["titulo"], pub["mensaje"], pub["categoria"], pub["autor"], pub["fijado"], pub["publicado"]),
        )
        pub["id"] = str(fila["id_publicacion"])
    resto = [p for p in publicaciones if p["id"] != pub["id"]]
    _cache_publicaciones = _ordenar(resto + [pub])
    return _cache_publicaciones


def eliminar_publicacion(publicaciones: list[dict], pub_id: str) -> list[dict]:
    global _cache_publicaciones
    if pub_id.isdigit():
        neon_db.ejecutar("DELETE FROM tablonpublicaciones WHERE id_publicacion = %s", (int(pub_id),))
    _cache_publicaciones = [p for p in publicaciones if p["id"] != pub_id]
    return _cache_publicaciones
