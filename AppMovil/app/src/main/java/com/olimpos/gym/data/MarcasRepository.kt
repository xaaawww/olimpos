package com.olimpos.gym.data

import org.json.JSONObject

/**
 * Marcas personales del socio (tabla "marcaspersonales"). El socio las carga
 * desde la Calculadora/Mis marcas; el sistema de empleados las lee para que
 * un entrenador o el dueño las verifique (ver sección "Verificación de
 * Marcas"). Devuelve `null` si la API falla — quien llama debe tratarlo
 * como "todavía no se sabe", no mostrar datos falsos.
 */
private fun jsonAMarca(j: JSONObject): MarcaPersonal? {
    val ejercicio = j.optString("ejercicio").takeIf { it.isNotEmpty() } ?: return null
    return MarcaPersonal(
        id = j.optString("id"),
        ejercicio = ejercicio,
        pesoKg = j.optDouble("peso", 0.0).toFloat(),
        reps = j.optInt("repeticiones", 0),
        fecha = j.optString("fecha", ""),
        timestamp = j.optLong("timestamp", 0L),
        verificado = j.optBoolean("verificado", false)
    )
}

suspend fun cargarMarcasDesdeFirebase(): List<MarcaPersonal>? {
    return try {
        Api.get("/v1/marcas").optJSONArray("marcas")?.objetos()?.mapNotNull(::jsonAMarca) ?: emptyList()
    } catch (e: Exception) {
        null
    }
}

/** Rango general de un socio (promedio calibrado por ejercicio — ver
 *  [puntajeGeneralDeSocio]), para la Escalera del Olimpo — quién más del
 *  club llegó a cada nivel. [creadoMs] sale del alta de su acceso a la app
 *  (colección "socios_app", ver auth_repo.py); [pesoKg]/[sexo]/[edad] del
 *  onboarding (colección "datos_fisicos") — es la base real del cálculo,
 *  ya no una referencia fija compartida por todos. */
data class SocioRango(
    val socioId: String,
    val nombre: String,
    val nivel: NivelMuscular,
    val verificado: Boolean,
    val kgTotales: Float,
    val pesoKg: Float,
    val edad: Int?,
    val sexo: SexoBiologico?,
    val mejorLevantamiento: MejorLevantamiento?,
    val creadoMs: Long? = null,
    /** Rango por zona muscular (mismo cálculo que el Bodygraph propio, ver
     *  [resumenMuscular]) — ya sale calculado acá de paso, así que el perfil
     *  de CUALQUIER socio en Clasificación puede mostrar su Bodygraph real,
     *  no solo el de uno mismo. */
    val rangoPorZona: Map<ZonaMuscular, RangoMuscular?> = emptyMap()
)

/** Referencia SOLO para el caso borde de una cuenta sin datos físicos
 *  todavía (no debería pasar: el onboarding es obligatorio desde el primer
 *  login — ver MainActivity — pero una cuenta de prueba vieja podría no
 *  tenerlos). */
private const val PESO_CORPORAL_REFERENCIA = 80f

/** Trae el rango general de TODOS los socios con marcas cargadas (no solo
 *  el actual), agrupando por socio_id, y cruzando contra sus datos físicos
 *  reales. Solo entran a la Escalera del Olimpo los que tengan marcas en
 *  al menos [MINIMO_EJERCICIOS_PARA_CLASIFICACION] ejercicios distintos —
 *  ver [puntajeGeneralDeSocio]. */
suspend fun cargarRangosDeSocios(): List<SocioRango>? {
    return try {
        // Una sola llamada trae todo lo necesario: las marcas de todos los
        // socios, cuándo se unió cada uno y sus datos físicos (sin nada privado).
        val j = Api.get("/v1/clasificacion")
        val creadoPorUid = j.optJSONObject("socios")?.let { o -> o.keys().asSequence().associateWith { o.optLong(it) } } ?: emptyMap()
        val datosFisicosPorUid = j.optJSONObject("datos_fisicos")?.let { o ->
            o.keys().asSequence().mapNotNull { uid -> o.optJSONObject(uid)?.let(::jsonADatosFisicos)?.let { uid to it } }.toMap()
        } ?: emptyMap()
        val marcasJson = j.optJSONArray("marcas")?.objetos().orEmpty()

        marcasJson
            .groupBy { it.optString("socio_id", "?") }
            .mapNotNull { (socioId, docs) ->
                val nombre = docs.firstOrNull()?.optString("socio_nombre")?.takeIf { it.isNotEmpty() } ?: socioId
                val marcas = docs.mapNotNull(::jsonAMarca)
                val datosFisicos = datosFisicosPorUid[socioId]
                // El socio pidió no aparecer para los demás (botón en
                // Clasificación) — su propio rango sigue viéndolo él, ya
                // que eso se calcula aparte con sus propias marcas, no con
                // esta lista compartida.
                if (datosFisicos?.ocultoClasificacion == true) return@mapNotNull null
                val pesoCorporal = datosFisicos?.pesoKg ?: PESO_CORPORAL_REFERENCIA
                val puntajeGeneral = puntajeGeneralDeSocio(marcas, pesoCorporal, datosFisicos?.sexo) ?: return@mapNotNull null
                val resumen = resumenMuscular(marcas, pesoCorporal, datosFisicos?.sexo)
                SocioRango(
                    socioId = socioId,
                    nombre = nombre,
                    nivel = nivelDesdePuntaje(puntajeGeneral),
                    verificado = resumen.verificado,
                    kgTotales = kgTotalesVigentes(marcas, pesoCorporal),
                    pesoKg = pesoCorporal,
                    edad = datosFisicos?.edad,
                    sexo = datosFisicos?.sexo,
                    mejorLevantamiento = mejorLevantamientoVigente(marcas, pesoCorporal),
                    creadoMs = creadoPorUid[socioId],
                    rangoPorZona = ZonaMuscular.entries.associateWith { zona ->
                        resumen.puntajes[zona]?.let(::nivelDesdePuntaje)?.rango
                    }
                )
            }
    } catch (e: Exception) {
        null
    }
}

/** Guarda una marca nueva, siempre como pendiente de verificar. El
 *  [timestamp] es lo que decide, en [resumenMuscular], que esta marca
 *  reemplace a la anterior del mismo ejercicio en vez de acumularse. */
suspend fun guardarMarcaEnFirebase(ejercicio: String, pesoKg: Float, reps: Int, fecha: String, timestamp: Long): Boolean {
    return try {
        Api.post(
            "/v1/marcas",
            JSONObject().put("ejercicio", ejercicio).put("peso", pesoKg.toDouble()).put("repeticiones", reps).put("timestamp", timestamp)
        )
        true
    } catch (e: Exception) {
        false
    }
}

/** Borra una marca ya cargada. El Bodygraph y la Clasificación se
 *  recalculan a partir de lo que quede en la base (ver [resumenMuscular]/
 *  [puntajeGeneralDeSocio]), así que borrar la única marca de un ejercicio
 *  puede hacer bajar el rango — quien llama debe recargar [DatosRemotos]
 *  después de esto para que se note sin reiniciar la app. */
suspend fun eliminarMarcaEnFirebase(marcaId: String): Boolean {
    if (marcaId.isBlank()) return false
    return try {
        Api.delete("/v1/marcas/$marcaId")
        true
    } catch (e: Exception) {
        false
    }
}
