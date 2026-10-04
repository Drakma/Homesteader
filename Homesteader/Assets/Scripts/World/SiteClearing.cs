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

            // everything baked into the vegetation chunks (trees, rocks, debris, bushes, plants)
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

            ForestTrees.ClearIn(inside);
            BerryBushes.ClearIn(inside);
            ForestSolids.ClearRocksIn(inside);

            // Plantables are treated like placed objects: never cleared (what the player planted stays; builders refuse to start over it).
            ForestSolids.MarkDirty();
        }
    }
}
