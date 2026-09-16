import bpy
import bmesh
import math
import os

# Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene

# Palette UV Coordinate Calculator (16x16 grid)
def get_uv(col, row):
    u = (col + 0.5) / 16.0
    v = 1.0 - (row + 0.5) / 16.0
    return (u, v)

UV_HICKORY = get_uv(0, 0)       # Light Hickory wood
UV_WOOD_DARK = get_uv(1, 0)      # Medium Timber
UV_STEEL_DARK = get_uv(2, 2)     # Gunmetal
UV_STEEL_LIGHT = get_uv(0, 2)    # Silver steel edge
UV_RED_PAINT = get_uv(3, 4)      # Red axe head paint

# Create Mesh and Object
mesh = bpy.data.meshes.new("SM_Tool_Axe_Felling")
obj = bpy.data.objects.new("SM_Tool_Axe_Felling", mesh)
scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bm = bmesh.new()

# ==============================================================================
# 1. ERGONOMIC FELLING AXE HANDLE (36" / 90cm)
# Oval cross-section with sweep curve, palm swell, throat, and eye
# ==============================================================================

# Handle cross-sections along Z (height)
# (z, x_radius, y_radius, y_offset)
handle_profile = [
    (0.0,   2.2, 4.2,  3.0),   # Knob / bottom cap
    (2.0,   2.5, 4.8,  2.5),   # Palm swell flare
    (6.0,   2.0, 3.8,  1.5),   # Lower grip
    (15.0,  1.7, 3.2,  0.5),   # Mid handle
    (35.0,  1.5, 2.8, -0.5),   # Throat (slight forward curve)
    (55.0,  1.6, 3.0, -1.0),   # Upper handle sweep
    (75.0,  1.8, 3.4, -0.5),   # Below head collar
    (82.0,  1.9, 3.8,  0.5),   # Eye entry
    (90.0,  1.8, 3.6,  1.0),   # Top of eye / protruding tenon
]

segments = 8  # 8-sided faceted oval
handle_rings = []

for z, rx, ry, y_off in handle_profile:
    ring = []
    for i in range(segments):
        theta = 2.0 * math.pi * (i / segments)
        vx = rx * math.cos(theta)
        vy = y_off + ry * math.sin(theta)
        ring.append(bm.verts.new((vx, vy, z)))
    handle_rings.append(ring)

# Connect handle rings with quads
handle_faces = []
for r in range(len(handle_rings) - 1):
    r1 = handle_rings[r]
    r2 = handle_rings[r + 1]
    for i in range(segments):
        ni = (i + 1) % segments
        f = bm.faces.new([r1[i], r1[ni], r2[ni], r2[i]])
        handle_faces.append(f)

# Bottom cap and top tenon cap
f_bot = bm.faces.new(list(reversed(handle_rings[0])))
f_top = bm.faces.new(handle_rings[-1])
handle_faces.extend([f_bot, f_top])

# ==============================================================================
# 2. FORGED STEEL AXE HEAD (Red Cheeks + Polished Bit Edge)
# Poll at back (Y > 0), Eye around handle, Cheeks and Bit at front (Y < 0)
# ==============================================================================

z_head_bot = 79.0
z_head_top = 89.0
z_head_mid = 84.0

# Eye & Poll (back hammer end)
# Back poll face:
v_poll_top_l = bm.verts.new((-2.2, 7.5, z_head_top))
v_poll_top_r = bm.verts.new(( 2.2, 7.5, z_head_top))
v_poll_bot_r = bm.verts.new(( 2.0, 7.0, z_head_bot))
v_poll_bot_l = bm.verts.new((-2.0, 7.0, z_head_bot))

f_poll = bm.faces.new([v_poll_top_l, v_poll_top_r, v_poll_bot_r, v_poll_bot_l])

# Eye collar side vertices
v_eye_top_l = bm.verts.new((-2.6, 0.5, z_head_top + 0.5))
v_eye_top_r = bm.verts.new(( 2.6, 0.5, z_head_top + 0.5))
v_eye_bot_r = bm.verts.new(( 2.4, 0.5, z_head_bot - 0.5))
v_eye_bot_l = bm.verts.new((-2.4, 0.5, z_head_bot - 0.5))

# Cheeks (widened wedged body with red paint)
v_chk_top_l = bm.verts.new((-2.0, -8.0, z_head_top + 1.0))
v_chk_top_r = bm.verts.new(( 2.0, -8.0, z_head_top + 1.0))
v_chk_bot_r = bm.verts.new(( 1.8, -8.0, z_head_bot - 1.5))
v_chk_bot_l = bm.verts.new((-1.8, -8.0, z_head_bot - 1.5))

# Tapered bit shoulder (transition to blade edge)
v_shd_top_l = bm.verts.new((-1.0, -18.0, z_head_top + 2.5))
v_shd_top_r = bm.verts.new(( 1.0, -18.0, z_head_top + 2.5))
v_shd_bot_r = bm.verts.new(( 0.8, -18.0, z_head_bot - 3.5))
v_shd_bot_l = bm.verts.new((-0.8, -18.0, z_head_bot - 3.5))

# Sharp curved bit cutting edge (sharp bevel blade)
v_blade_top = bm.verts.new((0.0, -23.0, z_head_top + 4.0))
v_blade_mid = bm.verts.new((0.0, -24.5, z_head_mid))
v_blade_bot = bm.verts.new((0.0, -22.5, z_head_bot - 5.0))

# Build Head Faces
steel_faces = []
red_faces = []
blade_faces = []

steel_faces.append(f_poll)

# Poll to eye
steel_faces.append(bm.faces.new([v_poll_top_l, v_eye_top_l, v_eye_bot_l, v_poll_bot_l])) # Left eye wall
steel_faces.append(bm.faces.new([v_eye_top_r, v_poll_top_r, v_poll_bot_r, v_eye_bot_r])) # Right eye wall
steel_faces.append(bm.faces.new([v_poll_top_l, v_poll_top_r, v_eye_top_r, v_eye_top_l])) # Top poll-eye
steel_faces.append(bm.faces.new([v_eye_bot_l, v_eye_bot_r, v_poll_bot_r, v_poll_bot_l])) # Bot poll-eye

# Eye to cheeks (Red Painted Cheeks)
red_faces.append(bm.faces.new([v_eye_top_l, v_chk_top_l, v_chk_bot_l, v_eye_bot_l])) # Left cheek
red_faces.append(bm.faces.new([v_chk_top_r, v_eye_top_r, v_eye_bot_r, v_chk_bot_r])) # Right cheek
steel_faces.append(bm.faces.new([v_eye_top_l, v_eye_top_r, v_chk_top_r, v_chk_top_l])) # Top spine
steel_faces.append(bm.faces.new([v_chk_bot_l, v_chk_bot_r, v_eye_bot_r, v_eye_bot_l])) # Bot collar

# Cheeks to shoulder (Red painted extension)
red_faces.append(bm.faces.new([v_chk_top_l, v_shd_top_l, v_shd_bot_l, v_chk_bot_l])) # Left shoulder
red_faces.append(bm.faces.new([v_shd_top_r, v_chk_top_r, v_chk_bot_r, v_shd_bot_r])) # Right shoulder
steel_faces.append(bm.faces.new([v_chk_top_l, v_chk_top_r, v_shd_top_r, v_shd_top_l])) # Top spine
steel_faces.append(bm.faces.new([v_shd_bot_l, v_shd_bot_r, v_chk_bot_r, v_chk_bot_l])) # Bot bearded beard

# Shoulder to cutting edge (Polished Silver Bevel)
blade_faces.append(bm.faces.new([v_shd_top_l, v_blade_top, v_blade_mid])) # Top-left bevel
blade_faces.append(bm.faces.new([v_shd_top_l, v_blade_mid, v_shd_bot_l])) # Mid-left bevel
blade_faces.append(bm.faces.new([v_shd_bot_l, v_blade_mid, v_blade_bot])) # Bot-left bevel

blade_faces.append(bm.faces.new([v_blade_top, v_shd_top_r, v_blade_mid])) # Top-right bevel
blade_faces.append(bm.faces.new([v_blade_mid, v_shd_top_r, v_shd_bot_r])) # Mid-right bevel
blade_faces.append(bm.faces.new([v_blade_mid, v_shd_bot_r, v_blade_bot])) # Bot-right bevel

# Top & Bottom blade caps
blade_faces.append(bm.faces.new([v_shd_top_l, v_shd_top_r, v_blade_top]))
blade_faces.append(bm.faces.new([v_blade_bot, v_shd_bot_r, v_shd_bot_l]))

# ==============================================================================
# 3. UV PALETTE ASSIGNMENT
# ==============================================================================
uv_layer = bm.loops.layers.uv.new("UVMap")

for f in handle_faces:
    for loop in f.loops:
        loop[uv_layer].uv = UV_HICKORY

for f in steel_faces:
    for loop in f.loops:
        loop[uv_layer].uv = UV_STEEL_DARK

for f in red_faces:
    for loop in f.loops:
        loop[uv_layer].uv = UV_RED_PAINT

for f in blade_faces:
    for loop in f.loops:
        loop[uv_layer].uv = UV_STEEL_LIGHT

# Set Flat Shading across all faces (Homesteader Low-Poly Faceted Standard)
for f in bm.faces:
    f.smooth = False

bm.to_mesh(mesh)
bm.free()

# Ensure normals are updated
mesh.update()

# Bounding box & stats
bbox = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box] if "mathutils" in globals() else None
verts_cnt = len(mesh.vertices)
poly_cnt = len(mesh.polygons)
print(f"PILOT BLENDER AXE CREATED: {verts_cnt} vertices, {poly_cnt} polygons")

# Set up Material with T_Homesteader_Palette.png
mat = bpy.data.materials.new(name="M_Homesteader_Palette")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

bsdf = nodes.get("Principled BSDF")
bsdf.inputs["Roughness"].default_value = 0.6
bsdf.inputs["Specular IOR Level"].default_value = 0.3 if "Specular IOR Level" in bsdf.inputs else 0.5

tex_node = nodes.new(type="ShaderNodeTexImage")
palette_path = r"c:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Textures\T_Homesteader_Palette.png"
if os.path.exists(palette_path):
    tex_node.image = bpy.data.images.load(palette_path)
    tex_node.interpolation = 'Closest'  # Nearest filtering to prevent color bleed

links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
obj.data.materials.append(mat)

# ==============================================================================
# 4. RENDER PREVIEW IMAGE (Isometric 3/4 Front View)
# ==============================================================================
cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 110.0  # 110cm ortho view
cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Camera angle: 45 yaw, ~35 pitch isometric
dist = 200.0
yaw = math.radians(45.0)
pitch = math.radians(35.264)

cam_x = dist * math.cos(pitch) * math.sin(yaw)
cam_y = -dist * math.cos(pitch) * math.cos(yaw)
cam_z = 45.0 + dist * math.sin(pitch)

cam_obj.location = (cam_x, cam_y, cam_z)
cam_obj.rotation_euler = (math.radians(54.736), 0, math.radians(45.0))

# Lights
light_key = bpy.data.lights.new(name="KeyLight", type='SUN')
light_key.energy = 4.0
light_key_obj = bpy.data.objects.new("KeyLight", light_key)
scene.collection.objects.link(light_key_obj)
light_key_obj.rotation_euler = (math.radians(45.0), math.radians(15.0), math.radians(-30.0))

light_fill = bpy.data.lights.new(name="FillLight", type='SUN')
light_fill.energy = 1.5
light_fill_obj = bpy.data.objects.new("FillLight", light_fill)
scene.collection.objects.link(light_fill_obj)
light_fill_obj.rotation_euler = (math.radians(60.0), math.radians(-30.0), math.radians(120.0))

# Output render settings
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'

render_out = r"c:\Users\casey\Desktop\Homesteader\HUD\scratch\pilot_blender_axe_render.png"
scene.render.filepath = render_out

bpy.ops.render.render(write_still=True)
print(f"RENDER SAVED TO: {render_out}")

# Export OBJ
obj_out = r"c:\Users\casey\Desktop\Homesteader\HUD\scratch\SM_Tool_Axe_Felling_Pilot.obj"
bpy.ops.wm.obj_export(filepath=obj_out, export_materials=True, export_uv=True, export_normals=True)
print(f"OBJ EXPORTED TO: {obj_out}")
