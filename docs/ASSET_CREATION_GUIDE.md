# Homesteader Master Asset Creation & Plugin Architecture Guide

This guide establishes the mandatory engineering and design standard for adding, modifying, generating, and documenting all assets across the **Homesteader** game project. All items are formatted as machine-readable plugin modules ready for the Homesteader plugin and modding system.

---

## 1. Directory Structure Standard

All project assets must be housed in a unified folder structure inside `C:\Users\casey\Desktop\Homesteader\assets\`, organized strictly by category and item ID:

```
assets/
└── <category>/
    └── <item_id>/
        ├── <item_id>.png              # 128×128 32-bit RGBA icon (NEVER icon.png)
        ├── <item_id>.json             # Plugin manifest (metrics, utilities, 4-stage growth)
        ├── README.md                  # Human-readable preview & quick reference
        ├── <ModelName>.obj            # Wavefront 3D mesh (or .fbx / .glb)
        ├── <ModelName>.mtl            # Material definitions for .obj
        ├── <ModelName>_Rig.fbx        # Rigging / skeletal mesh (if animated)
        └── ...                        # Additional LODs, textures, or animations
```

### Critical Rules:

1. **Icon File Name**: Must **always** be named `<item_id>.png`. **Never** name an icon `icon.png`.
2. **Item Identifier**: Snake_case lowercase without special characters (e.g., `crop_corn`, `fish_salmon`, `tree_oak_medium`, `baby_calf`).
3. **No `<item_id>.md`**: Use `<item_id>.json` as the primary machine-readable manifest for plugin loaders. Keep `README.md` as the human-readable Markdown preview.

---

## 2. 11-Category Taxonomy

Every asset must be classified into exactly one of the 11 core categories:

| Category          | Description & Scope                                                                                   | Example Items                                                                               |
| :---------------- | :---------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------ |
| **`farming`**     | Agricultural crops, seeds, produce, fertilizers, composters, furrows, and planting tools.             | `crop_corn`, `seed_tomato`, `fertilizer_organic`, `hoe_iron`, `produce_cabbage`             |
| **`ranching`**    | Livestock, baby animals, animal feed/hay, butchered meats, hides, shearing gear, and coops.           | `cow_angus`, `calf_angus`, `bale_hay_square`, `meat_steak`, `milk_pail`, `coop_chicken`     |
| **`logging`**     | Forest trees (small/med/large), timber logs, firewood, woodchips, tree taps, and felling axes.        | `tree_pine_tall`, `log_pine`, `firewood_bundle`, `axe_felling`, `wedge_splitting`           |
| **`fishing`**     | Whole fish species, clean fillets, fishing rods, lures, bobbers, and landing nets.                    | `fish_salmon`, `fish_bass`, `fillet_salmon`, `fillet_trout`, `rod_carbon`, `lure_crankbait` |
| **`building`**    | Modular structures, cabins, farmhouses, sheds, foundations, walls, doors, roofing, lumber.            | `cabin_small`, `barn`, `shed_tool`, `roof_metal`, `lumber_2x4`, `concrete_bag`              |
| **`tools`**       | General-purpose hand tools, power tools, measuring instruments, repair gear, and surveying equipment. | `hammer_claw`, `drill_cordless`, `multimeter`, `tape_measure`, `soil_tester`                |
| **`electricity`** | Power generation, solar PV, wind turbines, battery banks, inverters, breakers, and wiring.            | `solar_panel_500w`, `battery_lifepo4_5kwh`, `generator_diesel_10kw`, `wire_10awg`           |
| **`water`**       | Wells, submersible pumps, poly cisterns, pressure tanks, filtration, and PEX piping.                  | `well_casing_deep`, `pump_submersible_1hp`, `tank_poly_500gal`, `pipe_pex_1in`              |
| **`sewage`**      | Septic tanks, microbial digesters, leach field pipes, drain gravel, and outhouses.                    | `septic_tank_concrete_1000gal`, `pipe_perforated_4in`, `outhouse_rustic`                    |
| **`internet`**    | Starlink dishes, satellite mounts, Wi-Fi 6 mesh routers, ethernet, and PoE injectors.                 | `starlink_dish_standard`, `router_mesh_wifi6`, `cable_cat6_direct_burial`                   |
| **`hud`**         | UI elements, currency coins, stamina bars, health hearts, and clock dials.                            | `icon_coin_gold`, `icon_heart`, `icon_stamina`, `hud_clock_dial`                            |

---

## 3. Plugin Manifest Specification (`<item_id>.json`)

Every item folder must contain `<item_id>.json` conforming to the Homesteader Item Schema:

```json
{
	"$schema": "https://homesteader.game/schemas/item_v1.json",
	"id": "<item_id>",
	"name": "<Display Name>",
	"category": "<category>",
	"description": "<Item description>",
	"icon": "<item_id>.png",
	"properties": {
		"weight_kg": 1.0,
		"max_stack_size": 99,
		"base_value": 10.0,
		"is_consumable": false,
		"footprint": null
	},
	"models": [
		{
			"file": "<ModelName>.obj",
			"format": "obj",
			"dimensions_cm": { "x": 100.0, "y": 100.0, "z": 200.0 },
			"dimensions_m": { "x": 1.0, "y": 1.0, "z": 2.0 },
			"vertices": 240,
			"faces": 320,
			"bounding_box": {
				"min": [-50.0, -50.0, 0.0],
				"max": [50.0, 50.0, 200.0]
			}
		}
	],
	"utilities": {
		"water": {
			"metric": "None (unplumbed / dry)",
			"details": "None (unplumbed / dry)"
		},
		"electricity": {
			"metric": "None (passive / unpowered)",
			"details": "None (passive / unpowered)"
		},
		"sewage": {
			"metric": "None (no waste discharge)",
			"details": "None (no waste discharge)"
		},
		"battery": {
			"metric": "None (no internal battery)",
			"details": "None (no internal battery)"
		},
		"internet": {
			"metric": "None (offline / non-networked)",
			"details": "None (offline / non-networked)"
		}
	},
	"growth": {
		"is_growable": true,
		"growth_type": "tree",
		"species": "oak",
		"max_age": 100,
		"time_unit": "days",
		"total_stages": 4,
		"current_stage": {
			"stage": 3,
			"name": "medium",
			"age_min": 40,
			"age_max": 75
		},
		"stages": [
			{
				"stage": 1,
				"name": "sapling",
				"item_id": "sapling_oak",
				"age_min": 0,
				"age_max": 15
			},
			{
				"stage": 2,
				"name": "small",
				"item_id": "tree_oak_small",
				"age_min": 15,
				"age_max": 40
			},
			{
				"stage": 3,
				"name": "medium",
				"item_id": "tree_oak_medium",
				"age_min": 40,
				"age_max": 75
			},
			{
				"stage": 4,
				"name": "large (mature)",
				"item_id": "tree_oak_large",
				"age_min": 75,
				"age_max": 100
			}
		]
	},
	"plugin_metadata": {
		"version": "1.0.0",
		"author": "Homesteader Core",
		"compatible_api": "v1"
	}
}
```

---

## 4. 4-Stage Growth Lifecycle Progression

All items that grow in the game world must have an explicit 4-stage lifecycle model defined in their manifest. Each stage represents a discrete, interactable in-game asset with its own 3D model, bounding box, and icon:

### A. Forest Trees (Logging)

- **Lifecycle Sequence**: `sapling` (1) $\rightarrow$ `small` (2) $\rightarrow$ `medium` (3) $\rightarrow$ `large (mature)` (4)
- **Max Age Input**: 100 days (timber species: Oak, Pine, Birch, Maple) / 80-90 days (Fruit & Ornamental: Apple, Willow, Poplar).
- **Stage Brackets**:
  - Stage 1: `0 – 15 days` (Sapling)
  - Stage 2: `15 – 40 days` (Small tree, initial wood harvestable)
  - Stage 3: `40 – 75 days` (Medium tree, can be tapped for syrup/sap)
  - Stage 4: `75 – 100 days` (Mature canopy, maximum timber yield)

### B. Agricultural Crops (Farming)

- **Lifecycle Sequence**: `seed` (1) $\rightarrow$ `sprout` (2) $\rightarrow$ `growing` (3) $\rightarrow$ `large (mature)` (4)
- **Max Age Input**: 14 – 30 days depending on crop cultivar.
- **Stage Brackets**:
  - Stage 1: `0 – 25% max age` (Planted seed)
  - Stage 2: `25 – 50% max age` (Sprout / seedling emergence)
  - Stage 3: `50 – 75% max age` (Stalk, vine, or vegetative growth)
  - Stage 4: `75 – 100% max age` (Mature, ready for sickle/harvest)

### C. Livestock & Farm Animals (Ranching)

- **Lifecycle Sequence**: `baby` (1) $\rightarrow$ `juvenile` (2) $\rightarrow$ `adult` (3) $\rightarrow$ `large (mature)` (4)
- **Max Age Input**: 180 – 900 days (e.g., Chickens 180d, Swine 365d, Sheep 500d, Cattle 730d, Horses 900d).
- **Stage Brackets**:
  - Stage 1: `0 – 15% max age` (Baby / nursing: calf, chick, piglet, lamb, kid)
  - Stage 2: `15 – 40% max age` (Juvenile / weaned animal)
  - Stage 3: `40 – 70% max age` (Adult breeding animal: hen, cow, sow, ewe)
  - Stage 4: `70 – 100% max age` (Mature prime livestock: milk producer, wool bearer, draft horse)

---

## 5. Item Icon Standards

All item icons must adhere strictly to the project icon formatting rules:

1. **Dimensions & Canvas**: Exactly **128 × 128 pixels**, 32-bit RGBA.
2. **Safe Margin**: Item geometry must fit within `MAX_ITEM_DIM = 104 px` centered, guaranteeing at least **12px of clean transparent padding** on all 4 borders.
3. **100% Perimeter Alpha 0**: Outer border pixels (`x=0, x=127, y=0, y=127`) must have `alpha = 0`.
4. **No Frames or Borders**: Zero card outlines, square frames, slot boxes, halos, or artificial backgrounds.
5. **3D Low-Poly Faceted Aesthetic**: Isometric 3/4 front view (~35° pitch, 45° yaw), top-left key light.
6. **File Naming**: Strictly `<item_id>.png` (e.g., `crop_corn.png`, `barn.png`).

---

## 6. Automation Tooling

To regenerate manifests, compute geometry bounding boxes, and update the catalog:

```powershell
python tools/build_unified_assets_catalog.py
```
