"""_build_font.py - procedural HUD font.

Builds assets/hud_kit/font/homesteader_hud.ttf from a glyph spec table.
Every glyph is a list of polylines on a 16 wide x 24 tall design grid
(line weight 2 px), authored here as plain lists of (x, y) tuples. No
external font assets.

Required glyphs (see glyph_specs.py):
  - numerals 0-9, '-', '+', '/', ':', '.', space
  - AM/PM: A, M, P, m
  - speed chips: | (pause), 1x, 3x, 5x
  - seasons: S, W, A, plus digits/letters used by asset names

Usage:
    python assets/hud_kit/font/_build_font.py
"""
import os
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from glyph_specs import GLYPHS, GLYPH_WIDTH, ASCENDER, DESCENDER  # noqa


def _seg_to_font_units(x0, y0, x1, y1, weight_px, upem):
    """Convert a 2-px pixel-grid segment to font-unit coordinates.

    Returns four corners of the stroked segment as a list of (x, y)
    tuples, already shifted so pixel-y = 0 sits at the cap height and
    pixel-y = ASCENDER sits at baseline.

    Each pixel = upem / GLYPH_WIDTH font units (16 px = 2048 upem).
    """
    px = upem / GLYPH_WIDTH  # 128 font units per pixel
    w = weight_px * px / 2
    if x0 == x1:
        # Vertical: horizontal slab.
        x0u = x0 * px - w
        x1u = x0 * px + w
        y_top = (ASCENDER - y0) * px
        y_bot = (ASCENDER - y1) * px
        y_top, y_bot = sorted((y_top, y_bot))
        return [(x0u, y_top), (x1u, y_top), (x1u, y_bot), (x0u, y_bot)]
    if y0 == y1:
        # Horizontal: vertical slab.
        xa = min(x0, x1) * px
        xb = max(x0, x1) * px
        y0u = (ASCENDER - y0) * px - w
        y1u = (ASCENDER - y0) * px + w
        return [(xa, y0u), (xb, y0u), (xb, y1u), (xa, y1u)]
    # Diagonal: perpendicular slab.
    import math
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * w, dx / length * w
    pts = [
        (x0 * px + nx, (ASCENDER - y0) * px - ny),
        (x1 * px + nx, (ASCENDER - y1) * px - ny),
        (x1 * px - nx, (ASCENDER - y1) * px + ny),
        (x0 * px - nx, (ASCENDER - y0) * px + ny),
    ]
    return pts


def build_font(out_path):
    upem = 2048
    fb = FontBuilder(upem, isTTF=True)
    glyph_names = [g.name for g in GLYPHS]
    fb.setupGlyphOrder(glyph_names + [".notdef"])
    fb.setupCharacterMap({ord(g.char): g.name for g in GLYPHS if g.char})

    metrics = {g.name: (g.width_in_units, 0) for g in GLYPHS}
    metrics[".notdef"] = (GLYPH_WIDTH * (upem // GLYPH_WIDTH), 0)
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=ASCENDER, descent=-DESCENDER)
    fb.setupNameTable({
        "familyName": "Homesteader HUD",
        "styleName": "Regular",
    })
    fb.setupOS2(sTypoAscender=ASCENDER, sTypoDescender=-DESCENDER,
                 usWinAscent=ASCENDER, usWinDescent=DESCENDER)
    fb.setupHead(unitsPerEm=upem)

    glyph_dict = {}
    for glyph in GLYPHS:
        pen = TTGlyphPen(None)
        for stroke in glyph.strokes:
            for polyline in stroke:
                for i in range(len(polyline) - 1):
                    x0, y0 = polyline[i]
                    x1, y1 = polyline[i + 1]
                    corners = _seg_to_font_units(
                        x0, y0, x1, y1,
                        weight_px=2, upem=upem,
                    )
                    pen.moveTo(corners[0])
                    for c in corners[1:]:
                        pen.lineTo(c)
                    pen.closePath()
        glyph_dict[glyph.name] = pen.glyph()
    glyph_dict[".notdef"] = pen.glyph()
    fb.setupGlyf(glyph_dict)

    fb.font.save(out_path)
    print(f"[build-font] wrote {out_path} ({len(GLYPHS)} glyphs)")


if __name__ == "__main__":
    out = os.path.join(HERE, "homesteader_hud.ttf")
    build_font(out)
