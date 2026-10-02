using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Generation
{
    [RequireComponent(typeof(Terrain))]
    public partial class HomesteaderTerrainGenerator : MonoBehaviour
    {
        [Header("World Settings (500m x 500m Playable Map)")]
        public int worldSeed = 8462;
        public float terrainSizeX = 500f;
        public float terrainSizeZ = 500f;
        public float terrainHeight = 50f;

        [Header("Terraced Terrain")]
        [Tooltip("Quantize elevation into discrete steps for a stylized terraced contour look.")]
        public bool terraceEnabled = true;
        [Tooltip("Height of each terrace step in metres.")]
        public float terraceStepMeters = 0.5f;
        [Tooltip("Fraction of each terrace step that stays a flat plateau (the rest eases into a slope toward the next step, instead of a vertical cliff). 1 = old hard-edged terracing.")]
        [Range(0.05f, 1f)]
        public float terraceFlatness = 0.15f;

        [Header("Biome Definitions")]
        public List<BiomeData> biomes = new List<BiomeData>();

        [Header("Asset Catalog Spawning (Inverted Architecture)")]
        public List<AssetManifestSummary> registeredAssets = new List<AssetManifestSummary>();

        [Tooltip("Scatter the procedural trees, rocks, cattails, debris, flowers and tufts (ProceduralVegetation.cs).")]
        [UnityEngine.Serialization.FormerlySerializedAs("tempTreesEnabled")]
        public bool proceduralVegetationEnabled = true;

        private Terrain targetTerrain;
        private TerrainData terrainData;
        private Texture2D bakedBiomeMap;

        /// <summary>Current generation progress, 0..1. Read by WelcomeMenuController to update the progress bar.</summary>
        public float GenerationProgress { get; private set; }

        /// <summary>True while async terrain generation is running.</summary>
        public bool IsGenerating { get; private set; }

        /// <summary>Human-readable label for the current generation phase.</summary>
        public string GenerationPhase { get; private set; } = "";

        /// <summary>
        /// Call after changing worldSeed to invalidate any cached seed-dependent values.
        /// </summary>
        public void InvalidateSeedCache()
        {
            waterMask = null;
            waterDistField = null;
        }

        private void Reset()
        {
            SetupDefaultBiomes();
        }

        public void SetupDefaultBiomes()
        {
            biomes.Clear();

            // 1. River: Narrow single winding creek across the valley floor (Priority 12)
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

            // Willow Grove (Priority 5): damp low ground along the water, dominated by weeping willows
            biomes.Add(new BiomeData
            {
                id = "biome_willow_grove",
                name = "Willow Grove",
                priority = 5,
                description = "Damp, lush ground along the water under weeping willows.",
                color_hex = "#9cc04a",
                moisture = 0.80f,
                nutrients = 0.65f,
                noise = new BiomeNoiseConfig { frequency = 0.016f, octaves = 2, persistence = 0.5f, threshold = 0.5f, dither_bandwidth = 0.05f },
                elevation = new BiomeElevationConfig { base_offset_m = 0.2f, noise_amplitude_m = 1.2f, noise_frequency = 0.016f, max_slope_deg = 14.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "standard_dither" }
            });

            // Sand (Priority 5): beaches along parts of the shoreline and a few small irregular sand pits
            biomes.Add(new BiomeData
            {
                id = "biome_sand",
                name = "Sand",
                priority = 5,
                description = "Pale sand: stretches of the shoreline and a few small, irregular sand pits.",
                color_hex = "#d9c58c",
                moisture = 0.20f,
                nutrients = 0.05f,
                noise = new BiomeNoiseConfig { frequency = 0.05f, octaves = 2, persistence = 0.5f, threshold = 0.55f, dither_bandwidth = 0.04f },
                elevation = new BiomeElevationConfig { base_offset_m = 0.1f, noise_amplitude_m = 0.4f, noise_frequency = 0.03f, max_slope_deg = 10.0f },
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
                color_hex = "#8a6a3f",
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
                color_hex = "#1e6b34",
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
                color_hex = "#4d9c2e",
                moisture = 0.45f,
                nutrients = 0.60f,
                noise = new BiomeNoiseConfig { frequency = 0.008f, octaves = 3, persistence = 0.5f, threshold = 0.0f, dither_bandwidth = 0.04f },
                elevation = new BiomeElevationConfig { base_offset_m = 0.0f, noise_amplitude_m = 1.8f, noise_frequency = 0.009f, max_slope_deg = 18.0f },
                generative_ground = new GenerativeGroundConfig { shader_mode = "standard_dither" }
            });
        }

        // ========================================================================
        //  WATER SYSTEM — vertex-displaced mesh, continuous channels, SW-to-NE flow
        // ========================================================================

        /// <summary>Water level (metres above terrain baseline). Shared by all water features.</summary>
        public const float WaterLevel = 0.5f;

        private const int MAX_BRANCHES = 2;
        private const int MAX_PONDS = 2;

        private struct RiverFeature
        {
            public Vector2 start;
            public Vector2 end;
            public float halfWidth;
            public float meanderAmp;
            public float meanderFreq;
            public float meanderPhase;
        }

        private struct PondFeature
        {
            public Vector2 center;
            public float radius;
            public float noiseSeed;
            public float irregularity; // 0 = circle, 1 = very irregular
        }

        private RiverFeature mainRiver;
        private RiverFeature[] riverBranches = new RiverFeature[0];
        private PondFeature[] allPonds = new PondFeature[0];
        private bool[,] waterMask;          // [x, z] true = water, 1m resolution
        private float[,] waterDistField;     // [x, z] distance to nearest water in metres
        private float[,] shoreDepthField;    // [x, z] distance to nearest land in metres (0 outside water)
        private Texture2D waterMaskTex;      // For the water shader

        // Water mesh geometry only (CreateWaterSurface) is built from this finer-resolution mask instead of
        // the 1m waterMask above. Rasterizing the same river/pond stamps at WaterMeshSupersample x the
        // density gives a mesh boundary with steps a fraction of a metre wide instead of a full metre - the
        // 1m mask's blocky silhouette was still visible as a stair-step shoreline no matter how much the
        // shader alpha-faded its color, since a fading color can't change the polygon's actual outline shape.
        // Every OTHER water query (elevation, biome, distance field) stays on the coarse 1m waterMask above -
        // this is purely a rendering-resolution upgrade for the visible water surface.
        private const int WaterMeshSupersample = 3;
        private bool[,] fineWaterMask;       // [x, z] true = water, 1/WaterMeshSupersample metre resolution
        private GameObject waterSurfaceObj;

        /// <summary>
        /// Generates seeded water features: 1 SW-to-NE river with up to 2 branches, up to 2 ponds.
        /// River touches at least one map edge (starts on south edge, ends on north edge).
        /// </summary>
        private void GenerateWaterFeatures()
        {
            // Main river: enters through one map edge and leaves through a different one, in ANY direction.
            // It used to run south -> north every time. Opposite edges are favoured (a river crossing the
            // whole map) but adjacent edges give the diagonal/corner-cutting rivers, and the pair is rejected
            // if the two points are too close for a river to develop bends.
            Vector2 riverStart = Vector2.zero, riverEnd = Vector2.zero;
            for (int attempt = 0; attempt < 30; attempt++)
            {
                int edgeA = Random.Range(0, 4);
                int edgeB = Random.value < 0.6f ? (edgeA + 2) % 4 : (edgeA + (Random.value < 0.5f ? 1 : 3)) % 4;
                riverStart = RandomEdgePoint(edgeA);
                riverEnd = RandomEdgePoint(edgeB);
                if (Vector2.Distance(riverStart, riverEnd) > 0.6f * Mathf.Min(terrainSizeX, terrainSizeZ)) break;
            }
            mainRiver = new RiverFeature
            {
                start = riverStart,
                end = riverEnd,
                halfWidth = Random.Range(2f, 3.8f),
                meanderAmp = Random.Range(15f, 30f),
                meanderFreq = Random.Range(0.8f, 1.8f),
                meanderPhase = Random.Range(0f, Mathf.PI * 2f)
            };

            // Branches: up to 2, each splits off the main river.
            // Rule: rivers don't cross rivers — branches may only leave the main river,
            // never cross it or cross each other. Each candidate is checked against the
            // main river and all previously accepted branches; crossings are rejected.
            int branchCount = Random.Range(0, MAX_BRANCHES + 1);
            var acceptedBranches = new List<RiverFeature>();
            for (int i = 0; i < branchCount; i++)
            {
                bool accepted = false;
                for (int attempt = 0; attempt < 40 && !accepted; attempt++)
                {
                    // A branch can leave the main river ANYWHERE along it, not just around the middle.
                    float splitT = Random.Range(0.06f, 0.94f);
                    Vector2 splitPoint = GetRiverPoint(splitT, mainRiver);
                    // Leaves the main river at 35-85 degrees to either side of its direction, whichever way
                    // that river runs, and heads off up to a few hundred metres.
                    Vector2 mainDir = (mainRiver.end - mainRiver.start).normalized;
                    // 35-145 degrees to either side: heading downstream (a distributary) or back upstream (a tributary)
                    float turn = Random.Range(35f, 145f) * (Random.value > 0.5f ? 1f : -1f) * Mathf.Deg2Rad;
                    Vector2 branchDir = new Vector2(
                        mainDir.x * Mathf.Cos(turn) - mainDir.y * Mathf.Sin(turn),
                        mainDir.x * Mathf.Sin(turn) + mainDir.y * Mathf.Cos(turn));
                    Vector2 branchEnd = splitPoint + branchDir * Random.Range(120f, 260f);
                    float branchEndX = Mathf.Clamp(branchEnd.x, 0f, terrainSizeX);
                    float branchEndZ = Mathf.Clamp(branchEnd.y, 0f, terrainSizeZ);
                    if (Vector2.Distance(splitPoint, new Vector2(branchEndX, branchEndZ)) < 60f) continue;

                    var candidate = new RiverFeature
                    {
                        start = splitPoint,
                        end = new Vector2(branchEndX, branchEndZ),
                        halfWidth = Mathf.Max(1.5f, mainRiver.halfWidth * Random.Range(0.5f, 0.75f)),
                        meanderAmp = mainRiver.meanderAmp * 0.5f,
                        meanderFreq = mainRiver.meanderFreq * 1.1f,
                        meanderPhase = Random.Range(0f, Mathf.PI * 2f)
                    };

                    // Reject if the candidate crosses the main river (beyond the branch origin).
                    if (RiverCrossesRiver(candidate, mainRiver))
                        continue;

                    // Reject if the candidate crosses any previously accepted branch.
                    bool crossesBranch = false;
                    foreach (var ab in acceptedBranches)
                    {
                        if (RiverCrossesRiver(candidate, ab))
                        {
                            crossesBranch = true;
                            break;
                        }
                    }
                    if (crossesBranch)
                        continue;

                    acceptedBranches.Add(candidate);
                    accepted = true;
                }
            }
            riverBranches = acceptedBranches.ToArray();

            // Ponds: up to 2, placed away from the river
            int pondCount = Random.Range(0, MAX_PONDS + 1);
            allPonds = new PondFeature[pondCount];
            for (int i = 0; i < pondCount; i++)
            {
                Vector2 center = Vector2.zero;
                for (int attempt = 0; attempt < 20; attempt++)
                {
                    float cx = Random.Range(60f, terrainSizeX - 60f);
                    float cz = Random.Range(60f, terrainSizeZ - 60f);
                    center = new Vector2(cx, cz);
                    // Check distance to river path
                    float minDist = float.MaxValue;
                    for (float t = 0; t <= 1f; t += 0.02f)
                    {
                        float d = Vector2.Distance(center, GetRiverPoint(t, mainRiver));
                        if (d < minDist) minDist = d;
                    }
                    if (minDist > 50f) break;
                }
                allPonds[i] = new PondFeature
                {
                    center = center,
                    radius = Random.Range(15f, 30f),
                    noiseSeed = Random.Range(0f, 1000f),
                    irregularity = Random.Range(0.25f, 0.5f)
                };
            }
        }

        // ========================================================================
        //  STARTER ZONE RULES (GameRules.StarterZone)
        // ========================================================================

        /// <summary>True inside the square of ground around the spawn point (the starter tile's centre) that must be
        /// grass: GrassAreaM on a side. Everywhere else in the starter zone is ordinary biome generation.</summary>
        private bool InStarterGrassArea(float worldX, float worldZ)
        {
            var r = Homesteader.Growth.GameRules.StarterZone;
            if (!r.Enabled || r.GrassAreaM <= 0f) return false;
            float t = Homesteader.Land.LandOwnershipSystem.TileSize;
            float half = r.GrassAreaM * 0.5f;
            return Mathf.Abs(worldX - (r.TileX + 0.5f) * t) <= half && Mathf.Abs(worldZ - (r.TileZ + 0.5f) * t) <= half;
        }

        /// <summary>One of the rule's grass biomes for a point in the starter grass area, patchy rather than uniform.</summary>
        private BiomeData StarterGrassBiome(float worldX, float worldZ)
        {
            var ids = Homesteader.Growth.GameRules.StarterZone.LandBiomes;
            BiomeData fallback = GetBiomeById("biome_grass_plains");
            if (ids.Count == 0) return fallback;
            float n = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.02f, 2, 0.5f, worldSeed + 909);
            int i = Mathf.Clamp((int)(n * ids.Count), 0, ids.Count - 1);
            return GetBiomeById(ids[i]) ?? fallback;
        }

        /// <summary>
        /// Rasterises every river and pond into the starter zone at 1 m and returns the fraction of the zone that is
        /// water. perFeature (main river, each branch, each pond) receives how many cells each feature owns.
        /// </summary>
        private float MeasureStarterWater(int[] perFeature)
        {
            var r = Homesteader.Growth.GameRules.StarterZone;
            float tile = Homesteader.Land.LandOwnershipSystem.TileSize;
            float x0 = r.TileX * tile, z0 = r.TileZ * tile;
            int n = Mathf.RoundToInt(tile);
            var grid = new int[n, n];   // 0 = land, else feature index + 1

            var rivers = new List<RiverFeature> { mainRiver };
            rivers.AddRange(riverBranches);
            for (int k = 0; k < rivers.Count; k++)
            {
                RiverFeature river = rivers[k];
                float length = (river.end - river.start).magnitude;
                int steps = Mathf.CeilToInt(length / 0.5f) + 1;
                for (int i = 0; i <= steps; i++)
                {
                    float t = (float)i / steps;
                    Vector2 pt = GetRiverPoint(t, river);
                    float hw = GetRiverHalfWidthAt(t, river);
                    if (pt.x < x0 - hw - 2f || pt.x > x0 + tile + hw + 2f || pt.y < z0 - hw - 2f || pt.y > z0 + tile + hw + 2f) continue;
                    int rad = Mathf.CeilToInt(hw) + 1;
                    int cx = Mathf.RoundToInt(pt.x - x0), cz = Mathf.RoundToInt(pt.y - z0);
                    for (int dz = -rad; dz <= rad; dz++)
                        for (int dx = -rad; dx <= rad; dx++)
                        {
                            int px = cx + dx, pz = cz + dz;
                            if (px < 0 || pz < 0 || px >= n || pz >= n) continue;
                            if (dx * dx + dz * dz <= hw * hw) grid[px, pz] = k + 1;
                        }
                }
            }

            for (int k = 0; k < allPonds.Length; k++)
            {
                PondFeature pond = allPonds[k];
                float reach = pond.radius * (1f + pond.irregularity) + 2f;
                if (pond.center.x + reach < x0 || pond.center.x - reach > x0 + tile || pond.center.y + reach < z0 || pond.center.y - reach > z0 + tile) continue;
                int idx = rivers.Count + k + 1;
                for (int pz = 0; pz < n; pz++)
                    for (int px = 0; px < n; px++)
                    {
                        float wx = x0 + px + 0.5f, wz = z0 + pz + 0.5f;
                        float dx = wx - pond.center.x, dz = wz - pond.center.y;
                        if (dx * dx + dz * dz > reach * reach) continue;
                        float noise = BiomeNoise.FractalNoise2D(dx * 0.15f, dz * 0.15f, 0.5f, 2, 0.5f, Mathf.RoundToInt(pond.noiseSeed));
                        float effective = pond.radius * (1f - pond.irregularity + noise * pond.irregularity * 2f);
                        if (Mathf.Sqrt(dx * dx + dz * dz) <= effective) grid[px, pz] = idx;
                    }
            }

            System.Array.Clear(perFeature, 0, perFeature.Length);
            int water = 0;
            for (int pz = 0; pz < n; pz++)
                for (int px = 0; px < n; px++)
                    if (grid[px, pz] > 0)
                    {
                        water++;
                        if (grid[px, pz] - 1 < perFeature.Length) perFeature[grid[px, pz] - 1]++;
                    }
            return water / (float)(n * n);
        }

        /// <summary>
        /// Enforces the water part of the starter zone rule on the seeded features, before the water mask is built:
        /// shrinks what is in the zone until water covers no more than the allowed fraction, and adds a pond if the
        /// zone has no water feature at all. Deterministic for a given seed.
        /// </summary>
        private void EnforceStarterZoneWater()
        {
            var rule = Homesteader.Growth.GameRules.StarterZone;
            if (!rule.Enabled) return;

            const int MinFeatureCells = 30;   // a feature counts as "inside" with at least this many square metres
            float tile = Homesteader.Land.LandOwnershipSystem.TileSize;
            Vector2 zoneCentre = new Vector2((rule.TileX + 0.5f) * tile, (rule.TileZ + 0.5f) * tile);

            int[] per = new int[1 + riverBranches.Length + allPonds.Length];
            float fraction = MeasureStarterWater(per);

            // 1. Too much water: narrow the rivers and shrink the ponds that reach into the zone.
            for (int pass = 0; pass < 16 && fraction > rule.MaxWaterFraction; pass++)
            {
                if (per[0] > 0) mainRiver.halfWidth = Mathf.Max(1.3f, mainRiver.halfWidth * 0.9f);
                for (int b = 0; b < riverBranches.Length; b++)
                    if (per[1 + b] > 0) riverBranches[b].halfWidth = Mathf.Max(1.2f, riverBranches[b].halfWidth * 0.9f);
                for (int i = 0; i < allPonds.Length; i++)
                    if (per[1 + riverBranches.Length + i] > 0) allPonds[i].radius *= 0.85f;
                fraction = MeasureStarterWater(per);
            }

            // Still over (rivers already at their narrowest): drop the ponds that touch the zone.
            if (fraction > rule.MaxWaterFraction)
            {
                var keep = new List<PondFeature>();
                for (int i = 0; i < allPonds.Length; i++)
                    if (per[1 + riverBranches.Length + i] == 0) keep.Add(allPonds[i]);
                allPonds = keep.ToArray();
                per = new int[1 + riverBranches.Length + allPonds.Length];
                fraction = MeasureStarterWater(per);
            }

            // 2. Too little: at least MinWaterFeatures features must have water in the zone.
            int inside = 0;
            foreach (int cells in per) if (cells >= MinFeatureCells) inside++;
            var rng = new System.Random(worldSeed * 7919 + 13);
            for (int attempt = 0; attempt < 8 && inside < rule.MinWaterFeatures; attempt++)
            {
                // A small pond a little way from the spawn point (never on it).
                float angle = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                float dist = 22f + (float)rng.NextDouble() * 14f;
                var pond = new PondFeature
                {
                    center = zoneCentre + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * dist,
                    radius = 6f + (float)rng.NextDouble() * 3f,
                    noiseSeed = (float)(rng.NextDouble() * 1000.0),
                    irregularity = 0.3f + (float)rng.NextDouble() * 0.15f,
                };

                var list = new List<PondFeature>(allPonds) { pond };
                allPonds = list.ToArray();
                per = new int[1 + riverBranches.Length + allPonds.Length];
                fraction = MeasureStarterWater(per);

                // Keep the new pond within the cap too.
                int last = allPonds.Length - 1;
                for (int pass = 0; pass < 8 && fraction > rule.MaxWaterFraction && allPonds[last].radius > 3f; pass++)
                {
                    allPonds[last].radius *= 0.85f;
                    fraction = MeasureStarterWater(per);
                }

                inside = 0;
                foreach (int cells in per) if (cells >= MinFeatureCells) inside++;
            }

            Debug.Log($"[StarterZone] water {fraction * 100f:F1}% of the zone (cap {rule.MaxWaterFraction * 100f:F0}%), {inside} feature(s) inside.");
        }

        /// <summary>A random point on one map edge (0 = south, 1 = east, 2 = north, 3 = west), kept off the corners.</summary>
        private Vector2 RandomEdgePoint(int edge)
        {
            switch (edge)
            {
                case 0: return new Vector2(Random.Range(0.12f, 0.88f) * terrainSizeX, 0f);
                case 1: return new Vector2(terrainSizeX, Random.Range(0.12f, 0.88f) * terrainSizeZ);
                case 2: return new Vector2(Random.Range(0.12f, 0.88f) * terrainSizeX, terrainSizeZ);
                default: return new Vector2(0f, Random.Range(0.12f, 0.88f) * terrainSizeZ);
            }
        }

        /// <summary>Parametric point on a river path at parameter t [0,1].</summary>
        private Vector2 GetRiverPoint(float t, RiverFeature river)
        {
            Vector2 basePt = Vector2.Lerp(river.start, river.end, t);
            Vector2 dir = (river.end - river.start).normalized;
            Vector2 perp = new Vector2(-dir.y, dir.x);
            float meander = Mathf.Sin(t * river.meanderFreq * Mathf.PI * 2f + river.meanderPhase) * river.meanderAmp;
            meander += Mathf.Sin(t * river.meanderFreq * 2.5f + river.meanderPhase + 1.2f) * river.meanderAmp * 0.25f;

            // IRREGULAR, NOT A SINE. Two sines read as an obviously regular S-curve. Layered Perlin noise
            // (seeded by the river's own phase, so every river differs and the same river is identical on
            // every call) adds unrepeatable wander at three scales: broad bends, mid-size kinks and small
            // wobble. Faded to zero at both ends so the river still meets the map edge where it started.
            float seed = river.meanderPhase * 17.31f;
            float wander = (Mathf.PerlinNoise(t * 3.1f + seed, 0.37f) - 0.5f) * 2f * river.meanderAmp * 1.1f
                         + (Mathf.PerlinNoise(t * 8.3f + seed, 5.71f) - 0.5f) * 2f * river.meanderAmp * 0.45f
                         + (Mathf.PerlinNoise(t * 19f + seed, 9.13f) - 0.5f) * 2f * river.meanderAmp * 0.15f;
            float ends = Mathf.Clamp01(Mathf.Min(t, 1f - t) / 0.06f);
            return basePt + perp * (meander + wander * ends);
        }

        /// <summary>Half-width of a river at parameter t, with slight variation.</summary>
        private float GetRiverHalfWidthAt(float t, RiverFeature river)
        {
            // A real river's width drifts gradually, not in tight repeating pinches - 8 full oscillation
            // cycles packed across the whole river length (the old frequency here) produced a regular, sharp
            // sawtooth bank that no amount of shoreline blur could smooth out, since the width itself was
            // genuinely zigzagging every few metres. A low frequency and gentler amplitude reads as natural
            // width variation instead.
            // Irregular width: broad swells and narrows plus a finer wobble, all noise-driven and slow enough
            // (>= ~25m per feature) not to reintroduce the sawtooth bank the comment above warns about.
            float seed = river.meanderPhase * 11.7f;
            float w = 1f + (Mathf.PerlinNoise(t * 5.5f + seed, 2.9f) - 0.5f) * 0.7f
                         + (Mathf.PerlinNoise(t * 14f + seed, 7.3f) - 0.5f) * 0.25f;
            return river.halfWidth * Mathf.Max(0.7f, w);
        }

        /// <summary>
        /// Checks if a candidate river's centerline enters an existing river's channel,
        /// excluding the branch origin zone where they intentionally meet.
        /// Returns true if the candidate crosses the existing river beyond the branch point.
        /// </summary>
        private bool RiverCrossesRiver(RiverFeature candidate, RiverFeature existing)
        {
            // Rivers never cross. The two channels (not just their centrelines) must stay clear of each other everywhere except
            // right at the junction, where the branch leaves at a shallow angle and the channels necessarily overlap for a stretch:
            // that stretch is the length over which two channels of these widths separate at the narrowest allowed angle (35 degrees).
            const float margin = 3f;
            float needClear = existing.halfWidth + candidate.halfWidth + margin;
            float junctionLength = needClear / Mathf.Sin(35f * Mathf.Deg2Rad) + 12f;

            float pathLength = (candidate.end - candidate.start).magnitude;
            int steps = Mathf.CeilToInt(pathLength / 1f) + 1;

            int existingSteps = Mathf.CeilToInt((existing.end - existing.start).magnitude / 1f) + 1;
            Vector2[] existingPts = new Vector2[existingSteps + 1];
            for (int j = 0; j <= existingSteps; j++)
                existingPts[j] = GetRiverPoint((float)j / existingSteps, existing);

            float walked = 0f;
            Vector2 prev = GetRiverPoint(0f, candidate);
            for (int i = 0; i <= steps; i++)
            {
                Vector2 pt = GetRiverPoint((float)i / steps, candidate);
                walked += Vector2.Distance(prev, pt);
                prev = pt;
                if (walked < junctionLength) continue;   // still inside the junction

                float minSq = float.MaxValue;
                for (int j = 0; j <= existingSteps; j++)
                {
                    float d = (pt - existingPts[j]).sqrMagnitude;
                    if (d < minSq) minSq = d;
                }
                if (minSq < needClear * needClear) return true;
            }
            return false;
        }

        /// <summary>
        /// Builds the water mask: a 1m-resolution boolean grid marking every water cell.
        /// Walks each river path at 0.5m intervals and stamps circles, guaranteeing continuous
        /// channel coverage. Also stamps pond circles.
        /// </summary>
        private void GenerateWaterMask()
        {
            int res = Mathf.RoundToInt(terrainSizeX);

            // Build the fine mask first (same river/pond stamps, WaterMeshSupersample x the density - see
            // fineWaterMask's remarks) and derive the coarse waterMask FROM it by downsampling, rather than
            // stamping both independently. Two separate stamping passes could disagree at small spots -
            // typically a 1-2 fine-cell gap the coarse pass missed or added - and since elevation carving
            // (CalculateElevationAt) and the shore taper both key off the coarse mask while the actual water
            // MESH is built from the fine one, any disagreement meant a little patch of un-carved (or
            // wrongly-shallow) terrain sitting right under an otherwise flat water quad: a small chunk of
            // riverbed visibly poking up out of the water mid-channel. Deriving one from the other makes that
            // impossible - they can no longer disagree about what's water.
            BuildFineWaterMask(res);

            int fineRes = fineWaterMask.GetLength(0);
            waterMask = new bool[res, res];
            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    // Majority of the fine sub-cells, not "any": an OR rule dilates the coarse mask outward
                    // (a coarse cell counts as water if even one of its edge-touching fine cells does), which
                    // is exactly what pushed the river/pond biome (and IsWaterAt, which drives it) out onto
                    // the bank. Majority tracks the fine mask's true shape instead of inflating it, while
                    // still keeping the two masks close enough to avoid the mismatched-patch bug this
                    // consolidation was meant to fix.
                    int count = 0;
                    int fx0 = x * WaterMeshSupersample, fz0 = z * WaterMeshSupersample;
                    for (int fz = fz0; fz < fz0 + WaterMeshSupersample; fz++)
                        for (int fx = fx0; fx < fx0 + WaterMeshSupersample; fx++)
                            if (fx < fineRes && fz < fineRes && fineWaterMask[fx, fz]) count++;
                    int total = WaterMeshSupersample * WaterMeshSupersample;
                    waterMask[x, z] = count * 2 >= total;
                }
            }
            waterMask = SmoothBinaryMask(waterMask, res);

            // Build the water mask texture for the shader FROM THE FINE MASK, not the 1m one.
            //
            // THE JAGGED SHORELINE. The texture used to be the 1m coarse mask box-blurred over 3 texels, and
            // the mesh was built from the 0.33m fine mask with alpha = saturate(coverage * 3) - which is
            // already 1.0 at the mesh's own boundary. So the visible edge was the mesh polygon itself: a
            // literal staircase of 0.33m quads, however much the interior faded. Two changes fix it:
            //   1. The field is a GAUSSIAN blur of the fine mask at fine resolution, so its 0.5 contour is a
            //      smooth curve (the staircase averages out) and bilinear sampling of it stays smooth.
            //   2. The mesh is dilated to cover the whole blur (see CreateWaterSurface), and the shader draws
            //      the water where coverage crosses 0.5 with an anti-aliased ramp - the visible edge is now a
            //      contour of a smooth field, never a mesh boundary.
            if (waterMaskTex == null || waterMaskTex.width != fineRes)
            {
                waterMaskTex = new Texture2D(fineRes, fineRes, TextureFormat.RGBA32, false, true)
                {
                    filterMode = FilterMode.Bilinear,
                    wrapMode = TextureWrapMode.Clamp
                };
            }
            fineCoverage = GaussianCoverage(fineWaterMask, fineRes, WaterShoreSigmaMetres * WaterMeshSupersample);

            // Depth is smooth and cheap to evaluate, so it stays at 1m and is interpolated up to the fine grid.
            float[,] gate = BlurCoverage(waterMask, res, WaterShoreBlurRadius + 1);
            var depthCoarse = new float[res, res];
            const float maxWaterDepth = 4f; // normalise depth into 0-1 range
            for (int z = 0; z < res; z++)
                for (int x = 0; x < res; x++)
                    if (gate[x, z] > 0f)
                        depthCoarse[x, z] = Mathf.Clamp01((WaterLevel - CalculateElevationAt(x, z)) / maxWaterDepth);

            // Distance from each water cell to the nearest land, in metres, for the ice: ice grows from the
            // shore inwards, so the shader needs to know how far in from the bank each pixel is.
            var landMask = new bool[res, res];
            for (int z = 0; z < res; z++)
                for (int x = 0; x < res; x++)
                    landMask[x, z] = !waterMask[x, z];
            float[,] shoreDist = ChamferDistanceTransform(landMask, res);
            const float maxShoreDistEncoded = 32f;

            Color[] maskPixels = new Color[fineRes * fineRes];
            float fineCell = 1f / WaterMeshSupersample;
            for (int z = 0; z < fineRes; z++)
            {
                for (int x = 0; x < fineRes; x++)
                {
                    float cov = fineCoverage[x, z];
                    if (cov <= 0.0005f)
                    {
                        maskPixels[z * fineRes + x] = new Color(0f, 0f, 0f, 0f);
                        continue;
                    }
                    // Coarse texel i held the elevation of metre i and sat at world i + 0.5, so world w maps to
                    // coarse index w - 0.5. Bilinear between the four surrounding coarse cells.
                    float fx = Mathf.Clamp((x + 0.5f) * fineCell - 0.5f, 0f, res - 1.001f);
                    float fz = Mathf.Clamp((z + 0.5f) * fineCell - 0.5f, 0f, res - 1.001f);
                    int x0 = (int)fx, z0 = (int)fz;
                    float tx = fx - x0, tz = fz - z0;
                    float depth = Mathf.Lerp(
                        Mathf.Lerp(depthCoarse[x0, z0], depthCoarse[x0 + 1, z0], tx),
                        Mathf.Lerp(depthCoarse[x0, z0 + 1], depthCoarse[x0 + 1, z0 + 1], tx), tz);
                    // Bilinear shore distance (same half-metre offset as the depth above).
                    float sd = Mathf.Lerp(
                        Mathf.Lerp(shoreDist[x0, z0], shoreDist[x0 + 1, z0], tx),
                        Mathf.Lerp(shoreDist[x0, z0 + 1], shoreDist[x0 + 1, z0 + 1], tx), tz);
                    // Still water (a pond) vs a river: rivers keep an open channel down the middle when they
                    // are wide, ponds freeze all the way across.
                    float wx = (x + 0.5f) * fineCell, wz = (z + 0.5f) * fineCell;
                    float isPond = 0f;
                    foreach (var pond in allPonds)
                    {
                        float reach = pond.radius * (1f + pond.irregularity) + 3f;
                        if ((new Vector2(wx, wz) - pond.center).sqrMagnitude <= reach * reach) { isPond = 1f; break; }
                    }
                    // R = depth, G = smooth coverage (0.5 contour = the shoreline),
                    // B = distance from the shore (0..32 m), A = 1 inside a pond, 0 in a river.
                    maskPixels[z * fineRes + x] = new Color(depth, cov, Mathf.Clamp01(sd / maxShoreDistEncoded), isPond);
                }
            }

            waterMaskTex.SetPixels(maskPixels);
            waterMaskTex.Apply();
        }

        /// <summary>Gaussian standard deviation of the shoreline blur, in metres. Larger = smoother, softer
        /// shore; a channel narrower than ~2 sigma starts to lose coverage.</summary>
        private const float WaterShoreSigmaMetres = 1.0f;
        /// <summary>Smooth 0..1 coverage of the fine mask, kept so the mesh can be dilated to cover it.</summary>
        private float[,] fineCoverage;

        /// <summary>Separable Gaussian blur of a binary mask (sigma in cells). The 0.5 contour of the result
        /// is a smooth curve even where the mask itself is a staircase.</summary>
        private static float[,] GaussianCoverage(bool[,] mask, int res, float sigmaCells)
        {
            int radius = Mathf.CeilToInt(sigmaCells * 3f);
            var kernel = new float[radius * 2 + 1];
            float sum = 0f;
            for (int i = -radius; i <= radius; i++)
            {
                kernel[i + radius] = Mathf.Exp(-(i * i) / (2f * sigmaCells * sigmaCells));
                sum += kernel[i + radius];
            }
            for (int i = 0; i < kernel.Length; i++) kernel[i] /= sum;

            var horiz = new float[res, res];
            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    float acc = 0f;
                    for (int d = -radius; d <= radius; d++)
                    {
                        int sx = x + d;
                        // Outside the map counts as the edge cell, so water touching the border does not fade.
                        sx = sx < 0 ? 0 : (sx >= res ? res - 1 : sx);
                        if (mask[sx, z]) acc += kernel[d + radius];
                    }
                    horiz[x, z] = acc;
                }
            }
            var result = new float[res, res];
            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    float acc = 0f;
                    for (int d = -radius; d <= radius; d++)
                    {
                        int sz = z + d;
                        sz = sz < 0 ? 0 : (sz >= res ? res - 1 : sz);
                        acc += horiz[x, sz] * kernel[d + radius];
                    }
                    result[x, z] = acc;
                }
            }
            return result;
        }

        // Shoreline smoothing: how many metres the water/land boundary blurs over. Also how far
        // CreateWaterSurface dilates the mesh past the true water mask, so there's fringe geometry for that
        // blurred edge to actually fade across instead of being clipped by mesh bounds.
        private const int WaterShoreBlurRadius = 3;

        /// <summary>Separable box blur of a binary mask into a smooth 0..1 coverage field.</summary>
        private static float[,] BlurCoverage(bool[,] mask, int res, int radius)
        {
            var horiz = new float[res, res];
            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    int sum = 0, count = 0;
                    for (int dx = -radius; dx <= radius; dx++)
                    {
                        int sx = x + dx;
                        if (sx < 0 || sx >= res) continue;
                        count++;
                        if (mask[sx, z]) sum++;
                    }
                    horiz[x, z] = count > 0 ? (float)sum / count : 0f;
                }
            }

            var result = new float[res, res];
            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    float sum = 0f;
                    int count = 0;
                    for (int dz = -radius; dz <= radius; dz++)
                    {
                        int sz = z + dz;
                        if (sz < 0 || sz >= res) continue;
                        count++;
                        sum += horiz[x, sz];
                    }
                    result[x, z] = count > 0 ? sum / count : 0f;
                }
            }
            return result;
        }

        /// <summary>Two-pass smoothing shared by the coarse and fine water masks: majority-filter the
        /// boundary, then drop single-cell isolated peninsulas.</summary>
        private static bool[,] SmoothBinaryMask(bool[,] mask, int res)
        {
            bool[,] smoothed = new bool[res, res];
            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    if (mask[x, z]) { smoothed[x, z] = true; continue; }
                    int count = 0;
                    if (x > 0 && mask[x - 1, z]) count++;
                    if (x < res - 1 && mask[x + 1, z]) count++;
                    if (z > 0 && mask[x, z - 1]) count++;
                    if (z < res - 1 && mask[x, z + 1]) count++;
                    smoothed[x, z] = count >= 3;
                }
            }
            for (int z = 1; z < res - 1; z++)
            {
                for (int x = 1; x < res - 1; x++)
                {
                    if (!smoothed[x, z]) continue;
                    int waterN = 0;
                    if (smoothed[x - 1, z]) waterN++;
                    if (smoothed[x + 1, z]) waterN++;
                    if (smoothed[x, z - 1]) waterN++;
                    if (smoothed[x, z + 1]) waterN++;
                    if (waterN == 0) smoothed[x, z] = false;
                }
            }
            return smoothed;
        }

        /// <summary>Rasterizes the same river/pond stamps as GenerateWaterMask, but at WaterMeshSupersample x
        /// the density, into fineWaterMask - used only by CreateWaterSurface for the visible mesh.</summary>
        private void BuildFineWaterMask(int coarseRes)
        {
            int fineRes = coarseRes * WaterMeshSupersample;
            float cell = 1f / WaterMeshSupersample;
            fineWaterMask = new bool[fineRes, fineRes];

            StampRiverFine(mainRiver, fineRes, cell);
            foreach (var branch in riverBranches)
                StampRiverFine(branch, fineRes, cell);

            foreach (var pond in allPonds)
            {
                int cx = Mathf.RoundToInt(pond.center.x / cell);
                int cz = Mathf.RoundToInt(pond.center.y / cell);
                int r = Mathf.CeilToInt(pond.radius * (1f + pond.irregularity) / cell) + 2;
                for (int dz = -r; dz <= r; dz++)
                {
                    for (int dx = -r; dx <= r; dx++)
                    {
                        int px = cx + dx, pz = cz + dz;
                        if (px < 0 || pz < 0 || px >= fineRes || pz >= fineRes) continue;
                        // Noise sampled in world metres (not fine pixels) so the pond's irregular shape looks
                        // identical in character to the coarse mask's, just traced at finer resolution.
                        float worldDx = dx * cell, worldDz = dz * cell;
                        float noise = BiomeNoise.FractalNoise2D(
                            worldDx * 0.15f, worldDz * 0.15f, 0.5f, 2, 0.5f, Mathf.RoundToInt(pond.noiseSeed));
                        float effectiveRadius = pond.radius * (1f - pond.irregularity + noise * pond.irregularity * 2f);
                        if (Mathf.Sqrt(worldDx * worldDx + worldDz * worldDz) <= effectiveRadius)
                            fineWaterMask[px, pz] = true;
                    }
                }
            }

            fineWaterMask = SmoothBinaryMask(fineWaterMask, fineRes);

            // The isolated-cell pass in SmoothBinaryMask only removes single lone cells, not small clusters
            // of a few connected fine cells - and the finer stamping here (edge noise, the river's own width
            // oscillation) can leave exactly that: a tiny 2-4 cell water blob disconnected from the main
            // channel. Since the coarse waterMask (elevation/biome) never carves the ground under one of
            // these - it's below the majority threshold - the flat water mesh built over it just floats a
            // small water patch on top of un-carved grass. Keep only components above a minimum size.
            fineWaterMask = RemoveSmallComponents(fineWaterMask, fineRes, minComponentSize: 25);
        }

        /// <summary>Flood-fills every connected (8-directional) true component in mask and drops any smaller
        /// than minComponentSize - used to remove small stray water blobs disconnected from the main body.</summary>
        private static bool[,] RemoveSmallComponents(bool[,] mask, int res, int minComponentSize)
        {
            bool[,] visited = new bool[res, res];
            bool[,] result = new bool[res, res];
            var stack = new System.Collections.Generic.Stack<Vector2Int>();
            var component = new System.Collections.Generic.List<Vector2Int>();

            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    if (!mask[x, z] || visited[x, z]) continue;

                    component.Clear();
                    stack.Push(new Vector2Int(x, z));
                    visited[x, z] = true;
                    while (stack.Count > 0)
                    {
                        Vector2Int c = stack.Pop();
                        component.Add(c);
                        for (int dz = -1; dz <= 1; dz++)
                        {
                            for (int dx = -1; dx <= 1; dx++)
                            {
                                if (dx == 0 && dz == 0) continue;
                                int nx = c.x + dx, nz = c.y + dz;
                                if (nx < 0 || nz < 0 || nx >= res || nz >= res) continue;
                                if (!mask[nx, nz] || visited[nx, nz]) continue;
                                visited[nx, nz] = true;
                                stack.Push(new Vector2Int(nx, nz));
                            }
                        }
                    }

                    if (component.Count >= minComponentSize)
                        foreach (Vector2Int c in component) result[c.x, c.y] = true;
                }
            }
            return result;
        }

        private void StampRiverFine(RiverFeature river, int fineRes, float cell)
        {
            float pathLength = (river.end - river.start).magnitude;
            int steps = Mathf.CeilToInt(pathLength / (cell * 0.5f)) + 1;
            for (int i = 0; i <= steps; i++)
            {
                float t = (float)i / steps;
                Vector2 pt = GetRiverPoint(t, river);
                float hw = GetRiverHalfWidthAt(t, river);
                int cx = Mathf.RoundToInt(pt.x / cell);
                int cz = Mathf.RoundToInt(pt.y / cell);
                int r = Mathf.CeilToInt(hw / cell) + 1;
                for (int dz = -r; dz <= r; dz++)
                {
                    for (int dx = -r; dx <= r; dx++)
                    {
                        int px = cx + dx, pz = cz + dz;
                        if (px < 0 || pz < 0 || px >= fineRes || pz >= fineRes) continue;
                        float worldDx = dx * cell, worldDz = dz * cell;
                        if (Mathf.Sqrt(worldDx * worldDx + worldDz * worldDz) <= hw)
                            fineWaterMask[px, pz] = true;
                    }
                }
            }
        }

        private void StampRiver(RiverFeature river, int res)
        {
            float pathLength = (river.end - river.start).magnitude;
            int steps = Mathf.CeilToInt(pathLength / 0.5f) + 1;
            for (int i = 0; i <= steps; i++)
            {
                float t = (float)i / steps;
                Vector2 pt = GetRiverPoint(t, river);
                float hw = GetRiverHalfWidthAt(t, river);
                int cx = Mathf.RoundToInt(pt.x);
                int cz = Mathf.RoundToInt(pt.y);
                int r = Mathf.CeilToInt(hw) + 1;
                for (int dz = -r; dz <= r; dz++)
                {
                    for (int dx = -r; dx <= r; dx++)
                    {
                        int px = cx + dx, pz = cz + dz;
                        if (px < 0 || pz < 0 || px >= res || pz >= res) continue;
                        if (Mathf.Sqrt(dx * dx + dz * dz) <= hw)
                            waterMask[px, pz] = true;
                    }
                }
            }
        }

        /// <summary>
        /// Two-pass chamfer distance transform: computes approximate Euclidean distance from
        /// every cell to the nearest water cell. Used by CalculateElevationAt for shoreline banks.
        /// </summary>
        private void ComputeWaterDistanceField()
        {
            int res = waterMask.GetLength(0);
            waterDistField = ChamferDistanceTransform(waterMask, res);

            // Distance from each WATER cell to the nearest LAND cell (0 on land, same transform on the
            // inverted mask) - used to taper the riverbed/pondbed shallow near the shore. Without this the
            // bed sat at a near-constant depth right up to the shore, then jumped straight to bank height at
            // the edge: a real body of water shallows gradually as it nears the bank, so a constant-depth bed
            // meeting a flat water surface read as the surface hovering over a bed that never rose to meet it.
            bool[,] invertedMask = new bool[res, res];
            for (int z = 0; z < res; z++)
                for (int x = 0; x < res; x++)
                    invertedMask[x, z] = !waterMask[x, z];
            shoreDepthField = ChamferDistanceTransform(invertedMask, res);
        }

        /// <summary>Two-pass chamfer distance transform: approximate Euclidean distance from every cell to
        /// the nearest `true` cell in mask.</summary>
        private static float[,] ChamferDistanceTransform(bool[,] mask, int res)
        {
            float[,] dist = new float[res, res];
            for (int z = 0; z < res; z++)
                for (int x = 0; x < res; x++)
                    dist[x, z] = mask[x, z] ? 0f : 999f;

            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    if (x > 0) dist[x, z] = Mathf.Min(dist[x, z], dist[x - 1, z] + 1);
                    if (z > 0) dist[x, z] = Mathf.Min(dist[x, z], dist[x, z - 1] + 1);
                    if (x > 0 && z > 0) dist[x, z] = Mathf.Min(dist[x, z], dist[x - 1, z - 1] + 1.414f);
                    if (x < res - 1 && z > 0) dist[x, z] = Mathf.Min(dist[x, z], dist[x + 1, z - 1] + 1.414f);
                }
            }
            for (int z = res - 1; z >= 0; z--)
            {
                for (int x = res - 1; x >= 0; x--)
                {
                    if (x < res - 1) dist[x, z] = Mathf.Min(dist[x, z], dist[x + 1, z] + 1);
                    if (z < res - 1) dist[x, z] = Mathf.Min(dist[x, z], dist[x, z + 1] + 1);
                    if (x < res - 1 && z < res - 1) dist[x, z] = Mathf.Min(dist[x, z], dist[x + 1, z + 1] + 1.414f);
                    if (x > 0 && z < res - 1) dist[x, z] = Mathf.Min(dist[x, z], dist[x - 1, z + 1] + 1.414f);
                }
            }
            return dist;
        }

        /// <summary>Query whether a world position is inside a water feature.</summary>
        public bool IsWaterAt(float worldX, float worldZ)
        {
            if (waterMask == null) return false;
            int mx = Mathf.RoundToInt(worldX);
            int mz = Mathf.RoundToInt(worldZ);
            int res = waterMask.GetLength(0);
            if (mx < 0 || mz < 0 || mx >= res || mz >= res) return false;
            return waterMask[mx, mz];
        }

        /// <summary>Query distance to nearest water in metres (0 if inside water).
        /// Uses bilinear interpolation on the distance field for smooth shoreline banks.</summary>
        public float GetWaterDistance(float worldX, float worldZ)
        {
            if (waterDistField == null) return 999f;
            int res = waterDistField.GetLength(0);

            // True bilinear sample of the distance field (the previous nearest-cell lookup gave blocky,
            // 1m-stepped distances that carried straight into the bank height gradient as sharp angular
            // facets instead of a smooth curve into the water).
            float fx = Mathf.Clamp(worldX, 0f, res - 1.001f);
            float fz = Mathf.Clamp(worldZ, 0f, res - 1.001f);
            int x0 = Mathf.FloorToInt(fx), z0 = Mathf.FloorToInt(fz);
            int x1 = Mathf.Min(x0 + 1, res - 1), z1 = Mathf.Min(z0 + 1, res - 1);
            float tx = fx - x0, tz = fz - z0;

            float d00 = waterDistField[x0, z0], d10 = waterDistField[x1, z0];
            float d01 = waterDistField[x0, z1], d11 = waterDistField[x1, z1];
            float dx0 = Mathf.Lerp(d00, d10, tx);
            float dx1 = Mathf.Lerp(d01, d11, tx);
            return Mathf.Lerp(dx0, dx1, tz);
        }

        /// <summary>True if the point is inside any pond (using noise-perturbed radius).</summary>
        private bool IsInsidePond(float worldX, float worldZ)
        {
            foreach (var pond in allPonds)
            {
                float dx = worldX - pond.center.x;
                float dz = worldZ - pond.center.y;
                float dist = Mathf.Sqrt(dx * dx + dz * dz);
                float noise = BiomeNoise.FractalNoise2D(
                    dx * 0.15f, dz * 0.15f, 0.5f, 2, 0.5f, Mathf.RoundToInt(pond.noiseSeed));
                float effectiveRadius = pond.radius * (1f - pond.irregularity + noise * pond.irregularity * 2f);
                if (dist < effectiveRadius)
                    return true;
            }
            return false;
        }

        /// <summary>
        /// Creates the water surface mesh from the water mask. Only water cells become
        /// geometry, so the mesh exactly follows the river channel and pond shapes.
        /// Vertices sit at WaterLevel; the shader displaces them for ripples.
        /// </summary>
        private void CreateWaterSurface()
        {
            // Built from fineWaterMask (WaterMeshSupersample x finer than the 1m waterMask used everywhere
            // else) so the mesh's own silhouette has steps a fraction of a metre wide instead of a full
            // metre - no amount of shader alpha-fading can smooth an edge whose underlying polygon shape is
            // still a 1m staircase, so this is a resolution fix, not a shading one.
            int fineRes = fineWaterMask.GetLength(0);
            if (fineCoverage == null || fineCoverage.GetLength(0) != fineRes)
                fineCoverage = GaussianCoverage(fineWaterMask, fineRes, WaterShoreSigmaMetres * WaterMeshSupersample);
            float cell = 1f / WaterMeshSupersample;
            List<Vector3> vertices = new List<Vector3>();
            List<Vector2> uvs = new List<Vector2>();
            List<int> triangles = new List<int>();

            int waterCellCount = 0;
            for (int z = 0; z < fineRes - 1; z++)
            {
                for (int x = 0; x < fineRes - 1; x++)
                {
                    // Exactly the true water mask, no dilation: the bank just past the shore sits just under
                    // WaterLevel on purpose (so it can rise smoothly - see CalculateElevationAt), so extending
                    // the water mesh onto it made the water visibly flood the bank. The shore blur below
                    // instead feathers alpha INWARD from this same true edge, never drawing over dry land.
                    // Every cell the blur reaches, not just true water: the shader draws the shoreline at the
                    // 0.5 coverage contour and is fully transparent beyond it, so the extra geometry is invisible
                    // and only exists so the smooth contour is never clipped by a polygon boundary.
                    if (fineCoverage[x, z] < 0.02f && fineCoverage[x + 1, z] < 0.02f && fineCoverage[x, z + 1] < 0.02f && fineCoverage[x + 1, z + 1] < 0.02f) continue;
                    waterCellCount++;
                    int baseIdx = vertices.Count;
                    float wy = (WaterLevel + 14f);
                    float wx0 = x * cell, wx1 = (x + 1) * cell;
                    float wz0 = z * cell, wz1 = (z + 1) * cell;
                    vertices.Add(new Vector3(wx0, wy, wz0));
                    vertices.Add(new Vector3(wx1, wy, wz0));
                    vertices.Add(new Vector3(wx0, wy, wz1));
                    vertices.Add(new Vector3(wx1, wy, wz1));
                    float u0 = wx0 / terrainSizeX, u1 = wx1 / terrainSizeX;
                    float v0 = wz0 / terrainSizeZ, v1 = wz1 / terrainSizeZ;
                    uvs.Add(new Vector2(u0, v0));
                    uvs.Add(new Vector2(u1, v0));
                    uvs.Add(new Vector2(u0, v1));
                    uvs.Add(new Vector2(u1, v1));
                    triangles.Add(baseIdx); triangles.Add(baseIdx + 2); triangles.Add(baseIdx + 1);
                    triangles.Add(baseIdx + 1); triangles.Add(baseIdx + 2); triangles.Add(baseIdx + 3);
                }
            }

            // Destroy any existing WaterSurface children (the cached reference may be
            // null after a recompile/scene reload, so also search by name).
            if (waterSurfaceObj != null)
                DestroyImmediate(waterSurfaceObj);
            for (int i = transform.childCount - 1; i >= 0; i--)
            {
                var child = transform.GetChild(i);
                if (child.name == "WaterSurface")
                    DestroyImmediate(child.gameObject);
            }

            waterSurfaceObj = new GameObject("WaterSurface");
            waterSurfaceObj.transform.SetParent(transform, false);
            waterSurfaceObj.transform.localPosition = Vector3.zero;

            MeshFilter mf = waterSurfaceObj.AddComponent<MeshFilter>();
            MeshRenderer mr = waterSurfaceObj.AddComponent<MeshRenderer>();

            Mesh mesh = new Mesh { name = "WaterMesh" };
            // The finer mesh resolution can comfortably exceed 65535 vertices for a large water body.
            if (vertices.Count > 60000) mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            mesh.vertices = vertices.ToArray();
            mesh.uv = uvs.ToArray();
            mesh.triangles = triangles.ToArray();
            mesh.RecalculateNormals();
            mf.mesh = mesh;

            Debug.Log($"[TerrainGen] CreateWaterSurface: fineRes={fineRes}, waterCells={waterCellCount}, verts={mesh.vertexCount}, tris={mesh.triangles.Length/3}, maskTex={(waterMaskTex != null ? waterMaskTex.width+"x"+waterMaskTex.height : "NULL")}");

            Shader waterShader = Shader.Find("Homesteader/WaterSurface");
            if (waterShader != null)
            {
                Material mat = new Material(waterShader);
                if (waterMaskTex != null)
                    mat.SetTexture("_WaterMask", waterMaskTex);
                mat.SetVector("_TerrainBounds", new Vector4(terrainSizeX, terrainSizeZ, terrainHeight, 0f));
                mr.material = mat;
            }
            else
            {
                Debug.LogWarning("[TerrainGen] WaterSurface shader not found!");
            }
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
        }

        // ========================================================================
        //  BIOME LOOKUP
        // ========================================================================

        public BiomeData GetBiomeById(string id)
        {
            for (int i = 0; i < biomes.Count; i++)
            {
                if (biomes[i].id == id) return biomes[i];
            }
            return biomes.Count > 0 ? biomes[biomes.Count - 1] : null;
        }

        // ========================================================================
        //  ELEVATION
        // ========================================================================

        /// <summary>
        /// Quantizes elevation into discrete terrace steps for a stylized contour look.
        /// Water cells are exempt — riverbeds and pondbeds stay smooth so the water surface
        /// sits naturally above a continuous bed rather than stepped shelves.
        /// </summary>
        private float TerraceElevation(float elevMeters, float worldX, float worldZ)
        {
            float terraced = TerraceElevationCore(elevMeters, worldX, worldZ);
            // The road bed is not terraced (terrace steps across a road would read as a staircase), easing back to
            // the terraces a few metres off its edge.
            float road = RoadInfluence(worldX, worldZ);
            return road > 0f ? Mathf.Lerp(terraced, elevMeters, road) : terraced;
        }

        private float TerraceElevationCore(float elevMeters, float worldX, float worldZ)
        {
            if (!terraceEnabled || IsWaterAt(worldX, worldZ))
                return elevMeters;

            // Skip terracing in the edge falloff zone — terracing the smooth border
            // slope creates visible stacked platforms at map edges.
            float edgeDist = Mathf.Min(Mathf.Min(worldX, worldZ), Mathf.Min(terrainSizeX - worldX, terrainSizeZ - worldZ));
            const float edgeFalloff = 45f;
            if (edgeDist < edgeFalloff)
                return elevMeters;

            // Skip terracing near water — the shoreline bank needs to rise smoothly
            // so the player can climb out of rivers. CalculateElevationAt already blends the
            // bank/valley smoothly out to 40m (20m bank rise + 20m valley), so the terrace
            // exemption has to match that same distance - stopping at 20m here used to let the
            // 20-40m valley band get terrace-quantized on top of an already-smooth curve,
            // producing a hard step right where the shoreline was supposed to ease in.
            float waterDist = GetWaterDistance(worldX, worldZ);
            if (waterDist < 40f)
                return elevMeters;

            // Flat plateau in the middle of each step, easing smoothly into the next step near the edge -
            // terraced, but soft step-ups/downs instead of a vertical cliff every terraceStepMeters.
            float quant = Mathf.Round(elevMeters / terraceStepMeters) * terraceStepMeters;
            float offset = elevMeters - quant;                       // -0.5..0.5 step-widths from the tread centre
            float t = offset / terraceStepMeters;
            float absT = Mathf.Abs(t);
            float plateauHalf = terraceFlatness * 0.5f;
            float terraced = quant;
            if (absT > plateauHalf)
            {
                float u = Mathf.InverseLerp(plateauHalf, 0.5f, absT);
                u = Mathf.SmoothStep(0f, 1f, u);
                terraced = Mathf.Lerp(quant, elevMeters, u);
            }

            // Fade terracing in over the 20m past the water-smoothing band (40-60m out) rather than
            // switching straight to it, so the shoreline valley hands off into the terraced land smoothly.
            const float terraceFadeDistance = 20f;
            if (waterDist < 40f + terraceFadeDistance)
            {
                float fade = Mathf.SmoothStep(0f, 1f, (waterDist - 40f) / terraceFadeDistance);
                return Mathf.Lerp(elevMeters, terraced, fade);
            }
            return terraced;
        }

        /// <summary>
        /// Calculates physical ground elevation with edge falloff, riverbed carving, and
        /// smooth shoreline banks. Water features carve the terrain below WaterLevel so the
        /// water mesh (at WaterLevel) forms a surface above the bed.
        /// </summary>
        public float CalculateElevationAt(float worldX, float worldZ)
        {
            // 1. Macro undulating landscape — gentle rolling hills, kept low so all areas stay walkable.
            float largeHills = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0035f, 3, 0.5f, worldSeed + 777) * 11.0f - 5.5f;
            float rolling = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.008f, 2, 0.5f, worldSeed + 444) * 3.6f - 1.8f;
            float elevBase = largeHills + rolling;

            // 2. Gentle northern rise (Z > 240m) — reduced so the north stays accessible.
            if (worldZ > 240f)
            {
                float northT = (worldZ - 240f) / 260f;
                elevBase += northT * northT * 4.0f;
            }

            // 3. Micro ground texture detail
            float micro = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.035f, 2, 0.5f, worldSeed + 999) * 0.2f;
            float elev = elevBase + micro;

            // 4. No edge falloff — terrain generates fully to the map borders

            // 5. Water features: carve riverbed/pondbed below water level, shallowing near the shore so the
            // bed rises to meet the (flat) water surface instead of staying at a near-constant depth right
            // up to the bank - see shoreDepthField's remarks in ComputeWaterDistanceField.
            if (IsWaterAt(worldX, worldZ))
            {
                float fullDepth = 0.4f + BiomeNoise.ValueNoise2D(worldX * 0.1f, worldZ * 0.1f, worldSeed + 42) * 0.3f;
                const float shoreTaperDistance = 6f;
                float distToLand = shoreDepthField != null
                    ? shoreDepthField[Mathf.Clamp(Mathf.RoundToInt(worldX), 0, shoreDepthField.GetLength(0) - 1),
                                      Mathf.Clamp(Mathf.RoundToInt(worldZ), 0, shoreDepthField.GetLength(1) - 1)]
                    : shoreTaperDistance;
                float shallowT = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(distToLand / shoreTaperDistance));
                // Never shallower than 0.25m: at 0.05m the bed was a hair under the surface, so heightmap interpolation and
                // the ripples let terrain poke through the water. The bank below starts at the same height.
                float depth = Mathf.Lerp(0.25f, fullDepth, shallowT);
                return WaterLevel - depth;
            }

            // 6. Shoreline banks: smooth rise from water edge to surrounding terrain.
            // The bank must rise gradually enough that the CharacterController
            // (slopeLimit=45, stepOffset=0.3) can climb out. A 0.5m rise over 20m
            // is a ~1.4 degree slope — easily walkable.
            float waterDist = GetWaterDistance(worldX, worldZ);
            if (waterDist < 40f)
            {
                const float bankRiseDistance = 20f;
                const float bankRiseHeight = 0.5f;
                float minLandHeight = Mathf.Clamp(elevBase, WaterLevel, WaterLevel + bankRiseHeight);

                if (waterDist < bankRiseDistance)
                {
                    float t = Mathf.SmoothStep(0f, 1f, waterDist / bankRiseDistance);
                    return Mathf.Lerp(WaterLevel - 0.25f, minLandHeight, t);
                }

                // Valley floor: gradual blend from bank to full elevation
                const float valleyWidth = 20f;
                float shoreDist = waterDist - bankRiseDistance;
                float vt = Mathf.SmoothStep(0f, 1f, Mathf.Max(0f, shoreDist) / valleyWidth);
                return Mathf.Lerp(minLandHeight, elevBase, vt) + micro * vt;
            }

            return elev;
        }

        // ========================================================================
        //  BIOME EVALUATION
        // ========================================================================

        /// <summary>How big the noise-driven biome regions (forests, meadows, plains, arid lands) are relative to
        /// the original tuning: 1.15 = every region 15% larger in each direction. It divides the noise frequency,
        /// so the same seed gives the same style of layout at a larger scale (features move, they don't just grow).</summary>
        private const float BiomeSizeScale = 1.15f;

        private struct SandPit { public float x, z, radius; }
        private List<SandPit> _sandPits;
        private int _sandPitsSeed = int.MinValue;

        /// <summary>The sand pits for the current world seed: 2 or 3 centres on dry ground off the road and clear of the water, each 5 to 9 m in radius.</summary>
        private List<SandPit> SandPits()
        {
            if (_sandPits != null && _sandPitsSeed == worldSeed) return _sandPits;
            _sandPitsSeed = worldSeed;
            _sandPits = new List<SandPit>();
            var rng = new System.Random(worldSeed * 31 + 7919);
            int want = 2 + rng.Next(2);
            for (int attempt = 0; attempt < 200 && _sandPits.Count < want; attempt++)
            {
                float x = 40f + (float)rng.NextDouble() * (terrainSizeX - 80f);
                float z = 40f + (float)rng.NextDouble() * (terrainSizeZ - 80f);
                float r = 5f + (float)rng.NextDouble() * 4f;
                if (InStarterGrassArea(x, z) || GetWaterDistance(x, z) < r + 8f || IsNearRoad(x, z, r + 3f)) continue;
                bool apart = true;
                foreach (SandPit p in _sandPits) if ((p.x - x) * (p.x - x) + (p.z - z) * (p.z - z) < 60f * 60f) apart = false;
                if (!apart) continue;
                _sandPits.Add(new SandPit { x = x, z = z, radius = r });
            }
            return _sandPits;
        }

        private bool InSandPit(float worldX, float worldZ)
        {
            foreach (SandPit p in SandPits())
            {
                float dx = worldX - p.x, dz = worldZ - p.z;
                float d2 = dx * dx + dz * dz;
                if (d2 > (p.radius * 1.5f) * (p.radius * 1.5f)) continue;
                // an irregular outline: the radius wobbles with noise round the pit
                float wob = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.22f, 2, 0.5f, worldSeed + 6161);
                float rr = p.radius * (0.55f + wob * 0.9f);
                if (d2 < rr * rr) return true;
            }
            return false;
        }

        public BiomeData EvaluateBiomeAt(float worldX, float worldZ)
        {
            float elev = CalculateElevationAt(worldX, worldZ);
            return EvaluateBiomeAt(worldX, worldZ, elev);
        }

        public BiomeData EvaluateBiomeAt(float worldX, float worldZ, float elev)
        {
            // 1. Water — classified from the water mask, not analytic distance fields.
            if (IsWaterAt(worldX, worldZ))
            {
                if (IsInsidePond(worldX, worldZ))
                {
                    // Deep water in the pond core, shallower at the fringe
                    foreach (var pond in allPonds)
                    {
                        float dx = worldX - pond.center.x;
                        float dz = worldZ - pond.center.y;
                        float d = Mathf.Sqrt(dx * dx + dz * dz);
                        float noise = BiomeNoise.FractalNoise2D(
                            dx * 0.15f, dz * 0.15f, 0.5f, 2, 0.5f, Mathf.RoundToInt(pond.noiseSeed));
                        float effectiveRadius = pond.radius * (1f - pond.irregularity + noise * pond.irregularity * 2f);
                        if (d < effectiveRadius)
                        {
                            return d < effectiveRadius * 0.45f
                                ? GetBiomeById("biome_lake")
                                : GetBiomeById("biome_pond");
                        }
                    }
                }
                return GetBiomeById("biome_river");
            }

            // 1b. Starter zone rule (GameRules.StarterZone): the ground right around where the player begins is always
            // some form of grass - never marsh, scrub, rock or forest - whatever the seed.
            if (InStarterGrassArea(worldX, worldZ)) return StarterGrassBiome(worldX, worldZ);

            // 2. Shoreline fringe — narrow band around water, with noise-perturbed edge
            float waterDist = GetWaterDistance(worldX, worldZ);
            float fringeNoise = (BiomeNoise.ValueNoise2D(worldX * 0.05f, worldZ * 0.05f, worldSeed + 555) - 0.5f) * 3f;
            // Sand: random stretches of the shoreline (a low-frequency mask, so it comes in beaches, not speckles), a few metres wide
            if (waterDist < 5f + fringeNoise * 0.7f
                && BiomeNoise.FractalNoise2D(worldX, worldZ, 0.03f, 2, 0.5f, worldSeed + 4242) > 0.52f)
                return GetBiomeById("biome_sand");

            if (waterDist < 4f + fringeNoise)
            {
                float shoreNoise = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.06f, 2, 0.5f, worldSeed + 555);
                if (shoreNoise > 0.74f) return GetBiomeById("biome_dry_lands");
                if (shoreNoise < 0.30f) return GetBiomeById("biome_meadow");
                return GetBiomeById("biome_wetland_marsh");
            }

            // 2b. Sand pits: two or three small irregular patches of sand around the map
            if (InSandPit(worldX, worldZ)) return GetBiomeById("biome_sand");

            // 3. Willow Grove: patches of damp ground within a few strides of the water, past the shoreline fringe
            if (waterDist < 18f)
            {
                float groveNoise = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.02f / BiomeSizeScale, 2, 0.5f, worldSeed + 313);
                if (groveNoise > 0.54f) return GetBiomeById("biome_willow_grove");
            }

            // 4. Highlands & Mountain Knolls — thresholds lowered for the smoother terrain
            if (elev > 4.5f) return GetBiomeById("biome_rocky_ridge");
            if (elev > 2.5f) return GetBiomeById("biome_pine_hills");

            // 5. Arid Dry Lands (South-West corner, noise-gated)
            if (worldX < 70f && worldZ < 75f)
            {
                float aridNoise = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.03f / BiomeSizeScale, 2, 0.5f, worldSeed + 888);
                if (aridNoise > 0.45f) return GetBiomeById("biome_dry_lands");
            }

            // 6. Amorphous Regional Forest & Meadow Blobs
            float rNoise1 = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0275f / BiomeSizeScale, 3, 0.5f, worldSeed + 101);
            float rNoise2 = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0275f / BiomeSizeScale, 3, 0.5f, worldSeed + 202);

            // The grass band (meadow and plains) is the middle of rNoise1. It is +-0.118 wide, 15% more area than the
            // original +-0.100 (measured over four seeds: 53.5% -> 61.4% of the map before water, hills and the
            // starter zone override it), so the forests give up that much ground to grass.
            const float GrassBandHalf = 0.118f;
            if (rNoise1 > 0.5f + GrassBandHalf)
            {
                if (rNoise2 > 0.66f) return GetBiomeById("biome_maple_forest");
                if (rNoise2 > 0.33f) return GetBiomeById("biome_mixed_forest");
                return GetBiomeById("biome_birch_forest");
            }
            else if (rNoise1 < 0.5f - GrassBandHalf)
            {
                if (rNoise2 > 0.66f) return GetBiomeById("biome_oak_forest");
                if (rNoise2 > 0.33f) return GetBiomeById("biome_mixed_forest");
                return GetBiomeById("biome_poplar_forest");
            }
            else
            {
                return (rNoise2 > 0.50f)
                    ? GetBiomeById("biome_grass_plains")
                    : GetBiomeById("biome_meadow");
            }
        }

        // ========================================================================
        //  TERRAIN GENERATION
        // ========================================================================

        [ContextMenu("Generate Terrain")]
        public void GenerateTerrain()
        {
            Random.InitState(worldSeed);
            targetTerrain = GetComponent<Terrain>();
            if (targetTerrain == null) return;
            terrainData = targetTerrain.terrainData;
            terrainData.size = new Vector3(terrainSizeX, terrainHeight, terrainSizeZ);

            // Generate water features + mask + distance field BEFORE heightmap
            GenerateWaterFeatures();
            EnforceStarterZoneWater();
            GenerateWaterMask();
            ComputeWaterDistanceField();
            GenerateStarterRoad();

            int heightmapResolution = terrainData.heightmapResolution;
            float[,] heights = new float[heightmapResolution, heightmapResolution];

            int mapRes = Mathf.RoundToInt(terrainSizeX);
            if (bakedBiomeMap == null || bakedBiomeMap.width != mapRes)
            {
                bakedBiomeMap = new Texture2D(mapRes, mapRes, TextureFormat.RGBA32, false, true)
                {
                    filterMode = FilterMode.Bilinear,
                    wrapMode = TextureWrapMode.Clamp
                };
            }
            else
            {
                bakedBiomeMap.filterMode = FilterMode.Bilinear;
            }

            Color[] mapPixels = new Color[mapRes * mapRes];

            // 1. Generate procedural heightmap
            for (int z = 0; z < heightmapResolution; z++)
            {
                for (int x = 0; x < heightmapResolution; x++)
                {
                    float worldX = (float)x / (heightmapResolution - 1) * terrainSizeX;
                    float worldZ = (float)z / (heightmapResolution - 1) * terrainSizeZ;
                    float elevMeters = CalculateElevationAt(worldX, worldZ);
                    elevMeters = TerraceElevation(elevMeters, worldX, worldZ);
                    heights[z, x] = Mathf.Clamp01((elevMeters + 14f) / terrainHeight);
                }
            }
            terrainData.SetHeights(0, 0, heights);

            // 2. Bake biome control map
            for (int py = 0; py < mapRes; py++)
            {
                for (int px = 0; px < mapRes; px++)
                {
                    float worldX = ((float)px + 0.5f) / mapRes * terrainSizeX;
                    float worldZ = ((float)py + 0.5f) / mapRes * terrainSizeZ;
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
                            case "biome_willow_grove": modeInt = 16; break;
                            case "biome_sand": modeInt = 17; break;
                            default: modeInt = 0; break;
                        }
                    }

                    Color tint = Color.white;
                    if (biome == null || string.IsNullOrEmpty(biome.color_hex) ||
                        !ColorUtility.TryParseHtmlString(biome.color_hex, out tint))
                    {
                        tint = new Color(0.518f, 0.800f, 0.086f);
                    }
                    float a = (modeInt + 0.5f) / 18.0f;
                    mapPixels[py * mapRes + px] = new Color(tint.r, tint.g, tint.b, a);
                }
            }

            bakedBiomeMap.SetPixels(mapPixels);
            bakedBiomeMap.Apply();

            // Build border factor texture: 0 = interior, 1 = border.
            Texture2D borderTex = new Texture2D(mapRes, mapRes, TextureFormat.R8, false);
            borderTex.filterMode = FilterMode.Bilinear;
            borderTex.wrapMode = TextureWrapMode.Clamp;
            Color[] borderPixels = new Color[mapRes * mapRes];
            const int borderRadius = 6;
            for (int py = 0; py < mapRes; py++)
            {
                for (int px = 0; px < mapRes; px++)
                {
                    float myMode = mapPixels[py * mapRes + px].a;
                    int diff = 0, total = 0;
                    for (int dy = -borderRadius; dy <= borderRadius; dy++)
                    {
                        for (int dx = -borderRadius; dx <= borderRadius; dx++)
                        {
                            if (dx == 0 && dy == 0) continue;
                            int nx = Mathf.Clamp(px + dx, 0, mapRes - 1);
                            int ny = Mathf.Clamp(py + dy, 0, mapRes - 1);
                            float nMode = mapPixels[ny * mapRes + nx].a;
                            total++;
                            if (Mathf.Abs(nMode - myMode) > 0.01f) diff++;
                        }
                    }
                    // Amplify: sqrt makes small border values more visible
                    float bf = Mathf.Sqrt((float)diff / total);
                    borderPixels[py * mapRes + px] = new Color(bf, 0, 0, 1);
                }
            }
            borderTex.SetPixels(borderPixels);
            borderTex.Apply();

        if (targetTerrain.materialTemplate != null)
        {
            targetTerrain.materialTemplate.SetTexture("_BiomeMap", bakedBiomeMap);
            targetTerrain.materialTemplate.SetTexture("_BiomeBorderTex", borderTex);
            targetTerrain.materialTemplate.SetVector("_TerrainBounds", new Vector4(terrainSizeX, terrainSizeZ, terrainHeight, 0f));
            // Same smooth (bilinear, blurred) coverage texture the water surface fades alpha across - used by
            // the terrain shader to blend the water-bed color into the land color across a real band instead
            // of switching at the hard, point-sampled biomeMode boundary (isWater true/false can't itself be
            // smooth - IDs don't blend - so the fix is blending the two colors, not the branch condition).
            if (waterMaskTex != null) targetTerrain.materialTemplate.SetTexture("_WaterMask", waterMaskTex);
            ApplyRoadMaskToMaterial(targetTerrain.materialTemplate);
        }

        // 3. Create water surface mesh
            CreateWaterSurface();

            SpawnBiomeAssets();
            RegenerateGrass();
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

            // Procedural trees, rocks, shoreline and prairie dressing (see ProceduralVegetation.cs).
            if (proceduralVegetationEnabled) Homesteader.World.ProceduralVegetation.Generate(this);

            // Bridges where the road crosses water (ProceduralBridge.cs).
            Homesteader.World.ProceduralBridge.Generate(this);
        }

        /// <summary>
        /// Regenerates GPU-instanced grass blades from the baked biome map.
        /// </summary>
        /// <summary>TEMPORARY switch: turn the GPU grass off entirely (set true to bring it back).</summary>
        public bool grassEnabled = false;

        private void RegenerateGrass()
        {
            if (!grassEnabled) return;
            var grassRenderer = GetComponent<Homesteader.Grass.GrassRenderer>();
            if (grassRenderer == null)
                grassRenderer = gameObject.AddComponent<Homesteader.Grass.GrassRenderer>();
            grassRenderer.Regenerate();
        }

        /// <summary>
        /// Async version of GenerateTerrain that yields periodically so the main thread
        /// can update a progress bar.
        /// </summary>
        public IEnumerator GenerateTerrainAsync()
        {
            Random.InitState(worldSeed);
            Debug.Log($"[TerrainGen] GenerateTerrainAsync started with seed {worldSeed}");

            IsGenerating = true;
            GenerationProgress = 0f;

            targetTerrain = GetComponent<Terrain>();
            if (targetTerrain == null)
            {
                IsGenerating = false;
                GenerationProgress = 1f;
                yield break;
            }
            terrainData = targetTerrain.terrainData;
            terrainData.size = new Vector3(terrainSizeX, terrainHeight, terrainSizeZ);

            // Generate water features + mask + distance field BEFORE heightmap
            GenerationPhase = "Generating water features...";
            GenerateWaterFeatures();
            EnforceStarterZoneWater();
            GenerateWaterMask();
            ComputeWaterDistanceField();
            GenerationPhase = "Laying the road...";
            GenerateStarterRoad();
            GenerationProgress = 0.05f;
            yield return null;

            int heightmapResolution = terrainData.heightmapResolution;
            float[,] heights = new float[heightmapResolution, heightmapResolution];

            int mapRes = Mathf.RoundToInt(terrainSizeX);
            if (bakedBiomeMap == null || bakedBiomeMap.width != mapRes)
            {
                bakedBiomeMap = new Texture2D(mapRes, mapRes, TextureFormat.RGBA32, false, true)
                {
                    filterMode = FilterMode.Bilinear,
                    wrapMode = TextureWrapMode.Clamp
                };
            }
            else
            {
                bakedBiomeMap.filterMode = FilterMode.Bilinear;
            }

            Color[] mapPixels = new Color[mapRes * mapRes];

            // Phase 1: Heightmap (5% .. 40%)
            GenerationPhase = "Generating heightmap...";
            for (int z = 0; z < heightmapResolution; z++)
            {
                for (int x = 0; x < heightmapResolution; x++)
                {
                    float worldX = (float)x / (heightmapResolution - 1) * terrainSizeX;
                    float worldZ = (float)z / (heightmapResolution - 1) * terrainSizeZ;
                    float elevMeters = CalculateElevationAt(worldX, worldZ);
                    elevMeters = TerraceElevation(elevMeters, worldX, worldZ);
                    heights[z, x] = Mathf.Clamp01((elevMeters + 14f) / terrainHeight);
                }
                if (z % 64 == 0)
                {
                    GenerationProgress = Mathf.Lerp(0.05f, 0.40f, (float)z / heightmapResolution);
                    yield return null;
                }
            }
            terrainData.SetHeights(0, 0, heights);
            GenerationProgress = 0.40f;
            yield return null;

            // Phase 2: Biome control map (40% .. 70%)
            GenerationPhase = "Baking biome map...";
            for (int py = 0; py < mapRes; py++)
            {
                for (int px = 0; px < mapRes; px++)
                {
                    float worldX = ((float)px + 0.5f) / mapRes * terrainSizeX;
                    float worldZ = ((float)py + 0.5f) / mapRes * terrainSizeZ;
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
                            case "biome_willow_grove": modeInt = 16; break;
                            case "biome_sand": modeInt = 17; break;
                            default: modeInt = 0; break;
                        }
                    }

                    Color tint = Color.white;
                    if (biome == null || string.IsNullOrEmpty(biome.color_hex) ||
                        !ColorUtility.TryParseHtmlString(biome.color_hex, out tint))
                    {
                        tint = new Color(0.518f, 0.800f, 0.086f);
                    }
                    float a = (modeInt + 0.5f) / 18.0f;
                    mapPixels[py * mapRes + px] = new Color(tint.r, tint.g, tint.b, a);
                }
                if (py % 50 == 0)
                {
                    GenerationProgress = Mathf.Lerp(0.40f, 0.70f, (float)py / mapRes);
                    yield return null;
                }
            }
            GenerationProgress = 0.70f;
            yield return null;

            GenerationProgress = 0.85f;
            yield return null;

            bakedBiomeMap.SetPixels(mapPixels);
            bakedBiomeMap.Apply();

            // Build border factor texture: 0 = interior, 1 = border.
            GenerationPhase = "Computing biome borders...";
            {
                Texture2D borderTex = new Texture2D(mapRes, mapRes, TextureFormat.R8, false);
                borderTex.filterMode = FilterMode.Bilinear;
                borderTex.wrapMode = TextureWrapMode.Clamp;
                Color[] borderPixels = new Color[mapRes * mapRes];
                const int borderRadius = 6;
                for (int py = 0; py < mapRes; py++)
                {
                    for (int px = 0; px < mapRes; px++)
                    {
                        float myMode = mapPixels[py * mapRes + px].a;
                        int diff = 0, total = 0;
                        for (int dy = -borderRadius; dy <= borderRadius; dy++)
                        {
                            for (int dx = -borderRadius; dx <= borderRadius; dx++)
                            {
                                if (dx == 0 && dy == 0) continue;
                                int nx = Mathf.Clamp(px + dx, 0, mapRes - 1);
                                int ny = Mathf.Clamp(py + dy, 0, mapRes - 1);
                                float nMode = mapPixels[ny * mapRes + nx].a;
                                total++;
                                if (Mathf.Abs(nMode - myMode) > 0.01f) diff++;
                            }
                        }
                        float bf = Mathf.Sqrt((float)diff / total);
                        borderPixels[py * mapRes + px] = new Color(bf, 0, 0, 1);
                    }
                    if (py % 100 == 0) yield return null;
                }
                borderTex.SetPixels(borderPixels);
                borderTex.Apply();

                if (targetTerrain.materialTemplate != null)
                {
                    targetTerrain.materialTemplate.SetTexture("_BiomeMap", bakedBiomeMap);
                    targetTerrain.materialTemplate.SetTexture("_BiomeBorderTex", borderTex);
                    targetTerrain.materialTemplate.SetVector("_TerrainBounds", new Vector4(terrainSizeX, terrainSizeZ, terrainHeight, 0f));
                    if (waterMaskTex != null) targetTerrain.materialTemplate.SetTexture("_WaterMask", waterMaskTex);
                    ApplyRoadMaskToMaterial(targetTerrain.materialTemplate);
                }
            }
            GenerationProgress = 0.85f;
            yield return null;

            // Phase 4: Water surface mesh (85% .. 90%)
            GenerationPhase = "Creating water surface...";
            CreateWaterSurface();
            GenerationProgress = 0.90f;
            yield return null;

            // Phase 5: Asset spawning (90% .. 100%)
            GenerationPhase = "Scattering biome assets...";
            SpawnBiomeAssets();

            // Phase 6: Grass rendering
            GenerationPhase = "Planting grass...";
            RegenerateGrass();

            Homesteader.UI.MiniMap.InvalidateCache();

            GenerationProgress = 1f;
            GenerationPhase = "";
            IsGenerating = false;
        }
    }
}
