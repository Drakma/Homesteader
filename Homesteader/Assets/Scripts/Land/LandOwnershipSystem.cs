using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Land
{
    /// <summary>
    /// Manages a 5×5 grid of 100m×100m land tiles over the 500m×500m terrain.
    /// The centre tile (2,2) is the starter zone — owned by default.
    /// Players purchase adjacent tiles to expand their accessible area.
    /// Ownership persists via PlayerPrefs.
    /// </summary>
    public static class LandOwnershipSystem
    {
        public const int GridSize = 5;
        public const float TileSize = 100f;
        public const float MapSize = GridSize * TileSize; // 500m

        // Centre tile = starter zone
        public const int StarterX = 2;
        public const int StarterZ = 2;

        // Price per tile
        public const float TilePrice = 5000f;

        private static bool[,] _owned = new bool[GridSize, GridSize];
        private static bool _initialized = false;

        /// <summary>Called once on game start to load saved ownership or initialise defaults.</summary>
        public static void Initialize()
        {
            if (_initialized) return;
            _initialized = true;
            LoadOwnership();
        }

        /// <summary>Resets to defaults (only starter tile owned). Called on New Game.</summary>
        public static void ResetToDefaults()
        {
            _owned = new bool[GridSize, GridSize];
            _owned[StarterX, StarterZ] = true;
            SaveOwnership();
        }

        public static bool IsOwned(int tx, int tz)
        {
            if (tx < 0 || tx >= GridSize || tz < 0 || tz >= GridSize) return false;
            return _owned[tx, tz];
        }

        public static bool IsOwned(float worldX, float worldZ)
        {
            int tx, tz;
            WorldToTile(worldX, worldZ, out tx, out tz);
            return IsOwned(tx, tz);
        }

        /// <summary>Converts world coordinates to tile indices.</summary>
        public static void WorldToTile(float worldX, float worldZ, out int tx, out int tz)
        {
            tx = Mathf.FloorToInt(worldX / TileSize);
            tz = Mathf.FloorToInt(worldZ / TileSize);
        }

        /// <summary>Converts tile indices to the centre of the tile in world coordinates.</summary>
        public static Vector2 TileCenter(int tx, int tz)
        {
            return new Vector2(
                tx * TileSize + TileSize * 0.5f,
                tz * TileSize + TileSize * 0.5f
            );
        }

        /// <summary>Returns the tile bounds in world coordinates [minX, maxX, minZ, maxZ].</summary>
        public static void TileBounds(int tx, int tz, out float minX, out float maxX, out float minZ, out float maxZ)
        {
            minX = tx * TileSize;
            maxX = minX + TileSize;
            minZ = tz * TileSize;
            maxZ = minZ + TileSize;
        }

        /// <summary>
        /// Attempts to purchase a tile. Returns true if the purchase succeeded.
        /// A tile can only be purchased if it is adjacent to an already-owned tile.
        /// </summary>
        public static bool TryPurchaseTile(int tx, int tz)
        {
            if (tx < 0 || tx >= GridSize || tz < 0 || tz >= GridSize) return false;
            if (_owned[tx, tz]) return false;
            if (!IsAdjacentToOwned(tx, tz)) return false;

            if (!HudState.Active.SpendMoney(TilePrice)) return false;

            _owned[tx, tz] = true;
            SaveOwnership();
            return true;
        }

        /// <summary>Checks if a tile is orthogonally adjacent to any owned tile.</summary>
        public static bool IsAdjacentToOwned(int tx, int tz)
        {
            if (IsOwned(tx - 1, tz)) return true;
            if (IsOwned(tx + 1, tz)) return true;
            if (IsOwned(tx, tz - 1)) return true;
            if (IsOwned(tx, tz + 1)) return true;
            return false;
        }

        /// <summary>Returns all tiles that can currently be purchased (adjacent to owned, not yet owned).</summary>
        public static List<(int tx, int tz)> GetPurchasableTiles()
        {
            var result = new List<(int tx, int tz)>();
            for (int x = 0; x < GridSize; x++)
            {
                for (int z = 0; z < GridSize; z++)
                {
                    if (!_owned[x, z] && IsAdjacentToOwned(x, z))
                        result.Add((x, z));
                }
            }
            return result;
        }

        /// <summary>Returns all owned tile coordinates.</summary>
        public static List<(int tx, int tz)> GetOwnedTiles()
        {
            var result = new List<(int tx, int tz)>();
            for (int x = 0; x < GridSize; x++)
                for (int z = 0; z < GridSize; z++)
                    if (_owned[x, z]) result.Add((x, z));
            return result;
        }

        // ── Persistence ──────────────────────────────────────────────

        private const string PrefKey = "Homesteader.Land.";

        private static void SaveOwnership()
        {
            for (int x = 0; x < GridSize; x++)
                for (int z = 0; z < GridSize; z++)
                    PlayerPrefs.SetInt($"{PrefKey}{x}_{z}", _owned[x, z] ? 1 : 0);
            PlayerPrefs.Save();
        }

        private static void LoadOwnership()
        {
            // Check if any key exists; if not, use defaults
            bool anyKey = PlayerPrefs.HasKey($"{PrefKey}{StarterX}_{StarterZ}");
            if (!anyKey)
            {
                ResetToDefaults();
                return;
            }

            for (int x = 0; x < GridSize; x++)
                for (int z = 0; z < GridSize; z++)
                    _owned[x, z] = PlayerPrefs.GetInt($"{PrefKey}{x}_{z}", 0) == 1;
        }

        // ── Border edges ─────────────────────────────────────────────

        /// <summary>
        /// Represents a border edge between an owned and unowned tile.
        /// These are the visible yellow border lines.
        /// </summary>
        public struct BorderEdge
        {
            public float x1, z1, x2, z2;
        }

        /// <summary>
        /// Computes the border edges around owned tiles, removing internal edges
        /// between two owned tiles (so contiguous owned areas show a single outline).
        /// </summary>
        public static List<BorderEdge> ComputeBorderEdges()
        {
            var edges = new List<BorderEdge>();

            for (int x = 0; x < GridSize; x++)
            {
                for (int z = 0; z < GridSize; z++)
                {
                    if (!_owned[x, z]) continue;

                    TileBounds(x, z, out float minX, out float maxX, out float minZ, out float maxZ);

                    // North edge (z = maxZ) — show if neighbour to the north is not owned
                    if (!IsOwned(x, z + 1))
                        edges.Add(new BorderEdge { x1 = minX, z1 = maxZ, x2 = maxX, z2 = maxZ });

                    // South edge (z = minZ) — show if neighbour to the south is not owned
                    if (!IsOwned(x, z - 1))
                        edges.Add(new BorderEdge { x1 = minX, z1 = minZ, x2 = maxX, z2 = minZ });

                    // East edge (x = maxX) — show if neighbour to the east is not owned
                    if (!IsOwned(x + 1, z))
                        edges.Add(new BorderEdge { x1 = maxX, z1 = minZ, x2 = maxX, z2 = maxZ });

                    // West edge (x = minX) — show if neighbour to the west is not owned
                    if (!IsOwned(x - 1, z))
                        edges.Add(new BorderEdge { x1 = minX, z1 = minZ, x2 = minX, z2 = maxZ });
                }
            }

            return edges;
        }
    }
}
