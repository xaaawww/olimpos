import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime

import flet as ft
from theme import *
from components import stat_card, section_card, card_header, status_pill
import ocupacion_repo
import dashboard_repo


def _hace_cuanto(ms: int) -> str:
    if not ms:
        return "todavía no se cargó ningún valor"
    minutos = max(0, int((datetime.now().timestamp() * 1000 - ms) / 60000))
    if minutos < 1:
        return "hace instantes"
    if minutos < 60:
        return f"hace {minutos} min"
    horas = minutos // 60
    if horas < 24:
        return f"hace {horas} h"
    dias = horas // 24
    if dias == 1:
        return "ayer"
    if dias < 30:
        return f"hace {dias} días"
    return datetime.fromtimestamp(ms / 1000).strftime("el %d/%m/%Y")


def _tarjeta_ocupacion_en_vivo(page: ft.Page | None) -> ft.Container:
    """SOLO para el dueño: la misma ocupación que ven los socios en Inicio de
    la app (OcupacionEnVivo en HomeScreen.kt). Se calcula sola con las
    entradas reales (ver ocupacion_repo.py), así que acá solo se mira."""
    numero = ft.Text("—", size=30, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins")
    barra = ft.ProgressBar(value=0, color=GOLD, bgcolor=GRAY_LIGHT, height=8, border_radius=8)
    texto_estado = ft.Text("", size=11, color=TEXT_MUTED)
    lista = ft.Column(spacing=4)

    def _cargar(actualizar: bool):
        try:
            actual = ocupacion_repo.obtener_ocupacion()
            adentro = ocupacion_repo.entradas_recientes()
        except Exception as ex:
            texto_estado.value = f"⚠️ No se pudo leer la ocupación: {ex}"
            texto_estado.color = RED
            if actualizar and page:
                page.update()
            return
        numero.value = f"{actual['personas']} / {ocupacion_repo.capacidad()}"
        barra.value = min(1, actual["personas"] / ocupacion_repo.capacidad())
        texto_estado.value = f"Personas en el club ahora · leído {_hace_cuanto(actual['actualizado_ms'])}"
        texto_estado.color = TEXT_MUTED
        lista.controls = [
            ft.Row([
                ft.Text(f["nombre"], size=11.5, weight=ft.FontWeight.W_500, color=DARK, expand=True,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"entró {_hace_cuanto(f['entrada_ms'])}", size=11, color=TEXT_MUTED),
            ])
            for f in adentro[:8]
        ] or [ft.Text("Nadie mostró el carnet en este rato.", size=11, color=TEXT_MUTED)]
        if actualizar and page:
            page.update()

    _cargar(actualizar=False)

    contenido = ft.Column([
        card_header("🟢 Ocupación en vivo (app móvil)"),
        ft.Container(height=4),
        ft.Text(
            "Se calcula sola: cuenta a los socios que mostraron el carnet de acceso en "
            f"la app en los últimos {ocupacion_repo.MINUTOS_EN_EL_CLUB} minutos. Es el "
            "mismo número que ven todos los socios en Inicio.",
            size=11, color=TEXT_MUTED,
        ),
        ft.Container(height=10),
        numero,
        barra,
        ft.Container(height=4),
        texto_estado,
        ft.Container(height=8),
        ft.Text("EN EL CLUB AHORA", size=10.5, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
        lista,
        ft.Container(height=8),
        ft.TextButton("🔄 Actualizar", on_click=lambda e: _cargar(actualizar=True)),
    ], spacing=0)
    return section_card(contenido)


COLOR_ACTIVIDAD = {"socio": GREEN, "membresia": GOLD, "pago": BLUE, "marca": "#9333EA",
                   "rutina": GOLD_DARK, "dieta": "#16A34A", "entrada": TEXT_MUTED, "tablon": RED}
EMOJI_CATEGORIA = {"Aviso": "📢", "Evento": "🎉", "Promoción": "🏷️", "Importante": "⚠️"}
MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _error(texto: str) -> ft.Text:
    return ft.Text(f"⚠️ {texto}", size=11, color=RED)


def build_dashboard(role: str, navigate_fn, page: ft.Page | None = None) -> ft.Column:
    # ── Tarjetas de arriba (distintas según el rol, todas desde la base) ──
    try:
        stats_data = dashboard_repo.estadisticas(role)
        stats_row = ft.Row([stat_card(s[0], s[1], s[2], s[3], i == 0) for i, s in enumerate(stats_data)],
                           spacing=16, expand=True)
    except Exception as ex:
        stats_row = section_card(_error(f"No se pudieron calcular los números: {ex}"))

    # Quick access data per role
    quick_data = {
        "entrenador": [
            ("👥", "Mis Socios", "socios"),
            ("📋", "Rutinas", "rutinas"),
            ("📅", "Asistencia", "asistencia"),
            ("🏆", "Verificar marcas", "verificacion-marcas"),
            ("🏋️", "Ejercicios", "editor-ejercicios"),
            ("📝", "Nueva Rutina", "rutinas"),
        ],
        "nutricionista": [
            ("👥", "Mis Socios", "socios"),
            ("🍽️", "Asignar Dietas", "asignar-dietas"),
            ("🖼️", "Editor de Dietas", "editor-dietas"),
            ("🤖", "Argos", "argos"),
        ],
        "dueno": [
            ("➕", "Nuevo Socio", "socios"),
            ("📅", "Asistencia", "asistencia"),
            ("📋", "Asignar Rutina", "rutinas"),
            ("🍽️", "Asignar Dietas", "asignar-dietas"),
            ("📌", "Tablón del club", "tablon"),
            ("💳", "Membresías", "membresias"),
        ],
        "seguridad": [
            ("📅", "Control Acceso", "asistencia"),
            ("📷", "Cámaras", "camaras"),
            ("🔔", "Alertas", "notificaciones"),
        ],
        "recepcionista": [
            ("➕", "Nuevo Socio", "socios"),
            ("📅", "Asistencia", "asistencia"),
            ("💳", "Membresías", "membresias"),
            ("👥", "Ver Socios", "socios"),
        ],
    }
    qa_items = quick_data.get(role, [
        ("➕", "Nuevo Socio", "socios"),
        ("📅", "Asistencia", "asistencia"),
        ("📋", "Asignar Rutina", "rutinas"),
        ("🍽️", "Asignar Dietas", "asignar-dietas"),
        ("👥", "Ver Personal", "personal"),
        ("💳", "Membresías", "membresias"),
    ])

    def qcard(emoji, label, section):
        return ft.Container(
            content=ft.Column([
                ft.Text(emoji, size=28),
                ft.Text(label, size=11.5, weight=ft.FontWeight.W_600, color=DARK,
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

    # ── Gráfico mensual del año actual: se elige qué mirar ──
    anio = datetime.now().year
    serie_elegida = {"tipo": "entradas"}
    zona_grafico = ft.Column(spacing=0)
    botones_serie = ft.Row(spacing=4)

    def _dibujar_serie():
        try:
            valores = dashboard_repo.serie_mensual(serie_elegida["tipo"], anio)
        except Exception as ex:
            zona_grafico.controls = [_error(str(ex))]
            return
        maximo = max(valores) or 1
        mes_actual = datetime.now().month
        es_plata = serie_elegida["tipo"] == "ingresos"
        barras = []
        for i, v in enumerate(valores):
            actual = i + 1 == mes_actual
            etiqueta = (f"${v / 1000:.0f}k" if v >= 1000 else f"${v:.0f}") if es_plata else f"{v:.0f}"
            barras.append(ft.Column([
                ft.Text(etiqueta if v else "", size=8.5, weight=ft.FontWeight.W_600,
                        color=GOLD_DARK if actual else TEXT_MUTED),
                ft.Container(
                    bgcolor=GOLD if actual else (ft.Colors.with_opacity(0.3 + 0.5 * v / maximo, GOLD) if v else GRAY_LIGHT),
                    width=18, height=max(3, v / maximo * 100),
                    border_radius=ft.border_radius.only(top_left=4, top_right=4),
                ),
                ft.Text(MESES_CORTOS[i], size=9, color=DARK if actual else TEXT_MUTED, weight=ft.FontWeight.W_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4, alignment=ft.MainAxisAlignment.END))
        total = sum(valores)
        zona_grafico.controls = [
            ft.Row(barras, alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   vertical_alignment=ft.CrossAxisAlignment.END, height=140),
            ft.Container(height=6),
            ft.Text(f"Total {anio}: " + (dashboard_repo._pesos(total) if es_plata else f"{total:.0f}"),
                    size=11, color=TEXT_MUTED),
        ]

    def _boton_serie(tipo: str) -> ft.Container:
        activo = tipo == serie_elegida["tipo"]
        return ft.Container(
            ft.Text(dashboard_repo.SERIES[tipo], size=11, weight=ft.FontWeight.W_500,
                    color=DARK if activo else TEXT_MUTED),
            bgcolor=WHITE if activo else ft.Colors.TRANSPARENT, border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            on_click=lambda e, t=tipo: _elegir_serie(t), ink=True,
        )

    def _elegir_serie(tipo: str):
        serie_elegida["tipo"] = tipo
        botones_serie.controls = [_boton_serie(t) for t in dashboard_repo.SERIES]
        _dibujar_serie()
        if page:
            page.update()

    botones_serie.controls = [_boton_serie(t) for t in dashboard_repo.SERIES]
    _dibujar_serie()
    chart_card = section_card(
        ft.Column([
            card_header(f"📈 Mes a mes — {anio}"),
            ft.Container(height=6),
            ft.Container(botones_serie, bgcolor=CREAM, border_radius=10, padding=3,
                         border=ft.border.all(1.5, GRAY_LIGHT)),
            ft.Container(height=10),
            zona_grafico,
        ], spacing=0)
    )

    # ── Equipo: los empleados reales y si entraron hoy al sistema ──
    puede_ver_personal = role in ("dueno", "admin")
    try:
        miembros = dashboard_repo.equipo()
        filas_equipo = [
            ft.Container(
                content=ft.Row([
                    ft.Container(width=8, height=8, border_radius=4,
                                 bgcolor=GREEN if m["entro_hoy"] else GRAY_LIGHT),
                    ft.Column([
                        ft.Text(m["nombre"], size=12.5, weight=ft.FontWeight.W_600),
                        ft.Text(f"{m['rol']} · usuario {m['usuario']}", size=11, color=TEXT_MUTED),
                    ], spacing=1, expand=True),
                    ft.Text("activo hoy" if m["entro_hoy"] else "", size=10.5, color=GREEN, weight=ft.FontWeight.W_500),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=CREAM, border=ft.border.all(1.5, GRAY_LIGHT), border_radius=10,
                padding=ft.padding.symmetric(vertical=8, horizontal=12),
                tooltip="Entró hoy al sistema" if m["entro_hoy"] else "Hoy no entró al sistema",
                col={"sm": 12, "md": 6},
            ) for m in miembros
        ]
        conectados = sum(1 for m in miembros if m["entro_hoy"])
        resumen_equipo = f"{len(miembros)} empleados · {conectados} activo{'s' if conectados != 1 else ''} hoy"
    except Exception as ex:
        filas_equipo, resumen_equipo = [_error(str(ex))], ""
    trainers_card = section_card(
        ft.Column([
            card_header("👥 Equipo", "Ver personal ›" if puede_ver_personal else None,
                        (lambda e: navigate_fn("personal")) if puede_ver_personal else None),
            ft.Text(resumen_equipo, size=11, color=TEXT_MUTED),
            ft.Container(height=8),
            ft.ResponsiveRow(filas_equipo, spacing=8, run_spacing=8),
        ], spacing=0)
    )

    # ── Actividad reciente: lo que pasó de verdad en el club ──
    def act_item(a):
        return ft.Container(
            content=ft.Row([
                ft.Container(width=8, height=8, border_radius=4, bgcolor=COLOR_ACTIVIDAD.get(a["tipo"], GOLD),
                             margin=ft.margin.only(top=5)),
                ft.Column([
                    ft.Text(a["titulo"], size=12.5, weight=ft.FontWeight.W_500),
                    ft.Text(a["detalle"] or "", size=11.5, color=TEXT_MUTED),
                    ft.Text(_hace_cuanto(a["ms"]).capitalize(), size=11, color=TEXT_MUTED),
                ], spacing=1, expand=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
            padding=ft.padding.symmetric(vertical=10),
        )

    try:
        items_actividad = [act_item(a) for a in dashboard_repo.actividad_reciente()] \
            or [ft.Text("Todavía no hay actividad registrada.", size=11.5, color=TEXT_MUTED)]
    except Exception as ex:
        items_actividad = [_error(str(ex))]
    activity_card = section_card(
        ft.Column([
            card_header("🕐 Actividad Reciente"),
            ft.Container(height=4),
            ft.Column(items_actividad, spacing=0),
        ], spacing=0)
    )

    # ── Clases de hoy con las reservas reales de esta semana ──
    def class_row(c):
        llena = c["reservados"] >= c["capacidad"]
        return ft.Container(
            content=ft.Row([
                ft.Text(c["hora"], size=11, weight=ft.FontWeight.W_600, color=GOLD_DARK,
                        width=44, font_family="Poppins"),
                ft.Column([
                    ft.Text(c["nombre"], size=12.5, weight=ft.FontWeight.W_500),
                    ft.Text(c["lugar"] or "", size=10.5, color=TEXT_MUTED, max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=1, expand=True),
                status_pill(f"{c['reservados']}/{c['capacidad']}", "inactive" if llena else "active"),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CREAM, border=ft.border.all(1.5, GRAY_LIGHT),
            border_radius=10,
            padding=ft.padding.symmetric(vertical=10, horizontal=12),
            tooltip="Reservas de esta semana / cupo",
        )

    try:
        filas_clases = [class_row(c) for c in dashboard_repo.clases_de_hoy()] \
            or [ft.Text("Hoy no hay clases programadas.", size=11.5, color=TEXT_MUTED)]
    except Exception as ex:
        filas_clases = [_error(str(ex))]
    classes_card = section_card(
        ft.Column([
            card_header("📅 Clases de Hoy"),
            ft.Container(height=8),
            ft.Column(filas_clases, spacing=6),
        ], spacing=0)
    )

    # ── Banner: la novedad que publicó el dueño en el tablón ──
    try:
        nov = dashboard_repo.novedad()
    except Exception:
        nov = None
    if nov:
        etiqueta_banner = f"{EMOJI_CATEGORIA.get(nov['categoria'], '📌')} {nov['categoria'].upper()} · TABLÓN DEL CLUB"
        titulo_banner = nov["titulo"]
        texto_banner = nov["mensaje"]
        boton_banner = "Ver tablón →"
    else:
        etiqueta_banner = "📌 TABLÓN DEL CLUB"
        titulo_banner = "¡Bienvenido a\nOlimpos Gym!"
        if role == "dueno":
            texto_banner = ("Todavía no hay novedades publicadas. Lo que publiques en el tablón\n"
                            "aparece acá y en la app de todos los socios.")
            boton_banner = "Publicar novedad →"
        else:
            texto_banner = "Todavía no hay novedades publicadas en el tablón."
            boton_banner = "Ver tablón →"
    hero = ft.Container(
        content=ft.Stack([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Container(
                            content=ft.Text(etiqueta_banner, size=10.5, weight=ft.FontWeight.W_600, color=GOLD),
                            bgcolor=ft.Colors.with_opacity(0.15, GOLD),
                            border_radius=20,
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                        ),
                        ft.Text(titulo_banner, size=26, weight=ft.FontWeight.W_600,
                                color=ft.Colors.with_opacity(0.92, ft.Colors.WHITE),
                                font_family="Poppins"),
                        ft.Text(texto_banner, size=13, color=ft.Colors.with_opacity(0.55, ft.Colors.WHITE),
                                max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Container(
                            content=ft.Text(boton_banner, size=12, weight=ft.FontWeight.W_500, color=DARK),
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                colors=[GOLD, GOLD_DARK],
                            ),
                            border_radius=10,
                            padding=ft.padding.symmetric(horizontal=16, vertical=8),
                            on_click=lambda e: navigate_fn("tablon"), ink=True,
                        ),
                    ], spacing=10, expand=True),
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
    # La tarjeta de ocupación en vivo la ve solo el dueño (ya no se edita a
    # mano: se calcula sola con las entradas de los socios).
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
