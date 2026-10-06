"""
Builds the printed sacks (fertilizer, charcoal, the seed bag, the grain and leaf sacks) from the 20 lb sand bag model: the same mesh, scaled, with
its texture recoloured and a new label. Free and local (no Meshy).

    python tools/make_sacks.py                 (all of them; it paints the textures, then runs Blender on this same file)
    python tools/make_sacks.py mat_fertilizer  (only these)
    python tools/render_icon_from_model.py assets/<category>/<id>/<id>.glb assets/<category>/<id>/<id>.png

How: the sand bag's texture is beige paper with red blocks and a label panel on the top face. Every texel is recoloured by what it was (red ->
the accent colour, the rest -> the sack colour), and the label panel is painted new with the item's name. The panel is found in 3D: a map of
texel -> position on the bag (assets/_scratch/bags_20lb/pos_20lb_sand_bag.npy, made by uvmap.py there) says which texels lie on the top face.

Every item is already in the kit: only its model entry, its dimensions and its README are written.
"""
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_GLB = os.path.join(ROOT, 'assets', 'building', '20lb_sand_bag', '20lb_sand_bag.glb')
SCRATCH = os.path.join(ROOT, 'assets', '_scratch', 'bags_20lb')
OUT = os.path.join(ROOT, 'assets', '_scratch', 'simple_props', 'sacks')
BURLAP = (0.76, 0.63, 0.43)
CREAM = (0.96, 0.93, 0.85)
LABEL_X, LABEL_Y = 0.066, 0.076           # half the label panel, in metres on the sand bag (0.36 x 0.21 m)

# item: (scale of the sand bag, sack colour, accent colour, label colour, ink colour, the lines of the label)
SACKS = {
    'mat_fertilizer': (1.4, (0.2, 0.48, 0.24), (0.95, 0.8, 0.15), (0.97, 0.97, 0.94), (0.1, 0.3, 0.14), ['FERTILIZER', 'ALL PURPOSE']),
    'fuel_charcoal': (1.15, (0.1, 0.1, 0.11), (0.88, 0.3, 0.08), CREAM, (0.1, 0.1, 0.11), ['CHARCOAL', 'LUMP']),
    'tool_seedbag': (0.95, BURLAP, (0.25, 0.5, 0.2), CREAM, (0.15, 0.32, 0.12), ['SEED']),
    'ingredient_alfalfa': (0.6, BURLAP, (0.3, 0.55, 0.25), CREAM, (0.16, 0.32, 0.14), ['ALFALFA', 'HAY']),
    'ingredient_barley': (0.6, BURLAP, (0.82, 0.62, 0.18), CREAM, (0.4, 0.28, 0.06), ['BARLEY', 'GRAIN']),
    'ingredient_flax': (0.6, BURLAP, (0.35, 0.45, 0.78), CREAM, (0.15, 0.22, 0.45), ['FLAX']),
    'ingredient_hops': (0.6, BURLAP, (0.45, 0.66, 0.2), CREAM, (0.2, 0.34, 0.08), ['HOPS']),
    'ingredient_oats': (0.6, BURLAP, (0.7, 0.5, 0.25), CREAM, (0.38, 0.25, 0.1), ['OATS', 'GRAIN']),
    'ingredient_soybeans': (0.6, BURLAP, (0.62, 0.52, 0.14), CREAM, (0.34, 0.27, 0.05), ['SOYBEANS']),
    'ingredient_tobacco': (0.6, BURLAP, (0.5, 0.3, 0.15), CREAM, (0.3, 0.16, 0.07), ['TOBACCO', 'LEAF']),
}


def paint(item):
    """The recoloured texture of one sack (system Python: PIL and numpy)."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    scale, body, accent, label, ink, lines = SACKS[item]
    src = np.asarray(Image.open(os.path.join(SCRATCH, 'tex_20lb_sand_bag.png')).convert('RGB')).astype(np.float32) / 255.0
    pos = np.load(os.path.join(SCRATCH, 'pos_20lb_sand_bag.npy'))
    r, g, b = src[..., 0], src[..., 1], src[..., 2]
    red = np.clip((r - np.maximum(g, b) - 0.16) / 0.4, 0.0, 1.0)[..., None]                     # how red a texel was: the printed blocks
    lum = src.mean(-1)
    paper = lum[(red[..., 0] <= 0.0) & (lum > 0.6)]
    shade = np.clip(lum / np.median(paper), 0.0, 1.06)
    shade = np.where(shade < 0.75, 1.0, shade)[..., None]                                # the old lettering is dropped, the soft shading kept
    out = (np.array(body) * shade) * (1 - red) + np.array(accent) * red
    # the label: a picture laid over the middle of the top face, the lettering running across the bag
    px = 4000.0
    W, H = int(LABEL_X * 2 * px), int(LABEL_Y * 2 * px)
    text = Image.new('RGB', (H, W), tuple(int(c * 255) for c in label))                  # drawn lying down, then turned a quarter
    d = ImageDraw.Draw(text)
    inkc = tuple(int(c * 255) for c in ink)
    d.rectangle((14, 14, H - 15, W - 15), outline=tuple(int(c * 255) for c in accent), width=10)
    font = lambda size: ImageFont.truetype('arialbd.ttf', size)
    sizes = []
    for n, line in enumerate(lines):
        size = 150 if n == 0 else 76
        while d.textlength(line, font=font(size)) > H - 90:
            size -= 4
        sizes.append(size)
    total = sum(sizes) + 30 * (len(lines) - 1)
    y = (W - total) / 2 - 12
    for line, size in zip(lines, sizes):
        d.text(((H - d.textlength(line, font=font(size))) / 2, y), line, fill=inkc, font=font(size))
        y += size + 30
    canvas = np.asarray(text.rotate(-90, expand=True)).astype(np.float32) / 255.0         # W wide, H tall
    on_top = np.isfinite(pos[..., 0])
    x, yy = np.nan_to_num(pos[..., 0]), np.nan_to_num(pos[..., 1])
    inside = on_top & (np.abs(x) < LABEL_X) & (np.abs(yy) < LABEL_Y)
    u = np.clip(((x + LABEL_X) * px).astype(int), 0, W - 1)
    v = np.clip(((LABEL_Y - yy) * px).astype(int), 0, H - 1)
    out[inside] = canvas[v[inside], u[inside]]
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'tex_%s.png' % item))


def build(item):
    """The sack's GLB and manifest (inside Blender)."""
    import bpy
    import numpy as np
    from mathutils import Matrix
    scale = SACKS[item][0]
    found = glob.glob(os.path.join(ROOT, 'assets', '*', item, item + '.json'))
    if not found:
        print('SKIP (not in the kit)', item)
        return
    path = found[0]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC_GLB)
    new = bpy.data.images.load(os.path.join(OUT, 'tex_%s.png' % item))
    a = np.empty(new.size[0] * new.size[1] * 4, dtype=np.float32)
    new.pixels.foreach_get(a)
    for img in [i for i in bpy.data.images if i is not new and i.size[0] == new.size[0]]:
        img.pixels.foreach_set(a)
        img.update()
        img.pack()
        img.name = item + '_base_color'
    bpy.data.images.remove(new)
    bpy.context.view_layer.update()
    tris, dims = 0, [0, 0, 0]
    for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.data.transform(Matrix.Scale(scale, 4))
        o.data.update()
        o.name = item
        pts = [v.co for v in o.data.vertices]
        dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    bpy.ops.export_scene.gltf(filepath=os.path.join(os.path.dirname(path), item + '.glb'), export_format='GLB', use_selection=False)
    m = json.load(open(path, encoding='utf-8'))
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    import make_simple_props as props
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(os.path.dirname(path), 'README.md'),
               '# %s\n\n%s\n\nModel: the 20 lb sand bag (`20lb_sand_bag`) scaled by %.2f (%.2f x %.2f x %.2f m, lying flat), recoloured and relabelled '
               '%s by tools/make_sacks.py. %d triangles, texture embedded.\n' % (m['name'], m.get('description', ''), scale, *dims, ' / '.join(SACKS[item][5]), tris))
    print('sack', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    try:
        import bpy  # noqa: F401
        inside_blender = True
    except ImportError:
        inside_blender = False
    if inside_blender:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        for it in sys.argv[sys.argv.index('--') + 1:]:
            build(it)
    else:
        items = [i for i in sys.argv[1:] if i in SACKS] or list(SACKS)
        for it in items:
            paint(it)
        subprocess.run(['blender', '--background', '--python', os.path.abspath(__file__), '--'] + items, check=True)
