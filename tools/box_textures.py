"""
Textured cardboard boxes: the atlas of a box (one picture for all six faces: kraft cardboard, a colour band and a white label with the NAME of what is in it,
a taped seam across the top) and the layout of its faces in that picture. Pure Python; PIL is only needed to draw (make_atlas), so Blender can use layout().

    layout(w, d, h)          -> {'size': (px_w, px_h), 'faces': {name: (x, y, w, h)}} in pixels, origin top left
    make_atlas(spec)         -> a PIL image
spec: dict(w, d, h metres, name 'ROOFING NAILS', note 'BOX', band (r, g, b) 0..1)
"""
import os

KRAFT = (181, 142, 82)
FONT = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'arialbd.ttf')


def layout(w, d, h, px_per_m=None):
    """Front and back (w x h) side by side, left and right (d x h) under them, top and bottom (w x d) under those."""
    s = px_per_m or 1024.0 / w
    pw, pd, ph = int(round(w * s)), int(round(d * s)), int(round(h * s))
    faces = {
        'front': (0, 0, pw, ph), 'back': (pw, 0, pw, ph),
        'left': (0, ph, pd, ph), 'right': (pd, ph, pd, ph),
        'top': (0, 2 * ph, pw, pd), 'bottom': (pw, 2 * ph, pw, pd),
    }
    return {'size': (2 * pw, 2 * ph + pd), 'faces': faces}


def _font(size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()


def _fit(draw, text, box_w, box_h, start):
    """The largest font size (from start down) at which the text fits the box."""
    size = start
    while size > 8:
        f = _font(size)
        b = draw.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= box_w and b[3] - b[1] <= box_h:
            return f, b
        size -= 2
    f = _font(8)
    return f, draw.textbbox((0, 0), text, font=f)


def _wrap(draw, text, box_w, box_h, start):
    """The name on one line when it fits big enough, otherwise on two (split at the space that balances the lines)."""
    f, b = _fit(draw, text, box_w, box_h, start)
    words = text.split()
    if len(words) < 2 or (b[3] - b[1]) > box_h * 0.38:
        return [text], f
    best = None
    for i in range(1, len(words)):
        a, c = ' '.join(words[:i]), ' '.join(words[i:])
        f2, _ = _fit(draw, max(a, c, key=len), box_w, box_h / 2.2, start)
        size = f2.size if hasattr(f2, 'size') else 8
        if best is None or size > best[0]:
            best = (size, [a, c], f2)
    if best and best[0] > f.size * 1.15:
        return best[1], best[2]
    return [text], f


def _label_face(img, rect, spec, big=True):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    band = tuple(int(c * 255) for c in spec['band'])
    pad = int(h * 0.12)
    d.rectangle([x + int(w * 0.03), y + int(h * 0.17), x + w - int(w * 0.03), y + h - int(h * 0.17)], fill=band)                    # the colour band
    lx0, ly0, lx1, ly1 = x + int(w * 0.07), y + int(h * 0.26), x + w - int(w * 0.07), y + h - int(h * 0.26)
    d.rectangle([lx0, ly0, lx1, ly1], fill=(244, 243, 236), outline=(60, 50, 40), width=max(1, int(h * 0.012)))                    # the white label
    inner_w, inner_h = lx1 - lx0 - 2 * pad, ly1 - ly0 - pad
    note = spec.get('note')
    lines, f = _wrap(d, spec['name'], inner_w, inner_h * (0.62 if note else 0.9), int(inner_h * 0.8))
    heights = [d.textbbox((0, 0), ln, font=f)[3] - d.textbbox((0, 0), ln, font=f)[1] for ln in lines]
    nf = _font(max(8, int(inner_h * 0.17))) if note else None
    nh = (d.textbbox((0, 0), note, font=nf)[3] - d.textbbox((0, 0), note, font=nf)[1]) if note else 0
    total = sum(heights) + int(heights[0] * 0.25) * (len(lines) - 1) + (nh + int(nh * 0.7) if note else 0)
    cy = ly0 + (ly1 - ly0 - total) // 2
    for ln, lh in zip(lines, heights):
        b = d.textbbox((0, 0), ln, font=f)
        d.text((lx0 + (lx1 - lx0 - (b[2] - b[0])) // 2 - b[0], cy - b[1]), ln, font=f, fill=(25, 25, 28))
        cy += lh + int(heights[0] * 0.25)
    if note:
        b = d.textbbox((0, 0), note, font=nf)
        d.text((lx0 + (lx1 - lx0 - (b[2] - b[0])) // 2 - b[0], cy + int(nh * 0.45) - b[1]), note, font=nf, fill=(90, 80, 70))


def make_atlas(spec):
    import random
    from PIL import Image, ImageDraw
    lay = layout(spec['w'], spec['d'], spec['h'])
    W, H = lay['size']
    img = Image.new('RGB', (W, H), KRAFT)
    d = ImageDraw.Draw(img)
    rng = random.Random(spec['name'])
    for name, (x, y, w, h) in lay['faces'].items():           # kraft cardboard: faint flutes and speckle
        for k in range(0, w, 6):
            shade = rng.randint(-5, 5)
            d.line([(x + k, y), (x + k, y + h)], fill=tuple(max(0, min(255, c + shade)) for c in KRAFT), width=3)
        d.rectangle([x, y, x + w - 1, y + h - 1], outline=(150, 115, 65), width=2)
    tape = (206, 178, 120)
    seam = (120, 95, 55)
    # top: the flaps meet across the middle under a strip of packing tape
    x, y, w, h = lay['faces']['top']
    th = int(h * 0.2)
    d.rectangle([x, y + h // 2 - th // 2, x + w, y + h // 2 + th // 2], fill=tape, outline=(170, 140, 90), width=2)
    d.line([(x, y + h // 2), (x + w, y + h // 2)], fill=seam, width=2)
    # the tape runs on down the short sides, and a little over the top edge of the long sides
    for face in ('left', 'right'):
        fx, fy, fw, fh = lay['faces'][face]
        d.rectangle([fx + fw // 2 - th // 2, fy, fx + fw // 2 + th // 2, fy + int(fh * 0.22)], fill=tape, outline=(170, 140, 90), width=2)
    for face in ('front', 'back'):
        _label_face(img, lay['faces'][face], spec)
    for face in ('left', 'right'):
        _label_face(img, lay['faces'][face], dict(spec, note=None))
    # the bottom: just cardboard with the flap seam
    x, y, w, h = lay['faces']['bottom']
    d.line([(x, y + h // 2), (x + w, y + h // 2)], fill=seam, width=2)
    return img
