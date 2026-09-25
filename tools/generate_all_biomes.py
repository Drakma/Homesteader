import os
import json

BASE_DIR = r"C:\Users\casey\Desktop\Homesteader\assets"
BIOMES_DIR = os.path.join(BASE_DIR, "biomes")
os.makedirs(BIOMES_DIR, exist_ok=True)

# Calibrated for a 500m x 500m compact playable world map:
# Biome patches are ~30m - 90m across, creating cozy homestead parcels.
BIOMES = [
    {
        "id": "biome_river",
        "name": "River & Creek System",
        "priority": 12,
        "description": "Continuous winding fluvial river corridor with moving water, smoothed gravel bars, and muddy littoral margins.",
        "color_hex": "#06b6d4",
        "moisture": 1.0,
        "nutrients": 0.50,
        "noise": {
            "frequency": 0.010,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.94,
            "dither_bandwidth": 0.015
        },
        "elevation": {
            "base_offset_m": -3.5,
            "noise_amplitude_m": 0.8,
            "noise_frequency": 0.018,
            "max_slope_deg": 15.0
        },
        "generative_ground": {
            "shader_mode": "water_flow",
            "primary_color_hex": "#0284c7",
            "secondary_color_hex": "#38bdf8",
            "slope_color_hex": "#64748b",
            "pattern_scale": 2.5,
            "pattern_intensity": 0.75,
            "normal_micro_roughness": 0.15
        }
    },
    {
        "id": "biome_lake",
        "name": "Deep Lake",
        "priority": 11,
        "description": "Expansive open body of water with deep benthic depths, calm surface reflections, and sandy beachfront perimeters.",
        "color_hex": "#1d4ed8",
        "moisture": 1.0,
        "nutrients": 0.40,
        "noise": {
            "frequency": 0.009,
            "octaves": 3,
            "persistence": 0.45,
            "threshold": 0.88,
            "dither_bandwidth": 0.02
        },
        "elevation": {
            "base_offset_m": -5.0,
            "noise_amplitude_m": 1.2,
            "noise_frequency": 0.015,
            "max_slope_deg": 12.0
        },
        "generative_ground": {
            "shader_mode": "water_lake",
            "primary_color_hex": "#1e3a8a",
            "secondary_color_hex": "#2563eb",
            "slope_color_hex": "#94a3b8",
            "pattern_scale": 6.0,
            "pattern_intensity": 0.5,
            "normal_micro_roughness": 0.1
        }
    },
    {
        "id": "biome_pond",
        "name": "Pond & Wetland Basin",
        "priority": 10,
        "description": "Amorphous water depression with deep basin water, muddy waterline banks, sandy littoral shores, and dense cattail reed clusters.",
        "color_hex": "#3b82f6",
        "moisture": 0.95,
        "nutrients": 0.65,
        "noise": {
            "frequency": 0.018,
            "octaves": 3,
            "persistence": 0.45,
            "threshold": 0.82,
            "dither_bandwidth": 0.025
        },
        "elevation": {
            "base_offset_m": -3.0,
            "noise_amplitude_m": 0.8,
            "noise_frequency": 0.022,
            "max_slope_deg": 18.0
        },
        "generative_ground": {
            "shader_mode": "water_basin",
            "primary_color_hex": "#1e40af",
            "secondary_color_hex": "#78350f",
            "slope_color_hex": "#d97706",
            "pattern_scale": 1.8,
            "pattern_intensity": 0.6,
            "normal_micro_roughness": 0.2
        }
    },
    {
        "id": "biome_farmland",
        "name": "Farmland (Tilled Rows)",
        "priority": 8,
        "description": "Agricultural fields featuring distinct parallel tilled soil furrows, high moisture retention, and rich nutrient-dense dark loam.",
        "color_hex": "#78350f",
        "moisture": 0.65,
        "nutrients": 0.90,
        "noise": {
            "frequency": 0.015,
            "octaves": 2,
            "persistence": 0.5,
            "threshold": 0.66,
            "dither_bandwidth": 0.03
        },
        "elevation": {
            "base_offset_m": 0.5,
            "noise_amplitude_m": 1.0,
            "noise_frequency": 0.010,
            "max_slope_deg": 8.0
        },
        "generative_ground": {
            "shader_mode": "tilled_furrows",
            "primary_color_hex": "#451a03",
            "secondary_color_hex": "#290e02",
            "slope_color_hex": "#78350f",
            "pattern_scale": 1.0,
            "pattern_intensity": 0.85,
            "normal_micro_roughness": 0.4
        }
    },
    {
        "id": "biome_maintained_grass",
        "name": "Maintained Lawn",
        "priority": 7,
        "description": "Pristine domestic yard grass displaying alternating directional mower stripes, high turf density, and tidy homestead curb appeal.",
        "color_hex": "#10b981",
        "moisture": 0.55,
        "nutrients": 0.70,
        "noise": {
            "frequency": 0.020,
            "octaves": 2,
            "persistence": 0.5,
            "threshold": 0.68,
            "dither_bandwidth": 0.025
        },
        "elevation": {
            "base_offset_m": 0.3,
            "noise_amplitude_m": 0.6,
            "noise_frequency": 0.012,
            "max_slope_deg": 12.0
        },
        "generative_ground": {
            "shader_mode": "mower_stripes",
            "primary_color_hex": "#15803d",
            "secondary_color_hex": "#22c55e",
            "slope_color_hex": "#4b5563",
            "pattern_scale": 1.2,
            "pattern_intensity": 0.65,
            "normal_micro_roughness": 0.15
        }
    },
    {
        "id": "biome_wetland_marsh",
        "name": "Bog & Peat Marsh",
        "priority": 6,
        "description": "Soggy wetland basin saturated with standing water pools, squishy peat moss, high organic decomposition, and hummocks of marsh reeds.",
        "color_hex": "#365314",
        "moisture": 0.90,
        "nutrients": 0.60,
        "noise": {
            "frequency": 0.015,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.62,
            "dither_bandwidth": 0.04
        },
        "elevation": {
            "base_offset_m": -1.0,
            "noise_amplitude_m": 1.0,
            "noise_frequency": 0.020,
            "max_slope_deg": 10.0
        },
        "generative_ground": {
            "shader_mode": "standard_dither",
            "primary_color_hex": "#3f3f26",
            "secondary_color_hex": "#2e2b17",
            "slope_color_hex": "#57534e",
            "pattern_scale": 1.5,
            "pattern_intensity": 0.7,
            "normal_micro_roughness": 0.35
        }
    },
    {
        "id": "biome_maple_forest",
        "name": "Maple Forest",
        "priority": 5,
        "description": "Temperate deciduous forest characterized by sugar maples, thick autumnal red and golden leaf litter carpeting the rich forest floor.",
        "color_hex": "#ea580c",
        "moisture": 0.60,
        "nutrients": 0.75,
        "noise": {
            "frequency": 0.013,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.56,
            "dither_bandwidth": 0.05
        },
        "elevation": {
            "base_offset_m": 2.5,
            "noise_amplitude_m": 3.5,
            "noise_frequency": 0.014,
            "max_slope_deg": 25.0
        },
        "generative_ground": {
            "shader_mode": "leaf_litter",
            "primary_color_hex": "#9a3412",
            "secondary_color_hex": "#c2410c",
            "slope_color_hex": "#78350f",
            "pattern_scale": 1.4,
            "pattern_intensity": 0.6,
            "normal_micro_roughness": 0.25
        }
    },
    {
        "id": "biome_birch_forest",
        "name": "Birch Grove",
        "priority": 5,
        "description": "Luminous open deciduous grove dominated by white-barked birch trees, light mossy undergrowth, and sandy-loam soil.",
        "color_hex": "#a3e635",
        "moisture": 0.50,
        "nutrients": 0.60,
        "noise": {
            "frequency": 0.014,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.54,
            "dither_bandwidth": 0.05
        },
        "elevation": {
            "base_offset_m": 1.8,
            "noise_amplitude_m": 3.0,
            "noise_frequency": 0.014,
            "max_slope_deg": 22.0
        },
        "generative_ground": {
            "shader_mode": "standard_dither",
            "primary_color_hex": "#84cc16",
            "secondary_color_hex": "#bef264",
            "slope_color_hex": "#a8a29e",
            "pattern_scale": 1.2,
            "pattern_intensity": 0.5,
            "normal_micro_roughness": 0.2
        }
    },
    {
        "id": "biome_oak_forest",
        "name": "Oak Woodland",
        "priority": 5,
        "description": "Stately hardwood forest with mature broadleaf oaks, shaded understory, fallen acorns, and rich humus-laden topsoil.",
        "color_hex": "#15803d",
        "moisture": 0.55,
        "nutrients": 0.80,
        "noise": {
            "frequency": 0.012,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.53,
            "dither_bandwidth": 0.05
        },
        "elevation": {
            "base_offset_m": 3.0,
            "noise_amplitude_m": 3.5,
            "noise_frequency": 0.014,
            "max_slope_deg": 26.0
        },
        "generative_ground": {
            "shader_mode": "leaf_litter",
            "primary_color_hex": "#166534",
            "secondary_color_hex": "#3f2c1d",
            "slope_color_hex": "#57534e",
            "pattern_scale": 1.6,
            "pattern_intensity": 0.55,
            "normal_micro_roughness": 0.3
        }
    },
    {
        "id": "biome_poplar_forest",
        "name": "Poplar Stand",
        "priority": 5,
        "description": "Fast-growing tall poplar grove along gentle slopes and river floodplains with sandy clay soil and dense leafy scrub.",
        "color_hex": "#65a30d",
        "moisture": 0.58,
        "nutrients": 0.65,
        "noise": {
            "frequency": 0.013,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.55,
            "dither_bandwidth": 0.05
        },
        "elevation": {
            "base_offset_m": 1.8,
            "noise_amplitude_m": 2.5,
            "noise_frequency": 0.014,
            "max_slope_deg": 20.0
        },
        "generative_ground": {
            "shader_mode": "standard_dither",
            "primary_color_hex": "#4d7c0f",
            "secondary_color_hex": "#a3e635",
            "slope_color_hex": "#78716c",
            "pattern_scale": 1.3,
            "pattern_intensity": 0.5,
            "normal_micro_roughness": 0.2
        }
    },
    {
        "id": "biome_pine_hills",
        "name": "Pine Hills & Ridges",
        "priority": 4,
        "description": "Dense alpine conifer highlands featuring rolling hills, weathered rocky outcrops, pine needles on the forest floor, and scattered pinecones.",
        "color_hex": "#1e3a1f",
        "moisture": 0.45,
        "nutrients": 0.40,
        "noise": {
            "frequency": 0.011,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.49,
            "dither_bandwidth": 0.06
        },
        "elevation": {
            "base_offset_m": 5.0,
            "noise_amplitude_m": 5.5,
            "noise_frequency": 0.015,
            "max_slope_deg": 35.0
        },
        "generative_ground": {
            "shader_mode": "standard_dither",
            "primary_color_hex": "#143019",
            "secondary_color_hex": "#451a03",
            "slope_color_hex": "#52525b",
            "pattern_scale": 1.5,
            "pattern_intensity": 0.6,
            "normal_micro_roughness": 0.3
        }
    },
    {
        "id": "biome_mixed_forest",
        "name": "Mixed Timberland",
        "priority": 4,
        "description": "Biodiverse mixed woodland of conifers and deciduous hardwoods with diverse canopy cover, mossy logs, and rich damp ground.",
        "color_hex": "#166534",
        "moisture": 0.55,
        "nutrients": 0.70,
        "noise": {
            "frequency": 0.012,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.48,
            "dither_bandwidth": 0.05
        },
        "elevation": {
            "base_offset_m": 3.0,
            "noise_amplitude_m": 4.0,
            "noise_frequency": 0.014,
            "max_slope_deg": 28.0
        },
        "generative_ground": {
            "shader_mode": "leaf_litter",
            "primary_color_hex": "#15803d",
            "secondary_color_hex": "#713f12",
            "slope_color_hex": "#57534e",
            "pattern_scale": 1.5,
            "pattern_intensity": 0.55,
            "normal_micro_roughness": 0.25
        }
    },
    {
        "id": "biome_rocky_ridge",
        "name": "Rocky Ridge & Scree",
        "priority": 3,
        "description": "Arid craggy bedrock outcrops and steep gravel scree slopes with sparse alpine lichens and weathered stone.",
        "color_hex": "#71717a",
        "moisture": 0.20,
        "nutrients": 0.10,
        "noise": {
            "frequency": 0.014,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.65,
            "dither_bandwidth": 0.05
        },
        "elevation": {
            "base_offset_m": 6.5,
            "noise_amplitude_m": 5.5,
            "noise_frequency": 0.016,
            "max_slope_deg": 45.0
        },
        "generative_ground": {
            "shader_mode": "scree_triplanar",
            "primary_color_hex": "#52525b",
            "secondary_color_hex": "#71717a",
            "slope_color_hex": "#3f3f46",
            "pattern_scale": 2.0,
            "pattern_intensity": 0.8,
            "normal_micro_roughness": 0.5
        }
    },
    {
        "id": "biome_dry_lands",
        "name": "Dry Lands & Arid Scrub",
        "priority": 2,
        "description": "Sun-baked arid plains with low moisture, poor nutrients, dusty cracked earth, dry sand, and hardy drought-tolerant scrub.",
        "color_hex": "#ca8a04",
        "moisture": 0.15,
        "nutrients": 0.20,
        "noise": {
            "frequency": 0.012,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.42,
            "dither_bandwidth": 0.05
        },
        "elevation": {
            "base_offset_m": 1.0,
            "noise_amplitude_m": 2.0,
            "noise_frequency": 0.012,
            "max_slope_deg": 18.0
        },
        "generative_ground": {
            "shader_mode": "cracked_earth",
            "primary_color_hex": "#d97706",
            "secondary_color_hex": "#78350f",
            "slope_color_hex": "#a1a1aa",
            "pattern_scale": 1.8,
            "pattern_intensity": 0.7,
            "normal_micro_roughness": 0.35
        }
    },
    {
        "id": "biome_grass_plains",
        "name": "Lush Prairie / Grass Plains",
        "priority": 2,
        "description": "Expansive plains of thick, luscious nutrient-rich grass ideal for livestock grazing, rolling topography, and fertile sod.",
        "color_hex": "#4ade80",
        "moisture": 0.50,
        "nutrients": 0.75,
        "noise": {
            "frequency": 0.009,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.25,
            "dither_bandwidth": 0.06
        },
        "elevation": {
            "base_offset_m": 1.0,
            "noise_amplitude_m": 2.5,
            "noise_frequency": 0.010,
            "max_slope_deg": 16.0
        },
        "generative_ground": {
            "shader_mode": "standard_dither",
            "primary_color_hex": "#22c55e",
            "secondary_color_hex": "#86efac",
            "slope_color_hex": "#6b7280",
            "pattern_scale": 1.6,
            "pattern_intensity": 0.5,
            "normal_micro_roughness": 0.2
        }
    },
    {
        "id": "biome_meadow",
        "name": "Pasture & Meadow",
        "priority": 1,
        "description": "Open rolling homestead prairie with wild meadow grasses, scattered wildflowers, grazing livestock, and gentle knolls.",
        "color_hex": "#84cc16",
        "moisture": 0.45,
        "nutrients": 0.60,
        "noise": {
            "frequency": 0.009,
            "octaves": 3,
            "persistence": 0.5,
            "threshold": 0.0,
            "dither_bandwidth": 0.05
        },
        "elevation": {
            "base_offset_m": 0.0,
            "noise_amplitude_m": 2.2,
            "noise_frequency": 0.010,
            "max_slope_deg": 18.0
        },
        "generative_ground": {
            "shader_mode": "standard_dither",
            "primary_color_hex": "#65a30d",
            "secondary_color_hex": "#a3e635",
            "slope_color_hex": "#78716c",
            "pattern_scale": 1.5,
            "pattern_intensity": 0.45,
            "normal_micro_roughness": 0.2
        }
    }
]

created = 0
for b in BIOMES:
    b["$schema"] = "https://homesteader.game/schemas/biome.schema.json"
    filename = f"{b['id']}.json"
    path = os.path.join(BIOMES_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(b, f, indent=2, ensure_ascii=False)
        f.write("\n")
    created += 1

print(f"Generated {created} compact 500m-scale generative biome manifests in {BIOMES_DIR}!")
