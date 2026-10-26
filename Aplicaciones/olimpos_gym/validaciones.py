# OLIMPOS GYM — Validaciones de todos los formularios del sistema
#
# Dos capas, con las mismas reglas en todas las pantallas:
#   1. Mientras se escribe: los filtros (SOLO_DIGITOS, MONTO, FECHA, …) no
#      dejan tipear caracteres que no corresponden (letras en un DNI, etc.).
#   2. Al guardar: cada función de abajo limpia el valor y, si no sirve,
#      lanza ValueError con un mensaje claro para el empleado. Los *_repo
#      las llaman antes de tocar la base, así ninguna pantalla puede saltearlas.
#
# Los largos máximos coinciden con las columnas de Neon (si no, la base
# rechaza el dato con un error técnico en vez de un aviso entendible).

import re
import unicodedata
from datetime import date, datetime

import flet as ft

# ── largos de la base ──
MAX_NOMBRE = 60          # nombre / apellido de una persona
MAX_EMAIL = 120
MAX_DIRECCION = 120
MAX_TEXTO_CORTO = 255    # varchar(255) de la base

# ── filtros de tipeo (un carácter por vez) ──
SOLO_DIGITOS = ft.InputFilter(regex_string=r"[0-9]", allow=True, replacement_string="")
TELEFONO = ft.InputFilter(regex_string=r"[0-9+\s()\-]", allow=True, replacement_string="")
MONTO = ft.InputFilter(regex_string=r"[0-9.,]", allow=True, replacement_string="")
DECIMAL = MONTO
FECHA = ft.InputFilter(regex_string=r"[0-9/]", allow=True, replacement_string="")
NOMBRE = ft.InputFilter(regex_string=r"[A-Za-zÁÉÍÓÚáéíóúÜüÑñ' .\-]", allow=True, replacement_string="")
USUARIO = ft.InputFilter(regex_string=r"[A-Za-z0-9._]", allow=True, replacement_string="")
EMAIL = ft.InputFilter(regex_string=r"[A-Za-z0-9._%+\-@]", allow=True, replacement_string="")

_LETRAS_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÜüÑñ]+(?:[ '.\-][A-Za-zÁÉÍÓÚáéíóúÜüÑñ]+)*\.?$")
_EMAIL = re.compile(r"^[a-z0-9](?:[a-z0-9._%+\-]*[a-z0-9])?@[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?)*\.[a-z]{2,}$")


def _may(texto: str) -> str:
    """Primera letra en mayúscula sin tocar el resto (capitalize() pasaría "Press de Banca" a minúsculas)."""
    return texto[:1].upper() + texto[1:]


def _espacios(texto) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip()


# ── personas ──
def nombre_persona(valor, campo: str = "el nombre") -> str:
    """Letras (con tildes y ñ), espacios, apóstrofo, punto y guion. Ej.: "María José", "O'Neill"."""
    v = _espacios(valor)
    if not v:
        raise ValueError(f"Completá {campo}.")
    if len(v) < 2:
        raise ValueError(f"{_may(campo)} es muy corto.")
    if len(v) > MAX_NOMBRE:
        raise ValueError(f"{_may(campo)} puede tener hasta {MAX_NOMBRE} letras.")
    if not _LETRAS_NOMBRE.match(v):
        raise ValueError(f"{_may(campo)} solo puede tener letras (sin números ni símbolos).")
    return v


def dni(valor, obligatorio: bool = True) -> str | None:
    """DNI argentino: 7 u 8 números. Acepta que lo escriban con puntos o espacios y los saca."""
    v = re.sub(r"[.\s\-]", "", str(valor or ""))
    if not v:
        if obligatorio:
            raise ValueError("Completá el DNI.")
        return None
    if not v.isdigit():
        raise ValueError("El DNI solo puede tener números.")
    if not 7 <= len(v) <= 8:
        raise ValueError("El DNI tiene que tener 7 u 8 números.")
    if int(v) == 0 or len(set(v)) == 1:
        raise ValueError("Ese DNI no es válido.")
    return v


def email(valor, obligatorio: bool = True) -> str | None:
    """Email en minúsculas (así "Ana@Gmail.com" y "ana@gmail.com" son el mismo)."""
    v = str(valor or "").strip().lower()
    if not v:
        if obligatorio:
            raise ValueError("Completá el email.")
        return None
    if len(v) > MAX_EMAIL:
        raise ValueError(f"El email puede tener hasta {MAX_EMAIL} caracteres.")
    if " " in v or v.count("@") != 1 or ".." in v or not _EMAIL.match(v):
        raise ValueError("Ese email no es válido (ej.: nombre@gmail.com).")
    return v


def telefono(valor, obligatorio: bool = False) -> str | None:
    """Solo los números (se sacan espacios, guiones, paréntesis y el +): entre 8 y 15 dígitos."""
    crudo = str(valor or "").strip()
    v = re.sub(r"[\s\-()+]", "", crudo)
    if not v:
        if obligatorio:
            raise ValueError("Completá el teléfono.")
        return None
    if not v.isdigit():
        raise ValueError("El teléfono solo puede tener números.")
    if not 8 <= len(v) <= 15:
        raise ValueError("El teléfono tiene que tener entre 8 y 15 números (con código de área).")
    return v


def password(valor) -> str:
    v = str(valor or "")
    if v != v.strip():
        raise ValueError("La contraseña no puede empezar ni terminar con espacios.")
    if len(v) < 8:
        raise ValueError("La contraseña tiene que tener al menos 8 caracteres.")
    if len(v) > 64:
        raise ValueError("La contraseña puede tener hasta 64 caracteres.")
    if not re.search(r"[A-Za-z]", v) or not re.search(r"[0-9]", v):
        raise ValueError("La contraseña tiene que tener letras y números.")
    return v


def usuario(valor) -> str:
    v = str(valor or "").strip().lower()
    if not v:
        raise ValueError("Completá el usuario.")
    if not re.fullmatch(r"[a-z0-9._]+", v):
        raise ValueError("El usuario solo puede tener letras, números, punto y guion bajo.")
    if not 3 <= len(v) <= 30:
        raise ValueError("El usuario tiene que tener entre 3 y 30 caracteres.")
    if not v[0].isalpha():
        raise ValueError("El usuario tiene que empezar con una letra.")
    return v


# ── números ──
def numero(valor) -> float:
    """Lee un número como lo escribe la gente: "650.000", "650000", "650000,50",
    "1.250.000,5" (punto de miles, coma decimal). Lanza ValueError si no es un número."""
    if isinstance(valor, bool):
        raise ValueError("No es un número.")
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor or "").strip().replace("$", "").replace(" ", "")
    if not texto:
        raise ValueError("Vacío.")
    if "," in texto:                                    # coma decimal: los puntos son de miles
        if texto.count(",") > 1:
            raise ValueError("No es un número.")
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):     # 650.000 / 1.250.000
        texto = texto.replace(".", "")
    if not re.fullmatch(r"\d+(\.\d+)?", texto):
        raise ValueError("No es un número.")
    return float(texto)


def decimal(valor, campo: str, minimo: float | None = 0, maximo: float | None = None,
            obligatorio: bool = True, decimales: int = 2) -> float | None:
    if valor is None or str(valor).strip() == "":
        if obligatorio:
            raise ValueError(f"Completá {campo}.")
        return None
    try:
        v = numero(valor)
    except ValueError:
        raise ValueError(f"{_may(campo)} tiene que ser un número (ej.: 15000 o 15.000,50).")
    if minimo is not None and v < minimo:
        raise ValueError(f"{_may(campo)}: el mínimo es {_fmt(minimo)}.")
    if maximo is not None and v > maximo:
        raise ValueError(f"{_may(campo)}: el máximo es {_fmt(maximo)}.")
    return round(v, decimales)


def monto(valor, campo: str = "el monto", maximo: float = 100_000_000, obligatorio: bool = True) -> float | None:
    """Plata: mayor a cero y con un tope que evita errores de tipeo (un cero de más)."""
    v = decimal(valor, campo, minimo=None, maximo=maximo, obligatorio=obligatorio)
    if v is not None and v <= 0:
        raise ValueError(f"{_may(campo)} tiene que ser mayor a cero.")
    return v


def entero(valor, campo: str, minimo: int | None = 0, maximo: int | None = None, obligatorio: bool = True) -> int | None:
    if valor is None or str(valor).strip() == "":
        if obligatorio:
            raise ValueError(f"Completá {campo}.")
        return None
    texto = str(valor).strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):      # 1.500 = mil quinientos
        texto = texto.replace(".", "")
    if not re.fullmatch(r"-?\d+", texto):
        raise ValueError(f"{_may(campo)} tiene que ser un número entero.")
    v = int(texto)
    if minimo is not None and v < minimo:
        raise ValueError(f"{_may(campo)}: el mínimo es {minimo}.")
    if maximo is not None and v > maximo:
        raise ValueError(f"{_may(campo)}: el máximo es {maximo}.")
    return v


def _fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", ".") if float(n).is_integer() else f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── fechas ──
def fecha(valor, campo: str = "la fecha", minimo: date | None = None, maximo: date | None = None,
          obligatorio: bool = True) -> date | None:
    """dd/mm/aaaa (también acepta d/m/aaaa). Comprueba que la fecha exista (no 31/02)."""
    if isinstance(valor, datetime):
        v = valor.date()
    elif isinstance(valor, date):
        v = valor
    else:
        texto = str(valor or "").strip()
        if not texto:
            if obligatorio:
                raise ValueError(f"Completá {campo}.")
            return None
        m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", texto)
        if not m:
            raise ValueError(f"Escribí {campo} como dd/mm/aaaa (ej.: 05/03/2026).")
        try:
            v = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            raise ValueError(f"{_may(campo)} no existe ({texto}).")
    if v.year < 1900:
        raise ValueError(f"{_may(campo)} no es válida.")
    if minimo and v < minimo:
        raise ValueError(f"{_may(campo)} no puede ser anterior al {minimo:%d/%m/%Y}.")
    if maximo and v > maximo:
        raise ValueError(f"{_may(campo)} no puede ser posterior al {maximo:%d/%m/%Y}.")
    return v


# ── textos ──
def texto(valor, campo: str, maximo: int = MAX_TEXTO_CORTO, minimo: int = 1, obligatorio: bool = True,
          multilinea: bool = False) -> str | None:
    """Texto libre: sin espacios de más, con largo mínimo y máximo."""
    if multilinea:
        lineas = [_espacios(l) for l in str(valor or "").splitlines()]
        v = "\n".join(l for l in lineas if l)
    else:
        v = _espacios(valor)
    if not v:
        if obligatorio:
            raise ValueError(f"Completá {campo}.")
        return None
    if len(v) < minimo:
        raise ValueError(f"{_may(campo)} es muy corto (mínimo {minimo} caracteres).")
    if len(v) > maximo:
        raise ValueError(f"{_may(campo)} puede tener hasta {maximo} caracteres (tiene {len(v)}).")
    if not any(c.isalnum() for c in v):
        raise ValueError(f"{_may(campo)} tiene que tener letras o números.")
    return v


def etiquetas(valor, maximo_items: int = 3, maximo_largo: int = 20, campo: str = "las etiquetas") -> list[str]:
    """ "Fuerza, Piernas" -> ["Fuerza", "Piernas"]: sin repetidas ni vacías."""
    crudo = valor if isinstance(valor, list) else str(valor or "").split(",")
    vistos, salida = set(), []
    for t in crudo:
        t = _espacios(t)
        if not t:
            continue
        if len(t) > maximo_largo:
            raise ValueError(f"Cada una de {campo} puede tener hasta {maximo_largo} caracteres (\"{t}\").")
        clave = normalizar(t)
        if clave not in vistos:
            vistos.add(clave)
            salida.append(t)
    if len(salida) > maximo_items:
        raise ValueError(f"Poné como máximo {maximo_items} en {campo}.")
    return salida


def normalizar(texto_: str) -> str:
    """Para comparar sin importar mayúsculas, tildes ni espacios de más."""
    t = unicodedata.normalize("NFD", _espacios(texto_).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# ── repetidos en la base ──
def ya_existe(tabla: str, columna: str, valor, excluir: tuple[str, int] | None = None, sin_mayusculas: bool = False) -> bool:
    """¿Hay otra fila con este valor? [excluir] = (columna_id, id) para no chocar consigo mismo al editar."""
    import neon_db
    if valor in (None, ""):
        return False
    if not re.fullmatch(r"[a-z_]+", tabla) or not re.fullmatch(r"[a-z_]+", columna):
        raise ValueError("Tabla o columna inválida")
    campo = f"lower({columna})" if sin_mayusculas else columna
    sql, params = f"SELECT 1 AS x FROM {tabla} WHERE {campo} = %s", [valor.lower() if sin_mayusculas else valor]
    if excluir:
        if not re.fullmatch(r"[a-z_]+", excluir[0]):
            raise ValueError("Columna inválida")
        sql += f" AND {excluir[0]} <> %s"
        params.append(excluir[1])
    return neon_db.una_fila(sql + " LIMIT 1", tuple(params)) is not None


# ── ayuda para las pantallas ──
def marcar(campo: ft.TextField, error: str | None) -> bool:
    """Pinta el error debajo del campo (o lo borra). Devuelve True si quedó sin error."""
    campo.error = error
    return error is None


def revisar_varios(reglas: list) -> bool:
    """[(campo, regla), ...]: corre todas las reglas y marca cada error debajo
    de su campo, así el empleado ve todo lo que falta de una sola vez.
    Devuelve True si no hubo ningún error."""
    todo_bien = True
    for campo, regla in reglas:
        try:
            regla(campo.value)
            campo.error = None
        except ValueError as e:
            campo.error = str(e)
            todo_bien = False
    return todo_bien


def error_en_campo(mensaje: str, campos: dict, aviso: ft.Text | None = None) -> None:
    """Muestra [mensaje] debajo del campo al que se refiere. [campos] va de
    palabra clave a TextField, en orden de prioridad (ej. "apellido" antes que
    "nombre"). Si ninguno coincide, lo muestra en [aviso]. Borra errores viejos."""
    for c in campos.values():
        c.error = None
    texto_min = normalizar(mensaje)
    for clave, campo in campos.items():
        if normalizar(clave) in texto_min:
            campo.error = mensaje
            if aviso is not None:
                aviso.value = ""
            return
    if aviso is not None:
        aviso.value = mensaje


def revisar(campo: ft.TextField, funcion, *args, **kwargs):
    """Valida el valor del campo con [funcion]; marca el error en el campo y lo vuelve a lanzar."""
    try:
        v = funcion(campo.value, *args, **kwargs)
        campo.error = None
        return v
    except ValueError as e:
        campo.error = str(e)
        raise
