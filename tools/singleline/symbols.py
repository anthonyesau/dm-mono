"""Single-line versions of the glyphs added by tools/extend (v1.100).

Registers centre-line drawings in skeleton.G. Glyphs that DM Mono builds
from components (numerators, inferiors, most fractions, aliases) need no
entry here: build.py composes them from the Glyphs source.
"""

import math

import skeleton as SK
from skeleton import G, circle, ref

AXIS = 350
SLASH = math.atan2(850, 346)
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def poly(*pts, closed=False):
    d = "M%g %g " % pts[0] + " ".join("L%g %g" % p for p in pts[1:])
    return d + (" Z" if closed else "")


def arc(cx, cy, r, a0, a1):
    """Circular arc from angle a0 to a1 (radians, counter-clockwise)."""
    n = max(1, math.ceil(abs(a1 - a0) / (math.pi / 2) - 1e-9))
    step = (a1 - a0) / n
    h = 4 / 3 * math.tan(step / 4) * r
    pts = [(cx + r * math.cos(a0 + i * step), cy + r * math.sin(a0 + i * step)) for i in range(n + 1)]
    d = "M%g %g" % pts[0]
    for i in range(n):
        a, b = a0 + i * step, a0 + (i + 1) * step
        p0, p1 = pts[i], pts[i + 1]
        d += " C%g %g %g %g %g %g" % (p0[0] - h * math.sin(a), p0[1] + h * math.cos(a),
                                       p1[0] + h * math.sin(b), p1[1] - h * math.cos(b), *p1)
    return d


def arrow(tail, tip, head=150, spread=math.radians(37), double=False):
    """Shaft plus open arrowhead(s): the usual single-line drafting arrow."""
    dx, dy = tip[0] - tail[0], tip[1] - tail[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L

    def heads(p, ux, uy):
        out = []
        for s in (spread, -spread):
            c, si = math.cos(s), math.sin(s)
            bx, by = -(ux * c - uy * si), -(ux * si + uy * c)
            out.append(poly((p[0] + bx * head, p[1] + by * head), p))
        return out

    out = [poly(tail, tip)] + heads(tip, ux, uy)
    if double:
        out += heads(tail, -ux, -uy)
    return out


def bbox(name):
    xs, ys = [], []
    for p in SK.polylines(name):
        xs += [q[0] for q in p]
        ys += [q[1] for q in p]
    return min(xs), min(ys), max(xs), max(ys)


# ---------------------------------------------------------- small figures
FRAC_SX, FRAC_SY = 0.45, 0.403      # 700-unit figures -> 282-unit fraction figures
SUP = 0.6                           # superiors: 420 units tall, bottom at 280

for d in DIGITS:
    G[d + ".dnom"] = [ref(d, FRAC_SX, 0, 0, FRAC_SY, 300 - 300 * FRAC_SX, 0)]
    G[d + "superior"] = [ref(d, SUP, 0, 0, SUP, 300 - 300 * SUP, 280)]
for name, src, center in (("plus", "plus", AXIS), ("minus", "minus", AXIS), ("equal", "equal", AXIS),
                          ("parenleft", "parenleft", 313), ("parenright", "parenright", 313)):
    G[name + "superior"] = [ref(src, SUP, 0, 0, SUP, 300 - 300 * SUP, 490 - center * SUP)]
G["nsuperior"] = [ref("n", SUP, 0, 0, SUP, 300 - 300 * SUP, 280)]

# the original stacked fractions, redrawn from the fraction figures
for name, num, den in (("onehalf", "one", "two"), ("onequarter", "one", "four"),
                       ("threequarters", "three", "four")):
    G[name] = [ref(num + ".dnom", f=417), ref("fraction"), ref(den + ".dnom")]

_run = 700 / math.tan(SLASH)
G["fraction.diag"] = [poly((300 - _run / 2, 0), (300 + _run / 2, 700))]
_n = 0.33  # narrower figures for the "10" under the bar
G["onetenth"] = [ref("one.dnom", f=417), ref("fraction"),
                 ref("one", _n, 0, 0, FRAC_SY, 205 - 300 * _n, 0),
                 ref("zero", _n, 0, 0, FRAC_SY, 395 - 300 * _n, 0)]


# --------------------------------------------------- enclosed characters
ENC_R = 255


def enclosed(src, scale, sx=None, x_center=300):
    sx = scale if sx is None else sx
    x0, y0, x1, y1 = bbox(src)
    cx = (x0 + x1) / 2
    return ref(src, sx, 0, 0, scale, x_center - cx * sx, AXIS - 350 * scale)


for i in range(26):
    letter = chr(ord("A") + i)
    G["uni%04X" % (0x24B6 + i)] = [circle(300, AXIS, ENC_R), enclosed(letter, 0.36)]
G["uni24EA"] = [circle(300, AXIS, ENC_R), enclosed("zero", 0.40, sx=0.45)]
for n in range(1, 21):
    name = "uni%04X" % (0x2460 + n - 1)
    if n < 10:
        G[name] = [circle(300, AXIS, ENC_R), enclosed(DIGITS[n], 0.40, sx=0.45)]
    else:
        a, b = divmod(n, 10)
        G[name] = [circle(300, AXIS, ENC_R), enclosed(DIGITS[a], 0.30, sx=0.26, x_center=228),
                   enclosed(DIGITS[b], 0.30, sx=0.26, x_center=372)]


# ------------------------------------------------- drafting and GD&T
# Same layout as the outline symbols (tools/extend/recipes.py): the shapes
# use x 20-580 and up to cap height; lines here sit on the stroke centres.
R = 265  # circle size of ⌀ ○ ◎
_h = 345
_r60 = _h / math.tan(math.radians(60))
G["uni2300"] = [circle(300, AXIS, R), poly((300 - _r60, AXIS - _h), (300 + _r60, AXIS + _h))]
G["whiteCircle"] = [circle(300, AXIS, R)]
G["blackCircle"] = [circle(300, AXIS, r) for r in (R, R * 2 / 3, R / 3)] + [circle(300, AXIS, 8)]
G["bullseye"] = [circle(300, AXIS, R), circle(300, AXIS, 135)]

_cr, _ang, _hh = 180, math.radians(74), 320
_off, _run74 = _cr / math.sin(_ang), _hh / math.tan(_ang)
G["uni232D"] = [circle(300, AXIS, _cr)] + [
    poly((300 + s * _off - _run74, AXIS - _hh), (300 + s * _off + _run74, AXIS + _hh)) for s in (-1, 1)]
G["uni2316"] = [circle(300, AXIS, 190), poly((15, AXIS), (585, AXIS)), poly((300, 65), (300, 635))]
G["uni232F"] = [poly((120, 540), (480, 540)), poly((20, AXIS), (580, AXIS)), poly((120, 160), (480, 160))]
G["uni2312"] = [arc(300, 140, 270, 0, math.pi)]
G["uni2313"] = [arc(300, 140, 270, 0, math.pi), poly((30, 140), (570, 140))]
_ap = (550, 640)
_aa = math.atan2(_ap[1], _ap[0] - 20)
G["angle"] = [poly((580, 0), (20, 0), _ap)]
G["measuredangle"] = G["angle"] + [arc(20, 0, 400, 0, _aa)]
G["uni27C2"] = [poly((20, 0), (580, 0)), poly((300, 0), (300, 640))]
G["parallel"] = [poly((190, 0), (190, 700)), poly((410, 0), (410, 700))]
_r2 = 700 / math.tan(SLASH)
G["uni2AFD"] = [poly((cx - _r2 / 2, 0), (cx + _r2 / 2, 700)) for cx in (200, 400)]
G["uni23E4"] = [poly((20, AXIS), (580, AXIS))]
G["uni23E5"] = [poly((40, 180), (360, 180), (560, 520), (240, 520), closed=True)]
_ta = math.radians(66)
_tr = (690 - 60) / math.tan(_ta)
G["uni2330"] = [poly((20, 60), (380, 60))] + sum(
    (arrow((x, 60), (x + _tr, 690), head=120) for x in (60, 290)), [])
_A = 245
G["arrowleft"] = arrow((580, AXIS), (20, AXIS))
G["arrowup"] = arrow((300, 0), (300, 700))
G["arrowright"] = arrow((20, AXIS), (580, AXIS))
G["arrowdown"] = arrow((300, 700), (300, 0))
G["arrowleftright"] = arrow((15, AXIS), (585, AXIS), head=130, double=True)
G["arrowupdown"] = arrow((300, 0), (300, 700), head=130, double=True)
G["arrowupleft"] = arrow((300 + _A, AXIS - _A), (300 - _A, AXIS + _A))
G["arrowupright"] = arrow((300 - _A, AXIS - _A), (300 + _A, AXIS + _A))
G["arrowdownright"] = arrow((300 - _A, AXIS + _A), (300 + _A, AXIS - _A))
G["arrowdownleft"] = arrow((300 + _A, AXIS + _A), (300 - _A, AXIS - _A))
G["uni21A7"] = arrow((300, 700), (300, 0)) + [poly((110, 700), (490, 700))]
G["uni2334"] = [poly((45, 570), (45, 140), (555, 140), (555, 570))]
G["uni2335"] = [poly((45, 470), (300, 215), (555, 470))]
G["uni2332"] = [poly((30, 80), (575, AXIS), (30, 620), closed=True), poly((30, AXIS), (480, AXIS))]
G["uni2333"] = [poly((30, 95), (565, 95), (30, 575), closed=True)]
G["uni232E"] = [circle(385, AXIS, 180)] + arrow((575, AXIS), (20, AXIS), head=130)
# circle centred on the origin, crossed by the extension line; the dimension
# line runs from the centre to the arrowhead
G["uni2331"] = [circle(185, AXIS, 150), poly((185, 60), (185, 640))] + arrow((185, AXIS), (580, AXIS), head=120)
# the C sits high, clear of the L's foot
G["uni2104"] = [arc(290, 410, 235, math.radians(45), math.radians(315)),
                poly((300, 700), (300, 0), (580, 0))]
_sq = [(70, 100), (530, 100), (530, 600), (70, 600)]
G["whiteSquare"] = [poly(*_sq, closed=True)]
G["blackSquare"] = [poly((70 + i, 100 + i), (530 - i, 100 + i), (530 - i, 600 - i), (70 + i, 600 - i),
                         closed=True) for i in (0, 60, 120, 180)]


def _tri(up, inset=0):
    """Equilateral triangle (side 510) shrunk towards its centroid by `inset` units."""
    w = 255
    h = w * math.sqrt(3)
    if up:
        pts = [(300 - w, AXIS - 15 - h / 2), (300 + w, AXIS - 15 - h / 2), (300, AXIS - 15 + h / 2)]
    else:
        pts = [(300 - w, AXIS + 15 + h / 2), (300, AXIS + 15 - h / 2), (300 + w, AXIS + 15 + h / 2)]
    cx = sum(p[0] for p in pts) / 3
    cy = sum(p[1] for p in pts) / 3
    k = 1 - inset / (h / 3)  # inset measured at the inscribed circle
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts]


G["whiteUpPointingTriangle"] = [poly(*_tri(True), closed=True)]
G["whiteDownPointingTriangle"] = [poly(*_tri(False), closed=True)]
G["blackUpPointingTriangle"] = [poly(*_tri(True, i), closed=True) for i in (0, 45, 90, 135)]
G["blackDownPointingTriangle"] = [poly(*_tri(False, i), closed=True) for i in (0, 45, 90, 135)]

# ------------------------------------------------------------- math extras
G["minusplus"] = [poly((80, 488), (520, 488)), poly((80, 170), (520, 170)), poly((300, 0), (300, 340))]
G["equivalence"] = [poly((80, AXIS + d), (520, AXIS + d)) for d in (160, 0, -160)]
G["similar"] = [ref("asciitilde", f=AXIS - 321)]
G["minute"] = [poly((277, 430), (332, 700))]
G["second"] = [poly((277 + d, 430), (332 + d, 700)) for d in (-95, 95)]
G["uni2034"] = [poly((277 + d, 430), (332 + d, 700)) for d in (-160, 0, 160)]
