"""
Stacks of 10 and 20 for the building materials that had none (everything but paint), as GLBs in headless Blender: free, local, low-poly.

    blender --background --python tools/make_material_stacks.py                       (everything in MATERIALS)
    blender --background --python tools/make_material_stacks.py -- roofing_thatch     (only the ids named)
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png        (every item made)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

For each material it reads the single's own model (assets/building/<id>/*.glb) and writes assets/building/<id>_stack_<n>/ (model, manifest, README).
The stack is the single repeated, laid in rows and layers: on a wooden pallet when it fits one, in a cardboard tray when it is small (cans, buckets),
strapped when it is long.

  * a light single (under about 230 triangles) is copied as it is;
  * a heavier one is photographed square-on from above and from its four sides (flat lit, its own colours) and each copy is a 12-triangle block
    carrying those pictures, so twenty of them stay inside the triangle budget (the same trick as tools/make_bag_pallets.py).

SINGLES builds the single first where it had no model (wood_log, building_metal, building_glass, building_insulation_fiberglass_batt) or where the old
model was a short stub (the 2x8 joist, the 4x4 and round posts, the PVC, sewer and leach pipes): those are now at their real length (2.4 to 3.6 m), so a
stack of them is a long strapped bundle, never on a pallet.

A stack weighs its singles (plus 20 kg for a pallet) and costs them times 0.9. An item that is already in the kit keeps its name, price and the rest:
only its model entry and dimensions are updated. The equivalencies are saved through the kit (see the session notes in the READMEs).

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0.
"""
import glob
import json
import math
import os
import sys
import tempfile

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_bag_pallets as bp  # noqa: E402    (photograph, atlas, material, box, VIEWS)

ROOT = bp.ROOT
BUILD = bp.BUILD
COUNTS = (10, 20)
COUNTS_OF = {'building_bitumen_bucket': (9, 18)}   # a pallet of buckets is 3 x 3 on one layer or two
PALLET_KG = 20.0
PALLET_H = 0.15
TRAY_T = 0.006
NO_PALLET = {'wood_log'}   # lumber and pipe are never on a pallet: the long ones are too long for one anyway, a pile of logs just lies there
COPY_TRIS = 230            # a single up to this many triangles is copied; a heavier one becomes picture blocks

MATERIALS = """
masonry_brick_brown masonry_brick_charcoal masonry_brick_dark_red masonry_brick_grey masonry_brick_old_mill masonry_brick_oxblood masonry_brick_pressed_red
masonry_brick_red masonry_brick_rust masonry_brick_salmon masonry_brick_tan masonry_brick_white masonry_fieldstone
roofing_shingles_brown roofing_shingles_green roofing_shingles_red roofing_shingles_weathered roofing_seam_black roofing_seam_green roofing_seam_red
roofing_cedar_shakes roofing_clay_tile roofing_slate_tile roofing_thatch
building_siding_barn_red building_siding_brick_veneer building_siding_cedar_shake building_siding_charcoal_batten building_siding_cream building_siding_sage
building_siding_slate_blue building_siding_stucco_tan building_siding_weathered_grey building_siding_white
building_floor_carpet_beige building_floor_carpet_brown building_floor_carpet_burgundy building_floor_carpet_grey building_floor_carpet_navy
building_floor_tile_slate building_floor_tile_speckled building_floor_tile_terracotta building_floor_tile_white building_floor_vinyl_plank
lumber_joist_2x8 lumber_post_4x4 post_wood_round_6inch building_beam_glulam wood_log
sheet_plywood_cdx building_metal building_glass
building_insulation_fiberglass_batt
building_steel_stud_framing building_steel_frame_beam
pipe_pvc_half_inch pipe_pvc_one_inch pipe_pvc_two_inch pipe_sewer_solid_4inch pipe_leach_perforated_4inch drain_french_sock building_downspout
building_joint_compound_bucket building_thinset_bucket building_bitumen_bucket
""".split()


# ------------------------------------------------------------------ the four singles that had no model

def cyl_x(bm, mi, x0, x1, z, radius, sides=10):
    ra = [bm.verts.new((x0, radius * math.cos(2 * math.pi * k / sides), z + radius * math.sin(2 * math.pi * k / sides))) for k in range(sides)]
    rb = [bm.verts.new((x1, v.co.y, v.co.z)) for v in ra]
    for k in range(sides):
        bm.faces.new((ra[k], ra[(k + 1) % sides], rb[(k + 1) % sides], rb[k])).material_index = mi
    return ra, rb


def single_wood_log():
    bm = bmesh.new()
    mats = [bp.material('Bark', (0.36, 0.25, 0.16), rough=0.95), bp.material('EndGrain', (0.8, 0.66, 0.44), rough=0.85), bp.material('Rings', (0.62, 0.48, 0.3), rough=0.85)]
    r, length = 0.15, 1.2
    ra, rb = cyl_x(bm, 0, -length / 2, length / 2, r, r, sides=10)
    bm.faces.new(ra[::-1]).material_index = 1
    bm.faces.new(rb).material_index = 1
    for x, s in ((-length / 2 - 0.001, -1), (length / 2 + 0.001, 1)):          # a growth ring on each end
        ring = [bm.verts.new((x, r * 0.5 * math.cos(2 * math.pi * k / 8), r + r * 0.5 * math.sin(2 * math.pi * k / 8))) for k in range(8)]
        bm.faces.new(ring if s > 0 else ring[::-1]).material_index = 2
    for a in (0.6, 2.4, 4.1):                                                   # a few knots / bark ridges along it
        y, z = r * 1.01 * math.cos(a), r + r * 1.01 * math.sin(a)
        bp.box(bm, -length * 0.35, length * 0.35, y - 0.012, y + 0.012, z - 0.012, z + 0.012, 0)
    return bm, mats


def single_metal_sheet():
    bm = bmesh.new()
    mats = [bp.material('SheetMetal', (0.68, 0.7, 0.72), rough=0.35), bp.material('SheetEdge', (0.5, 0.52, 0.54), rough=0.4)]
    w, d, t = 1.0, 2.0, 0.003
    bp.box(bm, -w / 2, w / 2, -d / 2, d / 2, 0.0, t, 0)
    for y in (-d / 2 + 0.01, d / 2 - 0.01):                                     # the rolled edge at each end
        bp.box(bm, -w / 2 - 0.001, w / 2 + 0.001, y - 0.012, y + 0.012, -0.0005, t + 0.002, 1)
    return bm, mats


def single_glass_pane():
    bm = bmesh.new()
    glass = bp.material('Glass', (0.6, 0.78, 0.9), rough=0.1)
    glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.6      # (a pane lying on the ground: less see-through than a window, or it vanishes)
    for attr, val in (('blend_method', 'BLEND'), ('surface_render_method', 'BLENDED')):
        try:
            setattr(glass, attr, val)
        except Exception:
            pass
    glass.diffuse_color = (0.6, 0.78, 0.9, 0.5)
    mats = [glass, bp.material('GlassEdge', (0.45, 0.68, 0.72), rough=0.2), bp.material('CornerGuard', (0.75, 0.6, 0.4), rough=0.9)]
    w, d, t = 1.2, 1.5, 0.006
    bp.box(bm, -w / 2, w / 2, -d / 2, d / 2, 0.0, t, 0)
    for x0, x1, y0, y1 in ((-w / 2 - 0.002, w / 2 + 0.002, -d / 2 - 0.002, -d / 2 + 0.004), (-w / 2 - 0.002, w / 2 + 0.002, d / 2 - 0.004, d / 2 + 0.002),
                           (-w / 2 - 0.002, -w / 2 + 0.004, -d / 2, d / 2), (w / 2 - 0.004, w / 2 + 0.002, -d / 2, d / 2)):
        bp.box(bm, x0, x1, y0, y1, -0.0005, t + 0.0005, 1)                      # the green edge of the pane
    for sx in (-1, 1):
        for sy in (-1, 1):                                                      # cardboard corner guards
            cx, cy = sx * (w / 2 - 0.03), sy * (d / 2 - 0.03)
            bp.box(bm, cx - 0.04, cx + 0.04, cy - 0.04, cy + 0.04, -0.002, t + 0.002, 2)
    return bm, mats


def single_fiberglass_batt():
    bm = bmesh.new()
    mats = [bp.material('Fiberglass', (0.95, 0.62, 0.7), rough=0.95), bp.material('KraftFacing', (0.68, 0.52, 0.33), rough=0.9), bp.material('FacingPrint', (0.3, 0.24, 0.16), rough=0.9)]
    w, d, h = 0.4, 1.2, 0.15
    bp.box(bm, -w / 2, w / 2, -d / 2, d / 2, 0.006, h, 0)
    bp.box(bm, -w / 2 - 0.02, w / 2 + 0.02, -d / 2, d / 2, 0.0, 0.006, 1)        # the kraft paper facing with its stapling flanges
    for k in range(4):                                                          # the quilted ribs of the batt
        y = -d / 2 + d * (k + 0.5) / 4
        bp.box(bm, -w / 2 + 0.01, w / 2 - 0.01, y - 0.12, y + 0.12, h, h + 0.012, 0)
    for k in range(3):
        y = -d / 2 + d * (k + 1) / 4
        bp.box(bm, -w / 2 - 0.021, -w / 2 - 0.02, y - 0.1, y + 0.1, 0.001, 0.005, 2)
    return bm, mats


# ------------------------------------------------------------------ the long singles, at their real length

def tube(bm, mi, mi_bore, length, r_out, r_in, z=None, sides=10, x0=None):
    """A length of pipe along X lying on the ground: the wall, the bore and the two ends."""
    z = r_out if z is None else z
    x0 = -length / 2 if x0 is None else x0
    x1 = x0 + length
    oa, ob = cyl_x(bm, mi, x0, x1, z, r_out, sides)
    ia, ib = cyl_x(bm, mi_bore, x0, x1, z, r_in, sides)
    for k in range(sides):
        j = (k + 1) % sides
        bm.faces.new((oa[j], oa[k], ia[k], ia[j])).material_index = mi
        bm.faces.new((ob[k], ob[j], ib[j], ib[k])).material_index = mi
    return oa, ob


def single_pipe(rgb, r_out, length=3.0, bell=False, holes=False, stripe=None, hole_rgb=(0.05, 0.05, 0.05), n_holes=8):
    def build():
        bm = bmesh.new()
        mats = [bp.material('Pipe', rgb, rough=0.45), bp.material('PipeBore', tuple(c * 0.35 for c in rgb), rough=0.8)]
        r_in = r_out * 0.86
        tube(bm, 0, 1, length, r_out, r_in)
        if bell:                                             # the socket end of a sewer or drain pipe
            tube(bm, 0, 1, r_out * 1.6, r_out * 1.16, r_out * 1.02, z=r_out, x0=length / 2 - r_out * 1.6)
        if stripe:                                           # the printed line down a PVC pipe
            mats.append(bp.material('PipePrint', stripe, rough=0.6))
            bp.box(bm, -length / 2 + 0.2, length / 2 - 0.2, -r_out * 0.12, r_out * 0.12, 2 * r_out - 0.0005, 2 * r_out + 0.0008, 2)
        if holes:                                            # the perforations of a leach pipe, two rows
            mats.append(bp.material('PipeHole', hole_rgb, rough=0.9))
            hi = len(mats) - 1
            for k in range(n_holes):
                x = -length / 2 + length * (k + 0.5) / n_holes
                for a in (math.radians(55), math.radians(125)):
                    # a flat patch lying on the pipe's surface (two triangles a hole, so twenty pipes can still be real copies)
                    ca, sa = math.cos(a), math.sin(a)
                    rr = r_out * 1.004
                    pts = [(x + dx, rr * ca - dt * sa, r_out + rr * sa + dt * ca) for dx, dt in ((-0.014, -0.009), (0.014, -0.009), (0.014, 0.009), (-0.014, 0.009))]
                    bm.faces.new([bm.verts.new(q) for q in pts]).material_index = hi
        return bm, mats
    return build


def single_board(rgb, length, width, thick):
    def build():
        bm = bmesh.new()
        mats = [bp.material('Timber', rgb, rough=0.85), bp.material('EndGrain', tuple(c * 0.8 for c in rgb), rough=0.9)]
        bp.box(bm, -length / 2, length / 2, -width / 2, width / 2, 0.0, thick, 0)
        for x0, x1 in ((-length / 2 - 0.001, -length / 2 + 0.004), (length / 2 - 0.004, length / 2 + 0.001)):
            bp.box(bm, x0, x1, -width / 2 - 0.0005, width / 2 + 0.0005, -0.0005, thick + 0.0005, 1)
        return bm, mats
    return build


def single_round_post():
    bm = bmesh.new()
    mats = [bp.material('TreatedWood', (0.5, 0.42, 0.28), rough=0.9), bp.material('EndGrain', (0.72, 0.6, 0.4), rough=0.85)]
    r, length = 0.076, 2.4
    ra, rb = cyl_x(bm, 0, -length / 2, length / 2, r, r, sides=10)
    bm.faces.new(ra[::-1]).material_index = 1
    bm.faces.new(rb).material_index = 1
    return bm, mats


PVC_WHITE = (0.93, 0.93, 0.91)

SINGLES = {
    # lumber: a 2x8 is 38 x 184 mm, a 4x4 is 89 x 89 mm
    # lumber: a 2x4 stud is 38 x 89 mm and 2.4 m long (the colour of the boards in lumber_bundle_2x4_*, tools/make_simple_props.py)
    'lumber_stud_2x4': single_board((0.87, 0.73, 0.5), 2.4, 0.089, 0.038),
    'lumber_joist_2x8': single_board((0.78, 0.63, 0.41), 3.6, 0.184, 0.038),
    'lumber_post_4x4': single_board((0.55, 0.56, 0.36), 2.4, 0.089, 0.089),
    'post_wood_round_6inch': single_round_post,
    # pipe: 3 m lengths at their real outside diameters
    'pipe_pvc_half_inch': single_pipe(PVC_WHITE, 0.0107, stripe=(0.2, 0.3, 0.6)),
    'pipe_pvc_one_inch': single_pipe(PVC_WHITE, 0.0167, stripe=(0.2, 0.3, 0.6)),
    'pipe_pvc_two_inch': single_pipe(PVC_WHITE, 0.0302, stripe=(0.2, 0.3, 0.6)),
    'pipe_sewer_solid_4inch': single_pipe((0.3, 0.5, 0.36), 0.055, bell=True),
    'pipe_leach_perforated_4inch': single_pipe((0.92, 0.92, 0.9), 0.055, bell=True, holes=True),
    # the French drain pipe: black perforated PVC (the holes are drawn grey so they show on black)
    'drain_french_sock': single_pipe((0.06, 0.06, 0.065), 0.055, bell=True, holes=True, hole_rgb=(0.42, 0.42, 0.44), n_holes=14),
    # propane pipe: charcoal grey, a yellow gas line down it. The item is now fuel/fuel_pipe_propane (moved out of building), so this script no longer
    # rebuilds it or its stacks; the builder stays here as the record of how the model was made.
    'pipe_propane': single_pipe((0.2, 0.21, 0.23), 0.0167, stripe=(0.95, 0.78, 0.08)),
    'wood_log': single_wood_log,
    'building_metal': single_metal_sheet,
    'building_glass': single_glass_pane,
    'building_insulation_fiberglass_batt': single_fiberglass_batt,
}


def finish(bm, mats, name):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return o


def measure(obj):
    pts = [v.co for v in obj.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def export(obj, folder, item):
    os.makedirs(folder, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    lo, hi = measure(obj)
    return sum(len(p.vertices) - 2 for p in obj.data.polygons), [round(v, 3) for v in (hi - lo)]


def set_model(m, item, tris, dims):
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m.pop('dimensions', None)
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})


def build_single(item):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm, mats = SINGLES[item]()
    obj = finish(bm, mats, item)
    folder = os.path.join(BUILD, item)
    tris, dims = export(obj, folder, item)
    path = os.path.join(folder, item + '.json')
    m = json.load(open(path, encoding='utf-8'))
    set_model(m, item, tris, dims)
    m['properties']['placeable'] = True
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2)
    print('single', item, tris, 'tris', dims)


# ------------------------------------------------------------------ the stacks

def load_single(item):
    """The single's model as ONE object lying the way it stacks: a tall thing (a 3 m downspout standing up) is laid down. Returns (object, size, triangles)."""
    folder = os.path.join(BUILD, item)
    path = os.path.join(folder, item + '.glb')
    if not os.path.exists(path):
        found = sorted(glob.glob(os.path.join(folder, '*.glb')))
        if not found:
            return None
        path = found[0]
    bpy.ops.import_scene.gltf(filepath=path)
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        if o.data.users > 1:
            o.data = o.data.copy()
        world = o.matrix_world.copy()               # (the older models hang under a scaled parent: take the world matrix before unparenting)
        o.parent = None
        o.data.transform(world)
        o.matrix_world = Matrix.Identity(4)
    for o in list(bpy.context.scene.objects):
        if o.type != 'MESH':
            bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = meshes[0]
    lo, hi = measure(obj)
    size = hi - lo
    if size.z > 1.0 and size.z > max(size.x, size.y) * 1.5:
        obj.data.transform(Matrix.Rotation(math.radians(90), 4, 'X'))          # stood on end: lay it down, its length along Y
        lo, hi = measure(obj)
    obj.data.transform(Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))
    lo, hi = measure(obj)
    return obj, hi - lo, sum(len(p.vertices) - 2 for p in obj.data.polygons)


def arrange(n, size):
    """(across x, across y, layers): the stack that stays low and near a pallet's footprint."""
    sx, sy, sz = size
    best = None
    for cx in range(1, n + 1):
        for cy in range(1, n + 1):
            per = cx * cy
            if per > n:
                break
            layers = math.ceil(n / per)
            w, d, h = cx * sx, cy * sy, layers * sz
            cost = 100 * max(0.0, h - 1.6) + 30 * max(0.0, w - max(1.25, sx)) + 30 * max(0.0, d - max(1.05, sy)) + 2 * h
            cost += 3 * max(0.0, h / max(min(w, d), 0.05) - 2.0)                 # not a tower
            if max(sx, sy) > 1.5 and min(sx, sy) < 0.4:                          # a long thing: a bundle about as high as it is wide, not a flat raft
                cost += 1.2 * abs(math.log((d if sx > sy else w) / h))
            else:
                cost += 1.0 * abs(math.log(w / d))                               # nor a single file
            cost += 0.5 * (per * layers - n) / per                               # a full top layer is better
            if best is None or cost < best[0]:
                best = (cost, cx, cy, layers)
    return best[1:]


def slots(n, cx, cy, layers):
    out = []
    left = n
    for k in range(layers):
        cells = [(i, j) for j in range(cy) for i in range(cx)]
        if left < len(cells):
            cells = sorted(cells, key=lambda s: (abs(s[1] - (cy - 1) / 2), abs(s[0] - (cx - 1) / 2)))[:left]
        out += [(i, j, k) for i, j in cells]
        left -= len(cells)
    return out


def pallet_mesh(w, d):
    bm = bmesh.new()
    wood = bp.material('PalletWood', (0.62, 0.47, 0.3), rough=0.9)
    h = PALLET_H
    for y in (-d / 2 + 0.05, 0.0, d / 2 - 0.05):
        bp.box(bm, -w / 2, w / 2, y - 0.05, y + 0.05, 0.022, h - 0.022, 0)
    n = max(5, round(w / 0.18))
    for k in range(n):
        x = -w / 2 + 0.05 + (w - 0.1) * k / (n - 1)
        bp.box(bm, x - 0.05, x + 0.05, -d / 2, d / 2, h - 0.022, h, 0)
    for x in (-w / 2 + 0.05, 0.0, w / 2 - 0.05):
        bp.box(bm, x - 0.05, x + 0.05, -d / 2, d / 2, 0.0, 0.022, 0)
    return finish(bm, [wood], 'Pallet')


def tray_mesh(w, d):
    """A shallow cardboard tray under small things."""
    bm = bmesh.new()
    card = bp.material('TrayCardboard', (0.66, 0.5, 0.32), rough=0.9)
    x, y, t, lip = w / 2 + 0.012, d / 2 + 0.012, TRAY_T, 0.04
    bp.box(bm, -x, x, -y, y, 0.0, t, 0)
    for x0, x1, y0, y1 in ((-x, x, -y, -y + 0.006), (-x, x, y - 0.006, y), (-x, -x + 0.006, -y, y), (x - 0.006, x, -y, y)):
        bp.box(bm, x0, x1, y0, y1, t, lip, 0)
    return finish(bm, [card], 'Tray')


def straps_mesh(w, d, h):
    """Two straps round a long bundle, across its length."""
    bm = bmesh.new()
    strap = bp.material('Strap', (0.12, 0.14, 0.17), rough=0.5)
    along_y = d >= w
    for s in (-0.3, 0.3):
        if along_y:
            bp.box(bm, -w / 2 - 0.006, w / 2 + 0.006, s * d - 0.02, s * d + 0.02, -0.001, h + 0.006, 0)
        else:
            bp.box(bm, s * w - 0.02, s * w + 0.02, -d / 2 - 0.006, d / 2 + 0.006, -0.001, h + 0.006, 0)
    return finish(bm, [strap], 'Straps')


def block(bm, uv, size, mi, pos):
    """One copy as a plain block with the single's pictures on its faces (see make_bag_pallets.bag_block; no taper here)."""
    sx, sy, sz = size
    lo_ = [(-sx / 2, -sy / 2, 0.0), (sx / 2, -sy / 2, 0.0), (sx / 2, sy / 2, 0.0), (-sx / 2, sy / 2, 0.0)]
    hi_ = [(x, y, sz) for x, y, _ in lo_]
    n = len(bp.VIEWS)
    span = {'top': (sx, sy), 'front': (sx, sz), 'back': (sx, sz), 'left': (sy, sz), 'right': (sy, sz)}

    def tile(view, u, v):
        w, h = span[view]
        m = max(w, h)
        u = 0.5 + (min(max(u, 0.0), 1.0) - 0.5) * w / m
        v = 0.5 + (min(max(v, 0.0), 1.0) - 0.5) * h / m
        return ((bp.VIEWS.index(view) + u) / n, v)

    faces = [
        (hi_, 'top', lambda p: (p[0] / sx + 0.5, p[1] / sy + 0.5)),
        ([lo_[0], lo_[1], hi_[1], hi_[0]], 'front', lambda p: (p[0] / sx + 0.5, p[2] / sz)),
        ([lo_[2], lo_[3], hi_[3], hi_[2]], 'back', lambda p: (0.5 - p[0] / sx, p[2] / sz)),
        ([lo_[3], lo_[0], hi_[0], hi_[3]], 'left', lambda p: (0.5 - p[1] / sy, p[2] / sz)),
        ([lo_[1], lo_[2], hi_[2], hi_[1]], 'right', lambda p: (p[1] / sy + 0.5, p[2] / sz)),
        (lo_[::-1], 'top', lambda p: (p[0] / sx + 0.5, p[1] / sy + 0.5)),
    ]
    for pts, view, fn in faces:
        f = bm.faces.new([bm.verts.new(Vector(p) + Vector(pos)) for p in pts])
        f.material_index = mi
        for loop, p in zip(f.loops, pts):
            loop[uv].uv = tile(view, *fn(p))


def build_stack(item, n, src_manifest):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    loaded = load_single(item)
    if loaded is None:
        print('skip (no model):', item)
        return None
    src, size, tris1 = loaded
    sx, sy, sz = size
    cx, cy, layers = arrange(n, size)
    w, d, h = cx * sx, cy * sy, layers * sz
    # a pallet under things that fit one and fill a fair part of it; small things (cans, buckets) stand in a cardboard tray; long things are strapped
    on_pallet = max(sx, sy) <= 1.3 and w <= 1.5 and d <= 1.3 and min(w, d) >= 0.5 and item not in NO_PALLET
    in_tray = not on_pallet and max(w, d) < 0.9
    z0 = PALLET_H if on_pallet else (TRAY_T if in_tray else 0.0)
    places = [((i - (cx - 1) / 2) * sx, (j - (cy - 1) / 2) * sy, z0 + k * sz) for i, j, k in slots(n, cx, cy, layers)]
    stack = '%s_stack_%d' % (item, n)
    parts = []
    if tris1 <= COPY_TRIS:
        for p in places:
            o = src.copy()
            bpy.context.collection.objects.link(o)
            o.location = p
            parts.append(o)
        bpy.data.objects.remove(src)
        how = 'the single copied %d times' % n
    else:
        lo, hi = measure(src)
        with tempfile.TemporaryDirectory() as tmp:
            pics = bp.photograph(lo, hi, tmp)
        bpy.data.objects.remove(src)
        img = bp.atlas(pics, stack + '_faces')
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new('UVMap')
        for p in places:
            block(bm, uv, (sx * 0.992, sy * 0.992, sz * 0.992), 0, p)
        parts.append(finish(bm, [bp.material('Stacked', image=img)], 'Blocks'))
        how = '%d blocks carrying pictures of the single' % n
    if on_pallet:
        parts.append(pallet_mesh(max(1.2, w + 0.04), max(1.0, d + 0.04)))
    elif in_tray:
        parts.append(tray_mesh(w, d))
    elif max(w, d) > 1.5 and min(w, d) < 1.5:
        parts.append(straps_mesh(w, d, h))
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    obj = parts[0]
    obj.name = stack
    obj.data.name = stack
    folder = os.path.join(BUILD, stack)
    tris, dims = export(obj, folder, stack)

    path = os.path.join(folder, stack + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = json.loads(json.dumps(src_manifest))
        sp = src_manifest['properties']
        m['id'] = stack
        m['icon'] = stack + '.png'
        m['name'] = '%s Stack' % src_manifest['name']          # no count in a name (user rule): the kit and the game show it from pack_quantity
        m['description'] = '%d of %s, %s.' % (n, src_manifest['name'], 'stacked on a wooden pallet' if on_pallet else 'in a cardboard tray' if in_tray else 'stacked together')
        p = m['properties']
        p['weight_kg'] = round(sp['weight_kg'] * n + (PALLET_KG if on_pallet else 0.0), 2)
        p['base_value'] = round(sp['base_value'] * n * 0.9)
        p['max_stack_size'] = 1
        p['placeable'] = True
        p['pack_quantity'] = n
        for k in [k for k in p if k.startswith('look_')]:
            del p[k]
        for k in ('liquid_container', 'container'):
            m.pop(k, None)
    set_model(m, stack, tris, dims)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2)
    with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s\n\n%s\n\nProcedural model (tools/make_material_stacks.py) from `%s`: %d by %d, %d layers, %s; %d triangles, %.2f m tall.\n'
                % (m['name'], m['description'], item, cx, cy, layers, how, tris, dims[2]))
    print('stack', stack, '%dx%dx%d' % (cx, cy, layers), 'pallet' if on_pallet else 'tray' if in_tray else 'bundle', 'copies' if tris1 <= COPY_TRIS else 'blocks', tris, 'tris', dims)
    return stack


def main():
    only = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else None
    for item in MATERIALS:
        if only is not None and item not in only:
            continue
        path = os.path.join(BUILD, item, item + '.json')
        if not os.path.exists(path):
            print('skip (not in the kit):', item)
            continue
        if item in SINGLES:
            build_single(item)
        src_manifest = json.load(open(path, encoding='utf-8'))
        for n in COUNTS_OF.get(item, COUNTS):
            build_stack(item, n, src_manifest)


if __name__ == '__main__':
    main()
