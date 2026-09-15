import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))

import flet as ft
from theme import *
from components import stat_badge, status_pill, avatar, section_card
from views.dashboard import build_dashboard
from views.socios import build_socios
from views.personal import (build_personal, build_asistencia, build_rutinas, build_dietas,
                             build_progreso, build_pagos, build_reportes, build_notificaciones,
                             build_camaras, build_stock, build_configuracion, build_mi_perfil)
from views.editor_dietas import build_editor_dietas
from views.editor_ejercicios import build_editor_ejercicios
from views.editor_rutinas import build_editor_rutinas
from views.editor_membresias import build_editor_membresias
from views.verificacion_marcas import build_verificacion_marcas
from views.argos import build_argos


class AppShell:
    def __init__(self, page: ft.Page, role: str, on_logout):
        self.page = page
        self.role = role
        self.on_logout = on_logout
        self.role_data = ROLES[role]
        self.current_section = "dashboard"
        self.nav_items_refs = {}
        self.content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        self.topbar_title = ft.Text("Dashboard", size=17, weight=ft.FontWeight.W_800,
                                    color=DARK, font_family="Poppins", expand=True)

    def _build_sidebar(self) -> ft.Container:
        initials = self.role_data["initials"]
        name = self.role_data["name"]
        label = self.role_data["label"]

        brand = ft.Container(
            content=ft.Row([
                ft.Image(src="L21.png", width=32, height=32, fit=ft.BoxFit.CONTAIN),
                ft.Column([
                    ft.Text("OLIMPOS", size=15, weight=ft.FontWeight.W_900,
                            color=GOLD, font_family="Poppins"),
                    ft.Text("GYM SYSTEM", size=9, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
),
                ], spacing=0),
            ], spacing=10),
            padding=ft.padding.symmetric(vertical=20, horizontal=20),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.08, GOLD))),
        )

        user_section = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(initials[0], size=14, weight=ft.FontWeight.W_900, color=DARK),
                    width=36, height=36, border_radius=10,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                        colors=[GOLD, GOLD_DARK]
                    ),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(name, size=12, weight=ft.FontWeight.W_800,
                            color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
                    ft.Container(
                        content=ft.Text(label, size=9, weight=ft.FontWeight.W_700,
                                        color=GOLD),
                        bgcolor=ft.Colors.with_opacity(0.15, GOLD),
                        border_radius=4,
                        padding=ft.padding.symmetric(horizontal=6, vertical=1),
                    )
                ], spacing=3),
            ], spacing=10),
            padding=ft.padding.symmetric(vertical=14, horizontal=16),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.08, GOLD))),
        )

        nav_controls = []
        for item in self.role_data["nav"]:
            if "sep" in item:
                nav_controls.append(
                    ft.Container(
                        content=ft.Text(item["sep"].upper(), size=9, weight=ft.FontWeight.W_800,
                                        color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
),
                        padding=ft.padding.only(left=8, top=8, bottom=4),
                    )
                )
            else:
                nav_controls.append(self._nav_item(item))

        nav = ft.Container(
            content=ft.Column(nav_controls, spacing=2, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.symmetric(vertical=12, horizontal=10),
            expand=True,
        )

        logout_btn = ft.Container(
            content=ft.Row([
                ft.Text("🚪", size=14),
                ft.Text("Cerrar sesión", size=11.5, weight=ft.FontWeight.W_700,
                        color=ft.Colors.with_opacity(0.7, RED)),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            bgcolor=ft.Colors.with_opacity(0.08, RED),
            border=ft.border.all(1, ft.Colors.with_opacity(0.15, RED)),
            border_radius=8,
            padding=ft.padding.symmetric(vertical=8),
            on_click=lambda e: self.on_logout(),
            ink=True,
        )

        footer = ft.Container(
            content=logout_btn,
            padding=ft.padding.symmetric(vertical=14, horizontal=16),
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.with_opacity(0.08, GOLD))),
        )

        return ft.Container(
            content=ft.Column([brand, user_section, nav, footer],
                              spacing=0, expand=True),
            width=SIDEBAR_W,
            bgcolor=DARK2,
            border=ft.border.only(right=ft.BorderSide(1, ft.Colors.with_opacity(0.1, GOLD))),
            expand=False,
        )

    def _nav_item(self, item: dict) -> ft.Container:
        section_id = item["s"]
        is_active = section_id == self.current_section
        badge = item.get("b")

        row_children = [
            ft.Text(item["i"], size=16, width=22),
            ft.Text(item["l"], size=13, weight=ft.FontWeight.W_700,
                    color=GOLD if is_active else ft.Colors.with_opacity(0.45, ft.Colors.WHITE),
                    font_family="Poppins", expand=True),
        ]
        if badge:
            row_children.append(
                ft.Container(
                    content=ft.Text(badge, size=9, weight=ft.FontWeight.W_900, color=WHITE),
                    bgcolor=RED, border_radius=20,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                )
            )

        nav_container = ft.Container(
            content=ft.Row(row_children, spacing=10),
            bgcolor=ft.Colors.with_opacity(0.15, GOLD) if is_active else ft.Colors.TRANSPARENT,
            border=ft.border.only(left=ft.BorderSide(3, GOLD) if is_active else ft.BorderSide(0)),
            border_radius=10,
            padding=ft.padding.only(left=9, right=12, top=9, bottom=9),
            on_click=lambda e, s=section_id: self._navigate(s),
            ink=True,
        )
        self.nav_items_refs[section_id] = nav_container
        return nav_container

    def _navigate(self, section_id: str):
        self.current_section = section_id
        self.topbar_title.value = TITLES.get(section_id, section_id)

        for sid, container in self.nav_items_refs.items():
            is_active = sid == section_id
            container.bgcolor = ft.Colors.with_opacity(0.15, GOLD) if is_active else ft.Colors.TRANSPARENT
            container.border = ft.border.only(
                left=ft.BorderSide(3, GOLD) if is_active else ft.BorderSide(0)
            )
            row = container.content
            if isinstance(row, ft.Row) and len(row.controls) > 1:
                text_ctrl = row.controls[1]
                if isinstance(text_ctrl, ft.Text):
                    text_ctrl.color = GOLD if is_active else ft.Colors.with_opacity(0.45, ft.Colors.WHITE)

        self.content_area.controls.clear()
        content = self._build_section(section_id)
        self.content_area.controls.append(
            ft.Container(content=content, padding=24, expand=True)
        )
        self.page.update()

    def _build_section(self, section_id: str) -> ft.Control:
        builders = {
            "dashboard":      lambda: build_dashboard(self.role, lambda s: self._navigate(s)),
            "socios":         lambda: build_socios(self.page),
            "personal":       build_personal,
            "asistencia":     build_asistencia,
            "rutinas":        lambda: build_editor_rutinas(self.page, f"{self.role_data['name']} — {self.role_data['label']}"),
            "mi-rutina":      build_rutinas,
            "dietas":         build_dietas,
            "editor-dietas":  lambda: build_editor_dietas(self.page),
            "editor-ejercicios": lambda: build_editor_ejercicios(self.page),
            "verificacion-marcas": lambda: build_verificacion_marcas(self.page, self.role_data["name"]),
            "membresias":     lambda: build_editor_membresias(self.page, f"{self.role_data['name']} — {self.role_data['label']}"),
            "mi-dieta":       build_dietas,
            "progreso":       build_progreso,
            "mi-progreso":    build_progreso,
            "pagos":          build_pagos,
            "reportes":       build_reportes,
            "notificaciones": build_notificaciones,
            "camaras":        build_camaras,
            "stock":          build_stock,
            "configuracion":  build_configuracion,
            "mi-perfil":      build_mi_perfil,
            "argos":          lambda: build_argos(self.page, self.role),
        }
        builder = builders.get(section_id, lambda: ft.Text(f"Sección: {section_id}"))
        return builder()

    def _build_topbar(self) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                self.topbar_title,
                ft.Container(
                    content=ft.Row([
                        ft.Text("🔍", size=14),
                        ft.TextField(hint_text="Buscar socios, rutinas...", border=ft.InputBorder.NONE,
                                     hint_style=ft.TextStyle(color=TEXT_MUTED, size=13),
                                     text_style=ft.TextStyle(color=DARK, size=13),
                                     content_padding=0, height=32, expand=True,
                                     bgcolor=ft.Colors.TRANSPARENT),
                    ], spacing=8, expand=True),
                    bgcolor=CREAM, border=ft.border.all(1.5, GRAY_LIGHT),
                    border_radius=10, padding=ft.padding.symmetric(horizontal=12, vertical=4),
                    expand=True, width=280,
                ),
                ft.Container(
                    content=ft.Stack([
                        ft.Text("🔔", size=16),
                        ft.Container(
                            width=8, height=8,
                            bgcolor=RED, border_radius=4,
                            border=ft.border.all(2, WHITE),
                            right=0, top=0,
                        ),
                    ]),
                    width=36, height=36, border_radius=10,
                    bgcolor=CREAM, border=ft.border.all(1.5, GRAY_LIGHT),
                    alignment=ft.Alignment.CENTER,
                    on_click=lambda e: self._navigate("notificaciones"),
                    ink=True,
                ),
                ft.Container(
                    content=ft.Text(self.role_data["initials"][0], size=13,
                                    weight=ft.FontWeight.W_900, color=DARK),
                    width=36, height=36, border_radius=10,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                        colors=[GOLD, GOLD_DARK],
                    ),
                    alignment=ft.Alignment.CENTER,
                ),
            ], spacing=12),
            height=60,
            bgcolor=WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1.5, GRAY_LIGHT)),
            padding=ft.padding.symmetric(horizontal=24),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK)),
        )

    def build(self) -> ft.Row:
        sidebar = self._build_sidebar()
        topbar = self._build_topbar()

        self.content_area.controls.clear()
        self.content_area.controls.append(
            ft.Container(
                content=build_dashboard(self.role, lambda s: self._navigate(s)),
                padding=24, expand=True
            )
        )

        main_area = ft.Column([
            topbar,
            ft.Container(
                content=self.content_area,
                expand=True,
            ),
        ], spacing=0, expand=True)

        return ft.Row([sidebar, main_area], spacing=0, expand=True)
