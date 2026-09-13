package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.auth.FirebaseAuthInvalidCredentialsException
import com.google.firebase.auth.FirebaseAuthInvalidUserException
import com.google.firebase.auth.auth
import kotlinx.coroutines.tasks.await

/**
 * Sesión del socio actual vía Firebase Authentication. El socio nunca se
 * registra solo: un empleado le crea el usuario desde el sistema de
 * gestión (ver auth_repo.py) y le pasa el email/contraseña para que
 * entre acá — por eso [LoginScreen] ya no tiene una opción de "crear
 * cuenta".
 */
object SocioAuth {
    val uidActual: String? get() = Firebase.auth.currentUser?.uid
    val nombreActual: String? get() = Firebase.auth.currentUser?.displayName

    /** Devuelve un mensaje de error listo para mostrar si falla, o null si
     *  el login fue exitoso. */
    suspend fun iniciarSesion(email: String, password: String): String? {
        return try {
            Firebase.auth.signInWithEmailAndPassword(email.trim(), password).await()
            null
        } catch (e: FirebaseAuthInvalidUserException) {
            "No existe una cuenta con ese email. Pedile el acceso a tu entrenador."
        } catch (e: FirebaseAuthInvalidCredentialsException) {
            "Email o contraseña incorrectos."
        } catch (e: Exception) {
            "No se pudo iniciar sesión. Revisá tu conexión e intentá de nuevo."
        }
    }

    fun cerrarSesion() {
        Firebase.auth.signOut()
    }
}

/** id a usar como "socio_id" en Firestore (marcas, ranking) — el uid de
 *  Firebase Auth, no un nombre fijo. */
fun socioActualId(): String = SocioAuth.uidActual ?: "desconocido"

fun socioActualNombre(): String = SocioAuth.nombreActual ?: "Socio"
