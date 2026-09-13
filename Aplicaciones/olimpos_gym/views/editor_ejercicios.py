# OLIMPOS GYM — Editor Visual de Ejercicios (Dueño / Entrenador)
#
# A diferencia del editor de dietas, acá NO se sube una foto: se toca
# directamente el cuerpo (frente/espalda, el mismo dibujo que usa el
# Bodygraph de la app) para elegir qué zona muscular trabaja el ejercicio.
# Tocar una zona gris la agrega (queda dorada); tocar una zona ya elegida
# la selecciona para editar su información en el panel de la derecha —
# mismo estilo de interacción por clics (sin arrastrar) que el resto del
# sistema. Cada zona elegida pide los mismos datos que un "punto" en
# dietas: nombre, descripción y etiquetas.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from PIL import Image
from theme import *
from components import section_card, action_button, page_header, status_pill, divider
import ejercicios_repo as repo

# Tamaño en el que se muestra cada silueta (frente/espalda) en el editor.
CANVAS_W = 210
CANVAS_H = 420
# Resolución real de los PNG en img/cuerpo/ (para el hit-testing pixel a pixel).
ASSET_W = 400
ASSET_H = 800

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
        if 0 <= x_px < mascara.width and 0 <= y_px < mascara.height:
            if mascara.getpixel((x_px, y_px))[3] > 10:
                return zona
    return None


class EditorEjerciciosView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.error_carga = None
        try:
            self.ejercicios = repo.cargar_ejercicios()
        except Exception as ex:
            self.ejercicios = []
            self.error_carga = str(ex)
        self.vista = "lista"          # lista | editor | previa
        self.ejercicio = None
        self.punto_sel = None
        self.aviso = None
        self.root = ft.Column(spacing=16, expand=True)
        self._montado = False

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

        if not self.ejercicios:
            tarjetas = [section_card(ft.Column([
                ft.Text("🏋️", size=34),
                ft.Text("Todavía no creaste ningún ejercicio.", size=13, weight=ft.FontWeight.W_700, color=DARK),
                ft.Text("Usá \"Nuevo ejercicio\" para empezar.", size=12, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)]
        else:
            tarjetas = [self._tarjeta_ejercicio(e) for e in self.ejercicios]

        return ft.Column([
            page_header(
                "🏋️ Editor Visual de Ejercicios",
                "Elegí las zonas musculares trabajadas y publicalas en la Galería",
                actions=[action_button("➕ Nuevo ejercicio", "gold", on_click=self._crear_ejercicio)],
            ),
            *avisos,
            ft.Row(tarjetas, wrap=True, spacing=16, run_spacing=16),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _tarjeta_ejercicio(self, e: dict) -> ft.Container:
        estado = status_pill("Publicado", "active") if e.get("publicado") else status_pill("Borrador", "pending")
        zonas_chips = [
            status_pill(f"{repo.ZONAS_MUSCULARES[p['zona']]['emoji']} {repo.ZONAS_MUSCULARES[p['zona']]['etiqueta']}", "pending")
            for p in e.get("puntos", [])
        ]

        return section_card(
            ft.Column([
                ft.Row([
                    ft.Text(e["nombre"], size=14, weight=ft.FontWeight.W_800, font_family="Poppins", expand=True),
                    estado,
                ]),
                ft.Row(zonas_chips, spacing=6, run_spacing=6, wrap=True) if zonas_chips else
                    ft.Text("Todavía sin zonas musculares", size=11.5, color=TEXT_MUTED),
                ft.Row([
                    action_button("✏️ Editar", "outline", on_click=lambda ev, eid=e["id"]: self._abrir_editor(eid)),
                    action_button("👁️ Vista previa", "outline", on_click=lambda ev, eid=e["id"]: self._abrir_previa(eid)),
                    self._boton_texto("🗑️ Eliminar", RED, lambda ev, eid=e["id"]: self._eliminar_ejercicio(eid)),
                ], spacing=6),
            ], spacing=10, width=280),
            padding=14,
        )

    def _crear_ejercicio(self, e):
        nuevo = repo.nuevo_ejercicio()
        try:
            self.ejercicios = repo.guardar_ejercicio(self.ejercicios, nuevo)
        except Exception as ex:
            self.error_carga = str(ex)
            self._render()
            return
        self._abrir_editor(nuevo["id"])

    def _eliminar_ejercicio(self, ejercicio_id: str):
        try:
            self.ejercicios = repo.eliminar_ejercicio(self.ejercicios, ejercicio_id)
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    # ══════════════════════════ EDITOR ══════════════════════════
    def _abrir_editor(self, ejercicio_id: str):
        self.ejercicio = repo.obtener_ejercicio(self.ejercicios, ejercicio_id)
        self.punto_sel = self.ejercicio["puntos"][0]["id"] if self.ejercicio["puntos"] else None
        self.aviso = None
        self.vista = "editor"
        self._render()

    def _vista_editor(self) -> ft.Column:
        campo_nombre = ft.TextField(
            label="Nombre del ejercicio", value=self.ejercicio["nombre"], width=280,
            on_change=lambda e: self._set_ejercicio_campo("nombre", e.control.value),
        )
        publicado = self.ejercicio.get("publicado", False)
        switch_publicar = ft.Switch(
            label="Publicado en la Galería", value=publicado,
            active_color=GOLD, on_change=self._alternar_publicado,
        )
        campo_descripcion = ft.TextField(
            label="Descripción del ejercicio (técnica, para qué sirve)",
            value=self.ejercicio.get("descripcion", ""), multiline=True, min_lines=2, max_lines=4,
            on_change=lambda e: self._set_ejercicio_campo("descripcion", e.control.value),
        )
        campo_tags = ft.TextField(
            label="Etiquetas (separadas por coma, máx. 3, palabras cortas: ej. Empuje, Pecho)",
            value=", ".join(self.ejercicio.get("tags", [])),
            on_change=lambda e: self._set_ejercicio_tags(e.control.value),
        )

        avisos = []
        if self.aviso:
            avisos.append(ft.Container(
                content=ft.Text(self.aviso, size=12.5, weight=ft.FontWeight.W_700, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border=ft.border.all(1, GOLD_LIGHT), border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))
        avisos.append(ft.Container(
            content=ft.Text(
                "Tocá una zona gris para agregarla como músculo trabajado. Tocá una zona dorada para editar su información.",
                size=12, color=TEXT_MUTED, weight=ft.FontWeight.W_600),
            bgcolor=CREAM, border_radius=10, padding=10,
        ))

        cuerpos = ft.Row([
            self._columna_cuerpo("frente", "Frente"),
            self._columna_cuerpo("espalda", "Espalda"),
        ], spacing=20, alignment=ft.MainAxisAlignment.CENTER)

        cuerpo = ft.Row([
            ft.Column([cuerpos], spacing=0),
            ft.Container(width=16),
            ft.Column([
                section_card(ft.Column([
                    ft.Text("ZONAS TRABAJADAS", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED),
                    ft.Column(self._lista_puntos(), spacing=6),
                ], spacing=10), padding=14),
                ft.Container(height=10),
                section_card(self._form_punto(), padding=14),
            ], spacing=0, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

        return ft.Column([
            page_header(f"Editando: {self.ejercicio['nombre']}", "Editor visual de ejercicios",
                        actions=[action_button("← Volver al listado", "outline", on_click=self._volver_lista)]),
            *avisos,
            section_card(ft.Column([
                ft.Row([campo_nombre, ft.Container(expand=True), switch_publicar]),
                divider(),
                campo_descripcion,
                campo_tags,
            ], spacing=14), padding=16),
            cuerpo,
            ft.Row([
                action_button("💾 Guardar cambios", "dark", on_click=self._guardar),
                action_button("👁️ Vista previa", "outline", on_click=lambda e: self._abrir_previa(self.ejercicio["id"])),
            ], spacing=8),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _columna_cuerpo(self, vista: str, etiqueta: str) -> ft.Column:
        return ft.Column([
            self._lienzo_cuerpo(vista),
            ft.Text(etiqueta.upper(), size=10.5, weight=ft.FontWeight.W_800, color=TEXT_MUTED),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

    def _lienzo_cuerpo(self, vista: str) -> ft.Container:
        seleccionadas = {p["zona"] for p in self.ejercicio["puntos"]}
        capas = [ft.Image(src=f"cuerpo/base_{vista}.png", width=CANVAS_W, height=CANVAS_H, fit=ft.BoxFit.FILL)]
        for zona in repo.ZONAS_POR_VISTA[vista]:
            if zona in seleccionadas:
                capas.append(ft.Image(src=f"cuerpo/zona_{vista}_{zona}.png", width=CANVAS_W, height=CANVAS_H, fit=ft.BoxFit.FILL))
        capas.append(ft.GestureDetector(
            width=CANVAS_W, height=CANVAS_H,
            on_tap_down=lambda e, v=vista: self._tap_cuerpo(v, e),
        ))
        return ft.Container(
            content=ft.Stack(capas, width=CANVAS_W, height=CANVAS_H),
            width=CANVAS_W, height=CANVAS_H, border_radius=14,
            border=ft.border.all(1.5, GRAY_LIGHT), clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=WHITE,
        )

    def _tap_cuerpo(self, vista: str, e: ft.TapEvent):
        x_px = int(e.local_position.x / CANVAS_W * ASSET_W)
        y_px = int(e.local_position.y / CANVAS_H * ASSET_H)
        zona = _zona_en_punto(vista, x_px, y_px)
        if not zona:
            return
        existente = next((p for p in self.ejercicio["puntos"] if p["zona"] == zona), None)
        if existente:
            self.punto_sel = existente["id"]
        else:
            nuevo = repo.nuevo_punto(zona)
            self.ejercicio["puntos"].append(nuevo)
            self.punto_sel = nuevo["id"]
        self._render()

    def _lista_puntos(self) -> list[ft.Container]:
        if not self.ejercicio["puntos"]:
            return [ft.Text("Todavía no hay zonas elegidas. Tocá el cuerpo para agregar una.", size=12, color=TEXT_MUTED)]
        filas = []
        for p in self.ejercicio["puntos"]:
            activo = p["id"] == self.punto_sel
            zona_info = repo.ZONAS_MUSCULARES[p["zona"]]
            filas.append(ft.Container(
                content=ft.Row([
                    ft.Text(zona_info["emoji"], size=15),
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
        self.ejercicio["puntos"] = [p for p in self.ejercicio["puntos"] if p["id"] != punto_id]
        if self.punto_sel == punto_id:
            self.punto_sel = self.ejercicio["puntos"][0]["id"] if self.ejercicio["puntos"] else None
        self._render()

    def _seleccionar_punto(self, punto_id: str):
        self.punto_sel = punto_id
        self._render()

    def _form_punto(self) -> ft.Column:
        punto = next((p for p in self.ejercicio["puntos"] if p["id"] == self.punto_sel), None)
        if not punto:
            return ft.Column([
                ft.Text("INFORMACIÓN DE LA ZONA", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED),
                ft.Text("Tocá una zona muscular en el cuerpo para cargar su información.",
                        size=12.5, color=TEXT_MUTED),
            ], spacing=10)

        zona_info = repo.ZONAS_MUSCULARES[punto["zona"]]
        return ft.Column([
            ft.Row([
                ft.Text("INFORMACIÓN DE LA ZONA", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=True),
                status_pill(f"{zona_info['emoji']} {zona_info['etiqueta']}", "active"),
            ]),
            ft.TextField(label="Nombre del músculo", value=punto["nombre"],
                        on_change=lambda e: self._set_punto_campo(punto, "nombre", e.control.value)),
            ft.TextField(label="Descripción (cómo se fortalece con este ejercicio)", value=punto["descripcion"],
                        multiline=True, min_lines=2, max_lines=4,
                        on_change=lambda e: self._set_punto_campo(punto, "descripcion", e.control.value)),
            ft.TextField(label="Etiquetas (separadas por coma, máx. 3)", value=", ".join(punto.get("tags", [])),
                        on_change=lambda e: self._set_punto_tags(punto, e.control.value)),
        ], spacing=10)

    def _set_ejercicio_campo(self, campo: str, valor):
        self.ejercicio[campo] = valor

    def _set_ejercicio_tags(self, valor: str):
        self.ejercicio["tags"] = [t.strip() for t in valor.split(",") if t.strip()][:3]

    def _set_punto_campo(self, punto: dict, campo: str, valor):
        # Sin re-render acá a propósito: escribir en estos campos no debe
        # reconstruir toda la pantalla en cada tecla.
        punto[campo] = valor

    def _set_punto_tags(self, punto: dict, valor: str):
        punto["tags"] = [t.strip() for t in valor.split(",") if t.strip()][:3]

    def _alternar_publicado(self, e):
        self.ejercicio["publicado"] = e.control.value
        try:
            self.ejercicios = repo.guardar_ejercicio(self.ejercicios, self.ejercicio)
            self.aviso = "Ejercicio publicado ✓ Ya está disponible en la Galería." if e.control.value else \
                         "Ejercicio pasado a borrador. Ya no se muestra en la Galería."
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
        self._render()

    def _guardar(self, e):
        try:
            self.ejercicios = repo.guardar_ejercicio(self.ejercicios, self.ejercicio)
            self.aviso = "Cambios guardados ✓"
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
        self._render()

    def _volver_lista(self, e=None):
        self.ejercicio = None
        self.vista = "lista"
        self._render()

    # ══════════════════════════ VISTA PREVIA ══════════════════════════
    def _abrir_previa(self, ejercicio_id: str):
        self.ejercicio = repo.obtener_ejercicio(self.ejercicios, ejercicio_id)
        self.punto_sel = self.ejercicio["puntos"][0]["id"] if self.ejercicio["puntos"] else None
        self.vista = "previa"
        self._render()

    def _vista_previa(self) -> ft.Column:
        return ft.Column([
            page_header(f"Vista previa: {self.ejercicio['nombre']}",
                        "Así se va a ver dentro de la app móvil de OlimpΩs",
                        actions=[action_button("← Volver a editar", "outline",
                                               on_click=lambda e: self._abrir_editor(self.ejercicio["id"]))]),
            ft.Row([
                self._telefono_previa(),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _telefono_previa(self) -> ft.Container:
        punto = next((p for p in self.ejercicio["puntos"] if p["id"] == self.punto_sel), None)
        puntos = self.ejercicio["puntos"]
        idx = puntos.index(punto) + 1 if punto else 0

        detalle = ft.Column([ft.Text("Elegí una zona para ver su información.",
                                     size=12.5, color=TEXT_MUTED)])
        if punto:
            zona_info = repo.ZONAS_MUSCULARES[punto["zona"]]
            detalle = ft.Column([
                ft.Row([
                    status_pill(f"{zona_info['emoji']} {zona_info['etiqueta']}", "pending"),
                    ft.Container(expand=True),
                    ft.Text(f"{idx} / {len(puntos)}", size=11, color=TEXT_MUTED),
                ]),
                ft.Text(punto["nombre"], size=18, weight=ft.FontWeight.W_800, font_family="Poppins", color=DARK),
                ft.Text(punto["descripcion"] or "Sin descripción todavía.", size=12.5, color=TEXT_MUTED),
                ft.Row([status_pill(t, "active") for t in punto.get("tags", [])], spacing=6, wrap=True),
                ft.Row([
                    action_button("‹ Anterior", "outline", on_click=self._previa_anterior),
                    action_button("Siguiente ›", "outline", on_click=self._previa_siguiente),
                ], spacing=8),
            ], spacing=10)

        cuerpos = ft.Row([
            self._columna_cuerpo_previa("frente"),
            self._columna_cuerpo_previa("espalda"),
        ], spacing=14, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                cuerpos,
                ft.Container(height=14),
                section_card(ft.Column([
                    ft.Text(self.ejercicio.get("descripcion") or "Sin descripción todavía.",
                            size=12.5, color=DARK),
                    ft.Row([status_pill(t, "pending") for t in self.ejercicio.get("tags", [])], spacing=6, wrap=True),
                ], spacing=8), padding=14),
                ft.Container(height=14),
                section_card(detalle, padding=16),
            ], spacing=0),
            width=CANVAS_W * 2 + 60, padding=20, bgcolor=CREAM, border_radius=28,
            border=ft.border.all(8, DARK),
        )

    def _columna_cuerpo_previa(self, vista: str) -> ft.Stack:
        seleccionadas = {p["zona"] for p in self.ejercicio["puntos"]}
        capas = [ft.Image(src=f"cuerpo/base_{vista}.png", width=CANVAS_W, height=CANVAS_H, fit=ft.BoxFit.FILL)]
        for zona in repo.ZONAS_POR_VISTA[vista]:
            if zona in seleccionadas:
                capas.append(ft.Image(src=f"cuerpo/zona_{vista}_{zona}.png", width=CANVAS_W, height=CANVAS_H, fit=ft.BoxFit.FILL))
        return ft.Stack(capas, width=CANVAS_W, height=CANVAS_H)

    def _previa_anterior(self, e):
        puntos = self.ejercicio["puntos"]
        if not puntos:
            return
        idx = next((i for i, p in enumerate(puntos) if p["id"] == self.punto_sel), 0)
        self.punto_sel = puntos[(idx - 1) % len(puntos)]["id"]
        self._render()

    def _previa_siguiente(self, e):
        puntos = self.ejercicio["puntos"]
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


def build_editor_ejercicios(page: ft.Page) -> ft.Column:
    return EditorEjerciciosView(page).build()
