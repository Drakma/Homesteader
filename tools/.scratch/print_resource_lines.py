import sys
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\HudUI.uxml"
text = open(p, "r").read()
nl = chr(10)
for line in text.split(nl):
    if "resource" in line or "icon-tile" in line or "well" in line or "resources" in line:
        print(line.strip()[:140])
