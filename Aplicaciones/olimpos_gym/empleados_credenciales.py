# OLIMPOS GYM — Login del sistema de empleados
#
# Esto NO es Firebase Auth (eso es solo para socios, ver auth_repo.py): el
# sistema de empleados corre en la computadora del gimnasio. Antes los
# usuarios y contraseñas estaban escritos a mano en este archivo; ahora son
# filas de la tabla "empleados" (con rol, y la contraseña cifrada con scrypt:
# ni siquiera con acceso a la base se puede leer).
#
# Cada intento de entrada (bien o mal) queda registrado en "intentosacceso".

import neon_db

_actual: dict | None = None

# Contra los que prueban contraseñas: tantos intentos mal seguidos (sin uno
# bueno en el medio) dentro de la ventana bloquean a ese usuario un rato.
MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 15


class UsuarioBloqueado(RuntimeError):
    pass


def _fallidos_recientes(id_empleado: int) -> int:
    fila = neon_db.una_fila(
        "SELECT count(*) AS n FROM intentosacceso WHERE id_empleado = %s AND resultado = 'fallido'"
        " AND fecha > now() - make_interval(mins => %s)"
        " AND fecha > COALESCE((SELECT max(fecha) FROM intentosacceso WHERE id_empleado = %s AND resultado = 'exitoso'),"
        "                      '-infinity')",
        (id_empleado, MINUTOS_BLOQUEO, id_empleado))
    return int(fila["n"]) if fila else 0


def validar(usuario: str, password: str) -> str | None:
    """Devuelve el rol ('dueno', 'admin', ...) si el usuario/contraseña son
    correctos, o None. Lanza RuntimeError si no se puede consultar la base, y
    UsuarioBloqueado si ese usuario se equivocó demasiadas veces seguidas."""
    global _actual
    usuario = (usuario or "").strip().lower()[:50]
    try:
        fila = neon_db.una_fila(
            "SELECT e.id_empleado, e.usuario, e.nombre, e.apellido, e.contraseña AS clave, r.nombre AS rol, r.descripcion AS rol_label"
            " FROM empleados e JOIN rol r ON r.id_rol = e.rol"
            " WHERE e.usuario = %s AND e.estado = 'activo'",
            (usuario,),
        )
        if fila and _fallidos_recientes(fila["id_empleado"]) >= MAX_INTENTOS:
            raise UsuarioBloqueado(f"Demasiados intentos fallidos: el usuario queda bloqueado {MINUTOS_BLOQUEO} minutos. "
                                   "Si no recordás la contraseña, pedile al dueño o al administrador que la restablezca.")
    except UsuarioBloqueado:
        raise
    except Exception as ex:
        raise RuntimeError(f"No se pudo consultar la base de datos: {ex}") from ex

    correcto = bool(fila) and neon_db.verificar_password(password, fila["clave"])
    try:
        neon_db.ejecutar(
            "INSERT INTO intentosacceso (id_empleado, fecha, tipo_usuario, resultado, motivo, dispositivo)"
            " VALUES (%s, now(), 'empleado', %s, %s, 'Sistema de gestión (PC)')",
            (fila["id_empleado"] if fila else None, "exitoso" if correcto else "fallido",
             None if correcto else ("contraseña incorrecta" if fila else f"usuario inexistente: {usuario[:40]}")),
        )
    except Exception:
        pass  # el registro de auditoría nunca debe impedir entrar
    if not correcto:
        return None
    _actual = {"id_empleado": fila["id_empleado"], "usuario": fila["usuario"], "rol": fila["rol"],
               "nombre": f"{fila['nombre']} {fila['apellido']}".strip(), "rol_label": fila["rol_label"]}
    return fila["rol"]


def actual() -> dict | None:
    """El empleado que inició sesión: {"id_empleado", "usuario", "rol", "nombre", "rol_label"}."""
    return _actual


def id_empleado_actual() -> int | None:
    return _actual["id_empleado"] if _actual else None


def nombre_para_firmar() -> str:
    """'Carlos García — Dueño': como se firma lo que hace este empleado."""
    return f"{_actual['nombre']} — {_actual['rol_label']}" if _actual else "Sistema"


def cerrar_sesion() -> None:
    global _actual
    _actual = None


# Usuarios de demostración, uno por rol, para el panel del login. En la base
# la contraseña está cifrada (no se puede leer de ahí), por eso se repite acá
# en texto plano. Si se cambia una contraseña en la base, cambiarla también acá.
USUARIOS_DEMO = [
    {"label": "Dueño",         "usuario": "dueno",         "password": "Dueno#2026"},
    {"label": "Administrador", "usuario": "admin",         "password": "Admin#2026"},
    {"label": "Entrenador",    "usuario": "entrenador",    "password": "Entrenador#2026"},
    {"label": "Nutricionista", "usuario": "nutricionista", "password": "Nutricionista#2026"},
    {"label": "Seguridad",     "usuario": "seguridad",     "password": "Seguridad#2026"},
    {"label": "Recepcionista", "usuario": "recepcion",     "password": "Recepcion#2026"},
]


def listado_para_mostrar() -> list[dict]:
    """Una fila por rol (rol, usuario y contraseña) para el panel de
    referencia del login."""
    return USUARIOS_DEMO
