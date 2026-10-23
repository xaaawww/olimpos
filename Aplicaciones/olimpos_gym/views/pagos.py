# OLIMPOS GYM — Registro de pagos y cuotas
#
# Arriba, cuatro tarjetas con datos reales (ingresos del mes, pagos de hoy,
# cuotas vencidas y socios al día) con su mini gráfico. Debajo:
#   - evolución de ingresos (barras por mes) y resumen por plan del mes
#   - acciones: registrar pago, ver morosos, exportar el mes a CSV y (dueño /
#     administrador) cambiar precios de los planes
#   - próximos vencimientos (con "Cobrar" directo)
#   - últimos pagos del mes, filtrables por plan, con opción de anular
# Todo lee y escribe en Neon a través de pagos_repo.

import os
import sys
from datetime import date, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
import flet.canvas as cv
from theme import *
import pagos_repo as repo

COLOR_PLAN = {"Bronce": "#C2783E", "Oro": "#E0A800", "Platino": "#64748B"}
COLORES_AVATAR = [("#FEF3C7", "#B45309"), ("#DBEAFE", "#1D4ED8"), ("#EDE9FE", "#6D28D9"),
                  ("#FCE7F3", "#BE185D"), ("#DCFCE7", "#15803D"), ("#FFEDD5", "#C2410C")]
ICONO_METODO = {"Efectivo": ft.Icons.PAYMENTS_OUTLINED, "Transferencia": ft.Icons.ACCOUNT_BALANCE_OUTLINED,
                "Tarjeta de débito": ft.Icons.CREDIT_CARD, "Tarjeta de crédito": ft.Icons.CREDIT_CARD,
                "Mercado Pago": ft.Icons.QR_CODE_2}


def _plata(v: float) -> str:
    return "$" + f"{v:,.0f}".replace(",", ".")


def _plata_corta(v: float) -> str:
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M".replace(".", ",")
    if v >= 1000:
        return f"${v / 1000:.0f}k"
    return _plata(v)


def _iniciales(nombre: str) -> str:
    p = [x for x in nombre.split() if x]
    return ((p[0][0] + (p[1][0] if len(p) > 1 else "")) if p else "?").upper()


def _avatar(nombre: str, id_socio: int, lado: int = 36) -> ft.Container:
    fondo, color = COLORES_AVATAR[id_socio % len(COLORES_AVATAR)]
    return ft.Container(ft.Text(_iniciales(nombre), size=lado * 0.34, weight=ft.FontWeight.W_600, color=color),
                        width=lado, height=lado, border_radius=lado / 2, bgcolor=fondo, alignment=ft.Alignment.CENTER)


def _tarjeta(contenido, padding=22, expand=None) -> ft.Container:
    return ft.Container(contenido, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=18,
                        padding=padding, expand=expand)


def _titulo(icono, texto, derecha=None) -> ft.Row:
    return ft.Row([ft.Container(ft.Icon(icono, size=19, color=GOLD_DARK), width=36, height=36, border_radius=18,
                                bgcolor=GOLD_BG2, alignment=ft.Alignment.CENTER),
                   ft.Text(texto, size=16, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins", expand=True)]
                  + ([derecha] if derecha else []), spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _sparkline(valores: list[float], color: str, ancho: int = 190, alto: int = 44) -> ft.Control:
    """Mini gráfico de área para las tarjetas."""
    if not valores or not any(valores):
        return ft.Container(ft.Container(height=2, bgcolor=ft.Colors.with_opacity(0.35, color), border_radius=1),
                            height=alto, alignment=ft.Alignment.BOTTOM_CENTER, padding=ft.padding.only(bottom=6))
    vmax = max(valores) or 1
    n = len(valores)
    xs = [ancho * i / (n - 1) if n > 1 else ancho / 2 for i in range(n)]
    ys = [alto - 4 - v / vmax * (alto - 10) for v in valores]
    area = [cv.Path.MoveTo(xs[0], alto)] + [cv.Path.LineTo(x, y) for x, y in zip(xs, ys)] + \
           [cv.Path.LineTo(xs[-1], alto), cv.Path.Close()]
    linea = [cv.Path.MoveTo(xs[0], ys[0])] + [cv.Path.LineTo(x, y) for x, y in zip(xs[1:], ys[1:])]
    return cv.Canvas(shapes=[
        cv.Path(area, paint=ft.Paint(style=ft.PaintingStyle.FILL, gradient=ft.PaintLinearGradient(
            begin=(0, 0), end=(0, alto), colors=[ft.Colors.with_opacity(0.3, color), ft.Colors.with_opacity(0.0, color)]))),
        cv.Path(linea, paint=ft.Paint(color=color, stroke_width=2, style=ft.PaintingStyle.STROKE)),
    ], width=ancho, height=alto)


class PagosView:
    def __init__(self, page: ft.Page, rol: str = "dueno", firma: str = "Sistema"):
        self.page = page
        self.rol = rol
        self.firma = firma
        self.puede_planes = rol in ("dueno", "admin")
        h = repo.hoy()
        self.anio, self.mes = h.year, h.month
        self.meses_grafico = 6
        self.filtro_plan = None
        self.solo_morosos = False
        self.ver_todos_venc = False
        self.mensaje = ft.Text("", size=12.5, weight=ft.FontWeight.W_500)
        self.selector_archivo = ft.FilePicker()
        self.root = ft.Column(spacing=0)
        self._montado = False
        self._cargar()

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _cargar(self):
        try:
            self.resumen = repo.resumen(self.anio, self.mes)
            self.meses = repo.ultimos_meses(self.anio, self.mes, self.meses_grafico)
            self.planes_mes = repo.por_plan(self.anio, self.mes)
            self.pagos = repo.pagos_del_mes(self.anio, self.mes, self.filtro_plan)
            self.vencimientos = repo.vencimientos(15)
            self.planes = repo.planes()
            self.error = None
        except Exception as ex:
            self.error = str(ex)

    def _render(self):
        self.root.controls = [self._pantalla()]
        if self._montado:
            self.root.update()

    def _recargar(self):
        self._cargar()
        self._render()

    def _avisar(self, texto: str, color: str = GREEN):
        self.mensaje.value, self.mensaje.color = texto, color
        try:
            if self.mensaje.page:
                self.mensaje.update()
        except RuntimeError:
            pass

    # ══════════════ PANTALLA ══════════════
    def _pantalla(self) -> ft.Column:
        selector_mes = ft.Dropdown(
            value=f"{self.anio}-{self.mes}", width=210, dense=True, border_radius=12, border_color=GRAY_LIGHT,
            bgcolor=WHITE, text_size=13, leading_icon=ft.Icons.CALENDAR_TODAY_OUTLINED,
            options=[ft.DropdownOption(key=f"{a}-{m}", text=repo.nombre_mes(a, m)) for a, m in repo.meses_disponibles()],
            on_select=self._cambiar_mes)
        registrar = ft.Container(
            ft.Row([ft.Icon(ft.Icons.ADD, size=18, color=DARK),
                    ft.Text("Registrar pago", size=14, weight=ft.FontWeight.W_500, color=DARK)], spacing=8, tight=True),
            bgcolor=GOLD, border_radius=12, padding=ft.padding.symmetric(horizontal=22, vertical=13),
            on_click=lambda e: self._dialogo_pago(), ink=True)
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Pagos", size=13, color=TEXT_MUTED),
                ft.Text("Registro de pagos y cuotas", size=28, weight=ft.FontWeight.W_600, color=DARK,
                        font_family="Poppins", style=ft.TextStyle(height=1.15)),
                ft.Text("Controlá los pagos, vencimientos y estado de los socios en un solo lugar.",
                        size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            selector_mes, registrar,
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.END)
        if self.error:
            return ft.Column([cabecera, ft.Text(f"⚠️ No se pudo leer la base de datos: {self.error}", color=RED)],
                             spacing=20)
        return ft.Column([
            cabecera,
            ft.Row([self.mensaje], alignment=ft.MainAxisAlignment.END) if self.mensaje.value else ft.Container(),
            self._tarjetas(),
            ft.Row([ft.Container(self._evolucion(), expand=5), ft.Container(self._acciones(), expand=2)],
                   spacing=20, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row([ft.Container(self._tabla(), expand=5), ft.Container(self._proximos(), expand=2)],
                   spacing=20, vertical_alignment=ft.CrossAxisAlignment.START),
        ], spacing=20)

    def _cambiar_mes(self, e):
        self.anio, self.mes = (int(x) for x in e.control.value.split("-"))
        self._recargar()

    # ── tarjetas ──
    def _tarjetas(self) -> ft.Row:
        r = self.resumen

        def chip(texto, fondo, color, icono=None):
            return ft.Container(ft.Row(([ft.Icon(icono, size=14, color=color)] if icono else []) +
                                       [ft.Text(texto, size=12, weight=ft.FontWeight.W_600, color=color)],
                                       spacing=4, tight=True),
                                bgcolor=fondo, border_radius=12, padding=ft.padding.symmetric(horizontal=10, vertical=4))

        def cambio(valor, texto, formato):
            if valor is None:
                return ft.Text(texto, size=11.5, color=TEXT_MUTED)
            sube = valor >= 0
            fondo, color = ("#DCFCE7", "#15803D") if sube else ("#FEE2E2", "#DC2626")
            return ft.Row([chip(formato(valor), fondo, color, ft.Icons.ARROW_DROP_UP if sube else ft.Icons.ARROW_DROP_DOWN),
                           ft.Text(texto, size=11.5, color=TEXT_MUTED)], spacing=8)

        def tarjeta(icono, fondo, color, titulo, valor, pie, grafico, resaltada=False):
            return ft.Container(ft.Column([
                ft.Container(ft.Icon(icono, size=22, color=color), width=44, height=44, border_radius=22,
                             bgcolor=fondo, alignment=ft.Alignment.CENTER),
                ft.Text(titulo, size=13.5, color=DARK),
                ft.Text(valor, size=28, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.1)),
                pie,
                ft.Row([grafico], alignment=ft.MainAxisAlignment.END),
            ], spacing=8), bgcolor=GOLD_BG if resaltada else WHITE,
                border=ft.border.all(1, GOLD_LIGHT if resaltada else GRAY_LIGHT), border_radius=18,
                padding=ft.padding.only(left=20, right=20, top=18, bottom=12), expand=True, height=228)

        pct_al_dia = (r["al_dia"] / r["activos"] * 100) if r["activos"] else 0
        mes_actual = (self.anio, self.mes) == (repo.hoy().year, repo.hoy().month)
        return ft.Row([
            tarjeta(ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, GOLD_BG2, GOLD_DARK,
                    "Ingresos del mes" if mes_actual else f"Ingresos de {repo.MESES[self.mes - 1].lower()}",
                    _plata(r["ingresos"]),
                    cambio(round(r["ingresos_cambio"]) if r["ingresos_cambio"] is not None else None,
                           "vs. mes anterior" if r["ingresos_cambio"] is not None else "Sin pagos el mes anterior",
                           lambda v: f"{v:+d}%"),
                    _sparkline(r["ingresos_meses"], GOLD), resaltada=True),
            tarjeta(ft.Icons.GROUP_OUTLINED, "#DBEAFE", "#1D4ED8", "Pagos hoy", str(r["pagos_hoy"]),
                    cambio(r["pagos_hoy"] - r["pagos_ayer"], "vs. ayer", lambda v: f"{v:+d}"),
                    _sparkline(r["pagos_dias"], "#3B82F6")),
            tarjeta(ft.Icons.SCHEDULE, "#FEE2E2", "#DC2626", "Cuotas vencidas", str(r["vencidos"]),
                    chip("Urgente", "#FEE2E2", "#DC2626", ft.Icons.WARNING_AMBER_ROUNDED) if r["vencidos"]
                    else chip("Nadie debe", "#DCFCE7", "#15803D"),
                    ft.Text(f"{r['sin_plan']} socios sin plan" if r["sin_plan"] else "", size=11.5, color=TEXT_MUTED)),
            tarjeta(ft.Icons.EVENT_AVAILABLE, "#DCFCE7", "#15803D", "Socios al día", str(r["al_dia"]),
                    chip(f"{pct_al_dia:.0f}%".replace(".", ","), "#DBEAFE", "#1D4ED8"),
                    ft.Text(f"de {r['activos']} socios activos", size=11.5, color=TEXT_MUTED)),
        ], spacing=16)

    # ── evolución ──
    def _evolucion(self) -> ft.Container:
        meses = self.meses
        vmax = max([m["total"] for m in meses] + [1])
        alto = 200
        barras = []
        for m in meses:
            elegido = (m["anio"], m["mes"]) == (self.anio, self.mes)
            h = max(4, m["total"] / vmax * alto) if m["total"] else 4
            barras.append(ft.Column([
                ft.Text(_plata(m["total"]) if m["total"] else "", size=11.5, weight=ft.FontWeight.W_600, color=DARK),
                ft.Container(height=h, width=46, border_radius=ft.border_radius.only(top_left=8, top_right=8),
                             bgcolor=GOLD if elegido else ft.Colors.with_opacity(0.45, GOLD),
                             tooltip=f"{repo.nombre_mes(m['anio'], m['mes'])}: {_plata(m['total'])} · {m['pagos']} pagos"),
                ft.Text(m["etiqueta"], size=11.5, color=DARK if elegido else TEXT_MUTED,
                        weight=ft.FontWeight.W_500 if elegido else ft.FontWeight.W_400),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.END, spacing=6,
                expand=True))
        escala = ft.Column([ft.Text(_plata_corta(vmax * (4 - i) / 4), size=10.5, color=TEXT_MUTED)
                            for i in range(5)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, height=alto + 4)
        grafico = ft.Row([ft.Container(escala, padding=ft.padding.only(bottom=26, top=20)),
                          ft.Row(barras, spacing=8, expand=True, vertical_alignment=ft.CrossAxisAlignment.END,
                                 height=alto + 50)], spacing=10, vertical_alignment=ft.CrossAxisAlignment.END)
        periodo = ft.Dropdown(
            value=str(self.meses_grafico), width=170, dense=True, border_radius=12, border_color=GRAY_LIGHT, text_size=12.5,
            options=[ft.DropdownOption(key=str(k), text=t) for k, t in ((3, "Últimos 3 meses"), (6, "Últimos 6 meses"),
                                                                         (12, "Últimos 12 meses"))],
            on_select=self._cambiar_meses)
        # resumen por plan del mes elegido
        filas = []
        for p in self.planes_mes:
            filas.append(ft.Container(ft.Row([
                ft.Container(width=10, height=10, border_radius=5, bgcolor=COLOR_PLAN.get(p["plan"], GOLD)),
                ft.Column([ft.Text(p["plan"], size=13, color=DARK),
                           ft.Text(f"{p['pagos']} {'pago' if p['pagos'] == 1 else 'pagos'}", size=11, color=TEXT_MUTED)],
                          spacing=0, expand=True),
                ft.Column([ft.Text(f"{p['porcentaje']:.0f}%", size=13, weight=ft.FontWeight.W_600, color=DARK),
                           ft.Text(_plata(p["total"]), size=11, color=TEXT_MUTED)], spacing=0,
                          horizontal_alignment=ft.CrossAxisAlignment.END),
            ], spacing=10), padding=ft.padding.symmetric(vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT))))
        resumen = ft.Container(ft.Column([
            ft.Text("Resumen por plan", size=13, weight=ft.FontWeight.W_600, color=DARK),
            ft.Text(repo.nombre_mes(self.anio, self.mes), size=11, color=TEXT_MUTED),
            *(filas or [ft.Text("Sin pagos este mes.", size=12, color=TEXT_MUTED)]),
        ], spacing=4), width=230, bgcolor="#FBFAF6", border_radius=14, padding=14)
        return _tarjeta(ft.Column([
            _titulo(ft.Icons.INSIGHTS, "Evolución de ingresos", periodo),
            ft.Row([ft.Container(grafico, expand=True), resumen], spacing=18,
                   vertical_alignment=ft.CrossAxisAlignment.START),
        ], spacing=16))

    def _cambiar_meses(self, e):
        self.meses_grafico = int(e.control.value)
        self._recargar()

    # ── acciones rápidas ──
    def _acciones(self) -> ft.Container:
        def accion(icono, fondo, color, titulo, sub, al_tocar):
            return ft.Container(ft.Row([
                ft.Container(ft.Icon(icono, size=21, color=color), width=44, height=44, border_radius=22,
                             bgcolor=fondo, alignment=ft.Alignment.CENTER),
                ft.Column([ft.Text(titulo, size=13, weight=ft.FontWeight.W_600, color=DARK),
                           ft.Text(sub, size=11.5, color=TEXT_MUTED)], spacing=1, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=TEXT_MUTED),
            ], spacing=12), bgcolor="#FBFAF6", border_radius=14, padding=12, ink=True, on_click=al_tocar)

        vencidos = self.resumen["vencidos"]
        lista = [
            accion(ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, GOLD_BG2, GOLD_DARK, "Registrar pago",
                   "Cobro en el mostrador y renovación", lambda e: self._dialogo_pago()),
            accion(ft.Icons.WARNING_AMBER_ROUNDED, "#FEE2E2", "#DC2626", "Ver socios morosos",
                   f"{vencidos} con la cuota vencida" if vencidos else "Nadie tiene la cuota vencida",
                   lambda e: self._dialogo_morosos()),
            accion(ft.Icons.DOWNLOAD_OUTLINED, "#DBEAFE", "#1D4ED8", "Exportar pagos del mes",
                   f"CSV para Excel · {repo.nombre_mes(self.anio, self.mes)}", lambda e: self._exportar()),
        ]
        if self.puede_planes:
            lista.append(accion(ft.Icons.TUNE, "#EDE9FE", "#6D28D9", "Configurar planes",
                                "Precio y duración (también en la app)", lambda e: self._dialogo_planes()))
        return _tarjeta(ft.Column([_titulo(ft.Icons.BOLT, "Acciones rápidas"), *lista], spacing=10))

    # ── últimos pagos ──
    def _tabla(self) -> ft.Container:
        filtro = ft.Dropdown(
            value=self.filtro_plan or "todos", width=180, dense=True, border_radius=12, border_color=GRAY_LIGHT,
            text_size=12.5, options=[ft.DropdownOption(key="todos", text="Todos los planes")] +
                                    [ft.DropdownOption(key=p["nombre"], text=p["nombre"]) for p in self.planes],
            on_select=self._cambiar_plan)
        cols = [("SOCIO", 4), ("PLAN", 2), ("FECHA DE PAGO", 2), ("MONTO", 2), ("MÉTODO", 3), ("ESTADO", 2)]
        encabezado = ft.Container(ft.Row([ft.Text(t, size=11, weight=ft.FontWeight.W_500, color=TEXT_MUTED, expand=p)
                                          for t, p in cols] + [ft.Container(width=40)], spacing=10),
                                  padding=ft.padding.symmetric(horizontal=4, vertical=8))
        filas = []
        for p in self.pagos:
            pagado = p["estado"] == "Aprobado"
            estado = ft.Container(ft.Row([ft.Icon(ft.Icons.CHECK_BOX if pagado else ft.Icons.BLOCK, size=13,
                                                  color="#15803D" if pagado else "#DC2626"),
                                          ft.Text("Pagado" if pagado else p["estado"], size=11.5,
                                                  weight=ft.FontWeight.W_500, color="#15803D" if pagado else "#DC2626")],
                                         spacing=4, tight=True),
                                  bgcolor="#DCFCE7" if pagado else "#FEE2E2", border_radius=10,
                                  padding=ft.padding.symmetric(horizontal=8, vertical=3))
            menu = ft.PopupMenuButton(icon=ft.Icons.MORE_VERT, icon_color=DARK, tooltip="Más opciones", items=[
                ft.PopupMenuItem(content=ft.Text("🧾  Ver detalle"), on_click=lambda e, x=p: self._dialogo_detalle(x)),
                ft.PopupMenuItem(content=ft.Text("🚫  Anular pago", color=RED), disabled=not pagado,
                                 on_click=lambda e, x=p: self._confirmar_anular(x)),
            ])
            filas.append(ft.Container(ft.Row([
                ft.Row([_avatar(p["socio"], p["id_socio"], 34),
                        ft.Text(p["socio"], size=13, weight=ft.FontWeight.W_500, color=DARK, expand=True,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)], spacing=10, expand=4),
                ft.Text(p["plan"], size=12.5, color=TEXT_MUTED, expand=2),
                ft.Text(p["fecha_pago"].astimezone().strftime("%d/%m/%Y"), size=12.5, color=TEXT_MUTED, expand=2),
                ft.Text(_plata(p["monto"]), size=13, weight=ft.FontWeight.W_600,
                        color=GOLD_DARK if pagado else TEXT_MUTED, expand=2),
                ft.Row([ft.Icon(ICONO_METODO.get(p["metodo"], ft.Icons.PAYMENT), size=16, color=TEXT_MUTED),
                        ft.Text(p["metodo"], size=12.5, color=TEXT_MUTED, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS, expand=True)], spacing=6, expand=3),
                ft.Container(estado, expand=2),
                ft.Container(menu, width=40),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=4, vertical=6),
                border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT))))
        vacio = ft.Container(ft.Column([
            ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=38, color=GRAY),
            ft.Text(f"No hay pagos registrados en {repo.nombre_mes(self.anio, self.mes).lower()}"
                    + (f" del plan {self.filtro_plan}" if self.filtro_plan else "") + ".", size=13, color=TEXT_MUTED),
            ft.Text("Los cobros de Mercado Pago aparecen solos; los del mostrador se cargan con \"Registrar pago\".",
                    size=11.5, color=TEXT_MUTED),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30, alignment=ft.Alignment.CENTER,
            border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)))
        total = sum(p["monto"] for p in self.pagos if p["estado"] == "Aprobado")
        return _tarjeta(ft.Column([
            _titulo(ft.Icons.RECEIPT_LONG_OUTLINED, "Últimos pagos", filtro),
            ft.Text(f"{repo.nombre_mes(self.anio, self.mes)} · {len(self.pagos)} pagos · {_plata(total)} cobrado",
                    size=12, color=TEXT_MUTED),
            encabezado, *(filas or [vacio]),
        ], spacing=8))

    def _cambiar_plan(self, e):
        self.filtro_plan = None if e.control.value == "todos" else e.control.value
        self._recargar()

    # ── próximos vencimientos ──
    def _proximos(self) -> ft.Container:
        lista = self.vencimientos if self.ver_todos_venc else self.vencimientos[:5]
        filas = []
        for v in lista:
            d = v["dias"]
            if d < 0:
                texto, fondo, color = f"Venció hace {-d} {'día' if d == -1 else 'días'}", "#FEE2E2", "#DC2626"
            elif d == 0:
                texto, fondo, color = "Vence hoy", "#FEE2E2", "#DC2626"
            elif d <= 3:
                texto, fondo, color = f"{d} {'día' if d == 1 else 'días'}", "#FEF3C7", "#B45309"
            else:
                texto, fondo, color = f"{d} días", "#DBEAFE", "#1D4ED8"
            filas.append(ft.Container(ft.Row([
                _avatar(v["socio"], v["id_socio"], 38),
                ft.Column([ft.Text(v["socio"], size=13, weight=ft.FontWeight.W_600, color=DARK, max_lines=1,
                                   overflow=ft.TextOverflow.ELLIPSIS),
                           ft.Text(f"{v['plan']} · {v['vencimiento']:%d/%m/%Y}", size=11, color=TEXT_MUTED),
                           ft.Container(ft.Text(texto, size=10.5, weight=ft.FontWeight.W_600, color=color),
                                        bgcolor=fondo, border_radius=10,
                                        padding=ft.padding.symmetric(horizontal=8, vertical=2))], spacing=2, expand=True),
                ft.Container(ft.Text("Cobrar", size=12, weight=ft.FontWeight.W_500, color=GOLD_DARK), bgcolor=GOLD_BG2,
                             border_radius=10, padding=ft.padding.symmetric(horizontal=12, vertical=7), ink=True,
                             on_click=lambda e, x=v: self._dialogo_pago(x["id_socio"], x["plan"]),
                             tooltip="Registrar el pago y renovar"),
            ], spacing=10), padding=ft.padding.symmetric(vertical=8),
                border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT))))
        ver = ft.TextButton("Ver menos" if self.ver_todos_venc else "Ver todos",
                            on_click=self._alternar_venc, style=ft.ButtonStyle(color=GOLD_DARK)) \
            if len(self.vencimientos) > 5 else None
        return _tarjeta(ft.Column([
            _titulo(ft.Icons.EVENT_NOTE_OUTLINED, "Próximos vencimientos", ver),
            ft.Text("Vencidas y las que vencen en los próximos 15 días.", size=11.5, color=TEXT_MUTED),
            *(filas or [ft.Text("No vence ninguna membresía en los próximos 15 días.", size=12, color=TEXT_MUTED)]),
        ], spacing=6))

    def _alternar_venc(self, e):
        self.ver_todos_venc = not self.ver_todos_venc
        self._render()

    # ══════════════ DIÁLOGOS ══════════════
    def _dialogo_pago(self, id_socio: int | None = None, plan: str | None = None):
        try:
            socios = repo.socios()
        except Exception as ex:
            self._avisar(f"No se pudieron leer los socios: {ex}", RED)
            return
        por_id = {s["id_socio"]: s for s in socios}
        precios = {p["nombre"]: p for p in self.planes}
        error = ft.Text("", size=12, color=RED)
        renueva = ft.Text("", size=11.5, color=TEXT_MUTED)
        campo_socio = ft.Dropdown(
            label="Socio", value=str(id_socio) if id_socio in por_id else None, editable=True, enable_filter=True,
            width=420, menu_height=320, border_radius=10,
            options=[ft.DropdownOption(key=str(s["id_socio"]), text=f"{s['nombre']} · {s['email']}") for s in socios])
        campo_plan = ft.Dropdown(label="Plan", width=200, border_radius=10,
                                 value=plan or (por_id[id_socio]["plan"] if id_socio in por_id else None),
                                 options=[ft.DropdownOption(key=p["nombre"], text=f"{p['nombre']} · {_plata(p['precio'])}")
                                          for p in self.planes])
        campo_monto = ft.TextField(label="Monto", prefix="$ ", width=200, border_radius=10,
                                   keyboard_type=ft.KeyboardType.NUMBER,
                                   value=f"{precios[campo_plan.value]['precio']:.0f}" if campo_plan.value in precios else "")
        campo_metodo = ft.Dropdown(label="Medio de pago", value="Efectivo", width=200, border_radius=10,
                                   options=[ft.DropdownOption(key=m, text=m) for m in repo.METODOS])
        campo_fecha = ft.TextField(label="Fecha (dd/mm/aaaa)", value=repo.hoy().strftime("%d/%m/%Y"), width=200,
                                   border_radius=10)
        campo_comprobante = ft.TextField(label="N° de comprobante (opcional)", width=420, border_radius=10)
        renovar = ft.Checkbox(label="Renovar la membresía con este pago", value=True, active_color=GOLD)

        def fecha():
            try:
                return datetime.strptime((campo_fecha.value or "").strip(), "%d/%m/%Y").date()
            except ValueError:
                return None

        def actualizar_renovacion(e=None):
            s = por_id.get(int(campo_socio.value)) if (campo_socio.value or "").isdigit() else None
            p = precios.get(campo_plan.value)
            f = fecha()
            if not (renovar.value and s and p and f):
                renueva.value = "" if renovar.value else "Solo se registra el cobro; la membresía no cambia."
            else:
                desde = s["vencimiento"] if (s["vencimiento"] and s["vencimiento"] >= f and s["plan"] == p["nombre"]) else f
                from datetime import timedelta
                renueva.value = (f"Queda activa hasta el {desde + timedelta(days=p['duracion_dias']):%d/%m/%Y}"
                                 + (" (se suma a los días que le quedan)." if desde != f else "."))
            try:
                renueva.update()
            except RuntimeError:
                pass

        def elegir_socio(e):
            s = por_id.get(int(campo_socio.value)) if (campo_socio.value or "").isdigit() else None
            if s and s["plan"] and not campo_plan.value:
                campo_plan.value = s["plan"]
                elegir_plan(None)
            actualizar_renovacion()

        def elegir_plan(e):
            if campo_plan.value in precios:
                campo_monto.value = f"{precios[campo_plan.value]['precio']:.0f}"
                try:
                    campo_monto.update()
                    campo_plan.update()
                except RuntimeError:
                    pass
            actualizar_renovacion()

        campo_socio.on_select = elegir_socio
        campo_plan.on_select = elegir_plan
        campo_fecha.on_change = actualizar_renovacion
        renovar.on_change = actualizar_renovacion
        actualizar_renovacion()

        def guardar(e):
            if not (campo_socio.value or "").isdigit() or int(campo_socio.value) not in por_id:
                error.value = "Elegí un socio de la lista."
            elif campo_plan.value not in precios:
                error.value = "Elegí el plan."
            elif fecha() is None or fecha() > repo.hoy():
                error.value = "Revisá la fecha (dd/mm/aaaa, no puede ser futura)."
            else:
                try:
                    monto = float((campo_monto.value or "").replace(".", "").replace(",", "."))
                    resultado = repo.registrar_pago(int(campo_socio.value), campo_plan.value, monto,
                                                    campo_metodo.value, fecha(), campo_comprobante.value,
                                                    bool(renovar.value), self.firma)
                except ValueError as ex:
                    error.value = str(ex) if str(ex) else "El monto tiene que ser un número."
                except Exception as ex:
                    error.value = f"No se pudo guardar: {ex}"
                else:
                    self.page.pop_dialog()
                    nombre = por_id[int(campo_socio.value)]["nombre"]
                    self.mensaje.value = f"✓ Pago de {nombre} registrado" + \
                        (f" · activa hasta el {resultado['vence']:%d/%m/%Y}" if resultado["vence"] else "")
                    self.mensaje.color = GREEN
                    self._recargar()
                    return
            error.update()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar pago", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Column([campo_socio, ft.Row([campo_plan, campo_monto], spacing=20),
                               ft.Row([campo_metodo, campo_fecha], spacing=20), campo_comprobante,
                               renovar, renueva, error], spacing=14, tight=True, width=420),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.FilledButton("Registrar pago", on_click=guardar,
                                     style=ft.ButtonStyle(bgcolor=GOLD, color=DARK))],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def _dialogo_morosos(self):
        morosos = [v for v in self.vencimientos if v["dias"] < 0]
        try:
            morosos = [v for v in repo.vencimientos(0) if v["dias"] < 0]
        except Exception:
            pass
        filas = [ft.Row([
            _avatar(v["socio"], v["id_socio"], 34),
            ft.Column([ft.Text(v["socio"], size=13, weight=ft.FontWeight.W_500, color=DARK),
                       ft.Text(f"{v['plan']} · venció el {v['vencimiento']:%d/%m/%Y} (hace {-v['dias']} días)"
                               + (f" · {v['telefono']}" if v["telefono"] else ""), size=11.5, color=TEXT_MUTED)],
                      spacing=0, expand=True),
            ft.Text(_plata(v["precio"]), size=13, weight=ft.FontWeight.W_600, color="#DC2626"),
            ft.TextButton("Cobrar", on_click=lambda e, x=v: (self.page.pop_dialog(),
                                                             self._dialogo_pago(x["id_socio"], x["plan"])),
                          style=ft.ButtonStyle(color=GOLD_DARK)),
        ], spacing=12) for v in morosos]
        total = sum(v["precio"] for v in morosos)
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text("Socios morosos", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Column([
                ft.Text(f"{len(morosos)} con la cuota vencida · {_plata(total)} por cobrar" if morosos
                        else "Nadie tiene la cuota vencida.", size=12.5, color=TEXT_MUTED),
                *filas,
            ], spacing=12, tight=True, width=520, scroll=ft.ScrollMode.AUTO),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.page.pop_dialog())],
        ))

    def _dialogo_detalle(self, p: dict):
        def fila(titulo, valor):
            return ft.Row([ft.Text(titulo, size=12.5, color=TEXT_MUTED, width=150),
                           ft.Text(valor, size=13, color=DARK, expand=True)])
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text(f"Pago de {p['socio']}", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Column([
                fila("Monto", _plata(p["monto"])),
                fila("Plan", p["plan"]),
                fila("Fecha", p["fecha_pago"].astimezone().strftime("%d/%m/%Y %H:%M")),
                fila("Medio de pago", f"{p['metodo']} ({p['proveedor']})" if p["proveedor"] else p["metodo"]),
                fila("Comprobante", p["numero_comprobante"] or "—"),
                fila("Cubre hasta", p["fecha_vencimiento"].strftime("%d/%m/%Y") if p["fecha_vencimiento"] else "—"),
                fila("Estado", "Pagado" if p["estado"] == "Aprobado" else p["estado"]),
            ], spacing=10, tight=True, width=420),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.page.pop_dialog())],
        ))

    def _confirmar_anular(self, p: dict):
        def anular(e):
            self.page.pop_dialog()
            try:
                repo.anular_pago(p["id_pago"])
                self.mensaje.value, self.mensaje.color = f"Pago de {p['socio']} anulado", GOLD_DARK
            except Exception as ex:
                self.mensaje.value, self.mensaje.color = f"No se pudo anular: {ex}", RED
            self._recargar()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Anular este pago?", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text(f"{_plata(p['monto'])} de {p['socio']} ({p['fecha_pago'].astimezone():%d/%m/%Y}). "
                            "Deja de contar en los ingresos pero queda en el historial. La membresía no se modifica: "
                            "si hace falta, cambiala en Membresías.", size=13, color=TEXT_MUTED, width=420),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.TextButton("Anular pago", on_click=anular, style=ft.ButtonStyle(color=RED))],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def _dialogo_planes(self):
        campos = []
        error = ft.Text("", size=12, color=RED)
        for p in self.planes:
            precio = ft.TextField(value=f"{p['precio']:.0f}", prefix="$ ", width=150, dense=True, border_radius=10,
                                  label="Precio", keyboard_type=ft.KeyboardType.NUMBER)
            dias = ft.TextField(value=str(p["duracion_dias"]), suffix="días", width=120, dense=True, border_radius=10,
                                label="Duración", keyboard_type=ft.KeyboardType.NUMBER)
            campos.append((p, precio, dias))

        def guardar(e):
            cambios = []
            for p, precio, dias in campos:
                try:
                    nuevo_precio = float((precio.value or "").replace(".", "").replace(",", "."))
                    nuevos_dias = int(dias.value)
                except ValueError:
                    error.value = f"Revisá los números de {p['nombre']}."
                    error.update()
                    return
                if nuevo_precio <= 0 or nuevos_dias <= 0:
                    error.value = f"El precio y los días de {p['nombre']} tienen que ser mayores a cero."
                    error.update()
                    return
                if nuevo_precio != p["precio"] or nuevos_dias != p["duracion_dias"]:
                    cambios.append((p, nuevo_precio, nuevos_dias))
            try:
                for p, nuevo_precio, nuevos_dias in cambios:
                    repo.actualizar_plan(p["id_membresia"], nuevo_precio, nuevos_dias)
            except Exception as ex:
                error.value = f"No se pudo guardar: {ex}"
                error.update()
                return
            self.page.pop_dialog()
            self.mensaje.value = f"✓ {len(cambios)} {'plan actualizado' if len(cambios) == 1 else 'planes actualizados'}" \
                if cambios else "No hubo cambios en los planes"
            self.mensaje.color = GREEN
            self._recargar()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Configurar planes", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Column([
                ft.Text("Es el mismo catálogo que ve la app: Mercado Pago cobra estos precios. Los pagos ya hechos "
                        "no cambian.", size=12, color=TEXT_MUTED),
                *[ft.Row([ft.Container(width=12, height=12, border_radius=6, bgcolor=COLOR_PLAN.get(p["nombre"], GOLD)),
                          ft.Text(p["nombre"], size=14, weight=ft.FontWeight.W_500, color=DARK, expand=True),
                          precio, dias], spacing=12) for p, precio, dias in campos],
                error,
            ], spacing=14, tight=True, width=460),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.FilledButton("Guardar", on_click=guardar, style=ft.ButtonStyle(bgcolor=GOLD, color=DARK))],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    # ── exportar ──
    def _exportar(self):
        nombre = f"pagos_{self.anio}_{self.mes:02d}.csv"

        async def elegir():
            if self.selector_archivo not in self.page.services:
                self.page.services.append(self.selector_archivo)
            ruta = await self.selector_archivo.save_file(dialog_title="Guardar pagos del mes", file_name=nombre,
                                                         allowed_extensions=["csv"])
            if not ruta:
                return
            if not ruta.lower().endswith(".csv"):
                ruta += ".csv"
            try:
                cantidad = repo.exportar_csv(ruta, self.anio, self.mes)
                self._avisar(f"✓ {cantidad} pagos exportados a {os.path.basename(ruta)}")
            except Exception as ex:
                self._avisar(f"No se pudo exportar: {ex}", RED)
            self._render()
        self.page.run_task(elegir)


def build_pagos(page: ft.Page = None, rol: str = "dueno", firma: str = "Sistema") -> ft.Column:
    return PagosView(page, rol, firma).build()
