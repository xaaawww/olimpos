# OLIMPOS GYM — Gestión de ejercicios (Dueño / Entrenador)
#
# A la izquierda, la tabla del catálogo (dibujo, músculos, cómo se realiza);
# al tocar un ejercicio se abre a la derecha un panel con tres pestañas:
#   Información  el formulario: nombre, cómo se realiza (un paso por línea),
#                músculos, tipo (compuesto/aislado), aparato, nivel y series
#   Músculos     el bodygraph de frente y espalda: tocar un músculo lo agrega
#                o lo quita; el primero de la lista es el principal
#   Variantes    otros ejercicios del mismo grupo muscular, como lista chica
#
# Se edita una COPIA: nada llega a la base hasta "Guardar cambios", y cambiar
# de ejercicio con cambios pendientes pregunta antes. El dibujo de cada
# ejercicio vive en img/ejercicios/<id>.png ("Cambiar imagen" lo reemplaza).

import copy
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from PIL import Image
from theme import *
from components import status_pill
import ejercicios_repo as repo
import validaciones

# Bodygraph de la pestaña Músculos y su resolución real (para tocar pixel a pixel).
CANVAS_W, CANVAS_H = 150, 300
ASSET_W, ASSET_H = 400, 800
MAX_PASOS_CHARS = 500
NIVELES = ["Principiante", "Intermedio", "Avanzado"]
ORDENES = {"nombre": "Nombre (A-Z)", "grupo": "Grupo muscular", "recientes": "Recién editados"}
# Color de cada grupo muscular en los chips (fondo, texto).
COLOR_GRUPO = {
    "Pecho": ("#FEF3C7", "#B45309"), "Espalda": ("#DBEAFE", "#1D4ED8"), "Piernas": ("#DCFCE7", "#15803D"),
    "Hombros": ("#FFEDD5", "#C2410C"), "Brazos": ("#FCE7F3", "#BE185D"), "Core": ("#EDE9FE", "#6D28D9"),
}
GRIS_CHIP = ("#F1F0EA", "#6B6656")

_mascaras_cache: dict[tuple[str, str], "Image.Image"] = {}


def _mascara(vista: str, zona: str) -> "Image.Image":
    key = (vista, zona)
    if key not in _mascaras_cache:
        ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", "cuerpo", f"zona_{vista}_{zona}.png")
        _mascaras_cache[key] = Image.open(ruta).convert("RGBA")
    return _mascaras_cache[key]


def _zona_en_punto(vista: str, x_px: int, y_px: int) -> str | None:
    for zona in repo.ZONAS_POR_VISTA[vista]:
        mascara = _mascara(vista, zona)
        if 0 <= x_px < mascara.width and 0 <= y_px < mascara.height and mascara.getpixel((x_px, y_px))[3] > 10:
            return zona
    return None


def _actualizar(control: ft.Control):
    """Actualiza el control solo si ya está en pantalla (en Flet 0.84 pedir
    .page a un control que no se agregó lanza error)."""
    try:
        if control.page:
            control.update()
    except RuntimeError:
        pass


def _mini_cuerpo(ejercicio: dict, ancho: int, alto: int, vista: str | None = None,
                 principal: str | None = None) -> ft.Stack:
    """Silueta con los músculos del ejercicio en dorado (el principal a pleno)."""
    zonas = [p["zona"] for p in ejercicio.get("puntos") or []]
    if vista is None:
        vista = "espalda" if zonas and zonas[0] not in repo.ZONAS_POR_VISTA["frente"] else "frente"
    capas = [ft.Image(src=f"cuerpo/base_{vista}.png", width=ancho, height=alto, fit=ft.BoxFit.FILL)]
    for zona in repo.ZONAS_POR_VISTA[vista]:
        if zona in zonas:
            img = ft.Image(src=f"cuerpo/zona_{vista}_{zona}.png", width=ancho, height=alto, fit=ft.BoxFit.FILL)
            suave = principal is not None and zona != principal
            capas.append(ft.Container(img, opacity=0.45 if suave else 1, width=ancho, height=alto))
    return ft.Stack(capas, width=ancho, height=alto)


def _chip(texto: str, colores: tuple[str, str], punto: bool = True, on_quitar=None, chico: bool = False) -> ft.Container:
    fondo, color = colores
    controles = []
    if punto:
        controles.append(ft.Container(width=6, height=6, border_radius=3, bgcolor=color))
    controles.append(ft.Text(texto, size=11 if chico else 12, weight=ft.FontWeight.W_500, color=color,
                             max_lines=1, overflow=ft.TextOverflow.ELLIPSIS))
    if on_quitar:
        controles.append(ft.Container(ft.Icon(ft.Icons.CLOSE, size=13, color=color), on_click=on_quitar,
                                      border_radius=8, padding=1, tooltip="Quitar"))
    return ft.Container(ft.Row(controles, spacing=6, tight=True), bgcolor=fondo, border_radius=20,
                        padding=ft.padding.symmetric(horizontal=9 if chico else 11, vertical=3 if chico else 5))


def _colores_grupo(zona: str) -> tuple[str, str]:
    return COLOR_GRUPO.get(repo.GRUPO_DE_ZONA.get(zona), GRIS_CHIP)


class EditorEjerciciosView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.error_carga = None
        try:
            self.ejercicios = repo.cargar_ejercicios()
        except Exception as ex:
            self.ejercicios = []
            self.error_carga = str(ex)
        self.filtro = "Todos"
        self.busqueda = ""
        self.orden = "nombre"
        self.sel = None              # id del ejercicio abierto ("nuevo" si todavía no se guardó)
        self.ejercicio = None        # copia que se está editando
        self.pestana = "info"        # info | musculos | variantes
        self.sin_guardar = False
        self.imagen_nueva: str | None = None   # archivo elegido en "Cambiar imagen", se aplica al guardar
        self.version_img: dict[str, float] = {}
        self.root = ft.Column(spacing=0, expand=True)
        self.mensaje = ft.Text("", size=12, weight=ft.FontWeight.W_500)
        self.contador = ft.Text("", size=11, color=TEXT_MUTED)
        self.nombre_hover = ft.Text("", size=12, weight=ft.FontWeight.W_500, color=GOLD_DARK)
        self.buscador = ft.TextField(
            hint_text="Buscar ejercicio...", prefix_icon=ft.Icons.SEARCH, expand=True, dense=True,
            border_radius=12, border_color=GRAY_LIGHT, bgcolor=WHITE, on_change=self._buscar,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=13),
        )
        self.selector_orden = ft.Dropdown(
            value=self.orden, width=260, dense=True, text_size=13, border_radius=12, border_color=GRAY_LIGHT, bgcolor=WHITE,
            options=[ft.DropdownOption(key=k, text=f"Ordenar: {v}") for k, v in ORDENES.items()],
            on_select=self._cambiar_orden,
        )
        self.selector_archivo = ft.FilePicker()
        self._montado = False

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls = [self._pantalla()]
        if self._montado:
            self.root.update()

    # ══════════════════════════ PANTALLA ══════════════════════════
    def _pantalla(self) -> ft.Column:
        nuevo = ft.Container(
            ft.Row([ft.Icon(ft.Icons.ADD, size=18, color=DARK),
                    ft.Text("Nuevo ejercicio", size=14, weight=ft.FontWeight.W_500, color=DARK)], spacing=8, tight=True),
            bgcolor=GOLD, border_radius=12, padding=ft.padding.symmetric(horizontal=22, vertical=13),
            on_click=self._nuevo, ink=True,
        )
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Ejercicios", size=13, color=TEXT_MUTED),
                ft.Text("Gestión de ejercicios", size=28, weight=ft.FontWeight.W_600, color=DARK,
                        font_family="Poppins", style=ft.TextStyle(height=1.15)),
                ft.Text("Editá y organizá los ejercicios, indicando qué músculos trabajan y cómo se realizan.",
                        size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            ft.IconButton(ft.Icons.REFRESH, tooltip="Volver a leer de la base", on_click=self._refrescar),
            nuevo,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        izquierda = ft.Column([
            self._fila_filtros(),
            ft.Row([self.buscador, self.selector_orden], spacing=12),
            self._tabla(),
        ], spacing=16, expand=True)
        cuerpo = ft.Row([izquierda] + ([self._panel()] if self.sel else []),
                        spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)

        controles = [cabecera]
        if self.error_carga:
            controles.append(ft.Container(ft.Text(f"⚠️ No se pudo conectar con la base de datos: {self.error_carga}",
                                                  size=12, color=RED), bgcolor=BADGE_RED_BG, border_radius=10, padding=12))
        controles.append(cuerpo)
        self.columna = ft.Column(controles, spacing=22, scroll=ft.ScrollMode.AUTO, expand=True)
        return self.columna

    # ── filtros / búsqueda / orden ──
    def _fila_filtros(self) -> ft.Container:
        cuenta = {g: sum(1 for e in self.ejercicios if repo.grupo_de(e) == g) for g in repo.GRUPOS}
        opciones = [("Todos", len(self.ejercicios))] + [(g, n) for g, n in cuenta.items() if n]
        borradores = sum(1 for e in self.ejercicios if not e.get("publicado"))
        if borradores:
            opciones.append(("Borradores", borradores))

        def pill(nombre, cantidad):
            activo = nombre == self.filtro
            return ft.Container(
                ft.Text(f"{nombre} ({cantidad})", size=13, weight=ft.FontWeight.W_500 if activo else ft.FontWeight.W_400,
                        color=DARK),
                bgcolor=GOLD if activo else "#F4F2EB", border_radius=22,
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                on_click=lambda e, n=nombre: self._cambiar_filtro(n), ink=True,
            )
        return ft.Container(ft.Row([pill(n, c) for n, c in opciones], spacing=10, wrap=True, run_spacing=8),
                            bgcolor=WHITE, border_radius=18, border=ft.border.all(1, GRAY_LIGHT), padding=8)

    def _filtrados(self) -> list[dict]:
        res = self.ejercicios
        if self.filtro == "Borradores":
            res = [e for e in res if not e.get("publicado")]
        elif self.filtro in repo.GRUPOS:
            res = [e for e in res if repo.grupo_de(e) == self.filtro]
        texto = self.busqueda.strip().lower()
        if texto:
            res = [e for e in res if texto in e["nombre"].lower() or texto in repo.resumen_musculos(e).lower()]
        if self.orden == "grupo":
            orden_grupos = list(repo.GRUPOS)
            return sorted(res, key=lambda e: (orden_grupos.index(repo.grupo_de(e)) if repo.grupo_de(e) else 99,
                                              e["nombre"].lower()))
        if self.orden == "recientes":
            return sorted(res, key=lambda e: e.get("actualizado", ""), reverse=True)
        return sorted(res, key=lambda e: e["nombre"].lower())

    def _cambiar_filtro(self, nombre: str):
        self.filtro = nombre
        self._render()

    def _buscar(self, e):
        self.busqueda = e.control.value or ""
        self._render()

    def _cambiar_orden(self, e):
        self.orden = e.control.value or "nombre"
        self._render()

    # ── tabla ──
    def _imagen(self, ejercicio: dict, lado: int, radio: int = 10) -> ft.Control:
        src = repo.imagen_de(ejercicio)
        if not src:
            return ft.Container(_mini_cuerpo(ejercicio, lado // 2, lado), width=lado, height=lado,
                                alignment=ft.Alignment.CENTER, bgcolor="#F4F2EB", border_radius=radio)
        if ejercicio["id"] in self.version_img:
            # recién cambiada: se pasa en bytes para que no se muestre la versión guardada en caché
            with open(os.path.join(repo.CARPETA_IMAGENES, f"{ejercicio['id']}.png"), "rb") as f:
                src = f.read()
        return ft.Container(ft.Image(src=src, width=lado, height=lado, fit=ft.BoxFit.COVER),
                            width=lado, height=lado, border_radius=radio, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    def _chips_musculos(self, ejercicio: dict, maximo: int, chico: bool = False) -> ft.Row:
        zonas = list(dict.fromkeys(p["zona"] for p in ejercicio.get("puntos") or []))
        if not zonas:
            return ft.Row([ft.Text("Sin músculos", size=12, color=TEXT_MUTED, italic=True)])
        chips = []
        for i, z in enumerate(zonas[:maximo]):
            chips.append(_chip(repo.NOMBRE_CORTO[z].capitalize(), _colores_grupo(z) if i == 0 else GRIS_CHIP, chico=chico))
        if len(zonas) > maximo:
            chips.append(ft.Text(f"+{len(zonas) - maximo}", size=11.5, color=TEXT_MUTED))
        return ft.Row(chips, spacing=6, wrap=False)

    def _tabla(self) -> ft.Container:
        # proporción de cada columna (0 = ancho fijo, la de acciones)
        cols = [("EJERCICIO", 5), ("MÚSCULOS", 4), ("CÓMO SE REALIZA", 4), ("ACCIONES", 0)] if not self.sel else \
               [("EJERCICIO", 5), ("MÚSCULOS", 4), ("", 0)]
        encabezado = ft.Container(
            ft.Row([self._celda(ft.Text(t, size=11.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED), p)
                    for t, p in cols], spacing=12),
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
        )
        visibles = self._filtrados()
        filas = [self._fila(e, cols) for e in visibles] or [ft.Container(
            ft.Text("Ningún ejercicio coincide con la búsqueda." if self.ejercicios else "Todavía no hay ejercicios.",
                    size=13, color=TEXT_MUTED), padding=20, border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)))]
        return ft.Container(ft.Column([encabezado, *filas], spacing=0), bgcolor=WHITE,
                            border=ft.border.all(1, GRAY_LIGHT), border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    @staticmethod
    def _celda(control: ft.Control, proporcion: int) -> ft.Container:
        if proporcion:
            return ft.Container(control, expand=proporcion)
        return ft.Container(control, width=72, alignment=ft.Alignment.CENTER)

    def _fila(self, e: dict, cols) -> ft.Container:
        menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT, icon_color=DARK, tooltip="Más opciones",
            items=[
                ft.PopupMenuItem(content=ft.Text("✏️  Editar"), on_click=lambda ev, eid=e["id"]: self._abrir(eid)),
                ft.PopupMenuItem(content=ft.Text("📢  Pasar a borrador" if e.get("publicado") else "📢  Publicar en la app"),
                                 on_click=lambda ev, ej=e: self._alternar_publicado_lista(ej)),
                ft.PopupMenuItem(content=ft.Text("🗑️  Eliminar", color=RED), on_click=lambda ev, ej=e: self._confirmar_eliminar(ej)),
            ],
        )
        nombre = ft.Column([
            ft.Text(e["nombre"], size=13.5, weight=ft.FontWeight.W_500, color=DARK, max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS),
            *([] if e.get("publicado") else [ft.Text("Borrador", size=11, color=GOLD_DARK)]),
        ], spacing=1, expand=True)
        # con el panel abierto la tabla se angosta: un solo chip y "+N"
        celdas = [ft.Row([self._imagen(e, 58), nombre], spacing=14), self._chips_musculos(e, 1 if self.sel else 2)]
        if not self.sel:
            paso = (e.get("pasos") or [""])[0]
            celdas.append(ft.Text(paso or "—", size=12.5, color=TEXT_MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS))
        celdas.append(menu)
        elegido = e["id"] == self.sel
        return ft.Container(
            ft.Row([self._celda(c, p) for c, (_, p) in zip(celdas, cols)], spacing=12,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=GOLD_BG if elegido else None,
            padding=ft.padding.symmetric(horizontal=18, vertical=7),
            border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
            on_click=lambda ev, eid=e["id"]: self._abrir(eid), ink=True,
        )

    # ══════════════════════════ PANEL ══════════════════════════
    def _abrir(self, ejercicio_id: str):
        if self.sin_guardar and ejercicio_id != self.sel:
            self._preguntar_descartar(lambda: self._abrir_forzado(ejercicio_id))
            return
        self._abrir_forzado(ejercicio_id)

    def _abrir_forzado(self, ejercicio_id: str):
        self.sel = ejercicio_id
        self.ejercicio = copy.deepcopy(repo.obtener_ejercicio(self.ejercicios, ejercicio_id))
        self._reiniciar_panel()

    def _nuevo(self, e=None):
        if self.sin_guardar:
            self._preguntar_descartar(self._nuevo_forzado)
            return
        self._nuevo_forzado()

    def _nuevo_forzado(self):
        self.sel = "nuevo"
        self.ejercicio = repo.nuevo_ejercicio("")
        self.ejercicio.update({"tipo": "Compuesto", "nivel": "Principiante", "series": 3, "repeticiones": "8-12"})
        self._reiniciar_panel()

    def _reiniciar_panel(self):
        self.pestana = "info"
        self.sin_guardar = False
        self.imagen_nueva = None
        self._mostrar("", TEXT_MUTED)
        self._render()

    def _cerrar(self, e=None):
        if self.sin_guardar:
            self._preguntar_descartar(self._cerrar_forzado)
            return
        self._cerrar_forzado()

    def _cerrar_forzado(self):
        self.sel, self.ejercicio, self.sin_guardar, self.imagen_nueva = None, None, False, None
        self._render()

    def _panel(self) -> ft.Container:
        e = self.ejercicio
        publicado = e.get("publicado")
        estado = ft.Container(
            status_pill("Publicado" if publicado else "Borrador", "active" if publicado else "pending"),
            on_click=lambda ev: self._cambio("publicado", not publicado, rerender=True),
            tooltip="Tocá para pasarlo a borrador" if publicado else "Tocá para publicarlo en la app (se aplica al guardar)",
        )
        if self.imagen_nueva:
            with open(self.imagen_nueva, "rb") as f:
                imagen = ft.Container(ft.Image(src=f.read(), width=120, height=120, fit=ft.BoxFit.COVER),
                                      border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)
        else:
            imagen = self._imagen(e, 120, 16)
        cambiar = ft.Container(
            ft.Row([ft.Icon(ft.Icons.IMAGE_OUTLINED, size=17, color=GOLD_DARK),
                    ft.Text("Cambiar imagen", size=12.5, weight=ft.FontWeight.W_500, color=GOLD_DARK)], spacing=8, tight=True),
            bgcolor=GOLD_BG2, border_radius=10, padding=ft.padding.symmetric(horizontal=14, vertical=9),
            on_click=self._elegir_imagen, ink=True,
        )

        def tab(clave, texto):
            activa = self.pestana == clave
            return ft.Container(
                ft.Text(texto, size=14, weight=ft.FontWeight.W_500 if activa else ft.FontWeight.W_400,
                        color=DARK if activa else TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                padding=ft.padding.only(bottom=10), expand=True, alignment=ft.Alignment.CENTER,
                border=ft.border.only(bottom=ft.BorderSide(2.5, GOLD if activa else ft.Colors.TRANSPARENT)),
                on_click=lambda ev: self._cambiar_pestana(clave),
            )

        contenido = {"info": self._tab_info, "musculos": self._tab_musculos, "variantes": self._tab_variantes}[self.pestana]()
        return ft.Container(
            content=ft.Column([
                ft.Container(ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16, color=DARK),
                                     ft.Text("Volver", size=13, color=DARK)], spacing=8, tight=True),
                             on_click=self._cerrar, ink=True, border_radius=8,
                             padding=ft.padding.symmetric(horizontal=4, vertical=4)),
                ft.Row([
                    imagen,
                    ft.Column([
                        ft.Row([ft.Text(e["nombre"] or "Nuevo ejercicio", size=20, weight=ft.FontWeight.W_600, color=DARK,
                                        font_family="Poppins", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                                estado], spacing=8, vertical_alignment=ft.CrossAxisAlignment.START),
                        ft.Text(repo.resumen_musculos(e) or "Elegí los músculos que trabaja", size=13, color=TEXT_MUTED),
                        ft.Container(height=4),
                        cambiar,
                    ], spacing=2, expand=True),
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Container(ft.Row([tab("info", "Información"), tab("musculos", "Músculos"),
                                     tab("variantes", "Variantes")], spacing=0),
                             border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)), margin=ft.margin.only(top=10)),
                contenido,
            ], spacing=10),
            width=480, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=18,
            padding=ft.padding.symmetric(horizontal=24, vertical=18),
        )

    def _cambiar_pestana(self, clave: str):
        self.pestana = clave
        self._render()

    def _etiqueta(self, texto: str, obligatorio: bool = False) -> ft.Row:
        return ft.Row([ft.Text(texto, size=13, weight=ft.FontWeight.W_500, color=DARK)] +
                      ([ft.Text("*", size=13, color=RED)] if obligatorio else []), spacing=3)

    def _boton_guardar(self) -> list[ft.Control]:
        return [
            ft.Container(height=4),
            self.mensaje,
            ft.Container(ft.Text("Guardar cambios", size=14.5, weight=ft.FontWeight.W_500, color=DARK),
                         bgcolor=GOLD, border_radius=12, alignment=ft.Alignment.CENTER, height=48,
                         on_click=self._guardar, ink=True),
        ]

    # ── pestaña Información ──
    def _tab_info(self) -> ft.Column:
        e = self.ejercicio
        texto_pasos = "\n".join(e.get("pasos") or [])
        self.contador.value = f"{len(texto_pasos)}/{MAX_PASOS_CHARS}"
        campo_nombre = ft.TextField(value=e["nombre"], dense=True, border_radius=10, border_color=GRAY_LIGHT,
                                    hint_text="Ej.: Press de banca", text_size=13.5, max_length=80, counter=ft.Text(""),
                                    on_change=lambda ev: self._cambio("nombre", ev.control.value))
        campo_pasos = ft.TextField(
            value=texto_pasos, multiline=True, min_lines=4, max_lines=8, border_radius=10, border_color=GRAY_LIGHT,
            text_size=13.5,
            hint_text="Un paso por línea. Ej.:\nAcostate en el banco con los pies firmes.\nBajá la barra hasta el pecho.",
            on_change=self._cambio_pasos,
        )

        ya = {p["zona"] for p in e.get("puntos") or []}
        agregar = ft.PopupMenuButton(
            content=ft.Container(ft.Row([ft.Icon(ft.Icons.ADD, size=15, color=DARK),
                                         ft.Text("Agregar músculo", size=12, color=DARK)], spacing=6, tight=True),
                                 border=ft.border.all(1, GRAY_LIGHT), border_radius=18,
                                 padding=ft.padding.symmetric(horizontal=12, vertical=6)),
            items=[ft.PopupMenuItem(content=ft.Text(f"{info['emoji']}  {info['etiqueta']}"),
                                    on_click=lambda ev, z=z: self._alternar_zona(z))
                   for z, info in repo.ZONAS_MUSCULARES.items() if z not in ya],
            tooltip="Agregar un músculo",
        )
        chips = [_chip(repo.NOMBRE_CORTO[p["zona"]].capitalize(), _colores_grupo(p["zona"]) if i == 0 else GRIS_CHIP,
                       on_quitar=lambda ev, z=p["zona"]: self._alternar_zona(z))
                 for i, p in enumerate(e.get("puntos") or [])]

        def tipo(nombre):
            activo = e.get("tipo") == nombre
            return ft.Container(
                ft.Row(([ft.Icon(ft.Icons.CHECK, size=14, color=GOLD_DARK)] if activo else []) +
                       [ft.Text(nombre, size=12.5, weight=ft.FontWeight.W_500, color=GOLD_DARK if activo else TEXT_MUTED)],
                       spacing=6, tight=True),
                bgcolor=GOLD_BG2 if activo else "#F4F2EB", border=ft.border.all(1, GOLD_LIGHT if activo else "#F4F2EB"),
                border_radius=20, padding=ft.padding.symmetric(horizontal=14, vertical=7),
                on_click=lambda ev: self._cambio("tipo", "" if activo else nombre, rerender=True), ink=True,
            )

        def tarjeta(icono, titulo, control):
            return ft.Container(
                ft.Column([ft.Row([ft.Icon(icono, size=16, color=TEXT_MUTED),
                                   ft.Text(titulo, size=11, color=TEXT_MUTED, max_lines=1,
                                           overflow=ft.TextOverflow.ELLIPSIS, expand=True)], spacing=6),
                           control], spacing=4),
                border=ft.border.all(1, GRAY_LIGHT), border_radius=12, padding=ft.padding.symmetric(horizontal=12, vertical=9),
                expand=True,
            )

        sin_borde = dict(dense=True, border=ft.InputBorder.NONE, content_padding=0, text_size=13)
        aparato = ft.TextField(value=e.get("aparato", ""), hint_text="Ej.: Barra", **sin_borde, max_length=100,
                               counter=ft.Text(""),
                               on_change=lambda ev: self._cambio("aparato", ev.control.value))
        nivel = ft.PopupMenuButton(
            content=ft.Row([ft.Text(e.get("nivel") or "Elegir", size=13, color=DARK if e.get("nivel") else TEXT_MUTED),
                            ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=18, color=TEXT_MUTED)], spacing=0, tight=True),
            items=[ft.PopupMenuItem(content=ft.Text(n), on_click=lambda ev, n=n: self._cambio("nivel", n, rerender=True))
                   for n in NIVELES],
            tooltip="Nivel del ejercicio",
        )
        series = ft.TextField(value=str(e.get("series") or ""), width=26, hint_text="3", **sin_borde,
                              keyboard_type=ft.KeyboardType.NUMBER, on_change=self._cambio_series,
                              input_filter=validaciones.SOLO_DIGITOS, max_length=2, counter=ft.Text(""))
        reps = ft.TextField(value=e.get("repeticiones", ""), hint_text="8-12", expand=True, **sin_borde,
                            input_filter=ft.InputFilter(regex_string=r"[0-9\-]"), max_length=7, counter=ft.Text(""),
                            on_change=lambda ev: self._cambio("repeticiones", ev.control.value))

        return ft.Column([
            ft.Container(height=4),
            self._etiqueta("Nombre del ejercicio", True), campo_nombre,
            ft.Container(height=2),
            self._etiqueta("Descripción / Cómo se realiza", True), campo_pasos,
            ft.Row([self.contador], alignment=ft.MainAxisAlignment.END),
            ft.Row([ft.Text("Músculos que trabaja", size=13, weight=ft.FontWeight.W_500, color=DARK, expand=True), agregar]),
            ft.Row(chips, spacing=6, run_spacing=6, wrap=True) if chips else
                ft.Text("Todavía sin músculos. Agregalos acá o tocando el cuerpo en la pestaña Músculos.",
                        size=12, color=TEXT_MUTED),
            ft.Container(height=2),
            ft.Text("Tipo de ejercicio", size=13, weight=ft.FontWeight.W_500, color=DARK),
            ft.Row([tipo("Compuesto"), tipo("Aislado")], spacing=8),
            ft.Container(height=2),
            ft.Row([tarjeta(ft.Icons.FITNESS_CENTER, "Aparato", aparato),
                    tarjeta(ft.Icons.TRACK_CHANGES, "Nivel", nivel),
                    tarjeta(ft.Icons.SCHEDULE, "Series x reps",
                            ft.Row([series, ft.Text("x", size=13, color=DARK), reps], spacing=4))], spacing=8),
            *self._boton_guardar(),
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    # ── pestaña Músculos ──
    def _tab_musculos(self) -> ft.Column:
        e = self.ejercicio
        principal = e["puntos"][0]["zona"] if e.get("puntos") else None

        def lienzo(vista, titulo):
            capas = [_mini_cuerpo(e, CANVAS_W, CANVAS_H, vista=vista, principal=principal),
                     ft.GestureDetector(width=CANVAS_W, height=CANVAS_H, mouse_cursor=ft.MouseCursor.CLICK,
                                        on_tap_down=lambda ev, v=vista: self._tocar_cuerpo(v, ev),
                                        on_hover=lambda ev, v=vista: self._hover_cuerpo(v, ev),
                                        on_exit=lambda ev: self._mostrar_hover(None))]
            return ft.Column([ft.Container(ft.Stack(capas, width=CANVAS_W, height=CANVAS_H), bgcolor="#FBFAF6",
                                           border_radius=14, padding=8),
                              ft.Text(titulo, size=10.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED)],
                             horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

        chips = []
        for i, p in enumerate(e.get("puntos") or []):
            chip = _chip(repo.NOMBRE_CORTO[p["zona"]].capitalize(), _colores_grupo(p["zona"]) if i == 0 else GRIS_CHIP,
                         on_quitar=lambda ev, z=p["zona"]: self._alternar_zona(z))
            if i > 0:
                chip = ft.Container(chip, on_click=lambda ev, z=p["zona"]: self._hacer_principal(z),
                                    tooltip="Tocá para hacerlo el músculo principal")
            chips.append(chip)
        return ft.Column([
            ft.Container(height=4),
            ft.Text("Tocá un músculo para agregarlo o quitarlo. El primero es el principal.", size=12, color=TEXT_MUTED),
            ft.Row([lienzo("frente", "FRENTE"), lienzo("espalda", "ESPALDA")], spacing=14,
                   alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(self.nombre_hover, alignment=ft.Alignment.CENTER, height=18),
            ft.Text("Músculos elegidos", size=13, weight=ft.FontWeight.W_500, color=DARK),
            ft.Row(chips, spacing=6, run_spacing=6, wrap=True) if chips else
                ft.Text("Todavía no elegiste ninguno.", size=12, color=TEXT_MUTED),
            *self._boton_guardar(),
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def _zona_del_evento(self, vista: str, ev) -> str | None:
        return _zona_en_punto(vista, int(ev.local_position.x / CANVAS_W * ASSET_W),
                              int(ev.local_position.y / CANVAS_H * ASSET_H))

    def _tocar_cuerpo(self, vista: str, ev):
        zona = self._zona_del_evento(vista, ev)
        if zona:
            self._alternar_zona(zona)

    def _hover_cuerpo(self, vista: str, ev):
        self._mostrar_hover(self._zona_del_evento(vista, ev))

    def _mostrar_hover(self, zona: str | None):
        texto = ""
        if zona:
            elegida = any(p["zona"] == zona for p in self.ejercicio.get("puntos") or [])
            texto = f"{repo.ZONAS_MUSCULARES[zona]['etiqueta']} · tocá para {'quitar' if elegida else 'agregar'}"
        if texto != self.nombre_hover.value:
            self.nombre_hover.value = texto
            _actualizar(self.nombre_hover)

    # ── pestaña Variantes ──
    def _tab_variantes(self) -> ft.Column:
        e = self.ejercicio
        grupo = repo.grupo_de(e)
        zonas = {p["zona"] for p in e.get("puntos") or []}
        if not grupo:
            return ft.Column([ft.Container(height=4), ft.Text("Elegí los músculos del ejercicio para ver sus variantes.",
                                                              size=12.5, color=TEXT_MUTED)])
        # mismo grupo muscular o al menos un músculo en común; primero los que comparten más
        def en_comun(x):
            return len(zonas & {p["zona"] for p in x.get("puntos") or []})
        variantes = [x for x in self.ejercicios if x["id"] != e.get("id") and (repo.grupo_de(x) == grupo or en_comun(x))]
        variantes.sort(key=lambda x: (repo.grupo_de(x) != grupo, -en_comun(x), x["nombre"].lower()))

        # la misma tabla del medio, en chico
        encabezado = ft.Container(
            ft.Row([ft.Container(ft.Text("EJERCICIO", size=10.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED), expand=5),
                    ft.Container(ft.Text("MÚSCULOS", size=10.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED), expand=4),
                    ft.Container(width=20)], spacing=8),
            padding=ft.padding.symmetric(horizontal=12, vertical=9),
        )
        filas = [ft.Container(
            ft.Row([
                ft.Container(ft.Row([self._imagen(x, 40, 8),
                                     ft.Text(x["nombre"], size=12, weight=ft.FontWeight.W_500, color=DARK, max_lines=2,
                                             overflow=ft.TextOverflow.ELLIPSIS, expand=True)], spacing=10), expand=5),
                ft.Container(self._chips_musculos(x, 1, chico=True), expand=4),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=TEXT_MUTED),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=12, vertical=5), ink=True,
            border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
            on_click=lambda ev, eid=x["id"]: self._abrir(eid), tooltip="Abrir este ejercicio",
        ) for x in variantes]
        tabla = ft.Container(ft.Column([encabezado, *filas], spacing=0), border=ft.border.all(1, GRAY_LIGHT),
                             border_radius=12, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)
        return ft.Column([
            ft.Container(height=4),
            ft.Text(f"Variantes ({len(variantes)})", size=13, weight=ft.FontWeight.W_500, color=DARK),
            ft.Text("Ejercicios que trabajan los mismos músculos: sirven para reemplazarlo en una rutina.",
                    size=12, color=TEXT_MUTED),
            tabla if filas else ft.Text("No hay otros ejercicios parecidos.", size=12, color=TEXT_MUTED),
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    # ── cambios ──
    def _marcar(self):
        if not self.sin_guardar:
            self.sin_guardar = True
            self._mostrar("● Cambios sin guardar", GOLD_DARK)

    def _mostrar(self, texto: str, color: str):
        self.mensaje.value, self.mensaje.color = texto, color
        _actualizar(self.mensaje)

    def _cambio(self, campo: str, valor, rerender: bool = False):
        self.ejercicio[campo] = valor
        self._marcar()
        if rerender:
            self._render()

    def _cambio_pasos(self, ev):
        texto = ev.control.value or ""
        if len(texto) > MAX_PASOS_CHARS:
            texto = ev.control.value = texto[:MAX_PASOS_CHARS]
            _actualizar(ev.control)
        self.ejercicio["pasos"] = [l.strip() for l in texto.splitlines() if l.strip()]
        self.contador.value = f"{len(texto)}/{MAX_PASOS_CHARS}"
        _actualizar(self.contador)
        self._marcar()

    def _cambio_series(self, ev):
        try:
            self.ejercicio["series"] = max(1, int(ev.control.value)) if (ev.control.value or "").strip() else None
            self._marcar()
        except ValueError:
            pass

    def _alternar_zona(self, zona: str):
        puntos = self.ejercicio.setdefault("puntos", [])
        if any(p["zona"] == zona for p in puntos):
            self.ejercicio["puntos"] = [p for p in puntos if p["zona"] != zona]
        else:
            puntos.append(repo.nuevo_punto(zona))
        self._marcar()
        self._render()

    def _hacer_principal(self, zona: str):
        puntos = self.ejercicio["puntos"]
        self.ejercicio["puntos"] = [p for p in puntos if p["zona"] == zona] + [p for p in puntos if p["zona"] != zona]
        self._marcar()
        self._render()

    # ── imagen ──
    def _elegir_imagen(self, e=None):
        async def _abrir_selector():
            if self.selector_archivo not in self.page.services:
                self.page.services.append(self.selector_archivo)
            archivos = await self.selector_archivo.pick_files(
                dialog_title="Elegí el dibujo del ejercicio", file_type=ft.FilePickerFileType.IMAGE)
            if archivos and archivos[0].path:
                self.imagen_nueva = archivos[0].path
                self._marcar()
                self._render()
                self._mostrar("● Imagen nueva elegida: se aplica al guardar", GOLD_DARK)
        self.page.run_task(_abrir_selector)

    def _aplicar_imagen(self, ejercicio_id: str):
        """Guarda la imagen elegida como img/ejercicios/<id>.png (cuadrada, 512 px)."""
        im = Image.open(self.imagen_nueva).convert("RGB")
        lado = min(im.size)
        im = im.crop(((im.width - lado) // 2, (im.height - lado) // 2, (im.width + lado) // 2, (im.height + lado) // 2))
        os.makedirs(repo.CARPETA_IMAGENES, exist_ok=True)
        im.resize((512, 512), Image.LANCZOS).save(os.path.join(repo.CARPETA_IMAGENES, f"{ejercicio_id}.png"))
        self.version_img[ejercicio_id] = time.time()
        self.imagen_nueva = None

    # ── guardar / eliminar / publicar ──
    def _guardar(self, e=None) -> bool:
        if not (self.ejercicio.get("nombre") or "").strip():
            self._mostrar("Poné el nombre del ejercicio.", RED)
            return False
        if not self.ejercicio.get("pasos"):
            self._mostrar("Escribí cómo se realiza (al menos un paso).", RED)
            return False
        try:
            self.ejercicios = repo.guardar_ejercicio(self.ejercicios, copy.deepcopy(self.ejercicio))
            nuevo_id = self.ejercicios[-1]["id"]
            self.ejercicio["id"] = nuevo_id
            if self.imagen_nueva:
                self._aplicar_imagen(nuevo_id)
        except ValueError as ex:
            self._mostrar(f"⚠ {ex}", RED)
            return False
        except Exception as ex:
            self._mostrar(f"No se pudo guardar: {ex}", RED)
            return False
        self.sel = self.ejercicio["id"]
        self.sin_guardar = False
        self._render()
        self._mostrar("✓ Guardado", GREEN)
        return True

    def _alternar_publicado_lista(self, ejercicio: dict):
        copia = copy.deepcopy(ejercicio)
        copia["publicado"] = not copia.get("publicado")
        try:
            self.ejercicios = repo.guardar_ejercicio(self.ejercicios, copia)
        except ValueError as ex:
            self.error_carga = f"No se pudo {'publicar' if copia.get('publicado') else 'despublicar'} \"{copia.get('nombre')}\": {ex}"
        except Exception as ex:
            self.error_carga = str(ex)
        if self.sel == copia["id"] and not self.sin_guardar:
            self.ejercicio = copy.deepcopy(copia)
        self._render()

    def _confirmar_eliminar(self, ejercicio: dict):
        def _eliminar(ev):
            self.page.pop_dialog()
            try:
                self.ejercicios = repo.eliminar_ejercicio(self.ejercicios, ejercicio["id"])
            except Exception as ex:
                self.error_carga = str(ex)
            if self.sel == ejercicio["id"]:
                self._cerrar_forzado()
            else:
                self._render()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Eliminar este ejercicio?", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text(f"\"{ejercicio['nombre']}\" se borra para siempre y deja de verse en la app.",
                            size=13, color=TEXT_MUTED),
            actions=[ft.TextButton("Cancelar", on_click=lambda ev: self.page.pop_dialog()),
                     ft.TextButton("Eliminar", on_click=_eliminar, style=ft.ButtonStyle(color=RED))],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def _preguntar_descartar(self, continuar):
        def _guardar_y_seguir(ev):
            self.page.pop_dialog()
            if self._guardar():
                continuar()

        def _descartar(ev):
            self.page.pop_dialog()
            self.sin_guardar = False
            continuar()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Tenés cambios sin guardar", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text("¿Querés guardar el ejercicio antes de salir?", size=13, color=TEXT_MUTED),
            actions=[ft.TextButton("Seguir editando", on_click=lambda ev: self.page.pop_dialog()),
                     ft.TextButton("Descartar", on_click=_descartar, style=ft.ButtonStyle(color=RED)),
                     ft.TextButton("Guardar", on_click=_guardar_y_seguir)],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def _refrescar(self, e=None):
        try:
            self.ejercicios = repo.cargar_ejercicios(forzar=True)
            self.error_carga = None
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()


def build_editor_ejercicios(page: ft.Page) -> ft.Column:
    return EditorEjerciciosView(page).build()
