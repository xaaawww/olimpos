# OLIMPOS GYM — Configuración del sistema de empleados
#
# Se guarda en la tabla "configuracionsistema" (clave → JSON):
#   "empleado:<id>"  las preferencias de cada empleado (apariencia, inicio,
#                    qué avisos ve); lo siguen a cualquier computadora
#   "club"           datos del gimnasio que solo cambia el dueño (nombre,
#                    capacidad, cuándo avisar que está lleno)
# Lo único que queda en ESTA computadora es "recordar mi usuario" del login
# (data/sesion_local.json), porque se usa antes de saber quién entra.

import json
import os

import neon_db

ARCHIVO_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sesion_local.json")

PREFERENCIAS_BASE = {
    "acento": "dorado",            # ver theme.PALETAS
    "fondo": "crema",              # ver theme.FONDOS
    "menu_compacto": False,        # menú lateral solo con íconos
    "seccion_inicio": "dashboard",
    "confirmar_salida": True,      # preguntar antes de cerrar sesión
    "recordar_usuario": True,
    "contador_menu": True,         # número de avisos sin leer en el menú
    "avisos_apagados": [],         # tipos de notificaciones_repo.TIPOS que no quiere ver
    "dias_aviso_vencimiento": 7,
}

CLUB_BASE = {
    "nombre": "OLIMPOS GYM",
    "capacidad_maxima": 120,
    "porcentaje_lleno": 80,        # desde qué ocupación se avisa
    "dias_socio_nuevo": 30,        # cuántos días un socio cuenta como "nuevo"
}

_prefs: dict = dict(PREFERENCIAS_BASE)
_club: dict | None = None


def _leer(clave: str) -> dict:
    fila = neon_db.una_fila("SELECT valor FROM configuracionsistema WHERE clave = %s", (clave,))
    return dict(fila["valor"]) if fila else {}


def _escribir(clave: str, valor: dict) -> None:
    neon_db.ejecutar(
        "INSERT INTO configuracionsistema (clave, valor, fecha_actualizacion) VALUES (%s, %s::jsonb, now())"
        " ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor, fecha_actualizacion = now()",
        (clave, json.dumps(valor, ensure_ascii=False)),
    )


# ── preferencias del empleado ──
def cargar_preferencias(id_empleado: int | None) -> dict:
    """Trae las preferencias del empleado (las que no guardó, con su valor
    base) y las deja como las actuales. Si la base no responde, usa las base."""
    global _prefs
    guardadas = {}
    if id_empleado:
        try:
            guardadas = _leer(f"empleado:{id_empleado}")
        except Exception:
            guardadas = {}
    _prefs = {**PREFERENCIAS_BASE, **{k: v for k, v in guardadas.items() if k in PREFERENCIAS_BASE}}
    return _prefs


def preferencias() -> dict:
    return _prefs


def pref(clave: str):
    return _prefs.get(clave, PREFERENCIAS_BASE.get(clave))


def guardar_preferencia(id_empleado: int, clave: str, valor) -> None:
    if clave not in PREFERENCIAS_BASE:
        raise KeyError(clave)
    _prefs[clave] = valor
    # solo se guarda lo que difiere del valor base
    _escribir(f"empleado:{id_empleado}", {k: v for k, v in _prefs.items() if v != PREFERENCIAS_BASE[k]})


def restablecer_preferencias(id_empleado: int) -> dict:
    global _prefs
    neon_db.ejecutar("DELETE FROM configuracionsistema WHERE clave = %s", (f"empleado:{id_empleado}",))
    _prefs = dict(PREFERENCIAS_BASE)
    return _prefs


# ── datos del club ──
def club(forzar: bool = False) -> dict:
    global _club
    if _club is None or forzar:
        try:
            guardado = _leer("club")
        except Exception:
            guardado = {}
        _club = {**CLUB_BASE, **{k: v for k, v in guardado.items() if k in CLUB_BASE}}
    return _club


def guardar_club(clave: str, valor) -> None:
    if clave not in CLUB_BASE:
        raise KeyError(clave)
    datos = dict(club())
    datos[clave] = valor
    _escribir("club", datos)
    club()[clave] = valor


# ── esta computadora ──
def _local() -> dict:
    try:
        with open(ARCHIVO_LOCAL, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def usuario_recordado() -> str:
    return _local().get("ultimo_usuario", "")


def recordar_usuario(usuario: str | None) -> None:
    """Guarda (o borra, con None) el usuario que se precarga en el login."""
    datos = _local()
    if usuario:
        datos["ultimo_usuario"] = usuario
    else:
        datos.pop("ultimo_usuario", None)
    os.makedirs(os.path.dirname(ARCHIVO_LOCAL), exist_ok=True)
    with open(ARCHIVO_LOCAL, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
