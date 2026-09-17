# OLIMPOS GYM — Accesos de socios a la app (Firebase Authentication)
#
# El socio nunca se crea su propia cuenta: la crea acá un empleado, con la
# misma cuenta de servicio (Admin SDK) que ya usan dietas_repo/ejercicios_repo/
# marcas_repo, y le pasa el email y la contraseña generada al socio para que
# entre con eso en la app (fuera de este sistema — en persona, por WhatsApp,
# como prefiera el gimnasio).
#
# El uid que devuelve Firebase Auth pasa a ser el "socio_id" que la app móvil
# graba junto a cada marca en Firestore (antes era un texto fijo puesto a
# mano — "alex_rodriguez" — en la propia app), así que a partir de ahora cada
# socio tiene un id real y propio, sin tocar nada del resto del modelo.

import random
import string
import time

from firebase_admin import auth as fb_auth

import dietas_repo as _repo

COLECCION = "socios_app"
# El DNI va en una colección aparte, NO en "socios_app": esa la puede leer
# cualquier socio autenticado (necesario para "hace cuánto que es socio"
# en Clasificación), y un DNI es un dato mucho más sensible que un nombre
# o una fecha de alta. "socios_privado" solo la puede leer el propio socio
# sobre su propio uid (ver firestore.rules) — el sistema de empleados la
# lee entera porque el Admin SDK no pasa por esas reglas.
COLECCION_PRIVADA = "socios_privado"

# Caché en memoria: los accesos casi no cambian mientras el sistema está
# abierto (solo cuando un empleado da de alta o desactiva a alguien), así
# que no tiene sentido releer Firestore entero cada vez que se abre una
# pantalla que los necesita.
_cache_socios_app: dict[str, dict] | None = None
_cache_dni: dict[str, str] | None = None


def _app():
    _repo._asegurar_inicializado()
    return _repo._app


def generar_password(largo: int = 10) -> str:
    """Contraseña temporal para pasarle al socio — no hace falta que la
    recuerde el sistema, solo que se pueda leer y copiar una vez."""
    alfabeto = string.ascii_letters + string.digits
    return "".join(random.choices(alfabeto, k=largo))


def crear_acceso_socio(nombre: str, email: str, password: str, dni: str) -> tuple[bool, str]:
    """Crea el usuario en Firebase Auth y guarda su ficha en Firestore.
    Devuelve (True, uid) si salió bien, o (False, mensaje de error) si no."""
    try:
        user = fb_auth.create_user(
            email=email.strip(),
            password=password,
            display_name=nombre.strip(),
            app=_app(),
        )
    except fb_auth.EmailAlreadyExistsError:
        return False, "Ya existe una cuenta con ese email."
    except ValueError as e:
        return False, f"Datos inválidos: {e}"
    except Exception as e:
        return False, str(e)

    ficha = {
        "uid": user.uid,
        "nombre": nombre.strip(),
        "email": email.strip(),
        "activo": True,
        # Fecha de alta en milisegundos (no un string ISO): así la app móvil
        # la lee directo como epoch sin tener que parsear formatos de fecha.
        "creado_ms": int(time.time() * 1000),
        # La contraseña que ve acá el empleado es una generada al azar (ver
        # generar_password) — en el primer login la app móvil obliga a
        # cambiarla por una que el socio elija (ver CambiarPasswordScreen.kt
        # y firestore.rules), y ahí se pone en False.
        "debe_cambiar_password": True,
    }
    _repo._db().collection(COLECCION).document(user.uid).set(ficha)
    _repo._db().collection(COLECCION_PRIVADA).document(user.uid).set({
        "dni": dni.strip(),
    })

    global _cache_socios_app, _cache_dni
    if _cache_socios_app is not None:
        _cache_socios_app[user.uid] = ficha
    if _cache_dni is not None:
        _cache_dni[user.uid] = dni.strip()
    return True, user.uid


def listar_accesos_socios(forzar: bool = False) -> list[dict]:
    global _cache_socios_app
    if _cache_socios_app is None or forzar:
        docs = _repo._db().collection(COLECCION).stream()
        _cache_socios_app = {d.id: d.to_dict() for d in docs}
    return list(_cache_socios_app.values())


def dni_de_todos(forzar: bool = False) -> dict[str, str]:
    """uid -> DNI de todos los socios, para la búsqueda del sistema de
    empleados (ver verificacion_marcas.py). El Admin SDK no pasa por
    firestore.rules, así que acá sí se puede leer todo junto."""
    global _cache_dni
    if _cache_dni is None or forzar:
        docs = _repo._db().collection(COLECCION_PRIVADA).stream()
        _cache_dni = {d.id: d.to_dict().get("dni", "") for d in docs}
    return _cache_dni


def desactivar_acceso_socio(uid: str) -> None:
    """Bloquea el login sin borrar el historial de marcas del socio (que
    queda igual en Firestore, referenciado por este mismo uid)."""
    fb_auth.update_user(uid, disabled=True, app=_app())
    _repo._db().collection(COLECCION).document(uid).update({"activo": False})
    if _cache_socios_app is not None and uid in _cache_socios_app:
        _cache_socios_app[uid]["activo"] = False
