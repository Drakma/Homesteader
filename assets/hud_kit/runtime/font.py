"""font.py - bitmap font rendering for the Homesteader HUD.

Pulls glyphs out of assets/hud_kit/font/homesteader_hud.png via the
JSON index at font_index.json. Provides a single ImageFont-like API
that render.py uses:

    f = load_bitmap_font()
    draw.text((x, y), "12:00 PM", fill=(220,224,230), font=f)
"""
import json
import os

from PIL import Image, ImageDraw


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(HERE, "font")
ATLAS_PATH = os.path.join(FONT_DIR, "homesteader_hud.png")
INDEX_PATH = os.path.join(FONT_DIR, "font_index.json")


class BitmapFont:
    """A minimal bitmap font loader with a PIL.ImageFont-compatible
    surface for `draw.text`.

    Implements the PIL ImageFont protocol:
        textbbox((0, 0), text, font=self) -> (0, 0, w, h)
        getsize(text) -> (w, h)

    Note: we don't subclass PIL.ImageFont because PIL expects the font
    object to support many APIs we don't need. Rendering goes through
    render_text(canvas, xy, text, fill).
    """

    def __init__(self, atlas: Image.Image, index: dict):
        self._atlas = atlas
        self._index = index
        self.cell_w = index["cell_w"]
        self.cell_h = index["cell_h"]
        self.ascender = index["ascender"]
        self._by_id = {g["id"]: g for g in index["glyphs"]}
        self._by_char = {g["char"]: g for g in index["glyphs"]
                          if g.get("char")}

    def _active_id_map(self) -> dict:
        return self._by_id

    def _active_char_map(self) -> dict:
        return self._by_char

    def measure(self, text: str) -> int:
        if "{" in text:
            manual = self._extract_manual_ids(text)
            if manual is not None:
                return sum(self._advance(gid) for gid in manual)
        return sum(self._advance_for_char(c) for c in text)

    def _advance(self, gid: str) -> int:
        glyph = self._by_id.get(gid)
        if glyph is None:
            return self.cell_w
        return glyph["advance_px"]

    def _advance_for_char(self, c: str) -> int:
        if c == " ":
            return self.cell_w // 2
        glyph = self._active_char_map().get(c)
        if glyph is None:
            return self.cell_w // 2
        return glyph["advance_px"]

    def _extract_manual_ids(self, text: str):
        """If a text string contains {glyph_id} tokens, return the
        ordered list of glyph-id strings (otherwise None).
        """
        if "{" not in text:
            return None
        result = []
        i = 0
        while i < len(text):
            if text[i] == "{":
                end = text.index("}", i + 1)
                gid = text[i + 1:end]
                if (gid in self._active_id_map()
                        or any(gid in m for m in self._by_weight.values())):
                    result.append(gid)
                i = end + 1
            else:
                result.append(text[i])
                i += 1
        return result

    def render(self, canvas: Image.Image, xy: tuple, text: str,
               fill, scale: int = 1):
        """Rasterize `text` onto `canvas` at `(x, y)` xy, at `scale`x.

        fill is an RGB or RGBA tuple. Glyphs are stamped with their own
        alpha multiplied into the fill.

        Supports `{glyph_id}` manual ids (used for composite speed
        glyphs like `{pause}`, `{speed_1x}`).
        """
        x, y = xy
        scale_i = max(1, int(round(scale)))
        manual = self._extract_manual_ids(text)
        if manual is None:
            for c in text:
                if c == " ":
                    x += self._advance_for_char(" ") * scale_i
                    continue
                glyph = self._active_char_map().get(c)
                if glyph is None:
                    x += self.cell_w // 2 * scale_i
                    continue
                self._stamp(canvas, glyph, x, y, fill, scale_i)
                x += glyph["advance_px"] * scale_i
        else:
            for token in manual:
                if token.startswith("{") and token.endswith("}"):
                    continue
                # Manual id
                glyph = self._active_id_map().get(token)
                if glyph is None:
                    # Try other weights.
                    found = None
                    for w in self._index["weights"]:
                        g = self._by_weight[w].get(token)
                        if g:
                            found = g
                            break
                    if found is None:
                        continue
                    glyph = found
                self._stamp(canvas, glyph, x, y, fill, scale_i)
                x += glyph["advance_px"] * scale_i

    def _stamp(self, canvas: Image.Image, glyph: dict, x: int, y: int,
               fill, scale_i: int):
        cx, cy = glyph["col"], glyph["row"]
        cell = self._atlas.crop((cx * self.cell_w, cy * self.cell_h,
                                  (cx + 1) * self.cell_w,
                                  (cy + 1) * self.cell_h))
        if scale_i != 1:
            cell = cell.resize(
                (cell.width * scale_i, cell.height * scale_i),
                Image.NEAREST,
            )
        # Tint: multiply per-glyph alpha (from the cell) by the fill color.
        r, g, b = fill[0], fill[1], fill[2]
        alpha = fill[3] if len(fill) == 4 else 255
        # Build a tinted RGBA image: RGB=fill, A=cell alpha * alpha.
        r_ch, g_ch, b_ch, a_ch = cell.split()
        # Per-pixel: keep rgb=fill, scale alpha by overall alpha.
        if alpha < 255:
            a_ch = a_ch.point(lambda v: v * alpha // 255)
        cell = Image.merge("RGBA", (
            Image.new("L", cell.size, r),
            Image.new("L", cell.size, g),
            Image.new("L", cell.size, b),
            a_ch,
        ))
        # Alpha-composite with the surrounding canvas. Note that y on
        # canvas is the *top* of the cell (cap-height-rendered glyph).
        canvas.alpha_composite(cell, (int(x), int(y)))


def load_bitmap_font() -> BitmapFont:
    atlas = Image.open(ATLAS_PATH).convert("RGBA")
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)
    return BitmapFont(atlas, index)


class _DrawingProxy:
    """A thin wrapper around the canvas's ImageDraw.Draw that routes
    `text()` calls through the bitmap font. Acts as a drop-in for
    ImageDraw.Draw in render.py.
    """
    def __init__(self, canvas_draw: ImageDraw.ImageDraw,
                 canvas: Image.Image, font: BitmapFont):
        self._d = canvas_draw
        self._canvas = canvas
        self._font = font

    def rectangle(self, *args, **kwargs):
        return self._d.rectangle(*args, **kwargs)

    def line(self, *args, **kwargs):
        return self._d.line(*args, **kwargs)

    def text(self, xy, text, fill=None, font=None, **_):
        # Use the supplied `font` only if it's our BitmapFont; else
        # fall back to drawing via the wrapped ImageDraw.
        if isinstance(font, BitmapFont):
            self._font.render(self._canvas, xy, text, fill or (255, 255, 255))
            return
        return self._d.text(xy, text, fill=fill, font=font)


def make_text_drawer(canvas: Image.Image, font: BitmapFont):
    """Convenience: return an ImageDraw.Draw whose .text() routes
    through the bitmap font.
    """
    return _DrawingProxy(ImageDraw.Draw(canvas), canvas, font)
