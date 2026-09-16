package com.olimpos.gym.data

/* ═══════════════════════════════════════════════════════
   SOCIO — membresías, pagos, accesos, lockers, máquinas,
   nutrición y progreso. Datos de ejemplo (frontend puro).
   ═══════════════════════════════════════════════════════ */

/* ── Membresías y pagos ── */
data class PlanMembresia(
    val nombre: String,
    val precio: String,
    val beneficios: List<String>,
    val destacado: Boolean = false
)

val PLANES_MEMBRESIA = listOf(
    PlanMembresia("Bronce", "$18.000/mes", listOf("Acceso a sala de pesas", "Clases grupales limitadas", "1 evaluación física/año")),
    PlanMembresia("Oro", "$28.000/mes", listOf("Acceso total al club", "Clases grupales ilimitadas", "Spa 2x/mes", "Rutina personalizada"), destacado = true),
    PlanMembresia("Platino", "$42.000/mes", listOf("Todo lo de Oro", "Spa ilimitado", "1 sesión c/ entrenador personal/sem.", "Plan nutricional incluido"))
)

data class MetodoPago(val tipo: String, val detalle: String, val emoji: String)

// Sin métodos de pago de ejemplo: un socio nuevo todavía no cargó
// ninguno — "+ Agregar método de pago" en Membresía es el camino real.
val METODOS_PAGO = emptyList<MetodoPago>()

data class PagoHistorial(val periodo: String, val monto: String, val estado: String)

// Sin pagos de ejemplo: recién se ve algo acá cuando el socio paga una
// cuota de verdad.
val HISTORIAL_PAGOS = emptyList<PagoHistorial>()

/* ── Lockers ── */
enum class EstadoLocker { LIBRE, OCUPADO, RESERVADO_POR_MI }

data class Locker(val numero: Int, val zona: String, var estado: EstadoLocker)

// El número y la zona de cada locker es el layout físico real del
// vestidor (fijo, no cambia) — el `estado` acá es solo un valor de
// arranque sin usar: LockersScreen lo recalcula siempre a partir de las
// reservas reales en Firestore (ver LockersRepository.kt), así que ningún
// locker aparece "ocupado" sin que un socio real lo haya reservado.
val LOCKERS_EJEMPLO = listOf(
    Locker(12, "Vestidor Hombres", EstadoLocker.LIBRE),
    Locker(1, "Vestidor Hombres", EstadoLocker.LIBRE),
    Locker(2, "Vestidor Hombres", EstadoLocker.LIBRE),
    Locker(3, "Vestidor Hombres", EstadoLocker.LIBRE),
    Locker(4, "Vestidor Hombres", EstadoLocker.LIBRE),
    Locker(5, "Vestidor Hombres", EstadoLocker.LIBRE),
    Locker(6, "Vestidor Hombres", EstadoLocker.LIBRE)
)

/* ── Máquinas: ubicación y disponibilidad (vinculado al Plano) ── */
data class Maquina(val nombre: String, val zona: String, val disponible: Boolean)

val MAQUINAS_EJEMPLO = listOf(
    Maquina("Press de banca #2", "Sala de Pesas · Piso 2", true),
    Maquina("Sentadilla Smith", "Sala de Pesas · Piso 2", false),
    Maquina("Remo polea baja", "Sala de Pesas · Piso 2", true),
    Maquina("Prensa de piernas", "Sala de Pesas · Piso 2", true)
)

/* ── Ejercicio: detalle técnico (para la pantalla de detalle) ── */
data class DetalleEjercicio(
    val nombre: String,
    val musculos: List<String>,
    val tecnica: String,
    val series: Int,
    val reps: String,
    val descansoSeg: Int,
    val alternativa: String
)

val DETALLES_EJERCICIOS = mapOf(
    "Press de banca" to DetalleEjercicio(
        "Press de banca", listOf("Pectoral", "Tríceps", "Deltoides anterior"),
        "Escápulas retraídas y fijas al banco, pies firmes en el piso. Bajá la barra controlada hasta rozar el pecho y empujá en línea recta hacia arriba sin rebotar.",
        4, "8-10", 90, "Press con mancuernas"
    ),
    "Remo con barra" to DetalleEjercicio(
        "Remo con barra", listOf("Dorsal ancho", "Romboides", "Bíceps"),
        "Espalda recta con leve inclinación de cadera. Tirá la barra hacia el abdomen apretando los omóplatos, sin usar impulso lumbar.",
        4, "10-12", 75, "Remo en polea baja"
    ),
    "Press militar" to DetalleEjercicio(
        "Press militar", listOf("Deltoides", "Tríceps", "Core"),
        "Core apretado, evitá arquear la zona lumbar. Empujá la barra en línea recta por delante de la cara hasta extender los codos.",
        3, "8-10", 90, "Press con mancuernas sentado"
    ),
    "Dominadas asistidas" to DetalleEjercicio(
        "Dominadas asistidas", listOf("Dorsal ancho", "Bíceps", "Antebrazo"),
        "Agarre prono un poco más ancho que los hombros. Subí hasta que el mentón pase la barra, bajá controlado sin balancearte.",
        3, "6-8", 90, "Jalón al pecho en polea"
    ),
    "Curl de bíceps" to DetalleEjercicio(
        "Curl de bíceps", listOf("Bíceps braquial", "Antebrazo"),
        "Codos pegados al torso durante todo el recorrido. Subí controlado, apretá arriba y bajá lento sin balancear el cuerpo.",
        3, "10-12", 60, "Curl con mancuernas alternado"
    ),
    "Fondos en paralelas" to DetalleEjercicio(
        "Fondos en paralelas", listOf("Tríceps", "Pectoral inferior", "Deltoides anterior"),
        "Torso levemente inclinado adelante para más pecho, o recto para más tríceps. Bajá hasta 90° en el codo y empujá sin bloquear de golpe.",
        3, "8-10", 90, "Press francés con barra Z"
    )
)

/* ── Bodygraph: zonas musculares, a nivel de detalle real (mismo dataset
   anatómico que dibuja CuerpoMuscular — cada zona es un grupo que ya viene
   separado en los paths de origen, no una agrupación inventada). ── */
enum class ZonaMuscular(val etiqueta: String, val emoji: String) {
    // Emojis elegidos para que cada zona se distinga de sus vecinas — no
    // existe un emoji real para "trapecio" o "dorsal", así que se usan
    // metáforas visuales reconocibles en vez de repetir el mismo ícono
    // genérico en zonas que antes eran indistinguibles entre sí.
    PECHO_SUPERIOR("Parte superior del pecho", "🎽"),
    PECHO_INFERIOR("Parte inferior del pecho", "🎽"),
    DORSALES("Dorsales", "🦅"),
    TRAPECIO("Trapecios", "⛰️"),
    LUMBARES("Parte inferior de la espalda", "🪨"),
    DELTOIDES_ANTERIOR("Deltoides anterior", "⬆️"),
    DELTOIDES_MEDIO("Deltoides medio", "↔️"),
    DELTOIDES_POSTERIOR("Deltoides posterior", "↩️"),
    BICEPS("Bíceps", "💪"),
    TRICEPS("Tríceps", "🥊"),
    ANTEBRAZOS("Antebrazos", "✊"),
    ABDOMINALES("Abdominales", "🧱"),
    OBLICUOS("Oblicuos", "🌀"),
    ABDUCTORES("Abductores", "➡️"),
    ADUCTORES("Aductores", "⬅️"),
    PANTORRILLAS("Pantorrillas", "🦶"),
    GLUTEOS("Glúteos", "🍑"),
    ISQUIOTIBIALES("Isquiotibiales", "🦿"),
    CUADRICEPS("Cuádriceps", "🦵")
}

/** Agrupación amplia de zonas para la lista desplegable del Bodygraph (un
 *  renglón "Piernas 3/6" que al abrirse muestra Abductores/Aductores/
 *  Pantorrillas/Glúteos/Isquiotibiales/Cuádriceps por separado) — puramente
 *  de presentación, el dato real sigue siendo [ZonaMuscular] a nivel de
 *  detalle. "Dorsales" cubre la parte superior de la espalda: el dataset
 *  anatómico no distingue ahí una región más además de dorsales/trapecio/
 *  lumbares. */
enum class GrupoMuscular(val etiqueta: String, val emoji: String, val zonas: List<ZonaMuscular>) {
    PECHO("Pecho", "🎽", listOf(ZonaMuscular.PECHO_SUPERIOR, ZonaMuscular.PECHO_INFERIOR)),
    ESPALDA("Espalda", "🦅", listOf(ZonaMuscular.DORSALES, ZonaMuscular.LUMBARES, ZonaMuscular.TRAPECIO)),
    HOMBROS("Hombros", "🛡️", listOf(ZonaMuscular.DELTOIDES_ANTERIOR, ZonaMuscular.DELTOIDES_MEDIO, ZonaMuscular.DELTOIDES_POSTERIOR)),
    BRAZOS("Brazos", "💪", listOf(ZonaMuscular.BICEPS, ZonaMuscular.TRICEPS, ZonaMuscular.ANTEBRAZOS)),
    ABDOMINALES("Abdominales", "🧱", listOf(ZonaMuscular.ABDOMINALES, ZonaMuscular.OBLICUOS)),
    PIERNAS("Piernas", "🦵", listOf(ZonaMuscular.ABDUCTORES, ZonaMuscular.ADUCTORES, ZonaMuscular.PANTORRILLAS, ZonaMuscular.GLUTEOS, ZonaMuscular.ISQUIOTIBIALES, ZonaMuscular.CUADRICEPS))
}

/* ── Contacto con entrenador y sesiones personalizadas ── */
data class Entrenador(val nombre: String, val especialidad: String, val disponibilidad: String)

val ENTRENADORES = listOf(
    Entrenador("Martina Gómez", "Spinning · Funcional", "Lun a Vie 08:00–16:00"),
    Entrenador("Facundo López", "Fuerza · Powerlifting", "Mar a Sáb 14:00–22:00")
)

data class SesionEntrenador(val entrenador: String, val fecha: String, val hora: String, var estado: String)

// Sin sesión de ejemplo: recién aparece algo acá cuando el socio reserva
// una sesión de verdad (la pantalla ya tiene su propio estado vacío).
val SESIONES_EJEMPLO = mutableListOf<SesionEntrenador>()

/* ── Nutrición ── */
val PREFERENCIAS_ALIMENTARIAS = listOf("Vegetariano", "Vegano", "Sin gluten", "Sin lactosa", "Keto", "Alto en proteína")
val ALIMENTOS_EXCLUIBLES = listOf("Maní", "Mariscos", "Cebolla", "Picante", "Lácteos", "Huevo")

data class RecomendacionNutricional(val titulo: String, val detalle: String, val emoji: String)

val RECOMENDACIONES_NUTRICIONALES = listOf(
    RecomendacionNutricional("Subí la proteína en el desayuno", "Sumá 1 huevo extra o un yogur griego para llegar a tu objetivo diario.", "🥚"),
    RecomendacionNutricional("Hidratación post-entreno", "Tomá al menos 500ml de agua en la hora siguiente a entrenar fuerza.", "💧"),
    RecomendacionNutricional("Carbohidratos antes de entrenar", "Un plátano o avena 45 min antes mejora tu rendimiento en sentadilla.", "🍌")
)

data class HistorialNutricional(val fecha: String, val resumen: String)

// Sin historial de ejemplo: todavía no existe un seguimiento diario real
// del cumplimiento del plan de dieta.
val HISTORIAL_ALIMENTARIO = emptyList<HistorialNutricional>()

/* ── Progreso: historial de entrenamientos y evolución ── */
data class PuntoEvolucion(val etiqueta: String, val valor: Float)

// La evolución de fuerza ya se calcula de verdad a partir de las marcas
// cargadas (ver evolucionDeFuerza en GamificacionData.kt, usado desde
// ProgresoScreen). La de peso corporal sigue vacía a propósito: el peso
// solo se carga una vez en el onboarding y todavía no existe una pantalla
// para actualizarlo después, así que no hay más de un punto que graficar.
val EVOLUCION_PESO = emptyList<PuntoEvolucion>()

data class SesionHistorial(val fecha: String, val tipo: String, val duracion: String, val volumenKg: Int)

// Sin sesiones de ejemplo: todavía no existe un registro real de
// entrenamientos pasados (el seguimiento de rutina de hoy vive solo en
// memoria durante la sesión, ver EntrenarScreen.kt).
val HISTORIAL_ENTRENAMIENTOS = emptyList<SesionHistorial>()

/* ── Onboarding: días y franjas horarias ── */
val DIAS_SEMANA = listOf("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
val FRANJAS_HORARIAS = listOf("Mañana (6-12h)", "Tarde (12-18h)", "Noche (18-23h)")
val NIVELES_EXPERIENCIA = listOf("Principiante", "Intermedio", "Avanzado")
