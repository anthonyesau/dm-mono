"""Render docs/technical-symbols.png from the exported fonts.

usage: python specimen.py   (needs pillow, freetype-py, uharfbuzz)
"""

import os

import freetype
import uharfbuzz as hb
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
EXPORTS = os.path.join(ROOT, "exports")
OUT = os.path.join(ROOT, "docs", "technical-symbols.png")

ROWS = [
    ("Dimensioning", "⌀ ∅ ° ± ∓ × ′ ″ ‴ ⌴ ⌵ ↧ ⌲ ⌳ □ ℄ ⌒ ∠ ∡ ⌱", "", "Regular"),
    ("GD&T", "⏤ ⏥ ○ ⌭ ⌒ ⌓ ∠ ⟂ ∥ ⫽ ⌖ ◎ ⌯ ↗ ⌰ ⌮", "", "Regular"),
    ("Modifiers", "Ⓜ Ⓛ Ⓟ Ⓕ Ⓣ Ⓢ Ⓤ Ⓔ Ⓘ Ⓐ Ⓑ Ⓒ", "", "Regular"),
    ("Balloons", "⓪ ① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ ⑪ ⑫ ⑳", "", "Regular"),
    ("Fractions", "½ ¼ ¾ ⅛ ⅜ ⅝ ⅞ ⅓ ⅔ ⅕ ⅖ ⅗ ⅘ ⅙ ⅚ ⅐ ⅑ ⅒ ↉", "", "Regular"),
    ("frac feature", "3/16  5/32  7/64  11/8  1/2", "frac", "Regular"),
    ("Super/subscript", "m² mm³ 10⁻⁶ xⁿ H₂O ⁰¹²³⁴⁵⁶⁷⁸⁹ ₀₁₂₃₄₅₆₇₈₉", "", "Regular"),
    ("Arrows & shapes", "← ↑ → ↓ ↔ ↕ ↖ ↗ ↘ ↙ △ ▲ ▽ ▼ □ ■ ○ ●", "", "Regular"),
    ("Math", "≡ ∼ ≈ ≠ ≤ ≥ ∓ ⋅ ∥ ⊥ Ω Δ μ", "", "Regular"),
    ("In use", "⌀12.5 ±0.05  ⌴⌀18 ↧6  ⌵⌀10×90°", "", "Light"),
    ("In use", "⌖ ⌀0.1 Ⓜ A B  ⏥ 0.02  ⟂ 0.05 A", "", "Medium"),
    ("In use", "⌀12.5 ±0.05  ⌴⌀18 ↧6  ⌵⌀10×90°", "", "Italic"),
]

SIZE = 40
LABEL_SIZE = 16
PAD = 28


def font_path(style):
    return os.path.join(EXPORTS, f"DMMono-{style}.ttf")


def draw_text(img, xy, text, style, size, feats="", color=(20, 20, 20)):
    path = font_path(style)
    face = hb.Face(hb.Blob.from_file_path(path))
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {f: True for f in feats.split(",") if f})
    ft = freetype.Face(path)
    ft.set_pixel_sizes(0, size)
    scale = size / face.upem
    x, base = xy
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        ft.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
        bm = ft.glyph.bitmap
        if bm.width and bm.rows:
            mask = Image.frombytes("L", (bm.width, bm.rows), bytes(bm.buffer))
            img.paste(color, (int(x) + ft.glyph.bitmap_left, base - ft.glyph.bitmap_top), mask)
        x += pos.x_advance * scale
    return x


def main():
    row_h = int(SIZE * 1.55)
    label_w = 260
    width = label_w + int(SIZE * 0.6 * 40) + PAD
    height = PAD * 2 + row_h * len(ROWS) + 50
    img = Image.new("RGB", (width, height), (255, 255, 255))
    d = ImageDraw.Draw(img)
    draw_text(img, (PAD, PAD + 26), "DM Mono — technical symbol extension", "Medium", 26)
    y = PAD + 50
    for label, text, feats, style in ROWS:
        base = y + int(SIZE * 1.05)
        tag = label + (f" ({style})" if label == "In use" else "")
        draw_text(img, (PAD, base - 6), tag, "Regular", LABEL_SIZE, color=(120, 120, 120))
        draw_text(img, (label_w, base), text, style, SIZE, feats)
        d.line([(PAD, y + row_h - 4), (width - PAD, y + row_h - 4)], fill=(235, 235, 235))
        y += row_h
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
