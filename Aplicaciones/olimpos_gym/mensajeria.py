# OLIMPOS GYM — Envío de emails y mensajes de WhatsApp
#
# Dos canales, cada uno con un modo automático (si hay credenciales) y un
# modo que funciona siempre:
#
#   EMAIL
#     automático: SMTP (por ejemplo, la cuenta de Gmail del gimnasio con una
#                 "contraseña de aplicación"). Se configura en Configuración.
#     sin configurar: para la contraseña de un SOCIO, Firebase manda su propio
#                 email de recuperación (gratis, ver auth_repo). Para todo lo
#                 demás, avisa que falta configurar el email.
#
#   WHATSAPP
#     automático: WhatsApp Business Cloud API (Meta). Necesita un número que
#                 NO esté en uso en la app de WhatsApp, un token y el
#                 "phone number id". Los mensajes que inicia el gimnasio tienen
#                 que usar PLANTILLAS aprobadas por Meta (ver PLANTILLAS abajo).
#     sin configurar: abre WhatsApp Web/Desktop con el mensaje ya escrito
#                 (link wa.me) y el empleado solo toca "Enviar". Gratis.
#
# Las credenciales viven en mensajeria_credentials.json (fuera de git, igual
# que las demás credenciales del proyecto).

import json
import os
import re
import smtplib
import ssl
import urllib.parse
from email.message import EmailMessage
from email.utils import formataddr

import requests

CRED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mensajeria_credentials.json")
NOMBRE_GYM = "OlimpΩs Gym"

# Plantillas de WhatsApp (se crean y aprueban en Meta → WhatsApp Manager →
# Plantillas de mensajes, en español). Cada {{n}} es un parámetro.
PLANTILLAS = {
    "acceso_app": ("olimpos_acceso_app",
                   "Hola {{1}}! Ya está listo tu acceso a la app OlimpΩs. Email: {{2}} · Contraseña: {{3}}. "
                   "La primera vez que entres te va a pedir que la cambies."),
    "recuperar_password": ("olimpos_recuperar_password",
                           "Hola {{1}}! Para elegir una contraseña nueva de la app OlimpΩs entrá a este link: {{2}} "
                           "(vence en 1 hora). Si no lo pediste, ignorá este mensaje."),
    "password_temporal": ("olimpos_password_temporal",
                          "Hola {{1}}! Tu nueva contraseña temporal de OlimpΩs es {{2}}. "
                          "Al entrar te va a pedir que la cambies."),
    "recordatorio_cuota": ("olimpos_recordatorio_cuota",
                           "Hola {{1}}! Te recordamos que tu plan {{2}} de OlimpΩs {{3}}. "
                           "El valor es {{4}}. Podés pagar en recepción o desde la app."),
    "acceso_sistema": ("olimpos_acceso_sistema",
                       "Hola {{1}}! Tus datos para entrar al sistema de OlimpΩs: usuario {{2}} · contraseña {{3}}. "
                       "No se los pases a nadie."),
    "codigo_empleado": ("olimpos_codigo_empleado",
                        "Tu código para restablecer la contraseña del sistema OlimpΩs es {{1}}. Vence en 15 minutos."),
}


# ── credenciales ──
def credenciales() -> dict:
    try:
        with open(CRED_PATH, encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def guardar_credenciales(datos: dict) -> None:
    with open(CRED_PATH, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def email_configurado() -> bool:
    e = credenciales().get("email") or {}
    return bool(e.get("usuario") and e.get("password") and e.get("servidor"))


def whatsapp_configurado() -> bool:
    w = credenciales().get("whatsapp") or {}
    return bool(w.get("token") and w.get("phone_number_id"))


# ── teléfonos ──
def telefono_internacional(telefono: str) -> str | None:
    """Número para WhatsApp en formato internacional sin "+" (Argentina por
    defecto): "11 2233-4455" → "5491122334455", "0351 15 444-5555" → "5493514445555".
    None si no parece un número válido."""
    d = re.sub(r"\D", "", telefono or "")
    if not d:
        return None
    internacional = (telefono or "").strip().startswith("+") or d.startswith("00")
    if d.startswith("00"):
        d = d[2:]
    if d.startswith("54") and (internacional or len(d) >= 12):
        resto = d[2:]
        if resto.startswith("9"):
            resto = resto[1:]
    elif internacional:                                   # otro código de país: se deja como está
        return d if 8 <= len(d) <= 15 else None
    else:
        resto = d                                         # número argentino sin código de país
    resto = resto.lstrip("0")
    # "15" después del código de área (formato viejo de celular): se saca
    for largo_area in (2, 3, 4):
        if len(resto) == 12 and resto[largo_area:largo_area + 2] == "15":
            resto = resto[:largo_area] + resto[largo_area + 2:]
            break
    if len(resto) != 10:
        return None
    return "549" + resto


def link_whatsapp(telefono: str, texto: str) -> str | None:
    numero = telefono_internacional(telefono)
    if not numero:
        return None
    return f"https://wa.me/{numero}?text={urllib.parse.quote(texto)}"


# ── email ──
def _html(asunto: str, texto: str) -> str:
    parrafos = "".join(f"<p style='margin:0 0 12px'>{_escapar(p)}</p>" for p in texto.split("\n\n"))
    parrafos = re.sub(r"(https?://[^\s<]+)", r"<a href='\1' style='color:#A07820'>\1</a>", parrafos)
    return (
        "<div style='background:#FAFAF0;padding:24px;font-family:Arial,sans-serif'>"
        "<div style='max-width:520px;margin:auto;background:#fff;border:1px solid #E8E5D8;border-radius:14px;padding:24px'>"
        f"<div style='font-size:18px;font-weight:bold;color:#1F1D16;margin-bottom:4px'>{NOMBRE_GYM}</div>"
        f"<div style='font-size:15px;color:#A07820;margin-bottom:18px'>{_escapar(asunto)}</div>"
        f"<div style='font-size:14px;color:#1F1D16;line-height:1.5'>{parrafos}</div>"
        "<div style='font-size:11px;color:#888570;margin-top:18px'>Este mensaje lo envió el sistema del gimnasio.</div>"
        "</div></div>")


def _escapar(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")


def enviar_email(destino: str, asunto: str, texto: str) -> tuple[bool, str]:
    """(ok, detalle). No lanza excepciones: el detalle explica qué pasó."""
    cfg = credenciales().get("email") or {}
    if not email_configurado():
        return False, "El email no está configurado (Configuración → Mensajes)."
    if not destino or "@" not in destino:
        return False, "No hay un email válido al que enviar."
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = formataddr((cfg.get("remitente") or NOMBRE_GYM, cfg["usuario"]))
    msg["To"] = destino
    msg.set_content(texto)
    msg.add_alternative(_html(asunto, texto), subtype="html")
    try:
        puerto = int(cfg.get("puerto") or 587)
        if puerto == 465:
            with smtplib.SMTP_SSL(cfg["servidor"], puerto, context=ssl.create_default_context(), timeout=20) as s:
                s.login(cfg["usuario"], cfg["password"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg["servidor"], puerto, timeout=20) as s:
                s.starttls(context=ssl.create_default_context())
                s.login(cfg["usuario"], cfg["password"])
                s.send_message(msg)
        return True, f"Email enviado a {destino}."
    except smtplib.SMTPAuthenticationError:
        return False, "El servidor de email rechazó el usuario o la contraseña (en Gmail hay que usar una contraseña de aplicación)."
    except (OSError, smtplib.SMTPException) as e:
        return False, f"No se pudo enviar el email: {e}"


# ── WhatsApp Cloud API ──
def enviar_whatsapp(telefono: str, clave_plantilla: str, parametros: list[str]) -> tuple[bool, str]:
    """Manda una plantilla aprobada por la Cloud API. (ok, detalle)."""
    cfg = credenciales().get("whatsapp") or {}
    if not whatsapp_configurado():
        return False, "sin_api"
    numero = telefono_internacional(telefono)
    if not numero:
        return False, "El teléfono no es válido para WhatsApp."
    nombre, _ = PLANTILLAS[clave_plantilla]
    cuerpo = {
        "messaging_product": "whatsapp", "to": numero, "type": "template",
        "template": {
            "name": cfg.get("plantillas", {}).get(clave_plantilla, nombre),
            "language": {"code": cfg.get("idioma") or "es_AR"},
            "components": [{"type": "body", "parameters": [{"type": "text", "text": str(p)} for p in parametros]}],
        },
    }
    try:
        r = requests.post(
            f"https://graph.facebook.com/{cfg.get('version') or 'v21.0'}/{cfg['phone_number_id']}/messages",
            headers={"Authorization": f"Bearer {cfg['token']}"}, json=cuerpo, timeout=20)
    except requests.RequestException as e:
        return False, f"No se pudo conectar con WhatsApp: {e}"
    if r.ok:
        return True, f"WhatsApp enviado al {numero}."
    try:
        error = r.json().get("error", {}).get("message", r.text)
    except ValueError:
        error = r.text
    return False, f"WhatsApp rechazó el mensaje: {error}"


def texto_plantilla(clave: str, parametros: list[str]) -> str:
    """El mismo texto de la plantilla con los parámetros puestos (para el link wa.me)."""
    _, texto = PLANTILLAS[clave]
    for i, p in enumerate(parametros, start=1):
        texto = texto.replace("{{" + str(i) + "}}", str(p))
    return texto


def whatsapp(page, telefono: str, clave_plantilla: str, parametros: list[str]) -> tuple[bool, str]:
    """Lo que usan las pantallas: por la API si está configurada; si no, abre
    WhatsApp con el mensaje escrito (el empleado toca "Enviar")."""
    if whatsapp_configurado():
        return enviar_whatsapp(telefono, clave_plantilla, parametros)
    link = link_whatsapp(telefono, texto_plantilla(clave_plantilla, parametros))
    if not link:
        return False, "El teléfono no es válido para WhatsApp."
    page.launch_url(link)
    return True, "Se abrió WhatsApp con el mensaje escrito: tocá Enviar."
