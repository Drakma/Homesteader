"""splice_icons.py - rewrite the icon-drawing functions in
assets/hud_kit/_build_sprites.py with simpler 2D versions.

Used as one-shot helper while iterating on icon style. Reads the
surrounding file (panels/buttons/dividers/decor stays untouched) and
re-splices the icon block.

Usage:
    python tools/splice_icons.py
"""
import os
import sys


TARGET = r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\_build_sprites.py"


NEW_ICONS = '''def draw_vital_wellness():
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


'''


def main():
    with open(TARGET, "r", encoding="utf-8") as f:
        src = f.read()
    start_marker = "def _draw_vital_path"
    end_marker = "def build_all"
    start = src.find(start_marker)
    end = src.find(end_marker)
    if start == -1 or end == -1 or start >= end:
        raise SystemExit(f"bad bounds start={start} end={end}")
    new_src = src[:start] + NEW_ICONS + src[end:]
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(new_src)
    print(f"spliced: {end - start} -> {len(NEW_ICONS)} chars")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    main()
