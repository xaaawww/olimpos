package com.olimpos.gym.data

import com.olimpos.gym.R

/* GENERADO por AppMovil/imagenes_ejercicios.py — no editar a mano.
   Dibujos de los ejercicios, los mismos del sistema de empleados. */

private val POR_ID: Map<String, Int> = mapOf(
    "9" to R.drawable.ej_9,
    "10" to R.drawable.ej_10,
    "11" to R.drawable.ej_11,
    "12" to R.drawable.ej_12,
    "13" to R.drawable.ej_13,
    "14" to R.drawable.ej_14,
    "17" to R.drawable.ej_17,
    "18" to R.drawable.ej_18,
    "19" to R.drawable.ej_19,
    "20" to R.drawable.ej_20,
    "21" to R.drawable.ej_21,
    "22" to R.drawable.ej_22,
    "23" to R.drawable.ej_23,
    "24" to R.drawable.ej_24,
    "25" to R.drawable.ej_25,
    "26" to R.drawable.ej_26,
    "27" to R.drawable.ej_27,
    "28" to R.drawable.ej_28,
    "29" to R.drawable.ej_29,
    "30" to R.drawable.ej_30,
    "31" to R.drawable.ej_31,
    "32" to R.drawable.ej_32,
    "33" to R.drawable.ej_33,
)

private val POR_NOMBRE: Map<String, Int> = mapOf(
    "abduccion cadera maquina" to R.drawable.ej_9,
    "aduccion cadera maquina" to R.drawable.ej_10,
    "crunch abdominal" to R.drawable.ej_11,
    "curl biceps barra" to R.drawable.ej_12,
    "curl femoral" to R.drawable.ej_13,
    "dominadas" to R.drawable.ej_14,
    "elevacion talones" to R.drawable.ej_17,
    "elevaciones laterales" to R.drawable.ej_18,
    "extension cuadriceps" to R.drawable.ej_19,
    "extension triceps polea" to R.drawable.ej_20,
    "face pull" to R.drawable.ej_21,
    "fondos paralelas" to R.drawable.ej_22,
    "giro ruso" to R.drawable.ej_23,
    "hip thrust" to R.drawable.ej_24,
    "pajaros" to R.drawable.ej_25,
    "peso muerto" to R.drawable.ej_26,
    "peso muerto rumano" to R.drawable.ej_27,
    "press banca" to R.drawable.ej_28,
    "press inclinado mancuernas" to R.drawable.ej_29,
    "press militar barra" to R.drawable.ej_30,
    "remo barra" to R.drawable.ej_31,
    "sentadilla" to R.drawable.ej_32,
    "zancadas" to R.drawable.ej_33,
)

private fun claveNombre(nombre: String): String {
    val sinTildes = java.text.Normalizer.normalize(nombre.lowercase(), java.text.Normalizer.Form.NFD)
        .replace(Regex("\\p{Mn}+"), "")
        .replace(Regex("\\(.*?\\)"), " ")
    return Regex("[a-z0-9]+").findAll(sinTildes).map { it.value }
        .filter { it !in setOf("de", "con", "en", "la", "el") }.joinToString(" ")
}

/** Dibujo del ejercicio: por id del catálogo, o si no por nombre (los de la
 *  Calculadora, que comparten nombre con uno publicado). `null` si no tiene. */
fun imagenDeEjercicio(id: String? = null, nombre: String? = null): Int? =
    id?.let { POR_ID[it] } ?: nombre?.let { POR_NOMBRE[claveNombre(it)] }
