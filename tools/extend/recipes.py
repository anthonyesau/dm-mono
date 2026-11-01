"""Glyph recipes for the DM Mono technical extension.

Each recipe receives a Ctx for one master and returns a Shape: contours drawn
in upright space plus optional components. All coordinates are for the 600
unit monospaced cell, centred on x=300, math axis at y=350.
"""

import math
from dataclasses import dataclass, field

from geo import (arc_stroke, arrow, circle, hbar, polygon, polygon_outline, rect, ring,
                 slant_line, small_figure, vbar)

AXIS = 350
SLASH_ANGLE = math.atan2(850, 346)  # the angle of DM Mono's own slash


@dataclass
class Shape:
    contours: list = field(default_factory=list)
    components: list = field(default_factory=list)  # (glyphname, dx, dy)


@dataclass
class Ctx:
    font: object
    master_id: str
    master_name: str
    italic: bool
    t: float          # stroke of the math operators (minus, plus)
    ring_t: float     # stroke for enclosing circles
    sup: tuple        # (scale, dx, dy) for superior-size figures
    frac: tuple       # (scale, dx, dy) for fraction-size figures
    narrow: tuple     # (sx, sy, dx, dy) for two-digit circled numbers
    src: object       # src(name, paths=None) -> upright contours


DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
FRAC_CAP = 282     # height of the balloon figures (flat glyphs)
SUP_BOTTOM = 280
INF_SHIFT = -420

RECIPES = []  # (glyphname, unicode or None, fn)


def recipe(name, uni=None):
    def deco(fn):
        RECIPES.append((name, uni, fn))
        return fn
    return deco


def comps(*items):
    return Shape(components=list(items))


# =============================================================== small figures

def frac_figure(ctx, glyph, y_dst=0, cx_dst=300):
    """Small figures for the balloons (282 units tall, like the original ½ ¼ ¾)."""
    s, dx, dy = ctx.frac
    return small_figure(ctx.src(glyph), s, s, dx, dy, cx_dst=cx_dst, y_dst=y_dst)


# Fraction figures: diagonal fractions use figures nearly as tall as the
# superiors (400 units), slightly condensed so a numerator, the slash and a
# denominator fit in one cell. The zero drops its slash: fractions only hold
# figures, and the slash fills the zero's counter at this size.
FR_H, FR_SX = 400, 0.82
NUMR_SHIFT = 300  # numerators sit 300 units above the denominators (300..700)


def plain(ctx, digit):
    cs = ctx.src(digit)
    if digit == "zero":  # drop the slash: the contour made only of straight lines
        cs = [c for c in cs if any(seg is not None for seg in c.segs)]
    return cs


def fr_figure(ctx, digit, sx=FR_SX, cx=300, h=FR_H):
    s0, dx, dy = ctx.sup
    s = (h - 2 * dy) / 700
    out = small_figure(plain(ctx, digit), s * sx, s, dx, dy, y_dst=0)
    b = _bounds(out)
    return [c.translate(cx - (b[0] + b[2]) / 2, 0) for c in out]


def make_dnom(digit):
    @recipe(digit + ".dnom")
    def _(ctx):
        return Shape(fr_figure(ctx, digit))


def make_numr(digit):
    @recipe(digit + ".numr")
    def _(ctx):
        return comps((digit + ".dnom", 0, NUMR_SHIFT))


for _d in DIGITS:
    make_dnom(_d)
    make_numr(_d)

SUPERIOR_NAMES = {"zero": "zerosuperior", "one": "onesuperior", "two": "twosuperior",
                  "three": "threesuperior", "four": "foursuperior", "five": "fivesuperior",
                  "six": "sixsuperior", "seven": "sevensuperior", "eight": "eightsuperior",
                  "nine": "ninesuperior"}
SUP_UNI = {"zero": 0x2070, "four": 0x2074, "five": 0x2075, "six": 0x2076, "seven": 0x2077,
           "eight": 0x2078, "nine": 0x2079, "one": 0xB9, "two": 0xB2, "three": 0xB3}
EXISTING = {"onesuperior", "twosuperior", "threesuperior", "foursuperior"}


def sup_figure(ctx, glyph, src_center=None, dst_center=None):
    s, dx, dy = ctx.sup
    y_dst = SUP_BOTTOM
    if src_center is not None:  # centre a symbol on the superior figures
        y_dst = dst_center - src_center * s - dy
    return small_figure(ctx.src(glyph), s, s, dx, dy, y_dst=y_dst)


def make_sup(digit):
    name = SUPERIOR_NAMES[digit]
    if name in EXISTING:
        return

    @recipe(name, SUP_UNI[digit])
    def _(ctx):
        return Shape(sup_figure(ctx, digit))


for _d in DIGITS:
    make_sup(_d)

SUP_CENTER = SUP_BOTTOM + 210
SYM_SUPS = [("plus", 0x207A, "plus", AXIS), ("minus", 0x207B, "minus", AXIS),
            ("equal", 0x207C, "equal", AXIS), ("parenleft", 0x207D, "parenleft", 313),
            ("parenright", 0x207E, "parenright", 313)]


def make_sym_sup(base, uni, src, center):
    @recipe(base + "superior", uni)
    def _(ctx):
        return Shape(sup_figure(ctx, src, src_center=center, dst_center=SUP_CENTER))


for _a in SYM_SUPS:
    make_sym_sup(*_a)


@recipe("nsuperior", 0x207F)  # ⁿ
def _(ctx):
    return Shape(sup_figure(ctx, "n"))


def make_inf(sup_name, inf_name, uni):
    @recipe(inf_name, uni)
    def _(ctx):
        return comps((sup_name, 0, INF_SHIFT))


for _i, _d in enumerate(DIGITS):
    make_inf(SUPERIOR_NAMES[_d], _d + "inferior", 0x2080 + _i)
for _i, (_base, _u, _s, _c) in enumerate(SYM_SUPS):
    make_inf(_base + "superior", _base + "inferior", 0x208A + _i)


# ================================================================== fractions
# Diagonal fractions in one cell: the numerator sits left and high, the
# denominator right and low, either side of a steep fraction slash. ½ ¼ ¾ are
# redrawn the same way (they replace the designer's stacked versions).

FRACTIONS = [
    ("onequarter", 0xBC, "one", "four"), ("onehalf", 0xBD, "one", "two"),
    ("threequarters", 0xBE, "three", "four"),
    ("oneseventh", 0x2150, "one", "seven"), ("oneninth", 0x2151, "one", "nine"),
    ("onethird", 0x2153, "one", "three"), ("twothirds", 0x2154, "two", "three"),
    ("onefifth", 0x2155, "one", "five"), ("twofifths", 0x2156, "two", "five"),
    ("threefifths", 0x2157, "three", "five"), ("fourfifths", 0x2158, "four", "five"),
    ("onesixth", 0x2159, "one", "six"), ("fivesixths", 0x215A, "five", "six"),
    ("oneeighth", 0x215B, "one", "eight"), ("threeeighths", 0x215C, "three", "eight"),
    ("fiveeighths", 0x215D, "five", "eight"), ("seveneighths", 0x215E, "seven", "eight"),
    ("uni2189", 0x2189, "zero", "three"),
]
REPLACES = {"onehalf", "onequarter", "threequarters"}  # designer glyphs these recipes redraw
FR_DX = 150  # numerator and denominator sit this far either side of the centre
SLASH_FROM, SLASH_TO = (230, 30), (370, 670)


def bar_t(ctx):
    return {"Light": 52, "Medium": 60}[ctx.master_name]


def make_frac(name, uni, num, den):
    @recipe(name, uni)
    def _(ctx):
        return comps((num + ".numr", -FR_DX, 0), ("fraction.inline", 0, 0), (den + ".dnom", FR_DX, 0))


for _f in FRACTIONS:
    make_frac(*_f)


@recipe("onetenth", 0x2152)
def _(ctx):
    # Four figures and a slash have to share 600 units: the numerator 1 is
    # narrower and moves left with the slash, and the "10" is a little
    # shorter (and so narrower) than the other denominators.
    num = [c.translate(0, NUMR_SHIFT) for c in fr_figure(ctx, "one", sx=0.66, cx=100)]
    one, zero = fr_figure(ctx, "one", sx=0.72, cx=0, h=340), fr_figure(ctx, "zero", sx=0.72, cx=0, h=340)
    zb, ob = _bounds(zero), _bounds(one)
    zero = [c.translate(588 - zb[2], 0) for c in zero]
    gap = 12
    one = [c.translate(588 - (zb[2] - zb[0]) - gap - ob[2], 0) for c in one]
    return Shape(num + one + zero + [slant_line((178, 30), (300, 670), bar_t(ctx))])


@recipe("uni215F", 0x215F)  # ⅟ fraction numerator one
def _(ctx):
    return comps(("one.numr", -FR_DX, 0), ("fraction.inline", 0, 0))


@recipe("fraction.inline")  # the steep slash inside one-cell fractions
def _(ctx):
    return Shape([slant_line(SLASH_FROM, SLASH_TO, bar_t(ctx))])


@recipe("fraction.diag")  # the frac feature's slash, alone in its cell, so wider
def _(ctx):
    run = 700 / math.tan(SLASH_ANGLE)
    return Shape([slant_line((300 - run / 2, 0), (300 + run / 2, 700), bar_t(ctx) * 1.1)])


def _place_pair(left, right, gap):
    """Centre two contour groups side by side on x=300."""
    lb = _bounds(left)
    rb = _bounds(right)
    total = (lb[2] - lb[0]) + gap + (rb[2] - rb[0])
    x0 = 300 - total / 2
    out = [c.translate(x0 - lb[0], 0) for c in left]
    x1 = x0 + (lb[2] - lb[0]) + gap
    out += [c.translate(x1 - rb[0], 0) for c in right]
    return out


def _bounds(cs):
    bs = [c.bounds() for c in cs]
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


# ======================================================= enclosed characters

ENC_R = 282


def enclosure(ctx):
    return ring(300, AXIS, ENC_R, ctx.ring_t)


def make_circled_letter(letter, uni):
    @recipe("uni%04X" % uni, uni)
    def _(ctx):
        s, dx, dy = ctx.frac
        s *= 0.97
        inner = small_figure(ctx.src(letter), s, s, dx, dy, y_dst=AXIS - (700 * s + 2 * dy) / 2)
        b = _bounds(inner)
        inner = [c.translate(300 - (b[0] + b[2]) / 2, 0) for c in inner]
        return Shape(enclosure(ctx) + inner)


for _i in range(26):
    make_circled_letter(chr(ord("A") + _i), 0x24B6 + _i)


def make_circled_number(n, uni):
    @recipe("uni%04X" % uni, uni)
    def _(ctx):
        if n < 10:
            d = DIGITS[n]
            inner = frac_figure(ctx, d)
            inner = [c.translate(0, AXIS - FRAC_CAP / 2) for c in inner]
            b = _bounds(inner)
            inner = [c.translate(300 - (b[0] + b[2]) / 2, 0) for c in inner]
        else:
            sx, sy, dx, dy = ctx.narrow
            a, b_ = divmod(n, 10)
            left = small_figure(ctx.src(DIGITS[a]), sx, sy, dx, dy)
            right = small_figure(ctx.src(DIGITS[b_]), sx, sy, dx, dy)
            inner = _place_pair(left, right, gap=6)
            h = 700 * sy + 2 * dy
            inner = [c.translate(0, AXIS - h / 2) for c in inner]
        return Shape(enclosure(ctx) + inner)


make_circled_number(0, 0x24EA)
for _n in range(1, 21):
    make_circled_number(_n, 0x2460 + _n - 1)


# =================================================== GD&T & drafting symbols

# The symbols use the whole monospaced cell: x from about 20 to 580 and,
# where the shape allows, from the baseline up to cap height. Strokes inside
# a shape (crosses, centre lines) are lighter so the counters stay open at
# small sizes.
X0, X1 = 20, 580
CIRCLE_R = 280


def inner(ctx):
    """Stroke for lines that subdivide a shape."""
    return ctx.t * 0.75


@recipe("uni2300", 0x2300)  # ⌀ diameter sign
def _(ctx):
    t = ctx.t
    h = 350
    run = h / math.tan(math.radians(60))
    return Shape(ring(300, AXIS, CIRCLE_R, t)
                 + [slant_line((300 - run, AXIS - h), (300 + run, AXIS + h), t)])


@recipe("emptyset", 0x2205)  # ∅ (often typed in place of ⌀)
def _(ctx):
    return comps(("uni2300", 0, 0))


@recipe("whiteCircle", 0x25CB)  # ○ circularity
def _(ctx):
    return Shape(ring(300, AXIS, CIRCLE_R, ctx.t))


@recipe("blackCircle", 0x25CF)  # ●
def _(ctx):
    return Shape([circle(300, AXIS, CIRCLE_R)])


@recipe("bullseye", 0x25CE)  # ◎ concentricity
def _(ctx):
    t = ctx.t
    return Shape(ring(300, AXIS, CIRCLE_R, t) + ring(300, AXIS, CIRCLE_R * 0.5, t))


@recipe("uni232D", 0x232D)  # ⌭ cylindricity
def _(ctx):
    t = ctx.t
    r = 205
    ang = math.radians(74)
    off = (r - t / 2) / math.sin(ang)  # lines tangent to the circle
    half_h = 320
    run = half_h / math.tan(ang)
    out = ring(300, AXIS, r, t)
    for side in (-1, 1):
        cx = 300 + side * off
        # lighter lines keep the circle readable where they overlap it
        out.append(slant_line((cx - run, AXIS - half_h), (cx + run, AXIS + half_h), inner(ctx)))
    return Shape(out)


@recipe("uni2316", 0x2316)  # ⌖ position
def _(ctx):
    t = ctx.t
    arm = 290
    return Shape(ring(300, AXIS, 205, t)
                 + [hbar(300 - arm, 300 + arm, AXIS, inner(ctx)), vbar(300, AXIS - arm, AXIS + arm, inner(ctx))])


@recipe("uni232F", 0x232F)  # ⌯ symmetry
def _(ctx):
    t = ctx.t
    gap = 190
    return Shape([hbar(120, 480, AXIS + gap, t), hbar(X0, X1, AXIS, t), hbar(120, 480, AXIS - gap, t)])


ARC_BASE, ARC_R = 140, 285


@recipe("uni2312", 0x2312)  # ⌒ arc / profile of a line
def _(ctx):
    return Shape([arc_stroke(300, ARC_BASE, ARC_R, ctx.t, 0, math.pi)])


@recipe("uni2313", 0x2313)  # ⌓ segment / profile of a surface
def _(ctx):
    t = ctx.t
    return Shape([arc_stroke(300, ARC_BASE, ARC_R, t, 0, math.pi),
                  rect(300 - ARC_R, ARC_BASE, 300 + ARC_R, ARC_BASE + t)])


ANGLE_H = 640


def _angle_geom(ctx):
    """Bottom-left start, top-right end and slope of the angle's diagonal."""
    t = ctx.t
    w = t / math.sin(math.radians(55)) / 2  # close enough for the cut width
    p0, p1 = (X0 + w, 0), (X1 - 30 - w, ANGLE_H)
    return p0, p1, math.atan2(p1[1] - p0[1], p1[0] - p0[0])


def _angle(ctx):
    p0, p1, _ = _angle_geom(ctx)
    return [rect(X0, 0, X1, ctx.t), slant_line(p0, p1, ctx.t)]


@recipe("angle", 0x2220)  # ∠ angularity
def _(ctx):
    return Shape(_angle(ctx))


@recipe("measuredangle", 0x2221)  # ∡
def _(ctx):
    t = ctx.t
    r = 400
    _, _, ang = _angle_geom(ctx)
    return Shape(_angle(ctx) + [arc_stroke(X0, 0, r, t, 0, ang - (t / 2) / r)])


@recipe("uni27C2", 0x27C2)  # ⟂ perpendicular
def _(ctx):
    t = ctx.t
    return Shape([rect(X0, 0, X1, t), vbar(300, 0, ANGLE_H, t)])


@recipe("uni22A5", 0x22A5)  # ⊥ up tack
def _(ctx):
    return comps(("uni27C2", 0, 0))


@recipe("parallel", 0x2225)  # ∥
def _(ctx):
    t = ctx.t
    return Shape([vbar(300 - 110, 0, 700, t), vbar(300 + 110, 0, 700, t)])


@recipe("uni2AFD", 0x2AFD)  # ⫽ parallelism as drawn in GD&T frames
def _(ctx):
    t = ctx.t
    h = 700
    y0 = AXIS - h / 2
    run = h / math.tan(SLASH_ANGLE)
    out = []
    for cx in (300 - 100, 300 + 100):
        out.append(slant_line((cx - run / 2, y0), (cx + run / 2, y0 + h), t))
    return Shape(out)


@recipe("uni23E4", 0x23E4)  # ⏤ straightness
def _(ctx):
    return Shape([hbar(X0, X1, AXIS, ctx.t)])


@recipe("uni23E5", 0x23E5)  # ⏥ flatness
def _(ctx):
    h = 380
    run = h / math.tan(math.radians(60))
    y0, y1 = AXIS - h / 2, AXIS + h / 2
    base = (X1 - X0) - run
    pts = [(X0, y0), (X0 + base, y0), (X1, y1), (X1 - base, y1)]
    return Shape(polygon_outline(pts, ctx.t))


def head(ctx, scale=1.0):
    """(length, half width) of an arrowhead for this weight: wide (about 37 degrees
    either side of the shaft) so the heads stay visible at small sizes."""
    hw = (115 + 0.6 * ctx.t) * scale
    return hw * 1.35, hw


@recipe("uni2330", 0x2330)  # ⌰ total runout
def _(ctx):
    t = ctx.t
    y0, y1 = 60, 690
    ang = math.radians(66)
    run = (y1 - y0) / math.tan(ang)
    out = [rect(X0, y0, 380, y0 + t)]
    for x in (50, 270):
        out += arrow((x, y0 + t / 2), (x + run, y1), t, *head(ctx, 0.8))
    return Shape(out)


@recipe("arrowupright", 0x2197)  # ↗ circular runout
def _(ctx):
    a = 245
    return Shape(arrow((300 - a, AXIS - a), (300 + a, AXIS + a), ctx.t, *head(ctx)))


def make_arrow(name, uni, tail, tip, double=False):
    @recipe(name, uni)
    def _(ctx):
        return Shape(arrow(tail, tip, ctx.t, *head(ctx, 0.78 if double else 1.0), double=double))


_A = 245
make_arrow("arrowleft", 0x2190, (X1, AXIS), (X0, AXIS))
make_arrow("arrowup", 0x2191, (300, 0), (300, 700))
make_arrow("arrowright", 0x2192, (X0, AXIS), (X1, AXIS))
make_arrow("arrowdown", 0x2193, (300, 700), (300, 0))
make_arrow("arrowleftright", 0x2194, (X0 - 5, AXIS), (X1 + 5, AXIS), double=True)
make_arrow("arrowupdown", 0x2195, (300, 0), (300, 700), double=True)
make_arrow("arrowupleft", 0x2196, (300 + _A, AXIS - _A), (300 - _A, AXIS + _A))
make_arrow("arrowdownright", 0x2198, (300 - _A, AXIS + _A), (300 + _A, AXIS - _A))
make_arrow("arrowdownleft", 0x2199, (300 + _A, AXIS + _A), (300 - _A, AXIS - _A))


@recipe("uni21A7", 0x21A7)  # ↧ depth
def _(ctx):
    t = ctx.t
    return Shape(arrow((300, 700 - t / 2), (300, 0), t, *head(ctx)) + [rect(110, 700 - t, 490, 700)])


@recipe("uni2334", 0x2334)  # ⌴ counterbore / spotface
def _(ctx):
    t = ctx.t
    y0, y1 = 130, 570
    return Shape([rect(X0 + 10, y0, X0 + 10 + t, y1), rect(X1 - 10 - t, y0, X1 - 10, y1),
                  rect(X0 + 10, y0, X1 - 10, y0 + t)])


@recipe("uni2335", 0x2335)  # ⌵ countersink
def _(ctx):
    t = ctx.t
    H = 270
    y0 = AXIS - H / 2 - 10
    w = t * math.sqrt(2)
    return Shape([polygon([(300, y0), (300 + H, y0 + H), (300 + H - w, y0 + H), (300, y0 + w),
                           (300 - H + w, y0 + H), (300 - H, y0 + H)])])


@recipe("uni2332", 0x2332)  # ⌲ conical taper
def _(ctx):
    t = ctx.t
    h = 560
    pts = [(X0, AXIS - h / 2), (X1 + 5, AXIS), (X0, AXIS + h / 2)]
    return Shape(polygon_outline(pts, t * 0.9) + [hbar(X0, 470, AXIS, inner(ctx) * 0.85)])


@recipe("uni2333", 0x2333)  # ⌳ slope
def _(ctx):
    pts = [(X0, 80), (X1, 80), (X0, 590)]
    return Shape(polygon_outline(pts, ctx.t * 0.9))


@recipe("uni232E", 0x232E)  # ⌮ all around-profile
def _(ctx):
    t = ctx.t
    r = 195
    return Shape(ring(X1 - r, AXIS, r, t) + arrow((X1 - 5, AXIS), (X0 - 5, AXIS), inner(ctx), *head(ctx, 0.9)))


@recipe("uni2331", 0x2331)  # ⌱ dimension origin
def _(ctx):
    # The circle marks the origin: it is centred where the extension line
    # (vertical) meets the dimension line, which runs from that point to the
    # arrowhead. Inner lines are lighter so the circle stays readable.
    t = ctx.t
    r = 165
    cx = X0 + r
    return Shape(ring(cx, AXIS, r, t) + [vbar(cx, AXIS - 290, AXIS + 290, inner(ctx))]
                 + arrow((cx, AXIS), (X1 + 5, AXIS), inner(ctx), *head(ctx, 0.72)))


@recipe("uni2104", 0x2104)  # ℄ centre line
def _(ctx):
    t = ctx.t
    r, cy = 250, 410  # the C sits high, clear of the L's foot
    out = [arc_stroke(290, cy, r, t, math.radians(45), math.radians(315))]
    out += [vbar(300, 0, 700, t), rect(300 - t / 2, 0, X1, t)]
    return Shape(out)


SQ = (40, 70, 560, 630)


@recipe("whiteSquare", 0x25A1)  # □ square
def _(ctx):
    x0, y0, x1, y1 = SQ
    return Shape(polygon_outline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ctx.t))


@recipe("blackSquare", 0x25A0)  # ■
def _(ctx):
    return Shape([rect(*SQ)])


def _tri(up=True):
    w = 270
    h = 2 * w * math.sqrt(3) / 2
    y0 = AXIS - h / 2 + (-15 if up else 15)
    if up:
        return [(300 - w, y0), (300 + w, y0), (300, y0 + h)]
    return [(300 - w, y0 + h), (300, y0), (300 + w, y0 + h)]


@recipe("blackUpPointingTriangle", 0x25B2)
def _(ctx):
    return Shape([polygon(_tri(True))])


@recipe("whiteUpPointingTriangle", 0x25B3)
def _(ctx):
    return Shape(polygon_outline(_tri(True), ctx.t))


@recipe("blackDownPointingTriangle", 0x25BC)
def _(ctx):
    return Shape([polygon(_tri(False))])


@recipe("whiteDownPointingTriangle", 0x25BD)
def _(ctx):
    return Shape(polygon_outline(_tri(False), ctx.t))


# ================================================================ math extras

@recipe("minusplus", 0x2213)  # ∓
def _(ctx):
    cs = ctx.src("plusminus")
    b = _bounds(cs)
    return Shape([c.affine(1, 0, 0, -1, 0, b[1] + b[3]) for c in cs])


@recipe("equivalence", 0x2261)  # ≡
def _(ctx):
    t = ctx.t
    gap = 160
    return Shape([hbar(80, 520, AXIS + d, t) for d in (gap, 0, -gap)])


@recipe("similar", 0x223C)  # ∼ tilde operator
def _(ctx):
    b = _bounds(ctx.src("asciitilde"))
    return comps(("asciitilde", 0, round(AXIS - (b[1] + b[3]) / 2)))


@recipe("dotmath", 0x22C5)  # ⋅
def _(ctx):
    return comps(("periodcentered", 0, 0))


@recipe("uni2219", 0x2219)  # ∙
def _(ctx):
    return comps(("periodcentered", 0, 0))


def _prime_pts(cx_top, ctx):
    stem = ctx.t * 1.09
    top_w, bot_w = stem * 1.25, stem * 0.55
    y0, y1 = 430, 700
    cx_bot = cx_top - 55
    return polygon([(cx_bot - bot_w / 2, y0), (cx_bot + bot_w / 2, y0),
                    (cx_top + top_w / 2, y1), (cx_top - top_w / 2, y1)])


@recipe("minute", 0x2032)  # ′ prime (feet, arc minutes)
def _(ctx):
    return Shape([_prime_pts(332, ctx)])


@recipe("second", 0x2033)  # ″ double prime (inches, arc seconds)
def _(ctx):
    return Shape([_prime_pts(332 + d, ctx) for d in (-95, 95)])


@recipe("uni2034", 0x2034)  # ‴ triple prime
def _(ctx):
    return Shape([_prime_pts(332 + d, ctx) for d in (-160, 0, 160)])


# ================================================== aliases of existing glyphs

def alias(name, uni, base, dy=0):
    @recipe(name, uni)
    def _(ctx):
        return comps((base, 0, dy))


alias("Omega", 0x03A9, "Ohm")
alias("Delta", 0x0394, "increment")
alias("mu", 0x03BC, "micro")
alias("uni2010", 0x2010, "hyphen")
alias("uni2011", 0x2011, "hyphen")
alias("figuredash", 0x2012, "endash")
alias("uni2015", 0x2015, "emdash")


def blank(name, uni):
    @recipe(name, uni)
    def _(ctx):
        return Shape()


blank("figurespace", 0x2007)
blank("thinspace", 0x2009)
blank("uni202F", 0x202F)
