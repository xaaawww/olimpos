# OLIMPOS GYM — Argos, el asistente de IA de texto (Claude/Anthropic)
#
# Responde preguntas SOLO sobre OlimpΩs (horarios, membresías, máquinas,
# clases, catálogo de comidas, consejos generales de entrenamiento) — nada
# más. No ejecuta ninguna acción ni toca Firestore: es pura conversación de
# texto, de un solo turno de contexto por vez (sin historial guardado en
# ningún lado más que en memoria mientras la pantalla de chat está abierta).
#
# Requiere un archivo "anthropic_credentials.json" en esta misma carpeta
# (mismo criterio que firebase_credentials.json / openai_credentials.json:
# NUNCA se sube a git — ver .gitignore), con la forma:
#   {"api_key": "sk-ant-..."}
#
# La "base de conocimiento" (horarios reales, precios, políticas) la edita
# el dueño/administrador desde esta misma pantalla (ver views/argos.py) y
# vive en Firestore (colección "configuracion_app", documento "argos") —
# así la app móvil de los socios lee EXACTAMENTE el mismo texto, sin
# duplicar la información en dos lados.
#
# El cupo diario (MAXIMO_DIARIO) es propio de esta app — Anthropic no
# expone "cuántos mensajes te quedan hoy" — para no gastar de más sin
# darse cuenta (mismo patrón que generador_imagenes.py).

import json
import os
from datetime import datetime

import requests
from firebase_admin import firestore

import dietas_repo as repo  # reutiliza db_cliente(): ya inicializa Firebase una sola vez

BASE_DIR = os.path.dirname(__file__)
CRED_PATH = os.path.join(BASE_DIR, "anthropic_credentials.json")

MODELO = "claude-haiku-4-5-20251001"
MAX_TOKENS_RESPUESTA = 600
MAXIMO_DIARIO = 300

COLECCION_CONFIG = "configuracion_app"
DOC_ARGOS = "argos"
COLECCION_USO_DIARIO = "argos_uso_diario"

INSTRUCCIONES_BASE = (
    "Sos Argos, el asistente de IA del gimnasio OlimpΩs. Respondés ÚNICAMENTE "
    "preguntas relacionadas con OlimpΩs: horarios, membresías y precios, "
    "clases, máquinas y el plano del club, el catálogo de comidas/dietas, y "
    "consejos generales de entrenamiento y hábitos saludables. "
    "Si te preguntan algo que no tiene nada que ver con el gimnasio (tareas "
    "escolares, noticias, programación, temas personales ajenos al gym, "
    "consejos médicos/legales/financieros específicos, etc.), respondé "
    "amablemente que solo podés ayudar con temas de OlimpΩs y sugerí "
    "reformular la pregunta. Nunca inventes datos: si no tenés la "
    "información (por ejemplo, un precio o el estado de una cuenta puntual "
    "que no te dieron como dato), decilo con honestidad en vez de adivinar. "
    "Respuestas breves y claras, en español rioplatense, sin markdown "
    "pesado (nada de tablas)."
)


def _api_key() -> str:
    if not os.path.exists(CRED_PATH):
        raise RuntimeError(
            "Falta el archivo 'anthropic_credentials.json' en la carpeta del "
            "proyecto (Aplicaciones/olimpos_gym), con la forma "
            '{"api_key": "sk-ant-..."}.'
        )
    with open(CRED_PATH, encoding="utf-8") as f:
        return json.load(f)["api_key"]


# ══════════════ Base de conocimiento (editable por dueño/admin) ══════════════

def cargar_base_conocimiento() -> str:
    doc = repo.db_cliente().collection(COLECCION_CONFIG).document(DOC_ARGOS).get()
    return doc.to_dict().get("base_conocimiento", "") if doc.exists else ""


def guardar_base_conocimiento(texto: str):
    repo.db_cliente().collection(COLECCION_CONFIG).document(DOC_ARGOS).set({
        "base_conocimiento": texto,
        "actualizado": datetime.now().isoformat(timespec="seconds"),
    })


# ══════════════ Cupo diario ══════════════

def usos_hoy() -> int:
    doc_id = datetime.now().strftime("%Y-%m-%d")
    doc = repo.db_cliente().collection(COLECCION_USO_DIARIO).document(doc_id).get()
    return doc.to_dict().get("cantidad", 0) if doc.exists else 0


def usos_restantes_hoy() -> int:
    return max(0, MAXIMO_DIARIO - usos_hoy())


def _registrar_uso():
    doc_id = datetime.now().strftime("%Y-%m-%d")
    repo.db_cliente().collection(COLECCION_USO_DIARIO).document(doc_id).set(
        {"fecha": doc_id, "cantidad": firestore.Increment(1)}, merge=True
    )


# ══════════════ Conversación ══════════════

def preguntar(mensaje: str, historial: list[dict] | None = None) -> str:
    """[historial] es una lista de {"rol": "user"|"assistant", "texto": "..."}
    de la conversación actual (solo en memoria, se pierde al cerrar la
    pantalla). Devuelve la respuesta de texto de Argos, o lanza RuntimeError
    con un mensaje legible si algo falla (cupo agotado, error de Anthropic)."""
    if usos_restantes_hoy() <= 0:
        raise RuntimeError(
            f"Se llegó al máximo de {MAXIMO_DIARIO} mensajes de Argos hoy. Probá de nuevo mañana."
        )
    mensaje = (mensaje or "").strip()
    if not mensaje:
        raise RuntimeError("Escribí una pregunta primero.")

    try:
        base_conocimiento = cargar_base_conocimiento()
    except Exception:
        base_conocimiento = ""

    system = INSTRUCCIONES_BASE
    if base_conocimiento.strip():
        system += (
            "\n\nInformación real de OlimpΩs para basar tus respuestas "
            "(no la repitas textual siempre, usala como referencia):\n" + base_conocimiento
        )

    mensajes = [
        {"role": ("assistant" if h["rol"] == "assistant" else "user"), "content": h["texto"]}
        for h in (historial or [])
    ]
    mensajes.append({"role": "user", "content": mensaje})

    try:
        respuesta = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": _api_key(),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODELO,
                "max_tokens": MAX_TOKENS_RESPUESTA,
                "system": system,
                "messages": mensajes,
            },
            timeout=60,
        )
    except requests.RequestException as ex:
        raise RuntimeError(f"No se pudo conectar con Anthropic: {ex}")

    if respuesta.status_code != 200:
        try:
            detalle = respuesta.json().get("error", {}).get("message", respuesta.text[:300])
        except Exception:
            detalle = respuesta.text[:300]
        raise RuntimeError(f"Argos no pudo responder ({respuesta.status_code}): {detalle}")

    datos = respuesta.json()
    texto = "".join(bloque.get("text", "") for bloque in datos.get("content", []) if bloque.get("type") == "text")
    _registrar_uso()
    return texto.strip() or "No obtuve una respuesta — probá de nuevo."
