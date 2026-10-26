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


# ── "¿Olvidaste tu contraseña?" ──
# Se manda un código de 6 números al email (o WhatsApp) del empleado; con ese
# código elige una contraseña nueva. Se guarda solo el hash del código, vence
# a los 15 minutos y se anula después de 5 intentos mal. No se manda una
# contraseña nueva directo: así nadie puede dejar sin acceso a otro empleado
# con solo saber su usuario.
MINUTOS_CODIGO = 15
INTENTOS_CODIGO = 5


def _clave_recuperacion(id_empleado: int) -> str:
    return f"recuperacion:{id_empleado}"


def _ocultar(email: str) -> str:
    usuario, _, dominio = (email or "").partition("@")
    return (usuario[:2] + "•" * max(1, len(usuario) - 2) + "@" + dominio) if dominio else "tu email"


def iniciar_recuperacion(usuario: str) -> tuple[bool, str]:
    """Manda el código. (ok, mensaje para mostrar)."""
    import hashlib, json, secrets
    import mensajeria
    usuario = (usuario or "").strip().lower()[:50]
    # Primero la configuración: así la respuesta no revela si el usuario existe
    if not mensajeria.email_configurado() and not mensajeria.whatsapp_configurado():
        return False, ("El sistema todavía no tiene configurado el envío de emails ni de WhatsApp. "
                       "Pedile al dueño o al administrador que te restablezca la contraseña desde Personal.")
    fila = neon_db.una_fila(
        "SELECT id_empleado, nombre, email, telefono FROM empleados WHERE usuario = %s AND estado = 'activo'", (usuario,))
    generico = "Si el usuario existe, le mandamos un código a su email o WhatsApp."
    if not fila:
        return True, generico
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    neon_db.ejecutar(
        "INSERT INTO configuracionsistema (clave, valor, fecha_actualizacion) VALUES (%s, %s::jsonb, now())"
        " ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor, fecha_actualizacion = now()",
        (_clave_recuperacion(fila["id_empleado"]),
         json.dumps({"hash": hashlib.sha256(codigo.encode()).hexdigest(), "intentos": 0})))
    enviado = []
    if mensajeria.email_configurado() and fila["email"]:
        ok, _ = mensajeria.enviar_email(fila["email"], "Código para restablecer tu contraseña",
                                        f"Hola {fila['nombre']}!\n\nTu código es: {codigo}\n\n"
                                        f"Vence en {MINUTOS_CODIGO} minutos. Si no lo pediste, avisale al dueño.")
        if ok:
            enviado.append(_ocultar(fila["email"]))
    if mensajeria.whatsapp_configurado() and fila["telefono"]:
        ok, _ = mensajeria.enviar_whatsapp(fila["telefono"], "codigo_empleado", [codigo])
        if ok:
            enviado.append("tu WhatsApp")
    if not enviado:
        return False, "No se pudo mandar el código. Pedile al dueño o al administrador que te restablezca la contraseña."
    return True, f"Te mandamos un código a {' y '.join(enviado)}. Vence en {MINUTOS_CODIGO} minutos."


def confirmar_recuperacion(usuario: str, codigo: str, nueva: str) -> tuple[bool, str]:
    import hashlib, json
    import validaciones
    usuario = (usuario or "").strip().lower()[:50]
    fila = neon_db.una_fila("SELECT id_empleado FROM empleados WHERE usuario = %s AND estado = 'activo'", (usuario,))
    if not fila:
        return False, "El código no es válido o ya venció."
    clave = _clave_recuperacion(fila["id_empleado"])
    guardado = neon_db.una_fila(
        "SELECT valor, fecha_actualizacion > now() - make_interval(mins => %s) AS vigente"
        " FROM configuracionsistema WHERE clave = %s", (MINUTOS_CODIGO, clave))
    if not guardado or not guardado["vigente"]:
        return False, "El código no es válido o ya venció. Pedí uno nuevo."
    datos = guardado["valor"] if isinstance(guardado["valor"], dict) else json.loads(guardado["valor"])
    if datos.get("intentos", 0) >= INTENTOS_CODIGO:
        neon_db.ejecutar("DELETE FROM configuracionsistema WHERE clave = %s", (clave,))
        return False, "Demasiados intentos con un código incorrecto. Pedí uno nuevo."
    if hashlib.sha256((codigo or "").strip().encode()).hexdigest() != datos.get("hash"):
        datos["intentos"] = datos.get("intentos", 0) + 1
        neon_db.ejecutar("UPDATE configuracionsistema SET valor = %s::jsonb WHERE clave = %s", (json.dumps(datos), clave))
        return False, f"Código incorrecto. Te quedan {INTENTOS_CODIGO - datos['intentos']} intentos."
    try:
        nueva = validaciones.password(nueva)
    except ValueError as e:
        return False, str(e)
    with neon_db.transaccion() as cur:
        cur.execute("UPDATE empleados SET contraseña = %s WHERE id_empleado = %s",
                    (neon_db.hash_password(nueva), fila["id_empleado"]))
        cur.execute("DELETE FROM configuracionsistema WHERE clave = %s", (clave,))
    return True, "Listo: ya podés entrar con tu contraseña nueva."


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
