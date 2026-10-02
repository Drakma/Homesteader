using System.Collections.Generic;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Grades the ground round a foundation, live: the ground under the footprint is raised to the level of the structure and the ground
    /// outside it slopes smoothly down to meet the natural ground a few metres away (it is only ever raised, never dug). The terrain is
    /// edited in place (Terrain data SetHeights), so the collider, the ground height lookups and the grass follow without a reload.
    /// <see cref="Apply"/> takes a fraction, so a build can raise the ground as it goes; things lying on the ground in the area ride up with it.
    /// The terrain is rebuilt from the world seed on every load, so nothing is saved: a site that is built regrades its ground when it loads.
    /// </summary>
    public sealed class TerrainGrade
    {
        public const float BlendMetres = 3f;

        private readonly Terrain _terrain;
        private readonly TerrainData _data;
        private readonly int _x0, _z0, _w, _h;
        private readonly float[,] _orig, _target;
        private readonly List<Rider> _riders = new List<Rider>();
        private float _lastApplied = -1f;

        private struct Rider
        {
            public Transform T;
            public float BaseY, GroundBefore;
        }

        /// <summary>Plans the grade for a foundation (centre, heading, width and depth) that stands at <paramref name="level"/> (world Y). Null when off the terrain.</summary>
        public static TerrainGrade Plan(Vector3 centre, float yawDeg, Vector2 foot, float level)
        {
            Terrain t = Terrain.activeTerrain;
            if (t == null || t.terrainData == null) return null;
            return new TerrainGrade(t, centre, yawDeg, foot, level);
        }

        private TerrainGrade(Terrain terrain, Vector3 centre, float yawDeg, Vector2 foot, float level)
        {
            _terrain = terrain;
            _data = terrain.terrainData;
            int res = _data.heightmapResolution;
            Vector3 size = _data.size;
            Vector3 origin = terrain.transform.position;
            float stepX = size.x / (res - 1), stepZ = size.z / (res - 1);

            float reach = 0.5f * Mathf.Sqrt(foot.x * foot.x + foot.y * foot.y) + BlendMetres + 1f;
            int x0 = Mathf.Max(0, Mathf.FloorToInt((centre.x - reach - origin.x) / stepX));
            int x1 = Mathf.Min(res - 1, Mathf.CeilToInt((centre.x + reach - origin.x) / stepX));
            int z0 = Mathf.Max(0, Mathf.FloorToInt((centre.z - reach - origin.z) / stepZ));
            int z1 = Mathf.Min(res - 1, Mathf.CeilToInt((centre.z + reach - origin.z) / stepZ));
            _x0 = x0; _z0 = z0; _w = Mathf.Max(0, x1 - x0 + 1); _h = Mathf.Max(0, z1 - z0 + 1);
            if (_w < 2 || _h < 2) { _orig = new float[0, 0]; _target = _orig; return; }

            _orig = _data.GetHeights(_x0, _z0, _w, _h);
            _target = new float[_h, _w];
            float levelN = Mathf.Clamp01((level - origin.y) / size.y);
            Quaternion inverse = Quaternion.Euler(0f, -yawDeg, 0f);
            float hx = foot.x * 0.5f + 0.25f, hz = foot.y * 0.5f + 0.25f;
            for (int j = 0; j < _h; j++)
            {
                for (int i = 0; i < _w; i++)
                {
                    float wx = origin.x + (_x0 + i) * stepX, wz = origin.z + (_z0 + j) * stepZ;
                    Vector3 l = inverse * new Vector3(wx - centre.x, 0f, wz - centre.z);
                    float dx = Mathf.Max(0f, Mathf.Abs(l.x) - hx), dz = Mathf.Max(0f, Mathf.Abs(l.z) - hz);
                    float d = Mathf.Sqrt(dx * dx + dz * dz);
                    float o = _orig[j, i];
                    if (d <= 0f) _target[j, i] = Mathf.Max(o, levelN);
                    else if (d < BlendMetres)
                    {
                        float w = 1f - Mathf.SmoothStep(0f, 1f, d / BlendMetres);
                        _target[j, i] = Mathf.Max(o, Mathf.Lerp(o, levelN, w));
                    }
                    else _target[j, i] = o;
                }
            }

            // what lies on the ground in the area rides up with it
            float rx0 = origin.x + _x0 * stepX, rx1 = origin.x + (_x0 + _w - 1) * stepX, rz0 = origin.z + _z0 * stepZ, rz1 = origin.z + (_z0 + _h - 1) * stepZ;
            foreach (WorldItem w in WorldItem.All) AddRider(w != null ? w.transform : null, rx0, rx1, rz0, rz1);
            foreach (PlacedObject p in PlacedObject.All) AddRider(p != null ? p.transform : null, rx0, rx1, rz0, rz1);
            foreach (PlantedGrowth p in PlantedGrowth.All) AddRider(p != null ? p.transform : null, rx0, rx1, rz0, rz1);
        }

        private void AddRider(Transform t, float x0, float x1, float z0, float z1)
        {
            if (t == null) return;
            Vector3 p = t.position;
            if (p.x < x0 || p.x > x1 || p.z < z0 || p.z > z1) return;
            _riders.Add(new Rider { T = t, BaseY = p.y, GroundBefore = _terrain.SampleHeight(p) + _terrain.transform.position.y });
        }

        /// <summary>True when there was anything to grade.</summary>
        public bool Any => _w >= 2 && _h >= 2;

        /// <summary>Puts the ground at a fraction (0 = as it was, 1 = fully graded) between its natural shape and the finished grade.</summary>
        public void Apply(float fraction)
        {
            if (!Any) return;
            fraction = Mathf.Clamp01(fraction);
            if (Mathf.Abs(fraction - _lastApplied) < 0.004f) return;
            _lastApplied = fraction;
            var heights = new float[_h, _w];
            for (int j = 0; j < _h; j++)
                for (int i = 0; i < _w; i++)
                    heights[j, i] = Mathf.Lerp(_orig[j, i], _target[j, i], fraction);
            _data.SetHeightsDelayLOD(_x0, _z0, heights);
            _data.SyncHeightmap();

            foreach (Rider r in _riders)
            {
                if (r.T == null) continue;
                Vector3 p = r.T.position;
                float now = _terrain.SampleHeight(p) + _terrain.transform.position.y;
                p.y = r.BaseY + (now - r.GroundBefore);
                r.T.position = p;
            }
        }

        /// <summary>Tells the grass to place its blades on the new ground (call when a grade has finished or been undone).</summary>
        public static void RefreshGrass()
        {
            var grass = Object.FindAnyObjectByType<Homesteader.Grass.GrassRenderer>();
            if (grass != null) grass.RefreshHeights();
            ForestSolids.MarkDirty();
        }
    }
}
