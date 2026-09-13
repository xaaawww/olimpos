plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "2.0.20" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.20" apply false
    // Fase 3: se activa (quitando el "apply false" y agregándolo en app/build.gradle.kts)
    // recién cuando exista app/google-services.json — sin ese archivo, Gradle falla al sincronizar.
    id("com.google.gms.google-services") version "4.4.2" apply false
}
