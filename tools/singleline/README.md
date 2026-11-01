# DM Mono Single Line

A centre-line ("stroke") version of DM Mono for engraving, CNC routing, laser
marking and pen plotting. It covers the whole DM Mono character set,
including the technical-symbol extension (533 characters).

```sh
python tools/singleline/build.py      # writes exports/singleline/
python tools/singleline/check.py      # verifies both files (ezdxf optional)
python tools/singleline/specimen.py   # docs/single-line.png
```

## Files

| File | Format | Use it in |
| --- | --- | --- |
| `DMMonoSingleLine.otf` | OpenType (CFF). Every stroke is drawn out and back along itself, so each glyph encloses zero area. | Rhino, Fusion, VCarve/Aspire, Inkscape and other CAM software that accepts "double-stroke" engraving fonts |
| `DMMonoSingleLine.shx` | AutoCAD shape font (shapes 1.0) with true open strokes. Shape numbers are Unicode code points. | LightBurn, AutoCAD |

Because the OTF glyphs have no area, the font looks **blank** in word
processors and font previews. That is expected: engraving software reads
the paths, not the filled shape.

## Using it

**Rhino**: install the OTF, then use `TextObject` with *DM Mono Single
Line*. Rhino only recognises the single-line fonts on its built-in list, so
for this one turn on *Allow single-stroke fonts* (*Engrave* in some
versions) if the text comes out doubled. Rhino then drops the duplicated
return strokes and leaves one open curve per stroke.

**LightBurn**: SHX fonts are not installed in the system. Put
`DMMonoSingleLine.shx` in a folder, point LightBurn's font folder setting
at it, and choose it from the font list.

**CNC / CAM**: install the OTF and pick it in the engraving or V-carve text
tool. Programs that do not recognise double-stroke fonts may cut each line
twice; that is harmless, but the second pass can be avoided by exploding
the text and deleting duplicate curves.

**Cap height and cutter**: the strokes follow the centre of DM Mono Light's
strokes and end on the metric lines (baseline, x-height 496, cap height
700). A cutter about 1/10 of the cap height wide (for 10 mm capitals,
about 1 mm) gives back the weight of DM Mono Light; finer cutters give a
lighter, technical-lettering look.

## How it is made

* `skeleton.py`: hand-placed centre lines for every glyph DM Mono draws
  directly (letters, figures, punctuation, symbols, accents), as SVG path
  strings in font units. They were drawn over DM Mono Light's outlines.
  Horizontal positions follow the stroke centres; vertical extremes land on
  the metric lines so text aligns even with a fine tool.
* `symbols.py`: the technical-symbol extension (⌀, GD&T symbols, arrows,
  enclosed characters, superiors, fractions) as centre lines. Filled shapes
  (● ■ ▲ ▼) are drawn as nested outlines so they fill when engraved.
* `build.py`: composes everything DM Mono builds from components (accented
  letters, numerators, inferiors…) from the Glyphs source, then writes the
  OTF and the SHX. The SHX uses a 2.5-unit grid (cap height = 140 shape
  units); curves are split into short straight segments.

To change a glyph, edit its path in `skeleton.py` or `symbols.py`, rebuild,
and run `check.py`. Accented letters follow automatically.
