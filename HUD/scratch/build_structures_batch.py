"""
Headless Blender Script: Buildings & Structures Batch (14 Models) - Refined
Generates 14 high-fidelity 3D low-poly building models matching their item icons identically:
 1. SM_Struct_Barn
 2. SM_Struct_Cabin_Small
 3. SM_Struct_Cabin_Large
 4. SM_Struct_Shed
 5. SM_Struct_House_Starter
 6. SM_Struct_House_Farmhouse
 7. SM_Struct_Coop_Chicken
 8. SM_Struct_Silo
 9. SM_Struct_Greenhouse
10. SM_Struct_Stable
11. SM_Struct_Tent_Canvas
12. SM_Struct_Tent_Dome
13. SM_Struct_Camper_RV
14. SM_Struct_Camper_Teardrop

All models use T_Homesteader_Palette.png, flat shading, metric scaling (cm), and ground-aligned pivots (Zmin=0).
"""

import bpy
import bmesh
import math
import mathutils
import os

HUD_STRUCT_DIR = r"c:\Users\casey\Desktop\Homesteader\HUD\assets\building\structures"
UNREAL_STRUCT_DIR = r"c:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Meshes\building\structures"
RENDERS_DIR = r"c:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_structures"
PALETTE_PATH = r"c:\Users\casey\Desktop\Homesteader\HUD\assets\textures\palettes\T_Homesteader_Palette.png"

os.makedirs(HUD_STRUCT_DIR, exist_ok=True)
os.makedirs(UNREAL_STRUCT_DIR, exist_ok=True)
os.makedirs(RENDERS_DIR, exist_ok=True)

def get_uv(col, row):
    return ((col + 0.5) / 16.0, 1.0 - (row + 0.5) / 16.0)

# Master Palette UV definitions for Structures
UV_WOOD_LIGHT   = get_uv(0, 0)   # #deb887 Light wood planks / tan canvas
UV_WOOD_WARM    = get_uv(1, 0)   # #b08968 Warm pine wood
UV_WOOD_MID     = get_uv(2, 1)   # #8c5f3c Medium timber
UV_WOOD_DARK    = get_uv(1, 1)   # #583927 Dark bark / log shadow
UV_WOOD_DEEP    = get_uv(4, 0)   # #5c2d0f Deep dark wood
UV_CREAM_WALL   = get_uv(3, 0)   # #ebe6dc Warm farmhouse cream
UV_WHITE_TRIM   = get_uv(1, 8)   # #f5f5f0 Clean off-white trim
UV_PURE_WHITE   = get_uv(5, 8)   # #ffffff Pure white
UV_RED_BARN     = get_uv(3, 4)   # #dc2626 Classic barn red
UV_RED_DARK     = get_uv(0, 7)   # #b91c1c Deep barn red shadow
UV_TIN_ROOF     = get_uv(0, 2)   # #cbd5e1 Light galvanized sheet metal
UV_STEEL_MID    = get_uv(1, 2)   # #94a3b8 Medium grey steel
UV_STEEL_DARK   = get_uv(2, 2)   # #475569 Dark gunmetal / frame
UV_STONE_GREY   = get_uv(1, 3)   # #787d84 Stone chimney
UV_STONE_LIGHT  = get_uv(0, 3)   # #aaafb4 Light stone
UV_GLASS_CYAN   = get_uv(0, 12)  # #bae6fd Light greenhouse glass
UV_WINDOW_DARK  = get_uv(2, 3)   # #414b58 Dark tinted glass
UV_RV_BLUE      = get_uv(0, 10)  # #2563eb RV stripe & awning blue
UV_TENT_ORANGE  = get_uv(5, 4)   # #ea580c Dome tent orange rainfly
UV_TENT_BODY    = get_uv(2, 2)   # #475569 Dome tent grey-blue fabric
UV_TIRE_RUBBER  = get_uv(4, 15)  # #14161c Tire black
UV_CHROME_HUB   = get_uv(1, 15)  # #c8cdd7 Chrome hubcap
UV_GOLD_ACCENT  = get_uv(4, 6)   # #eab308 Brass / amber indicator
UV_SHINGLE_ROOF = get_uv(4, 4)   # #c3965f Warm roof shingles

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.film_transparent = True
    
    mat = bpy.data.materials.new(name="M_Homesteader_Palette")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Roughness'].default_value = 0.60
    
    node_tex = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(PALETTE_PATH):
        img = bpy.data.images.load(PALETTE_PATH)
        img.colorspace_settings.name = 'sRGB'
        node_tex.image = img
        node_tex.interpolation = 'Closest'
        
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    # Lighting setup
    l_key = bpy.data.lights.new("KeyLight", type='SUN')
    l_key.energy = 4.0
    l_key.color = (1.0, 0.98, 0.95)
    l_key_obj = bpy.data.objects.new("KeyLight", l_key)
    scene.collection.objects.link(l_key_obj)
    l_key_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(-35))
    
    l_fill = bpy.data.lights.new("FillLight", type='SUN')
    l_fill.energy = 1.9
    l_fill.color = (0.85, 0.90, 1.0)
    l_fill_obj = bpy.data.objects.new("FillLight", l_fill)
    scene.collection.objects.link(l_fill_obj)
    l_fill_obj.rotation_euler = (math.radians(60), math.radians(-30), math.radians(120))
    
    return scene, mat

def add_bmesh_face(bm, uv_layer, verts, uv, double_sided=True):
    col = int(uv[0] * 16.0)
    row = int(round((1.0 - uv[1]) * 16.0 - 0.5))
    
    # Safe 25% margin within the solid color cell to avoid any texture filtering bleed
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

def add_box(bm, uv_layer, min_co, max_co, uv_dict, double_sided=True):
    x0, y0, z0 = min_co
    x1, y1, z1 = max_co
    
    v000 = bm.verts.new((x0, y0, z0))
    v001 = bm.verts.new((x0, y0, z1))
    v010 = bm.verts.new((x0, y1, z0))
    v011 = bm.verts.new((x0, y1, z1))
    v100 = bm.verts.new((x1, y0, z0))
    v101 = bm.verts.new((x1, y0, z1))
    v110 = bm.verts.new((x1, y1, z0))
    v111 = bm.verts.new((x1, y1, z1))
    
    def uv_for(side):
        if isinstance(uv_dict, dict):
            return uv_dict.get(side, UV_WHITE_TRIM)
        return uv_dict

    # Outward face windings:
    # -Z (bottom): normal (0, 0, -1)
    add_bmesh_face(bm, uv_layer, [v000, v010, v110, v100], uv_for('nz'), double_sided=double_sided)
    # +Z (top): normal (0, 0, +1)
    add_bmesh_face(bm, uv_layer, [v001, v101, v111, v011], uv_for('pz'), double_sided=double_sided)
    # -Y (front): normal (0, -1, 0)
    add_bmesh_face(bm, uv_layer, [v000, v100, v101, v001], uv_for('ny'), double_sided=double_sided)
    # +Y (back): normal (0, +1, 0)
    add_bmesh_face(bm, uv_layer, [v010, v011, v111, v110], uv_for('py'), double_sided=double_sided)
    # -X (left): normal (-1, 0, 0)
    add_bmesh_face(bm, uv_layer, [v000, v001, v011, v010], uv_for('nx'), double_sided=double_sided)
    # +X (right): normal (+1, 0, 0)
    add_bmesh_face(bm, uv_layer, [v100, v110, v111, v101], uv_for('px'), double_sided=double_sided)

def add_cylinder_z(bm, uv_layer, z0, z1, r, sides, uv_side, uv_cap=None, cx=0.0, cy=0.0, double_sided=True):
    v_bot = []
    v_top = []
    for i in range(sides):
        a = i * 2.0 * math.pi / sides
        v_bot.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z0)))
        v_top.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z1)))
    for i in range(sides):
        nxt = (i + 1) % sides
        add_bmesh_face(bm, uv_layer, [v_bot[i], v_bot[nxt], v_top[nxt], v_top[i]], uv_side, double_sided=double_sided)
    if uv_cap:
        add_bmesh_face(bm, uv_layer, list(reversed(v_bot)), uv_cap, double_sided=double_sided)
        add_bmesh_face(bm, uv_layer, v_top, uv_cap, double_sided=double_sided)

def add_cylinder_x(bm, uv_layer, x0, x1, r, sides, uv_side, uv_cap=None, cy=0.0, cz=0.0, double_sided=True):
    v_left = []
    v_right = []
    min_x = min(x0, x1)
    max_x = max(x0, x1)
    for i in range(sides):
        a = i * 2.0 * math.pi / sides
        v_left.append(bm.verts.new((min_x, cy + r * math.cos(a), cz + r * math.sin(a))))
        v_right.append(bm.verts.new((max_x, cy + r * math.cos(a), cz + r * math.sin(a))))
    for i in range(sides):
        nxt = (i + 1) % sides
        add_bmesh_face(bm, uv_layer, [v_left[i], v_left[nxt], v_right[nxt], v_right[i]], uv_side, double_sided=double_sided)
    if uv_cap:
        add_bmesh_face(bm, uv_layer, list(reversed(v_left)), uv_cap, double_sided=double_sided)
        add_bmesh_face(bm, uv_layer, v_right, uv_cap, double_sided=double_sided)

def add_cylinder_y(bm, uv_layer, y0, y1, r, sides, uv_side, uv_cap=None, cx=0.0, cz=0.0, double_sided=True):
    v_front = []
    v_back = []
    min_y = min(y0, y1)
    max_y = max(y0, y1)
    for i in range(sides):
        a = i * 2.0 * math.pi / sides
        v_front.append(bm.verts.new((cx + r * math.cos(a), min_y, cz + r * math.sin(a))))
        v_back.append(bm.verts.new((cx + r * math.cos(a), max_y, cz + r * math.sin(a))))
    for i in range(sides):
        nxt = (i + 1) % sides
        add_bmesh_face(bm, uv_layer, [v_front[i], v_back[i], v_back[nxt], v_front[nxt]], uv_side, double_sided=double_sided)
    if uv_cap:
        add_bmesh_face(bm, uv_layer, list(reversed(v_front)), uv_cap, double_sided=double_sided)
        add_bmesh_face(bm, uv_layer, v_back, uv_cap, double_sided=double_sided)

def add_diagonal_strip(bm, uv_layer, x0, z0, x1, z1, y_front, w, uv):
    dx = x1 - x0
    dz = z1 - z0
    length = math.hypot(dx, dz)
    if length < 1e-4: return
    nx = -dz / length * (w * 0.5)
    nz =  dx / length * (w * 0.5)
    
    v0 = bm.verts.new((x0 + nx, y_front, z0 + nz))
    v1 = bm.verts.new((x1 + nx, y_front, z1 + nz))
    v2 = bm.verts.new((x1 - nx, y_front, z1 - nz))
    v3 = bm.verts.new((x0 - nx, y_front, z0 - nz))
    add_bmesh_face(bm, uv_layer, [v0, v1, v2, v3], uv, double_sided=True)

def add_diagonal_strip_yz(bm, uv_layer, y0, z0, y1, z1, x_face, w, uv):
    dy = y1 - y0
    dz = z1 - z0
    length = math.hypot(dy, dz)
    if length < 1e-4: return
    ny = -dz / length * (w * 0.5)
    nz =  dy / length * (w * 0.5)
    
    v0 = bm.verts.new((x_face, y0 + ny, z0 + nz))
    v1 = bm.verts.new((x_face, y1 + ny, z1 + nz))
    v2 = bm.verts.new((x_face, y1 - ny, z1 - nz))
    v3 = bm.verts.new((x_face, y0 - ny, z0 - nz))
    add_bmesh_face(bm, uv_layer, [v0, v1, v2, v3], uv, double_sided=True)

def finalize_and_export(mesh, obj, mat, name, ortho_scale=800.0, view_angle=(0.7, -0.7, 0.55)):
    scene = bpy.context.scene
    mesh.materials.append(mat)
    mesh.update()
    
    # Ground alignment: Zmin = 0
    min_z = min(v.co.z for v in mesh.vertices)
    for v in mesh.vertices:
        v.co.z -= min_z
    mesh.update()
    
    max_z = max(v.co.z for v in mesh.vertices)
    mid_z = max_z * 0.45
    
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho_scale
    cam_data.clip_end = 15000.0
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    dist = 2500.0
    vx, vy, vz = view_angle
    cam_obj.location = (dist * vx, dist * vy, mid_z + dist * vz)
    direction = -(cam_obj.location - mathutils.Vector((0, 0, mid_z))).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    render_path = os.path.join(RENDERS_DIR, f"{name}_render.png")
    scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
    print(f"  [RENDER] {render_path}")
    
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    for out_dir in [HUD_STRUCT_DIR, UNREAL_STRUCT_DIR]:
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
# 1. SM_Struct_Barn (Classic Gambrel Barn with Cupola, White Trim, Sliding Doors)
# ==============================================================================
def build_struct_barn():
    scene, mat = setup_scene()
    name = "SM_Struct_Barn"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l, h_wall = 600.0, 800.0, 320.0
    hw, hl = w * 0.5, l * 0.5
    
    # Lower barn main body (Red siding)
    add_box(bm, uv_layer, (-hw, -hl, 0), (hw, hl, h_wall), UV_RED_BARN)
    
    # White corner trim posts
    trim = 12.0
    for cx in [-hw, hw - trim]:
        for cy in [-hl, hl - trim]:
            add_box(bm, uv_layer, (cx, cy, 0), (cx + trim, cy + trim, h_wall), UV_WHITE_TRIM)
            
    # Base trim board
    add_box(bm, uv_layer, (-hw - 4, -hl - 4, 0), (hw + 4, hl + 4, 15), UV_WHITE_TRIM)
    # Mid belt trim board
    add_box(bm, uv_layer, (-hw - 3, -hl - 3, h_wall - 10), (hw + 3, hl + 3, h_wall), UV_WHITE_TRIM)
    
    # Gambrel Roof
    z_break = h_wall + 150.0
    z_peak = h_wall + 260.0
    x_break = hw * 0.78
    overhang = 25.0
    
    # Front gable polygon (-Y)
    v_g0 = bm.verts.new((-hw, -hl, h_wall))
    v_g1 = bm.verts.new((-x_break, -hl, z_break))
    v_g2 = bm.verts.new((0.0, -hl, z_peak))
    v_g3 = bm.verts.new((x_break, -hl, z_break))
    v_g4 = bm.verts.new((hw, -hl, h_wall))
    add_bmesh_face(bm, uv_layer, [v_g0, v_g1, v_g2, v_g3, v_g4], UV_RED_BARN)
    
    # Back gable polygon (+Y)
    v_bg0 = bm.verts.new((-hw, hl, h_wall))
    v_bg1 = bm.verts.new((-x_break, hl, z_break))
    v_bg2 = bm.verts.new((0.0, hl, z_peak))
    v_bg3 = bm.verts.new((x_break, hl, z_break))
    v_bg4 = bm.verts.new((hw, hl, h_wall))
    add_bmesh_face(bm, uv_layer, [v_bg4, v_bg3, v_bg2, v_bg1, v_bg0], UV_RED_BARN)
    
    # Gambrel Roof Panels (Light Galvanized Sheet Metal / Tin)
    y_front = -hl - overhang
    y_back = hl + overhang
    
    # Left steep slope
    r_l_bot_f = bm.verts.new((-hw - 20, y_front, h_wall - 10))
    r_l_bot_b = bm.verts.new((-hw - 20, y_back, h_wall - 10))
    r_l_mid_f = bm.verts.new((-x_break - 6, y_front, z_break + 6))
    r_l_mid_b = bm.verts.new((-x_break - 6, y_back, z_break + 6))
    add_bmesh_face(bm, uv_layer, [r_l_bot_f, r_l_mid_f, r_l_mid_b, r_l_bot_b], UV_TIN_ROOF)
    
    # Left shallow slope
    r_l_top_f = bm.verts.new((0.0, y_front, z_peak + 8))
    r_l_top_b = bm.verts.new((0.0, y_back, z_peak + 8))
    add_bmesh_face(bm, uv_layer, [r_l_mid_f, r_l_top_f, r_l_top_b, r_l_mid_b], UV_TIN_ROOF)
    
    # Right shallow slope
    r_r_mid_f = bm.verts.new((x_break + 6, y_front, z_break + 6))
    r_r_mid_b = bm.verts.new((x_break + 6, y_back, z_break + 6))
    add_bmesh_face(bm, uv_layer, [r_l_top_f, r_r_mid_f, r_r_mid_b, r_l_top_b], UV_TIN_ROOF)
    
    # Right steep slope
    r_r_bot_f = bm.verts.new((hw + 20, y_front, h_wall - 10))
    r_r_bot_b = bm.verts.new((hw + 20, y_back, h_wall - 10))
    add_bmesh_face(bm, uv_layer, [r_r_mid_f, r_r_bot_f, r_r_bot_b, r_r_mid_b], UV_TIN_ROOF)
    
    # White roof edge fascia trim on front and back
    add_bmesh_face(bm, uv_layer, [r_l_bot_f, r_l_mid_f, v_g1, v_g0], UV_WHITE_TRIM)
    add_bmesh_face(bm, uv_layer, [r_l_mid_f, r_l_top_f, v_g2, v_g1], UV_WHITE_TRIM)
    add_bmesh_face(bm, uv_layer, [r_l_top_f, r_r_mid_f, v_g3, v_g2], UV_WHITE_TRIM)
    add_bmesh_face(bm, uv_layer, [r_r_mid_f, r_r_bot_f, v_g4, v_g3], UV_WHITE_TRIM)
    
    # Rooftop Cupola (Square red box with pyramid tin roof)
    cw = 110.0
    ch = 90.0
    hcw = cw * 0.5
    z_cup_bot = z_peak - 10.0
    z_cup_top = z_cup_bot + ch
    add_box(bm, uv_layer, (-hcw, -hcw, z_cup_bot), (hcw, hcw, z_cup_top), UV_RED_BARN)
    for cx in [-hcw, hcw - 8]:
        for cy in [-hcw, hcw - 8]:
            add_box(bm, uv_layer, (cx, cy, z_cup_bot), (cx + 8, cy + 8, z_cup_top), UV_WHITE_TRIM)
    cp0 = bm.verts.new((-hcw - 15, -hcw - 15, z_cup_top))
    cp1 = bm.verts.new(( hcw + 15, -hcw - 15, z_cup_top))
    cp2 = bm.verts.new(( hcw + 15,  hcw + 15, z_cup_top))
    cp3 = bm.verts.new((-hcw - 15,  hcw + 15, z_cup_top))
    c_apex = bm.verts.new((0, 0, z_cup_top + 60.0))
    add_bmesh_face(bm, uv_layer, [cp0, cp1, c_apex], UV_TIN_ROOF)
    add_bmesh_face(bm, uv_layer, [cp1, cp2, c_apex], UV_TIN_ROOF)
    add_bmesh_face(bm, uv_layer, [cp2, cp3, c_apex], UV_TIN_ROOF)
    add_bmesh_face(bm, uv_layer, [cp3, cp0, c_apex], UV_TIN_ROOF)
    
    # Front Sliding Barn Doors with White X-Brace Frame
    dw, dh = 240.0, 220.0
    hdw = dw * 0.5
    dy = -hl - 5.0
    # Top track
    add_box(bm, uv_layer, (-hdw - 20, dy - 6, dh + 5), (hdw + 20, dy, dh + 18), UV_WHITE_TRIM)
    # Left red door panel
    add_box(bm, uv_layer, (-hdw, dy - 3, 0), (-2, dy - 1, dh), UV_RED_DARK)
    # Right red door panel
    add_box(bm, uv_layer, (2, dy - 3, 0), (hdw, dy - 1, dh), UV_RED_DARK)
    # Left door white border
    add_box(bm, uv_layer, (-hdw, dy - 5, 0), (-hdw + 10, dy - 2, dh), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-12, dy - 5, 0), (-2, dy - 2, dh), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-hdw, dy - 5, dh - 10), (-2, dy - 2, dh), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-hdw, dy - 5, 0), (-2, dy - 2, 10), UV_WHITE_TRIM)
    # Right door white border
    add_box(bm, uv_layer, (2, dy - 5, 0), (12, dy - 2, dh), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (hdw - 10, dy - 5, 0), (hdw, dy - 2, dh), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (2, dy - 5, dh - 10), (hdw, dy - 2, dh), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (2, dy - 5, 0), (hdw, dy - 2, 10), UV_WHITE_TRIM)
    
    # Left door X braces
    add_diagonal_strip(bm, uv_layer, -hdw + 10, 10, -12, dh - 10, dy - 5.5, 9.0, UV_WHITE_TRIM)
    add_diagonal_strip(bm, uv_layer, -hdw + 10, dh - 10, -12, 10, dy - 5.5, 9.0, UV_WHITE_TRIM)
    # Right door X braces
    add_diagonal_strip(bm, uv_layer, 12, 10, hdw - 10, dh - 10, dy - 5.5, 9.0, UV_WHITE_TRIM)
    add_diagonal_strip(bm, uv_layer, 12, dh - 10, hdw - 10, 10, dy - 5.5, 9.0, UV_WHITE_TRIM)
    
    # Upper hayloft square window with white trim and dark glass pane
    add_box(bm, uv_layer, (-45, dy - 4, z_break - 20), (45, dy, z_break + 70), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-35, dy - 6, z_break - 10), (35, dy - 3, z_break + 60), UV_WINDOW_DARK)
    add_box(bm, uv_layer, (-3, dy - 8, z_break - 10), (3, dy - 5, z_break + 60), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-35, dy - 8, z_break + 22), (35, dy - 5, z_break + 28), UV_WHITE_TRIM)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=1050.0)

# ==============================================================================
# 2. SM_Struct_Cabin_Small (Faceted Stacked Logs, Notched Corners, Stepped Roof)
# ==============================================================================
def build_struct_cabin_small():
    scene, mat = setup_scene()
    name = "SM_Struct_Cabin_Small"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l, h_wall = 440.0, 480.0, 260.0
    hw, hl = w * 0.5, l * 0.5
    
    # Internal core structure to block light leaks
    add_box(bm, uv_layer, (-hw + 10, -hl + 10, 0), (hw - 10, hl - 10, h_wall), UV_WOOD_DARK)
    
    # Stacked Faceted Horizontal Logs (6-sided cylinders with visible notches)
    log_r = 16.0
    log_d = 26.0
    n_logs = int(h_wall / log_d)
    ext = 24.0
    
    for i in range(n_logs):
        zc = (i + 0.5) * log_d
        if i % 2 == 0:
            # Front and Back logs along X
            add_cylinder_x(bm, uv_layer, -hw - ext, hw + ext, log_r, 6, UV_WOOD_MID, UV_WOOD_LIGHT, cy=-hl, cz=zc)
            add_cylinder_x(bm, uv_layer, -hw - ext, hw + ext, log_r, 6, UV_WOOD_MID, UV_WOOD_LIGHT, cy=hl, cz=zc)
        else:
            # Left and Right logs along Y
            add_cylinder_y(bm, uv_layer, -hl - ext, hl + ext, log_r, 6, UV_WOOD_WARM, UV_WOOD_LIGHT, cx=-hw, cz=zc)
            add_cylinder_y(bm, uv_layer, -hl - ext, hl + ext, log_r, 6, UV_WOOD_WARM, UV_WOOD_LIGHT, cx=hw, cz=zc)
            
    # Front and Back Gable Walls (Horizontal logs tapering to peak)
    z_peak = h_wall + 155.0
    n_gable_logs = 6
    for i in range(n_gable_logs):
        zc = h_wall + (i + 0.5) * (155.0 / n_gable_logs)
        frac = (i + 0.5) / n_gable_logs
        cur_w = hw * (1.0 - frac)
        if cur_w > 15.0:
            add_cylinder_x(bm, uv_layer, -cur_w, cur_w, log_r * 0.9, 6, UV_WOOD_MID, UV_WOOD_LIGHT, cy=-hl, cz=zc)
            add_cylinder_x(bm, uv_layer, -cur_w, cur_w, log_r * 0.9, 6, UV_WOOD_MID, UV_WOOD_LIGHT, cy=hl, cz=zc)
            
    # Gable wall interior fills to ensure no gap under roof
    g_f0 = bm.verts.new((-hw, -hl, h_wall))
    g_f1 = bm.verts.new((0.0, -hl, z_peak + 10))
    g_f2 = bm.verts.new((hw, -hl, h_wall))
    add_bmesh_face(bm, uv_layer, [g_f0, g_f1, g_f2], UV_WOOD_DARK)
    g_b0 = bm.verts.new((-hw, hl, h_wall))
    g_b1 = bm.verts.new((0.0, hl, z_peak + 10))
    g_b2 = bm.verts.new((hw, hl, h_wall))
    add_bmesh_face(bm, uv_layer, [g_b2, g_b1, g_b0], UV_WOOD_DARK)
    
    # Stepped Overlapping Timber Shingle Roof (6 shingle tiers per slope)
    overhang = 35.0
    n_tiers = 6
    y_f = -hl - overhang
    y_b =  hl + overhang
    
    for t in range(n_tiers):
        t0 = t / float(n_tiers)
        t1 = (t + 1.15) / float(n_tiers)
        # Left slope: from (-hw - overhang) to ridge x=0
        x_start_l = -hw - overhang + t0 * (hw + overhang)
        x_end_l   = -hw - overhang + t1 * (hw + overhang)
        z_start_l = h_wall - 10 + t0 * (z_peak - h_wall + 20)
        z_end_l   = h_wall - 10 + t1 * (z_peak - h_wall + 20)
        
        # Tier plank quad
        p_l0 = bm.verts.new((x_start_l, y_f, z_start_l + 4))
        p_l1 = bm.verts.new((x_end_l,   y_f, z_end_l + 4))
        p_l2 = bm.verts.new((x_end_l,   y_b, z_end_l + 4))
        p_l3 = bm.verts.new((x_start_l, y_b, z_start_l + 4))
        add_bmesh_face(bm, uv_layer, [p_l0, p_l1, p_l2, p_l3], UV_SHINGLE_ROOF if t%2==0 else UV_WOOD_LIGHT)
        
        # Right slope
        x_start_r = hw + overhang - t0 * (hw + overhang)
        x_end_r   = hw + overhang - t1 * (hw + overhang)
        p_r0 = bm.verts.new((x_end_r,   y_f, z_end_l + 4))
        p_r1 = bm.verts.new((x_start_r, y_f, z_start_l + 4))
        p_r2 = bm.verts.new((x_start_r, y_b, z_start_l + 4))
        p_r3 = bm.verts.new((x_end_r,   y_b, z_end_l + 4))
        add_bmesh_face(bm, uv_layer, [p_r0, p_r1, p_r2, p_r3], UV_SHINGLE_ROOF if t%2==0 else UV_WOOD_LIGHT)
        
    # Ridge cap beam
    add_box(bm, uv_layer, (-12.0, y_f, z_peak + 12), (12.0, y_b, z_peak + 24), UV_WOOD_MID)
    
    # Front Wood Door with Frame
    add_box(bm, uv_layer, (-50, -hl - 24, 0), (50, -hl - 12, 195), UV_WOOD_DARK)
    add_box(bm, uv_layer, (-42, -hl - 26, 0), (42, -hl - 18, 186), UV_WOOD_LIGHT)
    
    # Side 4-pane Window with Wood Frame
    add_box(bm, uv_layer, (hw + 8, -40, 90), (hw + 24, 60, 190), UV_WOOD_LIGHT)
    add_box(bm, uv_layer, (hw + 14, -30, 100), (hw + 20, 50, 180), UV_WINDOW_DARK)
    add_box(bm, uv_layer, (hw + 18, 8, 100), (hw + 22, 12, 180), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (hw + 18, -30, 138), (hw + 22, 50, 142), UV_WHITE_TRIM)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=650.0)

# ==============================================================================
# 3. SM_Struct_Cabin_Large (Stacked Logs, Porch, Railings, Stone Chimney)
# ==============================================================================
def build_struct_cabin_large():
    scene, mat = setup_scene()
    name = "SM_Struct_Cabin_Large"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l, h_wall = 620.0, 600.0, 320.0
    hw, hl = w * 0.5, l * 0.5
    
    # Core interior backing
    add_box(bm, uv_layer, (-hw + 10, -hl + 10, 0), (hw - 10, hl - 10, h_wall), UV_WOOD_DARK)
    
    # Stacked Faceted Horizontal Logs
    log_r = 17.0
    log_d = 28.0
    n_logs = int(h_wall / log_d)
    ext = 26.0
    
    for i in range(n_logs):
        zc = (i + 0.5) * log_d
        if i % 2 == 0:
            add_cylinder_x(bm, uv_layer, -hw - ext, hw + ext, log_r, 6, UV_WOOD_MID, UV_WOOD_LIGHT, cy=-hl, cz=zc)
            add_cylinder_x(bm, uv_layer, -hw - ext, hw + ext, log_r, 6, UV_WOOD_MID, UV_WOOD_LIGHT, cy=hl, cz=zc)
        else:
            add_cylinder_y(bm, uv_layer, -hl - ext, hl + ext, log_r, 6, UV_WOOD_WARM, UV_WOOD_LIGHT, cx=-hw, cz=zc)
            add_cylinder_y(bm, uv_layer, -hl - ext, hl + ext, log_r, 6, UV_WOOD_WARM, UV_WOOD_LIGHT, cx=hw, cz=zc)
            
    # Gables
    z_peak = h_wall + 190.0
    g_f0 = bm.verts.new((-hw, -hl, h_wall))
    g_f1 = bm.verts.new((0.0, -hl, z_peak + 15))
    g_f2 = bm.verts.new((hw, -hl, h_wall))
    add_bmesh_face(bm, uv_layer, [g_f0, g_f1, g_f2], UV_WOOD_MID)
    g_b0 = bm.verts.new((-hw, hl, h_wall))
    g_b1 = bm.verts.new((0.0, hl, z_peak + 15))
    g_b2 = bm.verts.new((hw, hl, h_wall))
    add_bmesh_face(bm, uv_layer, [g_b2, g_b1, g_b0], UV_WOOD_MID)
    
    # Stepped Shingle Roof (Main cabin)
    overhang = 40.0
    n_tiers = 7
    y_f = -hl - overhang
    y_b =  hl + overhang
    for t in range(n_tiers):
        t0 = t / float(n_tiers)
        t1 = (t + 1.15) / float(n_tiers)
        x_sl = -hw - overhang + t0 * (hw + overhang)
        x_el = -hw - overhang + t1 * (hw + overhang)
        z_sl = h_wall - 10 + t0 * (z_peak - h_wall + 25)
        z_el = h_wall - 10 + t1 * (z_peak - h_wall + 25)
        
        p_l0 = bm.verts.new((x_sl, y_f, z_sl + 4))
        p_l1 = bm.verts.new((x_el, y_f, z_el + 4))
        p_l2 = bm.verts.new((x_el, y_b, z_el + 4))
        p_l3 = bm.verts.new((x_sl, y_b, z_sl + 4))
        add_bmesh_face(bm, uv_layer, [p_l0, p_l1, p_l2, p_l3], UV_SHINGLE_ROOF if t%2==0 else UV_WOOD_LIGHT)
        
        x_sr = hw + overhang - t0 * (hw + overhang)
        x_er = hw + overhang - t1 * (hw + overhang)
        p_r0 = bm.verts.new((x_er, y_f, z_el + 4))
        p_r1 = bm.verts.new((x_sr, y_f, z_sl + 4))
        p_r2 = bm.verts.new((x_sr, y_b, z_sl + 4))
        p_r3 = bm.verts.new((x_er, y_b, z_el + 4))
        add_bmesh_face(bm, uv_layer, [p_r0, p_r1, p_r2, p_r3], UV_SHINGLE_ROOF if t%2==0 else UV_WOOD_LIGHT)
        
    add_box(bm, uv_layer, (-14.0, y_f, z_peak + 16), (14.0, y_b, z_peak + 28), UV_WOOD_MID)
    
    # Front Porch (Covered Deck, Steps, Columns, Railing)
    porch_depth = 200.0
    porch_y0 = -hl - porch_depth
    porch_z = 24.0
    add_box(bm, uv_layer, (-hw, porch_y0, 0), (hw, -hl, porch_z), UV_WOOD_WARM)
    add_box(bm, uv_layer, (-60, porch_y0 - 50, 0), (60, porch_y0, 12), UV_WOOD_MID)
    add_box(bm, uv_layer, (-50, porch_y0 - 25, 12), (50, porch_y0, 24), UV_WOOD_MID)
    
    col_w = 16.0
    h_col = 200.0
    col_x_positions = [-hw + 10, -80, 80, hw - 10 - col_w]
    for cx in col_x_positions:
        add_box(bm, uv_layer, (cx, porch_y0 + 10, porch_z), (cx + col_w, porch_y0 + 10 + col_w, porch_z + h_col), UV_WOOD_LIGHT)
        
    for r_x0, r_x1 in [(-hw + 10, -80), (80 + col_w, hw - 10)]:
        add_box(bm, uv_layer, (r_x0, porch_y0 + 14, porch_z + 80), (r_x1, porch_y0 + 22, porch_z + 90), UV_WOOD_LIGHT)
        add_box(bm, uv_layer, (r_x0, porch_y0 + 14, porch_z + 10), (r_x1, porch_y0 + 22, porch_z + 20), UV_WOOD_LIGHT)
        n_bal = int((r_x1 - r_x0) / 25.0)
        for b in range(1, n_bal):
            bx = r_x0 + b * 25.0
            add_box(bm, uv_layer, (bx - 3, porch_y0 + 16, porch_z + 20), (bx + 3, porch_y0 + 20, porch_z + 80), UV_WOOD_LIGHT)
            
    # Porch Roof (Meeting flush with cabin front wall)
    p_rf0 = bm.verts.new((-hw - 15, porch_y0 - 15, porch_z + h_col - 5))
    p_rf1 = bm.verts.new((-hw - 15, -hl, porch_z + h_col + 55))
    p_rf2 = bm.verts.new(( hw + 15, -hl, porch_z + h_col + 55))
    p_rf3 = bm.verts.new(( hw + 15, porch_y0 - 15, porch_z + h_col - 5))
    add_bmesh_face(bm, uv_layer, [p_rf0, p_rf3, p_rf2, p_rf1], UV_SHINGLE_ROOF)
    
    # Exterior Stone Chimney (Right gable wall)
    chim_w = 90.0
    chim_l = 80.0
    chim_x = hw - 20.0
    chim_h = z_peak + 80.0
    add_box(bm, uv_layer, (chim_x, -45, 0), (chim_x + chim_w, 45, 140), UV_STONE_GREY)
    add_box(bm, uv_layer, (chim_x + 10, -35, 140), (chim_x + chim_w - 10, 35, 220), UV_STONE_LIGHT)
    add_box(bm, uv_layer, (chim_x + 15, -30, 220), (chim_x + chim_w - 15, 30, chim_h), UV_STONE_GREY)
    add_box(bm, uv_layer, (chim_x + 10, -35, chim_h), (chim_x + chim_w - 10, 35, chim_h + 16), UV_STONE_LIGHT)
    add_box(bm, uv_layer, (chim_x + 24, -20, chim_h + 16), (chim_x + chim_w - 24, 20, chim_h + 20), UV_STEEL_DARK)
    
    # Front Entrance Door
    add_box(bm, uv_layer, (-45, -hl - 12, porch_z), (45, -hl, porch_z + 200), UV_WOOD_DARK)
    add_box(bm, uv_layer, (-36, -hl - 16, porch_z), (36, -hl - 10, porch_z + 190), UV_WOOD_LIGHT)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=950.0)

# ==============================================================================
# 4. SM_Struct_Shed (Rustic Vertical Board & Batten Timber Shed)
# ==============================================================================
def build_struct_shed():
    scene, mat = setup_scene()
    name = "SM_Struct_Shed"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l, h_wall = 320.0, 360.0, 260.0
    hw, hl = w * 0.5, l * 0.5
    
    add_box(bm, uv_layer, (-hw, -hl, 0), (hw, hl, h_wall), UV_WOOD_WARM)
    
    n_battens = 8
    for i in range(1, n_battens):
        x = -hw + i * (w / n_battens)
        add_box(bm, uv_layer, (x - 3, -hl - 4, 0), (x + 3, -hl, h_wall), UV_WOOD_MID)
        add_box(bm, uv_layer, (x - 3,  hl, 0), (x + 3,  hl + 4, h_wall), UV_WOOD_MID)
    for i in range(1, n_battens):
        y = -hl + i * (l / n_battens)
        add_box(bm, uv_layer, (-hw - 4, y - 3, 0), (-hw, y + 3, h_wall), UV_WOOD_MID)
        add_box(bm, uv_layer, ( hw, y - 3, 0), ( hw + 4, y + 3, h_wall), UV_WOOD_MID)
        
    z_peak = h_wall + 95.0
    g_f0 = bm.verts.new((-hw, -hl, h_wall))
    g_f1 = bm.verts.new((0.0, -hl, z_peak + 10))
    g_f2 = bm.verts.new((hw, -hl, h_wall))
    add_bmesh_face(bm, uv_layer, [g_f0, g_f1, g_f2], UV_WOOD_WARM)
    g_b0 = bm.verts.new((-hw, hl, h_wall))
    g_b1 = bm.verts.new((0.0, hl, z_peak + 10))
    g_b2 = bm.verts.new((hw, hl, h_wall))
    add_bmesh_face(bm, uv_layer, [g_b2, g_b1, g_b0], UV_WOOD_WARM)
    
    overhang = 30.0
    r_l0 = bm.verts.new((-hw - overhang, -hl - overhang, h_wall - 5))
    r_l1 = bm.verts.new((8.0, -hl - overhang, z_peak + 10))
    r_l2 = bm.verts.new((8.0,  hl + overhang, z_peak + 10))
    r_l3 = bm.verts.new((-hw - overhang,  hl + overhang, h_wall - 5))
    add_bmesh_face(bm, uv_layer, [r_l0, r_l1, r_l2, r_l3], UV_WOOD_LIGHT)
    
    r_r0 = bm.verts.new((-8.0, -hl - overhang, z_peak + 10))
    r_r1 = bm.verts.new((hw + overhang, -hl - overhang, h_wall - 5))
    r_r2 = bm.verts.new((hw + overhang,  hl + overhang, h_wall - 5))
    r_r3 = bm.verts.new((-8.0,  hl + overhang, z_peak + 10))
    add_bmesh_face(bm, uv_layer, [r_r0, r_r1, r_r2, r_r3], UV_WOOD_MID)
    
    dw, dh = 110.0, 200.0
    hdw = dw * 0.5
    add_box(bm, uv_layer, (-hdw - 8, -hl - 10, 0), (hdw + 8, -hl, dh + 8), UV_WOOD_LIGHT)
    add_box(bm, uv_layer, (-hdw, -hl - 14, 0), (hdw, -hl - 8, dh), UV_WOOD_MID)
    add_box(bm, uv_layer, (hdw - 24, -hl - 18, 95), (hdw - 16, -hl - 14, 115), UV_STEEL_DARK)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=500.0)

# ==============================================================================
# 5. SM_Struct_House_Starter (Starter House with White Trim, Entry Stoop & Awning)
# ==============================================================================
def build_struct_house_starter():
    scene, mat = setup_scene()
    name = "SM_Struct_House_Starter"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l, h_wall = 500.0, 560.0, 280.0
    hw, hl = w * 0.5, l * 0.5
    
    add_box(bm, uv_layer, (-hw, -hl, 0), (hw, hl, h_wall), UV_CREAM_WALL)
    add_box(bm, uv_layer, (-hw - 4, -hl - 4, 0), (hw + 4, hl + 4, 20), UV_STONE_GREY)
    
    # White corner trim posts
    trim = 12.0
    for cx in [-hw, hw - trim]:
        for cy in [-hl, hl - trim]:
            add_box(bm, uv_layer, (cx, cy, 20), (cx + trim, cy + trim, h_wall), UV_WHITE_TRIM)
            
    # Gable ends flush to roof
    z_peak = h_wall + 165.0
    g_f0 = bm.verts.new((-hw, -hl, h_wall))
    g_f1 = bm.verts.new((0.0, -hl, z_peak + 15))
    g_f2 = bm.verts.new((hw, -hl, h_wall))
    add_bmesh_face(bm, uv_layer, [g_f0, g_f1, g_f2], UV_CREAM_WALL)
    g_b0 = bm.verts.new((-hw, hl, h_wall))
    g_b1 = bm.verts.new((0.0, hl, z_peak + 15))
    g_b2 = bm.verts.new((hw, hl, h_wall))
    add_bmesh_face(bm, uv_layer, [g_b2, g_b1, g_b0], UV_CREAM_WALL)
    
    overhang = 35.0
    r_l0 = bm.verts.new((-hw - overhang, -hl - overhang, h_wall - 10))
    r_l1 = bm.verts.new((10.0, -hl - overhang, z_peak + 15))
    r_l2 = bm.verts.new((10.0,  hl + overhang, z_peak + 15))
    r_l3 = bm.verts.new((-hw - overhang,  hl + overhang, h_wall - 10))
    add_bmesh_face(bm, uv_layer, [r_l0, r_l1, r_l2, r_l3], UV_SHINGLE_ROOF)
    
    r_r0 = bm.verts.new((-10.0, -hl - overhang, z_peak + 15))
    r_r1 = bm.verts.new((hw + overhang, -hl - overhang, h_wall - 10))
    r_r2 = bm.verts.new((hw + overhang,  hl + overhang, h_wall - 10))
    r_r3 = bm.verts.new((-10.0,  hl + overhang, z_peak + 15))
    add_bmesh_face(bm, uv_layer, [r_r0, r_r1, r_r2, r_r3], UV_SHINGLE_ROOF)
    
    # White fascia edge trims
    add_bmesh_face(bm, uv_layer, [r_l0, r_l1, g_f1, g_f0], UV_WHITE_TRIM)
    add_bmesh_face(bm, uv_layer, [r_r1, r_r0, g_f1, g_f2], UV_WHITE_TRIM)
    
    # Front Porch Stoop with Covered Awning
    pw, pl, pz = 140.0, 100.0, 20.0
    hpw = pw * 0.5
    py = -hl - pl
    add_box(bm, uv_layer, (-hpw, py, 0), (hpw, -hl, pz), UV_WOOD_WARM)
    add_box(bm, uv_layer, (-hpw + 20, py - 35, 0), (hpw - 20, py, 10), UV_WOOD_MID)
    add_box(bm, uv_layer, (-hpw + 6, py + 6, pz), (-hpw + 18, py + 18, pz + 180), UV_WHITE_TRIM)
    add_box(bm, uv_layer, ( hpw - 18, py + 6, pz), ( hpw - 6, py + 18, pz + 180), UV_WHITE_TRIM)
    
    a_f0 = bm.verts.new((-hpw - 10, py - 10, pz + 175))
    a_f1 = bm.verts.new((0.0, py - 10, pz + 215))
    a_f2 = bm.verts.new(( hpw + 10, py - 10, pz + 175))
    a_b0 = bm.verts.new((-hpw - 10, -hl, pz + 195))
    a_b1 = bm.verts.new((0.0, -hl, pz + 235))
    a_b2 = bm.verts.new(( hpw + 10, -hl, pz + 195))
    add_bmesh_face(bm, uv_layer, [a_f0, a_f1, a_b1, a_b0], UV_SHINGLE_ROOF)
    add_bmesh_face(bm, uv_layer, [a_f1, a_f2, a_b2, a_b1], UV_SHINGLE_ROOF)
    
    # Front door
    add_box(bm, uv_layer, (-40, -hl - 8, pz), (40, -hl, pz + 190), UV_WOOD_DARK)
    
    # Framed Windows
    add_box(bm, uv_layer, (-hw + 60, -hl - 6, 90), (-hw + 140, -hl, 190), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-hw + 70, -hl - 10, 100), (-hw + 130, -hl - 4, 180), UV_WINDOW_DARK)
    add_box(bm, uv_layer, (hw, -40, 90), (hw + 6, 40, 190), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (hw + 4, -30, 100), (hw + 10, 30, 180), UV_WINDOW_DARK)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=750.0)

# ==============================================================================
# 6. SM_Struct_House_Farmhouse (Two-Story, Front Gable, Dormer Window, Wraparound Porch)
# ==============================================================================
def build_struct_house_farmhouse():
    scene, mat = setup_scene()
    name = "SM_Struct_House_Farmhouse"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l = 680.0, 720.0
    hw, hl = w * 0.5, l * 0.5
    h_f1 = 260.0
    h_f2 = 460.0
    
    # Ground floor body
    add_box(bm, uv_layer, (-hw, -hl, 0), (hw, hl, h_f1), UV_CREAM_WALL)
    # Second floor body
    add_box(bm, uv_layer, (-hw + 25, -hl + 25, h_f1), (hw - 25, hl - 25, h_f2), UV_CREAM_WALL)
    
    # Second floor front and back gables (Ridge runs along Y)
    z_peak = h_f2 + 185.0
    g_f0 = bm.verts.new((-hw + 25, -hl + 25, h_f2))
    g_f1 = bm.verts.new((0.0, -hl + 25, z_peak + 15))
    g_f2 = bm.verts.new((hw - 25, -hl + 25, h_f2))
    add_bmesh_face(bm, uv_layer, [g_f0, g_f1, g_f2], UV_CREAM_WALL)
    g_b0 = bm.verts.new((-hw + 25, hl - 25, h_f2))
    g_b1 = bm.verts.new((0.0, hl - 25, z_peak + 15))
    g_b2 = bm.verts.new((hw - 25, hl - 25, h_f2))
    add_bmesh_face(bm, uv_layer, [g_b2, g_b1, g_b0], UV_CREAM_WALL)
    
    # Main Roof
    overhang = 45.0
    y_f = -hl - overhang + 25
    y_b =  hl + overhang - 25
    
    r_l0 = bm.verts.new((-hw - overhang + 25, y_f, h_f2 - 10))
    r_l1 = bm.verts.new((10.0, y_f, z_peak + 15))
    r_l2 = bm.verts.new((10.0, y_b, z_peak + 15))
    r_l3 = bm.verts.new((-hw - overhang + 25, y_b, h_f2 - 10))
    add_bmesh_face(bm, uv_layer, [r_l0, r_l1, r_l2, r_l3], UV_SHINGLE_ROOF)
    
    r_r0 = bm.verts.new((-10.0, y_f, z_peak + 15))
    r_r1 = bm.verts.new((hw + overhang - 25, y_f, h_f2 - 10))
    r_r2 = bm.verts.new((hw + overhang - 25, y_b, h_f2 - 10))
    r_r3 = bm.verts.new((-10.0, y_b, z_peak + 15))
    add_bmesh_face(bm, uv_layer, [r_r0, r_r1, r_r2, r_r3], UV_SHINGLE_ROOF)
    
    # Front-facing Dormer Window on Right Roof Slope
    # Dormer sits on right slope (x > 0) with front face perpendicular to Y (facing -Y)
    dx_cen = hw * 0.45
    dw, dl, dh = 90.0, 110.0, 85.0
    hdw = dw * 0.5
    dy_f = -hl * 0.35
    dy_b = dy_f + dl
    dz_bot = h_f2 + 35.0
    dz_top = dz_bot + dh
    
    # Dormer side walls & front wall
    add_box(bm, uv_layer, (dx_cen - hdw, dy_f, dz_bot), (dx_cen + hdw, dy_b, dz_top), UV_CREAM_WALL)
    # Dormer front gable
    dg_f0 = bm.verts.new((dx_cen - hdw - 4, dy_f - 2, dz_top))
    dg_f1 = bm.verts.new((dx_cen, dy_f - 2, dz_top + 45))
    dg_f2 = bm.verts.new((dx_cen + hdw + 4, dy_f - 2, dz_top))
    add_bmesh_face(bm, uv_layer, [dg_f0, dg_f1, dg_f2], UV_CREAM_WALL)
    # Dormer pitched roof
    dr_l0 = bm.verts.new((dx_cen - hdw - 12, dy_f - 8, dz_top - 5))
    dr_l1 = bm.verts.new((dx_cen, dy_f - 8, dz_top + 48))
    dr_l2 = bm.verts.new((dx_cen, dy_b + 10, dz_top + 48))
    dr_l3 = bm.verts.new((dx_cen - hdw - 12, dy_b + 10, dz_top - 5))
    add_bmesh_face(bm, uv_layer, [dr_l0, dr_l1, dr_l2, dr_l3], UV_SHINGLE_ROOF)
    dr_r0 = bm.verts.new((dx_cen, dy_f - 8, dz_top + 48))
    dr_r1 = bm.verts.new((dx_cen + hdw + 12, dy_f - 8, dz_top - 5))
    dr_r2 = bm.verts.new((dx_cen + hdw + 12, dy_b + 10, dz_top - 5))
    dr_r3 = bm.verts.new((dx_cen, dy_b + 10, dz_top + 48))
    add_bmesh_face(bm, uv_layer, [dr_r0, dr_r1, dr_r2, dr_r3], UV_SHINGLE_ROOF)
    # Dormer front framed window
    add_box(bm, uv_layer, (dx_cen - 24, dy_f - 6, dz_bot + 18), (dx_cen + 24, dy_f, dz_top - 10), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (dx_cen - 18, dy_f - 8, dz_bot + 24), (dx_cen + 18, dy_f - 4, dz_top - 16), UV_WINDOW_DARK)
    
    # Wraparound Porch (L-shaped: Front and Right Side)
    p_depth = 130.0
    p_z = 24.0
    # Front porch deck
    add_box(bm, uv_layer, (-hw, -hl - p_depth, 0), (hw + p_depth, -hl, p_z), UV_WOOD_WARM)
    # Right side porch deck
    add_box(bm, uv_layer, (hw, -hl, 0), (hw + p_depth, hl, p_z), UV_WOOD_WARM)
    
    # Porch stairs (front and right side)
    add_box(bm, uv_layer, (-80, -hl - p_depth - 35, 0), (80, -hl - p_depth, 12), UV_WOOD_MID)
    add_box(bm, uv_layer, (-70, -hl - p_depth - 18, 12), (70, -hl - p_depth, 24), UV_WOOD_MID)
    add_box(bm, uv_layer, (hw + p_depth, -30, 0), (hw + p_depth + 35, 90, 12), UV_WOOD_MID)
    add_box(bm, uv_layer, (hw + p_depth, -20, 12), (hw + p_depth + 18, 80, 24), UV_WOOD_MID)
    
    # Porch Support Columns (White posts)
    col_w = 12.0
    col_h = 195.0
    # Front posts
    for px in [-hw + 10, -120, 0, 120, hw - 10, hw + p_depth - 12]:
        add_box(bm, uv_layer, (px, -hl - p_depth + 10, p_z), (px + col_w, -hl - p_depth + 10 + col_w, p_z + col_h), UV_WHITE_TRIM)
    # Side posts
    for py in [-hl + 100, 0, hl - 20]:
        add_box(bm, uv_layer, (hw + p_depth - 12 - col_w, py, p_z), (hw + p_depth - 12, py + col_w, p_z + col_h), UV_WHITE_TRIM)
        
    # Wraparound Porch Roof (Slanted hip/shed canopy)
    # Front section
    pr_f0 = bm.verts.new((-hw - 10, -hl - p_depth - 15, p_z + col_h - 5))
    pr_f1 = bm.verts.new(( hw + p_depth + 15, -hl - p_depth - 15, p_z + col_h - 5))
    pr_f2 = bm.verts.new(( hw, -hl, h_f1 + 8))
    pr_f3 = bm.verts.new((-hw - 10, -hl, h_f1 + 8))
    add_bmesh_face(bm, uv_layer, [pr_f0, pr_f1, pr_f2, pr_f3], UV_SHINGLE_ROOF)
    # Side section
    pr_s0 = bm.verts.new((hw + p_depth + 15, -hl - p_depth - 15, p_z + col_h - 5))
    pr_s1 = bm.verts.new((hw + p_depth + 15,  hl + 15, p_z + col_h - 5))
    pr_s2 = bm.verts.new((hw,  hl + 15, h_f1 + 8))
    pr_s3 = bm.verts.new((hw, -hl, h_f1 + 8))
    add_bmesh_face(bm, uv_layer, [pr_s0, pr_s1, pr_s2, pr_s3], UV_SHINGLE_ROOF)
    
    # White Porch Railing with Balusters
    # Front rail
    add_box(bm, uv_layer, (-hw + 10, -hl - p_depth + 14, p_z + 75), (hw + p_depth - 10, -hl - p_depth + 18, p_z + 85), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-hw + 10, -hl - p_depth + 14, p_z + 10), (hw + p_depth - 10, -hl - p_depth + 18, p_z + 18), UV_WHITE_TRIM)
    # Side rail
    add_box(bm, uv_layer, (hw + p_depth - 18, -hl + 10, p_z + 75), (hw + p_depth - 14, hl - 10, p_z + 85), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (hw + p_depth - 18, -hl + 10, p_z + 10), (hw + p_depth - 14, hl - 10, p_z + 18), UV_WHITE_TRIM)
    
    # Doors & Windows
    add_box(bm, uv_layer, (-45, -hl - 6, p_z), (45, -hl, p_z + 200), UV_WOOD_DARK)
    # Second floor upper window
    add_box(bm, uv_layer, (-35, -hl + 22, h_f2 - 110), (35, -hl + 28, h_f2 - 15), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-25, -hl + 20, h_f2 - 100), (25, -hl + 26, h_f2 - 25), UV_WINDOW_DARK)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=1150.0)

# ==============================================================================
# 7. SM_Struct_Coop_Chicken (Elevated Coop, Nesting Box, Ramp, Fenced Run)
# ==============================================================================
def build_struct_coop_chicken():
    scene, mat = setup_scene()
    name = "SM_Struct_Coop_Chicken"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    cw, cl = 180.0, 180.0
    hcw, hcl = cw * 0.5, cl * 0.5
    stilt_h = 90.0
    coop_h = 160.0
    cx_mid, cy_mid = -60.0, 60.0
    
    for sx in [cx_mid - hcw + 6, cx_mid + hcw - 18]:
        for sy in [cy_mid - hcl + 6, cy_mid + hcl - 18]:
            add_box(bm, uv_layer, (sx, sy, 0), (sx + 12, sy + 12, stilt_h), UV_WOOD_DARK)
            
    # Hen house box with horizontal siding plank battens
    add_box(bm, uv_layer, (cx_mid - hcw, cy_mid - hcl, stilt_h), (cx_mid + hcw, cy_mid + hcl, stilt_h + coop_h), UV_WOOD_WARM)
    for c_i in range(1, 6):
        c_z = stilt_h + c_i * (coop_h / 6.0)
        add_box(bm, uv_layer, (cx_mid - hcw - 2, cy_mid - hcl - 2, c_z - 2), (cx_mid + hcw + 2, cy_mid - hcl, c_z + 2), UV_WOOD_LIGHT)
        
    # Flush Gable Ends (Ridge along Y)
    rf_z_b = stilt_h + coop_h
    rf_z_p = rf_z_b + 65.0
    g_cf0 = bm.verts.new((cx_mid - hcw, cy_mid - hcl, rf_z_b))
    g_cf1 = bm.verts.new((cx_mid, cy_mid - hcl, rf_z_p + 10))
    g_cf2 = bm.verts.new((cx_mid + hcw, cy_mid - hcl, rf_z_b))
    add_bmesh_face(bm, uv_layer, [g_cf0, g_cf1, g_cf2], UV_WOOD_WARM)
    g_cb0 = bm.verts.new((cx_mid - hcw, cy_mid + hcl, rf_z_b))
    g_cb1 = bm.verts.new((cx_mid, cy_mid + hcl, rf_z_p + 10))
    g_cb2 = bm.verts.new((cx_mid + hcw, cy_mid + hcl, rf_z_b))
    add_bmesh_face(bm, uv_layer, [g_cb2, g_cb1, g_cb0], UV_WOOD_WARM)
    
    # Roof panels
    hr0 = bm.verts.new((cx_mid - hcw - 20, cy_mid - hcl - 15, rf_z_b - 5))
    hr1 = bm.verts.new((cx_mid, cy_mid - hcl - 15, rf_z_p + 10))
    hr2 = bm.verts.new((cx_mid, cy_mid + hcl + 15, rf_z_p + 10))
    hr3 = bm.verts.new((cx_mid - hcw - 20, cy_mid + hcl + 15, rf_z_b - 5))
    add_bmesh_face(bm, uv_layer, [hr0, hr1, hr2, hr3], UV_SHINGLE_ROOF)
    
    hr4 = bm.verts.new((cx_mid + hcw + 20, cy_mid - hcl - 15, rf_z_b - 5))
    hr5 = bm.verts.new((cx_mid + hcw + 20, cy_mid + hcl + 15, rf_z_b - 5))
    add_bmesh_face(bm, uv_layer, [hr1, hr4, hr5, hr2], UV_SHINGLE_ROOF)
    
    # Nesting Box
    nb_w, nb_l, nb_h = 70.0, 130.0, 75.0
    nb_x0 = cx_mid - hcw - nb_w
    nb_y0 = cy_mid - nb_l * 0.5
    add_box(bm, uv_layer, (nb_x0, nb_y0, stilt_h + 20), (cx_mid - hcw, nb_y0 + nb_l, stilt_h + 20 + nb_h), UV_WOOD_LIGHT)
    nl0 = bm.verts.new((nb_x0 - 8, nb_y0 - 6, stilt_h + 20 + nb_h - 15))
    nl1 = bm.verts.new((cx_mid - hcw + 4, nb_y0 - 6, stilt_h + 20 + nb_h + 10))
    nl2 = bm.verts.new((cx_mid - hcw + 4, nb_y0 + nb_l + 6, stilt_h + 20 + nb_h + 10))
    nl3 = bm.verts.new((nb_x0 - 8, nb_y0 + nb_l + 6, stilt_h + 20 + nb_h - 15))
    add_bmesh_face(bm, uv_layer, [nl0, nl1, nl2, nl3], UV_SHINGLE_ROOF)
    
    # Chicken Door & Cleated Ramp
    add_box(bm, uv_layer, (cx_mid - 25, cy_mid - hcl - 4, stilt_h), (cx_mid + 25, cy_mid - hcl, stilt_h + 65), UV_WOOD_DEEP)
    r_len = 160.0
    rm0 = bm.verts.new((cx_mid - 20, cy_mid - hcl, stilt_h + 5))
    rm1 = bm.verts.new((cx_mid + 20, cy_mid - hcl, stilt_h + 5))
    rm2 = bm.verts.new((cx_mid + 20, cy_mid - hcl - r_len, 2.0))
    rm3 = bm.verts.new((cx_mid - 20, cy_mid - hcl - r_len, 2.0))
    add_bmesh_face(bm, uv_layer, [rm0, rm1, rm2, rm3], UV_WOOD_MID)
    for c in range(1, 6):
        cz = stilt_h * (1.0 - c / 6.0)
        cy = cy_mid - hcl - c * (r_len / 6.0)
        add_box(bm, uv_layer, (cx_mid - 18, cy - 3, cz), (cx_mid + 18, cy + 3, cz + 4), UV_WOOD_LIGHT)
        
    # Fenced Enclosure Run with Timber Posts & Diagonal Wire Mesh Struts
    run_x0, run_x1 = -180.0, 180.0
    run_y0, run_y1 = -180.0, 180.0
    fence_h = 100.0
    posts_pos = [
        (run_x0, run_y0), (run_x1, run_y0), (run_x1, run_y1), (run_x0, run_y1),
        (0.0, run_y0), (run_x1, 0.0), (0.0, run_y1), (run_x0, 0.0)
    ]
    for px, py in posts_pos:
        add_box(bm, uv_layer, (px - 6, py - 6, 0), (px + 6, py + 6, fence_h), UV_WOOD_MID)
        
    for (px0, py0), (px1, py1) in [
        ((run_x0, run_y0), (run_x1, run_y0)),
        ((run_x1, run_y0), (run_x1, run_y1)),
        ((run_x1, run_y1), (run_x0, run_y1)),
        ((run_x0, run_y1), (run_x0, run_y0))
    ]:
        add_box(bm, uv_layer, (min(px0, px1), min(py0, py1), fence_h - 8), (max(px0, px1) + 4, max(py0, py1) + 4, fence_h), UV_WOOD_MID)
        add_box(bm, uv_layer, (min(px0, px1), min(py0, py1), 8), (max(px0, px1) + 4, max(py0, py1) + 4, 16), UV_WOOD_MID)
        # Diagonal wire lattice stays
        dw0 = bm.verts.new((px0, py0, 14))
        dw1 = bm.verts.new((px1, py1, fence_h - 12))
        dw2 = bm.verts.new((px1, py1, fence_h - 8))
        dw3 = bm.verts.new((px0, py0, 18))
        add_bmesh_face(bm, uv_layer, [dw0, dw1, dw2, dw3], UV_WHITE_TRIM)
        
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=600.0)

# ==============================================================================
# 8. SM_Struct_Silo (Galvanized Steel Grain Silo on Concrete Pad with Leg Stilts)
# ==============================================================================
def build_struct_silo():
    scene, mat = setup_scene()
    name = "SM_Struct_Silo"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    r_silo = 160.0
    h_pad = 20.0
    h_legs = 160.0
    h_cyl = 360.0
    h_cone = 150.0
    sides = 12
    
    add_cylinder_z(bm, uv_layer, 0.0, h_pad, r_silo * 1.25, sides, UV_STONE_LIGHT, UV_STONE_GREY)
    
    n_legs = 6
    for i in range(n_legs):
        a = i * 2.0 * math.pi / n_legs
        lx = (r_silo - 5.0) * math.cos(a)
        ly = (r_silo - 5.0) * math.sin(a)
        add_box(bm, uv_layer, (lx - 8, ly - 8, h_pad), (lx + 8, ly + 8, h_legs + 80), UV_STEEL_DARK)
        
    v_cone_apex = bm.verts.new((0.0, 0.0, h_legs - 50.0))
    v_cone_rim = []
    for i in range(sides):
        a = i * 2.0 * math.pi / sides
        v_cone_rim.append(bm.verts.new((r_silo * math.cos(a), r_silo * math.sin(a), h_legs)))
    for i in range(sides):
        nxt = (i + 1) % sides
        add_bmesh_face(bm, uv_layer, [v_cone_rim[i], v_cone_apex, v_cone_rim[nxt]], UV_STEEL_MID)
        
    n_rings = 4
    ring_h = h_cyl / n_rings
    for r in range(n_rings):
        z0 = h_legs + r * ring_h
        z1 = z0 + ring_h
        uv = UV_TIN_ROOF if (r % 2 == 0) else UV_STEEL_MID
        add_cylinder_z(bm, uv_layer, z0, z1, r_silo, sides, uv)
        add_cylinder_z(bm, uv_layer, z1 - 4, z1 + 4, r_silo + 4, sides, UV_WHITE_TRIM)
        
    z_roof_bot = h_legs + h_cyl
    z_roof_top = z_roof_bot + h_cone
    v_roof_apex = bm.verts.new((0.0, 0.0, z_roof_top))
    v_roof_rim = []
    for i in range(sides):
        a = i * 2.0 * math.pi / sides
        v_roof_rim.append(bm.verts.new(((r_silo + 10.0) * math.cos(a), (r_silo + 10.0) * math.sin(a), z_roof_bot)))
    for i in range(sides):
        nxt = (i + 1) % sides
        add_bmesh_face(bm, uv_layer, [v_roof_rim[i], v_roof_rim[nxt], v_roof_apex], UV_TIN_ROOF)
        
    add_cylinder_z(bm, uv_layer, z_roof_top, z_roof_top + 25.0, 35.0, 8, UV_STEEL_DARK, UV_STEEL_MID)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=950.0)

# ==============================================================================
# 9. SM_Struct_Greenhouse (Translucent Glass Panes, White Framework)
# ==============================================================================
def build_struct_greenhouse():
    scene, mat = setup_scene()
    name = "SM_Struct_Greenhouse"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l, h_wall = 360.0, 520.0, 200.0
    hw, hl = w * 0.5, l * 0.5
    
    # Concrete foundation curb
    add_box(bm, uv_layer, (-hw - 4, -hl - 4, 0), (hw + 4, hl + 4, 18), UV_STONE_LIGHT)
    # Foundation slab interior floor
    add_box(bm, uv_layer, (-hw, -hl, 10), (hw, hl, 18), UV_STONE_GREY)
    
    frame_w = 8.0
    for cx in [-hw, hw - frame_w]:
        for cy in [-hl, hl - frame_w]:
            add_box(bm, uv_layer, (cx, cy, 18), (cx + frame_w, cy + frame_w, h_wall), UV_WHITE_TRIM)
            
    n_bays = 4
    for b in range(1, n_bays):
        y = -hl + b * (l / n_bays)
        add_box(bm, uv_layer, (-hw, y - 4, 18), (-hw + frame_w, y + 4, h_wall), UV_WHITE_TRIM)
        add_box(bm, uv_layer, (hw - frame_w, y - 4, 18), (hw, y + 4, h_wall), UV_WHITE_TRIM)
        
    add_box(bm, uv_layer, (-hw, -hl, h_wall - frame_w), (hw, -hl + frame_w, h_wall), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-hw,  hl - frame_w, h_wall), (hw,  hl, h_wall), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-hw, -hl, h_wall - frame_w), (-hw + frame_w, hl, h_wall), UV_WHITE_TRIM)
    add_box(bm, uv_layer, ( hw - frame_w, -hl, h_wall - frame_w), ( hw, hl, h_wall), UV_WHITE_TRIM)
    
    z_peak = h_wall + 120.0
    # Front gable frame & glass
    gf0 = bm.verts.new((-hw, -hl, h_wall))
    gf1 = bm.verts.new((0.0, -hl, z_peak))
    gf2 = bm.verts.new((hw, -hl, h_wall))
    add_bmesh_face(bm, uv_layer, [gf0, gf1, gf2], UV_GLASS_CYAN)
    gb0 = bm.verts.new((-hw, hl, h_wall))
    gb1 = bm.verts.new((0.0, hl, z_peak))
    gb2 = bm.verts.new((hw, hl, h_wall))
    add_bmesh_face(bm, uv_layer, [gb2, gb1, gb0], UV_GLASS_CYAN)
    add_box(bm, uv_layer, (-frame_w*0.5, -hl, z_peak - frame_w), (frame_w*0.5, hl, z_peak + frame_w*0.5), UV_WHITE_TRIM)
    
    # Roof Rafter Bars
    for b in range(n_bays + 1):
        y = -hl + b * (l / n_bays)
        rf_l0 = bm.verts.new((-hw, y - 3, h_wall))
        rf_l1 = bm.verts.new((0.0, y - 3, z_peak))
        rf_l2 = bm.verts.new((0.0, y + 3, z_peak))
        rf_l3 = bm.verts.new((-hw, y + 3, h_wall))
        add_bmesh_face(bm, uv_layer, [rf_l0, rf_l1, rf_l2, rf_l3], UV_WHITE_TRIM)
        rf_r0 = bm.verts.new((0.0, y - 3, z_peak))
        rf_r1 = bm.verts.new((hw, y - 3, h_wall))
        rf_r2 = bm.verts.new((hw, y + 3, h_wall))
        rf_r3 = bm.verts.new((0.0, y + 3, z_peak))
        add_bmesh_face(bm, uv_layer, [rf_r0, rf_r1, rf_r2, rf_r3], UV_WHITE_TRIM)
        
    # Glass Panes: Wall sides, Roof, and Front Panes
    add_box(bm, uv_layer, (-hw + 2, -hl + 2, 20), (-hw + 4, hl - 2, h_wall - 4), UV_GLASS_CYAN)
    add_box(bm, uv_layer, ( hw - 4, -hl + 2, 20), ( hw - 2, hl - 2, h_wall - 4), UV_GLASS_CYAN)
    # Front wall flanking glass panes (left & right of door)
    add_box(bm, uv_layer, (-hw + 6, -hl - 1, 20), (-50, -hl + 3, h_wall - 6), UV_GLASS_CYAN)
    add_box(bm, uv_layer, ( 50, -hl - 1, 20), ( hw - 6, -hl + 3, h_wall - 6), UV_GLASS_CYAN)
    # Back wall glass
    add_box(bm, uv_layer, (-hw + 6, hl - 3, 20), (hw - 6, hl + 1, h_wall - 6), UV_GLASS_CYAN)
    
    # Roof glass
    gl_l0 = bm.verts.new((-hw + 2, -hl + 2, h_wall + 2))
    gl_l1 = bm.verts.new((-2.0, -hl + 2, z_peak - 2))
    gl_l2 = bm.verts.new((-2.0,  hl - 2, z_peak - 2))
    gl_l3 = bm.verts.new((-hw + 2,  hl - 2, h_wall + 2))
    add_bmesh_face(bm, uv_layer, [gl_l0, gl_l1, gl_l2, gl_l3], UV_GLASS_CYAN)
    
    gl_r0 = bm.verts.new((2.0, -hl + 2, z_peak - 2))
    gl_r1 = bm.verts.new((hw - 2, -hl + 2, h_wall + 2))
    gl_r2 = bm.verts.new((hw - 2,  hl - 2, h_wall + 2))
    gl_r3 = bm.verts.new((2.0,  hl - 2, z_peak - 2))
    add_bmesh_face(bm, uv_layer, [gl_r0, gl_r1, gl_r2, gl_r3], UV_GLASS_CYAN)
    
    # Front Entrance Door
    add_box(bm, uv_layer, (-45, -hl - 3, 18), (45, -hl + 5, 180), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (-38, -hl - 2, 24), (38, -hl + 4, 174), UV_GLASS_CYAN)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=700.0)

# ==============================================================================
# 10. SM_Struct_Stable (Open Aisle Breezeway Stable with Dutch Doors & Iron Bars)
# ==============================================================================
def build_struct_stable():
    scene, mat = setup_scene()
    name = "SM_Struct_Stable"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l, h_wall = 480.0, 840.0, 260.0
    hw, hl = w * 0.5, l * 0.5
    aisle_w = 180.0
    ha = aisle_w * 0.5
    
    z_peak = h_wall + 125.0
    # Front left & right stall front walls
    add_box(bm, uv_layer, (-hw, -hl, 0), (-ha, -hl + 15, h_wall), UV_WOOD_WARM)
    add_box(bm, uv_layer, (ha, -hl, 0), (hw, -hl + 15, h_wall), UV_WOOD_WARM)
    # Lintel beam over entrance
    add_box(bm, uv_layer, (-ha - 10, -hl, h_wall - 30), (ha + 10, -hl + 18, h_wall), UV_WOOD_MID)
    
    # Front gable triangle
    gf0 = bm.verts.new((-hw, -hl, h_wall))
    gf1 = bm.verts.new((0.0, -hl, z_peak + 15))
    gf2 = bm.verts.new((hw, -hl, h_wall))
    add_bmesh_face(bm, uv_layer, [gf0, gf1, gf2], UV_WOOD_WARM)
    
    # Back wall & gable
    add_box(bm, uv_layer, (-hw, hl - 15, 0), (hw, hl, h_wall), UV_WOOD_WARM)
    gb0 = bm.verts.new((-hw, hl, h_wall))
    gb1 = bm.verts.new((0.0, hl, z_peak + 15))
    gb2 = bm.verts.new((hw, hl, h_wall))
    add_bmesh_face(bm, uv_layer, [gb2, gb1, gb0], UV_WOOD_WARM)
    
    # Side stalls (3 horse stalls per side with Dutch doors & vertical silver bars)
    n_stalls = 3
    stall_l = l / n_stalls
    for s in range(n_stalls):
        y0 = -hl + s * stall_l
        y1 = y0 + stall_l
        
        # Right stalls (facing camera)
        add_box(bm, uv_layer, (hw - 4, y0 + 10, 0), (hw + 6, y1 - 10, 130), UV_WOOD_DARK)
        # Frame and X brace on lower Dutch door
        add_box(bm, uv_layer, (hw + 5, y0 + 10, 0), (hw + 7, y0 + 18, 130), UV_WOOD_LIGHT)
        add_box(bm, uv_layer, (hw + 5, y1 - 18, 0), (hw + 7, y1 - 10, 130), UV_WOOD_LIGHT)
        add_box(bm, uv_layer, (hw + 5, y0 + 10, 122), (hw + 7, y1 - 10, 130), UV_WOOD_LIGHT)
        add_box(bm, uv_layer, (hw + 5, y0 + 10, 0), (hw + 7, y1 - 10, 8), UV_WOOD_LIGHT)
        add_diagonal_strip_yz(bm, uv_layer, y0 + 18, 8, y1 - 18, 122, hw + 7.5, 7.0, UV_WOOD_LIGHT)
        add_diagonal_strip_yz(bm, uv_layer, y0 + 18, 122, y1 - 18, 8, hw + 7.5, 7.0, UV_WOOD_LIGHT)
        # Upper opening with vertical iron bars
        for b in range(1, 6):
            by = y0 + 10 + b * ((stall_l - 20) / 6.0)
            add_cylinder_z(bm, uv_layer, 130, h_wall, 3.2, 6, UV_TIN_ROOF, cx=hw - 2, cy=by)
            
        # Left stalls
        add_box(bm, uv_layer, (-hw - 6, y0 + 10, 0), (-hw + 4, y1 - 10, 130), UV_WOOD_DARK)
        add_diagonal_strip_yz(bm, uv_layer, y0 + 18, 8, y1 - 18, 122, -hw - 6.5, 7.0, UV_WOOD_LIGHT)
        add_diagonal_strip_yz(bm, uv_layer, y0 + 18, 122, y1 - 18, 8, -hw - 6.5, 7.0, UV_WOOD_LIGHT)
        for b in range(1, 6):
            by = y0 + 10 + b * ((stall_l - 20) / 6.0)
            add_cylinder_z(bm, uv_layer, 130, h_wall, 3.2, 6, UV_TIN_ROOF, cx=-hw + 2, cy=by)
            
    # Gabled Roof
    overhang = 35.0
    r_l0 = bm.verts.new((-hw - overhang, -hl - overhang, h_wall - 10))
    r_l1 = bm.verts.new((10.0, -hl - overhang, z_peak + 15))
    r_l2 = bm.verts.new((10.0,  hl + overhang, z_peak + 15))
    r_l3 = bm.verts.new((-hw - overhang,  hl + overhang, h_wall - 10))
    add_bmesh_face(bm, uv_layer, [r_l0, r_l1, r_l2, r_l3], UV_WOOD_LIGHT)
    
    r_r0 = bm.verts.new((-10.0, -hl - overhang, z_peak + 15))
    r_r1 = bm.verts.new((hw + overhang, -hl - overhang, h_wall - 10))
    r_r2 = bm.verts.new((hw + overhang,  hl + overhang, h_wall - 10))
    r_r3 = bm.verts.new((-10.0,  hl + overhang, z_peak + 15))
    add_bmesh_face(bm, uv_layer, [r_r0, r_r1, r_r2, r_r3], UV_WOOD_MID)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=950.0)

# ==============================================================================
# 11. SM_Struct_Tent_Canvas (Tan Canvas Wall Tent with X-Crossed Poles)
# ==============================================================================
def build_struct_tent_canvas():
    scene, mat = setup_scene()
    name = "SM_Struct_Tent_Canvas"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l = 320.0, 380.0
    hw, hl = w * 0.5, l * 0.5
    h_wall = 110.0
    h_ridge = 240.0
    
    # Sidewalls (Tan canvas cloth)
    sw_l0 = bm.verts.new((-hw, -hl, 0))
    sw_l1 = bm.verts.new((-hw,  hl, 0))
    sw_l2 = bm.verts.new((-hw,  hl, h_wall))
    sw_l3 = bm.verts.new((-hw, -hl, h_wall))
    add_bmesh_face(bm, uv_layer, [sw_l0, sw_l1, sw_l2, sw_l3], UV_WOOD_LIGHT)
    
    sw_r0 = bm.verts.new((hw, -hl, 0))
    sw_r1 = bm.verts.new((hw, -hl, h_wall))
    sw_r2 = bm.verts.new((hw,  hl, h_wall))
    sw_r3 = bm.verts.new((hw,  hl, 0))
    add_bmesh_face(bm, uv_layer, [sw_r0, sw_r1, sw_r2, sw_r3], UV_WOOD_WARM)
    
    # Slanted Roof Canopy (Tan Canvas)
    rc_l0 = bm.verts.new((-hw - 15, -hl - 10, h_wall - 5))
    rc_l1 = bm.verts.new((0.0, -hl - 10, h_ridge + 5))
    rc_l2 = bm.verts.new((0.0,  hl + 10, h_ridge + 5))
    rc_l3 = bm.verts.new((-hw - 15,  hl + 10, h_wall - 5))
    add_bmesh_face(bm, uv_layer, [rc_l0, rc_l1, rc_l2, rc_l3], UV_WOOD_LIGHT)
    
    rc_r0 = bm.verts.new((0.0, -hl - 10, h_ridge + 5))
    rc_r1 = bm.verts.new((hw + 15, -hl - 10, h_wall - 5))
    rc_r2 = bm.verts.new((hw + 15,  hl + 10, h_wall - 5))
    rc_r3 = bm.verts.new((0.0,  hl + 10, h_ridge + 5))
    add_bmesh_face(bm, uv_layer, [rc_r0, rc_r1, rc_r2, rc_r3], UV_WOOD_WARM)
    
    # Front Flap Doors (Split down center)
    tf0 = bm.verts.new((-hw, -hl, 0))
    tf1 = bm.verts.new((-hw, -hl, h_wall))
    tf2 = bm.verts.new((0.0, -hl, h_ridge))
    tf3 = bm.verts.new((-10.0, -hl, 0))
    add_bmesh_face(bm, uv_layer, [tf0, tf1, tf2, tf3], UV_WOOD_LIGHT)
    
    tf4 = bm.verts.new((10.0, -hl, 0))
    tf5 = bm.verts.new((0.0, -hl, h_ridge))
    tf6 = bm.verts.new((hw, -hl, h_wall))
    tf7 = bm.verts.new((hw, -hl, 0))
    add_bmesh_face(bm, uv_layer, [tf4, tf5, tf6, tf7], UV_WOOD_WARM)
    
    # Back wall
    tb0 = bm.verts.new((-hw, hl, 0))
    tb1 = bm.verts.new((hw, hl, 0))
    tb2 = bm.verts.new((hw, hl, h_wall))
    tb3 = bm.verts.new((0.0, hl, h_ridge))
    tb4 = bm.verts.new((-hw, hl, h_wall))
    add_bmesh_face(bm, uv_layer, [tb0, tb1, tb2, tb3, tb4], UV_WOOD_LIGHT)
    
    # Prominent Crossed X Timber Ridge Poles at Front and Back
    for py in [-hl - 6, hl + 6]:
        # Pole 1: from bottom-left (-hw) sloping up past ridge to (+30, h_ridge + 45)
        p1_0 = bm.verts.new((-hw - 6, py - 4, 0))
        p1_1 = bm.verts.new(( 32.0, py - 4, h_ridge + 45))
        p1_2 = bm.verts.new(( 32.0, py + 4, h_ridge + 45))
        p1_3 = bm.verts.new((-hw - 6, py + 4, 0))
        add_bmesh_face(bm, uv_layer, [p1_0, p1_1, p1_2, p1_3], UV_WOOD_MID)
        
        # Pole 2: from bottom-right (+hw) sloping up past ridge to (-30, h_ridge + 45)
        p2_0 = bm.verts.new(( hw + 6, py - 4, 0))
        p2_1 = bm.verts.new((-32.0, py - 4, h_ridge + 45))
        p2_2 = bm.verts.new((-32.0, py + 4, h_ridge + 45))
        p2_3 = bm.verts.new(( hw + 6, py + 4, 0))
        add_bmesh_face(bm, uv_layer, [p2_0, p2_1, p2_2, p2_3], UV_WOOD_MID)
        
    # Guy Lines with Wooden Stakes
    for side in [-1, 1]:
        for y_pos in [-hl * 0.6, hl * 0.6]:
            stake_x = side * (hw + 60.0)
            add_box(bm, uv_layer, (stake_x - 3, y_pos - 3, 0), (stake_x + 3, y_pos + 3, 22), UV_WOOD_DARK)
            gl0 = bm.verts.new((side * hw, y_pos, h_wall))
            gl1 = bm.verts.new((stake_x, y_pos, 15))
            gl2 = bm.verts.new((stake_x, y_pos + 2, 15))
            gl3 = bm.verts.new((side * hw, y_pos + 2, h_wall))
            add_bmesh_face(bm, uv_layer, [gl0, gl1, gl2, gl3], UV_WHITE_TRIM)
            
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=550.0)

# ==============================================================================
# 12. SM_Struct_Tent_Dome (Modern Dome Tent with Orange Rainfly & Guy Ropes)
# ==============================================================================
def build_struct_tent_dome():
    scene, mat = setup_scene()
    name = "SM_Struct_Tent_Dome"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    r_base = 150.0
    h_total = 175.0
    sides = 8
    
    # Lower Tent Body (Slate Grey-Blue)
    v_bot = []
    v_mid = []
    h_mid = h_total * 0.45
    r_mid = r_base * 0.95
    for i in range(sides):
        a = i * 2.0 * math.pi / sides
        v_bot.append(bm.verts.new((r_base * math.cos(a), r_base * math.sin(a), 0)))
        v_mid.append(bm.verts.new((r_mid * math.cos(a), r_mid * math.sin(a), h_mid)))
    for i in range(sides):
        nxt = (i + 1) % sides
        add_bmesh_face(bm, uv_layer, [v_bot[i], v_bot[nxt], v_mid[nxt], v_mid[i]], UV_TENT_BODY)
    add_bmesh_face(bm, uv_layer, list(reversed(v_bot)), UV_TIRE_RUBBER)
    
    # Top Rainfly (Orange, Hexagonal/Octagonal faceted dome with peaked vestibule)
    h_top = h_total
    v_top_rim = []
    r_fly = r_base * 1.05
    for i in range(sides):
        a = i * 2.0 * math.pi / sides
        f_ext = 1.25 if (i == 4 or i == 5) else 1.0
        v_top_rim.append(bm.verts.new((r_fly * f_ext * math.cos(a), r_fly * f_ext * math.sin(a), h_mid - 10)))
        
    v_apex = bm.verts.new((0.0, 0.0, h_top))
    for i in range(sides):
        nxt = (i + 1) % sides
        add_bmesh_face(bm, uv_layer, [v_top_rim[i], v_top_rim[nxt], v_apex], UV_TENT_ORANGE)
        
    add_box(bm, uv_layer, (-30, -r_base * 0.95, 0), (30, -r_base * 0.85, h_mid * 0.8), UV_WINDOW_DARK)
    
    for i in [1, 3, 5, 7]:
        a = i * 2.0 * math.pi / sides
        sx = (r_base + 45.0) * math.cos(a)
        sy = (r_base + 45.0) * math.sin(a)
        add_box(bm, uv_layer, (sx - 2, sy - 2, 0), (sx + 2, sy + 2, 12), UV_TIN_ROOF)
        g0 = bm.verts.new((r_fly * math.cos(a), r_fly * math.sin(a), h_mid))
        g1 = bm.verts.new((sx, sy, 8))
        g2 = bm.verts.new((sx + 1, sy + 1, 8))
        g3 = bm.verts.new((r_fly * math.cos(a) + 1, r_fly * math.sin(a) + 1, h_mid))
        add_bmesh_face(bm, uv_layer, [g0, g1, g2, g3], UV_WHITE_TRIM)
        
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=450.0)

# ==============================================================================
# 13. SM_Struct_Camper_RV (Travel Trailer with Blue Stripe, Hitch & Patio Awning)
# ==============================================================================
def build_struct_camper_rv():
    scene, mat = setup_scene()
    name = "SM_Struct_Camper_RV"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w, l, h_body = 230.0, 560.0, 240.0
    hw, hl = w * 0.5, l * 0.5
    z_floor = 45.0
    
    add_box(bm, uv_layer, (-hw, -hl + 40, z_floor), (hw, hl, z_floor + h_body), UV_PURE_WHITE)
    
    nf0 = bm.verts.new((-hw, -hl, z_floor + 40))
    nf1 = bm.verts.new(( hw, -hl, z_floor + 40))
    nf2 = bm.verts.new(( hw, -hl + 40, z_floor + h_body))
    nf3 = bm.verts.new((-hw, -hl + 40, z_floor + h_body))
    add_bmesh_face(bm, uv_layer, [nf0, nf1, nf2, nf3], UV_PURE_WHITE)
    add_box(bm, uv_layer, (-hw, -hl, z_floor), (hw, -hl + 40, z_floor + 40), UV_TIN_ROOF)
    
    stripe_z0 = z_floor + 80.0
    stripe_z1 = stripe_z0 + 26.0
    add_box(bm, uv_layer, (-hw - 1, -hl + 42, stripe_z0), (-hw + 1, hl, stripe_z1), UV_RV_BLUE)
    add_box(bm, uv_layer, ( hw - 1, -hl + 42, stripe_z0), ( hw + 1, hl, stripe_z1), UV_RV_BLUE)
    add_box(bm, uv_layer, (-hw, hl - 1, stripe_z0), (hw, hl + 1, stripe_z1), UV_RV_BLUE)
    
    add_box(bm, uv_layer, (-hw + 30, -hl + 8, z_floor + 100), (hw - 30, -hl + 14, z_floor + 180), UV_WINDOW_DARK)
    add_box(bm, uv_layer, (hw, -60, z_floor + 110), (hw + 3, 80, z_floor + 180), UV_WINDOW_DARK)
    add_box(bm, uv_layer, (hw, 120, z_floor + 110), (hw + 3, 210, z_floor + 180), UV_WINDOW_DARK)
    add_box(bm, uv_layer, (hw, -180, z_floor), (hw + 3, -90, z_floor + 195), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (hw + 1, -165, z_floor + 110), (hw + 4, -105, z_floor + 175), UV_WINDOW_DARK)
    
    awn_y0, awn_y1 = -80.0, 160.0
    awn_depth = 120.0
    awn_z_top = z_floor + h_body - 15.0
    awn_z_bot = awn_z_top - 45.0
    aw0 = bm.verts.new((hw, awn_y0, awn_z_top))
    aw1 = bm.verts.new((hw + awn_depth, awn_y0, awn_z_bot))
    aw2 = bm.verts.new((hw + awn_depth, awn_y1, awn_z_bot))
    aw3 = bm.verts.new((hw, awn_y1, awn_z_top))
    add_bmesh_face(bm, uv_layer, [aw0, aw1, aw2, aw3], UV_RV_BLUE)
    add_box(bm, uv_layer, (hw + awn_depth - 4, awn_y0, z_floor + 20), (hw + awn_depth + 4, awn_y0 + 6, awn_z_bot), UV_WHITE_TRIM)
    add_box(bm, uv_layer, (hw + awn_depth - 4, awn_y1 - 6, z_floor + 20), (hw + awn_depth + 4, awn_y1, awn_z_bot), UV_WHITE_TRIM)
    
    wheel_y = 60.0
    for side in [-1, 1]:
        wx = side * (hw - 4)
        add_cylinder_x(bm, uv_layer, wx - 16*side, wx + 16*side, 34.0, 12, UV_TIRE_RUBBER, UV_TIRE_RUBBER, cy=wheel_y, cz=34.0)
        add_cylinder_x(bm, uv_layer, wx + 14*side, wx + 17*side, 18.0, 8, UV_CHROME_HUB, UV_CHROME_HUB, cy=wheel_y, cz=34.0)
        
    tongue_tip_y = -hl - 90.0
    add_box(bm, uv_layer, (-25, tongue_tip_y, z_floor - 15), (25, -hl + 20, z_floor - 5), UV_STEEL_DARK)
    add_cylinder_z(bm, uv_layer, 0, z_floor + 15, 5.0, 6, UV_STEEL_DARK, cx=0, cy=tongue_tip_y + 15)
    for px in [-16, 16]:
        add_cylinder_z(bm, uv_layer, z_floor, z_floor + 45, 12.0, 8, UV_WHITE_TRIM, UV_WHITE_TRIM, cx=px, cy=-hl - 25)
        
    add_box(bm, uv_layer, (-40, -20, z_floor + h_body), (40, 80, z_floor + h_body + 24), UV_WHITE_TRIM)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=800.0)

# ==============================================================================
# 14. SM_Struct_Camper_Teardrop (Streamlined Teardrop Camper with Porthole Windows)
# ==============================================================================
def build_struct_camper_teardrop():
    scene, mat = setup_scene()
    name = "SM_Struct_Camper_Teardrop"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    w = 190.0
    hw = w * 0.5
    z_floor = 40.0
    
    profile_pts = [
        (-120.0, z_floor),          # Front bottom
        (-140.0, z_floor + 40.0),   # Front lower curve
        (-135.0, z_floor + 110.0),  # Front mid curve
        (-100.0, z_floor + 165.0),  # Front top curve
        ( -30.0, z_floor + 185.0),  # Crown peak
        (  50.0, z_floor + 170.0),  # Rear crown
        ( 120.0, z_floor + 120.0),  # Rear slope
        ( 160.0, z_floor + 50.0),   # Rear tail tip
        ( 140.0, z_floor),          # Rear bottom
    ]
    
    n_pts = len(profile_pts)
    v_left = [bm.verts.new((-hw, y, z)) for y, z in profile_pts]
    v_right = [bm.verts.new((hw, y, z)) for y, z in profile_pts]
    
    add_bmesh_face(bm, uv_layer, list(reversed(v_left)), UV_WHITE_TRIM)
    add_bmesh_face(bm, uv_layer, v_right, UV_WHITE_TRIM)
    
    for i in range(n_pts - 1):
        add_bmesh_face(bm, uv_layer, [v_left[i], v_right[i], v_right[i+1], v_left[i+1]], UV_PURE_WHITE)
    add_bmesh_face(bm, uv_layer, [v_left[-1], v_right[-1], v_right[0], v_left[0]], UV_STEEL_DARK)
    
    add_box(bm, uv_layer, (-hw - 1, -120, z_floor), (-hw + 1, 140, z_floor + 55), UV_STEEL_MID)
    add_box(bm, uv_layer, ( hw - 1, -120, z_floor), ( hw + 1, 140, z_floor + 55), UV_STEEL_MID)
    
    add_box(bm, uv_layer, (hw, -45, z_floor), (hw + 3, 35, z_floor + 140), UV_WHITE_TRIM)
    add_cylinder_x(bm, uv_layer, hw + 1, hw + 4, 14.0, 8, UV_WINDOW_DARK, UV_WINDOW_DARK, cy=-5, cz=z_floor + 85)
    add_cylinder_x(bm, uv_layer, hw + 1, hw + 4, 16.0, 8, UV_WINDOW_DARK, UV_WINDOW_DARK, cy=75, cz=z_floor + 95)
    
    wheel_y = 55.0
    for side in [-1, 1]:
        wx = side * (hw + 6)
        add_box(bm, uv_layer, (wx - 10*side, wheel_y - 35, z_floor + 25), (wx + 10*side, wheel_y + 35, z_floor + 45), UV_WHITE_TRIM)
        add_cylinder_x(bm, uv_layer, wx - 12*side, wx + 12*side, 28.0, 10, UV_TIRE_RUBBER, UV_TIRE_RUBBER, cy=wheel_y, cz=28.0)
        add_cylinder_x(bm, uv_layer, wx + 10*side, wx + 14*side, 15.0, 8, UV_CHROME_HUB, UV_CHROME_HUB, cy=wheel_y, cz=28.0)
        
    add_box(bm, uv_layer, (-20, -210, z_floor - 15), (20, -120, z_floor - 5), UV_STEEL_DARK)
    add_cylinder_z(bm, uv_layer, z_floor, z_floor + 50, 32.0, 8, UV_TIN_ROOF, UV_TIN_ROOF, cx=0, cy=-150)
    
    bm.to_mesh(mesh)
    bm.free()
    finalize_and_export(mesh, obj, mat, name, ortho_scale=550.0)

# ==============================================================================
# MAIN BATCH EXECUTION
# ==============================================================================
if __name__ == '__main__':
    print("=== BUILDING STRUCTURES BATCH IN BLENDER 5.2 ===")
    build_struct_barn()
    build_struct_cabin_small()
    build_struct_cabin_large()
    build_struct_shed()
    build_struct_house_starter()
    build_struct_house_farmhouse()
    build_struct_coop_chicken()
    build_struct_silo()
    build_struct_greenhouse()
    build_struct_stable()
    build_struct_tent_canvas()
    build_struct_tent_dome()
    build_struct_camper_rv()
    build_struct_camper_teardrop()
    print("\nSUCCESS: All 14 building/structure models built, rendered, and exported!")

