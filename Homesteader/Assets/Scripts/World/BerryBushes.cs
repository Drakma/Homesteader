using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>One berry bush scattered in the world (baked into a chunk mesh by ProceduralVegetation.Combine).</summary>
    public sealed class BerryBush
    {
        public int Kind;                 // 0 elderberry, 1 blueberry, 2 raspberry, 3 huckleberry, 4 haskap
        public string AssetId;           // the kit asset that carries its pick rules (the 'fruiting' schema)
        public Vector3 Position;         // world, at the base
        public Mesh Mesh;                // the chunk mesh the bush lives in
        public (int, int, bool) ChunkKey;
        public int VertStart, VertCount;
        public int FruitFirst, FruitPer, FruitTotal;   // where the berries are in the bush's vertices, vertices per berry, berries
        public uint Gone;                // bit i set = berry i is picked
        public uint Drawn = uint.MaxValue;   // bit i set = berry i is drawn in the baked mesh
        public float PickedUntil;        // game day all the picked berries are back (set at every pick)
        public Vector3[] FruitOrig;      // the berries' original vertices
        public int PickStamp;
    }

    /// <summary>
    /// Berry bushes you can pick by hand, like the fruit trees: right-click with the kit's tool (the basket) and ONE berry comes off, the left hand does
    /// the reach, and one of each of the kit's drops goes to the toolbar. The rules come from the bush asset's 'fruiting' add-on schema
    /// (bush_blueberry and so on): tools, drops, regrow_days. The picked berries all return regrow_days after the latest pick.
    /// </summary>
    public static class BerryBushes
    {
        public static readonly string[] AssetIds = { "bush_elderberry", "bush_blueberry", "bush_raspberry", "bush_huckleberry", "bush_haskap" };
        public static string AssetFor(int kind) => kind >= 0 && kind < AssetIds.Length ? AssetIds[kind] : null;

        private const float GridCell = 6f;
        private const float PickRadius = 0.75f;
        private const float ReachMetres = 4f;

        private static readonly List<BerryBush> All = new List<BerryBush>();
        private static readonly Dictionary<long, List<BerryBush>> Grid = new Dictionary<long, List<BerryBush>>();
        private static readonly Dictionary<Mesh, (int first, int per, int total)> Layouts = new Dictionary<Mesh, (int, int, int)>();
        private static readonly List<BerryBush> Picked = new List<BerryBush>();
        private static int _pickStamp;
        private static float _lastNotify;
        private static Ticker _ticker;

        public static int Count => All.Count;

        /// <summary>The first registered bush (used by editor tests).</summary>
        public static BerryBush First => All.Count > 0 ? All[0] : null;

        public static void Clear()
        {
            All.Clear();
            Grid.Clear();
            Layouts.Clear();
            Picked.Clear();
        }

        /// <summary>Bushes whose base is inside an area are gone (the ground under a foundation was cleared; the mesh part is SiteClearing's).</summary>
        public static void ClearIn(System.Func<float, float, bool> inside)
        {
            foreach (BerryBush b in All)
            {
                if (b.FruitTotal <= 0 || !inside(b.Position.x, b.Position.z)) continue;
                b.FruitTotal = 0;   // nothing left to pick
                b.Gone = 0;
            }
        }

        public static void SetLayout(Mesh bushMesh, int firstVert, int perBerry, int total) { Layouts[bushMesh] = (firstVert, perBerry, total); }

        public static void Register(BerryBush b, Mesh sourceMesh)
        {
            if (Layouts.TryGetValue(sourceMesh, out var l)) { b.FruitFirst = l.first; b.FruitPer = l.per; b.FruitTotal = Mathf.Clamp(l.total, 0, 32); }
            All.Add(b);
            long key = Key(Mathf.FloorToInt(b.Position.x / GridCell), Mathf.FloorToInt(b.Position.z / GridCell));
            if (!Grid.TryGetValue(key, out List<BerryBush> cell)) { cell = new List<BerryBush>(); Grid[key] = cell; }
            cell.Add(b);
        }

        public static void Started(Transform root)
        {
            if (root != null && _ticker == null) _ticker = root.gameObject.AddComponent<Ticker>();
        }

        private static long Key(int x, int z) => ((long)x << 32) ^ (uint)z;

        // ------------------------------------------------------------------ rules (the kit)

        private static AssetCatalogItem Rules(BerryBush b) => HudBindings.GetCatalogItem(b.AssetId);

        public static bool HasRules(BerryBush b)
        {
            var r = Rules(b);
            return r != null && r.fruiting_drops != null && r.fruiting_drops.Count > 0;
        }

        private static uint Full(BerryBush b) => b.FruitTotal >= 32 ? uint.MaxValue : (1u << b.FruitTotal) - 1u;

        public static int Left(BerryBush b)
        {
            if (b.PickedUntil > 0f && VegetationSeasons.GrowthDay >= b.PickedUntil) { b.Gone = 0; b.PickedUntil = 0f; }
            int n = 0;
            for (uint m = Full(b) & ~b.Gone; m != 0; m &= m - 1) n++;
            return n;
        }

        /// <summary>Ripe berries on it, the kit gives rules for it, and it is the season (winter bushes bear nothing).</summary>
        public static bool CanPick(BerryBush b) => b != null && b.FruitTotal > 0 && HasRules(b) && InSeason() && Left(b) > 0;

        private static bool InSeason()
        {
            return VegetationSeasons.SeasonPosition() >= 1f;   // winter is [0, 1): from 1 Dec to the start of spring
        }

        // ------------------------------------------------------------------ finding the bush under the cursor

        public static bool TryPick(Ray ray, out BerryBush picked)
        {
            picked = null;
            if (All.Count == 0) return false;
            float bestT = float.MaxValue;
            int stamp = ++_pickStamp;
            Vector3 o = ray.origin, d = ray.direction;
            float t0, t1;
            if (Mathf.Abs(d.y) > 1e-4f) { t0 = (3f - o.y) / d.y; t1 = (-2f - o.y) / d.y; if (t0 > t1) { float tmp = t0; t0 = t1; t1 = tmp; } t0 = Mathf.Max(t0, 0f); }
            else { t0 = 0f; t1 = 200f; }
            if (t1 <= t0) return false;
            Vector3 p0 = o + d * t0, p1 = o + d * t1;
            float len = new Vector2(p1.x - p0.x, p1.z - p0.z).magnitude;
            int steps = Mathf.Clamp(Mathf.CeilToInt(len / (GridCell * 0.5f)) + 1, 1, 200);
            for (int i = 0; i <= steps; i++)
            {
                Vector3 p = Vector3.Lerp(p0, p1, i / (float)steps);
                int cx = Mathf.FloorToInt(p.x / GridCell), cz = Mathf.FloorToInt(p.z / GridCell);
                for (int ox = -1; ox <= 1; ox++)
                    for (int oz = -1; oz <= 1; oz++)
                    {
                        if (!Grid.TryGetValue(Key(cx + ox, cz + oz), out List<BerryBush> cell)) continue;
                        for (int k = 0; k < cell.Count; k++)
                        {
                            BerryBush b = cell[k];
                            if (b.PickStamp == stamp) continue;
                            b.PickStamp = stamp;
                            Vector3 c = b.Position + Vector3.up * 0.45f;
                            float t = Vector3.Dot(c - o, d);
                            if (t < 0f) continue;
                            float dist = Vector3.Distance(o + d * t, c);
                            if (dist <= PickRadius && t < bestT) { bestT = t; picked = b; }
                        }
                    }
            }
            return picked != null;
        }

        // ------------------------------------------------------------------ picking

        public static bool TryPickBerry(BerryBush b, Transform player, string heldId)
        {
            if (!HasRules(b)) return false;
            if (!InSeason()) { Notify("Winter", "There are no berries on the bush in winter."); return false; }
            if (Left(b) <= 0) { Notify("Picked clean", "Every berry is picked: they grow back in " + Mathf.CeilToInt(Mathf.Max(b.PickedUntil - VegetationSeasons.GrowthDay, 0f)) + " days."); return false; }
            var rules = Rules(b);
            string need = rules.fruiting_tools != null && rules.fruiting_tools.Count > 0 ? string.Join(",", rules.fruiting_tools) : null;
            if (!string.IsNullOrEmpty(need) && !GrowthRegistry.ToolMatches(need, heldId))
            {
                Notify("Need a tool", $"You need {ToolNames(rules.fruiting_tools)} in your active slot to pick these.");
                return false;
            }
            if (player != null)
            {
                Vector3 d = b.Position - player.position;
                d.y = 0f;
                if (d.magnitude > ReachMetres) { Notify("Too far", "Move closer to pick the berries."); return false; }
            }
            if (FruitPickAnimator.Busy) return true;   // the player's hand is still on the last one

            // The whole bush at once: every berry still on it, picked in a few quick cycles while the player kneels. The berries are dealt out round the
            // cycles (a handful each); a cycle's berries come off the bush when its hand closes and go to the toolbar when it reaches the basket.
            uint left = Full(b) & ~b.Gone;
            var bits = new List<int>();
            for (int i = 0; i < 32; i++) if ((left & (1u << i)) != 0) bits.Add(i);
            if (bits.Count == 0) return false;
            for (int i = bits.Count - 1; i > 0; i--) { int j = Random.Range(0, i + 1); (bits[i], bits[j]) = (bits[j], bits[i]); }
            int cycles = Mathf.Clamp(Mathf.CeilToInt(bits.Count / 5f), 1, 4);
            var groups = new List<int>[cycles];
            for (int c = 0; c < cycles; c++) groups[c] = new List<int>();
            for (int i = 0; i < bits.Count; i++) groups[i % cycles].Add(bits[i]);

            void TakeOff(int c)
            {
                foreach (int bit in groups[c]) b.Gone |= 1u << bit;
                b.PickedUntil = VegetationSeasons.GrowthDay + Mathf.Max(1f, rules.fruiting_regrow_days);
                if (!Picked.Contains(b)) Picked.Add(b);
                Sync();
            }

            void IntoBasket(int c)
            {
                var drops = new List<GrowthDrop>();
                foreach (string id in rules.fruiting_drops) drops.Add(new GrowthDrop { ItemId = id, Min = groups[c].Count, Max = groups[c].Count });
                if (!GrowthDrop.Give(drops)) Notify("Toolbar full", "Some of the berries didn't fit and were lost.");
            }

            var positions = new Vector3[cycles];
            for (int c = 0; c < cycles; c++) positions[c] = BerryWorldPosition(b, groups[c][0]);
            Color colour = BerryColour(b.Kind);
            if (player != null && FruitPickAnimator.TryBeginSequence(player, positions, colour, TakeOff, IntoBasket, kneel: true, speed: 2f)) return true;
            for (int c = 0; c < cycles; c++) { TakeOff(c); IntoBasket(c); }
            return true;
        }

        private static Color BerryColour(int kind)
        {
            switch (kind)
            {
                case 0: return new Color(0.17f, 0.11f, 0.24f);
                case 1: return new Color(0.21f, 0.32f, 0.79f);
                case 2: return new Color(0.84f, 0.1f, 0.24f);
                case 3: return new Color(0.23f, 0.16f, 0.45f);
                default: return new Color(0.26f, 0.32f, 0.72f);
            }
        }

        private static Vector3 BerryWorldPosition(BerryBush b, int bit)
        {
            Vector3 fallback = b.Position + Vector3.up * 0.6f;
            if (b.Mesh == null || b.FruitPer <= 0) return fallback;
            List<Vector3> verts = ForestTrees.VertexListFor(b.Mesh);
            int start = b.VertStart + b.FruitFirst + bit * b.FruitPer;
            if (start + b.FruitPer > verts.Count) return fallback;
            Vector3 sum = Vector3.zero;
            for (int k = 0; k < b.FruitPer; k++) sum += b.FruitOrig != null ? b.FruitOrig[bit * b.FruitPer + k] : verts[start + k];
            return sum / b.FruitPer;
        }

        /// <summary>Shows or hides each berry of the picked bushes to match its mask (and brings them all back when the time is up).</summary>
        private static void Sync()
        {
            HashSet<Mesh> dirty = null;
            for (int i = Picked.Count - 1; i >= 0; i--)
            {
                BerryBush b = Picked[i];
                if (b.Mesh == null || b.FruitTotal <= 0 || b.FruitPer <= 0) { Picked.RemoveAt(i); continue; }
                Left(b);   // returns the berries when their time is up
                uint want = Full(b) & ~b.Gone;
                uint have = b.Drawn & Full(b);
                if (want != have)
                {
                    List<Vector3> verts = ForestTrees.VertexListFor(b.Mesh);
                    int start = b.VertStart + b.FruitFirst;
                    int count = b.FruitPer * b.FruitTotal;
                    if (start + count <= verts.Count)
                    {
                        if (b.FruitOrig == null) b.FruitOrig = verts.GetRange(start, count).ToArray();
                        uint changed = want ^ have;
                        for (int f = 0; f < b.FruitTotal; f++)
                        {
                            if ((changed & (1u << f)) == 0) continue;
                            bool show = (want & (1u << f)) != 0;
                            for (int k = 0; k < b.FruitPer; k++) verts[start + f * b.FruitPer + k] = show ? b.FruitOrig[f * b.FruitPer + k] : b.Position;
                        }
                        b.Drawn = want;
                        if (dirty == null) dirty = new HashSet<Mesh>();
                        dirty.Add(b.Mesh);
                    }
                }
                if (b.Gone == 0 && b.PickedUntil == 0f) Picked.RemoveAt(i);
            }
            if (dirty != null) foreach (Mesh m in dirty) m.SetVertices(ForestTrees.VertexListFor(m));
        }

        private sealed class Ticker : MonoBehaviour
        {
            private float _next;
            private void Update()
            {
                if (Picked.Count == 0 || Time.unscaledTime < _next) return;
                _next = Time.unscaledTime + 1.5f;
                Sync();
            }
        }

        // ------------------------------------------------------------------ hover panel

        public static void Describe(BerryBush b, out string title, List<(string, string)> rows)
        {
            title = HudBindings.GetItemName(b.AssetId);
            rows.Clear();
            var rules = Rules(b);
            if (rules == null || !HasRules(b)) return;
            if (!InSeason()) { rows.Add(("Berries", "None in winter")); return; }
            int left = Left(b);
            rows.Add(("Berries", left > 0 ? $"{left} of {b.FruitTotal} left" : $"All picked: back in {Mathf.CeilToInt(Mathf.Max(b.PickedUntil - VegetationSeasons.GrowthDay, 0f))} days"));
            if (rules.fruiting_tools != null && rules.fruiting_tools.Count > 0) rows.Add(("@tools|Pick with", string.Join(",", rules.fruiting_tools)));
            else rows.Add(("Pick with", "Nothing (by hand)"));
        }

        private static string ToolNames(List<string> tools)
        {
            var names = new List<string>();
            if (tools != null)
                foreach (string s in tools)
                    names.Add(s.StartsWith("#") ? s.Substring(1).Replace('_', ' ') : HudBindings.GetItemName(s));
            return names.Count > 0 ? string.Join(", ", names) : "nothing";
        }

        private static void Notify(string title, string message)
        {
            if (Time.unscaledTime - _lastNotify < 2.5f) return;
            _lastNotify = Time.unscaledTime;
            ToastNotificationSystem.ShowWarning(title, message);
        }

        // ------------------------------------------------------------------ saves

        public static List<Vector3> SavedPicked()
        {
            var list = new List<Vector3>();
            foreach (BerryBush b in Picked)
                if (b.PickedUntil > VegetationSeasons.GrowthDay) list.Add(new Vector3(b.Position.x, b.Position.z, b.PickedUntil));
            return list;
        }

        public static List<int> SavedPickedMasks()
        {
            var list = new List<int>();
            foreach (BerryBush b in Picked)
                if (b.PickedUntil > VegetationSeasons.GrowthDay) list.Add((int)b.Gone);
            return list;
        }

        public static void ApplyPicked(List<Vector3> picked, List<int> masks)
        {
            if (picked == null) return;
            for (int pi = 0; pi < picked.Count; pi++)
            {
                Vector3 p = picked[pi];
                BerryBush best = null;
                float bestD = 0.6f * 0.6f;
                foreach (BerryBush b in All)
                {
                    float dx = b.Position.x - p.x, dz = b.Position.z - p.y;
                    float d = dx * dx + dz * dz;
                    if (d < bestD) { bestD = d; best = b; }
                }
                if (best == null) continue;
                best.PickedUntil = p.z;
                best.Gone = masks != null && pi < masks.Count ? (uint)masks[pi] : Full(best);
                if (!Picked.Contains(best)) Picked.Add(best);
            }
            Sync();
        }
    }
}
