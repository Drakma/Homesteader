"""_build_atlas.py - bitmap font atlas for the Homesteader HUD.

Builds assets/hud_kit/font/homesteader_hud.png as a single image with
each glyph rasterized in its own cell. The atlas is consumed by
runtime/font.py.

Layout: row-major grid of GLYPH_CELL_W x GLYPH_CELL_H cells. Each cell
contains one glyph drawn as a 2-px stroke on the design grid.

One atlas image + one JSON index (font_index.json) with name -> (col,
row, advance_px). Codex uses the index to blit glyphs at runtime.

Design grid
-----------
GLYPH_WIDTH  = 16 px (cell width)
ASCENDER     = 24 px
DESCENDER    = 4 px
TOTAL_HEIGHT = ASCENDER + DESCENDER = 28 px (cell height)
LINE_WEIGHT  = 2 px
"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from glyph_specs import GLYPHS, GLYPH_WIDTH, ASCENDER  # noqa


CELL_W = GLYPH_WIDTH          # 16
CELL_H = ASCENDER             # 24
LINE_W = 2
PADDING = 0  # 0 - adjacent cells share borders


def _draw_segment(img, draw, x0, y0, x1, y1, color):
    """Draw a 2-px stroke along an integer pixel grid."""
    if x0 == x1:
        x0 -= LINE_W // 2
        y0, y1 = sorted((y0, y1))
        draw.rectangle([x0, y0, x0 + LINE_W - 1, y1], fill=color)
    elif y0 == y1:
        x0, x1 = sorted((x0, x1))
        y0 -= LINE_W // 2
        draw.rectangle([x0, y0, x1, y0 + LINE_W - 1], fill=color)
    else:
        import math
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        nx, ny = -dy / length * LINE_W / 2, dx / length * LINE_W / 2
        pts = [(x0 + nx, y0 - ny), (x1 + nx, y1 - ny),
               (x1 - nx, y1 + ny), (x0 - nx, y0 + ny)]
        draw.polygon(pts, fill=color)


def _draw_glyph(img, draw, top_left_x, top_left_y, glyph, color):
    """Draw one glyph into a CELL_W x CELL_H cell at top_left."""
    ox, oy = top_left_x, top_left_y
    for stroke in glyph.strokes:
        for polyline in stroke:
            if not polyline:
                continue
            for i in range(len(polyline) - 1):
                x0, y0 = polyline[i]
                x1, y1 = polyline[i + 1]
                _draw_segment(img, draw, x0 + ox, y0 + oy,
                              x1 + ox, y1 + oy, color)


def build_atlas(out_path=os.path.join(HERE, "homesteader_hud.png"),
                index_path=os.path.join(HERE, "font_index.json")):
    n = len(GLYPHS)
    cols = 16
    rows = (n + cols - 1) // cols
    canvas = Image.new("RGBA", (cols * CELL_W, rows * CELL_H),
                        (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    index = {"cell_w": CELL_W, "cell_h": CELL_H,
             "cols": cols, "rows": rows,
             "ascender": ASCENDER,
             "weights": ["regular"],
             "default_weight": "regular",
             "advance_mode": "monospace",
             "glyphs": []}
    for i, g in enumerate(GLYPHS):
        col, row = i % cols, i // cols
        x, y = col * CELL_W, row * CELL_H
        _draw_glyph(canvas, draw, x, y, g, color=(220, 224, 230, 255))
        index["glyphs"].append({
            "id": g.name,
            "char": g.char,
            "weight": "regular",
            "col": col,
            "row": row,
            "advance_px": CELL_W,
        })
    canvas.save(out_path, "PNG")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"[build-atlas] {n} glyphs -> {out_path} ({canvas.size[0]}x{canvas.size[1]})")
    print(f"[build-atlas] index -> {index_path}")


if __name__ == "__main__":
    build_atlas()
