# Lavender Homestead — Example Mod

A minimal but complete reference mod for the Homesteader mod system. Copy this
folder, rename it, and swap the content for your own.

See [docs/MODDING_GUIDE.md](../../docs/MODDING_GUIDE.md) for the full spec.

---

## What this mod adds

| Type        | Id                            | Spawnable? | What it is                                                                 |
| :---------- | :---------------------------- | :--------- | :------------------------------------------------------------------------- |
| `biome`     | `biome_lavender_fields`       | —          | Purple flowering meadows baked into the world.                             |
| `structure` | `struct_lavender_drying_shed` | **Yes**    | A small timber drying shed, scattered into the lavender fields and meadows. |
| `food`      | `food_tea_lavender`           | No         | A calming herbal tea — a craftable item only.                              |

This mod demonstrates the two asset features worth copying:

- **`is_spawnable`** — the shed is scattered by world generation into the biomes
  listed in its `spawning.biomes[]`; the tea is data-only. In the Asset Kit that's
  the **Spawnable in World** toggle plus the **Choose Biomes…** picker.
- **`namespace`** — the shed declares `"namespace": "lavender_homestead"`, so its id
  can never collide with a same-named asset from another mod. The registry keys on
  the combined `lavender_homestead:struct_lavender_drying_shed`.

## Layout

```
example_lavender_homestead/
├── mod.json                                  <- the manifest (required)
├── biomes/
│   └── biome_lavender_fields.json
└── assets/
    ├── structures/
    │   └── struct_lavender_drying_shed.json
    └── food/
        └── food_tea_lavender.json
```

## Install

Copy this folder into your mods directory:

```
<persistentDataPath>/Mods/example_lavender_homestead/
```

…or zip it up and drop `example_lavender_homestead.zip` into the same place.
Both work identically.

## Verify it loaded

Press Play and check the console for:

```
[Mods] Applied example_lavender_homestead: +1 biomes, +2 assets, 0 files
```

A `modload_report.txt` is also written beside the mods folder.

## Try changing something

- Set `"priority": 20` on the biome to make it win more collisions.
- Change `"color_hex"` to see the map/legend color update.
- Add a second biome file to `biomes/` — the `"path": "biomes/*.json"`
  wildcard picks up new files with no manifest change.
- Flip the shed's `"is_spawnable"` to `false` and it stops appearing in the world
  while staying craftable.