import calendar
from datetime import date, timedelta

import flet as ft
from theme import *
from components import stat_card, section_card, card_header, avatar, action_button, page_header
import asistencia_repo

MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS_CORTOS = ["L", "M", "X", "J", "V", "S", "D"]
DIAS_LARGOS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
AVATAR_VARIANTES = ["gold", "blue", "red", "purple", "green", "dark"]
# Pueden cargar una entrada a mano los que atienden la puerta (y los jefes).
ROLES_QUE_REGISTRAN = ("dueno", "admin", "recepcionista", "seguridad")


def _iniciales(nombre: str) -> str:
    partes = [p for p in (nombre or "").split() if p]
    return "".join(p[0] for p in partes[:2]).upper() or "?"


def _barras(valores: list[int], etiquetas: list[str], alto: int = 110, resaltar_max: bool = True) -> ft.Row:
    """Gráfico de barras simple: cada barra con su número arriba."""
    maximo = max(valores) if valores and max(valores) > 0 else 1
    columnas = []
    for v, etq in zip(valores, etiquetas):
        es_max = resaltar_max and v == maximo and v > 0
        columnas.append(ft.Column([
            ft.Text(str(v) if v else "", size=9, weight=ft.FontWeight.W_600,
                    color=GOLD_DARK if es_max else TEXT_MUTED),
            ft.Container(
                bgcolor=GOLD if es_max else (ft.Colors.with_opacity(0.25 + 0.5 * v / maximo, GOLD) if v else GRAY_LIGHT),
                width=16, height=max(3, v / maximo * alto),
                border_radius=ft.border_radius.only(top_left=4, top_right=4),
            ),
            ft.Text(etq, size=9, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3,
           alignment=ft.MainAxisAlignment.END))
    return ft.Row(columnas, alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                  vertical_alignment=ft.CrossAxisAlignment.END, height=alto + 36)


def _fecha_larga(d: date) -> str:
    if d == date.today():
        return "Hoy"
    if d == date.today() - timedelta(days=1):
        return "Ayer"
    return f"{DIAS_LARGOS[d.weekday()]} {d.day}/{d.month:02d}/{d.year}"


def _dialogo_registrar(page: ft.Page, al_registrar):
    try:
        socios = asistencia_repo.socios_para_registrar()
    except Exception as ex:
        page.show_dialog(ft.AlertDialog(title=ft.Text("No se pudo cargar la lista de socios"),
                                        content=ft.Text(str(ex))))
        return
    selector = ft.Dropdown(
        label="Socio", width=380, editable=True, enable_filter=True,
        options=[ft.DropdownOption(key=str(s["id_socio"]),
                                   text=f"{s['nombre']} · #{s['id_socio']:04d}" + (f" · DNI {s['dni']}" if s["dni"] else ""))
                 for s in socios],
    )
    mensaje = ft.Text("", size=12, weight=ft.FontWeight.W_500, color=RED)

    def _registrar(e):
        if not selector.value:
            mensaje.value = "Elegí un socio."
            page.update()
            return
        try:
            nuevo = asistencia_repo.registrar_entrada(int(selector.value), "manual")
        except Exception as ex:
            mensaje.value = f"No se pudo registrar: {ex}"
            page.update()
            return
        page.pop_dialog()
        al_registrar("✓ Entrada registrada" if nuevo
                     else "Ese socio ya había entrado hace un rato: no se duplicó la entrada")

    page.show_dialog(ft.AlertDialog(
        modal=True,
        title=ft.Text("Registrar entrada", weight=ft.FontWeight.W_600, font_family="Poppins"),
        content=ft.Column([
            ft.Text("Para un socio que no mostró el carnet en la app (no la tiene, se quedó sin "
                    "batería…). Cuenta igual para la ocupación en vivo y para su racha.",
                    size=12, color=TEXT_MUTED),
            selector,
            mensaje,
        ], tight=True, spacing=12, width=400),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.pop_dialog()),
            action_button("✅ Registrar", "gold", on_click=_registrar),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    ))


def build_asistencia(page: ft.Page, role: str = "dueno") -> ft.Column:
    hoy = date.today()
    estado = {"anio": hoy.year, "mes": hoy.month, "dia": hoy}
    contenido = ft.Column(spacing=16)
    aviso = ft.Text("", size=12, weight=ft.FontWeight.W_500, color=GREEN)

    def _cambiar_mes(delta: int):
        m = estado["mes"] + delta
        estado["anio"] += (m - 1) // 12
        estado["mes"] = (m - 1) % 12 + 1
        render()

    def _elegir_dia(d: date):
        estado["dia"] = d
        estado["anio"], estado["mes"] = d.year, d.month
        render()

    def _calendario(por_dia: dict[int, int]) -> ft.Control:
        anio, mes = estado["anio"], estado["mes"]
        maximo = max(por_dia.values()) if por_dia else 0
        colores = [GRAY_LIGHT, ft.Colors.with_opacity(0.2, GOLD), ft.Colors.with_opacity(0.4, GOLD),
                   ft.Colors.with_opacity(0.7, GOLD), GOLD]
        celdas = [ft.Container(ft.Text(d, size=9, weight=ft.FontWeight.W_500, color=TEXT_MUTED),
                               alignment=ft.Alignment.CENTER) for d in DIAS_CORTOS]
        primer_dow, dias_mes = calendar.monthrange(anio, mes)
        celdas += [ft.Container() for _ in range(primer_dow)]
        for dia in range(1, dias_mes + 1):
            n = por_dia.get(dia, 0)
            d = date(anio, mes, dia)
            nivel = min(4, 1 + int(3 * n / maximo)) if n and maximo else 0
            elegido = d == estado["dia"]
            futuro = d > hoy
            celdas.append(ft.Container(
                content=ft.Column([
                    ft.Text(str(dia), size=10, weight=ft.FontWeight.W_600,
                            color=DARK if (nivel >= 3 or elegido) else (GRAY if futuro else TEXT_MUTED)),
                    ft.Text(str(n) if n else "", size=8, color=DARK),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=colores[nivel],
                border=ft.border.all(2, DARK) if elegido else (ft.border.all(1.5, GOLD_DARK) if d == hoy else None),
                border_radius=6, alignment=ft.Alignment.CENTER,
                on_click=None if futuro else (lambda e, d=d: _elegir_dia(d)), ink=not futuro,
                tooltip=f"{n} entrada{'s' if n != 1 else ''}",
            ))
        return ft.GridView(celdas, runs_count=7, spacing=4, run_spacing=4, child_aspect_ratio=1.15)

    def _fila_entrada(e) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Row([avatar(_iniciales(e["nombre"]), AVATAR_VARIANTES[e["id_socio"] % len(AVATAR_VARIANTES)]),
                        ft.Text(e["nombre"], size=13, weight=ft.FontWeight.W_600, expand=True,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)],
                       spacing=10, expand=3),
                ft.Text(e["hora"], size=13, weight=ft.FontWeight.W_500, expand=1),
                ft.Text(asistencia_repo.METODOS.get(e["metodo"], e["metodo"]), size=12, expand=2),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)),
        )

    def _vacio(texto: str) -> ft.Container:
        return ft.Container(ft.Text(texto, size=12, color=TEXT_MUTED), padding=14)

    def render(actualizar: bool = True):
        try:
            res = asistencia_repo.resumen()
            por_dia = asistencia_repo.por_dia_del_mes(estado["anio"], estado["mes"])
            entradas = asistencia_repo.entradas_del_dia(estado["dia"])
            horas = asistencia_repo.por_hora(30)
            semana = asistencia_repo.por_dia_semana(30)
            metodos = asistencia_repo.por_metodo(30)
            ranking = asistencia_repo.ranking_mes()
            ausentes = asistencia_repo.ausentes()
        except Exception as ex:
            contenido.controls = [section_card(ft.Text(f"No se pudo cargar la asistencia: {ex}", color=RED))]
            if actualizar:
                page.update()
            return

        dif = res["hoy"] - res["ayer"]
        stats = ft.Row([
            stat_card("En el club ahora", str(res["en_el_club"]),
                      f"entraron en los últimos {asistencia_repo.ocupacion_repo.MINUTOS_EN_EL_CLUB} min", "gold", True),
            stat_card("Entradas hoy", str(res["hoy"]),
                      f"{'▲' if dif > 0 else '▼' if dif < 0 else '='} {abs(dif)} vs ayer ({res['ayer']})",
                      "green" if dif >= 0 else "red"),
            stat_card("Socios esta semana", str(res["socios_semana"]),
                      f"promedio {res['promedio_diario']:g} entradas/día", "blue"),
            stat_card("Hora pico", f"{res['hora_pico']:02d}:00" if res["hora_pico"] is not None else "—",
                      f"{res['entradas_pico']} entradas (30 días)" if res["hora_pico"] is not None else "sin datos aún",
                      "gold"),
        ], spacing=16)

        total_mes = sum(por_dia.values())
        cal_card = section_card(ft.Column([
            ft.Row([
                ft.Text(f"🗓️ {MESES[estado['mes']]} {estado['anio']}", size=14, weight=ft.FontWeight.W_500,
                        font_family="Poppins", expand=True),
                ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=lambda e: _cambiar_mes(-1), tooltip="Mes anterior"),
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=lambda e: _cambiar_mes(1), tooltip="Mes siguiente",
                              disabled=(estado["anio"], estado["mes"]) >= (hoy.year, hoy.month)),
            ]),
            ft.Text(f"{total_mes} entradas en el mes · tocá un día para ver quién vino", size=11, color=TEXT_MUTED),
            ft.Container(_calendario(por_dia), width=330, height=290),
        ], spacing=6), padding=16)

        d = estado["dia"]
        dia_card = section_card(ft.Column([
            ft.Container(ft.Row([
                ft.Text(f"📋 Entradas — {_fecha_larga(d)}", size=14, weight=ft.FontWeight.W_500,
                        font_family="Poppins", expand=True),
                ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=lambda e: _elegir_dia(d - timedelta(days=1)), tooltip="Día anterior"),
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=lambda e: _elegir_dia(d + timedelta(days=1)),
                              tooltip="Día siguiente", disabled=d >= hoy),
            ]), padding=ft.padding.only(left=14, right=6, top=10)),
            ft.Container(ft.Row([
                ft.Text("SOCIO", size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=3),
                ft.Text("HORA", size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=1),
                ft.Text("CÓMO", size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED, expand=2),
            ]), bgcolor=CREAM, padding=ft.padding.symmetric(horizontal=14, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT))),
            ft.Column([_fila_entrada(e) for e in entradas] or [_vacio("Nadie registró entrada este día.")],
                      spacing=0, scroll=ft.ScrollMode.AUTO, height=250),
            ft.Container(ft.Text(f"{len(entradas)} entrada{'s' if len(entradas) != 1 else ''}", size=11, color=TEXT_MUTED),
                         padding=ft.padding.only(left=14, bottom=10, top=6)),
        ], spacing=0), padding=0)
        dia_card.expand = True

        rango_horas = list(range(6, 24))
        horas_card = section_card(ft.Column([
            card_header("⏰ Entradas por hora", "últimos 30 días"),
            ft.Container(height=8),
            _barras([horas.get(h, 0) for h in rango_horas], [f"{h}" for h in rango_horas]),
        ], spacing=0))
        horas_card.expand = 3

        total_met = sum(metodos.values())
        semana_card = section_card(ft.Column([
            card_header("📆 Por día de la semana", "últimos 30 días"),
            ft.Container(height=8),
            _barras(semana, DIAS_LARGOS, alto=80),
            ft.Divider(height=14, color=GRAY_LIGHT),
            ft.Text("CÓMO ENTRARON", size=10.5, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
            *([ft.Row([ft.Text(asistencia_repo.METODOS.get(m, m), size=12, expand=True),
                       ft.Text(f"{n}  ({round(100 * n / total_met)}%)", size=12, weight=ft.FontWeight.W_500)])
               for m, n in sorted(metodos.items(), key=lambda x: -x[1])]
              or [ft.Text("Sin entradas en los últimos 30 días.", size=11, color=TEXT_MUTED)]),
        ], spacing=4))
        semana_card.expand = 2

        ranking_card = section_card(ft.Column([
            card_header(f"🏆 Más constantes de {MESES[hoy.month].lower()}"),
            ft.Container(height=6),
            *([ft.Row([
                ft.Text(f"{i + 1}.", size=13, weight=ft.FontWeight.W_600, color=GOLD_DARK, width=24),
                ft.Text(r["nombre"], size=13, weight=ft.FontWeight.W_500, expand=True),
                ft.Text(f"{r['dias']} día{'s' if r['dias'] != 1 else ''}", size=12, color=TEXT_MUTED),
            ]) for i, r in enumerate(ranking)] or [_vacio("Todavía nadie vino este mes.")]),
        ], spacing=6))
        ranking_card.expand = True

        ausentes_card = section_card(ft.Column([
            card_header(f"💤 Dejaron de venir ({len(ausentes)})", f"{asistencia_repo.DIAS_AUSENTE}+ días sin entrar"),
            ft.Text("Socios activos para contactar — primero los que tienen un plan pago.", size=11, color=TEXT_MUTED),
            ft.Container(height=4),
            ft.Column([
                ft.Row([
                    ft.Text(a["nombre"], size=12.5, weight=ft.FontWeight.W_500, expand=True,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(a["plan"] or "sin plan", size=11, color=GOLD_DARK if a["plan"] else TEXT_MUTED, width=70),
                    ft.Text(f"última: {a['ultima'].strftime('%d/%m')}" if a["ultima"] else "nunca vino",
                            size=11, color=TEXT_MUTED, width=90),
                ]) for a in ausentes
            ] or [_vacio("Todos los socios activos vinieron en las últimas 2 semanas. 🎉")],
               spacing=6, scroll=ft.ScrollMode.AUTO, height=170),
        ], spacing=4))
        ausentes_card.expand = True

        contenido.controls = [
            stats,
            ft.Row([cal_card, dia_card], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row([horas_card, semana_card], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row([ranking_card, ausentes_card], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
        ]
        if actualizar:
            page.update()

    def _tras_registrar(texto: str):
        aviso.value = texto
        _elegir_dia(date.today())

    acciones = [aviso, action_button("🔄 Actualizar", "outline", on_click=lambda e: render())]
    if role in ROLES_QUE_REGISTRAN:
        acciones.append(action_button("➕ Registrar entrada", "gold",
                                      on_click=lambda e: _dialogo_registrar(page, _tras_registrar)))

    titulo = "📅 Control de Acceso" if role == "seguridad" else "📅 Asistencia"
    render(actualizar=False)
    return ft.Column([
        page_header(titulo, "Entradas reales al club: cada vez que un socio muestra el carnet en la app", actions=acciones),
        contenido,
    ], spacing=16, scroll=ft.ScrollMode.AUTO)
