package com.olimpos.gym.data

import com.olimpos.gym.R

/* ═══════════════════════════════════════════════════════
   DIETA — migrado de "Dieta Saludable.html" (mismo sistema
   de rotación e imagen real del plato que la página web,
   adaptado a pantalla de celular)
   ═══════════════════════════════════════════════════════ */

data class Ingrediente(
    val emoji: String,
    val nombre: String,
    val categoria: String,
    val angulo: Float,      // grados sobre el plato
    val radio: Float,       // 0 = centro del plato
    val kcal: String,
    val tags: List<String>,
    val aporte: String,
    val beneficios: List<String>
)

/** [imagen]: Int (drawable local, para los platos de ejemplo), String o
 *  ByteArray (Base64 decodificado, para los publicados desde el editor de
 *  empleados) — Coil admite los tres como "model" sin distinción.
 *  [tags]: hasta 3 palabras cortas que resumen el objetivo de la dieta
 *  (ej. "Definición", "Alta proteína"), se muestran como chips en la
 *  tarjeta del catálogo. [asignada]: true cuando el nutricionista/dueño
 *  la asignó puntualmente a este socio, para separarla del catálogo
 *  general en la pantalla de Dieta. */
data class Plato(
    val id: String,
    val nombre: String,
    val emoji: String,
    val imagen: Any,
    val descripcion: String = "",
    val tags: List<String> = emptyList(),
    val asignada: Boolean = false,
    val items: List<Ingrediente>
)

val PLATOS = listOf(
    Plato(
        id = "atun", nombre = "Atún", emoji = "🐟", imagen = R.drawable.dieta_atun,
        descripcion = "Alto en proteína y omega-3: ideal para definición muscular cuidando el corazón.",
        tags = listOf("Definición", "Alta proteína", "Corazón"),
        items = listOf(
        Ingrediente("🐟", "Atún sellado", "Proteína", 212f, 96f, "144 kcal",
            listOf("29 g proteína", "Omega-3", "Selenio"),
            "Pescado azul magro: proteína de alto valor biológico y ácidos grasos omega-3 que cuidan el corazón y bajan la inflamación.",
            listOf("Construye y repara músculo", "Omega-3 para corazón y cerebro", "Rico en vitamina B12 y selenio")),
        Ingrediente("🥦", "Brócoli", "Verdura", 300f, 96f, "34 kcal",
            listOf("Fibra", "Vitamina C", "Antioxidantes"),
            "Crucífera densa en nutrientes: mucha vitamina C, fibra y antioxidantes con muy pocas calorías.",
            listOf("Refuerza el sistema inmune", "Mejora la digestión por su fibra", "Aporta calcio y folato vegetales")),
        Ingrediente("🌶️", "Rábano", "Verdura", 22f, 96f, "16 kcal",
            listOf("Hidratante", "Vitamina C", "Bajo en kcal"),
            "Fresco y crujiente, casi todo agua: suma volumen y saciedad al plato con calorías mínimas.",
            listOf("Hidrata y refresca", "Favorece la digestión", "Antioxidantes que protegen las células")),
        Ingrediente("🍠", "Camote asado", "Carbohidrato", 112f, 96f, "86 kcal",
            listOf("Betacaroteno", "Fibra", "Energía"),
            "Carbohidrato complejo de bajo índice glucémico: energía estable y betacaroteno que el cuerpo convierte en vitamina A.",
            listOf("Energía de liberación lenta", "Vitamina A para vista y piel", "Potasio y fibra que sacian")),
        Ingrediente("🫒", "Aceite de oliva", "Grasa saludable", 270f, 0f, "120 kcal",
            listOf("Monoinsaturadas", "Vitamina E", "Polifenoles"),
            "Grasa monoinsaturada del aderezo: ayuda a absorber vitaminas liposolubles y da sabor sin grasas saturadas.",
            listOf("Cuida el colesterol bueno (HDL)", "Antioxidante: vitamina E y polifenoles", "Mejora la absorción de nutrientes"))
    )),
    Plato(
        id = "salmon", nombre = "Salmón", emoji = "🍣", imagen = R.drawable.dieta_salmon,
        descripcion = "Grasas saludables y proteína completa: energía estable para rendir y recuperarte mejor.",
        tags = listOf("Recuperación", "Energía", "Omega-3"),
        items = listOf(
        Ingrediente("🍣", "Salmón", "Proteína", 180f, 92f, "208 kcal",
            listOf("20 g proteína", "Omega-3", "Vitamina D"),
            "Pescado graso estrella: omega-3 EPA y DHA, proteína completa y una de las pocas fuentes naturales de vitamina D.",
            listOf("Omega-3 para corazón y cerebro", "Vitamina D para huesos e inmunidad", "Proteína completa de calidad")),
        Ingrediente("🌾", "Quinoa", "Cereal integral", 286f, 92f, "120 kcal",
            listOf("Proteína vegetal", "Fibra", "Sin gluten"),
            "Pseudocereal con proteína vegetal completa (todos los aminoácidos esenciales), fibra y minerales, sin gluten.",
            listOf("Proteína vegetal completa", "Energía de índice glucémico moderado", "Hierro y magnesio")),
        Ingrediente("🥦", "Brócoli", "Verdura", 20f, 92f, "34 kcal",
            listOf("Fibra", "Vitamina C", "Antioxidantes"),
            "Crucífera densa en nutrientes: vitamina C, fibra y antioxidantes con muy pocas calorías.",
            listOf("Refuerza el sistema inmune", "Mejora la digestión", "Calcio y folato vegetales")),
        Ingrediente("🥑", "Aguacate", "Grasa saludable", 128f, 92f, "160 kcal",
            listOf("Monoinsaturadas", "Potasio", "Fibra"),
            "Fruta cremosa rica en grasas monoinsaturadas, potasio y fibra que dan saciedad y cuidan el corazón.",
            listOf("Grasas que cuidan el corazón", "Más potasio que el plátano", "Fibra y vitamina E"))
    )),
    Plato(
        id = "ensalada", nombre = "Ensalada", emoji = "🥗", imagen = R.drawable.dieta_ensalada,
        descripcion = "Opción liviana y saciante, pensada para bajar porcentaje graso sin pasar hambre.",
        tags = listOf("Pérdida de grasa", "Liviano", "Saciante"),
        items = listOf(
        Ingrediente("🥚", "Huevo", "Proteína", 355f, 88f, "78 kcal",
            listOf("6 g proteína", "Colina", "Vitamina B12"),
            "Proteína completa y económica; la yema concentra colina, vitamina D y B12 esenciales para el cerebro.",
            listOf("Proteína completa de referencia", "Colina para la memoria", "Saciante con pocas calorías")),
        Ingrediente("🥬", "Hojas verdes", "Verdura", 228f, 88f, "15 kcal",
            listOf("Folato", "Fibra", "Vitamina K"),
            "Base de hojas frescas: folato, vitamina K y mucha agua y fibra con apenas calorías.",
            listOf("Volumen y saciedad sin calorías", "Folato y vitamina K", "Hidratan y aportan antioxidantes")),
        Ingrediente("🍊", "Naranja", "Fruta", 138f, 88f, "47 kcal",
            listOf("Vitamina C", "Fibra", "Antioxidantes"),
            "Cítrico jugoso cargado de vitamina C que refuerza las defensas y mejora la absorción del hierro vegetal.",
            listOf("Vitamina C para las defensas", "Fibra que regula el azúcar", "Hidratante y antioxidante")),
        Ingrediente("🫒", "Aderezo ligero", "Grasa saludable", 292f, 88f, "90 kcal",
            listOf("Con moderación", "Sabor", "Grasa buena"),
            "Un toque de grasa de sabor: usalo con moderación para realzar el plato sin disparar las calorías.",
            listOf("Realza el sabor del plato", "Ayuda a absorber vitaminas", "Mejor si es a base de aceite de oliva"))
    ))
)

/* ═══════════════════════════════════════════════════════
   PLANO — contenido migrado de "Plano Interactivo.html"
   (2 pisos, puntos con coordenadas % sobre el plano)
   ═══════════════════════════════════════════════════════ */

data class PuntoPlano(
    val n: Int,
    val x: Float,   // % horizontal
    val y: Float,   // % vertical
    val titulo: String,
    val desc: String
)

data class Piso(
    val etiqueta: String,
    val titulo: String,
    val nivel: String,
    val tag: String,
    val puntos: List<PuntoPlano>
)

val PISOS = listOf(
    Piso("Piso 1 — Planta Baja", "Recepción, Spinning & Galerías", "N ± 0.00 m", "PLANTA BAJA", listOf(
        PuntoPlano(1, 33f, 73f, "Recepción & Hall", "Punto de ingreso principal. Aquí se realiza el registro de miembros, control de acceso e información general del centro."),
        PuntoPlano(2, 39f, 27f, "Cafetería", "Área de descanso y nutrición. Se ofrecen bebidas, batidos proteicos y snacks saludables para antes y después del entrenamiento."),
        PuntoPlano(3, 41f, 47f, "Zona de Galerías", "Núcleo circular con escalera helicoidal que conecta ambos pisos. Espacio de circulación y exhibición central del complejo."),
        PuntoPlano(4, 47f, 49f, "Zona de Ventas", "Tienda de productos deportivos: ropa, suplementos y accesorios de entrenamiento."),
        PuntoPlano(5, 56f, 31f, "Vestidores Hombres", "Vestidores con lockers, duchas y servicios sanitarios para los usuarios masculinos."),
        PuntoPlano(6, 50f, 37f, "Vestidores Mujeres", "Vestidores con lockers, duchas y servicios sanitarios para las usuarias femeninas."),
        PuntoPlano(7, 73f, 45f, "Sala de Masajes", "Cabinas de masaje y recuperación muscular asistida por terapeutas profesionales."),
        PuntoPlano(8, 64f, 22f, "Sala de Danza / Aeróbicos", "Salón amplio para clases grupales de danza, zumba y rutinas aeróbicas dirigidas."),
        PuntoPlano(9, 53f, 69f, "Sala de Spinning", "Área equipada con bicicletas estáticas para clases de ciclismo indoor de alta intensidad."),
        PuntoPlano(10, 25f, 49f, "Administración & Oficinas", "Oficinas del personal administrativo, gerencia y atención a socios."),
        PuntoPlano(11, 20f, 66f, "Caseta de Vigilancia", "Control de seguridad y monitoreo del acceso peatonal al complejo."),
        PuntoPlano(12, 16f, 40f, "Servicios Sanitarios", "Baños públicos de apoyo ubicados cerca del acceso y áreas comunes.")
    )),
    Piso("Piso 2 — Nivel Superior", "Spa, Artes Marciales & Boxeo", "N + 3.50 m", "NIVEL SUPERIOR", listOf(
        PuntoPlano(1, 31f, 54f, "Hall & Escalera", "Distribuidor central del segundo nivel conectado por la escalera helicoidal de la galería."),
        PuntoPlano(2, 32f, 31f, "Estética Facial", "Cabinas dedicadas a tratamientos faciales, limpieza de cutis y cuidado de la piel."),
        PuntoPlano(3, 15f, 49f, "Saunas (H / M)", "Saunas secas separadas por género para relajación, desintoxicación y recuperación térmica."),
        PuntoPlano(4, 19f, 54f, "Sala de Espera", "Área de descanso para usuarios en turno de tratamientos de spa y relajación."),
        PuntoPlano(5, 12f, 63f, "Masajes", "Cabinas de masaje relajante y terapéutico con ambientación tranquila."),
        PuntoPlano(6, 32f, 70f, "Piscina de Aguas Termales", "Piscina de hidroterapia con aguas templadas para relajación muscular y circulación."),
        PuntoPlano(7, 28f, 77f, "Piscina de Lodo", "Tratamiento de fangoterapia: aplicación de lodos minerales con beneficios para la piel."),
        PuntoPlano(8, 45f, 63f, "Sala de Pesas / Estaciones", "Zona de musculación con estaciones de peso libre y máquinas de fuerza."),
        PuntoPlano(9, 73f, 39f, "Sala de Artes Marciales", "Tatami amplio para práctica de karate, judo y disciplinas de combate."),
        PuntoPlano(10, 60f, 64f, "Sala de Boxeo", "Ring y sacos de entrenamiento para boxeo y acondicionamiento físico de contacto."),
        PuntoPlano(11, 62f, 18f, "Terraza", "Terraza exterior para enfriamiento, descanso al aire libre y actividades ligeras.")
    ))
)

/* ═══ Clases de la semana (pantalla Inicio) ═══
   Antes vivían sueltas en la pestaña Entrenar; se mudaron a Inicio para
   reservar o ver de qué trata cada una (el contacto con el entrenador para
   pedir una rutina o sesión 1 a 1 se queda en Entrenar). */
data class ClaseSemana(
    val id: String,
    val hora: String, val dia: String, val nombre: String,
    val lugar: String, val descripcion: String
)

val CLASES_SEMANA = listOf(
    ClaseSemana(
        "spinning-hoy", "19:30", "HOY", "Spinning Intenso", "Sala de Spinning · Piso 1 · Prof. Martina",
        "Clase grupal en bicicleta fija con cambios de ritmo e intervalos guiados por la profesora. Foco en resistencia cardiovascular y piernas — llevá botella de agua y toalla."
    ),
    ClaseSemana(
        "boxeo-mar", "18:00", "MAR", "Boxeo", "Sala de Boxeo · Piso 2",
        "Técnica de golpes y combinaciones sobre bolsa, más trabajo de acondicionamiento físico. No hace falta experiencia previa; el gimnasio presta guantes y vendas."
    ),
    ClaseSemana(
        "danza-sab", "10:00", "SÁB", "Danza / Aeróbicos", "Sala de Danza · Piso 1",
        "Rutina coreografiada de bajo impacto pensada para resistencia y coordinación. Clase apta para todo nivel, ritmo variado según la coreografía de la semana."
    )
)

/* ═══ Rutina asignada por un entrenador, para la pestaña Entrenar ═══
   Serie a serie, con un peso de partida ajustable (ver botones +/- en la
   tarjeta): el socio registra cada serie a medida que la hace, y esa carga
   es la que se compara contra el Ghost Mode. La rutina real de cada socio
   se arma desde el sistema de empleados y se lee vía
   cargarRutinaAsignada() (EntrenamientoRepository.kt) — acá solo viven las
   formas de los datos, no un ejemplo fijo. */
data class EjercicioRutina(
    val nombre: String,
    val seriesObjetivo: Int,
    val pesoBaseKg: Float,
    /** Dominadas/fondos: el peso mostrado es lo AGREGADO al corporal, no el
     *  total (mismo criterio que EJERCICIOS_PESO_CORPORAL en GamificacionData.kt). */
    val esPesoCorporal: Boolean = false,
    /** Id real del ejercicio en el catálogo (colección "ejercicios", el
     *  mismo que arma la Galería) — el entrenador lo elige de una lista al
     *  armar la rutina, nunca escribe uno a mano (ver editor_rutinas.py).
     *  Con esto, el botón "Técnica" de Entrenar muestra la descripción y
     *  las zonas musculares reales de ese ejercicio en vez de un detalle
     *  inventado o vacío. */
    val ejercicioId: String? = null
)

data class RutinaDelDia(val nombre: String, val creadaPor: String, val ejercicios: List<EjercicioRutina>)
