# Lots

A LOT is a flat area of any size and shape paved with dirt, gravel, asphalt or concrete: a yard, a drive, a parking area, a pad, a pen floor. Like paths and roads it is a blueprint bought once at the depot
(`lot_dirt`, `lot_gravel`, `lot_asphalt`, `lot_concrete`; `tools/make_lot_blueprints.py` writes the manifests and icons).

## Laying one
- Hold the blueprint and left click the CORNERS on land you own. One corner then the opposite one makes a RECTANGLE of any size (the preview follows the cursor); three or more corners make any other shape (at most 24).
- Enter lays it. Backspace or a right click takes the last corner back; Esc (or another slot) throws the plan away.
- A lot is 4 m^2 to 2,500 m^2, on land you own, out of water, with no crossing edges. Trees, planted crops and placed objects (a pile of material does not count) inside it refuse it: fell, harvest or move them first. Plants and rocks that are left are cleared when it is laid.
- The material is the blueprint's `lot_material_item`, one per `lot_m2_per_item` square metres (a lot of A m^2 uses ceil(A / that)), from the toolbar and the 4 m work site round the FIRST corner (as for paths and fences).
  Dirt: small dirt pile, 3.5 m^2 each. Gravel: medium gravel pile, 8 m^2. Asphalt is a MIX: a medium gravel pile (the aggregate) per 6 m^2 AND a bucket of bitumen (`building_bitumen_bucket`, 20 litres) per 4 m^2. Bitumen is the `~bitumen` equivalency: a bucket, or a pallet of 9 or 18 buckets (`building_bitumen_bucket_stack_9` / `_stack_18`); a pallet that pays more than is owed is broken and the change is dropped as buckets at the work site. Concrete: a bag of concrete mix, 1.5 m^2.
- The ped walks to the nearest corner and works kneeling (2 to 14 seconds, by size); a movement key or Esc stops it and nothing is laid or used.
- **Shift + right click** on a lot with a pickaxe or a shovel breaks it up (nothing comes back). A newer lot lies a hair above an older one where they overlap.

## How it is drawn
`Growth/LotRun.cs`: the polygon is cut into triangles (ear clipping), then cut small (no edge over 1.5 m) so it follows the ground, and drawn 5 cm above it with a tiling surface of its own (dirt 4 m, gravel 2.5 m, asphalt 6 m, concrete 3 m slabs with an expansion joint along two edges). It has no collider: it is ground you walk, drive and build on.
`Growth/LotBuilder.cs` is the input, the preview and the laying. Saved in `GameSave.lots` (style, blueprint id, corner points).

## Manifest fields (base schema `_base_fences_paths`)
`lot_style` (dirt, gravel, asphalt, concrete), `lot_material_item`, `lot_m2_per_item`, and for a mix `lot_binder_item` (an item id or a ~equivalency) with `lot_binder_m2_per_item`; the catalog generator passes them on (`AssetCatalogItem.lot_*`).

Not done yet: concrete asks only for the bag of mix (no water or mixer, unlike the structure recipes).
