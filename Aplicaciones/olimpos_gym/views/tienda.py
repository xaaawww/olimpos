# OLIMPOS GYM — Tienda del club (solo el Dueño)
#
# Dos vistas:
#   Productos  a la izquierda la tabla (foto, etiquetas, precio, stock); al
#              tocar un producto se abre a la derecha el panel para editarlo:
#              nombre, descripción, etiquetas, precio, stock, imagen y si está
#              publicado en la app. Se organiza y filtra por etiquetas.
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

GRIS_CHIP = ("#F1F0EA", "#6B6656")
CHIP_ETIQUETA = ("#FEF3C7", "#B45309")


def _actualizar(control: ft.Control):
    try:
        if control.page:
            control.update()
    except RuntimeError:
        pass


def _plata(v: float) -> str:
    return "$ " + (f"{v:,.0f}".replace(",", ".") if float(v).is_integer()
                   else f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


def _chip(texto: str, colores: tuple[str, str], on_quitar=None, chico: bool = False) -> ft.Container:
    fondo, color = colores
    controles = [ft.Text(texto, size=11 if chico else 12, weight=ft.FontWeight.W_500, color=color,
                         max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)]
    if on_quitar:
        controles.append(ft.Container(ft.Icon(ft.Icons.CLOSE, size=13, color=color), on_click=on_quitar,
                                      border_radius=8, padding=1, tooltip="Quitar"))
    return ft.Container(ft.Row(controles, spacing=6, tight=True), bgcolor=fondo, border_radius=20,
                        padding=ft.padding.symmetric(horizontal=9 if chico else 11, vertical=3 if chico else 5))


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
        self.filtro = "Todos"
        self.busqueda = ""
        self.ver_historial = False
        self.sel = None              # id del producto abierto ("nuevo" si todavía no se guardó)
        self.producto = None         # copia que se está editando
        self.sin_guardar = False
        self.root = ft.Column(spacing=0, expand=True)
        self.mensaje = ft.Text("", size=12, weight=ft.FontWeight.W_500)
        self.contador = ft.Text("", size=11, color=TEXT_MUTED)
        self.buscador = ft.TextField(
            hint_text="Buscar producto...", prefix_icon=ft.Icons.SEARCH, expand=True, dense=True,
            border_radius=12, border_color=GRAY_LIGHT, bgcolor=WHITE, on_change=self._buscar,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=13),
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
                    ft.Text("Nuevo producto", size=14, weight=ft.FontWeight.W_500, color=DARK)], spacing=8, tight=True),
            bgcolor=GOLD, border_radius=12, padding=ft.padding.symmetric(horizontal=22, vertical=13),
            on_click=self._nuevo, ink=True,
        )
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Tienda", size=13, color=TEXT_MUTED),
                ft.Text("Tienda del club", size=28, weight=ft.FontWeight.W_600, color=DARK,
                        font_family="Poppins", style=ft.TextStyle(height=1.15)),
                ft.Text("Suplementos y productos que los socios piden desde la app y retiran en la recepción.",
                        size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            ft.IconButton(ft.Icons.REFRESH, tooltip="Volver a leer de la base", on_click=self._refrescar),
            *([nuevo] if self.vista == "productos" else []),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        controles = [cabecera, self._selector_vista()]
        if self.error_carga:
            controles.append(ft.Container(ft.Text(f"⚠️ {self.error_carga}", size=12, color=RED),
                                          bgcolor=BADGE_RED_BG, border_radius=10, padding=12))
        if self.vista == "productos":
            izquierda = ft.Column([self._fila_filtros(), ft.Row([self.buscador]), self._tabla()], spacing=16, expand=True)
            controles.append(ft.Row([izquierda] + ([self._panel()] if self.sel else []),
                                    spacing=20, vertical_alignment=ft.CrossAxisAlignment.START))
        else:
            controles.append(self._pedidos())
        return ft.Column(controles, spacing=22, scroll=ft.ScrollMode.AUTO, expand=True)

    def _selector_vista(self) -> ft.Row:
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
        return ft.Container(ft.Row([tab("productos", f"Productos ({len(self.productos)})"),
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

    # ── filtros / búsqueda ──
    def _fila_filtros(self) -> ft.Container:
        etiquetas = repo.todas_las_etiquetas(self.productos)
        opciones = [("Todos", len(self.productos))]
        for e in etiquetas:
            clave = validaciones.normalizar(e)
            opciones.append((e, sum(1 for p in self.productos if clave in map(validaciones.normalizar, p["etiquetas"]))))
        borradores = sum(1 for p in self.productos if not p["publicado"])
        sin_stock = sum(1 for p in self.productos if p["stock"] == 0)
        if borradores:
            opciones.append(("Borradores", borradores))
        if sin_stock:
            opciones.append(("Sin stock", sin_stock))

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
        res = self.productos
        if self.filtro == "Borradores":
            res = [p for p in res if not p["publicado"]]
        elif self.filtro == "Sin stock":
            res = [p for p in res if p["stock"] == 0]
        elif self.filtro != "Todos":
            clave = validaciones.normalizar(self.filtro)
            res = [p for p in res if clave in map(validaciones.normalizar, p["etiquetas"])]
        texto = validaciones.normalizar(self.busqueda)
        if texto:
            res = [p for p in res if texto in validaciones.normalizar(p["nombre"])
                   or any(texto in validaciones.normalizar(e) for e in p["etiquetas"])]
        return res

    def _cambiar_filtro(self, nombre: str):
        self.filtro = nombre
        self._render()

    def _buscar(self, e):
        self.busqueda = e.control.value or ""
        self._render()

    # ── tabla ──
    def _imagen(self, imagen: str | None, lado: int, radio: int = 10) -> ft.Control:
        if not imagen:
            return ft.Container(ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED, size=lado * 0.42, color=TEXT_MUTED),
                                width=lado, height=lado, alignment=ft.Alignment.CENTER, bgcolor="#F4F2EB",
                                border_radius=radio)
        return ft.Container(ft.Image(src=imagen, width=lado, height=lado, fit=ft.BoxFit.COVER),
                            width=lado, height=lado, border_radius=radio, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    def _tabla(self) -> ft.Container:
        cols = [("PRODUCTO", 5), ("ETIQUETAS", 4), ("PRECIO", 2), ("STOCK", 2), ("", 0)] if not self.sel else \
               [("PRODUCTO", 5), ("PRECIO", 2), ("", 0)]
        encabezado = ft.Container(
            ft.Row([self._celda(ft.Text(t, size=11.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED), p)
                    for t, p in cols], spacing=12),
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
        )
        filas = [self._fila(p, cols) for p in self._filtrados()] or [ft.Container(
            ft.Text("Ningún producto coincide con la búsqueda." if self.productos
                    else "Todavía no hay productos. Tocá «Nuevo producto» para cargar el primero.",
                    size=13, color=TEXT_MUTED), padding=20, border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)))]
        return ft.Container(ft.Column([encabezado, *filas], spacing=0), bgcolor=WHITE,
                            border=ft.border.all(1, GRAY_LIGHT), border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    @staticmethod
    def _celda(control: ft.Control, proporcion: int) -> ft.Container:
        if proporcion:
            return ft.Container(control, expand=proporcion)
        return ft.Container(control, width=56, alignment=ft.Alignment.CENTER)

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
        nombre = ft.Column([
            ft.Text(p["nombre"], size=13.5, weight=ft.FontWeight.W_500, color=DARK, max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS),
            *([] if p["publicado"] else [ft.Text("Borrador", size=11, color=GOLD_DARK)]),
        ], spacing=1, expand=True)
        celdas = [ft.Row([self._imagen(p["imagen"], 52), nombre], spacing=14)]
        if not self.sel:
            chips = [_chip(e, CHIP_ETIQUETA if i == 0 else GRIS_CHIP, chico=True) for i, e in enumerate(p["etiquetas"][:2])]
            if len(p["etiquetas"]) > 2:
                chips.append(ft.Text(f"+{len(p['etiquetas']) - 2}", size=11.5, color=TEXT_MUTED))
            celdas.append(ft.Row(chips or [ft.Text("Sin etiquetas", size=12, color=TEXT_MUTED, italic=True)], spacing=6))
        celdas.append(ft.Text(_plata(p["precio"]), size=13.5, weight=ft.FontWeight.W_500, color=DARK))
        if not self.sel:
            celdas.append(ft.Text("Sin stock" if p["stock"] == 0 else f"{p['stock']} u.", size=13,
                                  color=RED if p["stock"] == 0 else DARK))
        celdas.append(menu)
        return ft.Container(
            ft.Row([self._celda(c, pr) for c, (_, pr) in zip(celdas, cols)], spacing=12,
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

    def _etiqueta_campo(self, texto: str, obligatorio: bool = False) -> ft.Row:
        return ft.Row([ft.Text(texto, size=13, weight=ft.FontWeight.W_500, color=DARK)] +
                      ([ft.Text("*", size=13, color=RED)] if obligatorio else []), spacing=3)

    def _panel(self) -> ft.Container:
        p = self.producto
        publicado = p["publicado"]
        estado = ft.Container(
            status_pill("Publicado" if publicado else "Borrador", "active" if publicado else "pending"),
            on_click=lambda ev: self._cambio("publicado", not publicado, rerender=True),
            tooltip="Tocá para pasarlo a borrador" if publicado else "Tocá para publicarlo en la app (se aplica al guardar)",
        )

        def boton_suave(icono, texto, accion, color=GOLD_DARK, fondo=GOLD_BG2):
            return ft.Container(
                ft.Row([ft.Icon(icono, size=17, color=color),
                        ft.Text(texto, size=12.5, weight=ft.FontWeight.W_500, color=color)], spacing=8, tight=True),
                bgcolor=fondo, border_radius=10, padding=ft.padding.symmetric(horizontal=14, vertical=9),
                on_click=accion, ink=True,
            )
        botones_imagen = [boton_suave(ft.Icons.IMAGE_OUTLINED, "Cambiar imagen" if p["imagen"] else "Agregar imagen",
                                      self._elegir_imagen)]
        if p["imagen"]:
            botones_imagen.append(boton_suave(ft.Icons.DELETE_OUTLINE, "Quitar", lambda e: self._cambio("imagen", None, True),
                                              color=TEXT_MUTED, fondo="#F4F2EB"))

        # ── campos ──
        campo_nombre = ft.TextField(value=p["nombre"], dense=True, border_radius=10, border_color=GRAY_LIGHT,
                                    hint_text="Ej.: Proteína whey 1 kg", text_size=13.5, max_length=80, counter=ft.Text(""),
                                    on_change=lambda ev: self._cambio("nombre", ev.control.value))
        self.contador.value = f"{len(p['descripcion'] or '')}/{repo.MAX_DESCRIPCION}"
        campo_desc = ft.TextField(
            value=p["descripcion"], multiline=True, min_lines=3, max_lines=7, border_radius=10, border_color=GRAY_LIGHT,
            text_size=13.5, max_length=repo.MAX_DESCRIPCION, counter=ft.Text(""),
            hint_text="Para qué sirve, sabor, cómo se toma, tamaño…", on_change=self._cambio_descripcion,
        )

        chips = [_chip(e, CHIP_ETIQUETA if i == 0 else GRIS_CHIP, on_quitar=lambda ev, t=e: self._quitar_etiqueta(t))
                 for i, e in enumerate(p["etiquetas"])]
        ya = {validaciones.normalizar(e) for e in p["etiquetas"]}
        sugeridas = [e for e in dict.fromkeys(repo.todas_las_etiquetas(self.productos) + repo.ETIQUETAS_SUGERIDAS)
                     if validaciones.normalizar(e) not in ya]
        lleno = len(p["etiquetas"]) >= repo.MAX_ETIQUETAS
        nueva = ft.TextField(hint_text="Nueva etiqueta y Enter", dense=True, border_radius=10, border_color=GRAY_LIGHT,
                             text_size=13, max_length=30, counter=ft.Text(""), expand=True, disabled=lleno,
                             on_submit=lambda ev: self._agregar_etiqueta(ev.control.value))
        sugerencias = ft.PopupMenuButton(
            content=ft.Container(ft.Row([ft.Icon(ft.Icons.ADD, size=15, color=DARK),
                                         ft.Text("Sugeridas", size=12, color=DARK)], spacing=6, tight=True),
                                 border=ft.border.all(1, GRAY_LIGHT), border_radius=18,
                                 padding=ft.padding.symmetric(horizontal=12, vertical=8)),
            items=[ft.PopupMenuItem(content=ft.Text(e), on_click=lambda ev, t=e: self._agregar_etiqueta(t))
                   for e in sugeridas],
            tooltip="Elegir una etiqueta", disabled=lleno or not sugeridas,
        )

        def tarjeta(icono, titulo, control):
            return ft.Container(
                ft.Column([ft.Row([ft.Icon(icono, size=16, color=TEXT_MUTED),
                                   ft.Text(titulo, size=11, color=TEXT_MUTED)], spacing=6), control], spacing=4),
                border=ft.border.all(1, GRAY_LIGHT), border_radius=12, padding=ft.padding.symmetric(horizontal=12, vertical=9),
                expand=True,
            )
        sin_borde = dict(dense=True, border=ft.InputBorder.NONE, content_padding=0, text_size=14)
        precio = ft.TextField(value=(f"{p['precio']:g}".replace(".", ",") if p["precio"] else ""), hint_text="15000",
                              prefix=ft.Text("$ ", size=14, color=TEXT_MUTED), input_filter=validaciones.MONTO,
                              max_length=12, counter=ft.Text(""), **sin_borde,
                              on_change=lambda ev: self._cambio("precio", ev.control.value))
        stock = ft.TextField(value=str(p["stock"]), hint_text="0", input_filter=validaciones.SOLO_DIGITOS,
                             max_length=6, counter=ft.Text(""), suffix=ft.Text(" u.", size=13, color=TEXT_MUTED),
                             **sin_borde, on_change=lambda ev: self._cambio("stock", ev.control.value))

        return ft.Container(
            content=ft.Column([
                ft.Container(ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16, color=DARK),
                                     ft.Text("Volver", size=13, color=DARK)], spacing=8, tight=True),
                             on_click=self._cerrar, ink=True, border_radius=8,
                             padding=ft.padding.symmetric(horizontal=4, vertical=4)),
                ft.Row([
                    self._imagen(p["imagen"], 120, 16),
                    ft.Column([
                        ft.Row([ft.Text(p["nombre"] or "Nuevo producto", size=20, weight=ft.FontWeight.W_600, color=DARK,
                                        font_family="Poppins", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                                estado], spacing=8, vertical_alignment=ft.CrossAxisAlignment.START),
                        ft.Text(" · ".join(p["etiquetas"]) or "Sin etiquetas todavía", size=13, color=TEXT_MUTED),
                        ft.Container(height=4),
                        ft.Row(botones_imagen, spacing=8, wrap=True),
                    ], spacing=2, expand=True),
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Divider(height=18, color=GRAY_LIGHT),
                self._etiqueta_campo("Nombre del producto", True), campo_nombre,
                self._etiqueta_campo("Descripción"), campo_desc,
                ft.Row([self.contador], alignment=ft.MainAxisAlignment.END),
                ft.Row([ft.Text(f"Etiquetas (hasta {repo.MAX_ETIQUETAS})", size=13, weight=ft.FontWeight.W_500,
                                color=DARK, expand=True), sugerencias]),
                ft.Row(chips, spacing=6, run_spacing=6, wrap=True) if chips else
                    ft.Text("Agregá al menos una para ordenarlo en la app (ej.: Proteínas).", size=12, color=TEXT_MUTED),
                ft.Row([nueva]),
                ft.Row([tarjeta(ft.Icons.SELL_OUTLINED, "Precio", precio),
                        tarjeta(ft.Icons.INVENTORY_2_OUTLINED, "Stock disponible", stock)], spacing=8),
                ft.Container(height=4),
                self.mensaje,
                ft.Container(ft.Text("Guardar cambios", size=14.5, weight=ft.FontWeight.W_500, color=DARK),
                             bgcolor=GOLD, border_radius=12, alignment=ft.Alignment.CENTER, height=48,
                             on_click=self._guardar, ink=True),
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
            width=460, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=18,
            padding=ft.padding.symmetric(horizontal=24, vertical=18),
        )

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
        if rerender:
            self._render()

    def _cambio_descripcion(self, ev):
        texto = ev.control.value or ""
        self.producto["descripcion"] = texto
        self.contador.value = f"{len(texto)}/{repo.MAX_DESCRIPCION}"
        _actualizar(self.contador)
        self._marcar()

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
