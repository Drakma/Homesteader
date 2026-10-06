using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>One scattered rock (a boulder, a stone, scree) that a pickaxe can break: where it is, how big, and where it sits in its chunk mesh.</summary>
    public sealed class WorldRock
    {
        public Vector3 Position;
        public float Radius;          // horizontal half size
        public float Height;
        public float WeightKg;
        public Mesh Mesh;             // the chunk mesh it was merged into
        public (int, int, bool) ChunkKey;
        public int VertStart, VertCount;
        public bool IsBroken;
    }

    /// <summary>
    /// Every rock scattered by ProceduralVegetation (rocky ridge, shores, river beds), kept so the cursor can find one and a pickaxe can break it.
    /// The rocks are merged into chunk meshes, so breaking one collapses its vertices to a point (as a felled tree or a dug bush does) and takes its
    /// collider away. Broken rocks are saved as positions (GameSave.brokenRocks) and removed again when the world is regenerated on load.
    /// </summary>
    public static class WorldRocks
    {
        public const float DensityKgPerM3 = 2000f;
        private const float CellSize = 8f;

        public static readonly Dictionary<Transform, WorldRock> ByTransform = new Dictionary<Transform, WorldRock>();
        private static readonly Dictionary<Vector2Int, List<WorldRock>> Grid = new Dictionary<Vector2Int, List<WorldRock>>();
        private static readonly List<Vector2> Broken = new List<Vector2>();

        public static void Clear()
        {
            ByTransform.Clear();
            Grid.Clear();
            Broken.Clear();
        }

        /// <summary>Records a scattered rock (call where it is made, before the chunk merge).</summary>
        public static void Register(Transform placed, Mesh mesh)
        {
            if (placed == null || mesh == null) return;
            Vector3 e = mesh.bounds.extents;
            Vector3 sc = placed.lossyScale;
            float rx = e.x * sc.x, ry = e.y * sc.y, rz = e.z * sc.z;
            var rock = new WorldRock
            {
                Position = placed.position,
                Radius = Mathf.Max(rx, rz),
                Height = ry * 2f,
                WeightKg = 4f / 3f * Mathf.PI * rx * ry * rz * DensityKgPerM3,
            };
            ByTransform[placed] = rock;
            var cell = CellOf(rock.Position);
            if (!Grid.TryGetValue(cell, out List<WorldRock> list)) { list = new List<WorldRock>(); Grid[cell] = list; }
            list.Add(rock);
        }

        private static Vector2Int CellOf(Vector3 p) => new Vector2Int(Mathf.FloorToInt(p.x / CellSize), Mathf.FloorToInt(p.z / CellSize));

        /// <summary>The rock under the cursor: the nearest one the ray passes through (tested as a sphere round its middle), or null.</summary>
        private static int s_pickFrame = -1;
        private static Vector3 s_pickOrigin, s_pickDir;
        private static WorldRock s_pickResult;

        public static WorldRock TryPick(Ray ray)
        {
            if (Grid.Count == 0) return null;
            // asked by several cursor checks in one frame with the same ray
            if (s_pickFrame == Time.frameCount && s_pickOrigin == ray.origin && s_pickDir == ray.direction && (s_pickResult == null || !s_pickResult.IsBroken)) return s_pickResult;
            WorldRock r = TryPickUncached(ray);
            s_pickFrame = Time.frameCount;
            s_pickOrigin = ray.origin;
            s_pickDir = ray.direction;
            s_pickResult = r;
            return r;
        }

        private static WorldRock TryPickUncached(Ray ray)
        {
            // where the ray meets the ground (the terrain), then the rocks round that spot: a rock stands up, so the ray meets it in front of the ground behind it
            Vector3 aim;
            if (Physics.Raycast(ray, out RaycastHit hit, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore)) aim = hit.point;
            else return null;
            WorldRock best = null;
            float bestT = float.MaxValue;
            Vector2Int c0 = CellOf(aim);
            for (int dx = -1; dx <= 1; dx++)
                for (int dz = -1; dz <= 1; dz++)
                {
                    if (!Grid.TryGetValue(new Vector2Int(c0.x + dx, c0.y + dz), out List<WorldRock> list)) continue;
                    foreach (WorldRock r in list)
                    {
                        Vector3 centre = r.Position + Vector3.up * (r.Height * 0.5f);
                        float radius = Mathf.Max(r.Radius, r.Height * 0.5f, 0.12f) * 1.05f + 0.05f;
                        Vector3 oc = centre - ray.origin;
                        float t = Vector3.Dot(oc, ray.direction);
                        if (t < 0f) continue;
                        float d2 = oc.sqrMagnitude - t * t;
                        if (d2 > radius * radius) continue;
                        if (t < bestT) { bestT = t; best = r; }
                    }
                }
            return best;
        }

        /// <summary>Breaks a rock: it vanishes from the world (its part of the chunk mesh collapses, its collider goes).</summary>
        public static void Break(WorldRock rock)
        {
            if (rock == null || rock.IsBroken) return;
            rock.IsBroken = true;
            if (rock.Mesh != null && rock.VertCount > 0)
            {
                List<Vector3> verts = ForestTrees.VertexListFor(rock.Mesh);
                int end = Mathf.Min(verts.Count, rock.VertStart + rock.VertCount);
                for (int i = rock.VertStart; i < end; i++) verts[i] = rock.Position;
                rock.Mesh.SetVertices(verts);
            }
            Vector3 p = rock.Position;
            ForestSolids.ClearRocksIn((x, z) => Mathf.Abs(x - p.x) < 0.02f && Mathf.Abs(z - p.z) < 0.02f);
            if (Grid.TryGetValue(CellOf(p), out List<WorldRock> list)) list.Remove(rock);
            Broken.Add(new Vector2(p.x, p.z));
        }

        public static List<Vector2> SavedBroken() { return new List<Vector2>(Broken); }

        /// <summary>Breaks the rocks a save says were broken (after the world is generated).</summary>
        public static void ApplyBroken(List<Vector2> broken)
        {
            if (broken == null) return;
            foreach (Vector2 p in broken)
            {
                WorldRock best = null;
                float bestD = 0.05f * 0.05f;
                var cell = CellOf(new Vector3(p.x, 0f, p.y));
                if (!Grid.TryGetValue(cell, out List<WorldRock> list)) continue;
                foreach (WorldRock r in list)
                {
                    float dx = r.Position.x - p.x, dz = r.Position.z - p.y;
                    float d = dx * dx + dz * dz;
                    if (d < bestD) { bestD = d; best = r; }
                }
                if (best != null) Break(best);
            }
        }
    }
}
