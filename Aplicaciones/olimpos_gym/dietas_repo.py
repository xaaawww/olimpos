# OLIMPOS GYM — Repositorio de platos (catálogo de dietas)
#
# Los platos viven en la base de datos relacional (tabla "platos" y sus hijas:
# etiquetas, ingredientes, y las etiquetas/beneficios de cada ingrediente).
# Lo que se publica desde acá aparece directamente en la app móvil, que lee
# los mismos datos a través de la API.
#
# Las imágenes van dentro de la propia fila, codificadas en Base64 (columna
# "platos.imagen"), y se redimensionan/comprimen fuerte (ver comprimir_imagen)
# para que la app móvil las descargue rápido.
#
# Los platos se siguen manejando en la pantalla como diccionarios con la
# misma forma de siempre (para no tocar las pantallas):
# {
#   "id": "12",                 # id_plato (texto); "nuevo_xxxx" si todavía no se guardó
#   "nombre": "Atún",
#   "imagen": "<string Base64 JPEG, sin prefijo data:>",
#   "crop_x": 0.0, "crop_y": 0.0,  # -1..1, punto de recorte de la imagen (0,0 = centro)
#   "descripcion": "Alto en proteína, ideal para definición.",
#   "tags": ["Definición", "Alta proteína"],  # hasta 3
#   "asignada": False,  # en desuso: la asignación real es por socio y horario (ver dietas_asignadas_repo.py)
#   "macros": {"kcal": 450, "proteinas": 35, "carbs": 40, "grasas": 14},
#   "publicado": False,
#   "actualizado": "2026-09-09T10:00:00",
#   "puntos": [
#       {"id": "punto_xxxx", "x": 62.0, "y": 30.0, "nombre": "Atún sellado",
#        "categoria": "Proteína", "kcal": "144 kcal",
#        "tags": ["29 g proteína", "Omega-3"], "aporte": "...",
#        "beneficios": ["...", "..."]}
#   ]
# }

import base64
import io
import uuid
from datetime import date, datetime

import psycopg
from PIL import Image as PILImage

import neon_db

# Tamaño máximo del lado más largo y calidad JPEG.
DIMENSION_MAXIMA = 700
CALIDAD_JPEG = 70

_cache_platos: list[dict] | None = None


def _armar_platos(filas_platos, etiquetas, ingredientes, ing_etiquetas, ing_beneficios) -> list[dict]:
    tags_de: dict[int, list[str]] = {}
    for e in etiquetas:
        tags_de.setdefault(e["id_plato"], []).append(e["etiqueta"])
    etq_ing: dict[tuple, list[str]] = {}
    for e in ing_etiquetas:
        etq_ing.setdefault((e["id_plato"], e["ingrediente_id"]), []).append(e["etiqueta"])
    ben_ing: dict[tuple, list[str]] = {}
    for b in ing_beneficios:
        ben_ing.setdefault((b["id_plato"], b["ingrediente_id"]), []).append(b["beneficio"])
    puntos_de: dict[int, list[dict]] = {}
    for i in ingredientes:
        clave = (i["id_plato"], i["ingrediente_id"])
        puntos_de.setdefault(i["id_plato"], []).append({
            "id": i["ingrediente_id"], "x": i["x"], "y": i["y"], "nombre": i["nombre"], "categoria": i["categoria"],
            "kcal": i["kcal_texto"], "tags": etq_ing.get(clave, []), "aporte": i["aporte"],
            "beneficios": ben_ing.get(clave, []),
        })
    platos = []
    for p in filas_platos:
        platos.append({
            "id": str(p["id_plato"]), "nombre": p["nombre"], "imagen": p["imagen"],
            "crop_x": p["crop_x"] or 0.0, "crop_y": p["crop_y"] or 0.0, "descripcion": p["descripcion"] or "",
            "tags": tags_de.get(p["id_plato"], []), "asignada": False,
            "macros": {"kcal": p["kcal"] or 0, "proteinas": p["proteinas"] or 0, "carbs": p["carbs"] or 0, "grasas": p["grasas"] or 0},
            "publicado": p["estado"] == "publicado",
            "actualizado": p["fecha_actualizacion"].replace(tzinfo=None).isoformat(timespec="seconds"),
            "puntos": puntos_de.get(p["id_plato"], []),
        })
    return platos


def cargar_platos(forzar: bool = False) -> list[dict]:
    """Trae todos los platos (borradores y publicados). Se cachea en memoria
    (las imágenes pesan, y volver a pedirlas cada vez que se abre el editor
    hacía tardar la pantalla) — [forzar] fuerza una relectura real, por si
    otro empleado publicó algo desde otra máquina."""
    global _cache_platos
    if _cache_platos is None or forzar:
        _cache_platos = _armar_platos(
            neon_db.consulta("SELECT * FROM platos ORDER BY id_plato"),
            neon_db.consulta("SELECT * FROM platoetiquetas ORDER BY id_plato, orden"),
            neon_db.consulta("SELECT * FROM platoingredientes ORDER BY id_plato, orden"),
            neon_db.consulta("SELECT * FROM ingredienteetiquetas ORDER BY id_plato, ingrediente_id, orden"),
            neon_db.consulta("SELECT * FROM ingredientebeneficios ORDER BY id_plato, ingrediente_id, orden"),
        )
    return _cache_platos


def obtener_plato(platos: list[dict], plato_id: str) -> dict | None:
    return next((p for p in platos if p["id"] == plato_id), None)


def nuevo_plato(nombre: str = "Nuevo plato") -> dict:
    return {
        "id": f"nuevo_{uuid.uuid4().hex[:10]}",
        "nombre": nombre,
        "imagen": None,
        "crop_x": 0.0,
        "crop_y": 0.0,
        "descripcion": "",
        "tags": [],
        "asignada": False,
        "macros": {"kcal": 0, "proteinas": 0, "carbs": 0, "grasas": 0},
        "publicado": False,
        "actualizado": datetime.now().isoformat(timespec="seconds"),
        "puntos": [],
    }


def nuevo_punto(x: float, y: float) -> dict:
    return {
        "id": f"punto_{uuid.uuid4().hex[:8]}",
        "x": round(x, 2),
        "y": round(y, 2),
        "nombre": "Nuevo ingrediente",
        "categoria": "Proteína",
        "kcal": "",
        "tags": [],
        "aporte": "",
        "beneficios": [],
    }


def comprimir_imagen(img: PILImage.Image) -> str:
    """Redimensiona/comprime una imagen ya cargada en memoria y la devuelve
    codificada en Base64 (string, sin prefijo "data:"). Tanto ft.Image (Flet)
    como Coil (Android) aceptan un string Base64 como fuente. Usado tanto por
    [procesar_imagen] (imagen subida por el empleado) como por
    generador_imagenes.py (imagen generada con OpenAI) — mismo formato final
    para las dos, así la app móvil no distingue una de otra."""
    img = img.convert("RGB")
    img.thumbnail((DIMENSION_MAXIMA, DIMENSION_MAXIMA), PILImage.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=CALIDAD_JPEG)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def procesar_imagen(ruta_origen: str) -> str:
    """Igual que [comprimir_imagen], pero abriendo el archivo elegido por
    el empleado desde el selector de imágenes."""
    return comprimir_imagen(PILImage.open(ruta_origen))


def guardar_plato(platos: list[dict], plato: dict) -> list[dict]:
    global _cache_platos
    plato["actualizado"] = datetime.now().isoformat(timespec="seconds")
    m = plato.get("macros") or {}
    estado = "publicado" if plato.get("publicado") else "borrador"
    valores = (plato["nombre"], (plato.get("descripcion") or "")[:255], plato.get("imagen"), estado,
               m.get("kcal"), m.get("proteinas"), m.get("carbs"), m.get("grasas"),
               plato.get("crop_x"), plato.get("crop_y"))
    with neon_db.transaccion() as cur:
        if str(plato["id"]).isdigit():
            cur.execute(
                "UPDATE platos SET nombre=%s, descripcion=%s, imagen=%s, estado=%s, kcal=%s, proteinas=%s, carbs=%s,"
                " grasas=%s, crop_x=%s, crop_y=%s, fecha_actualizacion=now() WHERE id_plato=%s",
                valores + (int(plato["id"]),),
            )
            id_plato = int(plato["id"])
            cur.execute("DELETE FROM platoetiquetas WHERE id_plato=%s", (id_plato,))
            cur.execute("DELETE FROM platoingredientes WHERE id_plato=%s", (id_plato,))
        else:
            cur.execute(
                "INSERT INTO platos (nombre, descripcion, imagen, estado, kcal, proteinas, carbs, grasas, crop_x, crop_y)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_plato",
                valores,
            )
            id_plato = cur.fetchone()["id_plato"]
            plato["id"] = str(id_plato)
        for i, t in enumerate(dict.fromkeys(plato.get("tags", []))):
            cur.execute("INSERT INTO platoetiquetas (id_plato, etiqueta, orden) VALUES (%s,%s,%s)", (id_plato, t, i))
        vistos = set()
        for i, p in enumerate(plato.get("puntos", [])):
            if p["id"] in vistos:
                continue
            vistos.add(p["id"])
            cur.execute(
                "INSERT INTO platoingredientes (id_plato, ingrediente_id, nombre, categoria, aporte, kcal_texto, x, y, orden)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (id_plato, p["id"], p.get("nombre", ""), p.get("categoria", "Proteína"), (p.get("aporte") or "")[:500],
                 p.get("kcal", ""), p.get("x"), p.get("y"), i),
            )
            for j, t in enumerate(dict.fromkeys(p.get("tags", []))):
                cur.execute("INSERT INTO ingredienteetiquetas (id_plato, ingrediente_id, etiqueta, orden) VALUES (%s,%s,%s,%s)",
                            (id_plato, p["id"], t, j))
            for j, b in enumerate(dict.fromkeys(p.get("beneficios", []))):
                cur.execute("INSERT INTO ingredientebeneficios (id_plato, ingrediente_id, beneficio, orden) VALUES (%s,%s,%s,%s)",
                            (id_plato, p["id"], b[:500], j))
    existentes = [p for p in platos if p["id"] != plato["id"]]
    existentes.append(plato)
    _cache_platos = existentes
    return existentes


def eliminar_plato(platos: list[dict], plato_id: str) -> list[dict]:
    global _cache_platos
    try:
        neon_db.ejecutar("DELETE FROM platos WHERE id_plato = %s", (int(plato_id),))
    except psycopg.errors.ForeignKeyViolation:
        raise RuntimeError(
            "No se puede borrar: este plato está en la dieta de algún socio o en su historial de comidas. "
            "Quitalo de esas dietas primero (o dejalo como borrador)."
        )
    restantes = [p for p in platos if p["id"] != plato_id]
    _cache_platos = restantes
    return restantes


# ══════════════ Cupo diario de imágenes generadas con IA ══════════════
# OpenAI no expone "cuántas imágenes te quedan hoy" — ese tope es propio de
# esta app (ver generador_imagenes.py) para no gastar de más en la cuenta de
# OpenAI sin darse cuenta. Una fila por día en la tabla "consumoimagenesia".

def generaciones_ia_hoy() -> int:
    fila = neon_db.una_fila("SELECT cantidad FROM consumoimagenesia WHERE fecha = %s", (date.today(),))
    return fila["cantidad"] if fila else 0


def registrar_generacion_ia():
    neon_db.ejecutar(
        "INSERT INTO consumoimagenesia (fecha, cantidad) VALUES (%s, 1)"
        " ON CONFLICT (fecha) DO UPDATE SET cantidad = consumoimagenesia.cantidad + 1",
        (date.today(),),
    )
