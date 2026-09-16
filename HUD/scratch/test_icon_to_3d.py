import os
import math
import numpy as np
from PIL import Image

ICON_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
OUTPUT_SCRIPT = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\run_blender_reconstruct.py"
COMPARISON_OUT = r"C:\Users\casey\.gemini\antigravity\brain\6940286d-0152-4b36-9e37-9e6cff11c21a\calf_icon_comparison.png"

# 1. Load icon and extract silhouette contour
img = Image.open(ICON_PATH).convert("RGBA")
W, H = img.size
alpha = np.array(img)[:, :, 3]

# Binary mask threshold
mask = (alpha > 100).astype(np.uint8)

# Find boundary contours using simple 8-neighborhood edge detection
from collections import deque

# Simple Marching Squares / Boundary tracer
# Pad mask
padded = np.pad(mask, 1, mode='constant')

# Find starting pixel
start = None
for y in range(H):
    for x in range(W):
        if mask[y, x]:
            start = (x, y)
            break
    if start:
        break

# Moore-Neighbor Tracing
boundary = []
curr = start
# Directions: N, NE, E, SE, S, SW, W, NW
dirs = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

# Trace outline
visited = set()
cx, cy = start
b_dir = 6 # enter from left
outline = [start]

for _ in range(5000):
    found = False
    for i in range(8):
        d_idx = (b_dir + i) % 8
        dx, dy = dirs[d_idx]
        nx, ny = cx + dx, cy + dy
        if 0 <= nx < W and 0 <= ny < H and mask[ny, nx]:
            cx, cy = nx, ny
            b_dir = (d_idx + 5) % 8
            found = True
            break
    if not found or (cx, cy) == start and len(outline) > 5:
        break
    outline.append((cx, cy))

# Simplify outline by downsampling (keep ~120 smooth perimeter vertices)
step = max(1, len(outline) // 140)
sampled_outline = outline[::step]
print(f"Extracted {len(sampled_outline)} contour vertices from icon silhouette.")

# Convert to Blender world coordinates:
# Icon coordinates: X from 0 to 127 (left to right), Y from 0 to 127 (top to bottom).
# In isometric camera view (~35° pitch, 45° yaw):
# Screen U = (X - 64), Screen V = -(Y - 64)
# Let's write the Blender reconstruction script
blender_code = f"""import bpy
import bmesh
import math
import mathutils
import os

ICON_PATH = r"{ICON_PATH}"
RENDERS_DIR = r"C:\\Users\\casey\\Desktop\\Homesteader\\HUD\\scratch\\renders_test"
os.makedirs(RENDERS_DIR, exist_ok=True)

# 2D contour points in pixel space
pts_2d = {sampled_outline}

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True

# Create 3D Mesh
mesh = bpy.data.meshes.new("Baby_Calf_Icon_Model")
obj = bpy.data.objects.new("Baby_Calf_Icon_Model", mesh)
scene.collection.objects.link(obj)

bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")

# Convert 2D points to 3D in camera viewing plane
# Camera is at ~35° pitch, 45° yaw (isometric)
cam_pitch = math.radians(35)
cam_yaw = math.radians(45)

# Camera rotation matrix
R_cam = mathutils.Euler((cam_pitch, 0, cam_yaw), 'XYZ').to_matrix().to_4x4()
# Camera coordinate axes in world space:
# Right vector (Screen X):
v_right = R_cam @ mathutils.Vector((1, 0, 0, 0))
# Up vector (Screen Y):
v_up = R_cam @ mathutils.Vector((0, 1, 0, 0))
# Depth vector (pointing away from camera into scene):
v_depth = -(R_cam @ mathutils.Vector((0, 0, 1, 0)))

v_right = v_right.to_3d().normalized()
v_up = v_up.to_3d().normalized()
v_depth = v_depth.to_3d().normalized()

# Scale factor: 128 pixels ~ 50 cm
scale = 50.0 / 128.0
thickness = 22.0 # cm thickness for calf body

# Create front and back rings
front_verts = []
back_verts = []

center_x = 64.0
center_y = 64.0

for px, py in pts_2d:
    u = (px - center_x) * scale
    v = -(py - center_y) * scale
    
    # World position on center plane (Z base ~ 25)
    p_center = v_right * u + v_up * v + mathutils.Vector((0, 0, 25.0))
    
    # Front vertex (offset towards camera by +thickness/2)
    p_front = p_center - v_depth * (thickness * 0.5)
    # Back vertex (offset away from camera by -thickness/2)
    p_back = p_center + v_depth * (thickness * 0.5)
    
    vf = bm.verts.new(p_front)
    vb = bm.verts.new(p_back)
    front_verts.append(vf)
    back_verts.append(vb)

# Create Front Face (cap)
f_front = bm.faces.new(front_verts)
f_front.smooth = True

# Create Back Face (cap)
f_back = bm.faces.new(list(reversed(back_verts)))
f_back.smooth = True

# Bridge side walls
n = len(front_verts)
for i in range(n):
    nxt = (i + 1) % n
    fs = bm.faces.new([front_verts[i], front_verts[nxt], back_verts[nxt], back_verts[i]])
    fs.smooth = True

# Assign UV coordinates to all vertices matching the icon pixels!
for f in bm.faces:
    for loop in f.loops:
        # Project vertex to camera screen space (0 to 1)
        v_rel = loop.vert.co - mathutils.Vector((0, 0, 25.0))
        u_proj = v_rel.dot(v_right) / scale + center_x
        v_proj = v_rel.dot(v_up) / scale + center_y
        
        # UV space (0 to 1, V inverted)
        uv_u = max(0.0, min(1.0, u_proj / 128.0))
        uv_v = max(0.0, min(1.0, 1.0 - (v_proj / 128.0)))
        loop[uv_layer].uv = (uv_u, uv_v)

bm.to_mesh(mesh)
bm.free()

# Add Bevel Modifier for rounded organic 3D edges
bev = obj.modifiers.new("Bevel", 'BEVEL')
bev.width = 3.5
bev.segments = 4
bev.limit_method = 'NONE'

# Subsurf for extra smoothness
sub = obj.modifiers.new("Subsurf", 'SUBSURF')
sub.levels = 1

# Material with icon texture
mat = bpy.data.materials.new("M_Calf_Icon")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

node_out = nodes.new('ShaderNodeOutputMaterial')
node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
node_bsdf.inputs['Roughness'].default_value = 0.45
node_bsdf.inputs['Specular IOR Level'].default_value = 0.5

node_tex = nodes.new('ShaderNodeTexImage')
img = bpy.data.images.load(ICON_PATH)
node_tex.image = img
node_tex.interpolation = 'Linear'

links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
obj.data.materials.append(mat)

# Setup Camera matching isometric projection
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 55.0
cam_data.clip_end = 5000.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

dist = 500.0
cam_obj.location = mathutils.Vector((0, 0, 25.0)) - v_depth * dist
cam_obj.rotation_euler = (cam_pitch, 0, cam_yaw)

# Soft Key Light
l_key = bpy.data.lights.new("Key", 'SUN')
l_key.energy = 3.5
l_key.color = (1.0, 1.0, 1.0)
l_obj = bpy.data.objects.new("Key", l_key)
scene.collection.objects.link(l_obj)
l_obj.rotation_euler = (math.radians(35), 0, math.radians(-30))

render_path = os.path.join(RENDERS_DIR, "Reconstructed_Calf_render.png")
scene.render.filepath = render_path
bpy.ops.render.render(write_still=True)
print("SUCCESS: Rendered reconstructed calf to", render_path)
"""

with open(OUTPUT_SCRIPT, "w") as f:
    f.write(blender_code)

print("Wrote Blender reconstruction script.")

