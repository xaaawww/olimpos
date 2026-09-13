# OLIMPOS GYM — Repositorio de marcas personales (verificación de récords)
#
# Las marcas las carga el socio desde la Calculadora/Mis marcas de la app
# móvil (colección "marcas" en Firestore, mismo proyecto que dietas y
# ejercicios). Acá el dueño/entrenador las revisa y verifica — el Bodygraph
# del socio muestra un rango por músculo calculado a partir de estas marcas,
# y necesita quedar claro cuándo ese cálculo todavía no fue confirmado por
# nadie del gimnasio (evita que alguien infle su rango cargando pesos falsos
# sin que se note).
#
# Forma de una "marca" en Firestore:
# {
#   "socio_id": "alex_rodriguez", "socio_nombre": "Alex Rodríguez",
#   "ejercicio": "Press banca", "peso": 82.0, "repeticiones": 2,
#   "fecha": "hoy", "timestamp": 1725900000000, "verificado": False,
#   "verificado_por": None,
# }

import math

from dietas_repo import _db

COLECCION = "marcas"

# Espejo de CONTRIBUCION_MUSCULAR en GamificacionData.kt (app móvil): si se
# cambia un valor ahí, hay que cambiarlo acá también para que el ranking
# general del sistema de empleados coincida con el Bodygraph del socio.
CONTRIBUCION_MUSCULAR = {
    "Press banca": {"PECHO_INFERIOR": 1.0, "PECHO_SUPERIOR": 0.5, "TRICEPS": 0.6, "DELTOIDES_ANTERIOR": 0.5},
    "Flexiones": {"PECHO_INFERIOR": 0.75, "PECHO_SUPERIOR": 0.5, "TRICEPS": 0.5, "DELTOIDES_ANTERIOR": 0.4, "ABDOMINALES": 0.25, "OBLICUOS": 0.25},
    "Dominadas": {"DORSALES": 1.0, "BICEPS": 0.65, "ANTEBRAZOS": 0.5, "TRAPECIO": 0.35},
    "Sentadilla": {"CUADRICEPS": 1.0, "GLUTEOS": 0.7, "ADUCTORES": 0.4, "OBLICUOS": 0.3, "LUMBARES": 0.3, "ISQUIOTIBIALES": 0.15, "ABDOMINALES": 0.2, "ABDUCTORES": 0.1},
    "Peso muerto": {"GLUTEOS": 0.95, "ISQUIOTIBIALES": 0.85, "LUMBARES": 0.8, "ANTEBRAZOS": 0.6, "TRAPECIO": 0.5, "CUADRICEPS": 0.2, "ADUCTORES": 0.15},
    "Elevaciones laterales": {"DELTOIDES_MEDIO": 1.0, "TRAPECIO": 0.2},
    "Pájaros": {"DELTOIDES_POSTERIOR": 1.0, "TRAPECIO": 0.3},
    "Elevación de talones": {"PANTORRILLAS": 1.0},
}

# Espejo de RangoMuscular en GamificacionData.kt: 9 rangos, 3 niveles cada
# uno salvo el último (Dios).
RANGOS = ["Mortal", "Hoplita", "Espartano", "Héroe", "Semidiós", "Titán", "Coloso", "Olímpico", "Dios"]
NIVELES_MAX = {r: (1 if r == "Dios" else 3) for r in RANGOS}
TOTAL_NIVELES = sum(NIVELES_MAX.values())
PUNTOS_POR_NIVEL = 0.14

# Referencia SOLO para el caso borde de un socio sin datos físicos todavía
# (no debería pasar — el onboarding de la app es obligatorio — pero cubre
# cuentas de prueba viejas o el instante entre el alta y el primer login).
PESO_CORPORAL_REFERENCIA = 80.0

# Dominadas y flexiones mueven el peso corporal + lo agregado, no solo
# "peso" (que en esos dos representa el agregado, 0 si es a peso corporal
# puro) — espejo de EJERCICIOS_PESO_CORPORAL en GamificacionData.kt.
EJERCICIOS_PESO_CORPORAL = {"Dominadas", "Flexiones"}

# Espejo de ANCLAS_FUERZA en GamificacionData.kt: piso (principiante, cae en
# Mortal 1) y techo (Dios, ~15% por encima del nivel "Elite" publicado —
# el 0,1% más fuerte) de cada ejercicio, en múltiplos del peso corporal,
# separado por sexo. Ver el comentario de esa tabla en GamificacionData.kt
# para las fuentes — si se cambia un valor ahí, cambiarlo acá también.
ANCLAS_FUERZA = {
    "Sentadilla":            {"beginner_m": 0.75,  "dios_m": 2.90,  "beginner_f": 0.60,  "dios_f": 2.32},
    "Press banca":           {"beginner_m": 0.50,  "dios_m": 2.30,  "beginner_f": 0.33,  "dios_f": 1.50},
    "Peso muerto":           {"beginner_m": 1.00,  "dios_m": 3.15,  "beginner_f": 0.80,  "dios_f": 2.52},
    "Dominadas":             {"beginner_m": 1.00,  "dios_m": 2.90,  "beginner_f": 1.00,  "dios_f": 2.65},
    "Flexiones":             {"beginner_m": 0.65,  "dios_m": 2.20,  "beginner_f": 0.42,  "dios_f": 1.43},
    "Elevaciones laterales": {"beginner_m": 0.07,  "dios_m": 0.33,  "beginner_f": 0.053, "dios_f": 0.25},
    "Pájaros":               {"beginner_m": 0.056, "dios_m": 0.264, "beginner_f": 0.042, "dios_f": 0.20},
    "Elevación de talones":  {"beginner_m": 0.60,  "dios_m": 2.75,  "beginner_f": 0.48,  "dios_f": 2.20},
}

# Espejo de MINIMO_EJERCICIOS_PARA_CLASIFICACION en GamificacionData.kt.
MINIMO_EJERCICIOS_PARA_CLASIFICACION = 3


def calcular_1rm(peso: float, reps: int) -> float:
    return peso * (1 + reps / 30)


def carga_total(marca: dict, peso_corporal_kg: float = PESO_CORPORAL_REFERENCIA) -> float:
    peso = marca.get("peso", 0)
    if marca.get("ejercicio") in EJERCICIOS_PESO_CORPORAL:
        return peso_corporal_kg + peso
    return peso


def puntaje_de_marca(marca: dict, peso_corporal_kg: float, sexo: str | None) -> float:
    """Espejo de puntajeDeMarca() en GamificacionData.kt: progresión
    logarítmica entre el piso (principiante) y el techo (Dios) de la
    ancla de fuerza del ejercicio — no lineal, porque en la vida real
    cuesta mucho menos pasar de principiante a novato que de avanzado a
    elite."""
    if peso_corporal_kg <= 0:
        return 0.0
    ancla = ANCLAS_FUERZA.get(marca.get("ejercicio"))
    if ancla is None:
        return 0.0
    if sexo == "MASCULINO":
        piso, techo = ancla["beginner_m"], ancla["dios_m"]
    elif sexo == "FEMENINO":
        piso, techo = ancla["beginner_f"], ancla["dios_f"]
    else:
        piso = (ancla["beginner_m"] + ancla["beginner_f"]) / 2
        techo = (ancla["dios_m"] + ancla["dios_f"]) / 2
    ratio = carga_total(marca, peso_corporal_kg) / peso_corporal_kg
    if ratio <= 0:
        return 0.0
    progreso = math.log(ratio / piso) / math.log(techo / piso)
    progreso = min(max(progreso, 0.0), 1.0)
    return progreso * TOTAL_NIVELES * PUNTOS_POR_NIVEL


_cache_datos_fisicos: dict[str, dict] | None = None


def datos_fisicos_de_todos(forzar: bool = False) -> dict[str, dict]:
    """peso_kg y sexo reales de cada socio (colección "datos_fisicos", la
    completa el propio socio en el onboarding obligatorio de la app) — una
    sola lectura para todos, cacheada en memoria (cambia poco: cada socio
    la completa una sola vez, al principio)."""
    global _cache_datos_fisicos
    if _cache_datos_fisicos is None or forzar:
        try:
            docs = _db().collection("datos_fisicos").stream()
            _cache_datos_fisicos = {d.id: d.to_dict() for d in docs}
        except Exception:
            return {}
    return _cache_datos_fisicos


def nivel_desde_puntaje(puntaje: float) -> str:
    indice = min(max(int(puntaje / PUNTOS_POR_NIVEL), 0), TOTAL_NIVELES - 1)
    restante = indice
    for rango in RANGOS:
        max_n = NIVELES_MAX[rango]
        if restante < max_n:
            nivel = restante + 1
            return rango if rango == "Dios" else f"{rango} {nivel}"
        restante -= max_n
    return "Dios"


def todos_los_niveles() -> list[str]:
    """Los 25 rangos de la Escalera del Olimpo, de Dios (el más fuerte) a
    Mortal 1 (el más flojo) — para la grilla de 5x5 de Verificación de
    Marcas."""
    niveles = []
    for rango in RANGOS:
        for n in range(1, NIVELES_MAX[rango] + 1):
            niveles.append(rango if rango == "Dios" else f"{rango} {n}")
    return list(reversed(niveles))


_SLUG_RANGO = {
    "Mortal": "mortal", "Hoplita": "hoplita", "Espartano": "espartano",
    "Héroe": "heroe", "Semidiós": "semidios", "Titán": "titan",
    "Coloso": "coloso", "Olímpico": "olimpico", "Dios": "dios",
}


def imagen_de_nivel(nivel: str) -> str:
    """"Héroe 3" -> "rangos/rango_heroe_3.png"; "Dios" -> "rangos/rango_dios.png"
    — mismas imágenes que usa la app móvil (ver AppMovil/.../res/drawable/)."""
    partes = nivel.rsplit(" ", 1)
    if len(partes) == 2 and partes[1].isdigit():
        rango, n = partes
        return f"rangos/rango_{_SLUG_RANGO.get(rango, rango.lower())}_{n}.png"
    return f"rangos/rango_{_SLUG_RANGO.get(nivel, nivel.lower())}.png"


def ranking_por_rango(marcas: list[dict], datos_fisicos: dict[str, dict] | None = None) -> dict[str, list[dict]]:
    """Agrupa los socios por su rango EXACTO (el mismo que ven en la
    Escalera del Olimpo de la app) — para la grilla de Verificación de
    Marcas. Cada entrada trae lo necesario para ordenar (puntaje) y para
    buscar (nombre, socio_id, email, dni). Solo entran los socios que
    llegan al mínimo de ejercicios (ver MINIMO_EJERCICIOS_PARA_CLASIFICACION),
    igual que en la app."""
    if datos_fisicos is None:
        datos_fisicos = datos_fisicos_de_todos()

    por_socio: dict[str, list[dict]] = {}
    for m in marcas:
        por_socio.setdefault(m.get("socio_id", "?"), []).append(m)

    agrupado: dict[str, list[dict]] = {}
    for socio_id, ms in por_socio.items():
        nombre = ms[0].get("socio_nombre", socio_id)
        vigente_por_ejercicio: dict[str, dict] = {}
        for m in ms:
            ej = m.get("ejercicio")
            actual = vigente_por_ejercicio.get(ej)
            if actual is None or m.get("timestamp", 0) > actual.get("timestamp", 0):
                vigente_por_ejercicio[ej] = m
        if len(vigente_por_ejercicio) < MINIMO_EJERCICIOS_PARA_CLASIFICACION:
            continue

        datos = datos_fisicos.get(socio_id, {})
        peso_corporal = datos.get("peso_kg", PESO_CORPORAL_REFERENCIA)
        sexo = datos.get("sexo")
        puntajes = [puntaje_de_marca(m, peso_corporal, sexo) for m in vigente_por_ejercicio.values()]
        puntaje_general = sum(puntajes) / len(puntajes)

        agrupado.setdefault(nivel_desde_puntaje(puntaje_general), []).append({
            "socio_id": socio_id,
            "nombre": nombre,
            "puntaje": puntaje_general,
        })

    for socios in agrupado.values():
        socios.sort(key=lambda s: s["puntaje"], reverse=True)
    return agrupado


_cache_marcas: list[dict] | None = None


def cargar_marcas(forzar: bool = False) -> list[dict]:
    """Trae todas las marcas de todos los socios, más nuevas primero.
    Cacheada en memoria — [verificar_marca]/[rechazar_marca] actualizan la
    caché directo, así que no hace falta [forzar] después de esas acciones;
    solo si otro empleado cargó/verificó algo desde otra máquina."""
    global _cache_marcas
    if _cache_marcas is None or forzar:
        docs = _db().collection(COLECCION).stream()
        marcas = []
        for d in docs:
            data = d.to_dict()
            data["id"] = d.id
            marcas.append(data)
        marcas.sort(key=lambda m: m.get("timestamp", 0), reverse=True)
        _cache_marcas = marcas
    return _cache_marcas


def verificar_marca(marca_id: str, verificado_por: str) -> None:
    _db().collection(COLECCION).document(marca_id).update({
        "verificado": True,
        "verificado_por": verificado_por,
    })
    if _cache_marcas is not None:
        for m in _cache_marcas:
            if m.get("id") == marca_id:
                m["verificado"] = True
                m["verificado_por"] = verificado_por
                break


def rechazar_marca(marca_id: str) -> None:
    """Una marca rechazada se borra sin más: deja de contar para el cálculo
    y el socio no se entera (no hace falta justificar cada rechazo menor)."""
    global _cache_marcas
    _db().collection(COLECCION).document(marca_id).delete()
    if _cache_marcas is not None:
        _cache_marcas = [m for m in _cache_marcas if m.get("id") != marca_id]


def resumen_por_socio(marcas: list[dict], datos_fisicos: dict[str, dict] | None = None) -> dict[str, dict]:
    """Agrupa las marcas por socio y calcula la marca MÁS RECIENTE por
    ejercicio (no la más alta histórica, ni la suma de todas) — cargar una
    marca nueva reemplaza a la anterior del mismo ejercicio, igual que en
    la app móvil. [datos_fisicos] es el resultado de
    [datos_fisicos_de_todos] — se puede pasar ya cargado para no repetir la
    lectura a Firestore si el que llama ya lo tiene (ver verificacion_marcas.py).

    "puntajes" (por zona muscular) usa la misma calibración que el "nivel
    general" para que sea consistente, pero el "nivel_promedio" que se
    muestra en el ranking se calcula promediando por EJERCICIO, no por
    zona — si no, un socio que solo hace los 3 grandes levantamientos
    queda con deltoides medio/posterior y pantorrillas en cero para
    siempre (son las únicas 3 zonas que entrenan las isolaciones de la
    Calculadora), arrastrando su promedio para abajo sin motivo. Por el
    mismo criterio que la app, un socio con menos de
    MINIMO_EJERCICIOS_PARA_CLASIFICACION ejercicios distintos todavía no
    tiene "nivel general"."""
    if datos_fisicos is None:
        datos_fisicos = datos_fisicos_de_todos()

    por_socio: dict[str, list[dict]] = {}
    for m in marcas:
        por_socio.setdefault(m.get("socio_id", "?"), []).append(m)

    resultado = {}
    for socio_id, ms in por_socio.items():
        nombre = ms[0].get("socio_nombre", socio_id)
        vigente_por_ejercicio: dict[str, dict] = {}
        for m in ms:
            ej = m.get("ejercicio")
            actual = vigente_por_ejercicio.get(ej)
            if actual is None or m.get("timestamp", 0) > actual.get("timestamp", 0):
                vigente_por_ejercicio[ej] = m

        datos = datos_fisicos.get(socio_id, {})
        peso_corporal = datos.get("peso_kg", PESO_CORPORAL_REFERENCIA)
        sexo = datos.get("sexo")

        puntajes_por_ejercicio: dict[str, float] = {}
        puntajes_por_zona: dict[str, float] = {}
        for ejercicio, m in vigente_por_ejercicio.items():
            puntaje = puntaje_de_marca(m, peso_corporal, sexo)
            puntajes_por_ejercicio[ejercicio] = puntaje
            for zona, peso in CONTRIBUCION_MUSCULAR.get(ejercicio, {}).items():
                puntajes_por_zona[zona] = puntajes_por_zona.get(zona, 0) + puntaje * peso

        clasifica = len(vigente_por_ejercicio) >= MINIMO_EJERCICIOS_PARA_CLASIFICACION
        nivel_promedio = (
            nivel_desde_puntaje(sum(puntajes_por_ejercicio.values()) / len(puntajes_por_ejercicio))
            if clasifica else "Sin clasificar"
        )

        resultado[socio_id] = {
            "nombre": nombre,
            "puntajes": puntajes_por_zona,
            "nivel_promedio": nivel_promedio,
            "pendientes": sum(1 for m in ms if not m.get("verificado")),
            "total_marcas": len(ms),
        }
    return resultado
