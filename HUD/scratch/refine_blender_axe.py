"""
Precise camera and geometry tuning script for SM_Tool_Axe:
Matches tool_axe.png identically.
"""
import bpy
import bmesh
import math
import os

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True

# Palette UV Coordinates (512x512, 16x16 grid)
UV_WOOD_MAIN     = ((2 + 0.5)/16.0, 1.0 - (1 + 0.5)/16.0)   # RGB=(140, 95, 60) Warm rich brown
UV_WOOD_DARK     = ((1 + 0.5)/16.0, 1.0 - (1 + 0.5)/16.0)   # RGB=(88, 57, 39) Dark wood shadow
UV_WOOD_LIGHT    = ((0 + 0.5)/16.0, 1.0 - (0 + 0.5)/16.0)   # RGB=(222, 184, 135) Wedge wood
UV_HOLE_BLACK    = ((5 + 0.5)/16.0, 1.0 - (15 + 0.5)/16.0)  # RGB=(0, 0, 0) Black lanyard hole
UV_STEEL_LIGHT   = ((0 + 0.5)/16.0, 1.0 - (3 + 0.5)/16.0)   # RGB=(170, 175, 180) Brushed steel collar
UV_STEEL_DARK    = ((2 + 0.5)/16.0, 1.0 - (2 + 0.5)/16.0)   # RGB=(71, 85, 105) Recessed forged cheek
UV_STEEL_POLISHED= ((0 + 0.5)/16.0, 1.0 - (2 + 0.5)/16.0)   # RGB=(203, 213, 225) Polished cutting bevel

# Material
palette_path = r"c:\Users\casey\Desktop\Homesteader\HUD\assets\textures\palettes\T_Homesteader_Palette.png"
mat = bpy.data.materials.new(name="M_Homesteader_Palette")
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

node_output = nodes.new(type='ShaderNodeOutputMaterial')
node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
node_bsdf.inputs['Roughness'].default_value = 0.4
if 'Specular IOR Level' in node_bsdf.inputs:
    node_bsdf.inputs['Specular IOR Level'].default_value = 0.5
elif 'Specular' in node_bsdf.inputs:
    node_bsdf.inputs['Specular'].default_value = 0.5

node_tex = nodes.new(type='ShaderNodeTexImage')
if os.path.exists(palette_path):
    img = bpy.data.images.load(palette_path)
    img.colorspace_settings.name = 'sRGB'
    node_tex.image = img
    node_tex.interpolation = 'Closest'

links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])

# Mesh & BM
mesh = bpy.data.meshes.new("SM_Tool_Axe")
obj = bpy.data.objects.new("SM_Tool_Axe", mesh)
scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")

def add_face(bm_verts, uv_coord):
    f = bm.faces.new(bm_verts)
    f.smooth = False
    for loop in f.loops:
        loop[uv_layer].uv = uv_coord
    return f

# ----------------------------------------------------
# 1. HANDLE (Authentic S-curve hatchet grip, 30cm)
# Proportions match icon: stocky, ergonomic, rich wood
# ----------------------------------------------------
handle_levels = [
    # 0: Butt base with flared heel
    (0.0,  -0.8, 1.25, 2.6, 1.5),
    # 1: Fawn-foot heel swell
    (1.5,  -0.6, 1.35, 2.8, 1.6),
    # 2: Lanyard hole level
    (3.5,  -0.2, 1.2, 2.2, 1.5),
    # 3: Butt transition
    (5.5,   0.3, 1.1, 1.7, 1.4),
    # 4: Lower grip sweep (forward)
    (9.5,   1.0, 1.05, 1.5, 1.4),
    # 5: Mid handle reverse sweep (backward)
    (14.5,  0.2, 1.0, 1.5, 1.3),
    (18.5, -0.5, 1.0, 1.55, 1.3),
    # 6: Throat entering collar (sweeping forward)
    (22.5,  0.3, 1.05, 1.65, 1.4),
    # 7: Inside eye collar
    (24.5,  0.5, 1.15, 1.85, 1.55),
    (28.0,  0.5, 1.15, 1.85, 1.55),
    # 8: Protruding eye top (wedge)
    (29.2,  0.5, 1.1, 1.75, 1.45),
]

def make_ring(z, y_c, rx, ry_b, ry_f):
    d = 0.7071
    pts = [
        (0.0,        y_c - ry_b,        z), # 0: Back
        (rx * d,     y_c - ry_b * d,    z), # 1: Back-Right
        (rx,         y_c,               z), # 2: Right
        (rx * d,     y_c + ry_f * d,    z), # 3: Front-Right
        (0.0,        y_c + ry_f,        z), # 4: Front
        (-rx * d,    y_c + ry_f * d,    z), # 5: Front-Left
        (-rx,        y_c,               z), # 6: Left
        (-rx * d,    y_c - ry_b * d,    z), # 7: Back-Left
    ]
    return [bm.verts.new(p) for p in pts]

rings = [make_ring(*lvl) for lvl in handle_levels]

# Loft handle
for i in range(len(rings) - 1):
    rA = rings[i]
    rB = rings[i+1]
    for k in range(8):
        kn = (k + 1) % 8
        uv = UV_WOOD_DARK if k in [0, 1, 7] else UV_WOOD_MAIN
        add_face([rA[k], rA[kn], rB[kn], rB[k]], uv)

# Handle bottom cap
add_face([rings[0][0], rings[0][7], rings[0][6], rings[0][5], rings[0][4], rings[0][3], rings[0][2], rings[0][1]], UV_WOOD_DARK)

# Handle top wedge face
add_face([rings[-1][0], rings[-1][1], rings[-1][2], rings[-1][3], rings[-1][4], rings[-1][5], rings[-1][6], rings[-1][7]], UV_WOOD_LIGHT)

# Lanyard hole cutout faces on Left and Right
for side, sign in [('R', 1.0), ('L', -1.0)]:
    h_pts = []
    for a in range(6):
        ang = a * math.pi / 3.0
        py = -0.2 + 0.38 * math.cos(ang)
        pz = 3.5 + 0.38 * math.sin(ang)
        h_pts.append(bm.verts.new((sign * 1.22, py, pz)))
    if sign > 0:
        h_pts.reverse()
    add_face(h_pts, UV_HOLE_BLACK)

# ----------------------------------------------------
# 2. AXE HEAD (Authentic Camp Hatchet)
# Proportions match icon: broad cutting edge, distinct beard,
# recessed dark forged cheek inset, flat hammer poll.
# ----------------------------------------------------
# Poll Face (Y = -5.5)
pv_tr = bm.verts.new(( 1.1, -5.5, 28.0))
pv_tl = bm.verts.new((-1.1, -5.5, 28.0))
pv_br = bm.verts.new(( 1.1, -5.5, 24.2))
pv_bl = bm.verts.new((-1.1, -5.5, 24.2))
add_face([pv_tr, pv_tl, pv_bl, pv_br], UV_STEEL_LIGHT)

# Collar Back Junction (Y = -1.5)
cb_tr = bm.verts.new(( 1.45, -1.5, 28.6))
cb_tl = bm.verts.new((-1.45, -1.5, 28.6))
cb_br = bm.verts.new(( 1.45, -1.5, 23.5))
cb_bl = bm.verts.new((-1.45, -1.5, 23.5))

# Poll quads
add_face([cb_tr, cb_tl, pv_tl, pv_tr], UV_STEEL_LIGHT) # Top
add_face([pv_br, pv_bl, cb_bl, cb_br], UV_STEEL_LIGHT) # Bot
add_face([pv_tr, cb_tr, cb_br, pv_br], UV_STEEL_LIGHT) # Right
add_face([cb_tl, pv_tl, pv_bl, cb_bl], UV_STEEL_LIGHT) # Left

# Collar Front Junction (Y = 2.5)
cf_tr = bm.verts.new(( 1.4, 2.5, 28.8))
cf_tl = bm.verts.new((-1.4, 2.5, 28.8))
cf_br = bm.verts.new(( 1.4, 2.5, 23.2))
cf_bl = bm.verts.new((-1.4, 2.5, 23.2))

# Collar sides
add_face([cb_tr, cf_tr, cf_tl, cb_tl], UV_STEEL_LIGHT) # Top
add_face([cb_bl, cf_bl, cf_br, cb_br], UV_STEEL_LIGHT) # Bot
add_face([cb_br, cf_br, cf_tr, cb_tr], UV_STEEL_LIGHT) # Right
add_face([cf_bl, cb_bl, cb_tl, cf_tl], UV_STEEL_LIGHT) # Left

# Cheek Mid Ridge (Y = 6.8)
cm_top_r = bm.verts.new(( 0.75, 6.8, 29.5))
cm_top_l = bm.verts.new((-0.75, 6.8, 29.5))
cm_mid_r = bm.verts.new(( 0.58, 7.0, 24.0))
cm_mid_l = bm.verts.new((-0.58, 7.0, 24.0))
cm_brd_r = bm.verts.new(( 0.70, 6.4, 17.5)) # Dropped beard
cm_brd_l = bm.verts.new((-0.70, 6.4, 17.5))

# Recessed Dark Forged Cheek Panels
add_face([cf_tr, cm_top_r, cm_mid_r, cf_br], UV_STEEL_DARK)
add_face([cf_br, cm_mid_r, cm_brd_r], UV_STEEL_DARK)

add_face([cm_top_l, cf_tl, cf_bl, cm_mid_l], UV_STEEL_DARK)
add_face([cm_mid_l, cf_bl, cm_brd_l], UV_STEEL_DARK)

# Cheek Top & Under-beard transitions
add_face([cf_tr, cf_tl, cm_top_l, cm_top_r], UV_STEEL_LIGHT) # Top slope
add_face([cf_bl, cf_br, cm_brd_r, cm_brd_l], UV_STEEL_LIGHT) # Beard underside

# Polished Bevel Ridge (Y = 9.8)
bv_top_r = bm.verts.new(( 0.35, 10.0, 30.8))
bv_top_l = bm.verts.new((-0.35, 10.0, 30.8))
bv_mid_r = bm.verts.new(( 0.28, 10.6, 24.2))
bv_mid_l = bm.verts.new((-0.28, 10.6, 24.2))
bv_brd_r = bm.verts.new(( 0.32,  8.2, 17.2))
bv_brd_l = bm.verts.new((-0.32,  8.2, 17.2))

# Forward cheek to Bevel ridge
add_face([cm_top_r, bv_top_r, bv_mid_r, cm_mid_r], UV_STEEL_LIGHT)
add_face([cm_mid_r, bv_mid_r, bv_brd_r, cm_brd_r], UV_STEEL_LIGHT)

add_face([bv_top_l, cm_top_l, cm_mid_l, bv_mid_l], UV_STEEL_LIGHT)
add_face([bv_mid_l, cm_mid_l, cm_brd_l, bv_brd_l], UV_STEEL_LIGHT)

# Top & Beard spine
add_face([cm_top_r, cm_top_l, bv_top_l, bv_top_r], UV_STEEL_LIGHT)
add_face([bv_brd_r, bv_brd_l, cm_brd_l, cm_brd_r], UV_STEEL_LIGHT)

# Crescent Cutting Edge (X = 0, Bright Polished Bevel!)
ed_top = bm.verts.new((0.0, 11.4, 31.5)) # Top toe
ed_mid = bm.verts.new((0.0, 12.4, 24.5)) # Center crest
ed_brd = bm.verts.new((0.0,  9.2, 16.8)) # Bottom beard tip

# Right Bevel Facets
add_face([bv_top_r, ed_top, ed_mid, bv_mid_r], UV_STEEL_POLISHED)
add_face([bv_mid_r, ed_mid, ed_brd, bv_brd_r], UV_STEEL_POLISHED)

# Left Bevel Facets
add_face([ed_top, bv_top_l, bv_mid_l, ed_mid], UV_STEEL_POLISHED)
add_face([ed_mid, bv_mid_l, bv_brd_l, ed_brd], UV_STEEL_POLISHED)

# Top and Bottom closure
add_face([bv_top_r, bv_top_l, ed_top], UV_STEEL_POLISHED)
add_face([bv_brd_l, bv_brd_r, ed_brd], UV_STEEL_POLISHED)

# Finalize BMesh
bm.to_mesh(mesh)
bm.free()
mesh.materials.append(mat)
mesh.update()

# Center origin to bounds
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
obj.location = (0, 0, 0)
bpy.context.view_layer.update()

print(f"HATCHET CREATED: {len(mesh.vertices)} verts, {len(mesh.polygons)} polys")

# ==========================================
# CAMERA & LIGHTING (Matching tool_axe.png)
# ==========================================
# Look directly at the right cheek (+X side), with slight elevation and roll
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 32.0  # Perfect tight framing
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Camera viewing from +X side, elevated and pitched:
dist = 40.0
elev = math.radians(20.0) # Look slightly down onto the top bevel/poll
yaw  = math.radians(16.0) # Angle slightly toward the cutting edge face

cam_x = dist * math.cos(elev) * math.cos(yaw)
cam_y = dist * math.cos(elev) * math.sin(yaw)
cam_z = dist * math.sin(elev)

cam_obj.location = (cam_x, cam_y, cam_z)

# Target camera to object center with roll
# Using track to constraint or manual euler
# Point at (0, 0, 0)
direction = -cam_obj.location.normalized()
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

# Now roll camera around viewing axis to tilt the axe diagonally like in the icon (-45 degrees)
# In local camera space, roll is Z rotation
cam_obj.rotation_euler.rotate_axis('Z', math.radians(44.0))

# Lights
# Front key light illuminating the cheek brilliantly:
l_key = bpy.data.lights.new("KeyLight", type='SUN')
l_key.energy = 4.2
l_key.color = (1.0, 0.98, 0.95)
l_key_obj = bpy.data.objects.new("KeyLight", l_key)
scene.collection.objects.link(l_key_obj)
l_key_obj.location = cam_obj.location
l_key_obj.rotation_euler = cam_obj.rotation_euler
l_key_obj.rotation_euler.rotate_axis('X', math.radians(-25.0))
l_key_obj.rotation_euler.rotate_axis('Y', math.radians(-20.0))

# Fill Light:
l_fill = bpy.data.lights.new("FillLight", type='SUN')
l_fill.energy = 2.0
l_fill.color = (0.85, 0.90, 1.0)
l_fill_obj = bpy.data.objects.new("FillLight", l_fill)
scene.collection.objects.link(l_fill_obj)
l_fill_obj.rotation_euler = (math.radians(30), math.radians(60), math.radians(-120))

# Top rim light to catch eye wedge and top of poll:
l_rim = bpy.data.lights.new("RimLight", type='SUN')
l_rim.energy = 3.0
l_rim.color = (1.0, 1.0, 1.0)
l_rim_obj = bpy.data.objects.new("RimLight", l_rim)
scene.collection.objects.link(l_rim_obj)
l_rim_obj.rotation_euler = (math.radians(80), 0, 0)

# Render preview
render_out = r"c:\Users\casey\Desktop\Homesteader\HUD\scratch\identical_blender_axe_render.png"
scene.render.filepath = render_out
bpy.ops.render.render(write_still=True)
print(f"RENDER SAVED TO: {render_out}")

# Reset origin to base for canonical export (Zmin = 0, pivot at butt)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
# Find min Z in vertices to align pivot to Z=0
min_z = min(v.co.z for v in mesh.vertices)
for v in mesh.vertices:
    v.co.z -= min_z
mesh.update()

output_obj = r"c:\Users\casey\Desktop\Homesteader\HUD\scratch\SM_Tool_Axe_Identical.obj"
bpy.ops.wm.obj_export(
    filepath=output_obj,
    export_selected_objects=True,
    export_materials=True,
    export_uv=True,
    export_normals=True,
)
print(f"OBJ EXPORTED TO: {output_obj}")
