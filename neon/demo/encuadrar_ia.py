"""Achica las imágenes de IA para que el plato ocupe lo mismo que en las 3 originales
(≈82 % del cuadro, centrado) con margen blanco, y guarda cuánto se movió cada una en
imagenes_ia/ajustes.json para correr los puntos de los ingredientes igual.

    python encuadrar_ia.py
"""
import json, os
from PIL import Image
import platos_ia as pi

ORIG = r"C:\Users\sanch\OneDrive\Desktop\Prompts platos OlimpOS"
LADO, PLATO = 700, 0.82          # el plato de las originales mide ~82 % del cuadro
AQUI = os.path.dirname(os.path.abspath(__file__))


def caja(im):
    g = im.convert("L").point(lambda v: 255 if v < 235 else 0)
    return g.getbbox()


ajustes = {}
for dst, src in pi.ORIGENES.items():
    im = Image.open(os.path.join(ORIG, src)).convert("RGB")
    w, h = im.size
    x0, y0, x1, y1 = caja(im)
    cx, cy, diam = (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0)
    escala = PLATO * LADO / diam
    chica = im.resize((round(w * escala), round(h * escala)), Image.LANCZOS)
    lienzo = Image.new("RGB", (LADO, LADO), "white")
    ox, oy = round(LADO / 2 - cx * escala), round(LADO / 2 - cy * escala)
    lienzo.paste(chica, (ox, oy))
    lienzo.save(os.path.join(AQUI, "imagenes_ia", dst), quality=88)
    # un punto en (x %, y %) de la imagen original pasa a (ox + x/100·w·escala)/LADO
    ajustes[dst] = {"escala_x": w * escala / LADO, "escala_y": h * escala / LADO,
                    "dx": ox / LADO * 100, "dy": oy / LADO * 100}
json.dump(ajustes, open(os.path.join(AQUI, "imagenes_ia", "ajustes.json"), "w"), indent=1)
print(len(ajustes), "imágenes encuadradas")
