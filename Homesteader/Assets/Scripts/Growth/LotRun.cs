using System.Collections.Generic;
using Homesteader.Generation;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// One LOT the player laid: a flat area of any size and shape (a polygon of corner points on the ground) paved with dirt, gravel, asphalt or concrete. The polygon is
    /// triangulated (ear clipping), cut into small triangles so it follows the ground, and drawn 5 cm above it with a tiling surface of its own. No collider: it is ground you
    /// walk, drive and build on. Built by LotBuilder (docs/LOTS.md); saved in GameSave.lots.
    /// </summary>
    public sealed class LotRun : MonoBehaviour
    {
        public static readonly List<LotRun> All = new List<LotRun>();

        public string Style = "gravel";            // dirt, gravel, asphalt or concrete
        public string ItemId;                      // the blueprint it was laid with
        public readonly List<Vector3> Points = new List<Vector3>();
        public float Area;                         // square metres (flat)

        private const float Lift = 0.05f;          // above the ground, like a path
        private const float MaxEdge = 1.5f;        // metres: the triangles are cut until none has a longer edge, so the lot follows the ground
        private static int s_order;                // a lot laid later lies a hair above one laid earlier
        private int _order;
        private static readonly Dictionary<string, Material> s_mats = new Dictionary<string, Material>();

        private void OnEnable() { All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        public static LotRun Create(string style, string itemId, List<Vector3> points)
        {
            var go = new GameObject("Lot_" + style);
            var lot = go.AddComponent<LotRun>();
            lot.Style = style;
            lot.ItemId = itemId;
            lot.Points.AddRange(points);
            lot._order = ++s_order;
            lot.Area = PolygonArea(points);
            lot.Rebuild();
            return lot;
        }

        public static void Clear()
        {
            foreach (LotRun l in new List<LotRun>(All)) if (l != null) Destroy(l.gameObject);
            All.Clear();
        }

        // ------------------------------------------------------------------ geometry

        public static float SignedArea(IList<Vector3> p)
        {
            float a = 0f;
            for (int i = 0; i < p.Count; i++)
            {
                Vector3 u = p[i], v = p[(i + 1) % p.Count];
                a += u.x * v.z - v.x * u.z;
            }
            return a * 0.5f;
        }

        public static float PolygonArea(IList<Vector3> p) { return Mathf.Abs(SignedArea(p)); }

        public static bool Inside(IList<Vector3> poly, float x, float z)
        {
            bool inside = false;
            for (int i = 0, j = poly.Count - 1; i < poly.Count; j = i++)
            {
                if ((poly[i].z > z) != (poly[j].z > z) && x < (poly[j].x - poly[i].x) * (z - poly[i].z) / (poly[j].z - poly[i].z) + poly[i].x) inside = !inside;
            }
            return inside;
        }

        private static float Cross(Vector2 o, Vector2 a, Vector2 b) { return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x); }

        /// <summary>True when two edges of the polygon cross each other (a figure of eight, a bow tie): it cannot be a lot.</summary>
        public static bool SelfIntersects(IList<Vector3> p)
        {
            int n = p.Count;
            for (int i = 0; i < n; i++)
                for (int j = i + 1; j < n; j++)
                {
                    if (j == i + 1 || (i == 0 && j == n - 1)) continue;   // neighbours share a corner
                    Vector2 a = new Vector2(p[i].x, p[i].z), b = new Vector2(p[(i + 1) % n].x, p[(i + 1) % n].z);
                    Vector2 c = new Vector2(p[j].x, p[j].z), d = new Vector2(p[(j + 1) % n].x, p[(j + 1) % n].z);
                    if (Cross(a, b, c) * Cross(a, b, d) < 0f && Cross(c, d, a) * Cross(c, d, b) < 0f) return true;
                }
            return false;
        }

        /// <summary>Ear clipping: the polygon (counter-clockwise or clockwise) as triangles of indices into it. Null when it cannot be cut (a degenerate shape).</summary>
        public static List<int> Triangulate(IList<Vector3> poly)
        {
            int n = poly.Count;
            var idx = new List<int>();
            for (int i = 0; i < n; i++) idx.Add(i);
            if (SignedArea(poly) < 0f) idx.Reverse();   // work counter-clockwise (x right, z up)
            var tris = new List<int>();
            int guard = n * n + 8;
            while (idx.Count > 3 && guard-- > 0)
            {
                bool clipped = false;
                for (int k = 0; k < idx.Count; k++)
                {
                    int ia = idx[(k + idx.Count - 1) % idx.Count], ib = idx[k], ic = idx[(k + 1) % idx.Count];
                    Vector2 a = new Vector2(poly[ia].x, poly[ia].z), b = new Vector2(poly[ib].x, poly[ib].z), c = new Vector2(poly[ic].x, poly[ic].z);
                    if (Cross(a, b, c) <= 1e-6f) continue;   // a reflex or flat corner is not an ear
                    bool any = false;
                    foreach (int m in idx)
                    {
                        if (m == ia || m == ib || m == ic) continue;
                        Vector2 q = new Vector2(poly[m].x, poly[m].z);
                        if (Cross(a, b, q) >= 0f && Cross(b, c, q) >= 0f && Cross(c, a, q) >= 0f) { any = true; break; }
                    }
                    if (any) continue;
                    tris.Add(ia); tris.Add(ib); tris.Add(ic);
                    idx.RemoveAt(k);
                    clipped = true;
                    break;
                }
                if (!clipped) return null;
            }
            if (idx.Count == 3) { tris.Add(idx[0]); tris.Add(idx[1]); tris.Add(idx[2]); }
            return tris;
        }

        /// <summary>The polygon cut into small triangles (no edge longer than maxEdge), as a flat list of corner positions, three to a triangle.</summary>
        public static List<Vector3> Tessellate(IList<Vector3> poly, float maxEdge)
        {
            var result = new List<Vector3>();
            List<int> tris = Triangulate(poly);
            if (tris == null) return result;
            var stack = new Stack<Vector3[]>();
            for (int i = 0; i < tris.Count; i += 3) stack.Push(new[] { poly[tris[i]], poly[tris[i + 1]], poly[tris[i + 2]] });
            float max2 = maxEdge * maxEdge;
            int budget = 60000;
            while (stack.Count > 0 && budget-- > 0)
            {
                Vector3[] t = stack.Pop();
                int longest = 0;
                float best = 0f;
                for (int e = 0; e < 3; e++)
                {
                    Vector3 d = t[(e + 1) % 3] - t[e];
                    d.y = 0f;
                    float l = d.sqrMagnitude;
                    if (l > best) { best = l; longest = e; }
                }
                if (best <= max2) { result.Add(t[0]); result.Add(t[1]); result.Add(t[2]); continue; }
                Vector3 a = t[longest], b = t[(longest + 1) % 3], c = t[(longest + 2) % 3];
                Vector3 mid = (a + b) * 0.5f;
                stack.Push(new[] { a, mid, c });
                stack.Push(new[] { mid, b, c });
            }
            return result;
        }

        /// <summary>A mesh of the polygon draped on the ground, lift metres above it; UVs are the world position (the surface texture tiles in metres).</summary>
        public static Mesh BuildMesh(IList<Vector3> poly, float maxEdge, float lift, Mesh into)
        {
            List<Vector3> corners = Tessellate(poly, maxEdge);
            var verts = new List<Vector3>(corners.Count);
            var uvs = new List<Vector2>(corners.Count);
            var tris = new List<int>(corners.Count);
            var normals = new List<Vector3>(corners.Count);
            for (int i = 0; i < corners.Count; i += 3)
            {
                for (int k = 0; k < 3; k++)
                {
                    Vector3 c = corners[i + k];
                    verts.Add(new Vector3(c.x, TerrainHeightDetector.GetGroundY(c.x, c.z) + lift, c.z));
                    uvs.Add(new Vector2(c.x, c.z));
                    normals.Add(Vector3.up);
                }
                bool up = Vector3.Cross(verts[i + 1] - verts[i], verts[i + 2] - verts[i]).y >= 0f;   // wound so the top faces up
                tris.Add(i); tris.Add(up ? i + 1 : i + 2); tris.Add(up ? i + 2 : i + 1);
            }
            Mesh m = into != null ? into : new Mesh { name = "Lot", hideFlags = HideFlags.DontSave };
            m.Clear();
            m.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            m.SetVertices(verts);
            m.SetUVs(0, uvs);
            m.SetNormals(normals);
            m.SetTriangles(tris, 0);
            m.RecalculateBounds();
            return m;
        }

        private void Rebuild()
        {
            MeshFilter mf = GetComponent<MeshFilter>();
            if (mf == null) mf = gameObject.AddComponent<MeshFilter>();
            MeshRenderer mr = GetComponent<MeshRenderer>();
            if (mr == null) mr = gameObject.AddComponent<MeshRenderer>();
            mf.sharedMesh = BuildMesh(Points, MaxEdge, Lift + _order * 0.0015f, mf.sharedMesh);
            mr.sharedMaterial = Surface(Style);
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = true;
        }

        /// <summary>The lot under a ground point (the newest when several overlap), or null.</summary>
        public static LotRun At(float x, float z)
        {
            LotRun found = null;
            foreach (LotRun l in All) if (l != null && Inside(l.Points, x, z) && (found == null || l._order > found._order)) found = l;
            return found;
        }

        // ------------------------------------------------------------------ the surfaces

        private static Material Surface(string style)
        {
            if (s_mats.TryGetValue(style, out Material have) && have != null) return have;
            float tile = style == "asphalt" ? 6f : style == "concrete" ? 3f : style == "gravel" ? 2.5f : 4f;
            float smooth = style == "asphalt" ? 0.22f : style == "concrete" ? 0.12f : 0.03f;
            Shader sh = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            var mat = new Material(sh) { name = "Lot_" + style, hideFlags = HideFlags.DontSave };
            Texture2D tex = MakeTexture(style);
            if (mat.HasProperty("_BaseMap")) { mat.SetTexture("_BaseMap", tex); mat.SetTextureScale("_BaseMap", new Vector2(1f / tile, 1f / tile)); }
            mat.mainTexture = tex;
            mat.mainTextureScale = new Vector2(1f / tile, 1f / tile);
            if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", Color.white);
            if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", smooth);
            if (mat.HasProperty("_Metallic")) mat.SetFloat("_Metallic", 0f);
            s_mats[style] = mat;
            return mat;
        }

        private static float Tile(float x, float y, float f, float seed)
        {
            // noise that repeats every texture (x and y run 0..1): the four neighbours are blended in
            float a = Mathf.PerlinNoise(seed + x * f, seed + y * f);
            float b = Mathf.PerlinNoise(seed + (x - 1f) * f, seed + y * f);
            float c = Mathf.PerlinNoise(seed + x * f, seed + (y - 1f) * f);
            float d = Mathf.PerlinNoise(seed + (x - 1f) * f, seed + (y - 1f) * f);
            return Mathf.Lerp(Mathf.Lerp(a, b, x), Mathf.Lerp(c, d, x), y);
        }

        private static Texture2D MakeTexture(string style)
        {
            const int N = 128;
            var tex = new Texture2D(N, N, TextureFormat.RGBA32, true) { name = "LotTex_" + style, wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear, hideFlags = HideFlags.DontSave };
            Color baseC, dark;
            float coarse, fine, speck;
            switch (style)
            {
                case "dirt": baseC = new Color(0.43f, 0.32f, 0.21f); dark = new Color(0.30f, 0.22f, 0.14f); coarse = 5f; fine = 22f; speck = 0.10f; break;
                case "asphalt": baseC = new Color(0.17f, 0.17f, 0.19f); dark = new Color(0.10f, 0.10f, 0.12f); coarse = 3f; fine = 40f; speck = 0.22f; break;
                case "concrete": baseC = new Color(0.62f, 0.62f, 0.60f); dark = new Color(0.50f, 0.50f, 0.48f); coarse = 4f; fine = 30f; speck = 0.06f; break;
                default: baseC = new Color(0.62f, 0.60f, 0.55f); dark = new Color(0.42f, 0.40f, 0.37f); coarse = 6f; fine = 55f; speck = 0.30f; break;   // gravel
            }
            var px = new Color[N * N];
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float u = x / (float)N, v = y / (float)N;
                    float n = Tile(u, v, coarse, 11f) * 0.6f + Tile(u, v, fine, 47f) * 0.4f;
                    float s = Mathf.PerlinNoise(97f + u * 90f, 97f + v * 90f);
                    Color c = Color.Lerp(dark, baseC, Mathf.Clamp01(n * 1.3f - 0.1f));
                    c *= 1f - speck + speck * 2f * s;
                    if (style == "concrete")
                    {
                        // an expansion joint along two edges of every slab (the tile is one slab, 3 m)
                        if (x < 2 || y < 2) c *= 0.62f;
                    }
                    if (style == "asphalt" && s > 0.93f) c = Color.Lerp(c, new Color(0.45f, 0.45f, 0.47f), 0.5f);   // a pale chip of stone in the tar
                    c.a = 1f;
                    px[y * N + x] = c;
                }
            tex.SetPixels(px);
            tex.Apply(true);
            return tex;
        }
    }
}
