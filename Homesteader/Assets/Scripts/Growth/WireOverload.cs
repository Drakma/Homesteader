using System.Collections.Generic;
using Homesteader.Save;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// OVERLOAD (docs/OVERLOAD.md). Every piece of electric equipment has a rated current (manifest category_fields.max_current_a). Each grid tick the current through each part is worked
    /// out from what the system is delivering, and a part carrying more than its rating HEATS: the more over, the faster (360 game seconds divided by the overshoot, between 5 seconds and an hour).
    /// A part that heats to 1 TRIPS: it opens like a thrown disconnect (<see cref="WireNode.Open"/>), what is past it gets nothing, and it stays open until it is reset by a right click on it
    /// (a portable generator resets itself when it has cooled). A part under its rating cools. AC amps are watts / <see cref="AcV"/>, DC amps are watts / <see cref="DcV"/>.
    /// Wire counts too: a wire carrying more than its own rating heats the parts at both of its ends.
    /// </summary>
    public static partial class WireNetwork
    {
        public const float AcV = 240f;   // a split-phase service: panel, inverter and generator ratings are watts / 240
        public const float DcV = 48f;    // the battery bus

        /// <summary>Game seconds a part can carry <paramref name="r"/> times its rating before it trips (r above 1).</summary>
        public static float TripSeconds(float r) { return Mathf.Clamp(360f / Mathf.Max(0.001f, r - 1f), 5f, 3600f); }

        /// <summary>Heats a part that is <paramref name="r"/> times over its rating for <paramref name="dtS"/> game seconds, or cools it (r at most 1). Trips it when it is hot.</summary>
        public static void Heat(WireNode n, float r, float dtS, float amps)
        {
            if (n == null || n.Tripped) return;
            if (r > 1f) n.Heat = Mathf.Min(1f, n.Heat + dtS / TripSeconds(r));
            else n.Heat = Mathf.Max(0f, n.Heat - dtS / 600f);
            if (n.Heat >= 1f) Trip(n, amps);
        }

        /// <summary>Measures a part: records its current and heats or cools it against its rating. <paramref name="tolerance"/> lets a part run over for a while (a charge controller clips first).</summary>
        public static void Protect(WireNode n, float amps, float tolerance, float dtS)
        {
            if (n == null) return;
            n.LoadA = amps;
            float rated = n.RatedA;
            if (rated <= 0.01f || n.Tripped) return;
            Heat(n, amps / (rated * Mathf.Max(0.01f, tolerance)), dtS, amps);
        }

        private static void Trip(WireNode n, float amps)
        {
            n.Tripped = true;
            n.Heat = 1f;
            if (n.Role == WireRole.StandbyGenerator) { n.GenRunning = false; n.GenStarting = false; n.GenW = 0f; }
            Dbg.Log("[Overload] " + n.ItemId + " tripped: " + amps.ToString("0.#") + " A on a " + n.RatedA.ToString("0.#") + " A rating");
            ToastNotificationSystem.ShowWarning(HudBindings.GetItemName(n.ItemId) + " tripped", amps.ToString("0") + " A through a " + n.RatedA.ToString("0.#") + " A part. Reset it by hand once the load is down.");
            Redraw();
        }

        /// <summary>Resets a tripped part (a right click on it). It comes back warm: a circuit that is still overloaded trips it again soon.</summary>
        public static void Reset(WireNode n)
        {
            if (n == null || !n.Tripped) return;
            n.Tripped = false;
            n.Heat = 0.5f;
            n.LoadA = 0f;
            Redraw();
        }

        private static bool HasLink(WireNode n, string kind)
        {
            foreach (WireLink l in Links) if (l.Kind == kind && l.Connects(n)) return true;
            return false;
        }

        /// <summary>The watts one AC panel's own building draws (lights, water heaters, water pumps, network gear, and a fuel pump or a well pump wired to it).</summary>
        private static float PanelOwnW(WireNode n)
        {
            if (!IsEnergized(n)) return 0f;
            float w = 0f;
            AttachedObject at = n.GetComponent<AttachedObject>();
            if (at != null && at.Site != null)
            {
                ConstructionSite s = at.Site;
                w += LightEmitter.WantedWatts(s) + HeaterLoadW(s) + WaterPumpLoadW(s) + Net.LoadW(s);
            }
            foreach (WireLink fl in Links)
                if (fl.Kind == "ac" && fl.Connects(n) && fl.Other(n) != null && fl.Other(n).Role == WireRole.FuelPump) w += FuelNozzle.RunningW(fl.Other(n));
            ConstructionSite well = n.Well;
            if (well != null && WellWantsToRun(n))
            {
                AssetCatalogItem pump = HudBindings.GetCatalogItem(well.PumpId);
                if (pump != null) w += pump.power_draw_w;
            }
            return w;
        }

        /// <summary>For each AC panel of the system, the watts through it: its own building plus everything on the sub panels it feeds.</summary>
        private static Dictionary<WireNode, float> PanelCarriedW(List<WireNode> nodes)
        {
            var own = new Dictionary<WireNode, float>();
            var parent = new Dictionary<WireNode, WireNode>();
            var order = new List<WireNode>();
            var via = new Dictionary<WireNode, WireNode>();   // the last panel on the way from the source
            var queue = new Queue<WireNode>();
            foreach (WireNode n in nodes)
            {
                if (n == null) continue;
                if (n.Role == WireRole.AcPanel) own[n] = PanelOwnW(n);
                if (n.Role == WireRole.Inverter || n.Role == WireRole.WindTurbine || n.Role == WireRole.StandbyGenerator) { via[n] = null; queue.Enqueue(n); }
            }
            var seen = new HashSet<WireNode>(queue);
            while (queue.Count > 0)
            {
                WireNode u = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "ac" || !l.Connects(u)) continue;
                    WireNode v = l.Other(u);
                    if (v == null || v.Open || !seen.Add(v)) continue;
                    if (v.Role == WireRole.AcPanel) { parent[v] = via[u]; via[v] = v; order.Add(v); queue.Enqueue(v); }
                    else if (v.Role == WireRole.WallEntry || v.Role == WireRole.Disconnect || v.Role == WireRole.Lockout) { via[v] = via[u]; queue.Enqueue(v); }
                }
            }
            var carried = new Dictionary<WireNode, float>();
            foreach (var kv in own) carried[kv.Key] = kv.Value;
            for (int i = order.Count - 1; i >= 0; i--)   // the farthest panels first: each hands its total up to its parent
            {
                WireNode p = order[i];
                if (parent.TryGetValue(p, out WireNode up) && up != null) carried[up] = (carried.TryGetValue(up, out float have) ? have : 0f) + carried[p];
            }
            return carried;
        }

        /// <summary>Parts that protect a circuit and so trip on a wire run that carries too much: breakers, disconnects, wall entries, breaker boxes and lockout boxes.</summary>
        private static bool Protective(WireRole r)
        {
            return r == WireRole.DcBreaker || r == WireRole.Disconnect || r == WireRole.WallEntry || r == WireRole.AcPanel || r == WireRole.Lockout;
        }

        /// <summary>One grid tick's overload work for one system: the current through every part, heat and trips.</summary>
        public static void ApplyOverload(GridSystem sys, Balance b, float dtH)
        {
            if (sys == null || b == null || dtH <= 0f) return;
            float dtS = dtH * 3600f;
            float acDemand = Mathf.Max(0f, b.LoadW - b.WindUsedW);      // what must come through the inverters (the wind is AC and direct)
            float battA = (b.BatteryW + (b.Room ? b.SolarSpareW : 0f)) / DcV;   // what the batteries give or take
            float invDcA = (b.SolarUsedW + b.BatteryW) / DcV;
            float invRated = 0f, mpptRated = 0f, capSum = 0f;
            foreach (WireNode n in sys.Nodes)
            {
                if (n == null) continue;
                AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
                if (n.Role == WireRole.Inverter && it != null && MissingFrom(n) == WireRole.None) invRated += it.max_power_w;
                else if (n.Role == WireRole.Mppt && it != null) mpptRated += it.max_power_w;
                else if (n.Role == WireRole.Battery) capSum += n.CapacityWh;
            }
            float pvA = (mpptRated > 0f ? Mathf.Min(b.SolarW, mpptRated) : b.SolarW) / DcV;   // what the array pushes: the controller clips it, so a big array on a small controller does not push more through the breaker
            Dictionary<WireNode, float> carried = PanelCarriedW(sys.Nodes);
            var snapshot = new List<WireNode>(sys.Nodes);
            foreach (WireNode n in snapshot)
            {
                if (n != null && n.Tripped && n.Role == WireRole.SolarPanel) { n.Tripped = false; n.Heat = 0f; }   // a panel never trips (a save from before the wire rule was fixed)
                if (n == null || n.Tripped) continue;
                AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
                switch (n.Role)
                {
                    case WireRole.Inverter:
                        if (it == null || MissingFrom(n) != WireRole.None || invRated <= 0f) { n.LoadA = 0f; Heat(n, 0f, dtS, 0f); break; }
                        Protect(n, acDemand * (it.max_power_w / invRated) / AcV, 1f, dtS);
                        break;
                    case WireRole.AcPanel:
                        Protect(n, (carried.TryGetValue(n, out float cw) ? cw : 0f) / AcV, 1f, dtS);
                        break;
                    case WireRole.WallEntry:
                    case WireRole.Disconnect:
                    case WireRole.Lockout:
                        Protect(n, HasLink(n, "ac") ? acDemand / AcV : pvA, 1f, dtS);
                        break;
                    case WireRole.DcBreaker:
                        Protect(n, pvA, 1f, dtS);
                        break;
                    case WireRole.BusBar:
                        Protect(n, Mathf.Max(pvA, Mathf.Max(battA, invDcA)), 1f, dtS);
                        break;
                    case WireRole.Mppt:
                        Protect(n, mpptRated > 0f && it != null ? pvA * (it.max_power_w / mpptRated) : pvA, 1.25f, dtS);   // a controller clips first; it trips only well over its rating
                        break;
                    case WireRole.Battery:
                    {
                        // only the DISCHARGE heats a battery: the charge controller limits what goes in, but an inverter can pull more out than a small battery allows
                        float share = capSum > 0f ? n.CapacityWh / capSum : 0f;
                        Protect(n, b.BatteryW / DcV * share, 1f, dtS);
                        n.LoadA = battA * share;   // what it shows is the current either way (in or out)
                        break;
                    }
                }
            }
            // wire: a run carrying more than its own rating heats the parts at both of its ends
            foreach (WireLink l in new List<WireLink>(Links))
            {
                if (l.Auto || l.A == null || l.B == null || l.A.Tripped || l.B.Tripped || !sys.Nodes.Contains(l.A)) continue;
                AssetCatalogItem wire = HudBindings.GetCatalogItem(l.WireItem);
                if (wire == null || wire.max_current_a <= 0.01f) continue;
                float amps = Mathf.Max(l.A.LoadA, l.B.LoadA);
                float r = amps / wire.max_current_a;
                if (r > 1f) { if (Protective(l.A.Role)) Heat(l.A, r, dtS, amps); if (Protective(l.B.Role)) Heat(l.B, r, dtS, amps); }   // the breaker at the end of a run trips, not a panel or a battery
            }
        }

        /// <summary>WAILA rows for any protected part: its current against its rating, and whether it has tripped or is running hot.</summary>
        public static void OverloadRows(WireNode n, List<(string, string)> rows)
        {
            if (n == null) return;
            float rated = n.RatedA;
            if (rated <= 0.01f) return;
            if (n.Tripped) { rows.Add(("State", "Tripped: overload")); return; }
            rows.Add(("Current", n.LoadA.ToString("0.#") + " A of " + rated.ToString("0.#") + " A"));
            if (n.Heat > 0.05f) rows.Add(("Heat", Mathf.RoundToInt(n.Heat * 100f) + "% of a trip"));
        }

        // ------------------------------------------------------------------ saving: which parts are tripped (and which disconnects are thrown)

        public static List<GameSave.SavedTrip> CaptureTrips(Dictionary<GameObject, int> placed, Dictionary<GameObject, int> attached)
        {
            var list = new List<GameSave.SavedTrip>();
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || (!n.Tripped && !(n.Role == WireRole.Disconnect && n.SwitchOff) && n.Heat <= 0.01f)) continue;
                if (!Ref(n, placed, attached, out int kind, out int index)) continue;
                list.Add(new GameSave.SavedTrip { kind = kind, index = index, tripped = n.Tripped, off = n.Role == WireRole.Disconnect && n.SwitchOff, heat = n.Heat });
            }
            return list;
        }

        public static void RestoreTrips(List<GameSave.SavedTrip> saved, Dictionary<int, PlacedObject> placed, Dictionary<int, AttachedObject> attached)
        {
            if (saved == null) return;
            foreach (GameSave.SavedTrip t in saved)
            {
                WireNode n = Find(t.kind, t.index, placed, attached);
                if (n == null) continue;
                n.Tripped = t.tripped;
                n.Heat = t.heat;
                if (t.off) { n.SwitchOff = true; Disconnect.Show(n); }
            }
        }
    }
}
