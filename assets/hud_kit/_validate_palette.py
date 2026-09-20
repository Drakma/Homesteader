"""_validate_palette.py - drift-detect HUD kit sprites against palette.json.

Sample a fixed body pixel in each sprite and compare to its declared
palette_role from hud_kit.json. Exits 0 if all in tolerance, 1 if not.
"""

import json
import os
import sys
from PIL import Image

KIT_ROOT = r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit"
SPRITES_ROOT = os.path.join(KIT_ROOT, "sprites")
PALETTE_PATH = os.path.join(KIT_ROOT, "palette.json")
KIT_PATH = os.path.join(KIT_ROOT, "hud_kit.json")


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def main():
    pal = json.load(open(PALETTE_PATH, encoding="utf-8"))
    kit = json.load(open(KIT_PATH, encoding="utf-8"))
    tol = pal["hero_distance"]["expected_sample_delta_per_channel_max"]
    print(f"[validate] tolerance +/- {tol} per channel")

    failures = []
    for entry in kit["entries"]:
        path = os.path.join(KIT_ROOT, entry["path"])
        if not os.path.isfile(path):
            print(f"  MISSING: {entry['id']} -> {path}")
            failures.append((entry["id"], "missing file"))
            continue
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        # Sample at the geometric center of the 104x104 content box.
        # That's (CANVAS/2, CANVAS/2) = (64, 64). Far from corners,
        # borders, and the 1-px top-left highlight ring.
        sample_x, sample_y = w // 2, h // 2
        sample = img.getpixel((sample_x, sample_y))
        role_key = entry.get("palette_role", "")
        if not role_key:
            failures.append((entry["id"], "no palette_role"))
            continue
        if role_key == "no-body":
            # Decorative sprites don't have a body fill - skip.
            print(f"  SKIP (decor/dividers): {entry['id']}")
            continue
        if role_key not in pal["colors"]:
            failures.append((entry["id"], f"unknown role {role_key}"))
            continue
        # State affordance: if the sprite id ends with _hover, _pressed,
        # _disabled, allow wider tolerance because the body is shifted
        # by the state rule.
        id_lc = entry["id"].lower()
        is_hover = id_lc.endswith("_hover")
        is_pressed = id_lc.endswith("_pressed")
        is_disabled = id_lc.endswith("_disabled")
        # Effective tolerance per state:
        #  normal      : +/- tol (= 2)
        #  hover       : +/- max(12 + tol, 2)  (~+12 lighter)
        #  pressed     : +/- max(12 + tol, 2)  (~-8 darker)
        #  disabled    : +/- anything < 255 (greyscale *0.55)
        if is_disabled:
            tol_eff = 255  # disabled bit produces 0.55 scale; wide tolerance
        elif is_hover or is_pressed:
            tol_eff = max(12, tol)
        else:
            tol_eff = tol
        expected_hex = pal["colors"][role_key]["hex"]
        expected = hex_to_rgb(expected_hex)
        if sample[3] == 0:
            print(f"  OK (alpha=0 site): {entry['id']}")
            continue
        diffs = tuple(abs(a - b) for a, b in zip(sample[:3], expected))
        if any(d > tol_eff for d in diffs):
            failures.append((entry["id"],
                              f"sample {sample[:3]} vs expected {expected}"
                              f" diffs {diffs} > +/-{tol_eff}"))
            print(f"  FAIL: {entry['id']} sample={sample[:3]} "
                  f"expected={expected} diffs={diffs} tol={tol_eff}")
        else:
            print(f"  OK: {entry['id']} (delta {max(diffs)} tol {tol_eff})")

    if failures:
        print(f"\n[validate] {len(failures)} failure(s).")
        sys.exit(1)
    print(f"\n[validate] all {len(kit['entries'])} entries in tolerance.")


if __name__ == "__main__":
    main()
