# OLIMPOS GYM — Tablón del club (SOLO el Dueño lo modifica)
#
# Avisos, eventos y promociones que ven todos los socios en la app móvil
# (Inicio > "Tablón del club"). El dueño crea, edita, fija arriba, publica y
# borra desde acá. Cualquier otro rol que llegara a abrir esta pantalla ve
# un aviso de acceso denegado, sin ningún control de edición — y ningún
# socio puede escribir en el tablón desde la app (ver firestore.rules).

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime

import flet as ft
from theme import *
from components import section_card, action_button, page_header, status_pill, divider
import tablon_repo as repo

ROLES_QUE_EDITAN = ("dueno",)


def _fecha(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%d/%m/%Y")


class TablonView:
    def __init__(self, page: ft.Page, role: str, autor: str):
        self.page = page
        self.autor = autor
        self.puede_editar = role in ROLES_QUE_EDITAN
        self.error_carga = None
        try:
            self.publicaciones = repo.cargar_publicaciones() if self.puede_editar else []
        except Exception as ex:
            self.publicaciones = []
            self.error_carga = str(ex)
        self.vista = "lista"     # lista | editor
        self.pub = None
        self.es_nueva = False
        self.aviso = None
        self.root = ft.Column(spacing=16, expand=True)
        self._montado = False

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls.clear()
        if not self.puede_editar:
            self.root.controls.append(self._vista_denegada())
        elif self.vista == "lista":
            self.root.controls.append(self._vista_lista())
        else:
            self.root.controls.append(self._vista_editor())
        if self._montado:
            self.root.update()

    def _vista_denegada(self) -> ft.Column:
        return ft.Column([
            page_header("📌 Tablón del club", "Avisos, eventos y promociones para los socios"),
            section_card(ft.Column([
                ft.Text("🔒", size=34),
                ft.Text("Solo el dueño puede modificar el tablón.", size=13,
                        weight=ft.FontWeight.W_700, color=DARK),
                ft.Text("Tu rol no tiene permiso para crear, editar ni borrar publicaciones.",
                        size=12, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30),
        ], spacing=16)

    # ══════════════════════════ LISTA ══════════════════════════
    def _vista_lista(self) -> ft.Column:
        avisos = []
        if self.error_carga:
            avisos.append(ft.Container(
                content=ft.Text(f"⚠️ No se pudo conectar con Firebase: {self.error_carga}",
                                size=12, color="#DC2626", weight=ft.FontWeight.W_700),
                bgcolor="#FEE2E2", border_radius=10, padding=12,
            ))

        if not self.publicaciones:
            cuerpo = section_card(ft.Column([
                ft.Text("📌", size=34),
                ft.Text("Todavía no hay publicaciones en el tablón.", size=13, weight=ft.FontWeight.W_700, color=DARK),
                ft.Text("Usá \"Nueva publicación\" para avisarle algo a todos los socios.", size=12, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)
        else:
            cuerpo = section_card(ft.Column([self._fila_publicacion(p) for p in self.publicaciones], spacing=8), padding=14)

        return ft.Column([
            page_header(
                "📌 Tablón del club", "Lo que publiques acá lo ven todos los socios en la app",
                actions=[
                    action_button("🔄 Actualizar", "outline", on_click=self._refrescar),
                    action_button("➕ Nueva publicación", "gold", on_click=self._crear),
                ],
            ),
            *avisos,
            cuerpo,
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _fila_publicacion(self, p: dict) -> ft.Container:
        estado = status_pill("Publicado", "active") if p.get("publicado") else status_pill("Borrador", "pending")
        etiquetas = [ft.Text(f"{repo.EMOJI_CATEGORIA.get(p['categoria'], '📢')} {p['categoria']}",
                             size=11.5, weight=ft.FontWeight.W_700, color=GOLD_DARK)]
        if p.get("fijado"):
            etiquetas.append(status_pill("📌 Fijado", "suspended"))
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Row(etiquetas, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(p.get("titulo") or "(sin título)", size=13.5, weight=ft.FontWeight.W_700, color=DARK),
                    ft.Text(p.get("mensaje", ""), size=11.5, color=TEXT_MUTED, max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"{p.get('autor', '')} · {_fecha(p.get('creado_ms', 0))}", size=10.5, color=TEXT_MUTED),
                ], spacing=2, expand=True),
                estado,
                action_button("✏️ Editar", "outline", on_click=lambda e, pid=p["id"]: self._abrir_editor(pid)),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

    def _refrescar(self, e):
        try:
            self.publicaciones = repo.cargar_publicaciones(forzar=True)
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    def _crear(self, e):
        self.pub = repo.nueva_publicacion(self.autor)
        self.es_nueva = True
        self.aviso = None
        self.vista = "editor"
        self._render()

    def _abrir_editor(self, pub_id: str):
        self.pub = dict(repo.obtener_publicacion(self.publicaciones, pub_id))
        self.es_nueva = False
        self.aviso = None
        self.vista = "editor"
        self._render()

    # ══════════════════════════ EDITOR ══════════════════════════
    def _vista_editor(self) -> ft.Column:
        campo_titulo = ft.TextField(
            label="Título", value=self.pub["titulo"], max_length=repo.MAX_TITULO,
            on_change=lambda e: self.pub.__setitem__("titulo", e.control.value),
        )
        campo_mensaje = ft.TextField(
            label="Mensaje", value=self.pub["mensaje"], multiline=True, min_lines=4, max_lines=8,
            max_length=repo.MAX_MENSAJE,
            on_change=lambda e: self.pub.__setitem__("mensaje", e.control.value),
        )
        selector_categoria = ft.Dropdown(
            label="Categoría", value=self.pub["categoria"], width=220,
            options=[ft.DropdownOption(key=c, text=f"{repo.EMOJI_CATEGORIA[c]} {c}") for c in repo.CATEGORIAS],
            on_select=lambda e: self.pub.__setitem__("categoria", e.control.value),
        )
        switch_fijado = ft.Switch(
            label="📌 Fijar arriba de todo", value=self.pub["fijado"], active_color=GOLD,
            on_change=lambda e: self.pub.__setitem__("fijado", e.control.value),
        )
        switch_publicado = ft.Switch(
            label="Publicado en la app", value=self.pub["publicado"], active_color=GOLD,
            on_change=lambda e: self.pub.__setitem__("publicado", e.control.value),
        )

        avisos = []
        if self.aviso:
            avisos.append(ft.Container(
                content=ft.Text(self.aviso, size=12.5, weight=ft.FontWeight.W_700, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border=ft.border.all(1, GOLD_LIGHT), border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))

        return ft.Column([
            page_header(
                "Nueva publicación" if self.es_nueva else "Editar publicación",
                "Se muestra en Inicio > Tablón del club",
                actions=[action_button("← Volver al listado", "outline", on_click=self._volver_lista)],
            ),
            *avisos,
            section_card(ft.Column([
                campo_titulo, campo_mensaje,
                divider(),
                ft.Row([selector_categoria, ft.Container(expand=True), switch_fijado, switch_publicado], spacing=16),
            ], spacing=14), padding=16),
            ft.Row([
                action_button("💾 Guardar", "gold", on_click=self._guardar),
                self._boton_texto("🗑️ Eliminar publicación", RED, self._eliminar) if not self.es_nueva else ft.Container(),
            ], spacing=8),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _guardar(self, e):
        if not (self.pub["titulo"] or "").strip() or not (self.pub["mensaje"] or "").strip():
            self.aviso = "Completá el título y el mensaje antes de guardar."
            self._render()
            return
        self.pub["titulo"] = self.pub["titulo"].strip()
        self.pub["mensaje"] = self.pub["mensaje"].strip()
        try:
            self.publicaciones = repo.guardar_publicacion(self.publicaciones, self.pub)
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
            self._render()
            return
        self.es_nueva = False
        self.aviso = (
            "Publicación guardada ✓ Ya la ven los socios en la app."
            if self.pub["publicado"] else
            "Guardada como borrador: todavía no la ve ningún socio."
        )
        self._render()

    def _eliminar(self, e):
        try:
            self.publicaciones = repo.eliminar_publicacion(self.publicaciones, self.pub["id"])
        except Exception as ex:
            self.aviso = f"No se pudo eliminar: {ex}"
            self._render()
            return
        self._volver_lista()

    def _volver_lista(self, e=None):
        self.pub = None
        self.vista = "lista"
        self._render()

    def _boton_texto(self, texto: str, color: str, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Text(texto, size=11.5, weight=ft.FontWeight.W_700, color=color),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.3, color)),
            border_radius=8, on_click=on_click, ink=True,
        )


def build_tablon(page: ft.Page, role: str, autor: str) -> ft.Column:
    return TablonView(page, role, autor).build()
