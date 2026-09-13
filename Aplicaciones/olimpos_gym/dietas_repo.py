# OLIMPOS GYM — Repositorio de dietas (Fase 3: Firebase)
#
# Antes esto guardaba un JSON local; ahora los platos viven en Firestore.
# Lo que se publica desde acá aparece directamente en la app móvil (que lee
# la misma colección), sin tocar código de ninguna de las dos apps.
#
# Las imágenes van adentro del propio documento de Firestore, codificadas
# en Base64 (NO en Firebase Storage): Storage pasó a requerir el plan
# pago (Blaze) incluso para uso gratuito, y no todas las tarjetas prepagas
# pasan la verificación de Google. Firestore sigue siendo gratis (plan
# Spark), así que se evita por completo necesitar una tarjeta. La
# contrapartida es que cada imagen se redimensiona/comprime fuerte
# (ver _procesar_imagen) para entrar cómoda en el límite de 1MB por
# documento de Firestore.
#
# Requiere un archivo "firebase_credentials.json" (clave de cuenta de
# servicio) en esta misma carpeta — se descarga desde Firebase Console →
# Configuración del proyecto → Cuentas de servicio → Generar nueva clave
# privada.
#
# Forma de un "plato" en Firestore (coincide 1:1 con el modelo
# Plato/Ingrediente de la app móvil, para que no haga falta transformar
# datos de un lado al otro):
# {
#   "id": "plato_xxxxxxxx",
#   "nombre": "Atún",
#   "imagen": "<string Base64 JPEG, sin prefijo data:>",
#   "crop_x": 0.0, "crop_y": 0.0,  # -1..1, punto de recorte de la imagen (0,0 = centro)
#   "descripcion": "Alto en proteína, ideal para definición.",  # breve, se ve en la tarjeta del catálogo
#   "tags": ["Definición", "Alta proteína"],  # hasta 3, palabras cortas (objetivo de la dieta)
#   "asignada": False,  # True = aparece en "Asignadas por tu nutricionista" en vez del catálogo general
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
import os
import uuid
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore
from PIL import Image as PILImage

BASE_DIR = os.path.dirname(__file__)
CRED_PATH = os.path.join(BASE_DIR, "firebase_credentials.json")
COLECCION = "dietas"

# Tamaño máximo del lado más largo y calidad JPEG: pensado para que el
# string en Base64 resultante quede bien por debajo del límite de 1MB
# por documento de Firestore (en la práctica, unos 50-150KB).
DIMENSION_MAXIMA = 700
CALIDAD_JPEG = 70

_app = None


def _asegurar_inicializado():
    global _app
    if _app is not None:
        return
    if not os.path.exists(CRED_PATH):
        raise RuntimeError(
            "Falta el archivo 'firebase_credentials.json' en la carpeta del "
            "proyecto (Aplicaciones/olimpos_gym). Se descarga desde Firebase "
            "Console -> Configuración del proyecto -> Cuentas de servicio -> "
            "Generar nueva clave privada."
        )
    cred = credentials.Certificate(CRED_PATH)
    _app = firebase_admin.initialize_app(cred)


def _db():
    _asegurar_inicializado()
    return firestore.client()


def cargar_platos() -> list[dict]:
    """Trae todos los platos (borradores y publicados) desde Firestore."""
    docs = _db().collection(COLECCION).stream()
    return [d.to_dict() for d in docs]


def obtener_plato(platos: list[dict], plato_id: str) -> dict | None:
    return next((p for p in platos if p["id"] == plato_id), None)


def nuevo_plato(nombre: str = "Nuevo plato") -> dict:
    return {
        "id": f"plato_{uuid.uuid4().hex[:10]}",
        "nombre": nombre,
        "imagen": None,
        "crop_x": 0.0,
        "crop_y": 0.0,
        "descripcion": "",
        "tags": [],
        "asignada": False,
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


def procesar_imagen(ruta_origen: str) -> str:
    """Redimensiona/comprime la imagen elegida por el usuario y la devuelve
    codificada en Base64 (string, sin prefijo "data:"), lista para guardar
    directamente en el documento de Firestore. Tanto ft.Image/DecorationImage
    (Flet) como Coil (Android) aceptan un string Base64 como fuente."""
    img = PILImage.open(ruta_origen).convert("RGB")
    img.thumbnail((DIMENSION_MAXIMA, DIMENSION_MAXIMA), PILImage.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=CALIDAD_JPEG)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def guardar_plato(platos: list[dict], plato: dict) -> list[dict]:
    plato["actualizado"] = datetime.now().isoformat(timespec="seconds")
    _db().collection(COLECCION).document(plato["id"]).set(plato)
    existentes = [p for p in platos if p["id"] != plato["id"]]
    existentes.append(plato)
    return existentes


def eliminar_plato(platos: list[dict], plato_id: str) -> list[dict]:
    _db().collection(COLECCION).document(plato_id).delete()
    return [p for p in platos if p["id"] != plato_id]
