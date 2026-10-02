"""_add_media_glyphs.py - add the media / transport glyphs to every Homesteader HUD font file (idempotent).

Draws simple geometric outlines (no source font needed) and writes them in place into the kit fonts (assets/hud_kit/font/*.ttf)
and the Unity copies (Assets/Resources/HUDTree/Fonts/*.ttf). Codepoints:
  25B6 play, 25C0 reverse, 23F4/23F5 left/right, 25B2/23F6 up, 25BC/23F7 down, 25A0/23F9 stop, 25CF/23FA record, 23F8 pause,
  23ED next, 23EE previous, 23EF play/pause, 23E9 fast forward, 23EA rewind, 23EB/23EC double up/down, 23CF eject,
  266A/266B notes, E010 = pop-out, E000-E006 = shuffle, repeat, repeat one, speaker muted/low/medium/loud (BMP copies of the 1F5xx icons, use these in UI), 1F500 shuffle, 1F501 repeat, 1F502 repeat one, 1F507-1F50A speaker (muted, low, medium, loud).
Run: python assets/hud_kit/font/_add_media_glyphs.py
"""
import glob
import math
import os

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TARGETS = glob.glob(os.path.join(HERE, "*.ttf")) + glob.glob(os.path.join(ROOT, "Homesteader", "Assets", "Resources", "HUDTree", "Fonts", "*.ttf"))


def area(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2


class Shape:
    def __init__(self, adv=900):
        self.adv, self.contours = adv, []

    def add(self, pts, hole=False):
        a = area(pts)
        want_ccw = hole          # TrueType: outer contours clockwise, holes counter-clockwise
        if (a > 0) != want_ccw:
            pts = pts[::-1]
        self.contours.append(pts)
        return self

    def stroke(self, pts, w=70):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dx, dy = x1 - x0, y1 - y0
            n = math.hypot(dx, dy) or 1
            nx, ny = -dy / n * w / 2, dx / n * w / 2
            ex, ey = dx / n * w / 2, dy / n * w / 2
            self.add([(x0 - ex + nx, y0 - ey + ny), (x1 + ex + nx, y1 + ey + ny), (x1 + ex - nx, y1 + ey - ny), (x0 - ex - nx, y0 - ey - ny)])
        return self


def rect(x0, y0, x1, y1): return [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]
def tri_r(x0, x1, y0=30, y1=670): return [(x0, y0), (x0, y1), (x1, (y0 + y1) / 2)]
def tri_l(x0, x1, y0=30, y1=670): return [(x1, y0), (x1, y1), (x0, (y0 + y1) / 2)]
def tri_u(x0, x1, y0=40, y1=640): return [(x0, y0), ((x0 + x1) / 2, y1), (x1, y0)]
def tri_d(x0, x1, y0=40, y1=640): return [(x0, y1), (x1, y1), ((x0 + x1) / 2, y0)]
def ellipse(cx, cy, rx, ry, n=28, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(2 * math.pi * i / n) * c - ry * math.sin(2 * math.pi * i / n) * s,
             cy + rx * math.cos(2 * math.pi * i / n) * s + ry * math.sin(2 * math.pi * i / n) * c) for i in range(n)]
def wave(cx, cy, r0, r1, a=42, n=10):
    out = [(cx + r1 * math.cos(math.radians(-a + 2 * a * i / n)), cy + r1 * math.sin(math.radians(-a + 2 * a * i / n))) for i in range(n + 1)]
    inn = [(cx + r0 * math.cos(math.radians(a - 2 * a * i / n)), cy + r0 * math.sin(math.radians(a - 2 * a * i / n))) for i in range(n + 1)]
    return out + inn


def speaker(adv=1000):
    return Shape(adv).add([(100, 240), (280, 240), (500, 40), (500, 660), (280, 460), (100, 460)])


def build():
    g = {}
    g[0x25B6] = g[0x23F5] = Shape().add(tri_r(150, 770))
    g[0x25C0] = g[0x23F4] = Shape().add(tri_l(130, 750))
    g[0x25B2] = g[0x23F6] = Shape().add(tri_u(130, 770))
    g[0x25BC] = g[0x23F7] = Shape().add(tri_d(130, 770))
    g[0x25A0] = g[0x23F9] = Shape().add(rect(140, 40, 760, 660))
    g[0x25CF] = g[0x23FA] = Shape().add(ellipse(450, 350, 320, 320, 32))
    g[0x23F8] = Shape().add(rect(160, 30, 400, 670)).add(rect(500, 30, 740, 670))
    g[0x23ED] = Shape(940).add(tri_r(110, 660)).add(rect(690, 30, 830, 670))
    g[0x23EE] = Shape(940).add(rect(110, 30, 250, 670)).add(tri_l(280, 830))
    g[0x23EF] = Shape(980).add(tri_r(90, 520)).add(rect(580, 30, 700, 670)).add(rect(770, 30, 890, 670))
    g[0x23E9] = Shape(940).add(tri_r(80, 480)).add(tri_r(470, 870))
    g[0x23EA] = Shape(940).add(tri_l(70, 470)).add(tri_l(460, 860))
    g[0x23EB] = Shape().add(tri_u(130, 770, 20, 350)).add(tri_u(130, 770, 340, 670))
    g[0x23EC] = Shape().add(tri_d(130, 770, 350, 680)).add(tri_d(130, 770, 20, 350))
    g[0x23CF] = Shape().add(tri_u(130, 770, 250, 670)).add(rect(130, 30, 770, 170))
    g[0x266A] = Shape(700).add(ellipse(230, 110, 150, 105, 20, 0.4)).add(rect(330, 110, 390, 700)).add([(390, 700), (390, 540), (600, 380), (600, 500)])
    g[0x266B] = Shape(960).add(ellipse(230, 110, 150, 105, 20, 0.4)).add(ellipse(640, 60, 150, 105, 20, 0.4)) \
        .add(rect(330, 110, 390, 640)).add(rect(740, 60, 800, 600)).add([(330, 700), (800, 640), (800, 510), (330, 570)])
    shuf = Shape(950).stroke([(90, 520), (330, 520), (580, 180), (660, 180)]).stroke([(90, 180), (330, 180), (580, 520), (660, 520)])
    shuf.add([(650, 90), (650, 270), (840, 180)]).add([(650, 430), (650, 610), (840, 520)])
    g[0x1F500] = shuf
    def arc(cx, cy, r, a0, a1, n=8):
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

    def repeat_loop(one=False):
        sh = Shape(950)
        # top run heads right, bottom run heads left, each with a rounded end and an arrowhead
        sh.stroke([(110, 300), (110, 460)] + arc(210, 460, 100, 180, 90)[1:] + [(700, 560)], 64)
        sh.stroke([(790, 400), (790, 240)] + arc(690, 240, 100, 0, -90)[1:] + [(200, 140)], 64)
        sh.add([(690, 450), (690, 670), (880, 560)]).add([(210, 30), (210, 250), (20, 140)])
        if one:
            sh.add(rect(440, 250, 505, 470)).add([(440, 470), (505, 470), (390, 400)])
        return sh
    g[0x1F501] = repeat_loop()
    g[0x1F502] = repeat_loop(True)
    g[0x1F508] = speaker()
    g[0x1F509] = speaker().add(wave(500, 350, 200, 275, 50))
    g[0x1F50A] = speaker(1100).add(wave(500, 350, 200, 275, 50)).add(wave(500, 350, 350, 425, 50))
    g[0x1F507] = speaker().stroke([(620, 200), (880, 500)], 70).stroke([(620, 500), (880, 200)], 70)
    # Pop-out: a small empty square, open at its top-right corner, with an arrow leaving that corner diagonally up and to the right.
    pop = Shape(940).stroke([(450, 640), (100, 640), (100, 60), (700, 60), (700, 300)], 70)
    pop.stroke([(380, 300), (730, 650)], 70).add([(840, 760), (600, 760), (840, 520)])
    g[0xE010] = pop
    # The same five icons again in the Private Use Area (BMP, no emoji presentation): UI text uses these so no system emoji font can ever take over.
    for pua, src in ((0xE000, 0x1F500), (0xE001, 0x1F501), (0xE002, 0x1F502), (0xE003, 0x1F507), (0xE004, 0x1F508), (0xE005, 0x1F509), (0xE006, 0x1F50A)):
        g[pua] = g[src]
    return g


def patch(path, shapes):
    font = TTFont(path)
    glyf, hmtx, order = font["glyf"], font["hmtx"], font.getGlyphOrder()
    cmaps = [t for t in font["cmap"].tables if t.isUnicode()]
    names = {}
    for cp, sh in shapes.items():
        name = "media_%X" % cp
        pen = TTGlyphPen(None)
        for pts in sh.contours:
            pen.moveTo((round(pts[0][0]), round(pts[0][1])))
            for x, y in pts[1:]:
                pen.lineTo((round(x), round(y)))
            pen.closePath()
        glyph = pen.glyph()
        if name not in glyf.glyphs:
            order.append(name)
        glyf.glyphs[name] = glyph
        glyph.recalcBounds(glyf)
        hmtx.metrics[name] = (sh.adv, glyph.xMin)
        names[cp] = name
    font.setGlyphOrder(order)
    glyf.glyphOrder = order
    for cp, name in names.items():
        for t in cmaps:
            if cp <= 0xFFFF and t.format in (4, 12):
                t.cmap[cp] = name
    if any(cp > 0xFFFF for cp in names):
        t12 = next((t for t in cmaps if t.format == 12), None)
        if t12 is None:
            t12 = CmapSubtable.newSubtable(12)
            t12.platformID, t12.platEncID, t12.language = 3, 10, 0
            t12.cmap = dict(font.getBestCmap())
            font["cmap"].tables.append(t12)
        for cp, name in names.items():
            t12.cmap[cp] = name
    font.save(path)


if __name__ == "__main__":
    shapes = build()
    for path in TARGETS:
        patch(path, shapes)
        print("patched", os.path.relpath(path, ROOT))
