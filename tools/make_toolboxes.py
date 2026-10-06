"""
Builds the three toolboxes in headless Blender and writes their manifests (assets/tools/<id>/): free, local, low-poly, GLB with plain colour materials.

    blender --background --python tools/make_toolboxes.py
    python tools/render_icon_from_model.py assets/tools/<id>/<id>.glb assets/tools/<id>/<id>.png        (each one)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

  tool_toolbox_small    a red steel hand toolbox with a hip-roof lid, a carry handle and one latch (holds 10 kg)
  tool_toolbox_medium   a black plastic toolbox with a yellow lid, organiser bins in the lid, a folding handle and two latches (holds 25 kg)
  tool_toolbox_large    a blue steel jobsite chest on skids with side handles, a lid lip and a lock hasp (holds 80 kg)

Each is a CONTAINER (the manifest's container block) that takes TOOLS ONLY: accepts = ["tools"], the item category (ContainerRules.Accepts matches a
category name as well as #tags and item ids; a container never goes inside a container, so baskets and buckets stay out). They are closed boxes,
so show_fill is off. An item that is already in the kit keeps its name, price and the rest: only the model entry and dimensions are updated.

Pivot at the middle of the footprint with the bottom at z = 0, front (the latches) = -Y.
"""
import copy
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_structure_stages as base  # noqa: E402

M = base.material
TOOLS = os.path.join(base.ROOT, 'assets', 'tools')


def small():
    """A classic steel hand toolbox: a tray body, a hip-roof lid, a tube handle on two brackets, one draw latch."""
    b = base.Builder('tool_toolbox_small')
    red = M('ToolboxRed', (0.72, 0.1, 0.08), 0.45)
    dark = M('ToolboxRedDark', (0.5, 0.07, 0.06), 0.5)
    steel = M('ToolboxSteel', (0.72, 0.73, 0.75), 0.35)
    w, d, h = 0.42, 0.18, 0.11
    b.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, red)                                   # the body
    b.box(-w / 2 - 0.003, w / 2 + 0.003, -d / 2 - 0.003, d / 2 + 0.003, h - 0.012, h, dark)      # the rolled rim
    # the hip-roof lid: three steps narrowing to the ridge
    for k, (inset, z0, z1) in enumerate(((0.0, h, h + 0.03), (0.022, h + 0.03, h + 0.055), (0.05, h + 0.055, h + 0.072))):
        b.box(-w / 2, w / 2, -d / 2 + inset, d / 2 - inset, z0, z1, red if k % 2 == 0 else dark)
    top = h + 0.072
    for x in (-0.09, 0.09):                                                            # the handle brackets and the grip
        b.box(x - 0.008, x + 0.008, -0.012, 0.012, top, top + 0.034, steel)
    b.box(-0.105, 0.105, -0.009, 0.009, top + 0.034, top + 0.05, steel)
    b.box(-0.022, 0.022, -d / 2 - 0.009, -d / 2, h - 0.03, h + 0.026, steel)             # the latch
    b.box(-0.03, 0.03, -d / 2 - 0.012, -d / 2 - 0.009, h + 0.004, h + 0.014, steel)
    for x in (-w / 2 + 0.06, w / 2 - 0.06):                                            # the hinges at the back
        b.box(x - 0.02, x + 0.02, d / 2, d / 2 + 0.006, h - 0.01, h + 0.012, steel)
    return b


def medium():
    """A plastic toolbox: a black tub, a yellow lid with two clear-topped organiser bins, a folding handle, two latches."""
    b = base.Builder('tool_toolbox_medium')
    black = M('ToolboxBlack', (0.1, 0.1, 0.11), 0.6)
    yellow = M('ToolboxYellow', (0.95, 0.74, 0.08), 0.5)
    grey = M('ToolboxGrey', (0.3, 0.31, 0.33), 0.6)
    clear = M('OrganiserLid', (0.75, 0.82, 0.86), 0.2)
    w, d, h = 0.58, 0.28, 0.2
    b.box(-w / 2 + 0.012, w / 2 - 0.012, -d / 2 + 0.012, d / 2 - 0.012, 0.0, 0.02, black)       # the foot of the tub
    b.box(-w / 2, w / 2, -d / 2, d / 2, 0.02, h, black)                                # the tub
    for x in (-w * 0.3, 0.0, w * 0.3):                                                 # the ribs moulded into the front and back
        b.box(x - 0.012, x + 0.012, -d / 2 - 0.004, d / 2 + 0.004, 0.03, h - 0.02, grey)
    b.box(-w / 2 - 0.006, w / 2 + 0.006, -d / 2 - 0.006, d / 2 + 0.006, h, h + 0.05, yellow)     # the lid
    b.box(-w / 2 + 0.03, w / 2 - 0.03, -d / 2 + 0.03, d / 2 - 0.03, h + 0.05, h + 0.062, yellow)
    for x0, x1 in ((-w / 2 + 0.05, -0.07), (0.07, w / 2 - 0.05)):                        # the organiser bins in the lid
        b.box(x0, x1, -d / 2 + 0.05, d / 2 - 0.05, h + 0.062, h + 0.068, clear)
    b.box(-0.055, 0.055, -0.07, 0.07, h + 0.062, h + 0.07, black)                        # the handle well
    b.box(-0.045, 0.045, -0.012, 0.012, h + 0.07, h + 0.084, black)                      # the folding handle, lying flat
    for x in (-w * 0.27, w * 0.27):                                                    # the two latches
        b.box(x - 0.03, x + 0.03, -d / 2 - 0.014, -d / 2 - 0.006, h - 0.045, h + 0.03, yellow)
        b.box(x - 0.022, x + 0.022, -d / 2 - 0.018, -d / 2 - 0.014, h - 0.03, h - 0.012, black)
    for x in (-w / 2 + 0.09, w / 2 - 0.09):                                            # the hinges
        b.box(x - 0.03, x + 0.03, d / 2 + 0.006, d / 2 + 0.014, h - 0.012, h + 0.02, black)
    return b


def large():
    """A steel jobsite chest: a deep box on two skids, a lid with a lip, recessed side handles, a lock hasp, a stencil panel."""
    b = base.Builder('tool_toolbox_large')
    blue = M('ChestBlue', (0.1, 0.27, 0.55), 0.45)
    dark = M('ChestBlueDark', (0.07, 0.18, 0.38), 0.5)
    steel = M('ChestSteel', (0.62, 0.64, 0.66), 0.35)
    black = M('ChestBlack', (0.08, 0.08, 0.09), 0.6)
    plate = M('ChestPlate', (0.92, 0.92, 0.9), 0.6)
    w, d, h = 0.9, 0.5, 0.42
    skid = 0.05
    for x in (-w / 2 + 0.1, w / 2 - 0.1):                                              # the skids
        b.box(x - 0.045, x + 0.045, -d / 2 + 0.01, d / 2 - 0.01, 0.0, skid, dark)
    b.box(-w / 2, w / 2, -d / 2, d / 2, skid, skid + h, blue)                          # the box
    for z in (skid + h * 0.33, skid + h * 0.66):                                       # the stiffening ribs pressed round it
        b.box(-w / 2 - 0.006, w / 2 + 0.006, -d / 2 - 0.006, d / 2 + 0.006, z - 0.012, z + 0.012, dark)
    top = skid + h
    b.box(-w / 2 - 0.012, w / 2 + 0.012, -d / 2 - 0.012, d / 2 + 0.012, top, top + 0.07, blue)  # the lid, with its lip over the box
    b.box(-w / 2 + 0.05, w / 2 - 0.05, -d / 2 + 0.05, d / 2 - 0.05, top + 0.07, top + 0.082, dark)
    for s in (-1, 1):                                                                  # the side handles in their recesses
        x = s * w / 2
        b.box(min(x, x + s * 0.004), max(x, x + s * 0.004), -0.09, 0.09, skid + h * 0.5, skid + h * 0.72, black)
        b.box(min(x + s * 0.004, x + s * 0.03), max(x + s * 0.004, x + s * 0.03), -0.06, 0.06, skid + h * 0.56, skid + h * 0.6, steel)
    b.box(-0.04, 0.04, -d / 2 - 0.02, -d / 2 - 0.012, top - 0.07, top + 0.03, steel)     # the lock hasp
    b.box(-0.025, 0.025, -d / 2 - 0.03, -d / 2 - 0.02, top - 0.06, top - 0.025, black)   # and its padlock
    b.box(-0.2, 0.2, -d / 2 - 0.002, -d / 2, skid + h * 0.4, skid + h * 0.58, plate)     # the stencil panel
    for x in (-w * 0.3, w * 0.3):                                                      # the hinges at the back
        b.box(x - 0.05, x + 0.05, d / 2, d / 2 + 0.014, top - 0.03, top + 0.03, steel)
    return b


# id, name, description, builder, own weight kg, price, capacity kg, placed stacking limit
BOXES = [
    ('tool_toolbox_small', 'Small Toolbox', 'A red steel hand toolbox with a carry handle. It holds up to 10 kg of tools, and only tools.', small, 0.1, 25, 10, 1),
    ('tool_toolbox_medium', 'Medium Toolbox', 'A black and yellow plastic toolbox with organiser bins in the lid. It holds up to 25 kg of tools, and only tools.', medium, 0.1, 45, 25, 2),
    ('tool_toolbox_large', 'Large Tool Chest', 'A blue steel jobsite tool chest on skids with a lockable lid. It holds up to 80 kg of tools, and only tools.', large, 0.1, 180, 80, 1),
]


def main():
    tmpl = json.load(open(os.path.join(TOOLS, 'tool_cement_mixer', 'tool_cement_mixer.json'), encoding='utf-8'))
    for item, name, desc, build, weight, price, capacity, stacking in BOXES:
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        obj = build().finish()
        folder = os.path.join(TOOLS, item)
        os.makedirs(folder, exist_ok=True)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        mn = [min(v.co[i] for v in obj.data.vertices) for i in range(3)]
        mx = [max(v.co[i] for v in obj.data.vertices) for i in range(3)]
        sx, sy, sz = [round(mx[i] - mn[i], 3) for i in range(3)]
        path = os.path.join(folder, item + '.json')
        if os.path.exists(path):
            m = json.load(open(path, encoding='utf-8'))
        else:
            m = copy.deepcopy(tmpl)
            m['id'] = item
            m['icon'] = item + '.png'
            m['name'] = name
            m['description'] = desc
            m['properties'].update({'weight_kg': weight, 'base_value': price, 'max_stack_size': 1, 'placeable': True, 'display_weight': True,
                                    'is_buyable': True, 'stores': ['depot'], 'sale_unit': 'ea'})
            m['utilities']['electricity'] = {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'}
            m['category_fields'] = {'dimensions_m': {}, 'fuel_type': 'none', 'fuel_consumption_l_per_min': 0, 'power_draw_w': 0, 'tank_capacity_l': 0}
            m['container'] = {'capacity_kg': capacity, 'stacking_limit': stacking, 'accepts': ['tools'], 'show_fill': False}
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': sx, 'y': sz, 'z': sy}, 'triangles': tris}]
        m['category_fields']['dimensions_m'] = {'width': round(sx, 2), 'depth': round(sy, 2), 'height': round(sz, 2)}
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(m, f, indent=2)
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# %s\n\n%s\n\nProcedural model (tools/make_toolboxes.py), %d triangles, %.2f x %.2f x %.2f m. A container that accepts the `tools` category only '
                    '(capacity %s kg).\n' % (m['name'], m['description'], tris, sx, sy, sz, m.get('container', {}).get('capacity_kg')))
        print('toolbox', item, '|', m['name'], '|', tris, 'tris', sx, sy, sz)


if __name__ == '__main__':
    main()
