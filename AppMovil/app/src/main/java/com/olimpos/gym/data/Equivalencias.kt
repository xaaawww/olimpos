package com.olimpos.gym.data

import java.text.DecimalFormat
import java.text.DecimalFormatSymbols
import java.util.Locale
import kotlin.math.abs
import kotlin.math.floor
import kotlin.math.log10
import kotlin.math.pow

/* ═══════════════════════════════════════════════════════
   EQUIVALENCIAS DE CARGA — "Este mes levantaste el equivalente a…"
   Los kilos movidos en el mes se comparan con cosas de todos los
   tamaños: desde un gato hasta el universo observable, pasando por
   animales, vehículos, monumentos famosos, planetas y galaxias.
   Los pesos son aproximados (fuentes públicas: museos, NASA, etc.).
   ═══════════════════════════════════════════════════════ */

enum class EscalaEquivalencia(val titulo: String, val emoji: String) {
    CASA("En casa", "🏠"),
    ANIMALES("Animales", "🐾"),
    VEHICULOS("Vehículos", "🚦"),
    MONUMENTOS("Monumentos", "🏛️"),
    ESPACIO("El espacio", "🌌"),
}

data class Equivalencia(
    val kg: Double,
    val singular: String,      // "un elefante africano"
    val plural: String,        // "elefantes africanos"
    val emoji: String,
    val escala: EscalaEquivalencia,
    val dato: String,          // dato curioso que se muestra en la escala completa
)

val EQUIVALENCIAS: List<Equivalencia> = listOf(
    // ── en casa ──
    Equivalencia(4.5, "un gato", "gatos", "🐈", EscalaEquivalencia.CASA, "El gato doméstico promedio pesa 4,5 kg."),
    Equivalencia(50.0, "una bolsa de cemento", "bolsas de cemento", "🧱", EscalaEquivalencia.CASA, "En la obra se usan bolsas de 50 kg."),
    Equivalencia(70.0, "un lavarropas", "lavarropas", "🧺", EscalaEquivalencia.CASA, "Un lavarropas de carga frontal pesa unos 70 kg."),
    Equivalencia(120.0, "una heladera con freezer", "heladeras", "🧊", EscalaEquivalencia.CASA, "Una heladera grande pesa unos 120 kg vacía."),
    Equivalencia(400.0, "un piano de cola", "pianos de cola", "🎹", EscalaEquivalencia.CASA, "Un piano de cola de concierto pesa unos 400 kg."),
    // ── animales ──
    Equivalencia(30.0, "un golden retriever", "golden retrievers", "🐕", EscalaEquivalencia.ANIMALES, "Un golden adulto pesa unos 30 kg."),
    Equivalencia(120.0, "un oso panda", "osos panda", "🐼", EscalaEquivalencia.ANIMALES, "Un panda adulto pesa entre 100 y 150 kg."),
    Equivalencia(700.0, "una vaca", "vacas", "🐄", EscalaEquivalencia.ANIMALES, "Una vaca adulta pesa unos 700 kg."),
    Equivalencia(1_500.0, "un hipopótamo", "hipopótamos", "🦛", EscalaEquivalencia.ANIMALES, "Un hipopótamo adulto pesa 1,5 toneladas."),
    Equivalencia(6_000.0, "un elefante africano", "elefantes africanos", "🐘", EscalaEquivalencia.ANIMALES, "El animal terrestre más pesado de hoy: 6 toneladas."),
    Equivalencia(8_000.0, "un Tyrannosaurus rex", "Tyrannosaurus rex", "🦖", EscalaEquivalencia.ANIMALES, "El T. rex más grande que se conoce pesaba unas 8 toneladas."),
    Equivalencia(150_000.0, "una ballena azul", "ballenas azules", "🐋", EscalaEquivalencia.ANIMALES, "El animal más pesado que existió jamás: 150 toneladas."),
    // ── vehículos ──
    Equivalencia(110.0, "una moto", "motos", "🛵", EscalaEquivalencia.VEHICULOS, "Una moto chica pesa unos 110 kg."),
    Equivalencia(1_200.0, "un auto compacto", "autos compactos", "🚗", EscalaEquivalencia.VEHICULOS, "Un auto compacto pesa unos 1.200 kg."),
    Equivalencia(2_500.0, "una camioneta 4x4", "camionetas 4x4", "🚙", EscalaEquivalencia.VEHICULOS, "Una pick-up doble cabina pesa unos 2.500 kg."),
    Equivalencia(12_000.0, "un colectivo", "colectivos", "🚌", EscalaEquivalencia.VEHICULOS, "Un colectivo urbano vacío pesa unas 12 toneladas."),
    Equivalencia(41_000.0, "un avión Boeing 737", "aviones Boeing 737", "✈️", EscalaEquivalencia.VEHICULOS, "Un Boeing 737 vacío pesa unas 41 toneladas."),
    Equivalencia(120_000.0, "una locomotora", "locomotoras", "🚂", EscalaEquivalencia.VEHICULOS, "Una locomotora diésel pesa unas 120 toneladas."),
    Equivalencia(420_000.0, "la Estación Espacial Internacional", "Estaciones Espaciales", "🛰️", EscalaEquivalencia.VEHICULOS, "La EEI pesa 420 toneladas y da una vuelta a la Tierra cada 90 minutos."),
    Equivalencia(2_900_000.0, "el cohete Saturno V", "cohetes Saturno V", "🚀", EscalaEquivalencia.VEHICULOS, "El cohete que llevó a los astronautas a la Luna, lleno de combustible."),
    Equivalencia(52_310_000.0, "el Titanic", "Titanics", "🚢", EscalaEquivalencia.VEHICULOS, "El Titanic desplazaba 52.310 toneladas."),
    // ── monumentos ──
    Equivalencia(12_500.0, "un moái de la Isla de Pascua", "moáis", "🗿", EscalaEquivalencia.MONUMENTOS, "Un moái promedio pesa 12,5 toneladas de piedra volcánica."),
    Equivalencia(13_700.0, "la campana del Big Ben", "campanas del Big Ben", "🔔", EscalaEquivalencia.MONUMENTOS, "La Great Bell de Londres pesa 13,7 toneladas."),
    Equivalencia(225_000.0, "la Estatua de la Libertad", "Estatuas de la Libertad", "🗽", EscalaEquivalencia.MONUMENTOS, "Cobre y acero: 225 toneladas."),
    Equivalencia(635_000.0, "el Cristo Redentor", "Cristos Redentores", "⛰️", EscalaEquivalencia.MONUMENTOS, "Mide 30 metros y pesa 635 toneladas."),
    Equivalencia(7_300_000.0, "la Torre Eiffel", "Torres Eiffel", "🗼", EscalaEquivalencia.MONUMENTOS, "Solo su estructura de hierro: 7.300 toneladas."),
    Equivalencia(331_000_000.0, "el Empire State", "Empire States", "🏙️", EscalaEquivalencia.MONUMENTOS, "El rascacielos de Nueva York pesa 331.000 toneladas."),
    Equivalencia(887_000_000.0, "el puente Golden Gate", "puentes Golden Gate", "🌉", EscalaEquivalencia.MONUMENTOS, "El puente de San Francisco pesa 887.000 toneladas."),
    Equivalencia(5_900_000_000.0, "la Gran Pirámide de Giza", "Grandes Pirámides", "🔺", EscalaEquivalencia.MONUMENTOS, "Unos 2,3 millones de bloques de piedra: 5,9 millones de toneladas."),
    // ── el espacio ──
    Equivalencia(2.2e14, "el cometa Halley", "cometas Halley", "☄️", EscalaEquivalencia.ESPACIO, "Pasa cerca de la Tierra cada 76 años; vuelve en 2061."),
    Equivalencia(7.35e22, "la Luna", "Lunas", "🌙", EscalaEquivalencia.ESPACIO, "Está a 384.400 km y su gravedad mueve las mareas."),
    Equivalencia(6.42e23, "Marte", "Martes", "🔴", EscalaEquivalencia.ESPACIO, "El planeta rojo pesa la décima parte que la Tierra."),
    Equivalencia(5.97e24, "la Tierra", "Tierras", "🌍", EscalaEquivalencia.ESPACIO, "Nuestro planeta: 5,97 cuatrillones de toneladas."),
    Equivalencia(1.90e27, "Júpiter", "Júpiters", "🪐", EscalaEquivalencia.ESPACIO, "Pesa más que todos los otros planetas juntos, dos veces y media."),
    Equivalencia(1.99e30, "el Sol", "Soles", "☀️", EscalaEquivalencia.ESPACIO, "Tiene el 99,8 % de toda la masa del sistema solar."),
    Equivalencia(8.5e36, "Sagitario A*, el agujero negro del centro de la galaxia", "agujeros negros", "🕳️", EscalaEquivalencia.ESPACIO, "Pesa como 4,3 millones de soles juntos."),
    Equivalencia(2.3e42, "la galaxia de Andrómeda", "galaxias de Andrómeda", "🌀", EscalaEquivalencia.ESPACIO, "La galaxia vecina: está a 2,5 millones de años luz."),
    Equivalencia(3.0e42, "la Vía Láctea", "Vías Lácteas", "🌌", EscalaEquivalencia.ESPACIO, "Nuestra galaxia: entre 100.000 y 400.000 millones de estrellas."),
    Equivalencia(1.5e53, "el universo observable", "universos", "✨", EscalaEquivalencia.ESPACIO, "Toda la materia que podemos llegar a ver."),
).sortedBy { it.kg }

/** La cosa más pesada que ya superaste este mes (null si todavía no llegaste ni al gato). */
fun equivalenciaDeCarga(kg: Double): Equivalencia? = EQUIVALENCIAS.lastOrNull { it.kg <= kg }

/** La siguiente meta: la cosa más liviana que todavía no superaste. */
fun proximaEquivalencia(kg: Double): Equivalencia? = EQUIVALENCIAS.firstOrNull { it.kg > kg }

/** La mejor comparación de cada escala (para los chips de la tarjeta). */
fun mejorPorEscala(kg: Double): List<Equivalencia> = EscalaEquivalencia.values().map { escala ->
    val deEscala = EQUIVALENCIAS.filter { it.escala == escala }
    deEscala.lastOrNull { it.kg <= kg } ?: deEscala.first()
}

/** "3 elefantes africanos", "Un elefante africano". */
fun tituloEquivalencia(kg: Double, eq: Equivalencia): String {
    val veces = floor(kg / eq.kg).toLong()
    return if (veces >= 2) "${formatoEntero(veces.toDouble())} ${eq.plural}" else eq.singular.replaceFirstChar { it.uppercase() }
}

/** Cuánto de esa cosa moviste: "× 3,4", "42 %", "0,0031 %" o "2 × 10⁻¹⁸ %". */
fun vecesEquivalencia(kg: Double, eq: Equivalencia): String {
    val veces = kg / eq.kg
    if (veces >= 1) return "× ${if (veces >= 100) formatoEntero(veces) else formato(veces, 1)}"
    val pct = veces * 100
    return when {
        pct >= 1 -> "${formatoEntero(pct)} %"
        pct >= 0.0001 -> "${formato(pct, 4).trimEnd('0').trimEnd(',')} %"
        else -> "${cientifico(pct)} %"
    }
}

/** Años que tardarías en mover esa cosa a tu ritmo de este mes (null si ya la superaste). */
fun anosParaMover(kgDelMes: Double, eq: Equivalencia): Double? =
    if (kgDelMes <= 0 || kgDelMes >= eq.kg) null else eq.kg / (kgDelMes * 12)

fun textoAnos(anos: Double): String = when {
    anos < 1 -> "menos de un año"
    anos < 2 -> "1 año"
    anos < 1e6 -> "${formatoEntero(anos)} años"
    else -> "${cientifico(anos)} años"
}

/** Peso legible: "450 kg", "7.300 t", "5,97 × 10²⁴ kg". */
fun formatoPeso(kg: Double): String = when {
    kg < 1_000 -> "${formatoEntero(kg)} kg"
    kg < 1e12 -> "${if (kg < 10_000) formato(kg / 1000, 1) else formatoEntero(kg / 1000)} t"
    else -> "${cientifico(kg)} kg"
}

// ── formato de números en castellano (Argentina) ──

private val SIMBOLOS = DecimalFormatSymbols(Locale("es", "AR"))

private fun formatoEntero(v: Double): String = DecimalFormat("#,##0", SIMBOLOS).format(v)

private fun formato(v: Double, decimales: Int): String =
    DecimalFormat("#,##0." + "#".repeat(decimales), SIMBOLOS).format(v)

private val SUPERINDICES = mapOf('0' to '⁰', '1' to '¹', '2' to '²', '3' to '³', '4' to '⁴', '5' to '⁵',
    '6' to '⁶', '7' to '⁷', '8' to '⁸', '9' to '⁹', '-' to '⁻')

/** 2,3 × 10⁴² */
private fun cientifico(v: Double): String {
    if (v == 0.0) return "0"
    val exp = floor(log10(abs(v))).toInt()
    val mantisa = v / 10.0.pow(exp)
    val exponente = exp.toString().map { SUPERINDICES[it] ?: it }.joinToString("")
    return "${formato(mantisa, 1)} × 10$exponente"
}
