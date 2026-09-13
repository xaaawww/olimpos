# OLIMPOS GYM — Asignación de Rutinas (Dueño / Entrenador)
#
# Antes de esto, la app móvil mostraba la misma rutina fija ("Empuje
# pesado") a cualquier socio que abriera "Entrenar", atribuida siempre a
# un entrenador de ejemplo — nadie la asignaba de verdad. Acá se elige un
# socio de la lista y se le arma su rutina real: nombre, y una lista de
# ejercicios con series objetivo, peso de partida y si es un ejercicio de
# peso corporal (dominadas, fondos) — mismos campos que EjercicioRutina en
# la app móvil, sin duplicar la lógica de cálculo, solo los datos.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import section_card, action_button, page_header, status_pill, divider, avatar
import auth_repo
import rutinas_repo as repo


class EditorRutinasView:
    def __init__(self, page: ft.Page, nombre_entrenador: str):
        self.page = page
        self.nombre_entrenador = nombre_entrenador
        self.error_carga = None
        try:
            self.socios = auth_repo.listar_accesos_socios()
            self.rutinas = repo.cargar_rutinas()
        except Exception as ex:
            self.socios = []
            self.rutinas = {}
            self.error_carga = str(ex)
        self.vista = "lista"     # lista | editor
        self.socio_id = None
        self.rutina = None
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
        else:
            self.root.controls.append(self._vista_editor())
        if self._montado:
            self.root.update()

    # ══════════════════════════ LISTA DE SOCIOS ══════════════════════════
    def _vista_lista(self) -> ft.Column:
        avisos = []
        if self.error_carga:
            avisos.append(ft.Container(
                content=ft.Text(f"⚠️ No se pudo conectar con Firebase: {self.error_carga}",
                                size=12, color="#DC2626", weight=ft.FontWeight.W_700),
                bgcolor="#FEE2E2", border_radius=10, padding=12,
            ))

        if not self.socios:
            filas = [section_card(ft.Column([
                ft.Text("📋", size=34),
                ft.Text("Todavía no hay socios con acceso a la app.", size=13, weight=ft.FontWeight.W_700, color=DARK),
                ft.Text("Dales de alta desde \"Socios\" para poder asignarles una rutina.", size=12, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)]
        else:
            ordenados = sorted(self.socios, key=lambda s: s.get("nombre", ""))
            filas = [self._fila_socio(s) for s in ordenados]

        return ft.Column([
            page_header(
                "📋 Asignación de Rutinas", "Elegí un socio para armar o editar su rutina de Entrenar",
                actions=[action_button("🔄 Actualizar", "outline", on_click=self._refrescar)],
            ),
            *avisos,
            section_card(ft.Column(filas, spacing=8), padding=14),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _fila_socio(self, socio: dict) -> ft.Container:
        uid = socio["uid"]
        rutina = self.rutinas.get(uid)
        nombre = socio.get("nombre", "?")
        iniciales = "".join(p[0] for p in nombre.split()[:2]).upper() or "?"
        estado = status_pill(f"✓ {rutina['nombre']}", "active") if rutina else status_pill("Sin rutina asignada", "pending")

        return ft.Container(
            content=ft.Row([
                avatar(iniciales),
                ft.Column([
                    ft.Text(nombre, size=13.5, weight=ft.FontWeight.W_700, color=DARK),
                    ft.Text(socio.get("email", ""), size=11.5, color=TEXT_MUTED),
                ], spacing=1, expand=True),
                estado,
                action_button("✏️ Editar rutina" if rutina else "➕ Asignar rutina", "outline",
                              on_click=lambda e, u=uid: self._abrir_editor(u)),
            ], spacing=12, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

    def _refrescar(self, e):
        try:
            self.socios = auth_repo.listar_accesos_socios(forzar=True)
            self.rutinas = repo.cargar_rutinas(forzar=True)
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    # ══════════════════════════ EDITOR ══════════════════════════
    def _abrir_editor(self, socio_id: str):
        self.socio_id = socio_id
        self.rutina = repo.obtener_rutina(socio_id) or repo.nueva_rutina(socio_id, self.nombre_entrenador)
        # Copia superficial de la lista de ejercicios para poder editar sin
        # tocar la caché hasta que se guarde de verdad.
        self.rutina = {**self.rutina, "ejercicios": [dict(ej) for ej in self.rutina["ejercicios"]]}
        self.aviso = None
        self.vista = "editor"
        self._render()

    def _nombre_socio(self, socio_id: str) -> str:
        return next((s["nombre"] for s in self.socios if s["uid"] == socio_id), "?")

    def _vista_editor(self) -> ft.Column:
        campo_nombre = ft.TextField(
            label="Nombre de la rutina", value=self.rutina["nombre"], width=320,
            on_change=lambda e: self._set_rutina_campo("nombre", e.control.value),
        )

        avisos = []
        if self.aviso:
            avisos.append(ft.Container(
                content=ft.Text(self.aviso, size=12.5, weight=ft.FontWeight.W_700, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border=ft.border.all(1, GOLD_LIGHT), border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))

        filas_ejercicios = [self._fila_ejercicio(i, ej) for i, ej in enumerate(self.rutina["ejercicios"])]
        if not filas_ejercicios:
            filas_ejercicios = [ft.Text(
                "Todavía no agregaste ningún ejercicio. Usá \"+ Agregar ejercicio\" para empezar.",
                size=12.5, color=TEXT_MUTED,
            )]

        return ft.Column([
            page_header(
                f"Rutina de {self._nombre_socio(self.socio_id)}", "Armá los ejercicios, series y peso de partida",
                actions=[action_button("← Volver al listado", "outline", on_click=self._volver_lista)],
            ),
            *avisos,
            section_card(campo_nombre, padding=16),
            section_card(ft.Column([
                ft.Row([
                    ft.Text("EJERCICIOS", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=True),
                    action_button("+ Agregar ejercicio", "outline", on_click=self._agregar_ejercicio),
                ]),
                divider(),
                ft.Column(filas_ejercicios, spacing=10),
            ], spacing=10), padding=16),
            ft.Row([
                action_button("💾 Guardar rutina", "gold", on_click=self._guardar),
                self._boton_texto("🗑️ Eliminar rutina asignada", RED, self._eliminar) if repo.obtener_rutina(self.socio_id) else ft.Container(),
            ], spacing=8),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _fila_ejercicio(self, i: int, ejercicio: dict) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.TextField(
                    label="Ejercicio", value=ejercicio["nombre"], expand=True, dense=True,
                    on_change=lambda e, ej=ejercicio: self._set_ejercicio_campo(ej, "nombre", e.control.value),
                ),
                ft.TextField(
                    label="Series", value=str(ejercicio["series_objetivo"]), width=80, dense=True,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=lambda e, ej=ejercicio: self._set_ejercicio_entero(ej, "series_objetivo", e.control.value),
                ),
                ft.TextField(
                    label="Peso de partida (kg)", value=str(ejercicio["peso_base_kg"]), width=140, dense=True,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=lambda e, ej=ejercicio: self._set_ejercicio_flotante(ej, "peso_base_kg", e.control.value),
                ),
                ft.Column([
                    ft.Text("Peso corporal", size=10, color=TEXT_MUTED),
                    ft.Switch(
                        value=ejercicio["es_peso_corporal"], active_color=GOLD,
                        on_change=lambda e, ej=ejercicio: self._set_ejercicio_campo(ej, "es_peso_corporal", e.control.value),
                    ),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                self._boton_texto("🗑️", RED, lambda e, idx=i: self._eliminar_ejercicio(idx)),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CREAM, border=ft.border.all(1, GRAY_LIGHT), border_radius=10, padding=10,
        )

    def _agregar_ejercicio(self, e):
        self.rutina["ejercicios"].append(repo.nuevo_ejercicio_rutina())
        self._render()

    def _eliminar_ejercicio(self, idx: int):
        del self.rutina["ejercicios"][idx]
        self._render()

    def _set_rutina_campo(self, campo: str, valor):
        self.rutina[campo] = valor

    def _set_ejercicio_campo(self, ejercicio: dict, campo: str, valor):
        # Sin re-render acá a propósito: escribir el nombre no debe
        # reconstruir toda la pantalla en cada tecla (mismo criterio que el
        # editor de ejercicios).
        ejercicio[campo] = valor

    def _set_ejercicio_entero(self, ejercicio: dict, campo: str, valor: str):
        try:
            ejercicio[campo] = max(1, int(valor))
        except ValueError:
            pass

    def _set_ejercicio_flotante(self, ejercicio: dict, campo: str, valor: str):
        try:
            ejercicio[campo] = max(0.0, float(valor.replace(",", ".")))
        except ValueError:
            pass

    def _guardar(self, e):
        ejercicios_validos = [ej for ej in self.rutina["ejercicios"] if ej["nombre"].strip()]
        if not ejercicios_validos:
            self.aviso = "Agregá al menos un ejercicio con nombre antes de guardar."
            self._render()
            return
        self.rutina["ejercicios"] = ejercicios_validos
        try:
            self.rutinas = repo.guardar_rutina(self.rutina)
            self.aviso = "Rutina guardada ✓ Ya está disponible en la app del socio."
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
        self._render()

    def _eliminar(self, e):
        try:
            self.rutinas = repo.eliminar_rutina(self.socio_id)
        except Exception as ex:
            self.aviso = f"No se pudo eliminar: {ex}"
            self._render()
            return
        self._volver_lista()

    def _volver_lista(self, e=None):
        self.socio_id = None
        self.rutina = None
        self.vista = "lista"
        self._render()

    # ══════════════════════════ util ══════════════════════════
    def _boton_texto(self, texto: str, color: str, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Text(texto, size=11.5, weight=ft.FontWeight.W_700, color=color),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.3, color)),
            border_radius=8, on_click=on_click, ink=True,
        )


def build_editor_rutinas(page: ft.Page, nombre_entrenador: str) -> ft.Column:
    return EditorRutinasView(page, nombre_entrenador).build()
