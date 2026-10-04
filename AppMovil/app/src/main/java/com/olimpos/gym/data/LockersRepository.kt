package com.olimpos.gym.data

import org.json.JSONObject

/**
 * Reserva de locker (tablas "lockers" y "reservaslocker"). Un socio tiene como
 * mucho uno; reservar uno nuevo libera el anterior. Que dos socios no puedan
 * tener el mismo locker lo garantiza la base de datos con un índice único —
 * no depende de que la app se acuerde de chequearlo.
 */
suspend fun reservarLockerEnFirebase(numero: Int): Boolean {
    return try {
        Api.post("/v1/lockers/reservar", JSONObject().put("numero", numero))
        true
    } catch (e: Exception) {
        false
    }
}

suspend fun liberarLockerEnFirebase(): Boolean {
    return try {
        Api.delete("/v1/lockers/mio")
        true
    } catch (e: Exception) {
        false
    }
}

/** Número de locker -> uid del socio que lo tiene reservado, de TODOS los
 *  socios — hace falta para saber qué lockers están libres para
 *  cualquiera, no solo el propio. */
suspend fun cargarLockersDesdeFirebase(): Map<Int, String>? {
    return try {
        Api.get("/v1/lockers").optJSONArray("lockers")?.objetos()?.associate {
            it.optInt("numero") to it.optString("socio_id")
        } ?: emptyMap()
    } catch (e: Exception) {
        null
    }
}
