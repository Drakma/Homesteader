using System.Collections.Generic;
using UnityEngine;
using Homesteader.Generation;

namespace Homesteader.World
{
    /// <summary>
    /// A procedural post-and-rail fence along the boundary of owned land (LandBoundaryController gives it the border
    /// loops). Built in code, flat shaded with the Homesteader/Vegetation shader. The fence follows the terrain, stops
    /// for water (a post at each bank) and leaves an opening where the road passes through (a heavier gate post each
    /// side). No colliders: the invisible land walls still do the blocking.
    /// </summary>
    public static class ProceduralFence
    {
        private const float PostSpacing = 2.4f;
        private const float SampleStep = 0.5f;
        private const float WaterMargin = 0.9f;     // metres of bank the fence keeps back from the water
        private const float RoadMargin = 0.7f;      // clear verge either side of the road surface
        private const int PostMat = 0, RailMat = 1;

        private static Material[] _materials;

        /// <summary>Builds the fence for the given border loops (each a list of x, z points). Returns the object, or null.</summary>
        public static GameObject Build(Transform parent, List<List<Vector2>> loops, HomesteaderTerrainGenerator gen)
        {
            if (loops == null || loops.Count == 0) return null;

            var m = new BoxMesher();
            var rng = new System.Random(gen != null ? gen.worldSeed * 131 + 9 : 9);
            int runs = 0;

            foreach (List<Vector2> loop in loops)
            {
                if (loop.Count < 2) continue;

                // Sample the loop every half metre and mark where the fence cannot go.
                var pts = new List<Vector2>();
                for (int i = 0; i < loop.Count - 1; i++)
                {
                    Vector2 a = loop[i], b = loop[i + 1];
                    float len = Vector2.Distance(a, b);
                    int steps = Mathf.Max(1, Mathf.CeilToInt(len / SampleStep));
                    for (int s = 0; s < steps; s++) pts.Add(Vector2.Lerp(a, b, (float)s / steps));
                }
                pts.Add(loop[loop.Count - 1]);

                var blocked = new bool[pts.Count];
                for (int i = 0; i < pts.Count; i++) blocked[i] = IsBlocked(gen, pts[i]);

                int k = 0;
                while (k < pts.Count)
                {
                    if (blocked[k]) { k++; continue; }
                    int start = k;
                    while (k < pts.Count && !blocked[k]) k++;
                    int end = k - 1;
                    if (end - start < 2) continue;
                    BuildRun(m, pts, start, end, rng);
                    runs++;
                }
            }

            if (m.VertexCount == 0) return null;

            var go = new GameObject("LandFence");
            go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);   // vertices are in world space
            go.AddComponent<MeshFilter>().sharedMesh = m.ToMesh("LandFenceMesh", 2);
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = Materials();
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            return go;
        }

        private static bool IsBlocked(HomesteaderTerrainGenerator gen, Vector2 p)
        {
            if (gen == null) return false;
            if (p.x < 0f || p.y < 0f || p.x > gen.terrainSizeX || p.y > gen.terrainSizeZ) return false;
            if (gen.IsWaterAt(p.x, p.y) || gen.GetWaterDistance(p.x, p.y) < WaterMargin) return true;
            return gen.IsNearRoad(p.x, p.y, RoadMargin);
        }

        private static float GroundY(Vector2 p)
        {
            return TerrainHeightDetector.GetGroundY(p.x, p.y);
        }

        /// <summary>Posts and rails along pts[start..end], which is one unbroken stretch.</summary>
        private static void BuildRun(BoxMesher m, List<Vector2> pts, int start, int end, System.Random rng)
        {
            // Cumulative length along the stretch.
            int n = end - start + 1;
            var cum = new float[n];
            for (int i = 1; i < n; i++) cum[i] = cum[i - 1] + Vector2.Distance(pts[start + i - 1], pts[start + i]);
            float length = cum[n - 1];
            if (length < 1.2f) return;

            int postCount = Mathf.Max(2, Mathf.RoundToInt(length / PostSpacing) + 1);
            var postPos = new Vector3[postCount];
            var postTan = new Vector2[postCount];
            int seg = 0;
            for (int p = 0; p < postCount; p++)
            {
                float s = length * p / (postCount - 1);
                while (seg < n - 2 && cum[seg + 1] < s) seg++;
                float segLen = Mathf.Max(0.0001f, cum[seg + 1] - cum[seg]);
                float t = Mathf.Clamp01((s - cum[seg]) / segLen);
                Vector2 a = pts[start + seg], b = pts[start + seg + 1];
                Vector2 xz = Vector2.Lerp(a, b, t);
                postTan[p] = (b - a).normalized;
                postPos[p] = new Vector3(xz.x, GroundY(xz), xz.y);
            }

            for (int p = 0; p < postCount; p++)
            {
                bool endPost = p == 0 || p == postCount - 1;
                float h = (endPost ? 1.45f : 1.2f) + ((float)rng.NextDouble() - 0.5f) * 0.1f;
                float half = endPost ? 0.09f : 0.06f;
                Vector3 pos = postPos[p];
                Vector3 f = new Vector3(postTan[p].x, 0f, postTan[p].y);
                Vector3 r = Vector3.Cross(Vector3.up, f).normalized;
                // Posts are set in the ground, a little off true.
                m.Box(pos + Vector3.up * (h * 0.5f - 0.15f), r, Vector3.up, f, new Vector3(half, h * 0.5f, half), PostMat);
                if (endPost)
                    m.Box(pos + Vector3.up * (h - 0.13f), r, Vector3.up, f, new Vector3(half + 0.04f, 0.04f, half + 0.04f), PostMat);   // cap
            }

            // Two rails between each pair of posts, following the ground.
            for (int p = 0; p < postCount - 1; p++)
            {
                Vector3 a = postPos[p], b = postPos[p + 1];
                foreach (float height in new[] { 0.45f, 0.95f })
                {
                    Vector3 ra = a + Vector3.up * height + RailSide(postTan[p], 0.07f);
                    Vector3 rb = b + Vector3.up * height + RailSide(postTan[p + 1], 0.07f);
                    m.Beam(ra, rb, 0.035f, 0.05f, RailMat);
                }
            }
        }

        /// <summary>Rails sit on the face of the posts, not through them.</summary>
        private static Vector3 RailSide(Vector2 tangent, float offset)
        {
            return new Vector3(-tangent.y, 0f, tangent.x) * offset;
        }

        private static Material[] Materials()
        {
            if (_materials != null && _materials[0] != null) return _materials;
            Shader shader = Shader.Find("Homesteader/Vegetation") ?? Shader.Find("Universal Render Pipeline/Lit");
            string[] hex = { "#5f4c35", "#85704d" };   // posts, rails
            _materials = new Material[hex.Length];
            for (int i = 0; i < hex.Length; i++)
            {
                ColorUtility.TryParseHtmlString(hex[i], out Color c);
                var mat = new Material(shader) { hideFlags = HideFlags.DontSave, name = "Fence_" + i };
                mat.SetColor("_BaseColor", c);
                if (mat.HasProperty("_SwayAmp")) mat.SetFloat("_SwayAmp", 0f);
                if (mat.HasProperty("_Grow")) mat.SetFloat("_Grow", 1f);
                _materials[i] = mat;
            }
            return _materials;
        }
    }
}
