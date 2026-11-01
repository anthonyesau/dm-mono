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


def arrow(tail, tip, head=150, spread=math.radians(28), double=False):
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
R = 233  # circle size of ⌀ ○ ◎ (centre line of the outline version)
_h = 330
_r60 = _h / math.tan(math.radians(60))
G["uni2300"] = [circle(300, AXIS, R), poly((300 - _r60, AXIS - _h), (300 + _r60, AXIS + _h))]
G["whiteCircle"] = [circle(300, AXIS, R)]
G["blackCircle"] = [circle(300, AXIS, r) for r in (R, R * 2 / 3, R / 3)] + [circle(300, AXIS, 8)]
G["bullseye"] = [circle(300, AXIS, R), circle(300, AXIS, 105)]

_cr, _ang, _hh = 155, math.radians(72), 250
_off, _run72 = _cr / math.sin(_ang), _hh / math.tan(_ang)
G["uni232D"] = [circle(300, AXIS, _cr)] + [
    poly((300 + s * _off - _run72, AXIS - _hh), (300 + s * _off + _run72, AXIS + _hh)) for s in (-1, 1)]
G["uni2316"] = [circle(300, AXIS, 140), poly((30, AXIS), (570, AXIS)), poly((300, 80), (300, 620))]
G["uni232F"] = [poly((150, 515), (450, 515)), poly((50, AXIS), (550, AXIS)), poly((150, 185), (450, 185))]
G["uni2312"] = [arc(300, 175, 218, 0, math.pi)]
G["uni2313"] = [arc(300, 175, 218, 0, math.pi), poly((82, 175), (518, 175))]
_aa = math.radians(55)
G["angle"] = [poly((520, 0), (80, 0), (80 + 520 / math.tan(_aa), 520))]
G["measuredangle"] = G["angle"] + [arc(80, 0, 360, 0, _aa)]
G["uni27C2"] = [poly((80, 0), (520, 0)), poly((300, 0), (300, 520))]
G["parallel"] = [poly((205, 0), (205, 700)), poly((395, 0), (395, 700))]
_r2 = 640 / math.tan(SLASH)
G["uni2AFD"] = [poly((cx - _r2 / 2, 30), (cx + _r2 / 2, 670)) for cx in (205, 395)]
G["uni23E4"] = [poly((40, AXIS), (560, AXIS))]
G["uni23E5"] = [poly((70, 215), (395, 215), (530, 485), (205, 485), closed=True)]
_ta = math.radians(66)
_tr = (640 - 110) / math.tan(_ta)
G["uni2330"] = [poly((50, 110), (390, 110))] + sum(
    (arrow((x, 110), (x + _tr, 640), head=120) for x in (100, 340)), [])
_A = 225
G["arrowleft"] = arrow((560, AXIS), (40, AXIS))
G["arrowup"] = arrow((300, 0), (300, 700))
G["arrowright"] = arrow((40, AXIS), (560, AXIS))
G["arrowdown"] = arrow((300, 700), (300, 0))
G["arrowleftright"] = arrow((30, AXIS), (570, AXIS), head=130, double=True)
G["arrowupdown"] = arrow((300, 0), (300, 700), head=130, double=True)
G["arrowupleft"] = arrow((300 + _A, AXIS - _A), (300 - _A, AXIS + _A))
G["arrowupright"] = arrow((300 - _A, AXIS - _A), (300 + _A, AXIS + _A))
G["arrowdownright"] = arrow((300 - _A, AXIS + _A), (300 + _A, AXIS - _A))
G["arrowdownleft"] = arrow((300 + _A, AXIS + _A), (300 - _A, AXIS - _A))
G["uni21A7"] = arrow((300, 700), (300, 0)) + [poly((130, 700), (470, 700))]
G["uni2334"] = [poly((80, 500), (80, 190), (520, 190), (520, 500))]
G["uni2335"] = [poly((75, 465), (300, 240), (525, 465))]
G["uni2332"] = [poly((50, 150), (560, AXIS), (50, 550), closed=True), poly((50, AXIS), (560, AXIS))]
G["uni2333"] = [poly((50, 170), (550, 170), (50, 500), closed=True)]
G["uni232E"] = [circle(370, AXIS, 150)] + arrow((545, AXIS), (40, AXIS), head=130)
G["uni2331"] = [circle(170, AXIS, 95)] + arrow((170, AXIS), (560, AXIS), head=130)
G["uni2104"] = [arc(300, AXIS, 228, math.radians(48), math.radians(312)),
                poly((300, 680), (300, 20), (560, 20))]
_sq = [(112, 162), (488, 162), (488, 538), (112, 538)]
G["whiteSquare"] = [poly(*_sq, closed=True)]
G["blackSquare"] = [poly((112 + i, 162 + i), (488 - i, 162 + i), (488 - i, 538 - i), (112 + i, 538 - i),
                         closed=True) for i in (0, 60, 120, 180)]


def _tri(up, inset=0):
    """Equilateral triangle (side 460) shrunk towards its centroid by `inset` units."""
    h = 230 * math.sqrt(3)
    if up:
        pts = [(70, AXIS - 15 - h / 2), (530, AXIS - 15 - h / 2), (300, AXIS - 15 + h / 2)]
    else:
        pts = [(70, AXIS + 15 + h / 2), (300, AXIS + 15 - h / 2), (530, AXIS + 15 + h / 2)]
    cx = sum(p[0] for p in pts) / 3
    cy = sum(p[1] for p in pts) / 3
    k = 1 - inset / (h / 3)  # inset measured at the inscribed circle
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts]


G["whiteUpPointingTriangle"] = [poly(*_tri(True), closed=True)]
G["whiteDownPointingTriangle"] = [poly(*_tri(False), closed=True)]
G["blackUpPointingTriangle"] = [poly(*_tri(True, i), closed=True) for i in (0, 40, 80, 120)]
G["blackDownPointingTriangle"] = [poly(*_tri(False, i), closed=True) for i in (0, 40, 80, 120)]

# ------------------------------------------------------------- math extras
G["minusplus"] = [poly((80, 488), (520, 488)), poly((80, 170), (520, 170)), poly((300, 0), (300, 340))]
G["equivalence"] = [poly((80, AXIS + d), (520, AXIS + d)) for d in (160, 0, -160)]
G["similar"] = [ref("asciitilde", f=AXIS - 321)]
G["minute"] = [poly((277, 430), (332, 700))]
G["second"] = [poly((277 + d, 430), (332 + d, 700)) for d in (-95, 95)]
G["uni2034"] = [poly((277 + d, 430), (332 + d, 700)) for d in (-160, 0, 160)]
