package com.olimpos.gym.data

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshots.SnapshotStateList
import com.google.firebase.Firebase
import com.google.firebase.auth.auth
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * La sesión de entrenamiento del día: peso y reps de cada ejercicio, las
 * series ya registradas y el cronómetro. Vive fuera de la pantalla Entrenar
 * (antes estaba en `remember` y se perdía al cambiar de pestaña) y se guarda
 * en el teléfono, así tampoco se pierde si se cierra la app.
 *
 * Es una por socio, por rutina y por día: al cambiar de rutina o al día
 * siguiente arranca de cero.
 */
object SesionEntrenamiento {
    private const val PREFS = "olimpos_sesion_entrenamiento"

    private var clave: String? = null
    private var contexto: Context? = null

    val pesos: SnapshotStateList<Float> = mutableStateListOf()
    val reps: SnapshotStateList<Int> = mutableStateListOf()
    val seriesHechas: SnapshotStateList<SnapshotStateList<SerieHecha>> = mutableStateListOf()

    /** Momento en que se tocó "iniciar" (o se reanudó); null si está en pausa o sin empezar. */
    var corriendoDesde by mutableStateOf<Long?>(null); private set
    /** Lo acumulado en tramos anteriores (antes de cada pausa). */
    var acumuladoMs by mutableLongStateOf(0L); private set

    val iniciado: Boolean get() = corriendoDesde != null || acumuladoMs > 0

    fun transcurridoMs(ahora: Long = System.currentTimeMillis()): Long =
        acumuladoMs + (corriendoDesde?.let { ahora - it } ?: 0L)

    private fun hoy() = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())

    /** Deja lista la sesión de [rutina] para hoy: si ya había una guardada la
     *  recupera; si no (otra rutina, otro día, otro socio) arranca de cero. */
    fun preparar(context: Context, rutina: RutinaCompleta, pesoInicial: (EjercicioRutina) -> Float, repsIniciales: (EjercicioRutina) -> Int) {
        val uid = Firebase.auth.currentUser?.uid ?: "anon"
        val nueva = "$uid|${rutina.id}|${hoy()}|${rutina.ejercicios.joinToString(",") { it.nombre }}"
        if (nueva == clave && pesos.size == rutina.ejercicios.size) return
        contexto = context.applicationContext
        clave = nueva

        val guardada = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY, null)
            ?.let { runCatching { JSONObject(it) }.getOrNull() }
            ?.takeIf { it.optString("clave") == nueva }

        pesos.clear(); reps.clear(); seriesHechas.clear()
        rutina.ejercicios.forEachIndexed { i, ej ->
            val e = guardada?.optJSONArray("ejercicios")?.optJSONObject(i)
            pesos.add(e?.optDouble("peso")?.toFloat()?.takeIf { !it.isNaN() } ?: pesoInicial(ej))
            reps.add(e?.optInt("reps", 0)?.takeIf { it > 0 } ?: repsIniciales(ej))
            val lista = mutableStateListOf<SerieHecha>()
            e?.optJSONArray("series")?.let { arr ->
                for (j in 0 until arr.length()) {
                    val s = arr.getJSONObject(j)
                    lista.add(SerieHecha(s.getDouble("peso").toFloat(), s.getInt("reps")))
                }
            }
            seriesHechas.add(lista)
        }
        corriendoDesde = guardada?.takeIf { it.has("corriendoDesde") }?.optLong("corriendoDesde")
        acumuladoMs = guardada?.optLong("acumuladoMs") ?: 0L
    }

    fun ponerPeso(i: Int, kg: Float) { pesos[i] = kg; guardar() }
    fun ponerReps(i: Int, n: Int) { reps[i] = n; guardar() }
    fun agregarSerie(i: Int, serie: SerieHecha) { seriesHechas[i].add(serie); guardar() }

    /** Tocar el cronómetro: arranca, pausa o reanuda. */
    fun alternarCronometro() {
        val ahora = System.currentTimeMillis()
        val desde = corriendoDesde
        if (desde == null) {
            corriendoDesde = ahora
        } else {
            acumuladoMs += ahora - desde
            corriendoDesde = null
        }
        guardar()
    }

    /** "Terminar": se cierra la sesión — cronómetro a cero y series limpias
     *  (cada serie ya quedó guardada en el historial al registrarla). */
    fun terminar(pesoInicial: List<Float>, repsIniciales: List<Int>) {
        corriendoDesde = null
        acumuladoMs = 0L
        seriesHechas.forEach { it.clear() }
        // Se conserva el último peso/reps usado: es el punto de partida más útil para la próxima vez.
        if (pesos.isEmpty()) { pesos.addAll(pesoInicial); reps.addAll(repsIniciales) }
        guardar()
    }

    /** "Reiniciar rutina": todo como recién abierta — cronómetro a cero y en
     *  pausa, sin series marcadas y con el peso y las reps sugeridos. Las
     *  series que ya se registraron siguen en el historial (Ghost Mode, kg del
     *  mes): esto limpia la sesión de la pantalla, no borra entrenamientos. */
    fun reiniciar(pesoInicial: List<Float>, repsIniciales: List<Int>) {
        corriendoDesde = null
        acumuladoMs = 0L
        seriesHechas.forEach { it.clear() }
        pesoInicial.forEachIndexed { i, kg -> if (i < pesos.size) pesos[i] = kg }
        repsIniciales.forEachIndexed { i, n -> if (i < reps.size) reps[i] = n }
        guardar()
    }

    private fun guardar() {
        val ctx = contexto ?: return
        val ejercicios = JSONArray()
        pesos.indices.forEach { i ->
            ejercicios.put(JSONObject().apply {
                put("peso", pesos[i].toDouble())
                put("reps", reps.getOrElse(i) { 0 })
                put("series", JSONArray().apply {
                    seriesHechas.getOrNull(i)?.forEach { s ->
                        put(JSONObject().put("peso", s.pesoKg.toDouble()).put("reps", s.reps))
                    }
                })
            })
        }
        val json = JSONObject().put("clave", clave).put("acumuladoMs", acumuladoMs).put("ejercicios", ejercicios)
        corriendoDesde?.let { json.put("corriendoDesde", it) }
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY, json.toString()).apply()
    }

    private const val KEY = "sesion"
}
