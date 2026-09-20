package com.olimpos.gym.data

import com.google.firebase.firestore.firestore
import com.google.firebase.Firebase
import kotlinx.coroutines.tasks.await

/**
 * Membresía real asignada por un empleado (colección "membresias", un
 * documento por socio — ver membresias_repo.py). Antes "Mi membresía"
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
        val doc = Firebase.firestore.collection("membresias").document(socioActualId()).get().await()
        if (!doc.exists()) return null
        val plan = doc.getString("plan") ?: return null
        val fechaInicio = doc.getLong("fecha_inicio_ms") ?: return null
        MembresiaAsignada(plan, fechaInicio)
    } catch (e: Exception) {
        null
    }
}
