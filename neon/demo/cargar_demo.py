"""Carga los datos de demostración de OlimpOS.

    python cargar_demo.py            carga el catálogo de platos y los 10 usuarios de prueba
    python cargar_demo.py --borrar   borra los 10 usuarios de prueba (Firebase y base)

Usuarios: prueba1@gmail.com … prueba10@gmail.com, con contraseña prueba1 … prueba10.
Cada uno queda con membresía y pagos, rutinas, series de entrenamiento de las últimas
semanas, marcas verificadas, ingresos al club, dieta asignada, comidas registradas,
agua, peso, compañeros, reservas de clases y pedidos en la tienda.

Usa las credenciales del sistema de empleados (Aplicaciones/olimpos_gym): no guarda
ninguna clave acá. Se puede correr varias veces: lo que ya existe no se duplica.
"""
import base64
import io
import json
import os
import random
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
SISTEMA = os.path.join(AQUI, "..", "..", "Aplicaciones", "olimpos_gym")
sys.path.insert(0, SISTEMA)
sys.path.insert(0, AQUI)

from firebase_admin import auth as fb_auth  # noqa: E402
from PIL import Image  # noqa: E402

import auth_repo  # noqa: E402
import neon_db  # noqa: E402
import platos_demo as pd  # noqa: E402

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
AR = timezone(timedelta(hours=-3))
HOY = datetime.now(AR).date()
ENTRENADOR, NUTRICIONISTA = 9, 10       # id_empleado
FIRMA_ENTRENADOR = "Entrenador OlimpOS — Entrenador"

USUARIOS = [
    # nombre, apellido, sexo, edad, peso, objetivo, nivel, plan, fuerza (0..1)
    ("Lucía", "Fernández", "FEMENINO", 24, 61, "HIPERTROFIA", "Intermedio", "Oro", .45),
    ("Martín", "Gómez", "MASCULINO", 28, 82, "FUERZA", "Avanzado", "Platino", .62),
    ("Sofía", "Romero", "FEMENINO", 31, 58, "SALUD", "Principiante", "Bronce", .22),
    ("Tomás", "Álvarez", "MASCULINO", 22, 76, "HIPERTROFIA", "Intermedio", "Oro", .5),
    ("Valentina", "Torres", "FEMENINO", 27, 65, "FUERZA", "Avanzado", "Platino", .58),
    ("Nicolás", "Ruiz", "MASCULINO", 35, 90, "SALUD", "Principiante", "Oro", .28),
    ("Camila", "Díaz", "FEMENINO", 20, 55, "HIPERTROFIA", "Intermedio", "Platino", .4),
    ("Joaquín", "Acosta", "MASCULINO", 30, 85, "FUERZA", "Avanzado", "Platino", .7),
    ("Micaela", "Benítez", "FEMENINO", 26, 63, "SALUD", "Intermedio", "Oro", .33),
    ("Facundo", "Medina", "MASCULINO", 19, 72, "HIPERTROFIA", "Principiante", "Bronce", .3),
]

# Rutinas por objetivo: (nombre, [(ejercicio, series, peso relativo al peso corporal, es_peso_corporal)])
RUTINAS = {
    "FUERZA": [
        ("Fuerza · Piernas y espalda", [("Sentadilla", 5, 1.1, False), ("Peso muerto", 4, 1.3, False), ("Remo con barra", 4, .7, False),
                                         ("Dominadas", 4, 0, True), ("Elevación de talones", 3, .9, False), ("Crunch abdominal", 3, 0, True)]),
        ("Fuerza · Empuje", [("Press de banca", 5, .85, False), ("Press militar con barra", 4, .5, False), ("Fondos en paralelas", 3, 0, True),
                             ("Press inclinado con mancuernas", 3, .3, False), ("Extensión de tríceps en polea", 3, .3, False)]),
    ],
    "HIPERTROFIA": [
        ("Torso · Hipertrofia", [("Press de banca", 4, .65, False), ("Remo con barra", 4, .55, False), ("Press inclinado con mancuernas", 3, .25, False),
                                 ("Elevaciones laterales", 4, .1, False), ("Curl de bíceps con barra", 3, .3, False), ("Extensión de tríceps en polea", 3, .28, False)]),
        ("Piernas · Hipertrofia", [("Sentadilla", 4, .85, False), ("Peso muerto rumano", 4, .75, False), ("Hip thrust", 4, 1.0, False),
                                   ("Extensión de cuádriceps", 3, .45, False), ("Curl femoral", 3, .35, False), ("Elevación de talones", 4, .7, False)]),
    ],
    "SALUD": [
        ("Cuerpo completo", [("Sentadilla", 3, .5, False), ("Press de banca", 3, .4, False), ("Remo con barra", 3, .35, False),
                             ("Zancadas", 3, .2, False), ("Face pull", 3, .2, False), ("Giro ruso", 3, 0, True)]),
        ("Movilidad y core", [("Hip thrust", 3, .6, False), ("Abducción de cadera en máquina", 3, .4, False), ("Aducción de cadera en máquina", 3, .4, False),
                              ("Crunch abdominal", 3, 0, True), ("Pájaros (aperturas posteriores)", 3, .06, False)]),
    ],
}

# Marcas de la Calculadora (nombre en ejercicios / ejerciciosmarca)
MARCAS = ["Sentadilla", "Press banca", "Peso muerto", "Dominadas", "Flexiones", "Elevaciones laterales", "Pájaros", "Elevación de talones"]

TABLON = [
    ("¡Nuevas clases de funcional!", "Desde el lunes sumamos funcional los martes y jueves a las 19 h en la Sala 2. Cupo de 15 personas: reservá desde la app.", "Evento", True),
    ("Horario especial por el feriado", "El lunes 24 abrimos de 9 a 14 h. El resto de la semana, horario normal.", "Importante", False),
    ("2x1 en proteína whey", "Toda la semana, llevando dos potes de proteína en la tienda del club pagás uno. Pedilo desde la app y retiralo en recepción.", "Promoción", False),
    ("Desafío Olimpo de noviembre", "Quien sume más marcas verificadas este mes gana un mes de plan Platino. Mirá tu posición en la Escalera del Olimpo.", "Evento", False),
    ("Mantenimiento de la sala de cardio", "El miércoles de 7 a 10 h se revisan las cintas. Mientras tanto, usá las bicicletas y los remos del piso 2.", "Aviso", False),
]


def ts(d: date, hora: int, minuto: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hora, minuto, tzinfo=AR)


def semana_iso(d: date) -> str:
    a, s, _ = d.isocalendar()
    return f"{a}-W{s}"


# ───────────────────────── platos ─────────────────────────

def imagen_plato(svg: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        html, png = os.path.join(tmp, "p.html"), os.path.join(tmp, "p.png")
        open(html, "w", encoding="utf-8").write(f"<html><body style='margin:0'>{svg}</body></html>")
        subprocess.run([EDGE, "--headless", "--disable-gpu", "--hide-scrollbars", "--window-size=700,700",
                        f"--user-data-dir={os.path.join(tmp, 'edge')}", f"--screenshot={png}", "file:///" + html.replace("\\", "/")],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        buf = io.BytesIO()
        Image.open(png).convert("RGB").save(buf, format="JPEG", quality=86)
    return base64.b64encode(buf.getvalue()).decode()


def cargar_platos() -> dict[str, int]:
    """Devuelve {nombre del plato: id_plato} de los platos de demostración."""
    ids = {}
    for i, plato in enumerate(pd.PLATOS):
        svg, p = pd.armar(i, plato)
        fila = neon_db.una_fila("SELECT id_plato FROM platos WHERE nombre = %s", (p["nombre"],))
        if fila:
            ids[p["nombre"]] = fila["id_plato"]
            continue
        imagen = imagen_plato(svg)
        kcal, prot, carbs, grasas = p["macros"]
        with neon_db.transaccion() as cur:
            cur.execute(
                "INSERT INTO platos (nombre, descripcion, imagen, imagen_generada_ia, estado, kcal, proteinas, carbs, grasas, crop_x, crop_y)"
                " VALUES (%s,%s,%s,FALSE,'publicado',%s,%s,%s,%s,0,0) RETURNING id_plato",
                (p["nombre"], p["descripcion"], imagen, kcal, prot, carbs, grasas))
            idp = cur.fetchone()["id_plato"]
            for o, t in enumerate(p["tags"]):
                cur.execute("INSERT INTO platoetiquetas (id_plato, etiqueta, orden) VALUES (%s,%s,%s)", (idp, t, o))
            for q in p["puntos"]:
                cur.execute(
                    "INSERT INTO platoingredientes (id_plato, ingrediente_id, nombre, categoria, aporte, kcal_texto, x, y, orden)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (idp, q["id"], q["nombre"], q["categoria"], q["aporte"], q["kcal"], q["x"], q["y"], q["orden"]))
                for o, t in enumerate(q["etiquetas"]):
                    cur.execute("INSERT INTO ingredienteetiquetas (id_plato, ingrediente_id, etiqueta, orden) VALUES (%s,%s,%s,%s)",
                                (idp, q["id"], t, o))
                for o, b in enumerate(q["beneficios"]):
                    cur.execute("INSERT INTO ingredientebeneficios (id_plato, ingrediente_id, beneficio, orden) VALUES (%s,%s,%s,%s)",
                                (idp, q["id"], b, o))
        ids[p["nombre"]] = idp
        print(f"  plato {idp}: {p['nombre']}")
    return ids


def cargar_tablon():
    for i, (titulo, mensaje, cat, fijado) in enumerate(TABLON):
        if neon_db.una_fila("SELECT 1 FROM tablonpublicaciones WHERE titulo = %s", (titulo,)):
            continue
        cuando = datetime.now(AR) - timedelta(days=i * 2 + 1, hours=3)
        neon_db.ejecutar(
            "INSERT INTO tablonpublicaciones (titulo, mensaje, categoria, autor, fijado, publicado, fecha_creacion, fecha_actualizacion)"
            " VALUES (%s,%s,%s,'Dueño OlimpOS',%s,TRUE,%s,%s)", (titulo, mensaje, cat, fijado, cuando, cuando))


# ───────────────────────── usuarios ─────────────────────────

def usuario_firebase(email: str, password: str, nombre: str) -> str:
    app = auth_repo._app()
    try:
        u = fb_auth.get_user_by_email(email, app=app)
        fb_auth.update_user(u.uid, password=password, display_name=nombre, disabled=False, app=app)
        return u.uid
    except fb_auth.UserNotFoundError:
        return fb_auth.create_user(email=email, password=password, display_name=nombre, app=app).uid


def cargar_usuario(n: int, datos, platos: dict[str, int], ejercicios: dict[str, int], productos: list[dict]) -> int:
    nombre, apellido, sexo, edad, peso, objetivo, nivel, plan, fuerza = datos
    rng = random.Random(n * 7919)
    email, password = f"prueba{n}@gmail.com", f"prueba{n}"
    uid = usuario_firebase(email, password, f"{nombre} {apellido}")
    registro = HOY - timedelta(days=60 + n * 9)

    with neon_db.transaccion() as cur:
        cur.execute("SELECT id_socio FROM socios WHERE email = %s", (email,))
        fila = cur.fetchone()
        if fila:
            id_socio = fila["id_socio"]
            cur.execute("UPDATE socios SET firebase_uid = %s, estado = 'activo' WHERE id_socio = %s", (uid, id_socio))
            cur.execute("SELECT 1 FROM seriesentrenamiento WHERE id_socio = %s LIMIT 1", (id_socio,))
            if cur.fetchone():
                print(f"  prueba{n}: ya estaba cargado (id {id_socio})")
                return id_socio
        else:
            cur.execute(
                "INSERT INTO socios (firebase_uid, dni, nombre, apellido, email, telefono, sexo, fecha_nacimiento, nivel_experiencia,"
                " disponibilidad_horaria, direccion, estado, fecha_registro, rol)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'activo',%s,1) RETURNING id_socio",
                (uid, f"9900{n:04d}", nombre, apellido, email, f"11 0000-{n:04d}", sexo,
                 date(HOY.year - edad, 1 + n % 12, 3 + n), nivel, rng.choice(["Mañana", "Tarde", "Noche"]),
                 f"Calle de prueba {100 + n}", ts(registro, 10)))
            id_socio = cur.fetchone()["id_socio"]

        # perfil de la app (sin cambio obligatorio de contraseña) y datos físicos
        cur.execute(
            "INSERT INTO perfilapp (id_socio, edad, debe_cambiar_password, vio_plano, vistas_bodygraph) VALUES (%s,%s,FALSE,TRUE,%s)"
            " ON CONFLICT (id_socio) DO UPDATE SET edad = EXCLUDED.edad, debe_cambiar_password = FALSE, vio_plano = TRUE,"
            " vistas_bodygraph = EXCLUDED.vistas_bodygraph", (id_socio, edad, rng.randint(3, 12)))
        for s in ("ranking", "calculadora", "logros", "bodygraph"):
            cur.execute("INSERT INTO perfilappsecciones (id_socio, seccion) VALUES (%s,%s) ON CONFLICT DO NOTHING", (id_socio, s))
        cur.execute("INSERT INTO objetivos (id_socio, tipo, prioridad, estado, fecha_registro) VALUES (%s,%s,'principal','activo',%s)",
                    (id_socio, objetivo, ts(registro, 11)))
        delta = {"HIPERTROFIA": 3.2, "FUERZA": 2.0, "SALUD": -4.5}[objetivo]
        for k in range(10, -1, -1):
            d = HOY - timedelta(days=7 * k + 1)
            cur.execute("INSERT INTO progresopeso (id_socio, fecha, peso) VALUES (%s,%s,%s)",
                        (id_socio, d, round(peso - delta * k / 10 + rng.uniform(-.3, .3), 1)))

        # membresía, medio de pago y un pago por mes desde que se registró
        cur.execute("SELECT id_membresia, precio, duracion_dias FROM membresias WHERE nombre = %s", (plan,))
        m = cur.fetchone()
        tipo = rng.choice(["Mercado Pago", "Efectivo"])
        cur.execute("INSERT INTO mediospago (id_socio, tipo, proveedor, estado) VALUES (%s,%s,%s,'activo') RETURNING id_medio_pago",
                    (id_socio, tipo, "Mercado Pago" if tipo == "Mercado Pago" else "Mostrador"))
        id_medio = cur.fetchone()["id_medio_pago"]
        inicio = registro
        while inicio <= HOY:
            fin = inicio + timedelta(days=m["duracion_dias"])
            activa = inicio <= HOY < fin
            cur.execute(
                "INSERT INTO sociomembresia (id_socio, id_membresia, fecha_inicio, fecha_vencimiento, estado, asignado_por)"
                " VALUES (%s,%s,%s,%s,%s,'Recepcionista OlimpOS — Recepcionista')",
                (id_socio, m["id_membresia"], inicio, fin, "activa" if activa else "vencida"))
            cur.execute(
                "INSERT INTO pagos (id_socio, id_membresia, id_plan_pago, id_medio_pago, monto, fecha_pago, fecha_vencimiento, numero_comprobante, estado)"
                " VALUES (%s,%s,1,%s,%s,%s,%s,%s,'Aprobado')",
                (id_socio, m["id_membresia"], id_medio, m["precio"], ts(inicio, rng.randint(9, 20), rng.randint(0, 59)), fin,
                 f"{rng.randint(10**10, 10**11 - 1)}" if tipo == "Mercado Pago" else None))
            inicio = fin

        # rutinas: la del entrenador (activa) y una propia
        rutinas = []
        for i, (nom_rut, ejs) in enumerate(RUTINAS[objetivo]):
            cur.execute(
                "INSERT INTO rutinas (id_socio, id_empleado, nombre, descripcion, estado, origen, activa, creada_por, fecha_creacion)"
                " VALUES (%s,%s,%s,%s,'vigente',%s,%s,%s,%s) RETURNING cod_rutina",
                (id_socio, ENTRENADOR if i == 0 else None, nom_rut, None, "entrenador" if i == 0 else "socio", i == 0,
                 FIRMA_ENTRENADOR if i == 0 else "Vos mismo", ts(registro + timedelta(days=2 + i * 10), 18)))
            cod = cur.fetchone()["cod_rutina"]
            filas = []
            for o, (ej, series, rel, corporal) in enumerate(ejs):
                base = 0 if corporal else round(peso * rel * (0.75 + fuerza * 0.6) / 2.5) * 2.5
                cur.execute(
                    "INSERT INTO rutinaejercicio (cod_rutina, id_ejercicio, orden, nombre, series, repeticiones, peso, descanso, es_peso_corporal)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_rutina_ejercicio",
                    (cod, ejercicios.get(ej), o, ej, series, 8 if objetivo == "FUERZA" else 12, base, 90, corporal))
                filas.append((cur.fetchone()["id_rutina_ejercicio"], ej, series, base, corporal))
            rutinas.append(filas)

        # entrenamientos: 3 a 5 días por semana durante ~7 semanas, con progresión de cargas
        dias = []
        d = HOY - timedelta(days=49)
        while d <= HOY:
            if rng.random() < (.55 if nivel != "Principiante" else .42) and d.weekday() != 6 and d < HOY:
                dias.append(d)
            d += timedelta(days=1)
        for k, dia in enumerate(dias):
            filas = rutinas[k % 2]
            hora = {"Mañana": 8, "Tarde": 15, "Noche": 19}.get(rng.choice(["Mañana", "Tarde", "Noche"]), 18)
            inicio = ts(dia, hora, rng.randint(0, 40))
            cur.execute("INSERT INTO accesos (id_socio, fecha, metodo, resultado, dispositivo) VALUES (%s,%s,%s,'permitido','Recepción')",
                        (id_socio, inicio, rng.choice(["qr", "qr", "qr", "biometrico"])))
            progreso = 1 + 0.12 * (dia - dias[0]).days / 49
            t = inicio + timedelta(minutes=5)
            for id_re, ej, series, base, corporal in filas:
                for s in range(1, series + 1):
                    carga = 0 if corporal else round(base * progreso * rng.uniform(.95, 1.03) / 2.5) * 2.5
                    reps = rng.randint(6, 9) if objetivo == "FUERZA" else rng.randint(9, 13)
                    if corporal:
                        reps = rng.randint(8, 20)
                    t += timedelta(minutes=rng.randint(2, 3))
                    cur.execute(
                        "INSERT INTO seriesentrenamiento (id_socio, id_rutina_ejercicio, numero_serie, peso, repeticiones, fecha, ejercicio, es_peso_corporal)"
                        " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (id_socio, id_re, s, carga, reps, t, ej, corporal))

        # marcas de la Calculadora (2 o 3 por ejercicio, casi todas verificadas)
        cur.execute("SELECT em.id_ejercicio_marca, e.nombre, em.beginner_m, em.dios_m, em.beginner_f, em.dios_f, em.es_peso_corporal"
                    " FROM ejerciciosmarca em JOIN ejercicios e USING (id_ejercicio)")
        for em in cur.fetchall():
            ini, fin_ = (em["beginner_f"], em["dios_f"]) if sexo == "FEMENINO" else (em["beginner_m"], em["dios_m"])
            for j in range(rng.randint(2, 3)):
                nivel_marca = fuerza * (0.85 + 0.08 * j) * rng.uniform(.9, 1.05)
                ratio = float(ini) + (float(fin_) - float(ini)) * nivel_marca
                if em["es_peso_corporal"]:
                    reps = 1
                    lastre = max(0, round((ratio - 1) * peso / 2.5) * 2.5)
                    carga_peso, reps = (lastre, rng.randint(3, 6)) if lastre > 0 else (0, rng.randint(8, 25))
                else:
                    reps = rng.choice([1, 1, 3, 5])
                    carga_peso = max(2.5, round(ratio * peso / (1 + reps / 30) / 2.5) * 2.5)
                cuando = ts(HOY - timedelta(days=45 - j * 18 - rng.randint(0, 5)), 19, rng.randint(0, 59))
                verificada = not (j == 2 and rng.random() < .5)
                cur.execute(
                    "INSERT INTO marcaspersonales (id_socio, id_ejercicio_marca, peso, repeticiones, uno_rm_estimado, peso_corporal, fecha, estado,"
                    " id_empleado_verificador, fecha_verificacion, verificado_por)"
                    " VALUES (%s,%s,%s,%s,round(%s::numeric * (1 + %s::numeric / 30), 2),%s,%s,%s,%s,%s,%s)",
                    (id_socio, em["id_ejercicio_marca"], carga_peso, reps, carga_peso, reps, peso, cuando,
                     "verificada" if verificada else "pendiente", ENTRENADOR if verificada else None,
                     cuando + timedelta(minutes=10) if verificada else None, "Entrenador OlimpOS" if verificada else None))

        # dieta asignada: un plato por comida, según el objetivo
        elegir = {
            "HIPERTROFIA": ("Panqueques de avena", "Pollo grillado con arroz", "Salmón con batata"),
            "FUERZA": ("Tostadas con palta y huevo", "Lomo con papas al horno", "Pollo al curry con arroz integral"),
            "SALUD": ("Yogur griego con granola", "Ensalada de garbanzos", "Merluza con batata"),
        }[objetivo]
        if n % 2 == 0:
            elegir = {"HIPERTROFIA": ("Tostadas con maní y banana", "Bowl mexicano de pollo", "Carne con batata y choclo"),
                      "FUERZA": ("Revuelto con espinaca", "Carne con quinoa y morrones", "Salmón con batata"),
                      "SALUD": ("Bowl de avena con frutos rojos", "Atún con quinoa y palta", "Ensalada de pollo")}[objetivo]
        cur.execute("INSERT INTO dietas (id_socio, id_empleado, nombre, objetivo, fecha_creacion, estado) VALUES (%s,%s,%s,%s,%s,'vigente') RETURNING cod_dieta",
                    (id_socio, NUTRICIONISTA, f"Plan {objetivo.capitalize()}", objetivo, ts(registro + timedelta(days=3), 12)))
        cod_dieta = cur.fetchone()["cod_dieta"]
        cur.execute("INSERT INTO planalimentario (cod_dieta, nombre, fecha_inicio, estado) VALUES (%s,'Plan diario',%s,'vigente') RETURNING id_plan_alimentario",
                    (cod_dieta, registro + timedelta(days=3)))
        id_plan = cur.fetchone()["id_plan_alimentario"]
        momentos = ("desayuno", "almuerzo", "cena")
        for mom, nom in zip(momentos, elegir):
            cur.execute("INSERT INTO planplato (id_plan_alimentario, id_plato, momento, orden) VALUES (%s,%s,%s,0)", (id_plan, platos[nom], mom))
        cur.execute("SELECT id_plato, kcal, proteinas, carbs, grasas, imagen FROM platos WHERE id_plato = ANY(%s)", ([platos[x] for x in elegir],))
        info = {f["id_plato"]: f for f in cur.fetchall()}
        meta = [sum(info[platos[x]][k] for x in elegir) for k in ("kcal", "proteinas", "carbs", "grasas")]
        miniaturas = {}
        for idp, f in info.items():
            im = Image.open(io.BytesIO(base64.b64decode(f["imagen"]))).convert("RGB")
            im.thumbnail((320, 320))
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=70)
            miniaturas[idp] = base64.b64encode(buf.getvalue()).decode()

        # comidas registradas: los últimos 12 días, casi siempre las tres
        for k in range(12, -1, -1):
            dia = HOY - timedelta(days=k)
            cur.execute(
                "INSERT INTO comidasdia (id_socio, fecha, objetivo, meta_kcal, meta_proteinas, meta_carbs, meta_grasas)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)", (id_socio, dia, objetivo, *meta))
            for mom in momentos:
                cur.execute("INSERT INTO comidasdiametamomentos (id_socio, fecha, momento) VALUES (%s,%s,%s)", (id_socio, dia, mom))
            for mom, nom, hora in zip(momentos, elegir, (8, 13, 21)):
                if k > 7 and rng.random() < .08:
                    continue
                f = info[platos[nom]]
                factor = rng.uniform(.96, 1.06)
                cur.execute(
                    "INSERT INTO comidasregistradas (id_socio, fecha, momento, hora, kcal, proteinas, carbs, grasas, nota)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (id_socio, dia, mom, ts(dia, hora, rng.randint(0, 50)), round(f["kcal"] * factor), round(f["proteinas"] * factor),
                     round(f["carbs"] * factor), round(f["grasas"] * factor), rng.choice(["", "", "Muy rico", "Porción un poco más grande"])))
                cur.execute("INSERT INTO comidaregistradaplatos (id_socio, fecha, momento, id_plato) VALUES (%s,%s,%s,%s)",
                            (id_socio, dia, mom, f["id_plato"]))
                cur.execute("INSERT INTO fotoscomidas (id_socio, fecha, momento, imagen, fecha_foto) VALUES (%s,%s,%s,%s,%s)",
                            (id_socio, dia, mom, miniaturas[f["id_plato"]], ts(dia, hora, 55)))
        for idp in list(platos.values())[: 6 + n]:
            cur.execute("INSERT INTO platosprobados (id_socio, id_plato, fecha_probado) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                        (id_socio, idp, ts(HOY - timedelta(days=rng.randint(1, 40)), 13)))
        cur.execute("INSERT INTO preferenciasalimentarias (id_socio, tipo) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                    (id_socio, rng.choice(["Alta en proteína", "Sin lactosa", "Mediterránea", "Sin preferencias"])))

        # agua: de 5 a 9 vasos por día en las últimas dos semanas (hoy, algunos)
        for k in range(14, -1, -1):
            dia = HOY - timedelta(days=k)
            vasos = rng.randint(5, 9)
            for v in range(vasos):
                cur.execute("INSERT INTO registroagua (id_socio, fecha, cantidad_ml) VALUES (%s,%s,250)",
                            (id_socio, ts(dia, 8 + v * 14 // vasos, rng.randint(0, 59))))

        # reservas de clases de esta semana y la anterior
        cur.execute("SELECT id_clase FROM clases WHERE estado = 'activa' ORDER BY id_clase")
        clases = [f["id_clase"] for f in cur.fetchall()]
        for semana in (HOY - timedelta(days=7), HOY):
            for id_clase in rng.sample(clases, k=min(len(clases), rng.randint(1, 2))):
                cur.execute("INSERT INTO reservasclase (id_clase, id_socio, fecha_reserva, estado, semana) VALUES (%s,%s,%s,'confirmada',%s)",
                            (id_clase, id_socio, ts(semana - timedelta(days=semana.weekday()), 10), semana_iso(semana)))

        # pedidos en la tienda: uno entregado y, a veces, uno pendiente
        for estado, hace in (("entregado", 20), ("pendiente", 1)):
            if estado == "pendiente" and n % 3:
                continue
            items = rng.sample(productos, k=2)
            total = sum(float(p["precio"]) for p in items)
            cur.execute("INSERT INTO pedidostienda (id_socio, estado, total, fecha, fecha_cierre, id_empleado_cierre) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id_pedido",
                        (id_socio, estado, total, ts(HOY - timedelta(days=hace), 18),
                         ts(HOY - timedelta(days=hace - 1), 10) if estado == "entregado" else None, 12 if estado == "entregado" else None))
            id_pedido = cur.fetchone()["id_pedido"]
            for p in items:
                cur.execute("INSERT INTO pedidotiendaitems (id_pedido, id_producto, nombre, precio_unitario, cantidad) VALUES (%s,%s,%s,%s,1)",
                            (id_pedido, p["id_producto"], p["nombre"], p["precio"]))

    print(f"  prueba{n}: {nombre} {apellido} (id {id_socio}) · {len(dias)} entrenamientos")
    return id_socio


def cargar_companeros(ids: list[int]):
    with neon_db.transaccion() as cur:
        for i, a in enumerate(ids):
            for b in (ids[(i + 1) % len(ids)], ids[(i + 3) % len(ids)]):
                cur.execute("INSERT INTO companeros (id_socio, id_companero) VALUES (%s,%s) ON CONFLICT DO NOTHING", (a, b))


def borrar():
    app = auth_repo._app()
    for n in range(1, 11):
        email = f"prueba{n}@gmail.com"
        try:
            fb_auth.delete_user(fb_auth.get_user_by_email(email, app=app).uid, app=app)
        except fb_auth.UserNotFoundError:
            pass
        with neon_db.transaccion() as cur:
            cur.execute("SELECT id_socio FROM socios WHERE email = %s", (email,))
            f = cur.fetchone()
            if not f:
                continue
            s = f["id_socio"]
            for t in ("pedidotiendaitems WHERE id_pedido IN (SELECT id_pedido FROM pedidostienda WHERE id_socio = %s)",
                      "pedidostienda WHERE id_socio = %s", "pagos WHERE id_socio = %s", "mediospago WHERE id_socio = %s",
                      "sociomembresia WHERE id_socio = %s", "seriesentrenamiento WHERE id_socio = %s", "accesos WHERE id_socio = %s",
                      "rutinas WHERE id_socio = %s", "dietas WHERE id_socio = %s", "socios WHERE id_socio = %s"):
                cur.execute("DELETE FROM " + t, (s,))
        print(f"  borrado {email}")


def main():
    if "--borrar" in sys.argv:
        borrar()
        return
    print("Platos…")
    platos = cargar_platos()
    print("Tablón…")
    cargar_tablon()
    ejercicios = {f["nombre"]: f["id_ejercicio"] for f in neon_db.consulta(
        "SELECT DISTINCT ON (nombre) nombre, id_ejercicio FROM ejercicios WHERE estado = 'publicado' ORDER BY nombre, id_ejercicio")}
    productos = neon_db.consulta("SELECT id_producto, nombre, precio FROM productos WHERE publicado AND stock > 0 ORDER BY id_producto")
    print("Usuarios…")
    ids = [cargar_usuario(n, datos, platos, ejercicios, productos) for n, datos in enumerate(USUARIOS, start=1)]
    cargar_companeros(ids)
    print("Listo.")


if __name__ == "__main__":
    main()
