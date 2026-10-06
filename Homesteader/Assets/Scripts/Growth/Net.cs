using System.Collections;
using System.Collections.Generic;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The homestead's network (docs/INTERNET.md). The gear is cabled with Cat6 (the wire cutters, like any wire; kind "net") in the order
    /// dish or yagi, router, switch (optional), device, and every cable takes a PORT at each end: a device joins no more cables than it has ports,
    /// PoE devices (a camera, an access point, a yagi) only on PoE ports and everything else only on standard ones. The internet comes in at ONE
    /// satellite dish per network (its bandwidth, less in bad weather), goes through a router and on over the cables; a pair of yagi antennas aimed
    /// at each other carries it across the yard. A cable inside a building is in the walls (not drawn); one that comes in from outside goes through
    /// an Ethernet wall jack. A router's or an access point's Wi-Fi reaches the phone and the TVs within its range. Nothing here is saved: it is
    /// all read off the placed gear and its cables.
    /// </summary>
    public static class Net
    {
        public const float PoeW = 15f;        // what a PoE port gives
        public const float MaxCable = 100f;   // a Cat6 run is at most this long
        public const float FullAimDeg = 20f;  // a yagi aimed within this of its partner: the full link
        public const float HalfAimDeg = 45f;  // within this: half of it; wider: no link

        public static bool IsNet(WireRole r) { return r >= WireRole.NetDish && r <= WireRole.NetDevice; }
        private static bool Hub(WireRole r) { return r == WireRole.NetRouter || r == WireRole.NetSwitch || r == WireRole.NetRack; }
        private static bool End(WireRole r) { return r == WireRole.NetAp || r == WireRole.NetCamera || r == WireRole.NetDevice; }

        /// <summary>Which two kinds of gear a cable joins: dish to router, yagi to router or switch, router and switches to each other, any of those to a device. A wall jack takes any of them.</summary>
        public static bool Pair(WireRole a, WireRole b)
        {
            if (a == WireRole.NetAntenna || b == WireRole.NetAntenna) return false;   // a cellular booster only needs power
            if (a == WireRole.NetJack || b == WireRole.NetJack) return true;          // (what is behind the jack is checked in CanJoin)
            if (a == WireRole.NetDish || b == WireRole.NetDish) { WireRole o = a == WireRole.NetDish ? b : a; return o == WireRole.NetRouter || o == WireRole.NetRack; }
            if (a == WireRole.NetYagi || b == WireRole.NetYagi) return Hub(a == WireRole.NetYagi ? b : a);
            if (Hub(a) && Hub(b)) return true;
            return (Hub(a) && End(b)) || (Hub(b) && End(a));
        }

        public static string WhyNot(WireNode a, WireNode b)
        {
            if (a.Role == WireRole.NetAntenna || b.Role == WireRole.NetAntenna) return "A cellular antenna takes no cable: it only needs power.";
            if (!IsNet(a.Role) || !IsNet(b.Role)) return "A network cable joins network gear, not a " + WireNode.RoleName(IsNet(a.Role) ? b.Role : a.Role) + ".";
            if (a.Role == WireRole.NetDish || b.Role == WireRole.NetDish) return "A dish is cabled to a router. The order is dish or yagi, router, switch, device.";
            return "A " + WireNode.RoleName(a.Role) + " is not cabled to a " + WireNode.RoleName(b.Role) + ". The order is dish or yagi, router, switch, device.";
        }

        private static AssetCatalogItem Cat(string id) { return HudBindings.GetCatalogItem(id); }

        private static ConstructionSite SiteOf(WireNode n)
        {
            AttachedObject a = n.GetComponent<AttachedObject>();
            return a != null && a.Site != null ? a.Site : WireNetwork.SiteAround(n);
        }

        /// <summary>True when both are network gear in (or on) the same building: their cable is in the walls.</summary>
        public static bool SameBuilding(WireNode a, WireNode b)
        {
            if (a == null || b == null || !IsNet(a.Role) || !IsNet(b.Role)) return false;
            ConstructionSite sa = SiteOf(a);
            return sa != null && sa == SiteOf(b);
        }

        /// <summary>Inside a building's rooms (not a wall jack, which is on both sides, and not a thing mounted on the outside).</summary>
        private static bool Indoors(WireNode n)
        {
            if (n.Role == WireRole.NetJack) return false;
            AttachedObject a = n.GetComponent<AttachedObject>();
            if (a != null) return a.Site != null && !a.Exterior && a.Surface != "roof";
            return WireNetwork.SiteAround(n) != null;
        }

        private static IEnumerable<AssetCatalogItem> Parts(WireNode n)
        {
            if (n.Role == WireRole.NetRack)
            {
                NetRack rack = n.GetComponent<NetRack>();
                if (rack != null) foreach (string id in rack.Items) { AssetCatalogItem it = Cat(id); if (it != null) yield return it; }
            }
            else { AssetCatalogItem it = Cat(n.ItemId); if (it != null) yield return it; }
        }

        /// <summary>True for a router, and for a rack with a router in it.</summary>
        public static bool Routes(WireNode n)
        {
            if (n.Role == WireRole.NetRouter) return true;
            if (n.Role != WireRole.NetRack) return false;
            foreach (AssetCatalogItem it in Parts(n)) if (it.wire_role == "net_router") return true;
            return false;
        }

        /// <summary>A device that runs from the cable and so only goes on a PoE port (a camera, an access point, a yagi).</summary>
        public static bool NeedsPoe(WireNode n) { AssetCatalogItem it = Cat(n.ItemId); return it != null && it.poe_powered; }

        /// <summary>How many cables it takes: its ports (a rack: those of everything in it). A wall jack has two (one each side); a dish, yagi or device one.</summary>
        public static int Ports(WireNode n)
        {
            if (n.Role == WireRole.NetJack) return 2;
            int sum = 0;
            foreach (AssetCatalogItem it in Parts(n)) sum += Mathf.Max(0, it.net_ports);
            return sum > 0 || Hub(n.Role) ? sum : 1;
        }

        /// <summary>How many of its ports are PoE ports (15 W each): they take PoE devices, the rest take everything else.</summary>
        public static int PoePorts(WireNode n)
        {
            int sum = 0;
            foreach (AssetCatalogItem it in Parts(n)) if (it.poe) sum += Mathf.Max(0, it.net_ports);
            return sum;
        }

        /// <summary>The gear at the far end of a cable from <paramref name="from"/> that starts towards <paramref name="via"/>: through any wall jacks on the way. Null when it ends at a jack with nothing behind it.</summary>
        private static WireNode Beyond(WireNode from, WireNode via)
        {
            for (int guard = 0; guard < 16 && via != null && via.Role == WireRole.NetJack; guard++)
            {
                WireNode next = null;
                foreach (WireLink l in WireNetwork.Links)
                {
                    if (l.Kind != "net" || !l.Connects(via)) continue;
                    WireNode o = l.Other(via);
                    if (o != null && o != from) { next = o; break; }
                }
                from = via;
                via = next;
            }
            return via;
        }

        /// <summary>Its ports in use, by kind. A hub's cables to other hubs take standard ports first, then PoE ones. skip: a neighbour whose cable is not counted.</summary>
        private static void Usage(WireNode n, WireNode skip, out int standard, out int poe, out bool wan)
        {
            standard = 0; poe = 0; wan = false;
            int hubs = 0;
            bool routes = Routes(n);
            foreach (WireLink l in WireNetwork.Links)
            {
                if (l.Kind != "net" || !l.Connects(n)) continue;
                WireNode o = l.Other(n);
                if (o == null || o == skip) continue;
                WireNode p = Beyond(n, o);
                if (p != null && p.Role == WireRole.NetDish && routes && !wan) wan = true;   // the dish goes in the WAN port, which is not one of its ports
                else if (p != null && NeedsPoe(p)) poe++;
                else if (p != null && Hub(p.Role)) hubs++;
                else standard++;
            }
            int poeCap = PoePorts(n), stdCap = Ports(n) - poeCap;
            int inStd = Mathf.Clamp(stdCap - standard, 0, hubs);
            standard += inStd;
            poe += hubs - inStd;
        }

        /// <summary>The ports in use (standard and PoE together; a router's WAN port is not one of them).</summary>
        public static int Used(WireNode n) { Usage(n, null, out int s, out int p, out _); return s + p; }

        private static bool HasDish(WireNode n) { Usage(n, null, out _, out _, out bool wan); return wan; }

        /// <summary>Whether <paramref name="n"/> has a port of the right kind free for <paramref name="peer"/> (the gear at the far end; null = not known yet, any port does).</summary>
        private static bool PortFor(WireNode n, WireNode peer, WireNode skip, out string reason)
        {
            reason = null;
            string name = HudBindings.GetItemName(n.ItemId);
            if (!Hub(n.Role))
            {
                int cables = 0;
                foreach (WireLink l in WireNetwork.Links) if (l.Kind == "net" && l.Connects(n) && l.Other(n) != skip) cables++;
                if (cables >= Ports(n)) { reason = Ports(n) == 1 ? name + " has one port and it is in use." : "Both ports of " + name + " are in use."; return false; }
                return true;
            }
            if (n.Role == WireRole.NetRack && Ports(n) == 0) { reason = "The rack is empty: put a router or a switch in it first (left click with it in hand)."; return false; }
            Usage(n, skip, out int std, out int poe, out bool wan);
            int poeCap = PoePorts(n), stdCap = Ports(n) - poeCap;
            if (peer != null && peer.Role == WireRole.NetDish)
            {
                if (!Routes(n)) { reason = "A dish is cabled to a router: there is none in the rack."; return false; }
                if (wan) { reason = name + " already has a dish in its WAN port."; return false; }
                return true;
            }
            if (peer != null && NeedsPoe(peer))
            {
                if (poeCap == 0) { reason = "A " + WireNode.RoleName(peer.Role) + " runs from its cable: plug it into a PoE port (a PoE switch or injector). " + name + " has none."; return false; }
                if (poe >= poeCap) { reason = "All " + poeCap + " PoE ports of " + name + " are in use."; return false; }
                return true;
            }
            if (peer != null && !Hub(peer.Role))
            {
                if (stdCap == 0) { reason = name + " has only PoE ports: a " + WireNode.RoleName(peer.Role) + " goes on a standard port."; return false; }
                if (std >= stdCap) { reason = "All " + stdCap + " standard ports of " + name + " are in use."; return false; }
                return true;
            }
            if (std + poe >= stdCap + poeCap) { reason = "All " + (stdCap + poeCap) + " ports of " + name + " are in use."; return false; }
            return true;
        }

        private static int DishesWith(WireNode start, HashSet<WireNode> seen)
        {
            int dishes = 0;
            var queue = new Queue<WireNode>();
            if (seen.Add(start)) queue.Enqueue(start);
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                if (cur.Role == WireRole.NetDish) dishes++;
                foreach (WireLink l in WireNetwork.Links)
                {
                    if (l.Kind != "net" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o != null && seen.Add(o)) queue.Enqueue(o);
                }
            }
            return dishes;
        }

        /// <summary>
        /// Whether one more cable goes between the two: the gear at its two ends (through any wall jack) is a pair that is cabled, each has a port of the right kind free,
        /// the network gets no second dish, and a cable from outside comes into a building through a wall jack.
        /// </summary>
        public static bool CanJoin(WireNode a, WireNode b, out string reason)
        {
            reason = null;
            // the dish comes into the building through a wall jack: dish to jack, jack to router. Nothing else needs one.
            if ((a.Role == WireRole.NetDish && b.Role != WireRole.NetJack) || (b.Role == WireRole.NetDish && a.Role != WireRole.NetJack))
            {
                reason = "A dish is cabled to an Ethernet wall jack on the building, and the jack to the router inside.";
                return false;
            }
            // what is really at each end
            WireNode ra = a.Role == WireRole.NetJack ? Beyond(null, a) : a, rb = b.Role == WireRole.NetJack ? Beyond(null, b) : b;
            if (ra != null && ra.Role == WireRole.NetJack) ra = null;   // a jack with nothing behind it yet
            if (rb != null && rb.Role == WireRole.NetJack) rb = null;
            foreach (WireNode j in new[] { a, b })
                if (j.Role == WireRole.NetJack && !PortFor(j, null, null, out reason)) return false;
            if (ra != null && rb != null && ra != rb && !Pair(ra.Role, rb.Role)) { reason = WhyNot(ra, rb); return false; }
            if (ra == rb && ra != null) { reason = "That would cable it to itself."; return false; }
            // a port of the right kind at each end (the end behind a jack is already cabled to the jack: that cable is the one being completed)
            if (ra != null && !PortFor(ra, rb, a.Role == WireRole.NetJack ? FirstHop(ra, a) : null, out reason)) return false;
            if (rb != null && !PortFor(rb, ra, b.Role == WireRole.NetJack ? FirstHop(rb, b) : null, out reason)) return false;
            // one dish to a network
            var seen = new HashSet<WireNode>();
            if (DishesWith(a, seen) + DishesWith(b, seen) > 1) { reason = "This network already has a dish: a network takes one."; return false; }
            return true;
        }

        /// <summary>The neighbour of <paramref name="end"/> on its cable that leads to the jack <paramref name="jack"/> (the jack itself, or the first of a row of jacks).</summary>
        private static WireNode FirstHop(WireNode end, WireNode jack)
        {
            foreach (WireLink l in WireNetwork.Links)
            {
                if (l.Kind != "net" || !l.Connects(end)) continue;
                WireNode o = l.Other(end);
                if (o == null || o.Role != WireRole.NetJack) continue;
                WireNode cur = o, from = end;
                for (int guard = 0; guard < 16 && cur != null; guard++)
                {
                    if (cur == jack) return o;
                    WireNode next = null;
                    foreach (WireLink k in WireNetwork.Links)
                    {
                        if (k.Kind != "net" || !k.Connects(cur)) continue;
                        WireNode x = k.Other(cur);
                        if (x != null && x != from && x.Role == WireRole.NetJack) { next = x; break; }
                    }
                    from = cur;
                    cur = next;
                }
            }
            return null;
        }

        /// <summary>
        /// A cable that carries nothing: one from a DISH straight to anything but an Ethernet wall jack. The dish comes into its building through the jack (dish, jack,
        /// router); such a cable cannot be laid, and one from an older save is dead until it is run through a jack. Nothing else needs a jack.
        /// </summary>
        public static bool Dead(WireLink l)
        {
            if (l == null || l.Kind != "net" || l.A == null || l.B == null) return false;
            return (l.A.Role == WireRole.NetDish && l.B.Role != WireRole.NetJack) || (l.B.Role == WireRole.NetDish && l.A.Role != WireRole.NetJack);
        }

        private static bool DeadCableOn(WireNode n)
        {
            foreach (WireLink l in WireNetwork.Links) if (l.Kind == "net" && l.Connects(n) && Dead(l)) return true;
            return false;
        }

        /// <summary>
        /// How a building is on the network: through its Ethernet wall jack, and only when that jack leads to a working dish (powered, cabled through a router).
        /// 2 = connected, 1 = it has a jack but no working dish behind it, 0 = it has no jack.
        /// </summary>
        public static int StructureLink(ConstructionSite site)
        {
            if (site == null) return 0;
            Refresh();
            int best = 0;
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.NetJack) continue;
                AttachedObject a = n.GetComponent<AttachedObject>();
                if (a == null || a.Site != site) continue;
                best = Mathf.Max(best, s_online.Contains(n) ? 2 : 1);
            }
            return best;
        }

        /// <summary>True when the building has any network gear in or on it (so its look-at panel says how it is connected).</summary>
        public static bool HasGear(ConstructionSite site)
        {
            foreach (WireNode n in WireNode.All) if (n != null && IsNet(n.Role) && SiteOf(n) == site) return true;
            return false;
        }

        /// <summary>A cable that is not drawn: both its ends are in (or on) the same building, so it runs in the walls.</summary>
        public static bool Hidden(WireLink l) { return l != null && l.Kind == "net" && SameBuilding(l.A, l.B); }

        // ------------------------------------------------------------------ the rack UPS

        public const float UpsChargeHours = 4f;   // game hours a flat UPS takes to charge

        /// <summary>Watt-hours the UPS units in a rack hold when full (0: none in it). The charge itself is the rack node's ChargeWh (saved with it).</summary>
        public static float UpsCapacityWh(WireNode rack)
        {
            if (rack == null || rack.Role != WireRole.NetRack) return 0f;
            float sum = 0f;
            foreach (AssetCatalogItem it in Parts(rack)) if (it.rack_units > 0) sum += it.capacity_wh;
            return sum;
        }

        /// <summary>True while a rack is running from its UPS: its building has no power and the UPS still has charge.</summary>
        public static bool OnUps(WireNode rack) { return UpsCapacityWh(rack) > 0f && rack.ChargeWh > 0.01f && !Mains(rack); }

        /// <summary>What a rack runs: everything in it, what its PoE ports feed down their cables and the dish its router powers.</summary>
        public static float RackLoadW(WireNode rack)
        {
            float w = 0f;
            foreach (AssetCatalogItem part in Parts(rack)) w += part.power_draw_w;
            foreach (WireLink l in WireNetwork.Links)
            {
                if (l.Kind != "net" || !l.Connects(rack) || Dead(l)) continue;
                WireNode end = Beyond(rack, l.Other(rack));
                if (end == null) continue;
                if (end.Role == WireRole.NetDish ? Routes(rack) : NeedsPoe(end) && PoePorts(rack) > 0) { AssetCatalogItem it = Cat(end.ItemId); w += it != null ? it.power_draw_w : 0f; }
            }
            return w;
        }

        /// <summary>Game hours a rack's UPS would last at what the rack runs now (0 with no UPS or nothing running).</summary>
        public static float UpsHoursLeft(WireNode rack) { float w = RackLoadW(rack); return w > 0.5f ? Mathf.Min(rack.ChargeWh, UpsCapacityWh(rack)) / w : 0f; }

        /// <summary>Called with the game time that passed (WireNetwork.TickCharge): a UPS charges while its building has power and runs its rack down while it has none.</summary>
        public static void Tick(float gameHours)
        {
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.NetRack) continue;
                float cap = UpsCapacityWh(n);
                if (cap <= 0f) { n.ChargeWh = 0f; continue; }
                if (Mains(n)) n.ChargeWh = Mathf.Min(cap, n.ChargeWh + cap / UpsChargeHours * gameHours);
                else n.ChargeWh = Mathf.Max(0f, Mathf.Min(n.ChargeWh, cap) - RackLoadW(n) * gameHours);
            }
        }

        // ------------------------------------------------------------------ what the gear draws from its building

        /// <summary>
        /// The watts the network gear in (or on) a building draws from its power (power_draw_w): the routers and switches, each device in a rack, a TV, the cellular
        /// antenna, and what the PoE ports there feed down their cables (cameras, access points, yagis) and the dish its router powers. It draws whenever it stands there:
        /// this is part of the load the building's supply is measured against.
        /// </summary>
        public static float LoadW(ConstructionSite site)
        {
            if (site == null) return 0f;
            float w = 0f;
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || !IsNet(n.Role) || n.Role == WireRole.NetJack) continue;
                if (n.Role == WireRole.NetDish || NeedsPoe(n))
                {
                    // fed down its cable: it draws from the building of the hub it is plugged into
                    foreach (WireLink l in WireNetwork.Links)
                    {
                        if (l.Kind != "net" || !l.Connects(n) || Dead(l)) continue;
                        WireNode hub = Beyond(n, l.Other(n));
                        if (hub == null || !Hub(hub.Role) || SiteOf(hub) != site) continue;
                        if (n.Role == WireRole.NetDish ? Routes(hub) : PoePorts(hub) > 0) { AssetCatalogItem it = Cat(n.ItemId); w += it != null ? it.power_draw_w : 0f; break; }
                    }
                    continue;
                }
                if (SiteOf(n) != site) continue;
                foreach (AssetCatalogItem part in Parts(n)) w += part.power_draw_w;   // (a rack: everything in it)
                float ups = UpsCapacityWh(n);
                if (ups > 0f && n.ChargeWh < ups - 0.5f) w += ups / UpsChargeHours;   // a UPS that is charging
            }
            return w;
        }

        // ------------------------------------------------------------------ what is powered, what is online (worked out twice a second, when asked)

        private static readonly HashSet<WireNode> s_powered = new HashSet<WireNode>(), s_online = new HashSet<WireNode>();
        private static readonly Dictionary<WireNode, WireNode> s_partner = new Dictionary<WireNode, WireNode>();   // a yagi and the yagi it is linked to
        private static readonly Dictionary<WireNode, float> s_quality = new Dictionary<WireNode, float>();          // and how good that link is (1 full, 0.5 half)
        private static float s_time = -10f, s_totalMbps, s_ratedMbps;

        /// <summary>Megabits a second the online dishes bring in right now (less in bad weather), and what they are rated for.</summary>
        public static float TotalMbps { get { Refresh(); return s_totalMbps; } }
        public static float RatedMbps { get { Refresh(); return s_ratedMbps; } }
        private static float s_usedMbps;
        /// <summary>Megabits a second the online devices use (cameras, TVs), and what is left of what the dishes bring in: the HUD's number.</summary>
        public static float UsedMbps { get { Refresh(); return s_usedMbps + PhoneMbps; } }
        /// <summary>The devices that use the most bandwidth right now, most first: the online cameras and TVs, and the phone while it is on the Wi-Fi.</summary>
        public static List<KeyValuePair<string, float>> TopUsers(int count)
        {
            Refresh();
            var list = new List<KeyValuePair<string, float>>();
            foreach (WireNode n in s_online)
            {
                AssetCatalogItem it = n != null ? Cat(n.ItemId) : null;
                if (it != null && it.bandwidth_usage_mbps > 0f) list.Add(new KeyValuePair<string, float>(HudBindings.GetItemName(n.ItemId), it.bandwidth_usage_mbps));
            }
            if (PhoneMbps > 0f) list.Add(new KeyValuePair<string, float>("Phone", PhoneMbps));
            list.Sort((a, b) => b.Value.CompareTo(a.Value));
            if (list.Count > count) list.RemoveRange(count, list.Count - count);
            return list;
        }

        /// <summary>What the phone takes of the homestead's bandwidth right now: set by Connectivity (0 while it is on cellular or has no Wi-Fi with internet).</summary>
        public static float PhoneMbps;
        public static float AvailableMbps { get { Refresh(); return Mathf.Max(0f, s_totalMbps - s_usedMbps - PhoneMbps); } }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { s_powered.Clear(); s_online.Clear(); s_partner.Clear(); s_quality.Clear(); s_time = -10f; s_totalMbps = s_ratedMbps = 0f; }

        public static bool Powered(WireNode n) { Refresh(); return n != null && s_powered.Contains(n); }
        public static bool Online(WireNode n) { Refresh(); return n != null && s_online.Contains(n); }

        /// <summary>What the weather leaves of a dish's bandwidth (it is hit less than the cellular signal).</summary>
        public static float DishWeather()
        {
            if (TimeSystem.Instance == null) return 1f;
            switch (TimeSystem.Instance.Snapshot().Weather)
            {
                case HomesteaderWeather.Blizzard: return 0.55f;
                case HomesteaderWeather.Thunderstorm: return 0.7f;
                case HomesteaderWeather.Snow: return 0.85f;
                case HomesteaderWeather.Rain: return 0.9f;
                case HomesteaderWeather.Fog: return 0.95f;
                default: return 1f;
            }
        }

        /// <summary>On its building's power (a thing mounted on a building: that building's), or beside a running portable generator.</summary>
        private static bool Mains(WireNode n)
        {
            AttachedObject a = n.GetComponent<AttachedObject>();
            if (a != null && a.Site != null) { if (WireNetwork.SupplyRatio(a.Site) >= 0.85f) return true; }
            else if (WireNetwork.Powered(n)) return true;
            return PortableGenerator.RatioAt(n.transform.position) >= 0.85f;
        }

        private static void Refresh()
        {
            if (Time.unscaledTime - s_time < 0.5f) return;
            s_time = Time.unscaledTime;
            NetPlan.Tick();   // the subscription: a day off the month, a renewal when it runs out
            s_powered.Clear(); s_online.Clear(); s_partner.Clear(); s_quality.Clear();
            s_totalMbps = s_ratedMbps = s_usedMbps = 0f;
            var nodes = new List<WireNode>();
            foreach (WireNode n in WireNode.All) if (n != null && IsNet(n.Role)) nodes.Add(n);
            if (nodes.Count == 0) return;
            // power: the boxes (and a TV) on their building's power; a wall jack needs none; a PoE device from a PoE port; a dish from its router
            foreach (WireNode n in nodes)
            {
                if (n.Role == WireRole.NetJack) { s_powered.Add(n); continue; }
                if (n.Role == WireRole.NetDish || NeedsPoe(n)) continue;
                if ((Mains(n) || OnUps(n)) && (n.Role != WireRole.NetRack || Ports(n) > 0)) s_powered.Add(n);   // (a rack with a charged UPS runs on through a power cut)
            }
            foreach (WireNode n in nodes)
            {
                if (n.Role != WireRole.NetDish && !NeedsPoe(n)) continue;
                foreach (WireLink l in WireNetwork.Links)
                {
                    if (l.Kind != "net" || !l.Connects(n) || Dead(l)) continue;
                    WireNode hub = Beyond(n, l.Other(n));
                    if (hub == null || !Hub(hub.Role) || !s_powered.Contains(hub)) continue;
                    if (n.Role == WireRole.NetDish ? Routes(hub) : PoePorts(hub) > 0) { s_powered.Add(n); break; }
                }
            }
            // the yagi links: two powered yagis in range of each other, each aimed at the other
            foreach (WireNode y in nodes)
            {
                if (y.Role != WireRole.NetYagi || !s_powered.Contains(y)) continue;
                WireNode best = null;
                float bestQ = 0f, bestD = float.MaxValue;
                foreach (WireNode z in nodes)
                {
                    if (z == y || z.Role != WireRole.NetYagi || !s_powered.Contains(z)) continue;
                    float d = Vector3.Distance(y.transform.position, z.transform.position);
                    if (d > Mathf.Min(Range(y), Range(z)) || d < 2f) continue;
                    float q = Mathf.Min(Aim(y, z), Aim(z, y));
                    if (q > bestQ || (q == bestQ && q > 0f && d < bestD)) { best = z; bestQ = q; bestD = d; }
                }
                if (best != null && bestQ > 0f) { s_partner[y] = best; s_quality[y] = bestQ; }
            }
            // online: from each powered dish, over the cables through powered gear (and the wall jacks), and across the yagi links
            float weather = DishWeather();
            var queue = new Queue<WireNode>();
            foreach (WireNode n in nodes)
            {
                if (n.Role != WireRole.NetDish || !s_powered.Contains(n) || NetPlan.Current == null) continue;   // no plan: the dish brings nothing in
                AssetCatalogItem it = Cat(n.ItemId);
                float rated = it != null ? it.bandwidth_mbps : 0f;
                s_ratedMbps += rated;
                s_totalMbps += rated * weather;
                s_online.Add(n);
                queue.Enqueue(n);
            }
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                if (cur.Role == WireRole.NetYagi && s_partner.TryGetValue(cur, out WireNode far) && s_partner.TryGetValue(far, out WireNode back) && back == cur && s_online.Add(far)) queue.Enqueue(far);
                if (End(cur.Role)) continue;   // a camera, an access point or a TV passes nothing on
                foreach (WireLink l in WireNetwork.Links)
                {
                    if (l.Kind != "net" || !l.Connects(cur) || Dead(l)) continue;
                    WireNode o = l.Other(cur);
                    if (o != null && s_powered.Contains(o) && o.Role != WireRole.NetDish && s_online.Add(o)) queue.Enqueue(o);
                }
            }
            s_totalMbps = Mathf.Min(s_totalMbps, NetPlan.CapMbps);   // the plan caps it
            // a TV (or any plain device) with no cable is online over Wi-Fi when it is in range of a router or access point that is
            foreach (WireNode n in nodes)
                if (n.Role == WireRole.NetDevice && s_powered.Contains(n) && !s_online.Contains(n) && Emitter(n.transform.position, out _, out bool internet) && internet) s_online.Add(n);
            foreach (WireNode n in s_online) { AssetCatalogItem use = Cat(n.ItemId); if (use != null) s_usedMbps += use.bandwidth_usage_mbps; }
        }

        /// <summary>How far its radio reaches. A rack: the furthest of the routers in it (a rack with a router in it gives Wi-Fi like the router would).</summary>
        private static float Range(WireNode n)
        {
            if (n.Role != WireRole.NetRack) { AssetCatalogItem it = Cat(n.ItemId); return it != null ? it.range_m : 0f; }
            float best = 0f;
            foreach (AssetCatalogItem part in Parts(n)) if (part.wire_role == "net_router") best = Mathf.Max(best, part.range_m);
            return best;
        }

        /// <summary>How well a yagi is aimed at another: 1 within 20 degrees, 0.5 within 45, else 0 (its boom points along its own forward).</summary>
        private static float Aim(WireNode from, WireNode to)
        {
            Vector3 d = to.transform.position - from.transform.position, f = from.transform.forward;
            d.y = 0f; f.y = 0f;
            if (d.sqrMagnitude < 0.01f || f.sqrMagnitude < 0.01f) return 0f;
            float angle = Vector3.Angle(f, d);
            return angle <= FullAimDeg ? 1f : angle <= HalfAimDeg ? 0.5f : 0f;
        }

        // ------------------------------------------------------------------ aiming a yagi (while it is being placed, and once it stands)

        /// <summary>A yagi being placed this frame (its preview): where, which way its boom points, which item. The look-at panel shows its signal so two can be lined up.</summary>
        public static int PreviewFrame = -10;
        public static Vector3 PreviewPos, PreviewForward;
        public static string PreviewItem;

        public static bool IsYagi(string itemId) { AssetCatalogItem it = Cat(itemId); return it != null && it.wire_role == "net_yagi"; }

        public static void Preview(string itemId, Vector3 pos, Vector3 forward)
        {
            if (!IsYagi(itemId)) return;
            PreviewFrame = Time.frameCount; PreviewPos = pos; PreviewForward = forward; PreviewItem = itemId;
        }

        private static float Off(Vector3 from, Vector3 forward, Vector3 to)
        {
            Vector3 d = to - from;
            d.y = 0f; forward.y = 0f;
            return d.sqrMagnitude < 0.01f || forward.sqrMagnitude < 0.01f ? 180f : Vector3.Angle(forward, d);
        }

        private static float Quality(float offDeg) { return offDeg <= FullAimDeg ? 1f : offDeg <= HalfAimDeg ? 0.5f : 0f; }

        /// <summary>
        /// The signal a yagi standing at a spot and pointing a way would have, POWERED OR NOT (so two can be lined up before anything is cabled): the best of the other
        /// yagis in range, with how far off each of the two is aimed. quality 1 full, 0.5 half, 0 none. False when no other yagi is in range.
        /// </summary>
        public static bool YagiSignal(Vector3 pos, Vector3 forward, float range, WireNode self, out float quality, out float distance, out float myOff, out float theirOff)
        {
            quality = 0f; distance = 0f; myOff = theirOff = 180f;
            bool any = false;
            float bestScore = float.MaxValue;
            foreach (WireNode z in WireNode.All)
            {
                if (z == null || z == self || z.Role != WireRole.NetYagi) continue;
                float d = Vector3.Distance(pos, z.transform.position);
                if (d < 2f || d > Mathf.Min(range > 0f ? range : float.MaxValue, Range(z))) continue;
                float mine = Off(pos, forward, z.transform.position), theirs = Off(z.transform.position, z.transform.forward, pos);
                float q = Mathf.Min(Quality(mine), Quality(theirs)), score = (1f - q) * 1000f + mine + theirs;   // the best link first, then the best aimed
                if (score >= bestScore) continue;
                bestScore = score; any = true;
                quality = q; distance = d; myOff = mine; theirOff = theirs;
            }
            return any;
        }

        /// <summary>The rows that say how a yagi (standing, or the one being placed) is lined up with its partner.</summary>
        public static void SignalRows(Vector3 pos, Vector3 forward, float range, WireNode self, List<(string, string)> rows)
        {
            if (!YagiSignal(pos, forward, range, self, out float q, out float d, out float mine, out float theirs))
            {
                rows.Add(("Signal", "None: no other yagi in range"));
                return;
            }
            rows.Add(("Signal", q >= 1f ? "Full" : q > 0f ? "Half" : "None"));
            rows.Add(("Partner", UnitFormat.Distance(d) + " away"));
            rows.Add(("This one", Mathf.RoundToInt(mine) + "\u00b0 off" + (mine <= FullAimDeg ? "" : mine <= HalfAimDeg ? ": turn it for full" : ": turn it towards its partner")));
            rows.Add(("Its partner", Mathf.RoundToInt(theirs) + "\u00b0 off" + (theirs <= FullAimDeg ? "" : theirs <= HalfAimDeg ? ": turn that one for full" : ": turn that one this way")));
        }

        // ------------------------------------------------------------------ the radio side: Wi-Fi and the cellular booster

        private static bool Emitter(Vector3 pos, out float strength, out bool internet)
        {
            strength = 0f; internet = false;
            bool any = false;
            foreach (WireNode n in s_powered)
            {
                if (n == null || (n.Role != WireRole.NetRouter && n.Role != WireRole.NetAp)) continue;   // (a rack gives no Wi-Fi: access points cabled to it do)
                float range = Range(n);
                if (range <= 0f) continue;
                float d = Vector3.Distance(pos, n.transform.position);
                if (d > range) continue;
                float s = 1f - d / range;
                bool on = s_online.Contains(n);
                if (!any || (on && !internet) || (on == internet && s > strength)) { strength = s; internet = on; }
                any = true;
            }
            return any;
        }

        /// <summary>
        /// The Wi-Fi at a spot: the powered router or access point it is in range of (the one with internet first, then the strongest).
        /// strength 1 beside it, 0 at the edge of its range. False when none reaches.
        /// </summary>
        public static bool WifiAt(Vector3 pos, out float strength, out bool internet)
        {
            Refresh();
            return Emitter(pos, out strength, out internet);
        }

        /// <summary>What a powered cellular antenna in range multiplies the phone's signal by (1.3; 1 when none is near).</summary>
        public static float CellBoostAt(Vector3 pos)
        {
            Refresh();
            foreach (WireNode n in s_powered)
                if (n != null && n.Role == WireRole.NetAntenna && Vector3.Distance(pos, n.transform.position) <= Mathf.Max(1f, Range(n))) return 1.3f;
            return 1f;
        }

        // ------------------------------------------------------------------ the look-at panel

        public static string Status(WireNode n)
        {
            if (n.Role == WireRole.NetJack) return Online(n) ? "Online" : Used(n) >= 2 ? "Cabled through, no internet" : Used(n) == 1 ? "One side cabled" : "Not cabled";
            if (n.Role == WireRole.NetRack && Ports(n) == 0) return "Empty";
            if (!Powered(n)) return "No power";
            if (n.Role == WireRole.NetAntenna) return "Boosting the cellular signal";
            return Online(n) ? "Online" : "No internet";
        }

        private static string NameOf(WireNode n) { return HudBindings.GetItemName(n.ItemId); }

        /// <summary>
        /// Where the connection of a piece of gear that is not online is broken, in the order it would be fixed: its own cable and power first, then back along the cables
        /// towards the dish to the first thing that stops it (a cable through a wall with no jack, a device with no power, a yagi with no partner, no dish at all).
        /// </summary>
        public static string Break(WireNode n)
        {
            Refresh();
            if (n.Role == WireRole.NetAntenna) return "It has no power";
            if (NetPlan.Current == null) return "No internet plan: take one in ResView on the phone";
            int cables = 0;
            foreach (WireLink l in WireNetwork.Links) if (l.Kind == "net" && l.Connects(n)) cables++;
            if (cables == 0) return n.Role == WireRole.NetDevice ? "No cable, and no Wi-Fi with internet in range" : n.Role == WireRole.NetRack && Ports(n) == 0 ? "The rack is empty" : "No cable is plugged into it";
            // everything joined to it by cable (dead cables and unpowered gear included), remembering the way back
            var from = new Dictionary<WireNode, WireLink>();
            var order = new List<WireNode> { n };
            from[n] = null;
            for (int i = 0; i < order.Count; i++)
                foreach (WireLink l in WireNetwork.Links)
                {
                    if (l.Kind != "net" || !l.Connects(order[i])) continue;
                    WireNode o = l.Other(order[i]);
                    if (o != null && !from.ContainsKey(o)) { from[o] = l; order.Add(o); }
                }
            WireNode dish = null;
            foreach (WireNode o in order) if (o.Role == WireRole.NetDish) { dish = o; break; }
            if (dish == null)
            {
                // no dish on these cables: it may come over a yagi link
                foreach (WireNode o in order)
                {
                    if (o.Role != WireRole.NetYagi) continue;
                    if (!s_powered.Contains(o)) return NameOf(o) + " has no power: it goes on a PoE port of a powered switch";
                    if (!s_partner.TryGetValue(o, out WireNode far) || !s_partner.TryGetValue(far, out WireNode back) || back != o) return "The yagi link is down: no powered yagi is aimed back at " + NameOf(o);
                    return "The network at the far end of the yagi link is not connected";
                }
                return "No dish on this network";
            }
            // the way from the dish to it, nearest the dish first
            var path = new List<WireNode>();
            for (WireNode cur = dish; cur != null; ) { path.Add(cur); WireLink l = from[cur]; cur = l != null ? l.Other(cur) : null; }
            for (int i = 0; i < path.Count; i++)
            {
                WireNode cur = path[i];
                WireLink next = from[cur];   // the cable on towards the gear asked about
                if (next != null && Dead(next)) return "The cable between " + NameOf(cur) + " and " + NameOf(next.Other(cur)) + " does not go through an Ethernet wall jack: cable the dish to a jack, and the jack to the router";

                if (!s_powered.Contains(cur))
                {
                    if (cur.Role == WireRole.NetDish) return "The dish has no power: it is powered through its cable by a router that is on";
                    if (NeedsPoe(cur)) return NameOf(cur) + " has no power: it goes on a PoE port of a powered switch";
                    return NameOf(cur) + " has no power";
                }
                if (i > 0 && i < path.Count - 1 && End(cur.Role)) return NameOf(cur) + " passes nothing on: cable through a router or a switch";
            }
            return "No internet reaches it";
        }

        /// <summary>The look-at panel of a piece of network gear: "Internet: Connected" or "Not Connected", and for a router, switch or rack its ports in use.</summary>
        public static void Rows(WireNode n, List<(string, string)> rows)
        {
            Refresh();
            bool connected = n.Role == WireRole.NetAntenna ? s_powered.Contains(n) : s_online.Contains(n);
            rows.Add(("Internet", connected ? "Connected" : "Not Connected"));
            if (!connected) rows.Add(("Break", Break(n)));
            if (n.Role == WireRole.NetYagi) SignalRows(n.transform.position, n.transform.forward, Range(n), n, rows);   // how it is lined up, connected or not
            if (n.Role == WireRole.NetRack)
            {
                NetRack rack = n.GetComponent<NetRack>();
                // what is in it, ONE at a time with its icon, moving on every two seconds (a full rack would fill the panel)
                if (rack != null && rack.Items.Count > 0)
                {
                    int at = (int)(Time.unscaledTime / 2f) % rack.Items.Count;
                    rows.Add(("@item|" + rack.Items[at], "=" + (at + 1) + " of " + rack.Items.Count));
                }
                else if (rack != null) rows.Add(("In it", "Empty"));
                float upsCap = UpsCapacityWh(n);
                if (upsCap > 0f)
                {
                    int pct = Mathf.RoundToInt(Mathf.Clamp01(n.ChargeWh / upsCap) * 100f);
                    float left = UpsHoursLeft(n);
                    string time = left >= 1f ? Mathf.FloorToInt(left) + " h " + Mathf.RoundToInt((left - Mathf.Floor(left)) * 60f) + " min" : Mathf.RoundToInt(left * 60f) + " min";
                    rows.Add(("UPS", OnUps(n) ? pct + "%, on battery: " + time + " left" : pct + "%" + (left > 0f ? ", " + time + " of backup" : "")));
                }
            }
            if (Hub(n.Role))
            {
                Usage(n, null, out int std, out int poe, out _);
                int poeCap = PoePorts(n), stdCap = Ports(n) - poeCap;
                if (stdCap > 0) rows.Add(("Ports", std + " of " + stdCap));
                if (poeCap > 0) rows.Add(("PoE ports", poe + " of " + poeCap));
            }
        }
    }

    /// <summary>
    /// A wall rack (a mounted item whose manifest gives it rack_capacity_u): rackmount routers and switches (rack_units) slide into it, one above the
    /// other. A left click on the rack with one in hand puts it in; a right click on one in the rack takes it out (not while more cables are plugged
    /// in than the rest has ports for). The rack is cabled as ONE device: the ports of what is in it add up, it routes when a router is in it, its
    /// PoE ports are those of its PoE switches (Net.cs). What is in it is saved with the rack (GameSave.SavedAttached.shelfIds).
    /// </summary>
    public sealed class NetRack : MonoBehaviour
    {
        public const float Unit = 0.04445f, FirstUnit = 0.03f;   // one rack unit, and the height of the bottom of the first (tools/make_internet.py builds the rack with these)
        public const float Reach = 3.5f;

        public readonly List<string> Items = new List<string>();
        private readonly List<GameObject> _views = new List<GameObject>();
        public AttachedObject Mount { get; private set; }
        public int Capacity { get; private set; }
        private float _depth = 0.42f;

        public static NetRack AttachIfRack(AttachedObject mount)
        {
            AssetCatalogItem it = mount != null ? HudBindings.GetCatalogItem(mount.ItemId) : null;
            if (it == null || it.rack_capacity_u <= 0) return null;
            var r = mount.gameObject.AddComponent<NetRack>();
            r.Mount = mount;
            r.Capacity = it.rack_capacity_u;
            var box = mount.GetComponent<BoxCollider>();
            if (box != null) r._depth = box.center.z + box.size.z * 0.5f;
            return r;
        }

        private static int UnitsOf(string itemId) { AssetCatalogItem it = HudBindings.GetCatalogItem(itemId); return it != null ? it.rack_units : 0; }
        public int UsedUnits() { int u = 0; foreach (string id in Items) u += Mathf.Max(1, UnitsOf(id)); return u; }

        public string Describe()
        {
            if (Items.Count == 0) return "Empty";
            var sb = new System.Text.StringBuilder();
            foreach (string id in Items) sb.Append(sb.Length > 0 ? ", " : "").Append(HudBindings.GetItemName(id));
            return sb.ToString();
        }

        private static bool UnderCursor(Camera cam, Vector2 pointer, out NetRack rack, out int index)
        {
            rack = null; index = -1;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(pointer), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                rack = h.collider.GetComponentInParent<NetRack>();
                if (rack != null)
                {
                    // the rack's own collider is the nearest hit (a device sits a little behind its front edge), so look through ALL the hits on this rack for a device:
                    // stopping at the first hit meant a device in the rack could never be clicked, and could not be taken out
                    foreach (RaycastHit h2 in hits)
                    {
                        if (h2.collider == null || h2.collider.GetComponentInParent<NetRack>() != rack) continue;
                        for (int i = 0; i < rack._views.Count; i++)
                            if (rack._views[i] != null && h2.collider.transform.IsChildOf(rack._views[i].transform)) { index = i; return true; }
                    }
                    return true;
                }
                if (h.collider.isTrigger) continue;
                if (h.collider.GetComponentInParent<Renderer>() != null || h.collider.GetComponentInChildren<Renderer>() != null) return false;   // something solid and seen is in front
            }
            return false;
        }

        /// <summary>A left click with a rackmount device in hand over a rack: it slides in. True when the click was for a rack.</summary>
        public static bool TryPutHeld(Camera cam, Vector2 pointer)
        {
            if (cam == null || AttachedObject.All.Count == 0) return false;
            HudState hud = HudState.Active;
            if (hud == null || hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return false;
            string id = hud.Toolbar[hud.SelectedSlot].IconId;
            if (string.IsNullOrEmpty(id) || hud.Toolbar[hud.SelectedSlot].Count <= 0) return false;
            if (!UnderCursor(cam, pointer, out NetRack rack, out _)) return false;
            string name = HudBindings.GetItemName(rack.Mount.ItemId);
            int units = UnitsOf(id);
            if (units <= 0) { ToastNotificationSystem.ShowInfo(name, "Only rackmount routers and switches go in a rack."); return true; }
            var ped = PedController.Current;
            if (ped != null && new Vector2(ped.transform.position.x - rack.transform.position.x, ped.transform.position.z - rack.transform.position.z).magnitude > Reach) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to reach that."); return true; }
            if (rack.UsedUnits() + units > rack.Capacity) { ToastNotificationSystem.ShowInfo(name, "The rack is full."); return true; }
            if (!hud.ConsumeFromSelectedSlot(1)) return true;
            rack.Items.Add(id);
            AssetCatalogItem added = HudBindings.GetCatalogItem(id);
            WireNode rackNode = rack.GetComponent<WireNode>();
            if (rackNode != null && added != null && added.capacity_wh > 0f) rackNode.ChargeWh += added.capacity_wh;   // a UPS comes charged
            rack.StartCoroutine(rack.Show(rack.Items.Count - 1));
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        /// <summary>A right click on a device in a rack (no cutters or wrench in hand) takes it out. True when the click was for one.</summary>
        public static bool TryTake(Camera cam, Vector2 pointer)
        {
            if (cam == null || AttachedObject.All.Count == 0 || WireTool.JoinToolHeld() || AttachedObject.WrenchRemoval()) return false;
            if (!UnderCursor(cam, pointer, out NetRack rack, out int index) || index < 0 || index >= rack.Items.Count) return false;
            string id = rack.Items[index], name = HudBindings.GetItemName(id);
            var ped = PedController.Current;
            if (ped != null && new Vector2(ped.transform.position.x - rack.transform.position.x, ped.transform.position.z - rack.transform.position.z).magnitude > Reach) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to reach that."); return true; }
            WireNode node = rack.GetComponent<WireNode>();
            if (node != null)
            {
                AssetCatalogItem it = HudBindings.GetCatalogItem(id);
                int left = Net.Ports(node) - (it != null ? Mathf.Max(0, it.net_ports) : 0);
                int cables = 0;
                foreach (WireLink l in WireNetwork.Links) if (l.Kind == "net" && l.Connects(node)) cables++;
                if (cables > left) { ToastNotificationSystem.ShowInfo(name, "Unplug some cables first: more are plugged into the rack than the rest of it has ports for."); return true; }
            }
            HudState hud = HudState.Active;
            if (hud == null) return true;
            if (hud.AddItemToToolbar(id, 1, HudBindings.GetMaxStack(id)) < 1) { ToastNotificationSystem.ShowWarning("Toolbar full", "No room in the toolbar for that."); return true; }
            rack.Items.RemoveAt(index);
            if (node != null) node.ChargeWh = Mathf.Min(node.ChargeWh, Net.UpsCapacityWh(node));   // a UPS taken out takes its charge with it
            rack.Rebuild();
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        /// <summary>Puts back what a save says was in the rack.</summary>
        public void Restore(List<string> ids)
        {
            if (ids == null) return;
            foreach (string id in ids) Items.Add(id);
            Rebuild();
        }

        private void Rebuild()
        {
            foreach (GameObject v in _views) if (v != null) Destroy(v);
            _views.Clear();
            StopAllCoroutines();
            for (int i = 0; i < Items.Count; i++) StartCoroutine(Show(i));
        }

        /// <summary>Makes the model of the device in a slot (when its GLB has loaded) and seats it: its front at the rack's front, one unit above the last.</summary>
        private IEnumerator Show(int index)
        {
            string id = Items[index];
            if (!ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo info) || info.Prefab == null) yield break;
            GlbTemplate glb = info.Prefab.GetComponent<GlbTemplate>();
            if (glb != null)
            {
                glb.EnsureLoading();
                float until = Time.realtimeSinceStartup + 30f;
                while (!glb.Ready && !glb.Failed && Time.realtimeSinceStartup < until) yield return null;
                if (!glb.Ready) yield break;
            }
            if (index >= Items.Count || Items[index] != id) yield break;   // taken out meanwhile
            GameObject view = Instantiate(info.Prefab, transform);
            view.name = "Racked_" + id;
            view.SetActive(true);
            view.transform.localRotation = Quaternion.identity;
            view.transform.localPosition = Vector3.zero;
            foreach (Collider c in view.GetComponentsInChildren<Collider>(true)) Destroy(c);
            foreach (MonoBehaviour m in view.GetComponentsInChildren<MonoBehaviour>(true)) if (!(m is GlbTemplate)) Destroy(m);
            bool any = false;
            Bounds lb = default;
            foreach (Renderer r in view.GetComponentsInChildren<Renderer>(true))
            {
                Bounds wb = r.bounds;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = wb.center + new Vector3((i & 1) == 0 ? -wb.extents.x : wb.extents.x, (i & 2) == 0 ? -wb.extents.y : wb.extents.y, (i & 4) == 0 ? -wb.extents.z : wb.extents.z);
                    Vector3 local = view.transform.InverseTransformPoint(corner);
                    if (!any) { lb = new Bounds(local, Vector3.zero); any = true; } else lb.Encapsulate(local);
                }
            }
            int below = 0;
            for (int i = 0; i < index; i++) below += Mathf.Max(1, UnitsOf(Items[i]));
            // the device's front (its +z) just behind the rack's front edge; its foot on its unit
            view.transform.localPosition = new Vector3(-lb.center.x, FirstUnit + below * Unit - lb.min.y, _depth - 0.012f - lb.max.z);
            if (any)
            {
                var box = view.AddComponent<BoxCollider>();
                box.isTrigger = true;
                box.center = lb.center;
                box.size = Vector3.Max(lb.size, new Vector3(0.03f, 0.03f, 0.03f));
            }
            while (_views.Count <= index) _views.Add(null);
            _views[index] = view;
        }
    }
}
