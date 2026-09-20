"""tools/bake_kit_fonts.py - build the Homesteader HUD font family.

Re-emits the 5 TTF files that drive the HUD text rendering. Sources
the glyph designs and outlines from assets/hud_kit/font/.

Run:

    python tools/bake_kit_fonts.py [--source-ttf-dir <path>] [--out-dir <path>]

By default:
  - Source glyph specs + build script: assets/hud_kit/font/
  - Output TTFs:                          same directory as the build script
  - Unity destination (must mirror):     Homesteader/Assets/Resources/HUDTree/Fonts/

This script only invokes the upstream _build_hud_ttf.build_family()
function. It exists so we have a single tool entry-point in tools/ for
bake rigs; the source of truth stays in assets/.

Kerning is not present in this build - fontTools 4.65 dropped support
for the legacy 'kern' table API, and full GPOS construction is out of
scope. The font ships monospaced. UI Toolkit's ``kerning-mode`` USS
property and ``letter-spacing`` reach the same per-pair feel if we
ever want realtime kerning later.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SOURCE = os.path.join(PROJECT_DIR, "assets", "hud_kit", "font")
DEFAULT_OUT = DEFAULT_SOURCE
DEFAULT_UNITY_FONTS = os.path.join(
    PROJECT_DIR, "Homesteader", "Assets", "Resources", "HUDTree", "Fonts"
)

# Filenames we ship (must match _build_hud_ttf.Style.filename values).
SHIP_FILES = (
    "homesteader_hud.ttf",
    "homesteader_hud_medium.ttf",
    "homesteader_hud_bold.ttf",
    "homesteader_hud_italic.ttf",
    "homesteader_hud_bold_italic.ttf",
)

# Unity destination filenames (must use underscore, no hyphens).
UNITY_TARGETS = {
    "homesteader_hud.ttf":            "HomesteaderHUD.ttf",
    "homesteader_hud_medium.ttf":     "HomesteaderHUD_Medium.ttf",
    "homesteader_hud_bold.ttf":       "HomesteaderHUD_Bold.ttf",
    "homesteader_hud_italic.ttf":     "HomesteaderHUD_Italic.ttf",
    "homesteader_hud_bold_italic.ttf": "HomesteaderHUD_BoldItalic.ttf",
}


def main(argv):
    parser = argparse.ArgumentParser(prog="bake_kit_fonts")
    parser.add_argument("--source-ttf-dir", default=DEFAULT_SOURCE,
                        help="Directory containing glyph_specs.py + "
                             "_build_hud_ttf.py. Default: " + DEFAULT_SOURCE)
    parser.add_argument("--out-dir", default=DEFAULT_OUT,
                        help="Where to write the 5 TTFs. Default: source dir.")
    parser.add_argument("--no-mirror-unity", action="store_true",
                        help="Don't mirror the TTFs to the Unity project.")
    parser.add_argument("--unity-dest", default=DEFAULT_UNITY_FONTS,
                        help="Unity Resources/HUDTree/Fonts/ destination. "
                             "Default: " + DEFAULT_UNITY_FONTS)
    args = parser.parse_args(argv)

    sys.path.insert(0, args.source_ttf_dir)
    import _build_hud_ttf as bh  # type: ignore

    bh.build_family(out_dir=args.out_dir)

    if args.no_mirror_unity:
        return 0

    # Mirror to Unity.
    if not os.path.isdir(args.unity_dest):
        os.makedirs(args.unity_dest, exist_ok=True)
    for src_name in SHIP_FILES:
        src_p = os.path.join(args.out_dir, src_name)
        dst_name = UNITY_TARGETS.get(src_name, src_name)
        dst_p = os.path.join(args.unity_dest, dst_name)
        if not os.path.isfile(src_p):
            print("WARN: missing", src_p)
            continue
        shutil.copy2(src_p, dst_p)
        print("mirrored", src_p, "->", dst_p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
