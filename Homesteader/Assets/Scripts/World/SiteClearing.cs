using System.Collections.Generic;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Clears the ground under a foundation: every tree, rock, bush, plant, stump and scrap of debris standing inside its footprint
    /// (plus a margin) is removed when the foundation is built. The scattered world is baked into chunk meshes, so each baked object is
    /// found by the origin it stores in UV1 and collapsed to a point, like a felled tree. Things the player placed (items, crates,
    /// other sites) are left alone. Called by ConstructionSite when its foundation stage exists, and again when a save is loaded.
    /// </summary>
    public static class SiteClearing
    {
        /// <summary>Metres past the footprint that are cleared too (a trunk right at the edge would otherwise poke through the wall).</summary>
        public const float Margin = 0.75f;

        public static void ClearFootprint(Vector3 centre, float yawDeg, Vector2 size)
        {
            Quaternion inverse = Quaternion.Euler(0f, -yawDeg, 0f);
            float hx = size.x * 0.5f + Margin, hz = size.y * 0.5f + Margin;
            System.Func<float, float, bool> inside = (x, z) =>
            {
                Vector3 l = inverse * new Vector3(x - centre.x, 0f, z - centre.z);
                return Mathf.Abs(l.x) <= hx && Mathf.Abs(l.z) <= hz;
            };
            float reach = Mathf.Sqrt(hx * hx + hz * hz);
            ClearInside(centre, reach, inside);
        }

        /// <summary>Clears everything standing inside a lot's polygon (corner points on the ground), plus a margin.</summary>
        public static void ClearPolygon(IList<Vector3> poly)
        {
            float x0 = float.MaxValue, x1 = float.MinValue, z0 = float.MaxValue, z1 = float.MinValue;
            foreach (Vector3 p in poly) { x0 = Mathf.Min(x0, p.x); x1 = Mathf.Max(x1, p.x); z0 = Mathf.Min(z0, p.z); z1 = Mathf.Max(z1, p.z); }
            var centre = new Vector3((x0 + x1) * 0.5f, 0f, (z0 + z1) * 0.5f);
            float reach = Mathf.Sqrt((x1 - x0) * (x1 - x0) + (z1 - z0) * (z1 - z0)) * 0.5f + Margin;
            ClearInside(centre, reach, (x, z) => LotInside(poly, x, z));
        }

        private static bool LotInside(IList<Vector3> poly, float x, float z)
        {
            if (LotRun.Inside(poly, x, z)) return true;
            for (int i = 0; i < poly.Count; i++)   // or within the margin of an edge
            {
                Vector3 a = poly[i], b = poly[(i + 1) % poly.Count];
                Vector2 ab = new Vector2(b.x - a.x, b.z - a.z), ap = new Vector2(x - a.x, z - a.z);
                float t = ab.sqrMagnitude < 1e-6f ? 0f : Mathf.Clamp01(Vector2.Dot(ap, ab) / ab.sqrMagnitude);
                if ((ap - ab * t).sqrMagnitude <= Margin * Margin) return true;
            }
            return false;
        }

        /// <summary>Tilling: removes the ground cover (grass tufts, flowers, scattered debris) inside one rectangle exactly, with no margin; trees, bushes and rocks stay.</summary>
        public static void ClearGround(float x0, float z0, float x1, float z1)
        {
            ClearChunks(new Vector3((x0 + x1) * 0.5f, 0f, (z0 + z1) * 0.5f), Mathf.Sqrt((x1 - x0) * (x1 - x0) + (z1 - z0) * (z1 - z0)) * 0.5f,
                (x, z) => x >= x0 && x <= x1 && z >= z0 && z <= z1);
            ForestSolids.MarkDirty();
        }

        private static void ClearInside(Vector3 centre, float reach, System.Func<float, float, bool> inside)
        {
            ClearChunks(centre, reach, inside);
            ForestTrees.ClearIn(inside);
            BerryBushes.ClearIn(inside);
            ForestSolids.ClearRocksIn(inside);

            // Plantables are treated like placed objects: never cleared (what the player planted stays; builders refuse to start over it).
            ForestSolids.MarkDirty();
        }

        private static void ClearChunks(Vector3 centre, float reach, System.Func<float, float, bool> inside)
        {
            // everything baked into the vegetation chunks (debris, tufts, flowers, plants)
            var origins = new List<Vector2>();
            var heights = new List<Vector2>();
            foreach (MeshFilter mf in Object.FindObjectsByType<MeshFilter>())
            {
                if (mf == null || mf.sharedMesh == null || !mf.name.StartsWith("VegChunk_")) continue;
                Mesh mesh = mf.sharedMesh;
                Bounds b = mesh.bounds;
                if (centre.x + reach < b.min.x || centre.x - reach > b.max.x || centre.z + reach < b.min.z || centre.z - reach > b.max.z) continue;
                mesh.GetUVs(1, origins);
                mesh.GetUVs(2, heights);
                if (origins.Count != mesh.vertexCount || heights.Count != mesh.vertexCount) continue;
                List<Vector3> verts = ForestTrees.VertexListFor(mesh);
                bool changed = false;
                for (int i = 0; i < verts.Count; i++)
                {
                    if (!inside(origins[i].x, origins[i].y)) continue;
                    var at = new Vector3(origins[i].x, heights[i].x, origins[i].y);
                    if (verts[i] == at) continue;
                    verts[i] = at;   // every triangle of the object degenerates
                    changed = true;
                }
                if (changed) mesh.SetVertices(verts);
            }
        }
    }
}
