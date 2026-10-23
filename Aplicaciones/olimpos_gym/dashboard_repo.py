# OLIMPOS GYM — Repositorio del dashboard (pantalla de inicio del sistema)
#
# Todos los números del dashboard salen de la base, nada está escrito a mano:
# las tarjetas de cada rol, el gráfico mensual, la actividad reciente, las
# clases de hoy, el equipo y la novedad del banner (la última publicación
# del tablón). Las fechas se cuentan en hora de Argentina (la base guarda UTC).

from datetime import date

import neon_db
import asistencia_repo

ZONA = asistencia_repo.ZONA
HOY_LOCAL = asistencia_repo.HOY_LOCAL
# Mismo formato que dia de la tabla "clases" ("HOY" = todos los días).
DIAS_CLASE = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]


def _local(col: str) -> str:
    return f"({col} AT TIME ZONE '{ZONA}')"


def _n(sql: str, params=()) -> int:
    fila = neon_db.una_fila(sql, params)
    return int(list(fila.values())[0] or 0) if fila else 0


def _pesos(monto: float) -> str:
    return "$" + f"{monto:,.0f}".replace(",", ".")


# ───────────────────────── tarjetas por rol ─────────────────────────

def _socios_con_plan_vigente() -> int:
    return _n(f"""SELECT count(DISTINCT s.id_socio) FROM socios s
                  JOIN sociomembresia sm ON sm.id_socio = s.id_socio AND sm.estado = 'activa'
                  WHERE s.estado = 'activo' AND sm.fecha_vencimiento >= {HOY_LOCAL}""")


def estadisticas(role: str) -> list[tuple[str, str, str, str]]:
    """4 tarjetas (título, valor, etiqueta, color) según el rol."""
    asis = asistencia_repo.resumen()
    pico = f"pico {asis['hora_pico']:02d}:00" if asis["hora_pico"] is not None else "sin datos de pico aún"

    if role == "entrenador":
        rutinas = _n("SELECT count(*) FROM rutinas WHERE activa AND estado = 'vigente'")
        socios_rut = _n("SELECT count(DISTINCT id_socio) FROM rutinas WHERE activa AND estado = 'vigente'")
        pendientes = _n("SELECT count(*) FROM marcaspersonales WHERE estado = 'pendiente'")
        verificadas = _n("SELECT count(*) FROM marcaspersonales WHERE estado = 'verificada'")
        hoy_ent = neon_db.una_fila(
            f"""SELECT count(DISTINCT id_socio) AS socios, count(*) AS series FROM seriesentrenamiento
                WHERE {_local('fecha')}::date = {HOY_LOCAL}""")
        return [
            ("Rutinas activas", str(rutinas), f"de {socios_rut} socio{'s' if socios_rut != 1 else ''}", "green"),
            ("Marcas por verificar", str(pendientes), f"{verificadas} ya verificadas", "red" if pendientes else "green"),
            ("Entrenaron hoy", str(hoy_ent["socios"]), f"{hoy_ent['series']} series registradas", "gold"),
            ("Asistencia hoy", str(asis["hoy"]), f"{asis['en_el_club']} en el club ahora", "blue"),
        ]

    if role == "nutricionista":
        dietas = _n("SELECT count(*) FROM dietas WHERE estado = 'vigente'")
        sin_dieta = _n("""SELECT count(*) FROM socios s WHERE s.estado = 'activo' AND NOT EXISTS
                          (SELECT 1 FROM dietas d WHERE d.id_socio = s.id_socio AND d.estado = 'vigente')""")
        publicados = _n("SELECT count(*) FROM platos WHERE estado = 'publicado'")
        borradores = _n("SELECT count(*) FROM platos WHERE estado = 'borrador'")
        comidas_hoy = _n(f"SELECT count(*) FROM comidasregistradas WHERE fecha::date = {HOY_LOCAL}")
        comidas_sem = _n(f"SELECT count(*) FROM comidasregistradas WHERE fecha::date > {HOY_LOCAL} - 7")
        agua_hoy = _n(f"SELECT count(DISTINCT id_socio) FROM registroagua WHERE {_local('fecha')}::date = {HOY_LOCAL}")
        return [
            ("Dietas asignadas", str(dietas), f"{sin_dieta} socio{'s' if sin_dieta != 1 else ''} sin dieta", "green"),
            ("Platos publicados", str(publicados), f"{borradores} en borrador", "gold"),
            ("Comidas registradas hoy", str(comidas_hoy), f"{comidas_sem} en los últimos 7 días", "blue"),
            ("Registraron agua hoy", str(agua_hoy), "socios con su consumo cargado", "green"),
        ]

    if role == "seguridad":
        fallidos = _n(f"""SELECT count(*) FROM intentosacceso WHERE resultado = 'fallido'
                          AND {_local('fecha')}::date = {HOY_LOCAL}""")
        incidencias = _n("SELECT count(*) FROM incidenciasacceso WHERE estado NOT IN ('resuelta', 'cerrada')")
        return [
            ("En el club ahora", str(asis["en_el_club"]), "según los carnets mostrados", "gold"),
            ("Entradas hoy", str(asis["hoy"]), f"ayer: {asis['ayer']}", "green"),
            ("Logins fallidos hoy", str(fallidos), "en este sistema", "red" if fallidos else "green"),
            ("Incidencias abiertas", str(incidencias), "✓ sin incidencias" if not incidencias else "revisar", "red" if incidencias else "green"),
        ]

    if role == "recepcionista":
        por_vencer = _n(f"""SELECT count(*) FROM sociomembresia WHERE estado = 'activa'
                            AND fecha_vencimiento BETWEEN {HOY_LOCAL} AND {HOY_LOCAL} + 7""")
        vencidos = _n(f"""SELECT count(*) FROM sociomembresia sm JOIN socios s USING (id_socio)
                          WHERE sm.estado = 'activa' AND s.estado = 'activo' AND sm.fecha_vencimiento < {HOY_LOCAL}""")
        total = _n("SELECT count(*) FROM socios WHERE estado = 'activo'")
        return [
            ("Entradas hoy", str(asis["hoy"]), f"{asis['en_el_club']} en el club ahora", "green"),
            ("Socios con plan vigente", str(_socios_con_plan_vigente()), f"de {total} socios activos", "gold"),
            ("Vencen en 7 días", str(por_vencer), "avisar para renovar", "gold" if por_vencer else "green"),
            ("Planes vencidos", str(vencidos), "⚠️ cobrar renovación" if vencidos else "✓ al día", "red" if vencidos else "green"),
        ]

    # dueño y administrador
    nuevos = _n("SELECT count(*) FROM socios WHERE fecha_registro > now() - interval '7 days'")
    cobrado = neon_db.una_fila(
        f"""SELECT COALESCE(sum(monto), 0) AS total, count(*) AS n FROM pagos WHERE estado = 'Aprobado'
            AND date_trunc('month', {_local('fecha_pago')}) = date_trunc('month', now() AT TIME ZONE '{ZONA}')""")
    estimado = neon_db.una_fila(
        f"""SELECT COALESCE(sum(m.precio * 30.0 / m.duracion_dias), 0) AS total FROM sociomembresia sm
            JOIN membresias m USING (id_membresia) JOIN socios s USING (id_socio)
            WHERE sm.estado = 'activa' AND s.estado = 'activo' AND sm.fecha_vencimiento >= {HOY_LOCAL}""")["total"]
    personal = _n("SELECT count(*) FROM empleados WHERE estado = 'activo'")
    conectados = _n(f"""SELECT count(DISTINCT id_empleado) FROM intentosacceso WHERE resultado = 'exitoso'
                        AND {_local('fecha')}::date = {HOY_LOCAL}""")
    return [
        ("Socios activos", str(_socios_con_plan_vigente()), f"▲ {nuevos} nuevo{'s' if nuevos != 1 else ''} esta semana", "green"),
        ("Cobrado este mes", _pesos(float(cobrado["total"])),
         f"{cobrado['n']} pago{'s' if cobrado['n'] != 1 else ''} · planes vigentes: {_pesos(float(estimado))}/mes", "green"),
        ("Asistencia hoy", str(asis["hoy"]), pico, "blue"),
        ("Personal activo", str(personal), f"{conectados} {'entró' if conectados == 1 else 'entraron'} al sistema hoy", "gold"),
    ]


# ───────────────────────── gráfico mensual ─────────────────────────

SERIES = {
    "entradas": "Entradas al club",
    "altas": "Socios nuevos",
    "ingresos": "Cobrado (pagos aprobados)",
}


def serie_mensual(tipo: str, anio: int) -> list[float]:
    """12 valores (enero…diciembre) del año pedido."""
    if tipo == "altas":
        sql = f"SELECT extract(month FROM {_local('fecha_registro')})::int AS m, count(*) AS v FROM socios WHERE extract(year FROM {_local('fecha_registro')}) = %s GROUP BY 1"
    elif tipo == "ingresos":
        sql = f"SELECT extract(month FROM {_local('fecha_pago')})::int AS m, sum(monto) AS v FROM pagos WHERE estado = 'Aprobado' AND extract(year FROM {_local('fecha_pago')}) = %s GROUP BY 1"
    else:
        sql = f"SELECT extract(month FROM {_local('fecha')})::int AS m, count(*) AS v FROM accesos WHERE resultado = 'permitido' AND extract(year FROM {_local('fecha')}) = %s GROUP BY 1"
    valores = [0.0] * 12
    for f in neon_db.consulta(sql, (anio,)):
        valores[f["m"] - 1] = float(f["v"])
    return valores


# ───────────────────────── actividad reciente ─────────────────────────

def actividad_reciente(limite: int = 7) -> list[dict]:
    """Lo último que pasó en el club, de cualquier tipo, lo más nuevo primero:
    [{"tipo": "socio", "titulo": "...", "detalle": "...", "ms": 1758...}]."""
    socio = "trim(s.nombre || ' ' || s.apellido)"
    ms = lambda col: f"(extract(epoch FROM {col}) * 1000)::bigint"
    fecha_local = lambda col: f"({col}::timestamp AT TIME ZONE '{ZONA}')"
    sql = f"""
      SELECT * FROM (
        SELECT 'socio' AS tipo, 'Nuevo socio registrado' AS titulo, {socio} AS detalle, {ms('s.fecha_registro')} AS ms
          FROM socios s
        UNION ALL
        SELECT 'membresia', 'Membresía ' || m.nombre || ' asignada',
               {socio} || COALESCE(' — por ' || sm.asignado_por, ''), {ms(fecha_local('sm.fecha_inicio'))}
          FROM sociomembresia sm JOIN socios s USING (id_socio) JOIN membresias m USING (id_membresia)
        UNION ALL
        SELECT 'pago', 'Pago aprobado', {socio} || ' — $' || round(p.monto)::text, {ms('p.fecha_pago')}
          FROM pagos p JOIN socios s USING (id_socio) WHERE p.estado = 'Aprobado'
        UNION ALL
        SELECT 'marca', 'Marca verificada', {socio} || ' — ' || e.nombre || COALESCE(' (' || mp.verificado_por || ')', ''),
               {ms('mp.fecha_verificacion')}
          FROM marcaspersonales mp JOIN socios s USING (id_socio)
          JOIN ejerciciosmarca em USING (id_ejercicio_marca) JOIN ejercicios e ON e.id_ejercicio = em.id_ejercicio
          WHERE mp.estado = 'verificada' AND mp.fecha_verificacion IS NOT NULL
        UNION ALL
        SELECT 'rutina', 'Rutina creada', {socio} || ' — ' || r.nombre, {ms('r.fecha_creacion')}
          FROM rutinas r JOIN socios s USING (id_socio)
        UNION ALL
        SELECT 'dieta', 'Dieta asignada', {socio} || ' — ' || d.nombre, {ms('d.fecha_creacion')}
          FROM dietas d JOIN socios s USING (id_socio)
        UNION ALL
        SELECT 'entrada', 'Entrada al club', {socio}, {ms('a.fecha')}
          FROM accesos a JOIN socios s USING (id_socio) WHERE a.resultado = 'permitido'
        UNION ALL
        SELECT 'tablon', 'Publicado en el tablón', t.titulo, {ms('t.fecha_creacion')}
          FROM tablonpublicaciones t WHERE t.publicado
      ) x WHERE ms IS NOT NULL AND ms <= {ms('now()')} ORDER BY ms DESC LIMIT %s"""
    return neon_db.consulta(sql, (limite,))


# ───────────────────────── clases, equipo y novedad ─────────────────────────

def clases_de_hoy() -> list[dict]:
    """Clases que se dictan hoy con las reservas de esta semana (la app
    reserva por semana: misma clave "2026-W43" que la API)."""
    hoy = date.today()
    anio, semana, _ = hoy.isocalendar()
    return neon_db.consulta(
        """SELECT c.nombre, to_char(c.hora, 'HH24:MI') AS hora, c.lugar, c.capacidad,
                  (SELECT count(*) FROM reservasclase r WHERE r.id_clase = c.id_clase
                     AND r.semana = %s AND r.estado = 'confirmada') AS reservados
           FROM clases c WHERE c.estado = 'activa' AND c.dia IN ('HOY', %s) ORDER BY c.hora""",
        (f"{anio}-W{semana}", DIAS_CLASE[hoy.weekday()]),
    )


def equipo() -> list[dict]:
    """Empleados activos con su rol y si entraron hoy al sistema."""
    return neon_db.consulta(
        f"""SELECT trim(e.nombre || ' ' || e.apellido) AS nombre, e.usuario, r.descripcion AS rol,
                   EXISTS (SELECT 1 FROM intentosacceso i WHERE i.id_empleado = e.id_empleado AND i.resultado = 'exitoso'
                           AND {_local('i.fecha')}::date = {HOY_LOCAL}) AS entro_hoy
            FROM empleados e JOIN rol r ON r.id_rol = e.rol WHERE e.estado = 'activo' ORDER BY e.rol"""
    )


def novedad() -> dict | None:
    """La publicación del tablón que encabeza el dashboard: la fijada más
    nueva, o si no hay fijadas, la más nueva."""
    return neon_db.una_fila(
        "SELECT titulo, mensaje, categoria FROM tablonpublicaciones WHERE publicado"
        " ORDER BY fijado DESC, fecha_creacion DESC LIMIT 1"
    )
