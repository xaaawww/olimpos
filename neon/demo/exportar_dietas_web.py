"""Exporta los platos publicados de la base a la página web "Dieta Saludable".

    python exportar_dietas_web.py

Guarda cada imagen en Paginas/assets/platos/<id>.jpg y los datos (ingredientes con
su posición, kcal, aporte, etiquetas y beneficios) en Paginas/assets/platos/platos.js.
La página es pública y la API pide login, por eso los datos se copian acá en vez de
pedirlos en vivo: hay que volver a correrlo cuando se agregan o cambian platos.
"""
import base64
import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "Aplicaciones", "olimpos_gym"))
import neon_db  # noqa: E402

SALIDA = os.path.join(AQUI, "..", "..", "Paginas", "assets", "platos")
# En la página el plato es un círculo de 300 px con la imagen al 112 %: un punto en
# x % de la imagen queda a (x - 50) / 100 × 336 px del centro.
ESCALA_PX = 300 * 1.12 / 100


def main():
    os.makedirs(SALIDA, exist_ok=True)
    platos = neon_db.consulta(
        "SELECT id_plato, nombre, descripcion, imagen, kcal, proteinas, carbs, grasas FROM platos"
        " WHERE estado = 'publicado' AND imagen IS NOT NULL AND imagen <> '' ORDER BY id_plato")
    ing = neon_db.consulta("SELECT * FROM platoingredientes ORDER BY id_plato, orden")
    etq = neon_db.consulta("SELECT * FROM ingredienteetiquetas ORDER BY id_plato, ingrediente_id, orden")
    ben = neon_db.consulta("SELECT * FROM ingredientebeneficios ORDER BY id_plato, ingrediente_id, orden")
    salida = []
    for p in platos:
        archivo = f"{p['id_plato']}.jpg"
        with open(os.path.join(SALIDA, archivo), "wb") as f:
            f.write(base64.b64decode(p["imagen"]))
        items = []
        for i in (x for x in ing if x["id_plato"] == p["id_plato"]):
            dx, dy = (i["x"] - 50) * ESCALA_PX, (i["y"] - 50) * ESCALA_PX
            rad = math.hypot(dx, dy)
            clave = (p["id_plato"], i["ingrediente_id"])
            items.append({
                "name": i["nombre"], "cat": i["categoria"], "kcal": i["kcal_texto"], "aporte": i["aporte"],
                "angle": round(math.degrees(math.atan2(dy, dx)) % 360) if rad > 8 else 270,
                "rad": round(rad) if rad > 8 else 0,
                "tags": [e["etiqueta"] for e in etq if (e["id_plato"], e["ingrediente_id"]) == clave],
                "beneficios": [b["beneficio"] for b in ben if (b["id_plato"], b["ingrediente_id"]) == clave],
            })
        if items:
            salida.append({"id": p["id_plato"], "tab": p["nombre"], "name": p["nombre"], "desc": p["descripcion"] or "",
                           "img": f"assets/platos/{archivo}", "macros": [p["kcal"], p["proteinas"], p["carbs"], p["grasas"]],
                           "items": items})
    with open(os.path.join(SALIDA, "platos.js"), "w", encoding="utf-8") as f:
        f.write("// Generado por neon/demo/exportar_dietas_web.py — no editar a mano.\n")
        f.write("window.PLATOS_WEB = " + json.dumps(salida, ensure_ascii=False, indent=1) + ";\n")
    print(len(salida), "platos exportados")


if __name__ == "__main__":
    main()
