"""Catálogo final de platos de demostración, con las imágenes generadas con IA.

Cada plato usa una imagen de imagenes_ia/ y ubica cada ingrediente (x, y en % de la
imagen) donde aparece en el dibujo. Cuando la imagen salió distinta a la receta
pedida, el plato se ajustó a lo que muestra la imagen. "reemplaza" es el nombre que
tenía el plato antes, para actualizar esa misma fila en vez de crear otra.
"""
import json
import os

from platos_demo import ING

# Las coordenadas de PLATOS están medidas sobre la imagen original de ChatGPT; al
# encuadrarla con margen blanco (encuadrar_ia.py) los puntos se corren igual.
_AJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagenes_ia", "ajustes.json")
AJUSTES = json.load(open(_AJ)) if os.path.exists(_AJ) else {}

# (archivo, nombre, reemplaza, descripción, etiquetas, momento, [(ingrediente, x, y), ...], (centro, x, y) o None)
PLATOS = [
    # ── desayunos ──
    ("avena.jpg", "Bowl de avena con frutos rojos", None,
     "Avena cremosa con frutillas, arándanos y banana: energía que dura toda la mañana.",
     ["Energía", "Fibra", "Desayuno"], "desayuno",
     [("avena", 29, 29), ("frutillas", 73, 31), ("arandanos", 69, 69), ("banana", 31, 69)], ("miel", 50, 47)),
    ("tostadas_palta.jpg", "Tostadas con palta y huevo", None,
     "El desayuno completo: tostadas integrales con palta, huevo, tomates y espinaca.",
     ["Saciante", "Grasas buenas", "Desayuno"], "desayuno",
     [("tostada_palta", 37, 31), ("huevo_duro", 79, 35), ("tomate_cherry", 75, 69), ("espinaca", 31, 69)], None),
    ("yogur_granola.jpg", "Yogur griego con granola", None,
     "Yogur alto en proteína con granola crocante, kiwi y almendras.",
     ["Alta proteína", "Probióticos", "Desayuno"], "desayuno",
     [("yogur", 31, 29), ("granola", 77, 27), ("kiwi", 69, 69), ("almendras", 27, 62)], ("miel", 50, 50)),
    ("tropical.jpg", "Bowl tropical de yogur", None,
     "Yogur griego con banana, kiwi y naranja: vitamina C y proteína.",
     ["Vitamina C", "Alta proteína", "Fresco"], "desayuno",
     [("yogur", 31, 24), ("banana", 73, 26), ("kiwi", 74, 67), ("naranja", 31, 64)], ("miel", 50, 46)),
    ("yogur_frutos_rojos.jpg", "Yogur con granola y frutos rojos", None,
     "Yogur con granola, kiwi, frutillas y arándanos: antioxidantes y proteína para arrancar.",
     ["Antioxidantes", "Proteína", "Desayuno"], "desayuno",
     [("yogur", 25, 22), ("granola", 73, 26), ("kiwi", 73, 59), ("frutillas", 17, 53), ("arandanos", 37, 68)], ("miel", 50, 46)),
    ("yogur_banana.jpg", "Yogur con banana y frutillas", None,
     "Yogur con arándanos, frutillas, granola y banana: un desayuno dulce y completo.",
     ["Energía", "Probióticos", "Desayuno"], "desayuno",
     [("yogur", 31, 22), ("frutillas", 71, 28), ("granola", 71, 64), ("banana", 31, 68)], ("miel", 50, 46)),
    ("cottage.jpg", "Cottage con frutas y nueces", None,
     "Queso cottage con manzana, arándanos y nueces: proteína lenta y antioxidantes.",
     ["Recuperación", "Antioxidantes", "Liviano"], "desayuno",
     [("cottage", 27, 24), ("manzana", 73, 28), ("arandanos", 71, 64), ("nueces", 31, 64)], ("miel", 50, 45)),
    ("panqueques.jpg", "Panqueques de avena", None,
     "Panqueques sin harina con frutillas, banana, nueces y mantequilla de maní.",
     ["Pre-entreno", "Energía", "Volumen"], "desayuno",
     [("panqueques", 29, 32), ("frutillas", 71, 28), ("banana", 71, 66), ("nueces", 31, 70)], ("mani", 50, 46)),
    ("huevos_frutas.jpg", "Huevos con frutas", None,
     "Huevos duros con tostadas integrales, naranja y kiwi: simple, rápido y completo.",
     ["Práctico", "Proteína", "Vitamina C"], "desayuno",
     [("huevo_duro", 31, 28), ("naranja", 71, 32), ("kiwi", 73, 66), ("tostadas", 31, 64)], None),
    # ── almuerzos ──
    ("pollo_arroz.jpg", "Pollo grillado con arroz", None,
     "El clásico del gimnasio: pollo grillado con arroz integral, brócoli y batata.",
     ["Volumen", "Alta proteína", "Post-entreno"], "almuerzo",
     [("pollo", 31, 28), ("arroz_integral", 71, 28), ("brocoli", 71, 66), ("batata", 31, 66)], None),
    ("salmon_quinoa.jpg", "Salmón con quinoa y chauchas", "Salmón con quinoa y palta",
     "Salmón grillado con quinoa, chauchas y ensalada fresca: omega-3 y proteína completa.",
     ["Recuperación", "Omega-3", "Energía"], "almuerzo",
     [("salmon", 31, 28), ("quinoa", 71, 28), ("chauchas", 73, 66), ("ensalada", 31, 66)], None),
    ("tofu_arroz.jpg", "Tofu salteado con arroz", None,
     "Tofu dorado con arroz integral, morrones y brócoli.",
     ["Vegano", "Proteína vegetal", "Fibra"], "almuerzo",
     [("tofu", 31, 28), ("arroz_integral", 71, 28), ("brocoli", 69, 66), ("morron", 29, 66)], None),
    ("fideos_langostinos.jpg", "Fideos con langostinos", None,
     "Fideos integrales con langostinos, zapallitos grillados y champiñones, con salsa de tomate.",
     ["Energía", "Proteína magra", "Pre-entreno"], "almuerzo",
     [("fideos", 29, 26), ("langostinos", 71, 28), ("zapallito", 73, 70), ("champinones", 31, 66)], ("salsa_tomate", 50, 44)),
    ("lentejas.jpg", "Bowl de lentejas", None,
     "Lentejas con arroz integral, espinaca y batata: proteína vegetal completa.",
     ["Vegetariano", "Hierro", "Fibra"], "almuerzo",
     [("lentejas", 29, 26), ("arroz_integral", 73, 26), ("espinaca", 71, 64), ("batata", 29, 66)], ("salsa_yogur", 50, 46)),
    ("garbanzos_quinoa.jpg", "Bowl vegano de quinoa", None,
     "Quinoa con garbanzos especiados, palta y tomates con rúcula.",
     ["Vegano", "Fibra", "Saciante"], "almuerzo",
     [("garbanzos", 31, 26), ("quinoa", 73, 26), ("tomate_cherry", 69, 64), ("palta", 31, 64)], None),
    # ── cenas ──
    ("pollo_pepino.jpg", "Pollo con quinoa y pepino", None,
     "Pollo grillado con quinoa, tomates cherry y pepino, con salsa de yogur.",
     ["Definición", "Alta proteína", "Liviano"], "cena",
     [("pollo", 29, 28), ("quinoa", 71, 28), ("tomate_cherry", 71, 61), ("pepino", 31, 66)], ("salsa_yogur", 50, 47)),
    ("pollo_palta.jpg", "Pollo con quinoa y palta", None,
     "Pollo grillado con quinoa, palta y ensalada fresca, con aceite de oliva.",
     ["Grasas buenas", "Alta proteína", "Cena"], "cena",
     [("quinoa", 29, 24), ("palta", 71, 26), ("pollo", 71, 66), ("ensalada", 29, 64)], ("aceite", 50, 47)),
    ("pollo_esparragos.jpg", "Pollo con quinoa y espárragos", None,
     "Pollo grillado con quinoa con verduras, espárragos y batata asada.",
     ["Recuperación", "Alta proteína", "Cena"], "cena",
     [("pollo", 29, 28), ("quinoa", 71, 28), ("esparragos", 71, 66), ("batata", 29, 66)], ("salsa_yogur", 50, 44)),
]

# imagen de la carpeta "Prompts platos OlimpOS" → archivo de imagenes_ia/
ORIGENES = {
    "avena.jpg": "00.png", "tostadas_palta.jpg": "01.png", "yogur_granola.jpg": "02.png",
    "tropical.jpg": "Desayuno Tropical con Miel y Frutas-2.png",
    "yogur_frutos_rojos.jpg": "Desayuno colorido con miel y frutas-3.png",
    "yogur_banana.jpg": "Desayuno colorido con yogur y frutas-1.png",
    "cottage.jpg": "Desayuno nutritivo con miel y frutas.png",
    "panqueques.jpg": "Desayuno saludable con pancakes y fruta-4.png",
    "huevos_frutas.jpg": "Plato saludable con huevos, frutas y tostadas.png",
    "pollo_arroz.jpg": "Plato saludable de pollo y verduras-2.png",
    "salmon_quinoa.jpg": "Plato colorido de salmón y quinoa.png",
    "tofu_arroz.jpg": "Plato de tofu, arroz y verduras.png",
    "fideos_langostinos.jpg": "Plato gourmet de pasta, camarones y verduras.png",
    "lentejas.jpg": "Plato saludable de lentejas y espinaca.png",
    "garbanzos_quinoa.jpg": "Plato colorido de garbanzos y aguacate.png",
    "pollo_pepino.jpg": "Plato Saludable de Pollo y Quinoa-1.png",
    "pollo_palta.jpg": "Plato equilibrado con pollo, quinoa y aguacate.png",
    "pollo_esparragos.jpg": "Plato saludable de pollo y quinoa.png",
}


def slug(texto):
    return "punto_" + texto.lower().translate(str.maketrans("áéíóúñü ", "aeiounu_"))


def datos(plato):
    """Macros y puntos de un plato, con los datos de cada ingrediente."""
    archivo, nombre, reemplaza, desc, tags, momento, zonas, centro = plato
    items = zonas + ([centro] if centro else [])
    macros = [sum(ING[k][2][j] for k, _, _ in items) for j in range(4)]
    puntos = []
    aj = AJUSTES.get(archivo, {"escala_x": 1, "escala_y": 1, "dx": 0, "dy": 0})
    for orden, (k, x, y) in enumerate(items):
        x, y = round(aj["dx"] + x * aj["escala_x"], 1), round(aj["dy"] + y * aj["escala_y"], 1)
        nom, cat, (kcal, *_), aporte, ben, etq, _ = ING[k]
        puntos.append({"id": slug(nom), "nombre": nom, "categoria": cat, "aporte": aporte, "kcal": f"{kcal} kcal",
                       "x": float(x), "y": float(y), "orden": orden, "beneficios": ben, "etiquetas": etq})
    return {"archivo": archivo, "nombre": nombre, "reemplaza": reemplaza, "descripcion": desc, "tags": tags,
            "momento": momento, "macros": macros, "puntos": puntos}
