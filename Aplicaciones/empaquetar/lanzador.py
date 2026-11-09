"""Lanzador de OlimpOS.exe.

El .exe trae adentro Python 3.12 y todas las librerías (flet, psycopg,
firebase_admin, ...), pero NO el código del sistema: ese queda como archivos
.py comunes en la carpeta "sistema" al lado del .exe, junto con las
credenciales, las imágenes y data/. Así el sistema funciona igual que con
abrir_sistema.bat (rutas relativas a cada archivo, recarga de pantallas al
cambiar la apariencia, sesión guardada en data/) y para actualizarlo alcanza
con volver a correr construir.py.

La ventana de Flet (flet.exe) también viene en la carpeta "cliente", así no
se descarga nada la primera vez.
"""
import os
import runpy
import sys
import traceback

BASE = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
SISTEMA = os.path.join(BASE, "sistema")
CLIENTE = os.path.join(BASE, "cliente", "flet")


def _avisar(titulo, texto):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, texto, titulo, 0x10)
    except Exception:
        pass


def main():
    if os.path.isfile(os.path.join(CLIENTE, "flet.exe")):
        os.environ["FLET_VIEW_PATH"] = CLIENTE
    os.chdir(SISTEMA)
    sys.path.insert(0, SISTEMA)
    sys.path.insert(1, os.path.join(SISTEMA, "views"))
    sys.argv = [os.path.join(SISTEMA, "main.py")]
    try:
        runpy.run_path(os.path.join(SISTEMA, "main.py"), run_name="__main__")
    except SystemExit:
        raise
    except Exception:
        detalle = traceback.format_exc()
        with open(os.path.join(BASE, "error.log"), "w", encoding="utf-8") as f:
            f.write(detalle)
        _avisar("OlimpOS", "El sistema se cerró por un error.\n\n"
                           f"El detalle quedó en:\n{os.path.join(BASE, 'error.log')}\n\n"
                           + detalle.strip().splitlines()[-1])


if __name__ == "__main__":
    main()
