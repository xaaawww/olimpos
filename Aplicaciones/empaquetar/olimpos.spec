# PyInstaller: arma OlimpOS.exe (ver construir.py).
# Se analizan los módulos del sistema para juntar todas las librerías que
# usan, pero después se SACAN del paquete: el código del sistema viaja como
# .py en la carpeta "sistema" (ver lanzador.py).
import os
import glob
from PyInstaller.utils.hooks import collect_all

AQUI = os.path.abspath(SPECPATH)
APP = os.path.abspath(os.path.join(AQUI, "..", "olimpos_gym"))

modulos_app = [os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(APP, "*.py"))]
modulos_app += ["views." + os.path.splitext(os.path.basename(p))[0]
                for p in glob.glob(os.path.join(APP, "views", "*.py")) if not p.endswith("__init__.py")]

datas, binaries, hidden = [], [], []
for paquete in ("flet", "flet_desktop", "firebase_admin", "psycopg", "certifi"):
    try:
        d, b, h = collect_all(paquete)
        datas += d; binaries += b; hidden += h
    except Exception:
        pass

a = Analysis(
    [os.path.join(AQUI, "lanzador.py")],
    pathex=[APP, os.path.join(APP, "views")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden + modulos_app,
    excludes=["tkinter", "matplotlib", "IPython", "pytest"],
    noarchive=False,
)

# Fuera los módulos del sistema: se usan los .py de la carpeta "sistema".
APP_N = os.path.normcase(APP)
a.pure = [t for t in a.pure if not os.path.normcase(str(t[1])).startswith(APP_N)]

pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="OlimpOS",
    icon=os.path.join(AQUI, "olimpos.ico"),
    console=False,
    version=os.path.join(AQUI, "version.txt"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="OlimpOS")
