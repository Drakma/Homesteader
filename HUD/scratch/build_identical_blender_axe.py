"""
Headless Blender script to build an IDENTICAL 3D low-poly Axe model matching tool_axe.png:
- Authentic Scandinavian / Camp Hatchet proportions (head to handle ratio ~ 1:2.5)
- Distinct S-curved rich brown wooden handle with flared fawn-foot butt and lanyard hole
- Forged steel head with:
  * Flat hammer poll at the back
  * Light brushed steel collar surrounding the eye
  * Dark slate forged carbon steel recessed cheek panel
  * Downward flared beard
  * 3-facet curved crescent cutting edge with bright polished bevel
  * Wooden handle protrusion with eye wedge at the top
- Palette UV mapping referencing T_Homesteader_Palette.png
- High fidelity isometric render matching tool_axe.png framing and lighting
"""

import bpy
import math
import os
import sys

# Clear existing scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Scene setup
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True

# Colors in T_Homesteader_Palette.png (512x512, 16x16 grid)
# u = (col + 0.5) / 16.0, v = 1.0 - (row + 0.5) / 16.0
UV_WOOD_MAIN     = ((2 + 0.5)/16.0, 1.0 - (1 + 0.5)/16.0)   # RGB=(140, 95, 60) Rich medium brown
UV_WOOD_DARK     = ((1 + 0.5)/16.0, 1.0 - (1 + 0.5)/16.0)   # RGB=(88, 57, 39) Dark wood facet/shadow
UV_WOOD_WEDGE    = ((0 + 0.5)/16.0, 1.0 - (0 + 0.5)/16.0)   # RGB=(222, 184, 135) Light wood wedge
UV_HOLE_BLACK    = ((5 + 0.5)/16.0, 1.0 - (15 + 0.5)/16.0)  # RGB=(0, 0, 0) Lanyard hole interior
UV_STEEL_LIGHT   = ((0 + 0.5)/16.0, 1.0 - (3 + 0.5)/16.0)   # RGB=(170, 175, 180) Steel collar / poll
UV_STEEL_DARK    = ((2 + 0.5)/16.0, 1.0 - (2 + 0.5)/16.0)   # RGB=(71, 85, 105) Dark forged cheek inset
UV_STEEL_POLISHED= ((0 + 0.5)/16.0, 1.0 - (2 + 0.5)/16.0)   # RGB=(203, 213, 225) Bright polished edge bevel

# Create Material referencing T_Homesteader_Palette.png
palette_path = r"c:\Users\casey\Desktop\Homesteader\HUD\assets\textures\palettes\T_Homesteader_Palette.png"
mat = bpy.data.materials.new(name="M_Homesteader_Palette")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

node_output = nodes.new(type='ShaderNodeOutputMaterial')
node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
node_bsdf.inputs['Roughness'].default_value = 0.5
node_bsdf.inputs['Specular IOR Level' if 'Specular IOR Level' in node_bsdf.inputs else 'Specular'].default_value = 0.4

node_tex = nodes.new(type='ShaderNodeTexImage')
if os.path.exists(palette_path):
    img = bpy.data.images.load(palette_path)
    img.colorspace_settings.name = 'sRGB'
    node_tex.image = img
    node_tex.interpolation = 'Closest'  # Sharp pixel mapping, no bleeding

links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])

# ==========================================
# GEOMETRY GENERATION
# ==========================================
mesh = bpy.data.meshes.new("SM_Tool_Axe_Mesh")
obj = bpy.data.objects.new("SM_Tool_Axe", mesh)
bpy.context.collection.objects.link(obj)

verts = []
faces = []
face_uvs = []

def add_polygon(poly_verts, uv_coord):
    """poly_verts: list of 3D (x,y,z) tuples in counter-clockwise order."""
    base_idx = len(verts)
    for v in poly_verts:
        verts.append(v)
    face_idx = [base_idx + i for i in range(len(poly_verts))]
    faces.append(face_idx)
    face_uvs.append([uv_coord] * len(poly_verts))

def add_quad(v0, v1, v2, v3, uv_coord):
    add_polygon([v0, v1, v2, v3], uv_coord)

def add_tri(v0, v1, v2, uv_coord):
    add_polygon([v0, v1, v2], uv_coord)

# ----------------------------------------------------
# 1. HANDLE BUILDER (Faceted octagonal cross sections)
# ----------------------------------------------------
# S-curve hatchet handle profile
# levels: (z, y_center, radius_x, radius_y_back, radius_y_front)
handle_levels = [
    # Butt / Fawn-foot heel
    (0.0,  -0.5, 0.9, 1.8, 1.4),   # 0: bottom cap
    (1.5,  -0.3, 1.0, 1.9, 1.5),   # 1: lower swell
    (3.2,   0.0, 0.9, 1.6, 1.3),   # 2: butt transition (lanyard hole zone)
    (5.0,   0.3, 0.85, 1.4, 1.2),  # 3: lanyard hole top
    (9.0,   0.8, 0.8, 1.3, 1.2),   # 4: lower grip (curves forward)
    (15.0,  0.4, 0.75, 1.25, 1.15),# 5: mid lower
    (21.0, -0.4, 0.75, 1.3, 1.15), # 6: mid swell (curves backward)
    (27.0, -0.2, 0.75, 1.35, 1.2), # 7: upper body
    (31.5,  0.3, 0.8, 1.5, 1.3),   # 8: neck entering axe eye
    (34.0,  0.4, 0.85, 1.6, 1.4),  # 9: lower eye
    (38.0,  0.4, 0.85, 1.6, 1.4),  # 10: upper eye
    (39.2,  0.4, 0.8, 1.5, 1.3),   # 11: protruding eye tip (wedge)
]

def make_oct_ring(z, y_c, rx, ry_b, ry_f):
    """Generate 8 vertices for an octagonal cross-section."""
    # 0: Back, 1: Back-Right, 2: Right, 3: Front-Right, 4: Front, 5: Front-Left, 6: Left, 7: Back-Left
    diag = 0.7071
    return [
        (0.0,          y_c - ry_b,            z), # Back
        (rx * diag,    y_c - ry_b * diag,     z), # Back-Right
        (rx,           y_c,                   z), # Right
        (rx * diag,    y_c + ry_f * diag,     z), # Front-Right
        (0.0,          y_c + ry_f,            z), # Front
        (-rx * diag,   y_c + ry_f * diag,     z), # Front-Left
        (-rx,          y_c,                   z), # Left
        (-rx * diag,   y_c - ry_b * diag,     z), # Back-Left
    ]

ring_verts = [make_oct_ring(*lvl) for lvl in handle_levels]

# Loft rings
for i in range(len(handle_levels) - 1):
    rA = ring_verts[i]
    rB = ring_verts[i+1]
    for k in range(8):
        k_next = (k + 1) % 8
        v0 = rA[k]
        v1 = rA[k_next]
        v2 = rB[k_next]
        v3 = rB[k]
        # Assign main wood vs darker wood facets for rich woodgrain appearance
        uv = UV_WOOD_DARK if (k in [0, 1, 7]) else UV_WOOD_MAIN
        add_quad(v0, v1, v2, v3, uv)

# Bottom cap
b_cap = ring_verts[0]
add_polygon([b_cap[0], b_cap[7], b_cap[6], b_cap[5], b_cap[4], b_cap[3], b_cap[2], b_cap[1]], UV_WOOD_DARK)

# Top cap (wooden wedge in eye)
t_cap = ring_verts[-1]
add_polygon([t_cap[0], t_cap[1], t_cap[2], t_cap[3], t_cap[4], t_cap[5], t_cap[6], t_cap[7]], UV_WOOD_WEDGE)

# ----------------------------------------------------
# 2. LANYARD HOLE (Hexagonal through-hole at butt)
# ----------------------------------------------------
# At Z=3.0, Y=0.0: small through-hole cutout represented by black inset hex caps on left & right
hole_y = 0.0
hole_z = 3.0
hole_rad = 0.3
hole_hx = 0.92  # slightly outside handle surface
for side, sign in [('R', 1.0), ('L', -1.0)]:
    pts = []
    for a in range(6):
        ang = a * math.pi / 3.0
        py = hole_y + hole_rad * math.cos(ang)
        pz = hole_z + hole_rad * math.sin(ang)
        pts.append((sign * hole_hx, py, pz))
    if sign > 0:
        pts.reverse()
    add_polygon(pts, UV_HOLE_BLACK)

# ----------------------------------------------------
# 3. AXE HEAD BUILDER
# ----------------------------------------------------
# Hatchet Head Features:
# - Rear Poll: Y = -1.2 to -5.2, Z = 33.5 to 38.0, X = +-1.1
# - Eye Collar: Y = -1.2 to 2.2, Z = 32.5 to 39.0, X = +-1.2
# - Recessed Dark Forged Cheek: Y = 2.2 to 7.0, Z = 30.0 to 39.5, X = +-0.6
# - Outer Cheek Border: surrounds dark cheek, X = +-0.9
# - Flared Beard: drops to Z = 27.5, Y = 6.8
# - Top Toe: rises to Z = 40.8, Y = 9.8
# - Cutting Edge (Crescent Arc): 3 segments from Toe to Beard at Y = 10.5..11.2, X = 0.0
# - Polished Bevel: bevel transition ridge at Y = 9.2..9.8, X = +-0.3

# Key Landmarks on Axe Head:
# Poll face (flat rear hammer face at Y = -5.0)
poll_y = -5.0
p_top_r   = ( 0.85, poll_y, 38.2)
p_top_l   = (-0.85, poll_y, 38.2)
p_bot_r   = ( 0.85, poll_y, 33.8)
p_bot_l   = (-0.85, poll_y, 33.8)

# Eye Collar Junction (Y = -1.2)
c_back_tr = ( 1.25, -1.2, 38.8)
c_back_tl = (-1.25, -1.2, 38.8)
c_back_br = ( 1.25, -1.2, 33.0)
c_back_bl = (-1.25, -1.2, 33.0)

# Poll Quad faces
add_quad(p_top_r, p_top_l, p_bot_l, p_bot_r, UV_STEEL_LIGHT)  # Poll face
add_quad(c_back_tr, c_back_tl, p_top_l, p_top_r, UV_STEEL_LIGHT)  # Poll top
add_quad(p_bot_r, p_bot_l, c_back_bl, c_back_br, UV_STEEL_LIGHT)  # Poll bot
add_quad(p_top_r, c_back_tr, c_back_br, p_bot_r, UV_STEEL_LIGHT)  # Poll right
add_quad(c_back_tl, p_top_l, p_bot_l, c_back_bl, UV_STEEL_LIGHT)  # Poll left

# Eye Collar Front Junction (Y = 2.2)
c_frnt_tr = ( 1.2, 2.2, 39.2)
c_frnt_tl = (-1.2, 2.2, 39.2)
c_frnt_br = ( 1.2, 2.2, 32.2)
c_frnt_bl = (-1.2, 2.2, 32.2)

# Eye Collar Top/Bot/Sides
add_quad(c_back_tr, c_frnt_tr, c_frnt_tl, c_back_tl, UV_STEEL_LIGHT)  # Eye collar top
add_quad(c_back_bl, c_frnt_bl, c_frnt_br, c_back_br, UV_STEEL_LIGHT)  # Eye collar bot
add_quad(c_back_br, c_frnt_br, c_frnt_tr, c_back_tr, UV_STEEL_LIGHT)  # Eye collar right
add_quad(c_frnt_bl, c_back_bl, c_back_tl, c_frnt_tl, UV_STEEL_LIGHT)  # Eye collar left

# ----------------------------------------------------
# 4. BLADE, CHEEK & BEARD
# ----------------------------------------------------
# Ridge 1: Cheek body (Y = 6.2)
# Top toe slope, bottom flared beard
b_ridge_top_r = ( 0.65, 6.2, 40.0)
b_ridge_top_l = (-0.65, 6.2, 40.0)
b_ridge_mid_r = ( 0.50, 6.2, 34.0)
b_ridge_mid_l = (-0.50, 6.2, 34.0)
b_ridge_brd_r = ( 0.60, 5.8, 27.5) # Flared beard bottom
b_ridge_brd_l = (-0.60, 5.8, 27.5)

# Cheek Inset (Dark forged carbon steel panel)
# Right cheek dark inset
add_quad(c_frnt_tr, b_ridge_top_r, b_ridge_mid_r, c_frnt_br, UV_STEEL_DARK)
add_tri(c_frnt_br, b_ridge_mid_r, b_ridge_brd_r, UV_STEEL_DARK)

# Left cheek dark inset
add_quad(b_ridge_top_l, c_frnt_tl, c_frnt_bl, b_ridge_mid_l, UV_STEEL_DARK)
add_tri(b_ridge_mid_l, c_frnt_bl, b_ridge_brd_l, UV_STEEL_DARK)

# Cheek Top / Under-beard transitions
add_quad(c_frnt_tr, c_frnt_tl, b_ridge_top_l, b_ridge_top_r, UV_STEEL_LIGHT) # Top slope
add_quad(c_frnt_bl, c_frnt_br, b_ridge_brd_r, b_ridge_brd_l, UV_STEEL_LIGHT) # Beard underside

# Ridge 2: Polished Bevel Grind Transition (Y = 9.2)
bev_top_r = ( 0.28,  9.5, 41.2)
bev_top_l = (-0.28,  9.5, 41.2)
bev_mid_r = ( 0.22, 10.2, 34.5)
bev_mid_l = (-0.22, 10.2, 34.5)
bev_brd_r = ( 0.25,  8.0, 27.2)
bev_brd_l = (-0.25,  8.0, 27.2)

# Forward cheek to bevel ridge (Medium steel transition)
add_quad(b_ridge_top_r, bev_top_r, bev_mid_r, b_ridge_mid_r, UV_STEEL_LIGHT)
add_quad(b_ridge_mid_r, bev_mid_r, bev_brd_r, b_ridge_brd_r, UV_STEEL_LIGHT)

add_quad(bev_top_l, b_ridge_top_l, b_ridge_mid_l, bev_mid_l, UV_STEEL_LIGHT)
add_quad(bev_mid_l, b_ridge_mid_l, b_ridge_brd_l, bev_brd_l, UV_STEEL_LIGHT)

# Top and Bottom bevel edges
add_quad(b_ridge_top_r, b_ridge_top_l, bev_top_l, bev_top_r, UV_STEEL_POLISHED)
add_quad(bev_brd_r, bev_brd_l, b_ridge_brd_l, b_ridge_brd_r, UV_STEEL_LIGHT)

# Ridge 3: The Crescent Curved Cutting Edge (X = 0, Sharp Polished Bevel!)
edge_top = (0.0, 11.2, 41.8) # Top toe
edge_mid = (0.0, 12.1, 34.8) # Center crest of crescent arc
edge_brd = (0.0,  9.2, 26.8) # Bottom beard tip

# Polished Bevel Facets (Right side)
add_quad(bev_top_r, (0.0, 11.2, 41.8), (0.0, 12.1, 34.8), bev_mid_r, UV_STEEL_POLISHED)
add_quad(bev_mid_r, (0.0, 12.1, 34.8), (0.0,  9.2, 26.8), bev_brd_r, UV_STEEL_POLISHED)

# Polished Bevel Facets (Left side)
add_quad((0.0, 11.2, 41.8), bev_top_l, bev_mid_l, (0.0, 12.1, 34.8), UV_STEEL_POLISHED)
add_quad((0.0, 12.1, 34.8), bev_mid_l, bev_brd_l, (0.0,  9.2, 26.8), UV_STEEL_POLISHED)

# Top & Bottom closure
add_tri(bev_top_r, edge_top, bev_top_l, UV_STEEL_POLISHED)
add_tri(bev_brd_l, edge_brd, bev_brd_r, UV_STEEL_POLISHED)

# ==========================================
# BUILD MESH IN BLENDER
# ==========================================
mesh.from_pydata(verts, [], faces)
mesh.update()

# Assign material
mesh.materials.append(mat)

# Assign UVs per loop
uv_layer = mesh.uv_layers.new(name="UVMap")
for poly_idx, poly in enumerate(mesh.polygons):
    uvs = face_uvs[poly_idx]
    for loop_idx, loop in enumerate(poly.loop_indices):
        uv_layer.data[loop].uv = uvs[loop_idx]

# Ensure flat faceted shading
for f in mesh.polygons:
    f.use_smooth = False

print(f"IDENTICAL HATCHET CREATED: {len(mesh.vertices)} vertices, {len(mesh.polygons)} polygons")

# ==========================================
# CAMERA & LIGHTING (Matching tool_axe.png)
# ==========================================
# In tool_axe.png:
# Axe is tilted at approx -35° angle, viewing front-left side
# Let's rotate the object to match the icon orientation perfectly
obj.rotation_euler = (math.radians(-24), math.radians(28), math.radians(-32))
obj.location = (-0.8, -0.2, -18.5)

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 46.0  # Framing to fill canvas with safe margin
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

cam_obj.location = (0, -45, 0)
cam_obj.rotation_euler = (math.radians(90), 0, 0)

# Key Light (Top-Left)
light_data1 = bpy.data.lights.new(name="KeyLight", type='SUN')
light_data1.energy = 4.2
light_data1.color = (1.0, 0.98, 0.94)
light_obj1 = bpy.data.objects.new(name="KeyLight", object_data=light_data1)
scene.collection.objects.link(light_obj1)
light_obj1.rotation_euler = (math.radians(50), math.radians(-30), math.radians(-40))

# Fill Light (Soft bluish-gray fill)
light_data2 = bpy.data.lights.new(name="FillLight", type='SUN')
light_data2.energy = 1.8
light_data2.color = (0.85, 0.90, 1.0)
light_obj2 = bpy.data.objects.new(name="FillLight", object_data=light_data2)
scene.collection.objects.link(light_obj2)
light_obj2.rotation_euler = (math.radians(-30), math.radians(60), math.radians(120))

# Rim Light (Crisp edge highlight)
light_data3 = bpy.data.lights.new(name="RimLight", type='SUN')
light_data3.energy = 2.5
light_data3.color = (1.0, 1.0, 1.0)
light_obj3 = bpy.data.objects.new(name="RimLight", object_data=light_data3)
scene.collection.objects.link(light_obj3)
light_obj3.rotation_euler = (math.radians(-70), math.radians(-20), math.radians(0))

# ==========================================
# RENDER PREVIEW
# ==========================================
render_out = r"c:\Users\casey\Desktop\Homesteader\HUD\scratch\identical_blender_axe_render.png"
scene.render.filepath = render_out
bpy.ops.render.render(write_still=True)
print(f"RENDER SAVED TO: {render_out}")

# ==========================================
# EXPORT OBJ
# ==========================================
# Reset transform for canonical export (Z-up, pivot at base)
obj.rotation_euler = (0, 0, 0)
obj.location = (0, 0, 0)
bpy.context.view_layer.update()

output_obj = r"c:\Users\casey\Desktop\Homesteader\HUD\scratch\SM_Tool_Axe_Felling_Identical.obj"
bpy.ops.wm.obj_export(
    filepath=output_obj,
    export_selected_objects=True,
    export_materials=True,
    export_uv=True,
    export_normals=True,
)
print(f"OBJ EXPORTED TO: {output_obj}")
