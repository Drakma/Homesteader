"""
Builds the WINDOW SHUTTERS item (assets/building/building_window_shutters): a pair of louvred shutters (the item of the shutters of the window system, docs/WINDOWS.md).
In the game a right click on a window of a finished building with the item in hand fits a pair (centred on the window, each 0.38 m wide, 4 cm proud of the wall); a wrench and a right click on a
window with shutters takes them off again. The shutters the buildings come with are the same thing.

    blender --background --python tools/make_window_shutters.py
    python tools/render_icon_from_model.py assets/building/building_window_shutters/building_window_shutters.glb assets/building/building_window_shutters/building_window_shutters.png
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'building', 'building_window_shutters')
ID = 'building_window_shutters'


def build():
    import kitchen_lib as L
    L.reset_scene()
    K = L.Mesh('building_window_shutters')
    paint = L.material('ShutterPaint', (0.16, 0.30, 0.26), 0.7)
    w, h, t = 0.38, 1.50, 0.04
    gap = 0.06                                                 # the two shutters of a pair stand side by side
    for sx in (-1, 1):
        x0 = sx * (w / 2 + gap / 2) - w / 2
        x1 = x0 + w
        # the frame: two stiles, a top rail and a bottom rail, and the louvre slats between them
        f = 0.045
        K.box(x0, x0 + f, 0.0, t, 0.0, h, paint)
        K.box(x1 - f, x1, 0.0, t, 0.0, h, paint)
        K.box(x0 + f, x1 - f, 0.0, t, 0.0, f, paint)
        K.box(x0 + f, x1 - f, 0.0, t, h - f, h, paint)
        n = 22
        zs = (h - 2 * f) / n
        for k in range(n):
            z = f + k * zs
            K.box(x0 + f, x1 - f, 0.004, t - 0.004, z + zs * 0.15, z + zs * 0.62, paint)       # a slat
    obj = K.build()
    return L, obj


def main():
    L, obj = build()
    lo, hi = L.bounds(obj)
    os.makedirs(OUT, exist_ok=True)
    L.export_glb(obj, os.path.join(OUT, ID + '.glb'))
    tris = obj['triangles']
    src = os.path.join(ROOT, 'assets', 'building', 'building_window_double_hung', 'building_window_double_hung.json')
    m = json.load(open(src, encoding='utf-8'))
    m['id'] = ID
    m['name'] = 'Window Shutters'
    m['description'] = 'A pair of louvred shutters for a window. Right click a window of a finished building with them in hand to fit them; a wrench and a right click takes them off.'
    m['icon'] = ID + '.png'
    m['properties']['weight_kg'] = 6.0
    m['properties']['max_stack_size'] = 12
    m['properties']['base_value'] = 60
    m['properties']['sale_unit'] = 'pair'
    m['models'] = [{'file': ID + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(hi.x - lo.x, 3), 'y': round(hi.z - lo.z, 3), 'z': round(hi.y - lo.y, 3)}, 'triangles': int(tris)}]
    with open(os.path.join(OUT, ID + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write('\n')
    with open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s\n\n%s\n\nProcedural model (tools/make_window_shutters.py), %d triangles.\n' % (m['name'], m['description'], tris))
    print('built', ID, tris, 'tris')


if __name__ == '__main__':
    main()
