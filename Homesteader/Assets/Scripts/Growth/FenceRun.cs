using System;
using System.Collections.Generic;
using Homesteader.Generation;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// One fence the player built: a run of posts (a closed loop or an open line) with the fencing filled in between them, and any gates set
    /// into it. Built by FenceBuilder. The geometry is procedural (posts and rails or wires follow the ground, one mesh per run); colliders sit
    /// on the Ignore Raycast layer, so they stop the player and the animals but the mouse still sees straight through to the ground.
    /// The style and sizes come from the fence item's manifest (fence_style, fence_panel_m, fence_height_m); gates from the gate item
    /// (gate_width_m). Saved with the game (GameSave.fences).
    /// </summary>
    public sealed class FenceRun : MonoBehaviour
    {
        public static readonly List<FenceRun> All = new List<FenceRun>();

        [Serializable]
        public class Gate
        {
            public int Segment;        // which post-to-post segment
            public float S;            // metres from the segment's first post to the middle of the gate
            public float Width = 1.2f;
            public string ItemId;      // the gate item (gate_wood, gate_metal)
            public string Style = "wood";
            public bool Open;
            [NonSerialized] public Transform Pivot;
            [NonSerialized] public BoxCollider Collider;
            [NonSerialized] public float Angle;
            [NonSerialized] public float OpenSign = 1f;
        }

        public string Style = "wood";               // wood or wire
        public string PanelItemId, PostItemId;
        public float PanelLength = 2.4f, Height = 1.2f;
        public bool Closed;
        public int Limit = int.MaxValue;            // how many panels of the run are built so far (all of them for a finished fence)
        public readonly List<Vector3> Posts = new List<Vector3>();
        public readonly List<Gate> Gates = new List<Gate>();

        private const int IgnoreRaycastLayer = 2;
        private const float GateOpenDegrees = 100f;
        private MeshFilter _mf;
        private readonly List<GameObject> _colliderHolders = new List<GameObject>();
        private readonly List<GameObject> _gateObjects = new List<GameObject>();
        private static Material s_post, s_rail, s_wire, s_gate;

        private void OnEnable() { All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        public static FenceRun Create(string style, string panelItem, string postItem, float panelLength, float height, List<Vector3> posts, bool closed, List<Gate> gates)
        {
            var go = new GameObject("Fence_" + style);
            var run = go.AddComponent<FenceRun>();
            run.Style = style;
            run.PanelItemId = panelItem;
            run.PostItemId = postItem;
            run.PanelLength = Mathf.Max(0.5f, panelLength);
            run.Height = Mathf.Max(0.5f, height);
            run.Closed = closed;
            run.Posts.AddRange(posts);
            if (gates != null) run.Gates.AddRange(gates);
            run.Rebuild();
            return run;
        }

        public static void Clear()
        {
            foreach (FenceRun f in new List<FenceRun>(All)) if (f != null) Destroy(f.gameObject);
            All.Clear();
        }

        // ------------------------------------------------------------------ geometry helpers

        public int SegmentCount => Mathf.Max(0, Closed ? Posts.Count : Posts.Count - 1);

        public void SegmentEnds(int i, out Vector3 a, out Vector3 b)
        {
            a = Posts[i];
            b = Posts[(i + 1) % Posts.Count];
        }

        private static float GroundY(float x, float z) { return TerrainHeightDetector.GetGroundY(x, z); }

        private Vector3 PointOn(Vector3 a, Vector3 b, float s, float len)
        {
            float t = len > 0.0001f ? s / len : 0f;
            float x = Mathf.Lerp(a.x, b.x, t), z = Mathf.Lerp(a.z, b.z, t);
            return new Vector3(x, GroundY(x, z), z);
        }

        public static float Flat(Vector3 a, Vector3 b) { return new Vector2(b.x - a.x, b.z - a.z).magnitude; }

        /// <summary>How many panels (and so how many intermediate posts + 1 per segment) a run of these posts needs.</summary>
        public static void Needs(List<Vector3> posts, bool closed, float panelLength, out int postCount, out int panelCount)
        {
            panelCount = 0;
            postCount = posts.Count;
            int segs = closed ? posts.Count : posts.Count - 1;
            for (int i = 0; i < segs; i++)
            {
                float len = Flat(posts[i], posts[(i + 1) % posts.Count]);
                int np = Mathf.Max(1, Mathf.CeilToInt(len / Mathf.Max(0.5f, panelLength) - 0.001f));
                panelCount += np;
                postCount += np - 1;
            }
        }

        /// <summary>The two ends of the n-th panel of the run, in order along it (false past the last one).</summary>
        public bool PanelEnds(int index, out Vector3 a, out Vector3 b)
        {
            a = b = default;
            int n = 0;
            for (int seg = 0; seg < SegmentCount; seg++)
            {
                SegmentEnds(seg, out Vector3 sa, out Vector3 sb);
                float len = Flat(sa, sb);
                if (len < 0.05f) continue;
                int np = Mathf.Max(1, Mathf.CeilToInt(len / PanelLength - 0.001f));
                if (index < n + np)
                {
                    int pn = index - n;
                    a = PointOn(sa, sb, len * pn / np, len);
                    b = PointOn(sa, sb, len * (pn + 1) / np, len);
                    return true;
                }
                n += np;
            }
            return false;
        }

        /// <summary>Which post-to-post segment a ray passes closest to (within maxDistance of it), the metres along it, and the point.</summary>
        public bool NearestSegment(Ray ray, float maxDistance, out int segment, out float s, out float distance)
        {
            segment = -1; s = 0f; distance = float.MaxValue;
            for (int i = 0; i < SegmentCount; i++)
            {
                SegmentEnds(i, out Vector3 a, out Vector3 b);
                a.y = GroundY(a.x, a.z) + Height * 0.5f;
                b.y = GroundY(b.x, b.z) + Height * 0.5f;
                float d = RaySegmentDistance(ray, a, b, out float t);
                if (d < distance && d <= maxDistance) { distance = d; segment = i; s = t * Flat(a, b); }
            }
            return segment >= 0;
        }

        private static float RaySegmentDistance(Ray ray, Vector3 a, Vector3 b, out float t)
        {
            // closest points between the ray and the segment a-b
            Vector3 u = ray.direction, v = b - a, w0 = ray.origin - a;
            float aa = Vector3.Dot(u, u), bb = Vector3.Dot(u, v), cc = Vector3.Dot(v, v), dd = Vector3.Dot(u, w0), ee = Vector3.Dot(v, w0);
            float denom = aa * cc - bb * bb;
            float tc = denom < 1e-6f ? 0f : Mathf.Clamp01((aa * ee - bb * dd) / denom);
            Vector3 onSeg = a + v * tc;
            float sc = Mathf.Max(0f, Vector3.Dot(onSeg - ray.origin, u) / aa);
            t = tc;
            return Vector3.Distance(ray.origin + u * sc, onSeg);
        }

        // ------------------------------------------------------------------ building the mesh

        private sealed class MeshBuild
        {
            public readonly List<Vector3> V = new List<Vector3>();
            public readonly List<int> PostTris = new List<int>(), RailTris = new List<int>(), WireTris = new List<int>();

            public void Box(List<int> tris, Vector3 center, Quaternion rot, Vector3 size)
            {
                int b = V.Count;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 c = new Vector3((i & 1) == 0 ? -0.5f : 0.5f, (i & 2) == 0 ? -0.5f : 0.5f, (i & 4) == 0 ? -0.5f : 0.5f);
                    V.Add(center + rot * Vector3.Scale(c, size));
                }
                int[] f = { 0, 2, 3, 0, 3, 1, 4, 5, 7, 4, 7, 6, 0, 1, 5, 0, 5, 4, 2, 6, 7, 2, 7, 3, 0, 4, 6, 0, 6, 2, 1, 3, 7, 1, 7, 5 };
                foreach (int k in f) tris.Add(b + k);
            }
        }

        public void Rebuild()
        {
            foreach (GameObject g in _colliderHolders) if (g != null) Destroy(g);
            foreach (GameObject g in _gateObjects) if (g != null) Destroy(g);
            _colliderHolders.Clear();
            _gateObjects.Clear();
            if (Posts.Count < 2) return;

            var mb = new MeshBuild();
            bool wire = Style == "wire";
            float postH = Height + (wire ? 0.2f : 0.15f);
            Vector3 postSize = wire ? new Vector3(0.06f, postH, 0.06f) : new Vector3(0.14f, postH, 0.14f);
            float[] rails = wire ? new[] { 0.2f, 0.45f, 0.7f, 0.95f, Height - 0.05f } : new[] { 0.3f, 0.65f, Height - 0.08f };
            Vector3 railSize = wire ? new Vector3(0.012f, 0.012f, 1f) : new Vector3(0.04f, 0.1f, 1f);
            List<int> railTris = wire ? mb.WireTris : mb.RailTris;
            var postSpots = new List<Vector3>();
            int panelNo = 0;

            for (int seg = 0; seg < SegmentCount; seg++)
            {
                SegmentEnds(seg, out Vector3 a, out Vector3 b);
                float len = Flat(a, b);
                if (len < 0.05f) continue;
                int np = Mathf.Max(1, Mathf.CeilToInt(len / PanelLength - 0.001f));
                // the gate gaps on this segment, as [s0, s1] metres
                var gaps = new List<Vector2>();
                foreach (Gate g in Gates)
                    if (g.Segment == seg) gaps.Add(new Vector2(Mathf.Clamp(g.S - g.Width * 0.5f, 0f, len), Mathf.Clamp(g.S + g.Width * 0.5f, 0f, len)));
                gaps.Sort((p, q) => p.x.CompareTo(q.x));

                // panel by panel: only the first Limit panels of the whole run exist (the builder raises it as the ped finishes each section)
                int firstPanel = panelNo;
                panelNo += np;
                for (int pn = 0; pn < np; pn++)
                {
                    int g = firstPanel + pn;
                    bool built = g < Limit;
                    float ps0 = len * pn / np, ps1 = len * (pn + 1) / np;
                    // the post at the start of a panel stands once the panel before it is built (the very first post always does)
                    if ((g == 0 || g <= Limit) && (pn == 0 || !InGap(gaps, ps0))) postSpots.Add(PointOn(a, b, ps0, len));
                    if (!Closed && seg == SegmentCount - 1 && pn == np - 1 && built) postSpots.Add(PointOn(a, b, ps1, len));   // the last post of an open line
                    if (!built) continue;

                    // the fencing of this panel, in pieces that stop at the gate gaps (each piece also gets a collider)
                    var cuts = new List<float> { ps0 };
                    foreach (Vector2 gp in gaps)
                        if (gp.y > ps0 && gp.x < ps1) { cuts.Add(Mathf.Max(gp.x, ps0)); cuts.Add(Mathf.Min(gp.y, ps1)); }
                    cuts.Add(ps1);
                    for (int c = 0; c < cuts.Count; c += 2)
                    {
                        float s0 = cuts[c], s1 = cuts[c + 1];
                        if (s1 - s0 < 0.05f) continue;
                        int pieces = Mathf.Max(1, Mathf.CeilToInt((s1 - s0) / 1.2f));
                        for (int pc = 0; pc < pieces; pc++)
                        {
                            float qs0 = Mathf.Lerp(s0, s1, (float)pc / pieces), qs1 = Mathf.Lerp(s0, s1, (float)(pc + 1) / pieces);
                            Vector3 p0 = PointOn(a, b, qs0, len), p1 = PointOn(a, b, qs1, len);
                            foreach (float h in rails)
                            {
                                Vector3 q0 = p0 + Vector3.up * h, q1 = p1 + Vector3.up * h;
                                Vector3 dir = q1 - q0;
                                if (dir.sqrMagnitude < 1e-6f) continue;
                                Quaternion rot = Quaternion.LookRotation(dir.normalized, Vector3.up);
                                mb.Box(railTris, (q0 + q1) * 0.5f, rot, new Vector3(railSize.x, railSize.y, dir.magnitude + 0.02f));
                            }
                        }
                        AddCollider(PointOn(a, b, s0, len), PointOn(a, b, s1, len));
                    }
                }
                foreach (Vector2 gp in gaps) { postSpots.Add(PointOn(a, b, gp.x, len)); postSpots.Add(PointOn(a, b, gp.y, len)); }   // a gate's hinge and latch posts
            }

            foreach (Vector3 spot in postSpots)
                mb.Box(mb.PostTris, spot + Vector3.up * (postH * 0.5f - 0.05f), Quaternion.identity, postSize);

            var mesh = new Mesh { name = "FenceRun", indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            mesh.SetVertices(mb.V);
            mesh.subMeshCount = 3;
            mesh.SetTriangles(mb.PostTris, 0);
            mesh.SetTriangles(mb.RailTris, 1);
            mesh.SetTriangles(mb.WireTris, 2);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            if (_mf == null)
            {
                // (not "?? AddComponent": a Unity object that is missing is not a C# null, so ?? would never add it)
                _mf = gameObject.GetComponent<MeshFilter>();
                if (_mf == null) _mf = gameObject.AddComponent<MeshFilter>();
                if (gameObject.GetComponent<MeshRenderer>() == null) gameObject.AddComponent<MeshRenderer>();
            }
            if (_mf.sharedMesh != null) Destroy(_mf.sharedMesh);
            _mf.sharedMesh = mesh;
            var mr = GetComponent<MeshRenderer>();
            mr.sharedMaterials = new[] { Mat(ref s_post, new Color(0.45f, 0.32f, 0.2f), 0.2f), Mat(ref s_rail, new Color(0.62f, 0.47f, 0.3f), 0.2f), Mat(ref s_wire, new Color(0.55f, 0.57f, 0.6f), 0.7f) };
            if (wire) mr.sharedMaterials = new[] { Mat(ref s_wire, new Color(0.4f, 0.42f, 0.45f), 0.6f), Mat(ref s_rail, new Color(0.62f, 0.47f, 0.3f), 0.2f), Mat(ref s_wire, new Color(0.7f, 0.72f, 0.75f), 0.7f) };
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;

            foreach (Gate g in Gates) BuildGate(g);
        }

        private static bool InGap(List<Vector2> gaps, float s)
        {
            foreach (Vector2 g in gaps) if (s > g.x - 0.02f && s < g.y + 0.02f) return true;
            return false;
        }

        private void AddCollider(Vector3 p0, Vector3 p1)
        {
            Vector3 mid = (p0 + p1) * 0.5f + Vector3.up * (Height * 0.5f);
            Vector3 dir = p1 - p0;
            if (dir.sqrMagnitude < 1e-6f) return;
            var holder = new GameObject("FenceCollider");
            holder.layer = IgnoreRaycastLayer;   // stops bodies, invisible to the mouse raycasts
            holder.transform.SetParent(transform, false);
            holder.transform.position = mid;
            holder.transform.rotation = Quaternion.LookRotation(new Vector3(dir.x, 0f, dir.z).normalized, Vector3.up);
            var box = holder.AddComponent<BoxCollider>();
            box.size = new Vector3(0.14f, Height + Mathf.Abs(dir.y), dir.magnitude);
            _colliderHolders.Add(holder);
        }

        private static Material Mat(ref Material slot, Color c, float smoothness)
        {
            if (slot != null) return slot;
            Shader sh = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            slot = new Material(sh) { name = "Fence", hideFlags = HideFlags.DontSave };
            if (slot.HasProperty("_BaseColor")) slot.SetColor("_BaseColor", c);
            slot.color = c;
            if (slot.HasProperty("_Smoothness")) slot.SetFloat("_Smoothness", smoothness);
            return slot;
        }

        // ------------------------------------------------------------------ gates

        private void BuildGate(Gate g)
        {
            SegmentEnds(g.Segment, out Vector3 a, out Vector3 b);
            float len = Flat(a, b);
            if (len < 0.05f) return;
            float s0 = Mathf.Clamp(g.S - g.Width * 0.5f, 0f, len), s1 = Mathf.Clamp(g.S + g.Width * 0.5f, 0f, len);
            Vector3 hinge = PointOn(a, b, s0, len), latch = PointOn(a, b, s1, len);
            Vector3 dir = new Vector3(latch.x - hinge.x, 0f, latch.z - hinge.z);
            float w = dir.magnitude;
            if (w < 0.05f) return;

            var root = new GameObject("Gate");
            root.transform.SetParent(transform, false);
            root.transform.position = hinge;
            root.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);   // local +Z runs along the gate
            var leaf = new GameObject("Leaf");
            leaf.transform.SetParent(root.transform, false);
            g.Pivot = leaf.transform;

            // a rectangular frame, a diagonal brace and (for the metal gate) bars, all one mesh
            bool metal = g.Style == "metal";
            Color col = metal ? new Color(0.35f, 0.37f, 0.4f) : new Color(0.6f, 0.45f, 0.28f);
            var mb = new MeshBuild();
            float h = Height - 0.1f;
            Vector3 t = new Vector3(0.05f, 0.1f, 0.05f);
            mb.Box(mb.RailTris, new Vector3(0f, 0.15f, w * 0.5f), Quaternion.identity, new Vector3(0.05f, 0.1f, w));
            mb.Box(mb.RailTris, new Vector3(0f, h * 0.5f, w * 0.5f), Quaternion.identity, new Vector3(0.05f, 0.1f, w));
            mb.Box(mb.RailTris, new Vector3(0f, h, w * 0.5f), Quaternion.identity, new Vector3(0.05f, 0.1f, w));
            mb.Box(mb.RailTris, new Vector3(0f, h * 0.5f + 0.05f, 0.04f), Quaternion.identity, new Vector3(0.05f, h, 0.08f));
            mb.Box(mb.RailTris, new Vector3(0f, h * 0.5f + 0.05f, w - 0.04f), Quaternion.identity, new Vector3(0.05f, h, 0.08f));
            float diag = Mathf.Sqrt(w * w + h * h);
            mb.Box(mb.RailTris, new Vector3(0f, h * 0.5f + 0.1f, w * 0.5f), Quaternion.Euler(-Mathf.Atan2(h, w) * Mathf.Rad2Deg, 0f, 0f), new Vector3(0.04f, 0.08f, diag * 0.92f));
            if (metal)
                for (int k = 1; k < 6; k++)
                    mb.Box(mb.RailTris, new Vector3(0f, h * 0.5f + 0.05f, w * k / 6f), Quaternion.identity, new Vector3(0.025f, h, 0.025f));
            var mesh = new Mesh { name = "Gate" };
            mesh.SetVertices(mb.V);
            mesh.SetTriangles(mb.RailTris, 0);
            mesh.RecalculateNormals();
            leaf.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = leaf.AddComponent<MeshRenderer>();
            var gateMat = new Material(Mat(ref s_gate, col, 0.25f)) { name = "Gate" };   // its own, so a wood and a metal gate keep their colours
            if (gateMat.HasProperty("_BaseColor")) gateMat.SetColor("_BaseColor", col);
            gateMat.color = col;
            mr.sharedMaterial = gateMat;

            var colHolder = new GameObject("GateCollider");
            colHolder.layer = IgnoreRaycastLayer;
            colHolder.transform.SetParent(leaf.transform, false);
            colHolder.transform.localPosition = new Vector3(0f, h * 0.5f + 0.05f, w * 0.5f);
            g.Collider = colHolder.AddComponent<BoxCollider>();
            g.Collider.size = new Vector3(0.14f, h + 0.1f, w);
            g.Collider.enabled = !g.Open;
            g.Angle = g.Open ? GateOpenDegrees : 0f;
            leaf.transform.localRotation = Quaternion.Euler(0f, -g.OpenSign * g.Angle, 0f);
            _gateObjects.Add(root);
        }

        /// <summary>The gate whose leaf is nearest to a point, if one is within maxDistance.</summary>
        public Gate NearestGate(Vector3 point, float maxDistance)
        {
            Gate best = null;
            float bestD = maxDistance;
            foreach (Gate g in Gates)
            {
                SegmentEnds(g.Segment, out Vector3 a, out Vector3 b);
                float len = Flat(a, b);
                Vector3 mid = PointOn(a, b, g.S, len);
                float d = new Vector2(mid.x - point.x, mid.z - point.z).magnitude;
                if (d < bestD) { bestD = d; best = g; }
            }
            return best;
        }

        public void ToggleGate(Gate g, Vector3 from)
        {
            if (g == null || g.Pivot == null) return;
            g.Open = !g.Open;
            // opening swings away from whoever works it; closing swings back the same way (the side is not re-picked, or the leaf would jump across first)
            if (g.Open)
            {
                SegmentEnds(g.Segment, out Vector3 a, out Vector3 b);
                Vector3 along = (b - a); along.y = 0f; along.Normalize();
                Vector3 mid = PointOn(a, b, g.S, Flat(a, b));
                Vector3 side = Vector3.Cross(Vector3.up, along);
                g.OpenSign = Vector3.Dot(from - mid, side) > 0f ? 1f : -1f;
            }
            if (g.Collider != null) g.Collider.enabled = !g.Open;
        }

        private void Update()
        {
            foreach (Gate g in Gates)
            {
                if (g.Pivot == null) continue;
                float target = g.Open ? GateOpenDegrees : 0f;
                if (!Mathf.Approximately(g.Angle, target))
                {
                    g.Angle = Mathf.MoveTowards(g.Angle, target, 220f * Time.deltaTime);
                    g.Pivot.localRotation = Quaternion.Euler(0f, -g.OpenSign * g.Angle, 0f);
                    if (g.Collider != null) g.Collider.enabled = !g.Open && g.Angle <= 0.5f;   // solid again only once it is shut
                }
            }
        }

        /// <summary>
        /// A right click with an axe on a post (or, anywhere = true, with wire cutters anywhere along a wire fence): takes down the post-to-post section nearest the cursor (with any gate in it). A closed loop becomes an open
        /// run; an open run splits in two at the gap. Runs left with fewer than two posts go. Returns false when the ray is not on a post.
        /// </summary>
        public bool ChopSectionAt(Ray ray, bool anywhere = false)
        {
            if (Limit != int.MaxValue) return false;   // still being built
            if (!NearestSegment(ray, 0.4f, out int seg, out float s, out float d)) return false;
            SegmentEnds(seg, out Vector3 a, out Vector3 b);
            float len = Flat(a, b);
            if (len < 0.05f) return false;
            int np = Mathf.Max(1, Mathf.CeilToInt(len / PanelLength - 0.001f));
            float step = len / np;
            float off = Mathf.Abs(s - Mathf.Round(s / step) * step);
            if (!anywhere && off > 0.45f) return false;   // on the fencing, not on a post (wire cutters cut anywhere along the wire)

            int n = Posts.Count;
            var left = new List<Vector3>();
            var leftGates = new List<Gate>();
            List<Vector3> right = null;
            var rightGates = new List<Gate>();
            if (Closed)
            {
                // the loop opens at the removed section: start at the post after it and go all the way round
                for (int k = 0; k < n; k++) left.Add(Posts[(seg + 1 + k) % n]);
                foreach (Gate g in Gates)
                {
                    if (g.Segment == seg) continue;
                    g.Segment = (g.Segment - (seg + 1) + n) % n;
                    leftGates.Add(g);
                }
                Closed = false;
            }
            else
            {
                for (int k = 0; k <= seg; k++) left.Add(Posts[k]);
                right = new List<Vector3>();
                for (int k = seg + 1; k < n; k++) right.Add(Posts[k]);
                foreach (Gate g in Gates)
                {
                    if (g.Segment < seg) leftGates.Add(g);
                    else if (g.Segment > seg) { g.Segment -= seg + 1; rightGates.Add(g); }
                }
            }

            if (right != null && right.Count >= 2) Create(Style, PanelItemId, PostItemId, PanelLength, Height, right, false, rightGates);
            Posts.Clear();
            Posts.AddRange(left);
            Gates.Clear();
            Gates.AddRange(leftGates);
            if (Posts.Count < 2) { Destroy(gameObject); return true; }
            Rebuild();
            return true;
        }

        public void AddGate(Gate g)
        {
            Gates.Add(g);
            Rebuild();
        }

        /// <summary>True when a point (ground plane) lies inside a closed fence.</summary>
        public bool Encloses(Vector3 p)
        {
            if (!Closed || Posts.Count < 3) return false;
            bool inside = false;
            for (int i = 0, j = Posts.Count - 1; i < Posts.Count; j = i++)
            {
                Vector3 a = Posts[i], b = Posts[j];
                if ((a.z > p.z) != (b.z > p.z) && p.x < (b.x - a.x) * (p.z - a.z) / (b.z - a.z) + a.x) inside = !inside;
            }
            return inside;
        }
    }
}
