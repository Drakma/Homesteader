import os
import shutil
from gradio_client import Client, handle_file

ICON_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
OUTPUT_GLB = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\instantmesh_baby_calf.glb"
OUTPUT_OBJ = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\instantmesh_baby_calf.obj"

print("Connecting to TencentARC/InstantMesh...")
client = Client("TencentARC/InstantMesh")
print("Connected!")

print("Step 1: Preprocessing image...")
preprocessed = client.predict(
    handle_file(ICON_PATH),
    False, # do_remove_background
    api_name="/preprocess"
)
print("Preprocessed image:", preprocessed)

print("Step 2: Generating Multi-Views (sample_steps=75)...")
mvs = client.predict(
    handle_file(preprocessed),
    75, # sample_steps
    42, # sample_seed
    api_name="/generate_mvs"
)
print("Generated Multi-Views:", mvs)

print("Step 3: Reconstructing 3D Mesh...")
res_obj, res_glb = client.predict(
    api_name="/make3d"
)
print(f"Generated OBJ: {res_obj}")
print(f"Generated GLB: {res_glb}")

if res_glb and os.path.exists(res_glb):
    shutil.copy(res_glb, OUTPUT_GLB)
    print(f"SUCCESS: Saved InstantMesh GLB to {OUTPUT_GLB} ({os.path.getsize(OUTPUT_GLB)} bytes)")

if res_obj and os.path.exists(res_obj):
    shutil.copy(res_obj, OUTPUT_OBJ)
    print(f"SUCCESS: Saved InstantMesh OBJ to {OUTPUT_OBJ} ({os.path.getsize(OUTPUT_OBJ)} bytes)")

