import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *


class LoginView:
    def __init__(self, page: ft.Page, on_login_callback):
        self.page = page
        self.on_login = on_login_callback
        self.selected_role = None
        self.role_buttons = {}

    def _role_button(self, emoji: str, name: str, role_key: str) -> ft.Container:
        def on_click(e):
            self.selected_role = role_key
            for key, btn in self.role_buttons.items():
                btn.border = ft.border.all(1.5, ft.Colors.with_opacity(0.18, GOLD))
                btn.bgcolor = ft.Colors.with_opacity(0.04, ft.Colors.WHITE)
                btn.shadow = None
            self.role_buttons[role_key].border = ft.border.all(1.5, GOLD)
            self.role_buttons[role_key].bgcolor = ft.Colors.with_opacity(0.15, GOLD)
            self.role_buttons[role_key].shadow = ft.BoxShadow(
                blur_radius=0, spread_radius=3,
                color=ft.Colors.with_opacity(0.15, GOLD)
            )
            self.page.update()

        inner = ft.Column([
            ft.Text(emoji, size=22, text_align=ft.TextAlign.CENTER),
            ft.Text(name, size=11.5, weight=ft.FontWeight.W_800,
                    color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                    font_family="Poppins", text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

        btn = ft.Container(
            content=inner,
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.18, GOLD)),
            border_radius=12,
            padding=ft.padding.symmetric(vertical=14, horizontal=10),
            on_click=on_click,
            ink=True,
            expand=True,
        )
        self.role_buttons[role_key] = btn
        return btn

    def _do_login(self, e):
        if not self.selected_role:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Por favor seleccioná un tipo de usuario"),
                bgcolor=RED, open=True
            )
            self.page.update()
            return
        self.on_login(self.selected_role)

    def _select_socio(self):
        self.selected_role = "socio"
        for key, btn in self.role_buttons.items():
            btn.border = ft.border.all(1.5, ft.Colors.with_opacity(0.18, GOLD))
            btn.bgcolor = ft.Colors.with_opacity(0.04, ft.Colors.WHITE)
            btn.shadow = None
        self.role_buttons["socio"].border = ft.border.all(1.5, GOLD)
        self.role_buttons["socio"].bgcolor = ft.Colors.with_opacity(0.15, GOLD)
        self.role_buttons["socio"].shadow = ft.BoxShadow(
            blur_radius=0, spread_radius=3, color=ft.Colors.with_opacity(0.15, GOLD)
        )
        self.page.update()

    def build(self) -> ft.Stack:
        roles_grid = ft.Row([
            self._role_button("👑", "Dueño", "dueno"),
            self._role_button("🛡️", "Administrador", "admin"),
            self._role_button("🏋️", "Entrenador", "entrenador"),
            self._role_button("🥗", "Nutricionista", "nutricionista"),
            self._role_button("🔒", "Seguridad", "seguridad"),
            self._role_button("📋", "Recepcionista", "recepcionista"),
        ], spacing=10, wrap=False)

        socio_btn = ft.Container(
            content=ft.Row([
                ft.Text("💪", size=22),
                ft.Text("Socio", size=11.5, weight=ft.FontWeight.W_800,
                        color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                        font_family="Poppins"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.18, GOLD)),
            border_radius=12,
            padding=ft.padding.symmetric(vertical=14, horizontal=10),
            on_click=lambda e: self._select_socio(),
            ink=True,
            width=380,
        )
        self.role_buttons["socio"] = socio_btn

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
            width=400,
        )

        login_box = ft.Container(
            content=ft.Column([
                ft.Image(src="L21.png", width=120, height=120, fit=ft.BoxFit.CONTAIN),
                ft.Text("OLIMPOS", size=28, weight=ft.FontWeight.W_900, color=GOLD,
                        font_family="Poppins", text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(letter_spacing=3)),
                ft.Text("SISTEMA DE GESTIÓN INTEGRAL", size=11,
                        color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                        text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(letter_spacing=1.5)),
                ft.Container(height=24),
                ft.Text("SELECCIONÁ TU TIPO DE USUARIO", size=11, weight=ft.FontWeight.W_800,
                        color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                        style=ft.TextStyle(letter_spacing=1)),
                ft.Container(height=8),
                roles_grid,
                ft.Container(height=8),
                ft.Row([socio_btn], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=16),
                ft.Row([login_button], alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
               scroll=ft.ScrollMode.AUTO),
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, GOLD)),
            border_radius=28,
            padding=ft.padding.symmetric(vertical=40, horizontal=40),
            width=600,
            shadow=ft.BoxShadow(blur_radius=80, spread_radius=0,
                                color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK)),
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
            content=login_box,
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

        return ft.Stack([
            bg,
            centered,
        ], expand=True)
