using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Fuel pumps (docs/WIRING.md, "Fuel pumps"). A gasoline or diesel pump (wire_role fuel_pump) is piped with a fuel line to bulk fuel tanks (fuel_tank) and
    /// wired to a breaker box with AC wire; it pumps while that box is live. A right click on the pump takes its nozzle (the cursor turns into it and a hose
    /// runs from the pump to the player); a right click on a fuel container standing on the ground then starts filling it with the pump's fuel from the tanks,
    /// at <see cref="RateLpm"/> in game time, until it is full (a right click on it again stops). While it pumps its motor (power_draw_w) is load on that
    /// breaker box's system (<see cref="RunningW"/>). A right click on the pump hangs the nozzle up again, as does walking further off than the hose reaches.
    /// Vehicles will take fuel the same way (<see cref="Dispense"/>).
    /// </summary>
    public sealed class FuelNozzle : MonoBehaviour
    {
        public const float HoseM = 5f;          // how far from the pump the nozzle reaches
        private const float Reach = 4f;          // how near the player has to be to take the nozzle
        public const float RateLpm = 4f;         // what the pump gives a game minute

        private static WireNode s_pump;
        private static PlacedObject s_filling;   // the container being filled now (the pump runs)
        private static FuelNozzle s_hose;
        private LineRenderer _line;
        private static Material s_hoseMat;

        /// <summary>True while the player holds a pump's nozzle.</summary>
        public static bool Holding => s_pump != null;
        public static WireNode Pump => s_pump;

        /// <summary>The watts this pump draws now: its motor's while it is filling something, else nothing. Load on the breaker box it is wired to.</summary>
        public static float RunningW(WireNode pump)
        {
            if (pump == null || pump != s_pump || s_filling == null) return 0f;
            AssetCatalogItem it = HudBindings.GetCatalogItem(pump.ItemId);
            return it != null ? it.power_draw_w : 0f;
        }

        /// <summary>The liquid a pump gives: liquid_gasoline or liquid_diesel (from its fuel_type).</summary>
        public static string FuelOf(WireNode pump)
        {
            if (pump == null) return null;
            return pump.ItemId != null && pump.ItemId.Contains("diesel") ? "liquid_diesel" : "liquid_gasoline";
        }

        /// <summary>The bulk tanks a pump is piped to (through other tanks).</summary>
        public static List<PlacedObject> TanksOf(WireNode pump)
        {
            var tanks = new List<PlacedObject>();
            var seen = new HashSet<WireNode> { pump };
            var queue = new Queue<WireNode>();
            queue.Enqueue(pump);
            while (queue.Count > 0)
            {
                WireNode n = queue.Dequeue();
                foreach (WireLink l in WireNetwork.Links)
                {
                    if (l.Kind != "fuel" || !l.Connects(n)) continue;
                    WireNode o = l.Other(n);
                    if (o == null || o.Role != WireRole.FuelTank || !seen.Add(o)) continue;
                    PlacedObject p = o.GetComponent<PlacedObject>();
                    if (p != null) tanks.Add(p);
                    queue.Enqueue(o);
                }
            }
            return tanks;
        }

        /// <summary>Liters of the pump's fuel in the tanks it is piped to.</summary>
        public static float FuelL(WireNode pump)
        {
            string fuel = FuelOf(pump);
            float l = 0f;
            foreach (PlacedObject t in TanksOf(pump))
                if (LiquidRules.LiquidIn(t.ItemId, t.LiquidId) == fuel) l += LiquidRules.Held(t.ItemId, t.WireUsed);
            return l;
        }

        /// <summary>The pump runs while a breaker box it is wired to with AC wire is live (and not browning out).</summary>
        public static bool Powered(WireNode pump)
        {
            foreach (WireLink l in WireNetwork.Links)
            {
                if (l.Kind != "ac" || !l.Connects(pump)) continue;
                WireNode o = l.Other(pump);
                if (o == null || o.Role != WireRole.AcPanel || !WireNetwork.IsEnergized(o)) continue;
                AttachedObject at = o.GetComponent<AttachedObject>();
                if (at == null || at.Site == null || WireNetwork.SupplyRatio(at.Site) >= 0.85f) return true;
            }
            return false;
        }

        /// <summary>Takes up to <paramref name="liters"/> of the pump's fuel out of its tanks; returns what it took. For a container now, a vehicle later.</summary>
        public static float Dispense(WireNode pump, float liters)
        {
            string fuel = FuelOf(pump);
            float took = 0f;
            foreach (PlacedObject t in TanksOf(pump))
            {
                if (took >= liters - 0.001f) break;
                if (LiquidRules.LiquidIn(t.ItemId, t.LiquidId) != fuel) continue;
                float held = LiquidRules.Held(t.ItemId, t.WireUsed);
                float take = Mathf.Min(held, liters - took);
                if (take <= 0f) continue;
                t.WireUsed = LiquidRules.StoredFor(t.ItemId, held - take);
                took += take;
            }
            return took;
        }

        public static WireNode PumpUnderCursor(Camera cam, Vector2 pointer)
        {
            if (cam == null) return null;
            WireNode n = WireTool.NodeUnderCursor(cam, pointer);
            return n != null && n.Role == WireRole.FuelPump ? n : null;
        }

        /// <summary>A right click. True when it was for the nozzle (taken, hung up, or a container filled).</summary>
        public static bool TryRightClick(Camera cam, Vector2 pointer, Transform player)
        {
            if (cam == null || WireTool.JoinToolHeld()) return false;   // the cutters and the wrench wire and pipe the pump instead
            WireNode pump = PumpUnderCursor(cam, pointer);
            if (pump != null)
            {
                if (s_pump == pump) { HangUp(); return true; }
                if (player != null && Vector3.Distance(player.position, pump.transform.position) > Reach) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to the pump."); return true; }
                if (!Powered(pump)) { ToastNotificationSystem.ShowInfo("No power", "The pump needs AC wire from a live breaker box."); return true; }
                HangUp();
                s_pump = pump;
                var go = new GameObject("FuelHose");
                s_hose = go.AddComponent<FuelNozzle>();
                return true;
            }
            if (s_pump == null) return false;
            // the nozzle in hand: a fuel container on the ground
            PlacedObject target = PlacementController.PlacedUnderCursor();
            if (target == null || !LiquidRules.IsLiquidContainer(target.ItemId)) return false;
            string fuel = FuelOf(s_pump);
            string name = HudBindings.GetItemName(target.ItemId);
            if (Vector3.Distance(s_pump.transform.position, target.transform.position) > HoseM + 1f) { ToastNotificationSystem.ShowInfo("Out of reach", "The hose does not reach the " + name + "."); return true; }
            if (!LiquidRules.Accepts(target.ItemId, fuel)) { ToastNotificationSystem.ShowInfo("Wrong container", "The " + name + " does not take " + HudBindings.GetItemName(fuel) + "."); return true; }
            float held = LiquidRules.Held(target.ItemId, target.WireUsed);
            if (held > 0.01f && LiquidRules.LiquidIn(target.ItemId, target.LiquidId) != fuel) { ToastNotificationSystem.ShowInfo("Already holds something", "The " + name + " has another liquid in it."); return true; }
            if (s_filling == target) { s_filling = null; return true; }   // a right click on what is filling stops it
            float room = LiquidRules.Capacity(target.ItemId) - held;
            if (room <= 0.01f) { ToastNotificationSystem.ShowInfo("Full", "The " + name + " is full."); return true; }
            if (!Powered(s_pump)) { ToastNotificationSystem.ShowInfo("No power", "The pump has lost its power."); return true; }
            if (FuelL(s_pump) <= 0.01f) { ToastNotificationSystem.ShowInfo("No fuel", "The tanks this pump is piped to have no " + HudBindings.GetItemName(fuel) + "."); return true; }
            s_filling = target;
            return true;
        }

        /// <summary>Puts the nozzle back on its pump.</summary>
        public static void HangUp()
        {
            s_pump = null;
            s_filling = null;
            if (s_hose != null) Destroy(s_hose.gameObject);
            s_hose = null;
        }

        private void Update()
        {
            var ped = PedController.Current;
            if (s_pump == null || ped == null) { HangUp(); return; }
            Vector3 hand = ped.transform.position + Vector3.up * 1.0f + ped.transform.forward * 0.3f;
            Bounds b = PumpBounds(s_pump);
            Vector3 from = new Vector3(b.center.x, b.min.y + b.size.y * 0.55f, b.center.z);
            if (Vector3.Distance(new Vector3(from.x, 0f, from.z), new Vector3(hand.x, 0f, hand.z)) > HoseM + 0.5f) { HangUp(); return; }   // walked off: the nozzle goes back
            if (_line == null)
            {
                _line = gameObject.AddComponent<LineRenderer>();
                if (s_hoseMat == null)
                {
                    s_hoseMat = new Material(Shader.Find("Universal Render Pipeline/Lit")) { hideFlags = HideFlags.DontSave };
                    s_hoseMat.SetColor("_BaseColor", new Color(0.05f, 0.05f, 0.055f));
                }
                _line.sharedMaterial = s_hoseMat;
                _line.widthMultiplier = 0.03f;
                _line.positionCount = 12;
                _line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
            WireNetwork.Sag(_line, from, hand);
            Fill();
        }

        /// <summary>The pump runs: the container fills at RateLpm in game time until it is full, the tanks run dry, the power goes or it is out of the hose's reach.</summary>
        private static void Fill()
        {
            if (s_filling == null) return;
            if (s_filling == null || Vector3.Distance(s_pump.transform.position, s_filling.transform.position) > HoseM + 1f || !Powered(s_pump)) { s_filling = null; return; }
            TimeSystem time = TimeSystem.Instance;
            float minutes = time != null ? Time.unscaledDeltaTime * TimeSystem.SpeedToMultiplier(time.CurrentSpeed) * TimeConstants.GameMinutesPerRealSecondAt1X : 0f;
            if (minutes <= 0f) return;   // paused
            string fuel = FuelOf(s_pump);
            float held = LiquidRules.Held(s_filling.ItemId, s_filling.WireUsed);
            float room = LiquidRules.Capacity(s_filling.ItemId) - held;
            float got = Dispense(s_pump, Mathf.Min(room, RateLpm * minutes));
            if (got > 0f)
            {
                s_filling.LiquidId = fuel;
                s_filling.WireUsed = LiquidRules.StoredFor(s_filling.ItemId, held + got);
            }
            if (room - got <= 0.01f || got <= 0f) s_filling = null;   // full, or the tanks are dry
        }

        private static Bounds PumpBounds(WireNode pump)
        {
            bool any = false;
            Bounds b = new Bounds(pump.transform.position + Vector3.up * 0.8f, Vector3.one);
            foreach (Renderer r in pump.GetComponentsInChildren<Renderer>()) { if (r is LineRenderer) continue; if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds); }
            return b;
        }

        /// <summary>The look-at panel's rows for a pump or a bulk tank.</summary>
        public static void Rows(WireNode n, List<(string, string)> rows)
        {
            if (n.Role == WireRole.FuelPump)
            {
                string fuel = FuelOf(n);
                rows.Add(("Power", Powered(n) ? "On" : "No power (AC wire to a live breaker box)"));
                rows.Add(("Fuel", TanksOf(n).Count == 0 ? "No tank piped to it" : UnitFormat.Volume(FuelL(n)) + " of " + HudBindings.GetItemName(fuel)));
                rows.Add(("Nozzle", s_pump == n ? (s_filling != null ? "Filling the " + HudBindings.GetItemName(s_filling.ItemId) : "In your hand") : "Hung up"));
                if (RunningW(n) > 0f) rows.Add(("Drawing", SolarSun.Power(RunningW(n))));
                return;
            }
            int pumps = 0;
            foreach (WireLink l in WireNetwork.Links) if (l.Kind == "fuel" && l.Connects(n) && l.Other(n) != null && l.Other(n).Role == WireRole.FuelPump) pumps++;
            rows.Add(("Pumps piped to it", pumps.ToString()));
        }
    }
}
