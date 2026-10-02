using System.Collections.Generic;
using UnityEngine;
using Homesteader.Generation;

namespace Homesteader.World
{
    /// <summary>
    /// Procedural wooden bridges where a road crosses water. Finds every stretch of the road centreline
    /// (HomesteaderTerrainGenerator.RoadPoints) that is over water, and builds a plank deck with stringers, posts,
    /// rails and piles across it, in code, flat shaded like the rest of the procedural world (Homesteader/Vegetation
    /// shader, so it takes snow and rain). The deck and rails have colliders so the player walks over the water.
    /// Deterministic from the road and the seed, so nothing is saved. See docs/PROCEDURAL_VEGETATION.md.
    /// </summary>
    public static class ProceduralBridge
    {
        public sealed class BridgeInfo
        {
            public Vector3 Start;       // world, on the dry bank
            public Vector3 End;
            public float Length;
            public float Width;
        }

        /// <summary>Every bridge built for the current world (cleared on each generation).</summary>
        public static readonly List<BridgeInfo> Bridges = new List<BridgeInfo>();

        private const string RootName = "RoadBridges";
        private const float MinSpan = 4f;           // shorter than this is not worth a bridge
        private const float MaxSpan = 60f;
        private const float PlankPitch = 0.5f;
        private const float RailHeight = 0.9f;

        /// <summary>Builds a bridge over each water crossing of the road. Returns how many.</summary>
        public static int Generate(HomesteaderTerrainGenerator gen)
        {
            Bridges.Clear();
            Transform old = gen.transform.Find(RootName);
            if (old != null) Object.DestroyImmediate(old.gameObject);

            Terrain terrain = gen.GetComponent<Terrain>();
            IReadOnlyList<Vector2> pts = gen.RoadPoints;
            if (terrain == null || pts == null || pts.Count < 8) return 0;

            var rule = Homesteader.Growth.GameRules.StarterRoad;
            float width = Mathf.Clamp(rule.WidthM, 2.4f, 5f);

            var root = new GameObject(RootName).transform;
            root.SetParent(gen.transform, false);

            // Find the water crossings: runs of road points on water or right at a bank.
            int count = pts.Count;
            var wet = new bool[count];
            for (int i = 0; i < count; i++)
                wet[i] = gen.IsWaterAt(pts[i].x, pts[i].y) || gen.GetWaterDistance(pts[i].x, pts[i].y) < 1.3f;

            var spans = new List<Vector2Int>();
            int k = 0;
            while (k < count)
            {
                if (!wet[k]) { k++; continue; }
                int a = k;
                int b = k;
                int gap = 0;
                for (int j = k; j < count; j++)
                {
                    if (wet[j]) { b = j; gap = 0; }
                    else if (++gap > 6) break;   // a few dry points between two wet stretches is still one crossing
                }
                spans.Add(new Vector2Int(a, b));
                k = b + 1;
            }

            int built = 0;
            var rng = new System.Random(gen.worldSeed * 92821 + 5);
            foreach (Vector2Int span in spans)
            {
                // Abutments on dry ground: a little past the water at both ends.
                int a = Mathf.Max(span.x - 3, 0), b = Mathf.Min(span.y + 3, count - 1);
                if (a <= 0 || b >= count - 1) continue;     // the road starts or ends in water: nothing sensible to span
                Vector2 p0 = pts[a], p1 = pts[b];
                float length = Vector2.Distance(p0, p1);
                if (length < MinSpan || length > MaxSpan) continue;

                BuildBridge(gen, terrain, root, p0, p1, width, rng);
                built++;
            }

            if (built == 0) Object.DestroyImmediate(root.gameObject);
            return built;
        }

        /// <summary>Builds one bridge between two dry-bank points (terrain coordinates), whatever is between them. Also the
        /// entry point for bridges that are not on the generated road.</summary>
        public static void BuildAcross(HomesteaderTerrainGenerator gen, Vector2 from, Vector2 to, float width = 3.4f)
        {
            Terrain terrain = gen.GetComponent<Terrain>();
            if (terrain == null) return;
            Transform root = gen.transform.Find(RootName);
            if (root == null)
            {
                root = new GameObject(RootName).transform;
                root.SetParent(gen.transform, false);
            }
            BuildBridge(gen, terrain, root, from, to, width, new System.Random(gen.worldSeed + 77));
        }

        // ------------------------------------------------------------------ one bridge

        private static void BuildBridge(HomesteaderTerrainGenerator gen, Terrain terrain, Transform root, Vector2 p0, Vector2 p1, float width, System.Random rng)
        {
            float originY = gen.transform.position.y;
            float waterY = originY + 14f + HomesteaderTerrainGenerator.WaterLevel;   // world height of the water surface
            float GroundAt(float x, float z) => terrain.SampleHeight(new Vector3(x, 0f, z)) + originY;

            Vector2 dir2 = (p1 - p0).normalized;
            Vector3 dir = new Vector3(dir2.x, 0f, dir2.y);
            Vector3 right = Vector3.Cross(Vector3.up, dir).normalized;
            float length = Vector2.Distance(p0, p1);

            float y0 = GroundAt(p0.x, p0.y) + 0.06f;
            float y1 = GroundAt(p1.x, p1.y) + 0.06f;
            // Sit clear of the water, with a gentle arch so it reads as a bridge rather than a plank on the ground.
            float clearance = Mathf.Max(0f, waterY + 0.85f - Mathf.Lerp(y0, y1, 0.5f));
            float arch = 0.22f + clearance;

            Vector3 DeckPoint(float s)
            {
                float t = Mathf.Clamp01(s / length);
                float y = Mathf.Lerp(y0, y1, t) + Mathf.Sin(t * Mathf.PI) * arch;
                return new Vector3(p0.x + dir.x * s, y, p0.y + dir.z * s);
            }
            Vector3 Tangent(float s)
            {
                Vector3 d = (DeckPoint(Mathf.Min(s + 0.3f, length)) - DeckPoint(Mathf.Max(s - 0.3f, 0f))).normalized;
                return d;
            }

            var m = new BoxMesher();
            const int Plank0 = 0, Plank1 = 1, Plank2 = 2, Beam = 3, Rail = 4, Pile = 5;
            float half = width * 0.5f;

            // Planks across the deck.
            int planks = Mathf.CeilToInt(length / PlankPitch);
            float pitch = length / planks;
            for (int i = 0; i < planks; i++)
            {
                float s = (i + 0.5f) * pitch;
                Vector3 c = DeckPoint(s);
                Vector3 f = Tangent(s);
                Vector3 u = Vector3.Cross(f, right).normalized;
                float wobble = ((float)rng.NextDouble() - 0.5f) * 0.03f;
                float w = half + 0.02f + (float)rng.NextDouble() * 0.06f;
                m.Box(c - u * 0.07f + u * wobble, right, u, f, new Vector3(w, 0.07f, pitch * 0.5f - 0.014f), rng.Next(3) == 0 ? Plank2 : (rng.Next(2) == 0 ? Plank0 : Plank1));
            }

            // Stringers under the deck (three beams) and cross beams at both abutments.
            int segs = Mathf.Max(2, Mathf.CeilToInt(length / 1.2f));
            for (int side = -1; side <= 1; side++)
            {
                for (int i = 0; i < segs; i++)
                {
                    float sa = length * i / segs, sb = length * (i + 1) / segs;
                    Vector3 pa = DeckPoint(sa), pb = DeckPoint(sb);
                    Vector3 mid = (pa + pb) * 0.5f + right * (side * half * 0.78f);
                    Vector3 f = (pb - pa).normalized;
                    Vector3 u = Vector3.Cross(f, right).normalized;
                    m.Box(mid - u * 0.22f, right, u, f, new Vector3(0.09f, 0.11f, (pb - pa).magnitude * 0.5f + 0.02f), Beam);
                }
            }
            foreach (float s in new[] { 0.05f, length - 0.05f })
            {
                Vector3 c = DeckPoint(s);
                m.Box(new Vector3(c.x, Mathf.Min(c.y, GroundAt(c.x, c.z) + 0.1f) - 0.04f, c.z), right, Vector3.up, dir, new Vector3(half + 0.15f, 0.14f, 0.16f), Beam);
            }

            // Posts and rails down both sides.
            int posts = Mathf.Max(2, Mathf.CeilToInt(length / 1.8f) + 1);
            for (int side = -1; side <= 1; side += 2)
            {
                Vector3 prevTop = Vector3.zero, prevMid = Vector3.zero;
                for (int i = 0; i < posts; i++)
                {
                    float s = length * i / (posts - 1);
                    Vector3 c = DeckPoint(s) + right * (side * (half - 0.08f));
                    m.Box(c + Vector3.up * (RailHeight * 0.5f), right, Vector3.up, dir, new Vector3(0.07f, RailHeight * 0.5f, 0.07f), Rail);
                    Vector3 top = c + Vector3.up * (RailHeight - 0.04f);
                    Vector3 mid = c + Vector3.up * (RailHeight * 0.45f);
                    if (i > 0)
                    {
                        AddRail(m, prevTop, top, right, 0.05f, Rail);
                        AddRail(m, prevMid, mid, right, 0.04f, Rail);
                    }
                    prevTop = top; prevMid = mid;
                }
            }

            // Piles into the bed wherever the ground is well below the deck.
            foreach (float t in new[] { 0.22f, 0.5f, 0.78f })
            {
                Vector3 c = DeckPoint(length * t);
                for (int side = -1; side <= 1; side += 2)
                {
                    Vector3 p = c + right * (side * (half - 0.3f));
                    float ground = GroundAt(p.x, p.z);
                    if (c.y - ground < 0.55f) continue;
                    float top = c.y - 0.2f, bottom = ground - 0.3f;
                    m.Box(new Vector3(p.x, (top + bottom) * 0.5f, p.z), right, Vector3.up, dir, new Vector3(0.12f, (top - bottom) * 0.5f, 0.12f), Pile);
                }
            }

            // GameObject with the visual mesh.
            var go = new GameObject("Bridge");
            go.transform.SetParent(root, false);
            go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);   // vertices are in world space
            var mf = go.AddComponent<MeshFilter>();
            mf.sharedMesh = m.ToMesh("BridgeMesh", 6);
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = Materials();
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;

            // Walkable deck: a closed ribbon following the arch. Plus an invisible wall along each rail.
            var deck = new GameObject("BridgeDeckCollider");
            deck.transform.SetParent(go.transform, false);
            deck.AddComponent<MeshCollider>().sharedMesh = BuildDeckCollider(DeckPoint, Tangent, right, length, half + 0.1f);
            for (int side = -1; side <= 1; side += 2)
            {
                int wallSegs = Mathf.Max(2, Mathf.CeilToInt(length / 1.5f));
                for (int i = 0; i < wallSegs; i++)
                {
                    float sa = length * i / wallSegs, sb = length * (i + 1) / wallSegs;
                    Vector3 a = DeckPoint(sa) + right * (side * (half - 0.08f));
                    Vector3 b = DeckPoint(sb) + right * (side * (half - 0.08f));
                    var wall = new GameObject("BridgeRailCollider");
                    wall.transform.SetParent(go.transform, false);
                    wall.transform.position = (a + b) * 0.5f + Vector3.up * (RailHeight * 0.5f);
                    wall.transform.rotation = Quaternion.LookRotation((b - a).normalized, Vector3.up);
                    wall.AddComponent<BoxCollider>().size = new Vector3(0.14f, RailHeight, (b - a).magnitude + 0.05f);
                }
            }

            Bridges.Add(new BridgeInfo
            {
                Start = DeckPoint(0f), End = DeckPoint(length), Length = length, Width = width,
            });
        }

        private static void AddRail(BoxMesher m, Vector3 a, Vector3 b, Vector3 right, float thick, int mat)
        {
            Vector3 f = (b - a).normalized;
            Vector3 r = Vector3.Cross(Vector3.up, f).normalized;
            if (r.sqrMagnitude < 0.01f) r = right;
            Vector3 u = Vector3.Cross(f, r).normalized;
            m.Box((a + b) * 0.5f, r, u, f, new Vector3(thick, thick, (b - a).magnitude * 0.5f + 0.03f), mat);
        }

        /// <summary>A thin closed ribbon under the deck surface, so the character controller has something solid to stand on.</summary>
        private static Mesh BuildDeckCollider(System.Func<float, Vector3> deckPoint, System.Func<float, Vector3> tangent, Vector3 right, float length, float half)
        {
            int n = Mathf.Max(2, Mathf.CeilToInt(length / 0.75f));
            var v = new List<Vector3>();
            var t = new List<int>();
            for (int i = 0; i <= n; i++)
            {
                float s = length * i / n;
                Vector3 c = deckPoint(s);
                v.Add(c - right * half);                              // 4i + 0: top left
                v.Add(c + right * half);                              // 4i + 1: top right
                v.Add(c - right * half + Vector3.down * 0.3f);        // 4i + 2: bottom left
                v.Add(c + right * half + Vector3.down * 0.3f);        // 4i + 3: bottom right
            }
            for (int i = 0; i < n; i++)
            {
                int a = i * 4, b = (i + 1) * 4;
                // top (up-facing)
                t.AddRange(new[] { a, b, a + 1, a + 1, b, b + 1 });
                // bottom
                t.AddRange(new[] { a + 2, a + 3, b + 2, a + 3, b + 3, b + 2 });
                // left side
                t.AddRange(new[] { a, a + 2, b, b, a + 2, b + 2 });
                // right side
                t.AddRange(new[] { a + 1, b + 1, a + 3, a + 3, b + 1, b + 3 });
            }
            // end caps
            t.AddRange(new[] { 0, 1, 2, 1, 3, 2 });
            int e = n * 4;
            t.AddRange(new[] { e, e + 2, e + 1, e + 1, e + 2, e + 3 });
            var mesh = new Mesh { name = "BridgeDeckCollider" };
            mesh.SetVertices(v);
            mesh.SetTriangles(t, 0);
            mesh.RecalculateNormals();
            return mesh;
        }

        // ------------------------------------------------------------------ materials

        private static Material[] _materials;

        private static Material[] Materials()
        {
            if (_materials != null && _materials[0] != null) return _materials;
            Shader shader = Shader.Find("Homesteader/Vegetation") ?? Shader.Find("Universal Render Pipeline/Lit");
            string[] hex = { "#8a6a45", "#7a5c3c", "#6b4f33", "#54402c", "#7d6041", "#4a3a29" };
            _materials = new Material[hex.Length];
            for (int i = 0; i < hex.Length; i++)
            {
                ColorUtility.TryParseHtmlString(hex[i], out Color c);
                var mat = new Material(shader) { hideFlags = HideFlags.DontSave, name = "Bridge_" + i };
                mat.SetColor("_BaseColor", c);
                if (mat.HasProperty("_SwayAmp")) mat.SetFloat("_SwayAmp", 0f);
                if (mat.HasProperty("_Grow")) mat.SetFloat("_Grow", 1f);
                _materials[i] = mat;
            }
            return _materials;
        }
    }
}
