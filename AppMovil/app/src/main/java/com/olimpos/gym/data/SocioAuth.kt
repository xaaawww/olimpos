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
            // trim() también en la contraseña: al copiarla de WhatsApp se suele
            // llevar un espacio o salto de línea al final, y ninguna contraseña
            // válida empieza ni termina con espacios (ver CambiarPasswordScreen).
            Firebase.auth.signInWithEmailAndPassword(email.trim(), password.trim()).await()
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

    /** Firebase le manda al socio un email (en español) con un link para
     *  elegir una contraseña nueva. Por seguridad no se dice si el email
     *  existe o no: el mensaje de éxito es el mismo. */
    suspend fun enviarEmailRecuperacion(email: String): String? {
        val limpio = email.trim().lowercase()
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(limpio).matches()) return "Escribí un email válido."
        return try {
            Firebase.auth.setLanguageCode("es")
            Firebase.auth.sendPasswordResetEmail(limpio).await()
            null
        } catch (e: FirebaseAuthInvalidUserException) {
            null
        } catch (e: Exception) {
            "No se pudo enviar el email. Revisá tu conexión e intentá de nuevo."
        }
    }

    /** Cambiar la contraseña desde Configuración: Firebase pide haber entrado
     *  hace poco, así que primero se confirma la contraseña actual. */
    suspend fun cambiarPassword(actual: String, nueva: String): String? {
        val user = Firebase.auth.currentUser ?: return "Tu sesión expiró, volvé a iniciar sesión."
        val email = user.email ?: return "Tu cuenta no tiene email."
        errorDePassword(nueva)?.let { return it }
        if (actual.trim() == nueva) return "La contraseña nueva tiene que ser distinta de la actual."
        return try {
            user.reauthenticate(com.google.firebase.auth.EmailAuthProvider.getCredential(email, actual.trim())).await()
            user.updatePassword(nueva).await()
            null
        } catch (e: FirebaseAuthInvalidCredentialsException) {
            "La contraseña actual no es correcta."
        } catch (e: Exception) {
            "No se pudo cambiar la contraseña. Revisá tu conexión e intentá de nuevo."
        }
    }

    val emailActual: String? get() = Firebase.auth.currentUser?.email

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

/** null si la contraseña sirve; si no, qué le falta. Mismas reglas que el
 *  sistema de empleados: 8 a 64 caracteres, letras y números, sin espacios
 *  al principio ni al final. */
fun errorDePassword(p: String): String? = when {
    p != p.trim() -> "La contraseña no puede empezar ni terminar con espacios."
    p.length < 8 -> "La contraseña tiene que tener al menos 8 caracteres."
    p.length > 64 -> "La contraseña puede tener hasta 64 caracteres."
    !p.any { it.isLetter() } || !p.any { it.isDigit() } -> "La contraseña tiene que tener letras y números."
    else -> null
}

/** id del socio (marcas, ranking) — el uid de Firebase Auth, que la base de
 *  datos guarda en socios.firebase_uid. */
fun socioActualId(): String = SocioAuth.uidActual ?: "desconocido"

fun socioActualNombre(): String = SocioAuth.nombreActual ?: "Socio"
