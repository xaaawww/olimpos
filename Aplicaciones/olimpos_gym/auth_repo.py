# OLIMPOS GYM — Accesos de socios a la app
#
# El socio nunca se crea su propia cuenta: la crea acá un empleado. El LOGIN
# sigue en Firebase Authentication (guarda el email y la contraseña, cifrada)
# y la FICHA del socio (nombre, DNI, etc.) vive en la tabla "socios" de la
# base de datos relacional. Las dos se unen por el UID de Firebase, que se
# guarda en la columna "socios.firebase_uid".
#
# Si falla guardar la ficha, se borra también la cuenta recién creada en
# Firebase: nunca queda un acceso sin ficha.

import os
import random
import re
import string
import time

import firebase_admin
from firebase_admin import auth as fb_auth
from firebase_admin import credentials

import neon_db

CRED_PATH = os.path.join(os.path.dirname(__file__), "firebase_credentials.json")
_app_fb = None

# Caché en memoria: los accesos casi no cambian mientras el sistema está
# abierto (solo cuando un empleado da de alta o desactiva a alguien).
_cache_socios_app: dict[str, dict] | None = None
_cache_dni: dict[str, str] | None = None


def _app():
    global _app_fb
    if _app_fb is None:
        if not os.path.exists(CRED_PATH):
            raise RuntimeError(
                "Falta el archivo 'firebase_credentials.json' en la carpeta del "
                "proyecto (Aplicaciones/olimpos_gym). Se descarga desde Firebase "
                "Console -> Configuración del proyecto -> Cuentas de servicio -> "
                "Generar nueva clave privada."
            )
        _app_fb = firebase_admin.initialize_app(credentials.Certificate(CRED_PATH))
    return _app_fb


def generar_password(largo: int = 10) -> str:
    """Contraseña temporal para pasarle al socio — no hace falta que la
    recuerde el sistema, solo que se pueda leer y copiar una vez."""
    alfabeto = string.ascii_letters + string.digits
    return "".join(random.choices(alfabeto, k=largo))


def _dividir_nombre(completo: str) -> tuple[str, str]:
    partes = completo.split()
    if len(partes) <= 1:
        return (partes[0] if partes else "-"), ""
    return " ".join(partes[:-1]), partes[-1]


def crear_acceso_socio(nombre: str, email: str, password: str, dni: str) -> tuple[bool, str]:
    """Crea el usuario en Firebase Auth y su ficha en la tabla "socios".
    Devuelve (True, uid) si salió bien, o (False, mensaje de error) si no."""
    dni = (dni or "").strip()
    if dni and not re.fullmatch(r"[0-9]{6,10}", dni):
        return False, "El DNI debe tener solo números (entre 6 y 10 dígitos)."
    if dni and neon_db.una_fila("SELECT 1 AS x FROM socios WHERE dni = %s", (dni,)):
        return False, "Ya existe un socio con ese DNI."

    try:
        user = fb_auth.create_user(email=email.strip(), password=password, display_name=nombre.strip(), app=_app())
    except fb_auth.EmailAlreadyExistsError:
        return False, "Ya existe una cuenta con ese email."
    except ValueError as e:
        return False, f"Datos inválidos: {e}"
    except Exception as e:
        return False, str(e)

    nom, ape = _dividir_nombre(nombre.strip())
    try:
        with neon_db.transaccion() as cur:
            cur.execute(
                "INSERT INTO socios (firebase_uid, dni, nombre, apellido, email) VALUES (%s,%s,%s,%s,%s) RETURNING id_socio",
                (user.uid, dni or None, nom, ape, email.strip()),
            )
            id_socio = cur.fetchone()["id_socio"]
            # En el primer login la app móvil obliga a cambiar esta contraseña
            # temporal (ver CambiarPasswordScreen.kt); ahí se pone en False.
            cur.execute("INSERT INTO perfilapp (id_socio, debe_cambiar_password) VALUES (%s, TRUE)", (id_socio,))
    except Exception as e:
        try:
            fb_auth.delete_user(user.uid, app=_app())
        except Exception:
            pass
        return False, f"No se pudo guardar la ficha del socio: {e}"

    ficha = {"uid": user.uid, "nombre": nombre.strip(), "email": email.strip(), "activo": True,
             "creado_ms": int(time.time() * 1000), "debe_cambiar_password": True}
    global _cache_socios_app, _cache_dni
    if _cache_socios_app is not None:
        _cache_socios_app[user.uid] = ficha
    if _cache_dni is not None:
        _cache_dni[user.uid] = dni
    return True, user.uid


def listar_accesos_socios(forzar: bool = False) -> list[dict]:
    global _cache_socios_app
    if _cache_socios_app is None or forzar:
        filas = neon_db.consulta(
            "SELECT s.firebase_uid AS uid, trim(s.nombre || ' ' || s.apellido) AS nombre, s.email,"
            " (s.estado = 'activo') AS activo,"
            " (extract(epoch FROM s.fecha_registro) * 1000)::bigint AS creado_ms,"
            " COALESCE(p.debe_cambiar_password, FALSE) AS debe_cambiar_password"
            " FROM socios s LEFT JOIN perfilapp p USING (id_socio)"
            " WHERE s.firebase_uid IS NOT NULL ORDER BY s.fecha_registro"
        )
        _cache_socios_app = {f["uid"]: f for f in filas}
    return list(_cache_socios_app.values())


def dni_de_todos(forzar: bool = False) -> dict[str, str]:
    """uid -> DNI de todos los socios, para la búsqueda del sistema de
    empleados (ver verificacion_marcas.py)."""
    global _cache_dni
    if _cache_dni is None or forzar:
        filas = neon_db.consulta("SELECT firebase_uid, dni FROM socios WHERE firebase_uid IS NOT NULL")
        _cache_dni = {f["firebase_uid"]: f["dni"] or "" for f in filas}
    return _cache_dni


def desactivar_acceso_socio(uid: str) -> None:
    """Bloquea el login sin borrar el historial del socio (que queda igual
    en la base, referenciado por su misma fila)."""
    fb_auth.update_user(uid, disabled=True, app=_app())
    neon_db.ejecutar("UPDATE socios SET estado = 'inactivo' WHERE firebase_uid = %s", (uid,))
    if _cache_socios_app is not None and uid in _cache_socios_app:
        _cache_socios_app[uid]["activo"] = False
