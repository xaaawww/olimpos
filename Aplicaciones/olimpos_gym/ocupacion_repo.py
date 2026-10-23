# OLIMPOS GYM — Ocupación en vivo del gimnasio
#
# Se calcula sola con las entradas reales: cada vez que un socio toca
# "Mostrar carnet de acceso" en la app, la API agrega una fila a la tabla
# "accesos". No hay registro de SALIDA, así que se cuenta como "adentro" a
# cada socio que entró en los últimos MINUTOS_EN_EL_CLUB (mismo valor que en
# ApiWorker/src/util.ts, para que la app y este sistema muestren lo mismo).
#
# Antes el número lo cargaba el dueño a mano en la tabla "aforo"; esa tabla
# queda solo como historial y ya no se usa para la ocupación.

import neon_db

CAPACIDAD_MAXIMA = 120
MINUTOS_EN_EL_CLUB = 90


def capacidad() -> int:
    """Capacidad del club: la que puso el dueño en Configuración → Club (si
    no la cambió, CAPACIDAD_MAXIMA, el mismo valor que usa la API)."""
    import configuracion_repo
    return int(configuracion_repo.club().get("capacidad_maxima") or CAPACIDAD_MAXIMA)


def obtener_ocupacion() -> dict:
    """{"personas": int, "actualizado_ms": int}."""
    fila = neon_db.una_fila(
        "SELECT count(DISTINCT id_socio) AS personas, (extract(epoch FROM now()) * 1000)::bigint AS ahora_ms"
        " FROM accesos WHERE resultado = 'permitido' AND fecha > now() - make_interval(mins => %s)",
        (MINUTOS_EN_EL_CLUB,),
    )
    return {"personas": int(fila["personas"]), "actualizado_ms": int(fila["ahora_ms"])}


def entradas_recientes() -> list[dict]:
    """Los socios que ahora cuentan como "adentro", el más reciente primero:
    [{"nombre": "Matias Bellu", "entrada_ms": 1758000000000}]."""
    return neon_db.consulta(
        "SELECT trim(s.nombre || ' ' || s.apellido) AS nombre,"
        " (extract(epoch FROM max(a.fecha)) * 1000)::bigint AS entrada_ms"
        " FROM accesos a JOIN socios s USING (id_socio)"
        " WHERE a.resultado = 'permitido' AND a.fecha > now() - make_interval(mins => %s)"
        " GROUP BY s.id_socio, s.nombre, s.apellido ORDER BY entrada_ms DESC",
        (MINUTOS_EN_EL_CLUB,),
    )
