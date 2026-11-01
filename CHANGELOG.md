# DM Mono Changelog

## Unreleased

- DM Mono Single Line: centre-line OTF (out-and-back strokes, for Rhino and
  CAM) and SHX (for LightBurn and AutoCAD) covering the full character set,
  built by `tools/singleline/build.py`

- Variable fonts `DMMono[wght].ttf` and `DMMono-Italic[wght].ttf`
  (wght 300–500, default Regular), with STAT and named instances,
  built by `source/build.sh` into `exports/variable/`

## v1.100

Technical symbol extension (173 new glyphs, 152 new code points):

- Dimensioning and drafting symbols: ⌀ ∅ ′ ″ ‴ ∓ ⌴ ⌵ ↧ ⌲ ⌳ □ ℄ ⌒ ∡ ⌱
- GD&T characteristic symbols: ⏤ ⏥ ○ ⌭ ⌒ ⌓ ∠ ⟂ ⊥ ∥ ⫽ ⌖ ◎ ⌯ ↗ ⌰ ⌮
- Circled capitals Ⓐ–Ⓩ (GD&T modifiers) and circled numbers ⓪ ①–⑳
- Vulgar fractions ⅐–⅞, ↉ and ⅟ in the existing stacked style
- Superscripts ⁰ ⁴–⁹ ⁺ ⁻ ⁼ ⁽ ⁾ ⁿ and subscripts ₀–₉ ₊ ₋ ₌ ₍ ₎
- Arrows ←–↙, geometric shapes △ ▲ ▽ ▼ □ ■ ○ ● ◎
- ≡ ∼ ⋅ ∙, Greek aliases Ω Δ μ, hyphen/dash variants, extra spaces
- New `frac` feature for arbitrary fractions; new `numr`, `dnom`, `subs`
  and `sinf` features; `sups` extended to all figures and signs
- OS/2 Unicode ranges are now computed from the character set
- Build updated for current fontmake, gftools and ttfautohint

## v1.000

Initial Release
