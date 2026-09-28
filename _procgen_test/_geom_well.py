"""Run a probe to display the actual vital content extent in the canvas."""
import sys, os
KIT = os.path.abspath(r"C:\Users\casey\Desktop\Homesteader\assets/hud_kit")
sys.path.insert(0, KIT)
from runtime.divlayout import build_layout
m_w = 1920
layout = build_layout(m_w, 1080)
hdr = layout["divs"]["header"]
cells = layout["vital_cells"]
ext0 = min(c.x for c in cells) - hdr.x
ext_right = max(c.x + c.w for c in cells) - hdr.x
content_w = ext_right - ext0
print(f"header x=0..{m_w}")
print(f"vital cells extent: {ext0}..{ext_right}  (content_w={content_w})")
WW = content_w + 6 + 6 + 8 + 0
print(f"vital well width: {WW}  anchored left")
print(f"  predicted well left if anchor=left: {ext0 - 6 + 8}")
print(f"  predicted well right: {ext0 - 6 + 8 + WW}")
print(f"  predicted content pad-left inside well: {(WW - 8 - 0 - content_w) // 2}")
print(f"  predicted content pad-right inside well: {(WW - 8 - 0 - content_w) // 2}")
