import os
import shutil
from gradio_client import Client, handle_file

ICON_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
OUTPUT_GLB = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\triposr_baby_calf.glb"
OUTPUT_OBJ = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\triposr_baby_calf.obj"

print("Connecting to stabilityai/TripoSR...")
client = Client("stabilityai/TripoSR")
print("Connected!")

print("Step 1: Preprocessing image...")
preprocessed = client.predict(
    handle_file(ICON_PATH),
    False, # remove_background
    0.85,  # foreground_ratio
    api_name="/preprocess"
)
print("Preprocessed image:", preprocessed)

print("Step 2: Generating 3D Mesh (Marching Cubes 256)...")
res_obj, res_glb = client.predict(
    handle_file(preprocessed),
    256,
    api_name="/generate"
)

print(f"Generated OBJ: {res_obj}")
print(f"Generated GLB: {res_glb}")

if res_glb and os.path.exists(res_glb):
    shutil.copy(res_glb, OUTPUT_GLB)
    print(f"SUCCESS: Saved TripoSR GLB to {OUTPUT_GLB} ({os.path.getsize(OUTPUT_GLB)} bytes)")

if res_obj and os.path.exists(res_obj):
    shutil.copy(res_obj, OUTPUT_OBJ)
    print(f"SUCCESS: Saved TripoSR OBJ to {OUTPUT_OBJ} ({os.path.getsize(OUTPUT_OBJ)} bytes)")
