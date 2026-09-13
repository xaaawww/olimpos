import flet as ft
from theme import *
from components import stat_card, section_card, status_pill, avatar, action_button, page_header


SOCIOS_DATA = [
    ("ML", "gold",   "Martín López",     "#0248", "Premium Anual",    "30/12/2025", "92%", "green", "active",    "Activo"),
    ("AG", "blue",   "Ana González",     "#0247", "Estándar Mensual", "15/12/2025", "78%", "green", "active",    "Activo"),
    ("PS", "red",    "Pablo Suárez",     "#0243", "Mensual Básico",   "07/11/2025", "45%", "gold",  "debt",      "Deuda"),
    ("LT", "purple", "Lucía Torres",     "#0241", "Premium Anual",    "28/02/2026", "88%", "green", "active",    "Activo"),
    ("JR", "green",  "Juan Rodríguez",   "#0235", "Estándar Mensual", "20/12/2025", "62%", "gold",  "active",    "Activo"),
    ("MF", "gold",   "María Fernández",  "#0230", "Mensual Básico",   "01/12/2025", "28%", "red",   "inactive",  "Inactivo"),
    ("DC", "dark",   "Diego Castro",     "#0228", "Premium Anual",    "10/03/2026", "95%", "green", "active",    "Activo"),
    ("VP", "red",    "Valeria Pérez",    "#0225", "Estándar",         "—",          "—",   "gold",  "suspended", "Suspendida"),
]


def build_socios() -> ft.Column:
    stats_row = ft.Row([
        stat_card("Activos",       "219", "▲ +4",       "green", True),
        stat_card("Inactivos",     "18",  "▼ -2",       "red"),
        stat_card("Suspendidos",   "7",   "sin cambios", "gold"),
        stat_card("Nuevos (mes)",  "14",  "▲ +40%",     "blue"),
    ], spacing=16)

    # Tabs
    active_tab = ft.Ref[int]()

    def tab_btn(label, idx):
        is_active = idx == 0
        return ft.Container(
            content=ft.Text(label, size=12.5, weight=ft.FontWeight.W_700,
                            color=DARK if is_active else TEXT_MUTED, font_family="Poppins"),
            bgcolor=WHITE if is_active else ft.Colors.TRANSPARENT,
            border_radius=9,
            padding=ft.padding.symmetric(horizontal=18, vertical=8),
            shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.with_opacity(0.08, DARK)) if is_active else None,
            on_click=None, ink=True,
        )

    tabs = ft.Container(
        content=ft.Row([
            tab_btn("Todos", 0),
            tab_btn("Activos", 1),
            tab_btn("Inactivos", 2),
            tab_btn("Con deuda", 3),
            tab_btn("Nuevos", 4),
        ], spacing=4),
        bgcolor=CREAM,
        border_radius=12,
        border=ft.border.all(1.5, GRAY_LIGHT),
        padding=4,
    )

    # Table header
    header = ft.Container(
        content=ft.Row([
            ft.Text("SOCIO",       size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=3),
            ft.Text("PLAN",        size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=2),
            ft.Text("VENCIMIENTO", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=2),
            ft.Text("ASISTENCIA",  size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=1),
            ft.Text("ESTADO",      size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=1),
            ft.Text("ACCIONES",    size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=1),
        ], spacing=0),
        bgcolor=CREAM,
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT)),
    )

    def row(initials, av_var, name, num, plan, exp, asist, asist_var, status_var, status_lbl):
        venc_color = RED if exp.startswith("07/11") else DARK
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    avatar(initials, av_var),
                    ft.Column([
                        ft.Text(name, size=13, weight=ft.FontWeight.W_800),
                        ft.Text(num, size=11, color=TEXT_MUTED),
                    ], spacing=2),
                ], spacing=10, expand=3),
                ft.Text(plan, size=13, expand=2),
                ft.Text(exp, size=13, color=venc_color,
                        weight=ft.FontWeight.W_800 if exp.startswith("07/11") else ft.FontWeight.NORMAL,
                        expand=2),
                ft.Container(
                    content=ft.Text(asist, size=10.5, weight=ft.FontWeight.W_800,
                                    color={"green": BADGE_GREEN_TEXT, "red": BADGE_RED_TEXT,
                                           "gold": BADGE_GOLD_TEXT}.get(asist_var, DARK)),
                    bgcolor={"green": BADGE_GREEN_BG, "red": BADGE_RED_BG,
                             "gold": BADGE_GOLD_BG}.get(asist_var, CREAM),
                    border_radius=20, padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    expand=1,
                ) if asist != "—" else ft.Text("—", size=13, expand=1),
                ft.Container(content=status_pill(status_lbl, status_var), expand=1),
                ft.Container(
                    content=action_button("Ver perfil", "outline"),
                    expand=1,
                ),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
        )

    rows = [row(*s) for s in SOCIOS_DATA]

    table = section_card(
        ft.Column([header, ft.Column(rows, spacing=0)], spacing=0), padding=0
    )

    return ft.Column([
        page_header("👥 Socios", "248 socios registrados — 219 activos",
                    actions=[
                        action_button("🔽 Filtrar", "outline"),
                        action_button("📤 Exportar", "outline"),
                        action_button("➕ Nuevo Socio", "gold"),
                    ]),
        stats_row,
        tabs,
        table,
    ], spacing=16, scroll=ft.ScrollMode.AUTO)
