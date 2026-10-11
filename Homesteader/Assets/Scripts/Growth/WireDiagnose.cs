using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// WHY A BUILDING IS MISSING A UTILITY. WAILA used to list "Connected" for every utility a building had and said nothing about one it lacked. It now lists a utility only when
    /// something is wrong, and says what: a tripped or switched-off part, a breaker box on the inside, a missing link in the inverter chain, an empty tank, a pump with no power, the
    /// first break in the network. The broken part itself says it too, on its own card (OverloadRows: "Tripped: overload").
    /// </summary>
    public static partial class WireNetwork
    {
        private static string Nm(WireNode n) { return HudBindings.GetItemName(n.ItemId); }

        private static string BreakText(WireNode n) { return Nm(n) + (n.Tripped ? " is tripped" : " is switched off"); }

        /// <summary>What stops the building having electricity, or null when it has it (or has no breaker box to bring any: nothing is expected of it).</summary>
        public static string PowerProblem(ConstructionSite site)
        {
            if (site == null || AttachedObject.HasPower(site)) return null;
            AttachedObject box = null;
            foreach (AttachedObject a in AttachedObject.All)
                if (a != null && a.Site == site && a.ProvidesPower) { box = a; break; }
            if (box == null) return null;
            if (!box.Exterior) return "The breaker box is on the inside: it only brings power in from outside";
            WireNode bn = box.GetComponent<WireNode>();
            if (bn == null) return null;
            if (bn.Tripped) return Nm(bn) + " is tripped";
            var seen = new HashSet<WireNode> { bn };
            var queue = new Queue<WireNode>();
            queue.Enqueue(bn);
            string first = null;
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "ac" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null || !seen.Add(o)) continue;
                    if (o.Open) { if (first == null) first = BreakText(o); continue; }
                    if (o.Role == WireRole.Inverter) { string d = InverterProblem(o); if (d != null && first == null) first = d; }
                    else if (o.Role == WireRole.WindTurbine) { ConstructionSite ws = o.GetComponent<ConstructionSite>(); if (ws == null || !ws.Finished) { if (first == null) first = Nm(o) + " is not finished"; } }
                    else if (o.Role == WireRole.WallEntry || o.Role == WireRole.AcPanel || o.Role == WireRole.Disconnect) queue.Enqueue(o);
                }
            }
            if (seen.Count == 1) return "Nothing is wired to the breaker box";
            return first ?? "No inverter is wired to the breaker box";
        }

        /// <summary>What is wrong on the DC side of an inverter: a tripped or switched-off part in its chain, else the first link missing from it. Null when the chain is complete.</summary>
        private static string InverterProblem(WireNode inv)
        {
            var seen = new HashSet<WireNode> { inv };
            var queue = new Queue<WireNode>();
            queue.Enqueue(inv);
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind == "ac" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null || !seen.Add(o)) continue;
                    if (o.Open) return BreakText(o);
                    queue.Enqueue(o);
                }
            }
            WireRole miss = MissingFrom(inv);
            return miss == WireRole.None ? null : Nm(inv) + " is missing " + WireNode.RoleName(miss) + " in its chain";
        }

        /// <summary>Why a building's taps run dry, or null when it has water (or no inlet or tap to give any: nothing is expected of it).</summary>
        public static string WaterProblem(ConstructionSite site)
        {
            if (site == null) return null;
            WaterFor(site, out float all, out _);
            if (all > 0.5f) return null;
            bool fitted = false, tanks = false;
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || (n.Role != WireRole.WaterInlet && n.Role != WireRole.WaterSpigot)) continue;
                AttachedObject at = n.GetComponent<AttachedObject>();
                if (at != null && at.Site == site) { fitted = true; break; }
            }
            if (!fitted) return null;
            foreach (WireNode t in PlumbedTanks(site)) { tanks = true; break; }
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.WaterInlet) continue;
                AttachedObject at = n.GetComponent<AttachedObject>();
                if (at == null || at.Site != site) continue;
                foreach (KeyValuePair<WireNode, int> kv in TapSources(n)) { tanks = true; break; }
            }
            foreach (WireNode p in WireNode.All)
                if (p != null && p.Role == WireRole.WaterPump && !p.PumpRunning && !Powered(p) && SiteAround(p) == site) return Nm(p) + " has no power";
            return tanks ? "The water tanks are empty" : "No water tank is plumbed to it";
        }

        /// <summary>Why a building's network jack has no internet (the first break back to the dish), or null when it is online or has no jack.</summary>
        public static string InternetProblem(ConstructionSite site)
        {
            if (site == null || Net.StructureLink(site) != 1) return null;
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.NetJack) continue;
                AttachedObject a = n.GetComponent<AttachedObject>();
                if (a != null && a.Site == site) return Net.Break(n);
            }
            return null;
        }
    }
}
