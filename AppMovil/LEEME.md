# OlimpΩs — App Android nativa (Kotlin + Jetpack Compose)

App móvil del proyecto **Olimpos Gym**, con la identidad visual del sitio web
(dorado #C9A227 sobre negro #0d0b00, tarjetas con borde dorado, motivo Ω).

## Cómo abrirla
1. Descomprimí el ZIP.
2. En Android Studio: **File → Open…** y elegí la carpeta `Olimpos`.
3. Esperá el Gradle Sync (descarga dependencias la primera vez).
4. Ejecutá con ▶ en un emulador o celular (Android 8.0 / API 26 o superior).

## Versión liviana para los socios (variante `optimizada`, ~4 MB)
La variante `optimizada` es igual a `release`, pero R8 saca el código que no
se usa y los recursos sin referencia: pasa de ~17,7 MB a ~4,1 MB.

**Antes de compilar (una sola vez):** el Gradle del proyecto (8.9) no anda
con el Java 25 que trae Android Studio. En *File → Settings → Build,
Execution, Deployment → Build Tools → Gradle → Gradle JDK* elegí **Java 17**
(`C:\Program Files\Eclipse Adoptium\jdk-17...`).

- **Desde Android Studio:** *View → Tool Windows → Build Variants* → en `app`
  elegí `optimizada` → ▶ Run (con el celular conectado y la depuración USB
  activada), o *Build → Build APK(s)* para generar el archivo.
- **Por consola:** `gradlew assembleOptimizada` (con `JAVA_HOME` apuntando
  al JDK 17).
- El APK queda en `app/build/outputs/apk/optimizada/app-optimizada.apk`
  (hay una copia lista en `AppMovil/OlimpOS-liviana.apk`).

Ojo: está firmada con la clave de debug de ESTA computadora. Si en el celular
hay una versión instalada desde otra computadora (otra firma), Android no la
actualiza: hay que desinstalar la vieja primero (se cierra la sesión del socio).

## Secciones
- **Inicio** — carnet digital con medalla Ω animada, ocupación del gimnasio
  en vivo, próxima clase con reserva y accesos rápidos.
- **Entrenar** — rutina del día con checklist y anillo de progreso.
- **Dieta** — migración de *Dieta Saludable.html*: plato giratorio interactivo
  con 3 platos (Atún, Salmón, Ensalada), recorrido automático, kcal, tags
  y beneficios por ingrediente. Reescrito 100% en Compose (sin WebView).
- **Plano** — migración de *Plano Interactivo.html*: sector aparte (se abre
  desde Inicio o Perfil, no es pestaña principal). 2 pisos, 23 áreas,
  marcadores con zoom animado, leyenda y ficha de cada sala.
- **Perfil** — datos del socio, estadísticas y menú.

## Estructura
```
app/src/main/java/com/olimpos/gym/
├── MainActivity.kt          → navegación (4 pestañas + Plano aparte)
├── data/AppData.kt          → datos de dieta y plano (desde los HTML del Drive)
└── ui/
    ├── theme/Theme.kt       → paleta y tipografía OlimpΩs
    └── screens/             → Home, Entrenar, Dieta, Plano, Perfil, Comunes
```

## Fuentes exactas (opcional)
La app usa la tipografía del sistema con pesos fuertes. Para usar Poppins y
Nunito como en la web: descargalas de Google Fonts, poné los .ttf en
`app/src/main/res/font/` y reemplazá `FontFamily.SansSerif` en `Theme.kt`.

— Generado para el proyecto Olimpos · minSdk 26 · targetSdk 35 · Compose BOM 2024.09
