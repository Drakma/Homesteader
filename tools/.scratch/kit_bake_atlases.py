"""Bake Unity-ready atlases sourced from assets/hud_kit/.

Mirrors the existing bake_atlases.py pattern (200x56 button cells, 28x28
checkbox/radio, etc.) but pulls the underlying art from the hand-built
kit sprites instead of redrawing rectangles in PIL.

Output goes to Homesteader/Assets/Resources/HUDTree/Atlases/Kit/ so the
HUDTree Resources fallback can pick them up via the USS resource(...)
lookups written by the matching HUD uss block.

Atlas layout chosen for Unity UI Toolkit:
- button_atlas_kit.png : 200 x 896  (16 rows: 4 colors * 4 states)
  row order matches HudUI.uss button matrix:
    rows 0..3  : red    : unclicked, hover, clicked, disabled
    rows 4..7  : green
    rows 8..11 : amber
    rows 12..15 : slate
- vital_atlas_kit.png : 128 x 512  (4 rows x 128: thirst, hunger, stamina, wellness)
- resource_atlas_kit.png : 128 x 512 (4 rows: water, electricity, bandwidth, fuel)
- slot_atlas_kit.png : 128 x 384 (3 rows: slot_1x1, slot_1x1_active, slot_1x2)
- decor_atlas_kit.png : 128 x 512 (4 rows: close_x, glow_accent, separator_dot,
                                         double_divider)

Standalone (NOT atlas'd, kept as direct image sprites for UI use):
- speed_controls/*.png  (5 PNGs at 64x64 - meant for chip buttons)
- panels/*.png         (5 PNGs at 128x128 - meant for window backgrounds)
"""
import os
from collections import Counter
from PIL import Image

KIT = r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\sprites"
OUT = os.path.join(
    r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\Atlases",
    "Kit",
)
os.makedirs(OUT, exist_ok=True)


def paste_square(canvas, sprite_path, x0, y0, target_w, target_h):
    # Open sprite, crop to visual mass with 1px margin, then fit into cell.
    im = Image.open(sprite_path).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    iw, ih = im.size
    # Target content box keeps 1px margin on cell boundary
    avail_w = target_w - 2
    avail_h = target_h - 2
    scale = min(avail_w / iw, avail_h / ih) if iw and ih else 1.0
    nw = max(1, int(round(iw * scale)))
    nh = max(1, int(round(ih * scale)))
    im_resized = im.resize((nw, nh), Image.LANCZOS)
    ox = x0 + (target_w - nw) // 2
    oy = y0 + (target_h - nh) // 2
    canvas.alpha_composite(im_resized, (ox, oy))


def bake_buttons(cell_w=200, cell_h=56):
    """4 colors x 4 states = 16 rows. Each row 56 px tall."""
    color_keys = {
        "amber": "amber",
        "green": "green",
        "slate": "slate",
        # The kit has no explicit red button set - to keep the USS row
        # matrix 1:1 with the existing grid, fall back to slate for red.
        "red": None,
    }
    state_order = ["normal", "hover", "pressed", "disabled"]
    widths = cell_w
    rows = []
    for color_name, kit_color in color_keys.items():
        for state in state_order:
            rows.append((color_name, state, kit_color))
    canvas = Image.new("RGBA", (widths, cell_h * len(rows)), (0, 0, 0, 0))
    for i, (color, state, kit_color) in enumerate(rows):
        if kit_color is None:
            continue  # leave red row empty -> canvas remains transparent
        sprite_p = os.path.join(
            KIT, "buttons", f"btn_{kit_color}_{state}.png"
        )
        if not os.path.isfile(sprite_p):
            print(f"WARN: missing {sprite_p}")
            continue
        y0 = i * cell_h
        paste_square(canvas, sprite_p, 0, y0, cell_w, cell_h)
    canvas.save(os.path.join(OUT, "button_atlas_kit.png"))
    print(f"wrote button_atlas_kit.png ({canvas.size})")


def bake_vital(cell=128):
    vital_map = [
        ("vital_thirst.png", "Thirst"),
        ("vital_hunger.png", "Hunger"),
        ("vital_stamina.png", "Stamina"),
        ("vital_wellness.png", "Wellness"),
    ]
    canvas = Image.new("RGBA", (cell, cell * len(vital_map)), (0, 0, 0, 0))
    for i, (fn, _) in enumerate(vital_map):
        paste_square(canvas, os.path.join(KIT, "vitals", fn), 0, i * cell, cell, cell)
    out_p = os.path.join(OUT, "vital_atlas_kit.png")
    canvas.save(out_p)
    print(f"wrote {out_p} ({canvas.size})")


def bake_resource(cell=128):
    order = [
        "resource_water.png",
        "resource_electricity.png",
        "resource_bandwidth.png",
        "resource_fuel.png",
        "resource_money.png",
    ]
    canvas = Image.new("RGBA", (cell, cell * len(order)), (0, 0, 0, 0))
    for i, fn in enumerate(order):
        paste_square(canvas, os.path.join(KIT, "resources", fn), 0, i * cell, cell, cell)
    out_p = os.path.join(OUT, "resource_atlas_kit.png")
    canvas.save(out_p)
    print(f"wrote {out_p} ({canvas.size})")


def bake_slot(cell=128):
    order = [
        "slot_1x1.png",
        "slot_1x1_active.png",
        "slot_1x2.png",
    ]
    canvas = Image.new("RGBA", (cell, cell * len(order)), (0, 0, 0, 0))
    for i, fn in enumerate(order):
        paste_square(canvas, os.path.join(KIT, "toolbar_slots", fn), 0, i * cell, cell, cell)
    out_p = os.path.join(OUT, "slot_atlas_kit.png")
    canvas.save(out_p)
    print(f"wrote {out_p} ({canvas.size})")


def bake_decor(cell=128):
    order = [
        "close_x.png",
        "glow_accent.png",
        "separator_dot.png",
        "double_divider.png",
    ]
    canvas = Image.new("RGBA", (cell, cell * len(order)), (0, 0, 0, 0))
    for i, fn in enumerate(order):
        paste_square(canvas, os.path.join(KIT, "decor", fn), 0, i * cell, cell, cell)
    out_p = os.path.join(OUT, "decor_atlas_kit.png")
    canvas.save(out_p)
    print(f"wrote {out_p} ({canvas.size})")


def copy_speed_controls():
    sp = os.path.join(KIT, "speed_controls")
    if not os.path.isdir(sp):
        return
    dest = os.path.join(OUT, "speed_controls")
    os.makedirs(dest, exist_ok=True)
    for fn in sorted(os.listdir(sp)):
        if not fn.lower().endswith(".png"):
            continue
        Image.open(os.path.join(sp, fn)).convert("RGBA").save(os.path.join(dest, fn))
    print(f"copied speed_controls/ -> Kit/speed_controls/ ({len(os.listdir(dest))} files)")


def copy_panels():
    sp = os.path.join(KIT, "panels")
    if not os.path.isdir(sp):
        return
    dest = os.path.join(OUT, "panels")
    os.makedirs(dest, exist_ok=True)
    for fn in sorted(os.listdir(sp)):
        if not fn.lower().endswith(".png"):
            continue
        Image.open(os.path.join(sp, fn)).convert("RGBA").save(os.path.join(dest, fn))
    print(f"copied panels/ -> Kit/panels/ ({len(os.listdir(dest))} files)")


def copy_status_windows():
    sp = os.path.join(KIT, "status_windows")
    if not os.path.isdir(sp):
        return
    dest = os.path.join(OUT, "status_windows")
    os.makedirs(dest, exist_ok=True)
    for fn in sorted(os.listdir(sp)):
        if not fn.lower().endswith(".png"):
            continue
        Image.open(os.path.join(sp, fn)).convert("RGBA").save(os.path.join(dest, fn))
    print(f"copied status_windows/ -> Kit/status_windows/ ({len(os.listdir(dest))} files)")


def main():
    bake_buttons()
    bake_vital()
    bake_resource()
    bake_slot()
    bake_decor()
    copy_speed_controls()
    copy_panels()
    copy_status_windows()
    print("done")


if __name__ == "__main__":
    main()
