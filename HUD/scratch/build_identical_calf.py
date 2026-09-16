import bpy
import bmesh
import math
import mathutils
import os

ICON_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test"
TEX_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\textures\animals"
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'

tex_path = os.path.join(TEX_DIR, "T_Baby_Calf_BaseColor.png")

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

# Material Setup
mat = bpy.data.materials.new(name="M_Baby_Calf")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

node_out = nodes.new('ShaderNodeOutputMaterial')
node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
node_bsdf.inputs['Roughness'].default_value = 0.5
if 'Specular IOR Level' in node_bsdf.inputs:
    node_bsdf.inputs['Specular IOR Level'].default_value = 0.4
elif 'Specular' in node_bsdf.inputs:
    node_bsdf.inputs['Specular'].default_value = 0.4

node_tex = nodes.new('ShaderNodeTexImage')
img = bpy.data.images.load(tex_path)
img.colorspace_settings.name = 'sRGB'
node_tex.image = img
node_tex.interpolation = 'Linear'

links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])

# Eye Material (extra glossy specular reflection)
mat_eye = bpy.data.materials.new(name="M_Calf_Eye")
mat_eye.use_nodes = True
ne = mat_eye.node_tree.nodes
le = mat_eye.node_tree.links
ne.clear()
out_e = ne.new('ShaderNodeOutputMaterial')
bsdf_e = ne.new('ShaderNodeBsdfPrincipled')
bsdf_e.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)
bsdf_e.inputs['Roughness'].default_value = 0.05
if 'Specular IOR Level' in bsdf_e.inputs:
    bsdf_e.inputs['Specular IOR Level'].default_value = 1.0
elif 'Specular' in bsdf_e.inputs:
    bsdf_e.inputs['Specular'].default_value = 1.0
le.new(bsdf_e.outputs['BSDF'], out_e.inputs['Surface'])

# Highlight Material (pure glowing white)
mat_white = bpy.data.materials.new(name="M_Calf_White")
mat_white.use_nodes = True
nw = mat_white.node_tree.nodes
lw = mat_white.node_tree.links
nw.clear()
out_w = nw.new('ShaderNodeOutputMaterial')
bsdf_w = nw.new('ShaderNodeBsdfPrincipled')
bsdf_w.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
bsdf_w.inputs['Roughness'].default_value = 0.1
if 'Emission Color' in bsdf_w.inputs:
    bsdf_w.inputs['Emission Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf_w.inputs['Emission Strength'].default_value = 0.5
lw.new(bsdf_w.outputs['BSDF'], out_w.inputs['Surface'])

# -------------------------------------------------------------------------
# 3. BUILD GEOMETRY TO EXACTLY MATCH CANONICAL ICON
# -------------------------------------------------------------------------
# Icon orientation:
# Calf is facing +X / -Y (front-left from isometric view).
# Let's orient world coordinates so Calf is aligned along X:
# Head at +X, Rump at -X, Left flank towards -Y, Right flank towards +Y, Z is Up.
# From camera looking from (+X, -Y, +Z), we see:
# Head (front-left), Left flank, front-left leg, back-left leg, ears, horns, left eye!
# This matches the icon view!

def create_subdivided_box(name, center, size, uv_coord, mat_ref=mat, rot_euler=(0,0,0)):
    # Box with subsurf produces beautiful organic rounded cartoon forms
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat_ref)
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    bmesh.ops.create_cube(bm, size=1.0)
    
    # Scale and translate
    S = mathutils.Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    R = mathutils.Euler(rot_euler).to_matrix().to_4x4()
    T = mathutils.Matrix.Translation(center)
    M = T @ R @ S
    
    for v in bm.verts:
        v.co = M @ v.co
        
    for f in bm.faces:
        f.smooth = True
        for loop in f.loops:
            loop[uv_layer].uv = uv_coord
            
    bm.to_mesh(mesh)
    bm.free()
    
    # Add Subsurf
    sub = obj.modifiers.new("Subsurf", 'SUBSURF')
    sub.levels = 2
    sub.render_levels = 2
    return obj

# 1. Torso: Chubby rounded barrel
torso = create_subdivided_box("Calf_Torso", (-3.0, 0.0, 36.0), (38.0, 26.0, 24.0), UV_FUR, rot_euler=(0, math.radians(-3), 0))

# Belly patch (white)
belly = create_subdivided_box("Calf_Belly", (-2.0, -1.0, 28.0), (28.0, 23.5, 14.0), UV_WHITE, rot_euler=(0, math.radians(-2), math.radians(-5)))

# 2. Neck: Smooth transition from shoulder to head
neck = create_subdivided_box("Calf_Neck", (12.0, -2.0, 43.0), (18.0, 20.0, 20.0), UV_FUR, rot_euler=(0, math.radians(-25), math.radians(-10)))

# 3. Head: Adorable rounded chibi head, tilted cutely
head = create_subdivided_box("Calf_Head", (22.0, -5.0, 52.0), (25.0, 25.0, 25.0), UV_FUR, rot_euler=(math.radians(8), math.radians(-12), math.radians(-20)))

# Cream Forehead Blaze
blaze = create_subdivided_box("Calf_Blaze", (24.5, -6.5, 54.5), (20.0, 18.0, 22.0), UV_CREAM, rot_euler=(math.radians(8), math.radians(-12), math.radians(-20)))

# 4. Muzzle: Soft pink snout with nostrils
muzzle = create_subdivided_box("Calf_Muzzle", (32.0, -11.0, 45.0), (14.0, 17.0, 12.0), UV_PINK, rot_euler=(math.radians(8), math.radians(-10), math.radians(-25)))

# Nostrils
nos_l = create_subdivided_box("Calf_Nos_L", (37.5, -15.5, 43.8), (2.0, 3.5, 2.5), UV_NOSTRIL, rot_euler=(0, 0, math.radians(-25)))
nos_r = create_subdivided_box("Calf_Nos_R", (36.0, -9.0, 44.5), (2.0, 3.5, 2.5), UV_NOSTRIL, rot_euler=(0, 0, math.radians(-25)))

# 5. Eyes: Big cartoon glossy black eyes with white highlight
# Left eye (facing camera)
eye_l = create_subdivided_box("Calf_Eye_L", (28.2, -15.2, 54.0), (6.5, 3.5, 6.5), UV_EYE, mat_ref=mat_eye, rot_euler=(math.radians(5), math.radians(-10), math.radians(-40)))
# White highlight dot on top-left of pupil
hl_l = create_subdivided_box("Calf_Eye_HL_L", (28.8, -16.5, 56.2), (2.5, 1.8, 2.5), UV_WHITE, mat_ref=mat_white, rot_euler=(math.radians(5), math.radians(-10), math.radians(-40)))

# Right eye (subtle on far side)
eye_r = create_subdivided_box("Calf_Eye_R", (22.5, 5.8, 55.5), (6.0, 3.0, 6.0), UV_EYE, mat_ref=mat_eye, rot_euler=(math.radians(5), math.radians(-10), math.radians(20)))

# 6. Ears: Cute wide ears sticking out
# Left ear (facing camera / side)
ear_l = create_subdivided_box("Calf_Ear_L", (18.0, -16.5, 53.0), (7.0, 16.0, 4.5), UV_FUR, rot_euler=(math.radians(15), math.radians(10), math.radians(-35)))
ear_l_in = create_subdivided_box("Calf_Ear_L_In", (18.2, -16.8, 52.8), (5.5, 13.0, 3.5), UV_INNER_EAR, rot_euler=(math.radians(15), math.radians(10), math.radians(-35)))

# Right ear (top/back ear)
ear_r = create_subdivided_box("Calf_Ear_R", (15.0, 6.5, 63.0), (7.0, 15.0, 4.5), UV_FUR, rot_euler=(math.radians(-15), math.radians(-15), math.radians(35)))
ear_r_in = create_subdivided_box("Calf_Ear_R_In", (15.5, 6.2, 62.8), (5.5, 12.0, 3.5), UV_INNER_EAR, rot_euler=(math.radians(-15), math.radians(-15), math.radians(35)))

# 7. Horn Buds: Cute stubby cream horns
horn_l = create_subdivided_box("Calf_Horn_L", (21.5, -9.0, 62.5), (4.0, 4.0, 8.0), UV_HORN, rot_euler=(math.radians(20), math.radians(15), math.radians(-25)))
horn_r = create_subdivided_box("Calf_Horn_R", (16.5, 1.0, 65.0), (4.0, 4.0, 8.0), UV_HORN, rot_euler=(math.radians(-10), math.radians(15), math.radians(15)))

# 8. Four Sturdy Legs with Hooves
# Leg Left Front (closest to camera)
leg_lf = create_subdivided_box("Calf_Leg_LF", (10.0, -9.0, 20.0), (9.0, 9.0, 18.0), UV_FUR)
hoof_lf = create_subdivided_box("Calf_Hoof_LF", (10.0, -9.0, 5.0), (10.0, 10.0, 8.0), UV_HOOF)

# Leg Right Front (far side)
leg_rf = create_subdivided_box("Calf_Leg_RF", (12.0, 8.0, 20.0), (8.5, 8.5, 18.0), UV_FUR)
hoof_rf = create_subdivided_box("Calf_Hoof_RF", (12.0, 8.0, 5.0), (9.5, 9.5, 8.0), UV_HOOF)

# Leg Left Back
leg_lb = create_subdivided_box("Calf_Leg_LB", (-16.0, -8.5, 20.0), (9.0, 9.0, 18.0), UV_FUR)
hoof_lb = create_subdivided_box("Calf_Hoof_LB", (-16.0, -8.5, 5.0), (10.0, 10.0, 8.0), UV_HOOF)

# Leg Right Back
leg_rb = create_subdivided_box("Calf_Leg_RB", (-15.0, 7.5, 20.0), (8.5, 8.5, 18.0), UV_FUR)
hoof_rb = create_subdivided_box("Calf_Hoof_RB", (-15.0, 7.5, 5.0), (9.5, 9.5, 8.0), UV_HOOF)

# 9. Tail with Tuft
tail = create_subdivided_box("Calf_Tail", (-22.0, 0.0, 36.0), (5.0, 4.0, 12.0), UV_FUR, rot_euler=(0, math.radians(35), 0))
tuft = create_subdivided_box("Calf_Tail_Tuft", (-26.5, 0.0, 31.0), (5.5, 5.0, 8.0), UV_SHADOW, rot_euler=(0, math.radians(40), 0))

# -------------------------------------------------------------------------
# 4. CAMERA SETUP (Matching Canonical Homesteader Isometric Icon View)
# -------------------------------------------------------------------------
# Target center of animal
target = mathutils.Vector((2.0, -2.0, 35.0))

cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 82.0
cam_data.clip_end = 5000.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Camera viewing angle:
# Standard isometric: Yaw 45 deg, Pitch ~35.264 deg
dist = 500.0
yaw = math.radians(48.0)    # Slight angle to show front-left
pitch = math.radians(30.0)  # Downward tilt

cam_x = target.x + dist * math.cos(pitch) * math.cos(yaw)
cam_y = target.y - dist * math.cos(pitch) * math.sin(yaw)
cam_z = target.z + dist * math.sin(pitch)

cam_obj.location = (cam_x, cam_y, cam_z)
dir_vec = -(cam_obj.location - target).normalized()
cam_obj.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()

# -------------------------------------------------------------------------
# 5. 3-POINT LIGHTING SETUP (Studio Warmth matching Icon Aesthetic)
# -------------------------------------------------------------------------
# Key Light: Top-Left warm light
l_key = bpy.data.lights.new("Key", 'SUN')
l_key.energy = 4.8
l_key.color = (1.0, 0.98, 0.94)
l_k_obj = bpy.data.objects.new("Key", l_key)
scene.collection.objects.link(l_k_obj)
l_k_obj.rotation_euler = (math.radians(45), math.radians(15), math.radians(-30))

# Soft Fill Light: Bottom-Right cool tint to lift shadows (NO harsh black shadows!)
l_fill = bpy.data.lights.new("Fill", 'SUN')
l_fill.energy = 2.4
l_fill.color = (0.88, 0.92, 1.0)
l_f_obj = bpy.data.objects.new("Fill", l_fill)
scene.collection.objects.link(l_f_obj)
l_f_obj.rotation_euler = (math.radians(35), math.radians(-20), math.radians(140))

# Rim / Top Light: To give rim shine on back, head, ears
l_rim = bpy.data.lights.new("Rim", 'SUN')
l_rim.energy = 2.2
l_rim.color = (1.0, 1.0, 1.0)
l_r_obj = bpy.data.objects.new("Rim", l_rim)
scene.collection.objects.link(l_r_obj)
l_r_obj.rotation_euler = (math.radians(70), math.radians(0), math.radians(-80))

# Render test image
render_path = os.path.join(RENDERS_DIR, "Identical_Calf_v1_render.png")
scene.render.filepath = render_path
bpy.ops.render.render(write_still=True)
print("SUCCESS: Rendered to", render_path)
