"""
Paints the pictures the internet gear's models carry (tools/make_internet.py): port panels, LED rows, vents, labels, cable windings, the
satellite panels' faces. System Python + PIL; the PNGs go beside the case labels (assets/_scratch/case_labels) and Blender puts them on flat
quads (case_labels.add_flat).

    python tools/net_pictures.py
"""
import os
import random

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', '_scratch', 'case_labels')


def font(size, bold=True):
    try:
        return ImageFont.truetype('arialbd.ttf' if bold else 'arial.ttf', size)
    except OSError:
        return ImageFont.load_default()


def save(im, name):
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, name + '.png'))
    print('picture', name, im.size)


def centre(d, x, y, text, f, fill):
    d.text((x - d.textlength(text, font=f) / 2, y), text, font=f, fill=fill)


def jack(d, x, y, w=54, h=46, led=True, shell=(196, 198, 202)):
    """One RJ45 jack, its top left corner at (x, y): the metal shell, the dark opening with its latch notch, the gold contacts, two link lights."""
    d.rectangle((x, y, x + w, y + h), fill=shell, outline=(90, 92, 96), width=2)
    d.rectangle((x + 5, y + 6, x + w - 5, y + h - 12), fill=(16, 16, 18))
    d.rectangle((x + w * 0.32, y + h - 13, x + w * 0.68, y + h - 5), fill=(16, 16, 18))          # the latch notch
    for k in range(8):
        px = x + 10 + k * (w - 20) / 7
        d.line((px, y + 7, px, y + 15), fill=(214, 176, 72), width=2)
    if led:
        d.rectangle((x + 3, y - 9, x + 15, y - 3), fill=(70, 220, 90))
        d.rectangle((x + w - 15, y - 9, x + w - 3, y - 3), fill=(240, 170, 40))


def screws(d, W, H, inset=14, r=6, fill=(150, 152, 156)):
    for x, y in ((inset, inset), (W - inset, inset), (inset, H - inset), (W - inset, H - inset)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=(60, 60, 62))
        d.line((x - r + 2, y, x + r - 2, y), fill=(60, 60, 62), width=2)


def switch_front(name, ports, title, uplinks=0, body=(34, 36, 40), W=1024, H=128):
    """A switch's front: the model name, a power light, the jacks in a row (in two banks when there are many), uplink cages."""
    im = Image.new('RGB', (W, H), body)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(18, 18, 20), width=3)
    d.text((18, 14), title, font=font(22), fill=(232, 232, 228))
    d.text((18, 44), 'GIGABIT  PoE+', font=font(15), fill=(120, 190, 240))
    d.ellipse((22, 84, 36, 98), fill=(70, 220, 90))
    d.text((44, 82), 'PWR', font=font(14), fill=(170, 172, 176))
    d.ellipse((96, 84, 110, 98), fill=(240, 170, 40))
    d.text((118, 82), 'PoE', font=font(14), fill=(170, 172, 176))
    x0 = 200
    room = W - x0 - 24 - uplinks * 70
    step = min(64, room / ports)
    w = min(54, step - 6)
    for k in range(ports):
        x = x0 + k * step + (10 if ports > 8 and k >= ports // 2 else 0)
        jack(d, x, 48, w=w)
        centre(d, x + w / 2, 100, str(k + 1), font(13), (170, 172, 176))
    for k in range(uplinks):                                                             # SFP cages
        x = W - 24 - (uplinks - k) * 70 + 8
        d.rectangle((x, 50, x + 56, 92), fill=(150, 152, 156), outline=(80, 82, 86), width=2)
        d.rectangle((x + 5, 56, x + 51, 86), fill=(12, 12, 14))
        centre(d, x + 28, 100, 'SFP', font(13), (170, 172, 176))
    save(im, name)


def switch_front_2row(name, ports, title, W=1536, H=128, body=(34, 36, 40)):
    """A dense switch: the jacks in two rows."""
    im = Image.new('RGB', (W, H), body)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(18, 18, 20), width=3)
    d.text((18, 14), title, font=font(20), fill=(232, 232, 228))
    d.text((18, 44), 'GIGABIT  MANAGED', font=font(15), fill=(120, 190, 240))
    d.ellipse((22, 84, 36, 98), fill=(70, 220, 90))
    d.text((44, 82), 'PWR', font=font(14), fill=(170, 172, 176))
    per = ports // 2
    x0 = 300
    step = (W - x0 - 170) / per
    for r in range(2):
        for k in range(per):
            x = x0 + k * step + (12 if k >= per // 2 else 0)
            jack(d, x, 14 + r * 56, w=min(52, step - 6), h=42, led=False)
            d.rectangle((x + 2, 8 + r * 56, x + 10, 12 + r * 56), fill=(70, 220, 90))
    for k in range(2):
        x = W - 150 + k * 70
        d.rectangle((x, 44, x + 56, 86), fill=(150, 152, 156), outline=(80, 82, 86), width=2)
        d.rectangle((x + 5, 50, x + 51, 80), fill=(12, 12, 14))
        centre(d, x + 28, 94, 'SFP+', font(13), (170, 172, 176))
    save(im, name)


def rack_router_front(name, W=1536, H=128):
    """A rack router: the internet port, four LAN ports, a console port, a row of status lights."""
    im = Image.new('RGB', (W, H), (40, 44, 52))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(18, 18, 20), width=3)
    d.text((18, 14), 'GATEWAY ROUTER', font=font(24), fill=(232, 232, 228))
    d.text((18, 48), '4 LAN   1 WAN   VPN', font=font(15), fill=(120, 190, 240))
    for k, n in enumerate(('PWR', 'SYS', 'WAN', 'VPN')):
        x = 360 + k * 70
        d.ellipse((x, 40, x + 16, 56), fill=(70, 220, 90) if k != 3 else (60, 62, 66))
        centre(d, x + 8, 66, n, font(14), (170, 172, 176))
    jack(d, 760, 48, led=True, shell=(60, 130, 220))
    centre(d, 787, 100, 'WAN', font(14), (170, 172, 176))
    for k in range(4):
        jack(d, 900 + k * 70, 48, led=True, shell=(232, 196, 60))
        centre(d, 927 + k * 70, 100, 'LAN %d' % (k + 1), font(14), (170, 172, 176))
    jack(d, 1260, 48, led=False, shell=(120, 200, 220))
    centre(d, 1287, 100, 'CONSOLE', font(14), (170, 172, 176))
    d.rectangle((1380, 52, 1440, 82), fill=(60, 110, 200), outline=(150, 152, 156), width=2)
    centre(d, 1410, 100, 'USB', font(14), (170, 172, 176))
    save(im, name)


def camera_face(name, W=256, H=256):
    """A camera's front: the lens in its dark window, a ring of infrared lights round it."""
    import math
    im = Image.new('RGB', (W, H), (16, 16, 18))
    d = ImageDraw.Draw(im)
    c = W / 2
    d.ellipse((c - 62, c - 62, c + 62, c + 62), fill=(8, 8, 10), outline=(70, 72, 76), width=5)
    d.ellipse((c - 40, c - 40, c + 40, c + 40), fill=(20, 26, 46))
    d.ellipse((c - 22, c - 22, c + 22, c + 22), fill=(6, 8, 16))
    d.ellipse((c - 30, c - 34, c - 12, c - 16), fill=(120, 150, 210))
    for k in range(10):
        a = 2 * math.pi * k / 10
        x, y = c + 96 * math.cos(a), c + 96 * math.sin(a)
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(70, 20, 24), outline=(40, 40, 44))
    save(im, name)


def jack_face(name, W=256, H=416):
    """An Ethernet wall plate: white, a screw top and bottom, one keystone jack in the middle."""
    im = Image.new('RGB', (W, H), (240, 240, 236))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, W - 5, H - 5), radius=22, outline=(204, 204, 200), width=5)
    for y in (46, H - 46):
        d.ellipse((W / 2 - 13, y - 13, W / 2 + 13, y + 13), fill=(214, 214, 210), outline=(150, 152, 156), width=2)
        d.line((W / 2 - 9, y, W / 2 + 9, y), fill=(120, 122, 126), width=3)
    d.rounded_rectangle((W / 2 - 62, H / 2 - 62, W / 2 + 62, H / 2 + 62), radius=10, fill=(226, 226, 222), outline=(180, 180, 176), width=3)
    jack(d, W / 2 - 46, H / 2 - 40, w=92, h=78, led=False, shell=(246, 246, 242))
    centre(d, W / 2, H / 2 + 74, 'DATA', font(22), (120, 122, 126))
    save(im, name)


def ap_ceiling(name, W=384, H=384):
    """A ceiling access point seen from below: a white disc with a ring of light and the maker's dot."""
    im = Image.new('RGB', (W, H), (244, 244, 240))
    d = ImageDraw.Draw(im)
    c = W / 2
    d.ellipse((c - 150, c - 150, c + 150, c + 150), outline=(214, 214, 210), width=4)
    d.ellipse((c - 78, c - 78, c + 78, c + 78), outline=(70, 170, 250), width=9)
    d.ellipse((c - 12, c - 12, c + 12, c + 12), fill=(190, 190, 186))
    save(im, name)


def ups_front(name, W=1536, H=256):
    """A rack UPS: a vent grille across the front, a small display with the charge, the power button."""
    im = Image.new('RGB', (W, H), (24, 25, 28))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(12, 12, 14), width=4)
    for j in range(9):
        y = 30 + j * 22
        for i in range(34):
            x = 40 + i * 26
            d.rounded_rectangle((x, y, x + 18, y + 10), radius=4, fill=(8, 8, 10))
    d.rounded_rectangle((980, 40, 1330, 216), radius=10, fill=(14, 30, 38), outline=(90, 92, 96), width=4)     # the display
    d.text((1000, 54), 'ON LINE', font=font(26), fill=(120, 230, 160))
    d.text((1000, 96), '100%', font=font(64), fill=(210, 240, 250))
    for k in range(5):
        d.rectangle((1190 + k * 26, 110, 1208 + k * 26, 170), fill=(120, 230, 160))
    d.text((1000, 176), 'LOAD', font=font(20), fill=(150, 170, 180))
    d.ellipse((1380, 88, 1460, 168), fill=(40, 42, 46), outline=(150, 152, 156), width=4)                        # the power button
    d.arc((1400, 108, 1440, 148), 300, 240, fill=(120, 230, 160), width=5)
    d.line((1420, 100, 1420, 126), fill=(120, 230, 160), width=5)
    d.text((40, 222), 'UPS  3000 Wh   LINE-INTERACTIVE', font=font(20), fill=(170, 172, 176))
    save(im, name)


def rack_rail(name, W=64, H=512, units=8):
    """A rack's mounting rail: three square holes to the unit."""
    im = Image.new('RGB', (W, H), (26, 27, 30))
    d = ImageDraw.Draw(im)
    u = H / units
    for k in range(units):
        for j in range(3):
            y = k * u + u * (0.2 + 0.3 * j)
            d.rectangle((W / 2 - 9, y - 7, W / 2 + 9, y + 7), fill=(6, 6, 8), outline=(70, 72, 76))
        d.line((0, k * u, W, k * u), fill=(60, 62, 66), width=1)
    save(im, name)


def vents(name, rgb=(34, 36, 40), W=512, H=256, rows=5, slot=(20, 22, 24)):
    """Rows of cooling slots pressed into a lid or a side."""
    im = Image.new('RGB', (W, H), rgb)
    d = ImageDraw.Draw(im)
    for j in range(rows):
        y = H * (j + 0.5) / rows
        for i in range(14):
            x = 26 + i * (W - 52) / 14
            d.rounded_rectangle((x, y - 6, x + (W - 52) / 14 - 8, y + 6), radius=5, fill=slot)
    save(im, name)


def rear(name, power='48V DC', ports=0, body=(34, 36, 40), W=1024, H=128):
    """The back of a box: a power inlet, a ground screw, a rating sticker, any ports."""
    im = Image.new('RGB', (W, H), body)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(18, 18, 20), width=3)
    d.rounded_rectangle((W - 150, 30, W - 50, 100), radius=8, fill=(14, 14, 16), outline=(120, 122, 126), width=3)   # the power inlet
    for k in range(3):
        d.rectangle((W - 128 + k * 28, 52, W - 118 + k * 28, 78), fill=(190, 190, 186))
    d.text((W - 150, 104), power, font=font(14), fill=(190, 192, 196))
    d.ellipse((W - 210, 52, W - 184, 78), fill=(214, 176, 72), outline=(90, 80, 40), width=2)                       # the ground screw
    d.rectangle((40, 22, 380, 106), fill=(228, 228, 222))
    d.text((52, 28), 'MODEL  HS-NET', font=font(16), fill=(30, 30, 32))
    d.text((52, 50), 'INPUT  ' + power, font=font(14, False), fill=(30, 30, 32))
    rnd = random.Random(7)
    x = 52
    while x < 360:                                                                        # a bar code
        w = rnd.choice((2, 3, 5))
        d.rectangle((x, 74, x + w, 100), fill=(20, 20, 22))
        x += w + rnd.choice((2, 3, 4))
    for k in range(ports):
        jack(d, 430 + k * 66, 48, led=False)
    save(im, name)


def router_front(name, W=1024, H=128):
    """A router's front lip: a row of status lights with their names."""
    im = Image.new('RGB', (W, H), (22, 22, 24))
    d = ImageDraw.Draw(im)
    names = ('PWR', 'WAN', '2.4G', '5G', 'LAN1', 'LAN2', 'LAN3', 'LAN4', 'USB')
    for k, n in enumerate(names):
        x = 70 + k * (W - 140) / (len(names) - 1)
        col = (70, 220, 90) if n not in ('WAN', 'USB') else (80, 170, 250) if n == 'WAN' else (60, 62, 66)
        d.ellipse((x - 9, 40, x + 9, 58), fill=col)
        centre(d, x, 72, n, font(16), (170, 172, 176))
    save(im, name)


def router_back(name, W=1024, H=128):
    """A router's back: the internet port in blue, four yellow LAN ports, a USB port, the reset hole, the power jack and its switch."""
    im = Image.new('RGB', (W, H), (22, 22, 24))
    d = ImageDraw.Draw(im)
    jack(d, 120, 44, led=False, shell=(60, 130, 220))
    centre(d, 147, 98, 'INTERNET', font(14), (170, 172, 176))
    for k in range(4):
        jack(d, 230 + k * 66, 44, led=False, shell=(232, 196, 60))
        centre(d, 257 + k * 66, 98, str(k + 1), font(14), (170, 172, 176))
    d.rectangle((530, 50, 590, 80), fill=(60, 110, 200), outline=(150, 152, 156), width=2)
    centre(d, 560, 98, 'USB', font(14), (170, 172, 176))
    d.ellipse((640, 58, 654, 72), fill=(8, 8, 10))
    centre(d, 647, 98, 'RESET', font(14), (170, 172, 176))
    d.ellipse((730, 46, 770, 86), fill=(8, 8, 10), outline=(150, 152, 156), width=3)
    d.ellipse((745, 61, 755, 71), fill=(190, 190, 186))
    centre(d, 750, 98, '12V', font(14), (170, 172, 176))
    d.rectangle((830, 48, 890, 84), fill=(10, 10, 12), outline=(150, 152, 156), width=2)
    d.rectangle((834, 52, 860, 80), fill=(200, 30, 24))
    centre(d, 860, 98, 'POWER', font(14), (170, 172, 176))
    save(im, name)


def router_top(name, W=512, H=320):
    """A router's lid: a honeycomb of vent holes and the name."""
    im = Image.new('RGB', (W, H), (26, 26, 28))
    d = ImageDraw.Draw(im)
    for j in range(11):
        for i in range(22):
            x, y = 24 + i * 21.5 + (10.7 if j % 2 else 0), 70 + j * 19
            if x < W - 20:
                d.regular_polygon((x, y, 7), 6, fill=(10, 10, 12))
    d.text((24, 18), 'Wi-Fi ROUTER', font=font(26), fill=(210, 210, 206))
    d.text((W - 150, 24), 'AC1900', font=font(20), fill=(120, 190, 240))
    save(im, name)


def label(name, title, lines, rgb=(236, 236, 230), ink=(24, 24, 26), accent=(30, 90, 170), W=512, H=256, bars=True):
    """A printed sticker: a coloured band with the title, lines of small print, a bar code."""
    im = Image.new('RGB', (W, H), rgb)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(120, 120, 116), width=3)
    d.rectangle((3, 3, W - 4, 70), fill=accent)
    f = font(40)
    while d.textlength(title, font=f) > W - 30 and f.size > 14:
        f = font(f.size - 2)
    centre(d, W / 2, 35 - f.size / 2 - 2, title, f, (250, 250, 246))
    for k, line in enumerate(lines):
        d.text((18, 84 + k * 30), line, font=font(22, k == 0), fill=ink)
    if bars:
        rnd = random.Random(len(title))
        x = 18
        while x < W - 24:
            w = rnd.choice((2, 3, 5))
            d.rectangle((x, H - 58, x + w, H - 16), fill=ink)
            x += w + rnd.choice((2, 3, 4))
    save(im, name)


def winding(name, rgb, turns=22, W=64, H=512, print_text=None):
    """Cable wound on a reel or tied in a coil, seen from the side: one turn above the next, a shadow between them, the jacket's print now and then."""
    im = Image.new('RGB', (W, H), rgb)
    d = ImageDraw.Draw(im)
    step = H / turns
    dark = tuple(int(c * 0.45) for c in rgb)
    light = tuple(min(255, int(c * 1.25 + 14)) for c in rgb)
    for k in range(turns):
        y = k * step
        d.rectangle((0, y, W, y + step * 0.2), fill=dark)
        d.rectangle((0, y + step * 0.45, W, y + step * 0.6), fill=light)
        if print_text and k % 4 == 1:
            d.rectangle((W * 0.2, y + step * 0.66, W * 0.8, y + step * 0.82), fill=(240, 240, 236))
    save(im, name)


def ap_face(name, W=384, H=512):
    """An outdoor access point's front: a white moulded cover with a ring light, the maker's dot and a vent grille along the bottom."""
    im = Image.new('RGB', (W, H), (238, 238, 234))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, W - 11, H - 11), radius=40, outline=(206, 206, 202), width=5)
    cx, cy = W / 2, H * 0.36
    d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), outline=(60, 160, 250), width=10)
    d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(190, 190, 186))
    centre(d, cx, H * 0.6, 'OUTDOOR AP', font(26), (120, 122, 126))
    centre(d, cx, H * 0.67, 'Wi-Fi 5   IP67', font(18, False), (150, 152, 156))
    for k in range(9):
        x = 60 + k * (W - 120) / 8
        d.rounded_rectangle((x - 8, H - 96, x + 8, H - 44), radius=7, fill=(150, 152, 156))
    save(im, name)


def panel_face(name, W=512, H=320, rgb=(252, 252, 250)):
    """A flat satellite antenna's face: a smooth radome with a faint lip and the maker's small mark in a corner."""
    im = Image.new('RGB', (W, H), rgb)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, W - 7, H - 7), radius=26, outline=(214, 214, 210), width=6)
    d.rounded_rectangle((22, 22, W - 23, H - 23), radius=18, outline=(236, 236, 232), width=3)
    d.text((W - 150, H - 58), 'SATLINK', font=font(22), fill=(170, 172, 176))
    save(im, name)


def panel_back(name, W=512, H=320):
    """Its back: dark moulded ribs, a rating sticker, the cable port."""
    im = Image.new('RGB', (W, H), (58, 60, 64))
    d = ImageDraw.Draw(im)
    for k in range(9):
        x = 30 + k * (W - 60) / 8
        d.rectangle((x - 5, 20, x + 5, H - 20), fill=(40, 42, 46))
    d.rectangle((W / 2 - 110, H / 2 - 54, W / 2 + 110, H / 2 + 54), fill=(228, 228, 222))
    centre(d, W / 2, H / 2 - 44, 'SATELLITE TERMINAL', font(18), (30, 30, 32))
    centre(d, W / 2, H / 2 - 14, '48V DC   100W', font(16, False), (30, 30, 32))
    rnd = random.Random(3)
    x = W / 2 - 96
    while x < W / 2 + 96:
        w = rnd.choice((2, 3, 5))
        d.rectangle((x, H / 2 + 14, x + w, H / 2 + 44), fill=(20, 20, 22))
        x += w + rnd.choice((2, 3, 4))
    save(im, name)


def fabric(name, W=256, H=256, rgb=(214, 214, 210)):
    """Woven speaker cloth round a mesh router."""
    im = Image.new('RGB', (W, H), rgb)
    d = ImageDraw.Draw(im)
    for j in range(0, H, 6):
        for i in range(0, W, 6):
            if (i // 6 + j // 6) % 2 == 0:
                d.rectangle((i, j, i + 3, j + 3), fill=(190, 190, 186))
            else:
                d.rectangle((i + 2, j + 2, i + 5, j + 5), fill=(228, 228, 224))
    save(im, name)


def mesh_top(name, W=256, H=256):
    """A mesh router's lid: white, a ring of light, the Wi-Fi mark."""
    im = Image.new('RGB', (W, H), (240, 240, 236))
    d = ImageDraw.Draw(im)
    c = W / 2
    d.ellipse((c - 104, c - 104, c + 104, c + 104), outline=(80, 180, 250), width=8)
    for k, r in enumerate((60, 42, 24)):
        d.arc((c - r, c - r + 14, c + r, c + r + 14), 225, 315, fill=(150, 152, 156), width=7)
    d.ellipse((c - 7, c + 8, c + 7, c + 22), fill=(150, 152, 156))
    save(im, name)


def injector_top(name, W=512, H=224):
    im = Image.new('RGB', (W, H), (24, 24, 26))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, W - 9, H - 9), radius=18, outline=(60, 62, 66), width=4)
    d.text((28, 26), 'PoE INJECTOR', font=font(38), fill=(236, 236, 232))
    d.text((28, 76), '48V  30W  GIGABIT', font=font(22), fill=(120, 190, 240))
    d.text((28, 150), 'DATA IN', font=font(22), fill=(190, 192, 196))
    d.text((W - 150, 150), 'PoE OUT', font=font(22), fill=(240, 170, 40))
    d.line((150, 163, W - 170, 163), fill=(190, 192, 196), width=4)
    d.polygon(((W - 170, 152), (W - 152, 163), (W - 170, 174)), fill=(190, 192, 196))
    d.ellipse((W - 60, 30, W - 36, 54), fill=(70, 220, 90))
    save(im, name)


def port_end(name, text, shell=(196, 198, 202), body=(24, 24, 26), W=256, H=128):
    """The end of a small box with one jack in it."""
    im = Image.new('RGB', (W, H), body)
    d = ImageDraw.Draw(im)
    jack(d, W / 2 - 40, 24, w=80, h=64, led=False, shell=shell)
    centre(d, W / 2, 96, text, font(18), (200, 200, 196))
    save(im, name)


def arrestor_top(name, W=512, H=256):
    im = Image.new('RGB', (W, H), (176, 180, 186))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 4):                                                              # brushed aluminium
        d.line((0, y, W, y), fill=(168, 172, 178))
    screws(d, W, H, inset=22, r=9, fill=(120, 122, 126))
    centre(d, W / 2, 46, 'ETHERNET SURGE PROTECTOR', font(26), (24, 24, 26))
    centre(d, W / 2, 96, 'CAT6  PoE  GIGABIT', font(22), (24, 60, 130))
    d.text((60, 170), 'LINE', font=font(24), fill=(24, 24, 26))
    d.text((W - 190, 170), 'EQUIPMENT', font=font(24), fill=(24, 24, 26))
    d.polygon(((W / 2 - 16, 150), (W / 2 + 8, 150), (W / 2 - 4, 182), (W / 2 + 16, 182), (W / 2 - 14, 232), (W / 2 - 4, 194), (W / 2 - 22, 194)), fill=(230, 180, 30))
    save(im, name)


def main():
    switch_front('net_switch_front_5', 5, 'PoE SWITCH')
    switch_front('net_switch_front_8', 8, '8-PORT PoE SWITCH', uplinks=2)
    switch_front('net_switch_front_16', 16, '16-PORT MANAGED SWITCH', uplinks=2, W=1536)
    switch_front('net_switch_front_16_poe', 16, '16-PORT PoE+ SWITCH', uplinks=2, W=1536, body=(30, 40, 60))
    switch_front_2row('net_switch_front_32', 32, '32-PORT SWITCH')
    rack_router_front('net_rack_router_front')
    camera_face('net_camera_face')
    rack_rail('net_rack_rail')
    ups_front('net_ups_front')
    ap_ceiling('net_ap_ceiling')
    jack_face('net_jack_face')
    label('net_label_rack', '8U WALL RACK', ['19 in  EIA-310', 'Load 30 kg'], accent=(40, 40, 44), H=192, bars=False)
    vents('net_vents_dark')
    vents('net_vents_side', W=256, H=128, rows=3)
    rear('net_rear_switch', '100-240V AC')
    rear('net_rear_small', '48V DC')
    router_front('net_router_front')
    router_back('net_router_back')
    router_top('net_router_top')
    label('net_label_omni', 'OMNI 4G / LTE', ['698-2700 MHz', 'Gain 6 dBi', 'N-Female'], accent=(200, 60, 30))
    label('net_label_yagi', 'YAGI 4G / 5G', ['1710-2700 MHz', 'Gain 14 dBi', 'Aim at the tower'], accent=(30, 90, 170))
    label('net_label_cat6', 'CAT6 UTP', ['23 AWG solid copper', '550 MHz   CMR', 'Pull from this side'], accent=(20, 80, 170))
    label('net_label_patch', 'CAT6 PATCH', ['Snagless RJ45', 'Gigabit'], accent=(20, 80, 170), H=192, bars=False)
    winding('net_wind_blue', (38, 92, 190), print_text=True)
    winding('net_wind_grey', (150, 152, 156))
    ap_face('net_ap_face')
    panel_face('net_panel_face')
    panel_back('net_panel_back')
    fabric('net_fabric')
    mesh_top('net_mesh_top')
    injector_top('net_injector_top')
    port_end('net_port_in', 'DATA')
    port_end('net_port_out', 'PoE')
    port_end('net_port_alu', 'RJ45', body=(176, 180, 186))
    arrestor_top('net_arrestor_top')


if __name__ == '__main__':
    main()
