"""_build_hud_ttf.py - build homesteader_hud.ttf using fontTools.

Uses FontBuilder with an explicit glyphOrder pre-populated so the
setupGlyphOrder / setupGlyf ordering issue doesn't trip the size
mismatch assertion.

Stylistically inspired by Segoe UI / Fira. Glyphs are polylines in
glyph_specs.py converted to closed font-unit outlines via TTGlyphPen.
"""
import os
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glyph_specs import GLYPHS, GLYPH_WIDTH, ASCENDER  # noqa


UPEM = 1024
PX = UPEM // GLYPH_WIDTH


def _normalize(strokes):
    """Flatten nested polyline lists to a list of polylines.

    Each polyline is a list of (x, y) tuples.
    """
    out = []
    if not strokes:
        return out
    first = strokes[0]
    if isinstance(first, tuple):
        return list(strokes)
    if isinstance(first, list):
        if first and isinstance(first[0], tuple):
            # 2-deep: list of polylines.
            return [s for s in strokes if isinstance(s, list)]
        # 3-deep: list of strokes, each a list of polylines.
        for s in strokes:
            if isinstance(s, list):
                for p in s:
                    if isinstance(p, list) and len(p) >= 2:
                        out.append(p)
        return out
    return out


def _build_glyph(strokes):
    pen = TTGlyphPen(None)
    for poly in _normalize(strokes):
        if not poly or len(poly) < 2:
            continue
        closed = list(poly)
        if closed[0] != closed[-1]:
            closed.append(closed[0])
        x0, y0 = closed[0]
        pen.moveTo((x0 * PX, (ASCENDER - y0) * PX))
        for p in closed[1:]:
            pen.lineTo((p[0] * PX, (ASCENDER - p[1]) * PX))
        pen.closePath()
    return pen.glyph()


def build_ttf(out_path=os.path.join(HERE, "homesteader_hud.ttf")):
    glyph_order = [g.name for g in GLYPHS] + [".notdef"]

    fb = FontBuilder(UPEM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({ord(g.char): g.name for g in GLYPHS if g.char})
    metrics = {g.name: (g.width_in_units, 0) for g in GLYPHS}
    metrics[".notdef"] = (GLYPH_WIDTH * PX, 0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENDER * PX, descent=0)
    fb.setupNameTable({
        "familyName": "Homesteader HUD",
        "styleName": "Regular",
    })
    fb.setupOS2(sTypoAscender=ASCENDER * PX, sTypoDescender=0,
                 usWinAscent=ASCENDER * PX, usWinDescent=0)
    fb.setupHead(unitsPerEm=UPEM)

    glyph_dict = {}
    for g in GLYPHS:
        glyph_dict[g.name] = _build_glyph(g.strokes)
    # .notdef.
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((GLYPH_WIDTH * PX, 0))
    pen.lineTo((GLYPH_WIDTH * PX, ASCENDER * PX))
    pen.lineTo((0, ASCENDER * PX))
    pen.closePath()
    glyph_dict[".notdef"] = pen.glyph()
    fb.setupGlyf(glyph_dict)

    fb.font.save(out_path)
    print(f"[build-hud-ttf] -> {out_path} ({len(GLYPHS)} glyphs + .notdef)")


if __name__ == "__main__":
    build_ttf()
