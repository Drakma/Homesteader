"""
Builds the door styles in headless Blender and writes their manifests (assets/building/<id>/): four interior doors (0.9 m by 2.1 m) and four
exterior doors (1.2 m by 2.3 m, two of them glazed). Free, local, low-poly, GLB with plain colour materials. The plain panel doors
(building_door_interior, building_door_exterior) stay in tools/make_building_items.py.

    blender --background --python tools/make_doors.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png        (every door)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

Like the other building parts: pivot at the middle of the footprint, bottom at z = 0, front = -Y, hinges on the left (-X), knob on the right.
Paint: the doors are placeable, and a placed door is painted with a paint can like a building's door. Every material that should take the paint is
named Door... (DoorSlab, DoorPanel, DoorEdge, DoorTrim); the knob and hinges are DoorHardware and the panes Glass, which keep their own colour.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_building_items as mod  # noqa: E402

base = mod.base

IW, IH, IT = 0.9, 2.1, 0.04        # interior: width, height, thickness
EW, EH, ET = 1.2, 2.3, 0.06        # exterior
PROUD = 0.008                      # how far a raised panel or a rail stands out of the slab


def hardware(b, w, h, t, metal, deadbolt=False):
    for fy in (-1, 1):
        y0, y1 = (-t / 2 - 0.05, -t / 2) if fy < 0 else (t / 2, t / 2 + 0.05)
        b.box(w / 2 - 0.1, w / 2 - 0.06, y0, y1, 0.98, 1.04, metal)                    # the knob
        b.box(w / 2 - 0.115, w / 2 - 0.045, y0 + (0.044 if fy < 0 else 0.0), y1 - (0.0 if fy < 0 else 0.044), 0.96, 1.06, metal)   # its rose
        if deadbolt:
            b.box(w / 2 - 0.105, w / 2 - 0.055, y0 + (0.03 if fy < 0 else 0.0), y1 - (0.0 if fy < 0 else 0.03), 1.16, 1.21, metal)
    for hz in (0.25, h / 2, h - 0.25):
        b.box(-w / 2 - 0.012, -w / 2 + 0.01, -t / 2 - 0.006, t / 2 + 0.006, hz - 0.07, hz + 0.07, metal)   # the hinges


def both_faces(b, t, x0, x1, z0, z1, m, proud=PROUD):
    """A raised block on both faces of the slab."""
    b.box(x0, x1, -t / 2 - proud, -t / 2, z0, z1, m)
    b.box(x0, x1, t / 2, t / 2 + proud, z0, z1, m)


def rails(b, w, h, t, m, stile, rail_zs):
    """A frame laid over the slab on both faces: two stiles and the rails [(z0, z1), ...]; what is left between them reads as recessed panels."""
    both_faces(b, t, -w / 2, -w / 2 + stile, 0.0, h, m)
    both_faces(b, t, w / 2 - stile, w / 2, 0.0, h, m)
    for z0, z1 in rail_zs:
        both_faces(b, t, -w / 2 + stile, w / 2 - stile, z0, z1, m)


def glazed_slab(b, w, h, t, m, x0, x1, z0, z1):
    """The slab with a rectangular opening (x0..x1, z0..z1) left for glass."""
    b.box(-w / 2, x0, -t / 2, t / 2, 0.0, h, m)
    b.box(x1, w / 2, -t / 2, t / 2, 0.0, h, m)
    b.box(x0, x1, -t / 2, t / 2, 0.0, z0, m)
    b.box(x0, x1, -t / 2, t / 2, z1, h, m)


def lites(b, t, glass, bar, x0, x1, z0, z1, cols, rows, bar_w=0.022):
    """Glass in an opening, divided into cols x rows lites by muntin bars."""
    b.box(x0, x1, -0.005, 0.005, z0, z1, glass)
    for k in range(1, cols):
        x = x0 + (x1 - x0) * k / cols
        b.box(x - bar_w / 2, x + bar_w / 2, -t * 0.4, t * 0.4, z0, z1, bar)
    for k in range(1, rows):
        z = z0 + (z1 - z0) * k / rows
        b.box(x0, x1, -t * 0.4, t * 0.4, z - bar_w / 2, z + bar_w / 2, bar)


def metal():
    return base.material('DoorHardware', (0.62, 0.6, 0.56), 0.35)


def dark_metal():
    return base.material('DoorHardware', (0.12, 0.12, 0.13), 0.45)


# ------------------------------------------------------------------ interior

def interior_flush():
    b = base.Builder('building_door_interior_flush')
    veneer = base.material('DoorSlab', (0.8, 0.67, 0.48), 0.6)
    edge = base.material('DoorEdge', (0.7, 0.57, 0.4), 0.7)
    b.box(-IW / 2, IW / 2, -IT / 2, IT / 2, 0.0, IH, veneer)
    for x0, x1 in ((-IW / 2 - 0.002, -IW / 2 + 0.012), (IW / 2 - 0.012, IW / 2 + 0.002)):      # the solid edge strips of a flush door
        b.box(x0, x1, -IT / 2 - 0.001, IT / 2 + 0.001, 0.0, IH, edge)
    hardware(b, IW, IH, IT, metal())
    return b


def interior_shaker():
    b = base.Builder('building_door_interior_shaker')
    paint = base.material('DoorSlab', (0.94, 0.94, 0.92), 0.6)
    panel = base.material('DoorPanel', (0.88, 0.88, 0.86), 0.65)
    b.box(-IW / 2, IW / 2, -IT / 2, IT / 2, 0.0, IH, panel)
    rails(b, IW, IH, IT, paint, 0.11, [(0.0, 0.2), (0.96, 1.08), (IH - 0.12, IH)])        # two flat recessed panels
    hardware(b, IW, IH, IT, dark_metal())
    return b


def interior_six_panel():
    b = base.Builder('building_door_interior_six_panel')
    oak = base.material('DoorSlab', (0.66, 0.45, 0.25), 0.65)
    raised = base.material('DoorPanel', (0.73, 0.52, 0.3), 0.6)
    b.box(-IW / 2, IW / 2, -IT / 2, IT / 2, 0.0, IH, oak)
    for xa, xb in ((-IW / 2 + 0.1, -0.035), (0.035, IW / 2 - 0.1)):                       # two columns of three raised panels
        for za, zb in ((0.2, 0.86), (1.0, 1.66), (1.78, IH - 0.12)):
            both_faces(b, IT, xa, xb, za, zb, raised)
            both_faces(b, IT, xa + 0.035, xb - 0.035, za + 0.035, zb - 0.035, oak, proud=PROUD + 0.005)     # the field of the raised panel
    hardware(b, IW, IH, IT, metal())
    return b


def interior_french():
    b = base.Builder('building_door_interior_french')
    paint = base.material('DoorSlab', (0.95, 0.95, 0.93), 0.6)
    glass = base.glass_material()
    x0, x1, z0, z1 = -IW / 2 + 0.11, IW / 2 - 0.11, 0.24, IH - 0.12
    glazed_slab(b, IW, IH, IT, paint, x0, x1, z0, z1)
    lites(b, IT, glass, paint, x0, x1, z0, z1, 2, 5)                                    # ten lites
    hardware(b, IW, IH, IT, metal())
    return b


# ------------------------------------------------------------------ exterior

def exterior_six_panel():
    b = base.Builder('building_door_exterior_six_panel')
    paint = base.material('DoorSlab', (0.15, 0.21, 0.36), 0.5)
    raised = base.material('DoorPanel', (0.19, 0.26, 0.43), 0.5)
    b.box(-EW / 2, EW / 2, -ET / 2, ET / 2, 0.0, EH, paint)
    for xa, xb in ((-EW / 2 + 0.13, -0.05), (0.05, EW / 2 - 0.13)):
        for za, zb in ((0.24, 0.95), (1.1, 1.82), (1.95, EH - 0.13)):
            both_faces(b, ET, xa, xb, za, zb, raised)
            both_faces(b, ET, xa + 0.04, xb - 0.04, za + 0.04, zb - 0.04, paint, proud=PROUD + 0.006)
    b.box(-EW / 2, EW / 2, -ET / 2 - 0.012, ET / 2 + 0.012, 0.0, 0.03, metal())             # the sweep along the bottom
    hardware(b, EW, EH, ET, metal(), deadbolt=True)
    return b


def exterior_plank():
    b = base.Builder('building_door_exterior_plank')
    back = base.material('DoorEdge', (0.25, 0.16, 0.09), 0.85)
    plank = base.material('DoorSlab', (0.45, 0.29, 0.16), 0.8)
    plank2 = base.material('DoorPanel', (0.5, 0.33, 0.19), 0.8)
    iron = dark_metal()
    b.box(-EW / 2, EW / 2, -ET / 2 + 0.012, ET / 2 - 0.012, 0.0, EH, back)                # the core: it shows as the dark joints between the planks
    n = 6
    for k in range(n):
        x0 = -EW / 2 + EW * k / n + 0.004
        x1 = -EW / 2 + EW * (k + 1) / n - 0.004
        m = plank if k % 2 == 0 else plank2
        b.box(x0, x1, -ET / 2, -ET / 2 + 0.012, 0.0, EH, m)
        b.box(x0, x1, ET / 2 - 0.012, ET / 2, 0.0, EH, m)
    for z in (0.3, EH / 2, EH - 0.3):                                                   # the ledgers on the inside, the strap hinges on the outside
        b.box(-EW / 2 + 0.04, EW / 2 - 0.04, ET / 2, ET / 2 + 0.022, z - 0.07, z + 0.07, plank)
    for z in (0.3, EH - 0.3):
        b.box(-EW / 2, EW / 2 - 0.25, -ET / 2 - 0.008, -ET / 2, z - 0.03, z + 0.03, iron)
        b.box(EW / 2 - 0.29, EW / 2 - 0.25, -ET / 2 - 0.008, -ET / 2, z - 0.05, z + 0.05, iron)
    for x in (-EW / 2 + 0.12, -0.2, 0.2):                                               # studs on the straps
        for z in (0.3, EH - 0.3):
            b.box(x - 0.012, x + 0.012, -ET / 2 - 0.014, -ET / 2 - 0.008, z - 0.012, z + 0.012, iron)
    hardware(b, EW, EH, ET, iron, deadbolt=True)
    return b


def exterior_craftsman():
    b = base.Builder('building_door_exterior_craftsman')
    paint = base.material('DoorSlab', (0.2, 0.34, 0.27), 0.55)
    panel = base.material('DoorPanel', (0.16, 0.28, 0.22), 0.6)
    glass = base.glass_material()
    x0, x1, z0, z1 = -EW / 2 + 0.14, EW / 2 - 0.14, 1.72, EH - 0.14
    glazed_slab(b, EW, EH, ET, panel, x0, x1, z0, z1)
    lites(b, ET, glass, paint, x0, x1, z0, z1, 3, 1, bar_w=0.05)                        # three lites across the top
    # the frame over the lower part: two tall flat panels, and the shelf under the glass
    rails(b, EW, EH, ET, paint, 0.14, [(0.0, 0.24), (1.52, 1.72), (EH - 0.14, EH)])
    both_faces(b, ET, -0.05, 0.05, 0.24, 1.52, paint)
    b.box(-EW / 2 + 0.06, EW / 2 - 0.06, -ET / 2 - 0.03, -ET / 2, 1.6, 1.64, paint)       # the dentil shelf (outside face)
    for k in range(7):
        x = -EW / 2 + 0.12 + (EW - 0.24) * k / 6
        b.box(x - 0.025, x + 0.025, -ET / 2 - 0.022, -ET / 2, 1.56, 1.6, paint)
    b.box(-EW / 2, EW / 2, -ET / 2 - 0.012, ET / 2 + 0.012, 0.0, 0.03, dark_metal())
    hardware(b, EW, EH, ET, dark_metal(), deadbolt=True)
    return b


def exterior_half_lite():
    b = base.Builder('building_door_exterior_half_lite')
    paint = base.material('DoorSlab', (0.6, 0.14, 0.12), 0.5)
    raised = base.material('DoorPanel', (0.67, 0.18, 0.15), 0.5)
    white = base.material('DoorTrim', (0.94, 0.94, 0.92), 0.6)
    glass = base.glass_material()
    x0, x1, z0, z1 = -EW / 2 + 0.15, EW / 2 - 0.15, 1.18, EH - 0.16
    glazed_slab(b, EW, EH, ET, paint, x0, x1, z0, z1)
    lites(b, ET, glass, white, x0, x1, z0, z1, 3, 3)                                    # nine lites in the upper half
    for a, c, za, zb in ((x0 - 0.03, x1 + 0.03, z0 - 0.03, z0), (x0 - 0.03, x1 + 0.03, z1, z1 + 0.03)):       # the white glazing frame
        both_faces(b, ET, a, c, za, zb, white)
    for a, c in ((x0 - 0.03, x0), (x1, x1 + 0.03)):
        both_faces(b, ET, a, c, z0, z1, white)
    for xa, xb in ((-EW / 2 + 0.13, -0.05), (0.05, EW / 2 - 0.13)):                       # two raised panels below
        both_faces(b, ET, xa, xb, 0.24, 1.0, raised)
        both_faces(b, ET, xa + 0.04, xb - 0.04, 0.28, 0.96, paint, proud=PROUD + 0.006)
    b.box(-EW / 2, EW / 2, -ET / 2 - 0.012, ET / 2 + 0.012, 0.0, 0.03, metal())
    hardware(b, EW, EH, ET, metal(), deadbolt=True)
    return b


DOORS = [
    # id, name, description, builder, weight, stack, price, tags
    ('building_door_interior_flush', 'Interior Door (Flush)', 'A plain flush interior door in birch veneer, 0.9 m by 2.1 m.', interior_flush, 16.0, 6, 70, []),
    ('building_door_interior_shaker', 'Interior Door (Shaker)', 'A white shaker interior door with two flat recessed panels, 0.9 m by 2.1 m.', interior_shaker, 20.0, 6, 110, []),
    ('building_door_interior_six_panel', 'Interior Door (Six Panel)', 'A stained oak six-panel interior door, 0.9 m by 2.1 m.', interior_six_panel, 22.0, 6, 120, []),
    ('building_door_interior_french', 'Interior Door (French)', 'A white glazed interior door with ten lites, 0.9 m by 2.1 m.', interior_french, 24.0, 6, 180, []),
    ('building_door_exterior_six_panel', 'Exterior Door (Six Panel)', 'A navy six-panel steel entry door with a deadbolt, 1.2 m by 2.3 m.', exterior_six_panel, 40.0, 4, 240, []),
    ('building_door_exterior_plank', 'Exterior Door (Plank)', 'A rustic plank entry door with iron strap hinges, 1.2 m by 2.3 m.', exterior_plank, 48.0, 4, 260, []),
    ('building_door_exterior_craftsman', 'Exterior Door (Craftsman)', 'A green craftsman entry door with three lites over a dentil shelf, 1.2 m by 2.3 m.', exterior_craftsman, 44.0, 4, 320, []),
    ('building_door_exterior_half_lite', 'Exterior Door (Half Lite)', 'A red entry door with a nine-lite window in its upper half, 1.2 m by 2.3 m.', exterior_half_lite, 42.0, 4, 300, []),
]


def main():
    mod.ITEMS = DOORS       # make_building_items.main writes their models and manifests
    mod.PLACEABLE = mod.PLACEABLE | {d[0] for d in DOORS}      # a door can be stood on the ground, where a paint can paints it
    mod.main()
    for item_id, name, desc, *_ in DOORS:
        p = os.path.join(mod.BUILD, item_id, 'README.md')
        s = open(p, encoding='utf-8').read().replace('tools/make_building_items.py', 'tools/make_doors.py')
        open(p, 'w', encoding='utf-8', newline='\n').write(s)


if __name__ == '__main__':
    main()
