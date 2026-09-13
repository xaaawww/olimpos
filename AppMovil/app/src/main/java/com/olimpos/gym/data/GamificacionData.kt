package com.olimpos.gym.data

import android.content.Context

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

/** Identidad del socio actual: la app todavía no tiene login real contra un
 *  backend (ver [LoginScreen], puramente cosmético), así que — igual que el
 *  resto de los datos de ejemplo de este archivo (ranking, pagos) — se usa
 *  un socio fijo. Es el mismo id que debe usarse al guardar/leer "marcas"
 *  en Firestore para que el sistema de empleados pueda verificarlas. */
const val SOCIO_ACTUAL_ID = "alex_rodriguez"
const val SOCIO_ACTUAL_NOMBRE = "Alex Rodríguez"

val MIS_MARCAS = mutableListOf(
    MarcaPersonal(id = "m2", ejercicio = "Press banca", pesoKg = 82f, reps = 2, fecha = "20/08", timestamp = 1L, verificado = true),
    MarcaPersonal(id = "m1", ejercicio = "Sentadilla", pesoKg = 110f, reps = 3, fecha = "28/08", timestamp = 2L, verificado = true),
    MarcaPersonal(id = "m5", ejercicio = "Flexiones", pesoKg = 0f, reps = 32, fecha = "30/08", timestamp = 3L, verificado = false),
    MarcaPersonal(id = "m4", ejercicio = "Dominadas", pesoKg = 15f, reps = 6, fecha = "02/09", timestamp = 4L, verificado = true),
    MarcaPersonal(id = "m3", ejercicio = "Peso muerto", pesoKg = 140f, reps = 1, fecha = "05/09", timestamp = 5L, verificado = false),
    MarcaPersonal(id = "m6", ejercicio = "Elevaciones laterales", pesoKg = 12f, reps = 12, fecha = "06/09", timestamp = 6L, verificado = true),
    MarcaPersonal(id = "m7", ejercicio = "Pájaros", pesoKg = 8f, reps = 15, fecha = "07/09", timestamp = 7L, verificado = false),
    MarcaPersonal(id = "m8", ejercicio = "Elevación de talones", pesoKg = 60f, reps = 15, fecha = "08/09", timestamp = 8L, verificado = true)
)

/** Estimación de 1RM con fórmula de Epley: peso × (1 + reps/30) */
fun calcular1RM(pesoKg: Float, reps: Int): Float = pesoKg * (1f + reps / 30f)

/* ── Rangos musculares del Bodygraph ──
   9 rangos temáticos (mitología griega, a tono con "OlimpΩs"), cada uno con
   3 niveles salvo el último (Dios), que es el techo del sistema. */
enum class RangoMuscular(val etiqueta: String) {
    MORTAL("Mortal"),
    ESPARTANO("Espartano"),
    HOPLITA("Hoplita"),
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

private fun cargaTotal(marca: MarcaPersonal, pesoCorporalKg: Float): Float =
    if (marca.ejercicio in EJERCICIOS_PESO_CORPORAL) pesoCorporalKg + marca.pesoKg else marca.pesoKg

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
 *  1RM se relativiza al peso corporal para que el puntaje sea comparable
 *  entre socios de distinto tamaño. El estado "verificado" del Bodygraph
 *  depende de si esas marcas vigentes ya fueron confirmadas por un
 *  entrenador. */
fun resumenMuscular(marcas: List<MarcaPersonal>, pesoCorporalKg: Float): ResumenMuscular {
    val vigentePorEjercicio = marcas.groupBy { it.ejercicio }
        .mapNotNull { (_, ms) -> ms.maxByOrNull { it.timestamp } }

    val puntajes = mutableMapOf<ZonaMuscular, Float>()
    vigentePorEjercicio.forEach { marca ->
        val relativo = calcular1RM(cargaTotal(marca, pesoCorporalKg), marca.reps) / pesoCorporalKg
        CONTRIBUCION_MUSCULAR[marca.ejercicio]?.forEach { (zona, peso) ->
            puntajes[zona] = (puntajes[zona] ?: 0f) + relativo * peso
        }
    }

    return ResumenMuscular(
        puntajes = puntajes,
        verificado = vigentePorEjercicio.isNotEmpty() && vigentePorEjercicio.all { it.verificado },
        tieneMarcas = vigentePorEjercicio.isNotEmpty()
    )
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

val LOGROS = listOf(
    // ── Constancia y racha ──
    Logro("🔥", "Racha de fuego", "7 días seguidos entrenando", 1f, true),
    Logro("🎯", "Constancia de hierro", "30 días de asistencia en el mes", 0.4f, false),
    Logro("🛡️", "Racha de titanio", "30 días seguidos entrenando sin cortar la racha", 0.23f, false),
    Logro("♾️", "Racha eterna", "100 días seguidos entrenando", 0.07f, false),
    Logro("🐣", "Primer paso", "Completá tu primer entrenamiento", 1f, true),
    Logro("🌅", "Madrugador", "Entrená antes de las 7 de la mañana", 1f, true),
    Logro("🦉", "Búho nocturno", "Entrená después de las 22h", 0.5f, false),
    Logro("🎉", "Sin excusas", "Entrená un feriado", 0.5f, false),
    Logro("🏖️", "Guerrero de fin de semana", "Entrená sábado y domingo la misma semana", 0.5f, false),
    Logro("🔁", "Doble turno", "Entrená dos veces el mismo día", 0f, false),
    Logro("🐦‍🔥", "Ave fénix", "Volvé a entrenar después de 30 días de pausa", 0f, false),
    // ── Fuerza y marcas ──
    Logro("⚡", "Cazador de PRs", "5 marcas personales verificadas", 0.6f, false),
    Logro("🐘", "Levantador de elefantes", "Acumulá 6.000kg movidos en un mes", 0.74f, false),
    Logro("🏋️", "Club de los 100kg", "Sentadilla ≥ 100kg", 1f, true),
    Logro("🛏️", "Club de los 120kg", "Press de banca ≥ 120kg", 0.34f, false),
    Logro("⚙️", "Club de los 150kg", "Peso muerto ≥ 150kg", 0.55f, false),
    Logro("🧗", "Dominador", "10 dominadas seguidas sin soltar la barra", 0.3f, false),
    Logro("🤸", "Máquina de flexiones", "50 flexiones seguidas", 0.4f, false),
    Logro("✅", "Verificado", "Tu primera marca confirmada por un entrenador", 1f, true),
    Logro("🔒", "Sin trampas", "10 marcas verificadas seguidas", 0.2f, false),
    Logro("🧮", "Calculadora en mano", "Usá la Calculadora 10 veces", 0.7f, false),
    // ── Bodygraph y rangos ──
    Logro("💪", "Bíceps de acero", "Bíceps en rango Héroe o superior", 0.5f, false),
    Logro("🦵", "Piernas de Titán", "Cuádriceps en rango Titán o superior", 0.2f, false),
    Logro("🔺", "Espalda de Coloso", "Dorsales en rango Coloso o superior", 0.1f, false),
    Logro("🫀", "Pecho Olímpico", "Pecho en rango Olímpico", 0.15f, false),
    Logro("⚖️", "Cuerpo equilibrado", "Los 14 músculos en rango Hoplita o superior", 0.35f, false),
    Logro("👁️", "Ojo en el progreso", "Revisá tu Bodygraph 20 veces", 0.65f, false),
    // ── Exploración de la app ──
    Logro("🧭", "Explorador", "Visitá las 6 secciones de la Arena", 1f, true),
    Logro("🗺️", "Cartógrafo", "Mirá el Plano del gimnasio", 1f, true),
    Logro("🎚️", "Cambio de look", "Cambiá tu objetivo de la Arena", 1f, true),
    Logro("🏆", "Coleccionista", "Desbloqueá 25 logros", 0.5f, false),
    Logro("👑", "Casi leyenda", "Desbloqueá 40 logros", 0.28f, false),
    // ── Ranking y comunidad ──
    Logro("📈", "Rey del ranking", "Llegá al top 3 en Clasificación", 0.3f, false),
    Logro("🥇", "Corona de laurel", "Llegá al puesto #1 en Clasificación", 0.1f, false),
    Logro("🤝", "Mentor", "Agregá a tu primer compañero de entrenamiento", 0f, false),
    Logro("👥", "Espíritu de equipo", "Entrená junto a un amigo 5 veces", 0.2f, false),
    // ── Nutrición ──
    Logro("🥗", "Plato consciente", "Completá tu perfil nutricional", 1f, true),
    Logro("🍽️", "Sibarita", "Probá 10 platos distintos del catálogo", 0.6f, false),
    Logro("📅", "Nutricionista amateur", "Completá 7 días seguidos tu plan de dieta", 0.43f, false),
    Logro("💧", "Hidratado", "Registrá tu consumo de agua 7 días seguidos", 0.86f, false),
    // ── Objetivos de la Arena ──
    Logro("🎖️", "Meta cumplida", "Alcanzá el objetivo de fuerza que elegiste", 0.5f, false),
    Logro("💪", "Meta de hipertrofia", "Alcanzá tu objetivo de hipertrofia", 0.4f, false),
    Logro("❤️", "Salud ante todo", "Alcanzá tu objetivo de salud general", 0.6f, false),
    // ── Gimnasio físico ──
    Logro("📲", "Puntualidad", "Ingresá al gimnasio con QR 20 veces", 0.8f, false),
    Logro("🖐️", "Biométrico", "Ingresá al gimnasio con huella 10 veces", 0.5f, false),
    Logro("🗄️", "Casillero propio", "Reservá tu primer locker", 1f, true),
    Logro("🔧", "Bien equipado", "Reservá una máquina desde el Plano", 1f, true),
    Logro("🎂", "Cliente fiel", "Cumplí 6 meses de membresía activa", 0.5f, false),
    Logro("📸", "Antes y después", "Subí tu primera foto de progreso", 0f, false),
    Logro("🎓", "Graduado", "Completá el onboarding completo de OlimpΩs", 1f, true),
    // ── Secretos: no aparecen en la grilla hasta desbloquearse ──
    Logro("🦉", "El ojo de Atenea", "Entrená pasada la medianoche 5 veces", 0f, false, secreto = true),
    Logro("🌟", "Ascensión completa", "Los 14 músculos alcanzaron rango Dios", 0f, false, secreto = true),
    Logro("🗿", "Corazón de Esparta", "Cargá una marca en los 5 ejercicios de la Calculadora el mismo día", 0f, false, secreto = true)
)

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

/** Total de ejemplo movido este mes (kg), usado en la tarjeta de equivalencia de Inicio */
const val EQUIVALENCIA_MENSUAL_KG = 16_750

fun equivalenciaDeCarga(kg: Int): Equivalencia = EQUIVALENCIAS.first { kg <= it.umbralKg }
fun cantidadEquivalencia(kg: Int, umbral: Int): Int = (kg / umbral.toFloat()).let { if (it < 1) 1 else it.toInt() }

/* ── Ghost Mode: comparación contra tu última sesión (ahora vive en la
   pantalla de rutina de Entrenar, no en Mis marcas) — el nombre coincide
   con el de RUTINA_HOY para que quede claro que es el mismo ejercicio. */
data class GhostModeResultado(val ejercicio: String, val pesoAnterior: Float, val repsAnterior: Int, val pesoActual: Float, val repsActual: Int)

val GHOST_MODE_EJEMPLO = GhostModeResultado("Press de banca", 80f, 8, 82f, 10)

/* ── Objetivo de la Arena ── */
enum class ObjetivoCompetencia(val etiqueta: String, val emoji: String) {
    FUERZA("Fuerza", "🏋️"),
    HIPERTROFIA("Hipertrofia", "💪"),
    SALUD("Salud general", "❤️")
}

private const val PREFS_ARENA = "olimpos_prefs"
private const val KEY_OBJETIVO = "objetivo_arena"

/** null = todavía no eligió objetivo: dispara la pantalla de selección la primera vez que entra a Arena. */
fun leerObjetivoArena(context: Context): ObjetivoCompetencia? {
    val guardado = context.getSharedPreferences(PREFS_ARENA, Context.MODE_PRIVATE).getString(KEY_OBJETIVO, null)
    return ObjetivoCompetencia.entries.firstOrNull { it.name == guardado }
}

fun guardarObjetivoArena(context: Context, objetivo: ObjetivoCompetencia) {
    context.getSharedPreferences(PREFS_ARENA, Context.MODE_PRIVATE).edit()
        .putString(KEY_OBJETIVO, objetivo.name)
        .apply()
}
