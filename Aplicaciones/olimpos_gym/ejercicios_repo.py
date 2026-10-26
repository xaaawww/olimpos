# OLIMPOS GYM — Repositorio de ejercicios (Galería de la app móvil)
#
# Mismo patrón que dietas_repo.py: los ejercicios viven en la base de datos
# relacional (tabla "ejercicios" y sus hijas: etiquetas, puntos musculares y
# las etiquetas de cada punto) y lo que se publica acá aparece directo en la
# Galería de la app móvil (Arena).
#
# A diferencia de las dietas, acá NO se sube una foto propia: los "puntos"
# de un ejercicio son zonas musculares fijas (las mismas que el Bodygraph
# de la app), elegidas tocando el cuerpo gris/dorado en el editor. Por eso
# no hay "imagen"/"crop_x"/"crop_y" — el dibujo del cuerpo es compartido
# (ver img/cuerpo/ y ZONAS_MUSCULARES) y la app móvil ya lo trae incluido.
#
# Los ejercicios se manejan en la pantalla como diccionarios con esta forma
# (coincide con el modelo EjercicioCatalogo/PuntoMuscular de la app móvil):
# {
#   "id": "17",   # id_ejercicio (texto); "nuevo_xxxx" si todavía no se guardó
#   "nombre": "Press de banca",
#   "descripcion": "Ejercicio de empuje horizontal...",
#   "tags": ["Empuje", "Pecho", "Fuerza"],  # hasta 3, palabras cortas
#   "publicado": False,
#   "actualizado": "2026-09-10T10:00:00",
#   "puntos": [
#       {"id": "punto_xxxx", "zona": "PECHO", "nombre": "Pectoral mayor",
#        "descripcion": "Empuja la barra desde el pecho...", "tags": ["Empuje", "Pecho"]}
#   ]
# }

import os
import uuid
from datetime import datetime

import neon_db
import validaciones

# Mismas 19 zonas que ZonaMuscular.kt en la app móvil — etiqueta y emoji
# calcados para que se vea igual de un lado y del otro. Nivel de detalle
# real (pecho superior/inferior, deltoides anterior/medio/posterior,
# abductores/aductores separados, etc.), no grupos grandes.
ZONAS_MUSCULARES = {
    "PECHO_SUPERIOR": {"etiqueta": "Parte superior del pecho", "emoji": "🎽"},
    "PECHO_INFERIOR": {"etiqueta": "Parte inferior del pecho", "emoji": "🎽"},
    "DORSALES": {"etiqueta": "Dorsales", "emoji": "🦅"},
    "TRAPECIO": {"etiqueta": "Trapecios", "emoji": "⛰️"},
    "LUMBARES": {"etiqueta": "Parte inferior de la espalda", "emoji": "🪨"},
    "DELTOIDES_ANTERIOR": {"etiqueta": "Deltoides anterior", "emoji": "⬆️"},
    "DELTOIDES_MEDIO": {"etiqueta": "Deltoides medio", "emoji": "↔️"},
    "DELTOIDES_POSTERIOR": {"etiqueta": "Deltoides posterior", "emoji": "↩️"},
    "BICEPS": {"etiqueta": "Bíceps", "emoji": "💪"},
    "TRICEPS": {"etiqueta": "Tríceps", "emoji": "🥊"},
    "ANTEBRAZOS": {"etiqueta": "Antebrazos", "emoji": "✊"},
    "ABDOMINALES": {"etiqueta": "Abdominales", "emoji": "🧱"},
    "OBLICUOS": {"etiqueta": "Oblicuos", "emoji": "🌀"},
    "ABDUCTORES": {"etiqueta": "Abductores", "emoji": "➡️"},
    "ADUCTORES": {"etiqueta": "Aductores", "emoji": "⬅️"},
    "PANTORRILLAS": {"etiqueta": "Pantorrillas", "emoji": "🦶"},
    "GLUTEOS": {"etiqueta": "Glúteos", "emoji": "🍑"},
    "ISQUIOTIBIALES": {"etiqueta": "Isquiotibiales", "emoji": "🦿"},
    "CUADRICEPS": {"etiqueta": "Cuádriceps", "emoji": "🦵"},
}

# Qué zonas tienen dibujo propio en cada vista del cuerpo (ver img/cuerpo/),
# tal cual vienen separadas en el dataset anatómico de origen — no es una
# elección arbitraria: pecho/abdominales/oblicuos solo existen de frente,
# glúteos/abductores/dorsales/lumbares solo de espalda, y el resto se ve
# (y se puede tocar) desde las dos vistas.
ZONAS_POR_VISTA = {
    "frente": [
        "OBLICUOS", "ABDOMINALES", "BICEPS", "TRICEPS", "TRAPECIO",
        "ADUCTORES", "CUADRICEPS", "PANTORRILLAS", "ANTEBRAZOS",
        "PECHO_SUPERIOR", "PECHO_INFERIOR", "DELTOIDES_ANTERIOR", "DELTOIDES_MEDIO",
    ],
    "espalda": [
        "TRAPECIO", "DORSALES", "TRICEPS", "LUMBARES", "ANTEBRAZOS",
        "ADUCTORES", "ISQUIOTIBIALES", "PANTORRILLAS",
        "DELTOIDES_POSTERIOR", "DELTOIDES_MEDIO", "GLUTEOS", "ABDUCTORES",
    ],
}


# Grupo de cada zona, para los filtros del listado (Pecho, Espalda…). El
# grupo de un ejercicio es el de su músculo principal (el primero elegido).
GRUPOS = {
    "Pecho": ["PECHO_SUPERIOR", "PECHO_INFERIOR"],
    "Espalda": ["DORSALES", "TRAPECIO", "LUMBARES"],
    "Piernas": ["CUADRICEPS", "ISQUIOTIBIALES", "GLUTEOS", "PANTORRILLAS", "ABDUCTORES", "ADUCTORES"],
    "Hombros": ["DELTOIDES_ANTERIOR", "DELTOIDES_MEDIO", "DELTOIDES_POSTERIOR"],
    "Brazos": ["BICEPS", "TRICEPS", "ANTEBRAZOS"],
    "Core": ["ABDOMINALES", "OBLICUOS"],
}
EMOJI_GRUPO = {"Pecho": "🎽", "Espalda": "🦅", "Piernas": "🦵", "Hombros": "🏔️", "Brazos": "💪", "Core": "🧱"}
GRUPO_DE_ZONA = {zona: grupo for grupo, zonas in GRUPOS.items() for zona in zonas}

# Nombre corto en minúscula para la línea "Pecho, tríceps" de cada tarjeta.
NOMBRE_CORTO = {
    "PECHO_SUPERIOR": "pecho superior", "PECHO_INFERIOR": "pecho", "DORSALES": "dorsales",
    "TRAPECIO": "trapecios", "LUMBARES": "lumbares", "DELTOIDES_ANTERIOR": "hombro anterior",
    "DELTOIDES_MEDIO": "hombro medio", "DELTOIDES_POSTERIOR": "hombro posterior", "BICEPS": "bíceps",
    "TRICEPS": "tríceps", "ANTEBRAZOS": "antebrazos", "ABDOMINALES": "abdominales", "OBLICUOS": "oblicuos",
    "ABDUCTORES": "abductores", "ADUCTORES": "aductores", "PANTORRILLAS": "pantorrillas",
    "GLUTEOS": "glúteos", "ISQUIOTIBIALES": "isquiotibiales", "CUADRICEPS": "cuádriceps",
}


def grupo_de(ejercicio: dict) -> str | None:
    puntos = ejercicio.get("puntos") or []
    return GRUPO_DE_ZONA.get(puntos[0]["zona"]) if puntos else None


def resumen_musculos(ejercicio: dict) -> str:
    """'Dorsales, bíceps, antebrazos' (el primero con mayúscula)."""
    nombres = list(dict.fromkeys(NOMBRE_CORTO[p["zona"]] for p in ejercicio.get("puntos") or []))
    texto = ", ".join(nombres)
    return texto[:1].upper() + texto[1:] if texto else ""


# Dibujo de cada ejercicio (estilo ilustración): img/ejercicios/<id_ejercicio>.png.
# Los que todavía no tienen se muestran con el bodygraph.
CARPETA_IMAGENES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "ejercicios")


def imagen_de(ejercicio: dict | None) -> str | None:
    """Ruta para ft.Image (relativa a img/) o None si el ejercicio no tiene dibujo."""
    if not ejercicio or not str(ejercicio.get("id", "")).isdigit():
        return None
    nombre = f"{ejercicio['id']}.png"
    return f"ejercicios/{nombre}" if os.path.exists(os.path.join(CARPETA_IMAGENES, nombre)) else None


_cache_ejercicios: list[dict] | None = None


def cargar_ejercicios(forzar: bool = False) -> list[dict]:
    """Trae todos los ejercicios del catálogo (borradores y publicados; los
    ejercicios de la Calculadora/Arena no entran, son de otro uso). Se cachea
    en memoria — [forzar] fuerza una relectura real, por si otro empleado
    publicó algo desde otra máquina."""
    global _cache_ejercicios
    if _cache_ejercicios is None or forzar:
        ejercicios = neon_db.consulta("SELECT * FROM ejercicios WHERE estado <> 'competencia' ORDER BY id_ejercicio")
        etiquetas = neon_db.consulta("SELECT * FROM ejercicioetiquetas ORDER BY id_ejercicio, orden")
        puntos = neon_db.consulta("SELECT * FROM ejerciciopuntos ORDER BY id_ejercicio, orden")
        etq_punto = neon_db.consulta("SELECT * FROM puntoetiquetas ORDER BY id_ejercicio, punto_id, orden")
        tags_de: dict[int, list[str]] = {}
        for e in etiquetas:
            tags_de.setdefault(e["id_ejercicio"], []).append(e["etiqueta"])
        tags_punto: dict[tuple, list[str]] = {}
        for e in etq_punto:
            tags_punto.setdefault((e["id_ejercicio"], e["punto_id"]), []).append(e["etiqueta"])
        puntos_de: dict[int, list[dict]] = {}
        for p in puntos:
            puntos_de.setdefault(p["id_ejercicio"], []).append({
                "id": p["punto_id"], "zona": p["zona"], "nombre": p["nombre"], "descripcion": p["descripcion"],
                "tags": tags_punto.get((p["id_ejercicio"], p["punto_id"]), []),
            })
        _cache_ejercicios = [{
            "id": str(e["id_ejercicio"]), "nombre": e["nombre"], "descripcion": e["descripcion"] or "",
            "tags": tags_de.get(e["id_ejercicio"], []), "publicado": e["estado"] == "publicado",
            "actualizado": e["fecha_actualizacion"].replace(tzinfo=None).isoformat(timespec="seconds"),
            "puntos": puntos_de.get(e["id_ejercicio"], []),
            "pasos": [x for x in (e.get("tecnica") or "").splitlines() if x.strip()],
            "consejo": e.get("consejo") or "",
            "tipo": e.get("tipo") or "", "aparato": e.get("aparato") or "", "nivel": e.get("dificultad") or "",
            "series": e.get("series"), "repeticiones": e.get("repeticiones") or "",
        } for e in ejercicios]
    return _cache_ejercicios


def obtener_ejercicio(ejercicios: list[dict], ejercicio_id: str) -> dict | None:
    return next((e for e in ejercicios if e["id"] == ejercicio_id), None)


def nuevo_ejercicio(nombre: str = "Nuevo ejercicio") -> dict:
    return {
        "id": f"nuevo_{uuid.uuid4().hex[:10]}",
        "nombre": nombre,
        "descripcion": "",
        "tags": [],
        "publicado": False,
        "actualizado": datetime.now().isoformat(timespec="seconds"),
        "puntos": [],
        "pasos": [],
        "consejo": "",
        "tipo": "", "aparato": "", "nivel": "", "series": None, "repeticiones": "",
    }


def nuevo_punto(zona: str) -> dict:
    return {
        "id": f"punto_{uuid.uuid4().hex[:8]}",
        "zona": zona,
        "nombre": ZONAS_MUSCULARES[zona]["etiqueta"],
        "descripcion": "",
        "tags": [],
    }


def validar_ejercicio(ejercicio: dict) -> None:
    """Revisa y limpia el ejercicio antes de guardarlo (ValueError con el primer problema)."""
    import re
    ejercicio["nombre"] = validaciones.texto(ejercicio.get("nombre"), "el nombre del ejercicio", maximo=80, minimo=3)
    excluir = ("id_ejercicio", int(ejercicio["id"])) if str(ejercicio.get("id", "")).isdigit() else None
    # Los de la Calculadora ("competencia") comparten nombre a propósito: no cuentan.
    sql = ("SELECT 1 AS x FROM ejercicios WHERE lower(nombre) = %s AND estado IN ('publicado', 'borrador')"
           + (" AND id_ejercicio <> %s" if excluir else "") + " LIMIT 1")
    if neon_db.una_fila(sql, (ejercicio["nombre"].lower(), *([excluir[1]] if excluir else []))):
        raise ValueError(f"Ya hay un ejercicio llamado \"{ejercicio['nombre']}\".")
    ejercicio["descripcion"] = validaciones.texto(ejercicio.get("descripcion"), "la descripción", maximo=255,
                                                  obligatorio=False) or ""
    ejercicio["aparato"] = validaciones.texto(ejercicio.get("aparato"), "el aparato", maximo=100, obligatorio=False) or ""
    ejercicio["series"] = validaciones.entero(ejercicio.get("series"), "las series", minimo=1, maximo=20, obligatorio=False)
    reps = re.sub(r"\s+", "", str(ejercicio.get("repeticiones") or ""))
    if reps and not re.fullmatch(r"\d{1,3}(-\d{1,3})?", reps):
        raise ValueError("Las repeticiones van como número o rango (ej.: 10 o 8-12).")
    if "-" in reps:
        a, b = (int(x) for x in reps.split("-"))
        if not 0 < a < b:
            raise ValueError("En el rango de repeticiones, el primero tiene que ser menor (ej.: 8-12).")
    elif reps and int(reps) == 0:
        raise ValueError("Las repeticiones tienen que ser mayores a cero.")
    ejercicio["repeticiones"] = reps
    pasos = [validaciones.texto(p, f"el paso {i + 1}", maximo=300) for i, p in enumerate(ejercicio.get("pasos", []))
             if str(p).strip()]
    if len(pasos) > 15:
        raise ValueError("La técnica puede tener hasta 15 pasos.")
    ejercicio["pasos"] = pasos
    ejercicio["consejo"] = validaciones.texto(ejercicio.get("consejo"), "el consejo", maximo=300, obligatorio=False) or ""
    ejercicio["tags"] = validaciones.etiquetas(ejercicio.get("tags", []), maximo_items=3, maximo_largo=20)
    if ejercicio.get("publicado") and not ejercicio.get("puntos"):
        raise ValueError("Para publicarlo, marcá al menos un músculo trabajado.")


def guardar_ejercicio(ejercicios: list[dict], ejercicio: dict) -> list[dict]:
    global _cache_ejercicios
    validar_ejercicio(ejercicio)
    ejercicio["actualizado"] = datetime.now().isoformat(timespec="seconds")
    estado = "publicado" if ejercicio.get("publicado") else "borrador"
    musculos = ", ".join(dict.fromkeys(ZONAS_MUSCULARES[p["zona"]]["etiqueta"] for p in ejercicio.get("puntos", [])))[:255] or None
    # Un paso por línea (así lo guarda la columna "tecnica").
    tecnica = chr(10).join(p.strip() for p in ejercicio.get("pasos", []) if p.strip()) or None
    consejo = (ejercicio.get("consejo") or "").strip() or None
    # Ficha del panel: tipo, aparato, nivel, series y repeticiones (rango en texto, ej. "8-12").
    ficha = ((ejercicio.get("tipo") or None), (ejercicio.get("aparato") or "").strip()[:100] or None,
             (ejercicio.get("nivel") or None), ejercicio.get("series") or None,
             (ejercicio.get("repeticiones") or "").strip()[:20] or None)
    with neon_db.transaccion() as cur:
        if str(ejercicio["id"]).isdigit():
            id_ejercicio = int(ejercicio["id"])
            cur.execute(
                "UPDATE ejercicios SET nombre=%s, descripcion=%s, musculos_trabajados=%s, estado=%s,"
                " tecnica=%s, consejo=%s, tipo=%s, aparato=%s, dificultad=%s, series=%s, repeticiones=%s,"
                " fecha_actualizacion=now() WHERE id_ejercicio=%s",
                (ejercicio["nombre"], ejercicio.get("descripcion", "")[:255], musculos, estado,
                 tecnica, consejo, *ficha, id_ejercicio),
            )
            cur.execute("DELETE FROM ejercicioetiquetas WHERE id_ejercicio=%s", (id_ejercicio,))
            cur.execute("DELETE FROM ejerciciopuntos WHERE id_ejercicio=%s", (id_ejercicio,))
        else:
            cur.execute(
                "INSERT INTO ejercicios (nombre, descripcion, musculos_trabajados, estado, tecnica, consejo,"
                " tipo, aparato, dificultad, series, repeticiones) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                " RETURNING id_ejercicio",
                (ejercicio["nombre"], ejercicio.get("descripcion", "")[:255], musculos, estado, tecnica, consejo, *ficha),
            )
            id_ejercicio = cur.fetchone()["id_ejercicio"]
            ejercicio["id"] = str(id_ejercicio)
        for i, t in enumerate(dict.fromkeys(ejercicio.get("tags", []))):
            cur.execute("INSERT INTO ejercicioetiquetas (id_ejercicio, etiqueta, orden) VALUES (%s,%s,%s)", (id_ejercicio, t, i))
        vistos = set()
        for i, p in enumerate(ejercicio.get("puntos", [])):
            if p["id"] in vistos:
                continue
            vistos.add(p["id"])
            cur.execute(
                "INSERT INTO ejerciciopuntos (id_ejercicio, punto_id, zona, nombre, descripcion, orden) VALUES (%s,%s,%s,%s,%s,%s)",
                (id_ejercicio, p["id"], p["zona"], p.get("nombre", ""), (p.get("descripcion") or "")[:500], i),
            )
            for j, t in enumerate(dict.fromkeys(p.get("tags", []))):
                cur.execute("INSERT INTO puntoetiquetas (id_ejercicio, punto_id, etiqueta, orden) VALUES (%s,%s,%s,%s)",
                            (id_ejercicio, p["id"], t, j))
    existentes = [e for e in ejercicios if e["id"] != ejercicio["id"]]
    existentes.append(ejercicio)
    _cache_ejercicios = existentes
    return existentes


def eliminar_ejercicio(ejercicios: list[dict], ejercicio_id: str) -> list[dict]:
    global _cache_ejercicios
    neon_db.ejecutar("DELETE FROM ejercicios WHERE id_ejercicio = %s", (int(ejercicio_id),))
    restantes = [e for e in ejercicios if e["id"] != ejercicio_id]
    _cache_ejercicios = restantes
    return restantes
