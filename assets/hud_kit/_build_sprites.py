"""_build_sprites.py - procedural HUD kit generator.

Produces every sprite in assets/hud_kit/sprites/ from the rules in
STYLE_GUIDE.md + palette.json. Idempotent: deleting the existing
sprites directory and rerunning regenerates the exact same files.

Canvas spec (palette.json):
  - 128x128 RGBA8
  - interior 104x104 content box, 12 px margin
  - 2 px border, 8 px corner radius

Run:
    python assets/hud_kit/_build_sprites.py
"""

import json
import math
import os
from PIL import Image, ImageDraw

KIT_ROOT = r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit"
SPRITES_ROOT = os.path.join(KIT_ROOT, "sprites")
PALETTE_PATH = os.path.join(KIT_ROOT, "palette.json")

CANVAS = 128
MARGIN = 12
CONTENT_BOX = CANVAS - 2 * MARGIN  # 104
BORDER = 2
CORNER = 0  # square corners everywhere; 0 disables rounded_rect rounding
BORDER_HEX = "#0a0e15"
HOVER_BORDER_HEX = "#1a1f29"
SELECTED_BORDER_HEX = "#c19a3c"


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _draw_rounded_rect(canvas_img: Image.Image, x0, y0, x1, y1,
                       radius, body_rgb, border_rgb,
                       border_px: int = BORDER):
    """Draw a rounded rectangle with the kit's standard border."""
    draw = ImageDraw.Draw(canvas_img)
    # Body fill first.
    draw.rounded_rectangle(
        [x0, y0, x1, y1], radius=radius,
        fill=body_rgb,
    )
    # 1-px top + left highlight: add +12 to body RGB (clamped 255).
    hl_rgb = tuple(min(255, c + 12) for c in body_rgb)
    for offset in range(border_px):
        # Top edge highlight (segmented to corners).
        draw.line([(x0 + radius, y0 + offset),
                   (x1 - radius, y0 + offset)], fill=hl_rgb)
        # Left edge highlight (segmented to corners).
        draw.line([(x0 + offset, y0 + radius),
                   (x0 + offset, y1 - radius)], fill=hl_rgb)
    # Border.
    if border_px:
        draw.rounded_rectangle(
            [x0, y0, x1, y1], radius=radius,
            outline=border_rgb, width=border_px,
        )


def blank_canvas():
    return Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))


def _wb(*args, **kwargs):
    """Write a mostly-empty PNG to disk."""
    pass


def draw_panel(body_hex: str, radius: int = CORNER):
    img = blank_canvas()
    body = _hex_to_rgb(body_hex)
    border = _hex_to_rgb(BORDER_HEX)
    x0, y0 = MARGIN, MARGIN
    x1, y1 = CANVAS - MARGIN - 1, CANVAS - MARGIN - 1
    _draw_rounded_rect(img, x0, y0, x1, y1, radius, body, border)
    return img


def draw_button(body_hex: str, state: str, radius: int = CORNER):
    """state in {normal, hover, pressed, disabled}."""
    img = blank_canvas()
    body = _hex_to_rgb(body_hex)
    if state == "hover":
        body = tuple(min(255, c + 8) for c in body)
        border = _hex_to_rgb(HOVER_BORDER_HEX)
    elif state == "pressed":
        body = tuple(max(0, c - 8) for c in body)
        border = _hex_to_rgb(HOVER_BORDER_HEX)
    elif state == "disabled":
        body = tuple(int(c * 0.55) for c in body)
        border = _hex_to_rgb(BORDER_HEX)
    else:  # normal
        border = _hex_to_rgb(BORDER_HEX)
    x0, y0 = MARGIN, MARGIN
    x1, y1 = CANVAS - MARGIN - 1, CANVAS - MARGIN - 1
    # For disabled state, we drop the body alpha to 0.55.
    if state == "disabled":
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=body)
        # Reduce body alpha through Image.putalpha.
        r, g, b, _ = img.split()
        # Use a rect alpha mask: full alpha inside the body shape.
        body_mask = Image.new("L", (CANVAS, CANVAS), 0)
        mdraw = ImageDraw.Draw(body_mask)
        mdraw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=140)
        # composite body color back with reduced alpha.
        composed = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        body_img = Image.new("RGBA", (CANVAS, CANVAS), body + (255,))
        composed.paste(body_img, (0, 0), body_mask)
        for offset in range(BORDER):
            draw.line([(x0 + radius, y0 + offset),
                       (x1 - radius, y0 + offset)],
                      fill=tuple(min(255, c + 12) for c in body))
            draw.line([(x0 + offset, y0 + radius),
                       (x0 + offset, y1 - radius)],
                      fill=tuple(min(255, c + 12) for c in body))
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius,
                               outline=border, width=BORDER)
        img = Image.alpha_composite(img, composed)
    else:
        _draw_rounded_rect(img, x0, y0, x1, y1, radius, body, border)
    return img


def draw_slot(active: bool = False, ratio: str = "1x1"):
    img = blank_canvas()
    body = _hex_to_rgb("#0e1b20")
    border = _hex_to_rgb("#0a0e15") if not active else _hex_to_rgb(SELECTED_BORDER_HEX)
    if ratio == "1x1":
        x0, y0 = MARGIN, MARGIN
        x1, y1 = CANVAS - MARGIN - 1, CANVAS - MARGIN - 1
    elif ratio == "1x2":
        # Wide slot: 1x2 cells = double-wide on horizontal axis.
        x0, y0 = MARGIN, MARGIN + 12
        x1, y1 = CANVAS - MARGIN - 1, CANVAS - MARGIN - 13
    else:
        raise ValueError(ratio)
    _draw_rounded_rect(img, x0, y0, x1, y1, CORNER + 2, body, border,
                       border_px=2)
    # If active, add a centered inset highlight ring.
    if active:
        draw = ImageDraw.Draw(img)
        inset = 6
        draw.rounded_rectangle(
            [x0 + inset, y0 + inset, x1 - inset, y1 - inset],
            radius=CORNER,
            outline=tuple(_hex_to_rgb("#c19a3c")),
            width=2,
        )
    return img


def draw_divider(orientation: str = "h"):
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    rgb = _hex_to_rgb("#1a1f29")
    mid = CANVAS // 2
    if orientation == "h":
        # 64 px wide centered line.
        x0, x1 = CANVAS // 2 - 32, CANVAS // 2 + 32
        draw.line([(x0, mid), (x1, mid)], fill=rgb, width=2)
    else:
        y0, y1 = CANVAS // 2 - 32, CANVAS // 2 + 32
        draw.line([(mid, y0), (mid, y1)], fill=rgb, width=2)
    return img


def draw_corner(position: str):
    """Quarter-round in one of {tl, tr, bl, br}."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#0a0e15")
    radius = 24
    if position == "tl":
        draw.pieslice([MARGIN, MARGIN, MARGIN + radius * 2,
                       MARGIN + radius * 2],
                      start=180, end=270, fill=body)
    elif position == "tr":
        draw.pieslice([CANVAS - MARGIN - radius * 2, MARGIN,
                       CANVAS - MARGIN - 1, MARGIN + radius * 2],
                      start=270, end=360, fill=body)
    elif position == "bl":
        draw.pieslice([MARGIN, CANVAS - MARGIN - radius * 2,
                       MARGIN + radius * 2, CANVAS - MARGIN - 1],
                      start=90, end=180, fill=body)
    elif position == "br":
        draw.pieslice([CANVAS - MARGIN - radius * 2,
                       CANVAS - MARGIN - radius * 2,
                       CANVAS - MARGIN - 1, CANVAS - MARGIN - 1],
                      start=0, end=90, fill=body)
    else:
        raise ValueError(position)
    return img


def draw_close_x():
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    rgb = _hex_to_rgb("#c4c8cf")
    mid = CANVAS // 2
    size = 18
    draw.line([(mid - size // 2, mid - size // 2),
               (mid + size // 2, mid + size // 2)],
              fill=rgb, width=2)
    draw.line([(mid - size // 2, mid + size // 2),
               (mid + size // 2, mid - size // 2)],
              fill=rgb, width=2)
    return img


def draw_glow_accent():
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    rgb = _hex_to_rgb("#c19a3c")
    mid = CANVAS // 2
    for r in range(8, 0, -2):
        a = int(255 * (r / 8) ** 2)
        overlay = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([mid - r, mid - r, mid + r, mid + r], fill=rgb + (a,))
        img = Image.alpha_composite(img, overlay)
    return img


def draw_separator_dot():
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    rgb = _hex_to_rgb("#7a8392")
    mid = CANVAS // 2
    draw.ellipse([mid - 2, mid - 2, mid + 2, mid + 2], fill=rgb)
    return img


def draw_double_divider():
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    rgb = _hex_to_rgb("#1a1f29")
    mid = CANVAS // 2
    x0, x1 = CANVAS // 2 - 30, CANVAS // 2 + 30
    draw.line([(x0, mid - 2), (x1, mid - 2)], fill=rgb, width=1)
    draw.line([(x0, mid + 2), (x1, mid + 2)], fill=rgb, width=1)
    return img


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def trim_to_visual_mass(img: Image.Image, pad: int = 1) -> Image.Image:
    # Trim transparent borders so the sprite has its actual visual mass
    # with a 1px margin on all sides while maintaining its original aspect.
    bbox = img.getbbox()
    if not bbox:
        return img
    cropped = img.crop(bbox)
    bw, bh = cropped.size
    out = Image.new("RGBA", (bw + 2 * pad, bh + 2 * pad), (0, 0, 0, 0))
    out.paste(cropped, (pad, pad))
    return out


def _save(img: Image.Image, path: str):
    _ensure_dir(os.path.dirname(path))
    img.save(path, "PNG")


PANEL_BODY = "#18202c"
STATUS_BODY = "#0e1b20"
BTN_SLATE = "#253142"
BTN_AMBER = "#784b06"
BTN_GREEN = "#1e4620"
SELECTED_ACCENT = "#c19a3c"

PANELS = [
    ("panel_compact_dialog", PANEL_BODY, 0),
    ("panel_large_dialog",   PANEL_BODY, 0),
    ("panel_drawer",         PANEL_BODY, 0),
    ("panel_modal",          PANEL_BODY, 0),
    ("panel_toast",          STATUS_BODY, 0),
]
BUTTON_COLORS = [
    ("slate", BTN_SLATE),
    ("amber", BTN_AMBER),
    ("green", BTN_GREEN),
]
BUTTON_STATES = ["normal", "hover", "pressed", "disabled"]
SLOTS = [
    ("slot_1x1",         False, "1x1"),
    ("slot_1x1_active",  True,  "1x1"),
    ("slot_1x2",         False, "1x2"),
]
DIVIDERS = [
    ("divider_h",   "h"),
    ("divider_v",   "v"),
    ("corner_tl",   "tl"),
    ("corner_tr",   "tr"),
    ("corner_bl",   "bl"),
    ("corner_br",   "br"),
]
DECORS = [
    ("close_x",        draw_close_x),
    ("glow_accent",    draw_glow_accent),
    ("separator_dot",  draw_separator_dot),
    ("double_divider", draw_double_divider),
]

SPEED_CONTROLS_DIR = os.path.join(SPRITES_ROOT, "speed_controls")
VITALS_DIR = os.path.join(SPRITES_ROOT, "vitals")
RESOURCES_DIR = os.path.join(SPRITES_ROOT, "resources")
os.makedirs(SPEED_CONTROLS_DIR, exist_ok=True)
os.makedirs(VITALS_DIR, exist_ok=True)
os.makedirs(RESOURCES_DIR, exist_ok=True)


def draw_speed_pause():
    """Universal pause icon: two vertical bars centered."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#dde3ea")
    bar_w = 18
    bar_h = 60
    left_x = CANVAS // 2 - bar_w - 6
    right_x = CANVAS // 2 + 6
    bar_y = (CANVAS - bar_h) // 2
    draw.rounded_rectangle([left_x, bar_y, left_x + bar_w - 1,
                            bar_y + bar_h - 1],
                           radius=4, fill=body)
    draw.rounded_rectangle([right_x, bar_y, right_x + bar_w - 1,
                            bar_y + bar_h - 1],
                           radius=4, fill=body)
    return img


def draw_speed_play(n_arrows: int):
    """One icon with `n_arrows` overlapping play triangles offset to
    the right of each other. Universal play triangle shape.
    """
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#dde3ea")
    # Total width budget: 104 (subject area).
    tri_w = 36
    tri_h = 64
    cx_center = CANVAS // 2
    base_x = MARGIN + 4
    base_y = (CANVAS - tri_h) // 2
    for i in range(n_arrows):
        offset = i * 14
        # Play triangle: left edge straight, right edge pointed.
        pts = [
            (base_x + offset, base_y),
            (base_x + offset, base_y + tri_h),
            (base_x + offset + tri_w, base_y + tri_h // 2),
        ]
        # For overlapping triangles, draw with reduced alpha on back.
        alpha = 255 - i * 40 if i > 0 else 255
        color = body + (alpha,)
        draw.polygon(pts, fill=color)
    return img


def draw_vital_wellness():
    """Simple heart silhouette + medical cross."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#d05060")
    cx, cy = CANVAS // 2, CANVAS // 2
    r = 22
    draw.ellipse([cx - r * 2 + 4, cy - r - 8,
                  cx, cy + r // 2 - 8], fill=body)
    draw.ellipse([cx, cy - r - 8,
                  cx + r * 2 - 4, cy + r // 2 - 8], fill=body)
    draw.polygon([
        (cx - r * 2, cy - 4),
        (cx + r * 2, cy - 4),
        (cx, CANVAS - MARGIN - 8),
    ], fill=body)
    arm_t = 6
    cross_h = 30
    cross_w = 30
    ccx = cx
    ccy = cy - 8
    draw.rectangle([ccx - arm_t // 2, ccy - cross_h // 2,
                    ccx + arm_t // 2, ccy + cross_h // 2],
                   fill=(255, 255, 255))
    draw.rectangle([ccx - cross_w // 2, ccy - arm_t // 2,
                    ccx + cross_w // 2, ccy + arm_t // 2],
                   fill=(255, 255, 255))
    return img


def draw_vital_stamina():
    """Stick figure in motion - ball + 4 lines."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#e8a040")
    cx, cy = CANVAS // 2, CANVAS // 2
    head_r = 8
    head_cy = cy - 28
    draw.ellipse([cx - head_r, head_cy - head_r,
                  cx + head_r, head_cy + head_r], fill=body)
    body_top = head_cy + head_r
    body_bot = body_top + 26
    draw.line([(cx, body_top), (cx, body_bot)], fill=body, width=6)
    draw.line([(cx, body_bot), (cx + 28, body_bot + 18)], fill=body, width=6)
    draw.line([(cx, body_bot), (cx - 22, body_bot + 12)], fill=body, width=6)
    draw.line([(cx, body_top + 6), (cx + 26, body_top - 6)], fill=body, width=6)
    draw.line([(cx, body_top + 6), (cx - 22, body_top + 20)], fill=body, width=6)
    return img


def draw_vital_thirst():
    """Simple drinking glass rectangle."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#5fb0d8")
    cx, cy = CANVAS // 2, CANVAS // 2
    glass_w, glass_h = 44, 76
    x0 = cx - glass_w // 2
    y0 = cy - glass_h // 2
    x1 = cx + glass_w // 2
    y1 = cy + glass_h // 2
    draw.rectangle([x0, y0, x1, y1], fill=body)
    return img


def draw_vital_hunger():
    """Simple rounded rectangle bread loaf."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#c89060")
    inset = 14
    x0 = MARGIN + inset
    y0 = MARGIN + inset + 4
    x1 = CANVAS - MARGIN - inset
    y1 = CANVAS - MARGIN - inset - 4
    draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=body)
    return img


def draw_resource_water():
    """Single-color water droplet."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#5fb0d8")
    cx, cy = CANVAS // 2, CANVAS // 2
    hw = 30
    pts = [
        (cx, MARGIN + 8),
        (cx + hw, cy + 12),
        (cx + hw - 6, CANVAS - MARGIN - 8),
        (cx, CANVAS - MARGIN - 8),
        (cx - hw + 6, CANVAS - MARGIN - 8),
        (cx - hw, cy + 12),
    ]
    draw.polygon(pts, fill=body)
    return img


def draw_resource_electricity():
    """Simple 6-point lightning bolt."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#e8c44a")
    cx, cy = CANVAS // 2, CANVAS // 2
    pts = [
        (cx + 8, MARGIN + 4),
        (cx - 18, cy + 8),
        (cx, cy + 8),
        (cx - 8, CANVAS - MARGIN - 4),
        (cx + 18, cy - 8),
        (cx, cy - 8),
    ]
    draw.polygon(pts, fill=body)
    return img


def draw_resource_bandwidth():
    """4 plain ascending rectangles."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    full = _hex_to_rgb("#4dc389")
    arena_left = MARGIN + 12
    arena_right = CANVAS - MARGIN - 12
    arena_bot = CANVAS - MARGIN - 8
    arena_w = arena_right - arena_left
    gap = 6
    bar_w = (arena_w - 3 * gap) // 4
    heights = [22, 36, 52, 68]
    for i in range(4):
        bx = arena_left + i * (bar_w + gap)
        bh = heights[i]
        top = arena_bot - bh
        draw.rectangle([bx, top, bx + bar_w - 1, arena_bot], fill=full)
    return img


def draw_resource_fuel():
    """Simple T-shape pump nozzle."""
    img = blank_canvas()
    draw = ImageDraw.Draw(img)
    body = _hex_to_rgb("#b0a020")
    cx, cy = CANVAS // 2, CANVAS // 2
    bar_w = 16
    bar_h = 56
    draw.rectangle([cx + 4, cy - bar_h // 2,
                    cx + 4 + bar_w, cy + bar_h // 2], fill=body)
    arm_y = cy - 8
    arm_h = 12
    draw.rectangle([cx - 36, arm_y,
                    cx + 4, arm_y + arm_h], fill=body)
    return img


def build_all():
    _ensure_dir(SPRITES_ROOT)
    # Panels.
    pan_dir = os.path.join(SPRITES_ROOT, "panels")
    for name, body_hex, radius in PANELS:
        img = draw_panel(body_hex, radius=radius)
        _save(img, os.path.join(pan_dir, f"{name}.png"))
    # Buttons: 3 colors x 4 states = 12.
    btn_dir = os.path.join(SPRITES_ROOT, "buttons")
    for color_name, color_hex in BUTTON_COLORS:
        for state in BUTTON_STATES:
            img = draw_button(color_hex, state)
            _save(img, os.path.join(btn_dir,
                                    f"btn_{color_name}_{state}.png"))
    # Slots.
    sl_dir = os.path.join(SPRITES_ROOT, "toolbar_slots")
    for name, active, ratio in SLOTS:
        img = draw_slot(active=active, ratio=ratio)
        _save(img, os.path.join(sl_dir, f"{name}.png"))
    # Status dividers + corners.
    s_dir = os.path.join(SPRITES_ROOT, "status_windows")
    for name, kind in DIVIDERS:
        if kind in ("h", "v"):
            img = draw_divider(kind)
        else:
            img = draw_corner(kind)
        _save(img, os.path.join(s_dir, f"{name}.png"))
    # Decor (trimmed to visual mass + 1px margin).
    d_dir = os.path.join(SPRITES_ROOT, "decor")
    for name, fn in DECORS:
        img = trim_to_visual_mass(fn(), pad=1)
        _save(img, os.path.join(d_dir, f"{name}.png"))
    # Speed controls (5 chips: pause, 1x/3x/5x/9x) (trimmed to visual mass + 1px margin).
    s_dir = os.path.join(SPRITES_ROOT, "speed_controls")
    _save(trim_to_visual_mass(draw_speed_pause(), pad=1), os.path.join(s_dir, "speed_pause.png"))
    _save(trim_to_visual_mass(draw_speed_play(1), pad=1), os.path.join(s_dir, "speed_1x.png"))
    _save(trim_to_visual_mass(draw_speed_play(2), pad=1), os.path.join(s_dir, "speed_3x.png"))
    _save(trim_to_visual_mass(draw_speed_play(3), pad=1), os.path.join(s_dir, "speed_5x.png"))
    _save(trim_to_visual_mass(draw_speed_play(4), pad=1), os.path.join(s_dir, "speed_9x.png"))
    # Vitals (4 icons: wellness, stamina, thirst, hunger) (trimmed to visual mass + 1px margin).
    v_dir = os.path.join(SPRITES_ROOT, "vitals")
    _save(trim_to_visual_mass(draw_vital_wellness(), pad=1), os.path.join(v_dir, "vital_wellness.png"))
    _save(trim_to_visual_mass(draw_vital_stamina(), pad=1),  os.path.join(v_dir, "vital_stamina.png"))
    _save(trim_to_visual_mass(draw_vital_thirst(), pad=1),   os.path.join(v_dir, "vital_thirst.png"))
    _save(trim_to_visual_mass(draw_vital_hunger(), pad=1),   os.path.join(v_dir, "vital_hunger.png"))
    # Resources (4 icons: water, electricity, bandwidth, fuel) (trimmed to visual mass + 1px margin).
    r_dir = os.path.join(SPRITES_ROOT, "resources")
    _save(trim_to_visual_mass(draw_resource_water(), pad=1),
          os.path.join(r_dir, "resource_water.png"))
    _save(trim_to_visual_mass(draw_resource_electricity(), pad=1),
          os.path.join(r_dir, "resource_electricity.png"))
    _save(trim_to_visual_mass(draw_resource_bandwidth(), pad=1),
          os.path.join(r_dir, "resource_bandwidth.png"))
    _save(trim_to_visual_mass(draw_resource_fuel(), pad=1),
          os.path.join(r_dir, "resource_fuel.png"))
    total = (len(PANELS)
             + len(BUTTON_COLORS) * len(BUTTON_STATES)
             + len(SLOTS)
             + len(DIVIDERS)
             + len(DECORS)
             + 5 + 4 + 4)
    print(f"[build-sprites] wrote {total} sprites under {SPRITES_ROOT}")


if __name__ == "__main__":
    build_all()
