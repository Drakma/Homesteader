using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Ground the player has turned into farmland with a hoe (see <see cref="Tiller"/>). It is kept as grid squares (the planting grid), painted into the
    /// terrain's baked biome map as the farmland ground (two tilled rows to a square), and counted as farmland by <see cref="PlantingZone.BiomeAt"/>, so crops
    /// that need farmland can be planted in it. Saved as the list of squares (GameSave.tilledCells, plus tilledAlongZ for those whose rows run along Z) and
    /// painted again after the world is generated on load.
    ///
    /// The rows keep one direction across a patch: the first square takes the direction the player was working in (the rows run away from them), and every
    /// square tilled next to tilled ground takes that ground's direction, so the furrows run on unbroken from square to square.
    /// </summary>
    public static class FarmlandSoil
    {
        public const string BiomeId = "biome_farmland";
        private const int FarmlandMode = 4;       // the terrain shader's mode of biome_farmland (HomesteaderTerrainGenerator.BakeBiomeMap)
        private const float ModeCount = 18f;

        private static readonly Dictionary<Vector2Int, bool> Cells = new Dictionary<Vector2Int, bool>();   // square -> its rows run along Z

        public static void Clear() { Cells.Clear(); }

        private static float Size => PlantingValidator.GridSizeM;

        public static Vector2Int CellOf(Vector3 p) => new Vector2Int(Mathf.FloorToInt(p.x / Size), Mathf.FloorToInt(p.z / Size));

        public static bool Contains(Vector3 p) => Cells.Count > 0 && Cells.ContainsKey(CellOf(p));

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

        /// <summary>Turns the grid square under the point into farmland. <paramref name="from"/> is where the player stands (the first square's rows run away
        /// from them); a square next to tilled ground ignores it and continues that ground's rows. False when it already is farmland.</summary>
        public static bool Till(Vector3 world, Vector3? from = null)
        {
            Vector2Int cell = CellOf(world);
            if (Cells.ContainsKey(cell)) return false;
            bool alongZ = false, decided = false;
            foreach (Vector2Int n in new[] { cell + Vector2Int.right, cell + Vector2Int.left, cell + Vector2Int.up, cell + Vector2Int.down })
                if (Cells.TryGetValue(n, out bool z)) { alongZ = z; decided = true; break; }
            if (!decided && from.HasValue)
            {
                Vector3 d = new Vector3(world.x - from.Value.x, 0f, world.z - from.Value.z);
                alongZ = Mathf.Abs(d.z) >= Mathf.Abs(d.x);   // working north or south: the rows run north-south
            }
            Cells[cell] = alongZ;
            Paint(new[] { cell });
            return true;
        }

        public static List<Vector2Int> Saved() { return new List<Vector2Int>(Cells.Keys); }

        /// <summary>The squares whose rows run along Z (every other tilled square runs along X).</summary>
        public static List<Vector2Int> SavedAlongZ()
        {
            var list = new List<Vector2Int>();
            foreach (KeyValuePair<Vector2Int, bool> kv in Cells) if (kv.Value) list.Add(kv.Key);
            return list;
        }

        /// <summary>Tills the squares a save says were tilled (after the world is generated).</summary>
        public static void ApplySaved(List<Vector2Int> saved, List<Vector2Int> alongZ = null)
        {
            if (saved == null || saved.Count == 0) return;
            var z = alongZ != null ? new HashSet<Vector2Int>(alongZ) : new HashSet<Vector2Int>();
            foreach (Vector2Int c in saved) Cells[c] = z.Contains(c);
            Paint(saved);
        }

        /// <summary>Paints the squares into the baked biome map: the farmland mode in every pixel they cover, and the row direction in the red channel (1 = along Z).</summary>
        private static void Paint(IEnumerable<Vector2Int> cells)
        {
            var gen = Object.FindAnyObjectByType<HomesteaderTerrainGenerator>();
            Texture2D map = gen != null ? gen.GetBakedBiomeMap() : null;
            if (map == null) return;
            Vector3 origin = gen.transform.position;
            int res = map.width;
            float size = Size;
            float minX = float.MaxValue, minZ = float.MaxValue, maxX = float.MinValue, maxZ = float.MinValue;
            foreach (Vector2Int c in cells)
            {
                minX = Mathf.Min(minX, c.x * size - origin.x); maxX = Mathf.Max(maxX, (c.x + 1) * size - origin.x);
                minZ = Mathf.Min(minZ, c.y * size - origin.z); maxZ = Mathf.Max(maxZ, (c.y + 1) * size - origin.z);
                Cells.TryGetValue(c, out bool alongZ);
                var colour = new Color(alongZ ? 1f : 0f, 0.21f, 0.06f, (FarmlandMode + 0.5f) / ModeCount);
                float x0 = c.x * size - origin.x, z0 = c.y * size - origin.z;
                int px0 = Mathf.Clamp(Mathf.FloorToInt(x0 / gen.terrainSizeX * res), 0, res - 1);
                int px1 = Mathf.Clamp(Mathf.CeilToInt((x0 + size) / gen.terrainSizeX * res) - 1, 0, res - 1);
                int py0 = Mathf.Clamp(Mathf.FloorToInt(z0 / gen.terrainSizeZ * res), 0, res - 1);
                int py1 = Mathf.Clamp(Mathf.CeilToInt((z0 + size) / gen.terrainSizeZ * res) - 1, 0, res - 1);
                for (int py = py0; py <= py1; py++)
                    for (int px = px0; px <= px1; px++) map.SetPixel(px, py, colour);
            }
            map.Apply();
            // The ground colour is rendered once into a texture (TerrainGroundBake): draw it again exactly where the farmland went in.
            var terrain = gen.GetComponent<Terrain>();
            if (terrain != null && terrain.materialTemplate != null && minX <= maxX)
                TerrainGroundBake.Rebake(terrain.materialTemplate, minX / gen.terrainSizeX, minZ / gen.terrainSizeZ, maxX / gen.terrainSizeX, maxZ / gen.terrainSizeZ);
        }
    }
}
