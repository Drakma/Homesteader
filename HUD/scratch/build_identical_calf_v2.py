import bpy
import bmesh
import math
import mathutils
import os

ICON_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test"
TEX_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\textures\animals"
tex_path = os.path.join(TEX_DIR, "T_Baby_Calf_BaseColor.png")

# Scene Setup
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'

# UV Coordinates
UV_FUR       = (0.75, 0.75)
UV_CREAM     = (0.25, 0.90)
UV_PINK      = (0.75, 0.90)
UV_HOOF      = (0.12, 0.65)
UV_INNER_EAR = (0.37, 0.65)
UV_HORN      = (0.62, 0.65)
UV_EYE       = (0.87, 0.65)
UV_WHITE     = (0.12, 0.35)
UV_SHADOW    = (0.37, 0.35)
UV_NOSTRIL   = (0.62, 0.35)

# Materials
mat_body = bpy.data.materials.new(name="M_Calf_Body")
mat_body.use_nodes = True
nb = mat_body.node_tree.nodes
lb = mat_body.node_tree.links
nb.clear()

out_b = nb.new('ShaderNodeOutputMaterial')
bsdf_b = nb.new('ShaderNodeBsdfPrincipled')
bsdf_b.inputs['Roughness'].default_value = 0.45
if 'Specular IOR Level' in bsdf_b.inputs:
    bsdf_b.inputs['Specular IOR Level'].default_value = 0.35
elif 'Specular' in bsdf_b.inputs:
    bsdf_b.inputs['Specular'].default_value = 0.35

tex_node = nb.new('ShaderNodeTexImage')
tex_node.image = bpy.data.images.load(tex_path)
tex_node.interpolation = 'Linear'

lb.new(tex_node.outputs['Color'], bsdf_b.inputs['Base Color'])
lb.new(bsdf_b.outputs['BSDF'], out_b.inputs['Surface'])

# Eye Material
mat_eye = bpy.data.materials.new(name="M_Calf_Eye")
mat_eye.use_nodes = True
ne = mat_eye.node_tree.nodes
le = mat_eye.node_tree.links
ne.clear()
out_e = ne.new('ShaderNodeOutputMaterial')
bsdf_e = ne.new('ShaderNodeBsdfPrincipled')
bsdf_e.inputs['Base Color'].default_value = (0.015, 0.015, 0.02, 1.0)
bsdf_e.inputs['Roughness'].default_value = 0.05
if 'Specular IOR Level' in bsdf_e.inputs:
    bsdf_e.inputs['Specular IOR Level'].default_value = 1.0
elif 'Specular' in bsdf_e.inputs:
    bsdf_e.inputs['Specular'].default_value = 1.0
le.new(bsdf_e.outputs['BSDF'], out_e.inputs['Surface'])

# Eye Highlight Material
mat_hl = bpy.data.materials.new(name="M_Calf_HL")
mat_hl.use_nodes = True
nh = mat_hl.node_tree.nodes
lh = mat_hl.node_tree.links
nh.clear()
out_h = nh.new('ShaderNodeOutputMaterial')
bsdf_h = nh.new('ShaderNodeBsdfPrincipled')
bsdf_h.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
bsdf_h.inputs['Roughness'].default_value = 0.1
if 'Emission Color' in bsdf_h.inputs:
    bsdf_h.inputs['Emission Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf_h.inputs['Emission Strength'].default_value = 0.8
lh.new(bsdf_h.outputs['BSDF'], out_h.inputs['Surface'])

# Helper: Quad-box builder with subsurf
def make_part(name, center, size, uv, mat=mat_body, rot=(0,0,0), subsurf_levels=2):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    bmesh.ops.create_cube(bm, size=1.0)
    
    S = mathutils.Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    R = mathutils.Euler(rot).to_matrix().to_4x4()
    T = mathutils.Matrix.Translation(center)
    M = T @ R @ S
    
    for v in bm.verts:
        v.co = M @ v.co
        
    for f in bm.faces:
        f.smooth = True
        for loop in f.loops:
            loop[uv_layer].uv = uv
            
    bm.to_mesh(mesh)
    bm.free()
    
    if subsurf_levels > 0:
        sub = obj.modifiers.new("Subsurf", 'SUBSURF')
        sub.levels = subsurf_levels
        sub.render_levels = subsurf_levels
    return obj

# -------------------------------------------------------------------------
# CALF MODELING (Calf facing +Y, Up = +Z, Right = +X, Left = -X)
# In canonical Homesteader view, camera looks from (-X, +Y, +Z) towards origin!
# Head is at +Y, tilted slightly towards -X (camera).
# Rump is at -Y.
# -------------------------------------------------------------------------

# 1. Torso: Plump rounded chibi cow body
torso = make_part("Calf_Torso", (0.0, -2.0, 36.0), (28.0, 38.0, 26.0), UV_FUR, rot=(math.radians(3), 0, 0))

# Belly patch (white)
belly = make_part("Calf_Belly", (-1.0, -1.0, 27.5), (25.5, 28.0, 15.0), UV_WHITE, rot=(math.radians(2), 0, math.radians(5)))

# White flank patch on left side
flank = make_part("Calf_Flank_L", (-12.5, -4.0, 34.0), (4.5, 16.0, 14.0), UV_WHITE, rot=(0, math.radians(-10), 0))

# 2. Neck: Connects torso smoothly to head
neck = make_part("Calf_Neck", (-2.0, 13.0, 44.0), (22.0, 20.0, 22.0), UV_FUR, rot=(math.radians(25), 0, math.radians(-5)))

# 3. Head: Big adorable rounded chibi head, tilted cutely towards camera
# In the icon, the head is tilted: chin towards viewer (-X), top of head towards right (+X)
head = make_part("Calf_Head", (-5.0, 24.0, 54.0), (27.0, 26.0, 26.0), UV_FUR, rot=(math.radians(12), math.radians(-10), math.radians(-18)))

# Cream Forehead Blaze (large flowing patch on head)
blaze = make_part("Calf_Blaze", (-6.5, 26.5, 56.5), (20.0, 21.0, 24.0), UV_CREAM, rot=(math.radians(12), math.radians(-10), math.radians(-18)))

# 4. Muzzle: Soft pink snout with nostrils
muzzle = make_part("Calf_Muzzle", (-11.0, 34.5, 46.0), (18.0, 15.0, 13.0), UV_PINK, rot=(math.radians(15), math.radians(-12), math.radians(-22)))

# Nostril dimples
nos_l = make_part("Calf_Nos_L", (-15.5, 40.5, 44.8), (3.0, 2.0, 2.5), UV_NOSTRIL, rot=(0, 0, math.radians(-22)))
nos_r = make_part("Calf_Nos_R", (-9.0, 39.0, 45.5), (3.0, 2.0, 2.5), UV_NOSTRIL, rot=(0, 0, math.radians(-22)))

# 5. Eyes: Big cartoon glossy black eyes with white highlight
# Left eye (prominently facing camera)
eye_l = make_part("Calf_Eye_L", (-15.2, 30.5, 55.5), (4.0, 7.5, 7.5), UV_EYE, mat=mat_eye, rot=(math.radians(10), math.radians(-12), math.radians(-38)))
# White highlight dot on top-left of pupil
hl_l = make_part("Calf_Eye_HL_L", (-16.5, 31.0, 57.8), (2.0, 2.6, 2.6), UV_WHITE, mat=mat_hl, rot=(math.radians(10), math.radians(-12), math.radians(-38)))

# Right eye (subtle on far side)
eye_r = make_part("Calf_Eye_R", (6.0, 24.5, 57.0), (3.5, 7.0, 7.0), UV_EYE, mat=mat_eye, rot=(math.radians(10), math.radians(-12), math.radians(20)))

# 6. Ears: Cute wide ears sticking out
# Left ear (pointing out towards -X, slightly down/drooping)
ear_l = make_part("Calf_Ear_L", (-17.0, 19.5, 54.5), (17.0, 7.5, 4.8), UV_FUR, rot=(math.radians(-10), math.radians(-15), math.radians(-35)))
ear_l_in = make_part("Calf_Ear_L_In", (-17.2, 19.8, 54.2), (14.0, 6.0, 3.8), UV_INNER_EAR, rot=(math.radians(-10), math.radians(-15), math.radians(-35)))

# Right ear (pointing up/out on top-right of head)
ear_r = make_part("Calf_Ear_R", (7.0, 16.5, 65.0), (16.0, 7.5, 4.8), UV_FUR, rot=(math.radians(15), math.radians(25), math.radians(35)))
ear_r_in = make_part("Calf_Ear_R_In", (6.8, 16.8, 64.8), (13.0, 6.0, 3.8), UV_INNER_EAR, rot=(math.radians(15), math.radians(25), math.radians(35)))

# 7. Horn Buds: Cute stubby cream horns
horn_l = make_part("Calf_Horn_L", (-9.2, 23.5, 64.5), (4.5, 4.5, 8.5), UV_HORN, rot=(math.radians(20), math.radians(-25), math.radians(-25)))
horn_r = make_part("Calf_Horn_R", (1.0, 18.0, 67.0), (4.5, 4.5, 8.5), UV_HORN, rot=(math.radians(20), math.radians(15), math.radians(15)))

# 8. Four Sturdy Legs with Hooves
# Left Front Leg (closest to camera, positioned forward)
leg_lf = make_part("Calf_Leg_LF", (-9.5, 11.0, 20.0), (9.5, 9.5, 18.0), UV_FUR)
hoof_lf = make_part("Calf_Hoof_LF", (-9.5, 11.0, 5.0), (10.5, 10.5, 8.0), UV_HOOF)

# Right Front Leg (far side, positioned slightly behind)
leg_rf = make_part("Calf_Leg_RF", (8.0, 13.0, 20.0), (9.0, 9.0, 18.0), UV_FUR)
hoof_rf = make_part("Calf_Hoof_RF", (8.0, 13.0, 5.0), (10.0, 10.0, 8.0), UV_HOOF)

# Left Back Leg (rear flank)
leg_lb = make_part("Calf_Leg_LB", (-9.0, -15.0, 20.0), (9.5, 9.5, 18.0), UV_FUR)
hoof_lb = make_part("Calf_Hoof_LB", (-9.0, -15.0, 5.0), (10.5, 10.5, 8.0), UV_HOOF)

# Right Back Leg (far rear)
leg_rb = make_part("Calf_Leg_RB", (7.5, -14.0, 20.0), (9.0, 9.0, 18.0), UV_FUR)
hoof_rb = make_part("Calf_Hoof_RB", (7.5, -14.0, 5.0), (10.0, 10.0, 8.0), UV_HOOF)

# 9. Tail with Tuft
tail = make_part("Calf_Tail", (0.0, -21.0, 36.0), (4.5, 5.5, 13.0), UV_FUR, rot=(math.radians(-35), 0, 0))
tuft = make_part("Calf_Tail_Tuft", (0.0, -25.5, 31.0), (5.5, 6.0, 8.5), UV_SHADOW, rot=(math.radians(-40), 0, 0))

# -------------------------------------------------------------------------
# CAMERA SETUP (Exact Isometric 3/4 View of Homesteader Icons)
# -------------------------------------------------------------------------
target = mathutils.Vector((-2.0, 2.0, 36.0))

cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 80.0
cam_data.clip_end = 5000.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Camera looking from (-X, +Y, +Z):
# Looking down at 30 deg pitch, 45 deg yaw
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
# LIGHTING SETUP (Warm Key from upper-left, soft fill, subtle rim)
# -------------------------------------------------------------------------
# Key Light: Positioned to the upper-left of camera to give identical highlights
l_key = bpy.data.lights.new("Key", 'SUN')
l_key.energy = 4.2
l_key.color = (1.0, 0.96, 0.90)
l_k_obj = bpy.data.objects.new("Key", l_key)
scene.collection.objects.link(l_k_obj)
# Angle: ~45 deg pitch, pointing from top-left
l_k_obj.rotation_euler = (math.radians(50), math.radians(-10), math.radians(65))

# Fill Light: Soft blue-tinted fill from bottom-right to soften shadows
l_fill = bpy.data.lights.new("Fill", 'SUN')
l_fill.energy = 2.0
l_fill.color = (0.90, 0.94, 1.0)
l_f_obj = bpy.data.objects.new("Fill", l_fill)
scene.collection.objects.link(l_f_obj)
l_f_obj.rotation_euler = (math.radians(35), math.radians(20), math.radians(-115))

# Top Ambient/Rim: Highlights top of spine, head, ears
l_rim = bpy.data.lights.new("Rim", 'SUN')
l_rim.energy = 1.8
l_rim.color = (1.0, 1.0, 1.0)
l_r_obj = bpy.data.objects.new("Rim", l_rim)
scene.collection.objects.link(l_r_obj)
l_r_obj.rotation_euler = (math.radians(85), 0, 0)

# Render test image
render_path = os.path.join(RENDERS_DIR, "Identical_Calf_v2_render.png")
scene.render.filepath = render_path
bpy.ops.render.render(write_still=True)
print("SUCCESS: Rendered v2 to", render_path)

