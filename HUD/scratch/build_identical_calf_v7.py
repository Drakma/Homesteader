import bpy
import bmesh
import math
import mathutils
import os

RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test"

# Scene Setup
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def make_mat(name, r255, g255, b255, roughness=0.60, specular=0.15, emission=None):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    lr = srgb_to_linear(r255 / 255.0)
    lg = srgb_to_linear(g255 / 255.0)
    lb = srgb_to_linear(b255 / 255.0)
    
    bsdf.inputs['Base Color'].default_value = (lr, lg, lb, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = specular
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = specular
        
    if emission:
        er, eg, eb = emission
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = (er, eg, eb, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 1.0
            
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

# Matte, soft velvety materials matching icon
mat_fur        = make_mat("M_Calf_Fur",        218, 146,  88, roughness=0.62, specular=0.12)
mat_blaze      = make_mat("M_Calf_Blaze",      251, 245, 235, roughness=0.60, specular=0.12)
mat_muzzle     = make_mat("M_Calf_Muzzle",     244, 206, 201, roughness=0.55, specular=0.15)
mat_inner_ear  = make_mat("M_Calf_InnerEar",  243, 148, 140, roughness=0.55, specular=0.15)
mat_belly      = make_mat("M_Calf_Belly",      245, 243, 240, roughness=0.60, specular=0.12)
mat_hoof       = make_mat("M_Calf_Hoof",        88,  54,  40, roughness=0.65, specular=0.10)
mat_horn       = make_mat("M_Calf_Horn",       250, 244, 234, roughness=0.45, specular=0.20)
mat_nostril    = make_mat("M_Calf_Nostril",    130,  70,  62, roughness=0.60, specular=0.10)
mat_eye        = make_mat("M_Calf_Eye",         18,  18,  22, roughness=0.03, specular=1.0)
mat_hl         = make_mat("M_Calf_Highlight",  255, 255, 255, roughness=0.05, specular=1.0, emission=(1.0, 1.0, 1.0))
mat_tail_tuft  = make_mat("M_Calf_Tuft",       150,  92,  52, roughness=0.60, specular=0.10)

def make_part(name, center, size, mat, rot=(0,0,0), subsurf_levels=2):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    
    S = mathutils.Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    R = mathutils.Euler(rot).to_matrix().to_4x4()
    T = mathutils.Matrix.Translation(center)
    M = T @ R @ S
    
    for v in bm.verts:
        v.co = M @ v.co
        
    for f in bm.faces:
        f.smooth = True
            
    bm.to_mesh(mesh)
    bm.free()
    
    if subsurf_levels > 0:
        sub = obj.modifiers.new("Subsurf", 'SUBSURF')
        sub.levels = subsurf_levels
        sub.render_levels = subsurf_levels
    return obj

# -------------------------------------------------------------------------
# CALF MODELING (Calf facing +Y, Up = +Z, Right = +X, Left = -X)
# -------------------------------------------------------------------------

# 1. Torso: Plump rounded chibi cow body (smooth single barrel)
torso = make_part("Calf_Torso", (0.0, 0.0, 26.0), (28.0, 36.0, 26.0), mat_fur, rot=(math.radians(2), 0, 0))

# Belly patch (white underside sweeping gently up the rear flank)
belly = make_part("Calf_Belly", (-1.0, -1.0, 17.5), (26.0, 30.0, 14.0), mat_belly, rot=(math.radians(2), 0, math.radians(2)))
flank = make_part("Calf_Flank_L", (-12.5, -7.0, 19.5), (3.5, 14.0, 11.0), mat_belly, rot=(math.radians(8), math.radians(-12), 0))

# 2. Neck: Smooth bridge into torso
neck = make_part("Calf_Neck", (-1.5, 10.5, 29.0), (25.0, 22.0, 23.0), mat_fur, rot=(math.radians(18), 0, math.radians(-5)))

# 3. Head: Adorable rounded chibi head
head = make_part("Calf_Head", (-3.5, 18.5, 36.0), (27.0, 25.0, 26.0), mat_fur, rot=(math.radians(10), math.radians(-8), math.radians(-15)))

# Cream Forehead Blaze
blaze = make_part("Calf_Blaze", (-4.0, 21.0, 37.5), (17.0, 20.0, 25.0), mat_blaze, rot=(math.radians(10), math.radians(-8), math.radians(-15)))

# 4. Muzzle: Soft pink snout with nostrils
muzzle = make_part("Calf_Muzzle", (-8.5, 27.5, 30.0), (19.0, 15.5, 13.0), mat_muzzle, rot=(math.radians(12), math.radians(-8), math.radians(-18)))

# Darker distinct nostril dimples
nos_l = make_part("Calf_Nos_L", (-12.2, 33.2, 29.0), (2.2, 1.6, 1.8), mat_nostril, rot=(0, 0, math.radians(-18)))
nos_r = make_part("Calf_Nos_R", (-6.5, 32.5, 29.5), (2.2, 1.6, 1.8), mat_nostril, rot=(0, 0, math.radians(-18)))

# 5. Eyes: Big cartoon glossy black eyes with prominent white highlight dot
eye_l = make_part("Calf_Eye_L", (-13.8, 23.0, 35.5), (4.0, 7.2, 7.2), mat_eye, rot=(math.radians(8), math.radians(-8), math.radians(-32)))
# Prominent white circle highlight at 10 o'clock
hl_l  = make_part("Calf_Eye_HL_L", (-15.2, 22.5, 38.0), (2.4, 2.6, 2.6), mat_hl, rot=(math.radians(8), math.radians(-8), math.radians(-32)))

eye_r = make_part("Calf_Eye_R", (7.0, 19.5, 38.5), (3.5, 6.5, 6.5), mat_eye, rot=(math.radians(8), math.radians(-8), math.radians(20)))

# 6. Ears
# Left ear (pointing horizontally with cupped pink interior)
ear_l    = make_part("Calf_Ear_L", (-14.0, 13.5, 37.5), (16.0, 7.0, 4.5), mat_fur, rot=(math.radians(-5), math.radians(-12), math.radians(-25)))
ear_l_in = make_part("Calf_Ear_L_In", (-14.2, 13.8, 37.2), (13.5, 5.5, 3.5), mat_inner_ear, rot=(math.radians(-5), math.radians(-12), math.radians(-25)))

# Right ear (pointing up-left with pink interior facing forward)
ear_r    = make_part("Calf_Ear_R", (6.5, 11.5, 46.0), (15.0, 7.0, 4.5), mat_fur, rot=(math.radians(15), math.radians(25), math.radians(45)))
ear_r_in = make_part("Calf_Ear_R_In", (6.8, 12.0, 46.2), (12.5, 5.5, 3.5), mat_inner_ear, rot=(math.radians(15), math.radians(25), math.radians(45)))

# 7. Horn Buds: Cute stubby cream horns
horn_l = make_part("Calf_Horn_L", (-6.5, 17.0, 45.5), (4.2, 4.2, 7.0), mat_horn, rot=(math.radians(18), math.radians(-20), math.radians(-20)))
horn_r = make_part("Calf_Horn_R", (1.5, 13.0, 47.0), (4.2, 4.2, 7.0), mat_horn, rot=(math.radians(18), math.radians(12), math.radians(15)))

# 8. Four Smooth Tapered Legs with Hooves (firmly grounded at Z=0)
# Single continuous leg cylinder from torso down to hoof!
# Front-left leg (straight down from shoulder)
leg_lf  = make_part("Calf_Leg_LF", (-7.5, 8.5, 12.5), (10.5, 10.5, 19.0), mat_fur)
hoof_lf = make_part("Calf_Hoof_LF", (-7.5, 8.5, 2.5), (11.0, 11.0, 5.0), mat_hoof)

# Front-right leg (tucked behind)
leg_rf  = make_part("Calf_Leg_RF", (5.5, 10.0, 12.5), (9.5, 9.5, 19.0), mat_fur)
hoof_rf = make_part("Calf_Hoof_RF", (5.5, 10.0, 2.5), (10.0, 10.0, 5.0), mat_hoof)

# Rear-left leg (hip to hoof)
leg_lb  = make_part("Calf_Leg_LB", (-7.0, -12.0, 12.5), (10.5, 10.5, 19.0), mat_fur)
hoof_lb = make_part("Calf_Hoof_LB", (-7.0, -12.0, 2.5), (11.0, 11.0, 5.0), mat_hoof)

# Rear-right leg
leg_rb  = make_part("Calf_Leg_RB", (5.5, -11.0, 12.5), (9.5, 9.5, 19.0), mat_fur)
hoof_rb = make_part("Calf_Hoof_RB", (5.5, -11.0, 2.5), (10.0, 10.0, 5.0), mat_hoof)

# 9. Tail with Tuft
tail = make_part("Calf_Tail", (0.0, -17.5, 26.0), (3.5, 4.5, 11.0), mat_fur, rot=(math.radians(-30), 0, 0))
tuft = make_part("Calf_Tail_Tuft", (0.0, -21.0, 22.0), (5.0, 5.5, 7.0), mat_tail_tuft, rot=(math.radians(-35), 0, 0))

# -------------------------------------------------------------------------
# CAMERA SETUP
# -------------------------------------------------------------------------
target = mathutils.Vector((-1.5, 2.5, 23.0))

cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 55.0
cam_data.clip_end = 5000.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

dist = 500.0
pitch = math.radians(22.0)
yaw = math.radians(50.0)

cam_x = target.x - dist * math.cos(pitch) * math.sin(yaw)
cam_y = target.y + dist * math.cos(pitch) * math.cos(yaw)
cam_z = target.z + dist * math.sin(pitch)

cam_obj.location = (cam_x, cam_y, cam_z)
dir_vec = -(cam_obj.location - target).normalized()
cam_obj.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()

# -------------------------------------------------------------------------
# LIGHTING SETUP
# -------------------------------------------------------------------------
l_key = bpy.data.lights.new("Key", 'SUN')
l_key.energy = 4.2
l_key.color = (1.0, 0.97, 0.92)
l_k_obj = bpy.data.objects.new("Key", l_key)
scene.collection.objects.link(l_k_obj)
l_k_obj.rotation_euler = (math.radians(45), math.radians(-10), math.radians(55))

l_fill = bpy.data.lights.new("Fill", 'SUN')
l_fill.energy = 2.6
l_fill.color = (1.0, 0.94, 0.88)
l_f_obj = bpy.data.objects.new("Fill", l_fill)
scene.collection.objects.link(l_f_obj)
l_f_obj.rotation_euler = (math.radians(30), math.radians(20), math.radians(-125))

l_front = bpy.data.lights.new("Front", 'SUN')
l_front.energy = 1.6
l_front.color = (1.0, 0.98, 0.95)
l_fr_obj = bpy.data.objects.new("Front", l_front)
scene.collection.objects.link(l_fr_obj)
l_fr_obj.rotation_euler = cam_obj.rotation_euler

l_rim = bpy.data.lights.new("Rim", 'SUN')
l_rim.energy = 1.8
l_rim.color = (1.0, 0.98, 0.95)
l_r_obj = bpy.data.objects.new("Rim", l_rim)
scene.collection.objects.link(l_r_obj)
l_r_obj.rotation_euler = (math.radians(80), 0, 0)

render_path = os.path.join(RENDERS_DIR, "Identical_Calf_v7_render.png")
scene.render.filepath = render_path
bpy.ops.render.render(write_still=True)
print("SUCCESS: Rendered v7 to", render_path)

