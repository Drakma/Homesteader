"""compose_preview.py - render 3 sample compositions from the kit.

Composes three preview images at 768x512 in the assets/hud_kit/preview/
folder:

  - preview_window.png   - panel with three buttons beneath
  - preview_toolbar.png  - 5-slot hotbar with the 3rd slot active
  - preview_status.png   - status window with dividers and corner accents

This is the canonical-looks-correct visual smoke test. If these
composites aren't readable as a HUD, the kit is wrong.
"""

import os
from PIL import Image

KIT_ROOT = r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit"
SPRITES_ROOT = os.path.join(KIT_ROOT, "sprites")
PREVIEW_DIR = os.path.join(KIT_ROOT, "preview")
os.makedirs(PREVIEW_DIR, exist_ok=True)


def _sprite(name: str, group: str) -> Image.Image:
    return Image.open(os.path.join(SPRITES_ROOT, group, f"{name}.png")
                      ).convert("RGBA")


def _paste(canvas: Image.Image, sprite: Image.Image, x: int, y: int):
    canvas.alpha_composite(sprite, (x, y))


def render_window_compose(out_path: str):
    canvas = Image.new("RGBA", (768, 512), (15, 18, 26, 0))
    # Inner panel - 1x1 of canvas; sit at top.
    _paste(canvas, _sprite("panel_large_dialog", "panels"), 64, 32)
    # Three buttons in a row at bottom.
    _paste(canvas, _sprite("btn_slate_normal", "buttons"), 64, 256)
    _paste(canvas, _sprite("btn_amber_normal", "buttons"), 256, 256)
    _paste(canvas, _sprite("btn_green_normal", "buttons"), 448, 256)
    # Close X in panel top-right.
    _paste(canvas, _sprite("close_x", "decor"), 580, 64)
    canvas.save(out_path, "PNG")


def render_toolbar_compose(out_path: str):
    canvas = Image.new("RGBA", (768, 256), (15, 18, 26, 0))
    # 5 slots in a row.
    x = 64
    for i in range(5):
        if i == 2:
            s = _sprite("slot_1x1_active", "toolbar_slots")
        else:
            s = _sprite("slot_1x1", "toolbar_slots")
        _paste(canvas, s, x, 64)
        x += 128
    canvas.save(out_path, "PNG")


def render_status_compose(out_path: str):
    canvas = Image.new("RGBA", (768, 512), (15, 18, 26, 0))
    # Place a row of 4 corners at the corners of an imaginary 384x256 rectangle.
    # corners offset by 64 from edges.
    _paste(canvas, _sprite("corner_tl", "status_windows"), 64, 64)
    _paste(canvas, _sprite("corner_tr", "status_windows"), 576, 64)
    _paste(canvas, _sprite("corner_bl", "status_windows"), 64, 320)
    _paste(canvas, _sprite("corner_br", "status_windows"), 576, 320)
    # Horizontal divider in middle.
    _paste(canvas, _sprite("divider_h", "status_windows"), 192, 192)
    canvas.save(out_path, "PNG")


def main():
    render_window_compose(os.path.join(PREVIEW_DIR, "preview_window.png"))
    render_toolbar_compose(os.path.join(PREVIEW_DIR, "preview_toolbar.png"))
    render_status_compose(os.path.join(PREVIEW_DIR, "preview_status.png"))
    print(f"[compose] wrote 3 previews in {PREVIEW_DIR}")


if __name__ == "__main__":
    main()
