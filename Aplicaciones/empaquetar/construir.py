"""Arma la carpeta "OlimpOS - Sistema" con OlimpOS.exe y deja un acceso
directo en el escritorio.

    py -3.12 construir.py            # arma todo de cero
    py -3.12 construir.py --codigo   # solo actualiza el código del sistema (rápido)

Resultado (fuera de git, en el escritorio):
    OlimpOS - Sistema/
        OlimpOS.exe      ← doble clic
        _internal/       Python 3.12 + librerías
        sistema/         el código (.py), img/, data/ y las credenciales
        cliente/flet/    la ventana de Flet
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
APP = AQUI.parent / "olimpos_gym"
ESCRITORIO = Path(os.environ["USERPROFILE"]) / "OneDrive" / "Desktop"
if not ESCRITORIO.exists():
    ESCRITORIO = Path(os.environ["USERPROFILE"]) / "Desktop"
DESTINO = ESCRITORIO / "OlimpOS - Sistema"
IGNORAR = shutil.ignore_patterns("__pycache__", "*.pyc", "usuarios_y_contraseñas.txt", "openai_credentials.json")


def copiar_codigo():
    """Copia el sistema (código, imágenes, credenciales). data/ se conserva si
    ya existía: ahí está la sesión guardada y la apariencia elegida."""
    sistema = DESTINO / "sistema"
    data_vieja = None
    if (sistema / "data").exists():
        data_vieja = DESTINO / "_data_tmp"
        shutil.rmtree(data_vieja, ignore_errors=True)
        shutil.copytree(sistema / "data", data_vieja)
    shutil.rmtree(sistema, ignore_errors=True)
    shutil.copytree(APP, sistema, ignore=IGNORAR)
    if data_vieja:
        shutil.rmtree(sistema / "data", ignore_errors=True)
        shutil.move(str(data_vieja), sistema / "data")
    shutil.copy2(AQUI / "olimpos.ico", sistema / "olimpos.ico")


def copiar_cliente():
    import flet_desktop.version
    cache = Path.home() / ".flet" / "client" / f"flet-desktop-full-{flet_desktop.version.version}" / "flet"
    if not (cache / "flet.exe").exists():
        import flet_desktop
        cache = flet_desktop.ensure_client_cached() / "flet"
    shutil.rmtree(DESTINO / "cliente", ignore_errors=True)
    shutil.copytree(cache, DESTINO / "cliente" / "flet")


def acceso_directo():
    lnk = ESCRITORIO / "OlimpOS.lnk"
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
          f"$s.TargetPath='{DESTINO / 'OlimpOS.exe'}';$s.WorkingDirectory='{DESTINO}';"
          f"$s.IconLocation='{DESTINO / 'OlimpOS.exe'},0';$s.Description='OlimpOS - Sistema de empleados';$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def main():
    if "--codigo" in sys.argv:
        copiar_codigo()
        print("Código actualizado en", DESTINO)
        return
    trabajo = AQUI / "build"
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--distpath", str(trabajo / "dist"), "--workpath", str(trabajo / "work"),
                    str(AQUI / "olimpos.spec")], check=True)
    DESTINO.mkdir(exist_ok=True)
    for viejo in ("OlimpOS.exe", "_internal"):
        p = DESTINO / viejo
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    shutil.copy2(trabajo / "dist" / "OlimpOS" / "OlimpOS.exe", DESTINO / "OlimpOS.exe")
    shutil.copytree(trabajo / "dist" / "OlimpOS" / "_internal", DESTINO / "_internal")
    copiar_codigo()
    copiar_cliente()
    acceso_directo()
    print("Listo:", DESTINO / "OlimpOS.exe")


if __name__ == "__main__":
    main()
