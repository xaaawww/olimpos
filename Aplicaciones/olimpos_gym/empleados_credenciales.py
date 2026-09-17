# OLIMPOS GYM — Credenciales de acceso al sistema de empleados
#
# Esto NO es Firebase Auth (eso es solo para socios, ver auth_repo.py): el
# sistema de empleados corre en la computadora del gimnasio, no reparte
# cuentas por internet, así que alcanza con una lista local de usuario y
# contraseña por rol. Vive en un archivo aparte (y no en login.py) para que
# la lista de abajo sea la única fuente de verdad, tanto para validar el
# login como para mostrarla en el panel de "Credenciales de acceso".

from theme import ROLES

CREDENCIALES = {
    "cgarcia":    {"password": "Garcia2026",    "role": "dueno"},
    "sramirez":   {"password": "Ramirez2026",   "role": "admin"},
    "crodriguez": {"password": "Rodriguez2026", "role": "entrenador"},
    "svillar":    {"password": "Villar2026",    "role": "nutricionista"},
    "rflores":    {"password": "Flores2026",    "role": "seguridad"},
    "pacosta":    {"password": "Acosta2026",    "role": "recepcionista"},
}


def validar(usuario: str, password: str) -> str | None:
    """Devuelve el rol si el usuario/contraseña son correctos, o None."""
    cuenta = CREDENCIALES.get(usuario.strip().lower())
    if cuenta and cuenta["password"] == password:
        return cuenta["role"]
    return None


def listado_para_mostrar() -> list[dict]:
    """Una fila por credencial, con el nombre y la etiqueta del rol ya
    resueltos contra theme.ROLES — para el panel de referencia del login."""
    filas = []
    for usuario, cuenta in CREDENCIALES.items():
        role_data = ROLES[cuenta["role"]]
        filas.append({
            "usuario": usuario,
            "password": cuenta["password"],
            "nombre": role_data["name"],
            "label": role_data["label"],
        })
    return filas
