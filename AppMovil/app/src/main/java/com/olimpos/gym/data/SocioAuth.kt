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

    /** true si a este socio todavía le queda pendiente cambiar la
     *  contraseña temporal que le generó el empleado al crear el acceso
     *  (ver auth_repo.py). Si no se puede consultar, se asume que no debe. */
    suspend fun debeCambiarPassword(): Boolean {
        if (uidActual == null) return false
        return try {
            Api.get("/v1/yo").optBoolean("debe_cambiar_password", false)
        } catch (e: Exception) {
            false
        }
    }

    /** Cambia la contraseña en Firebase Auth (que es quien la guarda) y le
     *  avisa a la API que ya no hace falta pedirla de nuevo. Devuelve un
     *  mensaje de error si falló, o null si salió bien. */
    suspend fun actualizarPassword(nueva: String): String? {
        val user = Firebase.auth.currentUser ?: return "Tu sesión expiró, volvé a iniciar sesión."
        return try {
            user.updatePassword(nueva).await()
            Api.post("/v1/yo/password-cambiada")
            null
        } catch (e: Exception) {
            "No se pudo cambiar la contraseña. Volvé a iniciar sesión e intentá de nuevo."
        }
    }
}

/** id del socio (marcas, ranking) — el uid de Firebase Auth, que la base de
 *  datos guarda en socios.firebase_uid. */
fun socioActualId(): String = SocioAuth.uidActual ?: "desconocido"

fun socioActualNombre(): String = SocioAuth.nombreActual ?: "Socio"
