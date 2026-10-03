# OLIMPOS GYM — Acceso a la base de datos relacional (PostgreSQL en Neon)
#
# Reemplaza a Firestore en el sistema de empleados. Requiere un archivo
# "neon_credentials.json" en esta misma carpeta (NUNCA se sube a git — ver
# .gitignore), con la forma:
#   {"database_url": "postgresql://usuario:clave@host/base?sslmode=require"}
#
# Neon apaga el servidor despues de un rato sin uso, lo que corta la conexion
# abierta: por eso cada consulta reintenta UNA vez reconectando.

import hashlib
import hmac
import json
import os
import secrets
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRED_PATH = os.path.join(BASE_DIR, "neon_credentials.json")

_conexion: psycopg.Connection | None = None


def _url() -> str:
    # Variable de entorno: permite apuntar a otra base (por ejemplo una de prueba) sin tocar el archivo.
    if os.environ.get("OLIMPOS_DATABASE_URL"):
        return os.environ["OLIMPOS_DATABASE_URL"]
    if not os.path.exists(CRED_PATH):
        raise RuntimeError(
            "Falta el archivo 'neon_credentials.json' en la carpeta del sistema. "
            'Tiene que contener {"database_url": "postgresql://..."} (cadena de '
            "conexion que se copia desde el panel de Neon, boton Connect)."
        )
    with open(CRED_PATH, encoding="utf-8") as f:
        return json.load(f)["database_url"]


def conexion() -> psycopg.Connection:
    """Conexion compartida; se vuelve a abrir sola si Neon la cerro."""
    global _conexion
    if _conexion is None or _conexion.closed:
        # prepare_threshold=None: el pooler de Neon no admite sentencias preparadas del lado del servidor.
        _conexion = psycopg.connect(_url(), row_factory=dict_row, prepare_threshold=None, connect_timeout=15)
    return _conexion


def _reintentable(fn):
    def envuelto(*args, **kwargs):
        global _conexion
        try:
            return fn(*args, **kwargs)
        except (psycopg.OperationalError, psycopg.InterfaceError):
            try:
                if _conexion is not None:
                    _conexion.close()
            except Exception:
                pass
            _conexion = None
            return fn(*args, **kwargs)
    return envuelto


@_reintentable
def consulta(sql: str, params=()) -> list[dict]:
    """SELECT (o INSERT/UPDATE ... RETURNING): devuelve la lista de filas como dicts."""
    cx = conexion()
    try:
        with cx.cursor() as cur:
            cur.execute(sql, params)
            filas = cur.fetchall() if cur.description else []
        cx.commit()
        return filas
    except psycopg.errors.Error:
        cx.rollback()
        raise


def una_fila(sql: str, params=()) -> dict | None:
    filas = consulta(sql, params)
    return filas[0] if filas else None


@_reintentable
def ejecutar(sql: str, params=()) -> int:
    """INSERT/UPDATE/DELETE sin resultado: devuelve cuantas filas toco."""
    cx = conexion()
    try:
        with cx.cursor() as cur:
            cur.execute(sql, params)
            n = cur.rowcount
        cx.commit()
        return n
    except psycopg.errors.Error:
        cx.rollback()
        raise


@contextmanager
def transaccion():
    """Varias sentencias que se aplican todas o ninguna:

        with neon_db.transaccion() as cur:
            cur.execute(...)
            cur.execute(...)
    """
    cx = _conexion_viva()
    cur = cx.cursor()
    try:
        yield cur
        cx.commit()
    except Exception:
        cx.rollback()
        raise
    finally:
        cur.close()


def _conexion_viva() -> psycopg.Connection:
    """Comprueba que la conexion siga abierta (Neon la corta tras un rato
    inactivo) y la rehace si hace falta, ANTES de empezar una transaccion."""
    global _conexion
    try:
        cx = conexion()
        cx.execute("SELECT 1")
        cx.commit()
        return cx
    except (psycopg.OperationalError, psycopg.InterfaceError):
        _conexion = None
        return conexion()


# ───────────────────────── contraseñas ─────────────────────────
# scrypt (de la biblioteca estandar): lento a proposito para que adivinar una
# contraseña por fuerza bruta sea carisimo. Formato: scrypt$n$r$p$sal$hash
_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    sal = secrets.token_bytes(16)
    h = hashlib.scrypt(password.encode("utf-8"), salt=sal, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${sal.hex()}${h.hex()}"


def verificar_password(password: str, almacenado: str) -> bool:
    try:
        _, n, r, p, sal, h = almacenado.split("$")
        calculado = hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(sal), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(calculado.hex(), h)
    except (ValueError, TypeError):
        return False
