"""
Builds the alternative FOUNDATION styles of a structure in headless Blender (free, local, low-poly): a concrete block stem wall, a brick
stem wall and a stilt (pile) foundation. The default poured slab is the 'Foundation' object of every stage model
(tools/make_structure_stages.py, tools/make_house_stages.py); when the foundation was built from other materials (the item's
properties.look_style, see docs/STRUCTURE_STAGES_GUIDE.md) the game hides that object and shows one of these models in its place.

    blender --background --python tools/make_foundation_variants.py -- small_cabin starter_house

Each variant is a stage-style manifest + GLB beside the foundation stage: stages/struct_foundation/struct_foundation_<id>_<style>.glb
(footprint centred, ground at z = 0, top of the deck at the foundation height). The stilt model stands on piles that go below the ground:
it is built with the ground at z = PILE and has an empty named GroundLevel there; the game lowers it so GroundLevel sits at the ground.
Materials: FoundationFace (recoloured by the block or brick item used), Mortar, Pile, Deck.
"""
import copy
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_structure_stages as base  # noqa: E402

Builder = base.Builder
STRUCTURES = base.STRUCTURES
PILE = 1.2   # how far the stilts go down below the ground


def courses(b, w, d, h, face, mortar, unit_l, courses_n):
    """A solid core with a perimeter skin of separate blocks (a small gap between them shows the mortar core)."""
    b.box(-w / 2 + 0.1, w / 2 - 0.1, -d / 2 + 0.1, d / 2 - 0.1, 0.0, h, mortar)
    ch = h / courses_n
    gap = 0.008
    depth = 0.2
    for c in range(courses_n):
        z0, z1 = c * ch + gap / 2, (c + 1) * ch - gap / 2
        off = (unit_l / 2) if c % 2 else 0.0
        for side in ('front', 'back'):
            y0, y1 = (-d / 2, -d / 2 + depth) if side == 'front' else (d / 2 - depth, d / 2)
            x = -w / 2 - off
            while x < w / 2 - 1e-3:
                xa, xb = max(x + gap / 2, -w / 2), min(x + unit_l - gap / 2, w / 2)
                if xb - xa > 0.04:
                    b.box(xa, xb, y0, y1, z0, z1, face)
                x += unit_l
        for side in ('left', 'right'):
            x0, x1 = (-w / 2, -w / 2 + depth) if side == 'left' else (w / 2 - depth, w / 2)
            y = -d / 2 + depth - off
            while y < d / 2 - depth - 1e-3:
                ya, yb = max(y + gap / 2, -d / 2 + depth), min(y + unit_l - gap / 2, d / 2 - depth)
                if yb - ya > 0.04:
                    b.box(x0, x1, ya, yb, z0, z1, face)
                y += unit_l
    # a capping slab and the front steps
    for k in range(3):
        b.box(-0.8, 0.8, -d / 2 - 0.3 * (k + 1), -d / 2, 0.0, h * (1 - (k + 1) * 0.28), face)


def block(b, w, d, h, M):
    courses(b, w, d, h, M['face'], M['mortar'], 0.4, 2)


def brick(b, w, d, h, M):
    courses(b, w, d, h, M['face'], M['mortar'], 0.25, 3)


def stilts(b, w, d, h, M):
    """Round piles under a timber deck. Built with the ground at z = PILE."""
    g = PILE
    pile, deck = M['pile'], M['deck']
    nx = max(2, int(round(w / 1.5)) + 1)
    ny = max(2, int(round(d / 1.5)) + 1)
    for i in range(nx):
        for j in range(ny):
            x = -w / 2 + 0.2 + (w - 0.4) * i / (nx - 1)
            y = -d / 2 + 0.2 + (d - 0.4) * j / (ny - 1)
            b.log((x, y, 0.0), (x, y, g + h - 0.22), 0.13, pile, sides=8)
    # beams across the piles, joists over them, then the deck boards
    for j in range(ny):
        y = -d / 2 + 0.2 + (d - 0.4) * j / (ny - 1)
        b.box(-w / 2, w / 2, y - 0.07, y + 0.07, g + h - 0.24, g + h - 0.12, deck)
    n = int(d / 0.5) + 1
    for k in range(n):
        y = -d / 2 + 0.05 + (d - 0.1) * k / max(1, n - 1)
        b.box(-w / 2, w / 2, y - 0.03, y + 0.03, g + h - 0.12, g + h - 0.04, deck)
    boards = int(d / 0.14)
    for k in range(boards):
        ya = -d / 2 + k * d / boards
        b.box(-w / 2, w / 2, ya + 0.004, ya + d / boards - 0.004, g + h - 0.04, g + h, M['deck_top'])
    for k in range(3):                                                                           # steps down to the ground
        b.box(-0.8, 0.8, -d / 2 - 0.3 * (k + 1), -d / 2, g + h * 0.0 + (h * (1 - (k + 1) * 0.28)) - 0.06, g + (h * (1 - (k + 1) * 0.28)), M['deck_top'])
        for x in (-0.76, 0.76):
            b.box(x - 0.04, x + 0.04, -d / 2 - 0.3 * (k + 1), -d / 2 - 0.3 * k, g - 0.1, g + (h * (1 - (k + 1) * 0.28)) - 0.06, pile)


STYLES = {'block': (block, (0.62, 0.62, 0.6)), 'brick': (brick, (0.62, 0.3, 0.22)), 'stilts': (stilts, None)}


def main():
    argv = sys.argv
    names = argv[argv.index('--') + 1:] if '--' in argv else ['small_cabin']
    for structure in names:
        folder = os.path.join(STRUCTURES, structure, 'stages', 'struct_foundation')
        mpath = os.path.join(folder, f'struct_foundation_{structure}.json')
        d0 = json.load(open(mpath, encoding='utf-8'))
        dims = d0['category_fields']['dimensions_m']
        w, d, h = dims['width'], dims['depth'], dims['height']
        for style, (fn, colour) in STYLES.items():
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            M = {
                'face': base.material('FoundationFace', colour or (0.6, 0.6, 0.58), 0.95), 'mortar': base.material('Mortar', (0.42, 0.42, 0.4), 0.95),
                'pile': base.material('Pile', (0.45, 0.32, 0.2), 0.9), 'deck': base.material('Deck', (0.55, 0.42, 0.27), 0.9),
                'deck_top': base.material('DeckBoards', (0.62, 0.47, 0.3), 0.85),
            }
            vid = f'struct_foundation_{structure}_{style}'
            b = Builder(vid)
            fn(b, w, d, h, M)
            obj = b.finish()
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            if style == 'stilts':
                marker = bpy.data.objects.new('GroundLevel', None)
                marker.location = (0.0, 0.0, PILE)
                bpy.context.collection.objects.link(marker)
                marker.select_set(True)
            bpy.context.view_layer.objects.active = obj
            out = os.path.join(folder, vid + '.glb')
            bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
            tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
            m = copy.deepcopy(d0)
            m['id'] = vid
            m['name'] = f"{d0['name'].split(' - ')[0]} - {style.capitalize()} Foundation"
            m['description'] = f'The {style} foundation style of the structure (shown instead of the poured slab when it was built from {style} materials).'
            m['icon'] = d0['icon']
            m['models'] = [{'file': vid + '.glb', 'format': 'glb', 'dimensions_m': {'x': w, 'y': h + (PILE if style == 'stilts' else 0.0), 'z': d}, 'triangles': tris}]
            json.dump(m, open(os.path.join(folder, vid + '.json'), 'w', encoding='utf-8'), indent=2)
            print('variant', vid, tris, 'tris')


if __name__ == '__main__':
    main()
