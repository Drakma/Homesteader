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

        public readonly Vector2 pondCenter = new Vector2(220f, 210f);

        /// <summary>
        /// Calculates the central winding curve of the river spine through the valley floor.
        /// Layered at several unrelated frequencies (rather than 2 smooth harmonics) so it
        /// meanders like a real river instead of a single lazy S-curve.
        /// </summary>
        public float GetRiverCenterX(float worldZ)
        {
            return 220f
                + Mathf.Sin(worldZ * 0.015f) * 45f
                + Mathf.Sin(worldZ * 0.035f + 1.2f) * 18f
                + Mathf.Sin(worldZ * 0.006f + 2.7f) * 30f
                + Mathf.Sin(worldZ * 0.07f + 0.4f) * 8f;
        }

        /// <summary>
        /// Half-width of the river channel, in metres - varies along its length instead of a
        /// constant width, like a real river narrowing and widening. Also flares out into a wide
        /// funnel-shaped mouth as it nears the pond, so the two water bodies erode into one
        /// smooth entrance instead of a narrow channel butting into the pond's edge.
        /// </summary>
        public float GetRiverHalfWidth(float worldX, float worldZ)
        {
            float baseWidth = Mathf.Clamp(
                4.0f + Mathf.Sin(worldZ * 0.04f) * 1.8f + Mathf.Sin(worldZ * 0.11f + 1.0f) * 1.2f,
                2.2f, 6.5f);

            float distToPondCenter = Vector2.Distance(new Vector2(worldX, worldZ), pondCenter);
            float mouthT = 1f - Mathf.Clamp01((distToPondCenter - 20f) / 35f);
            float mouthWiden = Mathf.SmoothStep(0f, 1f, mouthT) * 16f;

            // Per-position wobble (not just a function of Z) so the bank has real inlets/points
            // rather than a perfectly symmetric width change along the channel.
            float riverInlet = (Mathf.PerlinNoise(worldX * 0.12f + 15f, worldZ * 0.12f + 15f) - 0.5f) * 5f;

            return baseWidth + mouthWiden + riverInlet;
        }

        /// <summary>
        /// Organic perturbed radius of the natural kettle pond basin. Several unrelated
        /// frequencies plus two Perlin octaves (a broad wobble and a tighter one) so the
        /// shoreline has real inlets and small peninsulas, not a smooth flower-petal curve.
        /// </summary>
        public float GetPondRadius(float worldX, float worldZ)
        {
            float dx = worldX - pondCenter.x;
            float dz = worldZ - pondCenter.y;
            float angle = Mathf.Atan2(dz, dx);
            float inlets = (Mathf.PerlinNoise(Mathf.Cos(angle) * 3f + 40f, Mathf.Sin(angle) * 3f + 40f) - 0.5f) * 16f
                         + (Mathf.PerlinNoise(Mathf.Cos(angle) * 8f + 70f, Mathf.Sin(angle) * 8f + 70f) - 0.5f) * 8f;
            return 24f
                + Mathf.Sin(angle * 2f) * 7f
                + Mathf.Cos(angle * 3f) * 5f
                + Mathf.Sin(angle * 5f + 1.3f) * 3f
                + Mathf.Cos(angle * 7f + 0.7f) * 2f
                + inlets;
        }

        /// <summary>
        /// Whether the river gets a branching tributary - a per-world coin flip off the seed,
        /// independent of the island one.
        /// </summary>
        public bool RiverHasBranch => ((worldSeed / 3) % 2) == 0;

        private const float branchStartZ = 260f;

        /// <summary>
        /// Central curve of the tributary, only meaningful for worldZ > branchStartZ. Starts
        /// exactly at the main river's own centerline (offset 0) and diverges away from there,
        /// so it visibly splits off the main channel instead of appearing out of nowhere a fixed
        /// distance away from it.
        /// </summary>
        public float GetBranchCenterX(float worldZ)
        {
            float mainX = GetRiverCenterX(worldZ);
            float tLinear = Mathf.Clamp01((worldZ - branchStartZ) / 140f);
            // Smoothstep, not linear: a linear ramp has a nonzero slope right at the split, so the
            // branch immediately veers away at a visible angle - a sharp corner against the main
            // channel's bank. Smoothstep has zero slope at t=0, so it leaves tangent to the main
            // river and only gradually curves away.
            float t = tLinear * tLinear * (3f - 2f * tLinear);
            return mainX + t * 90f + Mathf.Sin(worldZ * 0.02f + 1f) * 12f * t;
        }

        /// <summary>
        /// Distance to the nearer of the main river and its optional branch, with that
        /// channel's own half-width. Centralizes the branch logic so CalculateElevationAt and
        /// EvaluateBiomeAt (and the shader) all treat the branch exactly like the main river.
        /// </summary>
        public float GetNearestRiverDistance(float worldX, float worldZ, out float halfWidth)
        {
            float mainX = GetRiverCenterX(worldZ);
            float distMain = Mathf.Abs(worldX - mainX);
            float mainHalfWidth = GetRiverHalfWidth(worldX, worldZ);
            halfWidth = mainHalfWidth;

            if (RiverHasBranch && worldZ > branchStartZ)
            {
                float branchX = GetBranchCenterX(worldZ);
                float distBranch = Mathf.Abs(worldX - branchX);

                // Tapers from a small-but-visible width up to full over the first 25m past the
                // split, so the tributary reads as narrowing off the main river. Tapering all the
                // way from 0 left a stretch thinner than the shoreline foam band itself, which
                // rendered as two bare foam lines with no visible water between them.
                float widthTaper = Mathf.Clamp01((worldZ - branchStartZ) / 25f);
                float branchFullWidth = Mathf.Clamp(mainHalfWidth * 0.6f, 1.8f, 4.5f);
                float branchHalfWidth = Mathf.Lerp(1.2f, branchFullWidth, widthTaper);

                // Smooth-min (polynomial), not a hard "whichever is closer": picking the strictly
                // nearer channel always leaves a sharp crease along the line where the two distance
                // fields are equal, no matter how smoothly the branch's own centerline curves away.
                // This rounds that seam off over a `blend` metre radius instead.
                const float blend = 6f;
                float h = Mathf.Clamp01(0.5f + 0.5f * (distMain - distBranch) / blend);
                float dist = Mathf.Lerp(distMain, distBranch, h) - blend * h * (1f - h);
                halfWidth = Mathf.Lerp(mainHalfWidth, branchHalfWidth, h);
                return dist;
            }
            return distMain;
        }

        /// <summary>
        /// Whether the pond gets a small island - a per-world coin flip off the seed, not always.
        /// </summary>
        public bool PondHasIsland => (worldSeed & 1) == 0;

        public readonly Vector2 islandOffset = new Vector2(7f, -5f);

        /// <summary>
        /// Irregular radius of the pond's optional island, in the same lumpy style as the
        /// shoreline itself.
        /// </summary>
        public float GetIslandRadius(float worldX, float worldZ, out float distToIsland)
        {
            Vector2 islandCenter = pondCenter + islandOffset;
            distToIsland = Vector2.Distance(new Vector2(worldX, worldZ), islandCenter);
            float angle = Mathf.Atan2(worldZ - islandCenter.y, worldX - islandCenter.x);
            return 6f + Mathf.Sin(angle * 3f) * 2f + Mathf.Cos(angle * 5f + 0.5f) * 1.2f;
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
        /// Water level, shared by every water feature (river, its branch, and the pond) - one
        /// constant flat plane. It used to grade uphill/downhill along the river's length, which
        /// is what caused the "breaks" where that slope met the pond's own flat level and could
        /// leave the water surface riding up or down with the surrounding terrain.
        /// </summary>
        public const float WaterLevel = 0.5f;

        public float GetRiverWaterLevel(float worldZ) => WaterLevel;

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
            // Smooth base (no high-frequency detail) - used as the shoreline target below. The
            // full "micro" detail term has a ~29m wavelength, short enough to wobble non-
            // monotonically within just the 10-35m shore/valley zone, which turned the "rise to
            // natural elevation" target into a bumpy one instead of a smooth ramp - a visible ridge
            // even after capping the rise height itself.
            float elevBase = largeHills + rolling;

            // 2. Highland mountain rise to the north (Z > 240m)
            if (worldZ > 240f)
            {
                float northT = (worldZ - 240f) / 260f;
                elevBase += northT * northT * 10.0f;
            }

            // 3. Micro ground texture detail on dry land
            float micro = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.035f, 2, 0.5f, worldSeed + 999) * 0.4f;
            float elev = elevBase + micro;

            // 4. HYDROLOGICAL FLAT CARVER
            const float pondWaterLevel = 0.5f;
            float riverWaterLevel = GetRiverWaterLevel(worldZ);

            float distToPond = Vector2.Distance(new Vector2(worldX, worldZ), pondCenter);
            float pondRadius = GetPondRadius(worldX, worldZ);
            float distToRiver = GetNearestRiverDistance(worldX, worldZ, out float riverHalfWidth);

            bool isPondWater = distToPond <= pondRadius;
            bool isRiverWater = !isPondWater && (distToRiver <= riverHalfWidth);

            // Optional island in the pond: carve it back out of the water, with its own small
            // rise and beach, instead of the pond being solid water end to end.
            if (isPondWater && PondHasIsland)
            {
                float islandRadius = GetIslandRadius(worldX, worldZ, out float distToIsland);
                if (distToIsland < islandRadius)
                {
                    float islandT = Mathf.SmoothStep(0f, 1f, 1f - distToIsland / islandRadius);
                    return Mathf.Lerp(pondWaterLevel + 0.8f, pondWaterLevel + 2.5f, islandT);
                }
                if (distToIsland < islandRadius + 2.5f)
                {
                    float t = Mathf.SmoothStep(0f, 1f, (distToIsland - islandRadius) / 2.5f);
                    return Mathf.Lerp(pondWaterLevel + 0.8f, pondWaterLevel, t);
                }
            }

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
            float riverBankDist = distToRiver - riverHalfWidth;

            // Immediate bank rises gently to this LOW capped height first - never straight to
            // whatever the local hill noise happens to be, which is what made banks feel like
            // steep, too-deep drop-offs wherever they crossed higher ground. The remaining climb
            // up to the real surrounding elevation happens gradually over the wider valley floor
            // below. Spread over a wide distance so it reads as a gradual slope, not a dropoff.
            const float bankRiseHeight = 1.0f;
            const float bankRiseDistance = 10.0f;
            // Clamped ABOVE at a natural terrain height, never forced up to a minimum bump - a
            // forced minimum still overshot above the real elevation wherever the natural ground
            // nearby was already low (very common right next to water, since water tends to sit in
            // low ground to begin with), so the valley floor had to dip back down from that forced
            // bump to the real, lower elevation - a visible ridge/levee right at the shore. The
            // only floor is the water's own level, so land can't dip below the water surface it's
            // bordering, but otherwise this rises to whatever the natural elevation actually is.
            float pondMinLandHeight = Mathf.Clamp(elevBase, pondWaterLevel, pondWaterLevel + bankRiseHeight);
            float riverMinLandHeight = Mathf.Clamp(elevBase, riverWaterLevel, riverWaterLevel + bankRiseHeight);
            float minLandHeight = (distToPond < 55.0f) ? pondMinLandHeight : riverMinLandHeight;

            if (pondBankDist < bankRiseDistance && pondBankDist >= 0f)
            {
                float t = Mathf.SmoothStep(0f, 1f, pondBankDist / bankRiseDistance);
                return Mathf.Lerp(pondWaterLevel, pondMinLandHeight, t);
            }
            else if (riverBankDist < bankRiseDistance && riverBankDist >= 0f)
            {
                float t = Mathf.SmoothStep(0f, 1f, riverBankDist / bankRiseDistance);
                return Mathf.Lerp(riverWaterLevel, riverMinLandHeight, t);
            }

            // C. Gentle valley floor around the river & pond. Measured as distance PAST the bank
            // zone above (not raw distance to the water), so it starts at exactly minLandHeight
            // where the bank zone leaves off - otherwise the two zones use different distance
            // metrics and the height jumps right at the seam between them.
            const float valleyWidth = 25.0f;
            float shoreDist = Mathf.Min(pondBankDist, riverBankDist) - bankRiseDistance;
            if (shoreDist < valleyWidth)
            {
                float vt = Mathf.SmoothStep(0f, 1f, Mathf.Max(0f, shoreDist) / valleyWidth);
                // Blends toward elevBase (also smooth, no high-frequency wobble), fading the micro
                // detail back in as vt approaches 1 so it reaches full elev exactly where this zone
                // ends and the unconstrained "return elev" below takes over - no seam between them.
                return Mathf.Lerp(minLandHeight, elevBase, vt) + micro * vt;
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
            float distToRiver = GetNearestRiverDistance(worldX, worldZ, out float riverHalfWidth);
            float distToPond = Vector2.Distance(new Vector2(worldX, worldZ), pondCenter);
            float pondRadius = GetPondRadius(worldX, worldZ);

            // 1. Water (Strictly in the sunken channels - occupying ~3% of map).
            // Pond is checked first: the river's path runs through the pond, and without this
            // order the river would win there and cut a visible seam straight across the pond.
            if (distToPond < pondRadius)
            {
                if (PondHasIsland)
                {
                    float islandRadius = GetIslandRadius(worldX, worldZ, out float distToIsland);
                    if (distToIsland < islandRadius) return GetBiomeById("biome_meadow");
                    if (distToIsland < islandRadius + 2.5f) return GetBiomeById("biome_dry_lands");
                }
                // Deep water in the body's core, shallower pond fringe around it - so both the
                // lake and pond biomes are actually reachable, not just pond.
                return distToPond < pondRadius * 0.45f
                    ? GetBiomeById("biome_lake")
                    : GetBiomeById("biome_pond");
            }
            if (distToRiver < riverHalfWidth)
            {
                return GetBiomeById("biome_river");
            }

            // 2. Shoreline fringe - a narrow beach band, not a wide ring, with its outer edge
            // perturbed by noise so it has real inlets and coves instead of tracing a perfectly
            // parallel offset of the water's edge. Varies what actually grows there (bog, sand,
            // or just grass running down to the waterline) instead of wetland_marsh being the
            // only thing that ever spawns next to water. Gated strictly to !isWater (checked
            // above already returned) so the fringe can never paint over the water itself, even
            // where the river's path runs close to the pond.
            float fringeNoise = (Mathf.PerlinNoise(worldX * 0.05f + 90f, worldZ * 0.05f + 90f) - 0.5f) * 3f;
            if (distToRiver < riverHalfWidth + 1.5f + fringeNoise || distToPond < (pondRadius + 2.5f + fringeNoise))
            {
                float shoreNoise = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.06f, 2, 0.5f, worldSeed + 555);
                if (shoreNoise > 0.74f) return GetBiomeById("biome_dry_lands");   // sandy/dirt bank
                if (shoreNoise < 0.30f) return GetBiomeById("biome_meadow");     // grass right to the waterline
                return GetBiomeById("biome_wetland_marsh");                      // boggy patch
            }

            // Maintained lawn is a cultivated yard, not a naturally-occurring biome - it no longer
            // spawns as part of normal terrain generation (mirrors the farmland fix).

            // 4a. Starter field: a farmland plot around the player spawn so crops can be planted right away.
            if (starterFieldEnabled &&
                Mathf.Abs(worldX - starterFieldCenter.x) < starterFieldHalfSize.x &&
                Mathf.Abs(worldZ - starterFieldCenter.y) < starterFieldHalfSize.y)
            {
                return GetBiomeById("biome_farmland");
            }

            // Farmland is deliberately placed only (the starter field above) - it's cultivated
            // by the player, not a naturally-occurring biome, so it no longer spawns as part of
            // normal terrain generation.

            // 5. Highlands & Mountain Knolls (North & High Peaks). The macro hill noise (rolling
            // -6..+6m plus the north-edge rise) rarely exceeds ~10-11m anywhere on the map, so the
            // old 14m rocky_ridge threshold was above the terrain's actual achievable range and
            // that biome could never spawn; 8.5/5.5 sit inside the real range while still keeping
            // rocky_ridge rarer than pine_hills.
            if (elev > 8.5f)
            {
                return GetBiomeById("biome_rocky_ridge");
            }
            if (elev > 5.5f)
            {
                return GetBiomeById("biome_pine_hills");
            }

            // 6. Arid Dry Lands (South-West Sun-baked Scrub). Was a solid 140x145m block (~8% of
            // the map, one single huge patch) - shrunk to a smaller corner and noise-gated so only
            // part of that corner is actually arid, breaking it into smaller patches instead of
            // one big chunk.
            if (worldX < 70f && worldZ < 75f)
            {
                float aridNoise = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.03f, 2, 0.5f, worldSeed + 888);
                if (aridNoise > 0.45f) return GetBiomeById("biome_dry_lands");
            }

            // 7. Amorphous Regional Forest & Meadow Blobs
            // Two continuous domain-warped orthogonal noise fields partition the remaining landscape into organic flowing blobs
            float rNoise1 = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0275f, 3, 0.5f, worldSeed + 101);
            float rNoise2 = BiomeNoise.FractalNoise2D(worldX, worldZ, 0.0275f, 3, 0.5f, worldSeed + 202);

            // Grass/meadow is the default open-country biome and should far outnumber forest -
            // forest only claims the tails of the noise range instead of most of it. FractalNoise2D
            // (3 octaves, persistence 0.5) rarely swings past roughly 0.1/0.9 in practice, so 0.85/
            // 0.15 thresholds were essentially unreachable and forest almost never spawned; 0.60/0.40
            // is comfortably inside the noise's real range (~76% grass, ~24% forest).
            if (rNoise1 > 0.60f)
            {
                if (rNoise2 > 0.66f) return GetBiomeById("biome_maple_forest");   // Vibrant Autumn Amber
                if (rNoise2 > 0.33f) return GetBiomeById("biome_mixed_forest");   // Biodiverse conifer/deciduous mix
                return GetBiomeById("biome_birch_forest");                       // Luminous Yellow-Green
            }
            else if (rNoise1 < 0.40f)
            {
                if (rNoise2 > 0.66f) return GetBiomeById("biome_oak_forest");     // Deep Canopy Hardwood
                if (rNoise2 > 0.33f) return GetBiomeById("biome_mixed_forest");   // Biodiverse conifer/deciduous mix
                return GetBiomeById("biome_poplar_forest");                      // Fresh Spring Green
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

            // One texel per metre so the biome map's texel grid lines up exactly with the
            // shader's 1m world-space grid overlay (a mismatched resolution here caused a
            // moire beat pattern between the two grids).
            int mapRes = Mathf.RoundToInt(terrainSizeX);
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

            // 2. Bake organic Biome Control Map.
            // RGB = the biome's actual color_hex tint, sampled BILINEARLY by the shader so
            // adjacent biomes blend smoothly at their border instead of stair-stepping at the
            // texel grid. A = ShaderMode [16-bucket full range], sampled with POINT filtering
            // so the shader can still hard-gate patterned biomes (water/lawn/farmland/wetland)
            // without inventing in-between mode ids.
            for (int py = 0; py < mapRes; py++)
            {
                for (int px = 0; px < mapRes; px++)
                {
                    // Divide by mapRes (not mapRes - 1): with mapRes == terrainSizeX this makes
                    // each texel exactly 1m wide, so texel boundaries land exactly on the
                    // shader's integer-metre grid lines instead of drifting away from them
                    // further from the origin.
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
                        tint = new Color(0.518f, 0.800f, 0.086f); // Meadow fallback
                    }

                    // Encode mode (0..15) across full range in distinct 1/16 buckets immune to gamma distortion
                    float a = (modeInt + 0.5f) / 16.0f;

                    mapPixels[py * mapRes + px] = new Color(tint.r, tint.g, tint.b, a);
                }
            }

            // Widen biome borders beyond the single-texel bilinear blend the shader already does,
            // by box-blurring the RGB tint (mode stays in A, untouched, so patterned biome gating
            // stays crisp). Separable pass: horizontal then vertical.
            const int blurRadius = 3;
            Color[] blurredH = new Color[mapRes * mapRes];
            for (int py = 0; py < mapRes; py++)
            {
                for (int px = 0; px < mapRes; px++)
                {
                    float r = 0f, g = 0f, b = 0f;
                    int count = 0;
                    for (int k = -blurRadius; k <= blurRadius; k++)
                    {
                        int sx = Mathf.Clamp(px + k, 0, mapRes - 1);
                        Color c = mapPixels[py * mapRes + sx];
                        r += c.r; g += c.g; b += c.b; count++;
                    }
                    Color orig = mapPixels[py * mapRes + px];
                    blurredH[py * mapRes + px] = new Color(r / count, g / count, b / count, orig.a);
                }
            }
            for (int px = 0; px < mapRes; px++)
            {
                for (int py = 0; py < mapRes; py++)
                {
                    float r = 0f, g = 0f, b = 0f;
                    int count = 0;
                    for (int k = -blurRadius; k <= blurRadius; k++)
                    {
                        int sy = Mathf.Clamp(py + k, 0, mapRes - 1);
                        Color c = blurredH[sy * mapRes + px];
                        r += c.r; g += c.g; b += c.b; count++;
                    }
                    Color orig = mapPixels[py * mapRes + px];
                    mapPixels[py * mapRes + px] = new Color(r / count, g / count, b / count, orig.a);
                }
            }

            bakedBiomeMap.SetPixels(mapPixels);
            bakedBiomeMap.Apply();

            // Pass baked biome map and 500m world bounds to the procedural terrain material
            if (targetTerrain.materialTemplate != null)
            {
                targetTerrain.materialTemplate.SetTexture("_BiomeMap", bakedBiomeMap);
                targetTerrain.materialTemplate.SetVector("_TerrainBounds", new Vector4(terrainSizeX, terrainSizeZ, terrainHeight, 0f));
                targetTerrain.materialTemplate.SetFloat("_HasIsland", PondHasIsland ? 1f : 0f);
                targetTerrain.materialTemplate.SetFloat("_HasBranch", RiverHasBranch ? 1f : 0f);
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
