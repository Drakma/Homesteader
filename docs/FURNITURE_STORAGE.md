# Furniture storage: what holds what

Every room-pack piece (kitchen, living, bedroom, bathroom, laundry, garage, dining, office) that can hold things does. The single source is `tools/furniture_storage.py`
(table + `apply()`); every `make_<pack>_assets.py` calls it while writing a manifest, and `python tools/furniture_storage.py` backfills existing manifests (idempotent).
Change a capacity or a shelf height THERE, then rerun it, then `generate_unity_asset_catalog.py` and `package_catalog_as_mods.py`.

## Two kinds

- **Closed** (drawers, doors, lids): a manifest `container` block. The C key opens it, capacity is a weight in kg, `accepts` is empty (anything), contents are not drawn.
  Contents are saved with the placed piece (`SavedPlaced.content*`).
- **Open** (real shelves): `support_surface` + `deck_heights`, the TOP FACE of each shelf in metres, lowest first, measured from the model code. Things are placed ON a shelf
  (`PalletDeck.cs`): point at the open front of a shelf, like things stack on each other up to their stacking limit, and never higher than the shelf above allows
  (`PalletDeck.Clearance`: gap to the next shelf minus a 3.5 cm board). A top shelf that is the model's own top (a desk, a cabinet top) is open above, up to `TopLimit` (1.6 m).
  What stands on a shelf is a placed object and is saved with the world; a piece that still carries things cannot be picked up.

A piece can be both. Wall items are never containers (a mounted thing has no contents window); a wall shelf uses `shelf: true` (single top face, `docs/ATTACHED_ITEMS.md`).

## Closed storage (capacity kg)

| Pack | Piece: kg |
|---|---|
| Living | sideboard 60, tv stand 40, toy chest 40, display cabinet (lower part) 30, end table 8 (classic drawer only), console table 10 (classic drawer only) |
| Bedroom | nightstand 15, dresser 60, chest of drawers 50, dressing table 20, wardrobe 90, blanket chest 40, writing desk 25 |
| Bathroom | single vanity 30, double vanity 50, linen cabinet 30, hamper 12 |
| Laundry | locker unit 60, folding counter 30, laundry basket 12, sorter 15 |
| Garage | base cabinet 60, tall cabinet 90, parts cabinet 25, rolling tool chest 70, top tool chest 25 |
| Dining | china cabinet (lower part) 35 |
| Office | writing desk 25, executive desk 40, credenza 60, filing cabinet 40, lateral file 55 |
| Kitchen | sink cabinet 30 (the fridges, freezers, base cabinets, pantry, island and cart already had one) |

## Open shelves (top face of each shelf, m)

| Piece | Shelves |
|---|---|
| Bookshelf | classic 0.125, 0.525, 0.925, 1.325, 1.705; modern 0.065 for the first |
| Coffee table | lower shelf 0.15 (modern 0.185), top 0.45 |
| Display cabinet | 0.812, 1.132, 1.452 (glass shelves) |
| China cabinet | 0.93, 1.232, 1.532, 1.832 |
| Bar cart | 0.21, 0.57, 0.85 |
| Wine rack | 0.02, 0.32, 0.61, 0.90, 1.20 |
| Laundry storage shelves | 0.225, 0.645, 1.065, 1.485, 1.80 |
| Shoe rack | 0.10, 0.28, 0.46 |
| Mudroom bench | classic 0.17, 0.50; modern 0.16, 0.46 |
| Steel shelving | 0.15, 0.63, 1.11, 1.59, 1.90 |
| Workbench | lower shelf 0.20 (modern 0.23), top 0.92 |
| Kitchen cart | lower shelf 0.23, top 0.88 |
| Kitchen spice rack | wall shelf (`shelf: true`) |

Tables, desks, counters, dressers and other single-top pieces keep one deck at their top.

## Things removed from the models

Shelves ship empty; the player fills them. Removed: books (bookshelf), plates and vase (display cabinet), plates (china cabinet), bottles and glasses (bar cart),
twelve bottles (wine rack), baskets and cushions (laundry storage shelves), boxes and bins (steel shelving), jars (kitchen spice rack). Models, icons and descriptions regenerated.
Still baked in on purpose (they are part of the piece, not stock): bedding on beds, the towel on the towel shelf and bar, clothes in the laundry basket, bags on the sorter.

## Code change

`PalletDeck.Clearance` used to give the topmost shelf only `model height - shelf - board`, which is about 5 cm for a desk or cabinet top (a single deck at the model's height), so
almost nothing could be put on it. A top shelf within 12 cm of the model's height is now open above (`TopLimit`).
