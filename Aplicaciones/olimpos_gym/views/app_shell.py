import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))

import flet as ft
from theme import *
from components import stat_badge, status_pill, avatar, section_card
import empleados_credenciales
import configuracion_repo
import notificaciones_repo
from views.dashboard import build_dashboard
from views.socios import build_socios
from views.asistencia import build_asistencia
from views.camaras import build_camaras
from views.gestion_personal import build_personal
from views.pagos import build_pagos
from views.progreso import build_progreso
from views.notificaciones import build_notificaciones
from views.configuracion import build_configuracion
from views.editor_dietas import build_editor_dietas
from views.editor_ejercicios import build_editor_ejercicios
from views.editor_rutinas import build_editor_rutinas
from views.editor_membresias import build_editor_membresias
from views.asignar_dietas import build_asignar_dietas
from views.tablon import build_tablon
from views.verificacion_marcas import build_verificacion_marcas
from views.argos import build_argos
from views.qr_ingreso import build_qr_ingreso


class AppShell:
    def __init__(self, page: ft.Page, role: str, on_logout, on_recargar=None):
        self.page = page
        self.role = role
        self.on_logout = on_logout
        self.on_recargar = on_recargar    # vuelve a armar todo con la apariencia nueva (ver main.py)
        self.role_data = ROLES[role]
        self.secciones = [i["s"] for i in self.role_data["nav"] if "s" in i]
        inicio = configuracion_repo.pref("seccion_inicio")
        self.current_section = inicio if inicio in self.secciones else "dashboard"
        self.compacto = bool(configuracion_repo.pref("menu_compacto"))
        self.nav_items_refs = {}
        self.content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        # contador de avisos sin leer, al lado de "Notificaciones"
        self.badge_texto = ft.Text("", size=10.5, weight=ft.FontWeight.W_600, color=WHITE)
        self.badge = ft.Container(self.badge_texto, bgcolor=RED, border_radius=10, visible=False,
                                  padding=ft.padding.symmetric(horizontal=6, vertical=1))

    def _build_sidebar(self) -> ft.Container:
        # Claro y simple: logo, secciones con íconos de línea y, abajo, el
        # empleado que inició sesión (el real, no un nombre fijo por rol).
        # En modo compacto (Configuración → Apariencia) quedan solo los íconos.
        if self.compacto:
            brand = ft.Container(ft.Image(src="L21.png", width=38, height=38, fit=ft.BoxFit.CONTAIN),
                                 alignment=ft.Alignment.CENTER, padding=ft.padding.only(top=26, bottom=22),
                                 tooltip=configuracion_repo.club()["nombre"])
        else:
            brand = ft.Container(
                content=ft.Row([
                    ft.Image(src="L21.png", width=38, height=38, fit=ft.BoxFit.CONTAIN),
                    ft.Column([
                        ft.Text("OlimpOS", size=22, weight=ft.FontWeight.W_500, color=DARK, font_family="Poppins",
                                style=ft.TextStyle(height=1.1)),
                        ft.Text(configuracion_repo.club()["nombre"], size=11, color=TEXT_MUTED, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS),
                    ], spacing=0, expand=True),
                ], spacing=10),
                padding=ft.padding.only(left=22, right=16, top=26, bottom=22),
            )

        nav_controls = []
        for item in self.role_data["nav"]:
            if "sep" in item:
                # Separación entre áreas: una línea fina y el nombre del área.
                if self.compacto:
                    nav_controls.append(ft.Container(ft.Divider(height=1, thickness=1, color=GRAY_LIGHT),
                                                     padding=ft.padding.symmetric(horizontal=8, vertical=8)))
                    continue
                nav_controls.append(ft.Container(
                    content=ft.Column([
                        ft.Divider(height=1, thickness=1, color=GRAY_LIGHT),
                        ft.Text(item["sep"].upper(), size=10.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED,
                                style=ft.TextStyle(letter_spacing=1.2)),
                    ], spacing=10),
                    padding=ft.padding.only(left=14, right=14, top=12, bottom=2),
                ))
            else:
                nav_controls.append(self._nav_item(item))

        nav = ft.Container(
            content=ft.Column(nav_controls, spacing=2, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.symmetric(horizontal=10 if self.compacto else 12),
            expand=True,
        )

        actual = empleados_credenciales.actual() or {}
        nombre = actual.get("nombre") or self.role_data["name"]
        rol = actual.get("rol_label") or self.role_data["label"]
        avatar_usuario = ft.Container(ft.Icon(ft.Icons.PERSON, size=22, color=WHITE), width=38, height=38,
                                      border_radius=19, bgcolor=GRAY, alignment=ft.Alignment.CENTER)
        usuario = ft.PopupMenuButton(
            content=avatar_usuario if self.compacto else ft.Row([
                avatar_usuario,
                ft.Column([
                    ft.Text(nombre, size=13, weight=ft.FontWeight.W_500, color=DARK,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(rol, size=11.5, color=TEXT_MUTED),
                ], spacing=0, expand=True),
                ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=18, color=TEXT_MUTED),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            tooltip=f"{nombre} · {rol}" if self.compacto else "Opciones de la cuenta",
            items=[
                ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=18, color=DARK),
                                                 ft.Text("Configuración")], spacing=10),
                                 on_click=lambda e: self._navigate("configuracion")),
                ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, size=18, color=RED),
                                                 ft.Text("Cerrar sesión", color=RED)], spacing=10),
                                 on_click=lambda e: self._cerrar_sesion()),
            ],
        )
        footer = ft.Container(
            content=usuario,
            padding=ft.padding.symmetric(vertical=16, horizontal=18 if not self.compacto else 0),
            alignment=ft.Alignment.CENTER if self.compacto else None,
            border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
        )

        return ft.Container(
            content=ft.Column([brand, nav, footer], spacing=0, expand=True),
            width=SIDEBAR_W_COMPACTO if self.compacto else SIDEBAR_W,
            bgcolor=SIDEBAR_BG,
            border=ft.border.only(right=ft.BorderSide(1, GRAY_LIGHT)),
            expand=False,
        )

    def _nav_item(self, item: dict) -> ft.Container:
        section_id = item["s"]
        is_active = section_id == self.current_section
        icono = ft.Icon(ICONOS_NAV.get(section_id, ft.Icons.CIRCLE_OUTLINED), size=20,
                        color=DARK if is_active else NAV_ICONO)
        texto = ft.Text(item["l"], size=14, weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.W_400,
                        color=DARK if is_active else NAV_TEXTO, expand=True, max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS)
        if self.compacto:
            contenido = ft.Stack([ft.Container(icono, alignment=ft.Alignment.CENTER, width=36, height=24)] +
                                 ([ft.Container(self.badge, right=-4, top=-6)] if section_id == "notificaciones" else []),
                                 width=36, height=24)
        else:
            contenido = ft.Row([icono, texto] + ([self.badge] if section_id == "notificaciones" else []), spacing=14)
        nav_container = ft.Container(
            content=contenido,
            bgcolor=NAV_ACTIVO_BG if is_active else ft.Colors.TRANSPARENT,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=8 if self.compacto else 14, vertical=10),
            alignment=ft.Alignment.CENTER if self.compacto else None,
            tooltip=item["l"] if self.compacto else None,
            on_click=lambda e, s=section_id: self._navigate(s),
            ink=True,
        )
        nav_container.data = (icono, texto)
        self.nav_items_refs[section_id] = nav_container
        return nav_container

    def _navigate(self, section_id: str):
        self.current_section = section_id

        for sid, container in self.nav_items_refs.items():
            is_active = sid == section_id
            container.bgcolor = NAV_ACTIVO_BG if is_active else ft.Colors.TRANSPARENT
            icono, texto = container.data
            texto.weight = ft.FontWeight.W_500 if is_active else ft.FontWeight.W_400
            texto.color = DARK if is_active else NAV_TEXTO
            icono.color = DARK if is_active else NAV_ICONO

        self.salir_de_seccion()
        self.content_area.controls.clear()
        content = self._build_section(section_id)
        self.content_area.controls.append(
            ft.Container(content=content, padding=ft.padding.symmetric(horizontal=36, vertical=30), expand=True,
                         alignment=ft.Alignment.TOP_LEFT)
        )
        self.page.update()

    def salir_de_seccion(self):
        """Avisa a la sección que se deja (ej. Cámaras corta su actualización
        en segundo plano). La sección lo pide con data={"al_salir": funcion}."""
        for envoltorio in self.content_area.controls:
            datos = getattr(getattr(envoltorio, "content", None), "data", None)
            if isinstance(datos, dict) and callable(datos.get("al_salir")):
                try:
                    datos["al_salir"]()
                except Exception:
                    pass

    def _build_section(self, section_id: str) -> ft.Control:
        builders = {
            "dashboard":      lambda: build_dashboard(self.role, lambda s: self._navigate(s), self.page),
            "socios":         lambda: build_socios(self.page),
            "personal":       lambda: build_personal(self.page, self.role),
            "asistencia":     lambda: build_asistencia(self.page, self.role),
            "rutinas":        lambda: build_editor_rutinas(self.page, f"{self.role_data['name']} — {self.role_data['label']}"),
            "editor-dietas":  lambda: build_editor_dietas(self.page),
            "asignar-dietas": lambda: build_asignar_dietas(self.page, f"{self.role_data['name']} — {self.role_data['label']}"),
            "tablon":         lambda: build_tablon(self.page, self.role, f"{self.role_data['name']} — {self.role_data['label']}"),
            "editor-ejercicios": lambda: build_editor_ejercicios(self.page),
            "verificacion-marcas": lambda: build_verificacion_marcas(self.page, self.role_data["name"]),
            "membresias":     lambda: build_editor_membresias(self.page, f"{self.role_data['name']} — {self.role_data['label']}"),
            "progreso":       lambda: build_progreso(self.page),
            "pagos":          lambda: build_pagos(self.page, self.role, empleados_credenciales.nombre_para_firmar()),
            "notificaciones": lambda: build_notificaciones(self.page, self.role, self._navigate, self.mostrar_contador),
            "camaras":        lambda: build_camaras(self.page, self.role),
            "configuracion":  lambda: build_configuracion(self.page, self.role, self),
            "argos":          lambda: build_argos(self.page, self.role),
            "qr-ingreso":     lambda: build_qr_ingreso(self.page, self.role),
        }
        builder = builders.get(section_id, lambda: ft.Text(f"Sección: {section_id}"))
        return builder()

    # ── contador de avisos ──
    def mostrar_contador(self, n: int):
        visible = bool(n) and bool(configuracion_repo.pref("contador_menu"))
        self.badge_texto.value = "99+" if n > 99 else str(n)
        if visible != self.badge.visible or self.badge.visible:
            self.badge.visible = visible
            try:
                if self.badge.page:
                    self.badge.update()
            except RuntimeError:
                pass

    def actualizar_contador(self):
        """Cuenta los avisos sin leer en segundo plano (son varias consultas)."""
        if "notificaciones" not in self.secciones:
            return
        def contar():
            self.mostrar_contador(notificaciones_repo.sin_leer(
                self.role, empleados_credenciales.id_empleado_actual()))
        self.page.run_thread(contar)

    # ── sesión ──
    def _cerrar_sesion(self):
        if not configuracion_repo.pref("confirmar_salida"):
            self.salir_de_seccion()
            self.on_logout()
            return

        def salir(e):
            self.page.pop_dialog()
            self.salir_de_seccion()
            self.on_logout()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Cerrar sesión?", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text("Vas a volver a la pantalla de inicio de sesión.", size=13, color=TEXT_MUTED),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.TextButton("Cerrar sesión", on_click=salir, style=ft.ButtonStyle(color=RED))],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def recargar(self, seccion: str | None = None):
        """Rearma la pantalla con la apariencia nueva (colores, fondo, menú)."""
        if self.on_recargar:
            self.salir_de_seccion()
            self.on_recargar(seccion or self.current_section)

    def build(self) -> ft.Row:
        sidebar = self._build_sidebar()

        self.content_area.controls.clear()
        self.content_area.controls.append(
            ft.Container(
                content=self._build_section(self.current_section),
                padding=ft.padding.symmetric(horizontal=36, vertical=30), expand=True,
                         alignment=ft.Alignment.TOP_LEFT,
            )
        )

        main_area = ft.Container(content=self.content_area, expand=True, bgcolor=CREAM,
                                 alignment=ft.Alignment.TOP_LEFT)   # pantallas cortas: arriba, no centradas
        return ft.Row([sidebar, main_area], spacing=0, expand=True)
