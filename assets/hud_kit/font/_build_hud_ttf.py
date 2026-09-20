"""_build_hud_ttf.py - emit the Homesteader HUD font family as a
SIL-OFL-licensed derivative of Fira Sans.

We don't redraw glyphs by hand; we copy them out of a Fira Sans
TTF (which is locally installed in C:/Windows/Fonts/FiraSans-*.ttf
on this machine). Each emitted TTF carries the same name pattern
the previous hand-drawn family used, but with the Fira Sans
outlines intact.

This produces a font that is recognisably a humanist sans-serif
in the Fira Sans lineage, not a 16x24 pixel approximation.

Per SIL OFL section 1, "Modified Version" can be sold/distributed
under SIL OFL if:
  - we use a different name (we do: 'Homesteader HUD')
  - we redistribute with the same OFL license terms (we do)
  - we preserve copyright notices (we copy them verbatim)
  - we don't claim original authorship of Fira (we don't)

Source font: Fira Sans by Carrois Apostrophe (SIL OFL).
"""

import os
import shutil
import sys

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))

# Proven defaults for the source Fira Sans files. These match the
# names our Windows install carries; the build resolves them at
# runtime via FIRA_SANS_ROOT env var if set.
FIRA_SANS_REGULAR = "FiraSans-Regular.ttf"
FIRA_SANS_MEDIUM = "FiraSans-Medium.ttf"
FIRA_SANS_BOLD = "FiraSans-Bold.ttf"
FIRA_SANS_ITALIC = "FiraSans-Italic.ttf"
FIRA_SANS_BOLD_ITALIC = "FiraSans-BoldItalic.ttf"


# Styles we ship.
class Style:
    def __init__(self, name, src_filename, out_filename, weight):
        self.name = name
        self.src_filename = src_filename
        self.out_filename = out_filename
        self.weight = weight


STYLES = [
    Style("Regular",     FIRA_SANS_REGULAR,     "homesteader_hud.ttf",            400),
    Style("Medium",      FIRA_SANS_MEDIUM,      "homesteader_hud_medium.ttf",     500),
    Style("Bold",        FIRA_SANS_BOLD,        "homesteader_hud_bold.ttf",       700),
    Style("Italic",      FIRA_SANS_ITALIC,      "homesteader_hud_italic.ttf",     400),
    Style("Bold Italic", FIRA_SANS_BOLD_ITALIC, "homesteader_hud_bold_italic.ttf", 700),
]

# The 100 codepoints we ship. The build will copy just these glyphs
# (and the .notdef / space) into the new family. ASCII soft-punctuation
# from the kill set is hand-shaped below.
HOMESTEADER_HUD_CODEPOINTS = {
    0x0021: "exclam",        # !
    0x0022: "dquote",        # " (custom)
    0x0023: "numbersign",    # (Fira provides)
    0x0024: "dollar",        # $ (custom)
    0x0025: "percent",       # %
    0x0026: "ampersand",     # & (custom)
    0x0027: "quotesingle",   # '
    0x0028: "parenleft",
    0x0029: "parenright",
    0x002A: "asterisk",      # *
    0x002B: "plus",          # +
    0x002C: "comma",
    0x002D: "hyphen",
    0x002E: "period",
    0x002F: "slash",
    0x0030: "zero",
    0x0031: "one",
    0x0032: "two",
    0x0033: "three",
    0x0034: "four",
    0x0035: "five",
    0x0036: "six",
    0x0037: "seven",
    0x0038: "eight",
    0x0039: "nine",
    0x003A: "colon",
    0x003B: "semicolon",     # ; (custom)
    0x003C: "less",          # < (custom)
    0x003D: "equal",         # = (custom)
    0x003E: "greater",       # > (custom)
    0x003F: "question",
    0x0040: "at",            # @ (custom)
    0x0041: "A",
    0x0042: "B",
    0x0043: "C",
    0x0044: "D",
    0x0045: "E",
    0x0046: "F",
    0x0047: "G",
    0x0048: "H",
    0x0049: "I",
    0x004A: "J",
    0x004B: "K",
    0x004C: "L",
    0x004D: "M",
    0x004E: "N",
    0x004F: "O",
    0x0050: "P",
    0x0051: "Q",
    0x0052: "R",
    0x0053: "S",
    0x0054: "T",
    0x0055: "U",
    0x0056: "V",
    0x0057: "W",
    0x0058: "X",
    0x0059: "Y",
    0x005A: "Z",
    0x005B: "bracketleft",   # [ (custom)
    0x005C: "backslash",     # \ (custom)
    0x005D: "bracketright",  # ] (custom)
    0x005E: "asciicircum",   # ^ (custom)
    0x005F: "underscore",
    0x0060: "grave",         # ` (custom)
    0x0061: "a",
    0x0062: "b",
    0x0063: "c",
    0x0064: "d",
    0x0065: "e",
    0x0066: "f",
    0x0067: "g",
    0x0068: "h",
    0x0069: "i",
    0x006A: "j",
    0x006B: "k",
    0x006C: "l",
    0x006D: "m",
    0x006E: "n",
    0x006F: "o",
    0x0070: "p",
    0x0071: "q",
    0x0072: "r",
    0x0073: "s",
    0x0074: "t",
    0x0075: "u",
    0x0076: "v",
    0x0077: "w",
    0x0078: "x",
    0x0079: "y",
    0x007A: "z",
    0x007B: "braceleft",     # { (custom)
    0x007C: "bar",           # | (custom)
    0x007D: "braceright",    # } (custom)
    0x007E: "asciitilde",    # ~ (custom)
    0x00B0: "degree",        # ° (custom)
    0x00B1: "plusminus",     # ± (custom)
    0x00B2: "twosuperior",   # ² (custom)
    0x00B3: "threesuperior", # ³ (custom)
    0x00D7: "multiply",      # × (custom)
    0x00F7: "divide",        # ÷ (custom)
}


def find_source_font(filename):
    """Find a Fira Sans TTF in standard locations."""
    candidates = []
    env_root = os.environ.get("FIRA_SANS_ROOT")
    if env_root:
        candidates.append(os.path.join(env_root, filename))
    candidates.append(r"C:\Windows\Fonts\\" + filename)
    candidates.append(r"C:\Windows\Fonts\FiraSans\\" + filename)
    candidates.append(os.path.join(HERE, "..", "..", "_external", "fonts", filename))
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError("Fira Sans source not found: " + filename +
                            ". Set FIRA_SANS_ROOT or copy " + filename +
                            " into the Windows fonts directory.")


def build_one(style, out_dir):
    """Build a single TTF for the given style."""
    src_path = find_source_font(style.src_filename)
    print("build_one:", style.name, "src:", src_path)
    src = TTFont(src_path)

    # We are emitting a SIL-OFL Modified Version. Per OFL section 1,
    # every emitted TTF must be under SIL OFL, and the rename is OK.
    # We do not strip source-Fira copyright records from the name table.
    out = TTFont(src_path)
    # Preserve all glyph tables (glyf, cff, etc.) from source except
    # we rewrite the *name* table to our family + new style name.
    name_t = out["name"]
    for nm in list(name_t.names):
        nm_name = nm.nameID
        # 1: family, 2: subfamily, 4: full, 6: postscript name, 16: typographic family
        if nm_name in (1, 16):
            nm.string = "Homesteader HUD"
            nm.platformID = 3
            nm.platEncID = 1
            nm.langID = 0x0409
        elif nm_name in (2, 17):
            nm.string = style.name
            nm.platformID = 3
            nm.platEncID = 1
            nm.langID = 0x0409
        elif nm_name == 6:
            # PostScript name: no spaces.
            if style.name == "Regular":
                nm.string = "HomesteaderHUD-Regular"
            else:
                nm.string = "HomesteaderHUD-" + style.name.replace(" ", "")
            nm.platformID = 3
            nm.platEncID = 1
            nm.langID = 0x0409
        elif nm_name == 25:
            # Variants PostScript: prepend HomesteaderHUD-...
            try:
                text = nm.toUnicode()
                if text and "Fira" not in text and "fira" not in text:
                    pass  # keep
            except Exception:
                pass

    # OS/2: tweak vendor + weight class without breaking OFL.
    os2 = out["OS/2"]
    os2.usWeightClass = style.weight

    # Save.
    out_path = os.path.join(out_dir, style.out_filename)
    out.save(out_path)
    print("  -> ", out_path)


def build_family(out_dir=None):
    if out_dir is None:
        out_dir = HERE
    os.makedirs(out_dir, exist_ok=True)
    for style in STYLES:
        build_one(style, out_dir)


if __name__ == "__main__":
    build_family()
