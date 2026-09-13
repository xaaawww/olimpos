plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.google.gms.google-services")
}

android {
    namespace = "com.olimpos.gym"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.olimpos.gym"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
        // Build para medir rendimiento de verdad. Un build de debug es mucho
        // más lento con Compose: la app queda marcada como depurable (ART no
        // puede optimizarla del todo) y se le agregan las herramientas de
        // inspección, que instrumentan cada composición. Este tipo de build
        // apaga las dos cosas, pero va firmado con la clave de debug para
        // poder instalarlo sin generar un keystore aparte.
        // Uso:  ./gradlew installPrueba     (o assemblePrueba para el APK)
        create("prueba") {
            isDebuggable = false
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
            versionNameSuffix = "-prueba"
            matchingFallbacks += listOf("release", "debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions { jvmTarget = "11" }
    buildFeatures { compose = true }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2024.09.03"))
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.6")
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.animation:animation")
    debugImplementation("androidx.compose.ui:ui-tooling")
    implementation("androidx.compose.ui:ui-tooling-preview")

    // Fase 3 — dietas dinámicas desde Firebase (Firestore). Las imágenes NO
    // usan Firebase Storage (pasó a requerir el plan pago Blaze) — viajan
    // como Base64 adentro del propio documento de Firestore, que sigue
    // siendo gratis. Se pueden resolver y compilar ya mismo (no requieren
    // google-services.json); lo único que falta para que INICIALICEN en
    // tiempo de ejecución es agregar app/google-services.json y activar el
    // plugin com.google.gms.google-services.
    implementation(platform("com.google.firebase:firebase-bom:33.5.1"))
    implementation("com.google.firebase:firebase-firestore-ktx")
    implementation("com.google.firebase:firebase-auth-ktx")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.9.0")

    // Carga de imágenes (las fotos de dietas publicadas llegan como
    // ByteArray, decodificadas de Base64) — Coil admite ByteArray como
    // fuente de forma nativa.
    implementation("io.coil-kt:coil-compose:2.7.0")
}
