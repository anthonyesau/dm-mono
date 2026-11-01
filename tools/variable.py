"""Finish a fontmake variable build of DM Mono.

usage: python variable.py IN.ttf OUT.ttf [--italic]

* pins the unused `ital` axis that the Glyphs sources declare (each file
  only has masters at one italic position), which removes it
* makes Regular (wght 400) the default instance, so apps without variable
  font support show Regular rather than Light
* writes a STAT table linking the upright and italic families
* sets the monospace flags and the unhinted-font gasp/prep tables
"""

import argparse

from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib.instancer import instantiateVariableFont

FAMILY = "DM Mono"
WEIGHTS = [(300, "Light"), (400, "Regular"), (500, "Medium")]


def finish(src, dst, italic):
    font = TTFont(src)
    axes = {a.axisTag: a for a in font["fvar"].axes}
    limits = {"wght": (axes["wght"].minValue, 400, axes["wght"].maxValue)}
    if "ital" in axes:
        limits["ital"] = axes["ital"].defaultValue  # all masters sit here
    font = instantiateVariableFont(font, limits, updateFontNames=False)

    name = font["name"]
    style = "Italic" if italic else "Regular"
    ps_family = "DMMono" + ("Italic" if italic else "")

    # default instance is now Regular / Italic
    for nid, value in ((1, FAMILY), (2, style), (4, f"{FAMILY} {style}"),
                       (6, "DMMono-" + style), (16, FAMILY), (17, style), (25, ps_family)):
        name.setName(value, nid, 3, 1, 0x409)
    for nid in (16, 17):
        name.removeNames(nameID=nid)
    font["OS/2"].usWeightClass = 400
    fs = font["OS/2"].fsSelection & ~(0x01 | 0x20 | 0x40)
    font["OS/2"].fsSelection = fs | (0x01 if italic else 0x40)
    font["head"].macStyle = 0x02 if italic else 0

    # named instances
    for inst in font["fvar"].instances:
        wght = inst.coordinates["wght"]
        label = dict(WEIGHTS)[wght]
        sub = (f"{label} Italic" if label != "Regular" else "Italic") if italic else label
        inst.subfamilyNameID = name.addName(sub)
        inst.postscriptNameID = name.addName("DMMono-" + sub.replace(" ", ""))

    axes_stat = [
        dict(tag="wght", name="Weight", ordering=0,
             values=[dict(value=v, name=n, **({"flags": 0x2} if v == 400 else {}))
                     for v, n in WEIGHTS]),
        dict(tag="ital", name="Italic", ordering=1,
             values=[dict(value=1, name="Italic")] if italic else
             [dict(value=0, name="Roman", flags=0x2, linkedValue=1)]),
    ]
    buildStatTable(font, axes_stat, elidedFallbackName=2)

    # monospace
    font["post"].isFixedPitch = 1
    font["OS/2"].panose.bProportion = 9
    widths = {w for w, _ in font["hmtx"].metrics.values() if w}
    assert widths == {600}, widths
    font["hhea"].advanceWidthMax = 600

    # unhinted: smooth rendering at all sizes, like gftools fix-nonhinting
    gasp = newTable("gasp")
    gasp.gaspRange = {0xFFFF: 0x000F}
    font["gasp"] = gasp
    if "prep" not in font:
        from fontTools.ttLib.tables import ttProgram
        prep = newTable("prep")
        prep.program = ttProgram.Program()
        prep.program.fromAssembly(["PUSHW[]", "511", "SCANCTRL[]", "PUSHB[]", "4", "SCANTYPE[]"])
        font["prep"] = prep
    font["head"].flags |= 1 << 3

    font.save(dst)
    print("wrote", dst)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--italic", action="store_true")
    a = ap.parse_args()
    finish(a.src, a.dst, a.italic)
