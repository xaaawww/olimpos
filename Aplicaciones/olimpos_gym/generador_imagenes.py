# OLIMPOS GYM — Generador de imágenes de platos con OpenAI (gpt-image-1)
#
# Genera la imagen de un plato a partir de su lista de ingredientes, con el
# mismo estilo visual que el resto del catálogo (ilustración plana, vista
# cenital, fondo blanco) — para que el empleado no tenga que salir a buscar
# fotos sueltas por internet que no combinan entre sí.
#
# Requiere un archivo "openai_credentials.json" en esta misma carpeta (mismo
# criterio que firebase_credentials.json: NUNCA se sube a git — ver
# .gitignore), con la forma:
#   {"api_key": "sk-..."}
#
# El límite diario (MAXIMO_DIARIO) es propio de esta app, no de OpenAI: la
# API no expone "cuántas imágenes te quedan hoy", así que ese conteo lo
# llevamos nosotros en Firestore (ver dietas_repo.generaciones_ia_hoy) para
# no gastar de más en la cuenta sin darse cuenta.

import base64
import io
import json
import os

import requests
from PIL import Image as PILImage

import dietas_repo as repo

BASE_DIR = os.path.dirname(__file__)
CRED_PATH = os.path.join(BASE_DIR, "openai_credentials.json")

MODELO = "gpt-image-1"
CALIDAD = "medium"
TAMANO = "1024x1024"
MAXIMO_DIARIO = 20

# Mismo estilo para TODAS las imágenes generadas — vista cenital tipo
# infografía nutricional, fondo blanco, sin texto/manos/cubiertos sueltos —
# calcado del estilo que ya tiene el catálogo (ver la imagen de referencia
# de atún + brócoli + batata + rabanitos que usó el dueño al pedir esto).
ESTILO_BASE = (
    "Ilustración vectorial plana (flat design) de comida saludable, vista "
    "cenital (cámara directamente desde arriba), servida en un plato blanco "
    "circular centrado en el cuadro, sobre fondo completamente blanco liso. "
    "Contornos finos y oscuros, sombreado sutil, colores vivos pero "
    "naturales — estilo de infografía nutricional prolija, el mismo en "
    "todas las imágenes de esta app. Ingredientes bien separados entre sí, "
    "cada uno ocupando su propia zona del plato, sin mezclarse ni "
    "amontonarse. Sin texto, sin números, sin marcas de agua, sin manos y "
    "sin cubiertos sueltos en la imagen (solo puede aparecer un pequeño "
    "bowl con aderezo/salsa si algún ingrediente lo pide). "
    "El plato tiene exactamente estos ingredientes: {ingredientes}."
)


def _api_key() -> str:
    if not os.path.exists(CRED_PATH):
        raise RuntimeError(
            "Falta el archivo 'openai_credentials.json' en la carpeta del "
            "proyecto (Aplicaciones/olimpos_gym), con la forma "
            '{"api_key": "sk-..."}.'
        )
    with open(CRED_PATH, encoding="utf-8") as f:
        return json.load(f)["api_key"]


def generaciones_hoy() -> int:
    return repo.generaciones_ia_hoy()


def generaciones_restantes_hoy() -> int:
    return max(0, MAXIMO_DIARIO - generaciones_hoy())


def generar_imagen_plato(ingredientes: list[str]) -> str:
    """Genera la imagen con OpenAI y devuelve el mismo formato que
    dietas_repo.procesar_imagen: un string Base64 JPEG ya comprimido, listo
    para guardar en plato["imagen"]. Lanza RuntimeError con un mensaje
    legible si algo falla (cupo diario agotado, sin ingredientes, error de
    OpenAI) — quien llama solo necesita mostrar ese mensaje como aviso."""
    if generaciones_restantes_hoy() <= 0:
        raise RuntimeError(
            f"Se llegó al máximo de {MAXIMO_DIARIO} imágenes generadas hoy. "
            "Probá de nuevo mañana, o subí una imagen propia mientras tanto."
        )
    if not ingredientes:
        raise RuntimeError("Escribí al menos un ingrediente antes de generar la imagen.")

    prompt = ESTILO_BASE.format(ingredientes=", ".join(ingredientes))
    try:
        respuesta = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"},
            json={"model": MODELO, "prompt": prompt, "size": TAMANO, "quality": CALIDAD, "n": 1},
            timeout=120,
        )
    except requests.RequestException as ex:
        raise RuntimeError(f"No se pudo conectar con OpenAI: {ex}")

    if respuesta.status_code != 200:
        try:
            detalle = respuesta.json().get("error", {}).get("message", respuesta.text[:300])
        except Exception:
            detalle = respuesta.text[:300]
        raise RuntimeError(f"OpenAI no pudo generar la imagen ({respuesta.status_code}): {detalle}")

    datos = respuesta.json()
    b64_original = datos["data"][0]["b64_json"]
    imagen_bytes = base64.b64decode(b64_original)
    img = PILImage.open(io.BytesIO(imagen_bytes))

    resultado = repo.comprimir_imagen(img)
    repo.registrar_generacion_ia()
    return resultado
