"""_sample_hud_palette.py - sample colors at 5 sites on each chrome PNG.

Returns: body / border / highlight / transparent-corner, in hex + alpha.
"""
from PIL import Image
import os

ITEMS = [
    "compact_window_dialog",
    "compact_window_crafting_kit",
    "compact_hotbar_tray_kit",
    "compact_hotbar_10slots",
    "compact_hotbar_slot",
    "hud_compact_btn_slate_normal",
    "hud_compact_btn_slate_hover",
    "hud_compact_btn_amber_normal",
    "hud_compact_btn_green_normal",
    "hud_compact_player_status_kit",
    "hud_compact_resources_kit",
    "hud_compact_selector_active_kit",
    "hud_compact_time_season_kit",
]
ASSETS = r"C:\Users\casey\Desktop\Homesteader\assets\hud"

print(f"{'item':<42} {'body':<9} {'border':<9} {'highlight':<9} {'corner_a':<10}")
for it in ITEMS:
    p = os.path.join(ASSETS, it, f"{it}.png")
    if not os.path.isfile(p):
        print(f"  {it:<40} MISSING")
        continue
    img = Image.open(p).convert("RGBA")
    w, h = img.size
    # body = a bit off-center to avoid centered-content leaves
    body = img.getpixel((w // 2 + 8, h // 2 + 8))
    # border: 4 px in from the top edge at the horizontal middle
    brd = img.getpixel((w // 2, 4))
    # highlight: a bit inside the top-left corner
    hl = img.getpixel((10, 10))
    # transparent zone: top-right corner
    trans = img.getpixel((w - 1, 1))
    body_hex = f"#{body[0]:02x}{body[1]:02x}{body[2]:02x}"
    brd_hex = f"#{brd[0]:02x}{brd[1]:02x}{brd[2]:02x}"
    hl_hex = f"#{hl[0]:02x}{hl[1]:02x}{hl[2]:02x}"
    print(f"  {it:<42} {body_hex:<9} {brd_hex:<9} {hl_hex:<9} a={trans[3]:>3}")
