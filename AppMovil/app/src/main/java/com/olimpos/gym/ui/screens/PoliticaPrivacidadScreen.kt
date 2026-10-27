package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.ui.theme.Olimpos

/** Política de privacidad (Ley 25.326). Es el mismo texto que
 *  Paginas/privacidad.html: si se cambia acá, cambiarlo allá también. */
private val SECCIONES_POLITICA: List<Pair<String, List<String>>> = listOf(
    "1. Quién es el responsable" to listOf(
        "OLIMPOS GYM, Av. del Olimpo 1200. Contacto para temas de privacidad: contacto@olimpos.com o en la recepción del gimnasio."
    ),
    "2. Qué datos tratamos" to listOf(
        "• Identificación y contacto: nombre, apellido, DNI, email, teléfono, dirección, fecha de nacimiento y sexo.",
        "• Datos de salud (sensibles): peso, altura, edad y, solo si decidís cargarla, una lesión o condición médica.",
        "• Entrenamiento y nutrición: marcas personales, rutinas, series, comidas registradas, agua y dieta asignada.",
        "• Imágenes: las fotos de progreso y de comidas que subas.",
        "• Actividad en el club: fecha y hora de cada ingreso (cuando escaneás el QR de la recepción), reservas de clases y lockers.",
        "• Mensajes con Argos: las preguntas que le hacés al asistente y sus respuestas.",
        "• Pagos: plan, monto, fecha y medio de pago. Los datos de tu tarjeta los maneja Mercado Pago; nosotros nunca los vemos ni los guardamos.",
        "• Sitio web: el nombre, el contacto y el mensaje que mandes por el formulario."
    ),
    "3. Para qué los usamos" to listOf(
        "• Gestionar tu membresía, tus pagos y tu acceso al gimnasio.",
        "• Armar tus rutinas y dietas, y calcular tus rangos y logros.",
        "• Mostrar la ocupación del club (solo la cantidad de personas, sin nombres).",
        "• Responder tus preguntas en Argos, usando tus propios datos de entrenamiento como contexto.",
        "• Mandarte por email o WhatsApp tus datos de acceso, enlaces para recuperar la contraseña y avisos de vencimiento de la cuota.",
        "No vendemos ni cedemos tus datos a terceros para publicidad."
    ),
    "4. Tu consentimiento" to listOf(
        "Al crear tu acceso y usar la app aceptás esta política. Los datos de salud son sensibles: nadie está obligado a darlos. Si no cargás una condición médica, la app funciona igual; tu peso y tu edad se usan solo para calcular tus rangos y tu plan. Si tenés menos de 18 años, necesitás la autorización de tu madre, padre o tutor."
    ),
    "5. Quién más los procesa" to listOf(
        "Usamos estos proveedores para que el sistema funcione. Cada uno trata solo lo necesario para su tarea, y algunos de sus servidores pueden estar fuera de la Argentina:",
        "• Google Firebase: inicio de sesión (email y contraseña).",
        "• Neon: la base de datos donde se guarda todo.",
        "• Cloudflare: los servidores que conectan la app con la base.",
        "• Mercado Pago: el cobro de las cuotas.",
        "• Anthropic: la inteligencia artificial de Argos, que recibe tu pregunta y el contexto necesario para responderla.",
        "• Google (Gmail) y Meta (WhatsApp): el envío de emails y mensajes, cuando se usan."
    ),
    "6. Qué ven los demás socios" to listOf(
        "En la Clasificación aparecen tu nombre y tus rangos; podés ocultarte en Configuración → Privacidad. Tus compañeros de entrenamiento ven los días que entrenaron juntos. Tu condición médica, tus fotos, tus pagos y tus comidas nunca se muestran a otros socios. Dentro del gimnasio solo los ve el personal que los necesita para su trabajo."
    ),
    "7. Cómo los protegemos" to listOf(
        "• Toda la información viaja cifrada (HTTPS).",
        "• Cada socio puede ver y cambiar solo sus propios datos: el servidor comprueba quién sos en cada pedido.",
        "• Las contraseñas nunca se guardan en texto.",
        "• Cada empleado ve solo las secciones de su puesto."
    ),
    "8. Cuánto tiempo los guardamos" to listOf(
        "Mientras seas socio. Si te das de baja y lo pedís, borramos tu cuenta y tus datos. Los registros de pagos se conservan el tiempo que exige la ley contable."
    ),
    "9. Tus derechos" to listOf(
        "• Acceso: podés pedir gratis, cada seis meses, qué datos tenemos tuyos (salvo que tengas un interés legítimo para pedirlo antes). Respondemos dentro de los 10 días corridos.",
        "• Rectificación y actualización: la mayoría los podés corregir en la app (Configuración); el resto, en la recepción.",
        "• Supresión: podés pedir que borremos tus datos. Rectificación y supresión se resuelven dentro de los 5 días hábiles.",
        "Para cualquiera de estos pedidos escribí a contacto@olimpos.com o acercate a la recepción."
    ),
    "10. Cambios a esta política" to listOf(
        "Si cambia algo importante, lo avisamos en la app y en el Tablón del club antes de que empiece a regir."
    )
)

private const val LEYENDA_AAIP = "LA AGENCIA DE ACCESO A LA INFORMACIÓN PÚBLICA, en su carácter de Órgano de Control de la " +
    "Ley N° 25.326, tiene la atribución de atender las denuncias y reclamos que interpongan quienes resulten afectados en " +
    "sus derechos por incumplimiento de las normas vigentes en materia de protección de datos personales."

@Composable
fun PoliticaPrivacidadScreen(onVolver: () -> Unit) {
    Column(Modifier.fillMaxSize().background(Olimpos.FondoA).verticalScroll(rememberScrollState())) {
        EncabezadoVolver("Política de privacidad", "Vigente desde el 27 de octubre de 2026", onVolver)
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 32.dp)) {
            Text(
                "Esta política explica qué datos personales trata OLIMPOS GYM a través de su app móvil, su sistema de gestión " +
                    "y su sitio web, para qué los usa y cómo podés ejercer tus derechos. Se rige por la Ley 25.326 de " +
                    "Protección de los Datos Personales de la República Argentina.",
                fontSize = 13.sp, color = Olimpos.Muted, lineHeight = 20.sp
            )
            SECCIONES_POLITICA.forEach { (titulo, parrafos) ->
                Spacer(Modifier.height(20.dp))
                Text(titulo, fontSize = 14.5.sp, fontWeight = FontWeight.SemiBold, color = Olimpos.Cream)
                parrafos.forEach {
                    Spacer(Modifier.height(6.dp))
                    Text(it, fontSize = 13.sp, color = Olimpos.Muted, lineHeight = 20.sp)
                }
            }
            Spacer(Modifier.height(24.dp))
            Text(
                LEYENDA_AAIP, fontSize = 11.5.sp, color = Olimpos.Muted, lineHeight = 18.sp,
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, Olimpos.Line, RoundedCornerShape(12.dp))
                    .padding(14.dp)
            )
        }
    }
}
