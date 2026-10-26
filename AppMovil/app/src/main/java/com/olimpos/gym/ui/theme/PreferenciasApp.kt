package com.olimpos.gym.ui.theme

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/** Tamaño de letra de toda la app (se aplica en MainActivity sobre el que el
 *  socio ya eligió en su celular). Normal = el tamaño de siempre. */
enum class EscalaLetra(val etiqueta: String, val factor: Float) {
    CHICA("Chica", 0.85f),
    NORMAL("Normal", 0.92f),
    GRANDE("Grande", 1.04f)
}

/** Preferencias locales del celular que cambian cómo se ve la app. Son
 *  `mutableStateOf`: al cambiarlas en Configuración, la app se redibuja sola. */
object PreferenciasApp {
    private const val PREFS = "olimpos_prefs"
    private const val KEY_LETRA = "escala_letra"

    var escalaLetra by mutableStateOf(EscalaLetra.NORMAL)
        private set

    fun cargar(context: Context) {
        val guardada = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY_LETRA, null)
        escalaLetra = EscalaLetra.entries.firstOrNull { it.name == guardada } ?: EscalaLetra.NORMAL
    }

    fun guardarEscalaLetra(context: Context, escala: EscalaLetra) {
        escalaLetra = escala
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY_LETRA, escala.name).apply()
    }
}
