#!/usr/bin/env python3
"""Generate the standardized icon for a finalized asset request.

Icon-only path: free FLUX.1 [schnell] concept render -> standardized 128x128
RGBA per docs/ITEM_ICON_STYLE_GUIDE.md. $0 cost, no Meshy call.

Usage:
  python tools/generate_request_icon.py <category> <item_id> "<description>"
"""
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "assets"))

import free_generator  # noqa: E402

STYLE_SUFFIX = (
    " Style: clean video game asset icon, 3D low-poly faceted render with visible "
    "geometric facets, ambient occlusion, smooth matte and satin materials, faceted "
    "specular highlights. View: EXTERNAL VIEW of the entire object/building from the outside, "
    "showing outer exterior facade, outer walls, and roof, with NO internal structures, no cutaway, "
    "no indoor camera perspective, and no internal rooms visible (unless the external view can "
    "naturally see inside through open windows or open doors). Isometric 3/4 front view, "
    "angled slightly from the left, floating centered in empty space. Lighting: soft studio "
    "key light from top-left, clean edge lighting, no cast shadows on floor. Background: solid "
    "uniform dark slate background (hex #2b3442), completely plain and flat, no borders, no frame, no text."
)


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)

    category, item_id, description = sys.argv[1], sys.argv[2], sys.argv[3]
    item_dir = os.path.join(REPO_ROOT, "assets", category, item_id)
    raw_path = os.path.join(item_dir, f"{item_id}_raw.png")
    icon_path = os.path.join(item_dir, f"{item_id}.png")

    prompt = description.rstrip(".") + "." + STYLE_SUFFIX

    print(f"item      : {category}/{item_id}")
    print(f"raw       : {raw_path}")
    print(f"icon      : {icon_path}")
    print(f"prompt    : {prompt}\n")

    os.makedirs(item_dir, exist_ok=True)

    ok = free_generator.generate_icon_flux(prompt, raw_path, width=1024, height=1024, steps=4)
    if not ok:
        raise SystemExit("icon generation FAILED (both FLUX and Pollinations)")

    print("\n[standardize] applying 128x128 RGBA icon standards...")
    free_generator.standardize_icon(raw_path, icon_path)

    if not os.path.exists(icon_path):
        raise SystemExit(f"standardize did not produce {icon_path}")

    from PIL import Image
    im = Image.open(icon_path)
    print(f"\nresult    : {im.size} {im.mode}")
    if im.mode == "RGBA":
        w, h = im.size
        perimeter = [im.getpixel((x, 0))[3] for x in range(w)]
        perimeter += [im.getpixel((x, h - 1))[3] for x in range(w)]
        perimeter += [im.getpixel((0, y))[3] for y in range(h)]
        perimeter += [im.getpixel((w - 1, y))[3] for y in range(h)]
        print(f"perimeter alpha max: {max(perimeter)}  (must be 0)")
        bbox = im.getchannel("A").getbbox()
        if bbox:
            print(f"content bbox: {bbox}  size {bbox[2]-bbox[0]}x{bbox[3]-bbox[1]} (max 104)")


if __name__ == "__main__":
    main()
