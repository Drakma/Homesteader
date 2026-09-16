import bpy
import math
import mathutils
import os

GLB_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\instantmesh_baby_calf.glb"
RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test"
os.makedirs(RENDERS_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'

bpy.ops.import_scene.gltf(filepath=GLB_PATH)

mesh = [o for o in scene.objects if o.type == 'MESH'][0]
# Unparent
mesh.parent = None
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
mesh.location = (0, 0, 0)

dim_max = max(mesh.dimensions)

# Setup Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = dim_max * 1.6
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Sun
l_sun = bpy.data.lights.new("Sun", 'SUN')
l_sun.energy = 4.0
l_obj = bpy.data.objects.new("Sun", l_sun)
scene.collection.objects.link(l_obj)
l_obj.rotation_euler = (math.radians(45), math.radians(-15), math.radians(60))

# Fill
l_fill = bpy.data.lights.new("Fill", 'SUN')
l_fill.energy = 2.5
l_f_obj = bpy.data.objects.new("Fill", l_fill)
scene.collection.objects.link(l_f_obj)
l_f_obj.rotation_euler = (math.radians(30), math.radians(20), math.radians(-120))

dist = 50.0
pitch = math.radians(20.0)

views = [
    ("0deg", 0),
    ("90deg", 90),
    ("180deg", 180),
    ("270deg", 270),
]

img_paths = []
for name, yaw_deg in views:
    yaw = math.radians(yaw_deg)
    cam_obj.location = (dist * math.cos(pitch) * math.sin(yaw), -dist * math.cos(pitch) * math.cos(yaw), dist * math.sin(pitch))
    direction = -cam_obj.location.normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    out_file = os.path.join(RENDERS_DIR, f"im_turntable_{name}.png")
    scene.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    img_paths.append(out_file)

print("Rendered 4 turntable views!")
