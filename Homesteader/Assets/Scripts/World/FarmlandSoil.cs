using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Ground the player has turned into farmland with a hoe (see <see cref="Tiller"/>). It is kept as grid squares (the planting grid), painted into the
    /// terrain's baked biome map as the farmland ground (tilled furrows), and counted as farmland by <see cref="PlantingZone.BiomeAt"/>, so crops that need
    /// farmland can be planted in it. Saved as the list of squares (GameSave.tilledCells) and painted again after the world is generated on load.
    /// </summary>
    public static class FarmlandSoil
    {
        public const string BiomeId = "biome_farmland";
        private const int FarmlandMode = 4;       // the terrain shader's mode of biome_farmland (HomesteaderTerrainGenerator.BakeBiomeMap)
        private const float ModeCount = 18f;

        private static readonly HashSet<Vector2Int> Cells = new HashSet<Vector2Int>();

        public static void Clear() { Cells.Clear(); }

        private static float Size => PlantingValidator.GridSizeM;

        public static Vector2Int CellOf(Vector3 p) => new Vector2Int(Mathf.FloorToInt(p.x / Size), Mathf.FloorToInt(p.z / Size));

        public static bool Contains(Vector3 p) => Cells.Count > 0 && Cells.Contains(CellOf(p));

        /// <summary>The ground there is farmland already: tilled by the player, or generated as a farm field.</summary>
        public static bool IsFarmland(Vector3 p)
        {
            if (Contains(p)) return true;
            var gen = Object.FindAnyObjectByType<HomesteaderTerrainGenerator>();
            if (gen == null) return false;
            Vector3 o = gen.transform.position;
            BiomeData b = gen.EvaluateBiomeAt(p.x - o.x, p.z - o.z);
            return b != null && b.id == BiomeId;
        }

        /// <summary>Turns the grid square under the point into farmland. False when it already is.</summary>
        public static bool Till(Vector3 world)
        {
            Vector2Int cell = CellOf(world);
            if (!Cells.Add(cell)) return false;
            Paint(new[] { cell });
            return true;
        }

        public static List<Vector2Int> Saved() { return new List<Vector2Int>(Cells); }

        /// <summary>Tills the squares a save says were tilled (after the world is generated).</summary>
        public static void ApplySaved(List<Vector2Int> saved)
        {
            if (saved == null || saved.Count == 0) return;
            foreach (Vector2Int c in saved) Cells.Add(c);
            Paint(saved);
        }

        /// <summary>Paints the squares into the baked biome map: the farmland mode and colour in every pixel they cover.</summary>
        private static void Paint(IEnumerable<Vector2Int> cells)
        {
            var gen = Object.FindAnyObjectByType<HomesteaderTerrainGenerator>();
            Texture2D map = gen != null ? gen.GetBakedBiomeMap() : null;
            if (map == null) return;
            BiomeData biome = gen.GetBiomeById(BiomeId);
            Color tint = new Color(0.47f, 0.21f, 0.06f);
            if (biome != null && !string.IsNullOrEmpty(biome.color_hex)) ColorUtility.TryParseHtmlString(biome.color_hex, out tint);
            var colour = new Color(tint.r, tint.g, tint.b, (FarmlandMode + 0.5f) / ModeCount);
            Vector3 origin = gen.transform.position;
            int res = map.width;
            float size = Size;
            foreach (Vector2Int c in cells)
            {
                float x0 = c.x * size - origin.x, z0 = c.y * size - origin.z;
                int px0 = Mathf.Clamp(Mathf.FloorToInt(x0 / gen.terrainSizeX * res), 0, res - 1);
                int px1 = Mathf.Clamp(Mathf.CeilToInt((x0 + size) / gen.terrainSizeX * res) - 1, 0, res - 1);
                int py0 = Mathf.Clamp(Mathf.FloorToInt(z0 / gen.terrainSizeZ * res), 0, res - 1);
                int py1 = Mathf.Clamp(Mathf.CeilToInt((z0 + size) / gen.terrainSizeZ * res) - 1, 0, res - 1);
                for (int py = py0; py <= py1; py++)
                    for (int px = px0; px <= px1; px++) map.SetPixel(px, py, colour);
            }
            map.Apply();
        }
    }
}
