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


def validar(usuario: str, password: str) -> str | None:
    """Devuelve el rol ('dueno', 'admin', ...) si el usuario/contraseña son
    correctos, o None. Lanza RuntimeError si no se puede consultar la base."""
    global _actual
    usuario = usuario.strip().lower()
    try:
        fila = neon_db.una_fila(
            "SELECT e.id_empleado, e.usuario, e.nombre, e.apellido, e.contraseña AS clave, r.nombre AS rol, r.descripcion AS rol_label"
            " FROM empleados e JOIN rol r ON r.id_rol = e.rol"
            " WHERE e.usuario = %s AND e.estado = 'activo'",
            (usuario,),
        )
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


def listado_para_mostrar() -> list[dict]:
    """Una fila por empleado (usuario, nombre y rol) para el panel de
    referencia del login. Las contraseñas ya no se pueden mostrar: están
    cifradas."""
    try:
        filas = neon_db.consulta(
            "SELECT e.usuario, e.nombre, e.apellido, r.descripcion AS label FROM empleados e"
            " JOIN rol r ON r.id_rol = e.rol WHERE e.estado = 'activo' ORDER BY e.id_empleado"
        )
    except Exception:
        return []
    return [{"usuario": f["usuario"], "nombre": f"{f['nombre']} {f['apellido']}".strip(), "label": f["label"]} for f in filas]
