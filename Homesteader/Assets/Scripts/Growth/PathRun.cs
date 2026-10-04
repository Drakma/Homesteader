using System;
using System.Collections.Generic;
using Homesteader.Generation;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// One path or road the player laid: a smooth curve through a few control points (Catmull-Rom), draped on the ground as a flat ribbon of the
    /// surface material, with a slim verge either side and, for asphalt, a dashed centre line. Built by PathBuilder. Kind, width and surface
    /// come from the material item's manifest (path_kind, path_width_m, path_style). It has no collider: it is ground you walk on.
    /// <see cref="Built"/> is how many metres of the route exist so far (the ped lays it section by section; a finished route is all of it).
    /// Saved with the game (GameSave.paths).
    /// </summary>
    public sealed class PathRun : MonoBehaviour
    {
        public static readonly List<PathRun> All = new List<PathRun>();

        public string Kind = "path";            // path or road
        public string Style = "gravel";         // dirt, gravel, stone, asphalt
        public string ItemId;                   // the material item
        public float Width = 1.2f;
        public float MetresPerItem = 2f;
        public readonly List<Vector3> Points = new List<Vector3>();
        public float Built = float.MaxValue;    // metres laid so far

        private const float Lift = 0.05f;       // above the ground, so the terrain does not poke through
        private const float Fade = 0.5f;       // metres of soft, ragged edge each side beyond the nominal width (like the starter road)
        private const float AlongMetres = 16f;  // the edge texture repeats every this many metres along the route
        private const float Step = 0.5f;        // metres between cross sections along the curve
        private MeshFilter _mf;
        private MeshRenderer _mr;
        private List<Vector3> _curve;
        private float _length;
        private static readonly Dictionary<string, Material> s_mats = new Dictionary<string, Material>();

        private void OnEnable() { All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        public static PathRun Create(string kind, string style, string itemId, float width, float metresPerItem, List<Vector3> points, float built)
        {
            var go = new GameObject("Path_" + style);
            var run = go.AddComponent<PathRun>();
            run.Kind = kind;
            run.Style = style;
            run.ItemId = itemId;
            run.Width = Mathf.Max(0.5f, width);
            run.MetresPerItem = Mathf.Max(0.25f, metresPerItem);
            run.Points.AddRange(points);
            run.Built = built;
            run.Rebuild();
            return run;
        }

        public static void Clear()
        {
            foreach (PathRun p in new List<PathRun>(All)) if (p != null) Destroy(p.gameObject);
            All.Clear();
        }

        // ------------------------------------------------------------------ the curve

        /// <summary>The smooth route through the control points, as points about <see cref="Step"/> apart, on the ground.</summary>
        public static List<Vector3> Sample(IList<Vector3> pts)
        {
            var dense = new List<Vector3>();
            int n = pts.Count;
            if (n == 0) return dense;
            if (n == 1) { dense.Add(pts[0]); return dense; }
            for (int i = 0; i < n - 1; i++)
            {
                Vector3 p0 = pts[Mathf.Max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Mathf.Min(n - 1, i + 2)];
                int sub = Mathf.Max(4, Mathf.CeilToInt(Vector3.Distance(p1, p2) / 0.15f));
                for (int k = 0; k < sub; k++) dense.Add(CatmullRom(p0, p1, p2, p3, k / (float)sub));
            }
            dense.Add(pts[n - 1]);

            // even spacing along the length
            var even = new List<Vector3> { dense[0] };
            float carried = 0f;
            for (int i = 1; i < dense.Count; i++)
            {
                Vector3 a = dense[i - 1], b = dense[i];
                float seg = Flat(a, b);
                while (carried + seg >= Step && seg > 1e-5f)
                {
                    float t = (Step - carried) / seg;
                    a = Vector3.Lerp(a, b, t);
                    even.Add(a);
                    seg = Flat(a, b);
                    carried = 0f;
                }
                carried += seg;
            }
            if (Flat(even[even.Count - 1], dense[dense.Count - 1]) > 0.05f) even.Add(dense[dense.Count - 1]);
            for (int i = 0; i < even.Count; i++) even[i] = OnGround(even[i]);
            return even;
        }

        private static Vector3 CatmullRom(Vector3 p0, Vector3 p1, Vector3 p2, Vector3 p3, float t)
        {
            float t2 = t * t, t3 = t2 * t;
            return 0.5f * ((2f * p1) + (-p0 + p2) * t + (2f * p0 - 5f * p1 + 4f * p2 - p3) * t2 + (-p0 + 3f * p1 - 3f * p2 + p3) * t3);
        }

        private static float Flat(Vector3 a, Vector3 b) { return new Vector2(b.x - a.x, b.z - a.z).magnitude; }

        private static Vector3 OnGround(Vector3 p) { return new Vector3(p.x, TerrainHeightDetector.GetGroundY(p.x, p.z), p.z); }

        public static float Length(IList<Vector3> curve)
        {
            float l = 0f;
            for (int i = 1; i < curve.Count; i++) l += Flat(curve[i - 1], curve[i]);
            return l;
        }

        /// <summary>The point and heading at a distance along the curve (clamped to its ends).</summary>
        public static Vector3 PointAt(IList<Vector3> curve, float distance, out Vector3 forward)
        {
            forward = Vector3.forward;
            if (curve.Count == 0) return Vector3.zero;
            if (curve.Count == 1) return curve[0];
            float run = 0f;
            for (int i = 1; i < curve.Count; i++)
            {
                float seg = Flat(curve[i - 1], curve[i]);
                forward = new Vector3(curve[i].x - curve[i - 1].x, 0f, curve[i].z - curve[i - 1].z).normalized;
                if (run + seg >= distance || i == curve.Count - 1)
                {
                    float t = seg > 1e-5f ? Mathf.Clamp01((distance - run) / seg) : 0f;
                    return Vector3.Lerp(curve[i - 1], curve[i], t);
                }
                run += seg;
            }
            return curve[curve.Count - 1];
        }

        /// <summary>Takes the plants, rocks and debris off the laid part of the route (used when a save is loaded; the builder clears each section as it lays it).</summary>
        public void ClearGround()
        {
            float to = Mathf.Min(Built, _length);
            for (float d = 0f; d < to; d += 2f)
            {
                float end = Mathf.Min(to, d + 2f);
                Vector3 mid = PointAt(_curve, (d + end) * 0.5f, out Vector3 fwd);
                Homesteader.World.SiteClearing.ClearFootprint(mid, Mathf.Atan2(fwd.x, fwd.z) * Mathf.Rad2Deg, new Vector2(Width, Mathf.Max(0.5f, end - d)));
            }
        }

        /// <summary>
        /// The point on the laid part of any path or road's centre line nearest to <paramref name="p"/>, when p is on that surface (within half its
        /// width). A new route starts and ends on it, so routes join.
        /// </summary>
        public static bool SnapToRoute(Vector3 p, out Vector3 snapped)
        {
            snapped = p;
            float best = float.MaxValue;
            foreach (PathRun run in All)
            {
                if (run == null || run._curve == null || run._curve.Count < 2) continue;
                float reach = run.Width * 0.5f, laid = 0f;
                for (int i = 1; i < run._curve.Count; i++)
                {
                    Vector3 a = run._curve[i - 1], b = run._curve[i];
                    float seg = Flat(a, b);
                    if (laid > run.Built) break;
                    laid += seg;
                    Vector2 ab = new Vector2(b.x - a.x, b.z - a.z), ap = new Vector2(p.x - a.x, p.z - a.z);
                    float t = ab.sqrMagnitude > 1e-6f ? Mathf.Clamp01(Vector2.Dot(ap, ab) / ab.sqrMagnitude) : 0f;
                    Vector3 q = Vector3.Lerp(a, b, t);
                    float d = Mathf.Sqrt((q.x - p.x) * (q.x - p.x) + (q.z - p.z) * (q.z - p.z));
                    if (d <= reach && d < best) { best = d; snapped = OnGround(q); }
                }
            }
            return best < float.MaxValue;
        }

        /// <summary>The part of the curve that is laid so far (all of it once the route is finished).</summary>
        public List<Vector3> LaidCurve()
        {
            var laid = new List<Vector3>();
            if (_curve == null) return laid;
            float acc = 0f;
            for (int i = 0; i < _curve.Count; i++)
            {
                if (i > 0) acc += Flat(_curve[i - 1], _curve[i]);
                if (acc > Built + 0.01f) break;
                laid.Add(_curve[i]);
            }
            return laid;
        }

        private static float DistanceToCurve(Vector3 p, IList<Vector3> curve)
        {
            float best = float.MaxValue;
            for (int i = 1; i < curve.Count; i++)
            {
                Vector2 a = new Vector2(curve[i - 1].x, curve[i - 1].z), b = new Vector2(curve[i].x, curve[i].z), q = new Vector2(p.x, p.z);
                Vector2 ab = b - a;
                float t = ab.sqrMagnitude > 1e-6f ? Mathf.Clamp01(Vector2.Dot(q - a, ab) / ab.sqrMagnitude) : 0f;
                best = Mathf.Min(best, (a + ab * t - q).magnitude);
            }
            return best;
        }

        /// <summary>
        /// A route laid over an older one replaces it: the stretches of finished routes that lie under the new surface (their centre line within half
        /// the new width of the new centre line) and run along it for a few metres are taken away, and what is left of the old route stays as pieces.
        /// A short overlap (a crossing) is not a replacement: the routes just blend there.
        /// </summary>
        public static void ReplaceUnder(IList<Vector3> newCurve, float newWidth, PathRun except)
        {
            if (newCurve == null || newCurve.Count < 2) return;
            float cover = newWidth * 0.5f;
            float minLen = Mathf.Max(3f, newWidth * 3f);
            foreach (PathRun old in new List<PathRun>(All))
            {
                if (old == null || old == except || old._curve == null || old._curve.Count < 2 || old.Built < old._length - 0.01f) continue;
                IList<Vector3> pts = old._curve;
                var covered = new bool[pts.Count];
                bool any = false;
                for (int i = 0; i < pts.Count; i++)
                {
                    covered[i] = DistanceToCurve(pts[i], newCurve) <= cover;
                    any |= covered[i];
                }
                if (!any) continue;
                var remove = new bool[pts.Count];
                bool removedSome = false;
                int a = 0;
                while (a < pts.Count)
                {
                    if (!covered[a]) { a++; continue; }
                    int b = a;
                    while (b + 1 < pts.Count && covered[b + 1]) b++;
                    float len = 0f;
                    for (int k = a + 1; k <= b; k++) len += Flat(pts[k - 1], pts[k]);
                    bool whole = a == 0 && b == pts.Count - 1;
                    if (len >= minLen || whole)
                    {
                        for (int k = a; k <= b; k++) remove[k] = true;
                        removedSome = true;
                    }
                    a = b + 1;
                }
                if (!removedSome) continue;
                // what is left becomes new runs, one for each unbroken piece
                var piece = new List<Vector3>();
                for (int i = 0; i <= pts.Count; i++)
                {
                    if (i < pts.Count && !remove[i]) { piece.Add(pts[i]); continue; }
                    if (piece.Count >= 3)
                    {
                        float plen = 0f;
                        for (int k = 1; k < piece.Count; k++) plen += Flat(piece[k - 1], piece[k]);
                        if (plen >= 1.5f) Create(old.Kind, old.Style, old.ItemId, old.Width, old.MetresPerItem, piece, float.MaxValue);
                    }
                    piece = new List<Vector3>();
                }
                Destroy(old.gameObject);
            }
        }

        public float TotalLength { get { return _length; } }

        public List<Vector3> Curve { get { return _curve; } }

        // ------------------------------------------------------------------ the mesh

        public void Rebuild()
        {
            _curve = Sample(Points);
            _length = Length(_curve);
            if (_mf == null)
            {
                _mf = gameObject.AddComponent<MeshFilter>();
                _mr = gameObject.AddComponent<MeshRenderer>();
                _mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }

            // only the first Built metres exist
            var run = new List<Vector3>();
            float acc = 0f;
            for (int i = 0; i < _curve.Count; i++)
            {
                if (i > 0) acc += Flat(_curve[i - 1], _curve[i]);
                if (acc > Built + 0.001f)
                {
                    Vector3 end = PointAt(_curve, Built, out _);
                    if (run.Count > 0 && Flat(run[run.Count - 1], end) > 0.02f) run.Add(OnGround(end));
                    break;
                }
                run.Add(_curve[i]);
            }
            if (run.Count < 2) { _mf.sharedMesh = null; return; }

            float total = Width + Fade * 2f;
            int across = Mathf.Max(3, Mathf.CeilToInt(total / 0.8f) + 1);
            if (across % 2 == 0) across++;
            bool line = Style == "asphalt";

            var v = new List<Vector3>();
            var uv = new List<Vector2>();
            var surf = new List<int>();
            var edge = new List<int>();
            var mark = new List<int>();
            var rows = new List<int>();   // index of the first vertex of each cross section
            // The cross sections: the route itself plus a rounded cap beyond each end (the width closes in like a half circle), so the ends are soft too.
            var ring = new List<Vector3>();
            var fac = new List<float>();
            var vd = new List<float>();
            float capR = total * 0.5f;
            int capN = Mathf.CeilToInt(capR / Step);
            Vector3 d0 = run[0] - run[1]; d0.y = 0f; d0 = d0.normalized;
            Vector3 dN = run[run.Count - 1] - run[run.Count - 2]; dN.y = 0f; dN = dN.normalized;
            for (int k = capN; k >= 1; k--)
            {
                Vector3 q = OnGround(run[0] + d0 * (k * Step));
                ring.Add(q); fac.Add(CapWidth(k * Step / capR)); vd.Add(-k * Step);
            }
            float dist = 0f;
            for (int i = 0; i < run.Count; i++)
            {
                if (i > 0) dist += Flat(run[i - 1], run[i]);
                ring.Add(run[i]); fac.Add(1f); vd.Add(dist);
            }
            for (int k = 1; k <= capN; k++)
            {
                Vector3 q = OnGround(run[run.Count - 1] + dN * (k * Step));
                ring.Add(q); fac.Add(CapWidth(k * Step / capR)); vd.Add(dist + k * Step);
            }
            for (int i = 0; i < ring.Count; i++)
            {
                Vector3 fwd = i == 0 ? ring[1] - ring[0] : i == ring.Count - 1 ? ring[i] - ring[i - 1] : ring[i + 1] - ring[i - 1];
                fwd.y = 0f;
                fwd = fwd.sqrMagnitude < 1e-6f ? Vector3.forward : fwd.normalized;
                Vector3 right = Vector3.Cross(Vector3.up, fwd);
                rows.Add(v.Count);
                for (int k = 0; k < across; k++)
                {
                    float f = k / (float)(across - 1) * 2f - 1f;   // -1 .. 1 across the width
                    Vector3 p = ring[i] + right * (f * total * 0.5f * fac[i]);
                    p.y = TerrainHeightDetector.GetGroundY(p.x, p.z) + Lift;
                    v.Add(p);
                    uv.Add(new Vector2(f * 0.5f + 0.5f, vd[i] / AlongMetres));
                }
            }
            for (int i = 0; i < ring.Count - 1; i++)
            {
                for (int k = 0; k < across - 1; k++)
                {
                    int a = rows[i] + k, b = rows[i] + k + 1, c = rows[i + 1] + k, d = rows[i + 1] + k + 1;
                    List<int> into = surf;   // the soft edge is in the texture's alpha, not in separate strips
                    into.Add(a); into.Add(c); into.Add(b);
                    into.Add(b); into.Add(c); into.Add(d);
                }
            }

            // the dashed centre line of an asphalt road, laid just above the surface
            if (line)
            {
                float lw = 0.08f, on = 3f, off = 3f;
                dist = 0f;
                float cycle = on + off;
                for (int i = 0; i < run.Count - 1; i++)
                {
                    float seg = Flat(run[i], run[i + 1]);
                    float mid = dist + seg * 0.5f;
                    dist += seg;
                    if (Mathf.Repeat(mid, cycle) > on) continue;
                    Vector3 f0 = run[i + 1] - run[i]; f0.y = 0f; f0 = f0.normalized;
                    Vector3 r0 = Vector3.Cross(Vector3.up, f0) * lw;
                    Vector3 a = run[i] - r0, b = run[i] + r0, c = run[i + 1] - r0, d = run[i + 1] + r0;
                    int baseIdx = v.Count;
                    foreach (Vector3 q in new[] { a, b, c, d })
                    {
                        Vector3 w = q;
                        w.y = TerrainHeightDetector.GetGroundY(q.x, q.z) + Lift + 0.015f;
                        v.Add(w);
                        uv.Add(Vector2.zero);
                    }
                    mark.Add(baseIdx); mark.Add(baseIdx + 2); mark.Add(baseIdx + 1);
                    mark.Add(baseIdx + 1); mark.Add(baseIdx + 2); mark.Add(baseIdx + 3);
                }
            }

            Mesh m = _mf.sharedMesh != null ? _mf.sharedMesh : new Mesh { name = "PathRun", hideFlags = HideFlags.DontSave };
            m.Clear();
            m.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            m.SetVertices(v);
            m.SetUVs(0, uv);
            m.subMeshCount = 3;
            m.SetTriangles(surf, 0);
            m.SetTriangles(surf, 1);      // the worn-edge skirt under the surface (same ribbon)
            m.SetTriangles(mark, 2);
            m.RecalculateNormals();
            m.RecalculateBounds();
            _mf.sharedMesh = m;
            _mr.sharedMaterials = new[] { Surface(Style, Width), Skirt(Style, Width), Line() };
        }

        // ------------------------------------------------------------------ materials

        private static Material Lit(string key, Color c, float smooth, Texture2D tex, float tiling)
        {
            if (s_mats.TryGetValue(key, out Material have) && have != null) return have;
            Shader sh = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            var mat = new Material(sh) { name = "Path_" + key, hideFlags = HideFlags.DontSave };
            if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", c);
            mat.color = c;
            if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", smooth);
            if (mat.HasProperty("_Metallic")) mat.SetFloat("_Metallic", 0f);
            if (tex != null)
            {
                mat.mainTexture = tex;
                mat.mainTextureScale = new Vector2(tiling, tiling);
            }
            s_mats[key] = mat;
            return mat;
        }

        private static Color BaseColor(string style)
        {
            switch (style)
            {
                case "dirt": return new Color(0.46f, 0.34f, 0.22f);
                case "stone": return new Color(0.58f, 0.56f, 0.53f);
                case "asphalt": return new Color(0.2f, 0.2f, 0.22f);
                default: return new Color(0.62f, 0.59f, 0.53f);   // gravel
            }
        }

        private static Material Surface(string style, float width)
        {
            string key = style + "_" + width.ToString("F2");
            if (s_mats.TryGetValue("surface_" + key, out Material have) && have != null) return have;
            Shader path = Shader.Find("Homesteader/PathSurface");
            if (path != null)
            {
                // The ribbon only gives the soft edge (alpha); the colour is made from the place in the WORLD, so two routes of one kind that cross
                // or join show one continuous surface (see PathSurface.shader).
                var m = new Material(path) { name = "Path_surface_" + key, hideFlags = HideFlags.DontSave };
                m.SetTexture("_BaseMap", EdgeTexture(style, width, false));
                m.SetColor("_BaseColor", BaseColor(style));
                m.SetFloat("_GrainAmt", 1f);
                m.SetFloat("_Flags", style == "stone" ? 1f : 0f);
                m.renderQueue = 2999;
                s_mats["surface_" + key] = m;
                return m;
            }
            float smooth = style == "asphalt" ? 0.35f : style == "stone" ? 0.25f : 0.05f;
            Material mat = Lit("surface_" + key, Color.white, smooth, EdgeTexture(style, width, false), 1f);
            // (fallback, no path shader) blended: the ragged edge fades out over the ground (transparent URP Lit)
            mat.SetFloat("_Surface", 1f);
            mat.SetFloat("_Blend", 0f);
            mat.SetOverrideTag("RenderType", "Transparent");
            mat.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
            mat.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            mat.SetFloat("_ZWrite", 0f);
            mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            mat.DisableKeyword("_ALPHATEST_ON");
            mat.renderQueue = 2999;
            mat.SetShaderPassEnabled("DepthOnly", false);
            return mat;
        }

        /// <summary>
        /// The darker worn edge: a skirt of soil colour under the surface, drawn BEFORE any surface (queue 2998), so the soft edge of a route shows
        /// a scuffed rim on the open ground, while wherever another route's surface lies over it (a crossing, a junction) that surface is drawn on
        /// top and hides it: no dark line across the other route.
        /// </summary>
        private static Material Skirt(string style, float width)
        {
            string key = "skirt_" + style + "_" + width.ToString("F2");
            if (s_mats.TryGetValue(key, out Material have) && have != null) return have;
            Shader path = Shader.Find("Homesteader/PathSurface");
            Color soil = style == "asphalt" ? new Color(0.3f, 0.29f, 0.28f) : new Color(0.34f, 0.28f, 0.19f);
            Material m;
            if (path != null)
            {
                m = new Material(path) { name = "Path_" + key, hideFlags = HideFlags.DontSave };
                m.SetTexture("_BaseMap", EdgeTexture(style, width, true));
                m.SetColor("_BaseColor", soil);
                m.SetFloat("_GrainAmt", 0.5f);
                m.SetFloat("_Flags", 0f);
            }
            else
            {
                m = Lit(key, soil, 0.05f, EdgeTexture(style, width, true), 1f);
                m.SetFloat("_Surface", 1f);
                m.SetOverrideTag("RenderType", "Transparent");
                m.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
                m.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                m.SetFloat("_ZWrite", 0f);
                m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                m.SetShaderPassEnabled("DepthOnly", false);
            }
            m.renderQueue = 2998;
            s_mats[key] = m;
            return m;
        }

        private static Material Line() { return Lit("line", new Color(0.95f, 0.8f, 0.2f), 0.2f, null, 1f); }

        private static readonly Dictionary<string, Texture2D> s_tex = new Dictionary<string, Texture2D>();

        private static float Hash(int x, int y)
        {
            float h = Mathf.Sin(x * 127.1f + y * 311.7f) * 43758.5453f;
            return h - Mathf.Floor(h);
        }

        /// <summary>Value noise 0..1 on a lattice of cells; it wraps every <paramref name="periodY"/> cells in y, so the texture tiles along the route.</summary>
        private static float ValueNoise(float x, float y, int periodY)
        {
            int ix = Mathf.FloorToInt(x), iy = Mathf.FloorToInt(y);
            float fx = x - ix, fy = y - iy;
            fx = fx * fx * (3f - 2f * fx);
            fy = fy * fy * (3f - 2f * fy);
            int y0 = ((iy % periodY) + periodY) % periodY, y1 = (y0 + 1) % periodY;
            float a = Mathf.Lerp(Hash(ix, y0), Hash(ix + 1, y0), fx);
            float b = Mathf.Lerp(Hash(ix, y1), Hash(ix + 1, y1), fx);
            return Mathf.Lerp(a, b, fy);
        }

        /// <summary>The width left at distance t (0..1 of the cap's length) from the end of the route: a half circle, never quite closed.</summary>
        private static float CapWidth(float t) { return Mathf.Max(0.12f, Mathf.Sqrt(Mathf.Max(0f, 1f - Mathf.Min(1f, t) * Mathf.Min(1f, t)))); }

        private static float Smooth(float t) { t = Mathf.Clamp01(t); return t * t * (3f - 2f * t); }

        /// <summary>
        /// The surface of one style at one width, with the edge done the way the starter road's mask does it: the width drifts slowly along the route,
        /// the edge is ragged and soft (worn ground, not a painted line), and a scuffed shoulder runs into the verge. Alpha is the coverage.
        /// </summary>
        private static Texture2D EdgeTexture(string style, float width, bool skirt)
        {
            string key = style + "_" + width.ToString("F2") + (skirt ? "_skirt" : "_b");
            if (s_tex.TryGetValue(key, out Texture2D have) && have != null) return have;
            const float PxM = 0.03125f;
            float total = width + Fade * 2f;
            int W = Mathf.Clamp(Mathf.RoundToInt(total / PxM), 16, 256);
            const int H = 512;   // AlongMetres / PxM
            var tex = new Texture2D(W, H, TextureFormat.RGBA32, true) { name = "PathTex_" + key, wrapMode = TextureWrapMode.Repeat, hideFlags = HideFlags.DontSave };
            tex.wrapModeU = TextureWrapMode.Clamp;
            var rnd = new System.Random(key.GetHashCode());
            Color baseC = BaseColor(style);
            Color soil = style == "asphalt" ? new Color(0.3f, 0.29f, 0.28f) : new Color(0.34f, 0.28f, 0.19f);
            bool flags = style == "stone";
            var px = new Color[W * H];
            for (int y = 0; y < H; y++)
            {
                float drift = 0.95f + 0.1f * ValueNoise(0.5f, y / 64f, 8);
                float hw = width * 0.5f * drift;
                for (int x = 0; x < W; x++)
                {
                    float d = Mathf.Abs((x + 0.5f) / W - 0.5f) * total;
                    float ragged = (ValueNoise(x / 16f, y / 32f, H / 32) - 0.5f) * 0.14f;
                    float edge = d + ragged;
                    float coverage = 1f - Smooth(Mathf.InverseLerp(hw - 0.35f, hw + 0.5f, edge));
                    if (skirt) coverage = (1f - Smooth(Mathf.InverseLerp(hw - 0.05f, hw + 0.5f, edge))) * 0.85f;   // opaque a little past the surface's solid part, fading out with it
                    var c = new Color(Mathf.Clamp01(baseC.r), Mathf.Clamp01(baseC.g), Mathf.Clamp01(baseC.b), 1f);   // (the path shader takes its colour from the world, only alpha is used)
                    // A faint scuff only: the edge fades out by ALPHA, so where two routes cross or join the edge of the top one fades into the other's
                    // surface and vanishes (a strong dark shoulder showed as a line across the route underneath).
                    float shoulder = Smooth(Mathf.InverseLerp(hw - 0.7f, hw + 0.1f, edge)) * (style == "asphalt" ? 0.08f : 0.14f);
                    c = Color.Lerp(c, soil, shoulder);
                    c.a = coverage;
                    px[y * W + x] = c;
                }
            }
            tex.SetPixels(px);
            tex.Apply(true);
            s_tex[key] = tex;
            return tex;
        }
    }
}
