import bpy
import bmesh
import os
import sys
import math
import mathutils

PALETTE_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\textures\palettes\T_Homesteader_Palette.png"
RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test"
os.makedirs(RENDERS_DIR, exist_ok=True)

def get_uv(col, row):
    return ((col + 0.5) / 16.0, 1.0 - (row + 0.5) / 16.0)

UV_WHITE        = get_uv(5, 8)   # Pure white (eye reflection)
UV_CREAM_WHITE  = get_uv(3, 0)   # Cream white (forehead blaze, belly patch)
UV_BLACK        = get_uv(4, 15)  # Glossy black (eyes)
UV_HOOF_BROWN   = get_uv(2, 1)   # Warm hoof brown
UV_PINK_SNOUT   = get_uv(4, 5)   # Peach/pink snout & inner ears
UV_DARK_BROWN   = get_uv(1, 1)   # Dark brown nostrils & tail tuft
UV_CARAMEL_TAN  = get_uv(1, 0)   # Caramel tan coat
UV_HORN_CREAM   = get_uv(3, 8)   # Cream horn buds

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
    node_bsdf.inputs['Roughness'].default_value = 0.45
    
    node_tex = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(PALETTE_PATH):
        img = bpy.data.images.load(PALETTE_PATH)
        img.colorspace_settings.name = 'sRGB'
        node_tex.image = img
        node_tex.interpolation = 'Closest'
        
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    # Sun lighting exactly matching the icon's top-left key illumination
    l_key = bpy.data.lights.new("KeyLight", type='SUN')
    l_key.energy = 5.5
    l_key.color = (1.0, 0.98, 0.94)
    l_key_obj = bpy.data.objects.new("KeyLight", l_key)
    scene.collection.objects.link(l_key_obj)
    l_key_obj.rotation_euler = (math.radians(35), math.radians(15), math.radians(-45))
    
    l_fill = bpy.data.lights.new("FillLight", type='SUN')
    l_fill.energy = 2.8
    l_fill.color = (0.88, 0.92, 1.0)
    l_fill_obj = bpy.data.objects.new("FillLight", l_fill)
    scene.collection.objects.link(l_fill_obj)
    l_fill_obj.rotation_euler = (math.radians(50), math.radians(-30), math.radians(135))
    
    return scene, mat

def build_cute_calf_v3():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("Organic_Calf_v3")
    mesh_obj = bpy.data.objects.new("Organic_Calf_v3", mesh)
    scene.collection.objects.link(mesh_obj)
    mesh_obj.data.materials.append(mat)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    def add_part(create_fn, center, scale, rot, uv):
        res = create_fn(bm)
        T = mathutils.Matrix.Translation(center)
        R = mathutils.Euler(rot).to_matrix().to_4x4()
        S = mathutils.Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
        M = T @ R @ S
        for v in res['verts']:
            v.co = M @ v.co
        for f in [f for f in bm.faces if any(v in res['verts'] for v in f.verts)]:
            f.smooth = True
            set_face_uv(f, uv_layer, uv)
        return res['verts']

    # -------------------------------------------------------------------------
    # 1. TORSO: Chubby, compact, smooth body
    # -------------------------------------------------------------------------
    # Rump
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=3, radius=13.0),
             center=(0.0, 9.0, 26.5), scale=(1.05, 1.15, 1.0), rot=(0,0,0), uv=UV_CARAMEL_TAN)
    # Mid-body / Flank
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=3, radius=13.5),
             center=(0.0, 0.0, 27.0), scale=(1.08, 1.15, 1.05), rot=(0,0,0), uv=UV_CARAMEL_TAN)
    # White belly patch
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=11.5),
             center=(0.0, 3.0, 20.0), scale=(0.95, 1.15, 0.75), rot=(0,0,0), uv=UV_CREAM_WHITE)
    # White flank spot on right side (visible in icon!)
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=7.5),
             center=(11.0, 5.0, 24.5), scale=(0.55, 1.0, 0.95), rot=(0,0,0), uv=UV_CREAM_WHITE)
    # Shoulders / Front chest
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=3, radius=13.2),
             center=(0.0, -8.5, 27.5), scale=(1.05, 1.1, 1.1), rot=(0,0,0), uv=UV_CARAMEL_TAN)

    # -------------------------------------------------------------------------
    # 2. HEAD & NECK: Lifted up & turned towards viewer (~15° pitch up, -10° yaw)
    # -------------------------------------------------------------------------
    head_rot = (math.radians(14), 0, math.radians(-8))
    
    # Neck transition
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=11.0),
             center=(-0.8, -15.5, 31.5), scale=(0.95, 0.95, 1.05), rot=head_rot, uv=UV_CARAMEL_TAN)

    # Main Chibi Head (Big spherical skull)
    head_center = (-1.5, -23.5, 37.5)
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=3, radius=14.0),
             center=head_center, scale=(1.12, 1.08, 1.05), rot=head_rot, uv=UV_CARAMEL_TAN)
             
    # Large Creamy-White Forehead Patch (Covers crown down between eyes to snout)
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=11.2),
             center=(-1.8, -26.5, 41.0), scale=(0.78, 0.85, 0.98), rot=head_rot, uv=UV_CREAM_WHITE)

    # -------------------------------------------------------------------------
    # 3. SNOUT: Lifted, friendly, cute rounded peach/pink dome
    # -------------------------------------------------------------------------
    snout_center = (-2.2, -33.5, 33.5)
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=3, radius=9.0),
             center=snout_center, scale=(1.2, 0.9, 0.85), rot=head_rot, uv=UV_PINK_SNOUT)
             
    # Two Soft Nostril Indents
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=1.5),
             center=(-5.2, -37.5, 33.8), scale=(0.7, 0.4, 0.9), rot=head_rot, uv=UV_DARK_BROWN)
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=1.5),
             center=( 0.8, -37.5, 33.8), scale=(0.7, 0.4, 1.0), rot=head_rot, uv=UV_DARK_BROWN)

    # -------------------------------------------------------------------------
    # 4. BIG CARTOON EYES: Glossy black with bright white reflection dot
    # -------------------------------------------------------------------------
    # Left eye (camera side)
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=3.4),
             center=(-12.5, -28.0, 39.0), scale=(0.4, 1.0, 1.05),
             rot=(0, math.radians(-15), math.radians(-25)), uv=UV_BLACK)
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=1.3),
             center=(-13.8, -29.2, 40.5), scale=(0.3, 0.7, 0.7),
             rot=(0, math.radians(-15), math.radians(-25)), uv=UV_WHITE)

    # Right eye
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=3.4),
             center=( 9.8, -28.5, 39.5), scale=(0.4, 1.0, 1.05),
             rot=(0, math.radians(15), math.radians(25)), uv=UV_BLACK)
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=1.3),
             center=( 11.0, -29.8, 41.0), scale=(0.3, 0.7, 0.7),
             rot=(0, math.radians(15), math.radians(25)), uv=UV_WHITE)

    # -------------------------------------------------------------------------
    # 5. EARS: Wide leaf-shaped rounded drooping lobes spreading outward
    # -------------------------------------------------------------------------
    # Left ear (camera side)
    add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=8, radius1=4.5, radius2=1.2, depth=11.0),
             center=(-18.5, -21.5, 39.5), scale=(1.0, 0.45, 0.85),
             rot=(math.radians(10), math.radians(-35), math.radians(10)), uv=UV_CARAMEL_TAN)
    add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=6, radius1=3.0, radius2=0.7, depth=8.5),
             center=(-18.0, -22.5, 39.2), scale=(0.9, 0.25, 0.7),
             rot=(math.radians(10), math.radians(-35), math.radians(10)), uv=UV_PINK_SNOUT)

    # Right ear
    add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=8, radius1=4.5, radius2=1.2, depth=11.0),
             center=( 16.5, -22.5, 40.5), scale=(1.0, 0.45, 0.85),
             rot=(math.radians(10), math.radians(35), math.radians(-10)), uv=UV_CARAMEL_TAN)
    add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=6, radius1=3.0, radius2=0.7, depth=8.5),
             center=( 16.0, -23.5, 40.2), scale=(0.9, 0.25, 0.7),
             rot=(math.radians(10), math.radians(35), math.radians(-10)), uv=UV_PINK_SNOUT)

    # -------------------------------------------------------------------------
    # 6. HORN BUDS: Cute small cream cones pointing outward-up
    # -------------------------------------------------------------------------
    add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=6, radius1=2.4, radius2=0.6, depth=7.0),
             center=(-7.2, -21.0, 48.5), scale=(1.0, 1.0, 1.0),
             rot=(math.radians(-5), math.radians(-25), 0), uv=UV_HORN_CREAM)
    add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=6, radius1=2.4, radius2=0.6, depth=7.0),
             center=( 5.2, -21.5, 49.0), scale=(1.0, 1.0, 1.0),
             rot=(math.radians(-5), math.radians(25), 0), uv=UV_HORN_CREAM)

    # -------------------------------------------------------------------------
    # 7. 4 STUBBY LEGS WITH WARM HOOVES
    # -------------------------------------------------------------------------
    legs_cfg = [
        (-8.2, -9.0),  # Front Left
        ( 8.2, -9.0),  # Front Right
        (-7.8, 10.0),  # Rear Left
        ( 7.8, 10.0),  # Rear Right
    ]
    for lx, ly in legs_cfg:
        # Upper Leg
        add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=False, segments=8, radius1=5.0, radius2=3.8, depth=12.0),
                 center=(lx, ly, 15.0), scale=(1.0, 1.0, 1.0), rot=(0,0,0), uv=UV_CARAMEL_TAN)
        # Lower Leg
        add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=False, segments=8, radius1=3.8, radius2=3.2, depth=7.0),
                 center=(lx, ly, 6.0), scale=(1.0, 1.0, 1.0), rot=(0,0,0), uv=UV_CARAMEL_TAN)
        # Hoof Foot
        add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=8, radius1=3.2, radius2=3.6, depth=3.0),
                 center=(lx, ly - 0.4, 1.5), scale=(1.0, 1.0, 1.0), rot=(0,0,0), uv=UV_HOOF_BROWN)

    # -------------------------------------------------------------------------
    # 8. TAIL
    # -------------------------------------------------------------------------
    add_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=6, radius1=1.8, radius2=1.0, depth=11.0),
             center=(0.0, 19.5, 23.0), scale=(1.0, 1.0, 1.0), rot=(math.radians(-35), 0, 0), uv=UV_CARAMEL_TAN)
    add_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=2.2),
             center=(0.0, 22.0, 18.0), scale=(0.8, 1.0, 1.4), rot=(0,0,0), uv=UV_DARK_BROWN)

    bm.to_mesh(mesh)
    bm.free()
    
    # Render
    max_z = max(v.co.z for v in mesh_obj.data.vertices)
    mid_z = max_z * 0.5
    
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 76.0
    cam_data.clip_end = 5000.0
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    dist = 800.0
    cam_obj.location = (dist * 0.7, -dist * 0.7, mid_z + dist * 0.45)
    direction = -(cam_obj.location - mathutils.Vector((0, 0, mid_z))).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    render_path = os.path.join(RENDERS_DIR, "Organic_Calf_v3_render.png")
    scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered v3: {render_path}")

if __name__ == '__main__':
    build_cute_calf_v3()

