"""Dibuja las imágenes de los platos de demostración (JPEG 700×700) con Edge sin ventana."""
import os, subprocess, sys
from PIL import Image
import platos_demo as pd

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SALIDA = sys.argv[1]
os.makedirs(SALIDA, exist_ok=True)
for i, p in enumerate(pd.PLATOS):
    svg, _ = pd.armar(i, p)
    html = os.path.join(SALIDA, f"{i:02d}.html")
    open(html, "w", encoding="utf-8").write(f"<html><body style='margin:0'>{svg}</body></html>")
    png = os.path.join(SALIDA, f"{i:02d}.png")
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--hide-scrollbars", "--window-size=700,700", f"--screenshot={png}",
                    "file:///" + html.replace("\\", "/")], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    Image.open(png).convert("RGB").save(os.path.join(SALIDA, f"{i:02d}.jpg"), quality=86)
    print(i, p[0])
