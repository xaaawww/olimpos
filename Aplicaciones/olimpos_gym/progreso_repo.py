# OLIMPOS GYM — Progreso físico de cada socio (datos de la app)
#
# Todo sale de lo que el socio registra en la app:
#   seriesentrenamiento  cada serie (ejercicio, peso, repeticiones, fecha)
#   progresopeso / salud su peso (y altura / % de grasa si los cargó)
#   objetivos            FUERZA, HIPERTROFIA o SALUD
#
# El trabajo de cada músculo se mide en SERIES EFECTIVAS: cada serie suma 1
# al músculo principal del ejercicio y 0,5 a los secundarios (los puntos que
# tiene el ejercicio en el editor). Es la medida que usan los entrenadores
# para armar rutinas: entre ~10 y ~20 series por semana por grupo muscular
# es el rango útil; menos se queda corto, más suele ser demasiado.
# Con eso se pinta el bodygraph y se arman las recomendaciones.

from collections import defaultdict
from datetime import date, datetime, timedelta

import neon_db
import ejercicios_repo

PERIODOS = {28: "Últimas 4 semanas", 90: "Últimos 3 meses", 180: "Últimos 6 meses", 3650: "Todo"}
SERIES_MIN, SERIES_MAX = 10, 20        # series efectivas por semana por grupo (rango útil)
PESO_SECUNDARIO = 0.5
# Pares que conviene mantener parejos (empuje / tirón, adelante / atrás)
EQUILIBRIOS = [
    ("Pecho", "Espalda", "empuje y tirón"),
    ("CUADRICEPS", "ISQUIOTIBIALES", "la parte de adelante y de atrás de las piernas"),
    ("DELTOIDES_ANTERIOR", "DELTOIDES_POSTERIOR", "el hombro de adelante y el de atrás"),
]


def _hoy() -> date:
    return date.today()


def lista_socios() -> list[dict]:
    """Una fila por socio para el listado: nombre, último entrenamiento,
    días entrenados en las últimas 4 semanas, peso y objetivo."""
    return neon_db.consulta(
        "SELECT s.id_socio, trim(s.nombre || ' ' || s.apellido) AS nombre, s.email,"
        " (SELECT max(se.fecha)::date FROM seriesentrenamiento se WHERE se.id_socio = s.id_socio) AS ultimo,"
        " (SELECT count(DISTINCT se.fecha::date) FROM seriesentrenamiento se WHERE se.id_socio = s.id_socio"
        "   AND se.fecha > now() - interval '28 days') AS dias_28,"
        " (SELECT pp.peso FROM progresopeso pp WHERE pp.id_socio = s.id_socio ORDER BY pp.fecha DESC LIMIT 1) AS peso,"
        " (SELECT o.tipo FROM objetivos o WHERE o.id_socio = s.id_socio AND o.estado = 'activo'"
        "   ORDER BY o.fecha_registro DESC LIMIT 1) AS objetivo"
        " FROM socios s WHERE s.estado = 'activo'"
        " ORDER BY ultimo DESC NULLS LAST, nombre")


# ── ejercicio → músculos ──
def _indice_ejercicios():
    ejercicios = ejercicios_repo.cargar_ejercicios()
    por_id = {e["id"]: e for e in ejercicios}
    por_nombre = {e["nombre"].strip().lower(): e for e in ejercicios}
    return ejercicios, por_id, por_nombre


def _musculos(ej: dict | None) -> list[tuple[str, float]]:
    """[(zona, peso)]: el primer punto es el principal (1), el resto 0,5."""
    if not ej:
        return []
    zonas = list(dict.fromkeys(p["zona"] for p in ej.get("puntos") or []))
    return [(z, 1.0 if i == 0 else PESO_SECUNDARIO) for i, z in enumerate(zonas)]


def _coma(v: float) -> str:
    """1 decimal con coma, como se escribe acá (2,5)."""
    return f"{v:.1f}".replace(".", ",")


def _uno_rm(peso: float, reps: int) -> float:
    """1RM estimado (fórmula de Epley); con 1 repetición es el mismo peso."""
    return peso if reps <= 1 else peso * (1 + reps / 30)


# ── detalle de un socio ──
def detalle(id_socio: int, dias: int = 90) -> dict:
    hoy = _hoy()
    desde = hoy - timedelta(days=dias - 1)
    desde_anterior = desde - timedelta(days=dias)
    socio = neon_db.una_fila(
        "SELECT s.id_socio, trim(s.nombre || ' ' || s.apellido) AS nombre, s.sexo, s.fecha_registro::date AS registro,"
        " s.nivel_experiencia, (SELECT o.tipo FROM objetivos o WHERE o.id_socio = s.id_socio AND o.estado = 'activo'"
        "   ORDER BY o.fecha_registro DESC LIMIT 1) AS objetivo FROM socios s WHERE s.id_socio = %s", (id_socio,))
    if not socio:
        raise ValueError("No existe ese socio")

    filas = neon_db.consulta(
        "SELECT s.ejercicio, s.peso, s.repeticiones, s.es_peso_corporal, s.fecha,"
        " (s.fecha AT TIME ZONE 'America/Argentina/Buenos_Aires')::date AS dia, re.id_ejercicio"
        " FROM seriesentrenamiento s LEFT JOIN rutinaejercicio re ON re.id_rutina_ejercicio = s.id_rutina_ejercicio"
        " WHERE s.id_socio = %s ORDER BY s.fecha", (id_socio,))
    pesos = neon_db.consulta(
        "SELECT fecha, peso FROM progresopeso WHERE id_socio = %s"
        " UNION SELECT fecha::date, peso FROM salud WHERE id_socio = %s AND peso IS NOT NULL ORDER BY 1",
        (id_socio, id_socio))
    salud = neon_db.una_fila(
        "SELECT altura, porcentaje_grasa FROM salud WHERE id_socio = %s AND (altura IS NOT NULL OR porcentaje_grasa IS NOT NULL)"
        " ORDER BY fecha DESC LIMIT 1", (id_socio,)) or {}

    ejercicios, por_id, por_nombre = _indice_ejercicios()
    peso_corporal = float(pesos[-1]["peso"]) if pesos else None

    series = []
    for f in filas:
        ej = por_id.get(str(f["id_ejercicio"])) if f["id_ejercicio"] else None
        ej = ej or por_nombre.get((f["ejercicio"] or "").strip().lower())
        peso = float(f["peso"]) if f["peso"] is not None else 0.0
        if f["es_peso_corporal"] or (not peso and peso_corporal):
            peso = peso + (peso_corporal or 0)          # dominadas, fondos...: cuenta el propio peso
        series.append({"dia": f["dia"], "ejercicio": ej["nombre"] if ej else (f["ejercicio"] or "Ejercicio"),
                       "ej": ej, "peso": peso, "reps": int(f["repeticiones"]),
                       "volumen": peso * int(f["repeticiones"])})

    actuales = [s for s in series if s["dia"] >= desde]
    anteriores = [s for s in series if desde_anterior <= s["dia"] < desde]
    semanas = max(1.0, min(dias, (hoy - min((s["dia"] for s in actuales), default=hoy)).days + 1) / 7) \
        if dias >= 3650 else dias / 7

    # ── trabajo por músculo ──
    por_zona = defaultdict(float)
    sin_musculo = 0
    for s in actuales:
        musculos = _musculos(s["ej"])
        if not musculos:
            sin_musculo += 1
        for z, w in musculos:
            por_zona[z] += w
    por_grupo = defaultdict(float)
    for z, v in por_zona.items():
        por_grupo[ejercicios_repo.GRUPO_DE_ZONA.get(z, "Otros")] += v
    grupos = []
    for g in ejercicios_repo.GRUPOS:
        total = por_grupo.get(g, 0.0)
        grupos.append({"grupo": g, "series": total, "por_semana": total / semanas,
                       "zonas": {z: por_zona[z] for z in ejercicios_repo.GRUPOS[g] if por_zona.get(z)}})
    # el bodygraph compara los músculos ENTRE SÍ: el más trabajado va a pleno
    maximo = max(por_zona.values(), default=0)
    intensidad = {z: v / maximo for z, v in por_zona.items()} if maximo else {}

    # ── sesiones (un día = una sesión) ──
    por_dia = defaultdict(list)
    for s in actuales:
        por_dia[s["dia"]].append(s)
    sesiones = []
    for dia in sorted(por_dia, reverse=True):
        ss = por_dia[dia]
        grupos_dia = defaultdict(float)
        for s in ss:
            for z, w in _musculos(s["ej"]):
                grupos_dia[ejercicios_repo.GRUPO_DE_ZONA.get(z, "Otros")] += w
        sesiones.append({"dia": dia, "series": len(ss), "ejercicios": len({s["ejercicio"] for s in ss}),
                         "volumen": sum(s["volumen"] for s in ss),
                         "grupos": [g for g, _ in sorted(grupos_dia.items(), key=lambda x: -x[1])][:3]})

    # ── progreso por ejercicio (mejor 1RM estimado de cada día) ──
    por_ej = defaultdict(lambda: defaultdict(float))
    for s in actuales:
        dia = por_ej[s["ejercicio"]]
        dia[s["dia"]] = max(dia[s["dia"]], _uno_rm(s["peso"], s["reps"]))
    progreso_ej = []
    for nombre, dias_rm in por_ej.items():
        orden = sorted(dias_rm.items())
        primero, ultimo = orden[0][1], orden[-1][1]
        cambio = ((ultimo - primero) / primero * 100) if primero else 0
        estancado = len(orden) >= 3 and max(v for _, v in orden[-3:]) <= orden[-3][1] * 1.01
        ej_series = [s for s in actuales if s["ejercicio"] == nombre]
        progreso_ej.append({
            "ejercicio": nombre, "sesiones": len(orden), "series": len(ej_series),
            "mejor_peso": max(s["peso"] for s in ej_series), "rm_inicial": primero, "rm_actual": ultimo,
            "cambio": cambio, "estancado": estancado, "ej": next((s["ej"] for s in ej_series if s["ej"]), None),
            "reps_prom": sum(s["reps"] for s in ej_series) / len(ej_series),
            "historia": [v for _, v in orden],
        })
    progreso_ej.sort(key=lambda p: (-p["sesiones"], -p["series"]))

    # ── semanas (para el gráfico de volumen) ──
    inicio_semana = desde - timedelta(days=desde.weekday())
    if dias >= 3650 and actuales:
        primero_dia = min(s["dia"] for s in actuales)
        inicio_semana = primero_dia - timedelta(days=primero_dia.weekday())
    volumen_semanal = []
    d = inicio_semana
    while d <= hoy:
        fin = d + timedelta(days=6)
        ss = [s for s in actuales if d <= s["dia"] <= fin]
        volumen_semanal.append({"semana": d, "volumen": sum(s["volumen"] for s in ss), "series": len(ss),
                                "dias": len({s["dia"] for s in ss})})
        d += timedelta(days=7)

    # ── tarjetas ──
    pesos_periodo = [p for p in pesos if p["fecha"] >= desde]
    peso_inicio = float(pesos_periodo[0]["peso"]) if pesos_periodo else None
    dias_act, dias_ant = len(por_dia), len({s["dia"] for s in anteriores})
    vol_act, vol_ant = sum(s["volumen"] for s in actuales), sum(s["volumen"] for s in anteriores)
    altura = float(salud["altura"]) if salud.get("altura") else None
    if altura and altura > 3:
        altura /= 100                                     # cargada en cm
    imc = round(peso_corporal / (altura ** 2), 1) if (peso_corporal and altura) else None
    ultimo = max((s["dia"] for s in series), default=None)
    resumen = {
        "peso": peso_corporal, "peso_cambio": (peso_corporal - peso_inicio) if (peso_corporal and peso_inicio
                                                                               and len(pesos_periodo) > 1) else None,
        "dias": dias_act, "dias_cambio": dias_act - dias_ant if anteriores or dias < 3650 else None,
        "por_semana": dias_act / semanas, "volumen": vol_act,
        "volumen_cambio": ((vol_act - vol_ant) / vol_ant * 100) if vol_ant else None,
        "series": len(actuales), "imc": imc, "grasa": float(salud["porcentaje_grasa"]) if salud.get("porcentaje_grasa") else None,
        "ultimo": ultimo, "dias_sin_entrenar": (hoy - ultimo).days if ultimo else None, "sin_musculo": sin_musculo,
    }

    datos = {"socio": socio, "dias": dias, "desde": desde, "semanas": semanas, "resumen": resumen,
             "pesos": [{"fecha": p["fecha"], "peso": float(p["peso"])} for p in pesos],
             "grupos": grupos, "zonas": dict(por_zona), "intensidad": intensidad, "sesiones": sesiones,
             "ejercicios": progreso_ej, "volumen_semanal": volumen_semanal}
    datos["recomendaciones"] = recomendaciones(datos, ejercicios)
    return datos


# ── recomendaciones para mejorar la rutina ──
def _sugerir(ejercicios: list[dict], zonas: list[str], hechos: set[str]) -> str | None:
    """Un ejercicio publicado cuyo músculo principal esté en esas zonas y que
    el socio no haya hecho en el período."""
    for e in sorted(ejercicios, key=lambda x: x["nombre"]):
        principal = (e.get("puntos") or [{}])[0].get("zona")
        if e.get("publicado") and principal in zonas and e["nombre"] not in hechos:
            return e["nombre"]
    return None


def recomendaciones(d: dict, ejercicios: list[dict]) -> list[dict]:
    r = d["resumen"]
    rec = []

    def agregar(nivel, icono, titulo, detalle):
        rec.append({"nivel": nivel, "icono": icono, "titulo": titulo, "detalle": detalle})

    if not r["series"]:
        if r["ultimo"]:
            agregar("alta", "EVENT_BUSY", f"No entrenó en este período",
                    f"Su último entrenamiento registrado fue el {r['ultimo']:%d/%m/%Y}. Conviene contactarlo.")
        else:
            agregar("alta", "EVENT_BUSY", "Todavía no registró entrenamientos",
                    "Cuando cargue series desde la app aparecen acá su trabajo por músculo y su progreso.")
        return rec

    hechos = {p["ejercicio"] for p in d["ejercicios"]}
    if r["dias_sin_entrenar"] is not None and r["dias_sin_entrenar"] >= 7:
        agregar("alta", "SCHEDULE", f"Hace {r['dias_sin_entrenar']} días que no entrena",
                "Retomar con una sesión más liviana que la última para no lesionarse.")
    if r["por_semana"] < 2:
        agregar("media", "CALENDAR_MONTH", f"Entrena {_coma(r['por_semana'])} días por semana",
                "Con 3 días por semana (cada músculo 2 veces) se progresa bastante más. Probar una rutina dividida en 3.")

    # grupos con poco, nada o demasiado trabajo
    for g in d["grupos"]:
        zonas = ejercicios_repo.GRUPOS[g["grupo"]]
        if g["series"] == 0:
            sug = _sugerir(ejercicios, zonas, hechos)
            agregar("alta", "PERSON_SEARCH", f"No trabajó {g['grupo'].lower()}",
                    f"0 series en el período." + (f" Sumar por ejemplo {sug}, 3 series." if sug else ""))
        elif g["por_semana"] < SERIES_MIN * 0.6:
            sug = _sugerir(ejercicios, zonas, hechos)
            faltan = max(1, round(SERIES_MIN - g["por_semana"]))
            agregar("media", "TRENDING_DOWN", f"Poco trabajo de {g['grupo'].lower()}",
                    f"{_coma(g['por_semana'])} series por semana (lo útil es {SERIES_MIN}–{SERIES_MAX}). "
                    f"Sumar unas {faltan} por semana" + (f", por ejemplo con {sug}." if sug else "."))
        elif g["por_semana"] > SERIES_MAX * 1.2:
            agregar("media", "WARNING_AMBER", f"Mucho volumen de {g['grupo'].lower()}",
                    f"{g['por_semana']:.0f} series por semana: más de {SERIES_MAX} suele no rendir y cansa. "
                    "Bajar series o repartirlas en más días.")

    # equilibrios
    zonas, grupos = d["zonas"], {g["grupo"]: g["series"] for g in d["grupos"]}
    for a, b, que in EQUILIBRIOS:
        va = grupos.get(a, zonas.get(a, 0))
        vb = grupos.get(b, zonas.get(b, 0))
        if max(va, vb) >= 4 and min(va, vb) < max(va, vb) / 1.6:
            fuerte, debil = (a, b) if va > vb else (b, a)
            nombre = lambda x: x.lower() if x in ejercicios_repo.GRUPOS else ejercicios_repo.NOMBRE_CORTO.get(x, x)
            zonas_debil = ejercicios_repo.GRUPOS.get(debil, [debil])
            sug = _sugerir(ejercicios, zonas_debil, hechos)
            agregar("media", "BALANCE", f"Desequilibrio entre {que}",
                    f"Hace {_coma(max(va, vb) / max(min(va, vb), 0.5))} veces más trabajo de {nombre(fuerte)} que de "
                    f"{nombre(debil)}." + (f" Agregar {sug}." if sug else ""))

    # ejercicios estancados y los que mejoran
    for p in d["ejercicios"]:
        if p["estancado"]:
            agregar("media", "PAUSE_CIRCLE_OUTLINE", f"{p['ejercicio']}: sin progreso en las últimas 3 sesiones",
                    "Subir 2,5 kg con menos repeticiones, cambiar el rango (ej. 6-8) o probar una variante.")
    mejores = [p for p in d["ejercicios"] if p["sesiones"] >= 2 and p["cambio"] >= 5]
    if mejores:
        p = max(mejores, key=lambda x: x["cambio"])
        agregar("baja", "TRENDING_UP", f"{p['ejercicio']}: +{p['cambio']:.0f}% de fuerza",
                f"El 1RM estimado pasó de {p['rm_inicial']:.0f} a {p['rm_actual']:.0f} kg. Mantener la progresión.")

    # repeticiones según el objetivo
    reps = sum(p["reps_prom"] * p["series"] for p in d["ejercicios"]) / max(1, sum(p["series"] for p in d["ejercicios"]))
    objetivo = d["socio"].get("objetivo")
    if objetivo == "FUERZA" and reps > 10:
        agregar("media", "FITNESS_CENTER", f"Su objetivo es fuerza y hace {reps:.0f} repeticiones en promedio",
                "Para fuerza rinde más trabajar pesado: 3 a 6 repeticiones en los ejercicios principales.")
    elif objetivo == "HIPERTROFIA" and (reps < 6 or reps > 15):
        agregar("media", "FITNESS_CENTER", f"Su objetivo es ganar músculo y hace {reps:.0f} repeticiones en promedio",
                "Para hipertrofia lo ideal es la mayoría de las series entre 8 y 12 repeticiones.")
    elif objetivo == "SALUD" and r["por_semana"] < 3:
        agregar("baja", "FAVORITE_BORDER", "Objetivo salud: sumar constancia",
                "Más que el peso, importa entrenar 3 veces por semana y variar los ejercicios.")

    if r["sin_musculo"]:
        agregar("baja", "HELP_OUTLINE", f"{r['sin_musculo']} series de ejercicios sin músculos cargados",
                "Son ejercicios escritos a mano que no están en el catálogo: no cuentan en el bodygraph.")

    orden = {"alta": 0, "media": 1, "baja": 2}
    rec.sort(key=lambda x: orden[x["nivel"]])
    return rec
