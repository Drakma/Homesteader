using UnityEngine;

namespace Homesteader.Generation
{
    /// <summary>
    /// The generator's side of WorldSnapshot: capture what a generation produced, and generate from a snapshot instead of from the noise functions.
    /// The Unity random stream is still consumed exactly as before (the water features are generated and then replaced), so what the trees and
    /// rocks do afterwards is unchanged.
    /// </summary>
    public partial class HomesteaderTerrainGenerator
    {
        /// <summary>Set by the bootstrap before generating a world that is being continued; used once, then cleared.</summary>
        public WorldSnapshot PendingSnapshot;

        /// <summary>What the last generation produced (or restored). Null until a world has been generated.</summary>
        public WorldSnapshot LastGenerated { get; private set; }

        /// <summary>True when LastGenerated was freshly computed (not loaded): it still has to be written beside the save.</summary>
        public bool SnapshotDirty { get; private set; }

        public void MarkSnapshotSaved() { SnapshotDirty = false; }

        private WorldSnapshot _using;   // the snapshot this generation is restoring from, or null

        /// <summary>Starts a generation: picks the pending snapshot up when it fits this world.</summary>
        private void BeginSnapshotUse()
        {
            _using = null;
            WorldSnapshot s = PendingSnapshot;
            PendingSnapshot = null;
            if (s == null || terrainData == null) return;
            int mapRes = Mathf.RoundToInt(terrainSizeX);
            if (!s.Matches(worldSeed, terrainData.heightmapResolution, mapRes, terrainSizeX, terrainSizeZ, terrainHeight))
            {
                Debug.LogWarning("[TerrainGen] the saved world snapshot does not fit this world (seed or size differ); generating from the seed instead.");
                return;
            }
            _using = s;
            Debug.Log($"[TerrainGen] restoring the saved world (seed {worldSeed}) from its snapshot instead of regenerating the ground.");
        }

        /// <summary>After the water features are generated: swap in the saved ones.</summary>
        private void RestoreFeaturesFromSnapshot()
        {
            if (_using == null || _using.Rivers.Count == 0) return;
            mainRiver = RiverFrom(_using.Rivers[0]);
            var branches = new RiverFeature[_using.Rivers.Count - 1];
            for (int i = 0; i < branches.Length; i++) branches[i] = RiverFrom(_using.Rivers[i + 1]);
            riverBranches = branches;
            var ponds = new PondFeature[_using.Ponds.Count];
            for (int i = 0; i < ponds.Length; i++)
            {
                float[] p = _using.Ponds[i];
                ponds[i] = new PondFeature { center = new Vector2(p[0], p[1]), radius = p[2], noiseSeed = p[3], irregularity = p[4] };
            }
            allPonds = ponds;
        }

        private static RiverFeature RiverFrom(float[] f)
        {
            return new RiverFeature { start = new Vector2(f[0], f[1]), end = new Vector2(f[2], f[3]), halfWidth = f[4], meanderAmp = f[5], meanderFreq = f[6], meanderPhase = f[7] };
        }

        /// <summary>True (with the road filled in) when the saved road is used instead of routing one.</summary>
        private bool RestoreRoadFromSnapshot()
        {
            if (_using == null) return false;
            roadPoints.Clear();
            roadPoints.AddRange(_using.Road);
            if (_using.RoadHalfWidth > 0f) roadHalfWidth = _using.RoadHalfWidth;
            return true;
        }

        /// <summary>The saved heights, or false when this generation is not restoring.</summary>
        private bool TryRestoreHeights(float[,] heights)
        {
            if (_using == null) return false;
            System.Array.Copy(_using.Heights, heights, heights.Length);
            return true;
        }

        /// <summary>The saved biome map pixels, or false when this generation is not restoring.</summary>
        private bool TryRestoreBiomeMap(Color[] mapPixels)
        {
            if (_using == null) return false;
            for (int i = 0; i < mapPixels.Length; i++)
            {
                float a = (_using.Modes[i] + 0.5f) / 18.0f;
                mapPixels[i] = new Color(_using.Rgb[i * 3] / 255f, _using.Rgb[i * 3 + 1] / 255f, _using.Rgb[i * 3 + 2] / 255f, a);
            }
            return true;
        }

        /// <summary>Ends a generation: keeps what it produced so the save can write it.</summary>
        private void EndSnapshotUse(float[,] heights, Color[] mapPixels, int mapRes)
        {
            if (_using != null)
            {
                LastGenerated = _using;
                SnapshotDirty = false;
                _using = null;
                return;
            }
            var s = new WorldSnapshot
            {
                Seed = worldSeed, HeightRes = terrainData.heightmapResolution, MapRes = mapRes,
                SizeX = terrainSizeX, SizeZ = terrainSizeZ, SizeY = terrainHeight,
                Heights = (float[,])heights.Clone(),
                Modes = new byte[mapPixels.Length], Rgb = new byte[mapPixels.Length * 3],
                RoadHalfWidth = roadHalfWidth,
            };
            for (int i = 0; i < mapPixels.Length; i++)
            {
                Color c = mapPixels[i];
                s.Modes[i] = (byte)Mathf.Clamp(Mathf.RoundToInt(c.a * 18f - 0.5f), 0, 255);
                s.Rgb[i * 3] = (byte)Mathf.Clamp(Mathf.RoundToInt(c.r * 255f), 0, 255);
                s.Rgb[i * 3 + 1] = (byte)Mathf.Clamp(Mathf.RoundToInt(c.g * 255f), 0, 255);
                s.Rgb[i * 3 + 2] = (byte)Mathf.Clamp(Mathf.RoundToInt(c.b * 255f), 0, 255);
            }
            s.Rivers.Add(RiverTo(mainRiver));
            foreach (RiverFeature r in riverBranches) s.Rivers.Add(RiverTo(r));
            foreach (PondFeature p in allPonds) s.Ponds.Add(new[] { p.center.x, p.center.y, p.radius, p.noiseSeed, p.irregularity });
            s.Road.AddRange(roadPoints);
            LastGenerated = s;
            SnapshotDirty = true;
        }

        private static float[] RiverTo(RiverFeature r)
        {
            return new[] { r.start.x, r.start.y, r.end.x, r.end.y, r.halfWidth, r.meanderAmp, r.meanderFreq, r.meanderPhase };
        }
    }
}
