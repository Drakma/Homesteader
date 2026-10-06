"""
Packages and piles of the building materials, with the equivalencies (tag_values in assets/_schemas/material_tags.json) the way the 2x4 lumber has them
(1 large bundle = 2 small = 20 studs): a recipe line "#tag x N" is paid by any mix of members worth N units. Procedural models in headless Blender, manifests,
tags and values; icons afterwards.

    blender --background --python tools/make_building_packs.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png        (every new pack)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

PACKS lists, per pack: id, name, description, builder, weight, stack, price and the tag it belongs to; UNITS says what the tag counts and what each member is worth.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_building_items as mod  # noqa: E402
import make_building_items2 as more  # noqa: E402
import make_structure_stages as base  # noqa: E402

M = base.material


# ------------------------------------------------------------------ shapes

def pallet(b, w, d, top_z=0.0):
    """A wooden pallet under the load (its top at z = 0.14). Returns the height."""
    wood = M('Pallet', (0.62, 0.46, 0.27), 0.9)
    for y in (-d / 2, 0.0, d / 2 - 0.09):
        b.box(-w / 2, w / 2, y, y + 0.09, 0.0, 0.09, wood)                # the three stringers
    for k in range(6):
        y0 = -d / 2 + k * (d - 0.1) / 5
        b.box(-w / 2, w / 2, y0, y0 + 0.1, 0.09, 0.14, wood)              # the deck boards
    return 0.14


def block_pallet(name, nx, ny, layers):
    b = base.Builder(name)
    w, d = nx * 0.4, ny * 0.2
    z = pallet(b, w + 0.04, d + 0.04)
    gray = M('Block', (0.62, 0.62, 0.6), 0.95)
    dark = M('BlockCore', (0.35, 0.35, 0.34), 0.95)
    for k in range(layers):
        for i in range(nx):
            for j in range(ny):
                x0 = -w / 2 + i * 0.4
                y0 = -d / 2 + j * 0.2
                b.box(x0 + 0.003, x0 + 0.397, y0 + 0.003, y0 + 0.197, z + k * 0.2, z + (k + 1) * 0.2 - 0.003, gray)
    for x in (-w * 0.3, w * 0.3):
        b.box(x - 0.012, x + 0.012, -d / 2 - 0.005, d / 2 + 0.005, z + layers * 0.2 - 0.01, z + layers * 0.2 + 0.003, M('Strap', (0.2, 0.25, 0.3), 0.5))
    return b


def bag_pallet(name, rows, cols, layers, body, band):
    b = base.Builder(name)
    bw, bd, bh = 0.62, 0.42, 0.14    # a bag lying flat: 0.62 long, 0.42 wide, 0.14 thick
    w, d = rows * bw, cols * bd
    z = pallet(b, w + 0.04, d + 0.04)
    paper = M('BagPaper', body, 0.9)
    label = M('BagLabel', band, 0.8)
    for k in range(layers):
        for i in range(rows):
            for j in range(cols):
                x0 = -w / 2 + i * bw
                y0 = -d / 2 + j * bd
                b.box(x0 + 0.004, x0 + bw - 0.004, y0 + 0.004, y0 + bd - 0.004, z + k * bh, z + (k + 1) * bh - 0.004, paper)
                if k == layers - 1:
                    b.box(x0 + 0.12, x0 + bw - 0.12, y0 + 0.08, y0 + bd - 0.08, z + (k + 1) * bh - 0.004, z + (k + 1) * bh, label)
    wrap = M('Wrap', (0.85, 0.9, 0.95), 0.2)
    b.box(-w / 2 - 0.006, w / 2 + 0.006, -d / 2 - 0.006, d / 2 + 0.006, z + 0.05, z + layers * bh * 0.95, wrap)      # the shrink wrap, a skin round the stack
    return b


def case(name, w, d, h, body, label, count_label=None):
    b = base.Builder(name)
    b.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, M('Case', body, 0.85))
    more.label_panel(b, w, d, h, label)
    more.tape_seam(b, w, d, h)
    return b


def stack_sheets(name, w, d, count, t, rgb, edge, strap=True):
    b = base.Builder(name)
    h = count * t
    z = pallet(b, w + 0.04, d + 0.04) if count * t > 0.3 else 0.0
    sheet = M('Sheet', rgb, 0.8)
    b.box(-w / 2, w / 2, -d / 2, d / 2, z, z + h, sheet)
    for k in range(1, 6):
        zz = z + h * k / 6
        b.box(-w / 2 - 0.002, w / 2 + 0.002, -d / 2 - 0.002, d / 2 + 0.002, zz - 0.004, zz + 0.004, M('Edge', edge, 0.7))
    if strap:
        sm = M('Strap', (0.2, 0.25, 0.3), 0.5)
        for x in (-w * 0.3, w * 0.3):
            b.box(x - 0.012, x + 0.012, -d / 2 - 0.006, d / 2 + 0.006, z - 0.004, z + h + 0.004, sm)
    return b


def truss_pack(name, span, rise, count):
    """The trusses standing side by side, 0.6 m apart, strapped together with two battens."""
    b = base.Builder(name)
    wood = M('Timber', (0.74, 0.58, 0.36), 0.85)
    plate = M('Plate', (0.55, 0.55, 0.57), 0.5)
    ex = span / 2
    lines = [((-ex, 0.0), (0.0, rise)), ((0.0, rise), (ex, 0.0)), ((-ex, 0.0), (ex, 0.0)), ((0.0, rise), (-ex / 3, 0.0)), ((0.0, rise), (ex / 3, 0.0)),
             ((-ex / 2, rise / 2), (-ex / 3, 0.0)), ((ex / 2, rise / 2), (ex / 3, 0.0))]
    for k in range(count):
        y = (k - (count - 1) / 2) * 0.6
        for (ax, az), (cx, cz) in lines:
            b.log((ax, y, az), (cx, y, cz), 0.045, wood, sides=4)
        b.box(-0.09, 0.09, y - 0.05, y + 0.05, 0.0, 0.07, plate)
        b.box(-0.09, 0.09, y - 0.05, y + 0.05, rise - 0.07, rise + 0.02, plate)
    span_y = (count - 1) * 0.6 + 0.12
    for x in (-ex * 0.5, ex * 0.5):
        z = rise * (1 - abs(x) / ex) + 0.04
        b.box(x - 0.03, x + 0.03, -span_y / 2, span_y / 2, z, z + 0.04, wood)         # a batten tying the stack, across the rafters
    return b


def lumber_bundle(name, nx, nz, length, w, t, rgb):
    return more.bundle(name, nx, nz, length, w, t, rgb)


# ------------------------------------------------------------------ the table

U = {   # per-unit weight (kg), per-unit price
    'rafter': (14.0, 24), 'block': (17.0, 3), 'mortar': (27.0, 14), 'concrete': (36.0, 12), 'foam': (4.0, 36), 'gutter': (3.0, 28), 'soffit': (1.5, 14),
    'fascia': (2.2, 11), 'nails': (5.0, 18), 'anchor': (8.0, 32), 'hanger': (7.0, 40), 'hurricane': (6.0, 36),
}


def pack(unit, n):
    return round(U[unit][0] * n * 1.05, 1), round(U[unit][1] * n * 0.9)


PACKS = [
    # id, name, description, builder, (weight, price), stack, tag
    ('building_bundle_rafter_2x8_small', 'Small 2x8 Rafter Bundle (10)', 'A strapped bundle of ten 2x8 rafter boards, 4 m long.',
     lambda: lumber_bundle('building_bundle_rafter_2x8_small', 5, 2, 4.0, 0.19, 0.04, (0.74, 0.58, 0.36)), pack('rafter', 10), 5, 'rafters'),
    ('building_bundle_rafter_2x8_large', 'Large 2x8 Rafter Bundle (25)', 'A strapped bundle of 25 2x8 rafter boards, 4 m long.',
     lambda: lumber_bundle('building_bundle_rafter_2x8_large', 5, 5, 4.0, 0.19, 0.04, (0.74, 0.58, 0.36)), pack('rafter', 25), 2, 'rafters'),
    ('building_concrete_block_pallet_small', 'Concrete Block Half Pallet (36)', 'A half pallet of 36 concrete blocks, strapped.',
     lambda: block_pallet('building_concrete_block_pallet_small', 3, 4, 3), pack('block', 36), 3, 'masonry_units'),
    ('building_concrete_block_pallet_large', 'Concrete Block Pallet (90)', 'A full pallet of 90 concrete blocks, strapped.',
     lambda: block_pallet('building_concrete_block_pallet_large', 3, 5, 6), pack('block', 90), 1, 'masonry_units'),
    ('building_mortar_mix_pallet', 'Mortar Mix Pallet (40)', 'A shrink-wrapped pallet of forty 60 lb bags of mortar mix.',
     lambda: bag_pallet('building_mortar_mix_pallet', 2, 2, 10, (0.78, 0.72, 0.6), (0.16, 0.36, 0.55)), pack('mortar', 40), 1, 'mortar'),
    ('building_concrete_mix_pallet', 'Concrete Mix Pallet (40)', 'A shrink-wrapped pallet of forty 80 lb bags of ready-mix concrete.',
     lambda: bag_pallet('building_concrete_mix_pallet', 2, 2, 10, (0.62, 0.62, 0.6), (0.85, 0.65, 0.12)), pack('concrete', 40), 1, 'concrete_mix'),
    ('building_insulation_foam_board_stack_small', 'Small Foam Board Stack (10)', 'Ten sheets of rigid foam board, strapped.',
     lambda: stack_sheets('building_insulation_foam_board_stack_small', 1.2, 2.4, 10, 0.05, (0.55, 0.72, 0.9), (0.45, 0.62, 0.8)), pack('foam', 10), 3, 'foam_board'),
    ('building_insulation_foam_board_stack_large', 'Large Foam Board Stack (24)', 'Twenty-four sheets of rigid foam board on a pallet, strapped.',
     lambda: stack_sheets('building_insulation_foam_board_stack_large', 1.2, 2.4, 24, 0.05, (0.55, 0.72, 0.9), (0.45, 0.62, 0.8)), pack('foam', 24), 1, 'foam_board'),
    ('building_gutter_bundle', 'Gutter Bundle (10)', 'A strapped bundle of ten 3 m gutter sections.',
     lambda: lumber_bundle('building_gutter_bundle', 5, 2, 3.0, 0.13, 0.11, (0.85, 0.86, 0.88)), pack('gutter', 10), 2, 'gutters'),
    ('building_soffit_bundle', 'Soffit Panel Bundle (10)', 'A strapped bundle of ten vented soffit panels.',
     lambda: stack_sheets('building_soffit_bundle', 0.3, 2.4, 10, 0.015, (0.93, 0.92, 0.88), (0.8, 0.8, 0.8)), pack('soffit', 10), 3, 'soffit'),
    ('building_fascia_bundle', 'Fascia Board Bundle (12)', 'A strapped bundle of twelve 2.4 m fascia boards.',
     lambda: lumber_bundle('building_fascia_bundle', 4, 3, 2.4, 0.14, 0.02, (0.95, 0.95, 0.92)), pack('fascia', 12), 3, 'fascia'),
    ('building_truss_small_pack', 'Small Roof Truss Pack (6)', 'Six 4 m roof trusses, strapped together.',
     lambda: truss_pack('building_truss_small_pack', 4.0, 1.2, 6), (round(28.0 * 6 * 1.03, 1), round(95 * 6 * 0.9)), 1, 'truss_small'),
    ('building_truss_medium_pack', 'Medium Roof Truss Pack (5)', 'Five 6 m roof trusses, strapped together.',
     lambda: truss_pack('building_truss_medium_pack', 6.0, 1.8, 5), (round(46.0 * 5 * 1.03, 1), round(160 * 5 * 0.9)), 1, 'truss_medium'),
    ('building_truss_large_pack', 'Large Roof Truss Pack (4)', 'Four 8 m roof trusses, strapped together.',
     lambda: truss_pack('building_truss_large_pack', 8.0, 2.4, 4), (round(70.0 * 4 * 1.03, 1), round(250 * 4 * 0.9)), 1, 'truss_large'),
]

# equivalency -> (unit word, {member item: units}); the singles are worth 1
UNITS = {
    'rafters': ('boards', {'building_lumber_rafter_2x8': 1, 'building_bundle_rafter_2x8_small': 10, 'building_bundle_rafter_2x8_large': 25}),
    'joists': ('boards', {'building_lumber_joist_2x10': 1, 'lumber_bundle_2x10_small': 6, 'lumber_bundle_2x10_large': 15}),
    'masonry_units': ('blocks', {'building_concrete_block': 1, 'masonry_cinder_block': 1, 'building_concrete_block_pallet_small': 36, 'building_concrete_block_pallet_large': 90}),
    'mortar': ('bags', {'building_mortar_mix_bag': 1, 'building_mortar_mix_bag_pallet_10': 10, 'building_mortar_mix_bag_pallet_20': 20}),
    'concrete_mix': ('bags', {'building_concrete_mix_bag': 1, 'building_concrete_mix_bag_pallet_10': 10, 'building_concrete_mix_bag_pallet_20': 20,
                              'building_concrete_mix_pallet': 40}),
    'foam_board': ('sheets', {'building_insulation_foam_board': 1, 'building_insulation_foam_board_stack_small': 10, 'building_insulation_foam_board_stack_large': 24}),
    'gutters': ('sections', {'building_gutter_section': 1, 'building_gutter_bundle': 10}),
    'soffit': ('panels', {'building_soffit_panel': 1, 'building_soffit_bundle': 10}),
    'fascia': ('boards', {'building_fascia_board': 1, 'building_fascia_bundle': 12}),
    'truss_small': ('trusses', {'building_truss_small': 1, 'building_truss_small_pack': 6}),
    'truss_medium': ('trusses', {'building_truss_medium': 1, 'building_truss_medium_pack': 5}),
    'truss_large': ('trusses', {'building_truss_large': 1, 'building_truss_large_pack': 4}),
}


def main():
    items = []
    for pid, name, desc, build, (weight, price), stack, tag in PACKS:
        items.append((pid, name, desc, build, weight, stack, price, []))      # no tag: the equivalency (below) is what makes them interchangeable
    mod.ITEMS = items       # only the packs: make_building_items.main writes their manifests and models
    mod.main()
    # the equivalencies (assets/_schemas/equivalencies.json): each is a unit system whose members are the single item and its packages
    path = os.path.join(mod.ROOT, 'assets', '_schemas', 'equivalencies.json')
    d = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {'equivalencies': {}}
    eqs = d.setdefault('equivalencies', {})
    for name, (unit, values) in UNITS.items():
        old = eqs.get(name, {})
        members = [{'item': k, 'value': v} for k, v in values.items()]
        # keep the tag members and anything else a person added in the equivalency editor
        keep = [m for m in old.get('members', []) if m.get('tag') or (m.get('item') and m['item'] not in values)]
        members = sorted(members + keep, key=lambda m: (m['value'], m.get('item') or '~' + m.get('tag', '')))
        eqs[name] = {'unit': old.get('unit') or unit, 'label': old.get('label') or name.replace('_', ' ').title(), 'members': members}
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, path)
    print('equivalencies written:', len(eqs))


if __name__ == '__main__':
    main()
