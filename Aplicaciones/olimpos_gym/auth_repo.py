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

from firebase_admin import auth as fb_auth

import dietas_repo as _repo

COLECCION = "socios_app"


def _app():
    _repo._asegurar_inicializado()
    return _repo._app


def generar_password(largo: int = 10) -> str:
    """Contraseña temporal para pasarle al socio — no hace falta que la
    recuerde el sistema, solo que se pueda leer y copiar una vez."""
    alfabeto = string.ascii_letters + string.digits
    return "".join(random.choices(alfabeto, k=largo))


def crear_acceso_socio(nombre: str, email: str, password: str) -> tuple[bool, str]:
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

    _repo._db().collection(COLECCION).document(user.uid).set({
        "uid": user.uid,
        "nombre": nombre.strip(),
        "email": email.strip(),
        "activo": True,
    })
    return True, user.uid


def listar_accesos_socios() -> list[dict]:
    docs = _repo._db().collection(COLECCION).stream()
    return [d.to_dict() for d in docs]


def desactivar_acceso_socio(uid: str) -> None:
    """Bloquea el login sin borrar el historial de marcas del socio (que
    queda igual en Firestore, referenciado por este mismo uid)."""
    fb_auth.update_user(uid, disabled=True, app=_app())
    _repo._db().collection(COLECCION).document(uid).update({"activo": False})
