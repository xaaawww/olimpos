# OLIMPOS GYM — Asignación de Membresías (Dueño / Administrador / Recepcionista)
#
# Antes cualquier socio se auto-asignaba un plan tocando un botón en la
# app móvil, sin que quedara registrado acá ni una fecha de inicio real.
# Acá se elige un socio y se le asigna su plan real (Bronce/Oro/Platino)
# con la fecha en la que arrancó — la app móvil ya no deja auto-elegirse
# un plan, solo "pedirlo".

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import section_card, action_button, page_header, status_pill, avatar
import auth_repo
import membresias_repo as repo


class EditorMembresiasView:
    def __init__(self, page: ft.Page, nombre_asignador: str):
        self.page = page
        self.nombre_asignador = nombre_asignador
        self.error_carga = None
        try:
            self.socios = auth_repo.listar_accesos_socios()
            self.membresias = repo.cargar_membresias()
        except Exception as ex:
            self.socios, self.membresias = [], {}
            self.error_carga = str(ex)
        self.vista = "lista"     # lista | editor
        self.socio_id = None
        self.plan_sel = None
        self.fecha_texto = None
        self.aviso = None
        self.root = ft.Column(spacing=16, expand=True)
        self._montado = False

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls.clear()
        self.root.controls.append(self._vista_lista() if self.vista == "lista" else self._vista_editor())
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

        if not self.socios:
            filas = [section_card(ft.Column([
                ft.Text("💳", size=34),
                ft.Text("Todavía no hay socios con acceso a la app.", size=13, weight=ft.FontWeight.W_700, color=DARK),
                ft.Text("Dales de alta desde \"Socios\" para poder asignarles una membresía.", size=12, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)]
        else:
            ordenados = sorted(self.socios, key=lambda s: s.get("nombre", ""))
            filas = [self._fila_socio(s) for s in ordenados]

        return ft.Column([
            page_header(
                "💳 Asignación de Membresías", "Elegí un socio para asignarle un plan real",
                actions=[action_button("🔄 Actualizar", "outline", on_click=self._refrescar)],
            ),
            *avisos,
            section_card(ft.Column(filas, spacing=8), padding=14),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _fila_socio(self, socio: dict) -> ft.Container:
        uid = socio["uid"]
        m = self.membresias.get(uid)
        nombre = socio.get("nombre", "?")
        iniciales = "".join(p[0] for p in nombre.split()[:2]).upper() or "?"
        estado = (
            status_pill(f"✓ Plan {m['plan']} · desde {repo.fecha_legible(m['fecha_inicio_ms'])}", "active")
            if m else status_pill("Sin membresía asignada", "pending")
        )

        return ft.Container(
            content=ft.Row([
                avatar(iniciales),
                ft.Column([
                    ft.Text(nombre, size=13.5, weight=ft.FontWeight.W_700, color=DARK),
                    ft.Text(socio.get("email", ""), size=11.5, color=TEXT_MUTED),
                ], spacing=1, expand=True),
                estado,
                action_button("✏️ Editar" if m else "➕ Asignar", "outline",
                              on_click=lambda e, u=uid: self._abrir_editor(u)),
            ], spacing=12, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

    def _refrescar(self, e):
        try:
            self.socios = auth_repo.listar_accesos_socios(forzar=True)
            self.membresias = repo.cargar_membresias(forzar=True)
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    # ══════════════════════════ EDITOR ══════════════════════════
    def _abrir_editor(self, socio_id: str):
        self.socio_id = socio_id
        existente = repo.obtener_membresia(socio_id)
        self.plan_sel = existente["plan"] if existente else repo.PLANES[0]
        self.fecha_texto = repo.fecha_legible(existente["fecha_inicio_ms"] if existente else repo.nueva_fecha_hoy_ms())
        self.aviso = None
        self.vista = "editor"
        self._render()

    def _nombre_socio(self, socio_id: str) -> str:
        return next((s["nombre"] for s in self.socios if s["uid"] == socio_id), "?")

    def _vista_editor(self) -> ft.Column:
        dropdown_plan = ft.Dropdown(
            label="Plan", value=self.plan_sel, width=200,
            options=[ft.DropdownOption(key=p, text=p) for p in repo.PLANES],
            on_select=lambda e: setattr(self, "plan_sel", e.control.value),
        )
        campo_fecha = ft.TextField(
            label="Fecha de inicio (dd/mm/aaaa)", value=self.fecha_texto, width=200,
            on_change=lambda e: setattr(self, "fecha_texto", e.control.value),
        )

        avisos = []
        if self.aviso:
            avisos.append(ft.Container(
                content=ft.Text(self.aviso, size=12.5, weight=ft.FontWeight.W_700, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border=ft.border.all(1, GOLD_LIGHT), border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))

        existente = repo.obtener_membresia(self.socio_id)
        return ft.Column([
            page_header(
                f"Membresía de {self._nombre_socio(self.socio_id)}", "Plan real y fecha de inicio",
                actions=[action_button("← Volver al listado", "outline", on_click=self._volver_lista)],
            ),
            *avisos,
            section_card(ft.Row([dropdown_plan, campo_fecha], spacing=14), padding=16),
            ft.Row([
                action_button("💾 Guardar", "gold", on_click=self._guardar),
                self._boton_texto("🗑️ Quitar membresía", RED, self._quitar) if existente else ft.Container(),
            ], spacing=8),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _guardar(self, e):
        fecha_ms = repo.parsear_fecha(self.fecha_texto or "")
        if fecha_ms is None:
            self.aviso = "Fecha inválida — usá el formato dd/mm/aaaa."
            self._render()
            return
        try:
            self.membresias = repo.asignar_membresia(self.socio_id, self.plan_sel, fecha_ms, self.nombre_asignador)
            self.aviso = "Membresía guardada ✓ Ya está disponible en la app del socio."
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
        self._render()

    def _quitar(self, e):
        try:
            self.membresias = repo.quitar_membresia(self.socio_id)
        except Exception as ex:
            self.aviso = f"No se pudo quitar: {ex}"
            self._render()
            return
        self._volver_lista()

    def _volver_lista(self, e=None):
        self.socio_id = None
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


def build_editor_membresias(page: ft.Page, nombre_asignador: str) -> ft.Column:
    return EditorMembresiasView(page, nombre_asignador).build()
