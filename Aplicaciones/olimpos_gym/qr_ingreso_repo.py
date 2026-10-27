# OLIMPOS GYM — QR de entrada al gimnasio
#
# Recepción (o el dueño) deja abierta la pantalla "QR de entrada" en la
# computadora del mostrador. El socio lo escanea con la app y así queda
# registrado que está adentro: el ingreso ya no lo marca el socio solo.
#
# El QR cambia cada VENTANA_SEGUNDOS: es un código HMAC-SHA256 calculado con
# una clave secreta que vive en la base (configuracionsistema, "qr_ingreso")
# y el número de ventana de tiempo. La API (ApiWorker/src/rutas_entrenamiento.ts)
# hace la misma cuenta para comprobarlo, así que no hace falta guardar cada
# código. Una foto del QR mandada a alguien que no está en el club deja de
# servir en un par de minutos.
#
# Formato del contenido:  OLIMPOS-INGRESO:<ventana>:<codigo de 16 hex>

import hashlib
import hmac
import io
import json
import secrets
import time

import neon_db

VENTANA_SEGUNDOS = 30
PREFIJO = "OLIMPOS-INGRESO"
_CLAVE_CONFIG = "qr_ingreso"

_secreto: bytes | None = None


def _secreto_actual() -> bytes:
    """La clave del QR; la crea la primera vez que se abre la pantalla."""
    global _secreto
    if _secreto is None:
        neon_db.ejecutar(
            "INSERT INTO configuracionsistema (clave, valor, fecha_actualizacion) VALUES (%s, %s::jsonb, now())"
            " ON CONFLICT (clave) DO NOTHING",
            (_CLAVE_CONFIG, json.dumps({"secreto": secrets.token_hex(32)})))
        fila = neon_db.una_fila("SELECT valor FROM configuracionsistema WHERE clave = %s", (_CLAVE_CONFIG,))
        valor = fila["valor"] if isinstance(fila["valor"], dict) else json.loads(fila["valor"])
        _secreto = bytes.fromhex(valor["secreto"])
    return _secreto


def cambiar_clave() -> None:
    """Invalida todos los QR anteriores (por si alguien copió la pantalla)."""
    global _secreto
    neon_db.ejecutar(
        "UPDATE configuracionsistema SET valor = %s::jsonb, fecha_actualizacion = now() WHERE clave = %s",
        (json.dumps({"secreto": secrets.token_hex(32)}), _CLAVE_CONFIG))
    _secreto = None


def ventana_actual(ahora: float | None = None) -> int:
    return int((ahora if ahora is not None else time.time()) // VENTANA_SEGUNDOS)


def segundos_restantes(ahora: float | None = None) -> int:
    t = ahora if ahora is not None else time.time()
    return VENTANA_SEGUNDOS - int(t % VENTANA_SEGUNDOS)


def codigo(ventana: int) -> str:
    return hmac.new(_secreto_actual(), str(ventana).encode(), hashlib.sha256).hexdigest()[:16]


def contenido(ventana: int | None = None) -> str:
    v = ventana_actual() if ventana is None else ventana
    return f"{PREFIJO}:{v}:{codigo(v)}"


def imagen_png(texto: str) -> bytes:
    """El QR como PNG, listo para ft.Image(src=...)."""
    import segno
    buf = io.BytesIO()
    segno.make_qr(texto, error="m").save(buf, kind="png", scale=12, border=2, dark="#111111", light="#ffffff")
    return buf.getvalue()
