"""Build DM Mono Single Line: a centre-line (stroke) version of DM Mono.

usage: python build.py [outdir]     (default: exports/singleline)

Writes
  DMMonoSingleLine.otf  every stroke drawn out and back along itself, the
                        "double-stroke" convention that Rhino (TextObject),
                        Fusion, VCarve and most CAM software read as a
                        single line
  DMMonoSingleLine.shx  AutoCAD shape font with true open strokes, for
                        LightBurn and AutoCAD

Glyph shapes come from skeleton.py (letters, figures, punctuation) and
symbols.py (the technical-symbol extension); everything DM Mono builds from
components (accented letters, numerators, ...) is composed the same way here.
"""

import math
import os
import struct
import sys

import glyphsLib
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)

import skeleton as SK  # noqa: E402
import symbols  # noqa: E402,F401  (registers the extension glyphs)

FAMILY = "DM Mono Single Line"
PS_NAME = "DMMonoSingleLine-Regular"
VERSION = "1.100"
ADVANCE = 600
SOURCE = os.path.join(ROOT, "source", "DMMono-MASTER.glyphs")

# Skeletons that only hold the strokes a glyph adds to its components.
PARTIAL = {"Ldot", "Lslash", "Oslash", "Q", "dcroat", "lslash", "oslash", "exclam", "question",
           "greaterequal", "lessequal", "plusminus"}


# ----------------------------------------------------------------- assembly

class Assembler:
    def __init__(self, font):
        self.font = font
        self.master = font.masters[0].id  # Light: the skeletons follow its stroke centres
        self.cache = {}

    def components(self, name):
        g = self.font.glyphs[name]
        if g is None:
            return []
        return [(c.name, tuple(c.transform)) for c in g.layers[self.master].components]

    def draw(self, name, pen):
        """Draw the glyph's centre lines into pen. Returns False if unknown."""
        if SK.has(name):
            SK.draw(name, pen)
            if name not in PARTIAL:
                return True
            comps = self.components(name)
        else:
            comps = self.components(name)
            if not comps:
                g = self.font.glyphs[name]
                # spaces and other blank glyphs are fine; anything drawn is not
                return g is not None and not g.layers[self.master].paths
        for cname, t in comps:
            if not self.draw(cname, TransformPen(pen, t)):
                raise KeyError(f"{name}: component {cname} has no single-line drawing")
        return True

    def subpaths(self, name):
        """[(closed, start, [segments])] with integer coordinates; None if unknown."""
        if name in self.cache:
            return self.cache[name]
        pen = RecordingPen()
        if not self.draw(name, pen):
            self.cache[name] = None
            return None
        out = []
        for closed, segs in SK.subpaths(pen.value):
            start = _pt(segs[0][1][0])
            path, cur = [], start
            for op, args in segs[1:]:
                if op == "lineTo":
                    p = _pt(args[0])
                    if p != cur:
                        path.append(("line", p))
                        cur = p
                elif op == "curveTo":
                    c1, c2, p = (_pt(a) for a in args)
                    path.append(("curve", c1, c2, p))
                    cur = p
                else:
                    raise ValueError(f"{name}: unsupported segment {op}")
            if closed and cur != start:
                path.append(("line", start))
            if path:
                out.append((closed, start, path))
        self.cache[name] = out
        return out


def _pt(p):
    return (int(round(p[0])), int(round(p[1])))


def glyph_list(font):
    """(name, [codepoints]) for every encoded glyph, in source order."""
    out = []
    for g in font.glyphs:
        unis = [int(u, 16) for u in (g.unicodes or [])]
        if unis and g.export:
            out.append((g.name, unis))
    return out


# ----------------------------------------------------------------- OTF

def draw_out_and_back(subpaths, pen):
    for closed, start, segs in subpaths:
        pen.moveTo(start)
        pts = [start]
        for seg in segs:
            if seg[0] == "line":
                pen.lineTo(seg[1])
            else:
                pen.curveTo(seg[1], seg[2], seg[3])
            pts.append(seg[-1])
        for i in range(len(segs) - 1, -1, -1):
            seg, back = segs[i], pts[i]
            if seg[0] == "line":
                pen.lineTo(back)
            else:
                pen.curveTo(seg[2], seg[1], back)
        pen.closePath()


def bounds(subpaths):
    xs, ys = [], []
    for closed, start, segs in subpaths:
        for p in [start] + [q for s in segs for q in s[1:]]:
            xs.append(p[0])
            ys.append(p[1])
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def build_otf(glyphs, path):
    order = [".notdef", "space"] + [n for n, _, _ in glyphs if n != "space"]
    cmap = {0x20: "space", 0xA0: "space"}
    charstrings, metrics = {}, {}

    nd = T2CharStringPen(ADVANCE, None)
    draw_out_and_back([(True, (100, 0), [("line", (500, 0)), ("line", (500, 700)),
                                         ("line", (100, 700)), ("line", (100, 0))])], nd)
    charstrings[".notdef"] = nd.getCharString(optimize=False)
    metrics[".notdef"] = (ADVANCE, 100)
    for name, unis, sub in [("space", [0x20], [])] + glyphs:
        for u in unis:
            cmap[u] = name
        if name in charstrings:
            continue
        pen = T2CharStringPen(ADVANCE, None)
        draw_out_and_back(sub, pen)
        # optimize=False: the specializer merges a line and its exact reverse
        # into one zero-length line, which would erase every straight stroke
        charstrings[name] = pen.getCharString(optimize=False)
        b = bounds(sub)
        metrics[name] = (ADVANCE, b[0] if b else 0)

    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupCFF(PS_NAME, {"FullName": FAMILY, "FamilyName": FAMILY, "Weight": "Regular",
                          "isFixedPitch": True}, charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=992, descent=-310)
    fb.setupNameTable({
        "copyright": "Copyright 2020 The DM Mono Project Authors (https://www.github.com/googlefonts/dm-mono)",
        "familyName": FAMILY,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{VERSION};{PS_NAME}",
        "fullName": FAMILY,
        "version": f"Version {VERSION}",
        "psName": PS_NAME,
        "description": "Single-line (centre-line) version of DM Mono for engraving, CNC and plotting. "
                       "Each stroke is drawn out and back along itself.",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
                              "This license is available with a FAQ at: https://openfontlicense.org",
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fb.setupOS2(sTypoAscender=992, sTypoDescender=-310, sTypoLineGap=0, usWinAscent=992,
                usWinDescent=310, sxHeight=496, sCapHeight=700, usWeightClass=400,
                achVendID="CF  ", fsType=0, fsSelection=0x40,
                panose=_panose())
    fb.setupPost(isFixedPitch=1, underlinePosition=-100, underlineThickness=50)
    fb.font["head"].fontRevision = float(VERSION)
    fb.save(path)


def _panose():
    from fontTools.ttLib.tables.O_S_2f_2 import Panose
    p = Panose()
    for k, v in dict(bFamilyType=2, bSerifStyle=11, bWeight=5, bProportion=9, bContrast=2,
                     bStrokeVariation=2, bArmStyle=1, bLetterForm=4, bMidline=1, bXHeight=3).items():
        setattr(p, k, v)
    return p


# ----------------------------------------------------------------- SHX
# Units: 1 shape unit = 5 font units, and every shape starts by halving
# vector lengths, so coordinates are stored on a 2.5-unit grid.
SHX_UNIT = 5.0
GRID = SHX_UNIT / 2
ABOVE, BELOW = round(700 / SHX_UNIT), round(220 / SHX_UNIT)


def flatten_segments(start, segs, tol=4.0):
    pts = [start]
    for seg in segs:
        if seg[0] == "line":
            pts.append(seg[1])
            continue
        p0, (c1, c2, p3) = pts[-1], seg[1:]
        length = math.dist(p0, c1) + math.dist(c1, c2) + math.dist(c2, p3)
        n = max(3, math.ceil(length / 22))
        for i in range(1, n + 1):
            t = i / n
            mt = 1 - t
            pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t ** 3 * p3[0],
                        mt ** 3 * p0[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t ** 3 * p3[1]))
    return pts


def _steps(dx, dy):
    """Split a displacement into pieces that fit signed bytes (and are never 0,0)."""
    n = max(1, math.ceil(max(abs(dx), abs(dy)) / 127))
    out, px, py = [], 0, 0
    for i in range(1, n + 1):
        x, y = round(dx * i / n), round(dy * i / n)
        out.append((x - px, y - py))
        px, py = x, y
    return [s for s in out if s != (0, 0)]


def _b(v):
    return v & 0xFF


def shx_codes(subpaths):
    codes = [3, 2]  # halve vector lengths: 2.5 font units per step
    cur = (0, 0)
    for closed, start, segs in subpaths:
        pts = [(round(x / GRID), round(y / GRID)) for x, y in flatten_segments(start, segs)]
        pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        codes.append(2)  # pen up
        for dx, dy in _steps(pts[0][0] - cur[0], pts[0][1] - cur[1]):
            codes += [8, _b(dx), _b(dy)]
        codes.append(1)  # pen down
        if len(pts) == 1:
            codes += [8, 0, 0]
        else:
            codes.append(9)
            for a, b in zip(pts, pts[1:]):
                for dx, dy in _steps(b[0] - a[0], b[1] - a[1]):
                    codes += [_b(dx), _b(dy)]
            codes += [0, 0]
        cur = pts[-1]
    codes.append(2)
    for dx, dy in _steps(round(ADVANCE / GRID) - cur[0], -cur[1]):
        codes += [8, _b(dx), _b(dy)]
    codes += [4, 2, 0]  # restore scale, end of shape
    return codes


def build_shx(glyphs, path):
    shapes = {0: FAMILY.encode() + b"\0" + bytes([ABOVE, BELOW, 0, 0])}
    shapes[10] = b"lf\0" + bytes([2, 8, 0, _b(-120), 8, 0, _b(-120), 0])
    shapes[32] = b"space\0" + bytes([2, 8, 120, 0, 0])
    for name, unis, sub in glyphs:
        codes = bytes(shx_codes(sub))
        if len(codes) > 2000:
            raise ValueError(f"{name}: shape too long for SHX ({len(codes)} bytes)")
        for u in unis:
            if u <= 0xFFFF and u not in shapes:
                shapes[u] = name.encode("ascii", "replace")[:30] + b"\0" + codes
    numbers = sorted(shapes)
    out = bytearray(b"AutoCAD-86 shapes 1.0\r\n\x1a")
    out += struct.pack("<HHH", numbers[0], numbers[-1], len(numbers))
    for n in numbers:
        out += struct.pack("<HH", n, len(shapes[n]))
    for n in numbers:
        out += shapes[n]
    out += b"EOF"
    with open(path, "wb") as f:
        f.write(out)


# ----------------------------------------------------------------- main

def collect():
    font = glyphsLib.GSFont(SOURCE)
    asm = Assembler(font)
    glyphs, missing = [], []
    for name, unis in glyph_list(font):
        if name == "space":
            continue
        sub = asm.subpaths(name)
        if sub is None:
            missing.append(name)
            continue
        glyphs.append((name, unis, sub))
    return glyphs, missing


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "exports", "singleline")
    os.makedirs(outdir, exist_ok=True)
    glyphs, missing = collect()
    if missing:
        print("no single-line drawing for:", " ".join(missing))
    build_otf(glyphs, os.path.join(outdir, "DMMonoSingleLine.otf"))
    build_shx(glyphs, os.path.join(outdir, "DMMonoSingleLine.shx"))
    print(f"{len(glyphs)} glyphs written to {outdir}")


if __name__ == "__main__":
    main()
