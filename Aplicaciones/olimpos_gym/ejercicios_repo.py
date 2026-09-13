# OLIMPOS GYM — Repositorio de ejercicios (Galería de la app móvil)
#
# Mismo patrón que dietas_repo.py: los ejercicios viven en Firestore y lo
# que se publica acá aparece directo en la Galería de la app móvil (Arena),
# sin tocar código de ninguna de las dos apps.
#
# A diferencia de las dietas, acá NO se sube una foto propia: los "puntos"
# de un ejercicio son zonas musculares fijas (las mismas que el Bodygraph
# de la app), elegidas tocando el cuerpo gris/dorado en el editor. Por eso
# no hay "imagen"/"crop_x"/"crop_y" — el dibujo del cuerpo es compartido
# (ver img/cuerpo/ y ZONAS_MUSCULARES) y la app móvil ya lo trae incluido.
#
# Requiere el mismo "firebase_credentials.json" que usan las dietas (ya
# está resuelto: comparten el mismo proyecto/base de Firebase).
#
# Forma de un "ejercicio" en Firestore (coincide 1:1 con el modelo
# EjercicioCatalogo/PuntoMuscular de la app móvil):
# {
#   "id": "ejercicio_xxxxxxxx",
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

import uuid
from datetime import datetime

from dietas_repo import _db

COLECCION = "ejercicios"

# Mismas 19 zonas que ZonaMuscular.kt en la app móvil — etiqueta y emoji
# calcados para que se vea igual de un lado y del otro. Nivel de detalle
# real (pecho superior/inferior, deltoides anterior/medio/posterior,
# abductores/aductores separados, etc.), no grupos grandes.
ZONAS_MUSCULARES = {
    "PECHO_SUPERIOR": {"etiqueta": "Parte superior del pecho", "emoji": "🫀"},
    "PECHO_INFERIOR": {"etiqueta": "Parte inferior del pecho", "emoji": "🫀"},
    "DORSALES": {"etiqueta": "Dorsales", "emoji": "🔺"},
    "TRAPECIO": {"etiqueta": "Trapecios", "emoji": "🔺"},
    "LUMBARES": {"etiqueta": "Parte inferior de la espalda", "emoji": "🔻"},
    "DELTOIDES_ANTERIOR": {"etiqueta": "Deltoides anterior", "emoji": "🔘"},
    "DELTOIDES_MEDIO": {"etiqueta": "Deltoides medio", "emoji": "🔘"},
    "DELTOIDES_POSTERIOR": {"etiqueta": "Deltoides posterior", "emoji": "🔘"},
    "BICEPS": {"etiqueta": "Bíceps", "emoji": "💪"},
    "TRICEPS": {"etiqueta": "Tríceps", "emoji": "💪"},
    "ANTEBRAZOS": {"etiqueta": "Antebrazos", "emoji": "✊"},
    "ABDOMINALES": {"etiqueta": "Abdominales", "emoji": "⭐"},
    "OBLICUOS": {"etiqueta": "Oblicuos", "emoji": "⭐"},
    "ABDUCTORES": {"etiqueta": "Abductores", "emoji": "🦵"},
    "ADUCTORES": {"etiqueta": "Aductores", "emoji": "🦵"},
    "PANTORRILLAS": {"etiqueta": "Pantorrillas", "emoji": "🦵"},
    "GLUTEOS": {"etiqueta": "Glúteos", "emoji": "🍑"},
    "ISQUIOTIBIALES": {"etiqueta": "Isquiotibiales", "emoji": "🦵"},
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


def cargar_ejercicios() -> list[dict]:
    """Trae todos los ejercicios (borradores y publicados) desde Firestore."""
    docs = _db().collection(COLECCION).stream()
    return [d.to_dict() for d in docs]


def obtener_ejercicio(ejercicios: list[dict], ejercicio_id: str) -> dict | None:
    return next((e for e in ejercicios if e["id"] == ejercicio_id), None)


def nuevo_ejercicio(nombre: str = "Nuevo ejercicio") -> dict:
    return {
        "id": f"ejercicio_{uuid.uuid4().hex[:10]}",
        "nombre": nombre,
        "descripcion": "",
        "tags": [],
        "publicado": False,
        "actualizado": datetime.now().isoformat(timespec="seconds"),
        "puntos": [],
    }


def nuevo_punto(zona: str) -> dict:
    return {
        "id": f"punto_{uuid.uuid4().hex[:8]}",
        "zona": zona,
        "nombre": ZONAS_MUSCULARES[zona]["etiqueta"],
        "descripcion": "",
        "tags": [],
    }


def guardar_ejercicio(ejercicios: list[dict], ejercicio: dict) -> list[dict]:
    ejercicio["actualizado"] = datetime.now().isoformat(timespec="seconds")
    _db().collection(COLECCION).document(ejercicio["id"]).set(ejercicio)
    existentes = [e for e in ejercicios if e["id"] != ejercicio["id"]]
    existentes.append(ejercicio)
    return existentes


def eliminar_ejercicio(ejercicios: list[dict], ejercicio_id: str) -> list[dict]:
    _db().collection(COLECCION).document(ejercicio_id).delete()
    return [e for e in ejercicios if e["id"] != ejercicio_id]
