"""
Headless Blender Script: Ground Clutter Batch
Generates 8 high-fidelity 3D low-poly clutter models matching their item icons identically:
1. SM_Clutter_Branch: Fallen branch with hexagonal cut face, heartwood center, bark rim, side shoots, green leaves
2. SM_Clutter_DirtClump: Faceted earth mound with embedded multi-tone stones
3. SM_Clutter_GrassTuft: Clump of faceted upright tapered grass blades
4. SM_Clutter_Pebbles: Cluster of 8 smooth faceted river pebbles in varied slate/gray tones
5. SM_Clutter_Twigs: Small crossed cluster of fallen woodland twigs
6. SM_Clutter_Leaves: Scattered autumn maple/oak leaves (orange, red, gold)
7. SM_Clutter_Pinecones: Faceted pinecone with layered scales
8. SM_Clutter_Acorns: Oak acorns with faceted caps and nuts

All models use T_Homesteader_Palette.png, flat shading, metric scaling, and ground-aligned pivots (Zmin=0).
"""

import bpy
import bmesh
import math
import mathutils
import os

# Output directories
HUD_MODELS_DIR = r"c:\Users\casey\Desktop\Homesteader\HUD\assets\ground\models"
UNREAL_MODELS_DIR = r"c:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Ground\Meshes"
RENDERS_DIR = r"c:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_clutter"
PALETTE_PATH = r"c:\Users\casey\Desktop\Homesteader\HUD\assets\textures\palettes\T_Homesteader_Palette.png"

os.makedirs(HUD_MODELS_DIR, exist_ok=True)
os.makedirs(UNREAL_MODELS_DIR, exist_ok=True)
os.makedirs(RENDERS_DIR, exist_ok=True)

# Helper: UV coordinates in 16x16 palette
def get_uv(col, row):
    return ((col + 0.5) / 16.0, 1.0 - (row + 0.5) / 16.0)

UV_BARK_DARK    = get_uv(1, 1)  # RGB=(88, 57, 39) Dark bark
UV_WOOD_HEART   = get_uv(0, 0)  # RGB=(222, 184, 135) Light heartwood
UV_WOOD_MID     = get_uv(2, 1)  # RGB=(140, 95, 60) Timber brown
UV_LEAF_GREEN   = get_uv(2, 5)  # RGB=(34, 197, 94) Fresh green leaf
UV_GRASS_GREEN  = get_uv(1, 4)  # RGB=(145, 185, 75) Grass tuft green
UV_GRASS_DARK   = get_uv(2, 5)  # Deep green
UV_DIRT_BROWN   = get_uv(2, 0)  # RGB=(127, 79, 36) Loam brown
UV_DIRT_DARK    = get_uv(4, 0)  # RGB=(92, 45, 15) Dark earth
UV_STONE_LIGHT  = get_uv(0, 2)  # RGB=(203, 213, 225) Light stone
UV_STONE_MID    = get_uv(1, 2)  # RGB=(148, 163, 184) Medium stone
UV_STONE_DARK   = get_uv(2, 2)  # RGB=(71, 85, 105) Dark slate
UV_LEAF_ORANGE  = get_uv(5, 4)  # RGB=(234, 88, 12) Autumn orange
UV_LEAF_RED     = get_uv(3, 4)  # RGB=(220, 38, 38) Autumn red
UV_LEAF_GOLD    = get_uv(4, 6)  # RGB=(234, 179, 8) Autumn gold
UV_PINE_BROWN   = get_uv(7, 1)  # RGB=(60, 42, 28) Pinecone brown
UV_ACORN_CAP    = get_uv(5, 1)  # RGB=(55, 40, 25) Acorn cap

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.film_transparent = True
    
    # Material
    mat = bpy.data.materials.new(name="M_Homesteader_Palette")
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Roughness'].default_value = 0.6
    
    node_tex = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(PALETTE_PATH):
        img = bpy.data.images.load(PALETTE_PATH)
        img.colorspace_settings.name = 'sRGB'
        node_tex.image = img
        node_tex.interpolation = 'Closest'
        
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    # Lighting (Standard low-poly key, fill, rim)
    l_key = bpy.data.lights.new("KeyLight", type='SUN')
    l_key.energy = 4.0
    l_key.color = (1.0, 0.98, 0.95)
    l_key_obj = bpy.data.objects.new("KeyLight", l_key)
    scene.collection.objects.link(l_key_obj)
    l_key_obj.rotation_euler = (math.radians(45), math.radians(15), math.radians(-35))
    
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

def finalize_and_export(mesh, obj, mat, name, ortho_scale=50.0):
    scene = bpy.context.scene
    mesh.materials.append(mat)
    mesh.update()
    
    # Ground alignment: set Zmin = 0
    min_z = min(v.co.z for v in mesh.vertices)
    for v in mesh.vertices:
        v.co.z -= min_z
    mesh.update()
    
    # Render preview
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho_scale
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    # Center camera on object bounds
    max_z = max(v.co.z for v in mesh.vertices)
    mid_z = max_z * 0.5
    cam_obj.location = (150, -150, mid_z + 120)
    
    # Look at center
    direction = -(cam_obj.location - mathutils.Vector((0, 0, mid_z))).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    render_path = os.path.join(RENDERS_DIR, f"{name}_render.png")
    scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
    print(f"  [RENDER] {render_path}")
    
    # Export OBJ & FBX to HUD and Unreal
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    for out_dir in [HUD_MODELS_DIR, UNREAL_MODELS_DIR]:
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

# ==============================================================================
# MODEL 1: SM_Clutter_Branch
# Hexagonal cut log with heartwood, bark rim, side shoots, green leaves
# ==============================================================================
def build_clutter_branch():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("SM_Clutter_Branch")
    obj = bpy.data.objects.new("SM_Clutter_Branch", mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    # Main log: lies along X axis from X=-25 to X=35 cm, radius ~ 4.5 cm
    # Hexagonal rings (6 sides)
    def make_hex(x, y_c, z_c, rad, ang_offset=0):
        pts = []
        for i in range(6):
            a = i * math.pi / 3.0 + ang_offset
            pts.append((x, y_c + rad * math.sin(a), z_c + rad * math.cos(a)))
        return [bm.verts.new(p) for p in pts]
    
    # Cut face at X=-25 cm
    r0 = make_hex(-25, 0, 4.5, 4.5)
    r1 = make_hex(-10, 0, 4.5, 4.2)
    r2 = make_hex(10, 1.0, 4.2, 3.8)
    r3 = make_hex(30, 2.5, 4.0, 3.2)
    r4 = make_hex(38, 3.2, 3.8, 2.4) # Tapered end
    
    rings = [r0, r1, r2, r3, r4]
    for i in range(len(rings) - 1):
        for k in range(6):
            kn = (k + 1) % 6
            add_bmesh_face(bm, uv_layer, [rings[i][k], rings[i][kn], rings[i+1][kn], rings[i+1][k]], UV_BARK_DARK)
            
    # Cut face heartwood cap (X=-25)
    add_bmesh_face(bm, uv_layer, [r0[0], r0[5], r0[4], r0[3], r0[2], r0[1]], UV_WOOD_HEART)
    # End cap (X=38)
    add_bmesh_face(bm, uv_layer, [r4[0], r4[1], r4[2], r4[3], r4[4], r4[5]], UV_BARK_DARK)
    
    # Side branch 1: shoots out at X=-5, angles +Y, +Z
    b1_base = make_hex(-5, 3.5, 5.5, 1.8)
    b1_mid  = make_hex(-2, 12.0, 12.0, 1.4)
    b1_tip  = make_hex(0, 18.0, 18.0, 0.8)
    for i in range(2):
        rA = [b1_base, b1_mid][i]
        rB = [b1_mid, b1_tip][i]
        for k in range(6):
            kn = (k + 1) % 6
            add_bmesh_face(bm, uv_layer, [rA[k], rA[kn], rB[kn], rB[k]], UV_BARK_DARK)
    add_bmesh_face(bm, uv_layer, [b1_tip[0], b1_tip[1], b1_tip[2], b1_tip[3], b1_tip[4], b1_tip[5]], UV_WOOD_HEART)
    
    # Leaf on branch 1
    lf1_v0 = bm.verts.new((-2, 12.0, 12.5))
    lf1_v1 = bm.verts.new((-4, 15.0, 15.0))
    lf1_v2 = bm.verts.new((-1, 19.0, 19.0))
    lf1_v3 = bm.verts.new(( 1, 16.0, 16.5))
    add_bmesh_face(bm, uv_layer, [lf1_v0, lf1_v1, lf1_v2, lf1_v3], UV_LEAF_GREEN)
    
    # Side branch 2: shoots out at X=15, angles -Y, +Z
    b2_base = make_hex(15, -3.0, 4.5, 1.6)
    b2_mid  = make_hex(20, -10.0, 6.0, 1.2)
    b2_tip  = make_hex(25, -16.0, 7.5, 0.7)
    for i in range(2):
        rA = [b2_base, b2_mid][i]
        rB = [b2_mid, b2_tip][i]
        for k in range(6):
            kn = (k + 1) % 6
            add_bmesh_face(bm, uv_layer, [rA[k], rA[kn], rB[kn], rB[k]], UV_BARK_DARK)
    add_bmesh_face(bm, uv_layer, [b2_tip[0], b2_tip[1], b2_tip[2], b2_tip[3], b2_tip[4], b2_tip[5]], UV_WOOD_HEART)
    
    # Leaf on branch 2
    lf2_v0 = bm.verts.new((20, -10.0, 6.5))
    lf2_v1 = bm.verts.new((22, -13.0, 8.5))
    lf2_v2 = bm.verts.new((26, -17.0, 9.5))
    lf2_v3 = bm.verts.new((24, -14.0, 7.5))
    add_bmesh_face(bm, uv_layer, [lf2_v0, lf2_v1, lf2_v2, lf2_v3], UV_LEAF_GREEN)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, "SM_Clutter_Branch", ortho_scale=75.0)

# ==============================================================================
# MODEL 2: SM_Clutter_DirtClump
# Faceted earth mound with embedded multi-tone stones
# ==============================================================================
def build_clutter_dirt_clump():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("SM_Clutter_DirtClump")
    obj = bpy.data.objects.new("SM_Clutter_DirtClump", mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    # Mound base perimeter (8 points, radius ~ 15cm)
    base_pts = [
        (15.0, 0.0, 0.0), (12.0, 11.0, 0.0), (0.0, 14.0, 0.0), (-11.0, 12.0, 0.0),
        (-14.0, 0.0, 0.0), (-12.0, -10.0, 0.0), (0.0, -15.0, 0.0), (11.0, -11.0, 0.0)
    ]
    bv = [bm.verts.new(p) for p in base_pts]
    
    # Mid ring (8 points, radius ~ 10cm, height ~ 6cm)
    mid_pts = [
        (10.0, 0.0, 5.5), (8.0, 8.0, 6.2), (0.0, 9.5, 5.8), (-8.0, 8.0, 6.5),
        (-9.5, 0.0, 6.0), (-8.0, -7.5, 5.5), (0.0, -10.0, 6.2), (8.0, -8.0, 5.8)
    ]
    mv = [bm.verts.new(p) for p in mid_pts]
    
    # Top peak crest (height ~ 12cm)
    tv0 = bm.verts.new((2.0, 1.0, 11.5))
    tv1 = bm.verts.new((-3.0, 2.0, 12.0))
    tv2 = bm.verts.new((-1.0, -3.0, 11.0))
    
    # Lower skirt quads
    for i in range(8):
        inxt = (i + 1) % 8
        uv = UV_DIRT_DARK if i in [4, 5, 6] else UV_DIRT_BROWN
        add_bmesh_face(bm, uv_layer, [bv[i], bv[inxt], mv[inxt], mv[i]], uv)
        
    # Upper slope quads / tris to peaks
    add_bmesh_face(bm, uv_layer, [mv[0], mv[1], tv0], UV_DIRT_BROWN)
    add_bmesh_face(bm, uv_layer, [mv[1], mv[2], tv1, tv0], UV_DIRT_BROWN)
    add_bmesh_face(bm, uv_layer, [mv[2], mv[3], mv[4], tv1], UV_DIRT_DARK)
    add_bmesh_face(bm, uv_layer, [mv[4], mv[5], tv2, tv1], UV_DIRT_DARK)
    add_bmesh_face(bm, uv_layer, [mv[5], mv[6], mv[7], tv2], UV_DIRT_BROWN)
    add_bmesh_face(bm, uv_layer, [mv[7], mv[0], tv0, tv2], UV_DIRT_BROWN)
    add_bmesh_face(bm, uv_layer, [tv0, tv1, tv2], UV_DIRT_BROWN)
    
    # Embedded stones (little faceted rocks on the mound)
    def add_pebble(cx, cy, cz, rad, stone_uv):
        p_pts = [
            (cx + rad, cy, cz), (cx, cy + rad, cz), (cx - rad, cy, cz), (cx, cy - rad, cz),
            (cx, cy, cz + rad * 0.8) # apex
        ]
        pv = [bm.verts.new(p) for p in p_pts]
        add_bmesh_face(bm, uv_layer, [pv[0], pv[1], pv[4]], stone_uv)
        add_bmesh_face(bm, uv_layer, [pv[1], pv[2], pv[4]], stone_uv)
        add_bmesh_face(bm, uv_layer, [pv[2], pv[3], pv[4]], stone_uv)
        add_bmesh_face(bm, uv_layer, [pv[3], pv[0], pv[4]], stone_uv)
        
    add_pebble(5.0, 4.0, 7.0, 2.2, UV_STONE_LIGHT)
    add_pebble(-5.0, -3.0, 6.5, 1.8, UV_STONE_MID)
    add_pebble(2.0, -6.0, 6.0, 2.0, UV_STONE_DARK)
    add_pebble(-4.0, 5.0, 8.0, 1.6, UV_STONE_LIGHT)
    add_pebble(11.0, -4.0, 1.0, 1.5, UV_STONE_MID)
    add_pebble(-10.0, 6.0, 1.0, 1.4, UV_STONE_DARK)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, "SM_Clutter_DirtClump", ortho_scale=38.0)

# ==============================================================================
# MODEL 3: SM_Clutter_GrassTuft
# Dense cluster of faceted upright tapered grass blades
# ==============================================================================
def build_clutter_grass_tuft():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("SM_Clutter_GrassTuft")
    obj = bpy.data.objects.new("SM_Clutter_GrassTuft", mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    # 14 distinct faceted blades spreading outwards
    blade_configs = [
        # (angle_deg, radius, height, bend_out, width, uv)
        (  0,  1.5, 28.0,  6.0, 2.2, UV_GRASS_GREEN),
        ( 25,  2.0, 32.0,  8.0, 2.0, UV_GRASS_GREEN),
        ( 55,  1.8, 26.0,  9.0, 1.8, UV_GRASS_DARK),
        ( 85,  1.2, 34.0,  5.0, 2.1, UV_GRASS_GREEN),
        (115,  2.2, 29.0, 10.0, 1.9, UV_GRASS_DARK),
        (145,  1.5, 36.0,  7.0, 2.3, UV_GRASS_GREEN),
        (175,  2.0, 27.0,  8.0, 2.0, UV_GRASS_DARK),
        (205,  1.8, 33.0,  9.0, 2.1, UV_GRASS_GREEN),
        (235,  2.2, 25.0, 11.0, 1.8, UV_GRASS_DARK),
        (265,  1.5, 35.0,  6.0, 2.2, UV_GRASS_GREEN),
        (295,  2.0, 30.0,  9.0, 2.0, UV_GRASS_GREEN),
        (325,  1.8, 27.0,  8.0, 1.9, UV_GRASS_DARK),
        # Center tall spikes
        ( 45,  0.5, 42.0,  3.0, 2.0, UV_GRASS_GREEN),
        (225,  0.5, 39.0,  4.0, 2.0, UV_GRASS_GREEN),
    ]
    
    for ang_deg, r_base, h, bend, w, uv in blade_configs:
        ang = math.radians(ang_deg)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        # perpendicular vector
        perp_x = -sin_a * (w * 0.5)
        perp_y =  cos_a * (w * 0.5)
        
        # Base verts
        bx = r_base * cos_a
        by = r_base * sin_a
        b_l = bm.verts.new((bx - perp_x, by - perp_y, 0.0))
        b_r = bm.verts.new((bx + perp_x, by + perp_y, 0.0))
        
        # Mid verts (height ~ 0.55*h, slight bend)
        mx = (r_base + bend * 0.45) * cos_a
        my = (r_base + bend * 0.45) * sin_a
        m_l = bm.verts.new((mx - perp_x * 0.7, my - perp_y * 0.7, h * 0.55))
        m_r = bm.verts.new((mx + perp_x * 0.7, my + perp_y * 0.7, h * 0.55))
        
        # Tip vert
        tx = (r_base + bend) * cos_a
        ty = (r_base + bend) * sin_a
        tip = bm.verts.new((tx, ty, h))
        
        # 1 quad + 1 tri per blade
        add_bmesh_face(bm, uv_layer, [b_l, b_r, m_r, m_l], uv)
        add_bmesh_face(bm, uv_layer, [m_l, m_r, tip], uv)
        
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, "SM_Clutter_GrassTuft", ortho_scale=45.0)

# ==============================================================================
# MODEL 4: SM_Clutter_Pebbles
# Cluster of 8 smooth faceted river pebbles
# ==============================================================================
def build_clutter_pebbles():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("SM_Clutter_Pebbles")
    obj = bpy.data.objects.new("SM_Clutter_Pebbles", mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    # 8 pebbles: (cx, cy, rx, ry, rz, uv, num_sides)
    pebble_data = [
        (-12.0,   4.0, 7.5, 5.5, 3.8, UV_STONE_LIGHT, 6),
        (  8.0,   8.0, 8.0, 6.0, 4.2, UV_STONE_MID,   7),
        ( -4.0,  -4.0, 6.5, 5.0, 3.5, UV_STONE_LIGHT, 6),
        (  5.0,  -5.0, 5.5, 4.5, 3.0, UV_STONE_DARK,  6),
        ( 14.0,  -4.0, 5.0, 4.0, 2.8, UV_STONE_MID,   5),
        (-13.0, -10.0, 4.5, 3.8, 2.4, UV_STONE_DARK,  5),
        ( -1.0,  12.0, 4.8, 4.0, 2.6, UV_STONE_MID,   5),
        (  2.0, -12.0, 4.0, 3.2, 2.2, UV_STONE_LIGHT, 5),
    ]
    
    for cx, cy, rx, ry, rz, uv, n_sides in pebble_data:
        # Base ring
        base_v = []
        for i in range(n_sides):
            a = i * 2 * math.pi / n_sides
            base_v.append(bm.verts.new((cx + rx * math.cos(a), cy + ry * math.sin(a), 0.0)))
            
        # Upper dome ring (scaled down and raised)
        up_v = []
        for i in range(n_sides):
            a = i * 2 * math.pi / n_sides
            up_v.append(bm.verts.new((cx + rx * 0.65 * math.cos(a), cy + ry * 0.65 * math.sin(a), rz * 0.7)))
            
        # Top apex
        apex = bm.verts.new((cx, cy, rz))
        
        # Bottom cap
        add_bmesh_face(bm, uv_layer, list(reversed(base_v)), uv)
        
        # Side quads & top tris
        for i in range(n_sides):
            inxt = (i + 1) % n_sides
            add_bmesh_face(bm, uv_layer, [base_v[i], base_v[inxt], up_v[inxt], up_v[i]], uv)
            add_bmesh_face(bm, uv_layer, [up_v[i], up_v[inxt], apex], uv)
            
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, "SM_Clutter_Pebbles", ortho_scale=38.0)

# ==============================================================================
# MODEL 5: SM_Clutter_Twigs
# Small crossed cluster of fallen woodland twigs
# ==============================================================================
def build_clutter_twigs():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("SM_Clutter_Twigs")
    obj = bpy.data.objects.new("SM_Clutter_Twigs", mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    # Function to add a cylindrical stick (5 sides)
    def add_stick(p0, p1, rad, uv):
        v0 = mathutils.Vector(p0)
        v1 = mathutils.Vector(p1)
        axis = (v1 - v0).normalized()
        up = mathutils.Vector((0, 0, 1)) if abs(axis.z) < 0.9 else mathutils.Vector((1, 0, 0))
        side = axis.cross(up).normalized()
        up = side.cross(axis).normalized()
        
        rA = []
        rB = []
        for i in range(5):
            a = i * 2 * math.pi / 5
            off = (side * math.cos(a) + up * math.sin(a)) * rad
            rA.append(bm.verts.new(v0 + off))
            rB.append(bm.verts.new(v1 + off * 0.8)) # slight taper
            
        for k in range(5):
            kn = (k + 1) % 5
            add_bmesh_face(bm, uv_layer, [rA[k], rA[kn], rB[kn], rB[k]], uv)
        add_bmesh_face(bm, uv_layer, [rA[0], rA[4], rA[3], rA[2], rA[1]], UV_WOOD_HEART)
        add_bmesh_face(bm, uv_layer, [rB[0], rB[1], rB[2], rB[3], rB[4]], UV_WOOD_HEART)
        
    # Main stick 1
    add_stick((-16.0, -8.0, 0.5), (14.0, 10.0, 1.2), 1.1, UV_BARK_DARK)
    # Offshoot on stick 1
    add_stick((-2.0, 0.5, 0.8), (4.0, 7.0, 2.0), 0.7, UV_BARK_DARK)
    
    # Crossed stick 2
    add_stick((-10.0, 12.0, 1.5), (16.0, -9.0, 0.5), 1.0, UV_WOOD_MID)
    # Offshoot on stick 2
    add_stick((2.0, 2.5, 1.2), (10.0, 5.0, 1.8), 0.6, UV_WOOD_MID)
    
    # Small third twig
    add_stick((-6.0, -11.0, 0.4), (8.0, -7.0, 0.8), 0.8, UV_BARK_DARK)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, "SM_Clutter_Twigs", ortho_scale=38.0)

# ==============================================================================
# MODEL 6: SM_Clutter_Leaves
# Scattered autumn leaves (orange, red, gold)
# ==============================================================================
def build_clutter_leaves():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("SM_Clutter_Leaves")
    obj = bpy.data.objects.new("SM_Clutter_Leaves", mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    # Function to add a 5-pointed low-poly maple/oak leaf
    def add_leaf(cx, cy, cz, rot_deg, scale, uv):
        rot = math.radians(rot_deg)
        c_r = math.cos(rot)
        s_r = math.sin(rot)
        
        pts_local = [
            ( 0.0, -3.0, 0.0),   # 0: stem base
            ( 0.0,  0.0, 0.6),   # 1: center vein
            ( 0.0,  4.5, 0.8),   # 2: top tip
            ( 2.2,  3.0, 0.4),   # 3: top-right lobe
            ( 3.5,  0.5, 0.2),   # 4: mid-right lobe
            ( 2.0, -1.5, 0.1),   # 5: bot-right lobe
            (-2.0, -1.5, 0.1),   # 6: bot-left lobe
            (-3.5,  0.5, 0.2),   # 7: mid-left lobe
            (-2.2,  3.0, 0.4),   # 8: top-left lobe
        ]
        
        lv = []
        for lx, ly, lz in pts_local:
            gx = cx + (lx * c_r - ly * s_r) * scale
            gy = cy + (lx * s_r + ly * c_r) * scale
            gz = cz + lz * scale
            lv.append(bm.verts.new((gx, gy, gz)))
            
        # Quads per leaf
        for quad in [[lv[0], lv[5], lv[4], lv[1]], [lv[1], lv[4], lv[3], lv[2]],
                     [lv[0], lv[1], lv[7], lv[6]], [lv[1], lv[2], lv[8], lv[7]]]:
            add_bmesh_face(bm, uv_layer, quad, uv)
            
    add_leaf(-6.0,   3.0, 0.2,   25, 2.2, UV_LEAF_ORANGE)
    add_leaf( 5.0,   6.0, 0.5,  -45, 2.4, UV_LEAF_RED)
    add_leaf( 7.0,  -4.0, 0.3,   70, 2.1, UV_LEAF_GOLD)
    add_leaf(-4.0,  -6.0, 0.4, -110, 2.0, UV_LEAF_ORANGE)
    add_leaf( 0.0,   0.0, 0.8,   10, 2.3, UV_LEAF_RED)
    add_leaf(-11.0, -2.0, 0.1,  -65, 1.8, UV_LEAF_GOLD)
    add_leaf( 11.0,  2.0, 0.2,  135, 1.7, UV_LEAF_ORANGE)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, "SM_Clutter_Leaves", ortho_scale=36.0)

# ==============================================================================
# MODEL 7: SM_Clutter_Pinecones
# Faceted pinecone with layered scales
# ==============================================================================
def build_clutter_pinecones():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("SM_Clutter_Pinecones")
    obj = bpy.data.objects.new("SM_Clutter_Pinecones", mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    def add_single_pinecone(cx, cy, tilt_deg, scale):
        tilt = math.radians(tilt_deg)
        # 5 tiers of 6 scales each
        tiers = [
            ( 1.5, 2.2),
            ( 4.5, 3.6),
            ( 8.0, 4.0),
            (11.5, 3.2),
            (14.5, 1.8),
        ]
        
        t_v = []
        for t_idx, (tz, trad) in enumerate(tiers):
            ring = []
            rot_off = (t_idx % 2) * (math.pi / 6.0)
            for i in range(6):
                a = i * 2 * math.pi / 6.0 + rot_off
                lx = trad * math.cos(a) * scale
                ly = trad * math.sin(a) * scale
                lz = tz * scale
                # Tilt
                rx = cx + lx * math.cos(tilt) - lz * math.sin(tilt)
                ry = cy + ly
                rz = lx * math.sin(tilt) + lz * math.cos(tilt)
                ring.append(bm.verts.new((rx, ry, rz)))
            t_v.append(ring)
            
        # Connect tiers
        for t in range(len(tiers) - 1):
            for k in range(6):
                kn = (k + 1) % 6
                add_bmesh_face(bm, uv_layer, [t_v[t][k], t_v[t][kn], t_v[t+1][kn], t_v[t+1][k]], UV_PINE_BROWN)
        # Base and Top caps
        add_bmesh_face(bm, uv_layer, [t_v[0][0], t_v[0][5], t_v[0][4], t_v[0][3], t_v[0][2], t_v[0][1]], UV_PINE_BROWN)
        add_bmesh_face(bm, uv_layer, [t_v[-1][0], t_v[-1][1], t_v[-1][2], t_v[-1][3], t_v[-1][4], t_v[-1][5]], UV_PINE_BROWN)
        
    add_single_pinecone(-4.0, -2.0,  15, 1.0)
    add_single_pinecone( 5.0,  3.0, -25, 0.85)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, "SM_Clutter_Pinecones", ortho_scale=32.0)

# ==============================================================================
# MODEL 8: SM_Clutter_Acorns
# Oak acorns with faceted caps and nuts
# ==============================================================================
def build_clutter_acorns():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("SM_Clutter_Acorns")
    obj = bpy.data.objects.new("SM_Clutter_Acorns", mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    def add_single_acorn(cx, cy, tilt_deg, scale):
        tilt = math.radians(tilt_deg)
        # 6-sided acorn: stem -> cap rim -> nut equator -> nut tip
        def make_acorn_ring(z, r):
            pts = []
            for i in range(6):
                a = i * 2 * math.pi / 6.0
                lx = r * math.cos(a) * scale
                ly = r * math.sin(a) * scale
                lz = z * scale
                rx = cx + lx * math.cos(tilt) - lz * math.sin(tilt)
                ry = cy + ly
                rz = lx * math.sin(tilt) + lz * math.cos(tilt)
                pts.append(bm.verts.new((rx, ry, rz)))
            return pts
            
        r_stem = make_acorn_ring(9.0, 0.5)
        r_cap_top = make_acorn_ring(8.0, 2.2)
        r_cap_rim = make_acorn_ring(6.0, 3.2)
        r_nut_mid = make_acorn_ring(3.0, 2.9)
        
        # Nut apex
        tip_x = cx - 0.0 * math.sin(tilt)
        tip_z = 0.0 * math.cos(tilt)
        tip = bm.verts.new((tip_x, cy, tip_z))
        
        # Stem to cap
        for k in range(6):
            kn = (k + 1) % 6
            add_bmesh_face(bm, uv_layer, [r_stem[k], r_stem[kn], r_cap_top[kn], r_cap_top[k]], UV_ACORN_CAP)
            add_bmesh_face(bm, uv_layer, [r_cap_top[k], r_cap_top[kn], r_cap_rim[kn], r_cap_rim[k]], UV_ACORN_CAP)
            add_bmesh_face(bm, uv_layer, [r_cap_rim[k], r_cap_rim[kn], r_nut_mid[kn], r_nut_mid[k]], UV_WOOD_MID)
            add_bmesh_face(bm, uv_layer, [r_nut_mid[k], r_nut_mid[kn], tip], UV_WOOD_MID)
            
    add_single_acorn(-4.0, -2.0,  30, 1.2)
    add_single_acorn( 4.0,  2.0, -40, 1.0)
    add_single_acorn( 1.0, -5.0,  60, 0.9)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, "SM_Clutter_Acorns", ortho_scale=28.0)

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == '__main__':
    print("=== BUILDING GROUND CLUTTER BATCH IN BLENDER 5.2 ===")
    build_clutter_branch()
    build_clutter_dirt_clump()
    build_clutter_grass_tuft()
    build_clutter_pebbles()
    build_clutter_twigs()
    build_clutter_leaves()
    build_clutter_pinecones()
    build_clutter_acorns()
    print("\nSUCCESS: All 8 ground clutter models built, rendered, and exported!")
