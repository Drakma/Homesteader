import bpy
import math
import mathutils
import os

GLB_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\instantmesh_baby_calf.glb"
RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test"
RENDER_OUT = os.path.join(RENDERS_DIR, "instantmesh_calf_render_front.png")
os.makedirs(RENDERS_DIR, exist_ok=True)

# Scene Setup
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'

# Import GLB
bpy.ops.import_scene.gltf(filepath=GLB_PATH)

main_obj = [obj for obj in scene.objects if obj.type == 'MESH'][0]

bpy.ops.object.select_all(action='DESELECT')
main_obj.select_set(True)
bpy.context.view_layer.objects.active = main_obj
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
main_obj.location = (0, 0, 0)

# Rotate object 180 degrees around Z so the front faces camera
main_obj.rotation_euler = (0, 0, math.radians(180))

min_z = min((main_obj.matrix_world @ v.co).z for v in main_obj.data.vertices)
max_z = max((main_obj.matrix_world @ v.co).z for v in main_obj.data.vertices)
dim_z = max_z - min_z
main_obj.location.z -= min_z

cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = dim_z * 2.0
cam_data.clip_end = 5000.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

target = mathutils.Vector((0, 0, dim_z * 0.5))
dist = 500.0
pitch = math.radians(20.0)
yaw = math.radians(45.0)

cam_x = target.x - dist * math.cos(pitch) * math.sin(yaw)
cam_y = target.y - dist * math.cos(pitch) * math.cos(yaw)
cam_z = target.z + dist * math.sin(pitch)

cam_obj.location = (cam_x, cam_y, cam_z)
dir_vec = -(cam_obj.location - target).normalized()
cam_obj.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()

# Lights
l_sun = bpy.data.lights.new("Sun", 'SUN')
l_sun.energy = 4.0
l_sun.color = (1.0, 0.98, 0.95)
l_obj = bpy.data.objects.new("Sun", l_sun)
scene.collection.objects.link(l_obj)
l_obj.rotation_euler = (math.radians(45), math.radians(-15), math.radians(60))

l_fill = bpy.data.lights.new("Fill", 'SUN')
l_fill.energy = 2.5
l_fill.color = (1.0, 0.95, 0.90)
l_f_obj = bpy.data.objects.new("Fill", l_fill)
scene.collection.objects.link(l_f_obj)
l_f_obj.rotation_euler = (math.radians(30), math.radians(20), math.radians(-120))

scene.render.filepath = RENDER_OUT
bpy.ops.render.render(write_still=True)
print(f"Rendered to: {RENDER_OUT}")

