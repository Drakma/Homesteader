import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\instantmesh_baby_calf.glb")

for obj in bpy.context.scene.objects:
    print(f"Object: {obj.name}, type: {obj.type}, rot: {obj.rotation_euler}, loc: {obj.location}, dims: {obj.dimensions}")

