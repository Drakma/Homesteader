import bpy
import sys
import os

argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
else:
    args = []

if len(args) < 1:
    print("Usage: blender -b -P obj_to_glb.py -- <input.obj> [output.glb]")
    sys.exit(1)

input_obj = os.path.abspath(args[0])
if len(args) >= 2:
    output_glb = os.path.abspath(args[1])
else:
    output_glb = os.path.splitext(input_obj)[0] + ".glb"

print(f"Converting OBJ: {input_obj} -> GLB: {output_glb}")

# Clear default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import OBJ
bpy.ops.wm.obj_import(filepath=input_obj)

# Export GLB
os.makedirs(os.path.dirname(output_glb), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=output_glb,
    export_format='GLB',
    export_materials='EXPORT'
)

print(f"SUCCESS: Exported {output_glb} ({os.path.getsize(output_glb)} bytes)")
