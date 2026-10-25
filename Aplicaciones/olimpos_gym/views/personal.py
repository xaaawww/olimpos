import flet as ft
from theme import *
from components import stat_card, section_card, status_pill, avatar, action_button, page_header

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
