import bpy
import bmesh
import os
import sys
import math
import mathutils

PALETTE_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\textures\palettes\T_Homesteader_Palette.png"
RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test"
COMPARISON_PATH = r"C:\Users\casey\.gemini\antigravity\brain\6940286d-0152-4b36-9e37-9e6cff11c21a\calf_icon_comparison.png"
ORIGINAL_ICON = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
os.makedirs(RENDERS_DIR, exist_ok=True)

def get_uv(col, row):
    return ((col + 0.5) / 16.0, 1.0 - (row + 0.5) / 16.0)

UV_WHITE        = get_uv(5, 8)   # Pure white
UV_OFFWHITE     = get_uv(1, 8)   # Cream white
UV_BLACK        = get_uv(4, 15)  # Rich black (eyes, hooves)
UV_HOOF_DARK    = get_uv(3, 15)  # Dark hoof brown/grey
UV_PINK_SKIN    = get_uv(1, 7)   # Pink snout/inner ears
UV_CHESTNUT_MID = get_uv(2, 1)   # Chestnut calf
UV_DARK_BROWN   = get_uv(1, 1)   # Dark brown
UV_TAN_JERSEY   = get_uv(1, 0)   # Caramel tan
UV_CREAM_HORN   = get_uv(0, 2)   # Cream horn

def set_face_uv(f, uv_layer, uv):
    col = int(uv[0] * 16.0)
    row = int(round((1.0 - uv[1]) * 16.0 - 0.5))
    u_min = (col + 0.25) / 16.0
    u_max = (col + 0.75) / 16.0
    v_min = 1.0 - (row + 0.75) / 16.0
    v_max = 1.0 - (row + 0.25) / 16.0
    
    n = len(f.loops)
    u_mid = (u_min + u_max) * 0.5
    v_mid = (v_min + v_max) * 0.5
    rad_u = (u_max - u_min) * 0.4
    rad_v = (v_max - v_min) * 0.4
    for i, loop in enumerate(f.loops):
        a = i * 2.0 * math.pi / n
        loop[uv_layer].uv = (u_mid + rad_u * math.cos(a), v_mid + rad_v * math.sin(a))

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
    node_bsdf.inputs['Roughness'].default_value = 0.55
    
    node_tex = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(PALETTE_PATH):
        img = bpy.data.images.load(PALETTE_PATH)
        img.colorspace_settings.name = 'sRGB'
        node_tex.image = img
        node_tex.interpolation = 'Closest'
        
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    # Lighting matching isometric icon angle (~35° pitch, 45° yaw)
    l_key = bpy.data.lights.new("KeyLight", type='SUN')
    l_key.energy = 4.2
    l_key.color = (1.0, 0.98, 0.95)
    l_key_obj = bpy.data.objects.new("KeyLight", l_key)
    scene.collection.objects.link(l_key_obj)
    l_key_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(-35))
    
    l_fill = bpy.data.lights.new("FillLight", type='SUN')
    l_fill.energy = 2.0
    l_fill.color = (0.85, 0.90, 1.0)
    l_fill_obj = bpy.data.objects.new("FillLight", l_fill)
    scene.collection.objects.link(l_fill_obj)
    l_fill_obj.rotation_euler = (math.radians(60), math.radians(-30), math.radians(120))
    
    return scene, mat

def build_model():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("Organic_Calf")
    mesh_obj = bpy.data.objects.new("Organic_Calf", mesh)
    scene.collection.objects.link(mesh_obj)
    mesh_obj.data.materials.append(mat)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    def create_ring(points):
        return [bm.verts.new(p) for p in points]
        
    def bridge_rings(r1, r2, uv):
        n = len(r1)
        for i in range(n):
            nxt = (i + 1) % n
            try:
                f = bm.faces.new([r1[i], r1[nxt], r2[nxt], r2[i]])
                f.smooth = True
                set_face_uv(f, uv_layer, uv)
            except ValueError:
                pass
                
    def cap_ring(ring, uv, reverse=False):
        try:
            verts = list(reversed(ring)) if reverse else ring
            f = bm.faces.new(verts)
            f.smooth = True
            set_face_uv(f, uv_layer, uv)
        except ValueError:
            pass

    # =========================================================================
    # 1. TORSO (Seamless 8-sided lofted cylinder)
    # =========================================================================
    # 8 points around torso: Top, TopRight, Right, BotRight, Bottom, BotLeft, Left, TopLeft
    def torso_pts(cy, cz, rx, rz_top, rz_bot):
        return [
            ( 0.0,            cy, cz + rz_top),
            ( rx * 0.707,     cy, cz + rz_top * 0.707),
            ( rx,             cy, cz),
            ( rx * 0.707,     cy, cz - rz_bot * 0.707),
            ( 0.0,            cy, cz - rz_bot),
            (-rx * 0.707,     cy, cz - rz_bot * 0.707),
            (-rx,             cy, cz),
            (-rx * 0.707,     cy, cz + rz_top * 0.707),
        ]
        
    r_rump_cap = [bm.verts.new((0, 22.0, 36.0))]
    r_rump   = create_ring(torso_pts(cy=18.0, cz=38.0, rx=12.0, rz_top=10.0, rz_bot=8.0))
    r_flank  = create_ring(torso_pts(cy=6.0,  cz=38.0, rx=13.5, rz_top=11.0, rz_bot=10.0))
    r_chest  = create_ring(torso_pts(cy=-8.0, cz=39.0, rx=14.0, rz_top=12.0, rz_bot=10.0))
    r_neck_b = create_ring(torso_pts(cy=-20.0,cz=42.0, rx=11.0, rz_top=11.0, rz_bot=8.0))
    
    # Cap rear rump
    cap_ring(r_rump, UV_TAN_JERSEY, reverse=True)
    bridge_rings(r_rump, r_flank, UV_TAN_JERSEY)
    bridge_rings(r_flank, r_chest, UV_TAN_JERSEY)
    bridge_rings(r_chest, r_neck_b, UV_TAN_JERSEY)
    
    # =========================================================================
    # 2. NECK & HEAD (Extruding forward and upward)
    # =========================================================================
    r_neck_m = create_ring(torso_pts(cy=-28.0, cz=50.0, rx=8.5, rz_top=9.0, rz_bot=7.0))
    bridge_rings(r_neck_b, r_neck_m, UV_TAN_JERSEY)
    
    # Head Base
    r_head_b = create_ring(torso_pts(cy=-34.0, cz=58.0, rx=10.0, rz_top=11.0, rz_bot=8.0))
    bridge_rings(r_neck_m, r_head_b, UV_TAN_JERSEY)
    
    # Mid Head (Cheeks & Eyeline - expanded)
    r_head_m = create_ring(torso_pts(cy=-42.0, cz=62.0, rx=13.0, rz_top=13.0, rz_bot=9.0))
    bridge_rings(r_head_b, r_head_m, UV_TAN_JERSEY)
    
    # Forehead to Snout Transition
    r_snout_b = create_ring(torso_pts(cy=-49.0, cz=59.0, rx=9.5, rz_top=9.0, rz_bot=7.5))
    bridge_rings(r_head_m, r_snout_b, UV_OFFWHITE) # White forehead blaze
    
    # Snout Tip
    r_snout_t = create_ring(torso_pts(cy=-55.0, cz=57.0, rx=8.0, rz_top=7.0, rz_bot=6.0))
    bridge_rings(r_snout_b, r_snout_t, UV_PINK_SKIN) # Pink muzzle
    cap_ring(r_snout_t, UV_PINK_SKIN)
    
    # Nostrils on snout tip
    for nx in [-3.5, 3.5]:
        res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.6)
        M = mathutils.Matrix.Translation((nx, -55.2, 57.0)) @ mathutils.Matrix.Diagonal((0.8, 0.4, 1.0, 1.0))
        for v in res['verts']:
            v.co = M @ v.co
        faces = [f for f in bm.faces if any(v in res['verts'] for v in f.verts)]
        for f in faces:
            f.smooth = True
            set_face_uv(f, uv_layer, UV_DARK_BROWN)
            
    # =========================================================================
    # 3. BIG CHIBI CARTOON EYES (High on cheek, forward facing)
    # =========================================================================
    for side, sign in [('l', -1), ('r', 1)]:
        # Large black shiny dome
        eye_center = (sign * 11.2, -43.5, 63.5)
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=4.2)
        # Rotated to look forward-outward
        R = mathutils.Euler((0, math.radians(sign * 15), math.radians(sign * 25))).to_matrix().to_4x4()
        S = mathutils.Matrix.Diagonal((0.45, 1.0, 1.05, 1.0))
        M = mathutils.Matrix.Translation(eye_center) @ R @ S
        for v in res['verts']:
            v.co = M @ v.co
        for f in [f for f in bm.faces if any(v in res['verts'] for v in f.verts)]:
            f.smooth = True
            set_face_uv(f, uv_layer, UV_BLACK)
            
        # White Specular Highlight Circle on Top-Left of eye!
        hl_center = (sign * 11.2 + sign * 1.5, -45.2, 65.5)
        res_hl = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.5)
        M_hl = mathutils.Matrix.Translation(hl_center) @ R @ mathutils.Matrix.Diagonal((0.3, 0.8, 0.8, 1.0))
        for v in res_hl['verts']:
            v.co = M_hl @ v.co
        for f in [f for f in bm.faces if any(v in res_hl['verts'] for v in f.verts)]:
            f.smooth = True
            set_face_uv(f, uv_layer, UV_WHITE)

    # =========================================================================
    # 4. EARS & HORNS
    # =========================================================================
    for side, sign in [('l', -1), ('r', 1)]:
        # Leaf-shaped drooping ear extending sideways
        e_root = (sign * 11.0, -38.0, 68.0)
        e_mid  = (sign * 18.0, -36.0, 66.0)
        e_tip  = (sign * 22.0, -34.0, 62.0)
        
        # Outer ear lobe
        res_e = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=4.5, radius2=1.0, depth=14.0)
        rot_e = mathutils.Euler((math.radians(15), math.radians(sign * -35), math.radians(sign * 15))).to_matrix().to_4x4()
        M_e = mathutils.Matrix.Translation(e_mid) @ rot_e @ mathutils.Matrix.Diagonal((1.0, 0.4, 0.8, 1.0))
        for v in res_e['verts']:
            v.co = M_e @ v.co
        for f in [f for f in bm.faces if any(v in res_e['verts'] for v in f.verts)]:
            f.smooth = True
            set_face_uv(f, uv_layer, UV_TAN_JERSEY)
            
        # Inner ear pink
        res_ep = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=3.0, radius2=0.5, depth=11.0)
        M_ep = mathutils.Matrix.Translation((sign * 17.5, -37.0, 65.5)) @ rot_e @ mathutils.Matrix.Diagonal((0.9, 0.25, 0.6, 1.0))
        for v in res_ep['verts']:
            v.co = M_ep @ v.co
        for f in [f for f in bm.faces if any(v in res_ep['verts'] for v in f.verts)]:
            f.smooth = True
            set_face_uv(f, uv_layer, UV_PINK_SKIN)
            
        # Tiny cute cream horn buds on top crown
        h_base = (sign * 6.0, -36.0, 72.0)
        h_tip  = (sign * 8.5, -34.0, 80.0)
        res_h = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=2.8, radius2=0.8, depth=9.0)
        rot_h = mathutils.Euler((math.radians(-10), math.radians(sign * 20), 0)).to_matrix().to_4x4()
        M_h = mathutils.Matrix.Translation(((h_base[0]+h_tip[0])*0.5, (h_base[1]+h_tip[1])*0.5, (h_base[2]+h_tip[2])*0.5)) @ rot_h
        for v in res_h['verts']:
            v.co = M_h @ v.co
        for f in [f for f in bm.faces if any(v in res_h['verts'] for v in f.verts)]:
            f.smooth = True
            set_face_uv(f, uv_layer, UV_CREAM_HORN)

    # =========================================================================
    # 5. 4 TAPERED LEGS WITH HOOVES
    # =========================================================================
    legs_cfg = [
        (-10.0, -12.0), # Front Left
        ( 10.0, -12.0), # Front Right
        (-9.0,   14.0), # Rear Left
        ( 9.0,   14.0), # Rear Right
    ]
    for lx, ly in legs_cfg:
        # Leg Upper to Knee
        res_lu = bmesh.ops.create_cone(bm, cap_ends=False, segments=8, radius1=5.5, radius2=4.2, depth=16.0)
        M_lu = mathutils.Matrix.Translation((lx, ly, 23.0))
        for v in res_lu['verts']:
            v.co = M_lu @ v.co
        for f in [f for f in bm.faces if any(v in res_lu['verts'] for v in f.verts)]:
            f.smooth = True
            set_face_uv(f, uv_layer, UV_TAN_JERSEY)
            
        # Leg Lower to Ankle
        res_ll = bmesh.ops.create_cone(bm, cap_ends=False, segments=8, radius1=4.2, radius2=3.5, depth=12.0)
        M_ll = mathutils.Matrix.Translation((lx, ly, 9.0))
        for v in res_ll['verts']:
            v.co = M_ll @ v.co
        for f in [f for f in bm.faces if any(v in res_ll['verts'] for v in f.verts)]:
            f.smooth = True
            set_face_uv(f, uv_layer, UV_TAN_JERSEY)
            
        # Hoof Foot
        res_hf = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=3.5, radius2=4.0, depth=4.0)
        M_hf = mathutils.Matrix.Translation((lx, ly - 0.5, 2.0))
        for v in res_hf['verts']:
            v.co = M_hf @ v.co
        for f in [f for f in bm.faces if any(v in res_hf['verts'] for v in f.verts)]:
            f.smooth = True
            set_face_uv(f, uv_layer, UV_HOOF_DARK)
            
    # =========================================================================
    # 6. TAIL
    # =========================================================================
    res_t = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=2.0, radius2=1.2, depth=16.0)
    rot_t = mathutils.Euler((math.radians(-30), 0, 0)).to_matrix().to_4x4()
    M_t = mathutils.Matrix.Translation((0.0, 24.0, 32.0)) @ rot_t
    for v in res_t['verts']:
        v.co = M_t @ v.co
    for f in [f for f in bm.faces if any(v in res_t['verts'] for v in f.verts)]:
        f.smooth = True
        set_face_uv(f, uv_layer, UV_TAN_JERSEY)
        
    # Tail tuft
    res_tf = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=2.6)
    M_tf = mathutils.Matrix.Translation((0.0, 27.5, 24.0)) @ mathutils.Matrix.Diagonal((0.8, 1.0, 1.5, 1.0))
    for v in res_tf['verts']:
        v.co = M_tf @ v.co
    for f in [f for f in bm.faces if any(v in res_tf['verts'] for v in f.verts)]:
        f.smooth = True
        set_face_uv(f, uv_layer, UV_DARK_BROWN)

    bm.to_mesh(mesh)
    bm.free()
    
    # Subdivision Modifier to achieve the smooth, stylized low-poly curvature of the icon!
    sub_mod = mesh_obj.modifiers.new(name="Subsurf", type='SUBSURF')
    sub_mod.levels = 1
    sub_mod.render_levels = 1
    
    # Render Preview
    max_z = max(v.co.z for v in mesh_obj.data.vertices)
    mid_z = max_z * 0.5
    
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 115.0
    cam_data.clip_end = 5000.0
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    dist = 800.0
    cam_obj.location = (dist * 0.7, -dist * 0.7, mid_z + dist * 0.45)
    direction = -(cam_obj.location - mathutils.Vector((0, 0, mid_z))).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    render_path = os.path.join(RENDERS_DIR, "Organic_Calf_render.png")
    scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered organic calf: {render_path}")

if __name__ == '__main__':
    build_model()
