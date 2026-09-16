from PIL import Image
import numpy as np

img = Image.open(r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png").convert("RGBA")
print("Size:", img.size)

# Find bbox of non-transparent pixels
bbox = img.split()[3].getbbox()
print("BBox:", bbox)

# Analyze unique dominant colors in the icon
arr = np.array(img)
alpha = arr[:, :, 3]
rgb = arr[:, :, :3]
visible_pixels = rgb[alpha > 128]

# Cluster or count colors
print("Total visible pixels:", len(visible_pixels))

