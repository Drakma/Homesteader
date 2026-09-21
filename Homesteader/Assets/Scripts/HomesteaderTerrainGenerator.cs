using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Generation
{
    [RequireComponent(typeof(Terrain))]
    public class HomesteaderTerrainGenerator : MonoBehaviour
    {
        [Header("World Settings (500m x 500m Playable Map)")]
        public int worldSeed = 1337;
        public float terrainSizeX = 500f;
        public float terrainSizeZ = 500f;
        public float terrainHeight = 50f;

        [Header("Biome Definitions")]
        public List<BiomeData> biomes = new List<BiomeData>();

        [Header("Asset Catalog Spawning (Inverted Architecture)")]
        public List<AssetManifestSummary> registeredAssets = new List<AssetManifestSummary>();

        private Terrain targetTerrain;
        private TerrainData terrainData;
        private Texture2D bakedBiomeMap;

        private void Reset()
        {
            SetupDefaultBiomes();
        }

        public void SetupDefaultBiomes()
        {
            biomes.Clear();

            // 1. River: Narrow single winding creek across the valley floor (Priority 12)
            // Evaluated as: isValley (macroRoll < -1.0) AND tight corridor around center line
            biomes.Add(new BiomeData
            {
                id = "biome_river",
                name = "River & Creek System",
                priority = 12,
                description = "Winding stream that carves naturally into the lowest valley basins.",
                color_hex = "#06b6d4",
                moisture = 1.0f,
                nutrients = 0.50f,
                noise = new BiomeNoiseConfig { frequency = 0.005f, octaves = 3, persistence = 0.5f, threshold = 0.95f, dither_bandwidth = 0.01f },
                elevation = new BiomeElevationConfig { base_offset_m = -2.5f, noise_amplitude_m = 0.5f, noise_frequency = 0.015f, max_slope_deg = 15.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "water_flow" }
            });

            // 2. Lake: Rare, strictly low-elevation deep basin in the lowest depression (Priority 11)
            biomes.Add(new BiomeData
            {
                id = "biome_lake",
                name = "Deep Lake",
                priority = 11,
                description = "Deep benthic lake basin confined strictly to low valley bottoms.",
                color_hex = "#1d4ed8",
                moisture = 1.0f,
                nutrients = 0.40f,
                noise = new BiomeNoiseConfig { frequency = 0.007f, octaves = 3, persistence = 0.45f, threshold = 0.78f, dither_bandwidth = 0.015f },
                elevation = new BiomeElevationConfig { base_offset_m = -4.0f, noise_amplitude_m = 0.8f, noise_frequency = 0.012f, max_slope_deg = 12.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "water_lake" }
            });

            // 3. Pond: Occasional small kettle basin in low spots (Priority 10)
            biomes.Add(new BiomeData
            {
                id = "biome_pond",
                name = "Pond & Wetland Basin",
                priority = 10,
                description = "Small kettle pond depression confined to low valley areas.",
                color_hex = "#3b82f6",
                moisture = 0.95f,
                nutrients = 0.65f,
                noise = new BiomeNoiseConfig { frequency = 0.012f, octaves = 3, persistence = 0.45f, threshold = 0.76f, dither_bandwidth = 0.02f },
                elevation = new BiomeElevationConfig { base_offset_m = -2.0f, noise_amplitude_m = 0.6f, noise_frequency = 0.015f, max_slope_deg = 18f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "water_basin" }
            });

            // 4. Farmland (Priority 8) - Tilled Furrows (~40-70m farm fields)
            biomes.Add(new BiomeData
            {
                id = "biome_farmland",
                name = "Farmland (Tilled Rows)",
                priority = 8,
                description = "Agricultural fields with distinct parallel tilled soil furrows.",
                color_hex = "#78350f",
                moisture = 0.65f,
                nutrients = 0.90f,
                noise = new BiomeNoiseConfig { frequency = 0.012f, octaves = 2, persistence = 0.5f, threshold = 0.65f, dither_bandwidth = 0.03f },
                elevation = new BiomeElevationConfig { base_offset_m = 0.5f, noise_amplitude_m = 1.0f, noise_frequency = 0.010f, max_slope_deg = 8.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "tilled_furrows" }
            });

            // 5. Maintained Lawn (Priority 7) - Mower Stripes (~30-50m yard parcels)
            biomes.Add(new BiomeData
            {
                id = "biome_maintained_grass",
                name = "Maintained Lawn",
                priority = 7,
                description = "Domestic yard grass with alternating directional mower stripes.",
                color_hex = "#10b981",
                moisture = 0.55f,
                nutrients = 0.70f,
                noise = new BiomeNoiseConfig { frequency = 0.016f, octaves = 2, persistence = 0.5f, threshold = 0.68f, dither_bandwidth = 0.025f },
                elevation = new BiomeElevationConfig { base_offset_m = 0.3f, noise_amplitude_m = 0.6f, noise_frequency = 0.012f, max_slope_deg = 12.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "mower_stripes" }
            });

            // 6. Wetland & Bog (Priority 6) - Valley marsh
            biomes.Add(new BiomeData
            {
                id = "biome_wetland_marsh",
                name = "Bog & Peat Marsh",
                priority = 6,
                description = "Soggy wetland basin with squishy peat and moss hummocks.",
                color_hex = "#365314",
                moisture = 0.90f,
                nutrients = 0.60f,
                noise = new BiomeNoiseConfig { frequency = 0.012f, octaves = 3, persistence = 0.5f, threshold = 0.60f, dither_bandwidth = 0.035f },
                elevation = new BiomeElevationConfig { base_offset_m = -1.0f, noise_amplitude_m = 0.8f, noise_frequency = 0.015f, max_slope_deg = 10.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "standard_dither" }
            });

            // 7. Maple Forest (Priority 5)
            biomes.Add(new BiomeData
            {
                id = "biome_maple_forest",
                name = "Maple Forest",
                priority = 5,
                description = "Autumn deciduous forest with vibrant leaf litter floor.",
                color_hex = "#ea580c",
                moisture = 0.60f,
                nutrients = 0.75f,
                noise = new BiomeNoiseConfig { frequency = 0.011f, octaves = 3, persistence = 0.5f, threshold = 0.54f, dither_bandwidth = 0.045f },
                elevation = new BiomeElevationConfig { base_offset_m = 2.5f, noise_amplitude_m = 3.0f, noise_frequency = 0.012f, max_slope_deg = 25.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "leaf_litter" }
            });

            // 8. Birch Forest (Priority 5)
            biomes.Add(new BiomeData
            {
                id = "biome_birch_forest",
                name = "Birch Grove",
                priority = 5,
                description = "Luminous grove with light moss undergrowth.",
                color_hex = "#a3e635",
                moisture = 0.50f,
                nutrients = 0.60f,
                noise = new BiomeNoiseConfig { frequency = 0.012f, octaves = 3, persistence = 0.5f, threshold = 0.52f, dither_bandwidth = 0.045f },
                elevation = new BiomeElevationConfig { base_offset_m = 1.8f, noise_amplitude_m = 2.5f, noise_frequency = 0.012f, max_slope_deg = 22.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "standard_dither" }
            });

            // 9. Oak Forest (Priority 5)
            biomes.Add(new BiomeData
            {
                id = "biome_oak_forest",
                name = "Oak Woodland",
                priority = 5,
                description = "Hardwood forest with rich shaded leaf soil.",
                color_hex = "#15803d",
                moisture = 0.55f,
                nutrients = 0.80f,
                noise = new BiomeNoiseConfig { frequency = 0.010f, octaves = 3, persistence = 0.5f, threshold = 0.50f, dither_bandwidth = 0.045f },
                elevation = new BiomeElevationConfig { base_offset_m = 3.0f, noise_amplitude_m = 3.0f, noise_frequency = 0.012f, max_slope_deg = 26.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "leaf_litter" }
            });

            // 10. Poplar Forest (Priority 5)
            biomes.Add(new BiomeData
            {
                id = "biome_poplar_forest",
                name = "Poplar Stand",
                priority = 5,
                description = "Tall grove along gentle knolls and floodplains.",
                color_hex = "#65a30d",
                moisture = 0.58f,
                nutrients = 0.65f,
                noise = new BiomeNoiseConfig { frequency = 0.011f, octaves = 3, persistence = 0.5f, threshold = 0.52f, dither_bandwidth = 0.045f },
                elevation = new BiomeElevationConfig { base_offset_m = 1.8f, noise_amplitude_m = 2.0f, noise_frequency = 0.012f, max_slope_deg = 20.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "standard_dither" }
            });

            // 11. Mixed Forest (Priority 4)
            biomes.Add(new BiomeData
            {
                id = "biome_mixed_forest",
                name = "Mixed Timberland",
                priority = 4,
                description = "Biodiverse mix of conifers and deciduous trees.",
                color_hex = "#166534",
                moisture = 0.55f,
                nutrients = 0.70f,
                noise = new BiomeNoiseConfig { frequency = 0.010f, octaves = 3, persistence = 0.5f, threshold = 0.46f, dither_bandwidth = 0.045f },
                elevation = new BiomeElevationConfig { base_offset_m = 3.0f, noise_amplitude_m = 3.5f, noise_frequency = 0.012f, max_slope_deg = 28.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "leaf_litter" }
            });

            // 12. Pine Hills (Priority 4)
            biomes.Add(new BiomeData
            {
                id = "biome_pine_hills",
                name = "Pine Hills & Ridges",
                priority = 4,
                description = "Rolling alpine conifer highlands with weathered rock outcrops.",
                color_hex = "#1e3a1f",
                moisture = 0.45f,
                nutrients = 0.40f,
                noise = new BiomeNoiseConfig { frequency = 0.009f, octaves = 3, persistence = 0.5f, threshold = 0.46f, dither_bandwidth = 0.055f },
                elevation = new BiomeElevationConfig { base_offset_m = 5.0f, noise_amplitude_m = 4.5f, noise_frequency = 0.012f, max_slope_deg = 35.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "standard_dither" }
            });

            // 13. Rocky Ridge (Priority 3)
            biomes.Add(new BiomeData
            {
                id = "biome_rocky_ridge",
                name = "Rocky Ridge & Scree",
                priority = 3,
                description = "High craggy bedrock knolls and gravel scree slopes.",
                color_hex = "#71717a",
                moisture = 0.20f,
                nutrients = 0.10f,
                noise = new BiomeNoiseConfig { frequency = 0.011f, octaves = 3, persistence = 0.5f, threshold = 0.60f, dither_bandwidth = 0.045f },
                elevation = new BiomeElevationConfig { base_offset_m = 6.5f, noise_amplitude_m = 4.5f, noise_frequency = 0.014f, max_slope_deg = 45.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "scree_triplanar" }
            });

            // 14. Dry Lands (Priority 2)
            biomes.Add(new BiomeData
            {
                id = "biome_dry_lands",
                name = "Dry Lands & Arid Scrub",
                priority = 2,
                description = "Arid sun-baked dirt and dusty plains.",
                color_hex = "#ca8a04",
                moisture = 0.15f,
                nutrients = 0.20f,
                noise = new BiomeNoiseConfig { frequency = 0.010f, octaves = 3, persistence = 0.5f, threshold = 0.38f, dither_bandwidth = 0.045f },
                elevation = new BiomeElevationConfig { base_offset_m = 1.0f, noise_amplitude_m = 1.8f, noise_frequency = 0.010f, max_slope_deg = 18.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "cracked_earth" }
            });

            // 15. Lush Grass Plains (Priority 2)
            biomes.Add(new BiomeData
            {
                id = "biome_grass_plains",
                name = "Lush Prairie / Grass Plains",
                priority = 2,
                description = "Expansive plains of thick, luscious nutrient-rich grass.",
                color_hex = "#4ade80",
                moisture = 0.50f,
                nutrients = 0.75f,
                noise = new BiomeNoiseConfig { frequency = 0.008f, octaves = 3, persistence = 0.5f, threshold = 0.22f, dither_bandwidth = 0.05f },
                elevation = new BiomeElevationConfig { base_offset_m = 1.0f, noise_amplitude_m = 2.0f, noise_frequency = 0.009f, max_slope_deg = 16.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "standard_dither" }
            });

            // 16. Meadow (Priority 1) - Baseline fallback
            biomes.Add(new BiomeData
            {
                id = "biome_meadow",
                name = "Pasture & Meadow",
                priority = 1,
                description = "Open rolling homestead prairie.",
                color_hex = "#84cc16",
                moisture = 0.45f,
                nutrients = 0.60f,
                noise = new BiomeNoiseConfig { frequency = 0.008f, octaves = 3, persistence = 0.5f, threshold = 0.0f, dither_bandwidth = 0.04f },
                elevation = new BiomeElevationConfig { base_offset_m = 0.0f, noise_amplitude_m = 1.8f, noise_frequency = 0.009f, max_slope_deg = 18.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "standard_dither" }
            });
        }

        public readonly Vector2 pondCenter = new Vector2(220f, 210f);

        /// <summary>
        /// Calculates the central winding curve of the river spine through the valley floor.
        /// </summary>
        public float GetRiverCenterX(float worldZ)
        {
            return 220f + Mathf.Sin(worldZ * 0.015f) * 45f + Mathf.Sin(worldZ * 0.035f + 1.2f) * 18f;
        }

        /// <summary>
        /// Organic perturbed radius of the natural kettle pond basin.
        /// </summary>
        public float GetPondRadius(float worldX, float worldZ)
        {
            float dx = worldX - pondCenter.x;
            float dz = worldZ - pondCenter.y;
            float angle = Mathf.Atan2(dz, dx);
            return 24f + Mathf.Sin(angle * 3f) * 5f + Mathf.Cos(angle * 4f) * 3f;
        }

        public BiomeData GetBiomeById(string id)
        {
            for (int i = 0; i < biomes.Count; i++)
            {
                if (biomes[i].id == id) return biomes[i];
            }
            return biomes.Count > 0 ? biomes[biomes.Count - 1] : null;
        }

        /// <summary>
        /// Water level along the winding river. Across the width of the channel (X), water is 100% FLAT.
        /// Along the length (Z), it maintains a smooth monotonic grade flowing downhill into and through the pond.
        /// </summary>
        public float GetRiverWaterLevel(float worldZ)
        {
            const float pondWaterLevel = 0.5f;
            if (worldZ >= 210f)
            {
                float t = (worldZ - 210f) / 290f;
                return pondWaterLevel + t * t * 3.0f;
            }
            else
            {
                float t = (210f - worldZ) / 210f;
                return pondWaterLevel - t * 0.5f;
            }
        }

        /// <summary>
        /// Calculates physical ground elevation with strict hydrological flat carving.
        /// Water features act as TRUE FLAT CARVERS:
        /// - The pond is 100% perfectly flat horizontal (zero downward bending or funnel).
        /// - The river is 100% flat across its channel width (zero V-trench).
        /// - Shoreline banks rise smoothly up from the flat water level to the surrounding land.
        /// </summary>
        public float CalculateElevationAt(float worldX, float worldZ)
        {
            // 1. Macro undulating landscape: rolling hills (-6m to +6m)
            float largeHills = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0035f, 3, 0.5f, worldSeed + 777) * 12.0f - 6.0f;
            float rolling = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.008f, 2, 0.5f, worldSeed + 444) * 4.0f - 2.0f;
            float elev = largeHills + rolling;

            // 2. Highland mountain rise to the north (Z > 240m)
            if (worldZ > 240f)
            {
                float northT = (worldZ - 240f) / 260f;
                elev += northT * northT * 10.0f;
            }

            // 3. Micro ground texture detail on dry land
            float micro = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.035f, 2, 0.5f, worldSeed + 999) * 0.4f;
            elev += micro;

            // 4. HYDROLOGICAL FLAT CARVER
            const float pondWaterLevel = 0.5f;
            float riverWaterLevel = GetRiverWaterLevel(worldZ);

            float distToPond = Vector2.Distance(new Vector2(worldX, worldZ), pondCenter);
            float pondRadius = GetPondRadius(worldX, worldZ);
            float riverX = GetRiverCenterX(worldZ);
            float distToRiver = Mathf.Abs(worldX - riverX);

            bool isPondWater = distToPond <= pondRadius;
            bool isRiverWater = !isPondWater && (distToRiver <= 3.8f);

            // A. Inside water features: GUARANTEED 100% FLAT (cannot bend down)
            if (isPondWater)
            {
                return pondWaterLevel;
            }
            if (isRiverWater)
            {
                return riverWaterLevel;
            }

            // B. Shoreline Banks: Carve smoothly UP from flat water level to surrounding land
            float pondBankDist = distToPond - pondRadius;
            float riverBankDist = distToRiver - 3.8f;

            // Surrounding land is guaranteed to stand at least 1.8m higher than water level
            float minLandHeight = (distToPond < 55.0f) ? (pondWaterLevel + 1.8f) : (riverWaterLevel + 1.5f);
            float targetLandElev = Mathf.Max(elev, minLandHeight);

            if (pondBankDist < 8.0f && pondBankDist >= 0f)
            {
                float t = Mathf.SmoothStep(0f, 1f, pondBankDist / 8.0f);
                return Mathf.Lerp(pondWaterLevel, targetLandElev, t);
            }
            else if (riverBankDist < 5.0f && riverBankDist >= 0f)
            {
                float t = Mathf.SmoothStep(0f, 1f, riverBankDist / 5.0f);
                return Mathf.Lerp(riverWaterLevel, targetLandElev, t);
            }

            // C. Gentle valley floor around the river & pond
            float valleyDist = Mathf.Min(distToRiver, distToPond);
            if (valleyDist < 35.0f)
            {
                float vt = Mathf.SmoothStep(0f, 1f, valleyDist / 35.0f);
                return Mathf.Lerp(targetLandElev, elev, vt);
            }

            return elev;
        }

        [Header("Starter Field")]
        [Tooltip("Carve a farmland biome plot around the player spawn (terrain-local metres).")]
        public bool starterFieldEnabled = true;
        public Vector2 starterFieldCenter = new Vector2(28f, 14f);
        [Tooltip("Half the field size on X and Z, in metres.")]
        public Vector2 starterFieldHalfSize = new Vector2(26f, 20f);

        public BiomeData EvaluateBiomeAt(float worldX, float worldZ)
        {
            float elev = CalculateElevationAt(worldX, worldZ);
            return EvaluateBiomeAt(worldX, worldZ, elev);
        }

        public BiomeData EvaluateBiomeAt(float worldX, float worldZ, float elev)
        {
            float riverX = GetRiverCenterX(worldZ);
            float distToRiver = Mathf.Abs(worldX - riverX);
            float distToPond = Vector2.Distance(new Vector2(worldX, worldZ), pondCenter);
            float pondRadius = GetPondRadius(worldX, worldZ);

            // 1. Water (Strictly in the sunken channels - occupying ~3% of map)
            if (distToRiver < 4.5f)
            {
                return GetBiomeById("biome_river");
            }
            if (distToPond < pondRadius)
            {
                return GetBiomeById("biome_pond");
            }

            // 2. Shoreline Wetland / Bog
            if (distToRiver < 9.5f || distToPond < (pondRadius + 8.0f))
            {
                return GetBiomeById("biome_wetland_marsh");
            }

            // 3. Homestead Domestic Yard (Maintained Lawn ~32m radius around cabin site)
            Vector2 lawnCenter = new Vector2(285f, 210f);
            if (Vector2.Distance(new Vector2(worldX, worldZ), lawnCenter) < 32f)
            {
                return GetBiomeById("biome_maintained_grass");
            }

            // 4a. Starter field: a farmland plot around the player spawn so crops can be planted right away.
            if (starterFieldEnabled &&
                Mathf.Abs(worldX - starterFieldCenter.x) < starterFieldHalfSize.x &&
                Mathf.Abs(worldZ - starterFieldCenter.y) < starterFieldHalfSize.y)
            {
                return GetBiomeById("biome_farmland");
            }

            // 4. Farmland (Tilled Furrows) - Two distinct agricultural parcels near homestead
            // Field 1: East homestead field (65m x 55m)
            if (Mathf.Abs(worldX - 335f) < 32f && Mathf.Abs(worldZ - 215f) < 28f)
            {
                return GetBiomeById("biome_farmland");
            }
            // Field 2: South-west field (40m x 35m)
            if (Mathf.Abs(worldX - 160f) < 22f && Mathf.Abs(worldZ - 170f) < 18f)
            {
                return GetBiomeById("biome_farmland");
            }

            // 5. Highlands & Mountain Knolls (North & High Peaks)
            if (elev > 14.0f)
            {
                return GetBiomeById("biome_rocky_ridge");
            }
            if (elev > 7.5f)
            {
                return GetBiomeById("biome_pine_hills");
            }

            // 6. Arid Dry Lands (South-West Sun-baked Scrub: X < 140, Z < 145)
            if (worldX < 140f && worldZ < 145f)
            {
                return GetBiomeById("biome_dry_lands");
            }

            // 7. Amorphous Regional Forest & Meadow Blobs
            // Two continuous domain-warped orthogonal noise fields partition the remaining landscape into organic flowing blobs
            float rNoise1 = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0055f, 3, 0.5f, worldSeed + 101);
            float rNoise2 = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0055f, 3, 0.5f, worldSeed + 202);

            if (rNoise1 > 0.58f)
            {
                return (rNoise2 > 0.50f)
                    ? GetBiomeById("biome_maple_forest")   // Vibrant Autumn Amber
                    : GetBiomeById("biome_birch_forest");   // Luminous Yellow-Green
            }
            else if (rNoise1 < 0.42f)
            {
                return (rNoise2 > 0.52f)
                    ? GetBiomeById("biome_oak_forest")      // Deep Canopy Hardwood
                    : GetBiomeById("biome_poplar_forest");  // Fresh Spring Green
            }
            else
            {
                return (rNoise2 > 0.50f)
                    ? GetBiomeById("biome_grass_plains")    // Vivid Emerald Prairie
                    : GetBiomeById("biome_meadow");          // Natural Rolling Pasture
            }
        }

        [ContextMenu("Generate Terrain")]
        public void GenerateTerrain()
        {
            targetTerrain = GetComponent<Terrain>();
            if (targetTerrain == null) return;
            terrainData = targetTerrain.terrainData;

            // Sync terrain size to 500m x 500m
            terrainData.size = new Vector3(terrainSizeX, terrainHeight, terrainSizeZ);

            int heightmapResolution = terrainData.heightmapResolution;
            float[,] heights = new float[heightmapResolution, heightmapResolution];

            int mapRes = 1024;
            if (bakedBiomeMap == null || bakedBiomeMap.width != mapRes)
            {
                // CRITICAL: linear = true ensures no sRGB-to-Linear gamma compression
                bakedBiomeMap = new Texture2D(mapRes, mapRes, TextureFormat.RGBA32, false, true)
                {
                    filterMode = FilterMode.Point,
                    wrapMode = TextureWrapMode.Clamp
                };
            }
            else
            {
                bakedBiomeMap.filterMode = FilterMode.Point;
            }

            Color[] mapPixels = new Color[mapRes * mapRes];

            // 1. Generate procedural heightmap with guaranteed sunken valley and bed for water
            for (int z = 0; z < heightmapResolution; z++)
            {
                for (int x = 0; x < heightmapResolution; x++)
                {
                    float worldX = (float)x / (heightmapResolution - 1) * terrainSizeX;
                    float worldZ = (float)z / (heightmapResolution - 1) * terrainSizeZ;

                    float elevMeters = CalculateElevationAt(worldX, worldZ);

                    // Normalize to Unity's [0, 1] terrain height space (14m baseline floor)
                    heights[z, x] = Mathf.Clamp01((elevMeters + 14f) / terrainHeight);
                }
            }

            terrainData.SetHeights(0, 0, heights);

            // 2. Bake organic Biome Control Map (R=ShaderMode [16-bucket full range], G=Moisture, B=Nutrients, A=1.0)
            for (int py = 0; py < mapRes; py++)
            {
                for (int px = 0; px < mapRes; px++)
                {
                    float worldX = (float)px / (mapRes - 1) * terrainSizeX;
                    float worldZ = (float)py / (mapRes - 1) * terrainSizeZ;

                    float elevMeters = CalculateElevationAt(worldX, worldZ);
                    BiomeData biome = EvaluateBiomeAt(worldX, worldZ, elevMeters);

                    int modeInt = 0;
                    if (biome != null)
                    {
                        switch (biome.id)
                        {
                            case "biome_river": modeInt = 1; break;
                            case "biome_lake": modeInt = 2; break;
                            case "biome_pond": modeInt = 3; break;
                            case "biome_farmland": modeInt = 4; break;
                            case "biome_maintained_grass": modeInt = 5; break;
                            case "biome_wetland_marsh": modeInt = 6; break;
                            case "biome_maple_forest": modeInt = 7; break;
                            case "biome_birch_forest": modeInt = 8; break;
                            case "biome_oak_forest": modeInt = 9; break;
                            case "biome_pine_hills": modeInt = 10; break;
                            case "biome_rocky_ridge": modeInt = 11; break;
                            case "biome_dry_lands": modeInt = 12; break;
                            case "biome_grass_plains": modeInt = 13; break;
                            case "biome_poplar_forest": modeInt = 14; break;
                            case "biome_mixed_forest": modeInt = 15; break;
                            default: modeInt = 0; break;
                        }
                    }

                    // Encode mode (0..15) across full range in distinct 1/16 buckets immune to gamma distortion
                    float r = (modeInt + 0.5f) / 16.0f;
                    float g = biome != null ? biome.moisture : 0.5f;
                    float b = biome != null ? biome.nutrients : 0.5f;

                    mapPixels[py * mapRes + px] = new Color(r, g, b, 1.0f);
                }
            }

            bakedBiomeMap.SetPixels(mapPixels);
            bakedBiomeMap.Apply();

            // Pass baked biome map and 500m world bounds to the procedural terrain material
            if (targetTerrain.materialTemplate != null)
            {
                targetTerrain.materialTemplate.SetTexture("_BiomeMap", bakedBiomeMap);
                targetTerrain.materialTemplate.SetVector("_TerrainBounds", new Vector4(terrainSizeX, terrainSizeZ, terrainHeight, 0f));
            }

            SpawnBiomeAssets();
        }

        public Texture2D GetBakedBiomeMap()
        {
            return bakedBiomeMap;
        }

        public void SpawnBiomeAssets()
        {
            Transform spawnerRoot = transform.Find("SpawnedAssets");
            if (spawnerRoot != null)
            {
                DestroyImmediate(spawnerRoot.gameObject);
            }
            spawnerRoot = new GameObject("SpawnedAssets").transform;
            spawnerRoot.parent = transform;

            foreach (var asset in registeredAssets)
            {
                // Data-only assets (is_spawnable == false) exist for crafting and
                // placement but are never scattered by the generator.
                if (!asset.CanSpawn)
                    continue;

                HashSet<string> targetBiomes = new HashSet<string>(asset.spawning.biomes);
                float areaHectares = (terrainSizeX * terrainSizeZ) / 10000f;
                int totalCount = Mathf.RoundToInt(asset.spawning.density_per_hectare * areaHectares);

                for (int i = 0; i < totalCount; i++)
                {
                    float rx = Random.Range(0f, terrainSizeX);
                    float rz = Random.Range(0f, terrainSizeZ);

                    float elev = CalculateElevationAt(rx, rz);
                    BiomeData biomeAtPoint = EvaluateBiomeAt(rx, rz, elev);
                    if (biomeAtPoint == null || !targetBiomes.Contains(biomeAtPoint.id))
                        continue;

                    float worldY = targetTerrain.SampleHeight(new Vector3(rx, 0, rz));
                    if (worldY < asset.spawning.elevation_min_m || worldY > asset.spawning.elevation_max_m)
                        continue;

                    Vector3 spawnPos = new Vector3(rx, worldY, rz);
                    Quaternion spawnRot = Quaternion.Euler(0f, Random.Range(0f, 360f), 0f);

                    if (asset.spawning.align_to_surface_normal)
                    {
                        Vector3 normal = terrainData.GetInterpolatedNormal(rx / terrainSizeX, rz / terrainSizeZ);
                        spawnRot = Quaternion.FromToRotation(Vector3.up, normal) * spawnRot;
                    }

                    GameObject instance = Instantiate(asset.prefab, spawnPos, spawnRot, spawnerRoot);
                    float scale = Random.Range(asset.spawning.scale_min, asset.spawning.scale_max);
                    instance.transform.localScale = Vector3.one * scale;
                }
            }
        }
    }
}
