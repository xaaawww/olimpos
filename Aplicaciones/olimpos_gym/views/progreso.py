# OLIMPOS GYM — Progreso físico
#
# Primero, un listado simple de socios (nombre, último entrenamiento y días
# entrenados en las últimas 4 semanas). Al tocar uno se abre su progreso:
#   - tarjetas: peso, días entrenados, volumen e IMC (o series)
#   - evolución (volumen semanal, series por semana o peso) dibujada a mano
#   - últimos entrenamientos
#   - trabajo por músculo sobre el MISMO bodygraph del editor de ejercicios:
#     cada zona se pinta más fuerte cuanto más series efectivas recibió
#   - "Qué cambiar": recomendaciones para ajustar la rutina
#   - progreso por ejercicio (1RM estimado, si avanza o está estancado)
# Los cálculos están en progreso_repo.py.

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))

import flet as ft
import flet.canvas as cv
from theme import *
import ejercicios_repo
import progreso_repo as repo
from editor_ejercicios import _zona_en_punto

CUERPO_W, CUERPO_H = 120, 240
ASSET_W, ASSET_H = 400, 800
COLOR_GRUPO = {
    "Pecho": "#F59E0B", "Espalda": "#3B82F6", "Piernas": "#22C55E",
    "Hombros": "#F97316", "Brazos": "#EC4899", "Core": "#8B5CF6",
}
NIVEL = {"alta": ("#FEE2E2", "#DC2626"), "media": ("#FEF3C7", "#B45309"), "baja": ("#DCFCE7", "#15803D")}
OBJETIVO = {"FUERZA": "Fuerza", "HIPERTROFIA": "Ganar músculo", "SALUD": "Salud"}


def _num(v: float, dec: int = 0) -> str:
    texto = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return texto


def _volumen(v: float) -> str:
    return f"{_num(v / 1000, 1)} t" if v >= 10000 else f"{_num(v)} kg"


def _hace(dias: int | None) -> str:
    if dias is None:
        return "Sin entrenamientos"
    if dias == 0:
        return "Hoy"
    if dias == 1:
        return "Ayer"
    return f"Hace {dias} días"


def _iniciales(nombre: str) -> str:
    partes = [p for p in nombre.split() if p]
    return ((partes[0][0] + (partes[1][0] if len(partes) > 1 else "")) if partes else "?").upper()


def _tarjeta(contenido: ft.Control, padding: int = 22, expand=None) -> ft.Container:
    return ft.Container(contenido, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=18,
                        padding=padding, expand=expand)


def _titulo_tarjeta(icono, texto: str, derecha: ft.Control | None = None) -> ft.Row:
    return ft.Row([
        ft.Container(ft.Icon(icono, size=19, color=GOLD_DARK), width=36, height=36, border_radius=18,
                     bgcolor=GOLD_BG2, alignment=ft.Alignment.CENTER),
        ft.Text(texto, size=16, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins", expand=True),
    ] + ([derecha] if derecha else []), spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)


class Grafico(ft.Container):
    """Gráfico de línea con área (sin librerías: se dibuja en un Canvas y se
    vuelve a dibujar al cambiar de tamaño)."""

    def __init__(self, valores: list[float], etiquetas: list[str], unidad: str, color: str, alto: int = 230):
        self.valores, self.etiquetas, self.unidad, self.color = valores, etiquetas, unidad, color
        self.lienzo = cv.Canvas(shapes=self._formas(560, alto), height=alto, expand=True,
                                on_resize=self._redimensionar)
        self.alto = alto
        super().__init__(content=self.lienzo, height=alto)

    def _redimensionar(self, e):
        self.lienzo.shapes = self._formas(e.width, self.alto)
        self.lienzo.update()

    def _formas(self, ancho: float, alto: float) -> list:
        izq, der, arriba, abajo = 48, 16, 14, 28
        w, h = max(ancho - izq - der, 10), alto - arriba - abajo
        vals = self.valores or [0]
        vmax = max(vals) or 1
        vmin = min(vals) if self.unidad == "kg" and min(vals) > 0 else 0
        if self.unidad == "kg" and vmin:                       # peso: escala ajustada al rango
            margen = max(1.0, (vmax - vmin) * 0.25)
            vmin, vmax = vmin - margen, vmax + margen
        rango = (vmax - vmin) or 1
        gris = ft.Paint(color=GRAY_LIGHT, stroke_width=1)
        texto = ft.TextStyle(size=10.5, color=TEXT_MUTED)
        formas = []
        for i in range(5):                                      # líneas de fondo y escala
            y = arriba + h * i / 4
            valor = vmax - rango * i / 4
            formas.append(cv.Line(izq, y, izq + w, y, gris))
            etiqueta = _volumen(valor) if self.unidad == "vol" else _num(valor, 1 if self.unidad == "kg" else 0)
            formas.append(cv.Text(izq - 8, y, etiqueta, texto, alignment=ft.Alignment.CENTER_RIGHT))
        n = len(vals)
        xs = [izq + (w * i / (n - 1) if n > 1 else w / 2) for i in range(n)]
        ys = [arriba + h - (v - vmin) / rango * h for v in vals]
        paso = max(1, n // 6)                                  # etiquetas del eje x sin amontonar
        for i in range(0, n, paso):
            formas.append(cv.Text(xs[i], arriba + h + 16, self.etiquetas[i], texto, alignment=ft.Alignment.CENTER))
        if n > 1:
            area = [cv.Path.MoveTo(xs[0], arriba + h)] + [cv.Path.LineTo(x, y) for x, y in zip(xs, ys)] + \
                   [cv.Path.LineTo(xs[-1], arriba + h), cv.Path.Close()]
            formas.append(cv.Path(area, paint=ft.Paint(style=ft.PaintingStyle.FILL, gradient=ft.PaintLinearGradient(
                begin=(0, arriba), end=(0, arriba + h), colors=[ft.Colors.with_opacity(0.28, self.color),
                                                                 ft.Colors.with_opacity(0.02, self.color)]))))
            linea = [cv.Path.MoveTo(xs[0], ys[0])] + [cv.Path.LineTo(x, y) for x, y in zip(xs[1:], ys[1:])]
            formas.append(cv.Path(linea, paint=ft.Paint(color=self.color, stroke_width=2.5,
                                                        style=ft.PaintingStyle.STROKE)))
        for i, (x, y) in enumerate(zip(xs, ys)):
            ultimo = i == n - 1
            formas.append(cv.Circle(x, y, 5 if ultimo else 3.5, ft.Paint(color=WHITE if ultimo else self.color)))
            if ultimo:
                formas.append(cv.Circle(x, y, 5, ft.Paint(color=DARK, stroke_width=2, style=ft.PaintingStyle.STROKE)))
        if vals and n:
            etiqueta = _volumen(vals[-1]) if self.unidad == "vol" else \
                f"{_num(vals[-1], 1)} kg" if self.unidad == "kg" else f"{_num(vals[-1], 1)}"
            formas.append(cv.Text(xs[-1] - 4, ys[-1] - 12, etiqueta,
                                  ft.TextStyle(size=11.5, weight=ft.FontWeight.W_600, color=DARK),
                                  alignment=ft.Alignment.BOTTOM_RIGHT))
        return formas


def _mini_linea(valores: list[float], color: str) -> ft.Control:
    """Línea chiquita (tendencia de un ejercicio)."""
    w, h = 90, 26
    if len(valores) < 2:
        return ft.Container(ft.Text("—", size=12, color=TEXT_MUTED), width=w)
    vmin, vmax = min(valores), max(valores)
    rango = (vmax - vmin) or 1
    xs = [w * i / (len(valores) - 1) for i in range(len(valores))]
    ys = [h - 3 - (v - vmin) / rango * (h - 6) for v in valores]
    camino = [cv.Path.MoveTo(xs[0], ys[0])] + [cv.Path.LineTo(x, y) for x, y in zip(xs[1:], ys[1:])]
    return cv.Canvas(shapes=[cv.Path(camino, paint=ft.Paint(color=color, stroke_width=2, style=ft.PaintingStyle.STROKE)),
                             cv.Circle(xs[-1], ys[-1], 3, ft.Paint(color=color))], width=w, height=h)


class ProgresoView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.socios, self.error = [], None
        self.busqueda = ""
        self.sel = None
        self.dias = 90
        self.metrica = "volumen"
        self.datos = None
        self.nombre_hover = ft.Text("Pasá el mouse por el cuerpo", size=12, color=TEXT_MUTED)
        self.root = ft.Column(spacing=0)
        self._montado = False
        self.buscador = ft.TextField(
            hint_text="Buscar socio...", prefix_icon=ft.Icons.SEARCH, dense=True, border_radius=12,
            border_color=GRAY_LIGHT, bgcolor=WHITE, on_change=self._buscar, width=340,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=13))
        self._cargar_lista()

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls = [self._detalle() if self.sel else self._lista()]
        if self._montado:
            self.root.update()

    # ══════════════════ LISTADO ══════════════════
    def _cargar_lista(self):
        try:
            self.socios = repo.lista_socios()
            self.error = None
        except Exception as ex:
            self.socios, self.error = [], str(ex)

    def _buscar(self, e):
        self.busqueda = (e.control.value or "").strip().lower()
        self._render()

    def _lista(self) -> ft.Column:
        from datetime import date
        visibles = [s for s in self.socios if self.busqueda in s["nombre"].lower()
                    or self.busqueda in (s["email"] or "").lower()]
        filas = []
        for i, s in enumerate(visibles):
            dias = (date.today() - s["ultimo"]).days if s["ultimo"] else None
            activo = s["dias_28"] or 0
            puntos = ft.Row([ft.Container(width=7, height=7, border_radius=4,
                                          bgcolor=GOLD if k < min(activo, 12) else GRAY_LIGHT) for k in range(12)],
                            spacing=3, tight=True)
            filas.append(ft.Container(
                ft.Row([
                    ft.Container(ft.Text(_iniciales(s["nombre"]), size=13, weight=ft.FontWeight.W_600, color=GOLD_DARK),
                                 width=40, height=40, border_radius=20, bgcolor=GOLD_BG2, alignment=ft.Alignment.CENTER),
                    ft.Column([ft.Text(s["nombre"], size=14, weight=ft.FontWeight.W_500, color=DARK),
                               ft.Text(s["email"] or "", size=11.5, color=TEXT_MUTED)], spacing=0, expand=4),
                    ft.Text(_hace(dias), size=13, color=DARK if dias is not None else TEXT_MUTED, expand=3),
                    ft.Container(ft.Row([puntos, ft.Text(f"{activo} {'día' if activo == 1 else 'días'}", size=12,
                                                         color=TEXT_MUTED)], spacing=10), expand=3),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=20, color=TEXT_MUTED),
                ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=20, vertical=12), ink=True,
                border=None if i == 0 else ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
                on_click=lambda e, sid=s["id_socio"]: self._abrir(sid),
            ))
        encabezado = ft.Container(ft.Row([
            ft.Container(width=40),
            ft.Text("SOCIO", size=11.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED, expand=4),
            ft.Text("ÚLTIMO ENTRENAMIENTO", size=11.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED, expand=3),
            ft.Text("ÚLTIMAS 4 SEMANAS", size=11.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED, expand=3),
            ft.Container(width=20),
        ], spacing=14), padding=ft.padding.only(left=20, right=20, top=14, bottom=4))
        tabla = ft.Container(ft.Column([encabezado, ft.Divider(height=1, color=GRAY_LIGHT)] + (filas or [
            ft.Container(ft.Text("Ningún socio coincide con la búsqueda.", size=13, color=TEXT_MUTED), padding=20)]),
            spacing=0), bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS)
        controles = [
            ft.Row([ft.Column([
                ft.Text("Entrenamiento", size=13, color=TEXT_MUTED),
                ft.Text("Progreso físico", size=28, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.15)),
                ft.Text("Elegí un socio para ver su evolución, qué músculos trabaja y qué conviene cambiar en su rutina.",
                        size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True), self.buscador], vertical_alignment=ft.CrossAxisAlignment.END),
        ]
        if self.error:
            controles.append(ft.Text(f"⚠️ No se pudo leer la base de datos: {self.error}", size=12, color=RED))
        controles.append(tabla)
        return ft.Column(controles, spacing=22)

    # ══════════════════ DETALLE ══════════════════
    def _abrir(self, id_socio: int):
        self.sel = id_socio
        self._cargar_detalle()
        self._render()

    def _volver(self, e=None):
        self.sel, self.datos = None, None
        self._render()

    def _cargar_detalle(self):
        try:
            self.datos = repo.detalle(self.sel, self.dias)
            self.error = None
        except Exception as ex:
            self.datos, self.error = None, str(ex)

    def _cambiar_periodo(self, e):
        self.dias = int(e.control.value)
        self._cargar_detalle()
        self._render()

    def _cambiar_metrica(self, clave: str):
        self.metrica = clave
        self._render()

    def _detalle(self) -> ft.Column:
        volver = ft.Container(ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16, color=DARK),
                                      ft.Text("Volver al listado", size=13, color=DARK)], spacing=8, tight=True),
                              on_click=self._volver, ink=True, border_radius=8, padding=4)
        if not self.datos:
            return ft.Column([volver, ft.Text(f"⚠️ No se pudo cargar el progreso: {self.error}", color=RED)], spacing=16)
        d = self.datos
        socio = d["socio"]
        periodo = ft.Dropdown(
            value=str(self.dias), width=210, dense=True, border_radius=12, border_color=GRAY_LIGHT, bgcolor=WHITE,
            text_size=13, leading_icon=ft.Icons.CALENDAR_TODAY_OUTLINED,
            options=[ft.DropdownOption(key=str(k), text=v) for k, v in repo.PERIODOS.items()],
            on_select=self._cambiar_periodo)
        subtitulo = [f"Objetivo: {OBJETIVO.get(socio['objetivo'], 'sin definir')}"]
        if socio.get("nivel_experiencia"):
            subtitulo.append(f"Nivel {socio['nivel_experiencia'].lower()}")
        if socio.get("registro"):
            subtitulo.append(f"Socio desde {socio['registro']:%d/%m/%Y}")
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Progreso físico", size=13, color=TEXT_MUTED),
                ft.Text(socio["nombre"], size=28, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.15)),
                ft.Text(" · ".join(subtitulo), size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            periodo,
        ], vertical_alignment=ft.CrossAxisAlignment.END)
        return ft.Column([
            volver, cabecera, self._tarjetas(),
            ft.Row([ft.Container(self._evolucion(), expand=3), ft.Container(self._sesiones(), expand=2)],
                   spacing=20, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row([ft.Container(self._musculos(), expand=3), ft.Container(self._recomendaciones(), expand=2)],
                   spacing=20, vertical_alignment=ft.CrossAxisAlignment.START),
            self._ejercicios(),
        ], spacing=20)

    # ── tarjetas de arriba ──
    def _tarjetas(self) -> ft.Row:
        r = self.datos["resumen"]

        def cambio(valor, texto, bueno_si_sube=True, formato=None):
            if valor is None:
                return ft.Text(texto, size=11.5, color=TEXT_MUTED)
            sube = valor > 0
            bueno = (sube == bueno_si_sube) if valor else True
            fondo, color = ("#DCFCE7", "#15803D") if bueno else ("#FEE2E2", "#DC2626")
            icono = ft.Icons.ARROW_DROP_UP if sube else (ft.Icons.ARROW_DROP_DOWN if valor < 0 else ft.Icons.REMOVE)
            return ft.Column([
                ft.Row([ft.Container(ft.Icon(icono, size=18, color=color), width=24, height=24, border_radius=12,
                                     bgcolor=fondo, alignment=ft.Alignment.CENTER),
                        ft.Text(formato(valor) if formato else f"{valor:+g}", size=14, weight=ft.FontWeight.W_600,
                                color=color)], spacing=8),
                ft.Text(texto, size=11, color=TEXT_MUTED),
            ], spacing=2)

        def tarjeta(icono, fondo, color, titulo, valor, pie):
            return ft.Container(ft.Column([
                ft.Row([ft.Container(ft.Icon(icono, size=22, color=color), width=44, height=44, border_radius=22,
                                     bgcolor=fondo, alignment=ft.Alignment.CENTER),
                        ft.Text(titulo, size=13, color=DARK)], spacing=12),
                ft.Text(valor, size=30, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.1)),
                pie,
            ], spacing=12), bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=18, padding=20,
                expand=True, height=178)

        if r["imc"]:
            estado = "Peso saludable" if 18.5 <= r["imc"] < 25 else ("Bajo peso" if r["imc"] < 18.5 else "Sobrepeso")
            cuarta = tarjeta(ft.Icons.MONITOR_HEART_OUTLINED, "#DBEAFE", "#1D4ED8", "IMC", _num(r["imc"], 1),
                             ft.Container(ft.Text(estado, size=12, weight=ft.FontWeight.W_500, color="#1D4ED8"),
                                          bgcolor="#DBEAFE", border_radius=12,
                                          padding=ft.padding.symmetric(horizontal=12, vertical=5)))
        else:
            cuarta = tarjeta(ft.Icons.REPEAT, "#DBEAFE", "#1D4ED8", "Series", _num(r["series"]),
                             ft.Text(f"{_num(r['series'] / self.datos['semanas'], 1)} por semana", size=12, color=TEXT_MUTED))
        return ft.Row([
            tarjeta(ft.Icons.MONITOR_WEIGHT_OUTLINED, GOLD_BG2, GOLD_DARK, "Peso actual",
                    f"{_num(r['peso'], 1)} kg" if r["peso"] else "—",
                    cambio(r["peso_cambio"], "vs. inicio del período" if r["peso_cambio"] is not None
                           else ("Un solo registro" if r["peso"] else "No registró su peso"),
                           bueno_si_sube=self.datos["socio"].get("objetivo") != "SALUD",
                           formato=lambda v: f"{_num(v, 1)} kg".replace(",0 ", " "))),
            tarjeta(ft.Icons.EVENT_AVAILABLE, "#DCFCE7", "#15803D", "Días entrenados", _num(r["dias"]),
                    cambio(r["dias_cambio"], (f"vs. período anterior · " if r["dias_cambio"] is not None else "")
                           + f"{_num(r['por_semana'], 1)} por semana")),
            tarjeta(ft.Icons.FITNESS_CENTER, "#EDE9FE", "#6D28D9", "Volumen total", _volumen(r["volumen"]),
                    cambio(round(r["volumen_cambio"]) if r["volumen_cambio"] is not None else None,
                           "vs. período anterior" if r["volumen_cambio"] is not None else "Peso × repeticiones",
                           formato=lambda v: f"{v:+d}%")),
            cuarta,
        ], spacing=16)

    # ── evolución ──
    def _evolucion(self) -> ft.Container:
        d = self.datos
        opciones = [("volumen", "Volumen"), ("series", "Series"), ("peso", "Peso")]
        selector = ft.Row([ft.Container(
            ft.Text(t, size=12, weight=ft.FontWeight.W_500 if c == self.metrica else ft.FontWeight.W_400, color=DARK),
            bgcolor=GOLD if c == self.metrica else "#F4F2EB", border_radius=14,
            padding=ft.padding.symmetric(horizontal=12, vertical=6), ink=True,
            on_click=lambda e, c=c: self._cambiar_metrica(c)) for c, t in opciones], spacing=6, tight=True)
        if self.metrica == "peso":
            pesos = d["pesos"]
            valores, etiquetas = [p["peso"] for p in pesos], [f"{p['fecha']:%d/%m}" for p in pesos]
            vacio = "Todavía no registró su peso." if not pesos else None
            texto = "Registros de peso del socio (todos)."
            unidad, color = "kg", GOLD
        else:
            semanas = d["volumen_semanal"]
            valores = [s["volumen"] if self.metrica == "volumen" else s["series"] for s in semanas]
            etiquetas = [f"{s['semana']:%d/%m}" for s in semanas]
            vacio = "No hay entrenamientos en este período." if not any(valores) else None
            texto = ("Kilos levantados por semana (peso × repeticiones)." if self.metrica == "volumen"
                     else "Cantidad de series por semana.")
            unidad, color = ("vol", "#8B5CF6") if self.metrica == "volumen" else ("n", "#3B82F6")
        cuerpo = ft.Container(ft.Text(vacio, size=13, color=TEXT_MUTED), height=230, alignment=ft.Alignment.CENTER) \
            if vacio else Grafico(valores, etiquetas, unidad, color)
        return _tarjeta(ft.Column([
            _titulo_tarjeta(ft.Icons.SHOW_CHART, "Evolución", selector),
            ft.Text(texto, size=12, color=TEXT_MUTED),
            cuerpo,
        ], spacing=10))

    # ── últimos entrenamientos ──
    def _sesiones(self) -> ft.Container:
        sesiones = self.datos["sesiones"]
        filas = []
        for s in sesiones[:5]:
            chips = [ft.Container(ft.Text(g, size=10.5, weight=ft.FontWeight.W_500, color=COLOR_GRUPO.get(g, TEXT_MUTED)),
                                  bgcolor=ft.Colors.with_opacity(0.12, COLOR_GRUPO.get(g, TEXT_MUTED)), border_radius=10,
                                  padding=ft.padding.symmetric(horizontal=8, vertical=2)) for g in s["grupos"]]
            filas.append(ft.Container(ft.Column([
                ft.Row([ft.Text(f"{s['dia']:%d/%m/%Y}", size=13.5, weight=ft.FontWeight.W_500, color=DARK, expand=True),
                        ft.Row(chips, spacing=4, tight=True)]),
                ft.Row([ft.Text(f"{s['series']} series", size=12, color=TEXT_MUTED),
                        ft.Text("|", size=12, color=GRAY_LIGHT),
                        ft.Text(f"{s['ejercicios']} {'ejercicio' if s['ejercicios'] == 1 else 'ejercicios'}", size=12,
                                color=TEXT_MUTED),
                        ft.Text("|", size=12, color=GRAY_LIGHT),
                        ft.Text(_volumen(s["volumen"]), size=12, color=TEXT_MUTED)], spacing=8),
            ], spacing=4), border=ft.border.all(1, GRAY_LIGHT), border_radius=12,
                padding=ft.padding.symmetric(horizontal=14, vertical=10)))
        mas = len(sesiones) - 5
        return _tarjeta(ft.Column([
            _titulo_tarjeta(ft.Icons.CALENDAR_MONTH_OUTLINED, "Últimos entrenamientos"),
            *(filas or [ft.Text("Sin entrenamientos en este período.", size=12.5, color=TEXT_MUTED)]),
            *([ft.Text(f"y {mas} más en el período", size=11.5, color=TEXT_MUTED)] if mas > 0 else []),
        ], spacing=10))

    # ── trabajo por músculo (bodygraph) ──
    def _cuerpo(self, vista: str) -> ft.Control:
        intensidad = self.datos["intensidad"]
        capas = [ft.Image(src=f"cuerpo/base_{vista}.png", width=CUERPO_W, height=CUERPO_H, fit=ft.BoxFit.FILL)]
        for zona in ejercicios_repo.ZONAS_POR_VISTA[vista]:
            if intensidad.get(zona):
                capas.append(ft.Container(
                    ft.Image(src=f"cuerpo/zona_{vista}_{zona}.png", width=CUERPO_W, height=CUERPO_H, fit=ft.BoxFit.FILL),
                    opacity=0.3 + 0.7 * intensidad[zona], width=CUERPO_W, height=CUERPO_H))
        capas.append(ft.GestureDetector(width=CUERPO_W, height=CUERPO_H, mouse_cursor=ft.MouseCursor.BASIC,
                                        on_hover=lambda e, v=vista: self._hover(v, e),
                                        on_exit=lambda e: self._hover(None, None)))
        return ft.Column([ft.Stack(capas, width=CUERPO_W, height=CUERPO_H),
                          ft.Text("FRENTE" if vista == "frente" else "ESPALDA", size=10, color=TEXT_MUTED,
                                  weight=ft.FontWeight.W_500)],
                         horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)

    def _hover(self, vista, e):
        texto = "Pasá el mouse por el cuerpo"
        if vista:
            zona = _zona_en_punto(vista, int(e.local_position.x / CUERPO_W * ASSET_W),
                                  int(e.local_position.y / CUERPO_H * ASSET_H))
            if zona:
                series = self.datos["zonas"].get(zona, 0)
                texto = f"{ejercicios_repo.ZONAS_MUSCULARES[zona]['etiqueta']}: " + \
                        (f"{_num(series, 1)} series efectivas" if series else "sin trabajo en el período")
        if texto != self.nombre_hover.value:
            self.nombre_hover.value = texto
            try:
                if self.nombre_hover.page:
                    self.nombre_hover.update()
            except RuntimeError:
                pass

    def _musculos(self) -> ft.Container:
        d = self.datos
        filas = []
        escala = repo.SERIES_MAX * 1.5
        for g in d["grupos"]:
            semana = g["por_semana"]
            if semana == 0:
                estado, color_estado = "Sin trabajo", "#DC2626"
            elif semana < repo.SERIES_MIN * 0.6:
                estado, color_estado = "Poco", "#B45309"
            elif semana > repo.SERIES_MAX * 1.2:
                estado, color_estado = "Mucho", "#B45309"
            else:
                estado, color_estado = "Bien", "#15803D"
            color = COLOR_GRUPO[g["grupo"]]
            ancho = min(1.0, semana / escala)
            barra = ft.Container(ft.Row([
                ft.Container(height=8, bgcolor=color, border_radius=4, expand=max(1, int(ancho * 1000))),
                ft.Container(height=8, expand=max(1, int((1 - ancho) * 1000))),
            ], spacing=0), bgcolor="#F1F0EA", border_radius=4, height=8)
            filas.append(ft.Column([
                ft.Row([
                    ft.Container(width=10, height=10, border_radius=5, bgcolor=color),
                    ft.Text(g["grupo"], size=13, color=DARK, expand=True),
                    ft.Text(f"{_num(semana, 1)} series/sem", size=13, weight=ft.FontWeight.W_600, color=DARK),
                    ft.Container(ft.Text(estado, size=11, weight=ft.FontWeight.W_500, color=color_estado),
                                 width=74, alignment=ft.Alignment.CENTER_RIGHT),
                ], spacing=10),
                barra,
            ], spacing=6))
        leyenda = ft.Row([
            ft.Text("Menos", size=10.5, color=TEXT_MUTED),
            ft.Container(width=90, height=8, border_radius=4, gradient=ft.LinearGradient(
                colors=[ft.Colors.with_opacity(0.2, GOLD), GOLD])),
            ft.Text("Más trabajo", size=10.5, color=TEXT_MUTED),
        ], spacing=6, tight=True)
        cuerpo = ft.Column([
            ft.Row([self._cuerpo("frente"), self._cuerpo("espalda")], spacing=10, tight=True),
            leyenda,
            ft.Container(self.nombre_hover, width=260, alignment=ft.Alignment.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
        return _tarjeta(ft.Column([
            _titulo_tarjeta(ft.Icons.ACCESSIBILITY_NEW, "Trabajo por músculo"),
            ft.Text(f"Series efectivas por semana: cada serie suma 1 al músculo principal del ejercicio y 0,5 a los "
                    f"secundarios. Lo útil es entre {repo.SERIES_MIN} y {repo.SERIES_MAX} por grupo.",
                    size=12, color=TEXT_MUTED),
            ft.Row([cuerpo, ft.Column(filas, spacing=16, expand=True)], spacing=24,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=12))

    # ── qué cambiar ──
    def _recomendaciones(self) -> ft.Container:
        recs = self.datos["recomendaciones"]
        filas = []
        for rec in recs[:7]:
            fondo, color = NIVEL[rec["nivel"]]
            filas.append(ft.Row([
                ft.Container(ft.Icon(getattr(ft.Icons, rec["icono"], ft.Icons.LIGHTBULB_OUTLINE), size=19, color=color),
                             width=40, height=40, border_radius=20, bgcolor=fondo, alignment=ft.Alignment.CENTER),
                ft.Column([ft.Text(rec["titulo"], size=13, weight=ft.FontWeight.W_500, color=DARK),
                           ft.Text(rec["detalle"], size=11.5, color=TEXT_MUTED)], spacing=2, expand=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START))
        if len(recs) > 7:
            filas.append(ft.Text(f"y {len(recs) - 7} sugerencias más de menor prioridad", size=11.5, color=TEXT_MUTED))
        if not recs:
            filas.append(ft.Text("Todo en orden: la rutina está equilibrada y progresa.", size=12.5, color=TEXT_MUTED))
        return _tarjeta(ft.Column([_titulo_tarjeta(ft.Icons.TIPS_AND_UPDATES_OUTLINED, "Qué cambiar en la rutina"),
                                   *filas], spacing=14))

    # ── progreso por ejercicio ──
    def _ejercicios(self) -> ft.Container:
        ejercicios = self.datos["ejercicios"]
        cols = [("EJERCICIO", 4), ("SESIONES", 1), ("MEJOR PESO", 1), ("1RM ESTIMADO", 2), ("TENDENCIA", 2), ("ESTADO", 2)]
        encabezado = ft.Row([ft.Text(t, size=11, weight=ft.FontWeight.W_500, color=TEXT_MUTED, expand=p)
                             for t, p in cols], spacing=12)
        filas = []
        for p in ejercicios:
            src = ejercicios_repo.imagen_de(p["ej"]) if p["ej"] else None
            imagen = ft.Container(ft.Image(src=src, width=38, height=38, fit=ft.BoxFit.COVER) if src else
                                  ft.Icon(ft.Icons.FITNESS_CENTER, size=18, color=TEXT_MUTED),
                                  width=38, height=38, border_radius=8, bgcolor="#F4F2EB",
                                  clip_behavior=ft.ClipBehavior.ANTI_ALIAS, alignment=ft.Alignment.CENTER)
            if p["sesiones"] < 2:
                estado, fondo, color = "Una sola sesión", "#F1F0EA", TEXT_MUTED
            elif p["estancado"]:
                estado, fondo, color = "Estancado", "#FEF3C7", "#B45309"
            elif p["cambio"] > 0:
                estado, fondo, color = f"Progresa +{p['cambio']:.0f}%", "#DCFCE7", "#15803D"
            else:
                estado, fondo, color = f"Bajó {p['cambio']:.0f}%", "#FEE2E2", "#DC2626"
            rm = f"{_num(p['rm_actual'])} kg" if p["sesiones"] < 2 else f"{_num(p['rm_inicial'])} → {_num(p['rm_actual'])} kg"
            filas.append(ft.Container(ft.Row([
                ft.Row([imagen, ft.Text(p["ejercicio"], size=13, weight=ft.FontWeight.W_500, color=DARK, expand=True,
                                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)], spacing=12, expand=4),
                ft.Text(str(p["sesiones"]), size=13, color=DARK, expand=1),
                ft.Text(f"{_num(p['mejor_peso'], 1).replace(',0', '')} kg", size=13, color=DARK, expand=1),
                ft.Text(rm, size=13, color=DARK, expand=2),
                ft.Container(_mini_linea(p["historia"], color if color != TEXT_MUTED else GOLD), expand=2),
                ft.Container(ft.Container(ft.Text(estado, size=11.5, weight=ft.FontWeight.W_500, color=color),
                                          bgcolor=fondo, border_radius=12,
                                          padding=ft.padding.symmetric(horizontal=10, vertical=4)), expand=2),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=8), border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT))))
        return _tarjeta(ft.Column([
            _titulo_tarjeta(ft.Icons.TRENDING_UP, "Progreso por ejercicio"),
            ft.Text("1RM estimado: el peso máximo que podría levantar una vez, calculado con su mejor serie de cada día.",
                    size=12, color=TEXT_MUTED),
            encabezado,
            *(filas or [ft.Text("Sin ejercicios registrados en este período.", size=12.5, color=TEXT_MUTED)]),
        ], spacing=10))


def build_progreso(page: ft.Page = None) -> ft.Column:
    return ProgresoView(page).build()
