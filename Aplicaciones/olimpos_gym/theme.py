# OLIMPOS GYM — Color Theme & Shared Styles

GOLD       = "#C9A227"
GOLD_LIGHT = "#F0D060"
GOLD_DARK  = "#A07820"
GOLD_BG    = "#FFFDE8"
GOLD_BG2   = "#FEF9C3"

DARK       = "#0d0b00"
DARK2      = "#1a1500"
DARK3      = "#252100"

CREAM      = "#FAFAF0"
WHITE      = "#FFFFFF"
GRAY_LIGHT = "#E8E5D8"
GRAY       = "#C0BAA0"
TEXT_MUTED = "#888570"

GREEN      = "#22C55E"
RED        = "#EF4444"
BLUE       = "#3B82F6"

# Badge background/text combos
BADGE_GREEN_BG   = "#DCFCE7"
BADGE_GREEN_TEXT = "#16A34A"
BADGE_RED_BG     = "#FEE2E2"
BADGE_RED_TEXT   = "#DC2626"
BADGE_GOLD_BG    = GOLD_BG2
BADGE_GOLD_TEXT  = GOLD_DARK
BADGE_BLUE_BG    = "#DBEAFE"
BADGE_BLUE_TEXT  = "#1D4ED8"

SIDEBAR_W = 250
SIDEBAR_W_COMPACTO = 76
SIDEBAR_BG = "#FBFAF6"
NAV_ACTIVO_BG = "#F7EDC4"
NAV_TEXTO = "#3F3B30"   # secciones no elegidas: un poco más suaves que el negro
NAV_ICONO = "#6B6656"

# ── Apariencia elegida por el empleado (Configuración → Apariencia) ──
# Color de acento: (principal, claro, oscuro, fondo suave, fondo chip, menú activo)
PALETAS = {
    "dorado":  ("Dorado",  "#C9A227", "#F0D060", "#A07820", "#FFFDE8", "#FEF9C3", "#F7EDC4"),
    "azul":    ("Azul",    "#3B82F6", "#93C5FD", "#1D4ED8", "#F0F6FF", "#DBEAFE", "#DCE8FD"),
    "verde":   ("Verde",   "#16A34A", "#86EFAC", "#15803D", "#F0FBF3", "#DCFCE7", "#D5F3DF"),
    "violeta": ("Violeta", "#7C3AED", "#C4B5FD", "#6D28D9", "#F7F3FF", "#EDE9FE", "#E6DEFC"),
    "coral":   ("Coral",   "#F97352", "#FDBA9F", "#C2410C", "#FFF6F2", "#FFEDD5", "#FDE1D6"),
}
# Fondo: (área de contenido, menú lateral)
FONDOS = {
    "crema":  ("Crema",       "#FAFAF0", "#FBFAF6"),
    "blanco": ("Blanco",      "#FFFFFF", "#FAFAFA"),
    "gris":   ("Gris suave",  "#F3F4F6", "#F9FAFB"),
}


def _aplicar_apariencia():
    global GOLD, GOLD_LIGHT, GOLD_DARK, GOLD_BG, GOLD_BG2, NAV_ACTIVO_BG, BADGE_GOLD_BG, BADGE_GOLD_TEXT
    global CREAM, SIDEBAR_BG
    try:
        import configuracion_repo
        prefs = configuracion_repo.preferencias()
    except Exception:
        return
    paleta = PALETAS.get(prefs.get("acento"), PALETAS["dorado"])
    _, GOLD, GOLD_LIGHT, GOLD_DARK, GOLD_BG, GOLD_BG2, NAV_ACTIVO_BG = paleta
    BADGE_GOLD_BG, BADGE_GOLD_TEXT = GOLD_BG2, GOLD_DARK
    _, CREAM, SIDEBAR_BG = FONDOS.get(prefs.get("fondo"), FONDOS["crema"])


_aplicar_apariencia()

# Ícono de línea de cada sección del menú (en vez de emojis).
import flet as _ft
ICONOS_NAV = {
    "dashboard": _ft.Icons.HOME_OUTLINED,
    "socios": _ft.Icons.PEOPLE_OUTLINE,
    "personal": _ft.Icons.BADGE_OUTLINED,
    "asistencia": _ft.Icons.CALENDAR_MONTH_OUTLINED,
    "qr-ingreso": _ft.Icons.QR_CODE_2,
    "rutinas": _ft.Icons.FORMAT_LIST_BULLETED,
    "editor-ejercicios": _ft.Icons.FITNESS_CENTER,
    "verificacion-marcas": _ft.Icons.EMOJI_EVENTS_OUTLINED,
    "asignar-dietas": _ft.Icons.RESTAURANT,
    "editor-dietas": _ft.Icons.RESTAURANT_MENU,
    "progreso": _ft.Icons.SHOW_CHART,
    "membresias": _ft.Icons.CARD_MEMBERSHIP,
    "pagos": _ft.Icons.PAYMENTS_OUTLINED,
    "tablon": _ft.Icons.PUSH_PIN_OUTLINED,
    "notificaciones": _ft.Icons.NOTIFICATIONS_NONE,
    "camaras": _ft.Icons.VIDEOCAM_OUTLINED,
    "configuracion": _ft.Icons.SETTINGS_OUTLINED,
    "argos": _ft.Icons.AUTO_AWESOME_OUTLINED,
}

# Role data
ROLES = {
    "dueno": {
        "label": "Dueño",
        "name": "Carlos García",
        "initials": "CG",
        "nav": [
            {"s": "dashboard", "i": "🏠", "l": "Dashboard"},
            {"sep": "Socios"},
            {"s": "socios", "i": "👥", "l": "Socios"},
            {"sep": "Personal & Clases"},
            {"s": "personal", "i": "👨‍💼", "l": "Personal"},
            {"s": "asistencia", "i": "📅", "l": "Asistencia"},
            {"s": "qr-ingreso", "i": "🔳", "l": "QR de entrada"},
            {"sep": "Entrenamiento"},
            {"s": "rutinas", "i": "📋", "l": "Rutinas"},
            {"s": "editor-ejercicios", "i": "🏋️", "l": "Ejercicios"},
            {"s": "verificacion-marcas", "i": "🏆", "l": "Verificación de Marcas"},
            {"s": "asignar-dietas", "i": "🍽️", "l": "Asignar Dietas"},
            {"s": "editor-dietas", "i": "🖼️", "l": "Dietas"},
            {"s": "progreso", "i": "📊", "l": "Progreso Físico"},
            {"sep": "Administración"},
            {"s": "membresias", "i": "💳", "l": "Membresías"},
            {"s": "pagos", "i": "💰", "l": "Pagos"},
            {"sep": "Comunicación"},
            {"s": "tablon", "i": "📌", "l": "Tablón del club"},
            {"sep": "Seguridad"},
            {"s": "camaras", "i": "📷", "l": "Cámaras"},
            {"sep": "Sistema"},
            {"s": "argos", "i": "🐕", "l": "Argos (Asistente IA)"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones"},
            {"s": "configuracion", "i": "⚙️", "l": "Configuración"},
        ],
    },
    "admin": {
        "label": "Administrador",
        "name": "Sofía Ramírez",
        "initials": "SR",
        "nav": [
            {"s": "dashboard", "i": "🏠", "l": "Dashboard"},
            {"sep": "Socios"},
            {"s": "socios", "i": "👥", "l": "Socios"},
            {"sep": "Personal"},
            {"s": "personal", "i": "👨‍💼", "l": "Personal"},
            {"s": "asistencia", "i": "📅", "l": "Asistencia"},
            {"sep": "Nutrición"},
            {"s": "asignar-dietas", "i": "🍽️", "l": "Asignar Dietas"},
            {"s": "editor-dietas", "i": "🖼️", "l": "Dietas"},
            {"sep": "Administración"},
            {"s": "membresias", "i": "💳", "l": "Membresías"},
            {"s": "pagos", "i": "💰", "l": "Pagos"},
            {"sep": "Sistema"},
            {"s": "argos", "i": "🐕", "l": "Argos (Asistente IA)"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones"},
            {"s": "configuracion", "i": "⚙️", "l": "Configuración"},
        ],
    },
    "entrenador": {
        "label": "Entrenador",
        "name": "Carlos Rodríguez",
        "initials": "CR",
        "nav": [
            {"s": "dashboard", "i": "🏠", "l": "Dashboard"},
            {"sep": "Mis Socios"},
            {"s": "socios", "i": "👥", "l": "Mis Socios"},
            {"s": "asistencia", "i": "📅", "l": "Asistencia"},
            {"sep": "Entrenamiento"},
            {"s": "rutinas", "i": "📋", "l": "Rutinas"},
            {"s": "editor-ejercicios", "i": "🏋️", "l": "Ejercicios"},
            {"s": "verificacion-marcas", "i": "🏆", "l": "Verificación de Marcas"},
            {"s": "progreso", "i": "📊", "l": "Progreso Físico"},
            {"sep": "Sistema"},
            {"s": "argos", "i": "🐕", "l": "Argos (Asistente IA)"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones"},
            {"s": "configuracion", "i": "⚙️", "l": "Configuración"},
        ],
    },
    "nutricionista": {
        "label": "Nutricionista",
        "name": "Sandra Villar",
        "initials": "SV",
        "nav": [
            {"s": "dashboard", "i": "🏠", "l": "Dashboard"},
            {"sep": "Mis Socios"},
            {"s": "socios", "i": "👥", "l": "Mis Socios"},
            {"sep": "Nutrición"},
            {"s": "asignar-dietas", "i": "🍽️", "l": "Asignar Dietas"},
            {"s": "editor-dietas", "i": "🖼️", "l": "Dietas"},
            {"s": "progreso", "i": "📊", "l": "Progreso Físico"},
            {"sep": "Sistema"},
            {"s": "argos", "i": "🐕", "l": "Argos (Asistente IA)"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones"},
            {"s": "configuracion", "i": "⚙️", "l": "Configuración"},
        ],
    },
    "seguridad": {
        "label": "Seguridad",
        "name": "Roberto Flores",
        "initials": "RF",
        "nav": [
            {"s": "dashboard", "i": "🏠", "l": "Dashboard"},
            {"sep": "Control"},
            {"s": "asistencia", "i": "📅", "l": "Control de Acceso"},
            {"s": "camaras", "i": "📷", "l": "Cámaras"},
            {"sep": "Sistema"},
            {"s": "argos", "i": "🐕", "l": "Argos (Asistente IA)"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones"},
            {"s": "configuracion", "i": "⚙️", "l": "Configuración"},
        ],
    },
    "recepcionista": {
        "label": "Recepcionista",
        "name": "Patricia Acosta",
        "initials": "PA",
        "nav": [
            {"s": "dashboard", "i": "🏠", "l": "Dashboard"},
            {"sep": "Socios"},
            {"s": "socios", "i": "👥", "l": "Socios"},
            {"s": "asistencia", "i": "📅", "l": "Asistencia"},
            {"s": "qr-ingreso", "i": "🔳", "l": "QR de entrada"},
            {"sep": "Administración"},
            {"s": "membresias", "i": "💳", "l": "Membresías"},
            {"s": "pagos", "i": "💰", "l": "Pagos"},
            {"sep": "Sistema"},
            {"s": "argos", "i": "🐕", "l": "Argos (Asistente IA)"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones"},
            {"s": "configuracion", "i": "⚙️", "l": "Configuración"},
        ],
    },
}

TITLES = {
    "dashboard": "Dashboard",
    "socios": "Socios",
    "personal": "Personal",
    "asistencia": "Asistencia",
    "qr-ingreso": "QR de entrada",
    "rutinas": "Rutinas",
    "editor-dietas": "Editor Visual de Dietas",
    "asignar-dietas": "Asignación de Dietas",
    "tablon": "Tablón del club",
    "editor-ejercicios": "Editor Visual de Ejercicios",
    "verificacion-marcas": "Verificación de Marcas",
    "membresias": "Asignación de Membresías",
    "progreso": "Progreso Físico",
    "pagos": "Pagos",
    "notificaciones": "Notificaciones",
    "camaras": "Cámaras",
    "configuracion": "Configuración",
    "argos": "Argos — Asistente IA",
}

