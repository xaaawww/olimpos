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

SIDEBAR_W = 220

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
            {"sep": "Entrenamiento"},
            {"s": "rutinas", "i": "📋", "l": "Rutinas"},
            {"s": "editor-ejercicios", "i": "🏋️", "l": "Editor Visual de Ejercicios"},
            {"s": "verificacion-marcas", "i": "🏆", "l": "Verificación de Marcas"},
            {"s": "dietas", "i": "🥗", "l": "Dietas"},
            {"s": "editor-dietas", "i": "🖼️", "l": "Editor Visual de Dietas"},
            {"s": "progreso", "i": "📊", "l": "Progreso Físico"},
            {"sep": "Administración"},
            {"s": "membresias", "i": "💳", "l": "Membresías"},
            {"s": "pagos", "i": "💰", "l": "Pagos"},
            {"s": "reportes", "i": "📈", "l": "Reportes"},
            {"s": "stock", "i": "📦", "l": "Stock"},
            {"sep": "Seguridad"},
            {"s": "camaras", "i": "📷", "l": "Cámaras"},
            {"sep": "Sistema"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones", "b": "5"},
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
            {"s": "dietas", "i": "🥗", "l": "Planes Nutricionales"},
            {"sep": "Administración"},
            {"s": "membresias", "i": "💳", "l": "Membresías"},
            {"s": "pagos", "i": "💰", "l": "Pagos"},
            {"s": "reportes", "i": "📈", "l": "Reportes"},
            {"s": "stock", "i": "📦", "l": "Stock"},
            {"sep": "Sistema"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones", "b": "3"},
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
            {"s": "editor-ejercicios", "i": "🏋️", "l": "Editor Visual de Ejercicios"},
            {"s": "verificacion-marcas", "i": "🏆", "l": "Verificación de Marcas"},
            {"s": "progreso", "i": "📊", "l": "Progreso Físico"},
            {"sep": "Sistema"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones", "b": "2"},
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
            {"s": "dietas", "i": "🥗", "l": "Planes Nutricionales"},
            {"s": "editor-dietas", "i": "🖼️", "l": "Editor Visual de Dietas"},
            {"s": "progreso", "i": "📊", "l": "Progreso Físico"},
            {"sep": "Sistema"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones", "b": "1"},
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
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones", "b": "1"},
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
            {"sep": "Administración"},
            {"s": "membresias", "i": "💳", "l": "Membresías"},
            {"s": "pagos", "i": "💰", "l": "Pagos"},
            {"sep": "Sistema"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones", "b": "4"},
        ],
    },
    "socio": {
        "label": "Socio",
        "name": "Martín López",
        "initials": "ML",
        "nav": [
            {"s": "dashboard", "i": "🏠", "l": "Inicio"},
            {"sep": "Mi Espacio"},
            {"s": "mi-perfil", "i": "👤", "l": "Mi Perfil"},
            {"s": "mi-rutina", "i": "📋", "l": "Mi Rutina"},
            {"s": "mi-dieta", "i": "🥗", "l": "Mi Dieta"},
            {"s": "mi-progreso", "i": "📊", "l": "Mi Progreso"},
            {"sep": "Cuenta"},
            {"s": "pagos", "i": "💳", "l": "Mis Pagos"},
            {"s": "notificaciones", "i": "🔔", "l": "Notificaciones", "b": "2"},
        ],
    },
}

TITLES = {
    "dashboard": "Dashboard",
    "mi-perfil": "Mi Perfil",
    "socios": "Socios",
    "personal": "Personal",
    "asistencia": "Asistencia",
    "rutinas": "Rutinas",
    "mi-rutina": "Mi Rutina",
    "dietas": "Planes Nutricionales",
    "editor-dietas": "Editor Visual de Dietas",
    "editor-ejercicios": "Editor Visual de Ejercicios",
    "verificacion-marcas": "Verificación de Marcas",
    "membresias": "Asignación de Membresías",
    "mi-dieta": "Mi Dieta",
    "progreso": "Progreso Físico",
    "mi-progreso": "Mi Progreso",
    "pagos": "Pagos",
    "reportes": "Reportes",
    "notificaciones": "Notificaciones",
    "camaras": "Cámaras",
    "stock": "Stock",
    "configuracion": "Configuración",
}

# Dashboard data per role
DASH_STATS = {
    "socio": [
        ("Mi Plan", "Premium", "Anual", "gold"),
        ("Vencimiento", "30/12", "✓ Al día", "green"),
        ("Mi asistencia", "87%", "▲ Excelente", "green"),
        ("Semanas activas", "6", "Consecutivas", "blue"),
    ],
    "entrenador": [
        ("Mis socios", "22", "▲ +2 nuevos", "green"),
        ("Clases hoy", "3", "Programadas", "gold"),
        ("Rutinas activas", "18", "▲ +4", "green"),
        ("Asistencia hoy", "67", "↗ Pico 18h", "blue"),
    ],
    "nutricionista": [
        ("Mis socios", "24", "Con plan activo", "green"),
        ("Planes creados", "4", "Templates", "gold"),
        ("Consultas esta sem.", "8", "▲ +2", "green"),
        ("Progreso promedio", "78%", "Objetivos OK", "blue"),
    ],
    "seguridad": [
        ("Personas en el gym", "23", "Ahora", "gold"),
        ("Ingresos hoy", "67", "▲ +8 vs ayer", "green"),
        ("Cámaras activas", "8/8", "✓ OK", "green"),
        ("Alertas hoy", "0", "✓ Sin incidentes", "green"),
    ],
    "recepcionista": [
        ("Ingresos hoy", "67", "▲ +8", "green"),
        ("Socios activos", "219", "Total", "gold"),
        ("Pagos hoy", "8", "$68.000", "green"),
        ("Cuotas vencidas", "3", "⚠️ Urgente", "red"),
    ],
    "dueno": [
        ("Socios Activos", "248", "▲ +4 esta semana", "green"),
        ("Ingresos del Mes", "$84k", "▲ +12.4%", "green"),
        ("Asistencia Hoy", "67", "↗ Pico a las 18h", "blue"),
        ("Personal Activo", "11", "3 turnos hoy", "gold"),
    ],
    "admin": [
        ("Socios Activos", "248", "▲ +4 esta semana", "green"),
        ("Ingresos del Mes", "$84k", "▲ +12.4%", "green"),
        ("Asistencia Hoy", "67", "↗ Pico a las 18h", "blue"),
        ("Personal Activo", "11", "3 turnos hoy", "gold"),
    ],
}
