# OLIMPOS GYM — Repositorio de la ficha de socios (pantalla "Socios")
#
# Lee los socios reales de la base: la ficha de "socios", el plan vigente de
# "sociomembresia" y la actividad que registran desde la app (las series de
# "seriesentrenamiento"). No hay registro de pagos ni de entradas al gimnasio
# todavía, así que el estado se deduce del plan:
#   Activo        -> socio activo con plan vigente
#   Plan vencido  -> socio activo cuyo plan ya pasó la fecha de vencimiento
#   Sin plan      -> socio activo sin ningún plan asignado
#   Inactivo      -> acceso a la app desactivado (ver auth_repo.desactivar_acceso_socio)
#
# La pantalla maneja cada socio como un diccionario:
# {
#   "id_socio": 1, "nombre": "Matias Bellu", "dni": "40111222", "email": "...",
#   "telefono": None, "plan": "Platino", "vencimiento": date(2026, 11, 1),
#   "estado": "Activo", "registro": date(2026, 10, 2),
#   "ultimo_entrenamiento": date(2026, 10, 2), "dias_entrenados": 1, ...
# }

from datetime import date, timedelta

import neon_db

ESTADOS = ["Activo", "Plan vencido", "Sin plan", "Inactivo"]
DIAS_NUEVO = 30  # "Nuevos" = registrados en los últimos N días (el dueño lo cambia en Configuración → Club)


def dias_nuevo() -> int:
    import configuracion_repo
    return int(configuracion_repo.club().get("dias_socio_nuevo") or DIAS_NUEVO)

_cache_socios: list[dict] | None = None


def cargar_socios(forzar: bool = False) -> list[dict]:
    global _cache_socios
    if _cache_socios is None or forzar:
        filas = neon_db.consulta(
            "SELECT s.id_socio, trim(s.nombre || ' ' || s.apellido) AS nombre, s.dni, s.email, s.telefono,"
            " s.direccion, s.sexo, s.fecha_nacimiento, s.nivel_experiencia, s.estado AS estado_socio,"
            " s.fecha_registro::date AS registro, (s.firebase_uid IS NOT NULL) AS tiene_app,"
            " COALESCE(p.debe_cambiar_password, FALSE) AS debe_cambiar_password, p.edad,"
            " m.nombre AS plan, sm.fecha_inicio AS plan_inicio, sm.fecha_vencimiento AS vencimiento, sm.asignado_por,"
            " (SELECT o.tipo FROM objetivos o WHERE o.id_socio = s.id_socio AND o.estado = 'activo'"
            "   ORDER BY o.fecha_registro DESC LIMIT 1) AS objetivo,"
            " (SELECT pp.peso FROM progresopeso pp WHERE pp.id_socio = s.id_socio ORDER BY pp.fecha DESC LIMIT 1) AS peso,"
            " (SELECT count(DISTINCT se.fecha::date) FROM seriesentrenamiento se WHERE se.id_socio = s.id_socio) AS dias_entrenados,"
            " (SELECT max(se.fecha)::date FROM seriesentrenamiento se WHERE se.id_socio = s.id_socio) AS ultimo_entrenamiento,"
            " (SELECT count(*) FROM marcaspersonales mp WHERE mp.id_socio = s.id_socio AND mp.estado = 'verificada') AS marcas_verificadas"
            " FROM socios s"
            " LEFT JOIN perfilapp p ON p.id_socio = s.id_socio"
            " LEFT JOIN sociomembresia sm ON sm.id_socio = s.id_socio AND sm.estado = 'activa'"
            " LEFT JOIN membresias m ON m.id_membresia = sm.id_membresia"
            " ORDER BY s.fecha_registro DESC"
        )
        hoy = date.today()
        for f in filas:
            if f["estado_socio"] != "activo":
                f["estado"] = "Inactivo"
            elif not f["plan"]:
                f["estado"] = "Sin plan"
            elif f["vencimiento"] and f["vencimiento"] < hoy:
                f["estado"] = "Plan vencido"
            else:
                f["estado"] = "Activo"
            f["nuevo"] = bool(f["registro"]) and f["registro"] >= hoy - timedelta(days=dias_nuevo())
        _cache_socios = filas
    return _cache_socios


def resumen(socios: list[dict]) -> dict[str, int]:
    """Cantidad por estado, más total y nuevos del último mes."""
    res = {e: 0 for e in ESTADOS}
    for s in socios:
        res[s["estado"]] += 1
    res["total"] = len(socios)
    res["nuevos"] = sum(1 for s in socios if s["nuevo"])
    return res


def filtrar(socios: list[dict], pestana: str, texto: str = "") -> list[dict]:
    """pestana: 'Todos' | uno de ESTADOS | 'Nuevos'. texto: busca en nombre, DNI y email."""
    if pestana == "Nuevos":
        socios = [s for s in socios if s["nuevo"]]
    elif pestana != "Todos":
        socios = [s for s in socios if s["estado"] == pestana]
    texto = texto.strip().lower()
    if texto:
        socios = [s for s in socios
                  if texto in (s["nombre"] or "").lower() or texto in (s["dni"] or "") or texto in (s["email"] or "").lower()]
    return socios


def fecha_corta(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else "—"


def uid_de(id_socio: int) -> str:
    """UID de Firebase del socio (la cuenta con la que entra a la app)."""
    fila = neon_db.una_fila("SELECT firebase_uid FROM socios WHERE id_socio = %s", (id_socio,))
    if not fila or not fila["firebase_uid"]:
        raise RuntimeError("Este socio no tiene cuenta en la app.")
    return fila["firebase_uid"]
