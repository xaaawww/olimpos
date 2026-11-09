"""Carga en la base el catálogo de platos con imágenes de IA (platos_ia.py).

    python aplicar_platos_ia.py

Actualiza los platos que ya existen (por nombre, o por el nombre que tenían antes),
crea los que faltan y pasa a borrador los platos de demostración dibujados que ya no
se usan. Después hay que volver a exportar la página web (exportar_dietas_web.py).
"""
import base64
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "..", "Aplicaciones", "olimpos_gym"))
import neon_db  # noqa: E402
import platos_demo  # noqa: E402
import platos_ia  # noqa: E402


def aplicar() -> dict[str, int]:
    ids = {}
    for plato in platos_ia.PLATOS:
        p = platos_ia.datos(plato)
        with open(os.path.join(AQUI, "imagenes_ia", p["archivo"]), "rb") as f:
            imagen = base64.b64encode(f.read()).decode()
        kcal, prot, carbs, grasas = p["macros"]
        with neon_db.transaccion() as cur:
            cur.execute("SELECT id_plato FROM platos WHERE nombre = %s OR nombre = %s ORDER BY (nombre = %s) DESC LIMIT 1",
                        (p["nombre"], p["reemplaza"] or p["nombre"], p["nombre"]))
            fila = cur.fetchone()
            if fila:
                idp = fila["id_plato"]
                cur.execute("UPDATE platos SET nombre=%s, descripcion=%s, imagen=%s, imagen_generada_ia=TRUE, estado='publicado',"
                            " kcal=%s, proteinas=%s, carbs=%s, grasas=%s, fecha_actualizacion=now() WHERE id_plato=%s",
                            (p["nombre"], p["descripcion"], imagen, kcal, prot, carbs, grasas, idp))
                cur.execute("DELETE FROM platoetiquetas WHERE id_plato = %s", (idp,))
                cur.execute("DELETE FROM platoingredientes WHERE id_plato = %s", (idp,))
            else:
                cur.execute("INSERT INTO platos (nombre, descripcion, imagen, imagen_generada_ia, estado, kcal, proteinas, carbs, grasas, crop_x, crop_y)"
                            " VALUES (%s,%s,%s,TRUE,'publicado',%s,%s,%s,%s,0,0) RETURNING id_plato",
                            (p["nombre"], p["descripcion"], imagen, kcal, prot, carbs, grasas))
                idp = cur.fetchone()["id_plato"]
            for o, t in enumerate(p["tags"]):
                cur.execute("INSERT INTO platoetiquetas (id_plato, etiqueta, orden) VALUES (%s,%s,%s)", (idp, t, o))
            for q in p["puntos"]:
                cur.execute("INSERT INTO platoingredientes (id_plato, ingrediente_id, nombre, categoria, aporte, kcal_texto, x, y, orden)"
                            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (idp, q["id"], q["nombre"], q["categoria"], q["aporte"], q["kcal"], q["x"], q["y"], q["orden"]))
                for o, t in enumerate(q["etiquetas"]):
                    cur.execute("INSERT INTO ingredienteetiquetas (id_plato, ingrediente_id, etiqueta, orden) VALUES (%s,%s,%s,%s)", (idp, q["id"], t, o))
                for o, b in enumerate(q["beneficios"]):
                    cur.execute("INSERT INTO ingredientebeneficios (id_plato, ingrediente_id, beneficio, orden) VALUES (%s,%s,%s,%s)", (idp, q["id"], b, o))
        ids[p["nombre"]] = idp
        print(f"  {idp}: {p['nombre']}")
    usados = set(ids) | {p[2] for p in platos_ia.PLATOS if p[2]}
    viejos = [p[0] for p in platos_demo.PLATOS if p[0] not in usados]
    n = neon_db.ejecutar("UPDATE platos SET estado = 'borrador' WHERE nombre = ANY(%s) AND estado = 'publicado'", (viejos,))
    print(f"  {n} platos dibujados pasaron a borrador")
    return ids


if __name__ == "__main__":
    aplicar()
