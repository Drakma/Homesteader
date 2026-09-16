import os
import re

index_path = r"c:\Users\casey\Desktop\Homesteader\HUD\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

print("HTML length:", len(html))

# Check for inline script blocks
scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
print(f"Found {len(scripts)} inline script blocks.")

# Check referenced assets in html
img_srcs = re.findall(r'src=["\'](assets/[^"\']+)["\']', html)
print(f"Found {len(img_srcs)} direct img srcs.")
missing_imgs = [s for s in img_srcs if not os.path.exists(os.path.join(r"c:\Users\casey\Desktop\Homesteader\HUD", s))]
print(f"Missing img srcs: {len(missing_imgs)}")
if missing_imgs:
    print("Sample missing:", missing_imgs[:10])

# Check href downloads
hrefs = re.findall(r'href=["\'](assets/[^"\']+)["\']', html)
print(f"Found {len(hrefs)} asset download hrefs.")
missing_hrefs = [h for h in hrefs if not os.path.exists(os.path.join(r"c:\Users\casey\Desktop\Homesteader\HUD", h))]
print(f"Missing download hrefs: {len(missing_hrefs)}")
if missing_hrefs:
    print("Sample missing hrefs:", missing_hrefs[:10])

