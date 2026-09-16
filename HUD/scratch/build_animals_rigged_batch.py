import bpy
import bmesh
import os
import sys
import math
import mathutils

# ==============================================================================
# HOMESTEADER ANIMALS BATCH GENERATOR (FULL TAXONOMY: ADULTS & ALL BABIES)
# ==============================================================================

PALETTE_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\textures\palettes\T_Homesteader_Palette.png"
HUD_ANIMALS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\ranching\animals"
HUD_ITEMS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"
UNREAL_ANIMALS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Ranching\Meshes"
UNREAL_ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"
UNREAL_RANCH_ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons\ranching\animals"
RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_animals"

for d in [HUD_ANIMALS_DIR, HUD_ITEMS_DIR, UNREAL_ANIMALS_DIR, UNREAL_ICONS_DIR, UNREAL_RANCH_ICONS_DIR, RENDERS_DIR]:
    os.makedirs(d, exist_ok=True)

def get_uv(col, row):
    return ((col + 0.5) / 16.0, 1.0 - (row + 0.5) / 16.0)

# Colors in Master Palette:
UV_WHITE        = get_uv(5, 8)   # #ffffff Pure white
UV_OFFWHITE     = get_uv(1, 8)   # #f5f5f0 Cream white / fleece
UV_BLACK        = get_uv(4, 15)  # #14161c Rich black
UV_HOOF_DARK    = get_uv(3, 15)  # #3c404b Dark hooves / claws
UV_SLATE_GREY   = get_uv(1, 3)   # #787d84 Muzzle grey / horn tips / barred down
UV_CREAM_HORN   = get_uv(0, 2)   # #cbd5e1 Horns cream / horn buds
UV_PINK_SKIN    = get_uv(1, 7)   # #f472b6 Pink pig / snout / udder / inner ears
UV_CRIMSON_COMB = get_uv(1, 5)   # #e11d48 Crimson wattle / comb
UV_GINGER_FUR   = get_uv(4, 1)   # #b95f37 Highland ginger / Red hen plumage
UV_AUBURN_PIG   = get_uv(4, 0)   # #5c2d0f Duroc auburn brown
UV_CHESTNUT_MID = get_uv(2, 1)   # #8c5f3c Chestnut brown / calf
UV_DARK_BROWN   = get_uv(1, 1)   # #583927 Goat spine / dark markings
UV_TAN_JERSEY   = get_uv(1, 0)   # #b08968 Jersey caramel tan / goat brown
UV_TAN_WOOL     = get_uv(4, 8)   # #e1b996 Tan wool / sheep
UV_GOLDEN_YELL  = get_uv(5, 5)   # #facc15 Chick yellow / beak / chicken legs
UV_ORANGE_BEAK  = get_uv(5, 4)   # #ea580c Chick beak / orange accents

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
    node_bsdf.inputs['Roughness'].default_value = 0.65
    
    node_tex = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(PALETTE_PATH):
        img = bpy.data.images.load(PALETTE_PATH)
        img.colorspace_settings.name = 'sRGB'
        node_tex.image = img
        node_tex.interpolation = 'Closest'
        
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    # 3-Point Sun Lighting matching Homesteader icon standard
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
        uv_coords = []
        u_mid = (u_min + u_max) * 0.5
        v_mid = (v_min + v_max) * 0.5
        rad_u = (u_max - u_min) * 0.4
        rad_v = (v_max - v_min) * 0.4
        for i in range(n):
            angle = i * 2.0 * math.pi / n
            uv_coords.append((u_mid + rad_u * math.cos(angle), v_mid + rad_v * math.sin(angle)))
            
    try:
        f_front = bm.faces.new(verts)
        f_front.smooth = True
        for loop, coord in zip(f_front.loops, uv_coords):
            loop[uv_layer].uv = coord
            
        if double_sided:
            f_back = bm.faces.new(list(reversed(verts)))
            f_back.smooth = True
            for loop, coord in zip(f_back.loops, list(reversed(uv_coords))):
                loop[uv_layer].uv = coord
    except ValueError:
        pass

class AnimalMeshContext:
    def __init__(self, bm, uv_layer):
        self.bm = bm
        self.uv_layer = uv_layer
        self.current_bone = None
        self.weights = {} # bone_name -> set of verts
        
    def set_bone(self, bone_name):
        self.current_bone = bone_name
        if bone_name not in self.weights:
            self.weights[bone_name] = set()
            
    def _track(self, verts):
        if self.current_bone:
            for v in verts:
                self.weights[self.current_bone].add(v)

    def add_box(self, min_co, max_co, uv, double_sided=True):
        x0, y0, z0 = min_co
        x1, y1, z1 = max_co
        v000 = self.bm.verts.new((x0, y0, z0))
        v001 = self.bm.verts.new((x0, y0, z1))
        v010 = self.bm.verts.new((x0, y1, z0))
        v011 = self.bm.verts.new((x0, y1, z1))
        v100 = self.bm.verts.new((x1, y0, z0))
        v101 = self.bm.verts.new((x1, y0, z1))
        v110 = self.bm.verts.new((x1, y1, z0))
        v111 = self.bm.verts.new((x1, y1, z1))
        
        verts_all = [v000, v001, v010, v011, v100, v101, v110, v111]
        self._track(verts_all)

        add_bmesh_face(self.bm, self.uv_layer, [v000, v010, v110, v100], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v001, v101, v111, v011], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v000, v100, v101, v001], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v010, v011, v111, v110], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v000, v001, v011, v010], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v100, v110, v111, v101], uv, double_sided=double_sided)

    def add_sloped_box(self, min_b, max_b, min_t, max_t, z_min, z_max, uv, double_sided=True):
        x0b, y0b = min_b
        x1b, y1b = max_b
        x0t, y0t = min_t
        x1t, y1t = max_t
        
        v000 = self.bm.verts.new((x0b, y0b, z_min))
        v001 = self.bm.verts.new((x0t, y0t, z_max))
        v010 = self.bm.verts.new((x0b, y1b, z_min))
        v011 = self.bm.verts.new((x0t, y1t, z_max))
        v100 = self.bm.verts.new((x1b, y0b, z_min))
        v101 = self.bm.verts.new((x1t, y0t, z_max))
        v110 = self.bm.verts.new((x1b, y1b, z_min))
        v111 = self.bm.verts.new((x1t, y1t, z_max))
        
        self._track([v000, v001, v010, v011, v100, v101, v110, v111])

        add_bmesh_face(self.bm, self.uv_layer, [v000, v010, v110, v100], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v001, v101, v111, v011], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v000, v100, v101, v001], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v010, v011, v111, v110], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v000, v001, v011, v010], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, [v100, v110, v111, v101], uv, double_sided=double_sided)

    def add_cylinder_z(self, z0, z1, r, sides, uv, cx=0.0, cy=0.0, double_sided=True):
        v_bot = []
        v_top = []
        for i in range(sides):
            a = i * 2.0 * math.pi / sides
            v_bot.append(self.bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z0)))
            v_top.append(self.bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z1)))
        self._track(v_bot + v_top)
        for i in range(sides):
            nxt = (i + 1) % sides
            add_bmesh_face(self.bm, self.uv_layer, [v_bot[i], v_bot[nxt], v_top[nxt], v_top[i]], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, list(reversed(v_bot)), uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, v_top, uv, double_sided=double_sided)

    def add_tapered_cylinder_z(self, z0, z1, r_bot, r_top, sides, uv, cx=0.0, cy=0.0, double_sided=True):
        v_bot = []
        v_top = []
        for i in range(sides):
            a = i * 2.0 * math.pi / sides
            v_bot.append(self.bm.verts.new((cx + r_bot * math.cos(a), cy + r_bot * math.sin(a), z0)))
            v_top.append(self.bm.verts.new((cx + r_top * math.cos(a), cy + r_top * math.sin(a), z1)))
        self._track(v_bot + v_top)
        for i in range(sides):
            nxt = (i + 1) % sides
            add_bmesh_face(self.bm, self.uv_layer, [v_bot[i], v_bot[nxt], v_top[nxt], v_top[i]], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, list(reversed(v_bot)), uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, v_top, uv, double_sided=double_sided)

    def add_cylinder_x(self, x0, x1, r, sides, uv, cy=0.0, cz=0.0, double_sided=True):
        v_l = []
        v_r = []
        min_x = min(x0, x1)
        max_x = max(x0, x1)
        for i in range(sides):
            a = i * 2.0 * math.pi / sides
            v_l.append(self.bm.verts.new((min_x, cy + r * math.cos(a), cz + r * math.sin(a))))
            v_r.append(self.bm.verts.new((max_x, cy + r * math.cos(a), cz + r * math.sin(a))))
        self._track(v_l + v_r)
        for i in range(sides):
            nxt = (i + 1) % sides
            add_bmesh_face(self.bm, self.uv_layer, [v_l[i], v_l[nxt], v_r[nxt], v_r[i]], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, list(reversed(v_l)), uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, v_r, uv, double_sided=double_sided)

    def add_cylinder_y(self, y0, y1, r, sides, uv, cx=0.0, cz=0.0, double_sided=True):
        v_f = []
        v_b = []
        min_y = min(y0, y1)
        max_y = max(y0, y1)
        for i in range(sides):
            a = i * 2.0 * math.pi / sides
            v_f.append(self.bm.verts.new((cx + r * math.cos(a), min_y, cz + r * math.sin(a))))
            v_b.append(self.bm.verts.new((cx + r * math.cos(a), max_y, cz + r * math.sin(a))))
        self._track(v_f + v_b)
        for i in range(sides):
            nxt = (i + 1) % sides
            add_bmesh_face(self.bm, self.uv_layer, [v_f[i], v_b[i], v_b[nxt], v_f[nxt]], uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, list(reversed(v_f)), uv, double_sided=double_sided)
        add_bmesh_face(self.bm, self.uv_layer, v_b, uv, double_sided=double_sided)

    def finish_and_skin(self, mesh_obj):
        self.bm.verts.ensure_lookup_table()
        self.bm.verts.index_update()
        bone_indices = {}
        for bone_name, vset in self.weights.items():
            bone_indices[bone_name] = [v.index for v in vset]
        self.bm.to_mesh(mesh_obj.data)
        self.bm.free()
        
        for bone_name, indices in bone_indices.items():
            if indices:
                vg = mesh_obj.vertex_groups.new(name=bone_name)
                vg.add(indices, 1.0, 'REPLACE')

# ==============================================================================
# SKELETON ARMATURE BUILDERS
# ==============================================================================

def create_quadruped_armature(scene, name, leg_span_x=22.0, leg_front_y=-36.0, leg_back_y=38.0, 
                             knee_z=26.0, hip_z=58.0, spine_z=95.0, head_y=-80.0, head_z=120.0):
    arm_data = bpy.data.armatures.new(f"{name}_Armature")
    arm_obj = bpy.data.objects.new(f"{name}_Armature", arm_data)
    scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    
    root = eb.new('root')
    root.head = (0, 0, 0)
    root.tail = (0, 0, 15)
    
    pelvis = eb.new('pelvis')
    pelvis.parent = root
    pelvis.head = (0, leg_back_y * 0.5, hip_z)
    pelvis.tail = (0, 0.0, hip_z + 5)
    
    spine = eb.new('spine_01')
    spine.parent = pelvis
    spine.head = (0, 0.0, hip_z + 5)
    spine.tail = (0, leg_front_y * 0.7, spine_z)
    
    chest = eb.new('chest')
    chest.parent = spine
    chest.head = (0, leg_front_y * 0.7, spine_z)
    chest.tail = (0, leg_front_y * 1.1, spine_z)
    
    neck = eb.new('neck')
    neck.parent = chest
    neck.head = (0, leg_front_y * 1.1, spine_z)
    neck.tail = (0, head_y * 0.8, head_z - 10)
    
    head = eb.new('head')
    head.parent = neck
    head.head = (0, head_y * 0.8, head_z - 10)
    head.tail = (0, head_y * 1.15, head_z)
    
    jaw = eb.new('jaw')
    jaw.parent = head
    jaw.head = (0, head_y * 0.9, head_z - 15)
    jaw.tail = (0, head_y * 1.2, head_z - 20)
    
    # Front Legs
    for side, sign, side_name in [(1, -1, 'fl'), (2, 1, 'fr')]:
        clav = eb.new(f'clavicle_{side_name}')
        clav.parent = chest
        clav.head = (0, leg_front_y, spine_z)
        clav.tail = (sign * leg_span_x, leg_front_y, hip_z)
        
        up = eb.new(f'leg_{side_name}_upper')
        up.parent = clav
        up.head = (sign * leg_span_x, leg_front_y, hip_z)
        up.tail = (sign * leg_span_x, leg_front_y, knee_z)
        
        low = eb.new(f'leg_{side_name}_lower')
        low.parent = up
        low.head = (sign * leg_span_x, leg_front_y, knee_z)
        low.tail = (sign * leg_span_x, leg_front_y, max(4.0, knee_z * 0.3))
        
        foot = eb.new(f'foot_{side_name}')
        foot.parent = low
        foot.head = (sign * leg_span_x, leg_front_y, max(4.0, knee_z * 0.3))
        foot.tail = (sign * leg_span_x, leg_front_y - 4, 0.0)
        
    # Back Legs
    for side, sign, side_name in [(1, -1, 'bl'), (2, 1, 'br')]:
        up = eb.new(f'leg_{side_name}_upper')
        up.parent = pelvis
        up.head = (sign * leg_span_x, leg_back_y, hip_z)
        up.tail = (sign * leg_span_x, leg_back_y, knee_z)
        
        low = eb.new(f'leg_{side_name}_lower')
        low.parent = up
        low.head = (sign * leg_span_x, leg_back_y, knee_z)
        low.tail = (sign * leg_span_x, leg_back_y, max(4.0, knee_z * 0.3))
        
        foot = eb.new(f'foot_{side_name}')
        foot.parent = low
        foot.head = (sign * leg_span_x, leg_back_y, max(4.0, knee_z * 0.3))
        foot.tail = (sign * leg_span_x, leg_back_y - 4, 0.0)
        
    # Tail
    t1 = eb.new('tail_01')
    t1.parent = pelvis
    t1.head = (0, leg_back_y + 8, hip_z + 6)
    t1.tail = (0, leg_back_y + 14, hip_z - 8)
    
    t2 = eb.new('tail_02')
    t2.parent = t1
    t2.head = (0, leg_back_y + 14, hip_z - 8)
    t2.tail = (0, leg_back_y + 18, knee_z)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def create_avian_armature(scene, name, hip_z=22.0, knee_z=12.0, head_y=-18.0, head_z=44.0):
    arm_data = bpy.data.armatures.new(f"{name}_Armature")
    arm_obj = bpy.data.objects.new(f"{name}_Armature", arm_data)
    scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    
    root = eb.new('root')
    root.head = (0, 0, 0)
    root.tail = (0, 0, 6)
    
    pelvis = eb.new('pelvis')
    pelvis.parent = root
    pelvis.head = (0, 0, hip_z)
    pelvis.tail = (0, -4, hip_z + 4)
    
    spine = eb.new('spine')
    spine.parent = pelvis
    spine.head = (0, -4, hip_z + 4)
    spine.tail = (0, -10, hip_z + 8)
    
    neck = eb.new('neck')
    neck.parent = spine
    neck.head = (0, -10, hip_z + 8)
    neck.tail = (0, head_y * 0.6, head_z - 6)
    
    head = eb.new('head')
    head.parent = neck
    head.head = (0, head_y * 0.6, head_z - 6)
    head.tail = (0, head_y, head_z)
    
    beak = eb.new('beak')
    beak.parent = head
    beak.head = (0, head_y, head_z - 2)
    beak.tail = (0, head_y - 6, head_z - 4)
    
    # Wings
    for sign, side in [(-1, 'l'), (1, 'r')]:
        w1 = eb.new(f'wing_{side}')
        w1.parent = spine
        w1.head = (sign * 8.0, -4.0, hip_z + 4)
        w1.tail = (sign * 12.0, 4.0, hip_z + 2)
        
        w2 = eb.new(f'wing_tip_{side}')
        w2.parent = w1
        w2.head = (sign * 12.0, 4.0, hip_z + 2)
        w2.tail = (sign * 10.0, 10.0, hip_z)
        
    # Legs
    for sign, side in [(-1, 'l'), (1, 'r')]:
        up = eb.new(f'leg_{side}_upper')
        up.parent = pelvis
        up.head = (sign * 4.5, -2.0, hip_z)
        up.tail = (sign * 4.5, 0.0, knee_z)
        
        low = eb.new(f'leg_{side}_lower')
        low.parent = up
        low.head = (sign * 4.5, 0.0, knee_z)
        low.tail = (sign * 4.5, -1.0, max(2.0, knee_z * 0.3))
        
        foot = eb.new(f'foot_{side}')
        foot.parent = low
        foot.head = (sign * 4.5, -1.0, max(2.0, knee_z * 0.3))
        foot.tail = (sign * 4.5, -5.0, 0.0)
        
    tail = eb.new('tail')
    tail.parent = pelvis
    tail.head = (0, 8.0, hip_z + 4)
    tail.tail = (0, 16.0, hip_z + 12)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=180.0, aliases=[], icon_name=None, icon_aliases=[]):
    scene = bpy.context.scene
    mesh_obj.data.materials.append(mat)
    mesh_obj.data.update()
    
    # Armature Modifier
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True
    
    # Render Preview
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
    
    render_path = os.path.join(RENDERS_DIR, f"{name}_render.png")
    scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
        
    # Select both for FBX export
    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    
    all_export_names = [name] + aliases
    for exp_name in all_export_names:
        for out_dir in [HUD_ANIMALS_DIR, UNREAL_ANIMALS_DIR]:
            fbx_path = os.path.join(out_dir, f"{exp_name}.fbx")
            bpy.ops.export_scene.fbx(
                filepath=fbx_path,
                use_selection=True,
                mesh_smooth_type='SMOOTH_GROUP',
                use_tspace=True,
                use_triangles=True,
                use_armature_deform_only=True,
                add_leaf_bones=False,
                axis_forward='Y',
                axis_up='Z'
            )
            obj_path = os.path.join(out_dir, f"{exp_name}.obj")
            bpy.ops.wm.obj_export(
                filepath=obj_path,
                export_selected_objects=True,
                export_materials=True,
                export_uv=True,
                export_normals=True,
                export_smooth_groups=True,
                forward_axis='Y',
                up_axis='Z'
            )
    print(f"  [EXPORT] {name} (+ {len(aliases)} aliases) exported as FBX/OBJ.")

# ==============================================================================
# MODEL BUILDERS
# ==============================================================================

# --- 1. CATTLE ---
def build_cow(breed="Holstein"):
    name = f"SKM_Animal_Cow_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    uv_main = UV_WHITE if breed in ["Holstein"] else (UV_TAN_JERSEY if breed == "Jersey" else UV_GINGER_FUR)
    uv_spot = UV_BLACK if breed == "Holstein" else uv_main
    uv_muzzle = UV_PINK_SKIN if breed == "Holstein" else (UV_SLATE_GREY if breed == "Jersey" else UV_DARK_BROWN)
    uv_horn = UV_CREAM_HORN
    
    # Body
    ctx.set_bone("pelvis")
    ctx.add_sloped_box((-32.0, -5.0), (32.0, 52.0), (-28.0, -5.0), (28.0, 48.0), 58.0, 126.0, uv_main)
    if breed == "Holstein":
        ctx.add_box((-32.5, 20.0, 85.0), (32.5, 50.0, 126.5), uv_spot)
    elif breed == "Highland":
        ctx.add_box((-35.0, -5.0, 48.0), (35.0, 50.0, 65.0), UV_GINGER_FUR)
        
    ctx.set_bone("chest")
    ctx.add_sloped_box((-34.0, -48.0), (34.0, -2.0), (-30.0, -45.0), (30.0, -2.0), 55.0, 125.0, uv_main)
    if breed == "Holstein":
        ctx.add_box((-34.5, -28.0, 75.0), (34.5, 5.0, 125.5), uv_spot)
    elif breed == "Highland":
        ctx.add_box((-35.0, -45.0, 48.0), (35.0, 0.0, 65.0), UV_GINGER_FUR)
        
    # Udder
    ctx.set_bone("pelvis")
    ctx.add_box((-12.0, 10.0, 48.0), (12.0, 28.0, 60.0), UV_PINK_SKIN)
    for tx in [-6.0, 6.0]:
        for ty in [14.0, 24.0]:
            ctx.add_cylinder_z(42.0, 48.0, 1.5, 4, UV_PINK_SKIN, cx=tx, cy=ty)
            
    # Neck
    ctx.set_bone("neck")
    ctx.add_sloped_box((-18.0, -68.0), (18.0, -42.0), (-14.0, -75.0), (14.0, -50.0), 85.0, 136.0, uv_main)
    
    # Head & Features
    ctx.set_bone("head")
    ctx.add_box((-16.0, -88.0, 108.0), (16.0, -68.0, 138.0), uv_main)
    if breed == "Holstein":
        ctx.add_box((0.0, -87.0, 115.0), (16.2, -69.0, 138.2), uv_spot)
    elif breed == "Highland":
        ctx.add_box((-16.5, -92.0, 110.0), (16.5, -80.0, 140.0), UV_GINGER_FUR)
        
    # Muzzle
    ctx.add_box((-13.0, -100.0, 96.0), (13.0, -86.0, 118.0), uv_muzzle)
    if breed == "Jersey":
        ctx.add_box((-13.5, -88.0, 95.0), (13.5, -84.0, 120.0), UV_OFFWHITE)
        
    # Ears
    for ex in [-16.0, 16.0]:
        sx = 1.0 if ex > 0 else -1.0
        ctx.add_box((ex, -78.0, 122.0), (ex + sx * 14.0, -70.0, 132.0), uv_main)
        ctx.add_box((ex + sx * 2.0, -76.0, 124.0), (ex + sx * 12.0, -72.0, 130.0), UV_PINK_SKIN)
        
    # Horns
    if breed == "Highland":
        ctx.add_cylinder_x(-55.0, -14.0, 3.2, 6, uv_horn, cy=-72.0, cz=138.0)
        ctx.add_tapered_cylinder_z(138.0, 158.0, 3.2, 0.8, 6, uv_horn, cx=-53.0, cy=-72.0)
        ctx.add_cylinder_x(14.0, 55.0, 3.2, 6, uv_horn, cy=-72.0, cz=138.0)
        ctx.add_tapered_cylinder_z(138.0, 158.0, 3.2, 0.8, 6, uv_horn, cx=53.0, cy=-72.0)
    else:
        for hx in [-14.0, 14.0]:
            ctx.add_tapered_cylinder_z(136.0, 148.0, 3.0, 0.8, 6, uv_horn, cx=hx, cy=-72.0)
            
    # 4 Legs
    legs = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -22.0, -36.0),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  22.0, -36.0),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl", -20.0,  38.0),
        ("leg_br_upper", "leg_br_lower", "foot_br",  20.0,  38.0),
    ]
    for up_b, low_b, foot_b, lx, ly in legs:
        ctx.set_bone(up_b)
        ctx.add_box((lx - 7.5, ly - 7.5, 26.0), (lx + 7.5, ly + 7.5, 58.0), uv_main)
        ctx.set_bone(low_b)
        ctx.add_box((lx - 5.5, ly - 5.5, 8.0), (lx + 5.5, ly + 5.5, 26.0), uv_main)
        ctx.set_bone(foot_b)
        ctx.add_box((lx - 6.5, ly - 7.5, 0.0), (lx + 6.5, ly + 6.5, 8.0), UV_HOOF_DARK)
        
    # Tail
    ctx.set_bone("tail_01")
    ctx.add_box((-2.0, 52.0, 65.0), (2.0, 56.0, 120.0), uv_main)
    ctx.set_bone("tail_02")
    ctx.add_box((-3.5, 51.0, 45.0), (3.5, 57.0, 65.0), uv_spot)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_quadruped_armature(scene, name, leg_span_x=22.0, leg_front_y=-36.0, leg_back_y=38.0, 
                                        knee_z=26.0, hip_z=58.0, spine_z=95.0, head_y=-80.0, head_z=120.0)
    aliases = ["SM_Animal_Cow_Adult"] if breed == "Holstein" else []
    icon_name = f"livestock_cow_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=220.0, aliases=aliases, icon_name=icon_name)

def build_calf(breed="Chestnut"):
    name = f"SKM_Animal_Cow_Calf_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    # Breed color mappings
    if breed == "Holstein":
        uv_main = UV_WHITE
        uv_spot = UV_BLACK
        uv_muzzle = UV_PINK_SKIN
    elif breed == "Jersey":
        uv_main = UV_TAN_JERSEY
        uv_spot = UV_TAN_JERSEY
        uv_muzzle = UV_SLATE_GREY
    elif breed == "Highland":
        uv_main = UV_GINGER_FUR
        uv_spot = UV_GINGER_FUR
        uv_muzzle = UV_DARK_BROWN
    else: # Chestnut
        uv_main = UV_CHESTNUT_MID
        uv_spot = UV_CHESTNUT_MID
        uv_muzzle = UV_PINK_SKIN
        
    # Torso (Chubby baby proportions)
    ctx.set_bone("pelvis")
    ctx.add_sloped_box((-18.0, 0.0), (18.0, 30.0), (-16.0, 0.0), (16.0, 28.0), 32.0, 72.0, uv_main)
    if breed == "Holstein":
        ctx.add_box((-18.5, 12.0, 48.0), (18.5, 28.0, 72.5), uv_spot)
    elif breed == "Highland":
        ctx.add_box((-19.0, 0.0, 28.0), (19.0, 28.0, 40.0), UV_GINGER_FUR) # Fluffy fringe
        
    ctx.set_bone("chest")
    ctx.add_sloped_box((-18.0, -30.0), (18.0, 0.0), (-16.0, -28.0), (16.0, 0.0), 32.0, 72.0, uv_main)
    if breed == "Holstein":
        ctx.add_box((-18.5, -20.0, 45.0), (18.5, -2.0, 72.5), uv_spot)
    elif breed == "Highland":
        ctx.add_box((-19.0, -28.0, 28.0), (19.0, 0.0, 40.0), UV_GINGER_FUR)
        
    # Neck & Head
    ctx.set_bone("neck")
    ctx.add_sloped_box((-10.0, -46.0), (10.0, -25.0), (-8.5, -50.0), (8.5, -32.0), 48.0, 82.0, uv_main)
    ctx.set_bone("head")
    ctx.add_box((-10.5, -58.0, 62.0), (10.5, -42.0, 82.0), uv_main)
    
    # Forehead details
    if breed == "Chestnut":
        # White diamond blaze on forehead
        ctx.add_box((-3.5, -58.2, 70.0), (3.5, -45.0, 80.0), UV_WHITE)
    elif breed == "Holstein":
        # Black eye patch
        ctx.add_box((0.0, -58.2, 65.0), (10.6, -42.0, 82.2), UV_BLACK)
    elif breed == "Highland":
        # Cute shaggy forelock tuft over forehead
        ctx.add_box((-11.0, -60.0, 72.0), (11.0, -45.0, 84.0), UV_GINGER_FUR)
        
    # Muzzle
    ctx.add_box((-8.0, -68.0, 55.0), (8.0, -56.0, 68.0), uv_muzzle)
    if breed == "Jersey":
        # Cream muzzle ring
        ctx.add_box((-8.5, -58.0, 54.0), (8.5, -55.0, 69.0), UV_OFFWHITE)
        
    # Ears
    for ex in [-10.0, 10.0]:
        sx = 1.0 if ex > 0 else -1.0
        ctx.add_box((ex, -48.0, 72.0), (ex + sx * 9.0, -42.0, 80.0), uv_main)
        ctx.add_box((ex + sx * 1.5, -47.0, 73.0), (ex + sx * 8.0, -43.0, 79.0), UV_PINK_SKIN)
        
    # 4 Legs
    legs = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -12.0, -20.0),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  12.0, -20.0),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl", -12.0,  22.0),
        ("leg_br_upper", "leg_br_lower", "foot_br",  12.0,  22.0),
    ]
    for up_b, low_b, foot_b, lx, ly in legs:
        ctx.set_bone(up_b)
        ctx.add_box((lx - 4.5, ly - 4.5, 16.0), (lx + 4.5, ly + 4.5, 34.0), uv_main)
        ctx.set_bone(low_b)
        ctx.add_box((lx - 3.5, ly - 3.5, 5.0), (lx + 3.5, ly + 3.5, 16.0), uv_main)
        ctx.set_bone(foot_b)
        ctx.add_box((lx - 4.0, ly - 4.5, 0.0), (lx + 4.0, ly + 4.5, 5.0), UV_HOOF_DARK)
        
    ctx.set_bone("tail_01")
    ctx.add_box((-1.8, 28.0, 42.0), (1.8, 31.0, 68.0), uv_main)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_quadruped_armature(scene, name, leg_span_x=12.0, leg_front_y=-20.0, leg_back_y=22.0, 
                                        knee_z=16.0, hip_z=34.0, spine_z=55.0, head_y=-50.0, head_z=75.0)
    
    # Aliases
    aliases = []
    icon_aliases = []
    if breed == "Holstein":
        aliases = ["SKM_Animal_Cow_Calf_Spotted"]
        icon_aliases = ["baby_calf_spotted"]
    elif breed == "Chestnut":
        aliases = ["SKM_Animal_Cow_Calf"]
        icon_aliases = ["baby_calf"]
        
    icon_name = f"baby_calf_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=130.0, aliases=aliases, 
                                icon_name=icon_name, icon_aliases=icon_aliases)

# --- 2. PIGS ---
def build_pig(breed="Pink"):
    name = f"SKM_Animal_Pig_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    uv_body = UV_PINK_SKIN if breed == "Pink" else (UV_BLACK if breed == "Hampshire" else UV_AUBURN_PIG)
    
    # Plump Barrel Body
    ctx.set_bone("pelvis")
    ctx.add_cylinder_y(-5.0, 36.0, 24.0, 8, uv_body, cx=0.0, cz=45.0)
    
    ctx.set_bone("chest")
    ctx.add_cylinder_y(-40.0, -5.0, 25.0, 8, UV_WHITE if breed == "Hampshire" else uv_body, cx=0.0, cz=45.0)
    
    # Head & Snout
    ctx.set_bone("head")
    ctx.add_sloped_box((-16.0, -62.0), (16.0, -38.0), (-14.0, -60.0), (14.0, -40.0), 32.0, 58.0, uv_body)
    ctx.add_cylinder_y(-70.0, -62.0, 7.5, 8, UV_PINK_SKIN, cx=0.0, cz=42.0)
    for nx in [-3.0, 3.0]:
        ctx.add_box((nx - 1.2, -70.2, 41.0), (nx + 1.2, -69.8, 43.5), UV_BLACK)
        
    # Ears
    for ex in [-15.0, 15.0]:
        sx = 1.0 if ex > 0 else -1.0
        if breed == "Duroc":
            # Drooping lop ears
            ctx.add_box((ex, -58.0, 48.0), (ex + sx * 12.0, -48.0, 56.0), uv_body)
        else:
            # Perky upright triangular ears
            ctx.add_box((ex, -52.0, 55.0), (ex + sx * 11.0, -44.0, 68.0), uv_body)
            
    # 4 Legs
    legs = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -16.0, -28.0, UV_WHITE if breed == "Hampshire" else uv_body),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  16.0, -28.0, UV_WHITE if breed == "Hampshire" else uv_body),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl", -15.0,  24.0, uv_body),
        ("leg_br_upper", "leg_br_lower", "foot_br",  15.0,  24.0, uv_body),
    ]
    for up_b, low_b, foot_b, lx, ly, l_uv in legs:
        ctx.set_bone(up_b)
        ctx.add_box((lx - 5.5, ly - 5.5, 12.0), (lx + 5.5, ly + 5.5, 26.0), l_uv)
        ctx.set_bone(low_b)
        ctx.add_box((lx - 4.5, ly - 4.5, 4.0), (lx + 4.5, ly + 4.5, 12.0), l_uv)
        ctx.set_bone(foot_b)
        ctx.add_box((lx - 5.0, ly - 5.5, 0.0), (lx + 5.0, ly + 5.0, 4.0), UV_HOOF_DARK)
        
    # Corkscrew Tail
    ctx.set_bone("tail_01")
    ctx.add_box((-1.5, 36.0, 48.0), (1.5, 42.0, 54.0), uv_body)
    ctx.set_bone("tail_02")
    ctx.add_box((-1.5, 40.0, 54.0), (1.5, 44.0, 60.0), uv_body)
    ctx.add_box((-1.5, 36.0, 58.0), (1.5, 42.0, 62.0), uv_body)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_quadruped_armature(scene, name, leg_span_x=16.0, leg_front_y=-28.0, leg_back_y=24.0, 
                                        knee_z=12.0, hip_z=26.0, spine_z=45.0, head_y=-55.0, head_z=50.0)
    aliases = ["SM_Animal_Pig_Adult"] if breed == "Pink" else []
    icon_name = f"livestock_pig_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=160.0, aliases=aliases, icon_name=icon_name)

def build_piglet(breed="Pink"):
    name = f"SKM_Animal_Pig_Piglet_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    if breed == "Pink":
        uv_body = UV_PINK_SKIN
    elif breed == "Hampshire":
        uv_body = UV_BLACK
    elif breed == "Duroc":
        uv_body = UV_AUBURN_PIG
    else: # Spotted
        uv_body = UV_PINK_SKIN
        
    # Torso (Round cute piglet)
    ctx.set_bone("pelvis")
    ctx.add_cylinder_y(-2.0, 18.0, 12.0, 8, uv_body, cx=0.0, cz=24.0)
    if breed == "Spotted":
        ctx.add_box((-10.0, 4.0, 22.0), (10.0, 16.0, 36.5), UV_BLACK) # Black rump spot
        
    ctx.set_bone("chest")
    ctx.add_cylinder_y(-20.0, -2.0, 12.5, 8, UV_WHITE if breed == "Hampshire" else uv_body, cx=0.0, cz=24.0)
    if breed == "Spotted":
        ctx.add_box((-10.5, -16.0, 20.0), (-2.0, -6.0, 34.0), UV_BLACK) # Black flank spot
        
    # Head & Snout
    ctx.set_bone("head")
    ctx.add_box((-9.0, -32.0, 16.0), (9.0, -18.0, 32.0), uv_body)
    ctx.add_cylinder_y(-37.0, -32.0, 4.5, 6, UV_PINK_SKIN, cx=0.0, cz=22.0)
    for nx in [-1.8, 1.8]:
        ctx.add_box((nx - 0.7, -37.2, 21.2), (nx + 0.7, -36.8, 22.8), UV_BLACK)
        
    # Ears
    for ex in [-9.0, 9.0]:
        sx = 1.0 if ex > 0 else -1.0
        if breed == "Duroc":
            # Folded down ear
            ctx.add_box((ex, -30.0, 24.0), (ex + sx * 6.0, -23.0, 30.0), uv_body)
        else:
            # Perky ear
            ctx.add_box((ex, -28.0, 28.0), (ex + sx * 6.0, -22.0, 38.0), uv_body)
            
    # 4 Short Legs
    legs = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -8.0, -14.0, UV_WHITE if breed == "Hampshire" else uv_body),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  8.0, -14.0, UV_WHITE if breed == "Hampshire" else uv_body),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl", -7.5,  12.0, uv_body),
        ("leg_br_upper", "leg_br_lower", "foot_br",  7.5,  12.0, uv_body),
    ]
    for up_b, low_b, foot_b, lx, ly, l_uv in legs:
        ctx.set_bone(up_b)
        ctx.add_box((lx - 2.8, ly - 2.8, 6.0), (lx + 2.8, ly + 2.8, 14.0), l_uv)
        ctx.set_bone(low_b)
        ctx.add_box((lx - 2.2, ly - 2.2, 2.0), (lx + 2.2, ly + 2.2, 6.0), l_uv)
        ctx.set_bone(foot_b)
        ctx.add_box((lx - 2.5, ly - 2.8, 0.0), (lx + 2.5, ly + 2.5, 2.0), UV_HOOF_DARK)
        
    # Tiny Corkscrew Tail
    ctx.set_bone("tail_01")
    ctx.add_box((-1.0, 18.0, 24.0), (1.0, 24.0, 28.0), uv_body)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_quadruped_armature(scene, name, leg_span_x=8.0, leg_front_y=-14.0, leg_back_y=12.0, 
                                        knee_z=6.0, hip_z=14.0, spine_z=24.0, head_y=-26.0, head_z=28.0)
    
    aliases = ["SKM_Animal_Pig_Piglet"] if breed == "Pink" else []
    icon_aliases = ["baby_piglet"] if breed == "Pink" else []
    icon_name = f"baby_piglet_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=90.0, aliases=aliases, 
                                icon_name=icon_name, icon_aliases=icon_aliases)

# --- 3. SHEEP ---
def build_sheep(breed="Suffolk"):
    name = f"SKM_Animal_Sheep_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    uv_fleece = UV_OFFWHITE if breed in ["Suffolk", "White"] else UV_TAN_WOOL
    uv_face = UV_BLACK if breed == "Suffolk" else (UV_OFFWHITE if breed == "White" else UV_TAN_JERSEY)
    
    # Voluminous Cloud Fleece
    ctx.set_bone("pelvis")
    ctx.add_sloped_box((-28.0, -5.0), (28.0, 44.0), (-25.0, -5.0), (25.0, 40.0), 45.0, 102.0, uv_fleece)
    ctx.set_bone("chest")
    ctx.add_sloped_box((-29.0, -42.0), (29.0, -2.0), (-26.0, -40.0), (26.0, -2.0), 45.0, 104.0, uv_fleece)
    
    # Wool cap on head
    ctx.set_bone("head")
    ctx.add_box((-11.0, -62.0, 88.0), (11.0, -48.0, 104.0), uv_fleece)
    ctx.add_box((-9.5, -74.0, 72.0), (9.5, -50.0, 92.0), uv_face)
    ctx.add_box((-7.5, -84.0, 68.0), (7.5, -72.0, 84.0), uv_face) # Snout
    
    # Drooping Ears
    for ex in [-10.0, 10.0]:
        sx = 1.0 if ex > 0 else -1.0
        ctx.add_box((ex, -64.0, 75.0), (ex + sx * 12.0, -56.0, 84.0), uv_face)
        
    # Slender 4 Legs
    legs = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -18.0, -28.0),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  18.0, -28.0),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl", -16.0,  30.0),
        ("leg_br_upper", "leg_br_lower", "foot_br",  16.0,  30.0),
    ]
    for up_b, low_b, foot_b, lx, ly in legs:
        ctx.set_bone(up_b)
        ctx.add_box((lx - 5.0, ly - 5.0, 22.0), (lx + 5.0, ly + 5.0, 48.0), uv_face)
        ctx.set_bone(low_b)
        ctx.add_box((lx - 3.8, ly - 3.8, 6.0), (lx + 3.8, ly + 3.8, 22.0), uv_face)
        ctx.set_bone(foot_b)
        ctx.add_box((lx - 4.5, ly - 5.0, 0.0), (lx + 4.5, ly + 4.5, 6.0), UV_HOOF_DARK)
        
    # Fluffy Tail
    ctx.set_bone("tail_01")
    ctx.add_box((-3.0, 42.0, 65.0), (3.0, 48.0, 85.0), uv_fleece)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_quadruped_armature(scene, name, leg_span_x=18.0, leg_front_y=-28.0, leg_back_y=30.0, 
                                        knee_z=22.0, hip_z=48.0, spine_z=80.0, head_y=-65.0, head_z=90.0)
    aliases = ["SM_Animal_Sheep_Adult"] if breed == "Suffolk" else []
    icon_name = f"livestock_sheep_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=170.0, aliases=aliases, icon_name=icon_name)

def build_lamb(breed="Suffolk"):
    name = f"SKM_Animal_Sheep_Lamb_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    if breed == "Suffolk":
        uv_fleece = UV_OFFWHITE
        uv_face = UV_BLACK
        uv_legs = UV_BLACK
    elif breed == "White":
        uv_fleece = UV_OFFWHITE
        uv_face = UV_OFFWHITE
        uv_legs = UV_OFFWHITE
    elif breed == "Tan":
        uv_fleece = UV_TAN_WOOL
        uv_face = UV_TAN_JERSEY
        uv_legs = UV_TAN_JERSEY
    else: # Spotted
        uv_fleece = UV_OFFWHITE
        uv_face = UV_BLACK
        uv_legs = UV_BLACK
        
    # Torso
    ctx.set_bone("pelvis")
    ctx.add_box((-15.0, -2.0, 26.0), (15.0, 24.0, 58.0), uv_fleece)
    if breed == "Spotted":
        ctx.add_box((-15.5, 6.0, 38.0), (15.5, 20.0, 58.5), UV_SLATE_GREY)
        
    ctx.set_bone("chest")
    ctx.add_box((-16.0, -24.0, 26.0), (16.0, 0.0, 60.0), uv_fleece)
    
    # Head
    ctx.set_bone("head")
    ctx.add_box((-7.0, -36.0, 52.0), (7.0, -24.0, 66.0), uv_fleece) # Head fleece cap
    ctx.add_box((-6.0, -44.0, 42.0), (6.0, -30.0, 56.0), uv_face)   # Snout & face
    # Drooping lamb ears
    for ex in [-6.0, 6.0]:
        sx = 1.0 if ex > 0 else -1.0
        ctx.add_box((ex, -34.0, 46.0), (ex + sx * 6.0, -28.0, 52.0), uv_face)
        
    # 4 Legs
    legs = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -10.0, -16.0),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  10.0, -16.0),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl",  -9.0,  16.0),
        ("leg_br_upper", "leg_br_lower", "foot_br",   9.0,  16.0),
    ]
    for up_b, low_b, foot_b, lx, ly in legs:
        ctx.set_bone(up_b)
        ctx.add_box((lx - 3.2, ly - 3.2, 12.0), (lx + 3.2, ly + 3.2, 28.0), uv_legs)
        ctx.set_bone(low_b)
        ctx.add_box((lx - 2.5, ly - 2.5, 4.0), (lx + 2.5, ly + 2.5, 12.0), uv_legs)
        ctx.set_bone(foot_b)
        ctx.add_box((lx - 2.8, ly - 3.2, 0.0), (lx + 2.8, ly + 2.8, 4.0), UV_HOOF_DARK)
        
    ctx.set_bone("tail_01")
    ctx.add_box((-2.0, 24.0, 42.0), (2.0, 28.0, 54.0), uv_fleece)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_quadruped_armature(scene, name, leg_span_x=10.0, leg_front_y=-16.0, leg_back_y=16.0, 
                                        knee_z=12.0, hip_z=28.0, spine_z=45.0, head_y=-35.0, head_z=55.0)
    
    aliases = ["SKM_Animal_Sheep_Lamb"] if breed == "Suffolk" else []
    icon_aliases = ["baby_lamb"] if breed == "Suffolk" else []
    icon_name = f"baby_lamb_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=100.0, aliases=aliases, 
                                icon_name=icon_name, icon_aliases=icon_aliases)

# --- 4. GOATS ---
def build_goat(breed="Brown"):
    name = f"SKM_Animal_Goat_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    uv_main = UV_TAN_JERSEY if breed == "Brown" else (UV_OFFWHITE if breed == "White" else UV_BLACK)
    
    # Slender Torso
    ctx.set_bone("pelvis")
    ctx.add_sloped_box((-18.0, -2.0), (18.0, 36.0), (-15.0, -2.0), (15.0, 32.0), 50.0, 95.0, uv_main)
    if breed == "BlackWhite":
        ctx.add_box((-18.5, 10.0, 65.0), (18.5, 34.0, 95.5), UV_WHITE)
    elif breed == "Brown":
        ctx.add_box((-3.0, -2.0, 94.0), (3.0, 36.0, 95.5), UV_DARK_BROWN) # Dark dorsal stripe
        
    ctx.set_bone("chest")
    ctx.add_sloped_box((-20.0, -36.0), (20.0, 0.0), (-16.0, -34.0), (16.0, 0.0), 50.0, 98.0, uv_main)
    if breed == "Brown":
        ctx.add_box((-16.0, -36.0, 50.0), (16.0, 0.0, 60.0), UV_WHITE) # White belly
        
    # High Slender Neck
    ctx.set_bone("neck")
    ctx.add_sloped_box((-11.0, -48.0), (11.0, -30.0), (-8.5, -55.0), (8.5, -38.0), 75.0, 118.0, uv_main)
    
    # Head & Goatee Beard
    ctx.set_bone("head")
    ctx.add_box((-10.0, -68.0, 95.0), (10.0, -48.0, 118.0), uv_main)
    ctx.add_box((-7.5, -82.0, 88.0), (7.5, -66.0, 106.0), uv_main) # Muzzle
    ctx.add_box((-3.0, -78.0, 72.0), (3.0, -68.0, 88.0), UV_OFFWHITE) # Beard
    if breed == "Brown":
        # White facial stripes
        ctx.add_box((-10.2, -72.0, 96.0), (-8.0, -56.0, 114.0), UV_WHITE)
        ctx.add_box((  8.0, -72.0, 96.0), ( 10.2, -56.0, 114.0), UV_WHITE)
        
    # Backward curved horns
    for hx in [-7.0, 7.0]:
        ctx.add_cylinder_z(116.0, 138.0, 2.2, 5, UV_CREAM_HORN, cx=hx, cy=-52.0)
        ctx.add_cylinder_y(-58.0, -48.0, 1.8, 5, UV_CREAM_HORN, cx=hx, cz=136.0)
        
    # Ears
    for ex in [-10.0, 10.0]:
        sx = 1.0 if ex > 0 else -1.0
        ctx.add_box((ex, -58.0, 104.0), (ex + sx * 11.0, -50.0, 112.0), uv_main)
        
    # 4 Legs with Stockings
    legs = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -14.0, -26.0),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  14.0, -26.0),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl", -13.0,  26.0),
        ("leg_br_upper", "leg_br_lower", "foot_br",  13.0,  26.0),
    ]
    for up_b, low_b, foot_b, lx, ly in legs:
        ctx.set_bone(up_b)
        ctx.add_box((lx - 4.5, ly - 4.5, 24.0), (lx + 4.5, ly + 4.5, 52.0), uv_main)
        ctx.set_bone(low_b)
        ctx.add_box((lx - 3.2, ly - 3.2, 6.0), (lx + 3.2, ly + 3.2, 24.0), UV_BLACK if breed == "Brown" else uv_main)
        ctx.set_bone(foot_b)
        ctx.add_box((lx - 4.0, ly - 4.5, 0.0), (lx + 4.0, ly + 4.0, 6.0), UV_HOOF_DARK)
        
    # Upright Alert Tail
    ctx.set_bone("tail_01")
    ctx.add_box((-2.5, 34.0, 85.0), (2.5, 40.0, 105.0), uv_main)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_quadruped_armature(scene, name, leg_span_x=14.0, leg_front_y=-26.0, leg_back_y=26.0, 
                                        knee_z=24.0, hip_z=52.0, spine_z=85.0, head_y=-60.0, head_z=105.0)
    aliases = ["SM_Animal_Goat_Adult"] if breed == "Brown" else []
    icon_name = f"livestock_goat_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=160.0, aliases=aliases, icon_name=icon_name)

def build_kid(breed="Brown"):
    name = f"SKM_Animal_Goat_Kid_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    if breed == "Brown":
        uv_main = UV_TAN_JERSEY
        uv_accent = UV_WHITE
        uv_stocking = UV_BLACK
    elif breed == "White":
        uv_main = UV_OFFWHITE
        uv_accent = UV_OFFWHITE
        uv_stocking = UV_OFFWHITE
    else: # BlackWhite
        uv_main = UV_BLACK
        uv_accent = UV_WHITE
        uv_stocking = UV_WHITE
        
    ctx.set_bone("pelvis")
    ctx.add_box((-10.0, 0.0, 26.0), (10.0, 20.0, 52.0), uv_main)
    if breed == "BlackWhite":
        ctx.add_box((-10.5, 4.0, 36.0), (10.5, 18.0, 52.5), UV_WHITE)
        
    ctx.set_bone("chest")
    ctx.add_box((-11.0, -18.0, 26.0), (11.0, 2.0, 54.0), uv_main)
    if breed == "Brown":
        ctx.add_box((-9.0, -18.0, 26.0), (9.0, 2.0, 32.0), UV_WHITE) # White belly
        
    ctx.set_bone("head")
    ctx.add_box((-6.5, -30.0, 48.0), (6.5, -16.0, 64.0), uv_main)
    ctx.add_box((-5.0, -38.0, 44.0), (5.0, -28.0, 55.0), uv_accent) # Muzzle
    if breed == "Brown":
        # White facial stripes
        ctx.add_box((-6.7, -34.0, 50.0), (-5.0, -22.0, 62.0), UV_WHITE)
        ctx.add_box(( 5.0, -34.0, 50.0), ( 6.7, -22.0, 62.0), UV_WHITE)
        
    # Tiny cute horn buds
    ctx.add_box((-4.5, -22.0, 64.0), (-2.5, -18.0, 68.0), UV_CREAM_HORN)
    ctx.add_box(( 2.5, -22.0, 64.0), ( 4.5, -18.0, 68.0), UV_CREAM_HORN)
    
    # Perky ears
    for ex in [-6.5, 6.5]:
        sx = 1.0 if ex > 0 else -1.0
        ctx.add_box((ex, -26.0, 54.0), (ex + sx * 6.0, -20.0, 60.0), uv_main)
        
    legs = [
        ("leg_fl_upper", "leg_fl_lower", "foot_fl", -7.5, -12.0),
        ("leg_fr_upper", "leg_fr_lower", "foot_fr",  7.5, -12.0),
        ("leg_bl_upper", "leg_bl_lower", "foot_bl", -7.0,  12.0),
        ("leg_br_upper", "leg_br_lower", "foot_br",  7.0,  12.0),
    ]
    for up_b, low_b, foot_b, lx, ly in legs:
        ctx.set_bone(up_b)
        ctx.add_box((lx - 2.6, ly - 2.6, 12.0), (lx + 2.6, ly + 2.6, 28.0), uv_main)
        ctx.set_bone(low_b)
        ctx.add_box((lx - 2.0, ly - 2.0, 4.0), (lx + 2.0, ly + 2.0, 12.0), uv_stocking)
        ctx.set_bone(foot_b)
        ctx.add_box((lx - 2.4, ly - 2.6, 0.0), (lx + 2.4, ly + 2.4, 4.0), UV_HOOF_DARK)
        
    ctx.set_bone("tail_01")
    ctx.add_box((-1.5, 18.0, 48.0), (1.5, 22.0, 58.0), uv_main)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_quadruped_armature(scene, name, leg_span_x=7.5, leg_front_y=-12.0, leg_back_y=12.0, 
                                        knee_z=12.0, hip_z=28.0, spine_z=46.0, head_y=-26.0, head_z=56.0)
    
    aliases = ["SKM_Animal_Goat_Kid"] if breed == "Brown" else []
    icon_aliases = ["baby_kid"] if breed == "Brown" else []
    icon_name = f"baby_kid_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=95.0, aliases=aliases, 
                                icon_name=icon_name, icon_aliases=icon_aliases)

# --- 5. CHICKENS ---
def build_chicken(breed="Red"):
    name = f"SKM_Animal_Chicken_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    uv_plumage = UV_GINGER_FUR if breed == "Red" else (UV_WHITE if breed == "White" else UV_SLATE_GREY)
    
    # Plump Avian Body
    ctx.set_bone("pelvis")
    ctx.add_cylinder_y(-4.0, 22.0, 14.0, 8, uv_plumage, cx=0.0, cz=25.0)
    
    ctx.set_bone("spine")
    ctx.add_cylinder_y(-22.0, -4.0, 14.5, 8, uv_plumage, cx=0.0, cz=26.0)
    
    # Neck & Head
    ctx.set_bone("neck")
    ctx.add_sloped_box((-7.0, -28.0), (7.0, -14.0), (-5.0, -26.0), (5.0, -16.0), 30.0, 45.0, uv_plumage)
    
    ctx.set_bone("head")
    ctx.add_box((-5.5, -30.0, 42.0), (5.5, -18.0, 52.0), uv_plumage)
    # Crimson Comb
    ctx.add_box((-1.2, -28.0, 52.0), (1.2, -18.0, 59.0), UV_CRIMSON_COMB)
    # Wattle
    ctx.add_box((-1.2, -30.0, 36.0), (1.2, -24.0, 42.0), UV_CRIMSON_COMB)
    
    # Beak
    ctx.set_bone("beak")
    ctx.add_tapered_cylinder_z(41.0, 47.0, 3.2, 0.5, 4, UV_GOLDEN_YELL, cx=0.0, cy=-32.0)
    
    # 2 Wings
    for sign, side in [(-1, 'l'), (1, 'r')]:
        ctx.set_bone(f'wing_{side}')
        wx = sign * 14.5
        ctx.add_box((wx - 2.0*sign, -12.0, 18.0), (wx + 2.0*sign, 10.0, 32.0), uv_plumage)
        ctx.set_bone(f'wing_tip_{side}')
        ctx.add_box((wx - 1.5*sign, 8.0, 20.0), (wx + 1.5*sign, 18.0, 28.0), uv_plumage)
        
    # 2 Legs
    for sign, side in [(-1, 'l'), (1, 'r')]:
        lx = sign * 6.5
        ctx.set_bone(f'leg_{side}_upper')
        ctx.add_box((lx - 2.5, -4.0, 10.0), (lx + 2.5, 2.0, 18.0), uv_plumage)
        ctx.set_bone(f'leg_{side}_lower')
        ctx.add_cylinder_z(3.0, 11.0, 1.2, 4, UV_GOLDEN_YELL, cx=lx, cy=-1.0)
        ctx.set_bone(f'foot_{side}')
        # 3 Forward Toes
        ctx.add_box((lx - 3.5, -8.0, 0.0), (lx - 1.5, 0.0, 3.0), UV_GOLDEN_YELL)
        ctx.add_box((lx - 1.0, -9.5, 0.0), (lx + 1.0, 0.0, 3.0), UV_GOLDEN_YELL)
        ctx.add_box((lx + 1.5, -8.0, 0.0), (lx + 3.5, 0.0, 3.0), UV_GOLDEN_YELL)
        
    # Tail Feathers
    ctx.set_bone("tail")
    ctx.add_sloped_box((-5.0, 14.0), (5.0, 26.0), (-7.0, 18.0), (7.0, 32.0), 28.0, 48.0, UV_BLACK if breed == "Red" else uv_plumage)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_avian_armature(scene, name, hip_z=18.0, knee_z=10.0, head_y=-21.0, head_z=48.0)
    aliases = ["SM_Animal_Chicken_Hen"] if breed == "Red" else []
    icon_name = f"livestock_chicken_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=80.0, aliases=aliases, icon_name=icon_name)

def build_chick(breed="Yellow"):
    name = f"SKM_Animal_Chicken_Chick_{breed}"
    scene, mat = setup_scene()
    
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(mesh_obj)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    ctx = AnimalMeshContext(bm, uv_layer)
    
    if breed == "Yellow":
        uv_body = UV_GOLDEN_YELL
    elif breed == "White":
        uv_body = UV_OFFWHITE
    elif breed == "Barred":
        uv_body = UV_SLATE_GREY
    else: # Brown
        uv_body = UV_CHESTNUT_MID
        
    # Fluffy ball body
    ctx.set_bone("pelvis")
    ctx.add_box((-6.0, -6.0, 7.0), (6.0, 8.0, 18.0), uv_body)
    if breed == "Barred":
        # White throat spot
        ctx.add_box((-3.0, -6.2, 10.0), (3.0, -3.0, 16.0), UV_OFFWHITE)
    elif breed == "Brown":
        # Darker dorsal stripe
        ctx.add_box((-2.0, -6.0, 17.5), (2.0, 8.0, 18.2), UV_DARK_BROWN)
        
    # Cute large head
    ctx.set_bone("head")
    ctx.add_box((-5.0, -14.0, 13.0), (5.0, -4.0, 23.0), uv_body)
    if breed == "Barred":
        # White crown spot
        ctx.add_box((-2.0, -10.0, 22.8), (2.0, -5.0, 23.2), UV_OFFWHITE)
        
    ctx.set_bone("beak")
    ctx.add_box((-1.5, -18.0, 15.0), (1.5, -13.0, 18.0), UV_ORANGE_BEAK)
    
    # 2 Tiny Wings
    for sign, side in [(-1, 'l'), (1, 'r')]:
        ctx.set_bone(f'wing_{side}')
        wx = sign * 6.5
        ctx.add_box((wx - 1.0*sign, -3.0, 10.0), (wx + 1.0*sign, 5.0, 16.0), uv_body)
        
        lx = sign * 3.2
        ctx.set_bone(f'leg_{side}_lower')
        ctx.add_cylinder_z(2.0, 7.0, 0.7, 4, UV_ORANGE_BEAK, cx=lx, cy=0.0)
        ctx.set_bone(f'foot_{side}')
        ctx.add_box((lx - 2.0, -4.0, 0.0), (lx + 2.0, 1.0, 2.0), UV_ORANGE_BEAK)
        
    ctx.set_bone("tail")
    ctx.add_box((-2.0, 7.0, 12.0), (2.0, 11.0, 16.0), uv_body)
    
    ctx.finish_and_skin(mesh_obj)
            
    arm_obj = create_avian_armature(scene, name, hip_z=10.0, knee_z=5.0, head_y=-9.0, head_z=18.0)
    
    aliases = ["SKM_Animal_Chicken_Chick"] if breed == "Yellow" else []
    icon_aliases = ["baby_chick"] if breed == "Yellow" else []
    icon_name = f"baby_chick_{breed.lower()}"
    finalize_and_export_skeletal(mesh_obj, arm_obj, mat, name, ortho_scale=45.0, aliases=aliases, 
                                icon_name=icon_name, icon_aliases=icon_aliases)

# ==============================================================================
# MAIN BATCH EXECUTION
# ==============================================================================
if __name__ == '__main__':
    print("=== BUILDING HOMESTEADER LIVESTOCK SUITE (15 ADULTS + 19 BABIES) ===")
    
    # 1. Cattle Family (3 Adults + 4 Calves)
    print("\n--- Generating Cattle Family ---")
    build_cow("Holstein")
    build_cow("Jersey")
    build_cow("Highland")
    build_calf("Holstein")
    build_calf("Jersey")
    build_calf("Highland")
    build_calf("Chestnut")
    
    # 2. Pig Family (3 Adults + 4 Piglets)
    print("\n--- Generating Pig Family ---")
    build_pig("Pink")
    build_pig("Hampshire")
    build_pig("Duroc")
    build_piglet("Pink")
    build_piglet("Hampshire")
    build_piglet("Duroc")
    build_piglet("Spotted")
    
    # 3. Sheep Family (3 Adults + 4 Lambs)
    print("\n--- Generating Sheep Family ---")
    build_sheep("Suffolk")
    build_sheep("White")
    build_sheep("Tan")
    build_lamb("Suffolk")
    build_lamb("White")
    build_lamb("Tan")
    build_lamb("Spotted")
    
    # 4. Goat Family (3 Adults + 3 Kids)
    print("\n--- Generating Goat Family ---")
    build_goat("Brown")
    build_goat("White")
    build_goat("BlackWhite")
    build_kid("Brown")
    build_kid("White")
    build_kid("BlackWhite")
    
    # 5. Chicken Family (3 Adults + 4 Chicks)
    print("\n--- Generating Chicken Family ---")
    build_chicken("Red")
    build_chicken("White")
    build_chicken("Barred")
    build_chick("Yellow")
    build_chick("White")
    build_chick("Barred")
    build_chick("Brown")
    
    print("\nSUCCESS: All 34 rigged skeletal livestock animal models and icons generated successfully!")
