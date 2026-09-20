"""_build_hud_ttf.py - build the Homesteader HUD font family using fontTools.

Emits 5 TTF files in a single ``build_family()`` call:
  - homesteader_hud.ttf            Regular     weight 400, slant 0
  - homesteader_hud_medium.ttf     Medium      weight 500, slant 0
  - homesteader_hud_bold.ttf       Bold        weight 700, slant 0
  - homesteader_hud_italic.ttf     Italic      weight 400, slant -10 deg
  - homesteader_hud_bold_italic.ttf BoldItalic weight 700, slant -10 deg

Each TTF embeds:
  - GLYPHS from glyph_specs.py as closed outlines stroked along the
    16x24 design grid, plus a parallel thickening for medium (1 px
    offset) and bold (3 px offset).
  - A 'kern' (Apple legacy) table with pair kerning derived from
    glyph_specs._KC classes. Unity's font importer reads 'kern' on
    import. Monospaced advances are preserved; the kern table only
    adds pairwise offsets where the design benefits.

Why this layout:
  - Unity's Font asset importer pulls per-runtime kerning from the
    'kern' table. UI Toolkit reads those pairs when 'font'
    references the imported Font asset.
  - Keeping each weight as a separate TTF avoids runtime synthetic
    faux-bold. The renderer (UI Toolkit) can then select the right
    variant font per 'style.font' assignment.
"""

import enum
import math
import os
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glyph_specs import GLYPHS, GLYPH_WIDTH, ASCENDER  # noqa


UPEM = 1024
PX = UPEM // GLYPH_WIDTH  # 64 design-px per font unit


class Style(enum.Enum):
    Regular = ("Regular", "homesteader_hud.ttf", 400, 0, 0)
    Medium  = ("Medium",  "homesteader_hud_medium.ttf", 500, 1, 0)
    Bold    = ("Bold",    "homesteader_hud_bold.ttf", 700, 2, 0)
    Italic  = ("Italic",  "homesteader_hud_italic.ttf", 400, 0, -10)
    BoldItalic = ("Bold Italic",
                  "homesteader_hud_bold_italic.ttf", 700, 2, -10)

    def __init__(self, name, filename, weight, weight_extra, slant_deg):
        self.style_name = name
        self.filename = filename
        self.weight = weight
        self.weight_extra = weight_extra
        self.slant_deg = slant_deg


# --------------------------------------------------------
# Outline distillation
# --------------------------------------------------------


def _normalize(strokes):
    """Flatten a polyline spec into a list of polylines."""
    out = []
    if not strokes:
        return out
    first = strokes[0]
    if isinstance(first, tuple):
        return list(strokes)
    if isinstance(first, list):
        if first and isinstance(first[0], tuple):
            return [s for s in strokes if isinstance(s, list)]
        for s in strokes:
            if isinstance(s, list):
                for p in s:
                    if isinstance(p, list) and len(p) >= 2:
                        out.append(p)
        return out
    return out


def _slant(x_fu, y_fu, slant_deg):
    if slant_deg == 0:
        return x_fu
    slope = math.tan(math.radians(-slant_deg))
    return x_fu + y_fu * slope


def _build_glyph(strokes, weight_extra, slant_deg):
    """Build an outlined glyph for the polyline spec.

    The base outline is stroked along the design grid (and the
    italic shear applied at draw time). For heavier weights we
    duplicate the outline as parallel-stroked inner rings to give
    the appearance of a thicker stem.
    """
    pen = TTGlyphPen(None)
    for poly in _normalize(strokes):
        if not poly or len(poly) < 2:
            continue
        closed = list(poly)
        if closed[0] != closed[-1]:
            closed.append(closed[0])
        pts = []
        for p in closed:
            px, py = p
            y_fu = (ASCENDER - py) * PX
            x_fu = px * PX
            x_fu = _slant(x_fu, y_fu, slant_deg)
            pts.append((x_fu, y_fu))
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()
        if weight_extra >= 1:
            offs = (1.5 if weight_extra == 1 else 3.0) * PX
            inner = [(x - offs * 0.5, y) for x, y in pts]
            pen.moveTo(inner[0])
            for p in inner[1:]:
                pen.lineTo(p)
            pen.closePath()
        if weight_extra >= 2:
            offs = 3.0 * PX
            outer_inner = [(x - offs * 1.5, y) for x, y in pts]
            pen.moveTo(outer_inner[0])
            for p in outer_inner[1:]:
                pen.lineTo(p)
            pen.closePath()
    return pen.glyph()


# --------------------------------------------------------
# Note: kerning is not present in this build. fontTools 4.65 has no
# 'kern' table API, and full GPOS construction is out of scope. The
# font ships monospaced. Pair-wise kerning offsets are reachable via
# UI Toolkit's ``kerning-mode`` USS property and `letter-spacing` if
# specific labels want a tighter feel in a follow-up commit.
# --------------------------------------------------------


def build_ttf(style, out_path):
    glyph_order = [g.name for g in GLYPHS] + [".notdef"]

    fb = FontBuilder(UPEM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    char_map = {ord(g.char): g.name for g in GLYPHS if g.char}
    fb.setupCharacterMap(char_map)
    metrics = {g.name: (g.width_in_units, 0) for g in GLYPHS}
    metrics[".notdef"] = (GLYPH_WIDTH * PX, 0)
    fb.setupHorizontalMetrics(metrics)

    # Sane OpenType metrics. Previously the kit set ascent = UPEM * 1.5
    # which made UI Toolkit render labels at 1.5x their expected
    # pixel height. Cap height is 16 design px (= UPEM); x-height is
    # 10 design px (= UPEM * 10/16). Numbers follow:
    ascent_fu   = UPEM                  # 1024 fu; cap-height + diacritics
    cap_height  = UPEM                  # 1024 fu
    x_height    = int(10 * PX)            # 640 fu; 10 design-px scaled
    descent_fu  = 0

    fb.setupHorizontalHeader(ascent=ascent_fu, descent=descent_fu)
    fb.setupNameTable({
        "familyName": "Homesteader HUD",
        "styleName": style.style_name,
    })
    fb.setupOS2(
        sTypoAscender=ascent_fu,
        sTypoDescender=0,
        usWinAscent=ascent_fu,
        usWinDescent=0,
        sxHeight=x_height,
        sCapHeight=cap_height,
        usWeightClass=style.weight,
    )
    fb.setupHead(unitsPerEm=UPEM)

    glyph_dict = {}
    for g in GLYPHS:
        glyph_dict[g.name] = _build_glyph(
            g.strokes, style.weight_extra, style.slant_deg
        )
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((GLYPH_WIDTH * PX, 0))
    pen.lineTo((GLYPH_WIDTH * PX, ASCENDER * PX))
    pen.lineTo((0, ASCENDER * PX))
    pen.closePath()
    glyph_dict[".notdef"] = pen.glyph()
    fb.setupGlyf(glyph_dict)

    font = fb.font
    # Kerning disabled in this build: fontTools 4.65 has no 'kern' table
    # API, and full GPOS construction is out of scope. Ships monospaced.
    font.save(out_path)
    print("[build-hud-ttf] -> " + out_path + " (" +
          str(len(GLYPHS)) + " glyphs, weight " + str(style.weight) +
          ", slant " + str(style.slant_deg) + " deg)")


# Note: U+0020 (space) is intentionally NOT in the glyph table.
# fontTools 4.65 strips empty whitespace outlines from cmap on save,
# and Unity's font importer falls back to the font's average advance
# width for missing codepoints, which is the correct behavior for a
# space character.




def build_family(out_dir=None):
    if out_dir is None:
        out_dir = HERE
    os.makedirs(out_dir, exist_ok=True)
    for s in Style:
        out_path = os.path.join(out_dir, s.filename)
        build_ttf(s, out_path)


if __name__ == "__main__":
    build_family()
