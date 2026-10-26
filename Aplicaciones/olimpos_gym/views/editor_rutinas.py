# OLIMPOS GYM — Asignación de Rutinas (Dueño / Entrenador)
#
# A la izquierda, la tabla de socios con su rutina; al tocar uno se abre a
# la derecha UN solo formulario para armarla: nombre, ejercicios (series,
# peso de partida, peso corporal) y un único buscador para agregar más, con
# un solo "Guardar cambios" al final.
#
# Los ejercicios de una rutina NO se escriben libremente: se eligen del
# mismo catálogo que arma la pantalla "Ejercicios" (ejercicios_repo), así la
# rutina hereda la técnica y las zonas musculares reales (el "bodygraph").
# Si no existe todavía, se puede crear ahí mismo como borrador nuevo.
#
# Se edita una copia: nada llega a la base hasta "Guardar cambios".

import copy
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import status_pill
import auth_repo
import ejercicios_repo
import rutinas_repo as repo
import validaciones

COLORES_AVATAR = [("#FEF3C7", "#A16207"), ("#DCFCE7", "#15803D"), ("#FCE7F3", "#BE185D"),
                  ("#EDE9FE", "#6D28D9"), ("#DBEAFE", "#1D4ED8"), ("#FFEDD5", "#C2410C")]
ORDENES = {"nombre": "Nombre (A-Z)", "sin_rutina": "Sin rutina primero", "ejercicios": "Más ejercicios"}
MAX_SUGERENCIAS = 6


def _iniciales(nombre: str) -> str:
    partes = [p for p in (nombre or "").split() if p]
    return "".join(p[0] for p in partes[:2]).upper() or "?"


def _avatar(nombre: str, clave: str, tam: int = 38) -> ft.Container:
    fondo, letra = COLORES_AVATAR[sum(map(ord, clave or "?")) % len(COLORES_AVATAR)]
    return ft.Container(ft.Text(_iniciales(nombre), size=tam * 0.36, weight=ft.FontWeight.W_600, color=letra),
                        width=tam, height=tam, border_radius=tam / 2, bgcolor=fondo, alignment=ft.Alignment.CENTER)


def _chip(texto: str, fondo: str = GOLD_BG, color: str = GOLD_DARK) -> ft.Container:
    return ft.Container(ft.Text(texto, size=11.5, weight=ft.FontWeight.W_500, color=color, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS),
                        bgcolor=fondo, border_radius=20, padding=ft.padding.symmetric(horizontal=10, vertical=4))


def _mini_cuerpo(catalogo_ej: dict | None, ancho: int = 30, alto: int = 60) -> ft.Stack:
    zonas = [p["zona"] for p in (catalogo_ej or {}).get("puntos", [])]
    vista = "espalda" if zonas and zonas[0] not in ejercicios_repo.ZONAS_POR_VISTA["frente"] else "frente"
    capas = [ft.Image(src=f"cuerpo/base_{vista}.png", width=ancho, height=alto, fit=ft.BoxFit.FILL)]
    for zona in ejercicios_repo.ZONAS_POR_VISTA[vista]:
        if zona in zonas:
            capas.append(ft.Image(src=f"cuerpo/zona_{vista}_{zona}.png", width=ancho, height=alto, fit=ft.BoxFit.FILL))
    return ft.Stack(capas, width=ancho, height=alto)


def _miniatura(catalogo_ej: dict | None, lado: int) -> ft.Container:
    """El dibujo del ejercicio si tiene; si no, el cuerpo en miniatura."""
    src = ejercicios_repo.imagen_de(catalogo_ej)
    if src:
        return ft.Container(ft.Image(src=src, width=lado, height=lado, fit=ft.BoxFit.COVER),
                            width=lado, height=lado, border_radius=10, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)
    return ft.Container(_mini_cuerpo(catalogo_ej, lado // 2, lado), width=lado, alignment=ft.Alignment.CENTER)


def _actualizar(control: ft.Control):
    try:
        if control.page:
            control.update()
    except RuntimeError:
        pass


class EditorRutinasView:
    def __init__(self, page: ft.Page, nombre_entrenador: str):
        self.page = page
        self.nombre_entrenador = nombre_entrenador
        self.error_carga = None
        try:
            self.socios = auth_repo.listar_accesos_socios()
            self.rutinas = repo.cargar_rutinas()
            self.catalogo = ejercicios_repo.cargar_ejercicios()
        except Exception as ex:
            self.socios, self.rutinas, self.catalogo = [], {}, []
            self.error_carga = str(ex)
        self.filtro = "Todos"       # Todos | Con rutina | Sin rutina
        self.busqueda = ""
        self.orden = "nombre"
        self.socio_id = None        # socio abierto en el panel
        self.rutina = None          # copia que se está editando
        self.pestana = "rutina"     # rutina | propias
        self.sin_guardar = False
        self.root = ft.Column(spacing=0, expand=True)
        self.mensaje = ft.Text("", size=12, weight=ft.FontWeight.W_500)
        self.buscador = ft.TextField(
            hint_text="Buscar socio o rutina...", prefix_icon=ft.Icons.SEARCH, expand=True, dense=True,
            border_radius=12, border_color=GRAY_LIGHT, bgcolor=WHITE, on_change=self._buscar,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
        )
        self.selector_orden = ft.Dropdown(
            value=self.orden, width=230, dense=True, border_radius=12, border_color=GRAY_LIGHT, bgcolor=WHITE,
            options=[ft.DropdownOption(key=k, text=f"Ordenar: {v}") for k, v in ORDENES.items()],
            on_select=self._cambiar_orden,
        )
        self.campo_agregar = ft.TextField(
            hint_text="Agregar ejercicio: escribí para buscar en el catálogo",
            prefix_icon=ft.Icons.ADD, dense=True, border_radius=10, border_color=GOLD_LIGHT,
            on_change=self._buscar_ejercicio,
        )
        self.sugerencias = ft.Column(spacing=0)
        self.caja_sugerencias = ft.Container(self.sugerencias, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT),
                                             border_radius=10, padding=4, visible=False)
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
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Rutinas", size=13, color=TEXT_MUTED),
                ft.Text("Asignación de rutinas", size=28, weight=ft.FontWeight.W_600, color=DARK,
                        font_family="Poppins", style=ft.TextStyle(height=1.15)),
                ft.Text("Armá la rutina de cada socio: qué ejercicios hace, cuántas series y con qué peso empieza.",
                        size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            ft.IconButton(ft.Icons.REFRESH, tooltip="Volver a leer de la base", on_click=self._refrescar),
        ], vertical_alignment=ft.CrossAxisAlignment.START)

        izquierda = ft.Column([
            self._fila_filtros(),
            ft.Row([self.buscador, self.selector_orden], spacing=12),
            self._tabla(),
        ], spacing=16, expand=True)

        cuerpo = ft.Row([izquierda] + ([self._panel()] if self.socio_id else []),
                        spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)

        controles = [cabecera]
        if self.error_carga:
            controles.append(ft.Container(
                ft.Text(f"⚠️ No se pudo conectar con la base de datos: {self.error_carga}", size=12, color=RED),
                bgcolor=BADGE_RED_BG, border_radius=10, padding=12))
        controles.append(cuerpo)
        return ft.Column(controles, spacing=22, scroll=ft.ScrollMode.AUTO, expand=True)

    # ── filtros, búsqueda y orden ──
    def _rutina_de(self, uid: str) -> dict | None:
        return repo.obtener_rutina_entrenador(uid)

    def _fila_filtros(self) -> ft.Container:
        con = sum(1 for s in self.socios if self._rutina_de(s["uid"]))
        opciones = [("Todos", len(self.socios)), ("Con rutina", con), ("Sin rutina", len(self.socios) - con)]
        return ft.Container(
            ft.Row([self._chip_filtro(n, c) for n, c in opciones], spacing=4, tight=True),
            bgcolor=WHITE, border_radius=26, border=ft.border.all(1, GRAY_LIGHT), padding=4,
        )

    def _chip_filtro(self, nombre: str, cantidad: int) -> ft.Container:
        activo = nombre == self.filtro
        return ft.Container(
            ft.Text(f"{nombre} ({cantidad})", size=13, weight=ft.FontWeight.W_500 if activo else ft.FontWeight.W_400,
                    color=DARK),
            bgcolor=GOLD if activo else ft.Colors.TRANSPARENT, border_radius=22,
            padding=ft.padding.symmetric(horizontal=20, vertical=9),
            on_click=lambda e, n=nombre: self._cambiar_filtro(n), ink=True,
        )

    def _socios_visibles(self) -> list[dict]:
        res = []
        texto = self.busqueda.strip().lower()
        for s in self.socios:
            rutina = self._rutina_de(s["uid"])
            if self.filtro == "Con rutina" and not rutina:
                continue
            if self.filtro == "Sin rutina" and rutina:
                continue
            if texto and texto not in (s.get("nombre") or "").lower() and texto not in (s.get("email") or "").lower() \
                    and not (rutina and texto in rutina["nombre"].lower()):
                continue
            res.append((s, rutina))
        if self.orden == "sin_rutina":
            res.sort(key=lambda x: (x[1] is not None, (x[0].get("nombre") or "").lower()))
        elif self.orden == "ejercicios":
            res.sort(key=lambda x: (-len(x[1]["ejercicios"]) if x[1] else 1, (x[0].get("nombre") or "").lower()))
        else:
            res.sort(key=lambda x: (x[0].get("nombre") or "").lower())
        return res

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
    def _tabla(self) -> ft.Container:
        cols = [("SOCIO", 4), ("RUTINA", 3), ("EJERCICIOS", 5), ("", 1)]
        encabezado = ft.Container(
            ft.Row([ft.Container(ft.Text(t, size=11.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED), expand=p)
                    for t, p in cols], spacing=12),
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
        )
        visibles = self._socios_visibles()
        filas = [self._fila_socio(s, r, cols) for s, r in visibles]
        if not filas:
            vacio = "Todavía no hay socios con acceso a la app." if not self.socios else "Ningún socio coincide con el filtro."
            filas = [ft.Container(ft.Text(vacio, size=13, color=TEXT_MUTED), padding=20,
                                  border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)))]
        return ft.Container(ft.Column([encabezado, *filas], spacing=0), bgcolor=WHITE,
                            border=ft.border.all(1, GRAY_LIGHT), border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    def _fila_socio(self, socio: dict, rutina: dict | None, cols) -> ft.Container:
        uid = socio["uid"]
        if rutina and rutina["ejercicios"]:
            nombres = [ej["nombre"] for ej in rutina["ejercicios"]]
            # Con el panel abierto la columna se angosta: un solo chip (recortado) y "+N".
            visibles = 1 if self.socio_id else 2
            chips = [ft.Container(_chip(n), width=170 if self.socio_id else None) for n in nombres[:visibles]]
            if len(nombres) > visibles:
                chips.append(_chip(f"+{len(nombres) - visibles}", CREAM, TEXT_MUTED))
            ejercicios = ft.Row(chips, spacing=6, wrap=False)
        else:
            ejercicios = ft.Text("—", size=13, color=TEXT_MUTED)
        menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT, icon_color=DARK, tooltip="Más opciones",
            items=[
                ft.PopupMenuItem(content=ft.Text("✏️  Editar rutina" if rutina else "➕  Asignar rutina"),
                                 on_click=lambda e, u=uid: self._abrir(u)),
                ft.PopupMenuItem(content=ft.Text("🗑️  Eliminar rutina", color=RED), disabled=not rutina,
                                 on_click=lambda e, u=uid: self._confirmar_eliminar(u)),
            ],
        )
        celdas = [
            ft.Row([
                _avatar(socio.get("nombre", "?"), uid),
                ft.Column([
                    ft.Text(socio.get("nombre", "?"), size=13.5, weight=ft.FontWeight.W_500, color=DARK,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(socio.get("email", ""), size=11.5, color=TEXT_MUTED, max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=0, expand=True),
            ], spacing=12),
            ft.Text(rutina["nombre"], size=13, color=DARK, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS) if rutina
                else ft.Text("Sin rutina", size=13, color=TEXT_MUTED, italic=True),
            ejercicios,
            menu,
        ]
        elegido = uid == self.socio_id
        return ft.Container(
            ft.Row([ft.Container(c, expand=p) for c, (_, p) in zip(celdas, cols)], spacing=12,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=GOLD_BG if elegido else None,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
            on_click=lambda e, u=uid: self._abrir(u), ink=True,
        )

    # ══════════════════════════ PANEL (formulario único) ══════════════════════════
    def _abrir(self, uid: str):
        if self.sin_guardar and uid != self.socio_id:
            self._preguntar_descartar(lambda: self._abrir_forzado(uid))
            return
        self._abrir_forzado(uid)

    def _abrir_forzado(self, uid: str):
        self.socio_id = uid
        existente = self._rutina_de(uid)
        self.rutina = copy.deepcopy(existente) if existente else repo.nueva_rutina(uid, self.nombre_entrenador)
        self.pestana = "rutina"
        self.campo_agregar.value = ""
        self.sin_guardar = False
        self._mostrar("", TEXT_MUTED)
        self._render()

    def _cerrar(self, e=None):
        if self.sin_guardar:
            self._preguntar_descartar(self._cerrar_forzado)
            return
        self._cerrar_forzado()

    def _cerrar_forzado(self):
        self.socio_id, self.rutina, self.sin_guardar = None, None, False
        self._render()

    def _socio(self) -> dict:
        return next((s for s in self.socios if s["uid"] == self.socio_id), {"nombre": "?", "email": ""})

    def _panel(self) -> ft.Container:
        socio = self._socio()
        existe = self._rutina_de(self.socio_id) is not None
        propias = repo.obtener_rutinas_propias(self.socio_id)

        def pestana(clave, texto):
            activa = self.pestana == clave
            return ft.Container(
                ft.Text(texto, size=14, weight=ft.FontWeight.W_500 if activa else ft.FontWeight.W_400,
                        color=DARK if activa else TEXT_MUTED),
                padding=ft.padding.only(left=4, right=4, bottom=10),
                border=ft.border.only(bottom=ft.BorderSide(2.5, GOLD if activa else ft.Colors.TRANSPARENT)),
                on_click=lambda e: self._cambiar_pestana(clave),
            )

        contenido = self._form_rutina(existe) if self.pestana == "rutina" else self._lista_propias(propias)
        return ft.Container(
            content=ft.Column([
                ft.Container(ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16, color=DARK),
                                     ft.Text("Volver", size=13, color=DARK)], spacing=8, tight=True),
                             on_click=self._cerrar, ink=True, border_radius=8,
                             padding=ft.padding.symmetric(horizontal=4, vertical=4)),
                ft.Row([
                    _avatar(socio.get("nombre", "?"), self.socio_id, 56),
                    ft.Column([
                        ft.Row([
                            ft.Text(socio.get("nombre", "?"), size=19, weight=ft.FontWeight.W_600, color=DARK,
                                    font_family="Poppins", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                            status_pill("Con rutina" if existe else "Sin rutina", "active" if existe else "pending"),
                        ], spacing=8),
                        ft.Text(socio.get("email", ""), size=12.5, color=TEXT_MUTED),
                    ], spacing=2, expand=True),
                ], spacing=14),
                ft.Container(
                    ft.Row([pestana("rutina", "Rutina"),
                            pestana("propias", f"Rutinas propias ({len(propias)})")], spacing=26),
                    border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)), margin=ft.margin.only(top=6),
                ),
                contenido,
            ], spacing=12),
            width=500, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=18,
            padding=ft.padding.symmetric(horizontal=24, vertical=18),
        )

    def _cambiar_pestana(self, clave: str):
        self.pestana = clave
        self._render()

    def _etiqueta(self, texto: str, obligatorio: bool = False) -> ft.Row:
        controles = [ft.Text(texto, size=13, weight=ft.FontWeight.W_500, color=DARK)]
        if obligatorio:
            controles.append(ft.Text("*", size=13, color=RED))
        return ft.Row(controles, spacing=3)

    def _form_rutina(self, existe: bool) -> ft.Column:
        campo_nombre = ft.TextField(
            value=self.rutina["nombre"], dense=True, border_radius=10, border_color=GRAY_LIGHT,
            hint_text="Ej.: Fuerza tren superior", max_length=80, counter=ft.Text(""),
            on_change=lambda e: self._cambio_rutina("nombre", e.control.value),
        )
        ejercicios = self.rutina["ejercicios"]
        filas = [self._fila_ejercicio(i, ej) for i, ej in enumerate(ejercicios)] or [ft.Container(
            ft.Text("Todavía no agregaste ejercicios. Buscalos abajo.", size=12.5, color=TEXT_MUTED),
            bgcolor=CREAM, border_radius=10, padding=14)]

        controles = [
            ft.Container(height=4),
            self._etiqueta("Nombre de la rutina", True),
            campo_nombre,
            ft.Container(height=4),
            ft.Row([self._etiqueta(f"Ejercicios ({len(ejercicios)})", True),
                    ft.Text("series · peso de partida", size=11.5, color=TEXT_MUTED)],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Column(filas, spacing=8),
            self._buscador_ejercicios(),
            ft.Container(height=6),
            self.mensaje,
            ft.Container(
                ft.Text("Guardar cambios", size=14.5, weight=ft.FontWeight.W_500, color=DARK),
                bgcolor=GOLD, border_radius=12, alignment=ft.Alignment.CENTER, height=48,
                on_click=self._guardar, ink=True,
            ),
        ]
        if existe:
            controles.append(ft.Row([ft.TextButton("Eliminar rutina asignada", style=ft.ButtonStyle(color=RED),
                                                   on_click=lambda e: self._confirmar_eliminar(self.socio_id))],
                                    alignment=ft.MainAxisAlignment.CENTER))
        return ft.Column(controles, spacing=8)

    def _fila_ejercicio(self, i: int, ej: dict) -> ft.Container:
        cat = ejercicios_repo.obtener_ejercicio(self.catalogo, ej.get("ejercicio_id")) if ej.get("ejercicio_id") else None
        musculos = ejercicios_repo.resumen_musculos(cat) if cat else ""
        series = ft.TextField(
            value=str(ej["series_objetivo"]), width=56, dense=True, text_align=ft.TextAlign.CENTER,
            border_radius=8, border_color=GRAY_LIGHT, keyboard_type=ft.KeyboardType.NUMBER, tooltip="Series (1 a 20)",
            input_filter=validaciones.SOLO_DIGITOS, max_length=2, counter=ft.Text(""),
            on_change=lambda e, x=ej: self._cambio_entero(x, "series_objetivo", e.control.value),
        )
        peso = ft.TextField(
            value=f"{ej['peso_base_kg']:g}" if isinstance(ej["peso_base_kg"], (int, float)) else str(ej["peso_base_kg"]),
            width=92, dense=True, text_align=ft.TextAlign.CENTER, suffix="kg",
            border_radius=8, border_color=GRAY_LIGHT, keyboard_type=ft.KeyboardType.NUMBER,
            tooltip="Peso de partida (0 a 500 kg)", disabled=ej["es_peso_corporal"],
            input_filter=validaciones.DECIMAL, max_length=6, counter=ft.Text(""),
            on_change=lambda e, x=ej: self._cambio_decimal(x, "peso_base_kg", e.control.value),
        )
        corporal = ft.Container(
            ft.Text("Corporal", size=11, weight=ft.FontWeight.W_500,
                    color=GOLD_DARK if ej["es_peso_corporal"] else TEXT_MUTED),
            bgcolor=GOLD_BG if ej["es_peso_corporal"] else CREAM, border_radius=16,
            border=ft.border.all(1, GOLD_LIGHT if ej["es_peso_corporal"] else GRAY_LIGHT),
            padding=ft.padding.symmetric(horizontal=8, vertical=5),
            tooltip="Se hace con el propio peso del cuerpo", ink=True,
            on_click=lambda e, x=ej: self._alternar_corporal(x),
        )
        return ft.Container(
            ft.Row([
                _miniatura(cat, 52),
                ft.Column([
                    ft.Text(ej["nombre"], size=13, weight=ft.FontWeight.W_500, color=DARK, max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(musculos or "—", size=11, color=TEXT_MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=0, expand=True),
                series, peso, corporal,
                ft.IconButton(ft.Icons.CLOSE, icon_size=16, tooltip="Quitar de la rutina",
                              on_click=lambda e, idx=i: self._quitar(idx)),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CREAM, border_radius=12, padding=ft.padding.only(left=8, right=0, top=6, bottom=6),
        )

    def _buscador_ejercicios(self) -> ft.Column:
        self._llenar_sugerencias()
        return ft.Column([self.campo_agregar, self.caja_sugerencias], spacing=4)

    def _llenar_sugerencias(self):
        texto = (self.campo_agregar.value or "").strip()
        self.caja_sugerencias.visible = bool(texto)
        if not texto:
            self.sugerencias.controls = []
            return
        ya = {ej.get("ejercicio_id") for ej in self.rutina["ejercicios"]}
        coincidencias = sorted([e for e in self.catalogo if texto.lower() in e["nombre"].lower()
                                or texto.lower() in ejercicios_repo.resumen_musculos(e).lower()],
                               key=lambda e: e["nombre"])
        filas = []
        for e in coincidencias[:MAX_SUGERENCIAS]:
            repetido = e["id"] in ya
            filas.append(ft.Container(
                ft.Row([
                    _miniatura(e, 40),
                    ft.Column([ft.Text(e["nombre"], size=13, color=DARK),
                               ft.Text(ejercicios_repo.resumen_musculos(e), size=11, color=TEXT_MUTED)],
                              spacing=0, expand=True),
                    ft.Text("ya está" if repetido else "agregar", size=11.5,
                            color=TEXT_MUTED if repetido else GOLD_DARK, weight=ft.FontWeight.W_500),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=10, vertical=6), border_radius=8, ink=True,
                on_click=None if repetido else (lambda ev, eid=e["id"]: self._agregar(eid)),
            ))
        if not coincidencias:
            filas.append(ft.Container(
                ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=18, color=GOLD_DARK),
                        ft.Text(f"Crear \"{texto}\" como ejercicio nuevo", size=13, color=GOLD_DARK)], spacing=8),
                padding=10, border_radius=8, ink=True, on_click=lambda ev, n=texto: self._crear_y_agregar(n),
            ))
        self.sugerencias.controls = filas

    def _lista_propias(self, propias: list[dict]) -> ft.Column:
        if not propias:
            return ft.Column([ft.Container(ft.Text("Este socio todavía no se armó rutinas propias desde la app.",
                                                   size=12.5, color=TEXT_MUTED), padding=10)])
        return ft.Column([
            ft.Text("Las arma el socio desde la app; acá son de solo lectura.", size=12, color=TEXT_MUTED),
            *[ft.Container(
                ft.Column([
                    ft.Row([ft.Text(r.get("nombre", "?"), size=13.5, weight=ft.FontWeight.W_500, color=DARK, expand=True),
                            status_pill("Activa" if r.get("activa") else "No la sigue",
                                        "active" if r.get("activa") else "pending")]),
                    ft.Row([_chip(ej.get("nombre", "?"), CREAM, TEXT_MUTED) for ej in r.get("ejercicios", [])],
                           spacing=6, run_spacing=6, wrap=True) if r.get("ejercicios") else
                        ft.Text("Sin ejercicios todavía", size=12, color=TEXT_MUTED),
                ], spacing=8),
                bgcolor=CREAM, border_radius=12, padding=12,
            ) for r in propias],
        ], spacing=10)

    # ── cambios ──
    def _marcar(self):
        if not self.sin_guardar:
            self.sin_guardar = True
            self._mostrar("● Cambios sin guardar", GOLD_DARK)

    def _mostrar(self, texto: str, color: str):
        self.mensaje.value, self.mensaje.color = texto, color
        _actualizar(self.mensaje)

    def _cambio_rutina(self, campo: str, valor):
        self.rutina[campo] = valor
        self._marcar()

    def _cambio_entero(self, ej: dict, campo: str, valor: str):
        # Se guarda lo escrito tal cual: si no sirve, lo frena la validación al guardar
        ej[campo] = valor
        self._marcar()

    def _cambio_decimal(self, ej: dict, campo: str, valor: str):
        ej[campo] = valor
        self._marcar()

    def _alternar_corporal(self, ej: dict):
        ej["es_peso_corporal"] = not ej["es_peso_corporal"]
        self._marcar()
        self._render()

    def _quitar(self, idx: int):
        del self.rutina["ejercicios"][idx]
        self._marcar()
        self._render()

    def _buscar_ejercicio(self, e):
        # Solo se redibujan las sugerencias: el campo sigue con el foco mientras se escribe.
        self._llenar_sugerencias()
        _actualizar(self.caja_sugerencias)

    def _agregar(self, ejercicio_id: str):
        cat = ejercicios_repo.obtener_ejercicio(self.catalogo, ejercicio_id)
        if not cat:
            return
        nuevo = repo.nuevo_ejercicio_rutina()
        nuevo.update({"ejercicio_id": ejercicio_id, "nombre": cat["nombre"]})
        self.rutina["ejercicios"].append(nuevo)
        self.campo_agregar.value = ""
        self._marcar()
        self._render()

    def _crear_y_agregar(self, nombre: str):
        nuevo_cat = ejercicios_repo.nuevo_ejercicio(nombre)
        try:
            self.catalogo = ejercicios_repo.guardar_ejercicio(self.catalogo, nuevo_cat)
        except Exception as ex:
            self._mostrar(f"No se pudo crear el ejercicio: {ex}", RED)
            return
        self._agregar(nuevo_cat["id"])
        self._mostrar(f"\"{nombre}\" se creó como borrador: completá sus músculos en Ejercicios.", GOLD_DARK)

    # ── guardar / eliminar ──
    def _guardar(self, e=None) -> bool:
        if not (self.rutina.get("nombre") or "").strip():
            self._mostrar("Poné un nombre a la rutina.", RED)
            return False
        self.rutina["ejercicios"] = [ej for ej in self.rutina["ejercicios"] if ej.get("ejercicio_id")]
        if not self.rutina["ejercicios"]:
            self._mostrar("Agregá al menos un ejercicio antes de guardar.", RED)
            return False
        try:
            copia = copy.deepcopy(self.rutina)
            self.rutinas = repo.guardar_rutina(copia)
            self.rutina.update({k: copia[k] for k in ("nombre", "ejercicios")})
            self.rutina["id"] = self._rutina_de(self.socio_id)["id"]
        except ValueError as ex:
            self._mostrar(f"⚠ {ex}", RED)
            return False
        except Exception as ex:
            self._mostrar(f"No se pudo guardar: {ex}", RED)
            return False
        self.sin_guardar = False
        self._render()
        self._mostrar("✓ Guardado: ya está en la app del socio", GREEN)
        return True

    def _confirmar_eliminar(self, uid: str):
        rutina = self._rutina_de(uid)
        if not rutina:
            return

        def _eliminar(e):
            self.page.pop_dialog()
            try:
                self.rutinas = repo.eliminar_rutina(rutina["id"], uid)
            except Exception as ex:
                self._mostrar(f"No se pudo eliminar: {ex}", RED)
                return
            if self.socio_id == uid:
                self._cerrar_forzado()
            else:
                self._render()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Eliminar la rutina?", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text(f"\"{rutina['nombre']}\" deja de verse en la app del socio.", size=13, color=TEXT_MUTED),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.TextButton("Eliminar", on_click=_eliminar, style=ft.ButtonStyle(color=RED))],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def _preguntar_descartar(self, continuar):
        def _guardar_y_seguir(e):
            self.page.pop_dialog()
            if self._guardar():
                continuar()

        def _descartar(e):
            self.page.pop_dialog()
            self.sin_guardar = False
            continuar()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Tenés cambios sin guardar", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text("¿Querés guardar la rutina antes de salir?", size=13, color=TEXT_MUTED),
            actions=[ft.TextButton("Seguir editando", on_click=lambda e: self.page.pop_dialog()),
                     ft.TextButton("Descartar", on_click=_descartar, style=ft.ButtonStyle(color=RED)),
                     ft.TextButton("Guardar", on_click=_guardar_y_seguir)],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def _refrescar(self, e):
        try:
            self.socios = auth_repo.listar_accesos_socios(forzar=True)
            self.rutinas = repo.cargar_rutinas(forzar=True)
            self.catalogo = ejercicios_repo.cargar_ejercicios(forzar=True)
            self.error_carga = None
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()


def build_editor_rutinas(page: ft.Page, nombre_entrenador: str) -> ft.Column:
    return EditorRutinasView(page, nombre_entrenador).build()
