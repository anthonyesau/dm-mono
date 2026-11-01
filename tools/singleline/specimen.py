"""Render docs/single-line.png by stroking the centre lines of the OTF.

(Normal text rendering shows nothing: every glyph encloses zero area.)
"""

import os

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OTF = os.path.join(ROOT, "exports", "singleline", "DMMonoSingleLine.otf")
OUT = os.path.join(ROOT, "docs", "single-line.png")

LINES = [
    (64, "DM Mono Single Line"),
    (40, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    (40, "abcdefghijklmnopqrstuvwxyz"),
    (40, "0123456789 ½¼¾⅛⅜⅝⅞ ¹²³ ₀₁₂"),
    (40, "ÀÉÎÕÜÇÑØÆŒĐŁŠŽ àéîõüçñøæœßł"),
    (40, "!?&@#$%*()[]{}<>+-=×÷±°€£¥©®"),
    (40, "⌀ ⌴ ⌵ ↧ ⌲ ⌳ ℄ ∠ ⟂ ∥ ⌖ ◎ ⌯ ⌭ ⏥ ↗ ⌰"),
    (40, "ⓂⓁⓅⒻⓉⓈ ①②③④⑤⑥⑦⑧⑨⑩"),
    (40, "⌀12.5 ±0.05  ⌴⌀18 ↧6  ⌵⌀10×90°"),
]


def polylines(gs, name, steps=14):
    rp = RecordingPen()
    gs[name].draw(rp)
    out, pts, n = [], [], 0
    for op, a in rp.value:
        if op == "moveTo":
            pts, n = [a[0]], 0
        elif op == "lineTo":
            pts.append(a[0])
        elif op == "curveTo":
            p0 = pts[-1]
            c1, c2, p3 = a
            for i in range(1, steps + 1):
                t = i / steps
                mt = 1 - t
                pts.append(tuple(mt ** 3 * p0[k] + 3 * mt * mt * t * c1[k] + 3 * mt * t * t * c2[k]
                                 + t ** 3 * p3[k] for k in (0, 1)))
        elif op == "closePath":
            out.append(pts[: len(pts) // 2 + 1])  # the outbound half is the stroke
    return out


def main():
    font = TTFont(OTF)
    cmap, gs = font.getBestCmap(), font.getGlyphSet()
    pad, width = 40, 1500
    height = pad * 2 + sum(int(s * 1.6) for s, _ in LINES)
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    y = pad
    for size, text in LINES:
        base = y + size
        sc = size / 700
        x = pad
        for ch in text:
            name = cmap.get(ord(ch))
            if name:
                for pl in polylines(gs, name):
                    d.line([(x + px * sc, base - py * sc) for px, py in pl], fill=(25, 25, 25),
                           width=max(1, round(size / 22)), joint="curve")
            x += 600 * sc
        y += int(size * 1.6)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
