"""
Paints the pictures the stationary sawmill's model carries (tools/make_sawmill.py): the maker's plate, the engine's cover, the fuel tank's label, hazard stickers and the
ruler along the bed. System Python + PIL; the PNGs go beside the other model pictures (assets/_scratch/case_labels) and Blender puts them on flat quads.

    python tools/sawmill_pictures.py
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


def plate(name, W=640, H=240):
    """The maker's plate on the frame: engraved steel, the name, the rating, rivets."""
    im = Image.new('RGB', (W, H), (172, 176, 182))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 3):                                     # brushed
        d.line((0, y, W, y), fill=(164, 168, 174))
    d.rectangle((4, 4, W - 5, H - 5), outline=(70, 72, 76), width=5)
    for x, y in ((24, 24), (W - 24, 24), (24, H - 24), (W - 24, H - 24)):
        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(120, 122, 126), outline=(60, 60, 62))
    centre(d, W / 2, 26, 'HOMESTEADER', font(34), (30, 32, 36))
    centre(d, W / 2, 70, 'STATIONARY SAWMILL', font(46), (20, 70, 40))
    d.line((40, 128, W - 40, 128), fill=(70, 72, 76), width=3)
    d.text((44, 142), 'LOG   4.0 m  /  0.5 m DIA', font=font(26, False), fill=(30, 32, 36))
    d.text((44, 178), 'ENGINE   GASOLINE  14 HP', font=font(26, False), fill=(30, 32, 36))
    save(im, 'sm_plate')


def engine_cover(name, W=512, H=512):
    """The engine's top shroud: red plastic, the maker's name, a ribbed grille, a fuel and oil reminder."""
    im = Image.new('RGB', (W, H), (176, 28, 24))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, W - 11, H - 11), radius=30, outline=(120, 16, 14), width=8)
    centre(d, W / 2, 34, 'HS', font(110), (245, 240, 230))
    centre(d, W / 2, 150, 'POWER', font(54), (245, 240, 230))
    d.line((60, 222, W - 60, 222), fill=(245, 240, 230), width=5)
    for k in range(8):                                           # the cooling grille
        y = 250 + k * 26
        d.rounded_rectangle((70, y, W - 70, y + 14), radius=7, fill=(70, 10, 10))
    d.text((70, 468), 'GASOLINE ONLY   SAE 30', font=font(22), fill=(245, 240, 230))
    save(im, name)


def tank_label(name, W=384, H=192):
    """The fuel tank: a yellow band that says what goes in it."""
    im = Image.new('RGB', (W, H), (232, 190, 30))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(40, 36, 20), width=6)
    centre(d, W / 2, 24, 'GASOLINE', font(66), (30, 28, 24))
    centre(d, W / 2, 112, 'UNLEADED  87', font(36), (30, 28, 24))
    d.polygon(((20, 150), (60, 150), (40, 118)), fill=(30, 28, 24))
    d.polygon(((W - 20, 150), (W - 60, 150), (W - 40, 118)), fill=(30, 28, 24))
    save(im, name)


def hazard(name, W=384, H=256):
    """A sticker on the blade guard: keep clear of the blade."""
    im = Image.new('RGB', (W, H), (250, 218, 40))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(20, 20, 20), width=8)
    d.polygon(((W / 2, 24), (W / 2 + 70, 140), (W / 2 - 70, 140)), outline=(20, 20, 20), fill=(250, 218, 40), width=8)
    d.rectangle((W / 2 - 6, 64, W / 2 + 6, 104), fill=(20, 20, 20))
    d.ellipse((W / 2 - 7, 114, W / 2 + 7, 128), fill=(20, 20, 20))
    centre(d, W / 2, 158, 'DANGER', font(46), (20, 20, 20))
    centre(d, W / 2, 210, 'ROTATING BLADE', font(26), (20, 20, 20))
    save(im, name)


def ruler(name, W=2048, H=64):
    """The scale along the bed's front rail: a mark every 10 cm, a long one every half metre, the metres numbered."""
    im = Image.new('RGB', (W, H), (214, 216, 218))
    d = ImageDraw.Draw(im)
    metres = 6.0
    for k in range(0, 61):
        x = 8 + k * (W - 16) / 60
        long = k % 10 == 0
        d.line((x, 0, x, H * (0.62 if long else 0.34 if k % 5 == 0 else 0.2)), fill=(20, 20, 22), width=3 if long else 2)
        if long:
            d.text((x + 5, H * 0.52), str(k // 10), font=font(24), fill=(20, 20, 22))
    save(im, name)


def log_stop(name, W=256, H=256):
    """The plate on the log stop at the end of the bed: a faded arrow."""
    im = Image.new('RGB', (W, H), (60, 64, 70))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(20, 22, 24), width=6)
    d.polygon(((40, 128), (130, 60), (130, 104), (216, 104), (216, 152), (130, 152), (130, 196)), fill=(236, 200, 40))
    save(im, name)


def main():
    plate('sm_plate')
    engine_cover('sm_engine')
    tank_label('sm_tank')
    hazard('sm_hazard')
    ruler('sm_ruler')
    log_stop('sm_stop')


if __name__ == '__main__':
    main()
