"""Helpers for reading outlines out of a glyphsLib GSFont."""

from geo import Contour, unslant


def layer_for(font, glyphname, master_id):
    g = font.glyphs[glyphname]
    if g is None:
        raise KeyError(glyphname)
    return g.layers[master_id]


def contours(font, glyphname, master_id, italic=False, paths=None):
    """Decomposed contours of a glyph for one master, in upright space."""
    out = _decompose(font, glyphname, master_id)
    if paths is not None:
        out = [out[i] for i in paths]
    return unslant(out) if italic else out


def _decompose(font, glyphname, master_id):
    layer = layer_for(font, glyphname, master_id)
    out = []
    for p in layer.paths:
        nodes = [(n.position.x, n.position.y, n.type) for n in p.nodes]
        out.append(Contour.from_nodes(nodes))
    for comp in layer.components:
        a, b, c, d, e, f = comp.transform
        for sub in _decompose(font, comp.name, master_id):
            out.append(sub.affine(a, b, c, d, e, f))
    return out
