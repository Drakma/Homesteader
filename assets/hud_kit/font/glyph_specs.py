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


GLYPH_WIDTH = 16
ASCENDER = 24
DESCENDER = 4


@dataclass
class _GlyphSpec:
    name: str
    char: str
    width_in_units: int
    strokes: list = field(default_factory=list)


_UPEM = 1024
_ADVANCE_UNITS = GLYPH_WIDTH * (_UPEM // GLYPH_WIDTH)


def _g(c, points_list):
    name = {
        " ": "space",
        "-": "hyphen",
        "+": "plus",
        "/": "slash",
        ":": "colon",
        ".": "period",
    }.get(c, None)
    if name is None:
        if c.isdigit():
            name = ["zero", "one", "two", "three", "four",
                    "five", "six", "seven", "eight", "nine"][int(c)]
        elif c.isalpha():
            # Caps distinct from lowercase: use uppercase glyph name.
            if c.isupper():
                # Capital letters use the cap-height shape via _cap().
                name = c.lower() + "_cap"
            else:
                name = c.lower()
        else:
            name = f"u{ord(c):04x}"
    return _GlyphSpec(name=name, char=c, width_in_units=_ADVANCE_UNITS,
                       strokes=points_list)


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


# Master glyph table.
GLYPHS = [
    _g(" ", [[[]]]),
    _g("-", [[[ (4, 14), (12, 14) ]]]),
    _g("+", [[[ (4, 14), (12, 14) ]], [[ (7, 11), (7, 17) ]]]),
    _g("/", [[[ (3, 20), (13, 4) ]]]),
    _g(":", [[[ (7, 10), (7, 12) ]], [[ (7, 16), (7, 18) ]]]),
    _g(".", [[[ (7, 20), (8, 20), (8, 19), (7, 19) ]]]),
    _g("0", _digit("0")),
    _g("1", _digit("1")),
    _g("2", _digit("2")),
    _g("3", _digit("3")),
    _g("4", _digit("4")),
    _g("5", _digit("5")),
    _g("6", _digit("6")),
    _g("7", _digit("7")),
    _g("8", _digit("8")),
    _g("9", _digit("9")),
    # Every uppercase letter used by HUD strings.
    _g("A", _cap("A")),
    _g("B", _cap("B")),
    _g("C", _cap("C")),
    _g("D", _cap("D")),
    _g("E", _cap("E")),
    _g("F", _cap("F")),
    _g("G", _cap("G")),
    _g("H", _cap("H")),
    _g("I", _cap("I")),
    _g("J", _cap("J")),
    _g("K", _cap("K")),
    _g("L", _cap("L")),
    _g("M", _cap("M")),
    _g("N", _cap("N")),
    _g("O", _cap("O")),
    _g("P", _cap("P")),
    _g("Q", _cap("Q")),
    _g("R", _cap("R")),
    _g("S", _cap("S")),
    _g("T", _cap("T")),
    _g("U", _cap("U")),
    _g("V", _cap("V")),
    _g("W", _cap("W")),
    _g("X", _cap("X")),
    _g("Y", _cap("Y")),
    _g("Z", _cap("Z")),
    # Lowercase letters for units + season words if needed later.
    _g("a", _low("a")),
    _g("b", _low("b")),
    _g("c", _low("c")),
    _g("d", _low("d")),
    _g("e", _low("e")),
    _g("f", _low("f")),
    _g("g", _low("g")),
    _g("h", _low("h")),
    _g("i", _low("i")),
    _g("j", _low("j")),
    _g("k", _low("k")),
    _g("l", _low("l")),
    _g("m", _low("m")),
    _g("n", _low("n")),
    _g("o", _low("o")),
    _g("p", _low("p")),
    _g("q", _low("q")),
    _g("r", _low("r")),
    _g("s", _low("s")),
    _g("t", _low("t")),
    _g("u", _low("u")),
    _g("v", _low("v")),
    _g("w", _low("w")),
    _g("x", _low("x")),
    _g("y", _low("y")),
    _g("z", _low("z")),
    _GlyphSpec(name="pause", char="\u23F8", width_in_units=_ADVANCE_UNITS,
               strokes=_pause()),
]
