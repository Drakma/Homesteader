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

# Helper to create material with exact sRGB color
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def make_mat(name, r255, g255, b255, roughness=0.45, specular=0.35, emission=None):
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

# Materials directly sampled from baby_calf.png
mat_fur        = make_mat("M_Calf_Fur",        218, 146,  88, roughness=0.42, specular=0.35)
mat_blaze      = make_mat("M_Calf_Blaze",      251, 245, 235, roughness=0.42, specular=0.35)
mat_muzzle     = make_mat("M_Calf_Muzzle",     244, 206, 201, roughness=0.42, specular=0.35)
mat_inner_ear  = make_mat("M_Calf_InnerEar",  243, 148, 140, roughness=0.42, specular=0.35)
mat_belly      = make_mat("M_Calf_Belly",      245, 243, 240, roughness=0.42, specular=0.35)
mat_hoof       = make_mat("M_Calf_Hoof",        92,  58,  44, roughness=0.50, specular=0.25)
mat_horn       = make_mat("M_Calf_Horn",       250, 244, 234, roughness=0.35, specular=0.35)
mat_nostril    = make_mat("M_Calf_Nostril",    160, 100,  92, roughness=0.50, specular=0.20)
mat_eye        = make_mat("M_Calf_Eye",         18,  18,  22, roughness=0.03, specular=1.0)
mat_hl         = make_mat("M_Calf_Highlight",  255, 255, 255, roughness=0.05, specular=1.0, emission=(1.0, 1.0, 1.0))
mat_tail_tuft  = make_mat("M_Calf_Tuft",       160, 100,  60, roughness=0.50, specular=0.20)

# Helper: Quad-box builder with subsurf
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
# Ground is at Z = 0
# -------------------------------------------------------------------------

# 1. Torso: Plump rounded chibi cow body (smooth bean)
torso = make_part("Calf_Torso", (0.0, 0.0, 31.0), (28.0, 42.0, 28.0), mat_fur, rot=(math.radians(2), 0, 0))

# Belly patch (white underside extending to side)
belly = make_part("Calf_Belly", (-0.5, 0.0, 22.0), (26.0, 32.0, 16.0), mat_belly, rot=(math.radians(2), 0, math.radians(2)))

# White flank crescent on left side (flank of calf)
flank = make_part("Calf_Flank_L", (-13.0, -5.0, 28.0), (3.5, 18.0, 15.0), mat_belly, rot=(0, math.radians(-10), 0))

# 2. Neck: Smooth bridge between torso and head
neck = make_part("Calf_Neck", (-1.5, 14.0, 37.0), (22.0, 22.0, 24.0), mat_fur, rot=(math.radians(20), 0, math.radians(-5)))

# 3. Head: Big adorable rounded chibi head, tilted cutely
head = make_part("Calf_Head", (-4.0, 24.0, 44.0), (28.0, 27.0, 28.0), mat_fur, rot=(math.radians(10), math.radians(-8), math.radians(-15)))

# Cream Forehead Blaze (covers almost the whole front face)
blaze = make_part("Calf_Blaze", (-5.5, 26.5, 46.0), (22.0, 22.0, 26.0), mat_blaze, rot=(math.radians(10), math.radians(-8), math.radians(-15)))

# 4. Muzzle: Soft pink snout with nostrils
muzzle = make_part("Calf_Muzzle", (-10.0, 34.0, 37.5), (18.5, 16.0, 13.5), mat_muzzle, rot=(math.radians(12), math.radians(-8), math.radians(-18)))

# Nostril dimples
nos_l = make_part("Calf_Nos_L", (-14.0, 40.0, 36.5), (2.8, 2.0, 2.2), mat_nostril, rot=(0, 0, math.radians(-18)))
nos_r = make_part("Calf_Nos_R", (-8.0, 39.0, 37.2), (2.8, 2.0, 2.2), mat_nostril, rot=(0, 0, math.radians(-18)))

# 5. Eyes: Big cartoon glossy black eyes with white highlight
# Left eye (facing camera, large and cute)
eye_l = make_part("Calf_Eye_L", (-14.5, 30.0, 44.5), (4.5, 7.5, 7.5), mat_eye, rot=(math.radians(8), math.radians(-8), math.radians(-32)))
# White highlight dot on top-left of pupil
hl_l = make_part("Calf_Eye_HL_L", (-15.6, 30.5, 46.8), (2.2, 2.8, 2.8), mat_hl, rot=(math.radians(8), math.radians(-8), math.radians(-32)))

# Right eye (subtle on far side)
eye_r = make_part("Calf_Eye_R", (7.0, 25.0, 47.0), (3.5, 6.5, 6.5), mat_eye, rot=(math.radians(8), math.radians(-8), math.radians(20)))

# 6. Ears: Cute wide ears sticking out
# Left ear (pointing horizontally to the right/side with pink interior)
ear_l = make_part("Calf_Ear_L", (-15.5, 19.5, 46.5), (17.0, 7.5, 4.8), mat_fur, rot=(math.radians(-5), math.radians(-12), math.radians(-25)))
ear_l_in = make_part("Calf_Ear_L_In", (-15.8, 19.8, 46.2), (14.0, 6.0, 3.8), mat_inner_ear, rot=(math.radians(-5), math.radians(-12), math.radians(-25)))

# Right ear (pointing up-left on top of head)
ear_r = make_part("Calf_Ear_R", (7.0, 16.5, 55.5), (16.0, 7.5, 4.8), mat_fur, rot=(math.radians(12), math.radians(22), math.radians(35)))
ear_r_in = make_part("Calf_Ear_R_In", (6.8, 16.8, 55.2), (13.0, 6.0, 3.8), mat_inner_ear, rot=(math.radians(12), math.radians(22), math.radians(35)))

# 7. Horn Buds: Cute stubby cream horns
horn_l = make_part("Calf_Horn_L", (-7.5, 23.5, 54.5), (4.5, 4.5, 7.5), mat_horn, rot=(math.radians(18), math.radians(-20), math.radians(-20)))
horn_r = make_part("Calf_Horn_R", (2.0, 18.5, 56.5), (4.5, 4.5, 7.5), mat_horn, rot=(math.radians(18), math.radians(12), math.radians(15)))

# 8. Four Sturdy Vertical Legs with Hooves (Z goes from 0 up to 26 cm)
# Left Front Leg (straight, sturdy, firmly grounded at Z=0)
leg_lf = make_part("Calf_Leg_LF", (-8.5, 11.0, 15.0), (10.0, 10.0, 20.0), mat_fur)
hoof_lf = make_part("Calf_Hoof_LF", (-8.5, 11.0, 3.5), (11.0, 11.0, 7.0), mat_hoof)

# Right Front Leg (behind, slightly inward)
leg_rf = make_part("Calf_Leg_RF", (6.5, 12.5, 15.0), (9.5, 9.5, 20.0), mat_fur)
hoof_rf = make_part("Calf_Hoof_RF", (6.5, 12.5, 3.5), (10.5, 10.5, 7.0), mat_hoof)

# Left Back Leg (rear flank)
leg_lb = make_part("Calf_Leg_LB", (-8.0, -14.0, 15.0), (10.0, 10.0, 20.0), mat_fur)
hoof_lb = make_part("Calf_Hoof_LB", (-8.0, -14.0, 3.5), (11.0, 11.0, 7.0), mat_hoof)

# Right Back Leg (far rear)
leg_rb = make_part("Calf_Leg_RB", (6.5, -13.0, 15.0), (9.5, 9.5, 20.0), mat_fur)
hoof_rb = make_part("Calf_Hoof_RB", (6.5, -13.0, 3.5), (10.5, 10.5, 7.0), mat_hoof)

# 9. Tail with Tuft
tail = make_part("Calf_Tail", (0.0, -20.5, 30.0), (4.0, 5.0, 12.0), mat_fur, rot=(math.radians(-30), 0, 0))
tuft = make_part("Calf_Tail_Tuft", (0.0, -24.5, 25.5), (5.5, 6.0, 8.0), mat_tail_tuft, rot=(math.radians(-35), 0, 0))

# -------------------------------------------------------------------------
# CAMERA SETUP (Lower elevation, looking straight-on isometric)
# -------------------------------------------------------------------------
target = mathutils.Vector((-2.0, 4.0, 28.0))

cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 68.0
cam_data.clip_end = 5000.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

dist = 500.0
pitch = math.radians(20.0) # Lower pitch to see face directly
yaw = math.radians(48.0)

cam_x = target.x - dist * math.cos(pitch) * math.sin(yaw)
cam_y = target.y + dist * math.cos(pitch) * math.cos(yaw)
cam_z = target.z + dist * math.sin(pitch)

cam_obj.location = (cam_x, cam_y, cam_z)
dir_vec = -(cam_obj.location - target).normalized()
cam_obj.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()

# -------------------------------------------------------------------------
# LIGHTING SETUP (Soft studio lighting matching icon)
# -------------------------------------------------------------------------
# Key Light: Top-left warm light
l_key = bpy.data.lights.new("Key", 'SUN')
l_key.energy = 4.0
l_key.color = (1.0, 0.97, 0.92)
l_k_obj = bpy.data.objects.new("Key", l_key)
scene.collection.objects.link(l_k_obj)
l_k_obj.rotation_euler = (math.radians(45), math.radians(-10), math.radians(55))

# Fill Light: Warm bounce fill
l_fill = bpy.data.lights.new("Fill", 'SUN')
l_fill.energy = 2.6
l_fill.color = (1.0, 0.94, 0.88)
l_f_obj = bpy.data.objects.new("Fill", l_fill)
scene.collection.objects.link(l_f_obj)
l_f_obj.rotation_euler = (math.radians(30), math.radians(20), math.radians(-125))

# Front Ambient: Very soft front light to keep facial crevices bright & cute
l_front = bpy.data.lights.new("Front", 'SUN')
l_front.energy = 1.5
l_front.color = (1.0, 0.98, 0.95)
l_fr_obj = bpy.data.objects.new("Front", l_front)
scene.collection.objects.link(l_fr_obj)
l_fr_obj.rotation_euler = cam_obj.rotation_euler

# Rim Light
l_rim = bpy.data.lights.new("Rim", 'SUN')
l_rim.energy = 1.8
l_rim.color = (1.0, 0.98, 0.95)
l_r_obj = bpy.data.objects.new("Rim", l_rim)
scene.collection.objects.link(l_r_obj)
l_r_obj.rotation_euler = (math.radians(80), 0, 0)

# Render test image
render_path = os.path.join(RENDERS_DIR, "Identical_Calf_v4_render.png")
scene.render.filepath = render_path
bpy.ops.render.render(write_still=True)
print("SUCCESS: Rendered v4 to", render_path)

