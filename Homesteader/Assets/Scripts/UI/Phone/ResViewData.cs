using System.Collections.Generic;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.UI
{
    /// <summary>
    /// What the ResView phone app shows, counted from the world as it is: the water in the tanks by type (clean, raw), the fuel in the tanks, drums and cans (gasoline, diesel
    /// and propane only), the septic tanks' sludge and the internet (the bandwidth the placed sources bring in, and what the placed devices use of it). Each total comes with the list of the things it is
    /// made of, for the app's detail screen.
    /// </summary>
    public static class ResViewData
    {
        public const string Water = "liquid_water";
        public static readonly string[] Fuels = { "liquid_gasoline", "liquid_diesel", "liquid_propane" };

        /// <summary>One thing in a detail list.</summary>
        public sealed class Row
        {
            public string ItemId, Name, Stat;
            public float Fraction = -1f;     // how full (0 to 1); below 0: no bar
        }

        // ------------------------------------------------------------------ water

        public sealed class WaterTotals
        {
            public float Clean, Raw, Capacity;
            public readonly List<Row> Rows = new List<Row>();
            public float Total { get { return Clean + Raw; } }
        }

        public static WaterTotals GetWater()
        {
            var w = new WaterTotals();
            foreach (WireNode n in WireNode.All)                      // the tanks on the water lines
            {
                if (n == null || n.Role != WireRole.WaterTank) continue;
                float cap = n.WaterCapacityL;
                float raw = Mathf.Clamp(n.RawL, 0f, n.WaterL);
                w.Clean += n.WaterL - raw;
                w.Raw += raw;
                w.Capacity += cap;
                string stat = UnitFormat.Volume(n.WaterL) + " of " + UnitFormat.Volume(cap) + "  •  " + WireNetwork.WaterType(n);
                if (n.HeaterW > 0f && n.WaterL > 1f) stat += "  •  " + Mathf.RoundToInt(n.TempC) + " C";
                w.Rows.Add(new Row { ItemId = n.ItemId, Name = HudBindings.GetItemName(n.ItemId), Stat = stat, Fraction = cap > 0f ? n.WaterL / cap : -1f });
            }
            foreach (PlacedObject o in PlacedObject.All)              // and what stands about in jugs and buckets (not tanks: they were counted above)
            {
                if (o == null || !LiquidRules.IsLiquidContainer(o.ItemId) || LiquidRules.LiquidIn(o.ItemId, o.LiquidId) != Water) continue;
                WireNode node = o.GetComponent<WireNode>();
                if (node != null && node.Role == WireRole.WaterTank) continue;
                AddContainer(o.ItemId, LiquidRules.Held(o.ItemId, o.WireUsed), "", w.Rows, ref w.Clean, ref w.Capacity);
            }
            HudState hud = HudState.Active;
            if (hud != null)
                foreach (ToolbarSlotData s in hud.Toolbar)
                {
                    if (s.Count != 1 || string.IsNullOrEmpty(s.IconId) || !LiquidRules.IsLiquidContainer(s.IconId) || LiquidRules.LiquidIn(s.IconId, null) != Water) continue;
                    AddContainer(s.IconId, LiquidRules.Held(s.IconId, s.WireUsed), "  •  carried", w.Rows, ref w.Clean, ref w.Capacity);
                }
            return w;
        }

        private static void AddContainer(string itemId, float held, string note, List<Row> rows, ref float total, ref float capacity)
        {
            float cap = LiquidRules.Capacity(itemId);
            total += held;
            capacity += cap;
            rows.Add(new Row { ItemId = itemId, Name = HudBindings.GetItemName(itemId), Stat = UnitFormat.Volume(held) + " of " + UnitFormat.Volume(cap) + note, Fraction = cap > 0f ? held / cap : -1f });
        }

        // ------------------------------------------------------------------ fuel

        public sealed class FuelTotals
        {
            public string Liquid;
            public float Held, Capacity;
            public readonly List<Row> Rows = new List<Row>();
        }

        /// <summary>Gasoline, diesel and propane, in that order: what is held, in what, and how much room those containers have.</summary>
        public static List<FuelTotals> GetFuel()
        {
            var list = new List<FuelTotals>();
            foreach (string liquid in Fuels) list.Add(new FuelTotals { Liquid = liquid });
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !LiquidRules.IsLiquidContainer(o.ItemId)) continue;
                FuelTotals f = list.Find(x => x.Liquid == LiquidRules.LiquidIn(o.ItemId, o.LiquidId));
                if (f != null) AddContainer(o.ItemId, LiquidRules.Held(o.ItemId, o.WireUsed), "", f.Rows, ref f.Held, ref f.Capacity);
            }
            HudState hud = HudState.Active;
            if (hud != null)
                foreach (ToolbarSlotData s in hud.Toolbar)
                {
                    if (s.Count != 1 || string.IsNullOrEmpty(s.IconId) || !LiquidRules.IsLiquidContainer(s.IconId)) continue;
                    FuelTotals f = list.Find(x => x.Liquid == LiquidRules.LiquidIn(s.IconId, null));
                    if (f != null) AddContainer(s.IconId, LiquidRules.Held(s.IconId, s.WireUsed), "  •  carried", f.Rows, ref f.Held, ref f.Capacity);
                }
            return list;
        }

        // ------------------------------------------------------------------ septic

        public sealed class SepticTotals
        {
            public float SludgeL, LiquidL, CapacityL;
            public float WorstFill;          // the fullest tank's sludge, as a share of what stops it (1 = it takes nothing more)
            public string Status = "";
            public readonly List<Row> Rows = new List<Row>();
        }

        /// <summary>How a tank's sludge stands: OK, wanting a pump-out, or full (Septic.cs: a third of the tank, half the tank).</summary>
        public static string SepticStatus(WireNode tank)
        {
            float cap = tank.SewageCapacityL;
            if (cap <= 0f) return "OK";
            return tank.SludgeL >= cap * Septic.FullAt ? "Full of solids: order a pump-out" : tank.SludgeL >= cap * Septic.PumpSoonAt ? "Needs pumping out soon" : "OK";
        }

        /// <summary>The septic tanks: the sludge settled in each (what the pump-out truck comes for), its liquid, and how near it is to full.</summary>
        public static SepticTotals GetSeptic()
        {
            var s = new SepticTotals();
            WireNode worst = null;
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.SepticTank) continue;
                float cap = n.SewageCapacityL, fill = Septic.SludgeFill(n);
                s.SludgeL += n.SludgeL;
                s.LiquidL += n.SewageL;
                s.CapacityL += cap;
                if (worst == null || fill > s.WorstFill) { worst = n; s.WorstFill = fill; }
                s.Rows.Add(new Row { ItemId = n.ItemId, Name = HudBindings.GetItemName(n.ItemId), Fraction = fill,
                    Stat = "Sludge " + UnitFormat.Volume(n.SludgeL) + (cap > 0f ? " (" + Mathf.RoundToInt(n.SludgeL / cap * 100f) + "% of the tank)" : "") + "  \u2022  " + SepticStatus(n) });
            }
            s.Status = worst != null ? SepticStatus(worst) : "";
            return s;
        }

        // ------------------------------------------------------------------ internet

        public sealed class NetTotals
        {
            public float TotalMbps, UsedMbps, RatedMbps;   // what the dishes bring in now, what is used of it, what the dishes are rated for (the weather takes some)
            public string Phone = "";       // how the phone itself is connected right now
            public readonly List<Row> Sources = new List<Row>(), Users = new List<Row>(), Gear = new List<Row>();
        }

        /// <summary>
        /// The network as it stands (Net.cs, docs/INTERNET.md): the bandwidth the ONLINE dishes bring in (a dish is online when it is cabled to a powered router), what the online
        /// devices use of it (cameras; TVs and the like count while there is any internet), and the gear between them with its state and ports.
        /// </summary>
        public static NetTotals GetNet()
        {
            var net = new NetTotals();
            net.TotalMbps = Net.TotalMbps;
            net.RatedMbps = Net.RatedMbps;
            float weather = Net.DishWeather();
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || !Net.IsNet(n.Role)) continue;
                AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
                string name = HudBindings.GetItemName(n.ItemId), status = Net.Status(n);
                if (n.Role == WireRole.NetDish)
                    net.Sources.Add(new Row { ItemId = n.ItemId, Name = name, Stat = (Net.Online(n) ? "Brings in " + Mbps((it != null ? it.bandwidth_mbps : 0f) * weather) + " of " : "Would bring in ") + Mbps(it != null ? it.bandwidth_mbps : 0f) + "  \u2022  " + status });
                else if (n.Role == WireRole.NetCamera || n.Role == WireRole.NetDevice)
                {
                    float use = it != null && Net.Online(n) ? it.bandwidth_usage_mbps : 0f;
                    net.UsedMbps += use;
                    net.Users.Add(new Row { ItemId = n.ItemId, Name = name, Stat = (use > 0f ? "Uses " + Mbps(use) : "Uses nothing") + "  \u2022  " + status });
                }
                else
                {
                    int ports = Net.Ports(n), used = Net.Used(n);
                    bool hub = n.Role == WireRole.NetRouter || n.Role == WireRole.NetSwitch || n.Role == WireRole.NetRack;
                    net.Gear.Add(new Row { ItemId = n.ItemId, Name = name, Stat = status + (hub ? "  \u2022  " + used + " of " + ports + " ports" : ""), Fraction = hub && ports > 0 ? (float)used / ports : -1f });
                }
            }
            // the things that stream and are not network gear themselves: online over Wi-Fi, when in range of a router or access point that has internet
            foreach (PlacedObject o in PlacedObject.All) if (o != null && o.GetComponent<WireNode>() == null) AddUser(o.ItemId, o.transform.position, net);
            foreach (AttachedObject a in AttachedObject.All) if (a != null && a.GetComponent<WireNode>() == null) AddUser(a.ItemId, a.transform.position, net);
            Connectivity.Refresh();
            net.Phone = Connectivity.Current == Connectivity.Link.Wifi ? (Connectivity.Online ? "Wi-Fi, " : "Wi-Fi without internet, ") + Connectivity.Bars + " of 4 bars"
                      : Connectivity.Current == Connectivity.Link.Cellular ? "Cellular, " + Connectivity.Bars + " of 4 bars" + (Connectivity.Boosted ? " (boosted)" : "")
                      : "No service";
            return net;
        }

        private static void AddUser(string itemId, Vector3 pos, NetTotals net)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            if (it == null || it.bandwidth_usage_mbps <= 0f) return;
            bool on = Net.WifiAt(pos, out _, out bool internet) && internet;
            if (on) net.UsedMbps += it.bandwidth_usage_mbps;
            net.Users.Add(new Row { ItemId = itemId, Name = HudBindings.GetItemName(itemId), Stat = on ? "Uses " + Mbps(it.bandwidth_usage_mbps) + "  \u2022  Wi-Fi" : "Offline: it needs Wi-Fi or a cable" });
        }

        public static string Mbps(float v) { return v >= 1000f ? (v / 1000f).ToString("0.#") + " Gbps" : v.ToString("0.#") + " Mbps"; }
    }
}
