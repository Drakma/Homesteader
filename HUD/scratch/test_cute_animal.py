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
UV_SLATE_GREY   = get_uv(1, 3)   # Slate grey
UV_CREAM_HORN   = get_uv(0, 2)   # Cream horn
UV_PINK_SKIN    = get_uv(1, 7)   # Pink snout/ears
UV_GINGER_FUR   = get_uv(4, 1)   # Highland ginger
UV_AUBURN_PIG   = get_uv(4, 0)   # Duroc auburn
UV_CHESTNUT_MID = get_uv(2, 1)   # Chestnut calf
UV_DARK_BROWN   = get_uv(1, 1)   # Dark brown
UV_TAN_JERSEY   = get_uv(1, 0)   # Caramel tan calf
UV_TAN_WOOL     = get_uv(4, 8)   # Tan wool
UV_GOLDEN_YELL  = get_uv(5, 5)   # Chick yellow
UV_ORANGE_BEAK  = get_uv(5, 4)   # Chick orange beak

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
    node_bsdf.inputs['Roughness'].default_value = 0.4
    
    node_tex = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(PALETTE_PATH):
        img = bpy.data.images.load(PALETTE_PATH)
        img.colorspace_settings.name = 'sRGB'
        node_tex.image = img
        node_tex.interpolation = 'Closest'
        
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    # 3-Point Lighting matching icon angle (~35 pitch, 45 yaw)
    l_key = bpy.data.lights.new("KeyLight", type='SUN')
    l_key.energy = 4.5
    l_key.color = (1.0, 0.98, 0.95)
    l_key_obj = bpy.data.objects.new("KeyLight", l_key)
    scene.collection.objects.link(l_key_obj)
    l_key_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(-35))
    
    l_fill = bpy.data.lights.new("FillLight", type='SUN')
    l_fill.energy = 2.2
    l_fill.color = (0.85, 0.90, 1.0)
    l_fill_obj = bpy.data.objects.new("FillLight", l_fill)
    scene.collection.objects.link(l_fill_obj)
    l_fill_obj.rotation_euler = (math.radians(60), math.radians(-30), math.radians(120))
    
    return scene, mat

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

class OrganicMeshBuilder:
    def __init__(self, mesh_obj):
        self.mesh_obj = mesh_obj
        self.bm = bmesh.new()
        self.uv_layer = self.bm.loops.layers.uv.new("UVMap")
        self.dvert_lay = self.bm.verts.layers.deform.verify()
        self.current_group_idx = None
        self.group_map = {}
        
    def set_bone(self, bone_name):
        if bone_name not in self.group_map:
            vg = self.mesh_obj.vertex_groups.new(name=bone_name)
            self.group_map[bone_name] = vg.index
        self.current_group_idx = self.group_map[bone_name]
            
    def _tag(self, verts):
        if self.current_group_idx is not None:
            for v in verts:
                v[self.dvert_lay][self.current_group_idx] = 1.0
                
    def add_icosphere(self, center, radius, subdivisions, uv, scale=(1.0, 1.0, 1.0), rot=(0,0,0)):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=subdivisions, radius=radius)
        verts = res['verts']
        
        T = mathutils.Matrix.Translation(center)
        R = mathutils.Euler(rot).to_matrix().to_4x4()
        S = mathutils.Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
        M = T @ R @ S
        
        for v in verts:
            v.co = M @ v.co
            
        self._tag(verts)
        
        faces = [f for f in self.bm.faces if any(v in verts for v in f.verts)]
        for f in faces:
            f.smooth = True
            set_face_uv(f, self.uv_layer, uv)
        return verts

    def add_cone_limb(self, start, end, r_start, r_end, segments, uv):
        v_dir = mathutils.Vector(end) - mathutils.Vector(start)
        length = v_dir.length
        if length < 0.001:
            return []
        v_dir.normalize()
        
        rot_q = mathutils.Vector((0, 0, 1)).rotation_difference(v_dir)
        mid = (mathutils.Vector(start) + mathutils.Vector(end)) * 0.5
        
        res = bmesh.ops.create_cone(
            self.bm,
            cap_ends=True,
            cap_tris=False,
            segments=segments,
            radius1=r_start,
            radius2=r_end,
            depth=length
        )
        verts = res['verts']
        
        T = mathutils.Matrix.Translation(mid)
        R = rot_q.to_matrix().to_4x4()
        M = T @ R
        
        for v in verts:
            v.co = M @ v.co
            
        self._tag(verts)
        
        faces = [f for f in self.bm.faces if any(v in verts for v in f.verts)]
        for f in faces:
            f.smooth = True
            set_face_uv(f, self.uv_layer, uv)
        return verts

    def finish(self):
        self.bm.to_mesh(self.mesh_obj.data)
        self.bm.free()

def render_model(mesh_obj, name, ortho_scale=120.0):
    scene = bpy.context.scene
    max_z = max(v.co.z for v in mesh_obj.data.vertices)
    mid_z = max_z * 0.5
    
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho_scale
    cam_data.clip_end = 5000.0
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    dist = 800.0
    cam_obj.location = (dist * 0.7, -dist * 0.7, mid_z + dist * 0.45)
    direction = -(cam_obj.location - mathutils.Vector((0, 0, mid_z))).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    out_path = os.path.join(RENDERS_DIR, f"{name}_test_render.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {out_path}")

def build_cute_calf():
    name = "Cute_Baby_Calf"
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    mesh_obj.data.materials.append(mat)
    
    b = OrganicMeshBuilder(mesh_obj)
    
    # 1. Torso: Plump rounded egg body
    b.set_bone("pelvis")
    b.add_icosphere((0.0, 12.0, 44.0), 22.0, 2, UV_TAN_JERSEY, scale=(0.95, 1.1, 1.0))
    b.add_icosphere((0.0, 6.0, 36.0), 18.0, 2, UV_OFFWHITE, scale=(0.85, 1.0, 0.7)) # White belly
    
    b.set_bone("chest")
    b.add_icosphere((0.0, -10.0, 46.0), 23.0, 2, UV_TAN_JERSEY, scale=(1.0, 1.1, 1.05))
    
    # 2. Neck
    b.set_bone("neck")
    b.add_icosphere((0.0, -26.0, 56.0), 16.0, 2, UV_TAN_JERSEY, scale=(0.85, 0.95, 1.1), rot=(math.radians(-25), 0, 0))
    
    # 3. Head: Big adorable rounded chibi head
    b.set_bone("head")
    b.add_icosphere((0.0, -38.0, 68.0), 20.0, 2, UV_TAN_JERSEY, scale=(1.05, 1.1, 1.05))
    b.add_icosphere((0.0, -42.0, 75.0), 14.0, 2, UV_OFFWHITE, scale=(0.7, 0.8, 0.9)) # Forehead blaze
    
    # Muzzle
    b.add_icosphere((0.0, -53.0, 60.0), 12.5, 2, UV_PINK_SKIN, scale=(1.15, 0.9, 0.85))
    b.add_icosphere((-4.0, -59.5, 60.0), 2.0, 1, UV_DARK_BROWN, scale=(0.7, 0.4, 0.9))
    b.add_icosphere(( 4.0, -59.5, 60.0), 2.0, 1, UV_DARK_BROWN, scale=(0.7, 0.4, 0.9))
    
    # Big Cute Eyes
    b.add_icosphere((-14.5, -46.0, 68.0), 4.5, 2, UV_BLACK, scale=(0.5, 1.0, 1.0), rot=(0, math.radians(-15), math.radians(-20)))
    b.add_icosphere((-16.2, -47.5, 69.8), 1.6, 1, UV_WHITE, scale=(0.4, 0.8, 0.8))
    b.add_icosphere(( 14.5, -46.0, 68.0), 4.5, 2, UV_BLACK, scale=(0.5, 1.0, 1.0), rot=(0, math.radians(15), math.radians(20)))
    b.add_icosphere(( 16.2, -47.5, 69.8), 1.6, 1, UV_WHITE, scale=(0.4, 0.8, 0.8))
    
    # Ears
    for ex, sx in [(-18.0, -1), (18.0, 1)]:
        b.add_icosphere((ex, -34.0, 72.0), 8.0, 2, UV_TAN_JERSEY, scale=(1.4, 0.6, 0.5), rot=(math.radians(10), sx * math.radians(-25), sx * math.radians(15)))
        b.add_icosphere((ex + sx*2.0, -35.0, 71.5), 5.5, 1, UV_PINK_SKIN, scale=(1.2, 0.4, 0.4), rot=(math.radians(10), sx * math.radians(-25), sx * math.radians(15)))
        
    # Horn buds
    for hx, sx in [(-7.5, -1), (7.5, 1)]:
        b.add_cone_limb((hx, -34.0, 82.0), (hx + sx*3.0, -32.0, 90.0), 3.0, 1.2, 6, UV_CREAM_HORN)
        
    # 4 Stubby Legs
    leg_coords = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -12.0, -12.0),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  12.0, -12.0),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl", -11.0,  18.0),
        ("leg_br_upper", "leg_br_lower", "foot_br",  11.0,  18.0),
    ]
    for up_b, low_b, foot_b, lx, ly in leg_coords:
        b.set_bone(up_b)
        b.add_cone_limb((lx, ly, 38.0), (lx, ly, 20.0), 7.5, 5.5, 8, UV_TAN_JERSEY)
        b.set_bone(low_b)
        b.add_cone_limb((lx, ly, 20.0), (lx, ly, 6.0), 5.5, 4.5, 8, UV_TAN_JERSEY)
        b.set_bone(foot_b)
        b.add_cone_limb((lx, ly, 6.0), (lx, ly - 1.0, 0.0), 5.0, 5.5, 8, UV_HOOF_DARK)
        
    # Tail
    b.set_bone("tail_01")
    b.add_cone_limb((0.0, 26.0, 46.0), (0.0, 30.0, 32.0), 2.5, 1.8, 6, UV_TAN_JERSEY)
    b.set_bone("tail_02")
    b.add_icosphere((0.0, 30.5, 28.0), 3.5, 1, UV_DARK_BROWN, scale=(0.8, 1.0, 1.5))
    
    b.finish()
    render_model(mesh_obj, name, ortho_scale=115.0)

def build_cute_piglet():
    name = "Cute_Baby_Piglet"
    scene, mat = setup_scene()
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    mesh_obj.data.materials.append(mat)
    
    b = OrganicMeshBuilder(mesh_obj)
    
    # 1. Torso
    b.set_bone("pelvis")
    b.add_icosphere((0.0, 8.0, 24.0), 16.0, 2, UV_PINK_SKIN, scale=(1.05, 1.15, 1.0))
    b.set_bone("chest")
    b.add_icosphere((0.0, -8.0, 25.0), 16.5, 2, UV_PINK_SKIN, scale=(1.1, 1.1, 1.05))
    
    # 2. Head
    b.set_bone("head")
    b.add_icosphere((0.0, -25.0, 27.0), 15.0, 2, UV_PINK_SKIN, scale=(1.1, 1.1, 1.05))
    
    # Button Snout
    b.add_cone_limb((0.0, -34.0, 23.0), (0.0, -38.5, 22.0), 6.5, 6.0, 8, UV_PINK_SKIN)
    b.add_icosphere((-2.2, -39.0, 22.0), 1.2, 1, UV_DARK_BROWN, scale=(0.6, 0.4, 1.0))
    b.add_icosphere(( 2.2, -39.0, 22.0), 1.2, 1, UV_DARK_BROWN, scale=(0.6, 0.4, 1.0))
    
    # Eyes
    b.add_icosphere((-10.5, -29.0, 31.0), 3.5, 2, UV_BLACK, scale=(0.5, 1.0, 1.0), rot=(0, math.radians(-15), math.radians(-20)))
    b.add_icosphere((-11.8, -30.2, 32.2), 1.2, 1, UV_WHITE, scale=(0.4, 0.8, 0.8))
    b.add_icosphere(( 10.5, -29.0, 31.0), 3.5, 2, UV_BLACK, scale=(0.5, 1.0, 1.0), rot=(0, math.radians(15), math.radians(20)))
    b.add_icosphere(( 11.8, -30.2, 32.2), 1.2, 1, UV_WHITE, scale=(0.4, 0.8, 0.8))
    
    # Ears
    for ex, sx in [(-12.0, -1), (12.0, 1)]:
        b.add_icosphere((ex, -22.0, 37.0), 6.5, 2, UV_PINK_SKIN, scale=(1.2, 0.6, 0.5), rot=(math.radians(15), sx * math.radians(-30), sx * math.radians(20)))
        
    # Legs
    leg_coords = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -8.5, -12.0),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  8.5, -12.0),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl", -8.0,  12.0),
        ("leg_br_upper", "leg_br_lower", "foot_br",  8.0,  12.0),
    ]
    for up_b, low_b, foot_b, lx, ly in leg_coords:
        b.set_bone(up_b)
        b.add_cone_limb((lx, ly, 18.0), (lx, ly, 8.0), 5.5, 4.2, 8, UV_PINK_SKIN)
        b.set_bone(foot_b)
        b.add_cone_limb((lx, ly, 8.0), (lx, ly, 0.0), 4.2, 4.0, 8, UV_HOOF_DARK)
        
    # Curly Tail
    b.set_bone("tail_01")
    b.add_cone_limb((0.0, 20.0, 27.0), (0.0, 25.0, 33.0), 2.0, 1.5, 6, UV_PINK_SKIN)
    b.set_bone("tail_02")
    b.add_icosphere((0.0, 24.0, 35.0), 2.8, 1, UV_PINK_SKIN, scale=(0.7, 1.2, 0.9))
    
    b.finish()
    render_model(mesh_obj, name, ortho_scale=75.0)

if __name__ == '__main__':
    print("Testing cute organic animal builders...")
    build_cute_calf()
    build_cute_piglet()
    print("Done!")

