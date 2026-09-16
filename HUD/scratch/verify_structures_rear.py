import bpy
import os
import math
import mathutils

MODELS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Building\Meshes"
OUT_DIR = r"C:\Users\casey\.gemini\antigravity\brain\6940286d-0152-4b36-9e37-9e6cff11c21a\rear_renders"
os.makedirs(OUT_DIR, exist_ok=True)

names = [
    "SM_Struct_Barn", "SM_Struct_Cabin_Small", "SM_Struct_Cabin_Large", 
    "SM_Struct_House_Starter", "SM_Struct_House_Farmhouse", "SM_Struct_Shed", 
    "SM_Struct_Coop_Chicken", "SM_Struct_Greenhouse", "SM_Struct_Silo", 
    "SM_Struct_Stable", "SM_Struct_Tent_Canvas", "SM_Struct_Tent_Dome", 
    "SM_Struct_Camper_RV", "SM_Struct_Camper_Teardrop"
]

scales = {
    "SM_Struct_Barn": 1200.0,
    "SM_Struct_Cabin_Small": 700.0,
    "SM_Struct_Cabin_Large": 900.0,
    "SM_Struct_Shed": 700.0,
    "SM_Struct_House_Starter": 850.0,
    "SM_Struct_House_Farmhouse": 1300.0,
    "SM_Struct_Coop_Chicken": 600.0,
    "SM_Struct_Silo": 1200.0,
    "SM_Struct_Greenhouse": 750.0,
    "SM_Struct_Stable": 1400.0,
    "SM_Struct_Tent_Canvas": 550.0,
    "SM_Struct_Tent_Dome": 500.0,
    "SM_Struct_Camper_RV": 1100.0,
    "SM_Struct_Camper_Teardrop": 700.0,
}

for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 384
    scene.render.resolution_y = 384
    scene.render.film_transparent = True
    
    obj_path = os.path.join(MODELS_DIR, f"{name}.obj")
    bpy.ops.wm.obj_import(filepath=obj_path)
    
    mesh_objs = [o for o in scene.objects if o.type == 'MESH']
    if not mesh_objs:
        continue
    obj = mesh_objs[0]
    
    max_z = max(v.co.z for v in obj.data.vertices)
    min_z = min(v.co.z for v in obj.data.vertices)
    mid_z = (max_z + min_z) * 0.45
    
    # Lighting
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_data.energy = 4.0
    light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
    scene.collection.objects.link(light_obj)
    light_obj.rotation_euler = (math.radians(45), math.radians(30), math.radians(135))
    
    # Camera at rear view: (-0.7, 0.7, 0.55)
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = scales.get(name, 900.0)
    cam_data.clip_end = 15000.0
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    dist = 2500.0
    target = mathutils.Vector((0, 0, mid_z))
    cam_obj.location = (dist * -0.7, dist * 0.7, mid_z + dist * 0.55)
    direction = -(cam_obj.location - target).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    out_file = os.path.join(OUT_DIR, f"{name}_rear.png")
    scene.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    print(f"Rendered rear: {name}")

print("All rear views re-rendered successfully!")

