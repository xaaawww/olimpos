# OLIMPOS GYM — Cámaras (Dueño / Seguridad)
#
# Cada cámara tiene hasta dos direcciones:
#   video  la transmisión EN VIVO (RTSP, como las cámaras IP de seguridad, o
#          HLS .m3u8); se reproduce con flet-video
#   url    una FOTO (JPG) del momento ("snapshot"), que la pantalla vuelve a
#          pedir cada pocos segundos; se usa si no hay video o si el video falla
#
# Mientras el gimnasio no tenga cámaras propias, vienen cargadas cámaras de
# PRUEBA: tráfico en vivo de Los Ángeles, públicas y gratis, de Caltrans (el
# departamento de transporte de California): video en vivo y foto de respaldo.
# La lista se guarda en "configuracionsistema" (clave "camaras"): agregar,
# renombrar o quitar cámaras no requiere tocar el código.

import io
import json
import os
import re
import uuid
from datetime import datetime

import requests
from PIL import Image, ImageStat

import neon_db

CLAVE = "camaras"
CARPETA_CAPTURAS = os.path.join(os.path.expanduser("~"), "Pictures", "OlimpOS - Cámaras")
_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OlimpOS"}
_CALTRANS = "https://cwwp2.dot.ca.gov/data/d7/cctv/image/{0}/{0}.jpg"
_CALTRANS_VIDEO = "https://wzmedia.dot.ca.gov/D7/CCTV-{0}.stream/playlist.m3u8"

CAMARAS_PRUEBA = [
    {"nombre": "Prueba 1 · Cypress Park", "ubicacion": "Los Ángeles, EE.UU. · autopista I-110", "codigo": "i110196avenue26offramp", "cctv": 196},
    {"nombre": "Prueba 2 · Pasadena", "ubicacion": "Los Ángeles, EE.UU. · I-210 y Lake Ave", "codigo": "i210449lakeave", "cctv": 449},
    {"nombre": "Prueba 3 · Encino", "ubicacion": "Los Ángeles, EE.UU. · US-101 y Balboa Blvd", "codigo": "us101631balboablvd", "cctv": 631},
    {"nombre": "Prueba 4 · Hawthorne", "ubicacion": "Los Ángeles, EE.UU. · I-105 y 118th St", "codigo": "i105305118thst", "cctv": 305},
    {"nombre": "Prueba 5 · Hollywood", "ubicacion": "Los Ángeles, EE.UU. · US-101 y Western Ave", "codigo": "us101606westernave", "cctv": 606},
    {"nombre": "Prueba 6 · Centro de LA", "ubicacion": "Los Ángeles, EE.UU. · I-710 y 3rd St", "codigo": "i7102853rdst", "cctv": 285},
]


def _por_defecto() -> list[dict]:
    return [{"id": c["codigo"], "nombre": c["nombre"], "ubicacion": c["ubicacion"],
             "url": _CALTRANS.format(c["codigo"]), "video": _CALTRANS_VIDEO.format(c["cctv"]), "prueba": True}
            for c in CAMARAS_PRUEBA]


# ── lista de cámaras ──
def listar() -> list[dict]:
    fila = neon_db.una_fila("SELECT valor FROM configuracionsistema WHERE clave = %s", (CLAVE,))
    if not fila:
        return _por_defecto()
    valor = fila["valor"]
    camaras = list(valor if isinstance(valor, list) else json.loads(valor))
    # las de prueba guardadas antes de que existiera el video lo toman de la lista actual
    actuales = {c["id"]: c for c in _por_defecto()}
    for c in camaras:
        if c.get("prueba") and not c.get("video") and c["id"] in actuales:
            c["video"] = actuales[c["id"]]["video"]
    return camaras


def _guardar(camaras: list[dict]) -> None:
    neon_db.ejecutar(
        "INSERT INTO configuracionsistema (clave, valor, fecha_actualizacion) VALUES (%s, %s::jsonb, now())"
        " ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor, fecha_actualizacion = now()",
        (CLAVE, json.dumps(camaras, ensure_ascii=False)))


def _validar(nombre: str, url: str, video: str = "") -> tuple[str, str, str]:
    nombre, url, video = (nombre or "").strip(), (url or "").strip(), (video or "").strip()
    if not nombre:
        raise ValueError("Poné un nombre (ej.: Entrada principal).")
    if not url and not video:
        raise ValueError("Poné al menos una dirección: la del video en vivo o la de la foto.")
    if url and not re.match(r"^https?://\S+$", url):
        raise ValueError("La dirección de la foto tiene que empezar con http:// o https://")
    if video and not re.match(r"^(rtsp|rtsps|https?)://\S+$", video):
        raise ValueError("La dirección del video tiene que empezar con rtsp://, http:// o https://")
    return nombre[:60], url, video


def agregar(nombre: str, ubicacion: str, url: str, video: str = "") -> list[dict]:
    nombre, url, video = _validar(nombre, url, video)
    camaras = listar()
    camaras.append({"id": uuid.uuid4().hex[:10], "nombre": nombre, "ubicacion": (ubicacion or "").strip()[:80],
                    "url": url, "video": video, "prueba": False})
    _guardar(camaras)
    return camaras


def editar(id_camara: str, nombre: str, ubicacion: str, url: str, video: str = "") -> list[dict]:
    nombre, url, video = _validar(nombre, url, video)
    camaras = listar()
    for c in camaras:
        if c["id"] == id_camara:
            c.update({"nombre": nombre, "ubicacion": (ubicacion or "").strip()[:80], "url": url, "video": video})
    _guardar(camaras)
    return camaras


def quitar(id_camara: str) -> list[dict]:
    camaras = [c for c in listar() if c["id"] != id_camara]
    _guardar(camaras)
    return camaras


def quitar_pruebas() -> list[dict]:
    camaras = [c for c in listar() if not c.get("prueba")]
    _guardar(camaras)
    return camaras


def restaurar_pruebas() -> list[dict]:
    propias = [c for c in listar() if not c.get("prueba")]
    camaras = _por_defecto() + propias
    _guardar(camaras)
    return camaras


# ── imagen ──
def _es_cartel(imagen: Image.Image) -> bool:
    """El "Temporarily Unavailable" de Caltrans (y otros carteles de sin señal):
    casi todo blanco y liso, sin la variedad de colores de una foto real."""
    gris = imagen.convert("L").resize((80, 60))
    arriba = gris.crop((0, 0, 80, 48))          # sin la franja de abajo con la fecha
    stat = ImageStat.Stat(arriba)
    return stat.mean[0] > 200 and stat.stddev[0] < 70


def capturar(camara: dict, timeout: float = 10) -> dict:
    """{"estado": "ok" | "sin_senal" | "error", "imagen": bytes | None,
        "detalle": str, "hora": datetime}"""
    hora = datetime.now()
    if not camara.get("url"):
        return {"estado": "error", "imagen": None, "detalle": "Sin dirección de foto", "hora": hora}
    try:
        r = requests.get(camara["url"], headers=_UA, timeout=timeout)
        if not r.ok:
            return {"estado": "error", "imagen": None, "detalle": f"La cámara respondió {r.status_code}", "hora": hora}
        imagen = Image.open(io.BytesIO(r.content))
        imagen.load()
    except requests.exceptions.Timeout:
        return {"estado": "error", "imagen": None, "detalle": "No responde (tiempo agotado)", "hora": hora}
    except requests.exceptions.RequestException:
        return {"estado": "error", "imagen": None, "detalle": "Sin conexión con la cámara", "hora": hora}
    except Exception:
        return {"estado": "error", "imagen": None, "detalle": "No devolvió una imagen", "hora": hora}
    if _es_cartel(imagen):
        return {"estado": "sin_senal", "imagen": r.content, "detalle": "La cámara no está transmitiendo", "hora": hora}
    return {"estado": "ok", "imagen": r.content, "detalle": f"{imagen.width}×{imagen.height}", "hora": hora}


def guardar_captura(camara: dict, imagen: bytes) -> str:
    os.makedirs(CARPETA_CAPTURAS, exist_ok=True)
    nombre = re.sub(r"[^\w\- ]", "", camara["nombre"]).strip().replace(" ", "_") or "camara"
    ruta = os.path.join(CARPETA_CAPTURAS, f"{nombre}_{datetime.now():%Y-%m-%d_%H-%M-%S}.jpg")
    with open(ruta, "wb") as f:
        f.write(imagen)
    return ruta
