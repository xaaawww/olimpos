# OLIMPOS GYM — Ocupación en vivo del gimnasio
#
# No hay ningún lector de accesos conectado (el socio solo marca que entró,
# nunca que salió, así que no alcanza para calcular "cuántos hay ADENTRO
# ahora mismo"). Por eso el número lo carga el dueño desde acá. Cada vez que
# lo actualiza se agrega una fila a la tabla "aforo" (así queda el historial
# de ocupación) y la app móvil muestra siempre la fila más reciente.

import neon_db

CAPACIDAD_MAXIMA = 120


def obtener_ocupacion() -> dict:
    """{"personas": int, "actualizado_ms": int} — personas=0 y
    actualizado_ms=0 si el dueño todavía no cargó ningún valor."""
    fila = neon_db.una_fila(
        "SELECT cantidad_personas, (extract(epoch FROM fecha) * 1000)::bigint AS ms FROM aforo ORDER BY fecha DESC, id_aforo DESC LIMIT 1"
    )
    if not fila:
        return {"personas": 0, "actualizado_ms": 0}
    return {"personas": int(fila["cantidad_personas"]), "actualizado_ms": int(fila["ms"])}


def actualizar_ocupacion(personas: int) -> dict:
    personas = max(0, min(CAPACIDAD_MAXIMA, personas))
    fila = neon_db.una_fila(
        "INSERT INTO aforo (cantidad_personas, capacidad_maxima) VALUES (%s, %s)"
        " RETURNING (extract(epoch FROM fecha) * 1000)::bigint AS ms",
        (personas, CAPACIDAD_MAXIMA),
    )
    return {"personas": personas, "actualizado_ms": int(fila["ms"])}
