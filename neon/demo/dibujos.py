"""Dibujos planos (SVG) de ingredientes para las imágenes de los platos de demostración.

Cada ingrediente se dibuja dentro de una zona circular del plato (centro cx, cy y
radio r). El estilo imita al de las imágenes del catálogo: ilustración plana, vista
desde arriba, contornos finos oscuros y fondo blanco.
"""
import math
import random

TRAZO = "#2f2a25"


def _p(x, y):
    return f"{x:.1f},{y:.1f}"


def esparcir(rng, cx, cy, r, n, sep, intentos=4000):
    """Puntos al azar dentro del círculo, separados al menos `sep`."""
    pts = []
    for _ in range(intentos):
        if len(pts) >= n:
            break
        a, d = rng.uniform(0, 2 * math.pi), r * math.sqrt(rng.random())
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        if all((x - px) ** 2 + (y - py) ** 2 >= sep * sep for px, py in pts):
            pts.append((x, y))
    return sorted(pts, key=lambda p: p[1])


def mancha(rng, cx, cy, r, color, borde=TRAZO, irregular=0.12, ancho=1.8):
    """Forma orgánica cerrada (base de arroz, puré, avena…)."""
    n = 14
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (1 + rng.uniform(-irregular, irregular))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = f"M{_p(*pts[0])}"
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        d += f" Q{_p(*p0)} {_p(mx, my)}"
    d += " Z"
    return f"<path d='{d}' fill='{color}' stroke='{borde}' stroke-width='{ancho}' stroke-linejoin='round'/>"


def brillo(x, y, rx, ry, op=0.45, rot=-30):
    return f"<ellipse cx='{x:.1f}' cy='{y:.1f}' rx='{rx:.1f}' ry='{ry:.1f}' fill='#fff' opacity='{op}' transform='rotate({rot} {x:.1f} {y:.1f})'/>"


# ───────────────────────── verduras ─────────────────────────

def brocoli(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * 0.78, 7, r * 0.42):
        a = rng.uniform(-40, 40)
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += f"<rect x='{x - 7:.1f}' y='{y:.1f}' width='14' height='{r * 0.32:.1f}' rx='6' fill='#a6cf6a' stroke='{TRAZO}' stroke-width='1.5'/>"
        for _ in range(6):
            dx, dy = rng.uniform(-r * 0.17, r * 0.17), rng.uniform(-r * 0.15, r * 0.05)
            rr = rng.uniform(r * 0.11, r * 0.16)
            s += f"<circle cx='{x + dx:.1f}' cy='{y + dy:.1f}' r='{rr:.1f}' fill='#3f8f3a' stroke='{TRAZO}' stroke-width='1.4'/>"
        for _ in range(7):
            dx, dy = rng.uniform(-r * 0.18, r * 0.18), rng.uniform(-r * 0.18, r * 0.04)
            s += f"<circle cx='{x + dx:.1f}' cy='{y + dy:.1f}' r='2.6' fill='#6fb84f'/>"
        s += "</g>"
    return s


def tomate_cherry(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * 0.82, 12, r * 0.3):
        rr = r * rng.uniform(0.16, 0.19)
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr:.1f}' fill='#e5412f' stroke='{TRAZO}' stroke-width='1.6'/>"
        s += brillo(x - rr * 0.35, y - rr * 0.35, rr * 0.32, rr * 0.18)
        pts = []
        for i in range(10):
            a = math.pi * i / 5 + rng.uniform(-.1, .1)
            d = rr * (0.42 if i % 2 == 0 else 0.15)
            pts.append(_p(x + d * math.cos(a), y + d * math.sin(a)))
        s += f"<polygon points='{' '.join(pts)}' fill='#4f9a3a' stroke='{TRAZO}' stroke-width='1'/>"
    return s


def tomate_rodajas(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * 0.62, 5, r * 0.5):
        rr = r * 0.32
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr:.1f}' fill='#e5412f' stroke='{TRAZO}' stroke-width='1.6'/>"
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr * .78:.1f}' fill='#f2705c'/>"
        for i in range(5):
            a = 2 * math.pi * i / 5
            ex, ey = x + rr * .45 * math.cos(a), y + rr * .45 * math.sin(a)
            s += f"<ellipse cx='{ex:.1f}' cy='{ey:.1f}' rx='{rr * .17:.1f}' ry='{rr * .1:.1f}' fill='#f7c66a' transform='rotate({math.degrees(a):.0f} {ex:.1f} {ey:.1f})'/>"
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr * .14:.1f}' fill='#f9a08f'/>"
    return s


def pepino(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * 0.7, 7, r * 0.4):
        rr = r * 0.22
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr:.1f}' fill='#4c8f3c' stroke='{TRAZO}' stroke-width='1.5'/>"
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr * .84:.1f}' fill='#d8efb5'/>"
        for i in range(6):
            a = 2 * math.pi * i / 6
            s += f"<ellipse cx='{x + rr * .38 * math.cos(a):.1f}' cy='{y + rr * .38 * math.sin(a):.1f}' rx='2.6' ry='1.6' fill='#f7f6e6' stroke='#a9c98a' stroke-width='.7'/>"
    return s


def zanahoria(rng, cx, cy, r):
    s = ""
    for i in range(9):
        x, y = cx + rng.uniform(-r * .55, r * .55), cy + rng.uniform(-r * .5, r * .5)
        a = rng.uniform(-60, 60)
        s += (f"<rect x='{x - r * .4:.1f}' y='{y - 6:.1f}' width='{r * .8:.1f}' height='13' rx='6' fill='#f08a24' stroke='{TRAZO}' "
              f"stroke-width='1.5' transform='rotate({a:.0f} {x:.1f} {y:.1f})'/>")
        s += (f"<line x1='{x - r * .3:.1f}' y1='{y:.1f}' x2='{x + r * .3:.1f}' y2='{y:.1f}' stroke='#f7b267' stroke-width='3' "
              f"stroke-linecap='round' transform='rotate({a:.0f} {x:.1f} {y:.1f})'/>")
    return s


def hojas(rng, cx, cy, r, colores=("#5fae45", "#87c95a", "#3e8a35")):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * 0.72, 11, r * 0.24):
        a = rng.uniform(0, 360)
        L, W = r * rng.uniform(.36, .48), r * rng.uniform(.2, .26)
        col = rng.choice(colores)
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += (f"<path d='M{x - L:.1f},{y:.1f} C{x - L * .4:.1f},{y - W:.1f} {x + L * .5:.1f},{y - W:.1f} {x + L:.1f},{y:.1f} "
              f"C{x + L * .5:.1f},{y + W:.1f} {x - L * .4:.1f},{y + W:.1f} {x - L:.1f},{y:.1f} Z' fill='{col}' stroke='{TRAZO}' stroke-width='1.4'/>")
        s += f"<line x1='{x - L * .8:.1f}' y1='{y:.1f}' x2='{x + L * .8:.1f}' y2='{y:.1f}' stroke='#d6efb8' stroke-width='1.4'/>"
        s += "</g>"
    return s


def espinaca(rng, cx, cy, r):
    return hojas(rng, cx, cy, r, ("#2f7a32", "#3c8c3a", "#276b2c"))


def morron(rng, cx, cy, r):
    s = ""
    for i in range(10):
        x, y = cx + rng.uniform(-r * .55, r * .55), cy + rng.uniform(-r * .55, r * .55)
        a, col = rng.uniform(0, 360), rng.choice(["#e23b2e", "#f5b82e", "#e23b2e", "#4f9a3a"])
        s += (f"<path d='M{x - r * .32:.1f},{y:.1f} Q{x:.1f},{y - r * .2:.1f} {x + r * .32:.1f},{y:.1f}' fill='none' stroke='{TRAZO}' "
              f"stroke-width='12' stroke-linecap='round' transform='rotate({a:.0f} {x:.1f} {y:.1f})'/>")
        s += (f"<path d='M{x - r * .32:.1f},{y:.1f} Q{x:.1f},{y - r * .2:.1f} {x + r * .32:.1f},{y:.1f}' fill='none' stroke='{col}' "
              f"stroke-width='9' stroke-linecap='round' transform='rotate({a:.0f} {x:.1f} {y:.1f})'/>")
    return s


def champinones(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .75, 9, r * .33):
        w = r * .26
        a = rng.uniform(-30, 30)
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += f"<path d='M{x - w:.1f},{y:.1f} A{w:.1f},{w * .85:.1f} 0 0 1 {x + w:.1f},{y:.1f} Z' fill='#c9a27a' stroke='{TRAZO}' stroke-width='1.5'/>"
        s += f"<rect x='{x - w * .3:.1f}' y='{y - 1:.1f}' width='{w * .6:.1f}' height='{w * .75:.1f}' rx='4' fill='#f1e3cf' stroke='{TRAZO}' stroke-width='1.5'/>"
        s += f"<path d='M{x - w * .8:.1f},{y - 2:.1f} A{w * .8:.1f},{w * .55:.1f} 0 0 1 {x + w * .8:.1f},{y - 2:.1f}' fill='#e8d3b6'/>"
        s += "</g>"
    return s


def zapallito(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .7, 7, r * .4):
        rr = r * .22
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr:.1f}' fill='#2f6b2a' stroke='{TRAZO}' stroke-width='1.5'/>"
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr * .82:.1f}' fill='#eef2b8'/>"
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr * .35:.1f}' fill='none' stroke='#cfd98a' stroke-width='2'/>"
        s += f"<path d='M{x - rr * .5:.1f},{y - rr * .3:.1f} l{rr * .25:.1f},{rr * .1:.1f}' stroke='#7a5a2a' stroke-width='2' stroke-linecap='round'/>"
    return s


def choclo(rng, cx, cy, r):
    s = mancha(rng, cx, cy, r * .62, "#f6d04d", irregular=.08)
    for x, y in esparcir(rng, cx, cy, r * .55, 40, 11):
        s += f"<rect x='{x - 5:.1f}' y='{y - 5:.1f}' width='10' height='10' rx='3.5' fill='#f9c22e' stroke='#c99412' stroke-width='1'/>"
        s += brillo(x - 1.5, y - 2, 2.5, 1.5, .55, 0)
    return s


def calabaza(rng, cx, cy, r):
    return cubos(rng, cx, cy, r, "#f39a2b", "#d06f12", "#fbc77a")


def remolacha(rng, cx, cy, r):
    return cubos(rng, cx, cy, r, "#a0224f", "#6f1236", "#c95a85")


# ───────────────────────── carbohidratos ─────────────────────────

def cubos(rng, cx, cy, r, color, oscuro, claro, n=11):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .72, n, r * .26):
        L = r * rng.uniform(.24, .3)
        a = rng.uniform(-25, 25)
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += f"<rect x='{x - L / 2 + 3:.1f}' y='{y - L / 2 + 4:.1f}' width='{L:.1f}' height='{L:.1f}' rx='5' fill='{oscuro}'/>"
        s += f"<rect x='{x - L / 2:.1f}' y='{y - L / 2:.1f}' width='{L:.1f}' height='{L:.1f}' rx='5' fill='{color}' stroke='{TRAZO}' stroke-width='1.5'/>"
        s += f"<rect x='{x - L / 2 + 4:.1f}' y='{y - L / 2 + 4:.1f}' width='{L * .4:.1f}' height='{L * .2:.1f}' rx='3' fill='{claro}' opacity='.8'/>"
        s += f"<circle cx='{x + L * .15:.1f}' cy='{y + L * .1:.1f}' r='1.4' fill='{TRAZO}' opacity='.6'/>"
        s += "</g>"
    return s


def batata(rng, cx, cy, r):
    return cubos(rng, cx, cy, r, "#f08b3a", "#c25f17", "#f8b97a")


def papa(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .68, 8, r * .32):
        a, L, W = rng.uniform(0, 360), r * .4, r * .17
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += (f"<path d='M{x - L:.1f},{y:.1f} Q{x:.1f},{y - W * 2.2:.1f} {x + L:.1f},{y:.1f} Z' fill='#f2cc6b' stroke='{TRAZO}' stroke-width='1.5'/>")
        s += f"<path d='M{x - L * .9:.1f},{y:.1f} Q{x:.1f},{y - W * 1.8:.1f} {x + L * .9:.1f},{y:.1f}' fill='none' stroke='#b9822b' stroke-width='3'/>"
        s += "</g>"
    for _ in range(8):
        x, y = cx + rng.uniform(-r * .5, r * .5), cy + rng.uniform(-r * .5, r * .5)
        s += f"<path d='M{x:.1f},{y:.1f} l6,-4 M{x + 3:.1f},{y:.1f} l5,3' stroke='#4c8a3a' stroke-width='1.8' stroke-linecap='round'/>"
    return s


def arroz(rng, cx, cy, r, base="#fbf8ee", grano="#ffffff", borde_grano="#c9c1ad"):
    s = mancha(rng, cx, cy, r * .9, base)
    for x, y in esparcir(rng, cx, cy, r * .82, 150, 7.5):
        a = rng.uniform(0, 180)
        s += f"<ellipse cx='{x:.1f}' cy='{y:.1f}' rx='5.2' ry='2.4' fill='{grano}' stroke='{borde_grano}' stroke-width='.9' transform='rotate({a:.0f} {x:.1f} {y:.1f})'/>"
    return s


def arroz_integral(rng, cx, cy, r):
    return arroz(rng, cx, cy, r, "#e9d6ae", "#e2c792", "#a7834a")


def quinoa(rng, cx, cy, r):
    s = mancha(rng, cx, cy, r * .9, "#efe1bf")
    for x, y in esparcir(rng, cx, cy, r * .84, 240, 5.5):
        col = rng.choice(["#f4e6c4", "#e9d3a0", "#f7ecd2", "#c9a46b"])
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2.6' fill='{col}' stroke='#b8955a' stroke-width='.7'/>"
    return s


def fideos(rng, cx, cy, r):
    s = mancha(rng, cx, cy, r * .75, "#f7e3a3", irregular=.1)
    for x, y in esparcir(rng, cx, cy, r * .66, 16, r * .2):
        a = rng.uniform(0, 180)
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += f"<rect x='{x - 15:.1f}' y='{y - 6:.1f}' width='30' height='12' rx='3' fill='#f3c95c' stroke='{TRAZO}' stroke-width='1.3' transform='skewX(-18)'/>"
        s += f"<line x1='{x - 8:.1f}' y1='{y - 5:.1f}' x2='{x - 8:.1f}' y2='{y + 5:.1f}' stroke='#d9a83a' stroke-width='1.2' transform='skewX(-18)'/>"
        s += f"<line x1='{x + 2:.1f}' y1='{y - 5:.1f}' x2='{x + 2:.1f}' y2='{y + 5:.1f}' stroke='#d9a83a' stroke-width='1.2' transform='skewX(-18)'/>"
        s += "</g>"
    return s


def lentejas(rng, cx, cy, r):
    s = mancha(rng, cx, cy, r * .9, "#9c6b3c")
    for x, y in esparcir(rng, cx, cy, r * .84, 170, 7):
        col = rng.choice(["#8a5a2e", "#a8763f", "#7b4e27"])
        s += f"<ellipse cx='{x:.1f}' cy='{y:.1f}' rx='4.2' ry='3.3' fill='{col}' stroke='#4e321b' stroke-width='.7'/>"
    return s


def garbanzos(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .82, 38, r * .14):
        rr = r * .085
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr:.1f}' fill='#e7c27c' stroke='{TRAZO}' stroke-width='1.2'/>"
        s += f"<path d='M{x - rr * .2:.1f},{y - rr * .8:.1f} Q{x + rr * .5:.1f},{y:.1f} {x - rr * .1:.1f},{y + rr * .8:.1f}' fill='none' stroke='#b88c3e' stroke-width='1.2'/>"
        s += brillo(x - rr * .35, y - rr * .35, rr * .3, rr * .18, .5)
    return s


def porotos(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .82, 50, r * .12):
        a = rng.uniform(0, 180)
        s += f"<ellipse cx='{x:.1f}' cy='{y:.1f}' rx='{r * .075:.1f}' ry='{r * .05:.1f}' fill='#2b2230' stroke='#120d14' stroke-width='1' transform='rotate({a:.0f} {x:.1f} {y:.1f})'/>"
        s += brillo(x - 2, y - 2, 2.6, 1.2, .5, a)
    return s


def tostadas(rng, cx, cy, r, untado=None):
    s = ""
    for i, (dx, dy, a) in enumerate([(-r * .22, -r * .12, -12), (r * .2, r * .14, 14)]):
        x, y, w, h = cx + dx, cy + dy, r * .62, r * .62
        s += f"<g transform='rotate({a} {x:.1f} {y:.1f})'>"
        s += (f"<path d='M{x - w / 2:.1f},{y + h / 2:.1f} L{x - w / 2:.1f},{y - h * .15:.1f} C{x - w * .62:.1f},{y - h * .62:.1f} "
              f"{x + w * .62:.1f},{y - h * .62:.1f} {x + w / 2:.1f},{y - h * .15:.1f} L{x + w / 2:.1f},{y + h / 2:.1f} Z' "
              f"fill='#b9773a' stroke='{TRAZO}' stroke-width='1.6'/>")
        s += (f"<path d='M{x - w * .42:.1f},{y + h * .42:.1f} L{x - w * .42:.1f},{y - h * .12:.1f} C{x - w * .5:.1f},{y - h * .5:.1f} "
              f"{x + w * .5:.1f},{y - h * .5:.1f} {x + w * .42:.1f},{y - h * .12:.1f} L{x + w * .42:.1f},{y + h * .42:.1f} Z' fill='#e8c58c'/>")
        for _ in range(9):
            s += f"<circle cx='{x + rng.uniform(-w * .35, w * .35):.1f}' cy='{y + rng.uniform(-h * .3, h * .35):.1f}' r='1.5' fill='#c99a5a'/>"
        if untado:
            s += mancha(rng, x, y + h * .02, w * .33, untado, borde="none", irregular=.18)
            if untado == "#9cc95a":
                for _ in range(6):
                    s += f"<circle cx='{x + rng.uniform(-w * .25, w * .25):.1f}' cy='{y + rng.uniform(-h * .22, h * .22):.1f}' r='1.6' fill='#4e7a2a'/>"
        s += "</g>"
    return s


def tostada_palta(rng, cx, cy, r):
    return tostadas(rng, cx, cy, r, "#9cc95a")


def tostada_mani(rng, cx, cy, r):
    return tostadas(rng, cx, cy, r, "#b8783c")


def avena(rng, cx, cy, r):
    s = mancha(rng, cx, cy, r * .92, "#ecd7ad")
    for x, y in esparcir(rng, cx, cy, r * .86, 130, 8):
        a = rng.uniform(0, 180)
        s += f"<ellipse cx='{x:.1f}' cy='{y:.1f}' rx='5.5' ry='3.8' fill='#f3e3c0' stroke='#c7a56a' stroke-width='.8' transform='rotate({a:.0f} {x:.1f} {y:.1f})'/>"
    return s


def granola(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .82, 48, r * .11):
        pts = [_p(x + r * .07 * math.cos(2 * math.pi * k / 6) * rng.uniform(.6, 1.3),
                  y + r * .07 * math.sin(2 * math.pi * k / 6) * rng.uniform(.6, 1.3)) for k in range(6)]
        col = rng.choice(["#c58a3e", "#d9a55a", "#a8692b"])
        s += f"<polygon points='{' '.join(pts)}' fill='{col}' stroke='{TRAZO}' stroke-width='1' stroke-linejoin='round'/>"
    return s


def panqueques(rng, cx, cy, r):
    s = ""
    for i in range(3):
        y = cy + r * .18 - i * r * .14
        s += f"<ellipse cx='{cx:.1f}' cy='{y:.1f}' rx='{r * .72:.1f}' ry='{r * .5:.1f}' fill='#c98a3d' stroke='{TRAZO}' stroke-width='1.6'/>"
        s += f"<ellipse cx='{cx:.1f}' cy='{y - 4:.1f}' rx='{r * .64:.1f}' ry='{r * .42:.1f}' fill='#e7b265'/>"
    s += mancha(rng, cx, cy - r * .2, r * .25, "#f3d79a", borde="none", irregular=.2)
    s += f"<path d='M{cx - r * .3:.1f},{cy - r * .2:.1f} Q{cx:.1f},{cy - r * .4:.1f} {cx + r * .32:.1f},{cy - r * .15:.1f}' fill='none' stroke='#b0661c' stroke-width='5' stroke-linecap='round' opacity='.8'/>"
    return s


def wrap(rng, cx, cy, r):
    s = ""
    for dx, a in ((-r * .25, -18), (r * .25, 18)):
        x = cx + dx
        s += f"<g transform='rotate({a} {x:.1f} {cy:.1f})'>"
        s += f"<rect x='{x - r * .2:.1f}' y='{cy - r * .62:.1f}' width='{r * .4:.1f}' height='{r * 1.24:.1f}' rx='{r * .2:.1f}' fill='#f0d9a4' stroke='{TRAZO}' stroke-width='1.6'/>"
        s += f"<ellipse cx='{x:.1f}' cy='{cy - r * .5:.1f}' rx='{r * .17:.1f}' ry='{r * .1:.1f}' fill='#7fbf54' stroke='{TRAZO}' stroke-width='1'/>"
        s += f"<circle cx='{x - 4:.1f}' cy='{cy - r * .5:.1f}' r='4' fill='#e5412f'/><circle cx='{x + 6:.1f}' cy='{cy - r * .52:.1f}' r='4' fill='#e9c08a'/>"
        for k in range(4):
            s += f"<circle cx='{x + rng.uniform(-r * .12, r * .12):.1f}' cy='{cy + rng.uniform(-r * .3, r * .5):.1f}' r='2.4' fill='#c9a46b'/>"
        s += "</g>"
    return s


# ───────────────────────── proteínas ─────────────────────────

def lonjas(rng, cx, cy, r, borde, centro, marcas=None, n=4, ancho=.36):
    s = ""
    a = rng.uniform(-35, -15)
    s += f"<g transform='rotate({a:.0f} {cx:.1f} {cy:.1f})'>"
    for i in range(n):
        x = cx - r * .5 + i * r * .33
        w, h = r * ancho, r * 1.3
        s += f"<rect x='{x - w / 2:.1f}' y='{cy - h / 2:.1f}' width='{w:.1f}' height='{h:.1f}' rx='{w * .45:.1f}' fill='{borde}' stroke='{TRAZO}' stroke-width='1.6'/>"
        s += f"<rect x='{x - w / 2 + 5:.1f}' y='{cy - h / 2 + 7:.1f}' width='{w - 10:.1f}' height='{h - 14:.1f}' rx='{w * .35:.1f}' fill='{centro}'/>"
        if marcas:
            for k in range(3):
                yy = cy - h * .3 + k * h * .3
                s += f"<line x1='{x - w * .35:.1f}' y1='{yy:.1f}' x2='{x + w * .35:.1f}' y2='{yy - 6:.1f}' stroke='{marcas}' stroke-width='3' stroke-linecap='round'/>"
        for _ in range(3):
            s += f"<circle cx='{x + rng.uniform(-w * .3, w * .3):.1f}' cy='{cy + rng.uniform(-h * .4, h * .4):.1f}' r='1.3' fill='#2a2a2a' opacity='.7'/>"
    s += "</g>"
    return s


def pollo(rng, cx, cy, r):
    return lonjas(rng, cx, cy, r, "#d39a52", "#f1d3a1", "#8a5523")


def pavo(rng, cx, cy, r):
    return lonjas(rng, cx, cy, r, "#c9935a", "#f4dcc0", None)


def carne(rng, cx, cy, r):
    return lonjas(rng, cx, cy, r, "#6d3b22", "#c85a5a", None)


def atun(rng, cx, cy, r):
    return lonjas(rng, cx, cy, r, "#9b8174", "#e0566a", None)


def salmon(rng, cx, cy, r):
    a = rng.uniform(-30, -10)
    w, h = r * 1.45, r * .9
    s = f"<g transform='rotate({a:.0f} {cx:.1f} {cy:.1f})'>"
    s += f"<rect x='{cx - w / 2 + 4:.1f}' y='{cy - h / 2 + 6:.1f}' width='{w:.1f}' height='{h:.1f}' rx='{h * .3:.1f}' fill='#c95a2c'/>"
    s += f"<rect x='{cx - w / 2:.1f}' y='{cy - h / 2:.1f}' width='{w:.1f}' height='{h:.1f}' rx='{h * .3:.1f}' fill='#f58b57' stroke='{TRAZO}' stroke-width='1.8'/>"
    for k in range(5):
        x = cx - w * .35 + k * w * .17
        s += f"<path d='M{x:.1f},{cy - h * .42:.1f} Q{x + w * .08:.1f},{cy:.1f} {x:.1f},{cy + h * .42:.1f}' fill='none' stroke='#fde1cc' stroke-width='3.2' stroke-linecap='round'/>"
    s += brillo(cx - w * .25, cy - h * .25, w * .12, h * .07, .35, 0)
    s += f"<circle cx='{cx + w * .3:.1f}' cy='{cy - h * .2:.1f}' r='5' fill='#7fbf54' stroke='{TRAZO}' stroke-width='1'/>"
    s += "</g>"
    s += f"<path d='M{cx - r * .2:.1f},{cy + r * .5:.1f} a{r * .2:.1f},{r * .13:.1f} 0 0 0 {r * .4:.1f},0 Z' fill='#f7e15a' stroke='{TRAZO}' stroke-width='1.4'/>"
    return s


def merluza(rng, cx, cy, r):
    a = rng.uniform(-25, -5)
    w, h = r * 1.45, r * .8
    s = f"<g transform='rotate({a:.0f} {cx:.1f} {cy:.1f})'>"
    s += f"<ellipse cx='{cx:.1f}' cy='{cy:.1f}' rx='{w / 2:.1f}' ry='{h / 2:.1f}' fill='#f6efe2' stroke='{TRAZO}' stroke-width='1.8'/>"
    s += f"<ellipse cx='{cx - 4:.1f}' cy='{cy - 4:.1f}' rx='{w / 2 - 10:.1f}' ry='{h / 2 - 10:.1f}' fill='#e9c98c' opacity='.55'/>"
    for k in range(4):
        x = cx - w * .3 + k * w * .2
        s += f"<path d='M{x:.1f},{cy - h * .3:.1f} q8,{h * .3:.1f} 0,{h * .6:.1f}' fill='none' stroke='#d8c6a6' stroke-width='2'/>"
    s += "</g>"
    s += f"<path d='M{cx + r * .2:.1f},{cy + r * .45:.1f} a{r * .2:.1f},{r * .13:.1f} 0 0 0 {r * .4:.1f},0 Z' fill='#f7e15a' stroke='{TRAZO}' stroke-width='1.4'/>"
    return s


def langostinos(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .62, 6, r * .42):
        a, rr = rng.uniform(0, 360), r * .2
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += f"<path d='M{x - rr:.1f},{y:.1f} A{rr:.1f},{rr:.1f} 0 1 1 {x + rr * .3:.1f},{y + rr * .95:.1f}' fill='none' stroke='{TRAZO}' stroke-width='{rr * .78 + 3:.1f}' stroke-linecap='round'/>"
        s += f"<path d='M{x - rr:.1f},{y:.1f} A{rr:.1f},{rr:.1f} 0 1 1 {x + rr * .3:.1f},{y + rr * .95:.1f}' fill='none' stroke='#f4875c' stroke-width='{rr * .78:.1f}' stroke-linecap='round'/>"
        for k in range(4):
            ang = math.pi * (1 + k * .32)
            s += f"<line x1='{x + rr * .62 * math.cos(ang):.1f}' y1='{y + rr * .62 * math.sin(ang):.1f}' x2='{x + rr * 1.36 * math.cos(ang):.1f}' y2='{y + rr * 1.36 * math.sin(ang):.1f}' stroke='#fbd0b8' stroke-width='2'/>"
        s += "</g>"
    return s


def tofu(rng, cx, cy, r):
    return cubos(rng, cx, cy, r, "#f6eed6", "#d9b56a", "#ffffff", n=10)


def huevo_duro(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .5, 4, r * .5):
        a = rng.uniform(-40, 40)
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += f"<ellipse cx='{x:.1f}' cy='{y:.1f}' rx='{r * .27:.1f}' ry='{r * .2:.1f}' fill='#ffffff' stroke='{TRAZO}' stroke-width='1.6'/>"
        s += f"<circle cx='{x + 2:.1f}' cy='{y:.1f}' r='{r * .12:.1f}' fill='#f6b928' stroke='#d38f12' stroke-width='1.2'/>"
        s += brillo(x + r * .01, y - r * .03, r * .04, r * .025, .6, 0)
        s += "</g>"
    return s


def huevo_frito(rng, cx, cy, r):
    s = mancha(rng, cx, cy, r * .7, "#ffffff", irregular=.18)
    s += f"<circle cx='{cx + 4:.1f}' cy='{cy - 2:.1f}' r='{r * .24:.1f}' fill='#f6a91c' stroke='#c47c0b' stroke-width='1.4'/>"
    s += brillo(cx - r * .05, cy - r * .1, r * .07, r * .04, .7)
    return s


def revuelto(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .7, 13, r * .22):
        s += mancha(rng, x, y, r * rng.uniform(.14, .2), rng.choice(["#f8d548", "#f6c935", "#fadf6e"]), irregular=.3, ancho=1.3)
    for _ in range(10):
        s += f"<circle cx='{cx + rng.uniform(-r * .5, r * .5):.1f}' cy='{cy + rng.uniform(-r * .5, r * .5):.1f}' r='2' fill='#3e8a35'/>"
    return s


def yogur(rng, cx, cy, r):
    s = mancha(rng, cx, cy, r * .8, "#fbfbf7", irregular=.07)
    s += f"<path d='M{cx - r * .4:.1f},{cy:.1f} C{cx - r * .3:.1f},{cy - r * .4:.1f} {cx + r * .3:.1f},{cy - r * .4:.1f} {cx + r * .2:.1f},{cy:.1f} S{cx - r * .2:.1f},{cy + r * .3:.1f} {cx:.1f},{cy + r * .05:.1f}' fill='none' stroke='#e3e1d6' stroke-width='3'/>"
    return s


def queso_cottage(rng, cx, cy, r):
    s = mancha(rng, cx, cy, r * .75, "#fbf9f2", irregular=.15)
    for x, y in esparcir(rng, cx, cy, r * .62, 26, 14):
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rng.uniform(4, 7):.1f}' fill='#ffffff' stroke='#ddd8c7' stroke-width='1'/>"
    return s


# ───────────────────────── frutas ─────────────────────────

def banana(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .78, 13, r * .27):
        rr = r * .16
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr:.1f}' fill='#fbeaa4' stroke='{TRAZO}' stroke-width='1.4'/>"
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr * .45:.1f}' fill='none' stroke='#e9d27a' stroke-width='1.2'/>"
        for k in range(3):
            a = 2 * math.pi * k / 3
            s += f"<circle cx='{x + rr * .2 * math.cos(a):.1f}' cy='{y + rr * .2 * math.sin(a):.1f}' r='1.3' fill='#8a6a2a'/>"
    return s


def frutillas(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .66, 6, r * .4):
        w, a = r * .2, rng.uniform(-30, 30)
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += (f"<path d='M{x:.1f},{y + w * 1.25:.1f} C{x - w * 1.3:.1f},{y + w * .2:.1f} {x - w:.1f},{y - w:.1f} {x:.1f},{y - w * .8:.1f} "
              f"C{x + w:.1f},{y - w:.1f} {x + w * 1.3:.1f},{y + w * .2:.1f} {x:.1f},{y + w * 1.25:.1f} Z' fill='#e2283a' stroke='{TRAZO}' stroke-width='1.5'/>")
        for _ in range(6):
            s += f"<ellipse cx='{x + rng.uniform(-w * .6, w * .6):.1f}' cy='{y + rng.uniform(-w * .4, w * .8):.1f}' rx='1.3' ry='2' fill='#fbe27a'/>"
        s += (f"<path d='M{x - w * .7:.1f},{y - w * .85:.1f} L{x:.1f},{y - w * .55:.1f} L{x + w * .7:.1f},{y - w * .85:.1f} "
              f"L{x + w * .2:.1f},{y - w * 1.1:.1f} L{x - w * .2:.1f},{y - w * 1.1:.1f} Z' fill='#4f9a3a' stroke='{TRAZO}' stroke-width='1'/>")
        s += "</g>"
    return s


def arandanos(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .8, 30, r * .15):
        rr = r * .085
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr:.1f}' fill='#3b4a8f' stroke='#1e2550' stroke-width='1.2'/>"
        s += brillo(x - rr * .35, y - rr * .35, rr * .3, rr * .18, .4)
        s += f"<circle cx='{x + rr * .2:.1f}' cy='{y + rr * .15:.1f}' r='{rr * .22:.1f}' fill='#26305f'/>"
    return s


def kiwi(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .6, 5, r * .5):
        rr = r * .27
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr:.1f}' fill='#8a6a3b' stroke='{TRAZO}' stroke-width='1.5'/>"
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr * .86:.1f}' fill='#7cbf3a'/>"
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr * .32:.1f}' fill='#e9f4c4'/>"
        for k in range(12):
            a = 2 * math.pi * k / 12
            s += f"<ellipse cx='{x + rr * .45 * math.cos(a):.1f}' cy='{y + rr * .45 * math.sin(a):.1f}' rx='2' ry='1.1' fill='#1d1d1d' transform='rotate({math.degrees(a):.0f} {x + rr * .45 * math.cos(a):.1f} {y + rr * .45 * math.sin(a):.1f})'/>"
    return s


def manzana(rng, cx, cy, r):
    s = ""
    for i in range(6):
        a = -60 + i * 24
        s += f"<g transform='rotate({a} {cx:.1f} {cy + r * .2:.1f})'>"
        s += f"<path d='M{cx - r * .1:.1f},{cy - r * .55:.1f} Q{cx + r * .32:.1f},{cy - r * .2:.1f} {cx - r * .1:.1f},{cy + r * .15:.1f} Z' fill='#d8323a' stroke='{TRAZO}' stroke-width='1.4'/>"
        s += f"<path d='M{cx - r * .1:.1f},{cy - r * .5:.1f} Q{cx + r * .23:.1f},{cy - r * .2:.1f} {cx - r * .1:.1f},{cy + r * .1:.1f} Z' fill='#fbf1cf'/>"
        s += "</g>"
    return s


def naranja(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .6, 5, r * .48):
        a, rr = rng.uniform(0, 360), r * .3
        s += f"<g transform='rotate({a:.0f} {x:.1f} {y:.1f})'>"
        s += f"<path d='M{x - rr:.1f},{y:.1f} A{rr:.1f},{rr:.1f} 0 0 1 {x + rr:.1f},{y:.1f} Z' fill='#f39b1d' stroke='{TRAZO}' stroke-width='1.5'/>"
        s += f"<path d='M{x - rr * .84:.1f},{y - 1:.1f} A{rr * .84:.1f},{rr * .84:.1f} 0 0 1 {x + rr * .84:.1f},{y - 1:.1f} Z' fill='#fbbd4a'/>"
        for k in range(1, 5):
            ang = math.pi + k * math.pi / 5
            s += f"<line x1='{x:.1f}' y1='{y:.1f}' x2='{x + rr * .8 * math.cos(ang):.1f}' y2='{y + rr * .8 * math.sin(ang):.1f}' stroke='#fde3a7' stroke-width='1.4'/>"
        s += "</g>"
    return s


def palta(rng, cx, cy, r):
    s = ""
    a0 = rng.uniform(-30, 10)
    s += f"<g transform='rotate({a0:.0f} {cx:.1f} {cy:.1f})'>"
    for i in range(5):
        x = cx - r * .4 + i * r * .2
        s += f"<ellipse cx='{x:.1f}' cy='{cy:.1f}' rx='{r * .16:.1f}' ry='{r * .55:.1f}' fill='#4f7a26' stroke='{TRAZO}' stroke-width='1.5' transform='rotate(-12 {x:.1f} {cy:.1f})'/>"
        s += f"<ellipse cx='{x + 2:.1f}' cy='{cy:.1f}' rx='{r * .12:.1f}' ry='{r * .5:.1f}' fill='#c7dd7a' transform='rotate(-12 {x:.1f} {cy:.1f})'/>"
        s += f"<ellipse cx='{x + 3:.1f}' cy='{cy:.1f}' rx='{r * .07:.1f}' ry='{r * .4:.1f}' fill='#e5ee9d' transform='rotate(-12 {x:.1f} {cy:.1f})'/>"
    s += "</g>"
    return s


# ───────────────────────── grasas y extras ─────────────────────────

def almendras(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .78, 20, r * .19):
        a, w = rng.uniform(0, 360), r * .1
        s += (f"<path d='M{x:.1f},{y - w * 1.5:.1f} C{x + w:.1f},{y - w * .5:.1f} {x + w:.1f},{y + w:.1f} {x:.1f},{y + w * 1.1:.1f} "
              f"C{x - w:.1f},{y + w:.1f} {x - w:.1f},{y - w * .5:.1f} {x:.1f},{y - w * 1.5:.1f} Z' fill='#b7743a' stroke='{TRAZO}' "
              f"stroke-width='1.2' transform='rotate({a:.0f} {x:.1f} {y:.1f})'/>")
        s += f"<line x1='{x:.1f}' y1='{y - w:.1f}' x2='{x:.1f}' y2='{y + w * .6:.1f}' stroke='#d79a5c' stroke-width='1.3' transform='rotate({a:.0f} {x:.1f} {y:.1f})'/>"
    return s


def nueces(rng, cx, cy, r):
    s = ""
    for x, y in esparcir(rng, cx, cy, r * .75, 12, r * .26):
        s += mancha(rng, x, y, r * .15, "#c8955a", irregular=.25, ancho=1.3)
        s += f"<path d='M{x - r * .1:.1f},{y:.1f} q{r * .05:.1f},-6 {r * .1:.1f},0 t{r * .1:.1f},0' fill='none' stroke='#8a5a2a' stroke-width='1.5'/>"
    return s


def semillas(rng, cx, cy, r):
    s = ""
    for _ in range(70):
        x, y = cx + rng.uniform(-r * .6, r * .6), cy + rng.uniform(-r * .6, r * .6)
        if (x - cx) ** 2 + (y - cy) ** 2 < (r * .6) ** 2:
            s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='1.8' fill='{rng.choice(['#3a3a3a', '#6b6b6b', '#e9e2cf'])}'/>"
    return s


def cuenco(rng, cx, cy, r, liquido, motas=None, remolino=None):
    rr = r * .55
    s = f"<circle cx='{cx + 3:.1f}' cy='{cy + 5:.1f}' r='{rr + 6:.1f}' fill='#000' opacity='.07'/>"
    s += f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{rr + 6:.1f}' fill='#ffffff' stroke='{TRAZO}' stroke-width='1.6'/>"
    s += f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{rr - 2:.1f}' fill='{liquido}' stroke='#00000022' stroke-width='1'/>"
    if remolino:
        s += f"<path d='M{cx - rr * .5:.1f},{cy:.1f} C{cx - rr * .4:.1f},{cy - rr * .5:.1f} {cx + rr * .4:.1f},{cy - rr * .5:.1f} {cx + rr * .3:.1f},{cy:.1f} S{cx - rr * .2:.1f},{cy + rr * .35:.1f} {cx:.1f},{cy + rr * .05:.1f}' fill='none' stroke='{remolino}' stroke-width='3'/>"
    for _ in range(12 if motas else 0):
        a, d = rng.uniform(0, 6.28), rr * .7 * math.sqrt(rng.random())
        s += f"<circle cx='{cx + d * math.cos(a):.1f}' cy='{cy + d * math.sin(a):.1f}' r='1.8' fill='{motas}'/>"
    s += brillo(cx - rr * .3, cy - rr * .35, rr * .25, rr * .1, .5)
    return s


def aceite(rng, cx, cy, r):
    return cuenco(rng, cx, cy, r, "#d8c43a", "#3a3a2a")


def hummus(rng, cx, cy, r):
    return cuenco(rng, cx, cy, r, "#e6c98f", "#b0461c", "#c9a76a")


def yogur_salsa(rng, cx, cy, r):
    return cuenco(rng, cx, cy, r, "#fbfbf3", "#3e8a35", "#e1ded0")


def miel(rng, cx, cy, r):
    return cuenco(rng, cx, cy, r, "#f2b52a", None, "#f8d06a")


def salsa_tomate(rng, cx, cy, r):
    return cuenco(rng, cx, cy, r, "#d9412c", "#3e8a35", "#ef6a50")


def mantequilla_mani(rng, cx, cy, r):
    return cuenco(rng, cx, cy, r, "#b8783c", None, "#cf9356")


def guacamole(rng, cx, cy, r):
    return cuenco(rng, cx, cy, r, "#9cc95a", "#e5412f", "#b6d978")


# ───────────────────────── plato ─────────────────────────

def zonas(n):
    """Centros y radios de las zonas del plato (lienzo 700×700, plato de radio 300)."""
    if n == 1:
        return [(350, 350, 200)]
    if n == 2:
        return [(262, 350, 150), (438, 350, 150)]
    if n == 3:
        return [(350 + 122 * math.cos(math.radians(a)), 350 + 122 * math.sin(math.radians(a)), 142) for a in (215, 325, 90)]
    if n == 4:
        return [(350 + 128 * math.cos(math.radians(a)), 350 + 128 * math.sin(math.radians(a)), 138) for a in (225, 315, 45, 135)]
    raise ValueError(n)


def plato_svg(semilla, dibujos, centro=None):
    """dibujos: lista de funciones (una por zona). centro: función de cuenco central o None.
    Devuelve (svg, posiciones en % para cada dibujo y para el centro)."""
    rng = random.Random(semilla)
    s = ("<svg xmlns='http://www.w3.org/2000/svg' width='700' height='700' viewBox='0 0 700 700'>"
         "<rect width='700' height='700' fill='#ffffff'/>"
         "<ellipse cx='356' cy='362' rx='302' ry='302' fill='#000' opacity='.06'/>"
         f"<circle cx='350' cy='350' r='300' fill='#f6f7f9' stroke='{TRAZO}' stroke-width='2.2'/>"
         "<circle cx='350' cy='350' r='268' fill='#fbfbfc' stroke='#e3e6ea' stroke-width='2'/>")
    pos = []
    for f, (x, y, r) in zip(dibujos, zonas(len(dibujos))):
        s += f(rng, x, y, r)
        pos.append((x / 7, y / 7))
    if centro:
        s += centro(rng, 350, 350, 100)
        pos.append((50.0, 50.0))
    # hierbas sueltas como en las imágenes del catálogo
    for _ in range(14):
        a, d = rng.uniform(0, 6.28), rng.uniform(150, 265)
        x, y = 350 + d * math.cos(a), 350 + d * math.sin(a)
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2.2' fill='#4f9a3a' opacity='.8'/>"
    return s + "</svg>", pos
