# Kitchen pack

A kitchen category of its own (`assets/kitchen/<id>/`, ids `kitchen_*`, shop chip "Kitchen", sold at the furniture store "Sofa So Good"), separate from the kit's general
`appliances`, `building` and other furniture items, which are not touched. 143 items, all procedural: free, local, low-poly (240 to 1,800 triangles each) with real detail
(rounded edges, proud doors with a dark seam, handles on posts, knobs, burners and grates, shaker panels, faucets) and procedural textures (brushed steel, oak, butcher block,
black granite, white marble).

## What is in it

| Group | Models | Finishes |
|---|---|---|
| Appliances | top-freezer, side-by-side and French-door refrigerators, upright and chest freezers, gas range, built-in cooktop, double oven tower, countertop and over-the-range microwaves, range hood, dishwasher, sink cabinet, toaster, kettle, coffee maker, stand mixer, blender, toaster oven | Stainless Steel, White, Black |
| Cabinetry | base, double-door, drawer and corner base cabinets, wall, wide wall and glass-door wall cabinets, pantry, island, work counter, open shelf, cart | White (shaker doors, marble top), Oak (slab doors, butcher-block top), Black (slab doors, granite top) |
| Tables and seating | dining, round pedestal and bistro tables, dining chair, counter stool, bench | White, Oak, Black |
| Accessories | trash can, canisters, utensil crock, paper towel holder, bread box (steel / white / black); stock pot, saucepan, skillet, dish rack, hanging pot rack; cutting board, fruit bowl, knife block, spice rack (oak / white / black) | as listed |

Wall items (over-the-range microwave, range hood, wall cabinets, open shelf, pot rack, spice rack) are `attach_surface: wall`, `attach_side: interior`, not `placeable`: mount them on a
finished building's wall like a light (docs/ATTACHED_ITEMS.md). Their models have the back on the plane y = 0 and stick out towards -y. The open shelf is a `shelf`. Cabinets, the island, the
work counter, the cart, tables and the bench carry `support_surface` with `deck_heights` at their top, so things can be stood on them.

## How it is built

- `tools/kitchen_lib.py`: the modelling kit (a bmesh builder with bevelled boxes, rounded prisms, cylinders, lathes and extruded outlines, box-projected UVs in metres), the procedural textures
  (numpy, seeded, tileable, written to `assets/_kitchen_textures/` and embedded in each GLB), the materials and the three appliance finishes.
- `tools/kitchen_models.py`: one function per model. Metres, centred on x and y, bottom at z = 0, FRONT = -Y.
- `tools/make_kitchen_assets.py`: the item list (names, descriptions, weights, prices), the GLB export and the manifests / READMEs; `--icons` renders the 128 px icons from the GLBs.
- `tools/kitchen_preview.py`: a contact sheet of any models and finishes, for judging them while they are built.

```
blender --background --python tools/make_kitchen_assets.py                      # every item (or: -- fridge_top range_oven)
python tools/make_kitchen_assets.py --icons --force                              # the icons
python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
blender --background --python tools/kitchen_preview.py -- out.png fridge_top:stainless kitchen_cart:oak
```

The category schema is `assets/_schemas/kitchen.schema.json` (`kitchen_kind`, `finish`, `power_draw_w`; the size comes from `_base_dimensions`). The category is registered in `assets/kit_config.json`.
The models do not do anything yet (nothing cooks or chills): they are furniture with a size, a weight and a price. `power_draw_w` is there for when they do.
