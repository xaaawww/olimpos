package com.olimpos.gym.data

import com.google.firebase.Firebase
import com.google.firebase.auth.FirebaseAuthInvalidCredentialsException
import com.google.firebase.auth.FirebaseAuthInvalidUserException
import com.google.firebase.auth.auth
import com.google.firebase.firestore.firestore
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
     *  (ver auth_repo.py). Si el documento es viejo y no tiene el campo
     *  (cuentas creadas antes de esta función), se asume que no debe. */
    suspend fun debeCambiarPassword(): Boolean {
        val uid = uidActual ?: return false
        return try {
            val doc = Firebase.firestore.collection("socios_app").document(uid).get().await()
            doc.getBoolean("debe_cambiar_password") ?: false
        } catch (e: Exception) {
            false
        }
    }

    /** Cambia la contraseña en Firebase Auth y apaga el flag en Firestore
     *  (ver firestore.rules: el socio solo puede tocar ese único campo, y
     *  solo para ponerlo en false). Devuelve un mensaje de error si falló,
     *  o null si salió bien. */
    suspend fun actualizarPassword(nueva: String): String? {
        val user = Firebase.auth.currentUser ?: return "Tu sesión expiró, volvé a iniciar sesión."
        return try {
            user.updatePassword(nueva).await()
            Firebase.firestore.collection("socios_app").document(user.uid)
                .update("debe_cambiar_password", false).await()
            null
        } catch (e: Exception) {
            "No se pudo cambiar la contraseña. Volvé a iniciar sesión e intentá de nuevo."
        }
    }
}

/** id a usar como "socio_id" en Firestore (marcas, ranking) — el uid de
 *  Firebase Auth, no un nombre fijo. */
fun socioActualId(): String = SocioAuth.uidActual ?: "desconocido"

fun socioActualNombre(): String = SocioAuth.nombreActual ?: "Socio"
