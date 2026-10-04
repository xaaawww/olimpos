# OLIMPOS GYM — Repositorio de rutinas (Dueño / Entrenador)
#
# Un entrenador/dueño arma LA rutina de cada socio (la de "origen" =
# "entrenador"); además el propio socio puede armarse las suyas desde la app
# móvil (origen = "socio"). En la base son filas de "rutinas" y sus
# ejercicios en "rutinaejercicio": un socio puede tener varias, con como
# mucho una del entrenador y una marcada como "activa" (la que sigue en
# Entrenar). Esta pantalla edita solo la del entrenador; las del socio se
# ven en modo lectura.
#
# La pantalla las sigue manejando como diccionarios de siempre:
# {
#   "id": "12",                     # cod_rutina (texto); ausente si todavía no se guardó
#   "socio_id": "uid123",           # UID de Firebase del socio
#   "origen": "entrenador",         # o "socio"
#   "activa": True,
#   "nombre": "Empuje pesado",
#   "creada_por": "Diego A. — Entrenador",
#   "actualizado": "2026-09-13T10:00:00",
#   "ejercicios": [
#       {"nombre": "Press de banca", "series_objetivo": 4, "peso_base_kg": 60.0,
#        "es_peso_corporal": False, "ejercicio_id": "17"},   # ejercicio_id None = escrito a mano
#   ]
# }

from datetime import datetime

import neon_db
from empleados_credenciales import id_empleado_actual

# Caché en memoria: uid -> lista de TODAS las rutinas de ese socio (de cualquier origen).
_cache_rutinas: dict[str, list[dict]] | None = None


def cargar_rutinas(forzar: bool = False) -> dict[str, list[dict]]:
    """Trae TODAS las rutinas de TODOS los socios (uid -> lista) — para
    saber en el listado quién ya tiene una del entrenador y quién no."""
    global _cache_rutinas
    if _cache_rutinas is None or forzar:
        rutinas = neon_db.consulta(
            "SELECT r.cod_rutina, s.firebase_uid, r.nombre, r.creada_por, r.origen, r.activa, r.fecha_actualizacion"
            " FROM rutinas r JOIN socios s USING (id_socio) WHERE s.firebase_uid IS NOT NULL ORDER BY r.cod_rutina"
        )
        ejercicios = neon_db.consulta(
            "SELECT cod_rutina, id_ejercicio, nombre, series, peso, es_peso_corporal FROM rutinaejercicio ORDER BY cod_rutina, orden"
        )
        de_rutina: dict[int, list[dict]] = {}
        for e in ejercicios:
            de_rutina.setdefault(e["cod_rutina"], []).append({
                "nombre": e["nombre"], "series_objetivo": e["series"] or 3, "peso_base_kg": float(e["peso"] or 0),
                "es_peso_corporal": e["es_peso_corporal"],
                "ejercicio_id": str(e["id_ejercicio"]) if e["id_ejercicio"] is not None else None,
            })
        agrupadas: dict[str, list[dict]] = {}
        for r in rutinas:
            agrupadas.setdefault(r["firebase_uid"], []).append({
                "id": str(r["cod_rutina"]), "socio_id": r["firebase_uid"], "origen": r["origen"], "activa": r["activa"],
                "nombre": r["nombre"], "creada_por": r["creada_por"] or "",
                "actualizado": r["fecha_actualizacion"].replace(tzinfo=None).isoformat(timespec="seconds"),
                "ejercicios": de_rutina.get(r["cod_rutina"], []),
            })
        _cache_rutinas = agrupadas
    return _cache_rutinas


def obtener_rutina_entrenador(socio_id: str) -> dict | None:
    """La única rutina de "origen" = "entrenador" de ese socio (la que edita
    esta pantalla) — ignora las que el socio se haya armado por su cuenta."""
    return next((r for r in cargar_rutinas().get(socio_id, []) if r.get("origen", "entrenador") == "entrenador"), None)


def obtener_rutinas_propias(socio_id: str) -> list[dict]:
    """Las rutinas que el socio armó por su cuenta desde la app — de solo
    lectura acá."""
    return [r for r in cargar_rutinas().get(socio_id, []) if r.get("origen") == "socio"]


def nueva_rutina(socio_id: str, creada_por: str) -> dict:
    # "activa" solo se prende sola si es la primera rutina que tiene ese
    # socio de cualquier origen — si ya seguía alguna (propia o de un
    # entrenador anterior), asignarle una nueva no le cambia qué sigue en
    # Entrenar sin que él lo elija.
    ya_tiene_alguna = len(cargar_rutinas().get(socio_id, [])) > 0
    return {
        "socio_id": socio_id,
        "origen": "entrenador",
        "activa": not ya_tiene_alguna,
        "nombre": "Nueva rutina",
        "creada_por": creada_por,
        "actualizado": datetime.now().isoformat(timespec="seconds"),
        "ejercicios": [],
    }


def nuevo_ejercicio_rutina() -> dict:
    # "ejercicio_id" es None hasta que el entrenador elige uno real del
    # catálogo (ver editor_rutinas.py) — no se permite un nombre suelto sin
    # referencia, así la rutina siempre usa ejercicios que ya existen (con
    # su técnica y zonas musculares reales). (El socio sí puede escribir uno
    # libre en las suyas propias, armadas desde la app móvil.)
    return {"ejercicio_id": None, "nombre": "", "series_objetivo": 3, "peso_base_kg": 0.0, "es_peso_corporal": False}


def guardar_rutina(rutina: dict) -> dict[str, list[dict]]:
    global _cache_rutinas
    rutina["actualizado"] = datetime.now().isoformat(timespec="seconds")
    rutina.setdefault("origen", "entrenador")
    rutina.setdefault("activa", False)
    with neon_db.transaccion() as cur:
        cur.execute("SELECT id_socio FROM socios WHERE firebase_uid = %s", (rutina["socio_id"],))
        id_socio = cur.fetchone()["id_socio"]
        if rutina["activa"]:
            # una sola activa por socio (índice único): se apagan las demás primero
            cur.execute("UPDATE rutinas SET activa = FALSE WHERE id_socio = %s AND activa AND cod_rutina IS DISTINCT FROM %s",
                        (id_socio, int(rutina["id"]) if rutina.get("id") else None))
        empleado = id_empleado_actual() if rutina["origen"] == "entrenador" else None
        if rutina.get("id"):
            cod = int(rutina["id"])
            cur.execute(
                "UPDATE rutinas SET nombre=%s, activa=%s, creada_por=%s, id_empleado=COALESCE(%s, id_empleado),"
                " fecha_actualizacion=now() WHERE cod_rutina=%s",
                (rutina["nombre"], rutina["activa"], rutina.get("creada_por"), empleado, cod),
            )
            cur.execute("DELETE FROM rutinaejercicio WHERE cod_rutina = %s", (cod,))
        else:
            cur.execute(
                "INSERT INTO rutinas (id_socio, id_empleado, nombre, creada_por, origen, activa) VALUES (%s,%s,%s,%s,%s,%s)"
                " RETURNING cod_rutina",
                (id_socio, empleado, rutina["nombre"], rutina.get("creada_por"), rutina["origen"], rutina["activa"]),
            )
            cod = cur.fetchone()["cod_rutina"]
            rutina["id"] = str(cod)
        for pos, e in enumerate(rutina["ejercicios"]):
            cur.execute(
                "INSERT INTO rutinaejercicio (cod_rutina, id_ejercicio, orden, nombre, series, peso, es_peso_corporal)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (cod, int(e["ejercicio_id"]) if e.get("ejercicio_id") else None, pos, e["nombre"],
                 e.get("series_objetivo", 3), e.get("peso_base_kg", 0), e.get("es_peso_corporal", False)),
            )
    cache = cargar_rutinas()
    lista = cache.setdefault(rutina["socio_id"], [])
    lista[:] = [r for r in lista if r.get("id") != rutina["id"]] + [rutina]
    return cache


def eliminar_rutina(rutina_id: str, socio_id: str) -> dict[str, list[dict]]:
    global _cache_rutinas
    neon_db.ejecutar("DELETE FROM rutinas WHERE cod_rutina = %s", (int(rutina_id),))
    cache = cargar_rutinas()
    if socio_id in cache:
        cache[socio_id] = [r for r in cache[socio_id] if r.get("id") != rutina_id]
    return cache
