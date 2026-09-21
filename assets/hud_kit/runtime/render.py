"""render.py - render the Homesteader HUD at any canvas size.

The layout is computed from `grid_layout.PLACEMENTS` (which itself knows
about the 9-cell grid) and a LayoutMetrics object that scales every
pixel off a 1920x1080 reference design. That means the layout is the
same on a 3840x2160 monitor, a 1366x768 laptop, or a windowed
1360x720 game canvas.

Every rendering helper takes a `m: LayoutMetrics`. Use `m.px(n)` to
scale any raw pixel value.

The 9-cell grid is the alignment system: every panel declares
`cell` + `anchor` and gets recomputed for any canvas size.
"""

import os
from dataclasses import dataclass
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from .time_system import TimeSystem, Speed, format_wall_clock
from .divlayout import build_layout, SIZE as DIV_SIZE, Div
from .state import HudState, VitalId, ResourceId
from .grid_layout import (
    Cell, Anchor, PanelPlacement, PLACEMENTS,
)

KIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(KIT_ROOT))
ASSETS_ROOT = os.path.join(PROJECT_ROOT, "assets")
SPRITES_ROOT = os.path.join(KIT_ROOT, "sprites")
_TTF_CANDIDATES = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]
_DERIVED_TTF_PATH = os.path.join(KIT_ROOT, "font", "homesteader_hud.ttf")
_FONT_PATHS = {
    "homesteader": None,
    "regular": _TTF_CANDIDATES[0],
    "bold": _TTF_CANDIDATES[1],
}
_DEFAULT_FONT_WEIGHT = "regular"

# Lazy-loaded bitmap HUD font (low-poly numerals + hightech letters).
_bitmap_font = None


def _hud_bitmap_font():
    """Return the bitmap HUD font (loaded lazily)."""
    global _bitmap_font
    if _bitmap_font is None:
        from .font import load_bitmap_font
        try:
            _bitmap_font = load_bitmap_font()
        except Exception:
            _bitmap_font = None
    return _bitmap_font


def _hud_font(size_px: int, weight: str = None):
    """Return a PIL ImageFont for the HUD. Structural copy of Segoe UI
    / Fira is hand-drawn in homesteader_hud.ttf; falls back to real
    Segoe UI / Arial if the custom font is missing.
    """
    weight = weight or _DEFAULT_FONT_WEIGHT
    paths = [_FONT_PATHS.get(weight), *_TTF_CANDIDATES]
    for p in paths:
        if not p or not os.path.isfile(p):
            continue
        try:
            f = ImageFont.truetype(p, size_px)
            return f
        except Exception:
            continue
    return ImageFont.load_default()


# Design canvas - this is what every LayoutMetrics value is authored
# against. Don't hard-code coordinates without this.
DESIGN_W = 1920
DESIGN_H = 1080


@dataclass
class LayoutMetrics:
    """Scaled design metrics for a particular output canvas.

    Single uniform scale factor so panel aspect ratios are preserved
    regardless of monitor aspect.

    Use:
        m = LayoutMetrics(canvas_w=1920, canvas_h=1080)
        m.px(120)  #  designer-pixel value scaled to the output canvas
        m.pct(0.05)  # 5% of canvas width
    """
    canvas_w: int
    canvas_h: int

    @property
    def s(self) -> float:
        # Pick the smaller axis so neither dimension overflows.
        return min(self.canvas_w / DESIGN_W, self.canvas_h / DESIGN_H)

    def px(self, n: int) -> int:
        return max(1, int(round(n * self.s)))

    def pct_w(self, frac: float) -> int:
        return int(round(self.canvas_w * frac))

    def pct_h(self, frac: float) -> int:
        return int(round(self.canvas_h * frac))


def _sprite(group: str, name: str) -> Image.Image:
    return Image.open(
        os.path.join(SPRITES_ROOT, group, f"{name}.png")
    ).convert("RGBA")


def _panel_at(canvas: Image.Image, m: LayoutMetrics, placement_key: str,
              panel_sprite_name: str, *, override_w: int = None,
              override_h: int = None):
    """Place a panel sprite from the kit at the cell+anchor from a
    registered PLACEMENTS entry. The panel sprite is 128x128 by
    default; we scale it to placement.panel_w x placement.panel_h using
    the canvas scale factor.

    Pass override_w/override_h to use a content-derived size instead of
    the static PLACEMENT size. The cell+anchor target stays the same.
    """
    p = PLACEMENTS[placement_key]
    # If override provided, use it; else fallback to the registered
    # size scaled to the canvas.
    px_w = override_w if override_w is not None else m.px(p.panel_w)
    px_h = override_h if override_h is not None else m.px(p.panel_h)
    # Re-resolve with the actual canvas size for this render.
    p_local = PanelPlacement(
        cell=p.cell, anchor=p.anchor,
        panel_w=px_w, panel_h=px_h,
        canvas_w=m.canvas_w, canvas_h=m.canvas_h,
        margin=m.px(p.margin), name=p.name,
    )
    x, y, w, h = p_local.rect()
    sprite = _sprite("panels", panel_sprite_name)
    if sprite.width != w or sprite.height != h:
        sprite = sprite.resize((w, h), Image.LANCZOS)
    canvas.alpha_composite(sprite, (x, y))
    return (x, y, w, h)


def _draw_full_width_panel(canvas: Image.Image, m: LayoutMetrics,
                           body_hex: str = None,
                           border_hex: str = None,
                           highlight_hex: str = None,
                           height_src: int = 96) -> tuple:
    """Draw a full-canvas-width top status bar procedurally.

    Delegates to ``_draw_header_band`` for the metallic-with-noise
    fill so all band-style headers share one renderer.

    Returns (x, y, w, h).
    """
    panel_w = m.canvas_w
    panel_h = m.px(height_src)
    y = 0                 # flush against canvas top - no gap
    x = 0
    if body_hex is None:
        body_hex = "#18202c"
    if border_hex is None:
        border_hex = "#0a0e15"
    if highlight_hex is None:
        # Default highlight: amber accent from palette.
        highlight_hex = "#c19a3c"
    _draw_header_band(canvas, x, y, panel_w, panel_h,
                      body_hex, border_hex, highlight_hex,
                      seed=0x4ad5011)
    return (x, y, panel_w, panel_h)


KIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(KIT_ROOT))
ASSETS_ROOT = os.path.join(PROJECT_ROOT, "assets")
SPRITES_ROOT = os.path.join(KIT_ROOT, "sprites")
_TTF_CANDIDATES = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]
_DERIVED_TTF_PATH = os.path.join(KIT_ROOT, "font", "homesteader_hud.ttf")
_FONT_PATHS = {
    "homesteader": None,
    "regular": _TTF_CANDIDATES[0],
    "bold": _TTF_CANDIDATES[1],
}
_DEFAULT_FONT_WEIGHT = "regular"

# Lazy-loaded bitmap HUD font (low-poly numerals + hightech letters).
_bitmap_font = None


def _hud_bitmap_font():
    """Return the bitmap HUD font (loaded lazily)."""
    global _bitmap_font
    if _bitmap_font is None:
        from .font import load_bitmap_font
        try:
            _bitmap_font = load_bitmap_font()
        except Exception:
            _bitmap_font = None
    return _bitmap_font


def _hud_font(size_px: int, weight: str = None):
    """Return a PIL ImageFont for the HUD. Structural copy of Segoe UI
    / Fira is hand-drawn in homesteader_hud.ttf; falls back to real
    Segoe UI / Arial if the custom font is missing.
    """
    weight = weight or _DEFAULT_FONT_WEIGHT
    paths = [_FONT_PATHS.get(weight), *_TTF_CANDIDATES]
    for p in paths:
        if not p or not os.path.isfile(p):
            continue
        try:
            f = ImageFont.truetype(p, size_px)
            return f
        except Exception:
            continue
    return ImageFont.load_default()


def _find_icon_path(asset_id: str):
    """Locate an icon PNG for a catalog asset_id.

    The catalog layout in this project is assets/<category>/<id>/<id>.png
    (e.g. assets/food/food_apple/food_apple.png). We try several
    conventions, then walk the assets tree as a fallback.
    """
    if not asset_id:
        return None
    # Direct lookups.
    candidates = [
        os.path.join(ASSETS_ROOT, asset_id, asset_id + ".png"),
        os.path.join(ASSETS_ROOT, asset_id, "icon.png"),
        os.path.join(KIT_ROOT, "sprites", asset_id + ".png"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    # Walk: find a folder name that matches asset_id or ends with
    # '_' + asset_id, then return its png.
    for root, dirs, files in os.walk(ASSETS_ROOT):
        for d in dirs:
            if d == asset_id or d.endswith("_" + asset_id):
                png = os.path.join(root, d, d + ".png")
                if os.path.isfile(png):
                    return png
    return None


def _render_icon_centered(src_img, target_w: int, target_h: int):
    """Crop the alpha bbox and scale the content into a (target_w,
    target_h) canvas while preserving aspect ratio of the actual
    content (no horizontal stretching). Result is centered.
    """
    if src_img.mode != "RGBA":
        src_img = src_img.convert("RGBA")
    alpha = src_img.split()[3]
    bbox = alpha.getbbox()
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    if bbox is None:
        return canvas
    l, t, r, b = bbox
    cropped = src_img.crop((l, t, r, b))
    cw, ch = cropped.size
    if cw <= 0 or ch <= 0:
        return canvas
    # Uniform scale = fits both dims.
    scale = min(target_w / cw, target_h / ch)
    new_w = max(1, int(cw * scale))
    new_h = max(1, int(ch * scale))
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2
    canvas.alpha_composite(resized, (paste_x, paste_y))
    return canvas


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _lerp_color(c0, c1, t):
    """Linearly interpolate two RGB tuples (3 ints each). t in [0, 1]."""
    t = max(0.0, min(1.0, float(t)))
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * t)) for i in range(3))


def _lerp_color(c0, c1, t):
    """Linearly interpolate two RGB tuples (3 ints each). t in [0, 1]."""
    t = max(0.0, min(1.0, float(t)))
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * t)) for i in range(3))


def _draw_header_band(canvas: Image.Image, x: int, y: int, w: int, h: int,
                       body_hex: str, border_hex: str,
                       highlight_hex: str, *,
                       seed: int = None):
    """Paint a single window/modal/header band with a faint metallic
    reflection and subtle noise. Visual style:

      - Body fill in `body_hex`, then a horizontal gradient sweeping
        top->bottom from a slightly lighter tint to a slightly darker
        shadow, evoking a metal strip catching light from above.
      - Optional vignette that brightens the upper-left corner (light
        source from above-left) for a soft 3D curl.
      - Light per-pixel noise (±2 in each channel) so a flat fill never
        reads as plastic.
      - 2 px bottom inner-edge "highlight" in `highlight_hex` and a
        2 px top inner-edge contour in `border_hex` to anchor the band.

    All sizes in canvas pixels. Caller picks `seed` for reproducibility;
    None picks from os.urandom when not set.
    """
    import os as _os
    import random as _random
    body = _hex_to_rgb(body_hex)
    bord = _hex_to_rgb(border_hex)
    hi = _hex_to_rgb(highlight_hex)
    # Lighter highlight color (warm white shifted toward body).
    light = _lerp_color(body, (255, 240, 220), 0.18)
    shadow = _lerp_color(body, (0, 0, 0), 0.32)

    # Build the band as a slice of the canvas for noise + alpha blending.
    band = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    band_px = band.load()
    rng = _random.Random(seed if seed is not None else _os.urandom(4))
    diag_max = max(1, w + h)
    # Small visible diagonal gradient (lower-left darker, upper-right
    # brighter) with magnitude up to 18 per channel. Noise ±2 rides on
    # top so the band still reads as brushed metal, not as plastic.
    rng_diag = _random.Random((seed if seed is not None else 0) ^ 0xA53F)
    drift_lo = tuple(rng_diag.randint(-2, 2) for _ in range(3))
    drift_hi = tuple(rng_diag.randint(-2, 2) for _ in range(3))
    drift_span = (-18, 18)  # max brightness swing along the diagonal
    for j in range(h):
        for i in range(w):
            t_d = (i + j) / diag_max        # 0..1 diagonal progress
            drift_t = drift_span[0] + (drift_span[1] - drift_span[0]) * t_d
            drift = _lerp_color(drift_lo, drift_hi, t_d)
            n = rng.randint(-2, 2)
            band_px[i, j] = (
                max(0, min(255, int(body[0] + drift_t + drift[0] + n))),
                max(0, min(255, int(body[1] + drift_t + drift[1] + n))),
                max(0, min(255, int(body[2] + drift_t + drift[2] + n))),
                255,
            )

    # Paste the band onto the canvas at (x, y).
    canvas.alpha_composite(band, (x, y))

    # Bottom inner-edge highlight (2 px).
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([x, y + h - 2, x + w, y + h - 1], fill=hi)
    # Top inner-edge contour (2 px).
    draw.rectangle([x, y, x + w, y + 1], fill=bord)


def _trim_alpha(img: Image.Image, pad_px: int = 1) -> Image.Image:
    """Trim transparent borders from a sprite, keeping at least `pad_px`
    of transparent margin around the remaining content. Returns the
    cropped RGBA image (or the original if it's already tight).

    Detection: find the bounding box of pixels whose alpha > 0.
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    bbox = img.getbbox()
    if bbox is None:
        # Fully transparent image - return as-is.
        return img
    l, t, r, b = bbox
    cropped = img.crop((max(0, l - pad_px), max(0, t - pad_px),
                         r + pad_px, b + pad_px))
    return cropped


def _trim_alpha_vertical(img: Image.Image, pad_px: int = 1) -> Image.Image:
    """Trim transparent borders only on top/bottom (preserve left/right
    margins). Returns the original size cropped vertically - aspect
    ratio of the content is preserved (no horizontal stretching occurs
    at render time when this trimmed image is rescaled to fit).
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.split()[3]
    bbox_h = alpha.getbbox()
    if bbox_h is None:
        return img
    _l, t, _r, b = bbox_h
    return img.crop((0, max(0, t - pad_px), img.width,
                      min(img.height, b + pad_px)))


def _pale(rgb):
    """Shift a color toward pale: 1.5x brightness, capped at 255."""
    r, g, b = rgb
    return (min(255, int(r * 1.5 + 30)),
            min(255, int(g * 1.5 + 30)),
            min(255, int(b * 1.5 + 30)))


def _tint_glyph(img, fill):
    """Tint a glyph sprite: keep its alpha, set RGB from `fill`."""
    r, g, b = fill[0], fill[1], fill[2]
    alpha = fill[3] if len(fill) == 4 else 255
    channels = img.split()
    a_ch = channels[3]
    if alpha < 255:
        a_ch = a_ch.point(lambda v: v * alpha // 255)
    return Image.merge("RGBA", (
        Image.new("L", img.size, r),
        Image.new("L", img.size, g),
        Image.new("L", img.size, b),
        a_ch,
    ))


_FONT_CACHE = {}


def _scaled_font(size_px: int, weight: str = "regular"):
    """A truetype font (Segoe UI variant) scaled to `size_px` design
    units, falling back to PIL's default if Segoe UI is unavailable.
    """
    key = (size_px, weight)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    p = _FONT_PATHS.get(weight, _FONT_PATHS["regular"])
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(p, size_px)
    except Exception:
        from PIL import ImageFont
        f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


VITAL_ICONS = {
    VitalId.WELLNESS: "sprites/vitals/vital_wellness.png",
    VitalId.STAMINA:  "sprites/vitals/vital_stamina.png",
    VitalId.THIRST:   "sprites/vitals/vital_thirst.png",
    VitalId.HUNGER:   "sprites/vitals/vital_hunger.png",
}

RESOURCE_ICONS = {
    ResourceId.WATER:       "sprites/resources/resource_water.png",
    ResourceId.ELECTRICITY: "sprites/resources/resource_electricity.png",
    ResourceId.BANDWIDTH:   "sprites/resources/resource_bandwidth.png",
    ResourceId.FUEL:        "sprites/resources/resource_fuel.png",
}

RESOURCE_ORDER = [
    ResourceId.WATER,
    ResourceId.ELECTRICITY,
    ResourceId.BANDWIDTH,
    ResourceId.FUEL,
]


def _format_resource_amount(r) -> str:
    """Format a resource amount with metric auto-scale.

    WATER/ELECTRICITY/FUEL: integer, keep one decimal for <10, else round.
    BANDWIDTH: K/M/G Mbps.
    """
    amt = r.total if r.subspecies else r.amount
    unit = r.unit
    if r.id is ResourceId.BANDWIDTH:
        if amt >= 1000:
            return f"{amt / 1000:.1f}G {unit}"
        if amt >= 100:
            return f"{int(round(amt))}M {unit}"
        if amt >= 10:
            return f"{int(round(amt))}M {unit}"
        return f"{amt:.1f}M {unit}"
    if r.id is ResourceId.ELECTRICITY:
        if amt >= 1000:
            return f"{amt / 1000:.2f}k {unit}"  # 2400 Wh -> 2.40k Wh
        return f"{int(round(amt))} {unit}"
    return f"{amt:.1f} {unit}"


def render_window(canvas: Image.Image, x: int, y: int, w: int, h: int,
                   title: str, m: LayoutMetrics, *,
                   show_close: bool = True,
                   body_hex: str = "#1a2230",
                   border_hex: str = "#0a0e15",
                   title_hex: str = "#c19a3c",
                   body_inset: int = 2):
    """Render a normalized window: header band with title (and close x
    if ``show_close``), plus a body region below it.

    The header reuses the metallic+noisy band style so it sits in the
    same visual family as the HUD's top status bar.
    """
    # Window body (square rect with dark face, no outer outline so it
    # sits flush against whatever surface is behind).
    draw = ImageDraw.Draw(canvas)
    body_color = _hex_to_rgb(body_hex)
    draw.rectangle(
        [int(x), int(y), int(x + w), int(y + h)],
        fill=body_color,
    )
    # Header band sits at the top of the body, hugging its edges (no
    # extra inset padding around the header so the title can use the
    # full header height).
    header_h_px = m.px(32)
    hx = int(x)
    hy = int(y)
    hw = int(w)
    hh = int(header_h_px)
    _draw_header_band(canvas, hx, hy, hw, hh,
                       body_hex="#222b3a",
                       border_hex=border_hex,
                       highlight_hex="#c19a3c",
                       seed=hash(title) & 0xFFFFFFFF)
    # Title text. Larger font so it fills the header height nicely.
    font_size = max(8, int(header_h_px * 0.60))
    font = _hud_font(font_size, weight="bold")
    ascent, descent = font.getmetrics()
    bbox = font.getbbox(title)
    bbox_h = bbox[3] - bbox[1]
    # Title: left-aligned past the close-x slot, vertically centered.
    # PIL's draw.text places (x, y) at the font's INTERNAL origin; the
    # ink mass is rendered with a vertical offset that we calibrate
    # empirically so the visible center aligns with the header
    # midpoint.
    target_center_y = hy + hh // 2
    # Empirical offset between draw-text y and rendered ink center for
    # the HUD font at bold weights: ink center sits ~half of
    # (ascent - descent) below draw y.
    center_offset = (ascent - descent) // 2
    draw_y = target_center_y - center_offset - bbox[1]
    tx = hx + m.px(36)
    draw.text((tx - bbox[0], draw_y), title,
              fill=_hex_to_rgb(title_hex), font=font)
    # Close x: anchored at the LEFT side of the header band (just
    # inside the left edge, vertically centered).
    if show_close:
        cx_x = hx + m.px(14)
        cx_y = hy + hh // 2
        # Two strokes to form an X.
        s = m.px(4)
        draw.line([(cx_x - s, cx_y - s), (cx_x + s, cx_y + s)],
                  fill=(220, 90, 90), width=max(1, m.px(2)))
        draw.line([(cx_x - s, cx_y + s), (cx_x + s, cx_y - s)],
                  fill=(220, 90, 90), width=max(1, m.px(2)))
    # Decorative body content area (mockup filler).
    return (int(x), int(y), int(w), int(h))


def render_modal(canvas: Image.Image, x: int, y: int, w: int, h: int,
                  title: str, body: str, m: LayoutMetrics, *,
                  body_hex: str = "#1a2230",
                  border_hex: str = "#0a0e15",
                  dump_pixels: int = 60):
    """Render a modal dialog: same window shell + close x, then a body
    placeholder block where real widgets would mount.
    """
    hh = m.px(32)
    render_window(canvas, x, y, w, h, title, m,
                  show_close=True, body_hex=body_hex,
                  border_hex=border_hex)
    # Textarea = entire area below the header, filling the body so the
    # full working area is available for content (no extra padding).
    body_x = int(x)
    body_y = int(y + hh)
    body_w = int(w)
    body_h = int(h - hh)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(
        [body_x, body_y, body_x + body_w, body_y + body_h],
        fill=_hex_to_rgb("#29344a"),
    )
    # Mockup body text.
    font = _hud_font(m.px(15))
    draw.text((body_x + m.px(8), body_y + m.px(8)),
              body, fill=(220, 224, 230), font=font)
    # Buttons row: a primary (OK) on the right, secondary (Cancel) just
    # to its left, anchored to bottom-right of the body.
    btn_h = m.px(28)
    btn_padding = m.px(10)
    btn_gap = m.px(8)
    btn_w_pad = m.px(40)
    btn_font = _hud_font(m.px(14), weight="bold")
    primary_label = "OK"
    secondary_label = "Cancel"
    primary_w = m.px(btn_w_pad) + btn_font.getbbox(primary_label)[2]
    secondary_w = m.px(btn_w_pad) + btn_font.getbbox(secondary_label)[2]
    row_y = body_y + body_h - btn_h - btn_padding
    primary_x = body_x + body_w - btn_padding - primary_w
    secondary_x = primary_x - btn_gap - secondary_w
    # Secondary: outline-style button.
    sek = _hex_to_rgb("#778899")
    draw.rectangle(
        [secondary_x, row_y, secondary_x + secondary_w, row_y + btn_h],
        fill=_hex_to_rgb("#222b3a"), outline=sek, width=1,
    )
    sbbox = btn_font.getbbox(secondary_label)
    sw_ = sbbox[2] - sbbox[0]
    sascent, sdescent = btn_font.getmetrics()
    s_center_off = (sascent - sdescent) // 2
    suy = row_y + btn_h // 2 - s_center_off - sbbox[1]
    draw.text((secondary_x + (secondary_w - sw_) // 2 - sbbox[0],
               suy),
              secondary_label, fill=(220, 224, 230), font=btn_font)
    # Primary: filled amber button.
    prim = _hex_to_rgb("#c19a3c")
    draw.rectangle(
        [primary_x, row_y, primary_x + primary_w, row_y + btn_h],
        fill=prim,
    )
    pbbox = btn_font.getbbox(primary_label)
    pw_ = pbbox[2] - pbbox[0]
    pascent, pdescent = btn_font.getmetrics()
    p_center_off = (pascent - pdescent) // 2
    puy = row_y + btn_h // 2 - p_center_off - pbbox[1]
    draw.text((primary_x + (primary_w - pw_) // 2 - pbbox[0],
               puy),
              primary_label, fill=(20, 24, 32), font=btn_font)
    return (int(x), int(y), int(w), int(h))


# Color palettes for button color schemes. Each color defines its
# normal body fill, then hover/click/disabled variants are derived by
# mixing with black/white.
BUTTON_COLORS = {
    "red":    ("#a82f2f", "#c44f4f", "#8a2424", "#5a1818", (245, 230, 230)),
    "green":  ("#3b7a4b", "#5fa070", "#2d5b3a", "#1f3d28", (235, 245, 235)),
    "amber":  ("#c19a3c", "#d8b25a", "#a07c2e", "#a47d3d", (20, 24, 32)),
    "slate":  ("#778899", "#92a3b6", "#5d6e7f", "#3e4754", (240, 244, 248)),
}


def render_button(canvas: Image.Image, x: int, y: int, w: int, h: int,
                   label: str, m: LayoutMetrics, *,
                   color: str = "amber",
                   state: str = "unclicked"):
    """Render a square-cornered button.

    color:
      red / green / amber / slate -- selects the palette.
    state:
      unclicked -- the default look (body, 1 px shadow outline,
                   darker top/left, lighter bottom/right).
      hover     -- lighter body, brighter bottom/right edge.
      clicked   -- darker body, dark recess on top/left.
      disabled  -- flat muted gray, dimmed label, no 3D edges.
    """
    if color not in BUTTON_COLORS:
        raise ValueError(f"unknown button color: {color}")
    if state not in ("unclicked", "hover", "clicked", "disabled"):
        raise ValueError(f"unknown button state: {state}")
    body_hex, hover_hex, click_hex, disabled_hex, label_color = (
        BUTTON_COLORS[color]
    )

    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = int(x), int(y), int(x + w), int(y + h)

    # Pick body per state.
    if state == "unclicked":
        body_rgb = _hex_to_rgb(body_hex)
        edge_label = label_color
    elif state == "hover":
        body_rgb = _hex_to_rgb(hover_hex)
        edge_label = label_color
    elif state == "clicked":
        body_rgb = _hex_to_rgb(click_hex)
        edge_label = label_color
    else:  # disabled
        body_rgb = _hex_to_rgb(disabled_hex)
        edge_label = _lerp_color(label_color, (90, 90, 90), 0.55)

    # Body. No 3D edges - flat per state.
    draw.rectangle([x0, y0, x1, y1], fill=body_rgb)

    # Label, vertically centered.
    font_size = max(8, int(h * 0.55))
    font = _hud_font(font_size, weight="bold")
    bbox = font.getbbox(label)
    text_w = bbox[2] - bbox[0]
    ascent, descent = font.getmetrics()
    center_off = (ascent - descent) // 2
    target_cy = y0 + h // 2
    draw_y = target_cy - center_off - bbox[1]
    tx = x0 + (w - text_w) // 2 - bbox[0]
    draw.text((tx, draw_y), label, fill=edge_label, font=font)
    return (x0, y0, x1, y1)


def render_slider(canvas: Image.Image, x: int, y: int, w: int, h: int,
                   value: float, m: LayoutMetrics, *,
                   min_value: float = 0.0,
                   max_value: float = 1.0,
                   track_kind: str = "slate",
                   state: str = "unclicked",
                   show_label: bool = True):
    """Render a horizontal slider.

    track_kind selects the track look:
      slate       -- standard lightslate-gray track.
      lightslate  -- brighter track (lighter gray-blue).
      disabled    -- flat muted track (still drawable but dim).

    state applies to the thumb (track stays muted in all cases).
    """
    """Render a horizontal slider.

    The track is a thin square-cornered bar; the thumb is a square
    knob ICON_SIZE wide that sits at the value position.

    state:
      unclicked / hover / clicked / disabled -- applied to the thumb
      (the track keeps its muted fill in all cases; only the thumb
      's color changes).
    """
    if state not in ("unclicked", "hover", "clicked", "disabled"):
        raise ValueError(f"unknown slider state: {state}")
    if track_kind not in ("slate", "lightslate", "disabled"):
        raise ValueError(f"unknown slider track_kind: {track_kind}")

    # Thumb palette mirrors the red/green/amber/slate families.
    THUMB_COLORS = {
        "red":    ("#a82f2f", "#c44f4f", "#8a2424", "#5a1818"),
        "green":  ("#3b7a4b", "#5fa070", "#2d5b3a", "#1f3d28"),
        "amber":  ("#c19a3c", "#d8b25a", "#a07c2e", "#5e4721"),
        "slate":  ("#778899", "#92a3b6", "#5d6e7f", "#3e4754"),
    }
    _thumb_hex, thumb_hover, thumb_click, thumb_disabled = THUMB_COLORS["slate"]
    # Track-kind overrides: when the entire slider is disabled, the
    # knob also uses the disabled palette regardless of the state.
    if track_kind == "disabled":
        thumb_rgb = _hex_to_rgb("#2a2f38")
    elif track_kind == "slate":
        thumb_rgb = _hex_to_rgb("#708090")
    elif track_kind == "lightslate":
        thumb_rgb = _hex_to_rgb("#778899")
    elif state == "unclicked":
        thumb_rgb = _hex_to_rgb("#778899")
    elif state == "hover":
        thumb_rgb = _hex_to_rgb(thumb_hover)
    elif state == "clicked":
        thumb_rgb = _hex_to_rgb(thumb_click)
    else:
        thumb_rgb = _hex_to_rgb(thumb_disabled)

    # Track palette per track_kind. Use the standard CSS values:
    #   slategray  (#708090) and lightslategray (#778899).
    # Both are also visible against the dark canvas.
    TRACK_COLORS = {
        "slate":       "#708090",
        "lightslate":  "#778899",
        "disabled":    "#2a2f38",
    }
    track_rgb = _hex_to_rgb(TRACK_COLORS[track_kind])
    outline_rgb = _hex_to_rgb("#0a0e15")

    draw = ImageDraw.Draw(canvas)
    x0, y0 = int(x), int(y)
    x1, y1 = int(x + w), int(y + h)

    # Layout: track mid-Y is y0 + h // 2; thumb extends above and below.
    track_h = max(6, m.px(10))
    track_y = y0 + (h - track_h) // 2
    # The track spans the whole slider width in the kind's color.
    draw.rectangle(
        [x0, track_y, x1, track_y + track_h - 1],
        fill=track_rgb, outline=outline_rgb, width=1,
    )

    # Filled portion of the track (from left up to thumb center).
    if max_value > min_value:
        frac = max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))
    else:
        frac = 0.0
    thumb_w = max(14, m.px(14))
    thumb_h = h
    thumb_x = x0 + int(round(frac * (w - thumb_w)))
    thumb_y = y0

    # Thumb: square body, drawn on top of the track.
    thumb_edge = _hex_to_rgb("#0a0e15")
    draw.rectangle(
        [thumb_x, thumb_y, thumb_x + thumb_w - 1, thumb_y + thumb_h - 1],
        fill=thumb_rgb, outline=thumb_edge, width=1,
    )
    # Optional inner notch for grip.
    notch_w = max(2, m.px(3))
    notch_h = max(8, m.px(18))
    notch_x = thumb_x + (thumb_w - notch_w) // 2
    notch_y = thumb_y + (thumb_h - notch_h) // 2
    notch = _lerp_color(thumb_rgb, (0, 0, 0), 0.45)
    draw.rectangle(
        [notch_x, notch_y, notch_x + notch_w - 1, notch_y + notch_h - 1],
        fill=notch,
    )

    # Optional value label above the slider.
    if show_label:
        font = _hud_font(max(8, int(h * 0.40)))
        text = f"{value:.2f}"
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        # Right-aligned over the thumb.
        tx = thumb_x + thumb_w // 2 - text_w // 2
        ty = max(0, y0 - bbox[3] - 2)
        # White-ish label; dimmed when the slider state is disabled.
        if state == "disabled":
            label_rgb = _lerp_color((220, 224, 230), (90, 90, 90), 0.5)
        else:
            label_rgb = (220, 224, 230)
        draw.text((tx - bbox[0], ty - bbox[1]),
                  text, fill=label_rgb, font=font)

    return (x0, y0, x1, y1)


def render_checkbox(canvas: Image.Image, x: int, y: int, size: int,
                     m: LayoutMetrics, *,
                     checked: bool = False,
                     state: str = "unclicked"):
    """Render a square checkbox.

    state:
      unclicked -- normal slate box.
      disabled  -- muted dark gray box, no check glyph even when
                   ``checked``.
    """
    if state not in ("unclicked", "disabled"):
        raise ValueError(f"unknown checkbox state: {state}")
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = int(x), int(y), int(x + size), int(y + size)
    if state == "disabled":
        bg = _hex_to_rgb("#2a2f38")
        edge = _hex_to_rgb("#1b1f27")
    else:
        bg = _hex_to_rgb("#3e4754")
        edge = _hex_to_rgb("#0a0e15")
    draw.rectangle([x0, y0, x1, y1], fill=bg, outline=edge, width=1)
    if checked and state != "disabled":
        # Checkmark: a clean two-stroke check.
        stroke = _hex_to_rgb("#c19a3c")
        pad = max(3, size // 5)
        ax = x0 + pad
        ay = y0 + size // 2
        bx = x0 + size // 3
        by = y1 - pad
        cx = x1 - pad
        cy = y0 + pad
        draw.line([(ax, ay), (bx, by)], fill=stroke, width=2)
        draw.line([(bx, by), (cx, cy)], fill=stroke, width=2)
    return (x0, y0, x1, y1)


def render_radio(canvas: Image.Image, x: int, y: int, size: int,
                  m: LayoutMetrics, *,
                  selected: bool = False,
                  state: str = "unclicked"):
    """Render a round radio button.

    state:
      unclicked -- normal slate disk.
      disabled  -- muted dark gray disk, no inner dot even when
                   ``selected``.
    """
    if state not in ("unclicked", "disabled"):
        raise ValueError(f"unknown radio state: {state}")
    draw = ImageDraw.Draw(canvas)
    cx = int(x + size // 2)
    cy = int(y + size // 2)
    if state == "disabled":
        bg = _hex_to_rgb("#2a2f38")
        edge = _hex_to_rgb("#1b1f27")
    else:
        bg = _hex_to_rgb("#3e4754")
        edge = _hex_to_rgb("#0a0e15")
    r_out = size // 2
    draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out],
                 fill=bg, outline=edge, width=1)
    if selected and state != "disabled":
        # Filled inner dot in amber.
        r_in = max(2, size // 3)
        fill = _hex_to_rgb("#c19a3c")
        draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in],
                     fill=fill)
    return (cx - r_out, cy - r_out, cx + r_out, cy + r_out)


def render_top_status_bar(canvas: Image.Image, state: HudState,
                          ts: TimeSystem, m: LayoutMetrics):
    """Layout-driven status bar: every section is a Div with explicit
    bounds; widget positions derive from the div's local origin.
    Move a div -> the entire section moves with it.
    """
    layout = build_layout(m.canvas_w, m.canvas_h)
    page = layout["page"]
    vital_widgets = layout["vital_widgets"]
    speed_widgets = layout["speed_widgets"]
    resource_widgets = layout["resource_widgets"]
    res_y_center = 0  # unused; alignment uses icon center directly
    header_div = page.get("header")
    vitals_div = page.get("vitals")
    time_div = page.get("time")
    speed_div = page.get("speed")
    resources_div = page.get("resources")

    # ---- Header (status bar panel) ----
    panel_rect = m.px(0), m.px(0), m.canvas_w, m.px(HEADER_H_SRC := DIV_SIZE["header_h"])
    _draw_full_width_panel(canvas, m, height_src=DIV_SIZE["header_h"])
    draw = ImageDraw.Draw(canvas)
    font = _hud_font(15)

    # ---- Cell highlights removed (no outline) ----
    vital_cells = layout.get("vital_cells") or []
    resource_cells = layout.get("resource_cells") or []   # noqa: 841
    inner_y = DIV_SIZE['header_h']  # placeholder, will be reset
    inner_h = DIV_SIZE['header_h'] // 2

    # ---- Draw pill-shaped "well" backgrounds for the VITAL and
    # RESOURCE GROUPS. The well is a slightly brighter slab in the
    # same color family as the header band. The body uses a soft
    # top-to-bottom gradient (top darker, bottom brighter). The
    # perimeter is 3D: dark along the top + left edges, light along
    # the bottom + right edges - both wrap around the rounded ends.
    def _draw_group_well(div):
        # The well div's bounds ALREADY include the inner pad; draw a
        # square-corner group with a single body color and a 3D-style
        # border (dark top/left, lighter bottom/right).
        cx = int(div.x * m.s)
        cy = int(div.y * m.s)
        cw = int(div.w * m.s)
        ch = int(div.h * m.s)
        bg = _hex_to_rgb("#29344a")
        shadow = _hex_to_rgb("#0a0e15")
        highlight = _hex_to_rgb("#8b9cba")
        # Body.
        draw.rectangle(
            [cx, cy, cx + cw - 1, cy + ch - 1],
            fill=bg,
        )
        # 3D border (square corners).
        # Top + left edges = shadow.
        draw.line([(cx, cy), (cx + cw - 1, cy)], fill=shadow, width=1)
        draw.line([(cx, cy), (cx, cy + ch - 1)], fill=shadow, width=1)
        # Bottom + right edges = highlight.
        draw.line([(cx, cy + ch - 1), (cx + cw - 1, cy + ch - 1)],
                  fill=highlight, width=1)
        draw.line([(cx + cw - 1, cy), (cx + cw - 1, cy + ch - 1)],
                  fill=highlight, width=1)

    layout_divs = layout.get("divs", {})
    hdr = layout_divs.get("header")
    vitals_group = layout_divs.get("vitals")
    resources_group = layout_divs.get("resources")
    header_right = (hdr.x + hdr.w) if hdr is not None else m.canvas_w
    # Compute the visible extent of children inside each group so the
    # well tightly wraps them (the div itself may have trailing padding).
    def _child_extent(parent, children):
        if not children:
            return None
        x0 = min(c.x for c in children) - parent.x
        y0 = min(c.y for c in children) - parent.y
        x1 = max(c.x + c.w for c in children) - parent.x
        y1 = max(c.y + c.h for c in children) - parent.y
        return x0, y0, x1 - x0, y1 - y0

    WELL_PAD_L, WELL_PAD_R, WELL_PAD_T, WELL_PAD_B = 1, 1, 1, 1

    def _build_well_in_header(header, cells, name, content_h, anchor,
                               outer_l, outer_r, content_h_used):
        if header is None or not cells:
            return None
        from dataclasses import replace as _replace
        header_local = _replace(header, x=0, y=0)
        ext = _child_extent(header_local, cells)
        ww_inner = ext[2] + WELL_PAD_L + WELL_PAD_R
        wh_inner = content_h_used + WELL_PAD_T + WELL_PAD_B
        ext0 = ext[0]
        ext_right = ext[0] + ext[2]
        # Position the well at the configured anchor offset from the
        # canvas edge. With anchor='left', the well's LEFT EDGE sits
        # outer_l px from the canvas left; anchor='right' places the
        # RIGHT EDGE outer_r px from the canvas right. Cells stay
        # centered inside the well symmetrically.
        if anchor == "left":
            wx = header.x + outer_l
        elif anchor == "right":
            wx = header.x + header.w - outer_r - ww_inner
        else:
            wx = header.x + (header.w - ww_inner) // 2
        # Place vertically so the well aligns with the cells' content
        # center rather than the header's vertical center.
        if cells:
            c_top = min(c.y for c in cells)
            c_bot = max(c.y + c.h for c in cells)
            content_center_y = (c_top + c_bot) // 2
            wy = content_center_y - wh_inner // 2
        else:
            wy = header.y + (header.h - wh_inner) // 2
        return Div(name=name, x=wx, y=wy, w=ww_inner, h=wh_inner)

    vitals_well = _build_well_in_header(hdr, vital_cells, "_vitals_well",
                                          DIV_SIZE['vital_icon'],
                                          anchor="left", outer_l=8,
                                          outer_r=0,
                                          content_h_used=18)
    resources_well = _build_well_in_header(hdr, resource_cells,
                                            "_resources_well",
                                            DIV_SIZE['res_icon'],
                                            anchor="right", outer_l=0,
                                            outer_r=8,
                                            content_h_used=18)
    # Position cells so they sit centered inside the well: cells
    # shift horizontally to match the well's inner left, and the well
    # itself is positioned to vertically center over the cells.
    def _center_cells_in_well(well, cells):
        if well is None or not cells:
            return
        dx = (well.x + WELL_PAD_L) - min(c.x for c in cells)
        for c in cells:
            c.x += dx
        # Vertical: cell height is fixed by layout; well only widens to
        # match cell height. No dy shift needed.

    _center_cells_in_well(vitals_well, vital_cells)
    _center_cells_in_well(resources_well, resource_cells)
    if vitals_well is not None:
        _draw_group_well(vitals_well)
    if resources_well is not None:
        _draw_group_well(resources_well)

    # ---- Vitals: 2 widgets per vital (icon + bar) ----
    n_vitals = len(state.vitals)
    for i, (wid, (vital_id, vital)) in enumerate(
        zip(vital_widgets[:n_vitals * 2:2], state.vitals.items())
    ):
        icon_w = vital_widgets[i * 2]
        bar_w = vital_widgets[i * 2 + 1]
        # Anchor-derived absolute canvas coords.
        m_factor = m.s
        ix = int(icon_w.abs_x() * m_factor)
        iy = int(icon_w.abs_y() * m_factor)
        iw = int(icon_w.w * m_factor)
        ih = int(icon_w.h * m_factor)
        # Draw icon
        icon_path = os.path.join(KIT_ROOT, VITAL_ICONS[vital_id])
        # Hard-trim to subject bbox (no pipeline whitespace).
        icon_img = _trim_alpha(Image.open(icon_path).convert("RGBA"),
                                pad_px=0)
        sc_w, sc_h = icon_img.width, icon_img.height
        scale = min(iw / sc_w, ih / sc_h) if sc_w and sc_h else 1.0
        new_w = max(1, int(sc_w * scale))
        new_h = max(1, int(sc_h * scale))
        icon_img = icon_img.resize((new_w, new_h), Image.LANCZOS)
        # Cell-center the cropped subject.
        px0 = ix + (iw - new_w) // 2
        py0 = iy + (ih - new_h) // 2
        canvas.alpha_composite(icon_img, (px0, py0))
        # Vital bar y stays the same so it aligns to the cell.
        # (Vital icon bounding-box outline removed.)
        # Draw bar
        val_clamped = max(-100, min(100, vital.value))
        bx = int(bar_w.abs_x() * m_factor)
        by = int(bar_w.abs_y() * m_factor)
        bw = int(bar_w.w * m_factor)
        bh = int(bar_w.h * m_factor)
        border_hex = (0x4a, 0x52, 0x60, 255)
        empty_hex = (0x16, 0x1e, 0x28, 255)
        bar_radius = max(2, bh // 2)
        draw.rounded_rectangle(
            [bx, by, bx + bw, by + bh],
            radius=bar_radius, fill=empty_hex,
            outline=border_hex, width=max(1, int(2 * m_factor)),
        )
        cx_bar = bx + bw // 2
        side_max = bw // 2
        amber = (255, 213, 79)
        green = (74, 196, 124)
        red = (220, 110, 90)

        def draw_band(xa, xb, c0, c1):
            """Fill the vertical band [xa..xb] with a left->right gradient
            from color c0 to c1 (RGB tuples).
            """
            if xb < xa:
                return
            span = max(1, xb - xa)
            for px in range(xa, xb + 1):
                t = (px - xa) / span
                color = _lerp_color(c0, c1, t)
                draw.line([(px, by + 1), (px, by + bh - 1)], fill=color, width=1)

        # Each side's full positive bar (val = 100) spans side_max.
        # Amber occupies 25 units of value (giving the band 25% of side_max).
        # Gradient takes the remaining value (0..75).
        amber_w = int(round(side_max * 0.25))

        if val_clamped > 0:
            # Solid amber zone: from center to amber_w (always drawn when
            # val > 0).
            ax_end = min(bx + bw - 1, cx_bar + amber_w)
            draw_band(cx_bar + 1, ax_end, amber, amber)
            if val_clamped > 25:
                # Gradient amber -> green from amber end to value end.
                v_frac = (val_clamped - 25) / 75.0
                gx_end = min(bx + bw - 1,
                              cx_bar + amber_w + int(round(v_frac * side_max * 0.75)))
                draw_band(ax_end + 1, gx_end, amber, green)
        elif val_clamped < 0:
            ax_end = max(bx + 1, cx_bar - amber_w)
            draw_band(ax_end, cx_bar - 1, amber, amber)
            if val_clamped < -25:
                v_frac = ((-val_clamped) - 25) / 75.0
                gx_end = max(bx + 1,
                              cx_bar - amber_w - int(round(v_frac * side_max * 0.75)))
                draw_band(gx_end, ax_end - 1, red, amber)
        # Center marker remains
        draw.line([(cx_bar, by + 1), (cx_bar, by + bh - 1)],
                  fill=(255, 255, 255, 220), width=1)
        # Center marker
        draw.line([(cx_bar, by + 1), (cx_bar, by + bh - 1)],
                  fill=(255, 255, 255, 220), width=1)

    # ---- Time + Speed ----
    snap = ts.snapshot()
    s_season = snap.season.value   # Title case as-is ("Spring", "Summer")
    s_day = f"Day {snap.day_of_year}"
    s_time = format_wall_clock(snap.cycle_minute)
    time_line = f"{s_season}, {s_day} {s_time}"
    time_font_size = max(10, int(DIV_SIZE['header_h'] * 0.32 * m.s))
    time_font = _hud_font(time_font_size, weight="bold")
    bbox = draw.textbbox((0, 0), time_line, font=time_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    time_line_x = int(time_div.x + (time_div.w * m.s - text_w) // 2)
    time_line_y = int(time_div.y * m.s) + max(1, int(m_factor_or_s := m.s))
    draw.text((time_line_x, time_line_y), time_line,
              fill=(220, 224, 230), font=time_font)

    speed_glyphs = [
        ("speed_pause.png", Speed.PAUSE),
        ("speed_1x.png", Speed.SPEED_1X),
        ("speed_3x.png", Speed.SPEED_3X),
        ("speed_5x.png", Speed.SPEED_5X),
        ("speed_9x.png", Speed.SPEED_9X),
    ]
    speed_y = int(time_line_y + text_h + DIV_SIZE['speed_text_pad'] * m.s)
    n_chips = len(speed_widgets)
    active_speed = ts.speed
    for i, (png_name, sp) in enumerate(speed_glyphs):
        wid = speed_widgets[i]
        sw = int(wid.w * m.s)
        sx = int(wid.abs_x() * m.s)
        cy = int(wid.abs_y() * m.s)
        is_active = sp is active_speed
        idle = (160, 168, 180, 255)
        active = (241, 196, 15, 255)
        icon_img = Image.open(os.path.join(SPRITES_ROOT, "speed_controls",
                                            png_name)).convert("RGBA")
        icon_img = icon_img.resize((sw, sw), Image.LANCZOS)
        tinted = _tint_glyph(icon_img, active if is_active else idle)
        canvas.alpha_composite(tinted, (sx, cy))

    # ---- Resources ----
    res_font_size = m.px(15)
    res_font = _hud_font(res_font_size)
    n_res = len(RESOURCE_ORDER)
    for i in range(n_res):
        r = state.resources[RESOURCE_ORDER[i]]
        icon_wid = resource_widgets[i * 2]
        text_wid = resource_widgets[i * 2 + 1]
        ix = int(icon_wid.abs_x() * m.s)
        iy = int(icon_wid.abs_y() * m.s)
        iw = int(icon_wid.w * m.s)
        ih = int(icon_wid.h * m.s)
        icon_path = os.path.join(KIT_ROOT, RESOURCE_ICONS[RESOURCE_ORDER[i]])
        # Hard-trim to subject bbox: removes pipeline whitespace on all
        # sides so the cell center really aligns with the mass.
        icon_img = _trim_alpha(Image.open(icon_path).convert("RGBA"),
                                pad_px=0)
        sc_w, sc_h = icon_img.width, icon_img.height
        scale = min(iw / sc_w, ih / sc_h) if sc_w and sc_h else 1.0
        new_w = max(1, int(sc_w * scale))
        new_h = max(1, int(sc_h * scale))
        icon_img = icon_img.resize((new_w, new_h), Image.LANCZOS)
        px0 = ix + (iw - new_w) // 2
        py0 = iy + (ih - new_h) // 2
        canvas.alpha_composite(icon_img, (px0, py0))
        # Text aligns to the SUBJECT's actual center (post-trim +
        # scale + cell-center), not the cell center.
        subject_center_y = py0 + new_h // 2
        value_text = _format_resource_amount(r)
        text_bbox = draw.textbbox((0, 0), value_text, font=res_font)
        text_h = text_bbox[3] - text_bbox[1]
        bbox_top = text_bbox[1]
        tx = ix + iw + m.px(2)
        # Place bbox-center at subject_center_y. PIL draws text with its
        # ascent baseline at y; bbox[1] is the top edge of ink (often
        # negative for TrueType). y = center - (bbox_top + text_h/2).
        text_y = subject_center_y - (bbox_top + text_h / 2)
        draw.text((tx, text_y), value_text,
                  fill=(220, 224, 230), font=res_font)


def _grid_overlay(canvas: Image.Image, m: LayoutMetrics) -> Image.Image:
    """Return a soft overlay showing the 9-cell grid. Used in debug
    previews only.
    """
    overlay = Image.new("RGBA", (m.canvas_w, m.canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cell_w = m.canvas_w // 3
    cell_h = m.canvas_h // 3
    line_color = (180, 200, 220, 80)
    for i in (1, 2):
        x = i * cell_w
        draw.line([(x, 0), (x, m.canvas_h)], fill=line_color, width=1)
    for j in (1, 2):
        y = j * cell_h
        draw.line([(0, y), (m.canvas_w, y)], fill=line_color, width=1)
    return Image.alpha_composite(canvas, overlay)


def render_speed_controls(canvas: Image.Image, state: HudState,
                          ts: TimeSystem, m: LayoutMetrics):
    """Speed chips are rendered inside the top status bar (see
    render_top_status_bar). This entry point exists for compatibility.
    """
    pass


def render_toolbar(canvas: Image.Image, state: HudState, m: LayoutMetrics):
    """Toolbar: layout-driven slot row at bottom-right. Position
    derived from the toolbar Div + slot Widgets.
    """
    layout = build_layout(m.canvas_w, m.canvas_h)
    toolbar_div = layout["page"].get("toolbar")
    slot_w = layout["toolbar_widgets"]
    draw = ImageDraw.Draw(canvas)
    bord = _hex_to_rgb("#0a0e15")
    body_status = _hex_to_rgb("#0e1b20")
    selected_bg = _hex_to_rgb("#778899")  # lightslategray
    active_top = _hex_to_rgb("#c19a3c")
    font = _hud_font(18, weight="bold")
    for i, slot in enumerate(state.toolbar):
        wid = slot_w[i]
        x = int(wid.abs_x() * m.s)
        y = int(wid.abs_y() * m.s)
        slot_size = int(wid.w * m.s)
        # Slot body. Use the lightslate outline for the selected slot
        # so all four sides match.
        slot_fill = selected_bg if i == state.selected_slot else body_status
        slot_outline = selected_bg if i == state.selected_slot else bord
        draw.rectangle([x, y, x + slot_size, y + slot_size],
                       fill=slot_fill, outline=slot_outline, width=m.px(2))
        if i == state.selected_slot:
            # 2 px tall selector line along the top edge.
            draw.rectangle([x - 1, y - 1, x + slot_size + 1, y + 1],
                           fill=active_top)
        if slot.icon_id:
            icon_path = _find_icon_path(slot.icon_id)
            if icon_path:
                icon_img = Image.open(icon_path).convert("RGBA")
                icon_size = slot_size - 2 * m.px(8)
                # Aspect-ratio-preserving scale to fit the slot box.
                max_dim = max(icon_size, icon_size)
                sc_w, sc_h = icon_img.width, icon_img.height
                scale = min(icon_size / sc_w, icon_size / sc_h) if sc_w and sc_h else 1.0
                new_w = max(1, int(sc_w * scale))
                new_h = max(1, int(sc_h * scale))
                icon_img = icon_img.resize((new_w, new_h), Image.LANCZOS)
                canvas.alpha_composite(
                    icon_img,
                    (x + m.px(8), y + m.px(8)),
                )
        if slot.icon_id and slot.count > 1:
            label = f"{slot.count}"
            text_bbox = draw.textbbox((0, 0), label, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            text_h = text_bbox[3] - text_bbox[1]
            ascent, _ = font.getmetrics()
            # Position text inside the slot, anchored to the bottom-right
            # with explicit padding. PIL's draw.text uses the baseline as
            # the y reference, so we offset by ascent.
            pad = 6
            tx = x + slot_size - text_w - pad
            ty = y + slot_size - pad - ascent
            draw.text((tx, ty), label, fill=(241, 196, 15), font=font)


def render_full(canvas_size: Tuple[int, int],
                state: HudState,
                ts: TimeSystem,
                show_grid: bool = False) -> Image.Image:
    """Render the full HUD. Works at any canvas size because every
    coordinate is scaled off DESIGN_W/DESIGN_H via LayoutMetrics.
    """
    m = LayoutMetrics(canvas_size[0], canvas_size[1])
    canvas = Image.new("RGBA", canvas_size, (15, 18, 26, 0))
    # Cheap fake 3D world for visual smoke-test contrast.
    w, h = canvas_size
    scenew = Image.new("RGB", (w, h), (90, 110, 70)).convert("RGBA")
    sky_h = max(1, h // 3)
    for y_idx in range(sky_h):
        t = y_idx / sky_h
        rr = int(140 + (200 - 140) * t)
        gg = int(170 + (220 - 170) * t)
        bb = int(190 + (235 - 190) * t)
        # Speed up significantly with draw.rect per row rather than
        # per-pixel putpixel.
        draw = ImageDraw.Draw(scenew)
        draw.rectangle([(0, y_idx), (w, y_idx + 1)],
                        fill=(rr, gg, bb, 255))
    for y_idx in range(sky_h, h):
        t = (y_idx - sky_h) / max(1, h - sky_h - 1)
        base_g = 110 + int(40 * t)
        draw = ImageDraw.Draw(scenew)
        draw.rectangle(
            [(0, y_idx), (w, y_idx + 1)],
            fill=(70, base_g, 50, 255),
        )
    canvas.alpha_composite(scenew, (0, 0))

    render_top_status_bar(canvas, state, ts, m)
    render_speed_controls(canvas, state, ts, m)
    render_toolbar(canvas, state, m)

    if show_grid:
        canvas = _grid_overlay(canvas, m)
    return canvas
