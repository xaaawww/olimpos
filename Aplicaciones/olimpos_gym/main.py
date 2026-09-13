import sys, os
# Ensure project root and views dir are importable
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "views"))

import flet as ft
from views.login import LoginView
from views.app_shell import AppShell


def main(page: ft.Page):
    page.title = "OLIMPOS GYM — Sistema de Gestión"
    page.window.width = 1280
    page.window.height = 820
    page.window.min_width = 960
    page.window.min_height = 640
    page.bgcolor = "#FAFAF0"
    page.padding = 0
    page.spacing = 0

    def on_login(role: str):
        page.clean()
        shell = AppShell(page, role, on_logout)
        page.add(shell.build())
        page.update()

    def on_logout():
        page.clean()
        login = LoginView(page, on_login)
        page.add(login.build())
        page.update()

    login = LoginView(page, on_login)
    page.add(login.build())
    page.update()


ft.run(main, assets_dir="img")
