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

UV_WHITE        = get_uv(5, 8)   # Pure white
UV_OFFWHITE     = get_uv(1, 8)   # Cream white
UV_BLACK        = get_uv(4, 15)  # Rich black (eyes, hooves)
UV_HOOF_DARK    = get_uv(3, 15)  # Dark hoof brown/grey
UV_PINK_SKIN    = get_uv(1, 7)   # Pink snout/inner ears
UV_DARK_BROWN   = get_uv(1, 1)   # Dark brown nostrils/tail
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
    node_bsdf.inputs['Roughness'].default_value = 0.5
    
    node_tex = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(PALETTE_PATH):
        img = bpy.data.images.load(PALETTE_PATH)
        img.colorspace_settings.name = 'sRGB'
        node_tex.image = img
        node_tex.interpolation = 'Closest'
        
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    # Sun lighting matching Homesteader 3/4 isometric icon standard
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

def build_cute_calf_v2():
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new("Organic_Calf_v2")
    mesh_obj = bpy.data.objects.new("Organic_Calf_v2", mesh)
    scene.collection.objects.link(mesh_obj)
    mesh_obj.data.materials.append(mat)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    def add_geom_part(create_fn, center, scale, rot, uv):
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

    # 1. Torso: Compact, rounded, plump body (length ~32cm, width ~24cm, height ~24cm)
    # Rear / Rump
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=12.5),
                  center=(0.0, 10.0, 26.0), scale=(1.0, 1.15, 1.0), rot=(0,0,0), uv=UV_TAN_JERSEY)
    # Flank / Mid-body
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=13.0),
                  center=(0.0, 1.0, 26.5), scale=(1.05, 1.15, 1.05), rot=(0,0,0), uv=UV_TAN_JERSEY)
    # White belly patch
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=11.0),
                  center=(0.0, 4.0, 20.5), scale=(0.9, 1.1, 0.7), rot=(0,0,0), uv=UV_OFFWHITE)
    # White flank spot on right side
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=7.0),
                  center=(10.5, 7.0, 24.0), scale=(0.5, 1.0, 1.0), rot=(0,0,0), uv=UV_OFFWHITE)
    # Front / Shoulders
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=13.0),
                  center=(0.0, -8.0, 27.5), scale=(1.05, 1.1, 1.1), rot=(0,0,0), uv=UV_TAN_JERSEY)

    # 2. Neck: Very short, thick connection directly to head
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=11.5),
                  center=(0.0, -16.0, 32.5), scale=(0.95, 0.95, 1.05), rot=(math.radians(-20),0,0), uv=UV_TAN_JERSEY)

    # 3. Head: Big adorable rounded chibi head (center at -23.0, Z=38.0)
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=13.5),
                  center=(0.0, -24.0, 38.0), scale=(1.1, 1.1, 1.05), rot=(math.radians(-10),0,0), uv=UV_TAN_JERSEY)
    # White forehead patch running down the front of the face
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=10.5),
                  center=(0.0, -28.0, 41.5), scale=(0.75, 0.85, 0.95), rot=(math.radians(-10),0,0), uv=UV_OFFWHITE)

    # 4. Muzzle: Soft pink rounded dome on lower front of face
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=8.5),
                  center=(0.0, -34.5, 33.0), scale=(1.2, 0.85, 0.85), rot=(math.radians(-5),0,0), uv=UV_PINK_SKIN)
    # Dark Nostrils
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=1.4),
                  center=(-2.8, -39.0, 33.0), scale=(0.7, 0.4, 1.0), rot=(0,0,0), uv=UV_DARK_BROWN)
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=1.4),
                  center=( 2.8, -39.0, 33.0), scale=(0.7, 0.4, 1.0), rot=(0,0,0), uv=UV_DARK_BROWN)

    # 5. Big Cartoon Eyes: Glossy black circular discs with white highlight reflection
    for sign, side in [(-1, 'l'), (1, 'r')]:
        # Eye base
        add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=2, radius=3.2),
                      center=(sign * 11.2, -29.5, 39.5), scale=(0.4, 1.0, 1.05),
                      rot=(0, math.radians(sign * 15), math.radians(sign * 25)), uv=UV_BLACK)
        # White reflection dot on top-left of eye
        add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=1.2),
                      center=(sign * 11.2 + sign * 1.0, -31.0, 41.0), scale=(0.3, 0.7, 0.7),
                      rot=(0, math.radians(sign * 15), math.radians(sign * 25)), uv=UV_WHITE)

    # 6. Ears: Wide leaf-shaped rounded drooping lobes spreading outward
    for sign, side in [(-1, 'l'), (1, 'r')]:
        # Outer ear
        add_geom_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=8, radius1=4.2, radius2=1.0, depth=10.0),
                      center=(sign * 16.5, -23.0, 40.0), scale=(1.0, 0.4, 0.85),
                      rot=(math.radians(10), math.radians(sign * -35), math.radians(sign * 10)), uv=UV_TAN_JERSEY)
        # Inner ear pink
        add_geom_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=6, radius1=2.8, radius2=0.6, depth=7.5),
                      center=(sign * 16.0, -24.0, 39.8), scale=(0.9, 0.25, 0.7),
                      rot=(math.radians(10), math.radians(sign * -35), math.radians(sign * 10)), uv=UV_PINK_SKIN)

    # 7. Horn Buds: Cute small cream cones pointing outward-up
    for sign, side in [(-1, 'l'), (1, 'r')]:
        add_geom_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=6, radius1=2.2, radius2=0.6, depth=6.5),
                      center=(sign * 6.5, -22.0, 48.0), scale=(1.0, 1.0, 1.0),
                      rot=(math.radians(-10), math.radians(sign * 25), 0), uv=UV_CREAM_HORN)

    # 8. 4 Thick Stubby Legs with Cloven Dark Hooves
    legs_cfg = [
        (-8.0, -9.0),  # Front Left
        ( 8.0, -9.0),  # Front Right
        (-7.5, 10.0),  # Rear Left
        ( 7.5, 10.0),  # Rear Right
    ]
    for lx, ly in legs_cfg:
        # Upper Leg
        add_geom_part(lambda b: bmesh.ops.create_cone(b, cap_ends=False, segments=8, radius1=4.8, radius2=3.8, depth=12.0),
                      center=(lx, ly, 15.0), scale=(1.0, 1.0, 1.0), rot=(0,0,0), uv=UV_TAN_JERSEY)
        # Lower Leg
        add_geom_part(lambda b: bmesh.ops.create_cone(b, cap_ends=False, segments=8, radius1=3.8, radius2=3.2, depth=7.0),
                      center=(lx, ly, 6.0), scale=(1.0, 1.0, 1.0), rot=(0,0,0), uv=UV_TAN_JERSEY)
        # Dark Cloven Hoof
        add_geom_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=8, radius1=3.2, radius2=3.5, depth=3.0),
                      center=(lx, ly - 0.4, 1.5), scale=(1.0, 1.0, 1.0), rot=(0,0,0), uv=UV_HOOF_DARK)

    # 9. Tail: Short curved tail with brown tuft
    add_geom_part(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=6, radius1=1.8, radius2=1.0, depth=11.0),
                  center=(0.0, 19.5, 23.0), scale=(1.0, 1.0, 1.0), rot=(math.radians(-35), 0, 0), uv=UV_TAN_JERSEY)
    add_geom_part(lambda b: bmesh.ops.create_icosphere(b, subdivisions=1, radius=2.2),
                  center=(0.0, 22.0, 18.0), scale=(0.8, 1.0, 1.4), rot=(0,0,0), uv=UV_DARK_BROWN)

    bm.to_mesh(mesh)
    bm.free()
    
    # Render
    max_z = max(v.co.z for v in mesh_obj.data.vertices)
    mid_z = max_z * 0.5
    
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 78.0
    cam_data.clip_end = 5000.0
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    dist = 800.0
    cam_obj.location = (dist * 0.7, -dist * 0.7, mid_z + dist * 0.45)
    direction = -(cam_obj.location - mathutils.Vector((0, 0, mid_z))).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    render_path = os.path.join(RENDERS_DIR, "Organic_Calf_v2_render.png")
    scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {render_path}")

if __name__ == '__main__':
    build_cute_calf_v2()

