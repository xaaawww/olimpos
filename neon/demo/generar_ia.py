"""Genera con OpenAI (gpt-image-1) las imágenes de los platos de demostración, con el
mismo estilo que las 3 primeras del catálogo. Usa la imagen del plato de atún como
referencia de estilo y pide cada ingrediente en una zona fija del plato, así los
puntos interactivos caen encima del ingrediente.

    python generar_ia.py <carpeta_salida> [índices...]
"""
import base64, json, os, sys
import requests

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "..", "Aplicaciones", "olimpos_gym"))
import neon_db  # noqa: E402
import platos_demo as pd  # noqa: E402

CRED = os.path.join(AQUI, "..", "..", "Aplicaciones", "olimpos_gym", "openai_credentials.json")
ZONAS = {4: ["arriba a la izquierda", "arriba a la derecha", "abajo a la derecha", "abajo a la izquierda"],
         3: ["arriba a la izquierda", "arriba a la derecha", "abajo, en el centro"]}

ESTILO = (
    "Ilustración de comida con el MISMO estilo exacto que la imagen de referencia: dibujo digital detallado y prolijo, "
    "vista cenital (desde arriba), un plato blanco circular centrado que ocupa casi todo el cuadro, fondo blanco liso, "
    "contornos finos, sombreado suave, colores vivos y naturales, hojitas de perejil sueltas sobre el borde del plato. "
    "Sin texto, sin números, sin marcas de agua, sin manos, sin cubiertos. "
    "Cada ingrediente ocupa SOLO su zona del plato, bien separado de los demás, porciones abundantes que llenan la zona. "
)


def prompt(plato):
    nombre, _, _, zonas, centro, _ = plato
    partes = [f"{pd.ING[k][0]} {donde}" for k, donde in zip(zonas, ZONAS[len(zonas)])]
    txt = ESTILO + f"Plato: {nombre}. Distribución: " + "; ".join(partes) + "."
    if centro:
        txt += f" En el centro exacto del plato, un bowl blanco pequeño con {pd.ING[centro][0].lower()}."
    else:
        txt += " El centro del plato queda donde se juntan las cuatro zonas, sin bowl."
    return txt


def main():
    salida = sys.argv[1]
    os.makedirs(salida, exist_ok=True)
    indices = [int(x) for x in sys.argv[2:]] or range(len(pd.PLATOS))
    key = json.load(open(CRED))["api_key"]
    ref = base64.b64decode(neon_db.una_fila("SELECT imagen FROM platos WHERE id_plato = 1")["imagen"])
    for i in indices:
        destino = os.path.join(salida, f"{i:02d}.png")
        if os.path.exists(destino):
            continue
        r = requests.post("https://api.openai.com/v1/images/edits", headers={"Authorization": f"Bearer {key}"},
                          files={"image[]": ("referencia.jpg", ref, "image/jpeg")},
                          data={"model": "gpt-image-1", "prompt": prompt(pd.PLATOS[i]), "size": "1024x1024", "quality": "medium", "n": "1"},
                          timeout=300)
        if r.status_code != 200:
            print(i, "ERROR", r.status_code, r.text[:300]); continue
        open(destino, "wb").write(base64.b64decode(r.json()["data"][0]["b64_json"]))
        print(i, pd.PLATOS[i][0], flush=True)


if __name__ == "__main__":
    main()
