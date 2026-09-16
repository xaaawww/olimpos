# OLIMPOS GYM — Argos, el asistente de IA de texto
#
# Chat simple: pregunta -> respuesta, sin ninguna otra acción (ver
# argos_repo.py). El historial de esta pantalla vive solo en memoria — se
# pierde al salir, a propósito (no se guarda ninguna conversación).
#
# El dueño/administrador ve además, en esta misma pantalla, un cuadro para
# editar la "base de conocimiento" (horarios reales, precios, políticas)
# que Argos usa como referencia — tanto acá como en la app móvil de los
# socios, que lee el mismo documento de Firestore.

import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import section_card, action_button, page_header, divider
import argos_repo

ROLES_QUE_EDITAN_BASE = ("dueno", "admin")

_REGEX_NEGRITA = re.compile(r"\*\*(.+?)\*\*")


def _spans_con_negrita(texto: str, color: str) -> list[ft.TextSpan]:
    """Convierte "**palabra**" en negrita real — Flet no interpreta markdown
    solo, y Argos (el modelo de lenguaje) escribe así seguido."""
    spans: list[ft.TextSpan] = []
    ultimo = 0
    for m in _REGEX_NEGRITA.finditer(texto):
        if m.start() > ultimo:
            spans.append(ft.TextSpan(texto[ultimo:m.start()]))
        spans.append(ft.TextSpan(m.group(1), style=ft.TextStyle(weight=ft.FontWeight.W_900, color=color)))
        ultimo = m.end()
    if ultimo < len(texto) or not spans:
        spans.append(ft.TextSpan(texto[ultimo:]))
    return spans


class ArgosView:
    def __init__(self, page: ft.Page, role: str):
        self.page = page
        self.role = role
        self.puede_editar_base = role in ROLES_QUE_EDITAN_BASE
        self.mensajes: list[dict] = []
        self.enviando = False
        self.error_envio = None

        self.error_cupo = None
        try:
            self.hoy = argos_repo.usos_hoy()
            self.restantes = argos_repo.usos_restantes_hoy()
        except Exception as ex:
            self.hoy, self.restantes = 0, 0
            self.error_cupo = str(ex)

        self.base_conocimiento_valor = ""
        self.error_base = None
        if self.puede_editar_base:
            try:
                self.base_conocimiento_valor = argos_repo.cargar_base_conocimiento()
            except Exception as ex:
                self.error_base = str(ex)

        self.aviso_base = None
        self.root = ft.Column(spacing=16, expand=True)
        self._montado = False

        self.campo_mensaje = ft.TextField(
            hint_text="Preguntale algo a Argos sobre OlimpΩs...",
            expand=True, multiline=True, min_lines=1, max_lines=4,
            border_radius=12, filled=True, fill_color=CREAM,
            border=ft.InputBorder.NONE, content_padding=12,
            on_submit=self._enviar,
        )
        self.lista_mensajes = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls.clear()
        self.root.controls.append(
            page_header("🐕 Argos", "Tu asistente de IA en OlimpΩs — preguntas sobre el gimnasio, nada más")
        )

        if self.error_cupo:
            self.root.controls.append(ft.Container(
                content=ft.Text(f"⚠️ No se pudo consultar el cupo diario: {self.error_cupo}",
                                size=12, color=RED, weight=ft.FontWeight.W_700),
                bgcolor="#FEE2E2", border_radius=10, padding=12,
            ))
        else:
            self.root.controls.append(ft.Container(
                content=ft.Text(
                    f"💬 Mensajes usados hoy: {self.hoy} de {argos_repo.MAXIMO_DIARIO} — quedan {self.restantes}.",
                    size=11.5, color=TEXT_MUTED if self.restantes > 0 else RED, weight=ft.FontWeight.W_700,
                ),
                bgcolor=CREAM, border_radius=10, padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))

        if self.puede_editar_base:
            self.root.controls.append(self._panel_base_conocimiento())

        self.root.controls.append(self._panel_chat())

        if self._montado:
            self.root.update()

    # ══════════════ Base de conocimiento (dueño/admin) ══════════════
    def _panel_base_conocimiento(self) -> ft.Container:
        campo = ft.TextField(
            label="Base de conocimiento de Argos (horarios, precios, políticas reales)",
            value=self.base_conocimiento_valor, multiline=True, min_lines=3, max_lines=8,
            on_change=lambda e: setattr(self, "base_conocimiento_valor", e.control.value),
        )
        avisos = []
        if self.error_base:
            avisos.append(ft.Text(f"⚠️ {self.error_base}", size=11.5, color=RED, weight=ft.FontWeight.W_700))
        if self.aviso_base:
            avisos.append(ft.Text(self.aviso_base, size=11.5, color=GOLD_DARK, weight=ft.FontWeight.W_700))

        return section_card(ft.Column([
            ft.Text("📚 Base de conocimiento", size=13.5, weight=ft.FontWeight.W_800, font_family="Poppins"),
            ft.Text(
                "Esto es lo único que Argos sabe de verdad sobre OlimpΩs — se usa tanto acá como en la "
                "app de los socios. Escribí horarios, precios de membresías, políticas de cancelación, etc.",
                size=11.5, color=TEXT_MUTED,
            ),
            campo,
            *avisos,
            ft.Row([action_button("💾 Guardar base de conocimiento", "gold", on_click=self._guardar_base)]),
        ], spacing=10), padding=16)

    def _guardar_base(self, e):
        try:
            argos_repo.guardar_base_conocimiento(self.base_conocimiento_valor)
            self.aviso_base = "Guardado ✓ Ya está disponible para Argos en esta pantalla y en la app móvil."
        except Exception as ex:
            self.aviso_base = None
            self.error_base = f"No se pudo guardar: {ex}"
        self._render()

    # ══════════════ Chat ══════════════
    def _panel_chat(self) -> ft.Container:
        if not self.mensajes:
            contenido_lista = [ft.Text(
                "Preguntale a Argos sobre horarios, membresías, clases, máquinas, el catálogo de comidas "
                "o consejos generales de entrenamiento.",
                size=12.5, color=TEXT_MUTED,
            )]
        else:
            contenido_lista = [self._burbuja(m) for m in self.mensajes]
            if self.enviando:
                contenido_lista.append(self._burbuja({"rol": "assistant", "texto": "Escribiendo…"}, atenuado=True))

        self.lista_mensajes.controls = contenido_lista

        error = []
        if self.error_envio:
            error.append(ft.Text(self.error_envio, size=11.5, color=RED, weight=ft.FontWeight.W_700))

        return section_card(ft.Column([
            ft.Container(content=self.lista_mensajes, height=340),
            divider(),
            *error,
            ft.Row([
                self.campo_mensaje,
                action_button("Enviar ➤", "gold", on_click=self._enviar),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.END),
        ], spacing=10), padding=16)

    def _burbuja(self, m: dict, atenuado: bool = False) -> ft.Row:
        es_usuario = m["rol"] == "user"
        color = DARK if es_usuario else WHITE

        # Argos suele escribir con **negrita** y listas con "- " — se
        # interpreta línea por línea en vez de mostrar los asteriscos
        # sueltos, para que la burbuja no se vea rara.
        filas_texto = []
        for linea in m["texto"].split("\n"):
            recortada = linea.strip()
            es_bullet = recortada.startswith("- ") or recortada.startswith("* ")
            contenido = recortada[2:] if es_bullet else linea
            hijos = []
            if es_bullet:
                hijos.append(ft.Text("•  ", size=13, weight=ft.FontWeight.W_900, color=color))
            hijos.append(ft.Text(spans=_spans_con_negrita(contenido, color), size=13,
                                 weight=ft.FontWeight.W_600, color=color))
            filas_texto.append(ft.Row(hijos, spacing=0))

        burbuja = ft.Container(
            content=ft.Column(filas_texto, spacing=3, tight=True),
            bgcolor=GOLD if es_usuario else DARK2,
            border_radius=14, padding=ft.padding.symmetric(horizontal=14, vertical=10),
            opacity=0.6 if atenuado else 1,
            width=None,
        )
        return ft.Row(
            [ft.Container(content=burbuja, expand=True)],
            alignment=ft.MainAxisAlignment.END if es_usuario else ft.MainAxisAlignment.START,
        )

    def _enviar(self, e):
        if self.enviando:
            return
        texto = (self.campo_mensaje.value or "").strip()
        if not texto:
            return
        self.mensajes.append({"rol": "user", "texto": texto})
        self.campo_mensaje.value = ""
        self.enviando = True
        self.error_envio = None
        self._render()
        try:
            respuesta = argos_repo.preguntar(texto, self.mensajes[:-1])
            self.mensajes.append({"rol": "assistant", "texto": respuesta})
            self.hoy = argos_repo.usos_hoy()
            self.restantes = argos_repo.usos_restantes_hoy()
        except Exception as ex:
            self.error_envio = str(ex)
        self.enviando = False
        self._render()


def build_argos(page: ft.Page, role: str) -> ft.Column:
    return ArgosView(page, role).build()
