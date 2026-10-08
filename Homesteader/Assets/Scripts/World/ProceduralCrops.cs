using System.Collections.Generic;
using UnityEngine;
using Homesteader.Growth;

namespace Homesteader.World
{
    /// <summary>
    /// Procedural crops: every kit crop group (corn, sunflower, wheat, pumpkin, carrot, potato, tomato, strawberry, herb, cotton) is drawn from
    /// meshes built here instead of GLB models, the same way the kit's tree groups use the procedural trees. A crop has the same six looks as a
    /// fruiting tree: sprout, small, medium, mature, ripe (the harvest look), plus withered and dead. They are NOT scattered in the world
    /// (crops do not occur naturally); they exist only as planted crops (seeds), as planting previews and as asset-kit models / icons.
    /// The kit's own stage models stay in the kit (the originals are kept in assets/_originals/crops_old); the groups' stage prefabs are
    /// replaced at world generation by <see cref="ApplyCropPrefabs"/>. Flat shaded, a few hundred triangles each, walk-through (no colliders).
    /// </summary>
    public static class ProceduralCrops
    {
        public static readonly string[] Names =
        {
            "corn", "sunflower", "wheat", "pumpkin", "carrot", "potato", "tomato", "strawberry", "herb", "cotton",
            "onion", "garlic", "lettuce", "cabbage", "spinach", "broccoli", "beet", "radish", "rhubarb",
            "peas", "green_beans", "cucumber", "hops", "zucchini", "peppers", "soybeans", "peanuts", "tobacco", "flax", "alfalfa",
            "oats", "barley", "watermelon", "cantaloupe", "canola",
        };

        /// <summary>The looks of a crop: five growth stages, then the two failure versions.</summary>
        public enum Phase { Sprout, Small, Medium, Mature, Ripe, Withered, Dead }

        private static readonly float[] Growth = { 0.18f, 0.42f, 0.7f, 1f, 1f };
        private const int Subs = 5;   // 0 stem, 1 leaf, 2 fruit, 3 accent (flowers, tassels, petals), 4 soil / stake

        // ------------------------------------------------------------------ colours

        private static Color Hex(string hex)
        {
            ColorUtility.TryParseHtmlString(hex, out Color c);
            return c;
        }

        private static Color[] Pal(string stem, string leaf, string fruit, string accent, string soil = "#5b4636")
        {
            return new[] { Hex(stem), Hex(leaf), Hex(fruit), Hex(accent), Hex(soil) };
        }

        /// <summary>The five colours (stem, leaf, fruit, accent, soil) of a crop at one look.</summary>
        public static Color[] Palette(string crop, Phase ph)
        {
            Color[] p;
            if (Specs.TryGetValue(crop, out Spec spec)) p = SpecPalette(spec, ph);
            else
            switch (crop)
            {
                case "corn":
                    p = ph == Phase.Ripe ? Pal("#8f9a45", "#8aa23c", "#eab93a", "#d6bd78") : Pal("#6b9a3a", "#5b9a35", "#d8c44a", "#d6c27a");
                    break;
                case "sunflower":
                    p = ph == Phase.Ripe ? Pal("#7d8a3a", "#6f8a30", "#4a2f1a", "#f2c126") : Pal("#5f8a35", "#4f8a2e", "#4a2f1a", "#f3c525");
                    break;
                case "wheat":
                    p = ph == Phase.Ripe ? Pal("#d2b85a", "#c9b050", "#dcbc50", "#cdb868") : (ph == Phase.Mature ? Pal("#9fb248", "#8fae40", "#a9b64a", "#b8b868") : Pal("#7fa83e", "#6fa03a", "#8fb04a", "#c8b060"));
                    break;
                case "pumpkin":
                    p = Pal("#5f8a3a", "#4f9a3a", ph == Phase.Ripe ? "#e8741c" : (ph == Phase.Mature ? "#c8941f" : "#7a9a2e"), "#f3c525");
                    break;
                case "carrot":
                    p = Pal("#5f9a3a", "#4f9a3a", "#e8801c", "#3f8a30");
                    break;
                case "potato":
                    p = ph == Phase.Ripe ? Pal("#9a9a45", "#a8a050", "#c9a46a", "#f0e8f4") : Pal("#5f8a3a", "#4a8a3a", "#c9a46a", "#f0e8f4");
                    break;
                case "tomato":
                    p = Pal("#5f8a35", "#4a8a30", ph == Phase.Ripe ? "#d8281e" : "#6aa03a", "#f3d030", "#8a6a40");
                    break;
                case "strawberry":
                    p = Pal("#5f8a3a", "#3f8a35", "#d8282e", "#f4f0e0");
                    break;
                case "herb":
                    p = Pal("#5a8a3a", "#4f9a3a", "#4f9a3a", "#8a5aa8");
                    break;
                default:   // cotton
                    p = Pal("#6b8a3a", "#4f8a30", ph == Phase.Ripe ? "#f4f0e6" : "#7aa040", "#a89a60");
                    break;
            }
            if (ph == Phase.Withered)
            {
                Color brown = Hex("#8a7440");
                for (int i = 0; i < 4; i++) p[i] = Color.Lerp(p[i], brown, i == 2 ? 0.45f : 0.7f);
            }
            else if (ph == Phase.Dead)
            {
                Color dark = Hex("#3b2f22");
                for (int i = 0; i < 4; i++) p[i] = Color.Lerp(p[i], dark, 0.85f);
            }
            return p;
        }

        // ------------------------------------------------------------------ mesh builder

        private sealed class CM
        {
            public readonly List<Vector3> V = new List<Vector3>();
            public readonly List<Vector3> N = new List<Vector3>();
            public readonly List<int>[] T = { new List<int>(), new List<int>(), new List<int>(), new List<int>(), new List<int>() };

            public void Tri(Vector3 a, Vector3 b, Vector3 c, int sub)
            {
                Vector3 n = Vector3.Cross(b - a, c - a);
                if (n.sqrMagnitude < 1e-12f) return;
                n.Normalize();
                int i = V.Count;
                V.Add(a); V.Add(b); V.Add(c);
                N.Add(n); N.Add(n); N.Add(n);
                T[sub].Add(i); T[sub].Add(i + 1); T[sub].Add(i + 2);
            }

            /// <summary>A triangle wound to face away from a point inside the shape.</summary>
            public void Out(Vector3 a, Vector3 b, Vector3 c, Vector3 inside, int sub)
            {
                Vector3 n = Vector3.Cross(b - a, c - a);
                if (Vector3.Dot(n, (a + b + c) / 3f - inside) < 0f) { Vector3 t = b; b = c; c = t; }
                Tri(a, b, c, sub);
            }

            public void Both(Vector3 a, Vector3 b, Vector3 c, int sub)
            {
                Tri(a, b, c, sub);
                Tri(a, c, b, sub);
            }

            public Mesh ToMesh(string name)
            {
                var mesh = new Mesh { name = name };
                mesh.SetVertices(V);
                mesh.SetNormals(N);
                mesh.subMeshCount = Subs;
                for (int s = 0; s < Subs; s++) mesh.SetTriangles(T[s], s);
                mesh.RecalculateBounds();
                return mesh;
            }
        }

        private static void Tube(CM m, Vector3 p0, Vector3 p1, float r0, float r1, int sides, int sub)
        {
            Vector3 centre = (p0 + p1) * 0.5f;
            Vector3 axis = (p1 - p0).normalized;
            Vector3 u = Vector3.Cross(axis, Mathf.Abs(axis.y) > 0.9f ? Vector3.right : Vector3.up).normalized;
            Vector3 v = Vector3.Cross(axis, u);
            for (int i = 0; i < sides; i++)
            {
                float a0 = i * Mathf.PI * 2f / sides, a1 = (i + 1) * Mathf.PI * 2f / sides;
                Vector3 d0 = u * Mathf.Cos(a0) + v * Mathf.Sin(a0);
                Vector3 d1 = u * Mathf.Cos(a1) + v * Mathf.Sin(a1);
                Vector3 b0 = p0 + d0 * r0, b1 = p0 + d1 * r0, t0 = p1 + d0 * r1, t1 = p1 + d1 * r1;
                m.Out(b0, t0, t1, centre, sub);
                m.Out(b0, t1, b1, centre, sub);
                if (r1 > 0.0005f) m.Out(t0, t1, p1, centre, sub);   // cap the tip
            }
        }

        /// <summary>A stem that curves: a chain of short tubes from base to tip with a lean (a point on the way is offset by lean * t^2).</summary>
        private static void Stem(CM m, Vector3 b, float h, Vector3 lean, float r0, float r1, int sides, int sub, int segs = 3)
        {
            Vector3 prev = b;
            for (int i = 1; i <= segs; i++)
            {
                float t = i / (float)segs;
                Vector3 p = b + Vector3.up * (h * t) + lean * (t * t);
                Tube(m, prev, p, Mathf.Lerp(r0, r1, (i - 1) / (float)segs), Mathf.Lerp(r0, r1, t), sides, sub);
                prev = p;
            }
        }

        private static Vector3 StemPoint(Vector3 b, float h, Vector3 lean, float t)
        {
            return b + Vector3.up * (h * t) + lean * (t * t);
        }

        /// <summary>A low-poly ellipsoid (rings x sides), flat shaded.</summary>
        private static void Blob(CM m, Vector3 c, float rx, float ry, float rz, int sub, int sides = 6, int rings = 3, Quaternion? rot = null)
        {
            Quaternion q = rot ?? Quaternion.identity;
            var pts = new Vector3[rings, sides];
            for (int r = 0; r < rings; r++)
            {
                float phi = Mathf.PI * (r + 1) / (rings + 1);
                float y = Mathf.Cos(phi), rr = Mathf.Sin(phi);
                for (int s = 0; s < sides; s++)
                {
                    float a = s * Mathf.PI * 2f / sides + (r % 2) * 0.3f;
                    pts[r, s] = c + q * new Vector3(Mathf.Cos(a) * rr * rx, y * ry, Mathf.Sin(a) * rr * rz);
                }
            }
            Vector3 top = c + q * new Vector3(0f, ry, 0f), bot = c + q * new Vector3(0f, -ry, 0f);
            for (int s = 0; s < sides; s++)
            {
                int n = (s + 1) % sides;
                m.Out(top, pts[0, s], pts[0, n], c, sub);
                for (int r = 0; r < rings - 1; r++)
                {
                    m.Out(pts[r, s], pts[r + 1, s], pts[r + 1, n], c, sub);
                    m.Out(pts[r, s], pts[r + 1, n], pts[r, n], c, sub);
                }
                m.Out(bot, pts[rings - 1, n], pts[rings - 1, s], c, sub);
            }
        }

        private static void Cone(CM m, Vector3 b, Vector3 tip, float r, int sides, int sub)
        {
            Tube(m, b, tip, r, 0f, sides, sub);
        }

        /// <summary>A leaf blade: three segments, double sided, curving up from the base and drooping at the tip.</summary>
        private static void Leaf(CM m, Vector3 b, Vector3 dirHoriz, float length, float width, float rise, float droop, int sub)
        {
            Vector3 d = new Vector3(dirHoriz.x, 0f, dirHoriz.z).normalized;
            Vector3 side = Vector3.Cross(Vector3.up, d).normalized;
            const int segs = 3;
            Vector3 lp = b, rp = b;
            for (int i = 1; i <= segs; i++)
            {
                float t = i / (float)segs;
                Vector3 c = b + d * (length * t) + Vector3.up * (length * (rise * t - droop * t * t));
                float w = width * Mathf.Sin(Mathf.PI * Mathf.Clamp01(t * 0.92f + 0.04f));
                Vector3 l = c - side * w, r = c + side * w;
                if (i == 1) { lp = b - side * width * 0.15f; rp = b + side * width * 0.15f; }
                m.Both(lp, l, rp, sub);
                m.Both(rp, l, r, sub);
                lp = l; rp = r;
            }
        }

        private static float R(System.Random rng, float a, float b) { return Mathf.Lerp(a, b, (float)rng.NextDouble()); }

        private static Vector3 Dir(float angle) { return new Vector3(Mathf.Cos(angle), 0f, Mathf.Sin(angle)); }

        private const float Golden = 2.39996f;

        // ------------------------------------------------------------------ the crops

        private sealed class Ctx
        {
            public CM M;
            public System.Random Rng;
            public float G;           // growth 0..1
            public bool Mature, Ripe, Wither;
            public float Droop => Wither ? 1.7f : 1f;
        }

        private static float Height(string crop)
        {
            if (Specs.TryGetValue(crop, out Spec spec)) return spec.H;
            switch (crop)
            {
                case "corn": return 1.9f;
                case "sunflower": return 1.7f;
                case "wheat": return 0.85f;
                case "pumpkin": return 0.35f;
                case "carrot": return 0.34f;
                case "potato": return 0.6f;
                case "tomato": return 1.05f;
                case "strawberry": return 0.34f;
                case "herb": return 0.45f;
                default: return 0.95f;   // cotton
            }
        }

        private static void Corn(Ctx c)
        {
            float H = Height("corn") * Mathf.Lerp(0.25f, 1f, c.G) * (c.Wither ? 0.85f : 1f);
            Vector3 lean = Dir(R(c.Rng, 0f, 6.28f)) * (c.Wither ? 0.25f : 0.05f);
            Stem(c.M, Vector3.zero, H, lean, 0.03f * (0.6f + c.G * 0.6f), 0.012f, 4, 0, 4);
            int leaves = Mathf.RoundToInt(Mathf.Lerp(3, 9, c.G));
            for (int i = 0; i < leaves; i++)
            {
                float t = Mathf.Lerp(0.12f, 0.88f, i / (float)Mathf.Max(1, leaves - 1));
                Vector3 b = StemPoint(Vector3.zero, H, lean, t);
                float len = Mathf.Lerp(0.3f, 0.75f, c.G) * (1.1f - t * 0.5f);
                Leaf(c.M, b, Dir(i * Golden), len, 0.06f, 0.35f, 0.75f * c.Droop, 1);
            }
            if (c.Mature)
            {
                Vector3 top = StemPoint(Vector3.zero, H, lean, 1f);
                for (int i = 0; i < 5; i++) Cone(c.M, top, top + Dir(i * 1.26f) * 0.05f + Vector3.up * 0.28f, 0.012f, 3, 3);   // the tassel
                for (int e = 0; e < 2; e++)
                {
                    Vector3 b = StemPoint(Vector3.zero, H, lean, 0.52f + e * 0.14f);
                    Vector3 dir = Dir(e * 3.1f + 0.6f);
                    Vector3 tip = b + dir * 0.1f + Vector3.up * 0.3f;
                    Tube(c.M, b, tip, 0.05f, 0.035f, 5, 1);                  // the husk
                    if (c.Ripe) Cone(c.M, tip, tip + dir * 0.02f + Vector3.up * 0.06f, 0.03f, 5, 2);   // kernels showing at the tip
                }
            }
        }

        private static void Sunflower(Ctx c)
        {
            float H = Height("sunflower") * Mathf.Lerp(0.2f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            Vector3 lean = Dir(0.5f) * (c.Wither ? 0.35f : 0.06f);
            Stem(c.M, Vector3.zero, H, lean, 0.032f * (0.6f + c.G * 0.5f), 0.02f, 4, 0, 4);
            int leaves = Mathf.RoundToInt(Mathf.Lerp(2, 8, c.G));
            for (int i = 0; i < leaves; i++)
            {
                float t = Mathf.Lerp(0.15f, 0.8f, i / (float)Mathf.Max(1, leaves - 1));
                Leaf(c.M, StemPoint(Vector3.zero, H, lean, t), Dir(i * Golden), Mathf.Lerp(0.18f, 0.34f, c.G), 0.13f, 0.18f, 0.55f * c.Droop, 1);
            }
            Vector3 top = StemPoint(Vector3.zero, H, lean, 1f);
            if (!c.Mature)
            {
                if (c.G > 0.5f) Blob(c.M, top + Vector3.up * 0.04f, 0.05f, 0.05f, 0.05f, 1);   // a bud
                return;
            }
            // the head: a disc facing out and up; ripe, it bows over
            Quaternion tilt = Quaternion.Euler(c.Ripe || c.Wither ? 70f : 25f, 0f, 0f);
            Vector3 centre = top + tilt * new Vector3(0f, 0f, 0.09f) + Vector3.up * 0.02f;
            Blob(c.M, centre, 0.17f, 0.04f, 0.17f, 2, 8, 2, tilt);
            if (!c.Wither)
                for (int i = 0; i < 14; i++)
                {
                    float a = i * Mathf.PI * 2f / 14f;
                    Vector3 d1 = tilt * (new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a)));
                    Vector3 d2 = tilt * (new Vector3(Mathf.Cos(a + 0.22f), 0f, Mathf.Sin(a + 0.22f)));
                    Vector3 tipP = centre + tilt * (new Vector3(Mathf.Cos(a + 0.11f), 0f, Mathf.Sin(a + 0.11f)) * 0.3f);
                    c.M.Both(centre + d1 * 0.15f, tipP, centre + d2 * 0.15f, 3);
                }
        }

        private static void Wheat(Ctx c)
        {
            float H = Height("wheat") * Mathf.Lerp(0.2f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            int n = Mathf.RoundToInt(Mathf.Lerp(5, 16, c.G));
            for (int i = 0; i < n; i++)
            {
                float a = R(c.Rng, 0f, 6.28f), d = R(c.Rng, 0.02f, 0.13f) * (0.5f + c.G * 0.5f);
                Vector3 b = Dir(a) * d;
                float h = H * R(c.Rng, 0.8f, 1.1f);
                Vector3 lean = Dir(a) * R(c.Rng, 0.02f, 0.1f) * (c.Wither ? 3f : (c.Ripe ? 2f : 1f));
                Stem(c.M, b, h, lean, 0.008f, 0.005f, 3, 0, 2);
                if (i % 2 == 0) Leaf(c.M, StemPoint(b, h, lean, 0.35f), Dir(a + 0.8f), h * 0.4f, 0.018f, 0.45f, 0.7f * c.Droop, 1);
                if (c.Mature)
                {
                    Vector3 top = StemPoint(b, h, lean, 1f);
                    Vector3 hd = (c.Ripe ? lean.normalized * 0.45f : Vector3.zero) + Vector3.up;
                    hd.Normalize();
                    Blob(c.M, top + hd * 0.05f, 0.016f, 0.06f, 0.016f, 2, 4, 3, Quaternion.FromToRotation(Vector3.up, hd));
                    for (int k = 0; k < 3; k++) Cone(c.M, top + hd * 0.09f, top + hd * 0.17f + Dir(k * 2.1f) * 0.02f, 0.004f, 3, 3);   // awns
                }
            }
        }

        private static void Pumpkin(Ctx c)
        {
            float span = Mathf.Lerp(0.18f, 0.95f, c.G) * (c.Wither ? 0.85f : 1f);
            int vines = c.G < 0.3f ? 1 : 3;
            for (int v = 0; v < vines; v++)
            {
                float a = v * 2.1f + 0.4f;
                Vector3 prev = Vector3.up * 0.03f;
                int segs = 4;
                for (int s = 1; s <= segs; s++)
                {
                    float t = s / (float)segs;
                    Vector3 p = Dir(a + Mathf.Sin(t * 3f + v) * 0.35f) * (span * t) + Vector3.up * (0.03f + 0.02f * Mathf.Sin(t * 5f));
                    Tube(c.M, prev, p, 0.016f * (1.2f - t * 0.5f), 0.014f * (1.2f - t * 0.5f), 3, 0);
                    if (s % 2 == 0 || c.G < 0.3f)
                        Leaf(c.M, p, Dir(a + (s % 2 == 0 ? 1.4f : -1.4f)), Mathf.Lerp(0.12f, 0.3f, c.G), 0.12f * Mathf.Lerp(0.6f, 1f, c.G), 0.28f, 0.7f * c.Droop, 1);
                    prev = p;
                }
                if (c.G > 0.5f && !c.Mature && v == 0) Blob(c.M, Dir(a + 0.2f) * span * 0.55f + Vector3.up * 0.05f, 0.03f, 0.025f, 0.03f, 3, 5, 2);   // a flower
            }
            if (c.G >= 0.65f)
            {
                float r = c.Ripe ? 0.4f : (c.Mature ? 0.28f : 0.08f);
                Vector3 at = Dir(0.3f) * 0.1f + Vector3.up * r * 0.85f;
                Blob(c.M, at, r, r * 0.82f, r, 2, 8, 3);
                Tube(c.M, at + Vector3.up * r * 0.7f, at + Vector3.up * (r * 0.7f + 0.07f) + Dir(0.9f) * 0.03f, 0.022f, 0.014f, 4, 0);
            }
        }

        private static void Carrot(Ctx c)
        {
            float H = Height("carrot") * Mathf.Lerp(0.3f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            int n = Mathf.RoundToInt(Mathf.Lerp(3, 9, c.G));
            for (int i = 0; i < n; i++)
            {
                float a = i * Golden;
                Vector3 b = Dir(a) * 0.015f + Vector3.up * 0.02f;
                Leaf(c.M, b, Dir(a), H * R(c.Rng, 0.85f, 1.1f), 0.022f, 1.1f, 0.45f * c.Droop, 1);
            }
            if (c.Mature) Blob(c.M, Vector3.up * 0.005f, 0.035f, 0.02f, 0.035f, 2, 6, 2);   // the root's crown at the soil
            if (c.Ripe) Blob(c.M, Vector3.up * 0.012f, 0.045f, 0.025f, 0.045f, 2, 6, 2);
        }

        private static void Potato(Ctx c)
        {
            float H = Height("potato") * Mathf.Lerp(0.25f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            if (c.G >= 0.4f) Blob(c.M, Vector3.up * 0.015f, 0.3f * Mathf.Lerp(0.5f, 1f, c.G), 0.07f, 0.3f * Mathf.Lerp(0.5f, 1f, c.G), 4, 8, 2);   // the hill
            int stems = Mathf.RoundToInt(Mathf.Lerp(2, 6, c.G));
            for (int i = 0; i < stems; i++)
            {
                float a = i * Golden;
                Vector3 lean = Dir(a) * H * 0.3f * c.Droop;
                Stem(c.M, Dir(a) * 0.03f + Vector3.up * 0.04f, H * R(c.Rng, 0.8f, 1f), lean, 0.012f, 0.007f, 3, 0, 2);
                for (int k = 0; k < 3; k++)
                {
                    float t = 0.4f + k * 0.28f;
                    Vector3 b = StemPoint(Dir(a) * 0.03f + Vector3.up * 0.04f, H, lean, t);
                    Leaf(c.M, b, Dir(a + k * 2.1f), Mathf.Lerp(0.08f, 0.2f, c.G), 0.07f, 0.3f, 0.6f * c.Droop, 1);
                }
                if (c.Mature && !c.Ripe && i % 2 == 0) Blob(c.M, StemPoint(Dir(a) * 0.03f + Vector3.up * 0.04f, H, lean, 1f), 0.025f, 0.02f, 0.025f, 3, 5, 2);   // flowers
            }
            if (c.Ripe) for (int i = 0; i < 3; i++) Blob(c.M, Dir(i * 2.1f + 0.4f) * 0.22f + Vector3.up * 0.045f, 0.06f, 0.04f, 0.045f, 2, 5, 2);   // tubers showing
        }

        private static void Tomato(Ctx c)
        {
            float H = Height("tomato") * Mathf.Lerp(0.2f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            if (c.G >= 0.4f) Tube(c.M, new Vector3(0.1f, 0f, 0f), new Vector3(0.1f, H * 1.05f, 0f), 0.014f, 0.012f, 3, 4);   // the stake
            Vector3 lean = Dir(2.4f) * (c.Wither ? 0.3f : 0.04f);
            Stem(c.M, Vector3.zero, H, lean, 0.016f * (0.6f + c.G * 0.5f), 0.009f, 4, 0, 4);
            int leaves = Mathf.RoundToInt(Mathf.Lerp(3, 12, c.G));
            for (int i = 0; i < leaves; i++)
            {
                float t = Mathf.Lerp(0.15f, 0.95f, i / (float)Mathf.Max(1, leaves - 1));
                Vector3 b = StemPoint(Vector3.zero, H, lean, t);
                Leaf(c.M, b, Dir(i * Golden), Mathf.Lerp(0.1f, 0.22f, c.G), 0.07f, 0.25f, 0.7f * c.Droop, 1);
            }
            if (c.Mature)
                for (int i = 0; i < (c.Ripe ? 9 : 6); i++)
                {
                    float t = Mathf.Lerp(0.3f, 0.85f, (i % 5) / 4f);
                    Vector3 b = StemPoint(Vector3.zero, H, lean, t) + Dir(i * 1.7f) * 0.07f;
                    float r = c.Ripe ? 0.045f : 0.032f;
                    Blob(c.M, b - Vector3.up * r, r, r * 0.9f, r, 2, 6, 3);
                    if (!c.Ripe && i % 3 == 0) Blob(c.M, b + Vector3.up * 0.08f, 0.018f, 0.014f, 0.018f, 3, 5, 2);   // a flower
                }
        }

        private static void Strawberry(Ctx c)
        {
            // a low bush: many leaf stems fanning out and up in all directions, berries and flowers hanging at the edge
            float H = Height("strawberry") * Mathf.Lerp(0.35f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            int n = Mathf.RoundToInt(Mathf.Lerp(4, 11, c.G));
            for (int i = 0; i < n; i++)
            {
                float a = i * Golden;
                float up = H * R(c.Rng, 0.5f, 1f);
                float spread = H * R(c.Rng, 0.25f, 0.7f);
                Vector3 b = Dir(a) * 0.015f + Vector3.up * 0.02f;
                Vector3 tip = b + Dir(a) * spread + Vector3.up * up;
                Tube(c.M, b, tip, 0.007f, 0.004f, 3, 0);
                for (int k = -1; k <= 1; k++)
                    Leaf(c.M, tip, Dir(a + k * 0.7f), H * 0.55f, 0.06f, 0.15f, 0.8f * c.Droop, 1);   // a trifoliate leaf on the stem
            }
            if (c.Mature)
                for (int i = 0; i < (c.Ripe ? 8 : 5); i++)
                {
                    float a = i * 1.9f + 0.4f;
                    Vector3 at = Dir(a) * H * 0.55f + Vector3.up * H * R(c.Rng, 0.25f, 0.55f);
                    if (c.Ripe) Blob(c.M, at, 0.03f, 0.036f, 0.03f, 2, 5, 2);
                    else Blob(c.M, at + Vector3.up * 0.03f, 0.022f, 0.012f, 0.022f, 3, 5, 2);   // the white flowers
                }
        }

        private static void Herb(Ctx c)
        {
            float H = Height("herb") * Mathf.Lerp(0.3f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            int n = Mathf.RoundToInt(Mathf.Lerp(3, 10, c.G));
            for (int i = 0; i < n; i++)
            {
                float a = i * Golden;
                Vector3 lean = Dir(a) * H * 0.35f * c.Droop;
                Vector3 b = Dir(a) * 0.015f;
                float h = H * R(c.Rng, 0.6f, 1f);
                Stem(c.M, b, h, lean, 0.008f, 0.005f, 3, 0, 2);
                for (int k = 0; k < 3; k++)
                    Leaf(c.M, StemPoint(b, h, lean, 0.45f + k * 0.25f), Dir(a + k * 2.1f + 0.5f), Mathf.Lerp(0.07f, 0.12f, c.G), 0.045f, 0.25f, 0.55f * c.Droop, 1);
                if (c.Ripe) Cone(c.M, StemPoint(b, h, lean, 1f), StemPoint(b, h, lean, 1f) + Vector3.up * 0.1f, 0.016f, 4, 3);   // flower spikes
            }
        }

        private static void Cotton(Ctx c)
        {
            float H = Height("cotton") * Mathf.Lerp(0.22f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            Vector3 lean = Dir(1.1f) * (c.Wither ? 0.25f : 0.03f);
            Stem(c.M, Vector3.zero, H, lean, 0.022f * (0.6f + c.G * 0.5f), 0.01f, 4, 0, 3);
            int leaves = Mathf.RoundToInt(Mathf.Lerp(3, 11, c.G));
            for (int i = 0; i < leaves; i++)
            {
                float t = Mathf.Lerp(0.15f, 0.95f, i / (float)Mathf.Max(1, leaves - 1));
                Leaf(c.M, StemPoint(Vector3.zero, H, lean, t), Dir(i * Golden), Mathf.Lerp(0.1f, 0.2f, c.G), 0.08f, 0.22f, 0.6f * c.Droop, 1);
            }
            if (c.Mature)
                for (int i = 0; i < (c.Ripe ? 8 : 5); i++)
                {
                    float t = Mathf.Lerp(0.3f, 0.9f, (i % 4) / 3f);
                    Vector3 b = StemPoint(Vector3.zero, H, lean, t) + Dir(i * 1.9f) * 0.07f;
                    if (c.Ripe)
                    {
                        Cone(c.M, b - Vector3.up * 0.02f, b + Vector3.up * 0.05f + Dir(i * 1.9f) * 0.03f, 0.035f, 4, 3);   // the dried bract
                        for (int k = 0; k < 3; k++) Blob(c.M, b + Dir(i * 1.9f + k * 2.1f) * 0.018f + Vector3.up * 0.045f, 0.028f, 0.026f, 0.028f, 2, 5, 2);   // the white bolls
                    }
                    else Blob(c.M, b, 0.03f, 0.036f, 0.03f, 2, 5, 2);   // green bolls
                }
        }

        /// <summary>A dead crop: a few bent, dried stubs and shrivelled leaves lying on the soil.</summary>
        private static void Dead(Ctx c, string crop)
        {
            float H = Mathf.Max(0.22f, Height(crop) * 0.3f);
            for (int i = 0; i < 4; i++)
            {
                float a = i * 1.7f + 0.3f;
                Vector3 lean = Dir(a) * H * 0.9f;
                Stem(c.M, Dir(a + 1f) * 0.02f, H * R(c.Rng, 0.6f, 1f), lean, 0.012f, 0.006f, 3, 0, 2);
                Leaf(c.M, Dir(a) * 0.12f + Vector3.up * 0.02f, Dir(a + 0.7f), H * 0.9f, 0.035f, 0.05f, 0.3f, 1);
            }
        }

        // ------------------------------------------------------------------ the data-driven crops

        private enum Kind { Rosette, Allium, Climber, Bush, Grain, VineFruit }
        private enum FruitShape { Blob, Tube, Cone, Pod }

        private sealed class Spec
        {
            public Kind Kind;
            public float H = 0.5f;          // mature height (a climber's pole, a vine's spread)
            public float Leaf = 0.2f, LW = 0.07f;     // leaf length and half width at maturity
            public int N = 8;               // leaves / stems at maturity
            public FruitShape Shape;
            public float FruitR = 0.04f;    // fruit radius
            public float FruitLen = 0f;     // tubes / pods: length
            public int FruitN = 5;
            public bool Root;               // a root / bulb at the soil (beet, radish, onion)
            public int HeadKind;            // 0 none, 1 tight ball (cabbage), 2 crown (broccoli), 3 heart of leaves (lettuce, spinach)
            public bool Upright;            // red-stemmed leaves standing up (beet)
            public bool Stalks;             // thick leaf stalks (rhubarb)
            public bool Flower = true;      // flowers at mature
            public int FlowerScatter;       // a bush that flowers in a cloud (canola): this many flowers over its upper half while it is mature and not yet ripe
            public string[] Colours;        // stem, leaf, fruit, accent (mature)
            public string RipeLeaf;         // leaf colour when ripe (null = same)
            public string RipeStem;
            public string RipeFruit;
            public string Soil = "#5b4636";
        }

        private static readonly Dictionary<string, Spec> Specs = new Dictionary<string, Spec>
        {
            { "lettuce", new Spec { Kind = Kind.Rosette, H = 0.22f, Leaf = 0.17f, LW = 0.085f, N = 14, HeadKind = 3, FruitR = 0.09f, Flower = false, Colours = new[] { "#9fc86a", "#7bc04a", "#8fd058", "#d8e08a" } } },
            { "spinach", new Spec { Kind = Kind.Rosette, H = 0.22f, Leaf = 0.15f, LW = 0.055f, N = 12, HeadKind = 3, FruitR = 0.055f, Flower = false, Colours = new[] { "#4a8a38", "#3a7a30", "#4a8a38", "#8ab04a" } } },
            { "cabbage", new Spec { Kind = Kind.Rosette, H = 0.3f, Leaf = 0.24f, LW = 0.12f, N = 9, HeadKind = 1, FruitR = 0.13f, Flower = false, Colours = new[] { "#8fbf70", "#6fae58", "#9fcf80", "#d8e08a" } } },
            { "broccoli", new Spec { Kind = Kind.Rosette, H = 0.5f, Leaf = 0.3f, LW = 0.08f, N = 8, HeadKind = 2, FruitR = 0.07f, Flower = false, Colours = new[] { "#7fae58", "#4f8a4a", "#3f8a3a", "#e8e070" } } },
            { "beet", new Spec { Kind = Kind.Rosette, H = 0.45f, Leaf = 0.24f, LW = 0.075f, N = 8, Root = true, Upright = true, FruitR = 0.095f, Flower = false, Colours = new[] { "#8a2a3a", "#4f8a3a", "#7a1f3a", "#c8e07a" } } },
            { "radish", new Spec { Kind = Kind.Rosette, H = 0.2f, Leaf = 0.13f, LW = 0.045f, N = 7, Root = true, FruitR = 0.03f, Flower = false, Colours = new[] { "#9a4a5a", "#5a9a3a", "#d83a5a", "#e8f0c8" } } },
            { "rhubarb", new Spec { Kind = Kind.Rosette, H = 0.55f, Leaf = 0.28f, LW = 0.2f, N = 6, Stalks = true, Flower = false, Colours = new[] { "#b52a3a", "#4a8a3a", "#b52a3a", "#d8e08a" } } },
            { "onion", new Spec { Kind = Kind.Allium, H = 0.45f, N = 7, Root = true, FruitR = 0.055f, Flower = false, Colours = new[] { "#7fae48", "#6fa03a", "#d8b060", "#f0e8c8" }, RipeLeaf = "#b8a458", RipeStem = "#a89850" } },
            { "garlic", new Spec { Kind = Kind.Allium, H = 0.5f, N = 6, Root = true, FruitR = 0.035f, Flower = true, Colours = new[] { "#7fae48", "#6fa03a", "#f0e6d0", "#d8c8a0" }, RipeLeaf = "#b8a458", RipeStem = "#a89850" } },
            { "peas", new Spec { Kind = Kind.Climber, H = 0.9f, Leaf = 0.07f, LW = 0.04f, N = 9, Shape = FruitShape.Pod, FruitLen = 0.075f, FruitR = 0.012f, FruitN = 8, Colours = new[] { "#7fa84a", "#6fb04a", "#6aa84a", "#f4f0f4" } } },
            { "green_beans", new Spec { Kind = Kind.Climber, H = 1.3f, Leaf = 0.1f, LW = 0.06f, N = 10, Shape = FruitShape.Pod, FruitLen = 0.15f, FruitR = 0.009f, FruitN = 10, Colours = new[] { "#6f9a3a", "#4f9a3a", "#5a9a3a", "#f0d8f0" } } },
            { "cucumber", new Spec { Kind = Kind.Climber, H = 1.0f, Leaf = 0.16f, LW = 0.11f, N = 8, Shape = FruitShape.Tube, FruitLen = 0.15f, FruitR = 0.026f, FruitN = 4, Colours = new[] { "#6f9a3a", "#4f8a30", "#3f7a30", "#f3d030" } } },
            { "hops", new Spec { Kind = Kind.Climber, H = 2.6f, Leaf = 0.13f, LW = 0.09f, N = 14, Shape = FruitShape.Cone, FruitLen = 0.07f, FruitR = 0.025f, FruitN = 16, Colours = new[] { "#7fa040", "#5f9a38", "#a8c85a", "#e8e0a0" } } },
            { "zucchini", new Spec { Kind = Kind.Bush, H = 0.5f, Leaf = 0.34f, LW = 0.16f, N = 8, Shape = FruitShape.Tube, FruitLen = 0.26f, FruitR = 0.045f, FruitN = 2, Colours = new[] { "#6f9a3a", "#4a8a35", "#2f6a35", "#f3c525" } } },
            { "peppers", new Spec { Kind = Kind.Bush, H = 0.55f, Leaf = 0.1f, LW = 0.05f, N = 14, Shape = FruitShape.Cone, FruitLen = 0.1f, FruitR = 0.032f, FruitN = 8, Colours = new[] { "#5f8a35", "#4a8a30", "#d8281e", "#f4f0e0" } } },
            { "soybeans", new Spec { Kind = Kind.Bush, H = 0.65f, Leaf = 0.12f, LW = 0.07f, N = 12, Shape = FruitShape.Pod, FruitLen = 0.05f, FruitR = 0.012f, FruitN = 14, Colours = new[] { "#6f8a3a", "#4f8a30", "#9ab05a", "#e8d8f0" }, RipeLeaf = "#b8a448", RipeStem = "#a89448", RipeFruit = "#c8b070" } },
            { "peanuts", new Spec { Kind = Kind.Bush, H = 0.3f, Leaf = 0.09f, LW = 0.05f, N = 12, Shape = FruitShape.Blob, FruitR = 0.03f, FruitN = 6, Root = true, Colours = new[] { "#6f8a3a", "#4f8a30", "#d8b878", "#f3d030" } } },
            { "tobacco", new Spec { Kind = Kind.Bush, H = 1.5f, Leaf = 0.45f, LW = 0.16f, N = 10, Shape = FruitShape.Blob, FruitR = 0.02f, FruitN = 0, Colours = new[] { "#6f8a3a", "#5a8a30", "#5a8a30", "#e8a0b8" }, RipeLeaf = "#a8a840" } },
            { "flax", new Spec { Kind = Kind.Bush, H = 0.8f, Leaf = 0.05f, LW = 0.012f, N = 22, Shape = FruitShape.Blob, FruitR = 0.012f, FruitN = 0, Colours = new[] { "#8fae58", "#6fa03a", "#9a7a3a", "#5a8ad8" }, RipeLeaf = "#b8a448", RipeStem = "#b8a850" } },
            { "alfalfa", new Spec { Kind = Kind.Bush, H = 0.5f, Leaf = 0.055f, LW = 0.03f, N = 26, Shape = FruitShape.Blob, FruitR = 0.015f, FruitN = 0, Colours = new[] { "#6f9a40", "#4f9a38", "#4f9a38", "#8a5ab8" } } },
            { "oats", new Spec { Kind = Kind.Grain, H = 0.95f, N = 9, Shape = FruitShape.Pod, Colours = new[] { "#8fb048", "#7fa83e", "#a8b858", "#c8b868" }, RipeStem = "#d8c068", RipeLeaf = "#d0b860", RipeFruit = "#e0c870" } },
            { "canola", new Spec { Kind = Kind.Bush, FlowerScatter = 30, H = 1.1f, Leaf = 0.1f, LW = 0.035f, N = 18, Shape = FruitShape.Pod, FruitLen = 0.06f, FruitR = 0.006f, FruitN = 22, Colours = new[] { "#7fa84a", "#5f9a58", "#9ab04a", "#f4d530" }, RipeLeaf = "#b8a448", RipeStem = "#b8a850", RipeFruit = "#c8b070" } },
            { "barley", new Spec { Kind = Kind.Grain, H = 0.85f, N = 14, Shape = FruitShape.Cone, Colours = new[] { "#8fb048", "#7fa83e", "#a8b858", "#c8b868" }, RipeStem = "#d8b860", RipeLeaf = "#d0b058", RipeFruit = "#e0c068" } },
            { "watermelon", new Spec { Kind = Kind.VineFruit, H = 1.0f, Leaf = 0.26f, LW = 0.13f, FruitR = 0.36f, FruitLen = 1.35f, Colours = new[] { "#5f8a3a", "#4f9a3a", "#3a8a3a", "#f3d030" } } },
            { "cantaloupe", new Spec { Kind = Kind.VineFruit, H = 0.9f, Leaf = 0.22f, LW = 0.12f, FruitR = 0.28f, FruitLen = 1f, Colours = new[] { "#6f8a3a", "#5a9a3a", "#d8b878", "#f3d030" } } },
        };

        private static Color[] SpecPalette(Spec s, Phase ph)
        {
            Color stem = Hex(ph == Phase.Ripe && s.RipeStem != null ? s.RipeStem : s.Colours[0]);
            Color leaf = Hex(ph == Phase.Ripe && s.RipeLeaf != null ? s.RipeLeaf : s.Colours[1]);
            string fruitHex = ph == Phase.Ripe && s.RipeFruit != null ? s.RipeFruit : s.Colours[2];
            if (ph == Phase.Mature && s.Kind == Kind.Bush && s.Shape == FruitShape.Cone) fruitHex = "#6aa03a";   // peppers are green before they redden
            return new[] { stem, leaf, Hex(fruitHex), Hex(s.Colours[3]), Hex(s.Soil) };
        }

        private static void BuildSpec(Ctx c, Spec s)
        {
            switch (s.Kind)
            {
                case Kind.Rosette: RosetteCrop(c, s); break;
                case Kind.Allium: AlliumCrop(c, s); break;
                case Kind.Climber: ClimberCrop(c, s); break;
                case Kind.Bush: BushCrop(c, s); break;
                case Kind.Grain: GrainCrop(c, s); break;
                default: VineFruitCrop(c, s); break;
            }
        }

        private static void FruitAt(Ctx c, Spec s, Vector3 at, float scale, float angle)
        {
            switch (s.Shape)
            {
                case FruitShape.Tube:
                {
                    Vector3 d = (Dir(angle) * 0.35f + Vector3.down).normalized;
                    Tube(c.M, at, at + d * s.FruitLen * scale, s.FruitR * scale, s.FruitR * scale * 0.8f, 5, 2);
                    break;
                }
                case FruitShape.Pod:
                {
                    Vector3 d = (Dir(angle) * 0.3f + Vector3.down).normalized;
                    Tube(c.M, at, at + d * s.FruitLen * scale, s.FruitR * scale, s.FruitR * scale * 0.5f, 4, 2);
                    break;
                }
                case FruitShape.Cone:
                {
                    Vector3 d = (Dir(angle) * 0.25f + Vector3.down).normalized;
                    Tube(c.M, at, at + d * s.FruitLen * scale, s.FruitR * scale, 0.002f, 5, 2);
                    break;
                }
                default:
                    Blob(c.M, at - Vector3.up * s.FruitR * scale, s.FruitR * scale, s.FruitR * scale * 0.9f, s.FruitR * scale, 2, 6, 3);
                    break;
            }
        }

        private static void RosetteCrop(Ctx c, Spec s)
        {
            float k = Mathf.Lerp(0.3f, 1f, c.G) * (c.Wither ? 0.85f : 1f);
            int n = Mathf.RoundToInt(Mathf.Lerp(3, s.N, c.G));
            if (s.Stalks)
            {
                for (int i = 0; i < n; i++)
                {
                    float a = i * Golden;
                    Vector3 b = Dir(a) * 0.03f;
                    Vector3 top = b + Dir(a) * 0.1f * k + Vector3.up * s.H * k;
                    Tube(c.M, b, top, 0.016f, 0.01f, 4, 0);
                    Leaf(c.M, top, Dir(a), s.Leaf * k, s.LW * k, 0.1f, 0.5f * c.Droop, 1);
                }
                return;
            }
            for (int i = 0; i < n; i++)
            {
                float a = i * Golden;
                if (s.Upright)
                {
                    // beet: red-stemmed leaves standing up out of the crown of the root
                    Vector3 ub = Dir(a) * 0.02f + Vector3.up * (c.G >= 0.7f ? s.FruitR * 1.2f : 0.01f);
                    Vector3 top = ub + Dir(a) * 0.04f * k + Vector3.up * s.H * 0.6f * k;
                    Tube(c.M, ub, top, 0.009f, 0.006f, 3, 0);
                    Leaf(c.M, top, Dir(a), s.Leaf * k, s.LW * k, 0.35f, 0.7f * c.Droop, 1);
                    continue;
                }
                Vector3 b = Dir(a) * 0.01f + Vector3.up * 0.02f;
                Leaf(c.M, b, Dir(a), s.Leaf * k * R(c.Rng, 0.85f, 1.1f), s.LW * k, s.HeadKind == 1 ? 0.9f : 0.55f, (s.HeadKind == 1 ? 0.3f : 0.6f) * c.Droop, 1);
            }
            if (s.Root && c.G >= 0.4f)
            {
                // the shoulder of the root sits half out of the soil
                float r = s.FruitR * (c.Ripe ? 1f : (c.Mature ? 0.8f : 0.5f));
                Blob(c.M, Vector3.up * r * 0.75f, r, r * 0.9f, r, 2, 7, 3);
                if (c.Ripe) Cone(c.M, Vector3.up * r * 0.1f, Vector3.down * r * 0.6f, r * 0.25f, 4, 2);   // the tail of the root
            }
            if (s.HeadKind > 0 && c.G >= 0.7f)
            {
                float r = s.FruitR * (c.Ripe ? 1f : (c.Mature ? 0.75f : 0.45f));
                if (s.HeadKind == 1) Blob(c.M, Vector3.up * (r * 0.9f + 0.03f), r, r * 0.9f, r, 2, 8, 3);   // cabbage: a tight ball
                else if (s.HeadKind == 3)
                {
                    // lettuce and spinach: a heart of upright, folded-in leaves
                    Blob(c.M, Vector3.up * (r * 0.7f + 0.03f), r * 0.8f, r * 0.9f, r * 0.8f, 2, 6, 3);
                    for (int i = 0; i < 8; i++)
                        Leaf(c.M, Dir(i * Golden) * r * 0.45f + Vector3.up * 0.03f, Dir(i * Golden), r * 2.4f, r * 0.8f, 1.5f, 0.25f, 1);
                }
                else
                {
                    Tube(c.M, Vector3.up * 0.02f, Vector3.up * s.H * 0.8f * k, 0.02f, 0.016f, 4, 0);          // broccoli: stalk and florets
                    for (int i = 0; i < 5; i++)
                        Blob(c.M, Vector3.up * s.H * 0.85f * k + Dir(i * 1.26f) * r * 0.8f, r * 0.7f, r * 0.55f, r * 0.7f, 2, 5, 2);
                    Blob(c.M, Vector3.up * s.H * 0.9f * k, r * 0.8f, r * 0.6f, r * 0.8f, 2, 5, 2);
                }
            }
        }

        private static void AlliumCrop(Ctx c, Spec s)
        {
            float k = Mathf.Lerp(0.3f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            int n = Mathf.RoundToInt(Mathf.Lerp(3, s.N, c.G));
            for (int i = 0; i < n; i++)
            {
                float a = i * Golden;
                Leaf(c.M, Dir(a) * 0.012f + Vector3.up * 0.03f, Dir(a), s.H * k * R(c.Rng, 0.85f, 1.1f), 0.012f, 1.2f, 0.55f * c.Droop * (c.Ripe ? 1.6f : 1f), 1);
            }
            if (s.Root && c.G >= 0.7f)
            {
                float r = s.FruitR * (c.Ripe ? 1f : 0.6f);
                Blob(c.M, Vector3.up * r * 0.6f, r, r * 0.85f, r, 2, 6, 3);
                if (c.Ripe) Cone(c.M, Vector3.up * r * 1.4f, Vector3.up * r * 2.2f, r * 0.3f, 4, 2);
            }
            if (c.Mature && !c.Ripe && s.Flower)
            {
                Vector3 tip = Vector3.up * s.H * 0.6f + Dir(0.5f) * 0.05f;   // a garlic scape with its bulbil
                Tube(c.M, Vector3.up * 0.1f, tip, 0.006f, 0.005f, 3, 0);
                Blob(c.M, tip + Vector3.up * 0.015f, 0.012f, 0.02f, 0.012f, 3, 4, 2);
            }
        }

        private static void ClimberCrop(Ctx c, Spec s)
        {
            float H = s.H * Mathf.Lerp(0.2f, 1f, c.G) * (c.Wither ? 0.85f : 1f);
            // a tripod of poles, which the vines climb
            if (c.G >= 0.3f)
                for (int i = 0; i < 3; i++)
                    Tube(c.M, Dir(i * 2.09f) * 0.18f, new Vector3(0f, s.H * 1.02f, 0f), 0.01f, 0.007f, 3, 4);
            int vines = c.G < 0.3f ? 1 : 3;
            for (int v = 0; v < vines; v++)
            {
                float a = v * 2.09f;
                Vector3 b = Dir(a) * 0.1f;
                Vector3 lean = Dir(a + 1.5f) * 0.05f * (c.Wither ? 3f : 1f);
                Vector3 prev = b;
                int segs = 5;
                for (int i = 1; i <= segs; i++)
                {
                    float t = i / (float)segs;
                    Vector3 p = Vector3.Lerp(b, Vector3.zero, t * 0.7f) + Vector3.up * (H * t) + Dir(a + t * 5f) * 0.03f + lean * t;
                    Tube(c.M, prev, p, 0.008f, 0.006f, 3, 0);
                    Leaf(c.M, p, Dir(a + i * 2.1f), s.Leaf * Mathf.Lerp(0.5f, 1f, c.G), s.LW * Mathf.Lerp(0.5f, 1f, c.G), 0.2f, 0.6f * c.Droop, 1);
                    if (c.Mature && i >= 2 && (i + v) % 2 == 0) FruitAt(c, s, p + Dir(a + i) * 0.05f, c.Ripe ? 1f : 0.55f, a + i);
                    if (c.Mature && !c.Ripe && i == 4) Blob(c.M, p + Vector3.up * 0.03f, 0.02f, 0.012f, 0.02f, 3, 5, 2);   // flowers
                    prev = p;
                }
            }
        }

        private static void BushCrop(Ctx c, Spec s)
        {
            float H = s.H * Mathf.Lerp(0.22f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            int stems = Mathf.RoundToInt(Mathf.Lerp(1, s.H > 1f ? 2 : 4, c.G));
            int perStem = Mathf.Max(2, Mathf.RoundToInt(Mathf.Lerp(2, s.N, c.G) / stems));
            for (int st = 0; st < stems; st++)
            {
                float a = st * 2.1f + 0.4f;
                Vector3 b = Dir(a) * (stems > 1 ? 0.04f : 0f);
                Vector3 lean = Dir(a) * H * (c.Wither ? 0.45f : (s.Leaf < 0.07f ? 0.2f : 0.1f));
                Stem(c.M, b, H * R(c.Rng, 0.85f, 1f), lean, 0.012f * (0.6f + c.G * 0.5f), 0.005f, 3, 0, 3);
                for (int i = 0; i < perStem; i++)
                {
                    float t = Mathf.Lerp(0.2f, 0.98f, i / (float)Mathf.Max(1, perStem - 1));
                    Vector3 p = StemPoint(b, H, lean, t);
                    Leaf(c.M, p, Dir(a + i * Golden), s.Leaf * Mathf.Lerp(0.5f, 1f, c.G) * (1.1f - t * 0.3f), s.LW * Mathf.Lerp(0.5f, 1f, c.G), 0.3f, 0.65f * c.Droop, 1);
                }
                if (!c.Mature) continue;
                int fn = c.Ripe ? s.FruitN : Mathf.Max(1, s.FruitN / 2);
                for (int f = 0; f < fn / stems + 1 && s.FruitN > 0; f++)
                {
                    float t = Mathf.Lerp(0.3f, 0.85f, f / (float)Mathf.Max(1, fn / stems));
                    Vector3 p = StemPoint(b, H, lean, t) + Dir(a + f * 1.7f) * 0.05f;
                    if (s.Root) p = Dir(a + f * 2f) * 0.08f + Vector3.up * 0.04f;    // peanuts: shells at the soil
                    FruitAt(c, s, p, c.Ripe ? 1f : 0.6f, a + f);
                }
                if (s.Flower && !c.Ripe) Blob(c.M, StemPoint(b, H, lean, 1f) + Vector3.up * 0.02f, 0.02f, 0.014f, 0.02f, 3, 5, 2);
                if (c.Ripe && s.FruitN == 0) Blob(c.M, StemPoint(b, H, lean, 1f) + Vector3.up * 0.02f, 0.03f, 0.025f, 0.03f, 3, 5, 2);   // tobacco, flax, alfalfa: flowers on top
            }
            if (s.FlowerScatter > 0 && c.Mature && !c.Ripe)   // canola: a cloud of yellow flowers over the top of the plant (gone when it sets pods)
                for (int i = 0; i < s.FlowerScatter; i++)
                    Blob(c.M, Dir(i * 2.4f) * R(c.Rng, 0.02f, 0.17f) + Vector3.up * H * R(c.Rng, 0.55f, 1f), 0.024f, 0.014f, 0.024f, 3, 5, 2);
            if (s.Leaf < 0.07f && c.Mature)   // flax and alfalfa: a scatter of flowers over the whole plant
                for (int i = 0; i < 8; i++)
                    Blob(c.M, Dir(i * 2.4f) * R(c.Rng, 0.03f, 0.13f) + Vector3.up * H * R(c.Rng, 0.6f, 1f), 0.016f, 0.01f, 0.016f, 3, 4, 2);
        }

        private static void GrainCrop(Ctx c, Spec s)
        {
            float H = s.H * Mathf.Lerp(0.2f, 1f, c.G) * (c.Wither ? 0.8f : 1f);
            int n = Mathf.RoundToInt(Mathf.Lerp(5, s.N, c.G));
            for (int i = 0; i < n; i++)
            {
                float a = R(c.Rng, 0f, 6.28f), d = R(c.Rng, 0.02f, 0.12f) * (0.5f + c.G * 0.5f);
                Vector3 b = Dir(a) * d;
                float h = H * R(c.Rng, 0.8f, 1.1f);
                Vector3 lean = Dir(a) * R(c.Rng, 0.02f, 0.08f) * (c.Wither ? 3f : (c.Ripe ? 1.8f : 1f));
                Stem(c.M, b, h, lean, 0.007f, 0.004f, 3, 0, 2);
                if (i % 2 == 0) Leaf(c.M, StemPoint(b, h, lean, 0.35f), Dir(a + 0.8f), h * 0.4f, 0.016f, 0.45f, 0.7f * c.Droop, 1);
                if (!c.Mature) continue;
                Vector3 top = StemPoint(b, h, lean, 1f);
                if (s.Shape == FruitShape.Pod)
                {
                    // oats: a loose, drooping panicle
                    for (int k = 0; k < 3; k++)
                    {
                        Vector3 tip = top + Dir(a + k * 2.1f) * 0.06f + Vector3.down * (c.Ripe ? 0.05f : 0.02f) + Vector3.up * 0.05f;
                        Tube(c.M, top, tip, 0.003f, 0.002f, 3, 0);
                        Blob(c.M, tip, 0.008f, 0.018f, 0.008f, 2, 4, 2);
                    }
                }
                else
                {
                    // barley: a long bearded head
                    Blob(c.M, top + Vector3.up * 0.04f, 0.014f, 0.055f, 0.014f, 2, 4, 3);
                    for (int k = 0; k < 4; k++) Cone(c.M, top + Vector3.up * 0.07f, top + Vector3.up * 0.2f + Dir(k * 1.57f) * 0.025f, 0.003f, 3, 3);
                }
            }
        }

        private static void VineFruitCrop(Ctx c, Spec s)
        {
            float span = Mathf.Lerp(0.18f, s.H, c.G) * (c.Wither ? 0.85f : 1f);
            int vines = c.G < 0.3f ? 1 : 3;
            for (int v = 0; v < vines; v++)
            {
                float a = v * 2.1f + 0.4f;
                Vector3 prev = Vector3.up * 0.03f;
                for (int sg = 1; sg <= 4; sg++)
                {
                    float t = sg / 4f;
                    Vector3 p = Dir(a + Mathf.Sin(t * 3f + v) * 0.35f) * (span * t) + Vector3.up * (0.03f + 0.02f * Mathf.Sin(t * 5f));
                    Tube(c.M, prev, p, 0.014f, 0.012f, 3, 0);
                    if (sg % 2 == 0 || c.G < 0.3f)
                        Leaf(c.M, p, Dir(a + (sg % 2 == 0 ? 1.4f : -1.4f)), s.Leaf * Mathf.Lerp(0.5f, 1f, c.G), s.LW * Mathf.Lerp(0.6f, 1f, c.G), 0.28f, 0.7f * c.Droop, 1);
                    prev = p;
                }
                if (c.G > 0.5f && !c.Mature && v == 0) Blob(c.M, Dir(a + 0.2f) * span * 0.55f + Vector3.up * 0.05f, 0.03f, 0.025f, 0.03f, 3, 5, 2);   // a flower
            }
            if (c.G >= 0.65f)
            {
                float r = s.FruitR * (c.Ripe ? 1f : (c.Mature ? 0.75f : 0.28f));
                float elong = s.FruitLen > 1.2f ? 1.3f : 1f;
                Vector3 at = Dir(0.3f) * 0.12f + Vector3.up * r * 0.85f;
                Blob(c.M, at, r * elong, r * 0.9f, r, 2, 8, 3);
                Tube(c.M, at + Vector3.up * r * 0.8f, at + Vector3.up * (r * 0.8f + 0.06f) + Dir(0.9f) * 0.03f, 0.02f, 0.012f, 4, 0);
            }
        }

        // ------------------------------------------------------------------ templates

        private static readonly Dictionary<string, Mesh> Meshes = new Dictionary<string, Mesh>();

        /// <summary>The mesh of a crop at one look (cached). Five submeshes: stem, leaf, fruit, accent, soil.</summary>
        public static Mesh BuildMesh(string crop, Phase ph)
        {
            string key = crop + "/" + ph;
            if (Meshes.TryGetValue(key, out Mesh cached) && cached != null) return cached;
            int seed = 17;
            foreach (char ch in key) seed = seed * 31 + ch;
            var c = new Ctx { M = new CM(), Rng = new System.Random(seed), G = ph <= Phase.Ripe ? Growth[(int)ph] : 1f };
            c.Mature = ph >= Phase.Mature && ph != Phase.Dead;
            c.Ripe = ph == Phase.Ripe;
            c.Wither = ph == Phase.Withered;
            if (ph == Phase.Dead) Dead(c, crop);
            else
                if (Specs.TryGetValue(crop, out Spec sp)) BuildSpec(c, sp);
                else
                switch (crop)
                {
                    case "corn": Corn(c); break;
                    case "sunflower": Sunflower(c); break;
                    case "wheat": Wheat(c); break;
                    case "pumpkin": Pumpkin(c); break;
                    case "carrot": Carrot(c); break;
                    case "potato": Potato(c); break;
                    case "tomato": Tomato(c); break;
                    case "strawberry": Strawberry(c); break;
                    case "herb": Herb(c); break;
                    default: Cotton(c); break;
                }
            Mesh mesh = c.M.ToMesh("Crop_" + key.Replace('/', '_'));
            Meshes[key] = mesh;
            return mesh;
        }

        private static readonly Dictionary<string, Material[]> Mats = new Dictionary<string, Material[]>();

        /// <summary>The game materials (Vegetation shader, so they sway in the wind) of a crop look.</summary>
        public static Material[] Materials(string crop, Phase ph)
        {
            string key = crop + "/" + ph;
            if (Mats.TryGetValue(key, out Material[] cached) && cached != null && cached.Length > 0 && cached[0] != null) return cached;
            Color[] pal = Palette(crop, ph);
            Shader veg = Shader.Find("Homesteader/Vegetation");
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            var mats = new Material[Subs];
            for (int i = 0; i < Subs; i++)
            {
                var m = new Material(veg != null ? veg : lit) { hideFlags = HideFlags.DontSave };
                m.SetColor("_BaseColor", pal[i]);
                m.SetFloat("_SwayAmp", i == 4 ? 0f : 0.3f);
                m.SetFloat("_SwayRef", Mathf.Max(0.2f, Height(crop)));
                m.SetFloat("_Grow", 1f);
                mats[i] = m;
            }
            Mats[key] = mats;
            return mats;
        }

        /// <summary>A standalone model of a crop look with plain URP/Lit materials (what the asset-kit GLB export and icon renders use).</summary>
        public static GameObject MakeExportModel(string crop, Phase ph)
        {
            var go = new GameObject("Crop_" + crop + "_" + ph);
            go.AddComponent<MeshFilter>().sharedMesh = BuildMesh(crop, ph);
            Color[] pal = Palette(crop, ph);
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            var mats = new Material[Subs];
            for (int i = 0; i < Subs; i++)
            {
                mats[i] = new Material(lit) { name = new[] { "Stem", "Leaf", "Fruit", "Accent", "Soil" }[i] };
                mats[i].SetColor("_BaseColor", pal[i]);
                mats[i].SetFloat("_Smoothness", 0.15f);
            }
            go.AddComponent<MeshRenderer>().sharedMaterials = mats;
            return go;
        }

        private static GameObject _holder;

        private static GameObject MakeTemplate(string crop, Phase ph)
        {
            var go = new GameObject("Crop_" + crop + "_" + ph);
            go.transform.SetParent(_holder.transform, false);
            go.AddComponent<MeshFilter>().sharedMesh = BuildMesh(crop, ph);
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = Materials(crop, ph);
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            return go;
        }

        /// <summary>
        /// Gives every crop growth group the procedural looks as its stage prefabs (stage i of the group = sprout .. ripe) and its withered /
        /// dead versions, replacing the kit's GLB models at runtime. Called with the other procedural vegetation at world generation.
        /// </summary>
        public static void ApplyCropPrefabs()
        {
            if (_holder == null)
            {
                _holder = new GameObject("ProceduralCropTemplates");
                _holder.SetActive(false);   // templates are never drawn themselves
                Object.DontDestroyOnLoad(_holder);
            }
            else
            {
                for (int i = _holder.transform.childCount - 1; i >= 0; i--) Object.Destroy(_holder.transform.GetChild(i).gameObject);
            }
            foreach (string crop in Names)
            {
                if (!GrowthRegistry.TryGetGroup(crop, "homesteader", out GrowthGroup g) || g.Stages.Count == 0) continue;
                for (int i = 0; i < g.Stages.Count; i++)
                    g.Stages[i].Prefab = MakeTemplate(crop, (Phase)Mathf.Min(i, (int)Phase.Ripe));
                if (g.Rules == null) continue;
                if (g.Rules.Withered == null) g.Rules.Withered = new GrowthVariant { Resource = "(procedural)", Model = "(procedural)" };
                g.Rules.Withered.Prefab = MakeTemplate(crop, Phase.Withered);
                if (g.Rules.Dead == null) g.Rules.Dead = new GrowthVariant { Resource = "(procedural)", Model = "(procedural)" };
                g.Rules.Dead.Prefab = MakeTemplate(crop, Phase.Dead);
            }
        }
    }
}
