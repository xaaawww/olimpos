# OLIMPOS GYM — NutriStore, la tienda del club (solo el Dueño)
#
# Dos vistas:
#   Productos  arriba cuatro tarjetas de resumen (productos, categorías, stock
#              bajo y valor del stock); abajo la tabla filtrable por categoría
#              (etiqueta) y estado. Al tocar un producto se abre a la derecha
#              "Editar producto": imagen, nombre, SKU, categorías, precio,
#              costo, stock, descripción y si está publicado en la app.
#   Pedidos    lo que pidieron los socios desde la app: se paga y retira en la
#              recepción, y acá se marca como entregado (o se cancela y el
#              stock vuelve).
#
# Igual que en Ejercicios, se edita una COPIA: nada llega a la base hasta
# "Guardar cambios", y salir con cambios pendientes pregunta antes.

import copy
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import status_pill
import dietas_repo
import empleados_credenciales
import tienda_repo as repo
import validaciones

POR_PAGINA = 8
CHIP_CATEGORIA = ("#EEF2F7", "#4B6584")
CHIP_GRIS = ("#F1F0EA", "#6B6656")
# Estado del stock: (fondo, texto, ícono)
ESTADOS = {
    "En stock":   ("#DCFCE7", "#16A34A", ft.Icons.CIRCLE),
    "Stock bajo": ("#FEF3C7", "#D97706", ft.Icons.WARNING_AMBER_ROUNDED),
    "Sin stock":  ("#FEE2E2", "#DC2626", ft.Icons.REMOVE_SHOPPING_CART_OUTLINED),
}
FILTROS_ESTADO = ["Todos los estados", "En stock", "Stock bajo", "Sin stock", "Borradores"]
CAMPO = dict(dense=True, border_radius=10, border_color=GRAY_LIGHT, bgcolor=WHITE, text_size=13.5,
             content_padding=ft.padding.symmetric(horizontal=12, vertical=12))


def _actualizar(control: ft.Control):
    try:
        if control.page:
            control.update()
    except RuntimeError:
        pass


def _plata(v: float) -> str:
    return "$ " + (f"{v:,.0f}".replace(",", ".") if float(v).is_integer()
                   else f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


def _chip(texto: str, colores: tuple[str, str], on_quitar=None) -> ft.Container:
    fondo, color = colores
    controles = [ft.Text(texto, size=11.5, weight=ft.FontWeight.W_500, color=color,
                         max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)]
    if on_quitar:
        controles.append(ft.Container(ft.Icon(ft.Icons.CLOSE, size=13, color=color), on_click=on_quitar,
                                      border_radius=8, padding=1, tooltip="Quitar"))
    return ft.Container(ft.Row(controles, spacing=6, tight=True), bgcolor=fondo, border_radius=8,
                        padding=ft.padding.symmetric(horizontal=10, vertical=4))


def _estado(texto: str) -> ft.Container:
    fondo, color, icono = ESTADOS[texto]
    return ft.Container(
        ft.Row([ft.Icon(icono, size=9 if icono == ft.Icons.CIRCLE else 12, color=color),
                ft.Text(texto, size=11.5, weight=ft.FontWeight.W_500, color=color)], spacing=5, tight=True),
        bgcolor=fondo, border_radius=20, padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )


def _etiqueta(texto: str, obligatorio: bool = False) -> ft.Row:
    return ft.Row([ft.Text(texto, size=12.5, color=TEXT_MUTED)] +
                  ([ft.Text("*", size=12.5, color=RED)] if obligatorio else []), spacing=3)


class TiendaView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.error_carga = None
        try:
            self.productos = repo.cargar_productos(forzar=True)
        except Exception as ex:
            self.productos = []
            self.error_carga = str(ex)
        self.vista = "productos"     # productos | pedidos
        self.categoria = None        # filtro por etiqueta (None = todas)
        self.estado = FILTROS_ESTADO[0]
        self.busqueda = ""
        self.pagina = 0
        self.ver_historial = False
        self.sel = None              # id del producto abierto ("nuevo" si todavía no se guardó)
        self.producto = None         # copia que se está editando
        self.sin_guardar = False
        self.root = ft.Column(spacing=0, expand=True)
        self.mensaje = ft.Text("", size=12, weight=ft.FontWeight.W_500)
        self.buscador = ft.TextField(
            hint_text="Buscar producto, categoría o SKU...", prefix_icon=ft.Icons.SEARCH, expand=True,
            on_change=self._buscar, **CAMPO,
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
        agregar = ft.Container(
            ft.Row([ft.Icon(ft.Icons.ADD, size=18, color=DARK),
                    ft.Text("Agregar producto", size=14, weight=ft.FontWeight.W_500, color=DARK)], spacing=8, tight=True),
            bgcolor=GOLD, border_radius=12, padding=ft.padding.symmetric(horizontal=22, vertical=13),
            on_click=self._nuevo, ink=True,
        )
        cabecera = ft.Row([
            ft.Column([
                ft.Text("NutriStore", size=28, weight=ft.FontWeight.W_600, color=DARK,
                        font_family="Poppins", style=ft.TextStyle(height=1.15)),
                ft.Text("Gestioná el catálogo de productos de la tienda. Los socios piden desde la app y retiran en la recepción.",
                        size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            ft.IconButton(ft.Icons.REFRESH, tooltip="Volver a leer de la base", on_click=self._refrescar),
            *([agregar] if self.vista == "productos" else []),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        controles = [cabecera, self._selector_vista()]
        if self.error_carga:
            controles.append(ft.Container(ft.Text(f"⚠️ {self.error_carga}", size=12, color=RED),
                                          bgcolor=BADGE_RED_BG, border_radius=10, padding=12))
        if self.vista == "productos":
            izquierda = ft.Column([self._resumen(), self._filtros(), self._tabla()], spacing=16, expand=True)
            controles.append(ft.Row([izquierda] + ([self._panel()] if self.sel else []),
                                    spacing=20, vertical_alignment=ft.CrossAxisAlignment.START))
        else:
            controles.append(self._pedidos())
        return ft.Column(controles, spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)

    def _selector_vista(self) -> ft.Container:
        try:
            pendientes = len(repo.pedidos("pendiente"))
        except Exception:
            pendientes = 0

        def tab(clave, texto):
            activa = self.vista == clave
            return ft.Container(
                ft.Text(texto, size=14, weight=ft.FontWeight.W_500 if activa else ft.FontWeight.W_400,
                        color=DARK if activa else TEXT_MUTED),
                padding=ft.padding.only(bottom=10, left=4, right=4),
                border=ft.border.only(bottom=ft.BorderSide(2.5, GOLD if activa else ft.Colors.TRANSPARENT)),
                on_click=lambda e: self._cambiar_vista(clave),
            )
        return ft.Container(ft.Row([tab("productos", "Productos"),
                                    tab("pedidos", f"Pedidos por retirar ({pendientes})")], spacing=24),
                            border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)))

    def _cambiar_vista(self, clave: str):
        if self.sin_guardar and clave != self.vista:
            self._preguntar_descartar(lambda: self._cambiar_vista_forzado(clave))
            return
        self._cambiar_vista_forzado(clave)

    def _cambiar_vista_forzado(self, clave: str):
        self.vista = clave
        self.sel, self.producto, self.sin_guardar = None, None, False
        self._render()

    # ── tarjetas de resumen ──
    def _resumen(self) -> ft.Control:
        r = repo.resumen(self.productos)

        def tarjeta(icono, color_icono, titulo, valor, pie, color_pie, accion=None):
            return ft.Container(
                ft.Row([
                    ft.Container(ft.Icon(icono, size=18, color=color_icono), width=36, height=36,
                                 bgcolor=ft.Colors.with_opacity(0.12, color_icono), border_radius=10,
                                 alignment=ft.Alignment.CENTER),
                    ft.Column([
                        ft.Text(titulo, size=12, color=TEXT_MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(valor, size=22, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(pie, size=11.5, color=color_pie, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ], spacing=0, expand=True),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
                bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=14, padding=16, expand=True,
                on_click=accion, ink=accion is not None,
            )
        publicados = sum(1 for p in self.productos if p["publicado"])
        tarjetas = [
            tarjeta(ft.Icons.INVENTORY_2_OUTLINED, "#4B6584", "Total de productos", str(r["total"]),
                    f"{publicados} publicados", GREEN),
            tarjeta(ft.Icons.SELL_OUTLINED, "#4B6584", "Categorías", str(r["categorias"]), "Ver todas", TEXT_MUTED,
                    lambda e: self._filtrar_categoria(None)),
            tarjeta(ft.Icons.WARNING_AMBER_ROUNDED, "#D97706", "Stock bajo", str(r["stock_bajo"]),
                    "Revisar" if r["stock_bajo"] else "Todo en orden", "#D97706" if r["stock_bajo"] else GREEN,
                    lambda e: self._filtrar_estado("Stock bajo")),
            tarjeta(ft.Icons.PAYMENTS_OUTLINED, "#4B6584", "Valor en stock", _plata(r["valor_stock"]),
                    "a precio de venta", TEXT_MUTED),
        ]
        # Con el panel abierto la columna se angosta: 2 × 2 para que no se aprieten los textos
        if self.sel:
            return ft.Column([ft.Row(tarjetas[:2], spacing=12), ft.Row(tarjetas[2:], spacing=12)], spacing=12)
        return ft.Row(tarjetas, spacing=12)

    # ── filtros ──
    def _filtros(self) -> ft.Control:
        categorias = ft.Dropdown(
            value=self.categoria or "__todas__", width=None if self.sel else 210, expand=bool(self.sel), dense=True, text_size=13, border_radius=10,
            border_color=GRAY_LIGHT, bgcolor=WHITE,
            options=[ft.DropdownOption(key="__todas__", text="Todas las categorías")] +
                    [ft.DropdownOption(key=e, text=e) for e in repo.todas_las_etiquetas(self.productos)],
            on_select=lambda e: self._filtrar_categoria(None if e.control.value == "__todas__" else e.control.value),
        )
        estados = ft.Dropdown(
            value=self.estado, width=None if self.sel else 190, expand=bool(self.sel), dense=True, text_size=13, border_radius=10, border_color=GRAY_LIGHT,
            bgcolor=WHITE, options=[ft.DropdownOption(key=e, text=e) for e in FILTROS_ESTADO],
            on_select=lambda e: self._filtrar_estado(e.control.value),
        )
        if self.sel:   # con el panel abierto: buscador arriba y los dos filtros abajo
            return ft.Column([ft.Row([self.buscador]), ft.Row([categorias, estados], spacing=10)], spacing=10)
        return ft.Row([self.buscador, categorias, estados], spacing=10)

    def _filtrar_categoria(self, categoria: str | None):
        self.categoria, self.pagina = categoria, 0
        self._render()

    def _filtrar_estado(self, estado: str):
        self.estado, self.pagina = estado or FILTROS_ESTADO[0], 0
        self._render()

    def _buscar(self, e):
        self.busqueda, self.pagina = e.control.value or "", 0
        self._render()

    def _filtrados(self) -> list[dict]:
        res = self.productos
        if self.categoria:
            clave = validaciones.normalizar(self.categoria)
            res = [p for p in res if clave in map(validaciones.normalizar, p["etiquetas"])]
        if self.estado == "Borradores":
            res = [p for p in res if not p["publicado"]]
        elif self.estado in ESTADOS:
            res = [p for p in res if repo.estado_stock(p) == self.estado]
        texto = validaciones.normalizar(self.busqueda)
        if texto:
            res = [p for p in res if texto in validaciones.normalizar(p["nombre"]) or texto in p["sku"].lower()
                   or any(texto in validaciones.normalizar(e) for e in p["etiquetas"])]
        return res

    # ── tabla ──
    def _imagen(self, imagen: str | None, lado: int, radio: int = 10) -> ft.Control:
        if not imagen:
            return ft.Container(ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED, size=lado * 0.42, color=TEXT_MUTED),
                                width=lado, height=lado, alignment=ft.Alignment.CENTER, bgcolor="#F4F2EB",
                                border_radius=radio)
        return ft.Container(ft.Image(src=imagen, width=lado, height=lado, fit=ft.BoxFit.COVER),
                            width=lado, height=lado, border_radius=radio, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    def _columnas(self):
        if self.sel:
            return [("Producto", 5), ("Precio", 2), ("Estado", 2), ("", 0)]
        return [("Producto", 5), ("Categoría", 3), ("Precio", 2), ("Stock", 1), ("Estado", 2), ("", 0)]

    @staticmethod
    def _celda(control: ft.Control, proporcion: int) -> ft.Container:
        if proporcion:
            return ft.Container(control, expand=proporcion)
        return ft.Container(control, width=48, alignment=ft.Alignment.CENTER)

    def _tabla(self) -> ft.Container:
        cols = self._columnas()
        encabezado = ft.Container(
            ft.Row([self._celda(ft.Text(t, size=12, weight=ft.FontWeight.W_500, color=TEXT_MUTED), p)
                    for t, p in cols], spacing=12),
            padding=ft.padding.symmetric(horizontal=18, vertical=13),
        )
        lista = self._filtrados()
        paginas = max(1, -(-len(lista) // POR_PAGINA))
        self.pagina = min(self.pagina, paginas - 1)
        desde = self.pagina * POR_PAGINA
        visibles = lista[desde:desde + POR_PAGINA]
        filas = [self._fila(p, cols) for p in visibles] or [ft.Container(
            ft.Text("Ningún producto coincide con los filtros." if self.productos
                    else "Todavía no hay productos. Tocá «Agregar producto» para cargar el primero.",
                    size=13, color=TEXT_MUTED), padding=20, border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)))]

        def boton_pagina(i):
            activa = i == self.pagina
            return ft.Container(ft.Text(str(i + 1), size=12, color=DARK, weight=ft.FontWeight.W_500 if activa else None),
                                width=26, height=26, alignment=ft.Alignment.CENTER, border_radius=6,
                                bgcolor=GOLD_BG2 if activa else None, on_click=lambda e: self._ir_pagina(i))
        pie = ft.Container(ft.Row([
            ft.Text(f"Mostrando {desde + 1 if lista else 0}–{desde + len(visibles)} de {len(lista)} productos",
                    size=12, color=TEXT_MUTED, expand=True),
            ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_size=18, disabled=self.pagina == 0,
                          on_click=lambda e: self._ir_pagina(self.pagina - 1)),
            *[boton_pagina(i) for i in range(paginas)],
            ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_size=18, disabled=self.pagina >= paginas - 1,
                          on_click=lambda e: self._ir_pagina(self.pagina + 1)),
        ], spacing=2), padding=ft.padding.symmetric(horizontal=18, vertical=6),
            border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)))
        return ft.Container(ft.Column([encabezado, *filas, pie], spacing=0), bgcolor=WHITE,
                            border=ft.border.all(1, GRAY_LIGHT), border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    def _ir_pagina(self, i: int):
        self.pagina = max(0, i)
        self._render()

    def _fila(self, p: dict, cols) -> ft.Container:
        menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT, icon_color=DARK, tooltip="Más opciones",
            items=[
                ft.PopupMenuItem(content=ft.Text("✏️  Editar"), on_click=lambda ev, pid=p["id"]: self._abrir(pid)),
                ft.PopupMenuItem(content=ft.Text("📢  Pasar a borrador" if p["publicado"] else "📢  Publicar en la app"),
                                 on_click=lambda ev, pr=p: self._alternar_publicado_lista(pr)),
                ft.PopupMenuItem(content=ft.Text("🗑️  Eliminar", color=RED), on_click=lambda ev, pr=p: self._confirmar_eliminar(pr)),
            ],
        )
        sub = f"SKU: {p['sku']}" if p["sku"] else "Sin SKU"
        nombre = ft.Column([
            ft.Text(p["nombre"], size=13.5, weight=ft.FontWeight.W_500, color=DARK, max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS),
            ft.Text(sub + ("" if p["publicado"] else " · Borrador"), size=11.5,
                    color=TEXT_MUTED if p["publicado"] else GOLD_DARK),
        ], spacing=1, expand=True)
        celdas = {"Producto": ft.Row([self._imagen(p["imagen"], 44), nombre], spacing=12),
                  "Categoría": ft.Row([_chip(p["etiquetas"][0], CHIP_CATEGORIA)] if p["etiquetas"] else
                                      [ft.Text("—", size=12.5, color=TEXT_MUTED)]),
                  "Precio": ft.Text(_plata(p["precio"]), size=13.5, color=DARK),
                  "Stock": ft.Text(str(p["stock"]), size=13.5, color=DARK),
                  "Estado": ft.Row([_estado(repo.estado_stock(p))]),
                  "": menu}
        return ft.Container(
            ft.Row([self._celda(celdas[t], pr) for t, pr in cols], spacing=12,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=GOLD_BG if p["id"] == self.sel else None,
            padding=ft.padding.symmetric(horizontal=18, vertical=8),
            border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
            on_click=lambda ev, pid=p["id"]: self._abrir(pid), ink=True,
        )

    # ══════════════════════════ PANEL ══════════════════════════
    def _abrir(self, id_producto: str):
        if self.sin_guardar and id_producto != self.sel:
            self._preguntar_descartar(lambda: self._abrir_forzado(id_producto))
            return
        self._abrir_forzado(id_producto)

    def _abrir_forzado(self, id_producto: str):
        self.sel = id_producto
        self.producto = copy.deepcopy(next(p for p in self.productos if p["id"] == id_producto))
        self._reiniciar_panel()

    def _nuevo(self, e=None):
        if self.sin_guardar:
            self._preguntar_descartar(self._nuevo_forzado)
            return
        self._nuevo_forzado()

    def _nuevo_forzado(self):
        self.sel = "nuevo"
        self.producto = repo.nuevo_producto()
        self._reiniciar_panel()

    def _reiniciar_panel(self):
        self.sin_guardar = False
        self._mostrar("", TEXT_MUTED)
        self._render()

    def _cerrar(self, e=None):
        if self.sin_guardar:
            self._preguntar_descartar(self._cerrar_forzado)
            return
        self._cerrar_forzado()

    def _cerrar_forzado(self):
        self.sel, self.producto, self.sin_guardar = None, None, False
        self._render()

    def _panel(self) -> ft.Container:
        p = self.producto
        publicado = p["publicado"]

        cambiar = ft.Container(
            ft.Row([ft.Icon(ft.Icons.UPLOAD_OUTLINED, size=15, color=DARK),
                    ft.Text("Cambiar imagen" if p["imagen"] else "Agregar imagen", size=12, color=DARK)],
                   spacing=6, tight=True, alignment=ft.MainAxisAlignment.CENTER),
            border=ft.border.all(1, GRAY_LIGHT), border_radius=8, padding=ft.padding.symmetric(vertical=7),
            on_click=self._elegir_imagen, ink=True, width=120,
        )
        quitar = ft.TextButton("Quitar imagen", style=ft.ButtonStyle(color=TEXT_MUTED),
                               on_click=lambda e: self._cambio("imagen", None, True)) if p["imagen"] else ft.Container()
        columna_imagen = ft.Column([self._imagen(p["imagen"], 120, 12), cambiar, quitar], spacing=6,
                                   horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        nombre = ft.TextField(value=p["nombre"], hint_text="Ej.: Proteína whey 1 kg", max_length=80, counter=ft.Text(""),
                              on_change=lambda ev: self._cambio("nombre", ev.control.value), **CAMPO)
        sku = ft.TextField(value=p["sku"], hint_text="Ej.: PRT-001", max_length=30, counter=ft.Text(""),
                           input_filter=ft.InputFilter(regex_string=r"[A-Za-z0-9\-]"), capitalization=ft.TextCapitalization.CHARACTERS,
                           on_change=lambda ev: self._cambio("sku", ev.control.value), **CAMPO)
        switch = ft.Switch(value=publicado, active_color=GOLD, scale=0.8,
                           on_change=lambda ev: self._cambio("publicado", ev.control.value, rerender=True))
        estado = ft.Row([status_pill("Publicado" if publicado else "Borrador", "active" if publicado else "pending"),
                         ft.Container(expand=True), ft.Text("Visible en la app", size=12, color=TEXT_MUTED), switch],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
        lado_derecho = ft.Column([estado, _etiqueta("Nombre del producto", True), nombre,
                                  _etiqueta("SKU"), sku], spacing=6, expand=True)

        # categorías (etiquetas)
        chips = [_chip(e, CHIP_CATEGORIA if i == 0 else CHIP_GRIS, on_quitar=lambda ev, t=e: self._quitar_etiqueta(t))
                 for i, e in enumerate(p["etiquetas"])]
        ya = {validaciones.normalizar(e) for e in p["etiquetas"]}
        sugeridas = [e for e in dict.fromkeys(repo.todas_las_etiquetas(self.productos) + repo.ETIQUETAS_SUGERIDAS)
                     if validaciones.normalizar(e) not in ya]
        lleno = len(p["etiquetas"]) >= repo.MAX_ETIQUETAS
        nueva = ft.TextField(hint_text="Escribí una categoría y Enter", max_length=30, counter=ft.Text(""), expand=True,
                             disabled=lleno, on_submit=lambda ev: self._agregar_etiqueta(ev.control.value), **CAMPO)
        sugerencias = ft.PopupMenuButton(
            content=ft.Container(ft.Row([ft.Text("Elegir", size=12.5, color=DARK),
                                         ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=16, color=DARK)], spacing=4, tight=True),
                                 border=ft.border.all(1, GRAY_LIGHT), border_radius=10, bgcolor=WHITE,
                                 padding=ft.padding.symmetric(horizontal=12, vertical=11)),
            items=[ft.PopupMenuItem(content=ft.Text(e), on_click=lambda ev, t=e: self._agregar_etiqueta(t)) for e in sugeridas],
            tooltip="Elegir una categoría", disabled=lleno or not sugeridas,
        )

        def plata(campo, valor, ayuda):
            return ft.TextField(value=(f"{valor:g}".replace(".", ",") if valor else ""), hint_text=ayuda,
                                prefix=ft.Text("$ ", size=13.5, color=TEXT_MUTED), input_filter=validaciones.MONTO,
                                max_length=12, counter=ft.Text(""),
                                on_change=lambda ev: self._cambio(campo, ev.control.value), **CAMPO)
        stock = ft.TextField(value=str(p["stock"]), hint_text="0", input_filter=validaciones.SOLO_DIGITOS, max_length=6,
                             counter=ft.Text(""), on_change=lambda ev: self._cambio("stock", ev.control.value), **CAMPO)
        descripcion = ft.TextField(
            value=p["descripcion"], multiline=True, min_lines=3, max_lines=6, max_length=repo.MAX_DESCRIPCION,
            hint_text="Para qué sirve, sabor, cómo se toma, tamaño…",
            on_change=lambda ev: self._cambio("descripcion", ev.control.value), **CAMPO)

        self.caja_margen = ft.Container(self._margen(), height=44, alignment=ft.Alignment.CENTER_LEFT)

        def columna(etiqueta, control):
            return ft.Column([etiqueta, control], spacing=6, expand=True)

        botones = ft.Row([
            ft.Container(ft.Text("Cancelar", size=13.5, color=DARK), border=ft.border.all(1, GRAY_LIGHT),
                         border_radius=10, alignment=ft.Alignment.CENTER, height=44, expand=True,
                         on_click=self._cerrar, ink=True),
            ft.Container(ft.Text("Guardar cambios", size=13.5, weight=ft.FontWeight.W_500, color=DARK),
                         bgcolor=GOLD, border_radius=10, alignment=ft.Alignment.CENTER, height=44, expand=True,
                         on_click=self._guardar, ink=True),
        ], spacing=10)

        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("Nuevo producto" if self.sel == "nuevo" else "Editar producto", size=18,
                                weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins", expand=True),
                        ft.IconButton(ft.Icons.CLOSE, icon_size=18, tooltip="Cerrar", on_click=self._cerrar)]),
                ft.Row([columna_imagen, lado_derecho], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
                _etiqueta(f"Categorías (hasta {repo.MAX_ETIQUETAS}; la primera es la principal)", True),
                ft.Row(chips, spacing=6, run_spacing=6, wrap=True) if chips else
                    ft.Text("Agregá al menos una para ordenarlo en la app.", size=12, color=TEXT_MUTED),
                ft.Row([nueva, sugerencias], spacing=8),
                ft.Row([columna(_etiqueta("Precio", True), plata("precio", p["precio"], "15000")),
                        columna(_etiqueta("Costo (opcional)"), plata("costo", p["costo"], "9000"))], spacing=10),
                ft.Row([columna(_etiqueta("Stock", True), stock),
                        columna(_etiqueta("Margen"), self.caja_margen)],
                       spacing=10),
                _etiqueta("Descripción"), descripcion,
                self.mensaje,
                botones,
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
            width=470, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16,
            padding=ft.padding.symmetric(horizontal=22, vertical=16),
        )

    def _margen(self) -> ft.Text:
        try:
            precio = validaciones.numero(self.producto["precio"]) if self.producto["precio"] not in (None, "") else 0
            costo = validaciones.numero(self.producto["costo"]) if self.producto["costo"] not in (None, "") else 0
        except ValueError:
            precio = costo = 0
        if precio > 0 and costo > 0:
            return ft.Text(f"{_plata(precio - costo)} ({(precio - costo) / precio:.0%})", size=13.5,
                           color=GREEN if precio > costo else RED)
        return ft.Text("Cargá el costo para verlo", size=12, color=TEXT_MUTED)

    # ── cambios ──
    def _marcar(self):
        if not self.sin_guardar:
            self.sin_guardar = True
            self._mostrar("● Cambios sin guardar", GOLD_DARK)

    def _mostrar(self, texto: str, color: str):
        self.mensaje.value, self.mensaje.color = texto, color
        _actualizar(self.mensaje)

    def _cambio(self, campo: str, valor, rerender: bool = False):
        self.producto[campo] = valor
        self._marcar()
        if campo in ("precio", "costo") and getattr(self, "caja_margen", None):
            self.caja_margen.content = self._margen()
            _actualizar(self.caja_margen)
        if rerender:
            self._render()

    def _agregar_etiqueta(self, texto: str):
        texto = " ".join((texto or "").split())
        if not texto:
            return
        try:
            self.producto["etiquetas"] = validaciones.etiquetas(self.producto["etiquetas"] + [texto],
                                                               maximo_items=repo.MAX_ETIQUETAS, maximo_largo=30)
        except ValueError as ex:
            self._mostrar(f"⚠ {ex}", RED)
            return
        self._marcar()
        self._render()

    def _quitar_etiqueta(self, texto: str):
        self.producto["etiquetas"] = [e for e in self.producto["etiquetas"] if e != texto]
        self._marcar()
        self._render()

    def _elegir_imagen(self, e=None):
        async def _abrir_selector():
            if self.selector_archivo not in self.page.services:
                self.page.services.append(self.selector_archivo)
            archivos = await self.selector_archivo.pick_files(
                dialog_title="Elegí la foto del producto", file_type=ft.FilePickerFileType.IMAGE)
            if archivos and archivos[0].path:
                try:
                    self.producto["imagen"] = dietas_repo.procesar_imagen(archivos[0].path)
                except Exception as ex:
                    self._mostrar(f"No se pudo abrir la imagen: {ex}", RED)
                    return
                self._marcar()
                self._render()
                self._mostrar("● Imagen nueva: se aplica al guardar", GOLD_DARK)
        self.page.run_task(_abrir_selector)

    # ── guardar / eliminar / publicar ──
    def _guardar(self, e=None) -> bool:
        copia = copy.deepcopy(self.producto)
        try:
            self.productos = repo.guardar(copia)
        except ValueError as ex:
            self._mostrar(f"⚠ {ex}", RED)
            return False
        except Exception as ex:
            self._mostrar(f"No se pudo guardar: {ex}", RED)
            return False
        self.producto = copy.deepcopy(next(p for p in self.productos if p["id"] == copia["id"]))
        self.sel = copia["id"]
        self.sin_guardar = False
        self._render()
        self._mostrar("✓ Guardado", GREEN)
        return True

    def _alternar_publicado_lista(self, producto: dict):
        copia = copy.deepcopy(producto)
        copia["publicado"] = not copia["publicado"]
        try:
            self.productos = repo.guardar(copia)
            self.error_carga = None
        except Exception as ex:
            self.error_carga = f"No se pudo {'publicar' if copia['publicado'] else 'despublicar'} \"{copia['nombre']}\": {ex}"
        if self.sel == copia["id"] and not self.sin_guardar:
            self.producto = copy.deepcopy(next((p for p in self.productos if p["id"] == copia["id"]), copia))
        self._render()

    def _confirmar_eliminar(self, producto: dict):
        def _eliminar(ev):
            self.page.pop_dialog()
            try:
                self.productos, aviso = repo.eliminar(producto["id"])
                self.error_carga = None if aviso == "Producto eliminado." else aviso
            except Exception as ex:
                self.error_carga = str(ex)
            if self.sel == producto["id"]:
                self._cerrar_forzado()
            else:
                self._render()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Eliminar este producto?", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text(f"\"{producto['nombre']}\" deja de verse en la app. Si ya tiene pedidos, queda como borrador.",
                            size=13, color=TEXT_MUTED, width=380),
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
            content=ft.Text("¿Querés guardar el producto antes de salir?", size=13, color=TEXT_MUTED),
            actions=[ft.TextButton("Seguir editando", on_click=lambda ev: self.page.pop_dialog()),
                     ft.TextButton("Descartar", on_click=_descartar, style=ft.ButtonStyle(color=RED)),
                     ft.TextButton("Guardar", on_click=_guardar_y_seguir)],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def _refrescar(self, e=None):
        try:
            self.productos = repo.cargar_productos(forzar=True)
            self.error_carga = None
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    # ══════════════════════════ PEDIDOS ══════════════════════════
    def _pedidos(self) -> ft.Column:
        try:
            lista = repo.pedidos(None if self.ver_historial else "pendiente")
            if self.ver_historial:
                lista = [p for p in lista if p["estado"] != "pendiente"]
        except Exception as ex:
            return ft.Column([ft.Text(f"No se pudieron cargar los pedidos: {ex}", color=RED)])
        selector = ft.Row([
            ft.Text("Historial de entregados y cancelados" if self.ver_historial
                    else "El socio paga y retira en la recepción. Marcalo como entregado cuando se lo lleve.",
                    size=13, color=TEXT_MUTED, expand=True),
            ft.TextButton("Ver pendientes" if self.ver_historial else "Ver historial",
                          on_click=lambda e: self._alternar_historial()),
        ])
        if not lista:
            vacio = ft.Container(ft.Text("No hay pedidos en el historial." if self.ver_historial
                                         else "No hay pedidos por retirar.", size=13, color=TEXT_MUTED),
                                 bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16, padding=22)
            return ft.Column([selector, vacio], spacing=14)
        return ft.Column([selector, ft.Row([self._tarjeta_pedido(p) for p in lista], wrap=True, spacing=14,
                                           run_spacing=14)], spacing=14)

    def _tarjeta_pedido(self, p: dict) -> ft.Container:
        items = [ft.Row([ft.Text(f"{i['cantidad']} × {i['nombre']}", size=13, color=DARK, expand=True),
                         ft.Text(_plata(float(i["precio"]) * i["cantidad"]), size=12.5, color=TEXT_MUTED)])
                 for i in p["items"]]
        if p["estado"] == "pendiente":
            acciones = ft.Row([
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=RED),
                              on_click=lambda e, pid=p["id"]: self._confirmar_cierre(pid, "cancelado")),
                ft.FilledButton("Entregado y cobrado", style=ft.ButtonStyle(bgcolor=GOLD, color=DARK),
                                on_click=lambda e, pid=p["id"]: self._cerrar_pedido(pid, "entregado")),
            ], alignment=ft.MainAxisAlignment.END)
        else:
            acciones = status_pill("Entregado" if p["estado"] == "entregado" else "Cancelado",
                                   "active" if p["estado"] == "entregado" else "inactive")
        return ft.Container(
            ft.Column([
                ft.Row([ft.Text(f"Pedido #{p['id']}", size=15, weight=ft.FontWeight.W_600, color=DARK,
                                font_family="Poppins", expand=True),
                        ft.Text(p["fecha"].astimezone().strftime("%d/%m %H:%M"), size=12, color=TEXT_MUTED)]),
                ft.Text(p["socio"], size=13, weight=ft.FontWeight.W_500, color=GOLD_DARK),
                ft.Divider(height=10, color=GRAY_LIGHT),
                *items,
                ft.Divider(height=10, color=GRAY_LIGHT),
                ft.Row([ft.Text("Total a cobrar" if p["estado"] == "pendiente" else "Total", size=13, color=TEXT_MUTED,
                                expand=True),
                        ft.Text(_plata(p["total"]), size=16, weight=ft.FontWeight.W_600, color=DARK)]),
                acciones,
            ], spacing=6),
            width=340, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16, padding=18,
        )

    def _alternar_historial(self):
        self.ver_historial = not self.ver_historial
        self._render()

    def _cerrar_pedido(self, id_pedido: int, estado: str):
        try:
            repo.cerrar_pedido(id_pedido, estado, empleados_credenciales.id_empleado_actual())
            self.productos = repo.cargar_productos()
            self.error_carga = None
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    def _confirmar_cierre(self, id_pedido: int, estado: str):
        def si(e):
            self.page.pop_dialog()
            self._cerrar_pedido(id_pedido, estado)
        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f"¿Cancelar el pedido #{id_pedido}?", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text("Los productos vuelven al stock y el socio lo ve como cancelado en la app.",
                            size=13, color=TEXT_MUTED, width=360),
            actions=[ft.TextButton("No", on_click=lambda e: self.page.pop_dialog()),
                     ft.TextButton("Sí, cancelar", on_click=si, style=ft.ButtonStyle(color=RED))],
            actions_alignment=ft.MainAxisAlignment.END,
        ))


def build_tienda(page: ft.Page) -> ft.Column:
    return TiendaView(page).build()
