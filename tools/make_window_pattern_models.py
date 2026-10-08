"""
Gives every window item the model of ITS pattern of bars (the muntin variants of tools/make_window_variants.py were copies of the base model, so their icons all looked the same).
For each type (double-hung, picture, slider) and each pattern (plain, two panes, four panes (the base item), six, eight) it builds the window with that grid of bars (the same grid as
Assets/Scripts/Growth/StructureWindows.cs MuntinGrid), writes the GLB into assets/building/<item>/ and updates the triangle count of the manifest.

    blender --background --python tools/make_window_pattern_models.py
    python tools/make_window_pattern_models.py --icons                       (outside Blender: the 128 px icons)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'assets', 'building')
TOOLS = os.path.join(ROOT, 'tools')
# the grid of each pattern: vertical bars, horizontal bars (StructureWindows.MuntinGrid) and the id suffix (PatternSuffix)
GRID = [(0, 0, '_plain'), (1, 0, '_panes2'), (1, 1, ''), (2, 1, '_panes6'), (3, 1, '_panes8')]
# type: (base id, width, height, frame colour)
TYPES = [('building_window_double_hung', 0.9, 1.4, (0.93, 0.92, 0.88)), ('building_window_picture', 1.5, 1.2, (0.28, 0.3, 0.32)), ('building_window_slider', 1.2, 0.8, (0.93, 0.92, 0.88))]


def items():
    for base, w, h, rgb in TYPES:
        for nv, nh, suffix in GRID:
            yield base, base + suffix, w, h, rgb, nv, nh


def sliding_sashes(b, w, h, rgb, nv, nh):
    """A sliding window is TWO windows side by side: the left sash in front, the right one behind it, each with its own frame and its own grid of bars (the game does the same: StructureWindows.SashFrames)."""
    import make_structure_stages as base_mod
    frame = base_mod.material('Frame', rgb, 0.6)
    f, r, ov = 0.05, 0.035, 0.02
    for s in (0, 1):
        a0 = -w / 2 + f if s == 0 else -ov
        a1 = ov if s == 0 else w / 2 - f
        y0, y1 = (-0.03, -0.005) if s == 0 else (0.005, 0.03)
        z0, z1 = f, h - f
        b.box(a0, a1, y0, y1, z1 - r, z1, frame)
        b.box(a0, a1, y0, y1, z0, z0 + r, frame)
        b.box(a0, a0 + r, y0, y1, z0, z1, frame)
        b.box(a1 - r, a1, y0, y1, z0, z1, frame)
        ia0, ia1, iz0, iz1 = a0 + r, a1 - r, z0 + r, z1 - r
        for i in range(1, nv + 1):
            x = ia0 + (ia1 - ia0) * i / (nv + 1)
            b.box(x - 0.01, x + 0.01, y0, y1, iz0, iz1, frame)
        for j in range(1, nh + 1):
            z = iz0 + (iz1 - iz0) * j / (nh + 1)
            b.box(ia0, ia1, y0, y1, z - 0.01, z + 0.01, frame)


def build_all():
    sys.path.insert(0, TOOLS)
    import bpy  # noqa: F401
    import make_building_items as mbi
    for base, item, w, h, rgb, nv, nh in items():
        mbi.reset()
        slider = base.endswith('slider')
        b, g = mbi.window(item, w, h, 0 if slider else nv, 0 if slider else nh, rgb)
        if slider:
            sliding_sashes(b, w, h, rgb, nv, nh)
        # (no extra meeting rail or stile: in the game the bars of the pattern are the whole look, the rail of a double-hung and the stile of a slider coincide with the cross)
        folder = os.path.join(BUILD, item)
        os.makedirs(folder, exist_ok=True)
        tris, _dims = mbi.export(b, g, folder, item)
        path = os.path.join(folder, item + '.json')
        m = json.load(open(path, encoding='utf-8'))
        m['models'][0]['triangles'] = int(tris)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print('window', item, tris, 'tris')


def icons():
    for base, item, *_ in items():
        glb = os.path.join(BUILD, item, item + '.glb')
        png = os.path.join(BUILD, item, item + '.png')
        r = subprocess.run([sys.executable, os.path.join(TOOLS, 'render_icon_from_model.py'), glb, png], capture_output=True, text=True)
        print(('icon ' if r.returncode == 0 else 'FAILED ') + item)


if __name__ == '__main__':
    if '--icons' in sys.argv:
        icons()
    else:
        build_all()
