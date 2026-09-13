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
            ft.Text("EMPLEADO",    size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=3),
            ft.Text("ROL",         size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=2),
            ft.Text("TURNO",       size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=2),
            ft.Text("ESPECIALIDAD",size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=3),
            ft.Text("ESTADO",      size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=1),
        ], spacing=0),
        bgcolor=CREAM, padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT)),
    )

    def emp_row(init, var, name, email, rol, turno, esp):
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    avatar(init, var),
                    ft.Column([ft.Text(name, size=13, weight=ft.FontWeight.W_800),
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
def build_asistencia() -> ft.Column:
    stats_row = ft.Row([
        stat_card("Ingresos hoy",      "67",     "▲ +8 vs ayer", "green", True),
        stat_card("Pico del día",       "18:00h", "23 personas",  "gold"),
        stat_card("Promedio semanal",   "61",     "▲ +5%",        "green"),
    ], spacing=16)

    # Calendar heatmap
    days = [0,0,1,2,3,4,3,2,1,3,4,3,2,0,1,2,3,4,3,2,1,0,2,3,4,3,2,1,0,0]
    color_map = {0:"#E8E5D8", 1: ft.Colors.with_opacity(0.15, GOLD),
                 2: ft.Colors.with_opacity(0.35, GOLD), 3: ft.Colors.with_opacity(0.6, GOLD), 4: GOLD}

    cal_cells = []
    day_labels = ["L","M","X","J","V","S","D"]
    for lbl in day_labels:
        cal_cells.append(ft.Container(
            content=ft.Text(lbl, size=9, weight=ft.FontWeight.W_700, color=TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
            alignment=ft.Alignment.CENTER, height=18,
        ))
    for i, d in enumerate(days):
        cal_cells.append(ft.Container(
            bgcolor=color_map[d], border_radius=4, height=22,
            content=ft.Text(str(i+1), size=9, weight=ft.FontWeight.W_700,
                            color=DARK if d >= 3 else TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            alignment=ft.Alignment.CENTER,
        ))

    calendar_card = section_card(
        ft.Column([
            ft.Text("🗓️ Mapa de asistencia — Noviembre 2025", size=14, weight=ft.FontWeight.W_700,
                    font_family="Poppins"),
            ft.Container(height=8),
            ft.GridView(cal_cells, runs_count=7, max_extent=36, spacing=3, run_spacing=3,
                        height=160),
        ], spacing=8)
    )

    # Recent entries
    entries = [
        ("ML", "gold",   "Martín López",    "09:14",  "✅ Ingreso"),
        ("AG", "blue",   "Ana González",    "09:22",  "✅ Ingreso"),
        ("PS", "red",    "Pablo Suárez",    "09:45",  "✅ Ingreso"),
        ("LT", "purple", "Lucía Torres",    "10:02",  "✅ Ingreso"),
        ("DC", "dark",   "Diego Castro",    "10:15",  "🚪 Egreso"),
        ("JR", "green",  "Juan Rodríguez",  "10:30",  "✅ Ingreso"),
    ]

    header = ft.Container(
        content=ft.Row([
            ft.Text("SOCIO",   size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=3),
            ft.Text("HORA",    size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=1),
            ft.Text("TIPO",    size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=1),
        ], spacing=0),
        bgcolor=CREAM, padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT)),
    )

    def entry_row(init, var, name, hora, tipo):
        return ft.Container(
            content=ft.Row([
                ft.Row([avatar(init, var),
                        ft.Text(name, size=13, weight=ft.FontWeight.W_800)],
                       spacing=10, expand=3),
                ft.Text(hora, size=13, weight=ft.FontWeight.W_700, expand=1),
                ft.Text(tipo, size=13, expand=1),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
        )

    entries_table = section_card(
        ft.Column([
            ft.Container(
                content=ft.Text("📋 Registros de hoy", size=14, weight=ft.FontWeight.W_700,
                                font_family="Poppins"),
                padding=ft.padding.only(left=14, right=14, top=16, bottom=4),
            ),
            header,
            ft.Column([entry_row(*e) for e in entries], spacing=0),
        ], spacing=0), padding=0
    )

    return ft.Column([
        page_header("📅 Asistencia", "Control de ingresos y egresos del gimnasio"),
        stats_row,
        ft.Row([calendar_card, entries_table], spacing=16,
               vertical_alignment=ft.CrossAxisAlignment.START),
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


# ─────────────────────────────────────────────
# RUTINAS
# ─────────────────────────────────────────────
def build_rutinas() -> ft.Column:
    plans = [
        ("Pecho & Tríceps", "Musculación", ["Empuje", "Fuerza", "Hipertrofia"],
         [("Press plano c/ barra", "4 × 8-10", "2 min"), ("Press inclinado mancuernas", "3 × 10-12", "90s"),
          ("Fondos en paralelas", "3 × 12", "60s"), ("Press francés", "3 × 10-12", "90s"),
          ("Extensiones de tríceps", "4 × 12", "60s")]),
        ("Espalda & Bíceps", "Musculación", ["Tirón", "Fuerza", "Volumen"],
         [("Dominadas pronadas", "4 × 6-8", "2 min"), ("Remo con barra", "4 × 8-10", "2 min"),
          ("Jalón al pecho", "3 × 10-12", "90s"), ("Curl con barra", "4 × 10", "90s")]),
    ]

    def plan_card(title, cat, tags, exercises):
        tag_chips = ft.Row([
            ft.Container(
                content=ft.Text(t, size=10, weight=ft.FontWeight.W_800, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border_radius=20,
                padding=ft.padding.symmetric(horizontal=9, vertical=3),
            ) for t in tags
        ], spacing=6)

        exs = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(str(i+1), size=11, weight=ft.FontWeight.W_900, color=GOLD),
                        width=26, height=26, bgcolor=DARK, border_radius=7,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Text(name, size=13, weight=ft.FontWeight.W_700, expand=True),
                    ft.Text(sets, size=12, color=TEXT_MUTED),
                    ft.Text(rest, size=11, color=TEXT_MUTED),
                ], spacing=12),
                bgcolor=CREAM, border=ft.border.all(1, GRAY_LIGHT),
                border_radius=10, padding=10,
            )
            for i, (name, sets, rest) in enumerate(exercises)
        ], spacing=6)

        return section_card(ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(title, size=14, weight=ft.FontWeight.W_800, color=DARK, font_family="Poppins"),
                    ft.Text(cat, size=11.5, color=TEXT_MUTED),
                ], spacing=2, expand=True),
                action_button("✏️ Editar", "outline"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=4),
            tag_chips,
            ft.Container(height=8),
            exs,
        ], spacing=4))

    return ft.Column([
        page_header("📋 Rutinas", "Gestión de planes de entrenamiento",
                    actions=[action_button("➕ Nueva Rutina", "gold")]),
        ft.Column([plan_card(*p) for p in plans], spacing=16),
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


# ─────────────────────────────────────────────
# DIETAS
# ─────────────────────────────────────────────
def build_dietas() -> ft.Column:
    plans = [
        ("Plan de Definición", "Pérdida de grasa y mantenimiento muscular", ["Bajo carb", "Alta proteína", "Déficit"],
         [("Desayuno", "7:00 AM", "Avena + proteína + frutas rojas. 450 kcal"),
          ("Almuerzo",  "13:00",   "Pechuga de pollo + arroz integral + ensalada. 650 kcal"),
          ("Merienda",  "17:00",   "Yogur griego + almendras. 280 kcal"),
          ("Cena",      "21:00",   "Salmón al horno + vegetales salteados. 520 kcal")]),
        ("Plan de Volumen", "Ganancia de masa muscular", ["Alto carb", "Superávit", "Fuerza"],
         [("Desayuno", "7:00 AM", "Huevos revueltos + avena + banana. 650 kcal"),
          ("Pre-entreno", "12:00", "Arroz + carne magra. 700 kcal"),
          ("Post-entreno", "15:00","Batido proteico + fruta. 400 kcal"),
          ("Cena",      "21:00",   "Pasta integral + pollo. 750 kcal")]),
    ]

    def diet_card(title, desc, tags, meals):
        tag_chips = ft.Row([
            ft.Container(
                content=ft.Text(t, size=10, weight=ft.FontWeight.W_800, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border_radius=20,
                padding=ft.padding.symmetric(horizontal=9, vertical=3),
            ) for t in tags
        ], spacing=6)

        meal_items = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(name, size=13, weight=ft.FontWeight.W_800),
                        ft.Text(detail, size=11.5, color=TEXT_MUTED),
                    ], spacing=2, expand=True),
                    ft.Text(time, size=11, weight=ft.FontWeight.W_800, color=GOLD_DARK,
                            font_family="Poppins"),
                ], spacing=12),
                bgcolor=CREAM, border=ft.border.all(1, GRAY_LIGHT),
                border_radius=10, padding=12,
            )
            for name, time, detail in meals
        ], spacing=6)

        return section_card(ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(title, size=14, weight=ft.FontWeight.W_800, font_family="Poppins"),
                    ft.Text(desc, size=11.5, color=TEXT_MUTED),
                ], spacing=2, expand=True),
                action_button("✏️ Editar", "outline"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=6),
            tag_chips,
            ft.Container(height=10),
            meal_items,
        ], spacing=4))

    return ft.Column([
        page_header("🥗 Planes Nutricionales", "Gestión de dietas y nutrición",
                    actions=[action_button("➕ Nuevo Plan", "gold")]),
        ft.Column([diet_card(*p) for p in plans], spacing=16),
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


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
                ft.Text(label, size=12, weight=ft.FontWeight.W_700),
                ft.Text(f"{int(val*100)}%", size=12, weight=ft.FontWeight.W_700),
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
        ft.Text("📊 Objetivos", size=14, weight=ft.FontWeight.W_700, font_family="Poppins"),
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
        content=ft.Row([ft.Text(h, size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=1)
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
                                          weight=ft.FontWeight.W_700, font_family="Poppins"),
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
            ft.Text("SOCIO",      size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=3),
            ft.Text("PLAN",       size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=2),
            ft.Text("FECHA",      size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=2),
            ft.Text("MONTO",      size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=1),
            ft.Text("MÉTODO",     size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=2),
            ft.Text("ESTADO",     size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=1),
        ], spacing=0),
        bgcolor=CREAM, padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT)),
    )

    def pago_row(init, var, name, plan, fecha, monto, metodo, estado):
        is_paid = "Pagado" in estado
        return ft.Container(
            content=ft.Row([
                ft.Row([avatar(init, var),
                        ft.Text(name, size=13, weight=ft.FontWeight.W_800)],
                       spacing=10, expand=3),
                ft.Text(plan,   size=13, expand=2),
                ft.Text(fecha,  size=13, expand=2),
                ft.Text(monto, size=13, weight=ft.FontWeight.W_700, color=GOLD_DARK, expand=1),
                ft.Text(metodo, size=13, expand=2),
                ft.Container(
                    content=ft.Text(estado, size=11, weight=ft.FontWeight.W_800,
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
# REPORTES
# ─────────────────────────────────────────────
def build_reportes() -> ft.Column:
    # Monthly bars
    monthly = [("Ene",55),("Feb",65),("Mar",70),("Abr",62),("May",78),
               ("Jun",85),("Jul",72),("Ago",90),("Sep",88),("Oct",92),("Nov",100),("Dic",84)]

    bars = ft.Row([
        ft.Column([
            ft.Container(
                bgcolor=GOLD if v == 100 else ft.Colors.with_opacity(0.35 + v/300, GOLD),
                width=28, height=v, border_radius=ft.border_radius.only(top_left=4, top_right=4),
            ),
            ft.Text(m, size=9, color=TEXT_MUTED, weight=ft.FontWeight.W_700),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
        for m, v in monthly
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.END)

    revenue_card = section_card(ft.Column([
        ft.Text("📈 Ingresos 2025", size=14, weight=ft.FontWeight.W_700, font_family="Poppins"),
        ft.Container(height=10),
        ft.Container(content=bars, height=130),
    ], spacing=0))

    # KPIs
    kpis = [
        ("Tasa de retención",  "89%",  BADGE_GREEN_TEXT,  BADGE_GREEN_BG),
        ("NPS",                "+72",  BADGE_BLUE_TEXT,   BADGE_BLUE_BG),
        ("Churn rate",         "4.2%", BADGE_RED_TEXT,    BADGE_RED_BG),
        ("LTV promedio",       "$38k", BADGE_GOLD_TEXT,   BADGE_GOLD_BG),
    ]

    kpi_row = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text(label, size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_700),
                ft.Text(value, size=24, weight=ft.FontWeight.W_900, color=text_c, font_family="Poppins"),
            ], spacing=4),
            bgcolor=bg_c, border_radius=12,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            expand=True,
        ) for label, value, text_c, bg_c in kpis
    ], spacing=12)

    return ft.Column([
        page_header("📈 Reportes", "Análisis y métricas del gimnasio",
                    actions=[action_button("📤 Exportar", "gold")]),
        kpi_row,
        revenue_card,
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


# ─────────────────────────────────────────────
# NOTIFICACIONES
# ─────────────────────────────────────────────
def build_notificaciones() -> ft.Column:
    notifs = [
        ("🔔", BADGE_GOLD_BG,   "Nueva inscripción",       "Martín López se inscribió al Plan Premium",          "Hace 5 min",  True),
        ("⚠️",  BADGE_RED_BG,   "Cuota vencida",            "Pablo Suárez tiene 3 días de mora en su cuota",      "Hace 1 hora", True),
        ("💪",  BADGE_BLUE_BG,  "Rutina completada",        "Diego Castro completó su semana de entrenamiento",   "Hace 2 hs",   True),
        ("🥗",  BADGE_GREEN_BG, "Consulta nutricional",     "Sandra Villar actualizó el plan de Lucía Torres",    "Hace 3 hs",   False),
        ("💳",  BADGE_GOLD_BG,  "Pago recibido",            "Ana González abonó su cuota mensual — $8.500",       "Ayer",        False),
        ("📊",  BADGE_BLUE_BG,  "Reporte semanal listo",    "El reporte de asistencia de la semana está disponible","Ayer",      False),
    ]

    def notif_item(icon, icon_bg, title, body, time, unread):
        dot = ft.Container(width=7, height=7, bgcolor=GOLD, border_radius=4,
                           margin=ft.margin.only(top=4)) if unread else ft.Container(width=7)
        return ft.Container(
            content=ft.Row([
                ft.Container(content=ft.Text(icon, size=17), bgcolor=icon_bg,
                             width=38, height=38, border_radius=11, alignment=ft.Alignment.CENTER),
                ft.Column([
                    ft.Row([
                        ft.Text(title, size=13, weight=ft.FontWeight.W_800, expand=True),
                        dot,
                    ]),
                    ft.Text(body, size=12, color=TEXT_MUTED),
                    ft.Text(time, size=10.5, color=TEXT_MUTED, weight=ft.FontWeight.W_600),
                ], spacing=1, expand=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
            padding=ft.padding.symmetric(vertical=14),
        )

    notif_list = section_card(ft.Column([
        ft.Row([
            ft.Text("🔔 Notificaciones", size=14, weight=ft.FontWeight.W_700, font_family="Poppins", expand=True),
            ft.TextButton("Marcar todas como leídas",
                          style=ft.ButtonStyle(color=GOLD_DARK,
                                               text_style=ft.TextStyle(size=11.5, weight=ft.FontWeight.W_700))),
        ]),
        ft.Container(height=4),
        ft.Column([notif_item(*n) for n in notifs], spacing=0),
    ], spacing=4))

    return ft.Column([
        page_header("🔔 Notificaciones", "Centro de alertas y novedades"),
        notif_list,
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
                            content=ft.Text(f"{cam_id} — {location}", size=10, weight=ft.FontWeight.W_800,
                                            color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE)),
                            bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
                            border_radius=6, padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            alignment=ft.Alignment.CENTER_LEFT,
                        ),
                        ft.Container(expand=True),
                        ft.Row([
                            ft.Container(width=6, height=6, bgcolor=RED, border_radius=3),
                            ft.Text("LIVE", size=9, weight=ft.FontWeight.W_800,
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
            ft.Text("📷 Feed en vivo", size=14, weight=ft.FontWeight.W_700, font_family="Poppins"),
            ft.Container(height=10),
            ft.Column(grid_rows, spacing=12),
        ], spacing=0)
    )

    return ft.Column([
        page_header("📷 Cámaras", "Sistema de videovigilancia — 8 cámaras activas"),
        stats_row, cam_grid,
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


# ─────────────────────────────────────────────
# STOCK
# ─────────────────────────────────────────────
def build_stock() -> ft.Column:
    items = [
        ("Mancuernas 5-30 kg (set)", "Equipamiento", "4 sets",    0.80, "Bueno",     GOLD_DARK, "active"),
        ("Barras olímpicas",          "Equipamiento", "12 unidades",0.90, "Excelente",GREEN,     "active"),
        ("Guantes de entrenamiento",  "Accesorios",   "8 pares",   0.25, "Escaso",   "#D97706", "pending"),
        ("Colchonetas de yoga",        "Equipamiento", "20 unidades",0.95, "Excelente",GREEN,     "active"),
        ("Creatina monohidratada",     "Suplementos",  "5 unidades", 0.20, "Crítico",  RED,       "inactive"),
        ("Bandas elásticas (set)",     "Equipamiento", "15 sets",   0.70, "Bueno",    GOLD_DARK, "active"),
    ]

    stats_row = ft.Row([
        stat_card("Artículos totales", "48",  "",             "gold", True),
        stat_card("Stock bajo",        "2",   "⚠️ Revisar",   "red"),
        stat_card("Críticos",          "1",   "🚨 Urgente",   "red"),
        stat_card("OK",                "45",  "✓ Disponible", "green"),
    ], spacing=16)

    header = ft.Container(
        content=ft.Row([
            ft.Text("ARTÍCULO",  size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=3),
            ft.Text("CATEGORÍA", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=2),
            ft.Text("CANTIDAD",  size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=2),
            ft.Text("ESTADO",    size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=3),
            ft.Text("",          size=11, expand=1),
        ], spacing=0),
        bgcolor=CREAM, padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT)),
    )

    def stock_row(name, cat, qty, pct, label, label_color, status):
        bar_color = RED if pct <= 0.20 else (GOLD if pct <= 0.30 else GREEN)
        return ft.Container(
            content=ft.Row([
                ft.Text(name, size=13, weight=ft.FontWeight.W_800, expand=3),
                ft.Text(cat, size=13, expand=2),
                ft.Text(qty, size=13, expand=2),
                ft.Row([
                    ft.Container(
                        content=ft.Container(bgcolor=bar_color, border_radius=3,
                                             height=5, width=pct),
                        bgcolor=GRAY_LIGHT, border_radius=3, height=5,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE, expand=True,
                    ),
                    ft.Text(label, size=11, weight=ft.FontWeight.W_800, color=label_color),
                ], spacing=8, expand=3),
                ft.Container(content=status_pill("OK" if status == "active" else
                                                  "Bajo" if status == "pending" else "Crítico",
                                                  status), expand=1),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
        )

    table = section_card(
        ft.Column([header, ft.Column([stock_row(*i) for i in items], spacing=0)], spacing=0),
        padding=0
    )

    return ft.Column([
        page_header("📦 Stock", "Inventario y control de materiales",
                    actions=[action_button("➕ Agregar ítem", "gold")]),
        stats_row, table,
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


# ─────────────────────────────────────────────
# CONFIGURACION
# ─────────────────────────────────────────────
def build_configuracion() -> ft.Column:
    menu_items = [
        ("🏢", "Información del gimnasio", True),
        ("💳", "Planes y precios", False),
        ("👥", "Gestión de roles", False),
        ("🔔", "Notificaciones automáticas", False),
        ("🎨", "Apariencia", False),
        ("💾", "Backup y datos", False),
        ("🔐", "Seguridad y accesos", False),
    ]

    menu = ft.Column([
        ft.Container(
            content=ft.Row([ft.Text(emoji, size=16), ft.Text(label, size=13,
                weight=ft.FontWeight.W_800 if active else ft.FontWeight.W_700,
                color=DARK if active else TEXT_MUTED)], spacing=8),
            bgcolor=GOLD_BG2 if active else ft.Colors.TRANSPARENT,
            border=ft.border.all(1.5, GOLD_LIGHT) if active else None,
            border_radius=10,
            padding=ft.padding.symmetric(vertical=10, horizontal=12),
            on_click=None, ink=True,
        ) for emoji, label, active in menu_items
    ], spacing=4)

    menu_card = section_card(ft.Column([
        ft.Text("📁 Menú de configuración", size=14, weight=ft.FontWeight.W_700, font_family="Poppins"),
        ft.Container(height=10),
        menu,
    ], spacing=0))

    # Gym info fields
    fields = [
        ("Nombre",    "OLIMPOS GYM"),
        ("CUIT",      "30-12345678-9"),
        ("Dirección", "Av. Mitre 1234, Buenos Aires"),
        ("Teléfono",  "011 4567-8901"),
        ("Apertura",  "06:00 hs"),
        ("Cierre",    "23:00 hs"),
    ]

    def field_box(label, value):
        return ft.Column([
            ft.Text(label.upper(), size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_800),
            ft.Container(
                content=ft.Text(value, size=13, weight=ft.FontWeight.W_700),
                bgcolor=CREAM, border=ft.border.all(1.5, GRAY_LIGHT),
                border_radius=10, padding=ft.padding.symmetric(horizontal=12, vertical=10),
            ),
        ], spacing=4, expand=True)

    field_pairs = []
    for i in range(0, len(fields), 2):
        pair = fields[i:i+2]
        field_pairs.append(ft.Row([field_box(*p) for p in pair], spacing=12))

    plans = [
        ("Premium Anual",    "$12.500/mes"),
        ("Estándar Mensual", "$8.500/mes"),
        ("Mensual Básico",   "$6.000/mes"),
    ]

    plans_list = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text(name, size=13, weight=ft.FontWeight.W_800, expand=True),
                ft.Text(price, size=13, weight=ft.FontWeight.W_900, color=GOLD_DARK),
            ]),
            bgcolor=CREAM, border_radius=10,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
        ) for name, price in plans
    ], spacing=6)

    info_card = section_card(ft.Column([
        ft.Text("🏢 Información del Gimnasio", size=14, weight=ft.FontWeight.W_700, font_family="Poppins"),
        ft.Container(height=12),
        ft.Column(field_pairs, spacing=12),
        ft.Container(height=12),
        ft.Text("💳 Planes activos", size=13, weight=ft.FontWeight.W_700, font_family="Poppins"),
        ft.Container(height=6),
        plans_list,
    ], spacing=0))

    return ft.Column([
        page_header("⚙️ Configuración del Sistema", "Ajustes generales de Olimpos Gym"),
        ft.Row([
            ft.Container(content=menu_card, width=260),
            ft.Container(content=info_card, expand=True),
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
    ], spacing=16, scroll=ft.ScrollMode.AUTO)


# ─────────────────────────────────────────────
# MI PERFIL
# ─────────────────────────────────────────────
def build_mi_perfil() -> ft.Column:
    # Profile banner
    banner = ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Text("M", size=28, weight=ft.FontWeight.W_900, color=DARK),
                width=72, height=72, border_radius=18,
                gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                            colors=[GOLD_LIGHT, GOLD]),
                border=ft.border.all(3, ft.Colors.with_opacity(0.3, GOLD)),
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column([
                ft.Text("Martín López", size=20, weight=ft.FontWeight.W_900,
                        color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE), font_family="Poppins"),
                ft.Text("Socio #0248 — Miembro desde Marzo 2023", size=12,
                        color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                ft.Container(height=4),
                ft.Row([
                    ft.Container(
                        content=ft.Text(t, size=10.5, weight=ft.FontWeight.W_700, color=GOLD),
                        bgcolor=ft.Colors.with_opacity(0.15, GOLD), border_radius=20,
                        padding=ft.padding.symmetric(horizontal=10, vertical=3),
                    ) for t in ["👑 Plan Premium", "🏋️ Musculación", "🥗 Dieta Activa"]
                ], spacing=6),
            ], spacing=4),
        ], spacing=20),
        gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                    colors=[DARK2, DARK3]),
        border_radius=16,
        border=ft.border.all(1, ft.Colors.with_opacity(0.15, GOLD)),
        padding=28,
    )

    # Membership card
    mem_card = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([ft.Text("⭐", size=12),
                                ft.Text("PLAN ACTIVO", size=10, weight=ft.FontWeight.W_800,
                                        color=GOLD)], spacing=6),
                bgcolor=ft.Colors.with_opacity(0.15, GOLD), border_radius=20,
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
            ),
            ft.Text("Premium Anual", size=20, weight=ft.FontWeight.W_900,
                    color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE), font_family="Poppins"),
            ft.Text("Vence el 30 de diciembre de 2025", size=12,
                    color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.1, GOLD), thickness=1),
            ft.Row([
                ft.Column([ft.Text("Próximo pago", size=10.5,
                                    color=ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                           ft.Text("30/12/2025", size=13, weight=ft.FontWeight.W_800, color=GOLD)], spacing=2),
                ft.Column([ft.Text("Monto", size=10.5,
                                    color=ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                           ft.Text("$12.500", size=13, weight=ft.FontWeight.W_800, color=GOLD)], spacing=2),
                ft.Column([ft.Text("Estado", size=10.5,
                                    color=ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                           ft.Text("✓ Al día", size=13, weight=ft.FontWeight.W_800, color=GREEN)], spacing=2),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=10),
        gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                    colors=[DARK, DARK3]),
        border_radius=16,
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, GOLD)),
        padding=22,
        expand=True,
    )

    # Personal data
    personal_fields = [
        ("Nombre",       "Martín López"),
        ("Nacimiento",   "15/07/1994"),
        ("Email",        "martin@email.com"),
        ("Teléfono",     "+54 9 11 1234-5678"),
        ("Entrenador",   "Carlos Rodríguez"),
        ("Nutricionista","Sandra Villar"),
    ]

    def field_item(label, value):
        return ft.Container(
            content=ft.Column([
                ft.Text(label.upper(), size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_800),
                ft.Text(value, size=13, weight=ft.FontWeight.W_700),
            ], spacing=3),
            bgcolor=CREAM, border_radius=10,
            padding=12, expand=True,
        )

    pairs = []
    for i in range(0, len(personal_fields), 2):
        chunk = personal_fields[i:i+2]
        pairs.append(ft.Row([field_item(*f) for f in chunk], spacing=10))

    personal_card = section_card(ft.Column([
        ft.Text("📋 Datos personales", size=14, weight=ft.FontWeight.W_700, font_family="Poppins"),
        ft.Container(height=10),
        ft.Column(pairs, spacing=10),
    ], spacing=0), expand=True)

    return ft.Column([
        page_header("👤 Mi Perfil", "Tu información como socio de Olimpos"),
        banner,
        ft.Row([mem_card, personal_card], spacing=16,
               vertical_alignment=ft.CrossAxisAlignment.START),
    ], spacing=16, scroll=ft.ScrollMode.AUTO)
