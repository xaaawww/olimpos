import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
import empleados_credenciales as _creds


class LoginView:
    def __init__(self, page: ft.Page, on_login_callback):
        self.page = page
        self.on_login = on_login_callback
        self.usuario_field = None
        self.password_field = None
        self.error_text = None

    def _do_login(self, e):
        usuario = (self.usuario_field.value or "").strip()
        password = self.password_field.value or ""

        if not usuario or not password:
            self._mostrar_error("Completá usuario y contraseña")
            return

        role = _creds.validar(usuario, password)
        if role is None:
            self._mostrar_error("Usuario o contraseña incorrectos")
            return

        self.error_text.value = ""
        self.page.update()
        self.on_login(role)

    def _mostrar_error(self, mensaje: str):
        self.error_text.value = mensaje
        self.page.update()

    def _credencial_row(self, fila: dict) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(fila["label"], size=12, weight=ft.FontWeight.W_800,
                            color=GOLD, font_family="Poppins"),
                    ft.Text(fila["nombre"], size=10.5,
                            color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                ], spacing=1, expand=True),
                ft.Column([
                    ft.Text(fila["usuario"], size=12.5, weight=ft.FontWeight.W_700,
                            color=ft.Colors.WHITE, font_family="Consolas, monospace"),
                    ft.Text(fila["password"], size=11,
                            color=ft.Colors.with_opacity(0.55, ft.Colors.WHITE),
                            font_family="Consolas, monospace"),
                ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(vertical=9, horizontal=4),
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))),
        )

    def build(self) -> ft.Stack:
        self.usuario_field = ft.TextField(
            label="Usuario", width=320, border_color=ft.Colors.with_opacity(0.25, GOLD),
            focused_border_color=GOLD, color=ft.Colors.WHITE, label_style=ft.TextStyle(color=GRAY),
            cursor_color=GOLD, on_submit=lambda e: self.password_field.focus(),
        )
        self.password_field = ft.TextField(
            label="Contraseña", width=320, password=True, can_reveal_password=True,
            border_color=ft.Colors.with_opacity(0.25, GOLD), focused_border_color=GOLD,
            color=ft.Colors.WHITE, label_style=ft.TextStyle(color=GRAY), cursor_color=GOLD,
            on_submit=self._do_login,
        )
        self.error_text = ft.Text("", size=12, color=RED, weight=ft.FontWeight.W_600)

        login_button = ft.Container(
            content=ft.Text("⚡ Ingresar al Sistema", size=14, weight=ft.FontWeight.W_700,
                            color=DARK, font_family="Poppins", text_align=ft.TextAlign.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[GOLD, GOLD_DARK],
            ),
            border_radius=12,
            padding=ft.padding.symmetric(vertical=14),
            on_click=self._do_login,
            ink=True,
            width=320,
        )

        login_box = ft.Container(
            content=ft.Column([
                ft.Image(src="L21.png", width=110, height=110, fit=ft.BoxFit.CONTAIN),
                ft.Text("OLIMPOS", size=26, weight=ft.FontWeight.W_900, color=GOLD,
                        font_family="Poppins", text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(letter_spacing=3)),
                ft.Text("SISTEMA DE GESTIÓN INTEGRAL", size=11,
                        color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                        text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(letter_spacing=1.5)),
                ft.Container(height=22),
                self.usuario_field,
                self.password_field,
                self.error_text,
                ft.Container(height=6),
                login_button,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10,
               scroll=ft.ScrollMode.AUTO),
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, GOLD)),
            border_radius=28,
            padding=ft.padding.symmetric(vertical=36, horizontal=40),
            width=420,
            shadow=ft.BoxShadow(blur_radius=80, spread_radius=0,
                                color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK)),
        )

        credenciales_panel = ft.Container(
            content=ft.Column([
                ft.Text("🔑 CREDENCIALES DE ACCESO", size=12, weight=ft.FontWeight.W_800,
                        color=GOLD, font_family="Poppins", style=ft.TextStyle(letter_spacing=1)),
                ft.Text("Para la demo — un usuario por rol", size=10.5,
                        color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
                ft.Container(height=6),
                ft.Column(
                    [self._credencial_row(f) for f in _creds.listado_para_mostrar()],
                    spacing=0,
                ),
            ], spacing=2),
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.15, GOLD)),
            border_radius=20,
            padding=ft.padding.symmetric(vertical=22, horizontal=22),
            width=340,
        )

        bg = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[DARK, DARK2, DARK3],
            ),
        )

        centered = ft.Container(
            content=ft.Row(
                [login_box, credenciales_panel],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=28,
                wrap=True,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=20,
        )

        return ft.Stack([
            bg,
            centered,
        ], expand=True)
