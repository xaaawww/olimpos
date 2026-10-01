# OLIMPOS GYM — Ocupación en vivo del gimnasio
#
# No hay ningún lector de accesos conectado a Firestore (ver "ingresos" en
# app móvil: el socio solo marca que entró, nunca que salió, así que no
# alcanza para calcular "cuántos hay ADENTRO ahora mismo"). Antes, la
# tarjeta "Ocupación del gimnasio" de Inicio en la app móvil mostraba un
# número inventado que cambiaba solo cada pocos segundos (ver
# OcupacionEnVivo en HomeScreen.kt) — ahora ese número es real: lo carga el
# dueño desde acá, y queda guardado en Firestore para que la app lo lea.
#
# Vive en la colección "configuracion_app" (mismo lugar que la base de
# conocimiento de Argos) — es, ni más ni menos, otro dato de configuración
# del club.

from datetime import datetime

from dietas_repo import _db

COLECCION = "configuracion_app"
DOC_OCUPACION = "ocupacion"

CAPACIDAD_MAXIMA = 120


def obtener_ocupacion() -> dict:
    """{"personas": int, "actualizado_ms": int} — personas=0 y
    actualizado_ms=0 si el dueño todavía no cargó ningún valor."""
    doc = _db().collection(COLECCION).document(DOC_OCUPACION).get()
    if not doc.exists:
        return {"personas": 0, "actualizado_ms": 0}
    datos = doc.to_dict()
    return {
        "personas": int(datos.get("personas", 0)),
        "actualizado_ms": int(datos.get("actualizado_ms", 0)),
    }


def actualizar_ocupacion(personas: int) -> dict:
    personas = max(0, min(CAPACIDAD_MAXIMA, personas))
    ahora_ms = int(datetime.now().timestamp() * 1000)
    _db().collection(COLECCION).document(DOC_OCUPACION).set({
        "personas": personas,
        "actualizado_ms": ahora_ms,
    })
    return {"personas": personas, "actualizado_ms": ahora_ms}
