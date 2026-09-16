"""
Headless Blender Script: Trees Batch
Generates 13 high-fidelity 3D low-poly tree models matching their item icons identically:
- Oak (Large, Medium, Small): Gnarled trunk, flared root buttresses, multi-branching canopy, forest green faceted foliage
- Pine (Large, Medium, Small): Straight trunk, 6 tiered conical skirts with faceted zigzag fronds, deep evergreen
- Birch (Large, Medium, Small): Slender white trunk with dark notches, high branches, pastel lime-green foliage clusters
- Maple (Large, Medium, Small): Spreading crown of vibrant fiery autumn red & orange foliage
- Sapling: Young slender sapling stem with small foliage leaves

All models use T_Homesteader_Palette.png, flat shading, metric scaling (cm), and ground-aligned pivots (Zmin=0).
"""

import bpy
import bmesh
import math
import mathutils
import os

HUD_TREES_DIR = r"c:\Users\casey\Desktop\Homesteader\HUD\assets\logging\trees"
UNREAL_TREES_DIR = r"c:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Meshes\logging\trees"
RENDERS_DIR = r"c:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_trees"
PALETTE_PATH = r"c:\Users\casey\Desktop\Homesteader\HUD\assets\textures\palettes\T_Homesteader_Palette.png"

os.makedirs(HUD_TREES_DIR, exist_ok=True)
os.makedirs(UNREAL_TREES_DIR, exist_ok=True)
os.makedirs(RENDERS_DIR, exist_ok=True)

def get_uv(col, row):
    return ((col + 0.5) / 16.0, 1.0 - (row + 0.5) / 16.0)

UV_BARK_DARK    = get_uv(1, 1)  # RGB=(88, 57, 39) Dark bark
UV_WOOD_MID     = get_uv(2, 1)  # RGB=(140, 95, 60) Trunk wood
UV_BIRCH_WHITE  = get_uv(0, 2)  # RGB=(203, 213, 225) Birch white bark
UV_BIRCH_NOTCH  = get_uv(2, 2)  # RGB=(71, 85, 105) Dark notch
UV_OAK_GREEN    = get_uv(2, 5)  # RGB=(34, 197, 94) Forest oak green
UV_OAK_DARK     = get_uv(1, 4)  # Olive green
UV_PINE_GREEN   = get_uv(2, 5)  # Evergreen
UV_BIRCH_GREEN  = get_uv(1, 4)  # Light spring green
UV_MAPLE_RED    = get_uv(3, 4)  # RGB=(220, 38, 38) Autumn red
UV_MAPLE_ORANGE = get_uv(5, 4)  # RGB=(234, 88, 12) Autumn orange

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.film_transparent = True
    
    mat = bpy.data.materials.new(name="M_Homesteader_Palette")
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Roughness'].default_value = 0.65
    
    node_tex = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(PALETTE_PATH):
        img = bpy.data.images.load(PALETTE_PATH)
        img.colorspace_settings.name = 'sRGB'
        node_tex.image = img
        node_tex.interpolation = 'Closest'
        
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    # Sun lights
    l_key = bpy.data.lights.new("KeyLight", type='SUN')
    l_key.energy = 4.2
    l_key.color = (1.0, 0.98, 0.95)
    l_key_obj = bpy.data.objects.new("KeyLight", l_key)
    scene.collection.objects.link(l_key_obj)
    l_key_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(-35))
    
    l_fill = bpy.data.lights.new("FillLight", type='SUN')
    l_fill.energy = 1.8
    l_fill.color = (0.85, 0.90, 1.0)
    l_fill_obj = bpy.data.objects.new("FillLight", l_fill)
    scene.collection.objects.link(l_fill_obj)
    l_fill_obj.rotation_euler = (math.radians(60), math.radians(-30), math.radians(120))
    
    return scene, mat

def add_bmesh_face(bm, uv_layer, verts, uv, double_sided=True):
    col = int(uv[0] * 16.0)
    row = int(round((1.0 - uv[1]) * 16.0 - 0.5))
    
    u_min = (col + 0.25) / 16.0
    u_max = (col + 0.75) / 16.0
    v_min = 1.0 - (row + 0.75) / 16.0
    v_max = 1.0 - (row + 0.25) / 16.0
    
    n = len(verts)
    if n == 4:
        uv_coords = [
            (u_min, v_min),
            (u_max, v_min),
            (u_max, v_max),
            (u_min, v_max)
        ]
    elif n == 3:
        uv_coords = [
            (u_min, v_min),
            (u_max, v_min),
            ((u_min + u_max) * 0.5, v_max)
        ]
    else:
        u_mid = (u_min + u_max) * 0.5
        v_mid = (v_min + v_max) * 0.5
        ru = (u_max - u_min) * 0.45
        rv = (v_max - v_min) * 0.45
        uv_coords = []
        for i in range(n):
            ang = 2.0 * math.pi * i / n
            uv_coords.append((u_mid + ru * math.cos(ang), v_mid + rv * math.sin(ang)))
            
    f = bm.faces.new(verts)
    f.smooth = False
    for loop, uv_pt in zip(f.loops, uv_coords):
        loop[uv_layer].uv = uv_pt
        
    if double_sided:
        verts_rev = [bm.verts.new(v.co) for v in reversed(verts)]
        f_rev = bm.faces.new(verts_rev)
        f_rev.smooth = False
        for loop, uv_pt in zip(f_rev.loops, reversed(uv_coords)):
            loop[uv_layer].uv = uv_pt
            
    return f

def finalize_and_export(mesh, obj, mat, name, ortho_scale=600.0):
    scene = bpy.context.scene
    mesh.materials.append(mat)
    mesh.update()
    
    # Align ground Zmin = 0
    min_z = min(v.co.z for v in mesh.vertices)
    for v in mesh.vertices:
        v.co.z -= min_z
    mesh.update()
    
    max_z = max(v.co.z for v in mesh.vertices)
    mid_z = max_z * 0.5
    
    # Camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho_scale
    cam_data.clip_end = 5000.0
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    dist = 1200.0
    cam_obj.location = (dist * 0.7, -dist * 0.7, mid_z + dist * 0.45)
    direction = -(cam_obj.location - mathutils.Vector((0, 0, mid_z))).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    render_path = os.path.join(RENDERS_DIR, f"{name}_render.png")
    scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
    print(f"  [RENDER] {render_path}")
    
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    for out_dir in [HUD_TREES_DIR, UNREAL_TREES_DIR]:
        obj_path = os.path.join(out_dir, f"{name}.obj")
        bpy.ops.wm.obj_export(
            filepath=obj_path,
            export_selected_objects=True,
            export_materials=True,
            export_uv=True,
            export_normals=True,
            export_smooth_groups=True,
            forward_axis='Y',
            up_axis='Z',
        )
        fbx_path = os.path.join(out_dir, f"{name}.fbx")
        bpy.ops.export_scene.fbx(
            filepath=fbx_path,
            use_selection=True,
            mesh_smooth_type='SMOOTH_GROUP',
            use_tspace=True,
            use_triangles=True,
            axis_forward='Y',
            axis_up='Z',
        )
    print(f"  [EXPORT] {name}.obj and {name}.fbx exported successfully.")

# Helper to add a low-poly icosphere cluster
def add_foliage_blob(bm, uv_layer, center, radius, uv, jitter=0.12, seed=0):
    rng = mathutils.noise
    cx, cy, cz = center
    # 12-vertex icosahedron base
    phi = (1.0 + math.sqrt(5.0)) * 0.5
    raw_verts = [
        (-1,  phi, 0), ( 1,  phi, 0), (-1, -phi, 0), ( 1, -phi, 0),
        (0, -1,  phi), (0,  1,  phi), (0, -1, -phi), (0,  1, -phi),
        ( phi, 0, -1), ( phi, 0,  1), (-phi, 0, -1), (-phi, 0,  1)
    ]
    bm_v = []
    for i, (vx, vy, vz) in enumerate(raw_verts):
        vec = mathutils.Vector((vx, vy, vz)).normalized()
        j = 1.0 + math.sin(i * 3.7 + seed) * jitter
        pos = mathutils.Vector((cx, cy, cz)) + vec * (radius * j)
        bm_v.append(bm.verts.new(pos))
        
    faces_idx = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
    ]
    for idxs in faces_idx:
        add_bmesh_face(bm, uv_layer, [bm_v[idxs[0]], bm_v[idxs[1]], bm_v[idxs[2]]], uv)

# ==============================================================================
# OAK TREES (Gnarled trunk, buttressed root flares, organic canopy)
# ==============================================================================
def build_tree_oak(size_name, scale):
    scene, mat = setup_scene()
    name = f"SM_Tree_Oak_{size_name}"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    h_total = 600.0 * scale
    r_trunk = 45.0 * scale
    
    # 6-sided trunk with root buttress flares
    def make_trunk_ring(z, r, flare=1.0, y_off=0):
        pts = []
        for i in range(6):
            a = i * math.pi / 3.0
            # Root flare ribs on i=0, 2, 4
            f = flare if (i % 2 == 0) else (1.0 + (flare - 1.0) * 0.4)
            pts.append((r * f * math.cos(a), y_off + r * f * math.sin(a), z))
        return [bm.verts.new(p) for p in pts]
    
    r0 = make_trunk_ring(0.0, r_trunk, flare=1.8)     # Base root flare
    r1 = make_trunk_ring(h_total * 0.08, r_trunk, flare=1.3)
    r2 = make_trunk_ring(h_total * 0.22, r_trunk * 0.85, flare=1.05, y_off=10*scale)
    r3 = make_trunk_ring(h_total * 0.40, r_trunk * 0.72, flare=1.0, y_off=18*scale)
    r4 = make_trunk_ring(h_total * 0.55, r_trunk * 0.60, flare=1.0, y_off=12*scale)
    
    trunk_rings = [r0, r1, r2, r3, r4]
    for i in range(len(trunk_rings) - 1):
        for k in range(6):
            kn = (k + 1) % 6
            add_bmesh_face(bm, uv_layer, [trunk_rings[i][k], trunk_rings[i][kn], trunk_rings[i+1][kn], trunk_rings[i+1][k]], UV_BARK_DARK)
            
    # Base cap
    add_bmesh_face(bm, uv_layer, [r0[0], r0[5], r0[4], r0[3], r0[2], r0[1]], UV_BARK_DARK)
    
    # Foliage Canopy Clusters (Faceted icospheres matching icon)
    canopy_specs = [
        # (cx, cy, cz, radius, uv)
        (  0.0,  15.0*scale, h_total * 0.82, 175.0*scale, UV_OAK_GREEN),  # Central crown
        (-120.0*scale, -40.0*scale, h_total * 0.68, 140.0*scale, UV_OAK_DARK),   # Left lobe
        ( 125.0*scale, -30.0*scale, h_total * 0.70, 145.0*scale, UV_OAK_GREEN),  # Right lobe
        (  10.0*scale, 120.0*scale, h_total * 0.65, 135.0*scale, UV_OAK_DARK),   # Front lobe
        (-70.0*scale,  80.0*scale, h_total * 0.78, 120.0*scale, UV_OAK_GREEN),  # Upper-left
        ( 75.0*scale,  70.0*scale, h_total * 0.80, 125.0*scale, UV_OAK_GREEN),  # Upper-right
        (  0.0, -100.0*scale, h_total * 0.62, 115.0*scale, UV_OAK_DARK),   # Back lobe
    ]
    for idx, (cx, cy, cz, rad, uv) in enumerate(canopy_specs):
        add_foliage_blob(bm, uv_layer, (cx, cy, cz), rad, uv, seed=idx * 23)
        
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=h_total * 1.35)

# ==============================================================================
# PINE TREES (Straight trunk, 6 stacked tiered conical skirts with zigzag fronds)
# ==============================================================================
def build_tree_pine(size_name, scale):
    scene, mat = setup_scene()
    name = f"SM_Tree_Pine_{size_name}"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    h_total = 750.0 * scale
    r_trunk = 32.0 * scale
    
    # Straight Trunk (6 sides)
    r0 = []
    r1 = []
    for i in range(6):
        a = i * math.pi / 3.0
        r0.append(bm.verts.new((r_trunk * math.cos(a), r_trunk * math.sin(a), 0.0)))
        r1.append(bm.verts.new((r_trunk * 0.65 * math.cos(a), r_trunk * 0.65 * math.sin(a), h_total * 0.35)))
    for k in range(6):
        kn = (k + 1) % 6
        add_bmesh_face(bm, uv_layer, [r0[k], r0[kn], r1[kn], r1[k]], UV_BARK_DARK)
    add_bmesh_face(bm, uv_layer, [r0[0], r0[5], r0[4], r0[3], r0[2], r0[1]], UV_BARK_DARK)
    
    # 6 Tiered Conical Skirts
    # Each tier: top neck ring -> flared bottom skirt with 8 zigzag points
    tiers = [
        # (z_bot, z_top, r_bot, r_top)
        (h_total * 0.22, h_total * 0.38, 210.0*scale, 105.0*scale),
        (h_total * 0.35, h_total * 0.50, 185.0*scale,  90.0*scale),
        (h_total * 0.48, h_total * 0.63, 155.0*scale,  75.0*scale),
        (h_total * 0.61, h_total * 0.76, 125.0*scale,  58.0*scale),
        (h_total * 0.74, h_total * 0.88,  95.0*scale,  40.0*scale),
        (h_total * 0.86, h_total * 1.00,  65.0*scale,   0.0),       # Top conical cap
    ]
    
    n_pts = 8
    for z_b, z_t, r_b, r_t in tiers:
        # Skirt bottom ring with faceted zigzag fronds
        v_bot = []
        for i in range(n_pts):
            a = i * 2 * math.pi / n_pts
            zig = 1.15 if (i % 2 == 0) else 0.85
            v_bot.append(bm.verts.new((r_b * zig * math.cos(a), r_b * zig * math.sin(a), z_b)))
            
        if r_t > 0:
            v_top = []
            for i in range(n_pts):
                a = i * 2 * math.pi / n_pts
                v_top.append(bm.verts.new((r_t * math.cos(a), r_t * math.sin(a), z_t)))
            for k in range(n_pts):
                kn = (k + 1) % n_pts
                add_bmesh_face(bm, uv_layer, [v_bot[k], v_bot[kn], v_top[kn], v_top[k]], UV_PINE_GREEN)
            # Underside closure
            add_bmesh_face(bm, uv_layer, list(reversed(v_bot)), UV_BARK_DARK)
        else:
            # Top tip apex
            apex = bm.verts.new((0.0, 0.0, z_t))
            for k in range(n_pts):
                kn = (k + 1) % n_pts
                add_bmesh_face(bm, uv_layer, [v_bot[k], v_bot[kn], apex], UV_PINE_GREEN)
            add_bmesh_face(bm, uv_layer, list(reversed(v_bot)), UV_BARK_DARK)
            
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=h_total * 1.25)

# ==============================================================================
# BIRCH TREES (Slender white bark trunk with dark notches, light spring canopy)
# ==============================================================================
def build_tree_birch(size_name, scale):
    scene, mat = setup_scene()
    name = f"SM_Tree_Birch_{size_name}"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    h_total = 680.0 * scale
    r_trunk = 22.0 * scale
    
    # Multi-segmented white trunk with dark notches
    trunk_levels = [
        (0.0,            r_trunk * 1.2, UV_BIRCH_WHITE, 0),
        (h_total * 0.12, r_trunk * 1.0, UV_BIRCH_WHITE, 4),
        (h_total * 0.20, r_trunk * 0.95, UV_BIRCH_NOTCH, 8),  # Dark notch ring
        (h_total * 0.24, r_trunk * 0.92, UV_BIRCH_WHITE, 10),
        (h_total * 0.38, r_trunk * 0.85, UV_BIRCH_WHITE, 15),
        (h_total * 0.44, r_trunk * 0.82, UV_BIRCH_NOTCH, 18),  # Dark notch ring
        (h_total * 0.48, r_trunk * 0.80, UV_BIRCH_WHITE, 20),
        (h_total * 0.65, r_trunk * 0.70, UV_BIRCH_WHITE, 24),
    ]
    
    rings = []
    for z, r, _, y_off in trunk_levels:
        ring = []
        for i in range(6):
            a = i * math.pi / 3.0
            ring.append(bm.verts.new((r * math.cos(a), y_off * scale + r * math.sin(a), z)))
        rings.append(ring)
        
    for i in range(len(rings) - 1):
        uv = trunk_levels[i][2]
        for k in range(6):
            kn = (k + 1) % 6
            add_bmesh_face(bm, uv_layer, [rings[i][k], rings[i][kn], rings[i+1][kn], rings[i+1][k]], uv)
    add_bmesh_face(bm, uv_layer, [rings[0][0], rings[0][5], rings[0][4], rings[0][3], rings[0][2], rings[0][1]], UV_BARK_DARK)
    
    # High oval lime-green foliage clusters
    canopy_specs = [
        (  0.0,  25.0*scale, h_total * 0.84, 135.0*scale, UV_BIRCH_GREEN),
        (-60.0*scale, -20.0*scale, h_total * 0.68, 105.0*scale, UV_BIRCH_GREEN),
        ( 65.0*scale,  10.0*scale, h_total * 0.72, 110.0*scale, UV_BIRCH_GREEN),
        ( 10.0*scale,  75.0*scale, h_total * 0.62,  95.0*scale, UV_BIRCH_GREEN),
    ]
    for idx, (cx, cy, cz, rad, uv) in enumerate(canopy_specs):
        add_foliage_blob(bm, uv_layer, (cx, cy, cz), rad, uv, seed=idx * 17)
        
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=h_total * 1.30)

# ==============================================================================
# MAPLE TREES (Vibrant fiery autumn red & orange foliage)
# ==============================================================================
def build_tree_maple(size_name, scale):
    scene, mat = setup_scene()
    name = f"SM_Tree_Maple_{size_name}"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    h_total = 620.0 * scale
    r_trunk = 40.0 * scale
    
    r0 = []
    r1 = []
    r2 = []
    for i in range(6):
        a = i * math.pi / 3.0
        r0.append(bm.verts.new((r_trunk * 1.4 * math.cos(a), r_trunk * 1.4 * math.sin(a), 0.0)))
        r1.append(bm.verts.new((r_trunk * math.cos(a), r_trunk * math.sin(a), h_total * 0.18)))
        r2.append(bm.verts.new((r_trunk * 0.75 * math.cos(a), r_trunk * 0.75 * math.sin(a), h_total * 0.45)))
        
    for rA, rB in [(r0, r1), (r1, r2)]:
        for k in range(6):
            kn = (k + 1) % 6
            add_bmesh_face(bm, uv_layer, [rA[k], rA[kn], rB[kn], rB[k]], UV_BARK_DARK)
    add_bmesh_face(bm, uv_layer, [r0[0], r0[5], r0[4], r0[3], r0[2], r0[1]], UV_BARK_DARK)
    
    # Dense autumn canopy clusters (Red & Orange)
    canopy_specs = [
        (  0.0,   0.0,       h_total * 0.80, 165.0*scale, UV_MAPLE_RED),
        (-90.0*scale, -40.0*scale, h_total * 0.65, 135.0*scale, UV_MAPLE_ORANGE),
        ( 95.0*scale, -30.0*scale, h_total * 0.66, 140.0*scale, UV_MAPLE_RED),
        (  0.0,  95.0*scale, h_total * 0.62, 130.0*scale, UV_MAPLE_ORANGE),
        (-55.0*scale,  65.0*scale, h_total * 0.75, 120.0*scale, UV_MAPLE_RED),
        ( 60.0*scale,  60.0*scale, h_total * 0.76, 125.0*scale, UV_MAPLE_ORANGE),
    ]
    for idx, (cx, cy, cz, rad, uv) in enumerate(canopy_specs):
        add_foliage_blob(bm, uv_layer, (cx, cy, cz), rad, uv, seed=idx * 29)
        
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=h_total * 1.35)

# ==============================================================================
# TREE SAPLING (Slender young stem with 4 small green foliage leaves)
# ==============================================================================
def build_tree_sapling():
    scene, mat = setup_scene()
    name = "SM_Tree_Sapling"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    h_total = 110.0
    r_stem = 2.4
    
    # Stem (5 sides)
    r0 = []
    r1 = []
    r2 = []
    for i in range(5):
        a = i * 2 * math.pi / 5.0
        r0.append(bm.verts.new((r_stem * 1.3 * math.cos(a), r_stem * 1.3 * math.sin(a), 0.0)))
        r1.append(bm.verts.new((r_stem * math.cos(a), 3.0 + r_stem * math.sin(a), h_total * 0.5)))
        r2.append(bm.verts.new((r_stem * 0.6 * math.cos(a), 8.0 + r_stem * 0.6 * math.sin(a), h_total)))
        
    for rA, rB in [(r0, r1), (r1, r2)]:
        for k in range(5):
            kn = (k + 1) % 5
            add_bmesh_face(bm, uv_layer, [rA[k], rA[kn], rB[kn], rB[k]], UV_WOOD_MID)
    add_bmesh_face(bm, uv_layer, [r0[0], r0[4], r0[3], r0[2], r0[1]], UV_BARK_DARK)
    
    # 4 small sapling leaves radiating from the top stem
    for i, a_deg in enumerate([0, 90, 180, 270]):
        ang = math.radians(a_deg)
        c_a = math.cos(ang)
        s_a = math.sin(ang)
        perp_x = -s_a * 4.0
        perp_y =  c_a * 4.0
        
        bx = 8.0 * s_a
        by = 8.0 * c_a
        
        lv0 = bm.verts.new((bx, by, h_total * 0.85))
        lv1 = bm.verts.new((bx + 12.0 * c_a - perp_x, by + 12.0 * s_a - perp_y, h_total * 0.92))
        lv2 = bm.verts.new((bx + 24.0 * c_a, by + 24.0 * s_a, h_total * 0.95))
        lv3 = bm.verts.new((bx + 12.0 * c_a + perp_x, by + 12.0 * s_a + perp_y, h_total * 0.92))
        
        add_bmesh_face(bm, uv_layer, [lv0, lv1, lv2, lv3], UV_OAK_GREEN)
        
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=140.0)

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == '__main__':
    print("=== BUILDING TREES BATCH IN BLENDER 5.2 ===")
    # 1. Oak Trees
    build_tree_oak("Large",  1.0)
    build_tree_oak("Medium", 0.75)
    build_tree_oak("Small",  0.52)
    
    # 2. Pine Trees
    build_tree_pine("Large",  1.0)
    build_tree_pine("Medium", 0.72)
    build_tree_pine("Small",  0.48)
    
    # 3. Birch Trees
    build_tree_birch("Large",  1.0)
    build_tree_birch("Medium", 0.72)
    build_tree_birch("Small",  0.50)
    
    # 4. Maple Trees
    build_tree_maple("Large",  1.0)
    build_tree_maple("Medium", 0.74)
    build_tree_maple("Small",  0.50)
    
    # 5. Tree Sapling
    build_tree_sapling()
    
    print("\nSUCCESS: All 13 tree models built, rendered, and exported!")
