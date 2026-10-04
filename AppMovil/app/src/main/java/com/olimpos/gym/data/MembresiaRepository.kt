package com.olimpos.gym.data

/**
 * Membresía real asignada por un empleado (tabla "membresiasocio" — ver
 * membresias_repo.py). Antes "Mi membresía"
 * dejaba que el propio socio se activara un plan tocando un botón, sin
 * que quedara ninguna fecha de inicio real ni que el gimnasio se
 * enterara — el logro "Cliente fiel" (6 meses de membresía activa) no
 * tenía de dónde salir. `null` = todavía no le asignaron ninguna.
 */
data class MembresiaAsignada(val plan: String, val fechaInicioMs: Long)

/** Argos (el asistente de IA) es un beneficio de pago: solo lo incluyen los
 *  planes de este conjunto — el intermedio (Oro) y el superior (Platino). El
 *  Worker de Argos lo verifica también del lado del servidor (ver
 *  ArgosWorker/src/index.ts) — este chequeo de la app es solo para mostrar
 *  el bloqueo sin ir a preguntarle al servidor. */
val PLANES_CON_ARGOS = setOf("Oro", "Platino")

fun planIncluyeArgos(plan: String?): Boolean = plan in PLANES_CON_ARGOS

suspend fun cargarMembresiaDesdeFirebase(): MembresiaAsignada? {
    return try {
        val j = Api.get("/v1/membresia")
        if (!j.optBoolean("existe", false)) return null
        val plan = j.textoONull("plan") ?: return null
        val fechaInicio = j.numeroONull("fecha_inicio_ms")?.toLong() ?: return null
        MembresiaAsignada(plan, fechaInicio)
    } catch (e: Exception) {
        null
    }
}
