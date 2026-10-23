# OLIMPOS GYM — Repositorio de asistencia (pantalla "Asistencia" y dashboard)
#
# Todo sale de la tabla "accesos": una fila por entrada al club. La agrega la
# API cuando el socio toca "Mostrar carnet de acceso" en la app, o este mismo
# sistema cuando recepción registra una entrada a mano (registrar_entrada).
# No hay registro de salida: "en el club ahora" usa la misma regla que la
# ocupación en vivo (ver ocupacion_repo.MINUTOS_EN_EL_CLUB).
#
# Los días y las horas se agrupan en hora de Argentina (la base guarda UTC).

from datetime import date, timedelta

import neon_db
import ocupacion_repo

ZONA = "America/Argentina/Buenos_Aires"
LOCAL = f"(a.fecha AT TIME ZONE '{ZONA}')"
HOY_LOCAL = f"(now() AT TIME ZONE '{ZONA}')::date"
DIAS_AUSENTE = 14  # "dejaron de venir": sin entrar hace 14 días o más
METODOS = {"qr": "📱 Carnet (app)", "manual": "✍️ Manual", "biometrico": "🖐️ Biométrico"}


def resumen() -> dict:
    """Números de la cabecera: hoy, ayer, semana, promedio, pico y ahora."""
    f = neon_db.una_fila(
        f"""SELECT
              count(*) FILTER (WHERE {LOCAL}::date = {HOY_LOCAL}) AS hoy,
              count(*) FILTER (WHERE {LOCAL}::date = {HOY_LOCAL} - 1) AS ayer,
              count(DISTINCT a.id_socio) FILTER (WHERE {LOCAL}::date > {HOY_LOCAL} - 7) AS socios_semana,
              count(*) FILTER (WHERE {LOCAL}::date > {HOY_LOCAL} - 30) AS ultimos_30,
              count(DISTINCT a.id_socio) FILTER (WHERE {LOCAL}::date > {HOY_LOCAL} - 30) AS socios_30
            FROM accesos a WHERE a.resultado = 'permitido'"""
    )
    pico = neon_db.una_fila(
        f"""SELECT extract(hour FROM {LOCAL})::int AS hora, count(*) AS n FROM accesos a
            WHERE a.resultado = 'permitido' AND {LOCAL}::date > {HOY_LOCAL} - 30
            GROUP BY 1 ORDER BY n DESC, hora LIMIT 1"""
    )
    return {
        "hoy": int(f["hoy"]), "ayer": int(f["ayer"]), "socios_semana": int(f["socios_semana"]),
        "promedio_diario": round(int(f["ultimos_30"]) / 30, 1), "socios_30": int(f["socios_30"]),
        "hora_pico": pico["hora"] if pico else None, "entradas_pico": int(pico["n"]) if pico else 0,
        "en_el_club": ocupacion_repo.obtener_ocupacion()["personas"],
    }


def por_dia_del_mes(anio: int, mes: int) -> dict[int, int]:
    """{día del mes: entradas} del mes pedido."""
    filas = neon_db.consulta(
        f"""SELECT extract(day FROM {LOCAL})::int AS dia, count(*) AS n FROM accesos a
            WHERE a.resultado = 'permitido' AND extract(year FROM {LOCAL}) = %s AND extract(month FROM {LOCAL}) = %s
            GROUP BY 1""",
        (anio, mes),
    )
    return {f["dia"]: int(f["n"]) for f in filas}


def por_hora(dias: int = 30) -> dict[int, int]:
    """{hora 0-23: entradas} de los últimos `dias` días."""
    filas = neon_db.consulta(
        f"""SELECT extract(hour FROM {LOCAL})::int AS hora, count(*) AS n FROM accesos a
            WHERE a.resultado = 'permitido' AND {LOCAL}::date > {HOY_LOCAL} - %s GROUP BY 1""",
        (dias,),
    )
    return {f["hora"]: int(f["n"]) for f in filas}


def por_dia_semana(dias: int = 30) -> list[int]:
    """Entradas por día de la semana (lunes=0 … domingo=6) de los últimos `dias` días."""
    filas = neon_db.consulta(
        f"""SELECT extract(isodow FROM {LOCAL})::int AS dow, count(*) AS n FROM accesos a
            WHERE a.resultado = 'permitido' AND {LOCAL}::date > {HOY_LOCAL} - %s GROUP BY 1""",
        (dias,),
    )
    res = [0] * 7
    for f in filas:
        res[f["dow"] - 1] = int(f["n"])
    return res


def por_metodo(dias: int = 30) -> dict[str, int]:
    filas = neon_db.consulta(
        f"""SELECT a.metodo, count(*) AS n FROM accesos a
            WHERE a.resultado = 'permitido' AND {LOCAL}::date > {HOY_LOCAL} - %s GROUP BY 1""",
        (dias,),
    )
    return {f["metodo"]: int(f["n"]) for f in filas}


def entradas_del_dia(dia: date) -> list[dict]:
    """Cada entrada de ese día, la más reciente primero."""
    return neon_db.consulta(
        f"""SELECT trim(s.nombre || ' ' || s.apellido) AS nombre, s.id_socio, a.metodo,
                   to_char({LOCAL}, 'HH24:MI') AS hora
            FROM accesos a JOIN socios s USING (id_socio)
            WHERE a.resultado = 'permitido' AND {LOCAL}::date = %s ORDER BY a.fecha DESC""",
        (dia,),
    )


def ranking_mes(limite: int = 5) -> list[dict]:
    """Socios con más días de asistencia en el mes calendario actual."""
    return neon_db.consulta(
        f"""SELECT trim(s.nombre || ' ' || s.apellido) AS nombre, s.id_socio,
                   count(DISTINCT {LOCAL}::date) AS dias
            FROM accesos a JOIN socios s USING (id_socio)
            WHERE a.resultado = 'permitido' AND date_trunc('month', {LOCAL}) = date_trunc('month', now() AT TIME ZONE '{ZONA}')
            GROUP BY s.id_socio, s.nombre, s.apellido ORDER BY dias DESC, nombre LIMIT %s""",
        (limite,),
    )


def ausentes() -> list[dict]:
    """Socios activos que no entran hace DIAS_AUSENTE días o más (o nunca),
    para que recepción los contacte. Incluye el plan vigente si tienen."""
    filas = neon_db.consulta(
        f"""SELECT trim(s.nombre || ' ' || s.apellido) AS nombre, s.id_socio, m.nombre AS plan,
                   (SELECT max((a.fecha AT TIME ZONE '{ZONA}')::date) FROM accesos a
                     WHERE a.id_socio = s.id_socio AND a.resultado = 'permitido') AS ultima
            FROM socios s
            LEFT JOIN sociomembresia sm ON sm.id_socio = s.id_socio AND sm.estado = 'activa'
            LEFT JOIN membresias m ON m.id_membresia = sm.id_membresia
            WHERE s.estado = 'activo'"""
    )
    limite = date.today() - timedelta(days=DIAS_AUSENTE)
    res = [f for f in filas if f["ultima"] is None or f["ultima"] <= limite]
    # Primero los que tienen plan pago (son los que más importa recuperar).
    return sorted(res, key=lambda f: (f["plan"] is None, f["ultima"] or date.min))


def socios_para_registrar() -> list[dict]:
    return neon_db.consulta(
        "SELECT id_socio, trim(nombre || ' ' || apellido) AS nombre, dni FROM socios"
        " WHERE estado = 'activo' ORDER BY nombre, id_socio"
    )


def registrar_entrada(id_socio: int, metodo: str = "manual") -> bool:
    """Entrada cargada por recepción (socio sin la app, celular sin batería…).
    Igual que la API: si ya entró hace menos de MINUTOS_EN_EL_CLUB no se
    duplica. Devuelve True si se agregó una entrada nueva."""
    fila = neon_db.una_fila(
        "INSERT INTO accesos (id_socio, metodo, resultado)"
        " SELECT %s, %s, 'permitido'"
        " WHERE NOT EXISTS (SELECT 1 FROM accesos WHERE id_socio = %s AND resultado = 'permitido'"
        "                   AND fecha > now() - make_interval(mins => %s))"
        " RETURNING id_acceso",
        (id_socio, metodo, id_socio, ocupacion_repo.MINUTOS_EN_EL_CLUB),
    )
    return fila is not None
