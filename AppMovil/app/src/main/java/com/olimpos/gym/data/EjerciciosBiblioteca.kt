package com.olimpos.gym.data

/* ═══════════════════════════════════════════════════════
   BIBLIOTECA DE EJERCICIOS — galería de ejercicios cargada
   por el Dueño/Entrenador desde el sistema de empleados.
   No hay foto propia: cada ejercicio marca las zonas
   musculares que trabaja sobre el mismo cuerpo compartido
   del Bodygraph ([CuerpoMuscular]) — mismo patrón que las
   dietas para la sincronización (Firestore), con un catálogo
   de ejemplo como respaldo si todavía no hay nada publicado.
   ═══════════════════════════════════════════════════════ */

/** Una zona muscular trabajada por el ejercicio: qué zona es, cómo se
 *  fortalece con este ejercicio y etiquetas cortas — igual que un punto
 *  de dieta, pero anclado a una zona fija en vez de una posición libre. */
data class PuntoMuscular(
    val id: String,
    val zona: ZonaMuscular,
    val nombre: String,
    val descripcion: String,
    val tags: List<String>
)

/** [tags]: hasta 3 palabras cortas para la tarjeta y el buscador de la
 *  Galería. [puntos]: las zonas musculares trabajadas, elegidas sobre el
 *  cuerpo compartido en el editor de empleados. */
data class EjercicioCatalogo(
    val id: String,
    val nombre: String,
    val descripcion: String,
    val tags: List<String> = emptyList(),
    val puntos: List<PuntoMuscular> = emptyList()
)

val EJERCICIOS_CATALOGO_EJEMPLO = listOf(
    EjercicioCatalogo(
        id = "press_banca", nombre = "Press de banca",
        descripcion = "Ejercicio de empuje horizontal con barra, base del entrenamiento de pecho. " +
            "Escápulas retraídas y fijas al banco, pies firmes en el piso.",
        tags = listOf("Empuje", "Pecho", "Fuerza"),
        puntos = listOf(
            PuntoMuscular("p1", ZonaMuscular.PECHO_INFERIOR, "Pecho", "Empuja la barra desde el pecho: el motor principal del movimiento.", listOf("Empuje", "Fuerza")),
            PuntoMuscular("p2", ZonaMuscular.DELTOIDES_ANTERIOR, "Hombros", "Estabilizan la barra y ayudan en el bloqueo final del movimiento.", listOf("Estabilidad")),
            PuntoMuscular("p3", ZonaMuscular.TRICEPS, "Tríceps", "Terminan de extender el codo en la fase final del empuje.", listOf("Empuje"))
        )
    ),
    EjercicioCatalogo(
        id = "remo_barra", nombre = "Remo con barra",
        descripcion = "Ejercicio de tracción horizontal para espalda media y baja. " +
            "Espalda recta con leve inclinación de cadera, sin usar impulso lumbar.",
        tags = listOf("Tracción", "Espalda"),
        puntos = listOf(
            PuntoMuscular("p1", ZonaMuscular.DORSALES, "Dorsales", "Tira la barra hacia el abdomen apretando los omóplatos.", listOf("Tracción")),
            PuntoMuscular("p2", ZonaMuscular.BICEPS, "Bíceps", "Ayudan a sostener y traccionar la barra durante todo el recorrido.", listOf("Tracción"))
        )
    ),
    EjercicioCatalogo(
        id = "sentadilla", nombre = "Sentadilla",
        descripcion = "El ejercicio de tren inferior por excelencia: fuerza y masa muscular en piernas y core. " +
            "Pecho arriba, rodillas alineadas con la punta del pie.",
        tags = listOf("Piernas", "Fuerza", "Core"),
        puntos = listOf(
            PuntoMuscular("p1", ZonaMuscular.CUADRICEPS, "Cuádriceps", "Hacen la mayor parte del trabajo al bajar y subir.", listOf("Fuerza")),
            PuntoMuscular("p2", ZonaMuscular.GLUTEOS, "Glúteos", "Empujan con fuerza en la fase de subida.", listOf("Fuerza")),
            PuntoMuscular("p3", ZonaMuscular.ABDOMINALES, "Abdominales", "Se mantienen apretados durante todo el movimiento para proteger la espalda baja.", listOf("Estabilidad"))
        )
    )
)
