"""Probe vital layout dimensions."""
import sys, os
KIT = os.path.abspath(r"C:\Users\casey\Desktop\Homesteader\assets/hud_kit")
sys.path.insert(0, KIT)
from runtime.divlayout import build_layout, SIZE

m_w = 1920
layout = build_layout(m_w, 1080)
hdr = layout["divs"]["header"]
vit = layout["divs"]["vitals"]
print(f"header: x={hdr.x} y={hdr.y} w={hdr.w} h={hdr.h}")
print(f"vitals: x={vit.x} y={vit.y} w={vit.w} h={vit.h}")
print(f"vital_icon = {SIZE['vital_icon']}")
cells = layout["vital_cells"]
for i, c in enumerate(cells):
    print(f"  cell[{i}]: x={c.x} y={c.y} w={c.w} h={c.h}")
