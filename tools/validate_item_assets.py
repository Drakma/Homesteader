import os
import sys
from PIL import Image

def validate_assets():
    print("=================================================================")
    print("VALIDATING HOMESTEADER ITEM ICONS & 3D ASSETS")
    print("=================================================================")

    from items_water import WATER_BUILDERS
    from items_sewage import SEWAGE_BUILDERS
    from items_electricity import ELECTRICITY_BUILDERS
    from items_internet import INTERNET_BUILDERS
    from items_building import BUILDING_BUILDERS
    from items_tools import TOOLS_BUILDERS
    from items_farming_ranching import FARMING_RANCHING_BUILDERS
    from items_fishing_logging import FISHING_LOGGING_BUILDERS

    all_builders = (
        WATER_BUILDERS +
        SEWAGE_BUILDERS +
        ELECTRICITY_BUILDERS +
        INTERNET_BUILDERS +
        BUILDING_BUILDERS +
        TOOLS_BUILDERS +
        FARMING_RANCHING_BUILDERS +
        FISHING_LOGGING_BUILDERS
    )

    script_dir = os.path.dirname(os.path.abspath(__file__))
    hud_dir = os.path.dirname(script_dir)
    hud_assets_dir = os.path.join(hud_dir, "assets")
    ue5_icons_dir = os.path.abspath(os.path.join(hud_dir, "..", "Homesteader", "Content", "Homesteader", "UI", "Icons"))
    ue5_meshes_dir = os.path.abspath(os.path.join(hud_dir, "..", "Homesteader", "Content", "Homesteader", "Assets", "Meshes"))

    print(f"Total items in catalog to validate: {len(all_builders)}")

    errors = []
    success_count = 0

    for item_id, _, category, subcategory in all_builders:
        # Paths
        hud_png = os.path.join(hud_assets_dir, category, subcategory, f"{item_id}.png")
        hud_obj = os.path.join(hud_assets_dir, category, subcategory, f"{item_id}.obj")
        ue5_png = os.path.join(ue5_icons_dir, category, subcategory, f"{item_id}.png")
        ue5_obj = os.path.join(ue5_meshes_dir, category, subcategory, f"{item_id}.obj")

        # 1. Existence checks
        for p, label in [(hud_png, "HUD PNG"), (hud_obj, "HUD OBJ"), (ue5_png, "UE5 PNG"), (ue5_obj, "UE5 OBJ")]:
            if not os.path.isfile(p):
                errors.append(f"[{item_id}] Missing {label} at {p}")

        if not os.path.isfile(hud_png):
            continue

        # 2. Icon image validation
        try:
            im = Image.open(hud_png)
            if im.size != (128, 128):
                errors.append(f"[{item_id}] Invalid size {im.size} (expected 128x128)")
            if im.mode != "RGBA":
                errors.append(f"[{item_id}] Invalid mode {im.mode} (expected RGBA)")

            # Check perimeter alpha
            px = im.load()
            w, h = im.size
            bad_perimeter = 0
            for x in range(w):
                if px[x, 0][3] != 0 or px[x, h - 1][3] != 0:
                    bad_perimeter += 1
            for y in range(h):
                if px[0, y][3] != 0 or px[w - 1, y][3] != 0:
                    bad_perimeter += 1

            if bad_perimeter > 0:
                errors.append(f"[{item_id}] Non-zero alpha on perimeter ({bad_perimeter} pixels)")

            # Check bbox safe margin
            bbox = im.getbbox()
            if bbox is None:
                errors.append(f"[{item_id}] Icon is completely empty transparent")
            else:
                bx0, by0, bx1, by1 = bbox
                margin_left = bx0
                margin_top = by0
                margin_right = w - bx1
                margin_bottom = h - by1
                min_margin = min(margin_left, margin_top, margin_right, margin_bottom)
                bw = bx1 - bx0
                bh = by1 - by0

                if min_margin < 12:
                    errors.append(f"[{item_id}] Insufficient margin: min margin={min_margin}px (req >= 12px), bbox=({bx0},{by0},{bx1},{by1})")
                if bw > 104 or bh > 104:
                    errors.append(f"[{item_id}] Bounding box ({bw}x{bh}) exceeds MAX_ITEM_DIM 104px")

            # 3. OBJ file non-empty
            if os.path.isfile(hud_obj):
                fsize = os.path.getsize(hud_obj)
                if fsize < 100:
                    errors.append(f"[{item_id}] OBJ file abnormally small ({fsize} bytes)")

            if not any(item_id in e for e in errors):
                success_count += 1

        except Exception as e:
            errors.append(f"[{item_id}] Exception during check: {e}")

    print(f"\n=================================================================")
    print(f"VALIDATION SUMMARY:")
    print(f"Total Validated: {len(all_builders)}")
    print(f"Passed All Rules: {success_count} / {len(all_builders)}")
    print(f"Total Errors Found: {len(errors)}")
    print("=================================================================")

    if errors:
        print("\nERRORS:")
        for err in errors[:30]:
            print(f" - {err}")
        if len(errors) > 30:
            print(f" ... and {len(errors) - 30} more errors")
        sys.exit(1)
    else:
        print("\nALL 149 ITEM ICONS & 3D ASSETS STRICTLY COMPLIANT WITH HOMESTEADER STANDARDS!")
        sys.exit(0)

if __name__ == "__main__":
    validate_assets()

