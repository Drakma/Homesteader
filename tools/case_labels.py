"""
The printed label of a cardboard case: the product's name and "x<count>" (PVC TEE FITTING x10), on all four sides of the box.

    python tools/case_labels.py            paints every label (PIL) into assets/_scratch/case_labels/<case id>.png, and the tank stickers
    then build the cases: blender --background --python tools/make_fitting_cases.py ; ... tools/make_tape_cases.py

Two halves, because Blender's Python has no PIL: paint() runs in the system Python, add() runs inside Blender (the case builders call it) and
puts the picture on four quads, one on each wall. A case with no painted label is left with bare cardboard.

User rule: a case, box or pack carries its product name; the count is written x10, not "Case of 10".
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = os.path.join(ROOT, 'assets', '_scratch', 'case_labels')
GAME_STICKERS = os.path.join(ROOT, 'Homesteader', 'Assets', 'Resources', 'TankStickers')     # one picture per liquid, swapped in at run time
PX = (640, 240)                     # the picture; ASPECT is its shape on the box
ASPECT = PX[0] / PX[1]

# single: (label colour, the counts)
CASES = {
    'pipe_pvc_elbow': ((0.15, 0.3, 0.6), (10, 20)),
    'pipe_pvc_tee': ((0.15, 0.3, 0.6), (10, 20)),
    'building_valve_ball_pvc': ((0.8, 0.12, 0.1), (10, 20)),
    'building_pvc_cement_can': ((0.85, 0.5, 0.08), (6, 12)),
    'building_pvc_primer_can': ((0.5, 0.2, 0.62), (6, 12)),
    'building_insulation_spray_foam': ((0.2, 0.3, 0.55), (8, 16)),
    'building_weatherstripping_roll': ((0.2, 0.45, 0.3), (6, 12)),
    'building_drywall_tape_roll': ((0.15, 0.3, 0.6), (6, 12)),
}


def paint(case, name, count, rgb):
    """White label, a colour band down the left, the name in capitals (one or two lines) and the count."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = PX
    col = tuple(int(c * 255) for c in rgb)
    im = Image.new('RGB', PX, (247, 247, 243))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 44, H), fill=col)
    d.rectangle((0, 0, W - 1, H - 1), outline=col, width=6)
    font = lambda size: ImageFont.truetype('arialbd.ttf', size)
    words = name.upper().split()
    lines = [' '.join(words)]
    room = W - 44 - 200
    if d.textlength(lines[0], font=font(64)) > room and len(words) > 1:        # too long for one line: break it where the halves are most even
        k = min(range(1, len(words)), key=lambda i: abs(len(' '.join(words[:i])) - len(' '.join(words[i:]))))
        lines = [' '.join(words[:k]), ' '.join(words[k:])]
    size = 96 if len(lines) == 1 else 76
    while max(d.textlength(t, font=font(size)) for t in lines) > room:
        size -= 2
    y = (H - size * len(lines) - 12 * (len(lines) - 1)) / 2 - 6
    for t in lines:
        d.text((66, y), t, fill=(28, 28, 30), font=font(size))
        y += size + 12
    tag = 'x%d' % count
    d.text((W - 26 - d.textlength(tag, font=font(104)), (H - 104) / 2 - 10), tag, fill=col, font=font(104))
    os.makedirs(LABELS, exist_ok=True)
    im.save(os.path.join(LABELS, case + '.png'))


def add(obj, case, size, fill=0.8):
    """Inside Blender: puts the case's label on its four walls (size = the box's width, depth, height) and joins it to `obj`."""
    import bmesh
    import bpy
    path = os.path.join(LABELS, case + '.png')
    if not os.path.exists(path):
        print('no label painted for', case, '(python tools/case_labels.py)')
        return obj
    W, D, H = size
    m = bpy.data.materials.new('CaseLabel')
    m.use_nodes = True
    tex = m.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path)
    tex.image.pack()
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.7
    m.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    e = 0.0012
    zc = H * 0.5
    # each wall: its middle, the direction that is "right" for someone looking at it, how wide it is
    for mid, right, wide in (((0, -D / 2 - e), (1, 0), W), ((0, D / 2 + e), (-1, 0), W), ((W / 2 + e, 0), (0, 1), D), ((-W / 2 - e, 0), (0, -1), D)):
        lh = min(H * 0.9, wide * fill / ASPECT)
        lw = lh * ASPECT
        pts = [(mid[0] + right[0] * sx * lw / 2, mid[1] + right[1] * sx * lw / 2, zc + sz * lh / 2) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        f = bm.faces.new([bm.verts.new(p) for p in pts])
        for loop, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uv].uv = t
    me = bpy.data.meshes.new('label')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    lab = bpy.data.objects.new('label', me)
    bpy.context.collection.objects.link(lab)
    if not obj.data.uv_layers:                       # (joining into a mesh with no UV map loses the label's)
        obj.data.uv_layers.new(name='UVMap')
    bpy.ops.object.select_all(action='DESELECT')
    lab.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    return obj


# a tank's sticker: (the big word, the small line, colour)
STICKERS = {
    'tank_propane': ('PROPANE', 'FLAMMABLE GAS   NO SMOKING', (0.8, 0.1, 0.08)),
    'tank_fuel': ('FUEL', 'FLAMMABLE   NO SMOKING', (0.1, 0.1, 0.11)),      # (a bulk tank takes diesel or gasoline: in the game the sticker names which)
}


def paint_sticker(name, title, sub, rgb, folder=None, diamond=True):
    """A warning sticker: a hazard diamond at the left, the big word, a small line under it."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = PX
    col = tuple(int(c * 255) for c in rgb)
    im = Image.new('RGB', PX, (250, 250, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=col, width=8)
    if diamond:
        cx, cy, r = 110, H // 2, 78
        d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=(214, 30, 24), outline=(20, 20, 20))
        d.polygon([(cx, cy - 34), (cx + 20, cy + 6), (cx + 8, cy + 30), (cx - 8, cy + 30), (cx - 20, cy + 6)], fill=(250, 250, 246))       # a flame
    font = lambda size: ImageFont.truetype('arialbd.ttf', size)
    left = 214 if diamond else 40
    room = W - left - 32
    size = 100
    while d.textlength(title, font=font(size)) > room:
        size -= 2
    d.text((left, H / 2 - size - 2 if sub else (H - size) / 2 - 10), title, fill=col, font=font(size))
    small = 34
    while d.textlength(sub, font=font(small)) > room:
        small -= 1
    d.text((left + 2, H / 2 + 26), sub, fill=(28, 28, 30), font=font(small))
    os.makedirs(folder or LABELS, exist_ok=True)
    im.save(os.path.join(folder or LABELS, name + '.png'))


def add_tank_sticker(obj, name, radius, zc, height, x_mid=0.0, steps=6):
    """Inside Blender: wraps the sticker on both sides of a tank lying along x (its axis at height zc), curved to the tank, and joins it to `obj`."""
    import math
    import bmesh
    import bpy
    path = os.path.join(LABELS, name + '.png')
    if not os.path.exists(path):
        print('no sticker painted:', name, '(python tools/case_labels.py)')
        return obj
    m = bpy.data.materials.new('TankSticker')
    m.use_nodes = True
    tex = m.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path)
    tex.image.pack()
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.6
    m.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    width = height * ASPECT
    rr = radius + 0.003
    span = height / radius                             # the angle the sticker covers round the tank
    for side in (-1, 1):                               # -1: the -y side (read from the front), 1: the +y side
        xl, xr = x_mid * -side - side * -width / 2, x_mid * -side + side * -width / 2      # the reader's left and right
        for k in range(steps):
            a0, a1 = -span / 2 + span * k / steps, -span / 2 + span * (k + 1) / steps
            ring = lambda x, a: (x, side * rr * math.cos(a), zc + rr * math.sin(a))
            f = bm.faces.new([bm.verts.new(q) for q in (ring(xl, a0), ring(xr, a0), ring(xr, a1), ring(xl, a1))])
            for loop, t in zip(f.loops, ((0, k / steps), (1, k / steps), (1, (k + 1) / steps), (0, (k + 1) / steps))):
                loop[uv].uv = t
    me = bpy.data.meshes.new('sticker')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    lab = bpy.data.objects.new('sticker', me)
    bpy.context.collection.objects.link(lab)
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name='UVMap')
    bpy.ops.object.select_all(action='DESELECT')
    lab.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    return obj


def add_flat(obj, name, quads):
    """Inside Blender: puts the painted picture `name` on flat quads (each: bottom left, bottom right, top right, top left, as its reader sees
    it) and joins them to `obj`."""
    import bmesh
    import bpy
    path = os.path.join(LABELS, name + '.png')
    if not os.path.exists(path):
        print('no label painted:', name, '(python tools/case_labels.py)')
        return obj
    m = bpy.data.materials.new('Picture_' + name)
    m.use_nodes = True
    tex = m.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path)
    tex.image.pack()
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.6
    m.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    for q in quads:
        f = bm.faces.new([bm.verts.new(c) for c in q])
        for loop, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uv].uv = t
    me = bpy.data.meshes.new('plate')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    lab = bpy.data.objects.new('plate', me)
    bpy.context.collection.objects.link(lab)
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name='UVMap')
    bpy.ops.object.select_all(action='DESELECT')
    lab.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    return obj


def paint_generator_panel(name, watts):
    """A portable generator's control panel as a picture: two duplex outlets, a twist-lock outlet, the engine switch, two breakers, a voltmeter,
    the rating."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 640, 400
    im = Image.new('RGB', (W, H), (38, 40, 44))
    d = ImageDraw.Draw(im)
    font = lambda size: ImageFont.truetype('arialbd.ttf', size)
    d.rounded_rectangle((6, 6, W - 7, H - 7), radius=14, outline=(120, 122, 126), width=4)
    for x, y in ((22, 22), (W - 34, 22), (22, H - 34), (W - 34, H - 34)):                 # the four screws
        d.ellipse((x, y, x + 12, y + 12), fill=(150, 152, 156))
    d.text((34, 26), '%dW' % watts, fill=(245, 245, 240), font=font(46))
    d.text((34, 78), '120V / 240V AC   60Hz', fill=(190, 192, 196), font=font(18))
    for k in range(2):                                                                    # the duplex outlets
        x0 = 40 + k * 130
        d.rounded_rectangle((x0, 130, x0 + 100, 330), radius=12, fill=(225, 225, 220), outline=(90, 90, 92), width=3)
        for y0 in (150, 245):
            d.rounded_rectangle((x0 + 18, y0, x0 + 82, y0 + 66), radius=10, fill=(245, 245, 240), outline=(120, 120, 122), width=2)
            d.rectangle((x0 + 34, y0 + 14, x0 + 39, y0 + 38), fill=(30, 30, 32))
            d.rectangle((x0 + 60, y0 + 14, x0 + 65, y0 + 38), fill=(30, 30, 32))
            d.ellipse((x0 + 44, y0 + 44, x0 + 56, y0 + 56), fill=(30, 30, 32))
    cx, cy, r = 370, 250, 62                                                              # the twist-lock outlet
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(225, 225, 220), outline=(90, 90, 92), width=3)
    d.ellipse((cx - r + 12, cy - r + 12, cx + r - 12, cy + r - 12), fill=(28, 28, 30))
    for a0 in (20, 110, 200, 290):
        d.arc((cx - 34, cy - 34, cx + 34, cy + 34), a0, a0 + 44, fill=(200, 200, 196), width=8)
    d.text((cx - 30, cy + r + 6), '240V 30A', fill=(190, 192, 196), font=font(15))
    d.rounded_rectangle((470, 34, 600, 150), radius=10, fill=(20, 20, 22), outline=(120, 122, 126), width=3)       # the voltmeter
    d.pieslice((486, 60, 584, 158), 200, 340, fill=(235, 235, 228))
    d.line((535, 118, 562, 76), fill=(200, 30, 24), width=4)
    d.text((512, 122), 'VOLTS', fill=(190, 192, 196), font=font(14))
    d.rounded_rectangle((480, 190, 540, 290), radius=8, fill=(20, 20, 22), outline=(120, 122, 126), width=3)        # the engine switch
    d.rectangle((488, 198, 532, 240), fill=(200, 30, 24))
    d.rectangle((488, 242, 532, 282), fill=(60, 60, 62))
    d.text((552, 204), 'ON', fill=(235, 235, 228), font=font(16))
    d.text((552, 254), 'OFF', fill=(235, 235, 228), font=font(16))
    for k in range(2):                                                                    # the breakers
        x0 = 480 + k * 62
        d.ellipse((x0, 316, x0 + 44, 360), fill=(20, 20, 22), outline=(120, 122, 126), width=3)
        d.ellipse((x0 + 12, 328, x0 + 32, 348), fill=(225, 225, 220))
    os.makedirs(LABELS, exist_ok=True)
    im.save(os.path.join(LABELS, name + '.png'))


def paint_perforated(name, rgb=(150, 152, 156)):
    """Perforated steel: a muffler's heat shield."""
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (256, 256), rgb)
    d = ImageDraw.Draw(im)
    for j in range(13):
        for i in range(13):
            x, y = 10 + i * 20 + (10 if j % 2 else 0), 10 + j * 20
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(34, 34, 36))
    d.rectangle((0, 0, 255, 255), outline=(90, 92, 96), width=6)
    os.makedirs(LABELS, exist_ok=True)
    im.save(os.path.join(LABELS, name + '.png'))


def paint_fins(name, rgb=(96, 98, 102)):
    """An engine's cooling fins and a recoil starter's vents: dark slots across cast metal."""
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (256, 256), rgb)
    d = ImageDraw.Draw(im)
    for j in range(12):
        d.rectangle((14, 12 + j * 20, 242, 21 + j * 20), fill=(30, 30, 32))
        d.line((14, 23 + j * 20, 242, 23 + j * 20), fill=(150, 152, 156), width=2)
    os.makedirs(LABELS, exist_ok=True)
    im.save(os.path.join(LABELS, name + '.png'))


def paint_onoff(name):
    """The plate beside a switch handle: ON at the top, OFF at the bottom."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (160, 400), (28, 28, 30))
    d = ImageDraw.Draw(im)
    font = lambda size: ImageFont.truetype('arialbd.ttf', size)
    d.rectangle((4, 4, 155, 395), outline=(200, 200, 196), width=4)
    d.rectangle((14, 14, 145, 150), fill=(200, 30, 24))
    d.text((80 - d.textlength('ON', font=font(64)) / 2, 46), 'ON', fill=(250, 250, 246), font=font(64))
    d.rectangle((14, 250, 145, 385), fill=(40, 120, 60))
    d.text((80 - d.textlength('OFF', font=font(56)) / 2, 286), 'OFF', fill=(250, 250, 246), font=font(56))
    os.makedirs(LABELS, exist_ok=True)
    im.save(os.path.join(LABELS, name + '.png'))


def main():
    paint_sticker('disconnect_label', 'SAFETY SWITCH', 'DANGER   HIGH VOLTAGE', (0.8, 0.1, 0.08))       # the safety disconnect (tools/make_disconnect_switch.py)
    paint_onoff('disconnect_onoff')
    for watts in (5000, 7500):                           # the portable generators' pictures (tools/make_portable_generators.py)
        paint_generator_panel('generator_panel_%d' % watts, watts)
        paint_sticker('generator_tank_%d' % watts, '%dW' % watts, 'PORTABLE GENERATOR', (0.1, 0.1, 0.12), diamond=False)
    paint_perforated('generator_shield')
    paint_fins('generator_fins')
    print('generator pictures painted')
    for amps in (32, 64, 128):                           # the DC breaker boxes' rating labels (tools/make_dc_breaker_boxes.py)
        paint_sticker('breaker_box_dc_%da' % amps, '%dA' % amps, 'DC BREAKER BOX', (0.12, 0.3, 0.62), diamond=False)
        print('label breaker_box_dc_%da' % amps)
    for kw in (10, 14, 28):                              # the standby generators' rating plates (tools/make_generators.py)
        paint_sticker('generator_%dkw' % kw, '%d kW' % kw, 'STANDBY GENERATOR', (0.1, 0.35, 0.2), diamond=False)
        print('plate generator_%dkw' % kw)
    for name, (title, sub, rgb) in STICKERS.items():
        paint_sticker(name, title, sub, rgb)
        print('sticker', name, '|', title)
    # the game's stickers, one per liquid: a tank's sticker names what is in it (Assets/Scripts/Growth/TankSticker.cs)
    for path in sorted(glob.glob(os.path.join(ROOT, 'assets', 'liquids', '*', '*.json'))):
        m = json.load(open(path, encoding='utf-8'))
        flammable = bool((m.get('category_fields') or {}).get('flammable'))
        paint_sticker(m['id'], m['name'].upper(), 'FLAMMABLE   NO SMOKING' if flammable else '', (0.8, 0.1, 0.08) if flammable else (0.1, 0.25, 0.5),
                      folder=GAME_STICKERS, diamond=flammable)
    paint_sticker('empty', 'EMPTY', '', (0.35, 0.35, 0.37), folder=GAME_STICKERS, diamond=False)
    print('game stickers ->', GAME_STICKERS)
    for single, (rgb, counts) in CASES.items():
        found = glob.glob(os.path.join(ROOT, 'assets', '*', single, single + '.json'))
        if not found:
            print('skip (not in the kit):', single)
            continue
        name = json.load(open(found[0], encoding='utf-8'))['name']
        for n in counts:
            paint('%s_case_%d' % (single, n), name, n, rgb)
            print('label', '%s_case_%d' % (single, n), '|', name.upper(), 'x%d' % n)


if __name__ == '__main__':
    main()
