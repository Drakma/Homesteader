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
mat_fur        = make_mat("M_Calf_Fur",        218, 146,  88, roughness=0.45, specular=0.3)
mat_blaze      = make_mat("M_Calf_Blaze",      251, 245, 235, roughness=0.45, specular=0.3)
mat_muzzle     = make_mat("M_Calf_Muzzle",     244, 206, 201, roughness=0.45, specular=0.3)
mat_inner_ear  = make_mat("M_Calf_InnerEar",  243, 148, 140, roughness=0.45, specular=0.3)
mat_belly      = make_mat("M_Calf_Belly",      245, 243, 240, roughness=0.45, specular=0.3)
mat_hoof       = make_mat("M_Calf_Hoof",        92,  58,  44, roughness=0.55, specular=0.2)
mat_horn       = make_mat("M_Calf_Horn",       250, 244, 234, roughness=0.40, specular=0.3)
mat_nostril    = make_mat("M_Calf_Nostril",    160, 100,  92, roughness=0.50, specular=0.2)
mat_eye        = make_mat("M_Calf_Eye",         18,  18,  22, roughness=0.04, specular=1.0)
mat_hl         = make_mat("M_Calf_Highlight",  255, 255, 255, roughness=0.05, specular=1.0, emission=(1.0, 1.0, 1.0))
mat_tail_tuft  = make_mat("M_Calf_Tuft",       160, 100,  60, roughness=0.50, specular=0.2)

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
# -------------------------------------------------------------------------

# 1. Torso: Plump rounded chibi cow body
torso = make_part("Calf_Torso", (0.0, -1.0, 36.0), (28.0, 38.0, 28.0), mat_fur, rot=(math.radians(2), 0, 0))

# Belly patch (white)
belly = make_part("Calf_Belly", (-1.0, -0.5, 26.5), (26.0, 26.0, 16.0), mat_belly, rot=(math.radians(2), 0, math.radians(4)))

# White flank patch on left side
flank = make_part("Calf_Flank_L", (-13.2, -4.0, 32.0), (3.0, 15.0, 13.0), mat_belly, rot=(0, math.radians(-10), 0))

# 2. Neck: Connects torso smoothly to head
neck = make_part("Calf_Neck", (-2.0, 13.0, 42.0), (22.0, 20.0, 23.0), mat_fur, rot=(math.radians(22), 0, math.radians(-5)))

# 3. Head: Adorable rounded chibi head, tilted cutely towards camera
head = make_part("Calf_Head", (-5.0, 23.0, 52.0), (28.0, 26.0, 27.0), mat_fur, rot=(math.radians(12), math.radians(-10), math.radians(-18)))

# Cream Forehead Blaze (large flowing patch on head)
blaze = make_part("Calf_Blaze", (-6.5, 25.5, 54.5), (21.0, 21.0, 25.0), mat_blaze, rot=(math.radians(12), math.radians(-10), math.radians(-18)))

# 4. Muzzle: Soft pink snout with nostrils
muzzle = make_part("Calf_Muzzle", (-11.5, 33.5, 44.5), (19.0, 15.0, 14.0), mat_muzzle, rot=(math.radians(15), math.radians(-12), math.radians(-22)))

# Nostril dimples
nos_l = make_part("Calf_Nos_L", (-16.0, 39.5, 43.5), (3.0, 2.0, 2.5), mat_nostril, rot=(0, 0, math.radians(-22)))
nos_r = make_part("Calf_Nos_R", (-9.5, 38.0, 44.2), (3.0, 2.0, 2.5), mat_nostril, rot=(0, 0, math.radians(-22)))

# 5. Eyes: Big cartoon glossy black eyes with white highlight
# Left eye (prominently facing camera)
eye_l = make_part("Calf_Eye_L", (-15.5, 29.5, 53.5), (4.5, 8.0, 8.0), mat_eye, rot=(math.radians(10), math.radians(-12), math.radians(-38)))
# White highlight dot on top-left of pupil
hl_l = make_part("Calf_Eye_HL_L", (-16.8, 30.0, 56.0), (2.2, 2.8, 2.8), mat_hl, rot=(math.radians(10), math.radians(-12), math.radians(-38)))

# Right eye (subtle on far side)
eye_r = make_part("Calf_Eye_R", (6.5, 23.5, 55.5), (3.5, 7.0, 7.0), mat_eye, rot=(math.radians(10), math.radians(-12), math.radians(20)))

# 6. Ears: Cute wide ears sticking out
# Left ear (pointing out towards -X, slightly down/drooping)
ear_l = make_part("Calf_Ear_L", (-17.0, 18.5, 53.5), (17.0, 7.5, 4.8), mat_fur, rot=(math.radians(-10), math.radians(-15), math.radians(-35)))
ear_l_in = make_part("Calf_Ear_L_In", (-17.3, 18.8, 53.2), (14.0, 6.0, 3.8), mat_inner_ear, rot=(math.radians(-10), math.radians(-15), math.radians(-35)))

# Right ear (pointing up/out on top-right of head)
ear_r = make_part("Calf_Ear_R", (7.0, 15.5, 63.5), (16.0, 7.5, 4.8), mat_fur, rot=(math.radians(15), math.radians(25), math.radians(35)))
ear_r_in = make_part("Calf_Ear_R_In", (6.8, 15.8, 63.2), (13.0, 6.0, 3.8), mat_inner_ear, rot=(math.radians(15), math.radians(25), math.radians(35)))

# 7. Horn Buds: Cute stubby cream horns
horn_l = make_part("Calf_Horn_L", (-9.2, 22.5, 63.5), (4.5, 4.5, 8.5), mat_horn, rot=(math.radians(20), math.radians(-25), math.radians(-25)))
horn_r = make_part("Calf_Horn_R", (1.0, 17.0, 65.5), (4.5, 4.5, 8.5), mat_horn, rot=(math.radians(20), math.radians(15), math.radians(15)))

# 8. Four Sturdy Thick Legs with Hooves
# Left Front Leg (thick, sturdy, connecting into shoulder)
shoulder_lf = make_part("Calf_Shoulder_LF", (-9.0, 10.0, 26.0), (12.0, 12.0, 14.0), mat_fur)
leg_lf = make_part("Calf_Leg_LF", (-9.0, 10.0, 17.0), (10.5, 10.5, 14.0), mat_fur)
hoof_lf = make_part("Calf_Hoof_LF", (-9.0, 10.0, 5.0), (11.5, 11.5, 9.0), mat_hoof)

# Right Front Leg
shoulder_rf = make_part("Calf_Shoulder_RF", (8.0, 12.0, 26.0), (11.0, 11.0, 14.0), mat_fur)
leg_rf = make_part("Calf_Leg_RF", (8.0, 12.0, 17.0), (10.0, 10.0, 14.0), mat_fur)
hoof_rf = make_part("Calf_Hoof_RF", (8.0, 12.0, 5.0), (11.0, 11.0, 9.0), mat_hoof)

# Left Back Leg (rear flank / hip)
hip_lb = make_part("Calf_Hip_LB", (-8.5, -14.0, 26.0), (12.5, 12.5, 14.0), mat_fur)
leg_lb = make_part("Calf_Leg_LB", (-8.5, -14.0, 17.0), (10.5, 10.5, 14.0), mat_fur)
hoof_lb = make_part("Calf_Hoof_LB", (-8.5, -14.0, 5.0), (11.5, 11.5, 9.0), mat_hoof)

# Right Back Leg
hip_rb = make_part("Calf_Hip_RB", (7.5, -13.0, 26.0), (11.5, 11.5, 14.0), mat_fur)
leg_rb = make_part("Calf_Leg_RB", (7.5, -13.0, 17.0), (10.0, 10.0, 14.0), mat_fur)
hoof_rb = make_part("Calf_Hoof_RB", (7.5, -13.0, 5.0), (11.0, 11.0, 9.0), mat_hoof)

# 9. Tail with Tuft
tail = make_part("Calf_Tail", (0.0, -20.5, 36.0), (4.5, 5.5, 13.0), mat_fur, rot=(math.radians(-35), 0, 0))
tuft = make_part("Calf_Tail_Tuft", (0.0, -25.0, 31.0), (6.0, 6.5, 9.0), mat_tail_tuft, rot=(math.radians(-40), 0, 0))

# -------------------------------------------------------------------------
# CAMERA SETUP
# -------------------------------------------------------------------------
target = mathutils.Vector((-2.0, 2.0, 36.0))

cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 82.0
cam_data.clip_end = 5000.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

dist = 500.0
pitch = math.radians(28.0)
yaw = math.radians(52.0)

cam_x = target.x - dist * math.cos(pitch) * math.sin(yaw)
cam_y = target.y + dist * math.cos(pitch) * math.cos(yaw)
cam_z = target.z + dist * math.sin(pitch)

cam_obj.location = (cam_x, cam_y, cam_z)
dir_vec = -(cam_obj.location - target).normalized()
cam_obj.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()

# -------------------------------------------------------------------------
# LIGHTING SETUP (Warm studio lighting matching icon)
# -------------------------------------------------------------------------
# Key Light: Top-left warm light
l_key = bpy.data.lights.new("Key", 'SUN')
l_key.energy = 4.2
l_key.color = (1.0, 0.96, 0.90)
l_k_obj = bpy.data.objects.new("Key", l_key)
scene.collection.objects.link(l_k_obj)
l_k_obj.rotation_euler = (math.radians(50), math.radians(-10), math.radians(65))

# Fill Light: Warm bounce fill (NOT cold blue!)
l_fill = bpy.data.lights.new("Fill", 'SUN')
l_fill.energy = 2.4
l_fill.color = (1.0, 0.92, 0.85)
l_f_obj = bpy.data.objects.new("Fill", l_fill)
scene.collection.objects.link(l_f_obj)
l_f_obj.rotation_euler = (math.radians(35), math.radians(20), math.radians(-115))

# Rim / Top Light
l_rim = bpy.data.lights.new("Rim", 'SUN')
l_rim.energy = 2.0
l_rim.color = (1.0, 0.98, 0.95)
l_r_obj = bpy.data.objects.new("Rim", l_rim)
scene.collection.objects.link(l_r_obj)
l_r_obj.rotation_euler = (math.radians(85), 0, 0)

# Render test image
render_path = os.path.join(RENDERS_DIR, "Identical_Calf_v3_render.png")
scene.render.filepath = render_path
bpy.ops.render.render(write_still=True)
print("SUCCESS: Rendered v3 to", render_path)

