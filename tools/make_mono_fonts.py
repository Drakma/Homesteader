"""Generates monospaced variants of the HomesteaderHUD font family.

Sets every glyph in CHARSET's advance width to the widest glyph among them,
centering each glyph's ink within its new cell via the left side bearing.
Outputs <Name>_Mono.ttf next to the source fonts.

CHARSET is scoped to what the HUD's header date/time readout actually
renders (season/month names, digits, colon, space) rather than full
printable ASCII, so the cell is as tight as the real content allows - a
wider glyph like '@' (never used here) would otherwise force needless
padding around every character.

Unity's legacy dynamic-font text renderer (-unity-font in USS) does not
honor the `letter-spacing` USS property, so spacing has to be baked into
the font's own advance-width metrics like this instead.

Run after editing the source .ttf files, then re-import in Unity:
    python tools/make_mono_fonts.py
"""
import os
from fontTools.ttLib import TTFont

FONTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Homesteader", "Assets", "Resources", "HUDTree", "Fonts",
)

SOURCES = [
    "HomesteaderHUD_Bold.ttf",
]

CHARSET = set(
    "SpringSummerAutumnWinterJanuaryFebruaryMarchAprilMayJuneJuly"
    "AugustSeptemberOctoberNovemberDecember0123456789: "
)


def make_mono(src_path):
    f = TTFont(src_path)
    hmtx = f["hmtx"]
    cmap = f.getBestCmap()

    target = 0
    for ch in CHARSET:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        aw, _ = hmtx[gname]
        target = max(target, aw)

    changed = 0
    for ch in CHARSET:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        aw, lsb = hmtx[gname]
        if aw == 0:
            continue
        hmtx[gname] = (target, lsb + (target - aw) // 2)
        changed += 1

    out_path = src_path.replace(".ttf", "_Mono.ttf")
    f.save(out_path)
    print(f"{os.path.basename(src_path)}: {changed} glyphs -> advance {target}/1000 em, saved {os.path.basename(out_path)}")


if __name__ == "__main__":
    for name in SOURCES:
        make_mono(os.path.join(FONTS_DIR, name))
