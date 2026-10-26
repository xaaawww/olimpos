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
import validaciones

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
    recuerde el sistema, solo que se pueda leer y copiar una vez. Siempre
    trae letras y números (sin 0/O ni 1/l/I, que se confunden al dictarla)."""
    letras = "".join(c for c in string.ascii_letters if c not in "OlI")
    numeros = "23456789"
    base = [random.choice(letras) for _ in range(largo - 2)] + [random.choice(numeros) for _ in range(2)]
    random.shuffle(base)
    return "".join(base)


def _dividir_nombre(completo: str) -> tuple[str, str]:
    partes = completo.split()
    return " ".join(partes[:-1]), partes[-1]


def validar_socio(nombre: str, email: str, password: str, dni: str, telefono: str = "") -> dict:
    """Revisa y limpia todos los datos de un socio nuevo; ValueError con el
    primer problema. Incluye los repetidos: DNI y email (sin importar mayúsculas)."""
    nombre = validaciones.nombre_persona(nombre, "el nombre y apellido")
    if len(nombre.split()) < 2:
        raise ValueError("Escribí nombre y apellido (por lo menos dos palabras).")
    datos = {
        "nombre": nombre,
        "dni": validaciones.dni(dni),
        "telefono": validaciones.telefono(telefono, obligatorio=True),
        "email": validaciones.email(email),
        "password": validaciones.password(password),
    }
    if validaciones.ya_existe("socios", "dni", datos["dni"]):
        raise ValueError("Ya hay un socio registrado con ese DNI.")
    if validaciones.ya_existe("socios", "email", datos["email"], sin_mayusculas=True):
        raise ValueError("Ya hay un socio registrado con ese email.")
    return datos


def crear_acceso_socio(nombre: str, email: str, password: str, dni: str, telefono: str = "") -> tuple[bool, str]:
    """Crea el usuario en Firebase Auth y su ficha en la tabla "socios".
    Devuelve (True, uid) si salió bien, o (False, mensaje de error) si no."""
    try:
        d = validar_socio(nombre, email, password, dni, telefono)
    except ValueError as e:
        return False, str(e)
    nombre, email, password, dni = d["nombre"], d["email"], d["password"], d["dni"]

    try:
        user = fb_auth.create_user(email=email, password=password, display_name=nombre, app=_app())
    except fb_auth.EmailAlreadyExistsError:
        return False, "Ya existe una cuenta de la app con ese email."
    except ValueError as e:
        return False, f"Datos inválidos: {e}"
    except Exception as e:
        return False, str(e)

    nom, ape = _dividir_nombre(nombre)
    try:
        with neon_db.transaccion() as cur:
            cur.execute(
                "INSERT INTO socios (firebase_uid, dni, nombre, apellido, email, telefono) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id_socio",
                (user.uid, dni, nom, ape, email, d["telefono"]),
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
        texto = str(e)
        if "socios_dni_key" in texto:
            return False, "Ya hay un socio registrado con ese DNI."
        if "socios_email" in texto:
            return False, "Ya hay un socio registrado con ese email."
        return False, f"No se pudo guardar la ficha del socio: {texto.splitlines()[0]}"

    ficha = {"uid": user.uid, "nombre": nombre, "email": email, "activo": True,
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
