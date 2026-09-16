import os
import shutil
from gradio_client import Client, handle_file

ICON_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
OUTPUT_GLB = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\trellis_baby_calf.glb"

print("Connecting to Trellis...")
client = Client("trellis-community/TRELLIS")
print("Connected!")

print("Step 1: Preprocessing image...")
preprocessed = client.predict(
    image=handle_file(ICON_PATH),
    api_name="/preprocess_image"
)
print("Preprocessed result:", preprocessed)

print("Step 2: Generating 3D asset and extracting GLB...")
result = client.predict(
    image=preprocessed,
    multiimages=[],
    seed=42,
    ss_guidance_strength=7.5,
    ss_sampling_steps=12,
    slat_guidance_strength=3.0,
    slat_sampling_steps=12,
    multiimage_algo='stochastic',
    mesh_simplify=0.95,
    texture_size=1024,
    api_name="/generate_and_extract_glb"
)

print("Result received:", result)
for item in result:
    if isinstance(item, str) and item.endswith(".glb") and os.path.exists(item):
        shutil.copy(item, OUTPUT_GLB)
        print(f"SUCCESS: Saved TRELLIS GLB to {OUTPUT_GLB} ({os.path.getsize(OUTPUT_GLB)} bytes)")
        break
    elif isinstance(item, dict) and "path" in item and item["path"].endswith(".glb"):
        shutil.copy(item["path"], OUTPUT_GLB)
        print(f"SUCCESS: Saved TRELLIS GLB to {OUTPUT_GLB} ({os.path.getsize(OUTPUT_GLB)} bytes)")
        break

