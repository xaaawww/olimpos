package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.firestore.firestore
import kotlinx.coroutines.tasks.await
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

/**
 * Dieta diaria del socio: qué le asignó su nutricionista en cada horario, la
 * meta de kcal/macros de ese día y la racha de dieta.
 *
 * El nutricionista/dueño arma la asignación desde el sistema de empleados
 * ("Asignar Dietas", ver dietas_asignadas_repo.py): un documento por socio en
 * "dietas_asignadas" con los platos de Desayuno, Almuerzo y Cena. Los valores
 * nutricionales de cada plato (kcal, proteínas, carbohidratos, grasas por
 * porción) los carga el mismo nutricionista en el Editor Visual de Dietas.
 */

data class Macros(val kcal: Int = 0, val proteinas: Int = 0, val carbs: Int = 0, val grasas: Int = 0) {
    operator fun plus(otro: Macros) = Macros(
        kcal + otro.kcal, proteinas + otro.proteinas, carbs + otro.carbs, grasas + otro.grasas
    )
    val esVacio: Boolean get() = kcal == 0 && proteinas == 0 && carbs == 0 && grasas == 0
}

/** Lee un mapa de Firestore ({"kcal":…, "proteinas":…, "carbs":…, "grasas":…}). */
fun macrosDeMapa(mapa: Map<*, *>?): Macros = Macros(
    kcal = (mapa?.get("kcal") as? Number)?.toInt() ?: 0,
    proteinas = (mapa?.get("proteinas") as? Number)?.toInt() ?: 0,
    carbs = (mapa?.get("carbs") as? Number)?.toInt() ?: 0,
    grasas = (mapa?.get("grasas") as? Number)?.toInt() ?: 0
)

/** [clave] es la misma que usa el sistema de empleados en Firestore. */
enum class MomentoComida(val clave: String, val etiqueta: String, val emoji: String) {
    DESAYUNO("desayuno", "Desayuno", "🌅"),
    ALMUERZO("almuerzo", "Almuerzo", "☀️"),
    CENA("cena", "Cena", "🌙")
}

data class DietaAsignada(val comidas: Map<MomentoComida, List<String>>, val asignadaPor: String) {
    val platoIds: Set<String> get() = comidas.values.flatten().toSet()
    val vacia: Boolean get() = platoIds.isEmpty()

    /** Platos asignados a [momento] que ya están publicados (los que el
     *  socio realmente puede ver — ver firestore.rules). */
    fun platosDe(momento: MomentoComida, platos: List<Plato>): List<Plato> =
        comidas[momento].orEmpty().mapNotNull { id -> platos.firstOrNull { it.id == id } }
}

/** `null` = todavía no le asignaron ninguna dieta (o Firebase falló). */
suspend fun cargarDietaAsignada(): DietaAsignada? {
    return try {
        val doc = Firebase.firestore.collection("dietas_asignadas").document(socioActualId()).get().await()
        if (!doc.exists()) return null
        val mapa = doc.get("comidas") as? Map<*, *> ?: return null
        val comidas = MomentoComida.entries.associateWith { m ->
            (mapa[m.clave] as? List<*>)?.mapNotNull { it as? String }.orEmpty()
        }
        DietaAsignada(comidas, doc.getString("asignada_por") ?: "").takeUnless { it.vacia }
    } catch (e: Exception) {
        null
    }
}

/** Meta de un día: la suma de los platos asignados y en qué horarios hay
 *  algo asignado. */
data class MetaDia(val macros: Macros, val momentos: Set<MomentoComida>)

fun metaDelDia(dieta: DietaAsignada?, platos: List<Plato>): MetaDia? {
    if (dieta == null) return null
    val momentos = MomentoComida.entries.filter { dieta.platosDe(it, platos).isNotEmpty() }.toSet()
    if (momentos.isEmpty()) return null
    val macros = momentos
        .flatMap { dieta.platosDe(it, platos) }
        .fold(Macros()) { acc, p -> acc + (p.macros ?: Macros()) }
    return MetaDia(macros, momentos)
}

/* ══════════════════════ Racha de dieta ══════════════════════ */

/**
 * Cuánto se puede desviar el día de la meta de kcal según el objetivo del
 * socio. Es el ÚNICO lugar donde vive esta regla — para cambiarla, tocar solo
 * estos números:
 *  - Fuerza: 90–115% de las kcal de la dieta, y al menos 90% de la proteína.
 *  - Hipertrofia: no quedarse corto (95%) ni pasarse mucho (125%), proteína al 95%.
 *  - Salud general: sin pasarse (85–110%), proteína al 80%.
 */
data class ReglaObjetivo(val kcalMinPct: Int, val kcalMaxPct: Int, val proteinaMinPct: Int) {
    val descripcion: String
        get() = "entre el $kcalMinPct% y el $kcalMaxPct% de tus kcal y al menos el $proteinaMinPct% de tu proteína"
}

fun reglaDe(objetivo: ObjetivoCompetencia): ReglaObjetivo = when (objetivo) {
    ObjetivoCompetencia.FUERZA -> ReglaObjetivo(90, 115, 90)
    ObjetivoCompetencia.HIPERTROFIA -> ReglaObjetivo(95, 125, 95)
    ObjetivoCompetencia.SALUD -> ReglaObjetivo(85, 110, 80)
}

private val FORMATO_FECHA = ThreadLocal.withInitial { SimpleDateFormat("yyyyMMdd", Locale.US) }

/** Día calendario local como "aaaammdd" — la misma clave que usan los
 *  documentos de "comidas_dia" (ver ComidasRepository.kt). */
fun fechaClave(timestampMs: Long = System.currentTimeMillis()): String =
    FORMATO_FECHA.get()!!.format(Date(timestampMs))

/**
 * Un día cuenta para la racha si: (1) había una dieta asignada, (2) el socio
 * registró TODOS los horarios que tenían algo asignado, y (3) las kcal y la
 * proteína del día caen dentro de lo que pide su objetivo (ver
 * [ReglaObjetivo]). [metaVigente] reemplaza a la meta guardada SOLO para el
 * día de hoy: si el nutricionista asigna o cambia la dieta a mitad del día,
 * hoy se evalúa con la dieta actual; los días pasados quedan como estaban.
 */
fun diaCumplido(dia: DiaComidas, objetivoActual: ObjetivoCompetencia, metaVigente: MetaDia? = null): Boolean {
    val meta = (if (dia.fecha == fechaClave()) metaVigente else null) ?: dia.meta ?: return false
    if (meta.momentos.isEmpty()) return false
    if (!meta.momentos.all { it in dia.comidas }) return false
    val regla = reglaDe(dia.objetivo ?: objetivoActual)
    val totales = dia.totales
    if (meta.macros.kcal > 0) {
        val pct = totales.kcal * 100 / meta.macros.kcal
        if (pct < regla.kcalMinPct || pct > regla.kcalMaxPct) return false
    }
    if (meta.macros.proteinas > 0 && totales.proteinas * 100 / meta.macros.proteinas < regla.proteinaMinPct) return false
    return true
}

/** Racha ACTUAL de días seguidos cumplidos, contando desde hoy — o desde
 *  ayer si hoy todavía no se completó (un día de gracia, igual que la racha
 *  de asistencia: no se corta por no haber terminado de comer). */
fun rachaDietaActual(dias: List<DiaComidas>, objetivo: ObjetivoCompetencia, metaVigente: MetaDia?): Int {
    val cumplidos = dias.filter { diaCumplido(it, objetivo, metaVigente) }.map { it.fecha }.toSet()
    if (cumplidos.isEmpty()) return 0
    val cursor = Calendar.getInstance()
    if (fechaClave(cursor.timeInMillis) !in cumplidos) cursor.add(Calendar.DAY_OF_YEAR, -1)
    var racha = 0
    while (fechaClave(cursor.timeInMillis) in cumplidos) {
        racha++
        cursor.add(Calendar.DAY_OF_YEAR, -1)
    }
    return racha
}
