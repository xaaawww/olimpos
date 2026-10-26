import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
import empleados_credenciales as _creds
import configuracion_repo
import neon_db
import validaciones


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

        try:
            role = _creds.validar(usuario, password)
        except RuntimeError as ex:
            self._mostrar_error(str(ex))
            return
        if role is None:
            # Avisa cuántos intentos le quedan antes del bloqueo (sin decir si el usuario existe)
            try:
                fila = neon_db.una_fila("SELECT id_empleado FROM empleados WHERE usuario = %s AND estado = 'activo'",
                                        (usuario.lower(),))
                quedan = _creds.MAX_INTENTOS - _creds._fallidos_recientes(fila["id_empleado"]) if fila else None
            except Exception:
                quedan = None
            self._mostrar_error("Usuario o contraseña incorrectos"
                                + (f" · te quedan {quedan} intento{'s' if quedan != 1 else ''}" if quedan and quedan <= 3 else ""))
            return

        self.error_text.value = ""
        self.page.update()
        self.on_login(role)

    def _dialogo_recuperar(self):
        """Paso 1: usuario → se manda un código. Paso 2: código + contraseña nueva."""
        usuario = ft.TextField(label="Tu usuario", value=(self.usuario_field.value or "").strip(), dense=True,
                               input_filter=validaciones.USUARIO, max_length=30, counter=ft.Text(""), width=340)
        codigo = ft.TextField(label="Código de 6 números", dense=True, input_filter=validaciones.SOLO_DIGITOS,
                              max_length=6, counter=ft.Text(""), width=340, visible=False)
        nueva = ft.TextField(label="Contraseña nueva", password=True, can_reveal_password=True, dense=True,
                             max_length=64, counter=ft.Text(""), width=340, visible=False,
                             helper="8 o más caracteres, con letras y números")
        repetir = ft.TextField(label="Repetir contraseña nueva", password=True, can_reveal_password=True, dense=True,
                               max_length=64, counter=ft.Text(""), width=340, visible=False)
        mensaje = ft.Text("Te mandamos un código a tu email o WhatsApp para elegir una contraseña nueva.",
                          size=12.5, color=TEXT_MUTED, width=340)
        boton = ft.FilledButton("Mandarme el código", style=ft.ButtonStyle(bgcolor=GOLD, color=DARK))

        def pedir(e):
            if not usuario.value:
                mensaje.value, mensaje.color = "Escribí tu usuario.", RED
                self.page.update()
                return
            try:
                ok, texto = _creds.iniciar_recuperacion(usuario.value)
            except Exception as ex:
                ok, texto = False, f"No se pudo: {ex}"
            mensaje.value, mensaje.color = texto, (GREEN if ok else RED)
            if ok:
                for c in (codigo, nueva, repetir):
                    c.visible = True
                usuario.disabled = True
                boton.content, boton.on_click = "Cambiar contraseña", confirmar
            self.page.update()

        def confirmar(e):
            if (nueva.value or "") != (repetir.value or ""):
                mensaje.value, mensaje.color = "Las contraseñas nuevas no coinciden.", RED
                self.page.update()
                return
            try:
                ok, texto = _creds.confirmar_recuperacion(usuario.value, codigo.value, nueva.value or "")
            except Exception as ex:
                ok, texto = False, f"No se pudo: {ex}"
            mensaje.value, mensaje.color = texto, (GREEN if ok else RED)
            if ok:
                self.usuario_field.value, self.password_field.value = usuario.value.strip().lower(), ""
                boton.content, boton.on_click = "Volver a entrar", lambda ev: self.page.pop_dialog()
                for c in (codigo, nueva, repetir):
                    c.disabled = True
            self.page.update()

        boton.on_click = pedir
        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Recuperar contraseña", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Column([mensaje, usuario, codigo, nueva, repetir], spacing=10, tight=True, width=360),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.page.pop_dialog()), boton],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def _mostrar_error(self, mensaje: str):
        self.error_text.value = mensaje
        self.page.update()

    def _completar(self, fila: dict):
        self.usuario_field.value = fila["usuario"]
        self.password_field.value = fila["password"]
        self.error_text.value = ""
        self.page.update()

    def _credencial_row(self, fila: dict) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Text(fila["label"], size=12, weight=ft.FontWeight.W_600,
                        color=GOLD, font_family="Poppins", expand=True),
                ft.Column([
                    ft.Text(fila["usuario"], size=12.5, weight=ft.FontWeight.W_500,
                            color=ft.Colors.WHITE, font_family="Consolas, monospace"),
                    ft.Text(fila["password"], size=11.5,
                            color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
                            font_family="Consolas, monospace"),
                ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(vertical=8, horizontal=6),
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))),
            border_radius=8,
            ink=True,
            on_click=lambda e, f=fila: self._completar(f),
            tooltip="Clic para completar usuario y contraseña",
        )

    def build(self) -> ft.Stack:
        self.usuario_field = ft.TextField(
            label="Usuario", width=320, border_color=ft.Colors.with_opacity(0.25, GOLD),
            focused_border_color=GOLD, color=ft.Colors.WHITE, label_style=ft.TextStyle(color=GRAY),
            cursor_color=GOLD, on_submit=lambda e: self.password_field.focus(),
            input_filter=validaciones.USUARIO, max_length=30, counter=ft.Text(""),
            value=configuracion_repo.usuario_recordado(),   # "Recordar mi usuario" (Configuración)
        )
        self.password_field = ft.TextField(
            label="Contraseña", width=320, password=True, can_reveal_password=True,
            border_color=ft.Colors.with_opacity(0.25, GOLD), focused_border_color=GOLD,
            color=ft.Colors.WHITE, label_style=ft.TextStyle(color=GRAY), cursor_color=GOLD,
            on_submit=self._do_login, max_length=64, counter=ft.Text(""),
        )
        self.error_text = ft.Text("", size=12, color=RED, weight=ft.FontWeight.W_500)

        login_button = ft.Container(
            content=ft.Text("⚡ Ingresar al Sistema", size=14, weight=ft.FontWeight.W_500,
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
                ft.Text("OLIMPOS", size=26, weight=ft.FontWeight.W_600, color=GOLD,
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
                ft.TextButton("¿Olvidaste tu contraseña?", on_click=lambda e: self._dialogo_recuperar(),
                              style=ft.ButtonStyle(color=ft.Colors.with_opacity(0.7, GOLD))),
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
                ft.Text("🔑 USUARIOS DEL SISTEMA", size=12, weight=ft.FontWeight.W_600,
                        color=GOLD, font_family="Poppins", style=ft.TextStyle(letter_spacing=1)),
                ft.Text("Un usuario por rol — tocá una fila para completar los datos", size=10.5,
                        color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
                ft.Row([
                    ft.Text("ROL", size=9.5, weight=ft.FontWeight.W_500, expand=True,
                            color=ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                    ft.Text("USUARIO / CONTRASEÑA", size=9.5, weight=ft.FontWeight.W_500,
                            color=ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                ]),
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
