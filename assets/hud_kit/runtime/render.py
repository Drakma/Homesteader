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
from .divlayout import build_layout, SIZE as DIV_SIZE
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

    Body and border are drawn as flat rectangles so there are no
    interpolation gaps when stretched across the entire canvas.
    Highlight color goes along the bottom edge inside the bar.

    Returns (x, y, w, h).
    """
    panel_w = m.canvas_w
    panel_h = m.px(height_src)
    y = 0                 # flush against canvas top - no gap
    x = 0
    draw = ImageDraw.Draw(canvas)
    if body_hex is None:
        body_hex = "#18202c"
    if border_hex is None:
        border_hex = "#0a0e15"
    if highlight_hex is None:
        # Default highlight: amber accent from palette.
        highlight_hex = "#c19a3c"
    body = _hex_to_rgb(body_hex)
    bord = _hex_to_rgb(border_hex)
    hi = _hex_to_rgb(highlight_hex)
    draw.rectangle([x, y, x + panel_w, y + panel_h], fill=body)
    draw.rectangle([x, y, x + panel_w, y + m.px(2)],
                   fill=bord)
    # The highlight IS the bottom line of the bar so it is the last
    # 1px-line. Anything drawn below this (from compositing later) sits
    # against the canvas background, never underneath the highlight.
    hi_y = y + panel_h - m.px(1)
    draw.rectangle([x, hi_y, x + panel_w, hi_y + m.px(1)],
                   fill=hi)
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
    font = _hud_font(15)
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
