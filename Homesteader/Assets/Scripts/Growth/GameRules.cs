using System;
using System.Collections.Generic;
using System.IO;
using Homesteader.Modding;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Game rules as MOD DATA (mod content type "gamerules", file gamerules.json). The values here
    /// are only the built-in defaults; a mod overrides individual keys, so with no gamerules mod
    /// the game behaves exactly as these defaults say. ModLoader is the only writer.
    /// See assets/_schemas/gamerules.schema.json.
    /// </summary>
    public static class GameRules
    {
        public sealed class PlantingRules
        {
            public float GridSizeM = 1f;
            public int ReachCells = 1;
            public float MaxSlopeDeg = 25f;
            public float CropSpacingM = 0.5f;
            public float TreeSpacingM = 2f;
            public HashSet<string> WaterBiomes = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
                { "biome_pond", "biome_river", "biome_lake" };
        }

        public static PlantingRules Planting { get; private set; } = new PlantingRules();

        /// <summary>Placing structures and props from the toolbar (PlacementController).</summary>
        public sealed class PlacementRules
        {
            public int ReachCells = 3;              // squares around the player a thing can be placed
            public float RotateStepDeg = 12.5f;     // one press of R
            public HashSet<string> Categories = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
                { "structures", "electricity", "water", "waste", "internet" };
        }

        public static PlacementRules Placement { get; private set; } = new PlacementRules();

        /// <summary>One graphics quality preset (see GraphicsOptions). It only changes how the world is drawn, never what is in it.</summary>
        public sealed class GraphicsPreset
        {
            public string Id = "high";
            public string Name = "High";
            public int MinVramMb = 0;          // what "Auto" needs to pick this preset: graphics memory ...
            public int MinCores = 0;           // ... and CPU cores
            public float ShadowDistance = 200f;   // metres; 0 = no shadows
            public int ShadowResolution = 4096;   // the sun's shadow map
            public int ShadowCascades = 2;
            public float RenderScale = 1f;
            public string Antialiasing = "msaa2"; // off, fxaa, smaa, msaa2, msaa4, msaa8
            public float SmallPlantRange = 46f;   // metres from the middle of the view that flowers, tufts and bushes are drawn
            public bool TerrainBlend = true;      // the soft biome boundaries (off = hard edges, the cheapest)
            public bool WaterReflections = true;  // the sky reflected in water (off = just the sun's glint)
            public int MaxFps = 0;                // with V-Sync off; 0 = no cap
        }

        /// <summary>The graphics presets: the default choice and the list, lowest quality first.</summary>
        public sealed class GraphicsRules
        {
            public string DefaultPreset = "auto";
            public List<GraphicsPreset> Presets = new List<GraphicsPreset> { new GraphicsPreset() };   // the built-in fallback; gamerules.json supplies the real list
        }

        public static GraphicsRules Graphics { get; private set; } = new GraphicsRules();

        /// <summary>
        /// The starter zone: the land tile the player begins in (centre of the map by default). World generation
        /// enforces these, whatever the seed: a square of ground around the spawn point is some form of grass, there is
        /// at least one water feature in the zone, and water never covers more than a set fraction of it. The rest of
        /// the zone is ordinary biome generation.
        /// </summary>
        public sealed class StarterZoneRules
        {
            public bool Enabled = true;
            public int TileX = Homesteader.Land.LandOwnershipSystem.StarterX;
            public int TileZ = Homesteader.Land.LandOwnershipSystem.StarterZ;
            public float GrassAreaM = 16f;   // side of the square around the spawn point that must be grass
            public List<string> LandBiomes = new List<string> { "biome_grass_plains", "biome_meadow" };   // maintained grass is player-made only
            public int MinWaterFeatures = 1;
            public float MaxWaterFraction = 0.15f;   // of the whole zone's area
        }

        public static StarterZoneRules StarterZone { get; private set; } = new StarterZoneRules();

        /// <summary>The road from a map edge to the starter grass area: generated with the world, soft and meandering.</summary>
        public sealed class StarterRoadRules
        {
            public bool Enabled = true;
            public float WidthM = 3.4f;     // dirt / gravel surface, edge to edge
            public float MeanderM = 4.5f;   // how far the road wanders sideways (on top of routing around water and hills)
        }

        public static StarterRoadRules StarterRoad { get; private set; } = new StarterRoadRules();

        /// <summary>How many squares away from the player's own square a plant can be harvested.</summary>
        public static int HarvestReachCells { get; private set; } = 1;

        // Zone objects this class built, keyed by zone id, so a later mod's zone can replace them
        // and a reload can remove them.
        private static readonly Dictionary<string, GameObject> zoneObjects =
            new Dictionary<string, GameObject>(StringComparer.OrdinalIgnoreCase);

        /// <summary>Back to the built-in defaults and removes every zone built from mod data.</summary>
        public static void Clear()
        {
            Planting = new PlantingRules();
            Placement = new PlacementRules();
            Graphics = new GraphicsRules();
            StarterZone = new StarterZoneRules();
            StarterRoad = new StarterRoadRules();
            HarvestReachCells = 1;
            foreach (GameObject go in zoneObjects.Values)
                if (go != null) UnityEngine.Object.Destroy(go);
            zoneObjects.Clear();
        }

        /// <summary>
        /// Merges one mod's gamerules.json. Only keys the file actually contains change anything,
        /// so a later mod overrides individual values of an earlier one.
        /// </summary>
        public static void Apply(ModInfo mod, ModJsonValue root, Action<string> warn = null)
        {
            ModJsonValue p = root.Get("planting");
            if (p.IsObject)
            {
                if (p.Has("grid_size_m")) Planting.GridSizeM = Mathf.Max(0.1f, p.Get("grid_size_m").AsFloat(Planting.GridSizeM));
                if (p.Has("reach_cells")) Planting.ReachCells = Mathf.Max(0, p.Get("reach_cells").AsInt(Planting.ReachCells));
                if (p.Has("max_slope_deg")) Planting.MaxSlopeDeg = Mathf.Clamp(p.Get("max_slope_deg").AsFloat(Planting.MaxSlopeDeg), 0f, 90f);
                if (p.Has("crop_spacing_m")) Planting.CropSpacingM = Mathf.Max(0f, p.Get("crop_spacing_m").AsFloat(Planting.CropSpacingM));
                if (p.Has("tree_spacing_m")) Planting.TreeSpacingM = Mathf.Max(0f, p.Get("tree_spacing_m").AsFloat(Planting.TreeSpacingM));
                if (p.Has("water_biomes"))
                    Planting.WaterBiomes = new HashSet<string>(p.Get("water_biomes").AsStringList(), StringComparer.OrdinalIgnoreCase);
            }

            ModJsonValue pl = root.Get("placement");
            if (pl.IsObject)
            {
                if (pl.Has("reach_cells")) Placement.ReachCells = Mathf.Max(0, pl.Get("reach_cells").AsInt(Placement.ReachCells));
                if (pl.Has("rotate_step_deg")) Placement.RotateStepDeg = Mathf.Clamp(pl.Get("rotate_step_deg").AsFloat(Placement.RotateStepDeg), 0.5f, 180f);
                if (pl.Has("categories"))
                    Placement.Categories = new HashSet<string>(pl.Get("categories").AsStringList(), StringComparer.OrdinalIgnoreCase);
            }

            ModJsonValue gfx = root.Get("graphics");
            if (gfx.IsObject)
            {
                if (gfx.Has("default_preset")) Graphics.DefaultPreset = gfx.Get("default_preset").AsString(Graphics.DefaultPreset);
                if (gfx.Has("presets"))
                {
                    var list = new List<GraphicsPreset>();
                    foreach (ModJsonValue v in gfx.Get("presets").Items)
                    {
                        string id = v.Get("id").AsString();
                        if (string.IsNullOrEmpty(id)) continue;
                        var d = new GraphicsPreset();
                        list.Add(new GraphicsPreset
                        {
                            Id = id,
                            Name = v.Get("name").AsString(id),
                            MinVramMb = Mathf.Max(0, v.Get("min_vram_mb").AsInt(d.MinVramMb)),
                            MinCores = Mathf.Max(0, v.Get("min_cores").AsInt(d.MinCores)),
                            ShadowDistance = Mathf.Max(0f, v.Get("shadow_distance").AsFloat(d.ShadowDistance)),
                            ShadowResolution = Mathf.Clamp(v.Get("shadow_resolution").AsInt(d.ShadowResolution), 256, 8192),
                            ShadowCascades = Mathf.Clamp(v.Get("shadow_cascades").AsInt(d.ShadowCascades), 1, 4),
                            RenderScale = Mathf.Clamp(v.Get("render_scale").AsFloat(d.RenderScale), 0.5f, 1.5f),
                            Antialiasing = v.Has("antialiasing") ? v.Get("antialiasing").AsString(d.Antialiasing) : (v.Has("msaa") ? (v.Get("msaa").AsInt(1) <= 1 ? "off" : "msaa" + v.Get("msaa").AsInt(2)) : d.Antialiasing),
                            SmallPlantRange = Mathf.Max(10f, v.Get("small_plant_range").AsFloat(d.SmallPlantRange)),
                            TerrainBlend = v.Get("terrain_blend").AsBool(d.TerrainBlend),
                            WaterReflections = v.Get("water_reflections").AsBool(d.WaterReflections),
                            MaxFps = Mathf.Max(0, v.Get("max_fps").AsInt(d.MaxFps)),
                        });
                    }
                    if (list.Count > 0) Graphics.Presets = list;
                }
            }

            ModJsonValue sz = root.Get("starter_zone");
            if (sz.IsObject)
            {
                if (sz.Has("enabled")) StarterZone.Enabled = sz.Get("enabled").AsBool(StarterZone.Enabled);
                if (sz.Has("tile"))
                {
                    ModJsonValue tile = sz.Get("tile");
                    if (tile.Count >= 2)
                    {
                        StarterZone.TileX = Mathf.Clamp(tile.ArrayValue[0].AsInt(StarterZone.TileX), 0, Homesteader.Land.LandOwnershipSystem.GridSize - 1);
                        StarterZone.TileZ = Mathf.Clamp(tile.ArrayValue[1].AsInt(StarterZone.TileZ), 0, Homesteader.Land.LandOwnershipSystem.GridSize - 1);
                    }
                }
                if (sz.Has("grass_area_m")) StarterZone.GrassAreaM = Mathf.Max(0f, sz.Get("grass_area_m").AsFloat(StarterZone.GrassAreaM));
                if (sz.Has("land_biomes"))
                {
                    var list = new List<string>(sz.Get("land_biomes").AsStringList());
                    if (list.Count > 0) StarterZone.LandBiomes = list;
                }
                if (sz.Has("min_water_features")) StarterZone.MinWaterFeatures = Mathf.Max(0, sz.Get("min_water_features").AsInt(StarterZone.MinWaterFeatures));
                if (sz.Has("max_water_fraction")) StarterZone.MaxWaterFraction = Mathf.Clamp(sz.Get("max_water_fraction").AsFloat(StarterZone.MaxWaterFraction), 0.01f, 1f);
            }

            ModJsonValue sr = root.Get("starter_road");
            if (sr.IsObject)
            {
                if (sr.Has("enabled")) StarterRoad.Enabled = sr.Get("enabled").AsBool(StarterRoad.Enabled);
                if (sr.Has("width_m")) StarterRoad.WidthM = Mathf.Clamp(sr.Get("width_m").AsFloat(StarterRoad.WidthM), 1.5f, 8f);
                if (sr.Has("meander_m")) StarterRoad.MeanderM = Mathf.Clamp(sr.Get("meander_m").AsFloat(StarterRoad.MeanderM), 0f, 15f);
            }

            ModJsonValue h = root.Get("harvest");
            if (h.IsObject && h.Has("reach_cells"))
                HarvestReachCells = Mathf.Max(0, h.Get("reach_cells").AsInt(HarvestReachCells));

            foreach (ModJsonValue z in root.Get("zones").Items)
                BuildZone(mod, z, warn);
        }

        // ------------------------------------------------------------------ zones

        /// <summary>
        /// Builds a flat, textured, walk-through quad for a zone and gives it a PlantingZone so the
        /// planting rules see it as its biome. A later zone with the same id replaces the earlier one.
        /// </summary>
        private static void BuildZone(ModInfo mod, ModJsonValue z, Action<string> warn)
        {
            string id = z.Get("id").AsString();
            string biome = z.Get("biome").AsString();
            ModJsonValue center = z.Get("center");
            ModJsonValue size = z.Get("size");
            if (string.IsNullOrEmpty(id) || string.IsNullOrEmpty(biome) || center.Count < 2 || size.Count < 2)
            {
                warn?.Invoke("A zone needs id, biome, center [x, z] and size [width, depth]; skipped.");
                return;
            }

            float cx = center.ArrayValue[0].AsFloat(), cz = center.ArrayValue[1].AsFloat();
            float w = Mathf.Max(0.1f, size.ArrayValue[0].AsFloat()), d = Mathf.Max(0.1f, size.ArrayValue[1].AsFloat());
            float tile = Mathf.Max(0.1f, z.Get("tile_m").AsFloat(1f));
            float lift = z.Get("height_offset_m").AsFloat(0.005f);

            if (zoneObjects.TryGetValue(id, out GameObject old) && old != null)
                UnityEngine.Object.Destroy(old);

            // Sit on whatever ground is at the centre (terrain or flat plane); y = 0 if there is none.
            float groundY = Homesteader.Generation.TerrainHeightDetector.GetGroundY(cx, cz);

            var go = GameObject.CreatePrimitive(PrimitiveType.Plane);   // 10 x 10 m at scale 1
            go.name = $"Zone_{id}";
            go.transform.position = new Vector3(cx, groundY + lift, cz);
            go.transform.localScale = new Vector3(w / 10f, 1f, d / 10f);
            var col = go.GetComponent<Collider>();
            if (col != null) UnityEngine.Object.Destroy(col);   // visual only: clicks pass through to the ground

            Material mat = BuildZoneMaterial(mod, z.Get("texture").AsString(), w / tile, d / tile, warn);
            if (mat != null) go.GetComponent<MeshRenderer>().sharedMaterial = mat;

            var zone = go.AddComponent<PlantingZone>();
            zone.biomeId = biome;
            zone.size = new Vector2(w, d);

            zoneObjects[id] = go;
        }

        private static Material BuildZoneMaterial(ModInfo mod, string texturePath, float repeatX, float repeatZ, Action<string> warn)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            if (shader == null) return null;
            var mat = new Material(shader);
            if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", 0f);
            if (mat.HasProperty("_Metallic")) mat.SetFloat("_Metallic", 0f);

            if (string.IsNullOrEmpty(texturePath)) return mat;

            string path = Path.Combine(mod.RootPath, texturePath.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path))
            {
                warn?.Invoke($"Zone texture '{texturePath}' not found in the mod.");
                return mat;
            }

            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear };
            if (!tex.LoadImage(File.ReadAllBytes(path)))
            {
                warn?.Invoke($"Zone texture '{texturePath}' could not be read as an image.");
                return mat;
            }

            string prop = mat.HasProperty("_BaseMap") ? "_BaseMap" : "_MainTex";
            mat.SetTexture(prop, tex);
            mat.SetTextureScale(prop, new Vector2(repeatX, repeatZ));
            return mat;
        }
    }
}
