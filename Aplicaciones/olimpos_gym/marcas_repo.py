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
RANGOS = ["Mortal", "Espartano", "Hoplita", "Héroe", "Semidiós", "Titán", "Coloso", "Olímpico", "Dios"]
NIVELES_MAX = {r: (1 if r == "Dios" else 3) for r in RANGOS}
TOTAL_NIVELES = sum(NIVELES_MAX.values())
PUNTOS_POR_NIVEL = 0.14
PESO_CORPORAL_REFERENCIA = 80.0  # el sistema de empleados no conoce el peso real del socio

# Dominadas y flexiones mueven el peso corporal + lo agregado, no solo
# "peso" (que en esos dos representa el agregado, 0 si es a peso corporal
# puro) — espejo de EJERCICIOS_PESO_CORPORAL en GamificacionData.kt.
EJERCICIOS_PESO_CORPORAL = {"Dominadas", "Flexiones"}


def calcular_1rm(peso: float, reps: int) -> float:
    return peso * (1 + reps / 30)


def carga_total(marca: dict) -> float:
    peso = marca.get("peso", 0)
    if marca.get("ejercicio") in EJERCICIOS_PESO_CORPORAL:
        return PESO_CORPORAL_REFERENCIA + peso
    return peso


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


def cargar_marcas() -> list[dict]:
    """Trae todas las marcas de todos los socios, más nuevas primero."""
    docs = _db().collection(COLECCION).stream()
    marcas = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        marcas.append(data)
    marcas.sort(key=lambda m: m.get("timestamp", 0), reverse=True)
    return marcas


def verificar_marca(marca_id: str, verificado_por: str) -> None:
    _db().collection(COLECCION).document(marca_id).update({
        "verificado": True,
        "verificado_por": verificado_por,
    })


def rechazar_marca(marca_id: str) -> None:
    """Una marca rechazada se borra sin más: deja de contar para el cálculo
    y el socio no se entera (no hace falta justificar cada rechazo menor)."""
    _db().collection(COLECCION).document(marca_id).delete()


def resumen_por_socio(marcas: list[dict]) -> dict[str, dict]:
    """Agrupa las marcas por socio y calcula, igual que resumenMuscular() en
    la app móvil, la marca MÁS RECIENTE por ejercicio (no la más alta
    histórica, ni la suma de todas) y el puntaje/nivel resultante por zona
    — cargar una marca nueva reemplaza a la anterior del mismo ejercicio."""
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

        puntajes: dict[str, float] = {}
        for m in vigente_por_ejercicio.values():
            relativo = calcular_1rm(carga_total(m), m["repeticiones"]) / PESO_CORPORAL_REFERENCIA
            for zona, peso in CONTRIBUCION_MUSCULAR.get(m["ejercicio"], {}).items():
                puntajes[zona] = puntajes.get(zona, 0) + relativo * peso

        resultado[socio_id] = {
            "nombre": nombre,
            "puntajes": puntajes,
            "nivel_promedio": nivel_desde_puntaje(sum(puntajes.values()) / len(puntajes)) if puntajes else "Sin marcas",
            "pendientes": sum(1 for m in ms if not m.get("verificado")),
            "total_marcas": len(ms),
        }
    return resultado
