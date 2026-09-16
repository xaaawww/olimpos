package com.olimpos.gym.data

import android.content.Context
import androidx.compose.runtime.Composable
import kotlin.math.ln

/* ═══════════════════════════════════════════════════════
   GAMIFICACIÓN — niveles/estándares de fuerza, PRs, logros,
   Ghost Mode, equivalencias de carga y objetivo de Arena.
   Todo con datos de ejemplo (frontend, sin backend).
   ═══════════════════════════════════════════════════════ */

data class EjercicioFuerza(val nombre: String, val emoji: String)

val EJERCICIOS_FUERZA = listOf(
    EjercicioFuerza("Sentadilla", "🏋️"),
    EjercicioFuerza("Press banca", "🛏️"),
    EjercicioFuerza("Peso muerto", "⚙️"),
    EjercicioFuerza("Dominadas", "🧗"),
    EjercicioFuerza("Flexiones", "🤸"),
    EjercicioFuerza("Elevaciones laterales", "🙌"),
    EjercicioFuerza("Pájaros", "🐦"),
    EjercicioFuerza("Elevación de talones", "🦶")
)


/* ── PRs / marcas personales ── */
data class MarcaPersonal(
    val id: String = "",
    val ejercicio: String,
    val pesoKg: Float,
    val reps: Int,
    val fecha: String,
    /** Momento en que se cargó (epoch millis) — decide cuál es "la" marca
     *  vigente de cada ejercicio para el Bodygraph (ver [resumenMuscular]):
     *  siempre la más reciente, nunca la más alta histórica. */
    val timestamp: Long = 0L,
    val verificado: Boolean
)

// La identidad del socio actual sale de Firebase Auth (ver SocioAuth.kt:
// socioActualId()/socioActualNombre()), no de un valor fijo — cada socio
// entra con la cuenta que le creó un empleado desde el sistema de gestión.
// Tampoco hay marcas de ejemplo: un socio nuevo arranca sin marcas
// cargadas, hasta que registre las suyas en la Calculadora.

/** Estimación de 1RM con fórmula de Epley: peso × (1 + reps/30) */
fun calcular1RM(pesoKg: Float, reps: Int): Float = pesoKg * (1f + reps / 30f)

/* ── Rangos musculares del Bodygraph ──
   9 rangos temáticos (mitología griega, a tono con "OlimpΩs"), cada uno con
   3 niveles salvo el último (Dios), que es el techo del sistema. */
enum class RangoMuscular(val etiqueta: String) {
    MORTAL("Mortal"),
    HOPLITA("Hoplita"),
    ESPARTANO("Espartano"),
    HEROE("Héroe"),
    SEMIDIOS("Semidiós"),
    TITAN("Titán"),
    COLOSO("Coloso"),
    OLIMPICO("Olímpico"),
    DIOS("Dios");

    val nivelesMax: Int get() = if (this == DIOS) 1 else 3
}

data class NivelMuscular(val rango: RangoMuscular, val nivel: Int) {
    val etiquetaCompleta: String get() = if (rango == RangoMuscular.DIOS) rango.etiqueta else "${rango.etiqueta} $nivel"
    /** Progreso 0f..1f dentro del nivel actual, para la barrita hacia el siguiente. */
    fun progreso(puntaje: Float): Float {
        val base = ordenGlobal(rango, nivel) * PUNTOS_POR_NIVEL
        return ((puntaje - base) / PUNTOS_POR_NIVEL).coerceIn(0f, 1f)
    }
}

/** Puntaje necesario para subir un nivel. La curva es lineal a propósito:
 *  este es un juego de progresión de gimnasio, no una tabla de fuerza
 *  competitiva — lo importante es que cueste cada vez un poco más llegar
 *  al tope (Dios) y que sea fácil de calibrar a ojo. */
private const val PUNTOS_POR_NIVEL = 0.14f
private val TOTAL_NIVELES = RangoMuscular.entries.sumOf { it.nivelesMax }

private fun ordenGlobal(rango: RangoMuscular, nivel: Int): Int {
    var acumulado = 0
    for (r in RangoMuscular.entries) {
        if (r == rango) return acumulado + (nivel - 1)
        acumulado += r.nivelesMax
    }
    return acumulado
}

/** Convierte un puntaje acumulado (0f+) en el nivel muscular correspondiente. */
fun nivelDesdePuntaje(puntaje: Float): NivelMuscular {
    val indice = (puntaje / PUNTOS_POR_NIVEL).toInt().coerceIn(0, TOTAL_NIVELES - 1)
    var restante = indice
    for (rango in RangoMuscular.entries) {
        if (restante < rango.nivelesMax) return NivelMuscular(rango, restante + 1)
        restante -= rango.nivelesMax
    }
    return NivelMuscular(RangoMuscular.DIOS, 1)
}

/** Mini-descripción de cada nivel de la Escalera del Olimpo: un apodo y un
 *  texto que ubica al socio frente a "una persona promedio" — no son
 *  estándares de fuerza numéricos (eso se borró a pedido del usuario), sino
 *  una forma narrativa de transmitir qué tan lejos está cada rango. */
data class DescripcionRango(val apodo: String, val texto: String)

val DESCRIPCION_RANGO: Map<NivelMuscular, DescripcionRango> = mapOf(
    NivelMuscular(RangoMuscular.MORTAL, 1) to DescripcionRango(
        "El que comienza",
        "Empezaste a construir un cuerpo más fuerte. Podés superar esfuerzos cotidianos con facilidad y aguantar entrenamientos que antes parecían pesados."
    ),
    NivelMuscular(RangoMuscular.MORTAL, 2) to DescripcionRango(
        "El resistente",
        "Tu condición física empieza a destacar. Podés correr, cargar peso y entrenar durante bastante tiempo sin rendirte fácilmente."
    ),
    NivelMuscular(RangoMuscular.MORTAL, 3) to DescripcionRango(
        "El fuerte",
        "Ya estás por encima de una persona promedio. En una prueba de fuerza, resistencia o velocidad, podrías sorprender a más de uno."
    ),
    NivelMuscular(RangoMuscular.HOPLITA, 1) to DescripcionRango(
        "El firme",
        "Tu cuerpo soporta entrenamientos exigentes con una buena base de fuerza y resistencia. Ya no entrenás solo para verte fuerte, sino para rendir."
    ),
    NivelMuscular(RangoMuscular.HOPLITA, 2) to DescripcionRango(
        "El combatiente",
        "Tu físico es claramente atlético. Podés levantar cargas importantes, correr buenas distancias y sostener un esfuerzo prolongado."
    ),
    NivelMuscular(RangoMuscular.HOPLITA, 3) to DescripcionRango(
        "El incansable",
        "Tu resistencia empieza a ser una de tus mayores fortalezas. Incluso después de un entrenamiento duro, todavía podés seguir adelante."
    ),
    NivelMuscular(RangoMuscular.ESPARTANO, 1) to DescripcionRango(
        "El disciplinado",
        "Tu entrenamiento empieza a convertirse en una rutina seria. Tu cuerpo se adapta al esfuerzo y recuperás fuerzas más rápido."
    ),
    NivelMuscular(RangoMuscular.ESPARTANO, 2) to DescripcionRango(
        "El guerrero",
        "Tenés una condición física notable. Podés sostener un entrenamiento exigente durante bastante tiempo sin perder la técnica ni la concentración."
    ),
    NivelMuscular(RangoMuscular.ESPARTANO, 3) to DescripcionRango(
        "El preparado",
        "Fuerza, resistencia y disciplina empiezan a trabajar juntas. Estás preparado para afrontar pruebas físicas que dejarían agotada a la mayoría."
    ),
    NivelMuscular(RangoMuscular.HEROE, 1) to DescripcionRango(
        "El destacado",
        "Tu rendimiento físico está muy por encima del promedio. Fuerza, resistencia y coordinación empiezan a convertirte en un verdadero atleta."
    ),
    NivelMuscular(RangoMuscular.HEROE, 2) to DescripcionRango(
        "El campeón",
        "Tu cuerpo está preparado para grandes esfuerzos. Podés competir, entrenar intensamente y sostener un rendimiento que pocos consiguen."
    ),
    NivelMuscular(RangoMuscular.HEROE, 3) to DescripcionRango(
        "La leyenda",
        "Alcanzaste un nivel físico excepcional. No sos invencible, pero dentro de un gimnasio pocos podrían igualar tu dedicación y rendimiento."
    ),
    NivelMuscular(RangoMuscular.SEMIDIOS, 1) to DescripcionRango(
        "El excepcional",
        "Tu físico empieza a rozar niveles poco comunes. Tu fuerza y resistencia destacan incluso entre personas acostumbradas a entrenar."
    ),
    NivelMuscular(RangoMuscular.SEMIDIOS, 2) to DescripcionRango(
        "El prodigio",
        "Tu rendimiento es extraordinario. Levantás cargas importantes, soportás sesiones intensas y sostenés una disciplina que pocos pueden mantener."
    ),
    NivelMuscular(RangoMuscular.SEMIDIOS, 3) to DescripcionRango(
        "El fuera de serie",
        "Alcanzaste un nivel atlético que requiere años de entrenamiento constante. Tus resultados ya no son casualidad: son consecuencia de una preparación excepcional."
    ),
    NivelMuscular(RangoMuscular.TITAN, 1) to DescripcionRango(
        "El poderoso",
        "Tu fuerza física es impresionante. Podés mover cargas que para la mayoría serían demasiado exigentes y sostener un rendimiento sólido."
    ),
    NivelMuscular(RangoMuscular.TITAN, 2) to DescripcionRango(
        "El dominante",
        "Tu físico destaca incluso entre atletas experimentados. La fuerza y resistencia que construiste son fruto de una enorme cantidad de trabajo."
    ),
    NivelMuscular(RangoMuscular.TITAN, 3) to DescripcionRango(
        "El gigante",
        "Alcanzaste un nivel físico extraordinario. No necesitás poderes para impresionar: tus propios resultados hablan por vos."
    ),
    NivelMuscular(RangoMuscular.COLOSO, 1) to DescripcionRango(
        "El imponente",
        "Tu presencia física es difícil de ignorar. Combinás tamaño, fuerza y condición física a un nivel reservado para atletas muy dedicados."
    ),
    NivelMuscular(RangoMuscular.COLOSO, 2) to DescripcionRango(
        "El formidable",
        "Tu rendimiento está entre los más altos del gimnasio. Las cargas pesadas y los entrenamientos exigentes forman parte de tu rutina."
    ),
    NivelMuscular(RangoMuscular.COLOSO, 3) to DescripcionRango(
        "El máximo",
        "Llevaste tu preparación física a un nivel excepcional. Superarte ya no depende solamente de entrenar más, sino de perfeccionar cada detalle."
    ),
    NivelMuscular(RangoMuscular.OLIMPICO, 1) to DescripcionRango(
        "El atleta",
        "Tu cuerpo representa años de disciplina. Fuerza, resistencia, movilidad y técnica trabajan juntas para alcanzar un rendimiento extraordinario."
    ),
    NivelMuscular(RangoMuscular.OLIMPICO, 2) to DescripcionRango(
        "El campeón olímpico",
        "Tu preparación está en otro nivel. Cada repetición, cada kilo y cada segundo son el resultado de una disciplina constante y metódica."
    ),
    NivelMuscular(RangoMuscular.OLIMPICO, 3) to DescripcionRango(
        "El élite",
        "Alcanzaste un nivel físico que muy pocas personas consiguen. No sos invencible; simplemente llevaste tu potencial humano extremadamente lejos."
    ),
    NivelMuscular(RangoMuscular.DIOS, 1) to DescripcionRango(
        "La cima humana",
        "Llevaste tu cuerpo y tu disciplina a un nivel extraordinario. No necesitás romper las leyes de la física para ser considerado un dios: lograste acercarte al máximo potencial que un ser humano puede alcanzar."
    )
)

/** % en que cada ejercicio de la calculadora entrena cada zona muscular —
 *  ninguno trabaja "todo el cuerpo por igual": cada uno tiene su músculo
 *  protagonista (100%) y varios secundarios en menor medida. "Core" en
 *  Sentadilla se reparte entre oblicuos y lumbares (estabilización), y se
 *  suma aparte a abdominales — son dos roles distintos del mismo gesto. */
val CONTRIBUCION_MUSCULAR: Map<String, Map<ZonaMuscular, Float>> = mapOf(
    "Press banca" to mapOf(
        ZonaMuscular.PECHO_INFERIOR to 1f, ZonaMuscular.PECHO_SUPERIOR to 0.5f,
        ZonaMuscular.TRICEPS to 0.6f, ZonaMuscular.DELTOIDES_ANTERIOR to 0.5f
    ),
    "Flexiones" to mapOf(
        ZonaMuscular.PECHO_INFERIOR to 0.75f, ZonaMuscular.PECHO_SUPERIOR to 0.5f,
        ZonaMuscular.TRICEPS to 0.5f, ZonaMuscular.DELTOIDES_ANTERIOR to 0.4f,
        ZonaMuscular.ABDOMINALES to 0.25f, ZonaMuscular.OBLICUOS to 0.25f
    ),
    "Dominadas" to mapOf(
        ZonaMuscular.DORSALES to 1f, ZonaMuscular.BICEPS to 0.65f,
        ZonaMuscular.ANTEBRAZOS to 0.5f, ZonaMuscular.TRAPECIO to 0.35f
    ),
    "Sentadilla" to mapOf(
        ZonaMuscular.CUADRICEPS to 1f, ZonaMuscular.GLUTEOS to 0.7f,
        ZonaMuscular.ADUCTORES to 0.4f, ZonaMuscular.OBLICUOS to 0.3f, ZonaMuscular.LUMBARES to 0.3f,
        ZonaMuscular.ISQUIOTIBIALES to 0.15f, ZonaMuscular.ABDOMINALES to 0.2f, ZonaMuscular.ABDUCTORES to 0.1f
    ),
    "Peso muerto" to mapOf(
        ZonaMuscular.GLUTEOS to 0.95f, ZonaMuscular.ISQUIOTIBIALES to 0.85f,
        ZonaMuscular.LUMBARES to 0.8f, ZonaMuscular.ANTEBRAZOS to 0.6f,
        ZonaMuscular.TRAPECIO to 0.5f, ZonaMuscular.CUADRICEPS to 0.2f, ZonaMuscular.ADUCTORES to 0.15f
    ),
    // Los tres de acá abajo son los únicos que entrenan deltoides medio,
    // deltoides posterior y pantorrillas — sin ellos esas 3 zonas del
    // Bodygraph se quedan sin forma de subir de rango nunca.
    "Elevaciones laterales" to mapOf(
        ZonaMuscular.DELTOIDES_MEDIO to 1f, ZonaMuscular.TRAPECIO to 0.2f
    ),
    "Pájaros" to mapOf(
        ZonaMuscular.DELTOIDES_POSTERIOR to 1f, ZonaMuscular.TRAPECIO to 0.3f
    ),
    "Elevación de talones" to mapOf(
        ZonaMuscular.PANTORRILLAS to 1f
    )
)

/** Dominadas y flexiones mueven el peso corporal + lo que se le agregue —
 *  a diferencia de un press o una sentadilla, donde [MarcaPersonal.pesoKg]
 *  ya es toda la carga. Sin esto, cargar "0kg" en flexiones (peso corporal
 *  puro) puntuaría como si no se hubiese entrenado nada. */
private val EJERCICIOS_PESO_CORPORAL = setOf("Dominadas", "Flexiones")

/** Para la Calculadora/Mis marcas: en estos ejercicios el peso no hace
 *  falta (se puede registrar solo con reps) porque la carga real es el
 *  propio cuerpo — el campo "Peso (kg)" pasa a ser el agregado opcional
 *  (lastre, chaleco), no la carga total. */
fun esEjercicioPesoCorporal(ejercicio: String): Boolean = ejercicio in EJERCICIOS_PESO_CORPORAL

private fun cargaTotal(marca: MarcaPersonal, pesoCorporalKg: Float): Float =
    if (marca.ejercicio in EJERCICIOS_PESO_CORPORAL) pesoCorporalKg + marca.pesoKg else marca.pesoKg

/** Versión pública de [cargaTotal] — para mostrar el 1RM real (con el peso
 *  corporal ya sumado) en el historial de Mis marcas, en vez del peso
 *  agregado solo, que en dominadas/flexiones sin lastre queda en 0. */
fun cargaEfectivaDeMarca(marca: MarcaPersonal, pesoCorporalKg: Float): Float = cargaTotal(marca, pesoCorporalKg)

/* ── Calibración de rangos contra tablas de fuerza reales ──
   Cada ejercicio tiene su propio "piso" (ratio carga/peso-corporal de un
   principiante — cae en Mortal 1) y "techo" (ratio de Dios, ~15% por
   encima del nivel "Elite" publicado, para que sea de verdad excepcional:
   el 0,1% más fuerte, no solo "avanzado"). No es lo mismo levantar 150kg
   en press banca que en peso muerto, así que cada ejercicio se mide contra
   su propia vara, no una sola tabla genérica.
   Sentadilla/Press banca/Peso muerto/Dominadas: pisos y techos basados en
   tablas de fuerza publicadas (StrongerMobile, FORMA, strengthcalculator.org
   — beginner/elite en múltiplos del peso corporal; ratio mujer/hombre según
   la guía de esas mismas fuentes: ~80% en tren inferior, ~65% en tren
   superior, y el dato específico de dominadas con carga total).
   Flexiones/Pájaros/Elevación de talones: sin tabla pública consolidada —
   estimados por analogía con el movimiento comparable (flexiones ~ press
   banca con otra palanca; pájaros ~ una fracción de elevaciones laterales;
   elevación de talones ~ sentadilla, más accesible). */
private data class AnclaFuerza(val beginnerM: Float, val diosM: Float, val beginnerF: Float, val diosF: Float)

private val ANCLAS_FUERZA: Map<String, AnclaFuerza> = mapOf(
    "Sentadilla" to AnclaFuerza(beginnerM = 0.75f, diosM = 2.90f, beginnerF = 0.60f, diosF = 2.32f),
    "Press banca" to AnclaFuerza(beginnerM = 0.50f, diosM = 2.30f, beginnerF = 0.33f, diosF = 1.50f),
    "Peso muerto" to AnclaFuerza(beginnerM = 1.00f, diosM = 3.15f, beginnerF = 0.80f, diosF = 2.52f),
    "Dominadas" to AnclaFuerza(beginnerM = 1.00f, diosM = 2.90f, beginnerF = 1.00f, diosF = 2.65f),
    "Flexiones" to AnclaFuerza(beginnerM = 0.65f, diosM = 2.20f, beginnerF = 0.42f, diosF = 1.43f),
    "Elevaciones laterales" to AnclaFuerza(beginnerM = 0.07f, diosM = 0.33f, beginnerF = 0.053f, diosF = 0.25f),
    "Pájaros" to AnclaFuerza(beginnerM = 0.056f, diosM = 0.264f, beginnerF = 0.042f, diosF = 0.20f),
    "Elevación de talones" to AnclaFuerza(beginnerM = 0.60f, diosM = 2.75f, beginnerF = 0.48f, diosF = 2.20f)
)

/** Puntaje (misma escala 0f.. que usa [nivelDesdePuntaje]) de UNA marca
 *  puntual, calibrado contra su ancla de fuerza. La progresión es
 *  logarítmica a propósito: en la vida real cuesta mucho menos pasar de
 *  principiante a novato que de avanzado a elite, así que un ratio a mitad
 *  de camino entre el piso y el techo NO debería dar la mitad del puntaje. */
fun puntajeDeMarca(marca: MarcaPersonal, pesoCorporalKg: Float, sexo: SexoBiologico?): Float {
    if (pesoCorporalKg <= 0f) return 0f
    val ancla = ANCLAS_FUERZA[marca.ejercicio] ?: return 0f
    val (piso, techo) = when (sexo) {
        SexoBiologico.MASCULINO -> ancla.beginnerM to ancla.diosM
        SexoBiologico.FEMENINO -> ancla.beginnerF to ancla.diosF
        else -> (ancla.beginnerM + ancla.beginnerF) / 2f to (ancla.diosM + ancla.diosF) / 2f
    }
    val ratio = cargaTotal(marca, pesoCorporalKg) / pesoCorporalKg
    if (ratio <= 0f) return 0f
    val progreso = (ln(ratio / piso) / ln(techo / piso)).coerceIn(0f, 1f)
    return progreso * TOTAL_NIVELES * PUNTOS_POR_NIVEL
}

/** Cuántos ejercicios distintos hay que tener registrados (con marca
 *  vigente) para entrar en la Escalera del Olimpo — sin este piso, alguien
 *  con una sola marca cargada (buena o mala) tendría un rango "general"
 *  tan válido como alguien entrenado de verdad. 3 de los 8 ejercicios de la
 *  Calculadora: más de un tercio, para que el promedio no dependa de un
 *  único levantamiento. */
const val MINIMO_EJERCICIOS_PARA_CLASIFICACION = 3

/** Cuántos ejercicios distintos tiene registrados (con o sin verificar) —
 *  para avisarle al socio cuántos le faltan para entrar en la Escalera. */
fun cantidadEjerciciosVigentes(marcas: List<MarcaPersonal>): Int = marcas.map { it.ejercicio }.distinct().size

/** Resumen muscular calculado a partir de las marcas del socio: puntaje por
 *  zona + si ese resultado está respaldado por marcas ya verificadas. */
data class ResumenMuscular(
    val puntajes: Map<ZonaMuscular, Float>,
    val verificado: Boolean,
    val tieneMarcas: Boolean
)

/** Solo cuenta la marca MÁS RECIENTE de cada ejercicio (no la más alta
 *  histórica, ni la suma de todas) — cargar una marca nueva reemplaza a la
 *  anterior para el cálculo, no se acumulan puntos. Así el rango baja si
 *  la marca nueva es más floja, en vez de quedar pegado arriba por una
 *  marca vieja (aunque siga visible en el historial de "Mis marcas"). El
 *  estado "verificado" del Bodygraph depende de si esas marcas vigentes ya
 *  fueron confirmadas por un entrenador. Esto arma el detalle POR ZONA del
 *  Bodygraph — para el rango GENERAL de la Escalera del Olimpo usar
 *  [puntajeGeneralDeSocio], que promedia por ejercicio en vez de por zona
 *  (si no, un socio que solo hace los 3 grandes levantamientos queda con
 *  deltoides medio/posterior y pantorrillas en cero para siempre, porque
 *  hoy son zonas que solo entrenan las 3 isolaciones de la Calculadora). */
fun resumenMuscular(marcas: List<MarcaPersonal>, pesoCorporalKg: Float, sexo: SexoBiologico? = null): ResumenMuscular {
    val vigentePorEjercicio = marcas.groupBy { it.ejercicio }
        .mapNotNull { (_, ms) -> ms.maxByOrNull { it.timestamp } }

    val puntajes = mutableMapOf<ZonaMuscular, Float>()
    vigentePorEjercicio.forEach { marca ->
        val puntajeEjercicio = puntajeDeMarca(marca, pesoCorporalKg, sexo)
        CONTRIBUCION_MUSCULAR[marca.ejercicio]?.forEach { (zona, peso) ->
            puntajes[zona] = (puntajes[zona] ?: 0f) + puntajeEjercicio * peso
        }
    }

    return ResumenMuscular(
        puntajes = puntajes,
        verificado = vigentePorEjercicio.isNotEmpty() && vigentePorEjercicio.all { it.verificado },
        tieneMarcas = vigentePorEjercicio.isNotEmpty()
    )
}

/** Rango GENERAL para la Escalera del Olimpo: promedio del puntaje
 *  calibrado de cada ejercicio vigente (no por zona muscular — ver el
 *  comentario en [resumenMuscular]). `null` si no llega al mínimo de
 *  [MINIMO_EJERCICIOS_PARA_CLASIFICACION] ejercicios distintos. */
fun puntajeGeneralDeSocio(marcas: List<MarcaPersonal>, pesoCorporalKg: Float, sexo: SexoBiologico?): Float? {
    val vigentePorEjercicio = marcas.groupBy { it.ejercicio }
        .mapNotNull { (_, ms) -> ms.maxByOrNull { it.timestamp } }
    if (vigentePorEjercicio.size < MINIMO_EJERCICIOS_PARA_CLASIFICACION) return null
    return vigentePorEjercicio.map { puntajeDeMarca(it, pesoCorporalKg, sexo) }.average().toFloat()
}

/** Ejercicio en el que el socio levanta más veces su propio peso —
 *  el dato detrás de "{nombre} levanta X veces su peso" en Clasificación. */
data class MejorLevantamiento(val ejercicio: String, val vecesPesoCorporal: Float)

fun mejorLevantamientoVigente(marcas: List<MarcaPersonal>, pesoCorporalKg: Float): MejorLevantamiento? {
    if (pesoCorporalKg <= 0f) return null
    return marcas.groupBy { it.ejercicio }
        .mapNotNull { (_, ms) -> ms.maxByOrNull { it.timestamp } }
        .maxByOrNull { cargaTotal(it, pesoCorporalKg) / pesoCorporalKg }
        ?.let { MejorLevantamiento(it.ejercicio, cargaTotal(it, pesoCorporalKg) / pesoCorporalKg) }
}

/** Suma de la carga vigente (mismo criterio que [resumenMuscular]: solo la
 *  marca más reciente de cada ejercicio) de todos los ejercicios del socio —
 *  el "kg levantados" que se muestra en la Escalera del Olimpo. */
fun kgTotalesVigentes(marcas: List<MarcaPersonal>, pesoCorporalKg: Float): Float {
    val vigentePorEjercicio = marcas.groupBy { it.ejercicio }
        .mapNotNull { (_, ms) -> ms.maxByOrNull { it.timestamp } }
    return vigentePorEjercicio.sumOf { cargaTotal(it, pesoCorporalKg).toDouble() }.toFloat()
}

/** Texto de antigüedad ("Socio hace 3 meses") a partir de la fecha de alta
 *  de su acceso a la app (ver auth_repo.py: "creado_ms" en Firestore) — es
 *  la única fecha real que existe hoy por socio, así que se usa como
 *  aproximación de cuánto hace que forma parte del club. */
fun formatearAntiguedad(creadoMs: Long?): String {
    if (creadoMs == null) return "Fecha de alta no disponible"
    val dias = ((System.currentTimeMillis() - creadoMs) / 86_400_000L).coerceAtLeast(0)
    return when {
        dias < 1 -> "Se unió hoy"
        dias < 7 -> "Socio hace $dias día${if (dias == 1L) "" else "s"}"
        dias < 30 -> (dias / 7).let { "Socio hace $it semana${if (it == 1L) "" else "s"}" }
        dias < 365 -> (dias / 30).let { "Socio hace $it mes${if (it == 1L) "" else "es"}" }
        else -> (dias / 365).let { "Socio hace $it año${if (it == 1L) "" else "s"}" }
    }
}

/** Fecha legible ("13 sep 2026") a partir del timestamp real con el que se
 *  guarda cada marca — antes el campo "fecha" se guardaba como el literal
 *  "hoy", así que una marca cargada la semana pasada seguía mostrando "hoy"
 *  para siempre en el historial. El timestamp real (epoch ms) siempre
 *  existió; lo que faltaba era mostrarlo como texto. */
fun fechaLegible(timestampMs: Long): String {
    val formato = java.text.SimpleDateFormat("d MMM yyyy", java.util.Locale("es", "ES"))
    return formato.format(java.util.Date(timestampMs))
}

private fun fechaCorta(timestampMs: Long): String {
    val formato = java.text.SimpleDateFormat("d/M", java.util.Locale("es", "ES"))
    return formato.format(java.util.Date(timestampMs))
}

/** Evolución real de 1RM estimado a lo largo del tiempo, para el gráfico de
 *  "Evolución de fuerza" de Progreso. Se elige automáticamente el ejercicio
 *  con más marcas cargadas (el que tiene más puntos para graficar) — el
 *  socio no elige uno fijo porque cuál entrena más varía de persona a
 *  persona. `null` si todavía no cargó ninguna marca. */
data class EvolucionFuerza(val ejercicio: String, val puntos: List<PuntoEvolucion>)

fun evolucionDeFuerza(marcas: List<MarcaPersonal>): EvolucionFuerza? {
    if (marcas.isEmpty()) return null
    val ejercicioConMasHistoria = marcas.groupBy { it.ejercicio }
        .maxByOrNull { (_, ms) -> ms.size }
        ?.key ?: return null
    val puntos = marcas
        .filter { it.ejercicio == ejercicioConMasHistoria }
        .sortedBy { it.timestamp }
        .map { PuntoEvolucion(etiqueta = fechaCorta(it.timestamp), valor = calcular1RM(it.pesoKg, it.reps)) }
    return EvolucionFuerza(ejercicioConMasHistoria, puntos)
}

/* ── Logros / medallas ── */
data class Logro(
    val emoji: String,
    val nombre: String,
    val descripcion: String,
    val progreso: Float,
    val desbloqueado: Boolean,
    /** Los secretos no aparecen en la grilla ni cuentan para el total hasta
     *  que se desbloquean — son un bonus raro, no parte del 100% normal. */
    val secreto: Boolean = false
)

// Los 53 arrancan en 0f/false acá porque esto es solo la DEFINICIÓN (emoji,
// nombre, descripción) — el progreso/desbloqueo real de cada socio lo
// calcula calcularLogros() a partir de sus propios datos (marcas, series,
// ingresos, rangos musculares). Los que todavía no tienen una fuente de
// datos real detrás (un plan de dieta día a día, reservar una máquina
// desde el Plano) se quedan en 0f/false ahí también — ver el comentario
// en calcularLogros.

val LOGROS = listOf(
    // ── Constancia y racha ──
    Logro("🔥", "Racha de fuego", "7 días seguidos entrenando", 0f, false),
    Logro("🎯", "Constancia de hierro", "30 días de asistencia en el mes", 0f, false),
    Logro("🛡️", "Racha de titanio", "30 días seguidos entrenando sin cortar la racha", 0f, false),
    Logro("♾️", "Racha eterna", "100 días seguidos entrenando", 0f, false),
    Logro("🐣", "Primer paso", "Completá tu primer entrenamiento", 0f, false),
    Logro("🌅", "Madrugador", "Entrená antes de las 7 de la mañana", 0f, false),
    Logro("🌙", "Búho nocturno", "Entrená después de las 22h", 0f, false),
    Logro("🎉", "Sin excusas", "Entrená un feriado", 0f, false),
    Logro("🏖️", "Guerrero de fin de semana", "Entrená sábado y domingo la misma semana", 0f, false),
    Logro("🔁", "Doble turno", "Entrená dos veces el mismo día", 0f, false),
    Logro("🐦‍🔥", "Ave fénix", "Volvé a entrenar después de 30 días de pausa", 0f, false),
    // ── Fuerza y marcas ──
    Logro("⚡", "Cazador de PRs", "5 marcas personales verificadas", 0f, false),
    Logro("🐘", "Levantador de elefantes", "Acumulá 6.000kg movidos en un mes", 0f, false),
    Logro("🏋️", "Club de los 100kg", "Sentadilla ≥ 100kg", 0f, false),
    Logro("🛏️", "Club de los 120kg", "Press de banca ≥ 120kg", 0f, false),
    Logro("⛓️", "Club de los 150kg", "Peso muerto ≥ 150kg", 0f, false),
    Logro("🧗", "Dominador", "10 dominadas seguidas sin soltar la barra", 0f, false),
    Logro("🤸", "Máquina de flexiones", "50 flexiones seguidas", 0f, false),
    Logro("✅", "Verificado", "Tu primera marca confirmada por un entrenador", 0f, false),
    Logro("🕵️", "Sin trampas", "10 marcas verificadas seguidas", 0f, false),
    Logro("🧮", "Calculadora en mano", "Usá la Calculadora 10 veces", 0f, false),
    // ── Bodygraph y rangos ──
    Logro("💪", "Bíceps de acero", "Bíceps en rango Héroe o superior", 0f, false),
    Logro("🦵", "Piernas de Titán", "Cuádriceps en rango Titán o superior", 0f, false),
    Logro("🔺", "Espalda de Coloso", "Dorsales en rango Coloso o superior", 0f, false),
    Logro("🎽", "Pecho Olímpico", "Pecho en rango Olímpico", 0f, false),
    Logro("⚖️", "Cuerpo equilibrado", "Las 19 zonas musculares en rango Hoplita o superior", 0f, false),
    Logro("👁️", "Ojo en el progreso", "Revisá tu Bodygraph 20 veces", 0f, false),
    // ── Exploración de la app ──
    Logro("🧭", "Explorador", "Visitá las 6 secciones de la Arena", 0f, false),
    Logro("🗺️", "Cartógrafo", "Mirá el Plano del gimnasio", 0f, false),
    Logro("🎚️", "Cambio de look", "Cambiá tu objetivo de la Arena", 0f, false),
    Logro("🏆", "Coleccionista", "Desbloqueá 25 logros", 0f, false),
    Logro("👑", "Casi leyenda", "Desbloqueá 40 logros", 0f, false),
    // ── Ranking y comunidad ──
    Logro("📈", "Rey del ranking", "Llegá al top 3 en Clasificación", 0f, false),
    Logro("🥇", "Corona de laurel", "Llegá al puesto #1 en Clasificación", 0f, false),
    Logro("🤝", "Mentor", "Agregá a tu primer compañero de entrenamiento", 0f, false),
    Logro("👥", "Espíritu de equipo", "Entrená junto a un amigo 5 veces", 0f, false),
    // ── Nutrición ──
    Logro("🥗", "Plato consciente", "Completá tu perfil nutricional", 0f, false),
    Logro("🍽️", "Sibarita", "Probá 10 platos distintos del catálogo", 0f, false),
    Logro("📅", "Nutricionista amateur", "Completá 7 días seguidos tu plan de dieta", 0f, false),
    Logro("💧", "Hidratado", "Registrá tu consumo de agua 7 días seguidos", 0f, false),
    // ── Objetivos de la Arena ──
    Logro("🏁", "Meta cumplida", "Alcanzá el objetivo de fuerza que elegiste", 0f, false),
    Logro("💪", "Meta de hipertrofia", "Alcanzá tu objetivo de hipertrofia", 0f, false),
    Logro("❤️", "Salud ante todo", "Alcanzá tu objetivo de salud general", 0f, false),
    // ── Gimnasio físico ──
    Logro("📲", "Puntualidad", "Ingresá al gimnasio con QR 20 veces", 0f, false),
    Logro("🖐️", "Biométrico", "Ingresá al gimnasio con huella 10 veces", 0f, false),
    Logro("🔒", "Casillero propio", "Reservá tu primer locker", 0f, false),
    Logro("📍", "Bien equipado", "Reservá una máquina desde el Plano", 0f, false),
    Logro("🎂", "Cliente fiel", "Cumplí 6 meses de membresía activa", 0f, false),
    Logro("📸", "Antes y después", "Subí tu primera foto de progreso", 0f, false),
    Logro("🎓", "Graduado", "Completá el onboarding completo de OlimpΩs", 0f, false),
    // ── Secretos: no aparecen en la grilla hasta desbloquearse ──
    Logro("🦉", "El ojo de Atenea", "Entrená pasada la medianoche 5 veces", 0f, false, secreto = true),
    Logro("🌟", "Ascensión completa", "Las 19 zonas musculares alcanzaron rango Dios", 0f, false, secreto = true),
    Logro("🔱", "Corazón de Esparta", "Cargá una marca en los 5 ejercicios de la Calculadora el mismo día", 0f, false, secreto = true)
)

/** Todo lo que hace falta para calcular los logros de un socio — cada
 *  campo sale de una fuente ya real (Firestore), nada inventado. */
data class ContextoLogros(
    val socioId: String,
    val marcas: List<MarcaPersonal>,
    val series: List<SerieEntrenamiento>,
    val ingresos: List<Long>,
    val pesoCorporalKg: Float,
    val sexo: SexoBiologico?,
    val rangosSocios: List<SocioRango>,
    val onboardingCompleto: Boolean,
    /** Cuántos ingresos se marcaron con cada método (ver AccesoScreen) —
     *  ninguno es un lector real todavía, es el método que el socio tenía
     *  activado al tocar "Marcar mi ingreso de hoy". */
    val ingresosQr: Int = 0,
    val ingresosBiometrico: Int = 0,
    val vioPlano: Boolean = false,
    val vistasBodygraph: Int = 0,
    val seccionesArenaVisitadas: Int = 0,
    /** Distintos objetivos de la Arena que probó alguna vez (ver
     *  objetivosProbadosAlgunaVez en este mismo archivo). */
    val objetivosDistintosProbados: Int = 0,
    val tieneLockerReservado: Boolean = false,
    val tienePerfilNutricional: Boolean = false,
    /** Fecha real de inicio de la membresía asignada por un empleado
     *  (ver MembresiaRepository.kt) — `null` si todavía no le asignaron
     *  ninguna. */
    val membresiaFechaInicioMs: Long? = null,
    val platosDistintosProbados: Int = 0,
    /** Timestamps de "hoy tomé agua" (ver AguaRepository.kt) — se calcula
     *  la racha acá mismo, igual que con los ingresos. */
    val registrosAgua: List<Long> = emptyList(),
    val tieneFotoDeProgreso: Boolean = false,
    val tieneCompanero: Boolean = false,
    /** Ver [contarDiasEntrenadosConCompaneros] — días distintos que
     *  entrenó junto a algún compañero. */
    val diasEntrenadosConCompaneros: Int = 0
)

/** Arma el [ContextoLogros] leyendo [DatosRemotos] — un solo lugar para esta
 *  lógica, compartido por LogrosScreen (muestra la grilla) y ObservadorDeLogros
 *  (vigila en segundo plano para disparar la notificación de logro
 *  desbloqueado). Al ser @Composable, cada campo de DatosRemotos leído acá
 *  suscribe recomposición — no hace falta una lista manual de `remember(...)`. */
@Composable
fun construirContextoLogros(contexto: Context): ContextoLogros {
    val marcas = DatosRemotos.marcas ?: emptyList()
    val series = DatosRemotos.seriesEntrenamiento ?: emptyList()
    val ingresos = DatosRemotos.ingresos ?: emptyList()
    val rangosSocios = DatosRemotos.rangosSocios ?: emptyList()
    val datosFisicos = DatosRemotos.datosFisicosPropios
    val lockersOcupados = DatosRemotos.lockersOcupados ?: emptyMap()
    val perfilNutricional = DatosRemotos.perfilNutricional
    val membresia = DatosRemotos.membresia
    val platosProbados = DatosRemotos.platosProbados ?: emptySet()
    val registrosAgua = DatosRemotos.registrosAgua ?: emptyList()
    val fotosProgreso = DatosRemotos.fotosProgreso ?: emptyList()
    val companeros = DatosRemotos.companeros ?: emptyList()
    val diasEntrenadosConCompaneros = DatosRemotos.diasEntrenadosConCompaneros
    val socioId = socioActualId()
    return ContextoLogros(
        socioId = socioId,
        marcas = marcas,
        series = series,
        ingresos = ingresos.map { it.timestamp },
        pesoCorporalKg = datosFisicos?.pesoKg ?: 80f,
        sexo = datosFisicos?.sexo,
        rangosSocios = rangosSocios,
        onboardingCompleto = datosFisicos != null,
        ingresosQr = ingresos.count { it.metodo == "qr" },
        ingresosBiometrico = ingresos.count { it.metodo == "biometrico" },
        vioPlano = datosFisicos?.vioPlano ?: false,
        vistasBodygraph = datosFisicos?.vistasBodygraph ?: 0,
        seccionesArenaVisitadas = datosFisicos?.seccionesArenaVisitadas?.size ?: 0,
        objetivosDistintosProbados = objetivosProbadosAlgunaVez(contexto).size,
        tieneLockerReservado = lockersOcupados.containsValue(socioId),
        tienePerfilNutricional = perfilNutricional != null && (perfilNutricional.preferencias.isNotEmpty() || perfilNutricional.excluidos.isNotEmpty()),
        membresiaFechaInicioMs = membresia?.fechaInicioMs,
        platosDistintosProbados = platosProbados.size,
        registrosAgua = registrosAgua,
        tieneFotoDeProgreso = fotosProgreso.isNotEmpty(),
        tieneCompanero = companeros.isNotEmpty(),
        diasEntrenadosConCompaneros = diasEntrenadosConCompaneros
    )
}

private fun diaEpoch(timestampMs: Long): Long = timestampMs / 86_400_000L

/** Día de la semana de un "día-epoch" (0=domingo..6=sábado) — el 1/1/1970
 *  (día-epoch 0) fue jueves, de ahí el +4. Aproximado a UTC, no al huso
 *  horario local: suficiente para un logro, no para nada que dependa de
 *  precisión al minuto. */
private fun diaSemana(diaEpoch: Long): Int = ((diaEpoch + 4) % 7).toInt()

private fun horaLocal(timestampMs: Long): Int =
    java.util.Calendar.getInstance().apply { timeInMillis = timestampMs }.get(java.util.Calendar.HOUR_OF_DAY)

/** Feriados nacionales argentinos de fecha fija (mes, día) — simplificado:
 *  varios feriados reales se trasladan al lunes más cercano (ley 27.399) y
 *  hay puentes que cambian cada año, pero para este logro alcanza con la
 *  fecha de referencia. No incluye Semana Santa (depende de una fecha
 *  móvil que no vale la pena calcular acá). */
private val FERIADOS_ARGENTINA_MES_DIA = setOf(
    1 to 1,    // Año Nuevo
    3 to 24,   // Día de la Memoria
    4 to 2,    // Día del Veterano y de los Caídos en Malvinas
    5 to 1,    // Día del Trabajador
    5 to 25,   // Día de la Revolución de Mayo
    6 to 20,   // Paso a la Inmortalidad del Gral. Belgrano
    7 to 9,    // Día de la Independencia
    8 to 17,   // Paso a la Inmortalidad del Gral. San Martín
    10 to 12,  // Día del Respeto a la Diversidad Cultural
    11 to 20,  // Día de la Soberanía Nacional
    12 to 8,   // Inmaculada Concepción de María
    12 to 25   // Navidad
)

private fun esFeriadoArgentino(timestampMs: Long): Boolean {
    val cal = java.util.Calendar.getInstance().apply { timeInMillis = timestampMs }
    return (cal.get(java.util.Calendar.MONTH) + 1) to cal.get(java.util.Calendar.DAY_OF_MONTH) in FERIADOS_ARGENTINA_MES_DIA
}

/** Racha consecutiva más larga entre los días (en "día-epoch") dados —
 *  se usa la más larga de toda la historia, no la actual: un logro de
 *  racha ya ganado no debería "perderse" si después se corta la racha. */
private fun rachaMasLarga(dias: Set<Long>): Int {
    if (dias.isEmpty()) return 0
    var mejor = 0
    dias.forEach { dia ->
        if (dia - 1 !in dias) {
            var largo = 1
            var actual = dia
            while (actual + 1 in dias) { actual++; largo++ }
            if (largo > mejor) mejor = largo
        }
    }
    return mejor
}

/** Racha ACTUAL de días seguidos yendo al gimnasio, contando desde hoy (o
 *  desde ayer, si todavía no marcaste el ingreso de hoy — un día de
 *  gracia para no cortar la racha por no haber abierto la app todavía).
 *  A diferencia de [rachaMasLarga] (que se usa para los logros y nunca
 *  "retrocede"), esta es la que se muestra en Perfil y sí baja a 0 si se
 *  corta. */
fun rachaActualDeDias(ingresos: List<Long>): Int {
    val dias = ingresos.map(::diaEpoch).toSet()
    if (dias.isEmpty()) return 0
    val hoy = System.currentTimeMillis() / 86_400_000L
    var cursor = when {
        hoy in dias -> hoy
        (hoy - 1) in dias -> hoy - 1
        else -> return 0
    }
    var racha = 0
    while (cursor in dias) { racha++; cursor-- }
    return racha
}

/** Cuántos días distintos hubo al menos un ingreso en el mes calendario
 *  actual — para "Visitas mes" en Perfil y "Constancia de hierro". */
fun visitasEnElMesActual(ingresos: List<Long>): Int {
    val hoyCal = java.util.Calendar.getInstance()
    return ingresos.map(::diaEpoch).toSet().count { dia ->
        val cal = java.util.Calendar.getInstance().apply { timeInMillis = dia * 86_400_000L }
        cal.get(java.util.Calendar.MONTH) == hoyCal.get(java.util.Calendar.MONTH) &&
            cal.get(java.util.Calendar.YEAR) == hoyCal.get(java.util.Calendar.YEAR)
    }
}

private fun mapaKgPorMes(marcas: List<MarcaPersonal>, series: List<SerieEntrenamiento>, pesoCorporalKg: Float): Map<Pair<Int, Int>, Float> {
    val porMes = mutableMapOf<Pair<Int, Int>, Float>()
    fun sumar(timestamp: Long, kg: Float) {
        val cal = java.util.Calendar.getInstance().apply { timeInMillis = timestamp }
        val clave = cal.get(java.util.Calendar.YEAR) to cal.get(java.util.Calendar.MONTH)
        porMes[clave] = (porMes[clave] ?: 0f) + kg
    }
    marcas.forEach { sumar(it.timestamp, cargaTotal(it, pesoCorporalKg) * it.reps) }
    series.forEach { sumar(it.timestamp, (if (it.esPesoCorporal) pesoCorporalKg + it.pesoKg else it.pesoKg) * it.reps) }
    return porMes
}

private fun mejorMesKg(marcas: List<MarcaPersonal>, series: List<SerieEntrenamiento>, pesoCorporalKg: Float): Float =
    mapaKgPorMes(marcas, series, pesoCorporalKg).values.maxOrNull() ?: 0f

/** Posición (1 = primero) en la Escalera del Olimpo completa, ordenando
 *  por rango+nivel y de ahí por kg totales — `null` si el socio no
 *  aparece en la lista compartida (por ejemplo, si se ocultó de la
 *  Clasificación). */
private fun posicionEnRanking(socioId: String, rangosSocios: List<SocioRango>): Int? {
    val orden = rangosSocios.sortedWith(
        compareByDescending<SocioRango> { it.nivel.rango.ordinal }
            .thenByDescending { it.nivel.nivel }
            .thenByDescending { it.kgTotales }
    )
    val indice = orden.indexOfFirst { it.socioId == socioId }
    return if (indice >= 0) indice + 1 else null
}

/** Calcula el progreso/desbloqueo real de cada logro a partir de los datos
 *  del socio. Los que no tienen todavía una fuente de datos real detrás
 *  (cumplimiento de un plan de dieta día a día, reservar una máquina desde
 *  el Plano) se dejan tal cual vienen en [LOGROS] — 0%, bloqueados — en vez
 *  de inventar un progreso. */
fun calcularLogros(ctx: ContextoLogros): List<Logro> {
    val diasIngreso = ctx.ingresos.map(::diaEpoch).toSet()
    val racha = rachaMasLarga(diasIngreso)
    val visitasEsteMes = visitasEnElMesActual(ctx.ingresos)
    val finDeSemanaCompleto = diasIngreso.any { dia -> diaSemana(dia) == 6 && (dia + 1) in diasIngreso }
    val dosVecesElMismoDia = ctx.series.groupBy { diaEpoch(it.timestamp) }
        .any { (_, ss) -> ss.size >= 2 && (ss.maxOf { it.timestamp } - ss.minOf { it.timestamp }) >= 4 * 60 * 60 * 1000L }
    val pausaLargaYVolvio = diasIngreso.sorted().zipWithNext().any { (a, b) -> b - a >= 30 }

    fun vigente(ejercicio: String) = ctx.marcas.filter { it.ejercicio == ejercicio }.maxByOrNull { it.timestamp }

    val resumen = resumenMuscular(ctx.marcas, ctx.pesoCorporalKg, ctx.sexo)
    val nivelesPorZona = ZonaMuscular.entries.associateWith { z -> resumen.puntajes[z]?.let(::nivelDesdePuntaje) }
    fun rangoDe(z: ZonaMuscular) = nivelesPorZona[z]?.rango
    fun alMenos(z: ZonaMuscular, minimo: RangoMuscular) = (rangoDe(z)?.ordinal ?: -1) >= minimo.ordinal

    val posicion = posicionEnRanking(ctx.socioId, ctx.rangosSocios)

    val marcasPorDia = ctx.marcas.groupBy { diaEpoch(it.timestamp) }
    val diasCorazonEsparta = marcasPorDia.any { (_, ms) -> ms.map { it.ejercicio }.distinct().size >= 5 }

    val diasMadrugonExtremo = ctx.series.filter { horaLocal(it.timestamp) in 0..4 }
        .map { diaEpoch(it.timestamp) }.distinct().size

    val resultados = mutableMapOf<String, Pair<Float, Boolean>>()
    resultados["Racha de fuego"] = (racha / 7f).coerceIn(0f, 1f) to (racha >= 7)
    resultados["Racha de titanio"] = (racha / 30f).coerceIn(0f, 1f) to (racha >= 30)
    resultados["Racha eterna"] = (racha / 100f).coerceIn(0f, 1f) to (racha >= 100)
    resultados["Constancia de hierro"] = (visitasEsteMes / 30f).coerceIn(0f, 1f) to (visitasEsteMes >= 30)
    resultados["Primer paso"] = (if (ctx.series.isNotEmpty()) 1f else 0f) to ctx.series.isNotEmpty()
    resultados["Madrugador"] = (if (ctx.series.any { horaLocal(it.timestamp) < 7 }) 1f else 0f) to ctx.series.any { horaLocal(it.timestamp) < 7 }
    resultados["Búho nocturno"] = (if (ctx.series.any { horaLocal(it.timestamp) >= 22 }) 1f else 0f) to ctx.series.any { horaLocal(it.timestamp) >= 22 }
    resultados["Guerrero de fin de semana"] = (if (finDeSemanaCompleto) 1f else 0f) to finDeSemanaCompleto
    resultados["Doble turno"] = (if (dosVecesElMismoDia) 1f else 0f) to dosVecesElMismoDia
    resultados["Ave fénix"] = (if (pausaLargaYVolvio) 1f else 0f) to pausaLargaYVolvio
    val entrenoUnFeriado = ctx.series.any { esFeriadoArgentino(it.timestamp) } || ctx.marcas.any { esFeriadoArgentino(it.timestamp) }
    resultados["Sin excusas"] = (if (entrenoUnFeriado) 1f else 0f) to entrenoUnFeriado

    val verificadas = ctx.marcas.count { it.verificado }
    resultados["Cazador de PRs"] = (verificadas / 5f).coerceIn(0f, 1f) to (verificadas >= 5)
    val mejorMes = mejorMesKg(ctx.marcas, ctx.series, ctx.pesoCorporalKg)
    resultados["Levantador de elefantes"] = (mejorMes / 6000f).coerceIn(0f, 1f) to (mejorMes >= 6000f)
    val sentadilla = vigente("Sentadilla")?.pesoKg ?: 0f
    resultados["Club de los 100kg"] = (sentadilla / 100f).coerceIn(0f, 1f) to (sentadilla >= 100f)
    val pressBanca = vigente("Press banca")?.pesoKg ?: 0f
    resultados["Club de los 120kg"] = (pressBanca / 120f).coerceIn(0f, 1f) to (pressBanca >= 120f)
    val pesoMuerto = vigente("Peso muerto")?.pesoKg ?: 0f
    resultados["Club de los 150kg"] = (pesoMuerto / 150f).coerceIn(0f, 1f) to (pesoMuerto >= 150f)
    val repsDominadas = vigente("Dominadas")?.reps ?: 0
    resultados["Dominador"] = (repsDominadas / 10f).coerceIn(0f, 1f) to (repsDominadas >= 10)
    val repsFlexiones = vigente("Flexiones")?.reps ?: 0
    resultados["Máquina de flexiones"] = (repsFlexiones / 50f).coerceIn(0f, 1f) to (repsFlexiones >= 50)
    resultados["Verificado"] = (if (verificadas > 0) 1f else 0f) to (verificadas > 0)
    val ultimasDiez = ctx.marcas.sortedByDescending { it.timestamp }.take(10)
    resultados["Sin trampas"] = (ultimasDiez.count { it.verificado } / 10f).coerceIn(0f, 1f) to
        (ultimasDiez.size == 10 && ultimasDiez.all { it.verificado })
    resultados["Calculadora en mano"] = (ctx.marcas.size / 10f).coerceIn(0f, 1f) to (ctx.marcas.size >= 10)

    resultados["Bíceps de acero"] = (if (alMenos(ZonaMuscular.BICEPS, RangoMuscular.HEROE)) 1f else 0f) to alMenos(ZonaMuscular.BICEPS, RangoMuscular.HEROE)
    resultados["Piernas de Titán"] = (if (alMenos(ZonaMuscular.CUADRICEPS, RangoMuscular.TITAN)) 1f else 0f) to alMenos(ZonaMuscular.CUADRICEPS, RangoMuscular.TITAN)
    resultados["Espalda de Coloso"] = (if (alMenos(ZonaMuscular.DORSALES, RangoMuscular.COLOSO)) 1f else 0f) to alMenos(ZonaMuscular.DORSALES, RangoMuscular.COLOSO)
    val pechoOlimpico = alMenos(ZonaMuscular.PECHO_SUPERIOR, RangoMuscular.OLIMPICO) && alMenos(ZonaMuscular.PECHO_INFERIOR, RangoMuscular.OLIMPICO)
    resultados["Pecho Olímpico"] = (if (pechoOlimpico) 1f else 0f) to pechoOlimpico
    val zonasHoplitaOMas = ZonaMuscular.entries.count { alMenos(it, RangoMuscular.HOPLITA) }
    resultados["Cuerpo equilibrado"] = (zonasHoplitaOMas / ZonaMuscular.entries.size.toFloat()) to (zonasHoplitaOMas == ZonaMuscular.entries.size)

    resultados["Rey del ranking"] = (if (posicion != null && posicion <= 3) 1f else 0f) to (posicion != null && posicion <= 3)
    resultados["Corona de laurel"] = (if (posicion == 1) 1f else 0f) to (posicion == 1)

    resultados["Graduado"] = (if (ctx.onboardingCompleto) 1f else 0f) to ctx.onboardingCompleto

    resultados["Cartógrafo"] = (if (ctx.vioPlano) 1f else 0f) to ctx.vioPlano
    resultados["Ojo en el progreso"] = (ctx.vistasBodygraph / 20f).coerceIn(0f, 1f) to (ctx.vistasBodygraph >= 20)
    resultados["Explorador"] = (ctx.seccionesArenaVisitadas / 6f).coerceIn(0f, 1f) to (ctx.seccionesArenaVisitadas >= 6)
    resultados["Cambio de look"] = (if (ctx.objetivosDistintosProbados >= 2) 1f else 0f) to (ctx.objetivosDistintosProbados >= 2)
    resultados["Puntualidad"] = (ctx.ingresosQr / 20f).coerceIn(0f, 1f) to (ctx.ingresosQr >= 20)
    resultados["Biométrico"] = (ctx.ingresosBiometrico / 10f).coerceIn(0f, 1f) to (ctx.ingresosBiometrico >= 10)
    resultados["Casillero propio"] = (if (ctx.tieneLockerReservado) 1f else 0f) to ctx.tieneLockerReservado
    resultados["Plato consciente"] = (if (ctx.tienePerfilNutricional) 1f else 0f) to ctx.tienePerfilNutricional

    // Meses aproximados (30 días) desde que un empleado asignó la
    // membresía — no hay forma de saber si "pagó cada mes", solo desde
    // cuándo está asignada.
    val mesesDeMembresia = ctx.membresiaFechaInicioMs
        ?.let { (System.currentTimeMillis() - it) / (30L * 86_400_000L) } ?: 0L
    resultados["Cliente fiel"] = (mesesDeMembresia / 6f).coerceIn(0f, 1f) to (mesesDeMembresia >= 6)

    resultados["Sibarita"] = (ctx.platosDistintosProbados / 10f).coerceIn(0f, 1f) to (ctx.platosDistintosProbados >= 10)
    val rachaAgua = rachaMasLarga(ctx.registrosAgua.map(::diaEpoch).toSet())
    resultados["Hidratado"] = (rachaAgua / 7f).coerceIn(0f, 1f) to (rachaAgua >= 7)

    // Meta cumplida (Fuerza): el 1RM estimado del ejercicio con más
    // historia mejoró al menos 10% desde tu primera marca de ese
    // ejercicio hasta la más reciente — un objetivo de fuerza real,
    // aunque no exactamente el que el socio haya tipeado como "meta".
    val ejercicioConMasHistoria = ctx.marcas.groupBy { it.ejercicio }.maxByOrNull { it.value.size }?.value
    val mejoraFuerza = ejercicioConMasHistoria?.takeIf { it.size >= 2 }?.let { lista ->
        val ordenadas = lista.sortedBy { it.timestamp }
        val primero = calcular1RM(ordenadas.first().pesoKg, ordenadas.first().reps)
        val ultimo = calcular1RM(ordenadas.last().pesoKg, ordenadas.last().reps)
        if (primero > 0f) (ultimo - primero) / primero else null
    } ?: 0f
    resultados["Meta cumplida"] = (mejoraFuerza / 0.10f).coerceIn(0f, 1f) to (mejoraFuerza >= 0.10f)

    // Meta de hipertrofia: sin ninguna medición de masa muscular en la app,
    // se usa el volumen entrenado (kg movidos) como proxy real — entrenar
    // para hipertrofia es, en la práctica, sostener/aumentar el volumen —
    // en vez de inventar un número de "masa muscular" que no se mide.
    val mapaMeses = mapaKgPorMes(ctx.marcas, ctx.series, ctx.pesoCorporalKg)
    val hoyCal = java.util.Calendar.getInstance()
    val mesAnteriorCal = java.util.Calendar.getInstance().apply { add(java.util.Calendar.MONTH, -1) }
    val kgEsteMes = mapaMeses[hoyCal.get(java.util.Calendar.YEAR) to hoyCal.get(java.util.Calendar.MONTH)] ?: 0f
    val kgMesAnterior = mapaMeses[mesAnteriorCal.get(java.util.Calendar.YEAR) to mesAnteriorCal.get(java.util.Calendar.MONTH)] ?: 0f
    val hipertrofiaEnProgreso = kgMesAnterior > 0f && kgEsteMes > kgMesAnterior
    resultados["Meta de hipertrofia"] = (if (hipertrofiaEnProgreso) 1f else 0f) to hipertrofiaEnProgreso

    // Salud ante todo: sin objetivo de salud medible (no hay presión,
    // % grasa, etc.), se usa la constancia real de ir al gimnasio este
    // mes como proxy — venir seguido es, después de todo, el hábito de
    // salud que esta app sí puede ver.
    val visitasEsteMesParaSalud = visitasEnElMesActual(ctx.ingresos)
    resultados["Salud ante todo"] = (visitasEsteMesParaSalud / 12f).coerceIn(0f, 1f) to (visitasEsteMesParaSalud >= 12)

    resultados["Antes y después"] = (if (ctx.tieneFotoDeProgreso) 1f else 0f) to ctx.tieneFotoDeProgreso

    resultados["Mentor"] = (if (ctx.tieneCompanero) 1f else 0f) to ctx.tieneCompanero
    resultados["Espíritu de equipo"] = (ctx.diasEntrenadosConCompaneros / 5f).coerceIn(0f, 1f) to (ctx.diasEntrenadosConCompaneros >= 5)

    resultados["El ojo de Atenea"] = (diasMadrugonExtremo / 5f).coerceIn(0f, 1f) to (diasMadrugonExtremo >= 5)
    resultados["Ascensión completa"] = (ZonaMuscular.entries.count { alMenos(it, RangoMuscular.DIOS) } / ZonaMuscular.entries.size.toFloat()) to
        (ZonaMuscular.entries.all { alMenos(it, RangoMuscular.DIOS) })
    resultados["Corazón de Esparta"] = (if (diasCorazonEsparta) 1f else 0f) to diasCorazonEsparta

    // Coleccionista/Casi leyenda dependen del resto ya calculado, así que
    // se agregan al final contando cuántos quedaron desbloqueados arriba.
    val desbloqueadosHastaAhora = LOGROS.count { resultados[it.nombre]?.second == true }
    resultados["Coleccionista"] = (desbloqueadosHastaAhora / 25f).coerceIn(0f, 1f) to (desbloqueadosHastaAhora >= 25)
    resultados["Casi leyenda"] = (desbloqueadosHastaAhora / 40f).coerceIn(0f, 1f) to (desbloqueadosHastaAhora >= 40)

    return LOGROS.map { logro ->
        val (progreso, desbloqueado) = resultados[logro.nombre] ?: (logro.progreso to logro.desbloqueado)
        logro.copy(progreso = progreso, desbloqueado = desbloqueado)
    }
}

/* ── Equivalencia visual de carga ── */
data class Equivalencia(val umbralKg: Int, val texto: String, val emoji: String)

private val EQUIVALENCIAS = listOf(
    Equivalencia(80, "un auto compacto", "🚗"),
    Equivalencia(150, "un piano de cola", "🎹"),
    Equivalencia(300, "una vaca adulta", "🐄"),
    Equivalencia(1000, "una camioneta 4x4", "🚙"),
    Equivalencia(3000, "un elefante africano", "🐘"),
    Equivalencia(Int.MAX_VALUE, "una ballena beluga", "🐳")
)

private fun esDeEsteMes(timestampMs: Long): Boolean {
    val ahora = java.util.Calendar.getInstance()
    val cal = java.util.Calendar.getInstance().apply { timeInMillis = timestampMs }
    return cal.get(java.util.Calendar.MONTH) == ahora.get(java.util.Calendar.MONTH) &&
        cal.get(java.util.Calendar.YEAR) == ahora.get(java.util.Calendar.YEAR)
}

/** Kg movidos en el mes calendario actual, para la tarjeta de equivalencia
 *  de Inicio: suma peso×repeticiones de CADA marca de la Calculadora Y
 *  CADA serie de rutina registrada este mes (no solo la vigente por
 *  ejercicio, como el ranking — acá interesa el volumen real entrenado, no
 *  un PR puntual). El timestamp de cada una siempre fue real (epoch ms);
 *  lo que faltaba era filtrar por mes en vez de mostrar un 0 fijo. */
fun kgMovidosEsteMes(marcas: List<MarcaPersonal>, series: List<SerieEntrenamiento>, pesoCorporalKg: Float): Int {
    val deMarcas = marcas
        .filter { esDeEsteMes(it.timestamp) }
        .sumOf { (cargaTotal(it, pesoCorporalKg) * it.reps).toDouble() }
    val deSeries = series
        .filter { esDeEsteMes(it.timestamp) }
        .sumOf { ((if (it.esPesoCorporal) pesoCorporalKg + it.pesoKg else it.pesoKg) * it.reps).toDouble() }
    return (deMarcas + deSeries).toInt()
}

fun equivalenciaDeCarga(kg: Int): Equivalencia = EQUIVALENCIAS.first { kg <= it.umbralKg }
fun cantidadEquivalencia(kg: Int, umbral: Int): Int = (kg / umbral.toFloat()).let { if (it < 1) 1 else it.toInt() }

/* ── Ghost Mode: hoy vs. tu sesión anterior de este mismo ejercicio ── */

/** Una serie ya registrada en la sesión de HOY (en memoria, ver
 *  EntrenarScreen) — antes de guardarse en Firestore como
 *  [SerieEntrenamiento]. */
data class SerieHecha(val pesoKg: Float, val reps: Int)

private fun esMismoDia(timestampMs: Long, referencia: java.util.Calendar): Boolean {
    val cal = java.util.Calendar.getInstance().apply { timeInMillis = timestampMs }
    return cal.get(java.util.Calendar.DAY_OF_YEAR) == referencia.get(java.util.Calendar.DAY_OF_YEAR) &&
        cal.get(java.util.Calendar.YEAR) == referencia.get(java.util.Calendar.YEAR)
}

/** Comparación real de Ghost Mode: la mejor serie (por 1RM estimado) de
 *  HOY contra la mejor serie de la última sesión anterior en que se
 *  entrenó este mismo ejercicio (se excluye lo ya registrado hoy, así una
 *  serie de hoy no se compara contra sí misma). */
data class ComparacionGhostMode(
    val ejercicio: String,
    val pesoAnterior: Float,
    val repsAnterior: Int,
    val pesoHoy: Float,
    val repsHoy: Int
) {
    val supera: Boolean get() = calcular1RM(pesoHoy, repsHoy) > calcular1RM(pesoAnterior, repsAnterior)
    val diferenciaKg: Float get() = calcular1RM(pesoHoy, repsHoy) - calcular1RM(pesoAnterior, repsAnterior)
}

/** `null` si hoy todavía no se registró ninguna serie de este ejercicio, o
 *  si no hay ninguna sesión anterior (de otro día) para comparar. */
fun ghostModeDeEjercicio(ejercicio: String, seriesHoy: List<SerieHecha>, historial: List<SerieEntrenamiento>): ComparacionGhostMode? {
    if (seriesHoy.isEmpty()) return null
    val mejorHoy = seriesHoy.maxByOrNull { calcular1RM(it.pesoKg, it.reps) } ?: return null
    val hoyCal = java.util.Calendar.getInstance()
    val mejorAnterior = historial
        .filter { it.ejercicio == ejercicio && !esMismoDia(it.timestamp, hoyCal) }
        .maxByOrNull { calcular1RM(it.pesoKg, it.reps) } ?: return null
    return ComparacionGhostMode(
        ejercicio = ejercicio,
        pesoAnterior = mejorAnterior.pesoKg, repsAnterior = mejorAnterior.reps,
        pesoHoy = mejorHoy.pesoKg, repsHoy = mejorHoy.reps
    )
}

/* ── Objetivo de la Arena ── */
enum class ObjetivoCompetencia(val etiqueta: String, val emoji: String) {
    FUERZA("Fuerza", "🏋️"),
    HIPERTROFIA("Hipertrofia", "💪"),
    SALUD("Salud general", "❤️")
}

private const val PREFS_ARENA = "olimpos_prefs"
private const val KEY_OBJETIVO = "objetivo_arena"
private const val KEY_OBJETIVOS_HISTORICOS = "objetivos_historicos"

/** null = todavía no eligió objetivo: dispara la pantalla de selección la primera vez que entra a Arena. */
fun leerObjetivoArena(context: Context): ObjetivoCompetencia? {
    val guardado = context.getSharedPreferences(PREFS_ARENA, Context.MODE_PRIVATE).getString(KEY_OBJETIVO, null)
    return ObjetivoCompetencia.entries.firstOrNull { it.name == guardado }
}

fun guardarObjetivoArena(context: Context, objetivo: ObjetivoCompetencia) {
    val prefs = context.getSharedPreferences(PREFS_ARENA, Context.MODE_PRIVATE)
    val historicos = (prefs.getStringSet(KEY_OBJETIVOS_HISTORICOS, emptySet()) ?: emptySet()) + objetivo.name
    prefs.edit()
        .putString(KEY_OBJETIVO, objetivo.name)
        // Set nuevo (no el mismo mutado) — StringSet de SharedPreferences no
        // debe modificarse in-place, hay bugs documentados de Android si se
        // reusa la misma instancia.
        .putStringSet(KEY_OBJETIVOS_HISTORICOS, historicos)
        .apply()
}

/** Para el logro "Cambio de look": distintos objetivos que probó alguna vez
 *  (no solo el primero que eligió en el onboarding de la Arena). Vive en
 *  SharedPreferences igual que el objetivo actual — es un dato del
 *  dispositivo, no necesita ser cross-device para un logro. */
fun objetivosProbadosAlgunaVez(context: Context): Set<String> =
    context.getSharedPreferences(PREFS_ARENA, Context.MODE_PRIVATE).getStringSet(KEY_OBJETIVOS_HISTORICOS, emptySet()) ?: emptySet()

private const val KEY_NOTIFICACIONES_LOGROS = "notificaciones_logros_activas"

/** Si el toast + sonido de "logro desbloqueado" está activado — se puede
 *  apagar desde Configuración para quien lo encuentre molesto. Activado por
 *  default. */
fun leerNotificacionesLogrosActivas(context: Context): Boolean =
    context.getSharedPreferences(PREFS_ARENA, Context.MODE_PRIVATE).getBoolean(KEY_NOTIFICACIONES_LOGROS, true)

fun guardarNotificacionesLogrosActivas(context: Context, activas: Boolean) {
    context.getSharedPreferences(PREFS_ARENA, Context.MODE_PRIVATE).edit()
        .putBoolean(KEY_NOTIFICACIONES_LOGROS, activas)
        .apply()
}
