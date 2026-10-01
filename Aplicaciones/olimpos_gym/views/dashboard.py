import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime

import flet as ft
from theme import *
from components import stat_card, section_card, card_header, status_pill
import ocupacion_repo


def _hace_cuanto(ms: int) -> str:
    if not ms:
        return "todavía no se cargó ningún valor"
    minutos = max(0, int((datetime.now().timestamp() * 1000 - ms) / 60000))
    if minutos < 1:
        return "hace instantes"
    if minutos < 60:
        return f"hace {minutos} min"
    horas = minutos // 60
    return f"hace {horas} h"


def _tarjeta_ocupacion_en_vivo(page: ft.Page | None) -> ft.Container:
    """SOLO para el dueño: el número real que lee la tarjeta "Ocupación del
    gimnasio" de Inicio en la app móvil (ver OcupacionEnVivo en
    HomeScreen.kt) — antes era un número inventado que cambiaba solo. Acá
    el dueño lo carga a mano (no hay ningún lector de accesos conectado a
    Firestore) y queda guardado en configuracion_app/ocupacion."""
    try:
        actual = ocupacion_repo.obtener_ocupacion()
        error = None
    except Exception as ex:
        actual = {"personas": 0, "actualizado_ms": 0}
        error = str(ex)

    campo = ft.TextField(
        value=str(actual["personas"]), width=70, text_align=ft.TextAlign.CENTER,
        height=42, content_padding=8, keyboard_type=ft.KeyboardType.NUMBER,
    )
    texto_estado = ft.Text(
        f"Capacidad máxima: {ocupacion_repo.CAPACIDAD_MAXIMA} · Actualizado {_hace_cuanto(actual['actualizado_ms'])}",
        size=11, color=TEXT_MUTED,
    )
    aviso = ft.Text("", size=11, color=GREEN, weight=ft.FontWeight.W_700)

    def _clamp(n: int) -> int:
        return max(0, min(ocupacion_repo.CAPACIDAD_MAXIMA, n))

    def _sumar(delta: int):
        try:
            actual_n = int(campo.value or 0)
        except ValueError:
            actual_n = 0
        campo.value = str(_clamp(actual_n + delta))
        if page:
            page.update()

    def _guardar(e):
        try:
            n = _clamp(int(campo.value or 0))
        except ValueError:
            n = 0
        try:
            nuevo = ocupacion_repo.actualizar_ocupacion(n)
            campo.value = str(nuevo["personas"])
            texto_estado.value = f"Capacidad máxima: {ocupacion_repo.CAPACIDAD_MAXIMA} · Actualizado {_hace_cuanto(nuevo['actualizado_ms'])}"
            aviso.value = "✓ Guardado — ya se actualizó en la app"
            aviso.color = GREEN
        except Exception as ex:
            aviso.value = f"No se pudo guardar: {ex}"
            aviso.color = RED
        if page:
            page.update()

    contenido = ft.Column([
        card_header("🟢 Ocupación en vivo (app móvil)"),
        ft.Container(height=4),
        ft.Text(
            "Este número es el que ven TODOS los socios ahora mismo en Inicio. "
            "No hay ningún lector de accesos conectado — lo cargás vos a mano.",
            size=11, color=TEXT_MUTED,
        ),
        ft.Container(height=10),
        ft.Row(
            [
                ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, on_click=lambda e: _sumar(-1)),
                campo,
                ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, on_click=lambda e: _sumar(1)),
                ft.Text("personas", size=12.5, weight=ft.FontWeight.W_700),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
        ),
        ft.Container(height=8),
        ft.ElevatedButton(
            "💾 Guardar", on_click=_guardar, expand=True,
            style=ft.ButtonStyle(
                color=DARK, bgcolor=GOLD,
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_700),
            ),
        ),
        ft.Container(height=6),
        texto_estado,
        aviso,
    ], spacing=0)
    if error:
        contenido.controls.append(ft.Text(f"⚠️ {error}", size=11, color=RED))
    return section_card(contenido)


def build_dashboard(role: str, navigate_fn, page: ft.Page | None = None) -> ft.Column:
    stats_data = DASH_STATS.get(role, DASH_STATS["dueno"])

    # Stats row
    stat_cards = [
        stat_card(s[0], s[1], s[2], s[3], i == 0)
        for i, s in enumerate(stats_data)
    ]
    stats_row = ft.Row(stat_cards, spacing=16, expand=True)

    # Quick access data per role
    quick_data = {
        "entrenador": [
            ("👥", "Mis Socios", "socios"),
            ("📋", "Rutinas", "rutinas"),
            ("📅", "Asistencia", "asistencia"),
            ("📊", "Progreso", "progreso"),
            ("🔔", "Alertas", "notificaciones"),
            ("📝", "Nueva Rutina", "rutinas"),
        ],
        "nutricionista": [
            ("👥", "Mis Socios", "socios"),
            ("🍽️", "Asignar Dietas", "asignar-dietas"),
            ("📊", "Progreso", "progreso"),
            ("🔔", "Alertas", "notificaciones"),
            ("🖼️", "Editor de Dietas", "editor-dietas"),
            ("📅", "Consultas", "asistencia"),
        ],
        "dueno": [
            ("➕", "Nuevo Socio", "socios"),
            ("📋", "Asignar Rutina", "rutinas"),
            ("🍽️", "Asignar Dietas", "asignar-dietas"),
            ("📌", "Tablón del club", "tablon"),
            ("💰", "Registrar Pago", "pagos"),
            ("📊", "Ver Reportes", "reportes"),
        ],
        "seguridad": [
            ("📅", "Control Acceso", "asistencia"),
            ("📷", "Cámaras", "camaras"),
            ("🔔", "Alertas", "notificaciones"),
            ("⚠️", "Incidente", "notificaciones"),
        ],
        "recepcionista": [
            ("➕", "Nuevo Socio", "socios"),
            ("📅", "Asistencia", "asistencia"),
            ("💰", "Registrar Pago", "pagos"),
            ("👥", "Ver Socios", "socios"),
            ("🔔", "Notificaciones", "notificaciones"),
            ("🧾", "Comprobantes", "pagos"),
        ],
    }
    qa_items = quick_data.get(role, [
        ("➕", "Nuevo Socio", "socios"),
        ("📋", "Asignar Rutina", "rutinas"),
        ("🍽️", "Asignar Dietas", "asignar-dietas"),
        ("👥", "Ver Personal", "personal"),
        ("💰", "Registrar Pago", "pagos"),
        ("📊", "Ver Reportes", "reportes"),
    ])

    def qcard(emoji, label, section):
        return ft.Container(
            content=ft.Column([
                ft.Text(emoji, size=28),
                ft.Text(label, size=11.5, weight=ft.FontWeight.W_800, color=DARK,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            bgcolor=CREAM,
            border=ft.border.all(1.5, GRAY_LIGHT),
            border_radius=12,
            padding=16,
            on_click=lambda e, s=section: navigate_fn(s),
            ink=True,
            expand=True,
        )

    qa_rows = []
    for i in range(0, len(qa_items), 3):
        chunk = qa_items[i:i+3]
        qa_rows.append(
            ft.Row([qcard(*c) for c in chunk], spacing=10, expand=True)
        )

    quick_card = section_card(
        ft.Column([
            card_header("⚡ Accesos Rápidos"),
            ft.Container(height=8),
            ft.Column(qa_rows, spacing=10),
        ], spacing=0)
    )

    # Bar chart
    months = [
        ("Ene", 0.55), ("Feb", 0.65), ("Mar", 0.70), ("Abr", 0.62),
        ("May", 0.78), ("Jun", 0.85), ("Jul", 0.72), ("Ago", 0.90),
        ("Sep", 0.88), ("Oct", 0.92), ("Nov", 1.0),  ("Dic", 0.84),
    ]
    bars = []
    for m, h in months:
        alpha = 0.35 + h * 0.25
        color = GOLD if h == 1.0 else ft.Colors.with_opacity(alpha, GOLD)
        bars.append(
            ft.Column([
                ft.Container(
                    bgcolor=color,
                    width=18,
                    height=h * 100,
                    border_radius=ft.border_radius.only(top_left=4, top_right=4),
                ),
                ft.Text(m, size=9, color=TEXT_MUTED, weight=ft.FontWeight.W_700),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
        )

    chart_card = section_card(
        ft.Column([
            card_header("📈 Ingresos mensuales 2025", "Año completo"),
            ft.Container(height=8),
            ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   vertical_alignment=ft.CrossAxisAlignment.END, height=120),
        ], spacing=0)
    )

    # Trainers card
    trainers = [
        ("🧑", "Carlos R.", "Musculación"),
        ("👩", "Laura M.", "Cardio & Yoga"),
        ("🧔", "Diego P.", "CrossFit"),
    ]

    def trainer_card(emoji, name, spec):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(emoji, size=24),
                    width=56, height=56, border_radius=14,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                        colors=[GOLD_LIGHT, GOLD],
                    ),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(name, size=13, weight=ft.FontWeight.W_800),
                ft.Text(spec, size=11, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            bgcolor=CREAM, border=ft.border.all(1.5, GRAY_LIGHT),
            border_radius=12, padding=14, expand=True,
            on_click=lambda e: navigate_fn("personal"), ink=True,
        )

    trainers_card = section_card(
        ft.Column([
            card_header("🏋️ Entrenadores disponibles", "Ver todos ›", lambda e: navigate_fn("personal")),
            ft.Container(height=8),
            ft.Row([trainer_card(*t) for t in trainers], spacing=10),
        ], spacing=0)
    )

    # Activity feed
    activities = [
        (GREEN, "Nuevo socio inscripto", "Martín López — Plan Premium", "Hace 5 min"),
        (GOLD, "Rutina actualizada", "Carlos R. editó \"Pecho & Tríceps\"", "Hace 32 min"),
        (BLUE, "Pago registrado", "Ana González — $8.500", "Hace 1 hora"),
        (RED, "Cuota vencida", "Pablo Suárez — 3 días de mora", "Hace 2 horas"),
        ("#9333EA", "Plan nutricional creado", "Lucía Torres — Pérdida de peso", "Hace 3 horas"),
    ]

    def act_item(color, title, desc, time):
        return ft.Container(
            content=ft.Row([
                ft.Container(width=8, height=8, border_radius=4, bgcolor=color, margin=ft.margin.only(top=5)),
                ft.Column([
                    ft.Text(title, size=12.5, weight=ft.FontWeight.W_700),
                    ft.Text(desc, size=11.5, color=TEXT_MUTED),
                    ft.Text(time, size=11, color=TEXT_MUTED),
                ], spacing=1),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
            padding=ft.padding.symmetric(vertical=12),
        )

    activity_card = section_card(
        ft.Column([
            card_header("🕐 Actividad Reciente"),
            ft.Container(height=4),
            ft.Column([act_item(*a) for a in activities], spacing=0),
        ], spacing=0)
    )

    # Classes today
    classes = [
        ("08:00", "Funcional Matutino", "Laura M.", "12/15", "active"),
        ("10:00", "Yoga & Stretching", "Laura M.", "8/12", "active"),
        ("17:00", "CrossFit Avanzado", "Diego P.", "10/10", "pending"),
        ("19:00", "Musculación Guiada", "Carlos R.", "7/12", "active"),
        ("20:30", "Zumba", "Ana B.", "9/15", "active"),
    ]

    def class_row(time, name, trainer, spots, variant):
        return ft.Container(
            content=ft.Row([
                ft.Text(time, size=11, weight=ft.FontWeight.W_800, color=GOLD_DARK,
                        width=52, font_family="Poppins"),
                ft.Column([
                    ft.Text(name, size=12.5, weight=ft.FontWeight.W_700),
                    ft.Text(trainer, size=11, color=TEXT_MUTED),
                ], spacing=1, expand=True),
                status_pill(spots, variant),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CREAM, border=ft.border.all(1.5, GRAY_LIGHT),
            border_radius=10,
            padding=ft.padding.symmetric(vertical=10, horizontal=12),
        )

    classes_card = section_card(
        ft.Column([
            card_header("📅 Clases de Hoy"),
            ft.Container(height=8),
            ft.Column([class_row(*c) for c in classes], spacing=6),
        ], spacing=0)
    )

    # Hero banner
    hero = ft.Container(
        content=ft.Stack([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Text("⚡", size=11),
                                ft.Text("NOVEDAD DEL MES", size=10.5, weight=ft.FontWeight.W_800, color=GOLD),
                            ], spacing=6),
                            bgcolor=ft.Colors.with_opacity(0.15, GOLD),
                            border_radius=20,
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                        ),
                        ft.Text("¡Bienvenido a\nOlimpos Gym!", size=26, weight=ft.FontWeight.W_900,
                                color=ft.Colors.with_opacity(0.92, ft.Colors.WHITE),
                                font_family="Poppins"),
                        ft.Text("Nueva zona de peso libre inaugurada.\nEquipamiento importado, +60 máquinas.",
                                size=13, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
                        ft.Container(
                            content=ft.Text("Ver más →", size=12, weight=ft.FontWeight.W_700, color=DARK),
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                colors=[GOLD, GOLD_DARK],
                            ),
                            border_radius=10,
                            padding=ft.padding.symmetric(horizontal=16, vertical=8),
                            on_click=None, ink=True,
                        ),
                    ], spacing=10),
                    ft.Image(src="L21.png", width=130, height=130, fit=ft.BoxFit.CONTAIN),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=28, horizontal=32),
            ),
            # Top gold line
            ft.Container(
                height=2,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment.CENTER_LEFT, end=ft.Alignment.CENTER_RIGHT,
                    colors=[ft.Colors.TRANSPARENT, GOLD, ft.Colors.TRANSPARENT],
                ),
                top=0, left=0, right=0,
            ),
        ]),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
            colors=[DARK2, DARK3],
        ),
        border_radius=16,
        border=ft.border.all(1, ft.Colors.with_opacity(0.15, GOLD)),
    )

    left_col = ft.Column([quick_card, chart_card, trainers_card], spacing=16, expand=True)
    right_col_controls = [activity_card, classes_card]
    # Únicamente el dueño ve y controla la ocupación en vivo — ni el
    # "admin" (mismo panel que el dueño en todo lo demás) ni ningún otro
    # rol pueden tocar un dato que se muestra en la app de TODOS los socios.
    if role == "dueno":
        right_col_controls.insert(0, _tarjeta_ocupacion_en_vivo(page))
    right_col = ft.Column(right_col_controls, spacing=16, width=300)

    return ft.Column([
        hero,
        ft.Container(height=4),
        stats_row,
        ft.Container(height=4),
        ft.Row([left_col, right_col], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
    ], spacing=16, scroll=ft.ScrollMode.AUTO)
