import flet as ft
from theme import *
from components import stat_card, section_card, status_pill, avatar, action_button, page_header


# ─────────────────────────────────────────────
# PERSONAL
# ─────────────────────────────────────────────
PERSONAL_DATA = [
    ("CR", "gold",   "Carlos Rodríguez",  "carlos@olimpos.com",  "🏋️ Entrenador",   "Mañana y tarde",  "Musculación & Fuerza"),
    ("LM", "purple", "Laura Méndez",      "laura@olimpos.com",   "🏋️ Entrenadora",  "Mañana",          "Cardio & Yoga"),
    ("DP", "blue",   "Diego Peralta",     "diego@olimpos.com",   "🏋️ Entrenador",   "Tarde y noche",   "CrossFit & HIIT"),
    ("SV", "green",  "Sandra Villar",     "sandra@olimpos.com",  "🥗 Nutricionista", "Mañana",          "Deportiva & Clínica"),
    ("RF", "red",    "Roberto Flores",    "roberto@olimpos.com", "🔒 Seguridad",     "Noche",           "Control de acceso"),
    ("PA", "dark",   "Patricia Acosta",   "patricia@olimpos.com","📋 Recepcionista", "Mañana",          "Atención al socio"),
    ("AB", "gold",   "Ana Belén Castro",  "ana@olimpos.com",     "🏋️ Entrenadora",  "Tarde",           "Zumba & Aeróbicos"),
]


def build_personal() -> ft.Column:
    stats_row = ft.Row([
        stat_card("Entrenadores",  "4", "", "green", True),
        stat_card("Nutricionistas","2", "", "gold"),
        stat_card("Recepcionistas","3", "", "blue"),
        stat_card("Seguridad",     "2", "", "red"),
    ], spacing=16)

    header = ft.Container(
        content=ft.Row([
            ft.Text("EMPLEADO",    size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=3),
            ft.Text("ROL",         size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=2),
            ft.Text("TURNO",       size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=2),
            ft.Text("ESPECIALIDAD",size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=3),
            ft.Text("ESTADO",      size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=1),
        ], spacing=0),
        bgcolor=CREAM, padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT)),
    )

    def emp_row(init, var, name, email, rol, turno, esp):
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    avatar(init, var),
                    ft.Column([ft.Text(name, size=13, weight=ft.FontWeight.W_600),
                               ft.Text(email, size=11, color=TEXT_MUTED)], spacing=2),
                ], spacing=10, expand=3),
                ft.Text(rol, size=13, expand=2),
                ft.Text(turno, size=13, expand=2),
                ft.Text(esp, size=13, expand=3),
                ft.Container(content=status_pill("Activo", "active"), expand=1),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
        )

    table = section_card(
        ft.Column([header, ft.Column([emp_row(*e) for e in PERSONAL_DATA], spacing=0)], spacing=0),
        padding=0
    )

    return ft.Column([
        page_header("👨‍💼 Personal", "11 empleados registrados en el sistema",
                    actions=[action_button("➕ Agregar empleado", "gold")]),
        stats_row, table,
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


# ─────────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# PROGRESO
# ─────────────────────────────────────────────
def build_progreso() -> ft.Column:
    metrics = [
        ("Peso actual", "78 kg", "▼ -2.5 kg", "green"),
        ("% Grasa corporal", "18%", "▼ -3.2%", "green"),
        ("Masa muscular", "62 kg", "▲ +1.8 kg", "green"),
        ("IMC", "24.1", "Peso saludable", "blue"),
    ]
    stats_row = ft.Row([stat_card(m[0], m[1], m[2], m[3], i == 0)
                        for i, m in enumerate(metrics)], spacing=16)

    # Progress bars
    progress_items = [
        ("Objetivo de peso", 0.75, GOLD),
        ("Reducción de grasa", 0.60, GREEN),
        ("Ganancia muscular", 0.80, BLUE),
        ("Asistencia mensual", 0.87, GOLD),
    ]

    bars = ft.Column([
        ft.Column([
            ft.Row([
                ft.Text(label, size=12, weight=ft.FontWeight.W_500),
                ft.Text(f"{int(val*100)}%", size=12, weight=ft.FontWeight.W_500),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(
                content=ft.Container(
                    bgcolor=color, border_radius=3,
                    width=val, height=6,
                ),
                bgcolor=GRAY_LIGHT, border_radius=3, height=6,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
        ], spacing=5)
        for label, val, color in progress_items
    ], spacing=14)

    progress_card = section_card(ft.Column([
        ft.Text("📊 Objetivos", size=14, weight=ft.FontWeight.W_500, font_family="Poppins"),
        ft.Container(height=10),
        bars,
    ], spacing=0))

    # Measurements
    measures = [
        ("Fecha", "Peso", "Grasa%", "Músculo"),
        ("01/11/2025", "80.5 kg", "21.2%", "60.2 kg"),
        ("15/11/2025", "79.2 kg", "20.1%", "61.0 kg"),
        ("01/12/2025", "78.0 kg", "18.0%", "62.0 kg"),
    ]
    header = ft.Container(
        content=ft.Row([ft.Text(h, size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=1)
                        for h in measures[0]], spacing=0),
        bgcolor=CREAM, padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT)),
    )
    rows = [
        ft.Container(
            content=ft.Row([ft.Text(v, size=13, expand=1) for v in r], spacing=0),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
        ) for r in measures[1:]
    ]
    history_card = section_card(
        ft.Column([
            ft.Container(content=ft.Text("📅 Historial de mediciones", size=14,
                                          weight=ft.FontWeight.W_500, font_family="Poppins"),
                         padding=ft.padding.only(left=14, right=14, top=16, bottom=4)),
            header, ft.Column(rows, spacing=0),
        ], spacing=0), padding=0
    )

    return ft.Column([
        page_header("📊 Progreso Físico", "Seguimiento de evolución y métricas"),
        stats_row,
        ft.Row([progress_card, history_card], spacing=16,
               vertical_alignment=ft.CrossAxisAlignment.START),
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


# ─────────────────────────────────────────────
# PAGOS
# ─────────────────────────────────────────────
def build_pagos() -> ft.Column:
    stats_row = ft.Row([
        stat_card("Ingresos del mes", "$84.000", "▲ +12%", "green", True),
        stat_card("Pagos hoy",         "8",       "$68.000", "gold"),
        stat_card("Cuotas vencidas",   "3",       "⚠️ Urgente", "red"),
        stat_card("Socios al día",     "216",     "87.5%", "blue"),
    ], spacing=16)

    payments = [
        ("ML", "gold",   "Martín López",   "Premium Anual",    "04/11/2025", "$12.500", "Transferencia", "✅ Pagado"),
        ("AG", "blue",   "Ana González",   "Estándar Mensual", "04/11/2025", "$8.500",  "Efectivo",     "✅ Pagado"),
        ("LT", "purple", "Lucía Torres",   "Premium Anual",    "03/11/2025", "$12.500", "Tarjeta",      "✅ Pagado"),
        ("PS", "red",    "Pablo Suárez",   "Mensual Básico",   "07/11/2025", "$6.000",  "—",            "⚠️ Vencido"),
        ("JR", "green",  "Juan Rodríguez", "Estándar Mensual", "02/11/2025", "$8.500",  "Transferencia","✅ Pagado"),
    ]

    header = ft.Container(
        content=ft.Row([
            ft.Text("SOCIO",      size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=3),
            ft.Text("PLAN",       size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=2),
            ft.Text("FECHA",      size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=2),
            ft.Text("MONTO",      size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=1),
            ft.Text("MÉTODO",     size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=2),
            ft.Text("ESTADO",     size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=1),
        ], spacing=0),
        bgcolor=CREAM, padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT)),
    )

    def pago_row(init, var, name, plan, fecha, monto, metodo, estado):
        is_paid = "Pagado" in estado
        return ft.Container(
            content=ft.Row([
                ft.Row([avatar(init, var),
                        ft.Text(name, size=13, weight=ft.FontWeight.W_600)],
                       spacing=10, expand=3),
                ft.Text(plan,   size=13, expand=2),
                ft.Text(fecha,  size=13, expand=2),
                ft.Text(monto, size=13, weight=ft.FontWeight.W_500, color=GOLD_DARK, expand=1),
                ft.Text(metodo, size=13, expand=2),
                ft.Container(
                    content=ft.Text(estado, size=11, weight=ft.FontWeight.W_600,
                                    color=BADGE_GREEN_TEXT if is_paid else BADGE_RED_TEXT),
                    bgcolor=BADGE_GREEN_BG if is_paid else BADGE_RED_BG,
                    border_radius=20, padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    expand=1,
                ),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
        )

    table = section_card(
        ft.Column([header, ft.Column([pago_row(*p) for p in payments], spacing=0)], spacing=0),
        padding=0
    )

    return ft.Column([
        page_header("💰 Pagos", "Registro de pagos y cuotas",
                    actions=[action_button("➕ Registrar Pago", "gold")]),
        stats_row, table,
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


# ─────────────────────────────────────────────
# CAMARAS
# ─────────────────────────────────────────────
def build_camaras() -> ft.Column:
    cameras = [
        ("Cam 01", "Entrada Principal"), ("Cam 02", "Sala Musculación"),
        ("Cam 03", "Cardio Zone"),       ("Cam 04", "Recepción"),
        ("Cam 05", "Estacionamiento"),   ("Cam 06", "Vestuario Acceso"),
        ("Cam 07", "Patio Funcional"),   ("Cam 08", "Sala CrossFit"),
    ]

    def cam_box(cam_id, location):
        return ft.Container(
            content=ft.Stack([
                ft.Container(
                    content=ft.Text("📹", size=32),
                    alignment=ft.Alignment.CENTER,
                    bgcolor="#0a0800",
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(f"{cam_id} — {location}", size=10, weight=ft.FontWeight.W_600,
                                            color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE)),
                            bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
                            border_radius=6, padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            alignment=ft.Alignment.CENTER_LEFT,
                        ),
                        ft.Container(expand=True),
                        ft.Row([
                            ft.Container(width=6, height=6, bgcolor=RED, border_radius=3),
                            ft.Text("LIVE", size=9, weight=ft.FontWeight.W_600,
                                    color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE)),
                        ], spacing=4),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=8,
                    expand=True,
                ),
            ]),
            bgcolor="#0a0800",
            border_radius=12,
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.15, GOLD)),
            height=120,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    grid_rows = []
    for i in range(0, len(cameras), 3):
        chunk = cameras[i:i+3]
        grid_rows.append(ft.Row([cam_box(*c) for c in chunk], spacing=12, expand=True))

    stats_row = ft.Row([
        stat_card("Cámaras activas",  "8/8", "✓ Todas OK",    "green", True),
        stat_card("Grabando",         "8",   "Almacenamiento 64%", "blue"),
        stat_card("Alertas hoy",      "0",   "✓ Sin incidentes",   "green"),
    ], spacing=16)

    cam_grid = section_card(
        ft.Column([
            ft.Text("📷 Feed en vivo", size=14, weight=ft.FontWeight.W_500, font_family="Poppins"),
            ft.Container(height=10),
            ft.Column(grid_rows, spacing=12),
        ], spacing=0)
    )

    return ft.Column([
        page_header("📷 Cámaras", "Sistema de videovigilancia — 8 cámaras activas"),
        stats_row, cam_grid,
    ], spacing=16, scroll=ft.ScrollMode.AUTO)
