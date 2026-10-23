# Reglas de R8 para la versión "optimizada".
# Las librerías (Firebase, Coil, Compose, OkHttp) ya traen las suyas; la app
# no usa reflexión (el JSON se lee a mano con org.json), así que acá solo se
# conservan los números de línea para que un error se pueda ubicar.
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
