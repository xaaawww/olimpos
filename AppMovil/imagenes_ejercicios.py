# Copia los dibujos de los ejercicios del sistema de empleados a la app movil.
#
# El sistema de empleados guarda cada dibujo como
#   Aplicaciones/olimpos_gym/img/ejercicios/<id_ejercicio>.png
# (lo cambia el boton "Cambiar imagen" del editor de ejercicios). La app no
# puede leer esa carpeta, asi que este script los comprime (WebP 256 px, unos
# pocos KB cada uno) dentro de app/src/main/res/drawable-nodpi/ y genera
# ImagenesEjercicios.kt con la tabla id -> dibujo.
#
# Los ejercicios de la Calculadora/Arena (estado "competencia") no tienen
# dibujo propio: usan el del ejercicio publicado con el mismo nombre.
#
# Volver a correrlo (y recompilar la app) cada vez que se cambie un dibujo:
#     py -3.12 AppMovil\imagenes_ejercicios.py

import os
import re
import sys
import unicodedata

from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMPLEADOS = os.path.join(RAIZ, "Aplicaciones", "olimpos_gym")
ORIGEN = os.path.join(EMPLEADOS, "img", "ejercicios")
DESTINO = os.path.join(RAIZ, "AppMovil", "app", "src", "main", "res", "drawable-nodpi")
KOTLIN = os.path.join(RAIZ, "AppMovil", "app", "src", "main", "java", "com", "olimpos", "gym", "data", "ImagenesEjercicios.kt")

sys.path.insert(0, EMPLEADOS)
import neon_db  # noqa: E402  (mismas credenciales que el sistema de empleados)


def clave(nombre: str) -> str:
    """"Press de banca" y "Press banca" -> "press banca" (sin tildes, sin
    parentesis ni palabras de relleno), para emparejar los de la Calculadora."""
    s = unicodedata.normalize("NFD", nombre.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\(.*?\)", " ", s)
    palabras = [p for p in re.findall(r"[a-z0-9]+", s) if p not in ("de", "con", "en", "la", "el")]
    return " ".join(palabras)


def main():
    filas = neon_db.consulta("SELECT id_ejercicio, nombre, estado FROM ejercicios ORDER BY id_ejercicio")
    con_dibujo = [f for f in filas if os.path.exists(os.path.join(ORIGEN, f"{f['id_ejercicio']}.png"))]

    os.makedirs(DESTINO, exist_ok=True)
    for viejo in os.listdir(DESTINO):
        if re.fullmatch(r"ej_\d+\.webp", viejo):
            os.remove(os.path.join(DESTINO, viejo))
    for f in con_dibujo:
        im = Image.open(os.path.join(ORIGEN, f"{f['id_ejercicio']}.png")).convert("RGB")
        im.resize((256, 256), Image.LANCZOS).save(os.path.join(DESTINO, f"ej_{f['id_ejercicio']}.webp"), "WEBP", quality=82)

    por_id = {str(f["id_ejercicio"]): f"ej_{f['id_ejercicio']}" for f in con_dibujo}
    por_nombre = {}
    for f in con_dibujo:
        por_nombre.setdefault(clave(f["nombre"]), por_id[str(f["id_ejercicio"])])

    lineas_id = "\n".join(f'    "{i}" to R.drawable.{d},' for i, d in por_id.items())
    lineas_nombre = "\n".join(f'    "{k}" to R.drawable.{d},' for k, d in sorted(por_nombre.items()))
    with open(KOTLIN, "w", encoding="utf-8", newline="\n") as salida:
        salida.write(f"""package com.olimpos.gym.data

import com.olimpos.gym.R

/* GENERADO por AppMovil/imagenes_ejercicios.py — no editar a mano.
   Dibujos de los ejercicios, los mismos del sistema de empleados. */

private val POR_ID: Map<String, Int> = mapOf(
{lineas_id}
)

private val POR_NOMBRE: Map<String, Int> = mapOf(
{lineas_nombre}
)

private fun claveNombre(nombre: String): String {{
    val sinTildes = java.text.Normalizer.normalize(nombre.lowercase(), java.text.Normalizer.Form.NFD)
        .replace(Regex("\\\\p{{Mn}}+"), "")
        .replace(Regex("\\\\(.*?\\\\)"), " ")
    return Regex("[a-z0-9]+").findAll(sinTildes).map {{ it.value }}
        .filter {{ it !in setOf("de", "con", "en", "la", "el") }}.joinToString(" ")
}}

/** Dibujo del ejercicio: por id del catálogo, o si no por nombre (los de la
 *  Calculadora, que comparten nombre con uno publicado). `null` si no tiene. */
fun imagenDeEjercicio(id: String? = null, nombre: String? = null): Int? =
    id?.let {{ POR_ID[it] }} ?: nombre?.let {{ POR_NOMBRE[claveNombre(it)] }}
""")
    total = sum(os.path.getsize(os.path.join(DESTINO, f"{d}.webp")) for d in por_id.values())
    print(f"{len(por_id)} dibujos copiados ({total // 1024} KB en total)")
    sin = [f["nombre"] for f in filas if f["estado"] == "competencia" and clave(f["nombre"]) not in por_nombre]
    if sin:
        print("Sin dibujo en la Calculadora:", ", ".join(sin))


if __name__ == "__main__":
    main()
