"""
The SINGLE items of the building materials that only had packs, and the meshes of the packs that had none. Procedural models in headless Blender
(free, local, low-poly), manifests and READMEs; icons afterwards.

    blender --background --python tools/make_building_singles.py                  (everything)
    blender --background --python tools/make_building_singles.py -- deck_screw    (only the ids named)
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png        (every item below)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

  singles   framing_nail, finishing_nail, deck_screw (one nail, one screw: not a box of them), lag_bolt, anchor_bolt, joist_hanger, sheet_drywall, sheet_osb,
            lumber_board_2x6, building_rebar_steel_bar
  packs     sheet_drywall_stack_small / _large (10 / 25 sheets), sheet_osb_stack_small / _large (10 / 25), lumber_bundle_2x6_small / _large (10 / 25 boards),
            building_rebar_steel_bundle (10 bars), item_hardware_rebarbundle (25 bars)

A pack weighs its singles times 1.05 and costs them times 0.9 (as tools/make_building_packs.py does). An item that is already in the kit keeps everything
else in its manifest. The equivalencies (~framing_nails, ~finishing_nails, ~deck_screws, ~lag_bolts, ~anchor_bolts, ~joist_hangers, ~drywall, ~osb, ~lumber_2x6, ~rebar: the single is worth 1) are
saved through the kit.

Pivot at the middle of the footprint with the bottom at z = 0; long things lie along X.
The three rebar icons are rendered from a short (0.42 m) section of the same bars (set BAR_L before building): a 3 m bar is a hairline at icon size.
"""
import copy
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_building_items as mod  # noqa: E402
import make_building_packs as packs  # noqa: E402

base = mod.base
M = base.material
BUILD = mod.BUILD

SHEET_W, SHEET_D = 1.2, 2.4
DRYWALL_T, OSB_T = 0.0127, 0.011
DRYWALL_RGB, DRYWALL_EDGE = (0.87, 0.87, 0.84), (0.25, 0.4, 0.62)
OSB_RGB, OSB_EDGE = (0.77, 0.61, 0.37), (0.3, 0.5, 0.36)
BOARD_L, BOARD_W, BOARD_T = 2.4, 0.14, 0.038
TIMBER = (0.78, 0.63, 0.41)
BAR_L, BAR_R = 3.0, 0.0064
STEEL = (0.34, 0.27, 0.23)


def xring(b, x0, x1, y, z, radius, m, sides=8, radius1=None):
    """A short cylinder along X (Builder.log skips anything under 2 cm: a nut, a washer, a rib, a turn of thread). With `radius1` it tapers to
    that radius at x1 (a nail's point, a screw's countersunk head)."""
    i = b.mat_index(m)
    r1 = radius if radius1 is None else radius1
    ra = [b.bm.verts.new((x0, y + radius * math.cos(2 * math.pi * k / sides), z + radius * math.sin(2 * math.pi * k / sides))) for k in range(sides)]
    rb = [b.bm.verts.new((x1, y + r1 * math.cos(2 * math.pi * k / sides), z + r1 * math.sin(2 * math.pi * k / sides))) for k in range(sides)]
    faces = [b.bm.faces.new((ra[k], ra[(k + 1) % sides], rb[(k + 1) % sides], rb[k])) for k in range(sides)]
    faces += [b.bm.faces.new(ra[::-1]), b.bm.faces.new(rb)]
    for f in faces:
        f.material_index = i


# ------------------------------------------------------------------ singles

def anchor_bolt():
    """An L-shaped anchor bolt lying on the ground: the threaded end with its washer and nut, the hook at the other end."""
    b = base.Builder('anchor_bolt')
    zinc = M('Galvanised', (0.66, 0.68, 0.7), 0.4)
    dark = M('Thread', (0.5, 0.52, 0.54), 0.5)
    r = 0.0064
    z = 0.014
    b.log((-0.125, 0.0, z), (0.125, 0.0, z), r, zinc, sides=8)                    # the shank
    b.log((0.125, 0.0, z), (0.125, 0.06, z), r, zinc, sides=8)                    # the hook
    for k in range(6):                                                            # the thread, as rings
        x = -0.12 + k * 0.012
        xring(b, x, x + 0.005, 0.0, z, r * 1.18, dark)
    xring(b, -0.07, -0.058, 0.0, z, 0.012, zinc, sides=6)                         # the nut
    xring(b, -0.056, -0.053, 0.0, z, 0.014, zinc, sides=10)                       # the washer
    return b


def nail(name, length, shank, head, rgb, rings=0):
    """One nail lying on the ground: the head, the shank and the point. `rings`: the grip rings under the head of a framing nail."""
    b = base.Builder(name)
    steel = M('NailSteel', rgb, 0.4)
    z = head
    x0 = -length / 2
    xring(b, x0, x0 + max(0.0012, head * 0.25), 0.0, z, head, steel, sides=10)                      # the head
    xring(b, x0, length / 2 - shank * 5, 0.0, z, shank, steel)                                       # the shank
    xring(b, length / 2 - shank * 5, length / 2, 0.0, z, shank, steel, radius1=shank * 0.08)         # the point
    for k in range(rings):
        x = x0 + 0.012 + k * 0.004
        xring(b, x, x + 0.002, 0.0, z, shank * 1.22, steel)
    return b


def deck_screw():
    """One coated deck screw lying on the ground: a countersunk head with its drive recess, a smooth neck, the thread and the point."""
    b = base.Builder('deck_screw')
    coat = M('ScrewCoating', (0.35, 0.42, 0.3), 0.45)
    dark = M('ScrewRecess', (0.1, 0.11, 0.1), 0.6)
    length, shank, head = 0.075, 0.0021, 0.0045
    z = head
    x0 = -length / 2
    xring(b, x0, x0 + 0.001, 0.0, z, head, coat, sides=10)                                           # the rim of the head
    xring(b, x0 + 0.001, x0 + 0.0045, 0.0, z, head, coat, sides=10, radius1=shank)                    # the countersink
    xring(b, x0 - 0.0003, x0, 0.0, z, head * 0.45, dark, sides=6)                                    # the drive recess
    xring(b, x0 + 0.0045, length / 2 - 0.008, 0.0, z, shank, coat)                                   # the shank
    xring(b, length / 2 - 0.008, length / 2, 0.0, z, shank, coat, radius1=shank * 0.08)              # the point
    n = 16
    for k in range(n):                                                                               # the thread, as rings
        x = x0 + 0.022 + k * (length - 0.032) / n
        xring(b, x, x + 0.0012, 0.0, z, shank * 1.45, coat)
    return b


def lag_bolt():
    """One lag bolt (lag screw) lying on the ground: a hex head with its washer, a smooth shank, a coarse thread and the point."""
    b = base.Builder('lag_bolt')
    zinc = M('Galvanised', (0.66, 0.68, 0.7), 0.4)
    dark = M('Thread', (0.5, 0.52, 0.54), 0.5)
    length, shank, head = 0.1, 0.0048, 0.0085
    z = head * 1.3
    x0 = -length / 2
    xring(b, x0, x0 + 0.0065, 0.0, z, head, zinc, sides=6)                                           # the hex head
    xring(b, x0 + 0.0065, x0 + 0.0085, 0.0, z, head * 1.3, zinc, sides=12)                            # the washer
    xring(b, x0 + 0.0085, length / 2 - 0.012, 0.0, z, shank, zinc)                                   # the shank
    xring(b, length / 2 - 0.012, length / 2, 0.0, z, shank, zinc, radius1=shank * 0.1)               # the point
    n = 11
    for k in range(n):                                                                               # the thread, as rings
        x = x0 + 0.04 + k * (length - 0.052) / n
        xring(b, x, x + 0.002, 0.0, z, shank * 1.35, dark)
    return b


def joist_hanger():
    """A galvanised face-mount joist hanger standing on its seat: the U the joist sits in and the two nailing flanges."""
    b = base.Builder('joist_hanger')
    zinc = M('Galvanised', (0.7, 0.72, 0.74), 0.35)
    hole = M('NailHole', (0.2, 0.2, 0.21), 0.6)
    w, h, d, t = 0.04, 0.13, 0.05, 0.002
    b.box(-w / 2, w / 2, 0.0, d, 0.0, t, zinc)                                     # the seat
    for s in (-1, 1):
        x = s * w / 2
        b.box(min(x, x + s * t), max(x, x + s * t), 0.0, d, 0.0, h, zinc)          # a side of the U
        b.box(min(x, x + s * 0.036), max(x, x + s * 0.036), -t, 0.0, 0.0, h, zinc)  # its flange, against the header
        for k in range(4):                                                         # the nail holes
            zc = 0.02 + k * 0.03
            xc = x + s * 0.018
            b.box(xc - 0.004, xc + 0.004, -t - 0.0006, -t, zc - 0.004, zc + 0.004, hole)
        for k in range(2):
            zc = 0.035 + k * 0.05
            b.box(min(x, x + s * t) - (0.0006 if s < 0 else 0.0), max(x, x + s * t) + (0.0006 if s > 0 else 0.0), 0.02, 0.028, zc - 0.004, zc + 0.004, hole)
    return b


def sheet(name, t, rgb, edge, lines):
    """One sheet lying flat: the sheet, a coloured band along its two short ends (the factory edge tape / edge seal) and, on OSB, the nailing lines."""
    b = base.Builder(name)
    b.box(-SHEET_W / 2, SHEET_W / 2, -SHEET_D / 2, SHEET_D / 2, 0.0, t, M('Sheet', rgb, 0.8))
    em = M('Edge', edge, 0.7)
    for y0, y1 in ((-SHEET_D / 2 - 0.002, -SHEET_D / 2 + 0.03), (SHEET_D / 2 - 0.03, SHEET_D / 2 + 0.002)):
        b.box(-SHEET_W / 2 - 0.002, SHEET_W / 2 + 0.002, y0, y1, -0.0005, t + 0.001, em)
    if lines:
        lm = M('NailLine', tuple(c * 0.72 for c in rgb), 0.8)
        for k in range(1, 3):
            x = -SHEET_W / 2 + SHEET_W * k / 3
            b.box(x - 0.004, x + 0.004, -SHEET_D / 2 + 0.03, SHEET_D / 2 - 0.03, t, t + 0.001, lm)
        for k in range(1, 6):
            y = -SHEET_D / 2 + SHEET_D * k / 6
            b.box(-SHEET_W / 2, SHEET_W / 2, y - 0.004, y + 0.004, t, t + 0.001, lm)
    return b


def board_2x6():
    b = base.Builder('lumber_board_2x6')
    b.box(-BOARD_L / 2, BOARD_L / 2, -BOARD_W / 2, BOARD_W / 2, 0.0, BOARD_T, M('Timber', TIMBER, 0.85))
    end = M('EndGrain', tuple(c * 0.8 for c in TIMBER), 0.9)
    for x0, x1 in ((-BOARD_L / 2 - 0.001, -BOARD_L / 2 + 0.004), (BOARD_L / 2 - 0.004, BOARD_L / 2 + 0.001)):
        b.box(x0, x1, -BOARD_W / 2 - 0.0005, BOARD_W / 2 + 0.0005, -0.0005, BOARD_T + 0.0005, end)
    gm = M('Grain', tuple(c * 0.9 for c in TIMBER), 0.85)
    for y in (-0.035, 0.02, 0.05):                                                  # a few grain lines along the face
        b.box(-BOARD_L / 2 + 0.05, BOARD_L / 2 - 0.05, y - 0.002, y + 0.002, BOARD_T, BOARD_T + 0.0008, gm)
    return b


def rebar_bar():
    """One ribbed bar lying on the ground."""
    b = base.Builder('building_rebar_steel_bar')
    steel = M('Rebar', STEEL, 0.75)
    rib = M('RebarRib', tuple(c * 0.85 for c in STEEL), 0.75)
    b.log((-BAR_L / 2, 0.0, BAR_R * 1.25), (BAR_L / 2, 0.0, BAR_R * 1.25), BAR_R, steel, sides=8)
    n = 30
    for k in range(n):
        x = -BAR_L / 2 + BAR_L * (k + 0.5) / n
        xring(b, x - 0.006, x + 0.006, 0.0, BAR_R * 1.25, BAR_R * 1.25, rib)
    return b


# ------------------------------------------------------------------ packs

def rebar_bundle(name, rows):
    """Bars tied in a bundle: `rows` lists how many bars lie in each layer, bottom first."""
    b = base.Builder(name)
    steel = M('Rebar', STEEL, 0.75)
    wire = M('TieWire', (0.12, 0.12, 0.13), 0.5)
    d = BAR_R * 2 * 1.08
    top = 0.0
    width = max(rows) * d
    for k, count in enumerate(rows):
        z = BAR_R + k * d * 0.87
        for i in range(count):
            y = (i - (count - 1) / 2) * d
            b.log((-BAR_L / 2, y, z), (BAR_L / 2, y, z), BAR_R, steel, sides=6)
        top = z + BAR_R
    for x in (-BAR_L * 0.38, 0.0, BAR_L * 0.38):                                    # three wire ties round the bundle
        b.box(x - 0.006, x + 0.006, -width / 2 - 0.003, width / 2 + 0.003, -0.0005, top + 0.003, wire)
    return b


ITEMS = [
    # id, name, description, builder, weight kg, price, stack size
    ('anchor_bolt', 'Anchor Bolt', 'A 1/2 inch galvanised anchor bolt with its nut and washer, for bolting a sill plate to the foundation.', anchor_bolt, 0.4, 3, 50),
    ('framing_nail', 'Framing Nail', 'A 90 mm framing nail for stud walls, joists and rafters.',
     lambda: nail('framing_nail', 0.09, 0.0019, 0.0042, (0.62, 0.63, 0.65), rings=6), 0.02, 1, 99),
    ('finishing_nail', 'Finishing Nail', 'A slim 60 mm finishing nail with a small head, for trim, casing and moulding.',
     lambda: nail('finishing_nail', 0.06, 0.0011, 0.0019, (0.7, 0.71, 0.73)), 0.01, 1, 99),
    ('deck_screw', 'Deck Screw', 'A 75 mm coated deck screw for decking, sheathing and exterior work.', deck_screw, 0.02, 1, 99),
    ('lag_bolt', 'Lag Bolt', 'A 3/8 inch by 100 mm galvanised lag bolt with a hex head, for ledgers, posts and heavy timber.', lag_bolt, 0.07, 2, 50),
    ('joist_hanger', 'Joist Hanger', 'A galvanised face-mount joist hanger for a 2x joist.', joist_hanger, 0.3, 4, 50),
    ('sheet_drywall', 'Drywall Sheet', 'A 1.2 m by 2.4 m sheet of 12.7 mm drywall.', lambda: sheet('sheet_drywall', DRYWALL_T, DRYWALL_RGB, DRYWALL_EDGE, False), 22.0, 12, 10),
    ('sheet_osb', 'OSB Sheet', 'A 1.2 m by 2.4 m sheet of 11 mm OSB sheathing.', lambda: sheet('sheet_osb', OSB_T, OSB_RGB, OSB_EDGE, True), 20.0, 14, 10),
    ('lumber_board_2x6', '2x6 Lumber Board', 'A 2x6 framing board, 2.4 m long.', board_2x6, 6.5, 7, 20),
    ('building_rebar_steel_bar', 'Rebar Bar', 'A 3 m length of 12 mm ribbed steel rebar.', rebar_bar, 2.7, 6, 20),
]

# id, name, description, builder, the single it is made of, how many, stack size
PACKS = [
    ('sheet_drywall_stack_small', 'Small Drywall Stack (10)', 'A strapped stack of ten drywall sheets.',
     lambda: packs.stack_sheets('sheet_drywall_stack_small', SHEET_W, SHEET_D, 10, DRYWALL_T, DRYWALL_RGB, DRYWALL_EDGE), 'sheet_drywall', 10, 5),
    ('sheet_drywall_stack_large', 'Large Drywall Stack (25)', 'A strapped stack of 25 drywall sheets on a pallet.',
     lambda: packs.stack_sheets('sheet_drywall_stack_large', SHEET_W, SHEET_D, 25, DRYWALL_T, DRYWALL_RGB, DRYWALL_EDGE), 'sheet_drywall', 25, 2),
    ('sheet_osb_stack_small', 'Small OSB Stack (10)', 'A strapped stack of ten OSB sheathing sheets.',
     lambda: packs.stack_sheets('sheet_osb_stack_small', SHEET_W, SHEET_D, 10, OSB_T, OSB_RGB, OSB_EDGE), 'sheet_osb', 10, 5),
    ('sheet_osb_stack_large', 'Large OSB Stack (25)', 'A strapped stack of 25 OSB sheathing sheets.',
     lambda: packs.stack_sheets('sheet_osb_stack_large', SHEET_W, SHEET_D, 25, OSB_T, OSB_RGB, OSB_EDGE), 'sheet_osb', 25, 2),
    ('lumber_bundle_2x6_small', 'Small 2x6 Bundle (10)', 'A strapped bundle of ten 2x6 framing boards, 2.4 m long.',
     lambda: packs.lumber_bundle('lumber_bundle_2x6_small', 2, 5, BOARD_L, BOARD_W, BOARD_T, TIMBER), 'lumber_board_2x6', 10, 5),
    ('lumber_bundle_2x6_large', 'Large 2x6 Bundle (25)', 'A strapped bundle of 25 2x6 framing boards, 2.4 m long.',
     lambda: packs.lumber_bundle('lumber_bundle_2x6_large', 5, 5, BOARD_L, BOARD_W, BOARD_T, TIMBER), 'lumber_board_2x6', 25, 2),
    ('building_rebar_steel_bundle', 'Rebar Bundle (10)', 'Ten 3 m bars of 12 mm ribbed steel rebar, tied with wire.',
     lambda: rebar_bundle('building_rebar_steel_bundle', [4, 3, 2, 1]), 'building_rebar_steel_bar', 10, 10),
    ('item_hardware_rebarbundle', 'Large Rebar Bundle (25)', '25 3 m bars of 12 mm ribbed steel rebar, tied with wire.',
     lambda: rebar_bundle('item_hardware_rebarbundle', [7, 6, 5, 4, 3]), 'building_rebar_steel_bar', 25, 4),
]


def write(item_id, name, desc, build, weight, price, stack, tmpl, note):
    mod.reset()
    res = build()
    b, extra = res if isinstance(res, tuple) else (res, None)
    folder = os.path.join(BUILD, item_id)
    os.makedirs(folder, exist_ok=True)
    tris, (sx, sy, sz) = mod.export(b, extra, folder, item_id)
    path = os.path.join(folder, item_id + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))        # already in the kit: it keeps its other fields
    else:
        m = copy.deepcopy(tmpl)
        m['id'] = item_id
        m['icon'] = item_id + '.png'
    m['name'] = name
    m['description'] = desc
    m['properties'].update({'weight_kg': weight, 'max_stack_size': stack, 'base_value': price, 'placeable': True})
    m['models'] = [{'file': item_id + '.glb', 'format': 'glb', 'dimensions_m': {'x': sx, 'y': sz, 'z': sy}, 'triangles': tris}]
    m.pop('dimensions', None)
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': sx, 'depth': sy, 'height': sz})
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2)
    with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s\n\n%s\n\nProcedural model (tools/make_building_singles.py), %d triangles. %s\n' % (name, desc, tris, note))
    print('item', item_id, '|', name, '|', tris, 'tris', sx, sy, sz, '|', weight, 'kg', price)


def main():
    tmpl = json.load(open(os.path.join(BUILD, 'building_glass', 'building_glass.json'), encoding='utf-8'))
    only = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else None
    single = {}
    for item_id, name, desc, build, weight, price, stack in ITEMS:
        single[item_id] = (weight, price)
        if only is not None and item_id not in only:
            continue
        write(item_id, name, desc, build, weight, price, stack, tmpl, 'The single item: worth 1 in its equivalency.')
    for item_id, name, desc, build, of, count, stack in PACKS:
        if only is not None and item_id not in only:
            continue
        w, p = single[of]
        write(item_id, name, desc, build, round(w * count * 1.05, 1), round(p * count * 0.9), stack, tmpl, '%d of `%s`.' % (count, of))


if __name__ == '__main__':
    main()
