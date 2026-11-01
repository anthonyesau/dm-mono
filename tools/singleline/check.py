"""Check the single-line fonts in exports/singleline.

* every OTF contour is a path followed by its exact reverse (zero area), so
  Rhino and CAM software collapse it to one line
* every glyph is 600 units wide and the font passes OTS (if installed)
* the SHX parses (with ezdxf, if installed), has every character of the OTF,
  and its strokes stay within 3 units of the OTF's centre lines
"""

import math
import os
import subprocess
import sys

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "exports", "singleline")
OTF, SHX = os.path.join(D, "DMMonoSingleLine.otf"), os.path.join(D, "DMMonoSingleLine.shx")


def otf_strokes(gs, name, steps=16):
    rp = RecordingPen()
    gs[name].draw(rp)
    strokes, pts, ops = [], [], []
    for op, a in rp.value:
        if op == "moveTo":
            pts, ops = [a[0]], []
        elif op in ("lineTo", "curveTo"):
            ops.append(a)
            if op == "curveTo":
                p0, (c1, c2, p3) = pts[-1], a
                pts += [tuple(((1 - t) ** 3 * p0[k] + 3 * (1 - t) ** 2 * t * c1[k] + 3 * (1 - t) * t * t * c2[k]
                               + t ** 3 * p3[k]) for k in (0, 1)) for t in (i / steps for i in range(1, steps + 1))]
            else:
                pts.append(a[0])
        elif op == "closePath":
            strokes.append((pts, ops))
    return strokes


def seg_dist(q, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / L))
    return math.dist(q, (a[0] + t * dx, a[1] + t * dy))


def main():
    errors = []
    font = TTFont(OTF)
    cmap, gs = font.getBestCmap(), font.getGlyphSet()
    for cp, name in cmap.items():
        for pts, ops in otf_strokes(gs, name):
            ends = [ops[i][-1] for i in range(len(ops))]
            n = len(ops)
            if n % 2 or [pts[0]] + ends != ([pts[0]] + ends)[::-1]:
                errors.append(f"U+{cp:04X} {name}: contour is not an exact out-and-back stroke")
    widths = {w for w, _ in font["hmtx"].metrics.values()}
    if widths != {600}:
        errors.append(f"advance widths {widths}")
    try:
        r = subprocess.run([sys.executable, "-m", "ots", OTF, os.devnull], capture_output=True, text=True)
        if r.returncode:
            errors.append("OTS: " + r.stderr.strip())
    except FileNotFoundError:
        pass

    try:
        from ezdxf.fonts import shapefile
    except ImportError:
        print("ezdxf not installed: skipping SHX checks")
    else:
        shx = shapefile.shx_load(open(SHX, "rb").read())
        unit = 700 / shx.above
        for cp, name in cmap.items():
            if cp <= 32:
                continue
            if cp not in shx.shapes:
                errors.append(f"U+{cp:04X} missing from SHX")
                continue
            segs = [(p[i], p[i + 1]) for p, _ in otf_strokes(gs, name) for i in range(len(p) - 1)]
            path = shx.render_shape(cp)
            if abs(path.end.x * unit - 600) > 0.01 or abs(path.end.y) > 0.01:
                errors.append(f"U+{cp:04X} SHX advance is {path.end}")
            for sub in path.sub_paths():
                for v in sub.flattening(1):
                    q = (v.x * unit, v.y * unit)
                    if segs and min(seg_dist(q, a, b) for a, b in segs) > 3:
                        errors.append(f"U+{cp:04X} SHX stroke strays from the OTF at {q}")
                        break
    print(f"{len(cmap)} characters checked")
    for e in errors:
        print("ERROR", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
