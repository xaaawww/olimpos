#!python3.12
# La línea de arriba hace que "py main.py" y el doble clic abran Python 3.12
# (el que tiene las librerías de install.txt), aunque haya otro más nuevo.
import sys, os

if sys.version_info[:2] != (3, 12):
    print(f"Este sistema necesita Python 3.12 y se abrió con Python {sys.version.split()[0]}.\n"
          "Abrilo con abrir_sistema.bat (doble clic) o con:  py -3.12 main.py")
    input("Enter para cerrar...")
    sys.exit(1)

# Ensure project root and views dir are importable
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "views"))

import importlib
import flet as ft
import empleados_credenciales
import configuracion_repo
import theme
import views.app_shell
from views.login import LoginView

CARPETA_VISTAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "views")


def _recargar_modulos():
    """Vuelve a cargar theme y las pantallas para que tomen la apariencia del
    empleado (los colores y el fondo se leen al importar theme)."""
    importlib.reload(theme)
    import components
    importlib.reload(components)
    vistas = [m for n, m in list(sys.modules.items())
              if m is not None and getattr(m, "__file__", None)
              and os.path.dirname(os.path.abspath(m.__file__)) == CARPETA_VISTAS
              and not n.endswith("app_shell") and not n.endswith("__init__") and n != "views"]
    # dos pasadas: una pantalla que importa funciones de otra se queda con las nuevas
    for _ in range(2):
        for m in vistas:
            importlib.reload(m)
    for n in ("app_shell", "views.app_shell"):
        if n in sys.modules:
            importlib.reload(sys.modules[n])


def _apariencia_distinta() -> bool:
    return theme.GOLD != theme.PALETAS.get(configuracion_repo.pref("acento"), theme.PALETAS["dorado"])[1] \
        or theme.CREAM != theme.FONDOS.get(configuracion_repo.pref("fondo"), theme.FONDOS["crema"])[1]


def main(page: ft.Page):
    page.window.width = 1280
    page.window.height = 820
    page.window.min_width = 960
    page.window.min_height = 640
    page.padding = 0
    page.spacing = 0

    def titulo():
        page.title = f"{configuracion_repo.club(forzar=True)['nombre']} — Sistema de Gestión"

    def mostrar_shell(role: str, seccion: str | None = None):
        page.clean()
        page.bgcolor = theme.CREAM
        shell = views.app_shell.AppShell(page, role, on_logout, on_recargar=lambda s: recargar(role, s))
        if seccion:
            shell.current_section = seccion
        page.add(shell.build())
        page.title = f"{configuracion_repo.club()['nombre']} — Sistema de Gestión"
        page.update()
        shell.actualizar_contador()

    def recargar(role: str, seccion: str):
        _recargar_modulos()
        mostrar_shell(role, seccion)

    def on_login(role: str):
        actual = empleados_credenciales.actual() or {}
        prefs = configuracion_repo.cargar_preferencias(actual.get("id_empleado"))
        configuracion_repo.recordar_usuario(actual.get("usuario") if prefs["recordar_usuario"] else None)
        titulo()
        if _apariencia_distinta():
            _recargar_modulos()
        mostrar_shell(role)

    def on_logout():
        empleados_credenciales.cerrar_sesion()
        # el login vuelve con la apariencia de siempre
        configuracion_repo.cargar_preferencias(None)
        if _apariencia_distinta():
            _recargar_modulos()
        page.clean()
        page.bgcolor = theme.CREAM
        login = sys.modules["views.login"].LoginView(page, on_login)
        page.add(login.build())
        page.update()

    titulo()
    page.bgcolor = theme.CREAM

    login = LoginView(page, on_login)
    page.add(login.build())
    page.update()


ft.run(main, assets_dir="img")
