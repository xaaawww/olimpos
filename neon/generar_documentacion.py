"""
Genera la documentacion de la base de datos DIRECTAMENTE desde PostgreSQL
(asi nunca queda desactualizada respecto al esquema real):

    neon/diagrama_er.html          diagrama entidad-relacion (Mermaid, se abre en el navegador)
    neon/diccionario_de_datos.md   tabla por tabla: columnas, tipos, PK, FK, restricciones

Uso:  python neon/generar_documentacion.py [--url postgresql://...]
      (sin --url lee Aplicaciones/olimpos_gym/neon_credentials.json)
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import psycopg

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.dirname(os.path.abspath(__file__))

TIPOS = {"text": "text", "integer": "int", "smallint": "smallint", "bigint": "bigint", "boolean": "bool",
         "numeric": "numeric", "real": "real", "date": "date", "time without time zone": "time",
         "timestamp with time zone": "timestamptz", "uuid": "uuid"}

GRUPOS = [
    ("Personas y roles", ["socios", "empleados", "entrenadores", "profesionales", "rol", "perfilapp", "perfilappsecciones"]),
    ("Seguridad y accesos de usuarios", ["permisos", "rolpermiso", "usuariopermiso", "sesiones", "intentosacceso", "dispositivos",
                                         "politicasseguridad", "recuperacioncontraseña", "historialaccesos", "historialactividadusuarios"]),
    ("Membresías y pagos", ["membresias", "sociomembresia", "planespago", "mediospago", "pagos", "cuotas", "promociones", "membresiapromocion"]),
    ("Clases e instalaciones", ["clases", "clasehorario", "horarios", "disciplinas", "reservasclase", "instalaciones",
                                "ubicaciongimnasio", "turnos", "visitas", "maquinas", "usomaquinas"]),
    ("Entrenamiento", ["rutinas", "rutinaejercicio", "ejercicios", "ejerciciopuntos", "ejercicioetiquetas", "puntoetiquetas",
                       "zonasmusculares", "sesionesentrenamiento", "solicitudesrutina", "historialentrenamientos",
                       "progresofuerza", "progresopeso", "seriesentrenamiento"]),
    ("Arena (rangos y marcas)", ["gruposmusculares", "rangos", "ejerciciosmarca", "marcaspersonales", "rangossocio",
                                 "logros", "logrossocio", "nivelesescalera", "progresoarena", "companeros"]),
    ("Nutrición", ["dietas", "planalimentario", "planalimento", "planplato", "alimentos", "platos", "platoingredientes",
                   "platoetiquetas", "ingredienteetiquetas", "ingredientebeneficios", "platosprobados", "comidasdia",
                   "comidasregistradas", "comidaregistradaplatos", "fotoscomidas", "historialalimentario",
                   "preferenciasalimentarias", "restriccionesalimentarias", "alimentosexcluidos",
                   "evaluacionesnutricionales", "recomendacionesnutricionales", "solicitudesnutricionales", "registroagua"]),
    ("Salud y progreso", ["salud", "cuestionarios", "objetivos", "fotosprogreso"]),
    ("Lockers, accesos y aforo", ["lockers", "reservaslocker", "aperturaslocker", "accesos", "codigosacceso", "codigosqr",
                                  "datosbiometricos", "relojesdeportivos", "aforo", "incidenciasacceso"]),
    ("Comunicación y web", ["consultas", "notificaciones", "solicitudescontacto", "tablonpublicaciones", "contactosweb"]),
    ("Argos (asistente de IA)", ["argosbaseconocimiento", "argosconversaciones", "argosmensajes", "argoscupodiario", "consumoimagenesia"]),
]


def leer_esquema(cx):
    cols = defaultdict(list)
    for t, c, tipo, nulo, defecto, long in cx.execute("""
        SELECT table_name, column_name, data_type, is_nullable, column_default, character_maximum_length
        FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name, ordinal_position"""):
        cols[t].append(dict(nombre=c, tipo=TIPOS.get(tipo, tipo), nulo=nulo == "YES", defecto=defecto))
    pk, uk = defaultdict(list), defaultdict(list)
    for t, c, tipo_c, cname in cx.execute("""
        SELECT tc.table_name, kcu.column_name, tc.constraint_type, tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema, table_name)
        WHERE tc.table_schema='public' AND tc.constraint_type IN ('PRIMARY KEY','UNIQUE')
        ORDER BY tc.table_name, kcu.ordinal_position"""):
        (pk if tipo_c == "PRIMARY KEY" else uk)[t].append(c)
    fks = []
    for r in cx.execute("""
        SELECT c.conrelid::regclass::text, c.confrelid::regclass::text,
               (SELECT array_agg(a.attname ORDER BY k.i) FROM unnest(c.conkey) WITH ORDINALITY k(attnum,i)
                  JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.attnum),
               (SELECT array_agg(a.attname ORDER BY k.i) FROM unnest(c.confkey) WITH ORDINALITY k(attnum,i)
                  JOIN pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=k.attnum),
               c.confdeltype
        FROM pg_constraint c WHERE c.contype='f' AND c.connamespace='public'::regnamespace
        ORDER BY 1, 2"""):
        fks.append(dict(hija=r[0], padre=r[1], cols=r[2], cols_padre=r[3],
                        borrado={"c": "CASCADE", "r": "RESTRICT", "n": "SET NULL", "a": "NO ACTION"}[r[4]]))
    checks = defaultdict(list)
    for t, d in cx.execute("""SELECT conrelid::regclass::text, pg_get_constraintdef(oid) FROM pg_constraint
                              WHERE contype='c' AND connamespace='public'::regnamespace ORDER BY 1"""):
        checks[t].append(d)
    idx = defaultdict(list)
    for t, d in cx.execute("""SELECT tablename, indexdef FROM pg_indexes WHERE schemaname='public'
                              AND indexname NOT LIKE '%%_pkey' ORDER BY 1"""):
        idx[t].append(d)
    return cols, pk, uk, fks, checks, idx


def mermaid(cols, pk, uk, fks, tablas=None, solo_pk_de=(), sin_columnas=False):
    """Diagrama Mermaid. `tablas`: subconjunto a dibujar (None = todas).
    `solo_pk_de`: tablas de contexto que se dibujan con unicamente su PK.
    `sin_columnas`: dibuja solo nombres (vista general)."""
    tablas = set(tablas) if tablas is not None else set(cols)
    fk_cols = defaultdict(set)
    for f in fks:
        fk_cols[f["hija"]].update(f["cols"])
    out = ["erDiagram"]
    for t in sorted(tablas | set(solo_pk_de)):
        out.append(f"    {t} {{")
        if not sin_columnas:
            for c in cols[t]:
                if t in solo_pk_de and t not in tablas and c["nombre"] not in pk[t]:
                    continue
                marcas = []
                if c["nombre"] in pk[t]:
                    marcas.append("PK")
                if c["nombre"] in fk_cols[t]:
                    marcas.append("FK")
                if c["nombre"] in uk[t] and len(uk[t]) == 1:
                    marcas.append("UK")
                out.append(f"        {c['tipo'].replace(' ', '_')} {c['nombre']} {','.join(marcas)}".rstrip())
        out.append("    }")
    visibles = tablas | set(solo_pk_de)
    for f in fks:
        if f["hija"] in tablas and f["padre"] in visibles:
            rel = "||--o|" if set(f["cols"]) == set(pk[f["hija"]]) else "||--o{"
            out.append(f'    {f["padre"]} {rel} {f["hija"]} : "{", ".join(f["cols"])}"')
    return "\n".join(out)


def grupos_completos(cols):
    en_grupo = {t for _, ts in GRUPOS for t in ts}
    otras = sorted(set(cols) - en_grupo)
    return GRUPOS + ([("Otras", otras)] if otras else [])


def diagramas(cols, pk, uk, fks):
    """Lista de (titulo, codigo_mermaid): vista general + una por area."""
    res = [("Vista general", mermaid(cols, pk, uk, fks, sin_columnas=True))]
    for titulo, tablas in grupos_completos(cols):
        tablas = [t for t in tablas if t in cols]
        padres = {f["padre"] for f in fks if f["hija"] in tablas and f["padre"] not in tablas}
        res.append((titulo, mermaid(cols, pk, uk, fks, tablas=tablas, solo_pk_de=padres)))
    return res


def diccionario(cols, pk, uk, fks, checks, idx):
    fk_de = defaultdict(dict)
    for f in fks:
        for c, cp in zip(f["cols"], f["cols_padre"]):
            fk_de[f["hija"]][c] = f"{f['padre']}.{cp} (borrado: {f['borrado']})"
    md = ["# Diccionario de datos - OlimpOS Gym", "",
          f"Base de datos relacional PostgreSQL (Neon). {len(cols)} tablas, "
          f"{sum(len(v) > 0 for v in pk.values())} claves primarias, {len(fks)} claves foráneas.", "",
          "Leyenda: **PK** clave primaria · **FK** clave foránea (con su regla de borrado) · **UK** clave única · "
          "**NN** no admite nulos.", ""]
    for titulo, tablas in grupos_completos(cols):
        md += [f"## {titulo}", ""]
        for t in tablas:
            if t not in cols:
                continue
            md += [f"### {t}", "", "| Columna | Tipo | Restricciones |", "|---|---|---|"]
            for c in cols[t]:
                r = []
                if c["nombre"] in pk[t]:
                    r.append("**PK**" if len(pk[t]) == 1 else "**PK** (compuesta)")
                if c["nombre"] in fk_de[t]:
                    r.append(f"**FK** → {fk_de[t][c['nombre']]}")
                if c["nombre"] in uk[t] and len(uk[t]) == 1:
                    r.append("**UK**")
                if not c["nulo"] and c["nombre"] not in pk[t]:
                    r.append("NN")
                if c["defecto"] and "nextval" not in c["defecto"]:
                    r.append(f"por defecto `{c['defecto'][:40]}`")
                md.append(f"| {c['nombre']} | {c['tipo']} | {' · '.join(r)} |")
            extras = [f"`{x}`" for x in checks.get(t, [])] + [f"índice: `{x.split(' ON ')[-1][:90]}`" for x in idx.get(t, [])]
            if extras:
                md += ["", "Reglas adicionales: " + "; ".join(extras)]
            md.append("")
    return "\n".join(md)


HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>OlimpOS - Diagrama entidad-relación</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body{{font-family:system-ui,sans-serif;margin:0;background:#fffdf5;color:#1a1500}}
  header{{padding:14px 24px;background:#0d0b00;color:#f4e3a1}}
  header h1{{margin:0;font-size:20px}} header p{{margin:4px 0 0;font-size:13px;opacity:.8}}
  .barra{{padding:10px 24px;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #e6d9a8;align-items:center}}
  button{{border:1px solid #c9a227;background:#fff;border-radius:8px;padding:6px 12px;cursor:pointer;font-size:13px}}
  button.act{{background:#c9a227;color:#0d0b00;font-weight:700}}
  .sep{{width:1px;height:22px;background:#e6d9a8;margin:0 6px}}
  .panel{{display:none;overflow:auto;padding:16px;height:calc(100vh - 150px)}} .panel.act{{display:block}}
  .panel svg{{max-width:none !important}}
</style></head><body>
<header><h1>OlimpOS Gym - Diagrama entidad-relación</h1>
<p>{n} tablas · {npk} claves primarias · {nfk} claves foráneas · PostgreSQL (Neon)</p></header>
<div class="barra" id="tabs"></div>
<div id="paneles"></div>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({{startOnLoad:false, maxTextSize:900000, er:{{useMaxWidth:false}}, theme:"neutral"}});
  const D = {datos};
  const tabs=document.getElementById("tabs"), paneles=document.getElementById("paneles");
  const esc = {{}};
  async function mostrar(i){{
    [...tabs.querySelectorAll("button.t")].forEach((b,j)=>b.classList.toggle("act",i===j));
    [...paneles.children].forEach((p,j)=>p.classList.toggle("act",i===j));
    const p = paneles.children[i];
    if(!p.dataset.ok){{ await mermaid.run({{nodes:[p.querySelector(".mermaid")]}}); p.dataset.ok=1; esc[i]=1; ajustar(i); }}
  }}
  function svg(i){{ return paneles.children[i].querySelector("svg"); }}
  function ajustar(i){{ const s=svg(i); if(!s) return; const w=s.viewBox.baseVal.width, c=paneles.children[i].clientWidth-32;
    esc[i]=Math.min(1,c/w); aplicar(i); }}
  function aplicar(i){{ const s=svg(i); s.style.transformOrigin="0 0"; s.style.transform=`scale(${{esc[i]}})`;
    s.parentElement.style.width=(s.viewBox.baseVal.width*esc[i])+"px"; s.parentElement.style.height=(s.viewBox.baseVal.height*esc[i])+"px"; }}
  let actual=0;
  D.forEach((d,i)=>{{
    const b=document.createElement("button"); b.className="t"; b.textContent=d[0]; b.onclick=()=>{{actual=i;mostrar(i);}}; tabs.appendChild(b);
    const p=document.createElement("div"); p.className="panel"; const pre=document.createElement("pre"); pre.className="mermaid"; pre.textContent=d[1];
    p.appendChild(pre); paneles.appendChild(p);
  }});
  const sep=document.createElement("span"); sep.className="sep"; tabs.appendChild(sep);
  [["Alejar −",0.8],["Acercar +",1.25]].forEach(([t,f])=>{{ const b=document.createElement("button"); b.textContent=t;
    b.onclick=()=>{{esc[actual]*=f; aplicar(actual);}}; tabs.appendChild(b); }});
  const bf=document.createElement("button"); bf.textContent="Ajustar al ancho"; bf.onclick=()=>ajustar(actual); tabs.appendChild(bf);
  mostrar(0);
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    url = ap.parse_args().url
    if not url:
        url = json.load(open(os.path.join(RAIZ, "Aplicaciones", "olimpos_gym", "neon_credentials.json")))["database_url"]
    with psycopg.connect(url) as cx:
        cols, pk, uk, fks, checks, idx = leer_esquema(cx)
    diags = diagramas(cols, pk, uk, fks)
    open(os.path.join(SALIDA, "diagrama_er.html"), "w", encoding="utf-8").write(
        HTML.format(datos=json.dumps(diags, ensure_ascii=False).replace("</", "<\\/"),
                    n=len(cols), npk=sum(len(v) > 0 for v in pk.values()), nfk=len(fks)))
    open(os.path.join(SALIDA, "diccionario_de_datos.md"), "w", encoding="utf-8").write(
        diccionario(cols, pk, uk, fks, checks, idx))
    print(f"OK: {len(cols)} tablas, {len(fks)} claves foráneas -> neon/diagrama_er.html y neon/diccionario_de_datos.md")


if __name__ == "__main__":
    main()
