# OLIMPOS GYM — Editor Visual de Dietas (Administrador / Nutricionista)
#
# Permite subir la imagen de un plato, ubicar puntos interactivos sobre ella
# (con clics, ver dietas_repo/PASO_RECORTE), asociar información nutricional
# a cada uno, guardar los cambios, ver una vista previa de cómo se verá en
# la app móvil y publicarlo. Los datos viven en Firestore/Storage a través
# de dietas_repo — esta pantalla no sabe nada de esa capa, solo llama a sus
# funciones.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import section_card, action_button, page_header, status_pill, divider
import dietas_repo as repo

CANVAS = 460
RADIO_PUNTO = 14
PASO_RECORTE = 0.18
CATEGORIAS = ["Proteína", "Verdura", "Fruta", "Carbohidrato", "Grasa saludable", "Cereal integral"]

# Grilla de la lista: 3 columnas fijas — ANCHO_TARJETA en cache_width/height
# le pide a Flutter que decodifique cada imagen directo a este tamaño (x2
# para pantallas de alta densidad) en vez de al tamaño real guardado
# (hasta 700px, ver dietas_repo.DIMENSION_MAXIMA) y después achicarla —
# decodificar de entrada más chico es lo que más pesa al abrir esta lista.
COLUMNAS_LISTA = 3
ANCHO_TARJETA = 220
ALTO_IMAGEN = 130


class EditorDietasView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.error_carga = None
        try:
            self.platos = repo.cargar_platos()
        except Exception as ex:
            self.platos = []
            self.error_carga = str(ex)
        self.vista = "lista"          # lista | editor | previa
        self.plato = None
        self.punto_sel = None
        self.modo_agregar = False
        self.aviso = None
        self.root = ft.Column(spacing=16, expand=True)
        self._montado = False

        self.file_picker = ft.FilePicker()
        self.page.services.append(self.file_picker)

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls.clear()
        if self.vista == "lista":
            self.root.controls.append(self._vista_lista())
        elif self.vista == "editor":
            self.root.controls.append(self._vista_editor())
        elif self.vista == "previa":
            self.root.controls.append(self._vista_previa())
        # Actualizar solo esta sección, no toda la página (sidebar, topbar, etc.)
        # En el primer render todavía no está montada -> no hay nada que actualizar.
        if self._montado:
            self.root.update()

    # ══════════════════════════ LISTA ══════════════════════════
    def _vista_lista(self) -> ft.Column:
        avisos = []
        if self.error_carga:
            avisos.append(ft.Container(
                content=ft.Text(f"⚠️ No se pudo conectar con Firebase: {self.error_carga}",
                                size=12, color="#DC2626", weight=ft.FontWeight.W_700),
                bgcolor="#FEE2E2", border_radius=10, padding=12,
            ))

        if not self.platos:
            grilla = section_card(ft.Column([
                ft.Text("🥗", size=34),
                ft.Text("Todavía no creaste ninguna dieta.", size=13, weight=ft.FontWeight.W_700, color=DARK),
                ft.Text("Usá \"Nuevo plato\" para empezar.", size=12, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)
        else:
            tarjetas = [self._tarjeta_plato(p) for p in self.platos]
            filas = [tarjetas[i:i + COLUMNAS_LISTA] for i in range(0, len(tarjetas), COLUMNAS_LISTA)]
            grilla = ft.Column([ft.Row(fila, spacing=16) for fila in filas], spacing=16)

        return ft.Column([
            page_header(
                "🖼️ Editor Visual de Dietas",
                "Subí una imagen, ubicá los puntos y publicalos en la app móvil",
                actions=[
                    action_button("🔄 Actualizar", "outline", on_click=self._refrescar),
                    action_button("➕ Nuevo plato", "gold", on_click=self._crear_plato),
                ],
            ),
            *avisos,
            grilla,
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _tarjeta_plato(self, p: dict) -> ft.Container:
        if p.get("imagen"):
            imagen = ft.Image(
                src=p["imagen"], width=ANCHO_TARJETA, height=ALTO_IMAGEN, fit=ft.BoxFit.COVER,
                cache_width=ANCHO_TARJETA * 2, cache_height=ALTO_IMAGEN * 2,
            )
        else:
            imagen = ft.Container(
                width=ANCHO_TARJETA, height=ALTO_IMAGEN, bgcolor=CREAM, alignment=ft.Alignment.CENTER,
                content=ft.Text("Sin imagen todavía", size=11, color=TEXT_MUTED),
            )
        estado = status_pill("Publicado", "active") if p.get("publicado") else status_pill("Borrador", "pending")

        tarjeta = section_card(
            ft.Column([
                ft.Stack([
                    # El nombre solo aparece al pasar el mouse (tooltip
                    # nativo) — la grilla queda con solo imagen y botones.
                    ft.Container(
                        content=imagen, border_radius=12, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        tooltip=p["nombre"],
                    ),
                    ft.Container(content=estado, top=8, right=8),
                ]),
                ft.Row([
                    action_button("✏️", "outline", on_click=lambda e, pid=p["id"]: self._abrir_editor(pid)),
                    action_button("👁️", "outline", on_click=lambda e, pid=p["id"]: self._abrir_previa(pid)),
                    self._boton_texto("🗑️", RED, lambda e, pid=p["id"]: self._eliminar_plato(pid)),
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=10),
            padding=14,
        )
        # section_card() (components.py, compartido con otras pantallas) no
        # tiene parámetro "width" — se lo pone acá encima, en vez de tocar
        # ese helper para no afectar a quien más lo use.
        tarjeta.width = ANCHO_TARJETA + 28
        return tarjeta

    def _refrescar(self, e):
        """Fuerza una relectura real de Firestore — la lista se cachea en
        memoria para que abrir esta pantalla sea instantánea, así que esto
        es para cuando otro empleado publicó algo desde otra máquina."""
        try:
            self.platos = repo.cargar_platos(forzar=True)
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    def _crear_plato(self, e):
        nuevo = repo.nuevo_plato()
        try:
            self.platos = repo.guardar_plato(self.platos, nuevo)
        except Exception as ex:
            self.error_carga = str(ex)
            self._render()
            return
        self._abrir_editor(nuevo["id"])

    def _eliminar_plato(self, plato_id: str):
        try:
            self.platos = repo.eliminar_plato(self.platos, plato_id)
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    # ══════════════════════════ EDITOR ══════════════════════════
    def _abrir_editor(self, plato_id: str):
        self.plato = repo.obtener_plato(self.platos, plato_id)
        self.punto_sel = self.plato["puntos"][0]["id"] if self.plato["puntos"] else None
        self.modo_agregar = False
        self.aviso = None
        self.vista = "editor"
        self._render()

    def _vista_editor(self) -> ft.Column:
        campo_nombre = ft.TextField(
            label="Nombre del plato", value=self.plato["nombre"], width=280,
            on_change=lambda e: self._set_plato_campo("nombre", e.control.value),
        )
        publicado = self.plato.get("publicado", False)
        switch_publicar = ft.Switch(
            label="Publicado en la app", value=publicado,
            active_color=GOLD, on_change=self._alternar_publicado,
        )
        switch_asignada = ft.Switch(
            label="Asignada por nutricionista/dueño", value=self.plato.get("asignada", False),
            active_color=GOLD, on_change=self._alternar_asignada,
        )
        campo_descripcion = ft.TextField(
            label="Descripción breve (se ve en la tarjeta del catálogo)",
            value=self.plato.get("descripcion", ""), multiline=True, min_lines=2, max_lines=3,
            on_change=lambda e: self._set_plato_campo("descripcion", e.control.value),
        )
        campo_tags = ft.TextField(
            label="Etiquetas (separadas por coma, máx. 3, palabras cortas: ej. Definición, Energía)",
            value=", ".join(self.plato.get("tags", [])),
            on_change=lambda e: self._set_plato_tags(e.control.value),
        )

        acciones = ft.Row([
            action_button("🖼️ " + ("Cambiar imagen" if self.plato.get("imagen") else "Subir imagen"),
                          "outline", on_click=self._elegir_imagen),
            action_button(("➕ Agregar punto" if not self.modo_agregar else "✕ Cancelar"),
                          "gold" if not self.modo_agregar else "outline",
                          on_click=self._alternar_modo_agregar),
        ], spacing=8)

        avisos = []
        if self.aviso:
            avisos.append(ft.Container(
                content=ft.Text(self.aviso, size=12.5, weight=ft.FontWeight.W_700, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border=ft.border.all(1, GOLD_LIGHT), border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))
        if self.modo_agregar:
            avisos.append(ft.Container(
                content=ft.Text("Tocá un lugar de la imagen para colocar el nuevo punto.",
                                size=12, color=GOLD_DARK, weight=ft.FontWeight.W_700),
                bgcolor=GOLD_BG2, border_radius=10, padding=10,
            ))
        elif self.punto_sel and self.plato["puntos"]:
            avisos.append(ft.Container(
                content=ft.Text(
                    "Tocá la imagen para mover el punto seleccionado ahí. "
                    "Para mover otro punto, tocalo primero en \"Puntos del plato\".",
                    size=12, color=TEXT_MUTED, weight=ft.FontWeight.W_600),
                bgcolor=CREAM, border_radius=10, padding=10,
            ))

        lienzo_col = [self._lienzo(editable=True)]
        if self.plato.get("imagen"):
            lienzo_col += [ft.Container(height=10), self._controles_recorte()]

        cuerpo = ft.Row([
            ft.Column(lienzo_col, spacing=0),
            ft.Container(width=16),
            ft.Column([
                section_card(ft.Column([
                    ft.Text("PUNTOS DEL PLATO", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED),
                    ft.Column(self._lista_puntos(), spacing=6),
                ], spacing=10), padding=14),
                ft.Container(height=10),
                section_card(self._form_punto(), padding=14),
            ], spacing=0, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

        return ft.Column([
            page_header(f"Editando: {self.plato['nombre']}", "Editor visual de dietas",
                        actions=[action_button("← Volver al listado", "outline", on_click=self._volver_lista)]),
            *avisos,
            section_card(ft.Column([
                ft.Row([campo_nombre, ft.Container(expand=True), switch_publicar]),
                ft.Row([switch_asignada]),
                divider(),
                campo_descripcion,
                campo_tags,
                divider(),
                acciones,
            ], spacing=14), padding=16),
            cuerpo,
            ft.Row([
                action_button("💾 Guardar cambios", "dark", on_click=self._guardar),
                action_button("👁️ Vista previa", "outline", on_click=lambda e: self._abrir_previa(self.plato["id"])),
            ], spacing=8),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _lienzo(self, editable: bool) -> ft.Container:
        capas = []
        self._imagen_container = None
        if self.plato.get("imagen"):
            recorte = ft.Container(
                width=CANVAS, height=CANVAS,
                image=ft.DecorationImage(
                    src=self.plato["imagen"], fit=ft.BoxFit.COVER,
                    alignment=ft.Alignment(self.plato.get("crop_x", 0.0), self.plato.get("crop_y", 0.0)),
                ),
            )
            self._imagen_container = recorte
            capas.append(recorte)
        else:
            capas.append(ft.Container(
                width=CANVAS, height=CANVAS, bgcolor=CREAM, alignment=ft.Alignment.CENTER,
                content=ft.Text("Subí una imagen para empezar", size=13, color=TEXT_MUTED),
            ))

        if editable:
            capas.append(ft.GestureDetector(width=CANVAS, height=CANVAS, on_tap_down=self._tap_lienzo))

        for i, punto in enumerate(self.plato["puntos"]):
            capas.append(self._marcador(punto, i + 1))

        return ft.Container(
            content=ft.Stack(capas, width=CANVAS, height=CANVAS),
            width=CANVAS, height=CANVAS, border_radius=18,
            border=ft.border.all(1.5, GRAY_LIGHT), clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=WHITE,
        )

    def _marcador(self, punto: dict, numero: int) -> ft.GestureDetector:
        # Diseño mínimo a propósito: el círculo prolijo con número se ve
        # recién en la app móvil (Compose ya lo dibuja con ese detalle allá).
        activo = punto["id"] == self.punto_sel
        x_px = punto["x"] / 100 * CANVAS - RADIO_PUNTO
        y_px = punto["y"] / 100 * CANVAS - RADIO_PUNTO
        circulo = ft.Container(
            content=ft.Text(str(numero), size=11, weight=ft.FontWeight.W_900, color=DARK if activo else WHITE),
            width=RADIO_PUNTO * 2, height=RADIO_PUNTO * 2, border_radius=RADIO_PUNTO,
            bgcolor=GOLD if activo else DARK,
            alignment=ft.Alignment.CENTER,
        )
        # Solo tap: seleccionar este punto (para después moverlo con un clic
        # en el lienzo, o para arrastrarlo desde la lista de la derecha).
        return ft.GestureDetector(
            content=circulo, left=x_px, top=y_px,
            on_tap=lambda e, pid=punto["id"]: self._seleccionar_punto(pid),
        )

    def _controles_recorte(self) -> ft.Container:
        def flecha(txt, dx, dy):
            return self._boton_texto(txt, DARK, lambda e: self._mover_recorte(dx, dy))
        return section_card(ft.Column([
            ft.Text("POSICIÓN DEL RECORTE", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED),
            ft.Text("Si la imagen no entra entera, movela con las flechas.", size=11, color=TEXT_MUTED),
            ft.Row([flecha("◀", -PASO_RECORTE, 0), flecha("▲", 0, -PASO_RECORTE),
                    flecha("▼", 0, PASO_RECORTE), flecha("▶", PASO_RECORTE, 0),
                    ft.Container(width=8),
                    self._boton_texto("⟲ Centrar", GOLD_DARK, self._centrar_recorte)], spacing=6),
        ], spacing=8), padding=14)

    def _mover_recorte(self, dx: float, dy: float):
        cx = max(-1.0, min(1.0, self.plato.get("crop_x", 0.0) + dx))
        cy = max(-1.0, min(1.0, self.plato.get("crop_y", 0.0) + dy))
        self.plato["crop_x"], self.plato["crop_y"] = cx, cy
        if self._imagen_container is not None:
            self._imagen_container.image.alignment = ft.Alignment(cx, cy)
            self._imagen_container.update()

    def _centrar_recorte(self, e=None):
        self.plato["crop_x"], self.plato["crop_y"] = 0.0, 0.0
        if self._imagen_container is not None:
            self._imagen_container.image.alignment = ft.Alignment(0.0, 0.0)
            self._imagen_container.update()

    def _tap_lienzo(self, e: ft.TapEvent):
        if not self.plato.get("imagen"):
            return
        x_pct = max(0.0, min(100.0, e.local_position.x / CANVAS * 100))
        y_pct = max(0.0, min(100.0, e.local_position.y / CANVAS * 100))

        if self.modo_agregar:
            # Modo "Agregar punto": este toque crea un punto nuevo ahí.
            nuevo = repo.nuevo_punto(x_pct, y_pct)
            self.plato["puntos"].append(nuevo)
            self.punto_sel = nuevo["id"]
            self.modo_agregar = False
            self._render()
        elif self.punto_sel:
            # Sin modo agregar: este toque mueve el punto seleccionado.
            # Para mover OTRO punto, primero se lo selecciona tocándolo en
            # la lista "Puntos del plato" y recién después se toca acá.
            punto = next((p for p in self.plato["puntos"] if p["id"] == self.punto_sel), None)
            if punto:
                punto["x"], punto["y"] = x_pct, y_pct
                self._render()

    def _seleccionar_punto(self, punto_id: str):
        self.punto_sel = punto_id
        self.modo_agregar = False
        self._render()

    def _alternar_modo_agregar(self, e):
        self.modo_agregar = not self.modo_agregar
        self._render()

    def _lista_puntos(self) -> list[ft.Container]:
        if not self.plato["puntos"]:
            return [ft.Text("Todavía no hay puntos. Usá \"Agregar punto\".", size=12, color=TEXT_MUTED)]
        filas = []
        for i, p in enumerate(self.plato["puntos"]):
            activo = p["id"] == self.punto_sel
            filas.append(ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(str(i + 1), size=11, weight=ft.FontWeight.W_900,
                                        color=DARK if activo else WHITE),
                        width=22, height=22, border_radius=11,
                        bgcolor=GOLD if activo else DARK, alignment=ft.Alignment.CENTER,
                    ),
                    ft.Text(p["nombre"] or "Sin nombre", size=12.5, weight=ft.FontWeight.W_700, expand=True),
                    self._boton_texto("🗑️", RED, lambda e, pid=p["id"]: self._eliminar_punto(pid)),
                ], spacing=8),
                bgcolor=GOLD_BG if activo else WHITE,
                border=ft.border.all(1, GOLD_LIGHT if activo else GRAY_LIGHT),
                border_radius=10, padding=8,
                on_click=lambda e, pid=p["id"]: self._seleccionar_punto(pid),
                ink=True,
            ))
        return filas

    def _eliminar_punto(self, punto_id: str):
        self.plato["puntos"] = [p for p in self.plato["puntos"] if p["id"] != punto_id]
        if self.punto_sel == punto_id:
            self.punto_sel = self.plato["puntos"][0]["id"] if self.plato["puntos"] else None
        self._render()

    def _form_punto(self) -> ft.Column:
        punto = next((p for p in self.plato["puntos"] if p["id"] == self.punto_sel), None)
        if not punto:
            return ft.Column([
                ft.Text("INFORMACIÓN DEL PUNTO", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED),
                ft.Text("Seleccioná o agregá un punto para editar su información nutricional.",
                        size=12.5, color=TEXT_MUTED),
            ], spacing=10)

        return ft.Column([
            ft.Text("INFORMACIÓN DEL PUNTO", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED),
            ft.TextField(label="Nombre del ingrediente", value=punto["nombre"],
                        on_change=lambda e: self._set_punto_campo(punto, "nombre", e.control.value)),
            ft.Dropdown(
                label="Categoría", value=punto["categoria"],
                options=[ft.DropdownOption(key=c, text=c) for c in CATEGORIAS],
                on_select=lambda e: self._set_punto_campo(punto, "categoria", e.control.value),
            ),
            ft.TextField(label="Calorías (ej: 144 kcal)", value=punto["kcal"],
                        on_change=lambda e: self._set_punto_campo(punto, "kcal", e.control.value)),
            ft.TextField(label="Tags (separados por coma)", value=", ".join(punto.get("tags", [])),
                        on_change=lambda e: self._set_punto_lista(punto, "tags", e.control.value)),
            ft.TextField(label="Aporte / descripción", value=punto["aporte"], multiline=True, min_lines=2, max_lines=4,
                        on_change=lambda e: self._set_punto_campo(punto, "aporte", e.control.value)),
            ft.TextField(label="Beneficios (uno por línea)", value="\n".join(punto.get("beneficios", [])),
                        multiline=True, min_lines=3, max_lines=6,
                        on_change=lambda e: self._set_punto_beneficios(punto, e.control.value)),
        ], spacing=10)

    def _set_plato_campo(self, campo: str, valor):
        self.plato[campo] = valor

    def _set_plato_tags(self, valor: str):
        self.plato["tags"] = [t.strip() for t in valor.split(",") if t.strip()][:3]

    def _set_punto_campo(self, punto: dict, campo: str, valor):
        # Sin re-render acá a propósito: escribir en estos campos no debe
        # reconstruir toda la pantalla en cada tecla. La lista de puntos
        # (que muestra el nombre) se actualiza sola la próxima vez que algo
        # más dispare un render (elegir otro punto, agregar uno nuevo, etc.).
        punto[campo] = valor

    def _set_punto_lista(self, punto: dict, campo: str, valor: str):
        punto[campo] = [t.strip() for t in valor.split(",") if t.strip()]

    def _set_punto_beneficios(self, punto: dict, valor: str):
        punto["beneficios"] = [b.strip() for b in valor.split("\n") if b.strip()]

    def _alternar_publicado(self, e):
        self.plato["publicado"] = e.control.value
        try:
            self.platos = repo.guardar_plato(self.platos, self.plato)
            self.aviso = "Plato publicado ✓ Ya está disponible en la app móvil." if e.control.value else \
                         "Plato pasado a borrador. Ya no se muestra en la app móvil."
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
        self._render()

    def _alternar_asignada(self, e):
        self.plato["asignada"] = e.control.value
        try:
            self.platos = repo.guardar_plato(self.platos, self.plato)
            self.aviso = "Marcada como asignada ✓ Aparece en \"Asignadas por tu nutricionista\" en la app." \
                         if e.control.value else \
                         "Vuelve a aparecer en el catálogo general de la app."
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
        self._render()

    async def _elegir_imagen(self, e):
        archivos = await self.file_picker.pick_files(
            dialog_title="Elegir imagen del plato",
            file_type=ft.FilePickerFileType.IMAGE,
        )
        if not archivos:
            return
        self.aviso = "Procesando imagen…"
        self._render()
        try:
            self.plato["imagen"] = repo.procesar_imagen(archivos[0].path)
            self.aviso = "Imagen lista ✓ No olvides guardar los cambios."
        except Exception as ex:
            self.aviso = f"No se pudo procesar la imagen: {ex}"
        self._render()

    def _guardar(self, e):
        try:
            self.platos = repo.guardar_plato(self.platos, self.plato)
            self.aviso = "Cambios guardados ✓"
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
        self._render()

    def _volver_lista(self, e=None):
        self.plato = None
        self.vista = "lista"
        self._render()

    # ══════════════════════════ VISTA PREVIA ══════════════════════════
    def _abrir_previa(self, plato_id: str):
        self.plato = repo.obtener_plato(self.platos, plato_id)
        self.punto_sel = self.plato["puntos"][0]["id"] if self.plato["puntos"] else None
        self.vista = "previa"
        self._render()

    def _vista_previa(self) -> ft.Column:
        return ft.Column([
            page_header(f"Vista previa: {self.plato['nombre']}",
                        "Así se va a ver dentro de la app móvil de OlimpΩs",
                        actions=[action_button("← Volver a editar", "outline",
                                               on_click=lambda e: self._abrir_editor(self.plato["id"]))]),
            ft.Row([
                self._telefono_previa(),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _telefono_previa(self) -> ft.Container:
        punto = next((p for p in self.plato["puntos"] if p["id"] == self.punto_sel), None)
        puntos = self.plato["puntos"]
        idx = puntos.index(punto) + 1 if punto else 0

        detalle = ft.Column([ft.Text("Tocá un punto de la imagen para ver su información.",
                                     size=12.5, color=TEXT_MUTED)])
        if punto:
            detalle = ft.Column([
                ft.Row([
                    status_pill(punto["categoria"], "pending"),
                    ft.Container(expand=True),
                    ft.Text(f"{idx} / {len(puntos)}", size=11, color=TEXT_MUTED),
                ]),
                ft.Text(punto["nombre"], size=18, weight=ft.FontWeight.W_800, font_family="Poppins", color=DARK),
                ft.Text(punto["kcal"] or "—", size=20, weight=ft.FontWeight.W_900, color=GOLD_DARK),
                ft.Text(punto["aporte"] or "Sin descripción todavía.", size=12.5, color=TEXT_MUTED),
                ft.Row([status_pill(t, "active") for t in punto.get("tags", [])], spacing=6, wrap=True),
                ft.Column([
                    ft.Row([ft.Text("✓", size=11, color=GOLD_DARK, weight=ft.FontWeight.W_900),
                            ft.Text(b, size=11.5, color=TEXT_MUTED, expand=True)], spacing=6)
                    for b in punto.get("beneficios", [])
                ], spacing=4),
                ft.Row([
                    action_button("‹ Anterior", "outline", on_click=self._previa_anterior),
                    action_button("Siguiente ›", "outline", on_click=self._previa_siguiente),
                ], spacing=8),
            ], spacing=10)

        return ft.Container(
            content=ft.Column([
                self._lienzo(editable=False),
                ft.Container(height=14),
                section_card(detalle, padding=16),
            ], spacing=0),
            width=CANVAS + 40, padding=20, bgcolor=CREAM, border_radius=28,
            border=ft.border.all(8, DARK),
        )

    def _previa_anterior(self, e):
        puntos = self.plato["puntos"]
        if not puntos:
            return
        idx = next((i for i, p in enumerate(puntos) if p["id"] == self.punto_sel), 0)
        self.punto_sel = puntos[(idx - 1) % len(puntos)]["id"]
        self._render()

    def _previa_siguiente(self, e):
        puntos = self.plato["puntos"]
        if not puntos:
            return
        idx = next((i for i, p in enumerate(puntos) if p["id"] == self.punto_sel), -1)
        self.punto_sel = puntos[(idx + 1) % len(puntos)]["id"]
        self._render()

    # ══════════════════════════ util ══════════════════════════
    def _boton_texto(self, texto: str, color: str, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Text(texto, size=11.5, weight=ft.FontWeight.W_700, color=color),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.3, color)),
            border_radius=8, on_click=on_click, ink=True,
        )


def build_editor_dietas(page: ft.Page) -> ft.Column:
    return EditorDietasView(page).build()
