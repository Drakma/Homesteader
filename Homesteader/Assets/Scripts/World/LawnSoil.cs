using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Ground the player has mown into a fresh-cut lawn with a push mower (see <see cref="PushMower"/>). Like <see cref="FarmlandSoil"/> it is kept as grid squares (the planting grid), painted into the
    /// terrain's baked biome map as the maintained-lawn ground (mode 5: bands one mower deck wide, light and dark), and counted as that biome by <see cref="PlantingZone.BiomeAt"/>. The grass tufts and
    /// flowers on a mown square go; trees, bushes and rocks stay. Saved as the list of squares (GameSave.mowedCells, plus mowedAlongZ for those whose stripes run along Z) and painted again after the
    /// world is generated on load. docs/MOWING.md.
    ///
    /// The stripes keep one direction across a lawn: the first square takes the direction the mower was travelling (the stripes run the way it went), and every square mown next to lawn takes that lawn's
    /// direction, so the bands run on unbroken from square to square.
    /// </summary>
    public static class LawnSoil
    {
        public const string BiomeId = "biome_maintained_grass";
        private const int LawnMode = 5;           // the terrain shader's mode of biome_maintained_grass (HomesteaderTerrainGenerator.BakeBiomeMap)
        private const float ModeCount = 18f;

        private static readonly Dictionary<Vector2Int, bool> Cells = new Dictionary<Vector2Int, bool>();   // square -> its stripes run along Z

        public static void Clear() { Cells.Clear(); }

        private static float Size => PlantingValidator.GridSizeM;

        public static Vector2Int CellOf(Vector3 p) => new Vector2Int(Mathf.FloorToInt(p.x / Size), Mathf.FloorToInt(p.z / Size));

        public static bool Contains(Vector3 p) => Cells.Count > 0 && Cells.ContainsKey(CellOf(p));

        /// <summary>True when a mower can cut the grass there: open ground, not water, not a road, not farmland, not lawn already.</summary>
        public static bool Mowable(Vector3 p)
        {
            if (Contains(p) || FarmlandSoil.IsFarmland(p)) return false;
            var gen = Object.FindAnyObjectByType<HomesteaderTerrainGenerator>();
            if (gen == null) return false;
            Vector3 o = gen.transform.position;
            float lx = p.x - o.x, lz = p.z - o.z;
            return !gen.IsWaterAt(lx, lz) && !gen.IsNearRoad(lx, lz, 0.5f);
        }

        /// <summary>
        /// Mows the squares under these points (a mower's deck sampled along its path) as the mower travels in <paramref name="travel"/>. Returns how many squares are new lawn. Painted and baked once for all of
        /// them, so a deck crossing several squares at once costs one bake.
        /// </summary>
        public static int Mow(List<Vector3> points, Vector3 travel)
        {
            var fresh = new List<Vector2Int>();
            foreach (Vector3 world in points)
            {
                Vector2Int cell = CellOf(world);
                if (Cells.ContainsKey(cell) || fresh.Contains(cell) || !Mowable(world)) continue;
                bool alongZ = false, decided = false;
                foreach (Vector2Int n in new[] { cell + Vector2Int.right, cell + Vector2Int.left, cell + Vector2Int.up, cell + Vector2Int.down })
                    if (Cells.TryGetValue(n, out bool z)) { alongZ = z; decided = true; break; }
                if (!decided) alongZ = Mathf.Abs(travel.z) >= Mathf.Abs(travel.x);   // travelling north or south: the stripes run north-south
                Cells[cell] = alongZ;
                fresh.Add(cell);
            }
            if (fresh.Count == 0) return 0;
            Paint(fresh);
            foreach (Vector2Int c in fresh) SiteClearing.ClearGround(c.x * Size, c.y * Size, (c.x + 1) * Size, (c.y + 1) * Size);   // the grass and flowers on it go
            return fresh.Count;
        }

        public static List<Vector2Int> Saved() { return new List<Vector2Int>(Cells.Keys); }

        /// <summary>The squares whose stripes run along Z (every other mown square runs along X).</summary>
        public static List<Vector2Int> SavedAlongZ()
        {
            var list = new List<Vector2Int>();
            foreach (KeyValuePair<Vector2Int, bool> kv in Cells) if (kv.Value) list.Add(kv.Key);
            return list;
        }

        /// <summary>Mows the squares a save says were mown (after the world is generated).</summary>
        public static void ApplySaved(List<Vector2Int> saved, List<Vector2Int> alongZ = null)
        {
            if (saved == null || saved.Count == 0) return;
            var z = alongZ != null ? new HashSet<Vector2Int>(alongZ) : new HashSet<Vector2Int>();
            foreach (Vector2Int c in saved) Cells[c] = z.Contains(c);
            Paint(saved);
            foreach (Vector2Int c in saved) SiteClearing.ClearGround(c.x * Size, c.y * Size, (c.x + 1) * Size, (c.y + 1) * Size);   // the world's cover grows back on every load
        }

        /// <summary>Paints the squares into the baked biome map: the lawn mode in every pixel they cover, and the stripe direction in the red channel (1 = along Z).</summary>
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
                var colour = new Color(alongZ ? 1f : 0f, 0.55f, 0.7f, (LawnMode + 0.5f) / ModeCount);   // (moisture and nutrients as the lawn biome has them)
                float x0 = c.x * size - origin.x, z0 = c.y * size - origin.z;
                int px0 = Mathf.Clamp(Mathf.FloorToInt(x0 / gen.terrainSizeX * res), 0, res - 1);
                int px1 = Mathf.Clamp(Mathf.CeilToInt((x0 + size) / gen.terrainSizeX * res) - 1, 0, res - 1);
                int py0 = Mathf.Clamp(Mathf.FloorToInt(z0 / gen.terrainSizeZ * res), 0, res - 1);
                int py1 = Mathf.Clamp(Mathf.CeilToInt((z0 + size) / gen.terrainSizeZ * res) - 1, 0, res - 1);
                for (int py = py0; py <= py1; py++)
                    for (int px = px0; px <= px1; px++) map.SetPixel(px, py, colour);
            }
            map.Apply();
            // The ground colour is rendered once into a texture (TerrainGroundBake): draw it again exactly where the lawn went in.
            var terrain = gen.GetComponent<Terrain>();
            if (terrain != null && terrain.materialTemplate != null && minX <= maxX)
                TerrainGroundBake.Rebake(terrain.materialTemplate, minX / gen.terrainSizeX, minZ / gen.terrainSizeZ, maxX / gen.terrainSizeX, maxZ / gen.terrainSizeZ);
        }
    }
}
