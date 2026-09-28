from PIL import Image, ImageDraw
import numpy as np

src_path = r"C:/Users/casey/.gemini/antigravity/brain/22a79297-c0db-46b0-a570-39cffdd3aaae/.user_uploaded/media_1789973909748.png"
ref_icon = Image.open(r"C:/Users/casey/Desktop/Homesteader/Homesteader/Assets/Resources/HUDTree/PhoneIcons/app_nail_it.png")
mask = ref_icon.split()[-1] # 128x128 alpha mask from existing icon

src_img = Image.open(src_path).convert("RGBA")

# Exact bounding boxes (213 x 213)
crops = {
    "app_voltvision.png": (112, 133, 325, 346),
    "app_techtrak.png": (409, 133, 622, 346),
    "app_trailer_shack.png": (710, 133, 923, 346)
}

for filename, bbox in crops.items():
    cropped = src_img.crop(bbox)
    resized = cropped.resize((128, 128), Image.Resampling.LANCZOS)
    
    # We apply the clean squircle alpha mask from existing icon
    # Check if corner of cropped is white
    r, g, b, a = resized.split()
    # Combine mask
    final_icon = Image.merge("RGBA", (r, g, b, mask))
    out_path = f"Homesteader/Assets/Resources/HUDTree/PhoneIcons/{filename}"
    final_icon.save(out_path)
    print(f"Saved {out_path} ({final_icon.size})")

