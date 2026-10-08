using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// WATER FLOW (docs/WATER_FLOW.md). Every part of a water line has a flow rating (manifest properties.flow_lph, liters an hour): pipes by their diameter, pumps, filters, spigots,
    /// faucets, the house inlet, tank fittings. The water that can get from one part to another is the NARROWEST part on the way (several ways: the best counts), and what moves is
    /// held to it: a well filling a cistern, a water pump moving stored water, a tap filling a bucket, the supply that keeps a water heater full. Nothing trips: a part that is too small
    /// only slows the water, and WAILA names the part that limits it.
    /// </summary>
    public static partial class WireNetwork
    {
        /// <summary>What a path lets through, in liters an hour (float.MaxValue: nothing on it limits), and the part that limits it.</summary>
        public struct FlowCap { public float Lph; public string By; public float Rec; }   // Rec: the share of the water that arrives (a reverse osmosis filter on the way wastes the rest)

        /// <summary>Game hours one tap fill runs (72 game seconds): a tap gives at most its flow for that long per fill.</summary>
        public const float TapFillHours = 0.02f;

        /// <summary>Liters an hour a part passes (its flow_lph) when it is a part of a water line that limits the flow; 0 = it does not.</summary>
        public static float NodeFlowLph(WireNode n)
        {
            if (n == null) return 0f;
            switch (n.Role)
            {
                case WireRole.WaterFilter:
                case WireRole.WaterSpigot:
                case WireRole.WaterInlet:
                case WireRole.WaterTank:
                case WireRole.WaterPump:
                    AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
                    return it != null ? it.flow_lph : 0f;
                default:
                    return 0f;
            }
        }

        private static string PartName(WireNode n) { return HudBindings.GetItemName(n.ItemId); }

        /// <summary>The share of its water a part passes on as product: below 1 for a reverse osmosis filter (manifest filter_recovery_pct), 1 for everything else.</summary>
        public static float RecoveryOf(WireNode n)
        {
            if (n == null || n.Role != WireRole.WaterFilter) return 1f;
            AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
            return it != null && it.filter_recovery_pct > 0f && it.filter_recovery_pct < 100f ? it.filter_recovery_pct / 100f : 1f;
        }

        /// <summary>The share of the water drawn from <paramref name="tank"/> that arrives at the end of a path (1 when no reverse osmosis filter is on it).</summary>
        private static float RecOf(Dictionary<WireNode, FlowCap> caps, WireNode tank)
        {
            return caps.TryGetValue(tank, out FlowCap c) && c.Rec > 0.01f ? c.Rec : 1f;
        }

        /// <summary>
        /// What the water lines let through from <paramref name="from"/> to every part they reach: a way is as good as its narrowest pipe or part, and of several ways the best counts.
        /// The part the start itself is counts too (a spigot).
        /// </summary>
        public static Dictionary<WireNode, FlowCap> FlowCaps(WireNode from)
        {
            var caps = new Dictionary<WireNode, FlowCap>();
            if (from == null) return caps;
            float own = NodeFlowLph(from);
            caps[from] = new FlowCap { Lph = own > 0f ? own : float.MaxValue, By = own > 0f ? PartName(from) : null, Rec = 1f };
            var queue = new Queue<WireNode>();
            queue.Enqueue(from);
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "water" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null || o.Well != null) continue;
                    FlowCap c = caps[cur];
                    float pipe = PipeFlowLph(l.WireItem);
                    if (pipe > 0f && pipe < c.Lph) { c.Lph = pipe; c.By = "the pipe (" + UnitFormat.Volume(pipe) + " an hour)"; }
                    float rec = RecoveryOf(o);
                    if (rec < 1f)
                    {
                        c.Rec *= rec;                                       // a reverse osmosis filter: only a share of what comes in comes out
                        if (c.Lph < float.MaxValue) c.Lph *= rec;
                        c.By = PartName(o);
                    }
                    float part = NodeFlowLph(o);
                    if (part > 0f && part < c.Lph) { c.Lph = part; c.By = PartName(o); }
                    if (caps.TryGetValue(o, out FlowCap had) && (had.Lph > c.Lph + 0.01f || (Mathf.Abs(had.Lph - c.Lph) <= 0.01f && had.Rec >= c.Rec))) continue;
                    caps[o] = c;
                    queue.Enqueue(o);
                }
            }
            return caps;
        }

        /// <summary>The flow a path lets through to a part: float.MaxValue when it is not reached or nothing limits it.</summary>
        private static float CapTo(Dictionary<WireNode, FlowCap> caps, WireNode n)
        {
            return caps.TryGetValue(n, out FlowCap c) ? c.Lph : float.MaxValue;
        }

        /// <summary>
        /// What the water lines can give at a tap or an inlet: the best way to a tank it can draw from (<see cref="TapSources"/>), held to the narrowest part on it. float.MaxValue when
        /// nothing limits it or it draws from nothing yet.
        /// </summary>
        public static float SupplyFlowLph(WireNode from, out string by)
        {
            by = null;
            if (from == null) return float.MaxValue;
            Dictionary<WireNode, FlowCap> caps = FlowCaps(from);
            float best = 0f;
            foreach (KeyValuePair<WireNode, int> kv in TapSources(from))
                if (caps.TryGetValue(kv.Key, out FlowCap c) && c.Lph > best) { best = c.Lph; by = c.By; }
            return best > 0f ? best : float.MaxValue;
        }

        /// <summary>The flow a building's supply line gives: the best of its inlets.</summary>
        public static float SiteSupplyFlowLph(ConstructionSite site, out string by)
        {
            by = null;
            float best = 0f;
            bool any = false;
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.WaterInlet) continue;
                AttachedObject at = n.GetComponent<AttachedObject>();
                if (at == null || at.Site != site) continue;
                float f = SupplyFlowLph(n, out string b);
                any = true;
                if (f > best) { best = f; by = b; }
            }
            return any && best > 0f ? best : float.MaxValue;
        }

        /// <summary>The flow of a tap on a building: its own rating, or the building's supply line if that is narrower.</summary>
        public static float TapFlowLph(WireNode tap, ConstructionSite site, out string by)
        {
            float supply = SiteSupplyFlowLph(site, out by);
            float own = NodeFlowLph(tap);
            if (own > 0f && own < supply) { by = PartName(tap); return own; }
            return supply;
        }

        /// <summary>The flow a water pump can move: its own rating, held to the narrowest way from the cistern it pulls to a tank with room (and on out from the pump to one).</summary>
        private static float PumpLimitLph(WireNode pump, List<List<KeyValuePair<WireNode, int>>> sides, int intake, out string by, out float rec)
        {
            by = null;
            rec = 1f;
            float rate = pump.PumpFlowLph;
            Dictionary<WireNode, FlowCap> caps = FlowCaps(pump);
            float inCap = 0f, outCap = 0f;
            string inBy = null, outBy = null;
            for (int i = 0; i < sides.Count; i++)
                foreach (KeyValuePair<WireNode, int> t in sides[i])
                {
                    if (!caps.TryGetValue(t.Key, out FlowCap c)) continue;
                    if (i == intake) { if (t.Key.WaterL > 0.5f && c.Lph > inCap) { inCap = c.Lph; inBy = c.By; } }
                    else if (t.Key.WaterL < t.Key.WaterCapacityL - 0.5f && c.Lph > outCap) { outCap = c.Lph; outBy = c.By; rec = c.Rec > 0.01f ? c.Rec : 1f; }
                }
            float limit = rate;
            if (inCap > 0f && inCap < limit) { limit = inCap; by = inBy; }
            if (outCap > 0f && outCap < limit) { limit = outCap; by = outBy; }
            return limit;
        }

        /// <summary>The part that holds back the water reaching <paramref name="n"/> (a well or a running pump pushing more than the way to it lets through), or null.</summary>
        public static string LimitedBy(WireNode n)
        {
            if (n == null) return null;
            foreach (WireNode w in WireNode.All)
            {
                if (w == null) continue;
                float rate;
                if (w.Well != null) { if (!IsEnergized(w) || !WellWantsToRun(w)) continue; rate = WellFlowLph(w); }
                else if (w.Role == WireRole.WaterPump && w.PumpRunning) rate = w.PumpFlowLph;
                else continue;
                if (rate <= 0f) continue;
                if (FlowCaps(w).TryGetValue(n, out FlowCap c) && c.Lph < rate - 0.5f && c.By != null) return c.By;
            }
            return null;
        }

        /// <summary>WAILA rows for a part of a water line: what it can pass, and what holds the water back on its way.</summary>
        public static void FlowRows(WireNode n, List<(string, string)> rows)
        {
            if (n == null) return;
            float rated = NodeFlowLph(n);
            if (rated > 0f && n.Role != WireRole.WaterPump) rows.Add(("Rated flow", UnitFormat.Volume(rated) + " an hour"));
            float rec = RecoveryOf(n);
            if (rec < 1f) rows.Add(("Recovery", Mathf.RoundToInt(rec * 100f) + "% comes out as clean water, the rest (" + UnitFormat.Volume(1f / rec - 1f) + " for every " + UnitFormat.Volume(1f) + " made) is rejected to the drain"));
            string by = n.Role == WireRole.WaterPump && n.PumpRunning ? n.FlowLimitedBy : LimitedBy(n);
            if (!string.IsNullOrEmpty(by)) rows.Add(("Limited by", by));
        }
    }
}
