"""glyph_specs.py - glyph design specs for the Homesteader HUD font.

Stylistically inspired by the structure of Segoe UI and Fira (clean
humanist sans-serif, even stem-width, distinct terminals) but every
glyph is redrawn from scratch on a 16 x 24 design grid.

DESIGN GRID
-----------
Width       16 px
Ascender    24 px (top of cap height)
x-height    y=10..20 (10 px tall lowercase)
Cap height  y=4..20  (16 px tall)
Numerals    y=8..20  (12 px tall)
Baseline    y=20

Each glyph author is a list of polylines. Each polyline is a closed
contour on the design grid so the TTF builder can stroke each segment
as a filled quad in font units.

Coordinate system
-----------------
(x, y) is (pixel-from-left, pixel-from-top). The y-axis is flipped
(font y = ASCENDER - pixel_y) at draw time.
"""

from dataclasses import dataclass, field
import enum


GLYPH_WIDTH = 16
ASCENDER = 24
DESCENDER = 4


class _KC(enum.Enum):
    # Kerning classes. Each glyph declares one of these; the GPOS
    # builder generates pair kerning off (KC_a, KC_b) -> shift.
    Cap = "cap"        # A-Z, brackets, parentheses, digits
    Low = "low"        # a-z, lowercase-ish glyphs
    Digit = "digit"    # 0-9
    Punct = "punct"    # . , : ; ! ? % - _ + / \\ ^ ~ * & =
    Space = "space"    # space only


@dataclass
class _GlyphSpec:
    name: str
    char: str
    width_in_units: int
    strokes: list = field(default_factory=list)
    kclass: _KC = _KC.Punct


_UPEM = 1024
_ADVANCE_UNITS = GLYPH_WIDTH * (_UPEM // GLYPH_WIDTH)


def _g(c, points_list, kclass=None):
    name = {
        " ": "space",
        "-": "hyphen",
        "+": "plus",
        "/": "slash",
        "\\": "backslash",
        ":": "colon",
        ".": "period",
        ",": "comma",
        "'": "apostrophe",
        "\"": "dquote",
        "(": "parenleft",
        ")": "parenright",
        "?": "question",
        "!": "exclam",
        "%": "percent",
        "&": "ampersand",
        "*": "asterisk",
        "_": "underscore",
        "[": "bracketleft",
        "]": "bracketright",
        "<": "less",
        ">": "greater",
        "~": "asciitilde",
        ";": "semicolon",
        "^": "circumflex",
        "=": "equal",
        "#": "hash",
        "$": "dollar",
        "@": "at",
        "`": "grave",
        "|": "bar",
        "{": "braceleft",
        "}": "braceright",
        "°": "degree",
        "±": "plusminus",
        "²": "twosuperior",
        "³": "threesuperior",
        "×": "multiply",
        "÷": "divide",
    }.get(c, None)
    if name is None:
        if c.isdigit():
            name = ["zero", "one", "two", "three", "four",
                    "five", "six", "seven", "eight", "nine"][int(c)]
        elif c.isalpha():
            if c.isupper():
                name = c.lower() + "_cap"
            else:
                name = c.lower()
        else:
            name = f"u{ord(c):04x}"

    # Default kerning class inference.
    if kclass is None:
        if c == " ":
            kclass = _KC.Space
        elif c.isdigit():
            kclass = _KC.Digit
        elif c.isupper():
            kclass = _KC.Cap
        elif c.isalpha():
            kclass = _KC.Low
        else:
            kclass = _KC.Punct

    return _GlyphSpec(name=name, char=c, width_in_units=_ADVANCE_UNITS,
                       strokes=points_list, kclass=kclass)


# Force the auto-kclass on the existing call sites that pass punct chars.
_GLYPH_OVERRIDES = {
    "-": _KC.Punct,
    "+": _KC.Punct,
    "/": _KC.Punct,
    "\\": _KC.Punct,
    ":": _KC.Punct,
    ".": _KC.Punct,
}


_NUM_X1, _NUM_X2 = 2, 14
_NUM_Y1, _NUM_Y2 = 8, 20
_CAP_X1, _CAP_X2 = 1, 15
_CAP_Y1, _CAP_Y2 = 4, 20
_LOW_X1, _LOW_X2 = 3, 14
_LOW_Y1, _LOW_Y2 = 10, 20


def _digit(d):
    """Numerals: 12 px wide, 12 px tall, 1 px stem. Low-poly Segoe/Fira
    proportions.
    """
    x1, x2 = _NUM_X1, _NUM_X2
    y1, y2 = _NUM_Y1, _NUM_Y2
    if d == "0":
        return [[(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]]
    if d == "1":
        cx = (x1 + x2) // 2
        return [
            [(cx - 2, y1 + 2), (cx, y1), (cx, y2)],
            [(cx - 2, y2), (x2, y2)],
        ]
    if d == "2":
        return [
            [(x1, y1 + 2), (x1 + 2, y1), (x2 - 2, y1), (x2, y1 + 2),
             (x2, y1 + 4), (x1 + 4, y1 + 7), (x1, y1 + 9),
             (x1, y2), (x2, y2)],
        ]
    if d == "3":
        return [
            [(x1 + 2, y1), (x2 - 2, y1), (x2, y1 + 2), (x2, y1 + 6),
             (x2 - 2, y1 + 7), (x1 + 2, y1 + 7),
             (x2 - 2, y1 + 7), (x2, y1 + 8), (x2, y1 + 12),
             (x2 - 2, y2), (x1 + 2, y2)],
        ]
    if d == "4":
        return [
            [(x2 - 1, y1), (x1 + 2, y1 + 6), (x2, y1 + 6), (x2, y1)],
            [(x2, y1), (x2, y2)],
        ]
    if d == "5":
        return [
            [(x2, y1), (x1 + 2, y1), (x1, y1 + 2),
             (x1, y1 + 6), (x2 - 2, y1 + 6), (x2, y1 + 8),
             (x2, y2), (x1 + 2, y2)],
        ]
    if d == "6":
        return [
            [(x2 - 1, y1 + 1), (x1 + 2, y1 + 1), (x1, y1 + 3),
             (x1, y1 + 6), (x1, y2), (x2 - 2, y2), (x2, y1 + 8),
             (x2 - 2, y1 + 6), (x1, y1 + 6)],
        ]
    if d == "7":
        return [
            [(x1, y1), (x2, y1), (x1 + 2, y2)],
        ]
    if d == "8":
        return [
            [(x1 + 3, y1), (x2 - 2, y1), (x2, y1 + 3), (x1, y1 + 6),
             (x2, y1 + 9), (x2, y2), (x1 + 3, y2), (x1, y1 + 9),
             (x1, y1 + 3), (x1 + 3, y1), (x2 - 2, y1)],
        ]
    if d == "9":
        return [
            [(x2 - 2, y1 + 4), (x1, y1 + 4), (x1, y1 + 2),
             (x1 + 3, y1), (x2 - 2, y1), (x2, y1 + 3),
             (x2, y2), (x2 - 2, y2), (x1, y1 + 6)],
        ]
    raise ValueError(d)


def _cap(c):
    x1, x2 = _CAP_X1, _CAP_X2
    y1, y2 = _CAP_Y1, _CAP_Y2
    half = (x1 + x2) // 2
    if c == "A":
        return [
            [(x1, y2), (half, y1), (x2, y2)],
            [(x1 + 3, y1 + 8), (x2 - 3, y1 + 8)],
        ]
    if c == "M":
        cx1 = x1 + (x2 - x1) // 4
        cx2 = x2 - (x2 - x1) // 4
        return [
            [(x1, y2), (x1, y1), (cx1, y1 + 8), (cx2, y1),
             (x2, y1), (x2, y2)],
        ]
    if c == "P":
        return [
            [(x1, y2), (x1, y1), (x2 - 1, y1), (x2, y1 + 4),
             (x2, y1 + 6), (x1, y1 + 6), (x1, y2)],
        ]
    if c == "W":
        return [
            [(1, y1), (1, y2), (5, y1 + 10), (8, y2),
             (11, y1 + 10), (15, y1), (15, y2)],
        ]
    if c == "S":
        return [
            [(x2, y1), (x1 + 1, y1), (x1, y1 + 2),
             (x1, y1 + 6), (x2 - 1, y1 + 6), (x2, y1 + 8),
             (x2, y2), (x1 + 1, y2)],
        ]
    if c == "D":
        return [
            [(x1, y1), (x1, y2), (x1 + 6, y2),
             (x2, y1 + 4), (x1 + 6, y1), (x1, y1)],
        ]
    if c == "B":
        return [
            [(x1, y2), (x1, y1), (x2 - 1, y1), (x2, y1 + 3),
             (x2 - 1, y1 + 6), (x1, y1 + 6),
             (x2 - 1, y1 + 6), (x2, y1 + 10),
             (x2 - 1, y2), (x1, y2)],
        ]
    if c == "K":
        return [
            [(x1, y2), (x1, y1)],
            [(x2, y1), (x1 + 2, y1 + 8), (x2, y2)],
        ]
    if c == "L":
        return [
            [(x1, y1), (x1, y2), (x2, y2)],
        ]
    if c == "T":
        return [
            [(x1, y1), (x2, y1)],
            [(half, y1), (half, y2)],
        ]
    if c == "H":
        return [
            [(x1, y1), (x1, y2)],
            [(x2, y1), (x2, y2)],
            [(x1, y1 + 8), (x2, y1 + 8)],
        ]
    if c == "R":
        return [
            [(x1, y2), (x1, y1), (x2 - 1, y1), (x2, y1 + 3),
             (x2 - 1, y1 + 7), (x1, y1 + 7),
             (x1 + 6, y1 + 7), (x2, y2)],
        ]
    if c == "N":
        return [
            [(x1, y2), (x1, y1), (x2, y2), (x2, y1)],
        ]
    if c == "I":
        return [
            [(x1, y1), (x2, y1)],
            [(half, y1), (half, y2)],
            [(x1, y2), (x2, y2)],
        ]
    if c == "U":
        return [
            [(x1, y1), (x1, y2 - 4), (x1 + 5, y2),
             (x2 - 5, y2), (x2, y2 - 4), (x2, y1)],
        ]
    if c == "C":
        return [
            [(x2, y1 + 2), (x1 + 1, y1), (x1, y1 + 4),
             (x1, y2 - 4), (x1 + 1, y2), (x2, y2 - 2)],
        ]
    if c == "G":
        return [
            [(x2 - 1, y1 + 1), (x1 + 1, y1), (x1, y1 + 4),
             (x1, y2 - 4), (x1 + 1, y2), (x2 - 1, y2),
             (x2, y2 - 4), (x2, y1 + 10), (half, y1 + 10)],
        ]
    if c == "E":
        return [
            [(x2, y1), (x1, y1), (x1, y2), (x2, y2)],
            [(x1, y1 + 8), (x2, y1 + 8)],
        ]
    if c == "F":
        return [
            [(x2, y1), (x1, y1), (x1, y2)],
            [(x1, y1 + 8), (x2, y1 + 8)],
        ]
    if c == "J":
        return [
            [(half, y1), (half, y2), (x1 + 1, y2), (x1, y1 + 4)],
        ]
    if c == "O":
        return [
            [(x1 + 5, y1), (x1, y1 + 4), (x1, y2 - 4),
             (x1 + 5, y2), (x2 - 5, y2), (x2, y2 - 4),
             (x2, y1 + 4), (x2 - 5, y1), (x1 + 5, y1)],
        ]
    if c == "Q":
        # Like O plus a small tail.
        return [
            [(x1 + 5, y1), (x1, y1 + 4), (x1, y2 - 4),
             (x1 + 5, y2), (x2 - 5, y2), (x2 - 2, y2),
             (x2 + 2, y2 + 2), (x2, y2 + 2),
             (x2, y2 - 4), (x2 - 5, y1), (x1 + 5, y1)],
        ]
    if c == "V":
        return [
            [(x1, y1), (half, y2), (x2, y1)],
        ]
    if c == "X":
        return [
            [(x1, y1), (x2, y2)],
            [(x2, y1), (x1, y2)],
        ]
    if c == "Y":
        return [
            [(x1, y1), (half, y1 + 8), (x2, y1)],
            [(half, y1 + 8), (half, y2)],
        ]
    if c == "Z":
        return [
            [(x1, y1), (x2, y1), (x1, y2), (x2, y2)],
        ]
    raise ValueError(c)


def _low(c):
    x1, x2 = _LOW_X1, _LOW_X2
    y1, y2 = _LOW_Y1, _LOW_Y2
    half = (x1 + x2) // 2
    if c == "m":
        cx1 = x1 + 4
        cx2 = cx1 + 4
        return [
            [(x1, y2), (x1, y1 + 4), (cx1, y1), (cx1, y2)],
            [(cx1, y1), (cx2, y1 + 4), (cx2, y2)],
            [(cx2, y1), (x2, y1 + 4), (x2, y2)],
        ]
    if c == "u":
        return [
            [(x1, y1), (x1, y2 - 4), (x1 + 5, y2),
             (x2 - 5, y2), (x2, y2 - 4), (x2, y1)],
        ]
    if c == "e":
        return [
            [(half, y1), (x1 + 1, y1 + 4), (x1, y1 + 4),
             (x1, y2 - 3), (x1 + 5, y2), (x2 - 1, y2),
             (x2, y1 + 6), (x1, y1 + 6), (half, y1)],
        ]
    if c == "r":
        return [
            [(x1 + 1, y1 + 2), (x1, y1 + 4), (x1, y2)],
            [(x1, y1 + 4), (x1 + 4, y1), (x1 + 4, y1 + 2)],
        ]
    if c == "d":
        return [
            [(x2, y1 - 2), (x2, y2)],
            [(x2, y2), (x1 + 5, y2), (x1, y1 + 5),
             (x1 + 5, y1), (x2, y1)],
        ]
    if c == "a":
        return [
            [(x1 + 4, y1), (x1, y1 + 4), (x1, y2 - 2),
             (x1 + 4, y2), (x2, y2 - 2), (x2, y1 + 4),
             (x2, y1 + 6), (x1, y1 + 6), (x1 + 4, y1)],
        ]
    if c == "y":
        return [
            [(x1, y1), (half, y1 + 8)],
            [(x2, y1), (half, y1 + 8), (half, y2 + 4)],
        ]
    if c == "n":
        return [
            [(x1, y2), (x1, y1 + 4), (x1 + 4, y1), (x1 + 4, y2)],
            [(x1 + 4, y1), (x2, y1 + 4), (x2, y2)],
        ]
    if c == "o":
        return [
            [(x1 + 4, y1), (x1, y1 + 4), (x1, y2 - 2),
             (x1 + 4, y2), (x2 - 1, y2), (x2, y1 + 4),
             (x2 - 1, y1), (x1 + 4, y1)],
        ]
    if c == "h":
        return [
            [(x1, y1 - 2), (x1, y2)],
            [(x1, y1 + 4), (x1 + 4, y1), (x1 + 4, y2)],
            [(x1 + 4, y1), (x2, y1 + 4), (x2, y2)],
        ]
    if c == "i":
        return [
            [(half, y1 + 1), (half, y1 + 2)],
            [(half, y1 + 4), (half, y2)],
        ]
    if c == "l":
        return [
            [(half, y1 - 2), (half, y2)],
        ]
    if c == "t":
        return [
            [(half, y1), (half, y2)],
            [(x1, y1 + 4), (x2, y1 + 4)],
        ]
    if c == "b":
        return [
            [(x1, y1 - 2), (x1, y2)],
            [(x1, y2), (x1 + 4, y2), (x1 + 4, y1),
             (x2, y1 + 4), (x2, y2 - 2), (x1 + 4, y2)],
        ]
    if c == "k":
        return [
            [(x1, y1 - 2), (x1, y2)],
            [(x2, y1), (half, y1 + 5), (x2, y2)],
        ]
    if c == "w":
        return [
            [(x1, y1), (x1 + 2, y2), (half, y1 + 4),
             (x2 - 2, y2), (x2, y1)],
        ]
    if c == "x":
        return [
            [(x1, y1), (x2, y2)],
            [(x2, y1), (x1, y2)],
        ]
    if c == "p":
        return [
            [(x1, y1 - 2), (x1, y2 + 4)],
            [(x1, y2), (x1 + 4, y2), (x2, y1 + 4),
             (x1 + 4, y1), (x1, y1)],
        ]
    if c == "q":
        return [
            [(x2, y1), (x2, y2 + 4)],
            [(x2, y1), (x1 + 4, y1), (x1, y1 + 4),
             (x1 + 4, y2), (x2, y2)],
        ]
    if c == "g":
        return [
            [(x2, y1), (x2, y2 + 4), (x1 + 4, y2 + 4),
             (x1 + 4, y2 - 1)],
            [(x2, y1), (x1 + 4, y1), (x1, y1 + 4),
             (x1 + 4, y2), (x2, y2 - 2)],
        ]
    if c == "s":
        return [
            [(x2, y1), (x1 + 1, y1), (x1, y1 + 4),
             (x2, y2), (x1 + 1, y2)],
        ]
    if c == "c":
        return [
            [(x2, y1), (x1, y1 + 4), (x1, y2 - 2), (x2, y2)],
        ]
    if c == "f":
        return [
            [(half, y1), (half, y2)],
            [(x1, y1 + 5), (x2, y1 + 5)],
        ]
    if c == "j":
        return [
            [(half, y1), (half, y2 + 4), (x1 + 2, y2 + 4),
             (x1 + 2, y2 - 1)],
        ]
    if c == "v":
        return [
            [(x1, y1), (half, y2), (x2, y1)],
        ]
    if c == "z":
        return [
            [(x1, y1), (x2, y1), (x1, y2), (x2, y2)],
        ]
    raise ValueError(c)


def _pause():
    # Two strokes (each a single polyline).
    return [
        [(4, _CAP_Y1), (4, _CAP_Y2), (8, _CAP_Y2),
         (8, _CAP_Y1), (4, _CAP_Y1)],
        [(9, _CAP_Y1), (9, _CAP_Y2), (13, _CAP_Y2),
         (13, _CAP_Y1), (9, _CAP_Y1)],
    ]


def _play(n_arrows: int):
    """N overlapping right-pointing triangles (play arrow sequence)."""
    polys = []
    base_y = _CAP_Y1
    h = _CAP_Y2 - _CAP_Y1
    width = 7
    step = 5
    for i in range(n_arrows):
        ox = 1 + i * step
        polys.append([
            (ox, base_y),
            (ox, base_y + h),
            (ox + width, base_y + h // 2),
        ])
    return polys


# ------------------------------------------------------------
# Punctuation glyph designs. Each occupies the 16-px design grid
# and respects the same cap/num/low band conventions used above.
# (Comma, apostrophe, parentheses, ? ! % & * _ [ ] < > ~ ; ^)
# ------------------------------------------------------------

def _comma():
    # Mirror of the period glyph but with a small descender tail at
    # the bottom-left so it sits visibly lower.
    return [
        [(5, 15), (7, 15), (7, 17), (5, 17), (5, 15)],
        [(5, 17), (4, 20), (5, 21)],
    ]


def _apostrophe():
    return [[(7, 14), (8, 14), (8, 18), (7, 18), (7, 14)]]


def _parenleft():
    return [[
        (10, 4), (5, 8), (5, 16), (10, 20), (7, 20),
        (4, 16), (4, 8), (7, 4), (10, 4),
    ]]


def _parenright():
    return [[
        (6, 4), (11, 8), (11, 16), (6, 20), (9, 20),
        (12, 16), (12, 8), (9, 4), (6, 4),
    ]]


def _question():
    return [
        [(4, 7), (7, 4), (12, 4), (12, 10), (8, 14),
         (8, 17), (8, 18)],
        [(8, 20), (8, 21)],
    ]


def _exclam():
    return [
        [(7, 4), (8, 4), (8, 16), (7, 16), (7, 4)],
        [(7, 19), (8, 19)],
    ]


def _percent():
    return [
        [(4, 7), (4, 5), (5, 4), (6, 4), (7, 5), (7, 7),
         (6, 8), (5, 8), (4, 7)],
        [(9, 10), (13, 16)],
        [(12, 14), (10, 14), (9, 16), (9, 17), (10, 18),
         (12, 18), (13, 17), (13, 16), (12, 14)],
    ]


def _ampersand():
    return [[
        (8, 4), (5, 4), (4, 7), (4, 9), (6, 10), (12, 16),
        (12, 19), (10, 20), (7, 20), (5, 19), (4, 17),
        (4, 14), (5, 12), (8, 9), (12, 9), (12, 6),
        (10, 4), (8, 4),
    ]]


def _asterisk():
    return [
        [(7, 4), (7, 20)],
        [(3, 12), (13, 12)],
        [(4, 6), (12, 18)],
        [(4, 18), (12, 6)],
    ]


def _underscore():
    return [[(3, 19), (13, 19)]]


def _bracketleft():
    return [[
        (8, 4), (4, 4), (4, 20), (8, 20), (6, 18),
        (6, 6), (8, 4),
    ]]


def _bracketright():
    return [[
        (8, 4), (12, 4), (12, 20), (8, 20), (10, 18),
        (10, 6), (8, 4),
    ]]


def _less():
    return [[(11, 4), (4, 12), (11, 20), (10, 20),
             (3, 12), (10, 4), (11, 4)]]


def _greater():
    return [[(5, 4), (12, 12), (5, 20), (6, 20),
             (13, 12), (6, 4), (5, 4)]]


def _asciitilde():
    return [[(3, 13), (4, 11), (6, 11), (7, 13),
             (8, 15), (10, 15), (11, 13), (12, 11),
             (13, 11), (14, 13)]]


def _semicolon():
    return [
        [(7, 9), (8, 9), (8, 13), (7, 13), (7, 9)],
        [(7, 13), (6, 16), (7, 17)],
        [(7, 19), (8, 19), (8, 20), (7, 20), (7, 19)],
    ]


def _circumflex():
    return [[(3, 8), (8, 4), (13, 8), (12, 8),
             (8, 5), (4, 8), (3, 8)]]


def _backslash():
    return [[(3, 4), (13, 20)]]


def _equal():
    return [[(4, 10), (12, 10)], [(4, 14), (12, 14)]]


# ------------------------------------------------------------
# Additional punctuation glyphs - second pass. These cover
# quoted text ($) "@#hash"), math (±²³), and full ASCII
# punctuation ("#@`{|}) so HUD chrome never has to fall back
# to the system font.
# ------------------------------------------------------------


def _dquote():
    # Two parallel vertical marks at the top of the design grid.
    return [
        [(7, 4), (7, 9), (8, 9), (8, 4), (7, 4)],
        [(10, 4), (10, 9), (11, 9), (11, 4), (10, 4)],
    ]


def _hash():
    # Two slanted verticals + two horizontal cross-bars.
    return [
        [(4, 6), (4, 18), (5, 18), (5, 6), (4, 6)],
        [(11, 6), (11, 18), (12, 18), (12, 6), (11, 6)],
        [(4, 8), (12, 8)],
        [(4, 16), (12, 16)],
        # Slight slant for hash-blocks
    ]


def _dollar():
    # Vertical line with two C-curves forming an S shape.
    return [
        [(7, 4), (7, 20)],
        [(5, 6), (5, 8), (8, 8), (10, 11),
         (10, 14), (7, 14), (10, 14), (10, 17),
         (7, 18), (5, 18), (5, 20)],
    ]


def _at():
    # Open inner ring + outer C with a tail.
    return [
        [(5, 12), (5, 8), (7, 6), (10, 6),
         (13, 8), (13, 12), (11, 12), (11, 10),
         (10, 8), (8, 9), (7, 11), (8, 13),
         (10, 13), (10, 15), (10, 17), (7, 18),
         (5, 17)],
    ]


def _grave():
    # Backtick - same height as apostrophe (top of design) but flipped.
    return [[(7, 4), (7, 8), (8, 8), (8, 4), (7, 4)]]


def _bar():
    # Vertical bar - thick stem with cutout at top/bottom.
    return [[(7, 4), (9, 4), (9, 20), (7, 20), (7, 4)]]


def _braceleft():
    # Curly brace - rounded left brace.
    return [
        [(11, 4), (7, 4), (6, 5), (6, 9),
         (4, 10), (6, 11), (6, 15),
         (7, 16), (11, 20), (8, 20),
         (5, 15), (5, 10), (5, 5),
         (8, 4)],
    ]


def _braceright():
    return [
        [(5, 4), (9, 4), (10, 5), (10, 9),
         (12, 10), (10, 11), (10, 15),
         (9, 16), (5, 20), (8, 20),
         (11, 15), (11, 10), (11, 5),
         (8, 4)],
    ]


def _degree():
    # Small filled circle in upper part of glyph.
    return [
        [(8, 6), (6, 6), (5, 8), (5, 10),
         (6, 12), (8, 12), (10, 10),
         (10, 8), (8, 6)],
    ]


def _plusminus():
    # Plus stacked above a horizontal minus line.
    return [
        [(4, 12), (12, 12)],
        [(8, 8), (8, 16)],
        [(4, 14), (12, 14)],
    ]


def _multiply():
    # x-style cross used by hand-marked values.
    return [[(4, 4), (12, 20)], [(12, 4), (4, 20)]]


def _divide():
    # Diagonal slash + small dot above + small dot below.
    return [
        [(4, 8), (5, 8), (5, 9), (4, 9), (4, 8)],
        [(3, 20), (13, 4)],
        [(10, 15), (11, 15), (11, 16), (10, 16), (10, 15)],
    ]


def _two_super():
    # Tiny circle that reads as a superscript "2".
    return [
        [(7, 13), (8, 13), (10, 12), (10, 11),
         (8, 9), (6, 11), (6, 15), (10, 15)],
    ]


def _three_super():
    return [
        [(6, 12), (9, 12), (10, 13),
         (8, 14), (10, 15), (10, 17),
         (9, 18), (7, 18), (6, 17)],
    ]


def _solidus_alt():
    # A wider `/` variant for fraction use.
    return [[(3, 18), (13, 6)]]


# Hyphen with a small filled rectangle to survive fontTools'
# "single line is degenerate outline" optimisation that strips
# the basic U+002D codepoint from cmap at save time.
def _hyphen():
    return [[(4, 13), (12, 13), (12, 15), (4, 15), (4, 13)]]



# Master glyph table.
GLYPHS = [
    # No glyph for U+0020. fontTools 4.65 strips space from cmap if a
    # glyph is registered, and Unity falls back gracefully on missing
    # codepoints using the font's average advance. Keeping space off
    # the glyph table avoids any rendering as a "black square" stub.
    _g("-", _hyphen(), kclass=_KC.Punct),
    _g("+", [[(4, 14), (12, 14)], [(7, 11), (7, 17)]], kclass=_KC.Punct),
    _g("#", _hash(), kclass=_KC.Punct),
    _g("$", _dollar(), kclass=_KC.Punct),
    _g("@", _at(), kclass=_KC.Punct),
    _g("`", _grave(), kclass=_KC.Punct),
    _g("\"", _dquote(), kclass=_KC.Punct),
    _g("|", _bar(), kclass=_KC.Punct),
    _g("{", _braceleft(), kclass=_KC.Punct),
    _g("}", _braceright(), kclass=_KC.Punct),
    _g("°", _degree(), kclass=_KC.Punct),
    _g("±", _plusminus(), kclass=_KC.Punct),
    _g("²", _two_super(), kclass=_KC.Punct),
    _g("³", _three_super(), kclass=_KC.Punct),
    _g("×", _multiply(), kclass=_KC.Punct),
    _g("÷", _divide(), kclass=_KC.Punct),
    _g("/", [[(3, 20), (13, 4)]], kclass=_KC.Punct),
    _g(":", [[(7, 10), (7, 12)], [(7, 16), (7, 18)]], kclass=_KC.Punct),
    _g(".", [[(7, 20), (8, 20), (8, 19), (7, 19)]], kclass=_KC.Punct),
    _g(",", _comma(), kclass=_KC.Punct),
    _g("'", _apostrophe(), kclass=_KC.Punct),
    _g("(", _parenleft(), kclass=_KC.Cap),
    _g(")", _parenright(), kclass=_KC.Cap),
    _g("?", _question(), kclass=_KC.Punct),
    _g("!", _exclam(), kclass=_KC.Punct),
    _g("%", _percent(), kclass=_KC.Cap),
    _g("&", _ampersand(), kclass=_KC.Punct),
    _g("*", _asterisk(), kclass=_KC.Punct),
    _g("_", _underscore(), kclass=_KC.Punct),
    _g("[", _bracketleft(), kclass=_KC.Cap),
    _g("]", _bracketright(), kclass=_KC.Cap),
    _g("<", _less(), kclass=_KC.Cap),
    _g(">", _greater(), kclass=_KC.Cap),
    _g("~", _asciitilde(), kclass=_KC.Punct),
    _g(";", _semicolon(), kclass=_KC.Punct),
    _g("^", _circumflex(), kclass=_KC.Punct),
    _g("=", _equal(), kclass=_KC.Punct),
    _g("\\", _backslash(), kclass=_KC.Punct),
    _g("0", _digit("0"), kclass=_KC.Digit),
    _g("1", _digit("1")),
    _g("2", _digit("2")),
    _g("3", _digit("3")),
    _g("4", _digit("4")),
    _g("5", _digit("5")),
    _g("6", _digit("6")),
    _g("7", _digit("7")),
    _g("8", _digit("8")),
    _g("9", _digit("9"), kclass=_KC.Digit),
    # Every uppercase letter used by HUD strings.
    _g("A", _cap("A"), kclass=_KC.Cap),
    _g("B", _cap("B"), kclass=_KC.Cap),
    _g("C", _cap("C"), kclass=_KC.Cap),
    _g("D", _cap("D"), kclass=_KC.Cap),
    _g("E", _cap("E"), kclass=_KC.Cap),
    _g("F", _cap("F"), kclass=_KC.Cap),
    _g("G", _cap("G"), kclass=_KC.Cap),
    _g("H", _cap("H"), kclass=_KC.Cap),
    _g("I", _cap("I"), kclass=_KC.Cap),
    _g("J", _cap("J"), kclass=_KC.Cap),
    _g("K", _cap("K"), kclass=_KC.Cap),
    _g("L", _cap("L"), kclass=_KC.Cap),
    _g("M", _cap("M"), kclass=_KC.Cap),
    _g("N", _cap("N"), kclass=_KC.Cap),
    _g("O", _cap("O"), kclass=_KC.Cap),
    _g("P", _cap("P"), kclass=_KC.Cap),
    _g("Q", _cap("Q"), kclass=_KC.Cap),
    _g("R", _cap("R"), kclass=_KC.Cap),
    _g("S", _cap("S"), kclass=_KC.Cap),
    _g("T", _cap("T"), kclass=_KC.Cap),
    _g("U", _cap("U"), kclass=_KC.Cap),
    _g("V", _cap("V"), kclass=_KC.Cap),
    _g("W", _cap("W"), kclass=_KC.Cap),
    _g("X", _cap("X"), kclass=_KC.Cap),
    _g("Y", _cap("Y"), kclass=_KC.Cap),
    _g("Z", _cap("Z"), kclass=_KC.Cap),
    # Lowercase letters for units + season words if needed later.
    _g("a", _low("a"), kclass=_KC.Low),
    _g("b", _low("b"), kclass=_KC.Low),
    _g("c", _low("c"), kclass=_KC.Low),
    _g("d", _low("d"), kclass=_KC.Low),
    _g("e", _low("e"), kclass=_KC.Low),
    _g("f", _low("f"), kclass=_KC.Low),
    _g("g", _low("g"), kclass=_KC.Low),
    _g("h", _low("h"), kclass=_KC.Low),
    _g("i", _low("i"), kclass=_KC.Low),
    _g("j", _low("j"), kclass=_KC.Low),
    _g("k", _low("k"), kclass=_KC.Low),
    _g("l", _low("l"), kclass=_KC.Low),
    _g("m", _low("m"), kclass=_KC.Low),
    _g("n", _low("n"), kclass=_KC.Low),
    _g("o", _low("o"), kclass=_KC.Low),
    _g("p", _low("p"), kclass=_KC.Low),
    _g("q", _low("q"), kclass=_KC.Low),
    _g("r", _low("r"), kclass=_KC.Low),
    _g("s", _low("s"), kclass=_KC.Low),
    _g("t", _low("t"), kclass=_KC.Low),
    _g("u", _low("u"), kclass=_KC.Low),
    _g("v", _low("v"), kclass=_KC.Low),
    _g("w", _low("w"), kclass=_KC.Low),
    _g("x", _low("x"), kclass=_KC.Low),
    _g("y", _low("y"), kclass=_KC.Low),
    _g("z", _low("z"), kclass=_KC.Low),
    _GlyphSpec(name="pause", char="\u23F8", width_in_units=_ADVANCE_UNITS,
               strokes=_pause()),
]
# Reverse lookup tables for the build script.
_INDEX_BY_NAME = {g.name: i for i, g in enumerate(GLYPHS)}
_GLYPH_BY_CHAR = {g.char: g for g in GLYPHS if g.char}


def glyph_by_char(c):
    return _GLYPH_BY_CHAR.get(c)


def glyph_by_name(name):
    return GLYPHS[_INDEX_BY_NAME[name]] if name in _INDEX_BY_NAME else None


def glyph_index_by_name(name):
    return _INDEX_BY_NAME.get(name, -1)
