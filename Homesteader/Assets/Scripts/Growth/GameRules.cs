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
