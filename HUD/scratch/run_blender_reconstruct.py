import bpy
import bmesh
import math
import mathutils
import os

ICON_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test"
os.makedirs(RENDERS_DIR, exist_ok=True)

# 2D contour points in pixel space
pts_2d = [(31, 12), (33, 13), (34, 15), (36, 17), (38, 18), (40, 20), (42, 19), (44, 19), (46, 19), (48, 19), (50, 19), (52, 19), (54, 20), (56, 20), (58, 21), (60, 22), (62, 23), (64, 24), (66, 26), (68, 27), (70, 26), (72, 25), (74, 24), (76, 23), (78, 23), (80, 22), (82, 22), (84, 21), (86, 21), (88, 21), (90, 22), (92, 22), (94, 22), (96, 23), (98, 23), (100, 24), (102, 25), (104, 27), (105, 29), (107, 31), (108, 33), (109, 35), (110, 37), (111, 39), (111, 41), (111, 43), (112, 45), (111, 47), (112, 49), (113, 51), (115, 53), (115, 55), (114, 57), (114, 59), (113, 60), (111, 61), (111, 63), (111, 65), (110, 67), (111, 69), (111, 71), (111, 73), (111, 75), (111, 77), (111, 79), (110, 81), (110, 83), (110, 85), (109, 87), (109, 89), (109, 91), (109, 93), (108, 95), (107, 96), (105, 97), (103, 98), (101, 98), (99, 97), (97, 96), (96, 95), (96, 93), (97, 91), (97, 89), (97, 87), (98, 85), (98, 83), (97, 81), (96, 79), (94, 79), (92, 80), (90, 82), (90, 84), (89, 86), (87, 87), (85, 88), (83, 88), (81, 90), (81, 92), (80, 94), (79, 96), (79, 98), (78, 100), (78, 102), (78, 104), (78, 106), (78, 108), (78, 110), (77, 112), (75, 113), (73, 114), (71, 114), (69, 114), (67, 112), (65, 112), (64, 111), (65, 109), (65, 107), (65, 105), (66, 103), (66, 101), (66, 99), (65, 97), (65, 95), (64, 93), (64, 91), (63, 89), (61, 88), (59, 88), (58, 90), (58, 92), (58, 94), (58, 96), (57, 98), (57, 100), (58, 102), (56, 104), (54, 105), (52, 105), (50, 106), (48, 106), (46, 104), (44, 103), (44, 101), (45, 99), (45, 97), (46, 95), (46, 93), (46, 91), (45, 89), (44, 87), (44, 85), (43, 83), (43, 81), (42, 79), (41, 77), (39, 76), (37, 76), (35, 76), (33, 76), (31, 76), (29, 75), (27, 74), (25, 73), (23, 72), (21, 70), (20, 68), (19, 66), (19, 64), (18, 62), (18, 60), (19, 58), (20, 56), (21, 54), (22, 52), (22, 50), (22, 48), (23, 46), (23, 44), (23, 42), (24, 40), (25, 38), (25, 36), (24, 34), (22, 34), (20, 32), (18, 31), (16, 29), (15, 27), (13, 25), (12, 23), (12, 21), (13, 20), (15, 19), (17, 18), (19, 18), (21, 18), (23, 18), (25, 19), (27, 20), (29, 19), (29, 17), (29, 15), (30, 13)]

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
