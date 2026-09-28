using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Generation
{
    [RequireComponent(typeof(Terrain))]
    public class HomesteaderTerrainGenerator : MonoBehaviour
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

        [Header("Biome Definitions")]
        public List<BiomeData> biomes = new List<BiomeData>();

        [Header("Asset Catalog Spawning (Inverted Architecture)")]
        public List<AssetManifestSummary> registeredAssets = new List<AssetManifestSummary>();

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
        private Texture2D waterMaskTex;      // For the water shader
        private GameObject waterSurfaceObj;

        /// <summary>
        /// Generates seeded water features: 1 SW-to-NE river with up to 2 branches, up to 2 ponds.
        /// River touches at least one map edge (starts on south edge, ends on north edge).
        /// </summary>
        private void GenerateWaterFeatures()
        {
            // Main river: SW to NE. Start on south edge (western half), end on north edge (eastern half).
            float startX = Random.Range(50f, 200f);
            float endX = Random.Range(300f, 450f);
            mainRiver = new RiverFeature
            {
                start = new Vector2(startX, 0f),
                end = new Vector2(endX, terrainSizeZ),
                halfWidth = Random.Range(4f, 7f),
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
                float splitT = Random.Range(0.3f, 0.7f);
                Vector2 splitPoint = GetRiverPoint(splitT, mainRiver);

                bool accepted = false;
                for (int attempt = 0; attempt < 15 && !accepted; attempt++)
                {
                    float branchEndX = splitPoint.x + Random.Range(60f, 150f) * (Random.value > 0.5f ? 1f : -1f);
                    float branchEndZ = Random.Range(300f, terrainSizeZ);
                    branchEndX = Mathf.Clamp(branchEndX, 0f, terrainSizeX);

                    var candidate = new RiverFeature
                    {
                        start = splitPoint,
                        end = new Vector2(branchEndX, branchEndZ),
                        halfWidth = mainRiver.halfWidth * Random.Range(0.4f, 0.7f),
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

        /// <summary>Parametric point on a river path at parameter t [0,1].</summary>
        private Vector2 GetRiverPoint(float t, RiverFeature river)
        {
            Vector2 basePt = Vector2.Lerp(river.start, river.end, t);
            Vector2 dir = (river.end - river.start).normalized;
            Vector2 perp = new Vector2(-dir.y, dir.x);
            float meander = Mathf.Sin(t * river.meanderFreq * Mathf.PI * 2f + river.meanderPhase) * river.meanderAmp;
            meander += Mathf.Sin(t * river.meanderFreq * 2.5f + river.meanderPhase + 1.2f) * river.meanderAmp * 0.25f;
            return basePt + perp * meander;
        }

        /// <summary>Half-width of a river at parameter t, with slight variation.</summary>
        private float GetRiverHalfWidthAt(float t, RiverFeature river)
        {
            return river.halfWidth + Mathf.Sin(t * 8f + river.meanderPhase) * river.halfWidth * 0.2f;
        }

        /// <summary>
        /// Checks if a candidate river's centerline enters an existing river's channel,
        /// excluding the branch origin zone where they intentionally meet.
        /// Returns true if the candidate crosses the existing river beyond the branch point.
        /// </summary>
        private bool RiverCrossesRiver(RiverFeature candidate, RiverFeature existing)
        {
            // Tolerance around the branch origin — skip points near the candidate's start
            // so the intentional junction isn't flagged as a crossing.
            float branchTolerance = existing.halfWidth * 2f + 5f;

            float pathLength = (candidate.end - candidate.start).magnitude;
            int steps = Mathf.CeilToInt(pathLength / 1f) + 1;

            // Pre-compute existing river path points for efficiency.
            int existingSteps = Mathf.CeilToInt((existing.end - existing.start).magnitude / 1f) + 1;
            Vector2[] existingPts = new Vector2[existingSteps + 1];
            for (int j = 0; j <= existingSteps; j++)
            {
                float et = (float)j / existingSteps;
                existingPts[j] = GetRiverPoint(et, existing);
            }

            for (int i = 0; i <= steps; i++)
            {
                float t = (float)i / steps;
                Vector2 pt = GetRiverPoint(t, candidate);

                // Skip the branch origin zone.
                if (Vector2.Distance(pt, candidate.start) < branchTolerance)
                    continue;

                // Find minimum distance from this point to the existing river's centerline.
                float minDist = float.MaxValue;
                for (int j = 0; j <= existingSteps; j++)
                {
                    float d = Vector2.Distance(pt, existingPts[j]);
                    if (d < minDist) minDist = d;
                }

                // If the candidate's centerline enters the existing river's channel, it's a crossing.
                if (minDist < existing.halfWidth)
                    return true;
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
            waterMask = new bool[res, res];

            StampRiver(mainRiver, res);
            foreach (var branch in riverBranches)
                StampRiver(branch, res);

            foreach (var pond in allPonds)
            {
                int cx = Mathf.RoundToInt(pond.center.x);
                int cz = Mathf.RoundToInt(pond.center.y);
                int r = Mathf.CeilToInt(pond.radius * (1f + pond.irregularity)) + 2;
                for (int dz = -r; dz <= r; dz++)
                {
                    for (int dx = -r; dx <= r; dx++)
                    {
                        int px = cx + dx, pz = cz + dz;
                        if (px < 0 || pz < 0 || px >= res || pz >= res) continue;
                        // Noise-perturbed radius for irregular pond shapes
                        float angle = Mathf.Atan2(dz, dx);
                        float noise = BiomeNoise.FractalNoise2D(
                            dx * 0.15f, dz * 0.15f, 0.5f, 2, 0.5f, Mathf.RoundToInt(pond.noiseSeed));
                        float effectiveRadius = pond.radius * (1f - pond.irregularity + noise * pond.irregularity * 2f);
                        if (Mathf.Sqrt(dx * dx + dz * dz) <= effectiveRadius)
                            waterMask[px, pz] = true;
                    }
                }
            }

            // Smooth the water mask boundary to remove jagged pixelated shorelines.
            // Pass 1: A cell is water if it or 2+ of its 4 neighbours are water (majority filter).
            bool[,] smoothed = new bool[res, res];
            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    if (waterMask[x, z]) { smoothed[x, z] = true; continue; }
                    int count = 0;
                    if (x > 0 && waterMask[x - 1, z]) count++;
                    if (x < res - 1 && waterMask[x + 1, z]) count++;
                    if (z > 0 && waterMask[x, z - 1]) count++;
                    if (z < res - 1 && waterMask[x, z + 1]) count++;
                    smoothed[x, z] = count >= 3;
                }
            }
            // Pass 2: remove single-cell peninsulas for cleaner edges
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
                    if (waterN == 0) smoothed[x, z] = false; // isolated water cell
                }
            }
            waterMask = smoothed;

            // Build water mask texture for the shader
            if (waterMaskTex == null || waterMaskTex.width != res)
            {
                waterMaskTex = new Texture2D(res, res, TextureFormat.RGBA32, false, true)
                {
                    filterMode = FilterMode.Bilinear,
                    wrapMode = TextureWrapMode.Clamp
                };
            }
            Color[] maskPixels = new Color[res * res];
            const float maxWaterDepth = 4f; // normalise depth into 0-1 range
            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    if (!waterMask[x, z])
                    {
                        maskPixels[z * res + x] = Color.black;
                        continue;
                    }
                    // Encode water depth in R channel (0 = no water, >0 = water depth)
                    float bedElev = CalculateElevationAt(x, z);
                    float depth = Mathf.Clamp01((WaterLevel - bedElev) / maxWaterDepth);
                    // R = depth (0-1), G = 1 (water flag for shader), B = 0, A = 1
                    maskPixels[z * res + x] = new Color(depth, 1f, 0f, 1f);
                }
            }

            waterMaskTex.SetPixels(maskPixels);
            waterMaskTex.Apply();
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
            waterDistField = new float[res, res];

            for (int z = 0; z < res; z++)
                for (int x = 0; x < res; x++)
                    waterDistField[x, z] = waterMask[x, z] ? 0f : 999f;

            // Forward pass
            for (int z = 0; z < res; z++)
            {
                for (int x = 0; x < res; x++)
                {
                    if (x > 0) waterDistField[x, z] = Mathf.Min(waterDistField[x, z], waterDistField[x - 1, z] + 1);
                    if (z > 0) waterDistField[x, z] = Mathf.Min(waterDistField[x, z], waterDistField[x, z - 1] + 1);
                    if (x > 0 && z > 0) waterDistField[x, z] = Mathf.Min(waterDistField[x, z], waterDistField[x - 1, z - 1] + 1.414f);
                    if (x < res - 1 && z > 0) waterDistField[x, z] = Mathf.Min(waterDistField[x, z], waterDistField[x + 1, z - 1] + 1.414f);
                }
            }
            // Backward pass
            for (int z = res - 1; z >= 0; z--)
            {
                for (int x = res - 1; x >= 0; x--)
                {
                    if (x < res - 1) waterDistField[x, z] = Mathf.Min(waterDistField[x, z], waterDistField[x + 1, z] + 1);
                    if (z < res - 1) waterDistField[x, z] = Mathf.Min(waterDistField[x, z], waterDistField[x, z + 1] + 1);
                    if (x < res - 1 && z < res - 1) waterDistField[x, z] = Mathf.Min(waterDistField[x, z], waterDistField[x + 1, z + 1] + 1.414f);
                    if (x > 0 && z < res - 1) waterDistField[x, z] = Mathf.Min(waterDistField[x, z], waterDistField[x - 1, z + 1] + 1.414f);
                }
            }
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
        private float GetWaterDistance(float worldX, float worldZ)
        {
            if (waterDistField == null) return 999f;
            int res = waterDistField.GetLength(0);
            int x = Mathf.Clamp(Mathf.RoundToInt(worldX), 0, res - 1);
            int z = Mathf.Clamp(Mathf.RoundToInt(worldZ), 0, res - 1);
            return waterDistField[x, z];
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
            int res = waterMask.GetLength(0);
            List<Vector3> vertices = new List<Vector3>();
            List<Vector2> uvs = new List<Vector2>();
            List<int> triangles = new List<int>();

            int waterCellCount = 0;
            for (int z = 0; z < res - 1; z++)
            {
                for (int x = 0; x < res - 1; x++)
                {
                    if (!waterMask[x, z]) continue;
                    waterCellCount++;
                    int baseIdx = vertices.Count;
                    float wy = (WaterLevel + 14f);
                    vertices.Add(new Vector3(x, wy, z));
                    vertices.Add(new Vector3(x + 1, wy, z));
                    vertices.Add(new Vector3(x, wy, z + 1));
                    vertices.Add(new Vector3(x + 1, wy, z + 1));
                    float u0 = (float)x / res, u1 = (float)(x + 1) / res;
                    float v0 = (float)z / res, v1 = (float)(z + 1) / res;
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
            mesh.vertices = vertices.ToArray();
            mesh.uv = uvs.ToArray();
            mesh.triangles = triangles.ToArray();
            mesh.RecalculateNormals();
            mf.mesh = mesh;

            Debug.Log($"[TerrainGen] CreateWaterSurface: res={res}, waterCells={waterCellCount}, verts={mesh.vertexCount}, tris={mesh.triangles.Length/3}, maskTex={(waterMaskTex != null ? waterMaskTex.width+"x"+waterMaskTex.height : "NULL")}");

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
            if (!terraceEnabled || IsWaterAt(worldX, worldZ))
                return elevMeters;

            // Skip terracing in the edge falloff zone — terracing the smooth border
            // slope creates visible stacked platforms at map edges.
            float edgeDist = Mathf.Min(Mathf.Min(worldX, worldZ), Mathf.Min(terrainSizeX - worldX, terrainSizeZ - worldZ));
            const float edgeFalloff = 45f;
            if (edgeDist < edgeFalloff)
                return elevMeters;

            // Skip terracing near water — the shoreline bank needs to rise smoothly
            // so the player can climb out of rivers. Terracing the bank creates
            // vertical cliffs that trap the player in the water.
            float waterDist = GetWaterDistance(worldX, worldZ);
            if (waterDist < 20f)
                return elevMeters;

            return Mathf.Round(elevMeters / terraceStepMeters) * terraceStepMeters;
        }

        /// <summary>
        /// Calculates physical ground elevation with edge falloff, riverbed carving, and
        /// smooth shoreline banks. Water features carve the terrain below WaterLevel so the
        /// water mesh (at WaterLevel) forms a surface above the bed.
        /// </summary>
        public float CalculateElevationAt(float worldX, float worldZ)
        {
            // 1. Macro undulating landscape — gentle rolling hills, kept low so all areas stay walkable.
            float largeHills = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0035f, 3, 0.5f, worldSeed + 777) * 6.0f - 3.0f;
            float rolling = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.008f, 2, 0.5f, worldSeed + 444) * 2.0f - 1.0f;
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

            // 5. Water features: carve riverbed/pondbed below water level
            if (IsWaterAt(worldX, worldZ))
            {
                float depth = 0.4f + BiomeNoise.ValueNoise2D(worldX * 0.1f, worldZ * 0.1f, worldSeed + 42) * 0.3f;
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
                    return Mathf.Lerp(WaterLevel - 0.1f, minLandHeight, t);
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

        [Header("Starter Field")]
        [Tooltip("Carve a farmland biome plot around the player spawn (terrain-local metres).")]
        public bool starterFieldEnabled = false;
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

            // 2. Shoreline fringe — narrow band around water, with noise-perturbed edge
            float waterDist = GetWaterDistance(worldX, worldZ);
            float fringeNoise = (BiomeNoise.ValueNoise2D(worldX * 0.05f, worldZ * 0.05f, worldSeed + 555) - 0.5f) * 3f;
            if (waterDist < 4f + fringeNoise)
            {
                float shoreNoise = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.06f, 2, 0.5f, worldSeed + 555);
                if (shoreNoise > 0.74f) return GetBiomeById("biome_dry_lands");
                if (shoreNoise < 0.30f) return GetBiomeById("biome_meadow");
                return GetBiomeById("biome_wetland_marsh");
            }

            // 3. Starter field: farmland plot around the player spawn
            if (starterFieldEnabled &&
                Mathf.Abs(worldX - starterFieldCenter.x) < starterFieldHalfSize.x &&
                Mathf.Abs(worldZ - starterFieldCenter.y) < starterFieldHalfSize.y)
            {
                return GetBiomeById("biome_farmland");
            }

            // 4. Highlands & Mountain Knolls — thresholds lowered for the smoother terrain
            if (elev > 4.5f) return GetBiomeById("biome_rocky_ridge");
            if (elev > 2.5f) return GetBiomeById("biome_pine_hills");

            // 5. Arid Dry Lands (South-West corner, noise-gated)
            if (worldX < 70f && worldZ < 75f)
            {
                float aridNoise = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.03f, 2, 0.5f, worldSeed + 888);
                if (aridNoise > 0.45f) return GetBiomeById("biome_dry_lands");
            }

            // 6. Amorphous Regional Forest & Meadow Blobs
            float rNoise1 = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0275f, 3, 0.5f, worldSeed + 101);
            float rNoise2 = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0275f, 3, 0.5f, worldSeed + 202);

            if (rNoise1 > 0.60f)
            {
                if (rNoise2 > 0.66f) return GetBiomeById("biome_maple_forest");
                if (rNoise2 > 0.33f) return GetBiomeById("biome_mixed_forest");
                return GetBiomeById("biome_birch_forest");
            }
            else if (rNoise1 < 0.40f)
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
            GenerateWaterMask();
            ComputeWaterDistanceField();

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
                    float worldX = (float)px / mapRes * terrainSizeX;
                    float worldZ = (float)py / mapRes * terrainSizeZ;
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

                    Color tint = Color.white;
                    if (biome == null || string.IsNullOrEmpty(biome.color_hex) ||
                        !ColorUtility.TryParseHtmlString(biome.color_hex, out tint))
                    {
                        tint = new Color(0.518f, 0.800f, 0.086f);
                    }
                    float a = (modeInt + 0.5f) / 16.0f;
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
        }

        /// <summary>
        /// Regenerates GPU-instanced grass blades from the baked biome map.
        /// </summary>
        private void RegenerateGrass()
        {
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
            GenerateWaterMask();
            ComputeWaterDistanceField();
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
                    float worldX = (float)px / mapRes * terrainSizeX;
                    float worldZ = (float)py / mapRes * terrainSizeZ;
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

                    Color tint = Color.white;
                    if (biome == null || string.IsNullOrEmpty(biome.color_hex) ||
                        !ColorUtility.TryParseHtmlString(biome.color_hex, out tint))
                    {
                        tint = new Color(0.518f, 0.800f, 0.086f);
                    }
                    float a = (modeInt + 0.5f) / 16.0f;
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
