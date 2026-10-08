using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// PROPANE FLOW (docs/PROPANE_FLOW.md). A propane pipe has a flow rating by its diameter (manifest properties.flow_lph, liters an hour of LIQUID propane: 1/2 inch 7.5, 3/4 inch 15, 1 inch 30,
    /// 1-1/4 inch 55). A standby generator burns propane (its fuel_consumption_l_per_min at full load, 30 % of that idling): if the narrowest pipe between it and its tanks carries less than that, it is
    /// STARVED: it can give only the share of its rated power the line can feed, and WAILA names the pipe. Nothing trips.
    /// </summary>
    public static partial class WireNetwork
    {
        /// <summary>Liters an hour of liquid propane a propane pipe of this item carries (its flow_lph); 0 = an item that sets none.</summary>
        public static float PropanePipeFlowLph(string pipeItem)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(pipeItem);
            return it != null && it.wire_kind == "propane" ? it.flow_lph : 0f;
        }

        /// <summary>What the propane lines let through from <paramref name="from"/> to every part they reach: the narrowest pipe on the way, and of several ways the best.</summary>
        public static Dictionary<WireNode, FlowCap> PropaneCaps(WireNode from)
        {
            var caps = new Dictionary<WireNode, FlowCap>();
            if (from == null) return caps;
            caps[from] = new FlowCap { Lph = float.MaxValue, By = null, Rec = 1f };
            var queue = new Queue<WireNode>();
            queue.Enqueue(from);
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "propane" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null) continue;
                    FlowCap c = caps[cur];
                    float pipe = PropanePipeFlowLph(l.WireItem);
                    if (pipe > 0f && pipe < c.Lph)
                    {
                        AssetCatalogItem pi = HudBindings.GetCatalogItem(l.WireItem);
                        c.Lph = pipe;
                        c.By = "the propane pipe (" + (pi != null ? pi.name.Replace(" Stack", "") : "pipe") + ", " + UnitFormat.Volume(pipe) + " an hour)";
                    }
                    if (caps.TryGetValue(o, out FlowCap had) && had.Lph >= c.Lph) continue;
                    caps[o] = c;
                    queue.Enqueue(o);
                }
            }
            return caps;
        }

        /// <summary>Liters an hour of propane the lines can feed a standby generator: the best way to a tank that has propane. float.MaxValue when nothing limits it (or it has no tank yet).</summary>
        public static float PropaneFeedLph(WireNode gen, out string by)
        {
            by = null;
            Dictionary<WireNode, FlowCap> caps = PropaneCaps(gen);
            float best = 0f;
            bool any = false;
            foreach (PlacedObject p in GenTanks(gen))
            {
                if (LiquidRules.Held(p.ItemId, p.WireUsed) <= 0.01f) continue;
                WireNode tn = p.GetComponent<WireNode>();
                if (tn == null) continue;
                any = true;
                float cap = caps.TryGetValue(tn, out FlowCap c) ? c.Lph : float.MaxValue;
                if (cap > best) { best = cap; by = caps.TryGetValue(tn, out FlowCap c2) ? c2.By : null; }
            }
            return any ? best : float.MaxValue;
        }

        /// <summary>The watts a standby generator can really give: its rating, or less when the propane line cannot feed full load (it burns 30 % idling and the rest with the load). Sets <see cref="WireNode.FlowLimitedBy"/>.</summary>
        public static float GenCapableW(WireNode g, AssetCatalogItem gi)
        {
            if (g != null) g.FlowLimitedBy = null;
            if (g == null || gi == null) return 0f;
            float full = gi.fuel_lpm * 60f;
            if (full <= 0f) return gi.max_power_w;
            float feed = PropaneFeedLph(g, out string by);
            if (feed >= full) return gi.max_power_w;
            g.FlowLimitedBy = by;
            return gi.max_power_w * Mathf.Clamp01((feed / full - 0.3f) / 0.7f);
        }

        /// <summary>WAILA rows for a standby generator's fuel line: what the pipe feeds against what full load burns, and what limits it.</summary>
        public static void PropaneRows(WireNode g, List<(string, string)> rows)
        {
            AssetCatalogItem gi = HudBindings.GetCatalogItem(g.ItemId);
            if (gi == null || gi.fuel_lpm <= 0f) return;
            float full = gi.fuel_lpm * 60f;
            float feed = PropaneFeedLph(g, out string by);
            if (feed >= float.MaxValue) return;
            rows.Add(("Fuel line", UnitFormat.Volume(feed) + " an hour for " + UnitFormat.Volume(full) + " at full load"));
            if (feed < full - 0.01f && !string.IsNullOrEmpty(by))
                rows.Add(("Limited by", by + ": it can give " + SolarSun.Power(GenCapableW(g, gi)) + " of " + SolarSun.Power(gi.max_power_w)));
        }
    }
}
