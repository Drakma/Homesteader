using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The sewage side of a building (docs/SEPTIC.md). A building drains through its waste outlet, piped with black waste pipe (sewer links in
    /// <see cref="WireNetwork"/>) to a septic tank, through a macerator pump on the way if there is one. What a fixture uses (<see cref="Fixtures"/>) goes down the
    /// drain into that tank: a share of it settles as sludge (half as much when a powered macerator ground it), the rest is liquid. The tank is always kept full of
    /// liquid once it has filled: what comes in pushes the same amount out, to the tanks after it in series and through the distribution box to the leach fields,
    /// which soak it away into the ground at so many liters a day. When there is no room anywhere the system is backed up and the fixtures will not drain; when the
    /// sludge reaches half the tank it takes nothing more. The honey pot truck (a Septic Pump-Out in the Tank You app) empties a tank.
    /// </summary>
    public static class Septic
    {
        public const float SludgeShare = 0.03f;        // of what drains in, the share that settles as sludge
        public const float MaceratedShare = 0.015f;    // through a powered macerator pump: ground fine, half as much
        public const float PumpSoonAt = 1f / 3f;       // sludge at a third of the tank: it wants pumping out
        public const float FullAt = 0.5f;              // at half the tank it takes nothing more

        private static IEnumerable<WireNode> Neighbours(WireNode n)
        {
            foreach (WireLink l in WireNetwork.Links)
                if (l.Kind == "sewer" && l.Connects(n))
                {
                    WireNode o = l.Other(n);
                    if (o != null) yield return o;
                }
        }

        private static IEnumerable<WireNode> OutletsOf(ConstructionSite site)
        {
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.SewerOutlet) continue;
                AttachedObject at = n.GetComponent<AttachedObject>();
                if (at != null && at.Site == site) yield return n;
            }
        }

        /// <summary>
        /// The septic tank a building drains into: from its waste outlets along the pipe, through other buildings' outlets and macerator pumps, to the first tank.
        /// <paramref name="macerated"/>: a powered macerator is on the way. Null with the reason when it drains nowhere.
        /// </summary>
        public static WireNode TankFor(ConstructionSite site, out bool macerated, out string why)
        {
            macerated = false;
            why = null;
            bool anyOutlet = false, unpowered = false;
            // a macerator standing in the building with no pipe of its own is plumbed into its drain: everything goes through it
            bool inside = false;
            foreach (WireNode m in WireNode.All)
            {
                if (m == null || m.Role != WireRole.SewerPump || WireNetwork.Piped(m, "sewer") || WireNetwork.SiteAround(m) != site) continue;
                if (!WireNetwork.Powered(m)) { why = "The macerator pump has no power, so nothing drains through it."; return null; }
                inside = true;
            }
            var seen = new HashSet<WireNode>();
            var queue = new Queue<(WireNode node, bool mac)>();
            foreach (WireNode o in OutletsOf(site)) { anyOutlet = true; seen.Add(o); queue.Enqueue((o, inside)); }
            while (queue.Count > 0)
            {
                var cur = queue.Dequeue();
                foreach (WireNode o in Neighbours(cur.node))
                {
                    if (!seen.Add(o)) continue;
                    if (o.Role == WireRole.SepticTank) { macerated = cur.mac; return o; }
                    if (o.Role == WireRole.SewerPump)
                    {
                        if (!WireNetwork.Powered(o)) { unpowered = true; continue; }   // a macerator with no power: nothing gets through it
                        queue.Enqueue((o, true));
                    }
                    else if (o.Role == WireRole.SewerOutlet) queue.Enqueue((o, cur.mac));
                }
            }
            why = !anyOutlet ? "This building has no waste outlet: mount one outside and pipe it to a septic tank with black waste pipe." :
                  unpowered ? "The macerator pump has no power, so nothing drains through it." :
                  "The building's waste outlet is not piped to a septic tank.";
            return null;
        }

        /// <summary>Where a tank's overflow goes: the tanks after it in series, and the leach fields beyond its distribution boxes.</summary>
        private static void Downstream(WireNode tank, List<WireNode> tanks, List<WireNode> fields)
        {
            var seen = new HashSet<WireNode> { tank };
            var queue = new Queue<WireNode>();
            queue.Enqueue(tank);
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireNode o in Neighbours(cur))
                {
                    if (!seen.Add(o)) continue;
                    if (o.Role == WireRole.SepticTank) { tanks.Add(o); queue.Enqueue(o); }
                    else if (o.Role == WireRole.SepticDBox) queue.Enqueue(o);
                    else if (o.Role == WireRole.LeachField) fields.Add(o);   // the end of the line
                }
            }
        }

        private static float Room(WireNode t) { return Mathf.Max(0f, t.SewageCapacityL - t.SewageL - t.SludgeL); }

        /// <summary>
        /// Sends <paramref name="liters"/> down the building's drain (only when <paramref name="apply"/>; otherwise just says whether it would go). False with the
        /// reason when it drains nowhere or the system is backed up.
        /// </summary>
        public static bool Drain(ConstructionSite site, float liters, bool apply, out string why)
        {
            WireNode tank = TankFor(site, out bool macerated, out why);
            if (tank == null) return false;
            float cap = tank.SewageCapacityL;
            if (cap <= 0f) { why = "The septic tank is not finished."; return false; }
            if (tank.SludgeL >= cap * FullAt) { why = "The septic tank is full of solids: order a Septic Pump-Out in the Tank You app."; return false; }
            float sludge = liters * (macerated ? MaceratedShare : SludgeShare);
            float liquid = liters - sludge;
            var tanks = new List<WireNode>();
            var fields = new List<WireNode>();
            Downstream(tank, tanks, fields);
            float here = Mathf.Max(0f, cap - tank.SewageL - tank.SludgeL - sludge);
            float later = 0f;
            foreach (WireNode t in tanks) later += Room(t);
            float soak = 0f;
            foreach (WireNode f in fields) soak += Mathf.Max(0f, f.LeachStorageL - f.SewageL);
            if (liquid > here + later + soak + 0.01f)
            {
                why = fields.Count == 0 ? "The septic system is backed up: the tank is full and is not piped to a leach field (through a distribution box). Order a Septic Pump-Out, or add leach fields."
                                        : "The septic system is backed up: the leach fields are full. Give them time to soak away, or add another field.";
                return false;
            }
            if (!apply) return true;
            tank.SludgeL += sludge;
            if (tank.SewageL + tank.SludgeL > cap) tank.SewageL = Mathf.Max(0f, cap - tank.SludgeL);   // the sludge pushed some liquid on (counted in `here`)
            float put = Mathf.Min(liquid, here);
            tank.SewageL += put;
            float rest = liquid - put;
            foreach (WireNode t in tanks)
            {
                if (rest <= 0f) break;
                float p = Mathf.Min(rest, Room(t));
                t.SewageL += p;
                rest -= p;
            }
            if (rest > 0f && soak > 0f)
            {
                float share = rest / soak;   // each field takes its part of what is left, by the room it has
                foreach (WireNode f in fields) f.SewageL += Mathf.Max(0f, f.LeachStorageL - f.SewageL) * share;
            }
            return true;
        }

        /// <summary>The leach fields soak away over <paramref name="dtH"/> game hours.</summary>
        public static void Tick(float dtH)
        {
            foreach (WireNode n in WireNode.All)
                if (n != null && n.Role == WireRole.LeachField && n.SewageL > 0f) n.SewageL = Mathf.Max(0f, n.SewageL - n.LeachLpd * dtH / 24f);
        }

        /// <summary>The honey pot truck empties the tank: returns the liters it took.</summary>
        public static float PumpOut(WireNode tank)
        {
            if (tank == null) return 0f;
            float took = tank.SewageL + tank.SludgeL;
            tank.SewageL = 0f;
            tank.SludgeL = 0f;
            return took;
        }

        /// <summary>How full of solids a tank is, 0 to 1 of the point where it takes nothing more (the fullest first for the truck).</summary>
        public static float SludgeFill(WireNode tank) { float cap = tank != null ? tank.SewageCapacityL : 0f; return cap > 0f ? tank.SludgeL / (cap * FullAt) : 0f; }

        /// <summary>The look-at panel's rows for a part of a sewer line.</summary>
        public static void Rows(WireNode n, List<(string, string)> rows)
        {
            switch (n.Role)
            {
                case WireRole.SepticTank:
                {
                    float cap = n.SewageCapacityL;
                    rows.Add(("Liquid", UnitFormat.Volume(n.SewageL) + " of " + UnitFormat.Volume(cap)));
                    rows.Add(("Sludge", UnitFormat.Volume(n.SludgeL) + (cap > 0f ? " (" + Mathf.RoundToInt(n.SludgeL / cap * 100f) + "% of the tank)" : "")));
                    rows.Add(("Status", n.SludgeL >= cap * FullAt ? "Full of solids" : n.SludgeL >= cap * PumpSoonAt ? "Needs pumping out soon" : "OK"));
                    var tanks = new List<WireNode>();
                    var fields = new List<WireNode>();
                    Downstream(n, tanks, fields);
                    rows.Add(("Drains to", fields.Count > 0 ? fields.Count + (fields.Count == 1 ? " leach field" : " leach fields") : "No leach field (it backs up when full)"));
                    break;
                }
                case WireRole.LeachField:
                    rows.Add(("Holding", UnitFormat.Volume(n.SewageL) + " of " + UnitFormat.Volume(n.LeachStorageL)));
                    rows.Add(("Soaks away", UnitFormat.Volume(n.LeachLpd) + " a day"));
                    break;
                case WireRole.SepticDBox:
                {
                    int fields = 0;
                    foreach (WireNode o in Neighbours(n)) if (o.Role == WireRole.LeachField) fields++;
                    rows.Add(("Leach fields", fields.ToString()));
                    break;
                }
                case WireRole.SewerPump:
                {
                    if (!WireNetwork.Piped(n, "sewer") && WireNetwork.SiteAround(n) != null) rows.Add(("Plumbing", "Plumbed into the building's drain"));
                    bool on = WireNetwork.Powered(n);
                    rows.Add(("Power", on ? "On: it grinds the solids (half the sludge)" : "No power: nothing drains through it"));
                    AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
                    if (it != null && it.power_draw_w > 0f) rows.Add(("Rated", SolarSun.Power(it.power_draw_w)));
                    break;
                }
                case WireRole.SewerOutlet:
                {
                    AttachedObject at = n.GetComponent<AttachedObject>();
                    bool mac = false;
                    WireNode tank = at != null && at.Site != null ? TankFor(at.Site, out mac, out string _) : null;
                    rows.Add(("Drains to", tank != null ? "Septic tank" + (mac ? " (through a macerator)" : "") : "Nowhere: not piped to a septic tank"));
                    break;
                }
            }
            var names = new List<string>();
            foreach (WireNode o in Neighbours(n)) names.Add(HudBindings.GetItemName(o.ItemId));
            rows.Add(("Piped to", names.Count > 0 ? string.Join(", ", names) : "Nothing"));
        }
    }
}
