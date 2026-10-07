using System.Collections.Generic;
using Homesteader.Save;
using Homesteader.UI;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Homesteader.Growth
{
    /// <summary>What a wired device is in the solar chain (properties.wire_role of its manifest).</summary>
    public enum WireRole { None, SolarPanel, WallEntry, DcBreaker, Mppt, Battery, Inverter, AcPanel, BusBar, WindTurbine, PropaneTank, PropaneConnector, PropaneFiller, WaterTank, WaterFilter, WaterInlet, WaterSpigot, WaterPump, SewerOutlet, SewerPump, SepticTank, SepticDBox, LeachField, StandbyGenerator, Disconnect, Lockout, FuelTank, FuelPump, NetDish, NetYagi, NetRouter, NetSwitch, NetAp, NetCamera, NetRack, NetAntenna, NetJack, NetDevice }   // (the Net* roles stay together: Net.IsNet is a range)

    /// <summary>
    /// A device that wires can be connected to: a solar panel on its mount, a wall entry, a DC breaker box, an MPPT charge controller, a battery, an inverter, an AC panel (the outdoor
    /// breaker box) or a DC bus bar. Added to every placed and mounted object whose manifest has a wire_role (see <see cref="WireNode.Attach"/>).
    /// </summary>
    public sealed class WireNode : MonoBehaviour
    {
        public static readonly List<WireNode> All = new List<WireNode>();

        public WireRole Role { get; private set; }
        public string ItemId { get; private set; }
        private static int s_uid;
        public readonly int Uid = ++s_uid;   // a number of its own (the grid systems are keyed by their lowest)
        /// <summary>A battery's capacity in watt-hours: its own, or for a battery rack the sum of the batteries standing in it.</summary>
        public float CapacityWh
        {
            get
            {
                if (Role != WireRole.Battery) return 0f;
                AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId);
                if (it != null && it.capacity_wh > 0f) return it.capacity_wh;
                PlacedObject p = GetComponent<PlacedObject>();
                if (p == null || p.Contents == null) return 0f;
                float sum = 0f;
                foreach (ContainerStack c in p.Contents)
                {
                    AssetCatalogItem ci = HudBindings.GetCatalogItem(c.ItemId);
                    if (ci != null) sum += ci.capacity_wh * c.Count;
                }
                return sum;
            }
        }

        public float ChargeWh;
        public float WaterL;     // a water tank: the liters in it (saved with the object)
        public float RawL;       // of those, the liters that did not come through every filter stage (not drinkable)
        public float TempC = 12f;   // a water heater: the temperature of what it holds
        public bool PumpRunning;    // a water pump: moving water right now (its watts are load)
        public float PumpedLph;     // a water pump: what it moves while it runs
        public WireNode PumpIntake;  // a water pump: the first part on the side it pulls from (null while it stands)
        public float SewageL;        // a septic tank: the liquid in it; a leach field: the liquid its trenches hold (saved with the site)
        public float SludgeL;        // a septic tank: the solids settled in it (the honey pot truck pumps them out)
        public bool GenRunning;      // a standby generator: running now (it starts by itself when the power runs short)
        public bool GenStarting;     // and cranking: a few seconds before it takes the load
        public bool SwitchOff;       // a safety disconnect: thrown off (the handle down): the run is cut there (saved)
        public float GenW;           // and what it gives

        /// <summary>A septic tank's capacity in liters (0 for anything else).</summary>
        public float SewageCapacityL { get { if (Role != WireRole.SepticTank) return 0f; AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId); return it != null ? it.sewage_capacity_l : 0f; } }

        /// <summary>A leach field: liters a game day that soak away, and liters its trenches hold.</summary>
        public float LeachLpd { get { if (Role != WireRole.LeachField) return 0f; AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId); return it != null ? it.leach_lpd : 0f; } }
        public float LeachStorageL { get { if (Role != WireRole.LeachField) return 0f; AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId); return it != null ? it.leach_storage_l : 0f; } }
        public bool PumpClean;       // a water pump: what it pulls is clean

        /// <summary>A water tank that holds its water under pressure (a pressure tank, a water heater): the taps draw from it with no pump running.</summary>
        public bool Pressurized { get { if (Role != WireRole.WaterTank) return false; AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId); return it != null && it.pressurized; } }

        /// <summary>A water pump's flow in liters an hour (0 for anything else).</summary>
        public float PumpFlowLph { get { if (Role != WireRole.WaterPump) return 0f; AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId); return it != null ? it.flow_lph : 0f; } }

        /// <summary>A water pump's watts while it runs.</summary>
        public float PumpDrawW { get { if (Role != WireRole.WaterPump) return 0f; AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId); return it != null ? it.power_draw_w : 0f; } }

        /// <summary>A water heater's element in watts (0 for anything else).</summary>
        public float HeaterW { get { if (Role != WireRole.WaterTank) return 0f; AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId); return it != null ? it.heater_w : 0f; } }

        /// <summary>A water filter's stage bit: 1 sediment, 2 carbon, 4 uv (0 for anything else).</summary>
        public int FilterBit
        {
            get
            {
                if (Role != WireRole.WaterFilter) return 0;
                AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId);
                string st = it != null ? it.filter_stage : null;
                return st == "sediment" ? 1 : st == "carbon" ? 2 : st == "uv" ? 4 : 0;
            }
        }

        /// <summary>A water tank's capacity in liters (0 for anything else).</summary>
        public float WaterCapacityL { get { if (Role != WireRole.WaterTank) return 0f; AssetCatalogItem it = HudBindings.GetCatalogItem(ItemId); return it != null ? it.water_capacity_l : 0f; } }

        /// <summary>The drilled well this node is (its sub panel), or null.</summary>
        public ConstructionSite Well { get { ConstructionSite cs = GetComponent<ConstructionSite>(); return cs != null && cs.IsWell ? cs : null; } }   // a battery: the energy stored (saved with the object)

        private float _portTime = -10f;

        private void OnEnable() { if (!All.Contains(this)) All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { All.Clear(); }

        public static WireRole ParseRole(string s)
        {
            switch (s)
            {
                case "net_dish": return WireRole.NetDish;
                case "net_yagi": return WireRole.NetYagi;
                case "net_router": return WireRole.NetRouter;
                case "net_switch": return WireRole.NetSwitch;
                case "net_ap": return WireRole.NetAp;
                case "net_camera": return WireRole.NetCamera;
                case "net_rack": return WireRole.NetRack;
                case "net_antenna": return WireRole.NetAntenna;
                case "net_jack": return WireRole.NetJack;
                case "net_device": return WireRole.NetDevice;
                case "solar_panel": return WireRole.SolarPanel;
                case "wall_entry": return WireRole.WallEntry;
                case "dc_breaker": return WireRole.DcBreaker;
                case "mppt": return WireRole.Mppt;
                case "battery": return WireRole.Battery;
                case "inverter": return WireRole.Inverter;
                case "ac_panel": return WireRole.AcPanel;
                case "busbar": return WireRole.BusBar;
                case "wind_turbine": return WireRole.WindTurbine;
                case "propane_tank": return WireRole.PropaneTank;
                case "propane_connector": return WireRole.PropaneConnector;
                case "propane_filler": return WireRole.PropaneFiller;
                case "water_tank": return WireRole.WaterTank;
                case "water_filter": return WireRole.WaterFilter;
                case "water_inlet": return WireRole.WaterInlet;
                case "water_spigot": return WireRole.WaterSpigot;
                case "water_pump": return WireRole.WaterPump;
                case "sewer_outlet": return WireRole.SewerOutlet;
                case "sewer_pump": return WireRole.SewerPump;
                case "septic_tank": return WireRole.SepticTank;
                case "septic_dbox": return WireRole.SepticDBox;
                case "leach_field": return WireRole.LeachField;
                case "standby_generator": return WireRole.StandbyGenerator;
                case "disconnect": return WireRole.Disconnect;
                case "generator_lockout": return WireRole.Lockout;
                case "fuel_tank": return WireRole.FuelTank;
                case "fuel_pump": return WireRole.FuelPump;
                default: return WireRole.None;
            }
        }

        public static string RoleName(WireRole r)
        {
            switch (r)
            {
                case WireRole.NetDish: return "satellite dish";
                case WireRole.NetYagi: return "yagi antenna";
                case WireRole.NetRouter: return "router";
                case WireRole.NetSwitch: return "network switch";
                case WireRole.NetAp: return "access point";
                case WireRole.NetCamera: return "camera";
                case WireRole.NetRack: return "network rack";
                case WireRole.NetAntenna: return "cellular antenna";
                case WireRole.NetJack: return "Ethernet wall jack";
                case WireRole.NetDevice: return "network device";
                case WireRole.SolarPanel: return "solar panel";
                case WireRole.WallEntry: return "wall entry";
                case WireRole.DcBreaker: return "DC breaker box";
                case WireRole.Mppt: return "MPPT charge controller";
                case WireRole.Battery: return "battery";
                case WireRole.Inverter: return "inverter";
                case WireRole.AcPanel: return "AC panel";
                case WireRole.BusBar: return "bus bar";
                case WireRole.WindTurbine: return "wind turbine";
                case WireRole.PropaneTank: return "propane tank";
                case WireRole.PropaneConnector: return "propane house connector";
                case WireRole.PropaneFiller: return "propane fill post";
                case WireRole.WaterTank: return "water tank";
                case WireRole.WaterFilter: return "water filter";
                case WireRole.WaterInlet: return "building water inlet";
                case WireRole.WaterSpigot: return "spigot";
                case WireRole.WaterPump: return "water pump";
                case WireRole.SewerOutlet: return "building waste outlet";
                case WireRole.SewerPump: return "macerator pump";
                case WireRole.SepticTank: return "septic tank";
                case WireRole.SepticDBox: return "distribution box";
                case WireRole.LeachField: return "leach field";
                case WireRole.StandbyGenerator: return "standby generator";
                case WireRole.Disconnect: return "safety disconnect";
                case WireRole.Lockout: return "generator lockout box";
                case WireRole.FuelTank: return "bulk fuel tank";
                case WireRole.FuelPump: return "fuel pump";
                default: return "device";
            }
        }

        /// <summary>Makes a placed or mounted object a wire node when its manifest gives it a wire_role.</summary>
        public static void Attach(GameObject go, string itemId)
        {
            if (go == null) return;
            AssetCatalogItem info = HudBindings.GetCatalogItem(itemId);
            WireRole role = info != null ? ParseRole(info.wire_role) : WireRole.None;
            if (role == WireRole.None || go.GetComponent<WireNode>() != null) return;
            var n = go.AddComponent<WireNode>();
            n.Role = role;
            n.ItemId = itemId;
        }

        /// <summary>The node the object belongs to (a part of a mounted object finds its root), or null.</summary>
        public static WireNode Of(Component c) { return c != null ? c.GetComponentInParent<WireNode>() : null; }

        private Bounds _bounds;
        private bool _hasBounds;

        private Bounds ModelBounds()
        {
            if (_hasBounds && Time.unscaledTime - _portTime < 1f) return _bounds;
            bool any = false;
            Bounds b = default;
            foreach (Renderer r in GetComponentsInChildren<Renderer>())
            {
                if (r is LineRenderer) continue;
                if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds);
            }
            _bounds = any ? b : new Bounds(transform.position + Vector3.up * 0.3f, Vector3.one * 0.3f);
            _hasBounds = any;
            _portTime = Time.unscaledTime;
            return _bounds;
        }

        /// <summary>The device's bounds in the world (its renderers).</summary>
        public Bounds WorldBounds() { return ModelBounds(); }

        /// <summary>The middle of the device (a point to measure towards).</summary>
        public Vector3 BasePort { get { return ModelBounds().center; } }

        /// <summary>
        /// Where a wire meets the device, for a wire going to the point <paramref name="other"/>: the CONNECTION POINT, not the middle of the model. Wall devices (the charge
        /// controller, the inverter, the breaker boxes, the wall batteries) have their terminals along the bottom; a battery standing on the floor has them on top; a wall entry
        /// has two (its plate on each side of the wall) and the nearer one is used; a bus bar takes a wire anywhere on it.
        /// </summary>
        public Vector3 PortToward(Vector3 other)
        {
            Bounds b = ModelBounds();
            switch (Role)
            {
                case WireRole.WallEntry:
                {
                    Transform best = null;
                    float bestD = float.MaxValue;
                    foreach (Transform t in GetComponentsInChildren<Transform>())
                    {
                        if (!t.name.StartsWith("Plate")) continue;
                        float d = (t.position - other).sqrMagnitude;
                        if (d < bestD) { bestD = d; best = t; }
                    }
                    return best != null ? best.position + Vector3.up * 0.08f : b.center;   // the middle of the plate (its pivot is the bottom edge)
                }
                case WireRole.BusBar:
                {
                    // a wire goes to the studs on the FRONT of the bar, not into the middle of its body
                    Vector3 f = transform.forward;
                    float half = Mathf.Abs(f.x) * b.extents.x + Mathf.Abs(f.y) * b.extents.y + Mathf.Abs(f.z) * b.extents.z;
                    return b.center + f * half;
                }
                case WireRole.PropaneTank:
                {
                    // a tank takes any number of lines: each leaves from the foot of the tank on the side its device is on, so several do not lie on top of each other
                    Vector3 p = b.ClosestPoint(new Vector3(other.x, b.min.y, other.z));
                    return new Vector3(p.x, b.min.y + 0.02f, p.z);
                }
                case WireRole.Battery:
                    if (GetComponent<AttachedObject>() == null) return new Vector3(b.center.x, b.max.y, b.center.z);   // standing on the floor: the terminals are on top
                    break;
                case WireRole.WaterInlet:
                case WireRole.SewerOutlet:
                {
                    // a building's water inlet (or waste outlet) goes through the wall: from outside the pipe meets the foot of its riser (it stands 7 cm out from the wall); from inside
                    // the building it leaves the inside valve, right where it is
                    AttachedObject at = GetComponent<AttachedObject>();
                    if (at == null) break;
                    if (at.Site != null && at.Site.IsInsideWalls(other + Vector3.up * 0.3f))
                    {
                        // the waste outlet shows on the outside only: from inside, the pipe meets the wall where the drain goes through it
                        if (Role == WireRole.SewerOutlet)
                            return transform.position + Vector3.up * 0.4f - transform.forward * ((at.Thickness > 0.05f ? at.Thickness : AttachedObject.DefaultWall) + 0.03f);
                        foreach (Transform t in GetComponentsInChildren<Transform>())
                            if (t.name == "PlateFar")
                            {
                                Bounds fb = default;
                                bool any = false;
                                foreach (Renderer r in t.GetComponentsInChildren<Renderer>()) { if (!any) { fb = r.bounds; any = true; } else fb.Encapsulate(r.bounds); }
                                return any ? fb.center : t.position;
                            }
                    }
                    return transform.position + transform.forward * (Role == WireRole.SewerOutlet ? 0.12f : 0.07f);
                }
            }
            return new Vector3(b.center.x, b.min.y + 0.02f, b.center.z);   // along the bottom edge
        }
    }

    /// <summary>Owns the merged clip mesh of one wire run, so it is freed when the wire is.</summary>
    public sealed class WireClipMesh : MonoBehaviour
    {
        public Mesh Mesh;
        private void OnDestroy() { if (Mesh != null) Destroy(Mesh); }
    }

    /// <summary>One wire between two devices (a DC or an AC run), drawn as a sagging line.</summary>
    public sealed class WireLink
    {
        public WireNode A, B;
        public bool Auto;               // joined by itself (solar panels standing side by side): no wire, not drawn, not saved, not cut
        public bool Heavy;              // a buried run: the larger conduit rises out of the ground at each end
        public string Kind;        // "dc" or "ac"
        public float Length;       // metres of wire it used
        public string WireItem;    // the kind of wire it was made of (for the colour and the record)
        public LineRenderer Line;
        public List<Vector3> Route;     // the path tacked to the walls (world points), once worked out
        public bool Conduit;            // the run is outside: AC in galvanized steel conduit, DC in beige PVC
        public bool RouteFinal;         // true when the route is final (or there is none: the wire hangs in a plain sag)
        public float NextRouteTry;
        public int RouteTries;
        public Vector3 DrawnA, DrawnB;  // the end points the plain sag or pipe was last drawn between (not redrawn until one moves)
        public bool Drawn;
        public float NextHideCheck;     // a wire hidden in the walls is re-checked about once a second, not every frame
        public bool Connects(WireNode n) { return A == n || B == n; }
        public WireNode Other(WireNode n) { return A == n ? B : A; }
    }

    /// <summary>
    /// The wiring of the off-grid system. A solar chain is Solar Panel > Wall Entry > DC Breaker Box > MPPT Charge Controller > Battery > Inverter, and an inverter then feeds an AC panel
    /// (the outdoor breaker box on a building) with AC wire. A DC bus bar joins any DC devices. Connections work in either order (panel then entry is entry then panel). Making one takes
    /// wire cutters in the active slot, two devices no more than <see cref="MaxSpan"/> apart and enough wire of the right kind within <see cref="WireReach"/> of the player (a coil or spool
    /// in the toolbar or standing on the ground; its metres are counted, a spool is used up when empty). The run to a solar panel needs weather-rated DC wire. Connecting two devices that
    /// are already wired cuts the wire. A building has electricity only while its AC panel is wired to an inverter that is connected all the way back to a solar panel
    /// (<see cref="IsEnergized"/>). docs/WIRING.md.
    /// </summary>
    public static class WireNetwork
    {
        public const float WindSpan = 40f;
        public const float MaxSpan = 4f;          // two devices are at most this far apart
        public const float WireReach = 4f;        // the wire is within this of the player
        public const float Slack = 0.5f;          // extra wire a run uses on top of the distance
        public const string CuttersId = "tool_wire_cutters";

        public static readonly List<WireLink> Links = new List<WireLink>();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { Links.Clear(); }

        public static void Clear()
        {
            s_powerState.Clear();
            foreach (WireLink l in Links) if (l.Line != null) Object.Destroy(l.Line.gameObject);
            Links.Clear();
            WireTool.Cancel();
        }

        // ------------------------------------------------------------------ what can be wired to what

        private static bool IsDc(WireRole r)
        {
            return r == WireRole.SolarPanel || r == WireRole.WallEntry || r == WireRole.DcBreaker || r == WireRole.Mppt || r == WireRole.Battery || r == WireRole.Inverter || r == WireRole.BusBar;
        }

        public static bool IsPropane(WireRole r) { return r == WireRole.PropaneTank || r == WireRole.PropaneConnector || r == WireRole.PropaneFiller; }

        /// <summary>A link to a safety disconnect that is thrown off: the current stops there.</summary>
        public static bool Cut(WireLink l)
        {
            return (l.A != null && l.A.Role == WireRole.Disconnect && l.A.SwitchOff) || (l.B != null && l.B.Role == WireRole.Disconnect && l.B.SwitchOff);
        }

        public static bool IsSewer(WireRole r) { return r == WireRole.SewerOutlet || r == WireRole.SewerPump || r == WireRole.SepticTank || r == WireRole.SepticDBox || r == WireRole.LeachField; }

        private static bool SewerPair(WireRole a, WireRole b)
        {
            if (a > b) { WireRole t = a; a = b; b = t; }
            if (a == WireRole.SewerOutlet) return b == WireRole.SewerOutlet || b == WireRole.SewerPump || b == WireRole.SepticTank;   // a building's drain: on to the next building's, a macerator or the tank
            if (a == WireRole.SewerPump) return b == WireRole.SepticTank;
            if (a == WireRole.SepticTank) return b == WireRole.SepticTank || b == WireRole.SepticDBox;   // tanks in series, then the distribution box
            if (a == WireRole.SepticDBox) return b == WireRole.LeachField;
            return false;
        }

        /// <summary>"dc", "ac", "propane" (a pipe, not a wire), or null when the two roles cannot be joined (the order does not matter).</summary>
        public static string KindFor(WireRole a, WireRole b)
        {
            if (a == WireRole.None || b == WireRole.None) return null;
            if (Net.IsNet(a) || Net.IsNet(b)) return Net.IsNet(a) && Net.IsNet(b) && Net.Pair(a, b) ? "net" : null;   // network gear is cabled only to network gear (Net.cs, docs/INTERNET.md)
            // a propane line: a tank to a house connector, tank to tank (a manifold), connector to connector (on to the next house); never to anything electrical
            // a fuel line (gasoline / diesel): bulk tank to pump, tank to tank; and a pump takes AC wire from a breaker box for its motor
            if ((a == WireRole.FuelTank && (b == WireRole.FuelPump || b == WireRole.FuelTank)) || (b == WireRole.FuelTank && a == WireRole.FuelPump)) return "fuel";
            if ((a == WireRole.AcPanel && b == WireRole.FuelPump) || (b == WireRole.AcPanel && a == WireRole.FuelPump)) return "ac";
            if (a == WireRole.FuelTank || b == WireRole.FuelTank || a == WireRole.FuelPump || b == WireRole.FuelPump) return null;
            // a safety disconnect goes into a run of either kind: AC beside a breaker box, an inverter (its AC side), a turbine or a generator; DC beside the rest
            if (a == WireRole.Disconnect || b == WireRole.Disconnect)
            {
                WireRole o = a == WireRole.Disconnect ? b : a;
                if (o == WireRole.Disconnect) return null;
                if (o == WireRole.AcPanel || o == WireRole.Inverter || o == WireRole.WindTurbine || o == WireRole.StandbyGenerator) return "ac";
                return o != WireRole.Lockout && IsDc(o) ? "dc" : null;   // (a lockout box takes a standby generator and nothing else)
            }
            // a standby generator runs on propane: a propane line from a tank, and AC wire to a breaker box
            if ((a == WireRole.StandbyGenerator && b == WireRole.PropaneTank) || (b == WireRole.StandbyGenerator && a == WireRole.PropaneTank)) return "propane";
            if (IsPropane(a) || IsPropane(b)) return IsPropane(a) && IsPropane(b) ? "propane" : null;
            // a sewer line (black waste pipe): building waste outlet > (macerator pump) > septic tank > distribution box > leach fields (docs/SEPTIC.md)
            if (IsSewer(a) || IsSewer(b)) return IsSewer(a) && IsSewer(b) && SewerPair(a, b) ? "sewer" : null;
            if (a > b) { WireRole t = a; a = b; b = t; }
            if (a == WireRole.SolarPanel && b == WireRole.SolarPanel) return "dc";   // panels wired to each other add up
            if (a == WireRole.Inverter && b == WireRole.AcPanel) return "ac";
            if (a == WireRole.AcPanel && b == WireRole.AcPanel) return "ac";   // a breaker box feeds another (a subpanel)
            if (a == WireRole.AcPanel && b == WireRole.WindTurbine) return "ac";
            if (a == WireRole.StandbyGenerator && b == WireRole.Lockout) return "ac";   // a standby generator feeds a building only through its lockout box
            if (a == WireRole.AcPanel && b == WireRole.WaterTank) return "water";      // a well (its sub panel is its node) piped to a tank: checked in Connect
            if (a == WireRole.WaterTank && b == WireRole.WaterTank) return "water";    // tank to tank
            if (a == WireRole.AcPanel && b == WireRole.WaterFilter) return "water";    // a well to its first filter
            if (a == WireRole.WaterTank && b == WireRole.WaterFilter) return "water";  // a filter to a tank (or a tank on to a filter)
            if (a == WireRole.WaterFilter && b == WireRole.WaterFilter) return "water"; // filter to filter
            if (b == WireRole.WaterSpigot && (a == WireRole.AcPanel || a == WireRole.WaterTank || a == WireRole.WaterFilter || a == WireRole.WaterInlet)) return "water";   // out to a spigot standing in the yard (a spigot post): checked in Connect
            if (b == WireRole.WaterInlet && (a == WireRole.AcPanel || a == WireRole.WaterTank || a == WireRole.WaterFilter || a == WireRole.WaterInlet)) return "water";   // into a building (or inlet to inlet: one building's water on to the next)
            if (b == WireRole.WaterPump && (a == WireRole.AcPanel || a == WireRole.WaterTank || a == WireRole.WaterFilter || a == WireRole.WaterInlet || a == WireRole.WaterSpigot || a == WireRole.WaterPump)) return "water";   // a pump pulls from a cistern   // a wind turbine has its own inverter: AC straight to a panel, buried
            if (a == WireRole.WallEntry && b == WireRole.Inverter) return "ac";   // AC through the wall: inverter > wall entry > outdoor AC panel
            if (a == WireRole.WallEntry && b == WireRole.AcPanel) return "ac";
            if (a == WireRole.BusBar || b == WireRole.BusBar) return IsDc(a) && IsDc(b) ? "dc" : null;
            if (a == WireRole.SolarPanel && b == WireRole.WallEntry) return "dc";
            if (a == WireRole.WallEntry && b == WireRole.DcBreaker) return "dc";
            if (a == WireRole.DcBreaker && b == WireRole.Mppt) return "dc";
            if (a == WireRole.Mppt && b == WireRole.Battery) return "dc";
            if (a == WireRole.Battery && b == WireRole.Inverter) return "dc";
            return null;
        }

        public static WireLink LinkBetween(WireNode a, WireNode b)
        {
            foreach (WireLink l in Links) if ((l.A == a && l.B == b) || (l.A == b && l.B == a)) return l;
            return null;
        }

        // ------------------------------------------------------------------ connecting and cutting

        /// <summary>Wires two devices (or cuts the wire between them when it is there). False with the reason when nothing was done.</summary>
        public static bool Connect(WireNode a, WireNode b, Transform player, out string reason)
        {
            reason = null;
            if (a == null || b == null || a == b) return false;
            WireLink existing = LinkBetween(a, b);
            if (existing != null && existing.Auto) { reason = "Solar panels standing side by side are joined already. Wire any one panel of the group to a wall entry, or to a panel of another group."; return false; }
            if (existing != null) { Remove(existing); return true; }   // wired already: the cutters cut it

            string kind = KindFor(a.Role, b.Role);
            if (kind == null && (IsSewer(a.Role) || IsSewer(b.Role)))
            {
                reason = IsSewer(a.Role) && IsSewer(b.Role)
                    ? "A sewer line runs building waste outlet, macerator pump (optional), septic tank, distribution box, leach fields: a " + WireNode.RoleName(a.Role) + " does not join a " + WireNode.RoleName(b.Role) + "."
                    : "Black waste pipe joins a building's waste outlet, a macerator pump, septic tanks, a distribution box and leach fields, not a " + WireNode.RoleName(IsSewer(a.Role) ? b.Role : a.Role) + ".";
                return false;
            }
            if (kind == null && (IsPropane(a.Role) || IsPropane(b.Role)))
            {
                reason = "A propane line runs between propane tanks and house connectors, not to a " + WireNode.RoleName(IsPropane(a.Role) ? b.Role : a.Role) + ".";
                return false;
            }
            if (kind == null && (Net.IsNet(a.Role) || Net.IsNet(b.Role))) { reason = Net.WhyNot(a, b); return false; }
            if (kind == "net" && !Net.CanJoin(a, b, out reason)) return false;   // a port free at each end
            if (kind == null)
            {
                reason = "A " + WireNode.RoleName(a.Role) + " is not wired to a " + WireNode.RoleName(b.Role) + ". The chain is solar panel, wall entry, DC breaker box, MPPT, battery, inverter, then an AC panel (directly or through a wall entry).";
                return false;
            }
            if (kind == "water")
            {
                foreach (WireNode end in new[] { a, b })
                    if (end.Role == WireRole.WaterSpigot && end.GetComponent<AttachedObject>() != null) { reason = "A spigot on a building gets its water from the building's water inlet. Only a spigot post out in the yard is piped."; return false; }
                foreach (WireNode end in new[] { a, b })
                    if (end.Role != WireRole.WaterTank && end.Role != WireRole.WaterFilter && end.Role != WireRole.WaterInlet && end.Role != WireRole.WaterSpigot && end.Role != WireRole.WaterPump && end.Well == null) { reason = "A water line joins a well (with its sub panel), water filters, tanks and a building's water inlet."; return false; }
            }
            bool wind = a.Role == WireRole.WindTurbine || b.Role == WireRole.WindTurbine;
            foreach (WireNode wn in new[] { a, b })
            {
                ConstructionSite ws = wn.GetComponent<ConstructionSite>();
                if (ws != null && !ws.Finished) { reason = "Finish building it first."; return false; }
            }
            float distance = Vector3.Distance(a.PortToward(b.BasePort), b.PortToward(a.BasePort));   // between the two connection points
            bool panelRun = a.Role == WireRole.SolarPanel || b.Role == WireRole.SolarPanel;   // outdoor DC wire to a panel: a long run is buried like AC
            float span = kind == "net" ? Net.MaxCable : wind || panelRun || kind == "ac" || kind == "propane" || kind == "fuel" || kind == "water" || kind == "sewer" ? WindSpan : MaxSpan;   // AC runs (and a turbine's, a panel's, and a propane line) may be long: they are buried
            if (distance > span)
            {
                reason = "They are " + UnitFormat.Distance(distance) + " apart: a wire runs at most " + UnitFormat.Distance(span) + ".";
                return false;
            }
            bool outdoor = a.Role == WireRole.SolarPanel || b.Role == WireRole.SolarPanel;   // the run to a panel is outside: weather-rated wire only
            float need = distance + Slack;
            if (!TakeWire(kind, outdoor, need, player, out string wireItem))
            {
                string what = kind == "net" ? "Cat6 cable" : kind == "fuel" ? "fuel line" : kind == "sewer" ? "black waste pipe" : kind == "water" ? "PVC pipe" : kind == "propane" ? "propane pipe" : kind == "ac" ? "AC wire" : "DC wire";
                reason = "You need " + UnitFormat.Distance(need) + " of " + what + " within " + UnitFormat.Distance(WireReach) + " of you (a coil or spool in the toolbar or on the ground).";
                Dbg.Log("[Wire] refused: " + WireNode.RoleName(a.Role) + " + " + WireNode.RoleName(b.Role) + " kind " + kind + " outdoor " + outdoor + " need " + need.ToString("0.0") + " m; player " + (player != null ? "found" : "NULL") + "; " + WireScan(player));
                string other = NearbyOtherWire(kind, outdoor, need, player);
                if (other != null) reason = "That run needs " + what + ", and the wire near you is " + other + ".";
                return false;
            }
            Links.Add(new WireLink { A = a, B = b, Kind = kind, Length = need, WireItem = wireItem });
            return true;
        }

        public static void Remove(WireLink l)
        {
            if (l == null) return;
            if (l.Line != null) Object.Destroy(l.Line.gameObject);
            Links.Remove(l);
        }

        // ------------------------------------------------------------------ the wire it takes

        private static bool Accepts(string kind, bool outdoor, string wireKind)
        {
            if (kind == "net") return wireKind == "net";   // a network run is Cat6 cable
            if (kind == "water") return wireKind == "water";   // a water line is PVC pipe, counted in metres
            if (kind == "sewer") return wireKind == "sewer";   // a sewer line is black waste pipe
            if (kind == "fuel") return wireKind == "fuel";     // a fuel line
            if (kind == "propane") return wireKind == "propane";   // a propane line is made of propane pipe and nothing else
            if (kind == "ac") return wireKind == "ac";
            return wireKind == "dc_indoor" || wireKind == "dc_outdoor";   // a run outside is in conduit, so either DC wire will do
        }

        /// <summary>The wire within reach that is long enough but of the wrong kind, as "19 m of indoor DC wire" (null when there is none): said when a connection is refused.</summary>
        private static string NearbyOtherWire(string kind, bool outdoor, float metres, Transform player)
        {
            string found = null;
            HudState hud = HudState.Active;
            if (hud != null)
                for (int i = 0; i < hud.Toolbar.Count && found == null; i++)
                {
                    ToolbarSlotData s = hud.Toolbar[i];
                    if (s.Count <= 0 || string.IsNullOrEmpty(s.IconId)) continue;
                    float len = LengthOf(s.IconId, out string wk);
                    if (len > 0f && len * s.Count - s.WireUsed >= metres) found = WireWords(wk, len * s.Count - s.WireUsed);
                }
            if (found == null && player != null)
                foreach (PlacedObject o in PlacedObject.All)
                {
                    if (o == null || new Vector2(o.transform.position.x - player.position.x, o.transform.position.z - player.position.z).magnitude > WireReach) continue;
                    float len = LengthOf(o.ItemId, out string wk);
                    if (len > 0f && len - o.WireUsed >= metres) { found = WireWords(wk, len - o.WireUsed); break; }
                }
            return found;
        }

        /// <summary>Every coil or spool the toolbar and the ground hold, for the log of a refused connection.</summary>
        private static string WireScan(Transform player)
        {
            var sb = new System.Text.StringBuilder();
            HudState hud = HudState.Active;
            if (hud != null)
                for (int i = 0; i < hud.Toolbar.Count; i++)
                {
                    ToolbarSlotData t = hud.Toolbar[i];
                    if (t.Count <= 0 || string.IsNullOrEmpty(t.IconId)) continue;
                    float len = LengthOf(t.IconId, out string wk);
                    if (len > 0f) sb.Append("[toolbar ").Append(t.IconId).Append(' ').Append(wk).Append(' ').Append(len * t.Count - t.WireUsed).Append(" m] ");
                }
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null) continue;
                float len = LengthOf(o.ItemId, out string wk);
                if (len <= 0f) continue;
                float d = player != null ? new Vector2(o.transform.position.x - player.position.x, o.transform.position.z - player.position.z).magnitude : -1f;
                sb.Append("[placed ").Append(o.ItemId).Append(' ').Append(wk).Append(" left ").Append(len - o.WireUsed).Append(" m, ").Append(d.ToString("0.0")).Append(" m away] ");
            }
            foreach (WorldItem w in WorldItem.All)
                if (w != null && LengthOf(w.ItemId, out string wk2) > 0f) sb.Append("[dropped ").Append(w.ItemId).Append(' ').Append(wk2).Append("] ");
            return sb.ToString();
        }

        private static string WireWords(string wireKind, float left)
        {
            string name = wireKind == "net" ? "Cat6 cable" : wireKind == "fuel" ? "fuel line" : wireKind == "sewer" ? "black waste pipe" : wireKind == "water" ? "PVC pipe" : wireKind == "propane" ? "propane pipe" : wireKind == "ac" ? "AC wire" : wireKind == "dc_outdoor" ? "weather-rated DC wire" : wireKind == "dc_indoor" ? "indoor DC wire" : "wire";
            return UnitFormat.Distance(left) + " of " + name;
        }

        private static float LengthOf(string itemId, out string wireKind)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            wireKind = it != null ? it.wire_kind : null;
            return it != null && it.wire_length_m > 0f ? it.wire_length_m : 0f;
        }

        /// <summary>Uses <paramref name="metres"/> of a matching coil or spool within reach of the player: the toolbar first, then spools standing on the ground. False when there is not enough in one.</summary>
        private static bool TakeWire(string kind, bool outdoor, float metres, Transform player, out string wireItem)
        {
            wireItem = null;
            HudState hud = HudState.Active;
            int bestSlot = -1;
            PlacedObject bestPlaced = null;
            float bestLeft = float.MaxValue;
            if (hud != null)
                for (int i = 0; i < hud.Toolbar.Count; i++)
                {
                    ToolbarSlotData s = hud.Toolbar[i];
                    if (s.Count <= 0 || string.IsNullOrEmpty(s.IconId)) continue;
                    float len = LengthOf(s.IconId, out string wk);
                    if (len <= 0f || !Accepts(kind, outdoor, wk)) continue;
                    float left = len * s.Count - s.WireUsed;
                    if (left >= metres && left < bestLeft) { bestLeft = left; bestSlot = i; bestPlaced = null; wireItem = s.IconId; }
                }
            if (player != null)
                foreach (PlacedObject o in PlacedObject.All)
                {
                    if (o == null) continue;
                    if (new Vector2(o.transform.position.x - player.position.x, o.transform.position.z - player.position.z).magnitude > WireReach) continue;
                    float len = LengthOf(o.ItemId, out string wk);
                    if (len <= 0f || !Accepts(kind, outdoor, wk)) continue;
                    float left = len - o.WireUsed;
                    if (left >= metres && left < bestLeft) { bestLeft = left; bestPlaced = o; bestSlot = -1; wireItem = o.ItemId; }
                }
            if (bestSlot >= 0 && hud != null)
            {
                ToolbarSlotData s = hud.Toolbar[bestSlot];
                float len = LengthOf(s.IconId, out _);
                s.WireUsed += metres;
                while (s.WireUsed >= len - 0.001f && s.Count > 0) { s.Count--; s.WireUsed = Mathf.Max(0f, s.WireUsed - len); }
                if (s.Count <= 0) s = ToolbarSlotData.Empty();
                hud.Toolbar[bestSlot] = s;
                hud.SelectSlot(hud.SelectedSlot);
                HudBindings.Instance?.RefreshToolbar();
                return true;
            }
            if (bestPlaced != null)
            {
                bestPlaced.WireUsed += metres;
                if (bestPlaced.WireUsed >= LengthOf(bestPlaced.ItemId, out _) - 0.001f) bestPlaced.Remove();   // the spool is empty
                return true;
            }
            wireItem = null;
            return false;
        }

        // ------------------------------------------------------------------ the chain: is a building powered?

        /// <summary>
        /// The neighbours of a node: what it is wired to, and everything on the bus bars it is wired to (a bus bar does nothing but carry the current, so the devices on it are as good as
        /// wired to each other; bus bars wired to bus bars are one bar). The bus bars themselves are not neighbours.
        /// </summary>
        private static void Neighbours(WireNode n, List<WireNode> into)
        {
            into.Clear();
            var bars = new HashSet<WireNode>();
            var queue = new Queue<WireNode>();
            foreach (WireLink l in Links)
            {
                if (!l.Connects(n)) continue;
                WireNode o = l.Other(n);
                if (o == null) continue;
                if (o.Role == WireRole.Disconnect && o.SwitchOff) continue;   // thrown off: nothing past it
                if (o.Role == WireRole.BusBar || o.Role == WireRole.Disconnect) { if (bars.Add(o)) queue.Enqueue(o); }   // a disconnect that is on carries the current like a bar
                else into.Add(o);
            }
            while (queue.Count > 0)
            {
                WireNode bar = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (!l.Connects(bar)) continue;
                    WireNode far = l.Other(bar);
                    if (far == null || far == n) continue;
                    if (far.Role == WireRole.Disconnect && far.SwitchOff) continue;
                    if (far.Role == WireRole.BusBar || far.Role == WireRole.Disconnect) { if (bars.Add(far)) queue.Enqueue(far); }
                    else into.Add(far);
                }
            }
        }

        private static readonly WireRole[] ChainBack = { WireRole.Inverter, WireRole.Battery, WireRole.Mppt, WireRole.DcBreaker, WireRole.WallEntry, WireRole.SolarPanel };

        /// <summary>The first role the chain from this inverter lacks, or None when it runs all the way back to a solar panel.</summary>
        public static WireRole MissingFrom(WireNode inverter)
        {
            var reached = new HashSet<WireNode> { inverter };
            var frontier = new List<WireNode> { inverter };
            var near = new List<WireNode>();
            for (int step = 1; step < ChainBack.Length; step++)
            {
                var next = new List<WireNode>();
                foreach (WireNode n in frontier)
                {
                    Neighbours(n, near);
                    foreach (WireNode o in near)
                        if (o != null && o.Role == ChainBack[step] && reached.Add(o)) next.Add(o);
                }
                if (next.Count == 0) return ChainBack[step];
                frontier = next;
            }
            return WireRole.None;
        }

        /// <summary>True when an AC panel is wired to an inverter whose DC chain is complete back to a solar panel: the building the panel is on has electricity.</summary>
        public static bool IsEnergized(WireNode acPanel)
        {
            if (acPanel == null) return false;
            var seen = new HashSet<WireNode> { acPanel };
            var queue = new Queue<WireNode>();
            queue.Enqueue(acPanel);
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "ac" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null || !seen.Add(o)) continue;
                    if (o.Role == WireRole.Inverter) { if (MissingFrom(o) == WireRole.None) return true; }
                    else if (o.Role == WireRole.WindTurbine) { ConstructionSite ws = o.GetComponent<ConstructionSite>(); if (ws != null && ws.Finished) return true; }   // it has its own inverter
                    else if (o.Role == WireRole.WallEntry || o.Role == WireRole.AcPanel) queue.Enqueue(o);   // AC carried through a wall entry or on from another breaker box
                    else if (o.Role == WireRole.Disconnect) { if (!o.SwitchOff) queue.Enqueue(o); }   // through a safety disconnect while it is on
                }
            }
            return false;
        }

        // ------------------------------------------------------------------ the grid systems (the Grid OS app)

        /// <summary>One separate electrical system: every device joined by wire, however many buildings it spans.</summary>
        public sealed class GridSystem
        {
            public string Name;
            public int Panels;           // panels fitted
            public float SolarW, RatedW; // what they make now, and what they would make at full sun
            public int Batteries;
            public float StoredWh, CapacityWh;
            public float InverterW, InverterRatedW;
            public int Turbines;
            public float WindW, WindRatedW;
            public float LoadW, ServedW; // what the building's lights draw, and what the system can give them
            public float Ratio = 1f;     // served / load: the voltage the lights get, 1 full
            public float Voltage = NominalV;
            public float DirectW;        // generation that cannot be stored (wind AC straight to a panel, generators): used as it is made
            public float WastedW;        // solar the system makes and neither stores nor uses right now (batteries full, no controller, over its rating)
            public float FullInH = 0f;   // game hours until the batteries are full at the rate now (0 full, -1 not charging)
            public bool Live;            // an AC panel is energized
            public int Key;              // the same system keeps the same key while its lowest device stands
            public List<WireNode> Nodes = new List<WireNode>();
        }

        /// <summary>The last 24 game hours of a system, one sample every 15 game minutes (the graphs of the Grid OS app).</summary>
        public sealed class GridSeries
        {
            public const int Max = 96;
            public readonly List<float> Solar = new List<float>(), BatteryPct = new List<float>(), Inverter = new List<float>(), Wasted = new List<float>(), Load = new List<float>();
            public void Add(float solar, float pct, float inverter, float wasted, float load)
            {
                Solar.Add(solar); BatteryPct.Add(pct); Inverter.Add(inverter); Wasted.Add(wasted); Load.Add(load);
                while (Solar.Count > Max) { Solar.RemoveAt(0); BatteryPct.RemoveAt(0); Inverter.RemoveAt(0); Wasted.RemoveAt(0); Load.RemoveAt(0); }
            }
            /// <summary>The solar energy wasted over the window, in watt-hours (a sample is 15 game minutes).</summary>
            public float WastedWh() { float sum = 0f; foreach (float w in Wasted) sum += w * 0.25f; return sum; }
        }

        private static readonly Dictionary<int, GridSeries> s_series = new Dictionary<int, GridSeries>();
        private static float s_sampleHours;

        public const float NominalV = 115f;

        /// <summary>The power balance of one system for a stretch of dtH game hours (apply: take the energy out of the batteries and put the spare solar in).</summary>
        public sealed class Balance
        {
            public float LoadW, ServedW, Ratio = 1f;
            public float SolarW, SolarUsedW, SolarSpareW, WindW, WindUsedW, BatteryW;
            public float PumpW;   // what the running well pumps draw
            public readonly List<WireNode> RunningWells = new List<WireNode>();
            public bool Room;
            public readonly List<ConstructionSite> Sites = new List<ConstructionSite>();
        }

        public static Balance BalanceOf(List<WireNode> group, float dtH, bool apply)
        {
            var b = new Balance();
            float mpptCap = 0f, invRated = 0f, stored = 0f, room = 0f;
            bool acLive = false;
            var batteries = new List<WireNode>();
            foreach (WireNode n in group)
            {
                if (n == null) continue;
                AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
                switch (n.Role)
                {
                    case WireRole.SolarPanel: b.SolarW += SolarSun.PanelWatts(n); break;
                    case WireRole.WindTurbine: b.WindW += WindWatts(n); break;
                    case WireRole.Mppt: if (it != null) mpptCap += it.max_power_w; break;
                    case WireRole.Inverter: if (it != null && MissingFrom(n) == WireRole.None) invRated += it.max_power_w; break;
                    case WireRole.Battery:
                        if (n.CapacityWh > 0f) { batteries.Add(n); stored += Mathf.Min(n.ChargeWh, n.CapacityWh); room += Mathf.Max(0f, n.CapacityWh - n.ChargeWh); }
                        break;
                    case WireRole.AcPanel:
                    {
                        AttachedObject at = n.GetComponent<AttachedObject>();
                        if (at != null && at.Site != null && IsEnergized(n)) { acLive = true; if (!b.Sites.Contains(at.Site) && (!s_onGen.Contains(at.Site) || at.Site == s_probe)) b.Sites.Add(at.Site); }   // a building on its generator is not this system's load
                        // a fuel pump wired to this box: its motor is load while it fills something
                        if (IsEnergized(n))
                            foreach (WireLink fl in Links)
                                if (fl.Kind == "ac" && fl.Connects(n) && fl.Other(n) != null && fl.Other(n).Role == WireRole.FuelPump) b.PumpW += FuelNozzle.RunningW(fl.Other(n));
                        ConstructionSite well = n.Well;
                        if (well != null && IsEnergized(n) && WellWantsToRun(n))
                        {
                            AssetCatalogItem pump = HudBindings.GetCatalogItem(well.PumpId);
                            if (pump != null) { b.PumpW += pump.power_draw_w; b.RunningWells.Add(n); }
                        }
                        break;
                    }
                }
            }
            float solarAvail = mpptCap > 0f ? Mathf.Min(b.SolarW, mpptCap) : 0f;
            foreach (ConstructionSite s in b.Sites) b.LoadW += LightEmitter.WantedWatts(s) + HeaterLoadW(s) + WaterPumpLoadW(s) + Net.LoadW(s);   // the lights, the water heaters and the water pumps
            b.LoadW += b.PumpW;   // the well pumps are load like the lights
            float rem = b.LoadW;
            b.WindUsedW = Mathf.Min(b.WindW, rem);
            rem -= b.WindUsedW;
            float inv = invRated;
            b.SolarUsedW = Mathf.Min(Mathf.Min(solarAvail, rem), inv);
            rem -= b.SolarUsedW;
            inv -= b.SolarUsedW;
            float canGive = dtH > 0f ? stored / dtH : (stored > 0f ? float.MaxValue : 0f);
            b.BatteryW = Mathf.Max(0f, Mathf.Min(Mathf.Min(rem, inv), canGive));
            rem -= b.BatteryW;
            b.ServedW = b.LoadW - rem;
            b.Ratio = b.LoadW > 0.01f ? Mathf.Clamp01(b.ServedW / b.LoadW) : 1f;
            b.SolarSpareW = Mathf.Max(0f, solarAvail - b.SolarUsedW);
            b.Room = room > 0.5f;
            if (apply && dtH > 0f)
            {
                float take = b.BatteryW * dtH, give = b.Room ? b.SolarSpareW * dtH : 0f;
                foreach (WireNode n in batteries)
                {
                    if (take > 0f) { float t = Mathf.Min(take, n.ChargeWh); n.ChargeWh -= t; take -= t; }
                    if (give > 0f) { float r = Mathf.Max(0f, n.CapacityWh - n.ChargeWh); float g = Mathf.Min(r, give); n.ChargeWh += g; give -= g; }
                    n.ChargeWh = Mathf.Min(n.ChargeWh, n.CapacityWh);
                }
            }
            return b;
        }

        private static readonly Dictionary<ConstructionSite, float> s_siteRatio = new Dictionary<ConstructionSite, float>();

        /// <summary>How much of its voltage a building's lights get: 0 with no power at all (they go out at once), below 1 in a brownout, 1 otherwise.</summary>
        public static float SupplyRatio(ConstructionSite site)
        {
            if (site == null || !AttachedObject.HasPower(site)) return 0f;
            return s_siteRatio.TryGetValue(site, out float r) ? r : 1f;
        }

        public static GridSeries SeriesOf(int key)
        {
            if (!s_series.TryGetValue(key, out GridSeries s)) { s = new GridSeries(); s_series[key] = s; }
            return s;
        }

        private static void Sample()
        {
            var keys = new HashSet<int>();
            foreach (GridSystem sys in Systems())
            {
                keys.Add(sys.Key);
                SeriesOf(sys.Key).Add(sys.SolarW, sys.CapacityWh > 0f ? sys.StoredWh / sys.CapacityWh * 100f : 0f, sys.InverterW, sys.WastedW, sys.LoadW);
            }
            var stale = new List<int>();
            foreach (int k in s_series.Keys) if (!keys.Contains(k)) stale.Add(k);
            foreach (int k in stale) s_series.Remove(k);
        }

        /// <summary>One short line about a device for the system's component list.</summary>
        public static string NodeStat(WireNode n)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
            switch (n.Role)
            {
                case WireRole.SolarPanel:
                    return MountedPanel.PanelOn(n.gameObject) == null ? "No panel fitted" : SolarSun.Power(SolarSun.PanelWatts(n)) + " now";
                case WireRole.Battery:
                    return n.CapacityWh > 0f ? Mathf.RoundToInt(Mathf.Clamp01(n.ChargeWh / n.CapacityWh) * 100f) + "%  " + (n.ChargeWh >= 1000f ? (n.ChargeWh / 1000f).ToString("0.##") + " kWh" : Mathf.RoundToInt(n.ChargeWh) + " Wh") : "";
                case WireRole.Mppt:
                    return SolarSun.Power(it != null && it.max_power_w > 0f ? Mathf.Min(SolarSun.InputWatts(n), it.max_power_w) : SolarSun.InputWatts(n)) + " charging";
                case WireRole.Inverter:
                    return SolarSun.Power(InverterOutputW(n)) + " of " + SolarSun.Power(it != null ? it.max_power_w : 0f);
                case WireRole.AcPanel:
                    return IsEnergized(n) ? "Live" : "Not live";
                case WireRole.WindTurbine:
                    return SolarSun.Power(WindWatts(n)) + " of " + SolarSun.Power(it != null ? it.max_power_w : 0f);
                case WireRole.WaterTank:
                    return UnitFormat.Volume(n.WaterL) + " of " + UnitFormat.Volume(n.WaterCapacityL) + (n.WaterL > 0.5f ? ", " + WaterType(n).ToLowerInvariant() : "");
                case WireRole.WaterFilter:
                    return n.FilterBit == 1 ? "Sediment stage" : n.FilterBit == 2 ? "Carbon stage" : n.FilterBit == 4 ? "UV stage" : "Filter";
                default:
                    return SolarSun.Power(SolarSun.InputWatts(n));
            }
        }

        /// <summary>The energy stored in every battery in the world, in watt-hours (what the HUD shows).</summary>
        public static float TotalStoredWh()
        {
            float sum = 0f;
            foreach (WireNode n in WireNode.All) if (n != null && n.Role == WireRole.Battery) sum += n.ChargeWh;
            return sum;
        }

        /// <summary>The wired systems: devices that share a wire (through wall entries, bus bars and all) are one system, named after the buildings it is mounted on.</summary>
        private static List<GridSystem> s_systemsCache;
        private static float s_systemsTime = -10f;

        /// <summary>The systems as they were up to a quarter of a second ago: for what is drawn (WAILA, the phone), which asks every frame.</summary>
        public static List<GridSystem> SystemsCached()
        {
            if (s_systemsCache == null || Time.unscaledTime - s_systemsTime > 0.25f) { s_systemsCache = Systems(); s_systemsTime = Time.unscaledTime; }
            return s_systemsCache;
        }

        public static List<GridSystem> Systems()
        {
            var result = new List<GridSystem>();
            var seen = new HashSet<WireNode>();
            foreach (WireLink l in Links)
            {
                if (l.A == null || l.B == null || seen.Contains(l.A) || l.Kind == "net" || l.Kind == "sewer" || l.Kind == "propane" || l.Kind == "fuel" || Cut(l)) continue;   // a drain, gas or fuel line joins no power system
                var group = new List<WireNode> { l.A };
                seen.Add(l.A);
                for (int i = 0; i < group.Count; i++)
                    foreach (WireLink k in Links)
                    {
                        if (k.Kind == "net" || k.Kind == "sewer" || k.Kind == "propane" || k.Kind == "fuel" || Cut(k) || !k.Connects(group[i])) continue;
                        WireNode o = k.Other(group[i]);
                        if (o != null && seen.Add(o)) group.Add(o);
                    }
                var sys = new GridSystem();
                sys.Nodes = group;
                int lowest = int.MaxValue;
                foreach (WireNode gn in group) if (gn != null) lowest = Mathf.Min(lowest, gn.Uid);
                sys.Key = lowest;
                var sites = new List<ConstructionSite>();
                foreach (WireNode n in group)
                {
                    AttachedObject at = n.GetComponent<AttachedObject>();
                    if (at != null && at.Site != null && !sites.Contains(at.Site)) sites.Add(at.Site);
                    ConstructionSite own = n.GetComponent<ConstructionSite>();
                    if (own != null && !sites.Contains(own)) sites.Add(own);
                    AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
                    switch (n.Role)
                    {
                        case WireRole.SolarPanel:
                        {
                            string fitted = MountedPanel.PanelOn(n.gameObject);
                            if (fitted == null) break;
                            AssetCatalogItem pi = HudBindings.GetCatalogItem(fitted);
                            sys.Panels++;
                            sys.SolarW += SolarSun.PanelWatts(n);
                            if (pi != null) sys.RatedW += pi.max_power_w;
                            break;
                        }
                        case WireRole.Battery:
                            if (n.CapacityWh > 0f && sys.Batteries == 0) sys.FullInH = FullInHours(n);
                            if (n.CapacityWh > 0f) { sys.Batteries++; sys.StoredWh += Mathf.Min(n.ChargeWh, n.CapacityWh); sys.CapacityWh += n.CapacityWh; }
                            break;
                        case WireRole.Inverter:
                            sys.InverterW += InverterOutputW(n);
                            if (it != null) sys.InverterRatedW += it.max_power_w;
                            break;
                        case WireRole.AcPanel:
                            if (IsEnergized(n)) sys.Live = true;
                            break;
                        case WireRole.StandbyGenerator:
                            sys.DirectW += n.GenW;   // a running standby generator: AC used as it is made
                            break;
                        case WireRole.WindTurbine:
                            sys.Turbines++;
                            sys.WindW += WindWatts(n);
                            if (it != null) sys.WindRatedW += it.max_power_w;
                            break;
                    }
                }
                sys.DirectW = sys.WindW;   // wind makes AC for the panel it is wired to: it cannot go into a battery (no generators exist yet; they would add here)
                // solar is stored by the batteries on the same DC side as the panels, through a controller, while they have room: what they do not take is wasted
                Balance bal = BalanceOf(group, 0.25f, false);
                sys.LoadW = bal.LoadW;
                sys.ServedW = bal.ServedW;
                sys.Ratio = bal.Ratio;
                sys.Voltage = NominalV * bal.Ratio;
                sys.WastedW = Mathf.Max(0f, sys.SolarW - bal.SolarUsedW - (bal.Room ? bal.SolarSpareW : 0f));   // what the lights do not use and the batteries cannot take
                var names = new List<string>();
                foreach (ConstructionSite s in sites) { string nm = s.Name(); if (!names.Contains(nm)) names.Add(nm); }
                sys.Name = names.Count > 0 ? string.Join(" + ", names) : "Outdoor system";
                result.Add(sys);
            }
            return result;
        }

        // ------------------------------------------------------------------ battery charge

        /// <summary>Every device joined to <paramref name="from"/> by DC wire (bus bars included), the device itself too.</summary>
        private static List<WireNode> DcGroup(WireNode from)
        {
            var group = new List<WireNode> { from };
            var seen = new HashSet<WireNode> { from };
            for (int i = 0; i < group.Count; i++)
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "dc" || !l.Connects(group[i])) continue;
                    WireNode o = l.Other(group[i]);
                    if (o != null && seen.Add(o)) group.Add(o);
                }
            return group;
        }

        /// <summary>What the sun gives the batteries wired to <paramref name="battery"/> right now: the panels' output, only through a charge controller, held to its rating.</summary>
        public static float ChargeInputW(WireNode battery)
        {
            float panels = 0f, cap = 0f;
            foreach (WireNode n in DcGroup(battery))
            {
                if (n.Role == WireRole.SolarPanel) panels += SolarSun.PanelWatts(n);
                else if (n.Role == WireRole.Mppt) { AssetCatalogItem m = HudBindings.GetCatalogItem(n.ItemId); if (m != null) cap += m.max_power_w; }
            }
            return Mathf.Min(panels, cap);
        }

        /// <summary>Game hours until the batteries wired with this one are full at the charging rate right now: 0 when full, -1 when nothing is charging them.</summary>
        public static float FullInHours(WireNode battery)
        {
            float room = 0f;
            foreach (WireNode n in DcGroup(battery)) if (n.Role == WireRole.Battery) room += Mathf.Max(0f, n.CapacityWh - n.ChargeWh);
            if (room <= 0.5f) return 0f;
            float w = ChargeInputW(battery);
            return w > 1f ? room / w : -1f;
        }

        public static string FormatFullIn(float hours)
        {
            if (hours == 0f) return "Full";
            if (hours < 0f) return "Not charging";
            int minutes = Mathf.Max(1, Mathf.RoundToInt(hours * 60f));
            return minutes >= 60 ? (minutes / 60) + "h " + (minutes % 60) + "m" : minutes + "m";
        }

        private static float s_chargeTime;

        /// <summary>Fills the batteries from the sun in game time (twice a second). Nothing draws them down yet: no building load exists.</summary>
        private const float PanelJoinGap = 0.45f;   // metres between two panels' edges: closer than this they are one group
        private static float s_nextGroupScan;

        /// <summary>The distance between the edges of two boxes (0 when they touch or overlap).</summary>
        private static float BoxGap(Bounds a, Bounds b)
        {
            float dx = Mathf.Max(0f, Mathf.Abs(a.center.x - b.center.x) - (a.extents.x + b.extents.x));
            float dy = Mathf.Max(0f, Mathf.Abs(a.center.y - b.center.y) - (a.extents.y + b.extents.y));
            float dz = Mathf.Max(0f, Mathf.Abs(a.center.z - b.center.z) - (a.extents.z + b.extents.z));
            return Mathf.Sqrt(dx * dx + dy * dy + dz * dz);
        }

        /// <summary>Solar panels standing side by side (their edges within <see cref="PanelJoinGap"/>) are joined by themselves into a group: an unseen DC link of no length, so one wire
        /// from any panel of the group carries the whole group (<see cref="SolarSun.InputWatts"/> walks through them), and one wire from one group to another joins the two. Scanned about once a second.</summary>
        public static void TickSolarGroups()
        {
            if (Time.unscaledTime < s_nextGroupScan) return;
            s_nextGroupScan = Time.unscaledTime + 1f;
            var panels = new List<WireNode>();
            foreach (WireNode n in WireNode.All) if (n != null && n.Role == WireRole.SolarPanel && n.isActiveAndEnabled) panels.Add(n);
            for (int i = Links.Count - 1; i >= 0; i--)   // joints whose panels moved apart (or went) are dropped
            {
                WireLink l = Links[i];
                if (!l.Auto) continue;
                if (l.A == null || l.B == null || BoxGap(l.A.WorldBounds(), l.B.WorldBounds()) > PanelJoinGap + 0.1f) Links.RemoveAt(i);
            }
            for (int i = 0; i < panels.Count; i++)
                for (int j = i + 1; j < panels.Count; j++)
                {
                    if (BoxGap(panels[i].WorldBounds(), panels[j].WorldBounds()) > PanelJoinGap || LinkBetween(panels[i], panels[j]) != null) continue;
                    Links.Add(new WireLink { A = panels[i], B = panels[j], Kind = "dc", Length = 0f, Auto = true, RouteFinal = true });
                }
        }

        public static void TickCharge()
        {
            if (TimeSystem.Instance == null) return;
            float dt = Time.unscaledDeltaTime;
            s_chargeTime += dt * TimeSystem.SpeedToMultiplier(TimeSystem.Instance.CurrentSpeed);
            if (s_chargeTime < 0.5f) return;
            float gameHours = s_chargeTime * TimeConstants.GameMinutesPerRealSecondAt1X / 60f;
            s_chargeTime = 0f;
            s_sampleHours += gameHours;
            if (s_sampleHours >= 0.25f) { s_sampleHours = 0f; Sample(); }
            PortableGenerator.Tick();
            s_siteRatio.Clear();
            List<GridSystem> all = Systems();
            LogSystems(all);
            foreach (GridSystem sys in all)
            {
                Balance bal = BalanceOf(sys.Nodes, gameHours, true);   // the lights draw from the sun first and the batteries after; what the sun has spare charges them
                foreach (ConstructionSite site in bal.Sites) s_siteRatio[site] = bal.Ratio;
                if (bal.Ratio >= 0.85f) foreach (WireNode well in bal.RunningWells) PumpInto(well, WellFlowLph(well) * gameHours);   // a pump stalls in a brownout
            }
            TickLockouts(all, gameHours);   // the buildings with a generator lockout box: on the breaker box or on the generator, never both
            TickPowerAlerts(all);           // a toast when a building loses power, runs low, or goes over to its generator
            CountStores();                  // the HUD's water and fuel
            TickHeaters(gameHours);   // the water heaters warm with their building's power
            TickWaterPumps(gameHours);   // the water pumps pull water out of the cisterns
            Septic.Tick(gameHours);      // the leach fields soak away
            Net.Tick(gameHours);         // a rack UPS charges, or runs its rack through a power cut
            TickPlumbed(gameHours);      // the tanks plumbed into a building (a water heater with no pipe of its own) fill from its supply
        }

        private static string s_systemsSignature = "";

        /// <summary>Writes the systems to the log whenever they change (which devices are in which), so a wrong grouping can be read off.</summary>
        private static void LogSystems(List<GridSystem> all)
        {
            var sb = new System.Text.StringBuilder();
            foreach (GridSystem g in all)
            {
                sb.Append("[").Append(g.Name).Append(": ");
                foreach (WireNode n in g.Nodes) if (n != null) sb.Append(n.ItemId).Append('#').Append(n.Uid).Append(' ');
                sb.Append("] ");
            }
            string sig = sb.ToString();
            if (sig == s_systemsSignature) return;
            s_systemsSignature = sig;
            Dbg.Log("[Grid] " + all.Count + " system(s): " + sig);
        }

        /// <summary>What an inverter delivers right now: the solar reaching it (when its chain is complete), held to the controller and the inverter ratings.</summary>
        public static float InverterOutputW(WireNode inverter)
        {
            if (inverter == null || MissingFrom(inverter) != WireRole.None) return 0f;
            AssetCatalogItem inv = HudBindings.GetCatalogItem(inverter.ItemId);
            float w = SolarSun.InputWatts(inverter);
            float mpptCap = 0f;
            var seen = new HashSet<WireNode> { inverter };
            var queue = new Queue<WireNode>();
            queue.Enqueue(inverter);
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "dc" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null || !seen.Add(o)) continue;
                    if (o.Role == WireRole.SolarPanel) continue;
                    if (o.Role == WireRole.Mppt) { AssetCatalogItem m = HudBindings.GetCatalogItem(o.ItemId); if (m != null) mpptCap += m.max_power_w; }
                    queue.Enqueue(o);
                }
            }
            if (mpptCap > 0f) w = Mathf.Min(w, mpptCap);
            if (inv != null && inv.max_power_w > 0f) w = Mathf.Min(w, inv.max_power_w);
            return w;
        }

        // ------------------------------------------------------------------ wells and tanks (docs/WELLS.md)

        public const int AllStages = 7;   // sediment, carbon and uv: the water is clean

        /// <summary>The tanks a well (or a tank) is piped to, through filters and tanks, nearest first.</summary>
        public static List<WireNode> TanksOf(WireNode from)
        {
            var tanks = new List<WireNode>();
            foreach (KeyValuePair<WireNode, int> t in TankStages(from)) tanks.Add(t.Key);
            return tanks;
        }

        /// <summary>
        /// The tanks the water from <paramref name="from"/> reaches and, for each, the filter stages it went through on the best way there (bits: 1 sediment, 2 carbon,
        /// 4 uv; all three = clean). Water runs through filters and on through tanks.
        /// </summary>
        public static List<KeyValuePair<WireNode, int>> TankStages(WireNode from)
        {
            var result = new List<KeyValuePair<WireNode, int>>();
            var best = new Dictionary<WireNode, int>();
            var queue = new Queue<KeyValuePair<WireNode, int>>();
            best[from] = 0;
            queue.Enqueue(new KeyValuePair<WireNode, int>(from, 0));
            while (queue.Count > 0)
            {
                KeyValuePair<WireNode, int> cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "water" || !l.Connects(cur.Key)) continue;
                    WireNode o = l.Other(cur.Key);
                    if (o == null || o.Well != null || best.ContainsKey(o)) continue;
                    // the water takes the SHORTEST way (first reached): a filter further round a loop, which it never goes through, does not clean it
                    best[o] = cur.Value | o.FilterBit;
                    queue.Enqueue(new KeyValuePair<WireNode, int>(o, best[o]));
                }
            }
            foreach (KeyValuePair<WireNode, int> kv in best)
                if (kv.Key.Role == WireRole.WaterTank) result.Add(kv);
            return result;
        }

        /// <summary>A well pumps while it is finished, has its pump and some tank it is piped to has room.</summary>
        public static bool WellWantsToRun(WireNode wellNode)
        {
            ConstructionSite well = wellNode != null ? wellNode.Well : null;
            if (well == null || !well.Finished || string.IsNullOrEmpty(well.PumpId)) return false;
            foreach (WireNode t in TanksOf(wellNode)) if (t.WaterL < t.WaterCapacityL - 0.5f) return true;
            return false;
        }

        /// <summary>Liters an hour the well gives: its pump's flow, held to what the aquifer under it gives.</summary>
        public static float WellFlowLph(WireNode wellNode)
        {
            ConstructionSite well = wellNode != null ? wellNode.Well : null;
            if (well == null) return 0f;
            AssetCatalogItem pump = HudBindings.GetCatalogItem(well.PumpId);
            return pump != null ? Mathf.Min(pump.flow_lph, WaterTable.YieldLph(well.transform.position)) : 0f;
        }

        private const float GroundWaterC = 12f;

        /// <summary>Liters an hour a pipe of this item carries (its manifest's flow_lph); 0 = no limit (an item that sets none).</summary>
        public static float PipeFlowLph(string pipeItem)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(pipeItem);
            return it != null && it.wire_kind == "water" ? it.flow_lph : 0f;
        }

        /// <summary>
        /// What the pipes let through from <paramref name="from"/> to everything its water lines reach, in liters an hour: a way is as good as its NARROWEST pipe, and of
        /// several ways the best counts. float.MaxValue = nothing on the way limits it.
        /// </summary>
        public static Dictionary<WireNode, float> PipeCaps(WireNode from)
        {
            var caps = new Dictionary<WireNode, float>();
            if (from == null) return caps;
            var queue = new Queue<WireNode>();
            caps[from] = float.MaxValue;
            queue.Enqueue(from);
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "water" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null || o.Well != null) continue;
                    float pipe = PipeFlowLph(l.WireItem);
                    float c = Mathf.Min(caps[cur], pipe > 0f ? pipe : float.MaxValue);
                    if (caps.TryGetValue(o, out float had) && had >= c) continue;
                    caps[o] = c;
                    queue.Enqueue(o);
                }
            }
            return caps;
        }

        /// <summary>Liters an hour that actually leave the well: its flow (<see cref="WellFlowLph"/>), held to what the pipes carry to the best-piped tank that has room.</summary>
        public static float PipedFlowLph(WireNode wellNode)
        {
            float flow = WellFlowLph(wellNode);
            if (flow <= 0f) return 0f;
            Dictionary<WireNode, float> caps = PipeCaps(wellNode);
            float best = 0f;
            bool any = false;
            foreach (KeyValuePair<WireNode, float> kv in caps)
            {
                if (kv.Key.Role != WireRole.WaterTank) continue;
                if (kv.Key.WaterL < kv.Key.WaterCapacityL - 0.5f) { best = Mathf.Max(best, kv.Value); any = true; }
            }
            return any ? Mathf.Min(flow, best) : flow;
        }

        private static void PumpInto(WireNode wellNode, float liters)
        {
            // The pipes hold the pump back: liters is what the pump would lift this tick at its full flow; the narrowest pipe on the way to a tank lets only its share through.
            float flow = WellFlowLph(wellNode);
            Dictionary<WireNode, float> caps = PipeCaps(wellNode);
            float tick = liters;
            if (flow > 0f) liters *= Mathf.Clamp01(PipedFlowLph(wellNode) / flow);
            foreach (KeyValuePair<WireNode, int> kv in TankStages(wellNode))
            {
                if (liters <= 0f) break;
                WireNode t = kv.Key;
                float room = Mathf.Max(0f, t.WaterCapacityL - t.WaterL);
                float share = flow > 0f && caps.TryGetValue(t, out float cap) ? Mathf.Clamp01(cap / flow) : 1f;   // what the pipes to THIS tank carry
                float put = Mathf.Min(room, Mathf.Min(liters, tick * share));
                if (put <= 0f) continue;
                t.TempC = t.WaterL + put > 0f ? (t.TempC * t.WaterL + GroundWaterC * put) / (t.WaterL + put) : GroundWaterC;   // cold well water mixes in
                t.WaterL += put;
                if ((kv.Value & AllStages) != AllStages) t.RawL += put;   // it missed a filter stage: not drinkable
                liters -= put;
            }
        }

        // ------------------------------------------------------------------ what flows where (the look-at panel)

        private static Dictionary<WireNode, KeyValuePair<float, int>> s_flowMap;
        private static float s_flowTime = -10f;

        /// <summary>
        /// The water moving through every part of the water lines right now: for each part the wells pumping into it reach, the liters an hour going through it and
        /// the filter stages the water has been through by then (bits: 1 sediment, 2 carbon, 4 uv). Worked out at most twice a second.
        /// </summary>
        public static Dictionary<WireNode, KeyValuePair<float, int>> FlowMap()
        {
            if (s_flowMap != null && Time.unscaledTime - s_flowTime < 0.5f) return s_flowMap;
            s_flowTime = Time.unscaledTime;
            s_flowMap = new Dictionary<WireNode, KeyValuePair<float, int>>();
            foreach (WireNode w in WireNode.All)
            {
                if (w == null || w.Well == null || !IsEnergized(w) || !WellWantsToRun(w)) continue;
                float lph = WellFlowLph(w);
                var best = new Dictionary<WireNode, int> { [w] = 0 };
                var queue = new Queue<WireNode>();
                queue.Enqueue(w);
                while (queue.Count > 0)
                {
                    WireNode cur = queue.Dequeue();
                    foreach (WireLink l in Links)
                    {
                        if (l.Kind != "water" || !l.Connects(cur)) continue;
                        WireNode o = l.Other(cur);
                        if (o == null || o.Well != null || best.ContainsKey(o)) continue;
                        best[o] = best[cur] | o.FilterBit;   // the shortest way: a filter round a loop does not clean it
                        queue.Enqueue(o);
                    }
                }
                foreach (KeyValuePair<WireNode, int> kv in best)
                {
                    if (kv.Key == w) continue;
                    s_flowMap.TryGetValue(kv.Key, out KeyValuePair<float, int> was);
                    s_flowMap[kv.Key] = new KeyValuePair<float, int>(was.Key + lph, was.Value | kv.Value);
                }
            }
            // a running water pump moves water too: up its intake side (from the cistern, through an inlet or anything else on the way) and on out the other sides
            foreach (WireNode p in WireNode.All)
            {
                if (p == null || p.Role != WireRole.WaterPump || !p.PumpRunning || p.PumpIntake == null) continue;
                int src = p.PumpClean ? AllStages : 0;
                var best = new Dictionary<WireNode, int> { [p] = src };
                var queue = new Queue<WireNode>();
                best[p.PumpIntake] = src;
                queue.Enqueue(p.PumpIntake);
                while (queue.Count > 0)
                {
                    WireNode cur = queue.Dequeue();
                    foreach (WireLink l in Links)
                    {
                        if (l.Kind != "water" || !l.Connects(cur)) continue;
                        WireNode o = l.Other(cur);
                        if (o == null || o.Well != null || best.ContainsKey(o)) continue;
                        best[o] = src;   // the intake side: what it pulls, as it is
                        queue.Enqueue(o);
                    }
                }
                queue.Enqueue(p);
                while (queue.Count > 0)
                {
                    WireNode cur = queue.Dequeue();
                    foreach (WireLink l in Links)
                    {
                        if (l.Kind != "water" || !l.Connects(cur)) continue;
                        WireNode o = l.Other(cur);
                        if (o == null || o.Well != null || best.ContainsKey(o)) continue;
                        best[o] = best[cur] | o.FilterBit;   // the out side: cleaned by the filters on the way
                        queue.Enqueue(o);
                    }
                }
                foreach (KeyValuePair<WireNode, int> kv in best)
                {
                    s_flowMap.TryGetValue(kv.Key, out KeyValuePair<float, int> was);
                    s_flowMap[kv.Key] = new KeyValuePair<float, int>(was.Key + p.PumpedLph, was.Value | kv.Value);
                }
            }
            return s_flowMap;
        }

        /// <summary>Words for the filter stages water has been through.</summary>
        public static string StagesText(int mask)
        {
            if ((mask & AllStages) == AllStages) return "Clean (sediment, carbon, UV)";
            if (mask == 0) return "Raw (unfiltered)";
            var parts = new List<string>();
            if ((mask & 1) != 0) parts.Add("sediment");
            if ((mask & 2) != 0) parts.Add("carbon");
            if ((mask & 4) != 0) parts.Add("UV");
            return "Raw, " + string.Join(" and ", parts) + " done";
        }

        /// <summary>The flow and quality rows of a part of a water line.</summary>
        private static void WaterRows(WireNode n, List<(string, string)> rows)
        {
            if (FlowMap().TryGetValue(n, out KeyValuePair<float, int> f))
            {
                rows.Add(("Flow", UnitFormat.Volume(f.Key) + " an hour"));
                rows.Add(("Water here", StagesText(f.Value)));
            }
            else rows.Add(("Flow", "None (no well or water pump moving water through it)"));
        }

        /// <summary>What a tank holds: "Empty", "Clean water (drinkable)", "Raw well water (unfiltered)", or how much raw is mixed into the clean.</summary>
        public static string WaterType(WireNode tank)
        {
            if (tank == null || tank.WaterL < 0.5f) return "Empty";
            if (tank.RawL < 0.5f) return "Clean water (drinkable)";
            if (tank.RawL >= tank.WaterL - 0.5f) return "Raw well water (unfiltered)";
            return "Mixed: " + Mathf.RoundToInt(tank.RawL / tank.WaterL * 100f) + "% raw";
        }

        // ------------------------------------------------------------------ water into a building

        /// <summary>
        /// Takes up to <paramref name="liters"/> from the tanks the building's water inlets are piped to (nearest first) and returns what it took. Clean only: just water
        /// that came through every filter stage (or crosses them on the way to the inlet). Why there is none, when there is none.
        /// </summary>
        /// <summary>Takes water for a spigot standing in the yard (a spigot post) from the tanks it is piped to. Returns the liters taken; <paramref name="why"/> says why there were none.</summary>
        public static float DrawWaterAt(WireNode spigot, float liters, out string why) { return DrawWaterAt(spigot, liters, out why, out _); }

        public static float DrawWaterAt(WireNode spigot, float liters, out string why, out float rawTaken)
        {
            why = null;
            rawTaken = 0f;
            float took = 0f;
            bool anyTank = false;
            foreach (KeyValuePair<WireNode, int> kv in TapSources(spigot))
            {
                if (took >= liters - 0.001f) break;
                WireNode t = kv.Key;
                anyTank = true;
                float take = Mathf.Min(t.WaterL, liters - took);
                if (take <= 0f) continue;
                float rawPart = (kv.Value & AllStages) == AllStages ? 0f : take * (t.WaterL > 0f ? t.RawL / t.WaterL : 0f);
                t.RawL = Mathf.Max(0f, t.RawL - take * (t.WaterL > 0f ? t.RawL / t.WaterL : 0f));   // raw and clean leave in the proportion they are in the tank
                rawTaken += rawPart;                                                                // (unless the filters between it and the spigot clean it)
                t.WaterL -= take;
                took += take;
            }
            if (took <= 0.01f) why = anyTank ? "The tanks are empty." : "The spigot is not piped to a water tank.";
            return took;
        }

        public static float DrawWater(ConstructionSite site, float liters, bool cleanOnly, out string why) { return DrawWater(site, liters, cleanOnly, out why, out _); }

        public static float DrawWater(ConstructionSite site, float liters, bool cleanOnly, out string why, out float rawTaken) { return DrawWater(site, liters, cleanOnly, out why, out rawTaken, true); }

        // ------------------------------------------------------------------ plumbed in: a tank standing in a building with no pipe of its own

        /// <summary>True when the node has a link of this kind (a pipe or a wire of its own).</summary>
        public static bool Piped(WireNode n, string kind)
        {
            foreach (WireLink l in Links) if (l.Kind == kind && l.Connects(n)) return true;
            return false;
        }

        /// <summary>
        /// A water tank (a water heater, a pressure tank) standing in a finished building with no pipe of its own is plumbed into that building's water: the
        /// building's supply keeps it full (<see cref="TickPlumbed"/>) and the building's taps and fixtures draw from it first (hot water). Null when it is not.
        /// </summary>
        public static ConstructionSite PlumbedInto(WireNode n)
        {
            if (n == null || n.Role != WireRole.WaterTank || n.GetComponent<AttachedObject>() != null || Piped(n, "water")) return null;
            return SiteAround(n);
        }

        private static IEnumerable<WireNode> PlumbedTanks(ConstructionSite site)
        {
            foreach (WireNode n in WireNode.All)
                if (n != null && n.Role == WireRole.WaterTank && PlumbedInto(n) == site) yield return n;
        }

        private const float PlumbedFillLph = 1500f;

        /// <summary>The building's supply tops up the tanks plumbed into it, over dtH game hours.</summary>
        private static void TickPlumbed(float dtH)
        {
            foreach (WireNode t in WireNode.All)
            {
                if (t == null || t.Role != WireRole.WaterTank) continue;
                ConstructionSite site = PlumbedInto(t);
                if (site == null) continue;
                float room = Mathf.Min(t.WaterCapacityL - t.WaterL, PlumbedFillLph * dtH);
                if (room <= 0.01f) continue;
                float got = DrawWater(site, room, false, out _, out float raw, false);
                if (got <= 0f) continue;
                t.TempC = (t.TempC * t.WaterL + GroundWaterC * got) / (t.WaterL + got);
                t.WaterL += got;
                t.RawL += raw;
            }
        }

        private static float DrawWater(ConstructionSite site, float liters, bool cleanOnly, out string why, out float rawTaken, bool plumbed)
        {
            why = null;
            rawTaken = 0f;
            float took = 0f;
            bool anyInlet = false, anyTank = false, anyRaw = false;
            if (plumbed)
                foreach (WireNode t in PlumbedTanks(site))   // the water heater in the building first: hot water
                {
                    if (took >= liters - 0.001f) break;
                    anyTank = true;
                    float clean = Mathf.Max(0f, t.WaterL - t.RawL);
                    float avail = cleanOnly ? clean : t.WaterL;
                    if (t.WaterL > 0.01f && clean < 0.01f) anyRaw = true;
                    float take = Mathf.Min(avail, liters - took);
                    if (take <= 0f) continue;
                    float rawShare = cleanOnly ? 0f : (t.WaterL > 0f ? t.RawL / t.WaterL : 0f);
                    t.RawL = Mathf.Max(0f, t.RawL - take * rawShare);
                    rawTaken += take * rawShare;
                    t.WaterL -= take;
                    took += take;
                }
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.WaterInlet) continue;
                AttachedObject at = n.GetComponent<AttachedObject>();
                if (at == null || at.Site != site) continue;
                anyInlet = true;
                foreach (KeyValuePair<WireNode, int> kv in TapSources(n))   // a cistern only through a running water pump; a pressure tank directly
                {
                    if (took >= liters - 0.001f) break;
                    WireNode t = kv.Key;
                    anyTank = true;
                    bool filteredOnWay = (kv.Value & AllStages) == AllStages;
                    float clean = filteredOnWay ? t.WaterL : Mathf.Max(0f, t.WaterL - t.RawL);
                    float avail = cleanOnly ? clean : t.WaterL;
                    if (t.WaterL > 0.01f && clean < 0.01f) anyRaw = true;
                    float take = Mathf.Min(avail, liters - took);
                    if (take <= 0f) continue;
                    float rawShare = cleanOnly && !filteredOnWay ? 0f : (t.WaterL > 0f ? t.RawL / t.WaterL : 0f);
                    t.RawL = Mathf.Max(0f, t.RawL - take * rawShare);
                    if (!filteredOnWay) rawTaken += take * rawShare;
                    t.WaterL -= take;
                    took += take;
                }
            }
            if (took <= 0.01f)
                why = !anyInlet ? "This building has no water inlet: mount one outside and pipe it to a tank." :
                      !anyTank ? "The water inlet is not piped to a tank." :
                      cleanOnly && anyRaw ? "The water is raw: pipe it through the sediment, carbon and UV filters for drinking water." :
                      "The tanks are empty.";
            return took;
        }

        /// <summary>The liters a building's taps can give right now (all, and the clean part).</summary>
        public static void WaterFor(ConstructionSite site, out float all, out float clean)
        {
            all = 0f;
            clean = 0f;
            var counted = new HashSet<WireNode>();
            foreach (WireNode t in PlumbedTanks(site))
                if (counted.Add(t)) { all += t.WaterL; clean += Mathf.Max(0f, t.WaterL - t.RawL); }
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.WaterInlet) continue;
                AttachedObject at = n.GetComponent<AttachedObject>();
                if (at == null || at.Site != site) continue;
                foreach (KeyValuePair<WireNode, int> kv in TapSources(n))   // a cistern only through a running water pump; a pressure tank directly
                {
                    if (!counted.Add(kv.Key)) continue;
                    all += kv.Key.WaterL;
                    clean += (kv.Value & AllStages) == AllStages ? kv.Key.WaterL : Mathf.Max(0f, kv.Key.WaterL - kv.Key.RawL);
                }
            }
        }

        // ------------------------------------------------------------------ water pumps: stored water only moves with one

        internal static bool Powered(WireNode n)
        {
            ConstructionSite site = SiteAround(n);
            return site != null && SupplyRatio(site) >= 0.85f;
        }

        /// <summary>What the water pumps standing in this building draw while they run.</summary>
        public static float WaterPumpLoadW(ConstructionSite site)
        {
            float w = 0f;
            foreach (WireNode n in WireNode.All)
                if (n != null && n.Role == WireRole.WaterPump && n.PumpRunning && SiteAround(n) == site) w += n.PumpDrawW;
            return w;
        }

        /// <summary>The tanks on one side of a pump (from one of its pipes on, not back through the pump or into a well), each with the filter stages on the way to it.</summary>
        private static List<KeyValuePair<WireNode, int>> SideOf(WireNode pump, WireNode start)
        {
            var result = new List<KeyValuePair<WireNode, int>>();
            var best = new Dictionary<WireNode, int> { [pump] = 0, [start] = start.FilterBit };
            var queue = new Queue<WireNode>();
            queue.Enqueue(start);
            if (start.Role == WireRole.WaterTank) result.Add(new KeyValuePair<WireNode, int>(start, best[start]));
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "water" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null || o == pump || o.Well != null || best.ContainsKey(o)) continue;
                    best[o] = best[cur] | o.FilterBit;
                    queue.Enqueue(o);
                    if (o.Role == WireRole.WaterTank) result.Add(new KeyValuePair<WireNode, int>(o, best[o]));
                }
            }
            return result;
        }

        /// <summary>
        /// Every powered water pump moves stored water: from the side of it whose tanks hold the most (the cistern it pulls from) to the tanks on its other sides that have room,
        /// at its flow. Water that passes every filter stage on the way out arrives clean; otherwise it keeps the rawness it had.
        /// </summary>
        private static void TickWaterPumps(float dtH)
        {
            foreach (WireNode p in WireNode.All)
            {
                if (p == null || p.Role != WireRole.WaterPump) continue;
                p.PumpRunning = false;
                p.PumpedLph = 0f;
                p.PumpIntake = null;
                if (!Powered(p)) continue;
                var sides = new List<List<KeyValuePair<WireNode, int>>>();
                var starts = new List<WireNode>();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "water" || !l.Connects(p)) continue;
                    WireNode o = l.Other(p);
                    if (o != null && o.Well == null) { sides.Add(SideOf(p, o)); starts.Add(o); }   // (a building's water inlet is just a pipe: the side runs on through it)
                }
                if (sides.Count < 2) continue;
                int intake = -1;
                float most = 0.5f;
                for (int i = 0; i < sides.Count; i++)
                {
                    float sum = 0f;
                    foreach (KeyValuePair<WireNode, int> t in sides[i]) sum += t.Key.WaterL;
                    if (sum > most) { most = sum; intake = i; }
                }
                if (intake < 0) continue;
                float room = 0f;
                for (int i = 0; i < sides.Count; i++)
                    if (i != intake) foreach (KeyValuePair<WireNode, int> t in sides[i]) room += Mathf.Max(0f, t.Key.WaterCapacityL - t.Key.WaterL);
                float move = Mathf.Min(p.PumpFlowLph * dtH, Mathf.Min(most, room));
                if (move <= 0.01f) continue;
                // out of the cistern(s) on the intake side, raw and clean in their proportion
                float taken = 0f, raw = 0f;
                foreach (KeyValuePair<WireNode, int> t in sides[intake])
                {
                    if (taken >= move - 0.001f) break;
                    float take = Mathf.Min(t.Key.WaterL, move - taken);
                    if (take <= 0f) continue;
                    float rawPart = t.Key.WaterL > 0f ? take * t.Key.RawL / t.Key.WaterL : 0f;
                    t.Key.RawL = Mathf.Max(0f, t.Key.RawL - rawPart);
                    t.Key.WaterL -= take;
                    taken += take;
                    raw += rawPart;
                }
                float rawFrac = taken > 0f ? raw / taken : 0f;
                float left = taken;
                for (int i = 0; i < sides.Count && left > 0f; i++)
                {
                    if (i == intake) continue;
                    foreach (KeyValuePair<WireNode, int> t in sides[i])
                    {
                        if (left <= 0f) break;
                        float put = Mathf.Min(Mathf.Max(0f, t.Key.WaterCapacityL - t.Key.WaterL), left);
                        if (put <= 0f) continue;
                        t.Key.TempC = (t.Key.TempC * t.Key.WaterL + 15f * put) / (t.Key.WaterL + put);
                        t.Key.WaterL += put;
                        if ((t.Value & AllStages) != AllStages) t.Key.RawL += put * rawFrac;   // the filters on the way out clean it
                        left -= put;
                    }
                }
                p.PumpRunning = true;
                p.PumpedLph = dtH > 0f ? taken / dtH : 0f;
                p.PumpIntake = starts[intake];
                p.PumpClean = rawFrac < 0.01f;
            }
        }

        /// <summary>
        /// The tanks a building's tap can draw from through <paramref name="from"/> (its inlet, or a spigot post's own pipe): a pressurized tank (a pressure tank, a water heater)
        /// directly; a plain cistern only through a powered water pump on the way. Each with the filter stages between it and the tap.
        /// </summary>
        public static List<KeyValuePair<WireNode, int>> TapSources(WireNode from)
        {
            var result = new List<KeyValuePair<WireNode, int>>();
            var seen = new HashSet<(WireNode, int, bool)>();
            var queue = new Queue<(WireNode node, int mask, bool pumped)>();
            queue.Enqueue((from, from.FilterBit, false));
            var added = new HashSet<WireNode>();
            while (queue.Count > 0)
            {
                var cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "water" || !l.Connects(cur.node)) continue;
                    WireNode o = l.Other(cur.node);
                    if (o == null || o == from || o.Well != null) continue;
                    int mask = cur.mask | o.FilterBit;
                    bool pumped = cur.pumped || (o.Role == WireRole.WaterPump && Powered(o));
                    if (!seen.Add((o, mask, pumped))) continue;
                    queue.Enqueue((o, mask, pumped));
                    if (o.Role == WireRole.WaterTank && (o.Pressurized || pumped) && added.Add(o)) result.Add(new KeyValuePair<WireNode, int>(o, mask));
                }
            }
            return result;
        }

        // ------------------------------------------------------------------ water heaters

        public const float HotWaterC = 55f;

        /// <summary>The building a placed thing stands in, or null.</summary>
        internal static ConstructionSite SiteAround(WireNode n)
        {
            Vector3 p = n.transform.position;
            foreach (ConstructionSite s in ConstructionSite.All) if (s != null && s.Finished && s.IsInside(p)) return s;
            return null;
        }

        /// <summary>A heater heats while it holds water below its set temperature.</summary>
        private static bool WantsHeat(WireNode n) { return n.HeaterW > 0f && n.WaterL > 1f && n.TempC < HotWaterC - 0.5f; }

        /// <summary>What the water heaters standing in this building draw right now.</summary>
        public static float HeaterLoadW(ConstructionSite site)
        {
            float w = 0f;
            foreach (WireNode n in WireNode.All)
                if (n != null && WantsHeat(n) && SiteAround(n) == site) w += n.HeaterW;
            return w;
        }

        /// <summary>Heats (with the building's power) and lets cool every water heater, over dtH game hours.</summary>
        private static void TickHeaters(float dtH)
        {
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.HeaterW <= 0f || n.WaterL <= 1f) continue;
                ConstructionSite site = SiteAround(n);
                float power = site != null ? SupplyRatio(site) : 0f;
                if (WantsHeat(n) && power >= 0.85f)
                    n.TempC = Mathf.Min(HotWaterC, n.TempC + n.HeaterW * dtH * 0.86f / n.WaterL);   // 1 Wh warms a liter by 0.86 C
                n.TempC = Mathf.MoveTowards(n.TempC, 18f, 1.5f * dtH);                            // and it loses heat to the room
            }
        }

        /// <summary>What a finished wind turbine makes right now, in watts.</summary>
        public static float WindWatts(WireNode n)
        {
            ConstructionSite cs = n != null ? n.GetComponent<ConstructionSite>() : null;
            if (cs == null || !cs.Finished) return 0f;
            WindTurbine t = cs.GetComponentInChildren<WindTurbine>();
            return t != null ? t.Watts : 0f;
        }

        /// <summary>The power an AC panel is fed right now: every inverter wired to it (directly or through a wall entry).</summary>
        public static float SupplyW(WireNode acPanel)
        {
            if (acPanel == null) return 0f;
            float sum = 0f;
            var seen = new HashSet<WireNode> { acPanel };
            var queue = new Queue<WireNode>();
            queue.Enqueue(acPanel);
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "ac" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null || !seen.Add(o)) continue;
                    if (o.Role == WireRole.Inverter) sum += InverterOutputW(o);
                    else if (o.Role == WireRole.WindTurbine) sum += WindWatts(o);
                    else if (o.Role == WireRole.WallEntry || o.Role == WireRole.AcPanel) queue.Enqueue(o);
                }
            }
            return sum;
        }

        private static float pct0(AssetCatalogItem it, WireNode n) { return n.CapacityWh > 0f ? n.ChargeWh / n.CapacityWh : 0f; }

        /// <summary>Rows for the look-at panel: the part's own ratings, what the sun and the wiring give it right now, what it is wired to and what the chain still lacks.</summary>
        // ------------------------------------------------------------------ propane

        /// <summary>True when a propane line (through any number of connectors and tanks) joins this device to a propane tank that has propane in it.</summary>
        public static bool PropaneSupplied(WireNode start) { return PropaneSupplied(start, out _); }

        /// <summary>As above; <paramref name="piped"/> says whether a tank is piped to it at all (an empty one supplies nothing, but the line is there).</summary>
        public static bool PropaneSupplied(WireNode start, out bool piped)
        {
            piped = false;
            if (start == null) return false;
            var seen = new HashSet<WireNode> { start };
            var queue = new Queue<WireNode>();
            queue.Enqueue(start);
            while (queue.Count > 0)
            {
                WireNode n = queue.Dequeue();
                if (n.Role == WireRole.PropaneTank)
                {
                    if (n != start) piped = true;
                    PlacedObject tank = n.GetComponent<PlacedObject>();   // a tank supplies while it has propane in it (the fuel truck fills it: FuelDelivery.cs)
                    if (tank == null || LiquidRules.Held(tank.ItemId, tank.WireUsed) > 0.01f) return true;
                }
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "propane" || !l.Connects(n)) continue;
                    WireNode o = l.Other(n);
                    if (o != null && seen.Add(o)) queue.Enqueue(o);
                }
            }
            return false;
        }

        // ------------------------------------------------------------------ what the HUD shows for water and fuel

        /// <summary>Liters of potable (clean) water stored: the clean part of every water tank, and drinking water in containers on the ground.</summary>
        public static float PotableL { get; private set; }
        /// <summary>Liters of gasoline and diesel stored in fuel tanks, drums and cans on the ground.</summary>
        public static float FuelL { get; private set; }
        /// <summary>The breakdowns the HUD shows on hover: non-potable (raw) water, and each fuel (propane too, which is not in FuelL).</summary>
        public static float RawWaterL { get; private set; }
        public static float GasolineL { get; private set; }
        public static float DieselL { get; private set; }
        public static float PropaneL { get; private set; }

        private static void CountStores()
        {
            float water = 0f, raw = 0f, gas = 0f, diesel = 0f, propane = 0f;
            foreach (WireNode n in WireNode.All)
                if (n != null && n.Role == WireRole.WaterTank) { water += Mathf.Max(0f, n.WaterL - n.RawL); raw += Mathf.Min(n.RawL, n.WaterL); }
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !LiquidRules.IsLiquidContainer(o.ItemId)) continue;
                WireNode wn = o.GetComponent<WireNode>();
                if (wn != null && wn.Role == WireRole.WaterTank) continue;   // counted above
                string liquid = LiquidRules.LiquidIn(o.ItemId, o.LiquidId);
                float held = LiquidRules.Held(o.ItemId, o.WireUsed);
                if (held <= 0f) continue;
                if (liquid == "liquid_water") water += held;
                else if (liquid == "liquid_water_raw") raw += held;
                else if (liquid == "liquid_gasoline") gas += held;
                else if (liquid == "liquid_diesel") diesel += held;
                else if (liquid == "liquid_propane") propane += held;
            }
            PotableL = water;
            RawWaterL = raw;
            GasolineL = gas;
            DieselL = diesel;
            PropaneL = propane;
            FuelL = gas + diesel;
        }

        // ------------------------------------------------------------------ what draws power (the HUD's electricity breakdown)

        /// <summary>Everything drawing power right now, each with its watts, the most first: a powered building's lights, the water heaters heating, the water
        /// pumps and well pumps running, the fuel pumps pumping. <paramref name="total"/> is all of it.</summary>
        public static List<KeyValuePair<string, float>> TopLoads(int count, out float total)
        {
            var list = new List<KeyValuePair<string, float>>();
            foreach (ConstructionSite site in ConstructionSite.All)
            {
                if (site == null || !site.Finished || SupplyRatio(site) <= 0f) continue;
                float w = LightEmitter.WantedWatts(site);
                if (w > 0.5f) list.Add(new KeyValuePair<string, float>("Lights (" + site.Name() + ")", w));
                float netW = Net.LoadW(site);
                if (netW > 0.5f) list.Add(new KeyValuePair<string, float>("Network (" + site.Name() + ")", netW));
            }
            foreach (WireNode n in WireNode.All)
            {
                if (n == null) continue;
                string name = HudBindings.GetItemName(n.ItemId);
                if (WantsHeat(n) && SupplyRatio(SiteAround(n)) > 0f) list.Add(new KeyValuePair<string, float>(name, n.HeaterW));
                else if (n.Role == WireRole.WaterPump && n.PumpRunning) list.Add(new KeyValuePair<string, float>(name, n.PumpDrawW));
                else if (n.Role == WireRole.FuelPump && FuelNozzle.RunningW(n) > 0f) list.Add(new KeyValuePair<string, float>(name, FuelNozzle.RunningW(n)));
                else if (n.Well != null && IsEnergized(n) && WellWantsToRun(n))
                {
                    AssetCatalogItem pump = HudBindings.GetCatalogItem(n.Well.PumpId);
                    if (pump != null && pump.power_draw_w > 0f) list.Add(new KeyValuePair<string, float>(n.Well.Name() + " pump", pump.power_draw_w));
                }
            }
            total = 0f;
            foreach (var kv in list) total += kv.Value;
            list.Sort((x, y) => y.Value.CompareTo(x.Value));
            if (list.Count > count) list.RemoveRange(count, list.Count - count);
            return list;
        }

        // ------------------------------------------------------------------ power alerts

        private enum PowerState { Normal, Low, Generator, Lost }
        private static readonly Dictionary<ConstructionSite, PowerState> s_powerState = new Dictionary<ConstructionSite, PowerState>();

        /// <summary>
        /// Emergency toasts (the player may be anywhere): a building that had power losing it (severe), running low (a brownout, or the batteries feeding it under
        /// 15 %), going over to its standby generator, and its power coming back. Only on a change; the first look at a building (a fresh load, a newly wired one)
        /// says nothing. A building counts once it has a breaker box or a lockout box on its outside wall.
        /// </summary>
        private static void TickPowerAlerts(List<GridSystem> systems)
        {
            var soc = new Dictionary<ConstructionSite, float>();
            foreach (GridSystem sys in systems)
            {
                if (sys.CapacityWh <= 0f) continue;
                float level = sys.StoredWh / sys.CapacityWh;
                foreach (WireNode n in sys.Nodes)
                {
                    if (n == null || n.Role != WireRole.AcPanel) continue;
                    AttachedObject at = n.GetComponent<AttachedObject>();
                    if (at == null || at.Site == null || !at.Exterior) continue;
                    soc[at.Site] = soc.TryGetValue(at.Site, out float had) ? Mathf.Min(had, level) : level;
                }
            }
            var wired = new HashSet<ConstructionSite>();
            foreach (AttachedObject a in AttachedObject.All)
            {
                if (a == null || a.Site == null || !a.Exterior) continue;
                WireNode n = a.GetComponent<WireNode>();
                if ((a.ProvidesPower) || (n != null && n.Role == WireRole.Lockout)) wired.Add(a.Site);
            }
            // While a save is loading, and for a few seconds after, the grid is only half put back (a rack before its batteries, a panel before its wires):
            // the states are noted but no toast is shown for what is just the load settling.
            bool quiet = !Homesteader.Save.GameSaveManager.Restored || Time.realtimeSinceStartup - Homesteader.Save.GameSaveManager.RestoredAt < 6f;
            var gone = new List<ConstructionSite>();
            foreach (ConstructionSite k in s_powerState.Keys) if (k == null || !wired.Contains(k)) gone.Add(k);
            foreach (ConstructionSite k in gone) s_powerState.Remove(k);
            foreach (ConstructionSite site in wired)
            {
                if (!site.Finished) continue;
                bool seen = s_powerState.TryGetValue(site, out PowerState was);
                float ratio = SupplyRatio(site);
                float level = soc.TryGetValue(site, out float l) ? l : 1f;
                PowerState now;
                if (OnGenerator(site)) now = PowerState.Generator;
                else if (!AttachedObject.HasPower(site) || ratio < 0.05f) now = PowerState.Lost;
                else if (ratio < 0.85f || level < 0.15f) now = PowerState.Low;
                else now = seen && was == PowerState.Low && (ratio < 0.95f || level < 0.2f) ? PowerState.Low : PowerState.Normal;   // out of low only once well clear of it
                s_powerState[site] = now;
                if (!seen || now == was || quiet) continue;
                string name = site.Name();
                switch (now)
                {
                    case PowerState.Lost: ToastNotificationSystem.ShowSevere("Power lost", name + " has no power."); break;
                    case PowerState.Low:
                        ToastNotificationSystem.ShowWarning("Low power", name + (level < 0.15f ? ": the batteries are almost empty." : ": not enough power for everything running (the lights are dimming)."));
                        break;
                    case PowerState.Generator: ToastNotificationSystem.ShowWarning("On the generator", name + " is running on its standby generator."); break;
                    case PowerState.Normal:
                        if (was == PowerState.Lost || was == PowerState.Generator) ToastNotificationSystem.ShowSuccess("Power restored", name + " is back on its breaker box.");
                        break;
                }
            }
        }

        // ------------------------------------------------------------------ standby generators and their lockout boxes

        private static readonly HashSet<ConstructionSite> s_onGen = new HashSet<ConstructionSite>();
        private static ConstructionSite s_probe;   // a building on its generator, counted back in to see whether its breaker box could carry it again
        private static readonly Dictionary<ConstructionSite, float> s_genStarting = new Dictionary<ConstructionSite, float>();   // when the generator was called for
        public const float GenStartSeconds = 3f;   // a standby generator takes a few seconds to fire up and take the load

        /// <summary>True while the building runs on its generator (its lockout box has switched over).</summary>
        public static bool OnGenerator(ConstructionSite site) { return site != null && s_onGen.Contains(site); }

        private static List<WireNode> LockoutGens(WireNode lockout)
        {
            var gens = new List<WireNode>();
            foreach (WireLink l in Links)
            {
                if (l.Kind != "ac" || !l.Connects(lockout)) continue;
                WireNode o = l.Other(lockout);
                if (o != null && o.Role == WireRole.StandbyGenerator) gens.Add(o);
            }
            return gens;
        }

        /// <summary>
        /// The generator lockout boxes, every grid tick. A building with one runs on its breaker box while that can carry it; when the breaker box has no power,
        /// cannot carry the load, or its batteries are under 15 %, the box switches the building over to the standby generators wired to it (which start by
        /// themselves) and it runs on them alone: its breaker system stops carrying it and recharges. It switches back once that system could carry the building
        /// again with its batteries at half. A generator burns propane from its tanks, more the harder it works (30 % of full idling); with none it does not start.
        /// </summary>
        private static void TickLockouts(List<GridSystem> systems, float dtH)
        {
            var feeding = new HashSet<WireNode>();
            foreach (WireNode box in WireNode.All)
            {
                if (box == null || box.Role != WireRole.Lockout) continue;
                AttachedObject at = box.GetComponent<AttachedObject>();
                ConstructionSite site = at != null ? at.Site : null;
                if (site == null) continue;
                List<WireNode> gens = LockoutGens(box);
                float rated = 0f;
                foreach (WireNode g in gens) if (GenFuelL(g) > 0.01f) { AssetCatalogItem gi = HudBindings.GetCatalogItem(g.ItemId); if (gi != null) rated += gi.max_power_w; }
                bool on = s_onGen.Contains(site);
                // could the breaker box carry the building? (counted back in, without changing anything)
                float ratio = 0f, soc = 1f;
                bool mains = false;
                s_probe = site;
                foreach (GridSystem sys in systems)
                {
                    bool feeds = false;
                    foreach (WireNode n in sys.Nodes)
                    {
                        if (n == null || n.Role != WireRole.AcPanel) continue;
                        AttachedObject pa = n.GetComponent<AttachedObject>();
                        if (pa != null && pa.Site == site && pa.Exterior && IsEnergized(n)) { feeds = true; break; }
                    }
                    if (!feeds) continue;
                    mains = true;
                    ratio = Mathf.Max(ratio, BalanceOf(sys.Nodes, 0f, false).Ratio);
                    if (sys.CapacityWh > 0f) soc = Mathf.Min(soc, sys.StoredWh / sys.CapacityWh);
                }
                s_probe = null;
                bool mainsOk = mains && ratio >= 0.95f && soc >= (on ? 0.5f : 0.15f);
                bool useGen = !mainsOk && rated > 0f;
                // the generator does not take the load at once: it cranks and comes up to speed first (the building stays as it is meanwhile: dark or dim)
                if (useGen && !on)
                {
                    if (!s_genStarting.TryGetValue(site, out float since)) { s_genStarting[site] = Time.unscaledTime; since = Time.unscaledTime; }
                    if (Time.unscaledTime - since < GenStartSeconds)
                    {
                        foreach (WireNode g in gens) if (GenFuelL(g) > 0.01f) { g.GenRunning = false; g.GenW = 0f; g.GenStarting = true; feeding.Add(g); }
                        continue;
                    }
                }
                s_genStarting.Remove(site);
                if (useGen) s_onGen.Add(site); else s_onGen.Remove(site);
                if (box.SwitchOff != useGen) { box.SwitchOff = useGen; Disconnect.Show(box); }   // the handle shows which side feeds the building: up the breaker box, down the generator
                if (!useGen) continue;
                float load = LightEmitter.WantedWatts(site) + HeaterLoadW(site) + WaterPumpLoadW(site) + Net.LoadW(site);
                float give = Mathf.Min(load, rated);
                s_siteRatio[site] = load > 0.01f ? Mathf.Clamp01(give / load) : 1f;
                foreach (WireNode g in gens)
                {
                    AssetCatalogItem gi = HudBindings.GetCatalogItem(g.ItemId);
                    if (gi == null || gi.max_power_w <= 0f || GenFuelL(g) <= 0.01f) continue;
                    float share = rated > 0f ? gi.max_power_w / rated : 0f;
                    g.GenRunning = true;
                    g.GenStarting = false;
                    g.GenW = give * share;
                    feeding.Add(g);
                    if (dtH > 0f && gi.fuel_lpm > 0f) BurnPropane(g, gi.fuel_lpm * 60f * dtH * (0.3f + 0.7f * Mathf.Clamp01(g.GenW / gi.max_power_w)));
                }
            }
            foreach (WireNode g in WireNode.All)
                if (g != null && g.Role == WireRole.StandbyGenerator && !feeding.Contains(g)) { g.GenRunning = false; g.GenStarting = false; g.GenW = 0f; }
        }

        /// <summary>The propane tanks a standby generator is piped to (through other tanks), with propane in them or not.</summary>
        private static List<PlacedObject> GenTanks(WireNode gen)
        {
            var tanks = new List<PlacedObject>();
            var seen = new HashSet<WireNode> { gen };
            var queue = new Queue<WireNode>();
            queue.Enqueue(gen);
            while (queue.Count > 0)
            {
                WireNode n = queue.Dequeue();
                foreach (WireLink l in Links)
                {
                    if (l.Kind != "propane" || !l.Connects(n)) continue;
                    WireNode o = l.Other(n);
                    if (o == null || o.Role != WireRole.PropaneTank || !seen.Add(o)) continue;
                    PlacedObject p = o.GetComponent<PlacedObject>();
                    if (p != null) tanks.Add(p);
                    queue.Enqueue(o);
                }
            }
            return tanks;
        }

        /// <summary>Liters of propane a standby generator can burn: what the tanks it is piped to hold.</summary>
        public static float GenFuelL(WireNode gen)
        {
            float l = 0f;
            foreach (PlacedObject p in GenTanks(gen)) l += LiquidRules.Held(p.ItemId, p.WireUsed);
            return l;
        }

        private static void BurnPropane(WireNode gen, float liters)
        {
            foreach (PlacedObject p in GenTanks(gen))
            {
                if (liters <= 0f) break;
                float held = LiquidRules.Held(p.ItemId, p.WireUsed);
                float take = Mathf.Min(held, liters);
                if (take <= 0f) continue;
                p.WireUsed = LiquidRules.StoredFor(p.ItemId, held - take);
                liters -= take;
            }
        }

        /// <summary>A building has propane while a house connector mounted on it is piped to a propane tank.</summary>
        public static bool HasPropane(ConstructionSite site)
        {
            if (site == null) return false;
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n.Role != WireRole.PropaneConnector) continue;
                AttachedObject ao = n.GetComponent<AttachedObject>();
                if (ao != null && ao.Site == site && PropaneSupplied(n)) return true;
            }
            return false;
        }

        public static void Describe(WireNode n, List<(string, string)> rows)
        {
            if (n == null) return;
            if (Net.IsNet(n.Role)) { Net.Rows(n, rows); return; }   // network gear (docs/INTERNET.md)
            if (IsSewer(n.Role)) { Septic.Rows(n, rows); return; }   // a part of a sewer line (docs/SEPTIC.md)
            if (n.Role == WireRole.FuelPump || n.Role == WireRole.FuelTank) { FuelNozzle.Rows(n, rows); return; }
            if (n.Role == WireRole.Lockout)
            {
                AttachedObject la = n.GetComponent<AttachedObject>();
                bool gen = la != null && OnGenerator(la.Site);
                rows.Add(("Feeding from", gen ? "The generator" : "The breaker box"));
                rows.Add(("Generators", LockoutGens(n).Count.ToString()));
                return;
            }
            if (n.Role == WireRole.Disconnect)
            {
                rows.Add(("Switch", n.SwitchOff ? "Off: the power is cut here" : "On: the power flows through"));
                rows.Add(("Throw it", "Right click"));
            }
            if (n.Role == WireRole.StandbyGenerator)
            {
                AssetCatalogItem gi = HudBindings.GetCatalogItem(n.ItemId);
                float fuel = GenFuelL(n);
                bool box = false;
                foreach (WireLink l in Links) if (l.Kind == "ac" && l.Connects(n) && l.Other(n) != null && l.Other(n).Role == WireRole.Lockout) box = true;
                rows.Add(("Status", n.GenStarting ? "Starting up" : n.GenRunning ? "Running: " + SolarSun.Power(n.GenW) : fuel <= 0.01f ? (GenTanks(n).Count == 0 ? "No propane tank piped to it" : "Out of propane") : !box ? "Not wired to a lockout box" : "Standby (starts when the power runs short)"));
                if (gi != null && gi.max_power_w > 0f) rows.Add(("Rated", SolarSun.Power(gi.max_power_w)));
                rows.Add(("Propane", UnitFormat.Volume(fuel)));
                if (gi != null && gi.fuel_lpm > 0f) rows.Add(("Burns", UnitFormat.Volume(gi.fuel_lpm * 60f) + " an hour at full load"));
                return;
            }
            if (n.Role == WireRole.PropaneConnector)
            {
                bool on = PropaneSupplied(n, out bool piped);
                rows.Add(("Propane", on ? "Piped to a tank: the building has propane" : piped ? "Piped to a tank, but the tank is empty (order propane in Tank You)" : "No tank piped to it"));
                return;
            }
            if (n.Role == WireRole.PropaneFiller)
            {
                bool on = PropaneSupplied(n, out bool piped);
                rows.Add(("Propane", on ? "Piped to a tank: right click it with a portable tank to fill it" : piped ? "Piped to a tank, but the tank is empty (order propane in Tank You)" : "No tank piped to it"));
                return;
            }
            if (n.Role == WireRole.PropaneTank)
            {
                int lines = 0;
                foreach (WireLink l in Links) if (l.Kind == "propane" && l.Connects(n)) lines++;
                rows.Add(("Propane lines", lines.ToString()));
                return;
            }
            AssetCatalogItem it = HudBindings.GetCatalogItem(n.ItemId);
            WireRole role = n.Role;
            if (it != null)
            {
                if (it.max_power_w > 0f) rows.Add(("Rated", SolarSun.Power(it.max_power_w)));
                if (it.max_current_a > 0f) rows.Add(("Current", it.max_current_a.ToString("0.#") + " A"));
                if (it.voltage_v > 0f) rows.Add(("Voltage", it.voltage_v.ToString("0.#") + " V"));
                if (n.CapacityWh > 0f) rows.Add(("Capacity", n.CapacityWh >= 1000f ? (n.CapacityWh / 1000f).ToString("0.##") + " kWh" : Mathf.RoundToInt(n.CapacityWh) + " Wh"));
            }
            switch (role)
            {
                case WireRole.SolarPanel:
                {
                    string fitted = MountedPanel.PanelOn(n.gameObject);
                    if (fitted == null) { rows.Add(("Panel", "None fitted")); break; }
                    AssetCatalogItem pi = HudBindings.GetCatalogItem(fitted);
                    rows.Add(("Panel", SolarSun.Power(pi != null ? pi.max_power_w : 0f)));
                    float f = SolarSun.Factor(out float sun, out float sky);
                    float w = pi != null ? pi.max_power_w * f : 0f;
                    HomesteaderWeather wx = TimeSystem.Instance != null ? TimeSystem.Instance.Snapshot().Weather : HomesteaderWeather.Sunny;
                    rows.Add(("Output", SolarSun.Power(w) + (pi != null && pi.max_power_w > 0f ? " (" + Mathf.RoundToInt(f * 100f) + "%)" : "")));
                    rows.Add(("Sun", sun <= 0f ? "Night" : Mathf.RoundToInt(sun * 100f) + "%"));
                    rows.Add(("Sky", wx + " " + Mathf.RoundToInt(sky * 100f) + "%"));
                    break;
                }
                case WireRole.WallEntry:
                case WireRole.DcBreaker:
                case WireRole.BusBar:
                    rows.Add(("Carrying", SolarSun.Power(SolarSun.InputWatts(n))));
                    break;
                case WireRole.Mppt:
                {
                    float input = SolarSun.InputWatts(n);
                    rows.Add(("Solar input", SolarSun.Power(input)));
                    rows.Add(("Charging", SolarSun.Power(it != null && it.max_power_w > 0f ? Mathf.Min(input, it.max_power_w) : input)));
                    break;
                }
                case WireRole.Battery:
                {
                    if (n.CapacityWh > 0f)
                    {
                        float pct = Mathf.Clamp01(n.ChargeWh / n.CapacityWh);
                        rows.Add(("Charge", Mathf.RoundToInt(pct * 100f) + "% (" + (n.ChargeWh >= 1000f ? (n.ChargeWh / 1000f).ToString("0.##") + " kWh" : Mathf.RoundToInt(n.ChargeWh) + " Wh") + ")"));
                    }
                    else rows.Add(("Charge", "No batteries"));
                    float inW = ChargeInputW(n);
                    rows.Add(("Charging", pct0(it, n) >= 1f ? "Full" : SolarSun.Power(inW)));
                    if (n.CapacityWh > 0f) rows.Add(("Full in", FormatFullIn(FullInHours(n))));
                    break;
                }
                case WireRole.Inverter:
                {
                    WireRole miss = MissingFrom(n);
                    rows.Add(("Solar input", SolarSun.Power(SolarSun.InputWatts(n))));
                    rows.Add(("Output", SolarSun.Power(InverterOutputW(n))));
                    rows.Add(("Chain", miss == WireRole.None ? "Complete" : "Needs " + WireNode.RoleName(miss)));
                    break;
                }
                case WireRole.WaterTank:
                    if (PlumbedInto(n) != null) rows.Add(("Plumbing", "Plumbed into the building's water"));
                    rows.Add(("Water", UnitFormat.Volume(n.WaterL) + " of " + UnitFormat.Volume(n.WaterCapacityL)));
                    rows.Add(("Type", WaterType(n)));
                    WaterRows(n, rows);
                    if (n.HeaterW > 0f) rows.Add(("Temperature", Mathf.RoundToInt(n.TempC) + " C" + (WantsHeat(n) ? ", heating" : "")));
                    break;
                case WireRole.WaterPump:
                    rows.Add(("Pump", n.PumpRunning ? UnitFormat.Volume(n.PumpedLph) + " an hour" : !Powered(n) ? "No power (it needs its building's power)" : "Idle (nothing to pull, or nowhere to put it)"));
                    rows.Add(("Rated", UnitFormat.Volume(n.PumpFlowLph) + " an hour, " + SolarSun.Power(n.PumpDrawW)));
                    if (n.PumpRunning) rows.Add(("Pulling", n.PumpClean ? "Clean water" : "Raw water"));
                    break;
                case WireRole.WaterInlet:
                case WireRole.WaterSpigot:
                {
                    AttachedObject at = n.GetComponent<AttachedObject>();
                    if (at != null && at.Site != null)
                    {
                        // an inlet or a tap holds no water: it passes on what the building's tanks hold (the quality only; the amount is on the tanks)
                        WaterFor(at.Site, out float all, out float clean);
                        rows.Add(("Supplies", all < 0.5f ? "No water" : clean >= all - 0.5f ? "Clean water" : clean < 0.5f ? "Raw water" : "Mixed (" + Mathf.RoundToInt((all - clean) / all * 100f) + "% raw)"));
                    }
                    if (n.Role == WireRole.WaterInlet) WaterRows(n, rows);
                    break;
                }
                case WireRole.WaterFilter:
                {
                    int bit = n.FilterBit;
                    rows.Add(("Stage", bit == 1 ? "Sediment" : bit == 2 ? "Carbon" : bit == 4 ? "UV sterilizing" : "Filter"));
                    WaterRows(n, rows);
                    break;
                }
                case WireRole.WindTurbine:
                {
                    rows.Add(("Output", SolarSun.Power(WindWatts(n))));
                    WeatherEffectsManager wm = WeatherEffectsManager.Instance;
                    if (wm != null) rows.Add(("Wind", wm.WindSpeedMps.ToString("0.#") + " m/s"));
                    break;
                }
                case WireRole.AcPanel:
                {
                    bool wired = false;
                    foreach (WireLink l in Links) if (l.Connects(n)) wired = true;
                    rows.Add(("Power", IsEnergized(n) ? "Live" : wired ? "Chain incomplete" : "No inverter"));
                    if (n.Well != null)
                    {
                        bool running = IsEnergized(n) && WellWantsToRun(n);
                        rows.Add(("Pump", running ? UnitFormat.Volume(PipedFlowLph(n)) + " an hour" + (PipedFlowLph(n) < WellFlowLph(n) - 0.5f ? " (the pipe limits it: the pump gives " + UnitFormat.Volume(WellFlowLph(n)) + ")" : "") : TanksOf(n).Count == 0 ? "No tank piped" : !IsEnergized(n) ? "No power" : "Tanks full"));
                    }
                    rows.Add(("Supply", SolarSun.Power(SupplyW(n))));
                    foreach (GridSystem gs in SystemsCached())
                    {
                        if (!gs.Nodes.Contains(n)) continue;
                        rows.Add(("Load", SolarSun.Power(gs.LoadW)));
                        rows.Add(("Voltage", Mathf.RoundToInt(gs.Voltage) + " V" + (gs.Ratio < 0.98f ? " (low)" : "")));
                        break;
                    }
                    break;
                }
            }
            var names = new List<string>();
            foreach (WireLink l in Links) if (l.Connects(n) && l.Other(n) != null) names.Add(WireNode.RoleName(l.Other(n).Role));
            rows.Add(("Wired to", names.Count > 0 ? string.Join(", ", names) : "Nothing"));
        }

        // ------------------------------------------------------------------ the lines

        private static Material s_dcMat, s_acMat, s_pendMat;

        private static Material MakeMat(Color c)
        {
            // lit, so conduit, wire and clips are dark at night like everything else (an unlit material glows)
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { hideFlags = HideFlags.DontSave };
            m.SetColor("_BaseColor", c);
            m.SetFloat("_Smoothness", 0.25f);
            m.SetFloat("_Metallic", 0f);
            return m;
        }

        public static void Redraw()
        {
            if (s_dcMat == null) { s_dcMat = MakeMat(new Color(0.08f, 0.08f, 0.1f)); s_acMat = MakeMat(new Color(0.88f, 0.86f, 0.78f)); s_pendMat = MakeMat(new Color(0.3f, 0.9f, 0.5f)); }
            for (int i = Links.Count - 1; i >= 0; i--)
            {
                WireLink l = Links[i];
                if (l.A == null || l.B == null) { Remove(l); continue; }   // one end was taken down
                if (l.Auto) continue;   // a joint between panels side by side: nothing to draw
                if (l.Line != null && !l.Line.enabled && l.RouteFinal && Time.unscaledTime < l.NextHideCheck) continue;   // hidden in the walls
                if (WireRouter.NetInWalls(l) || (l.Kind == "net" && l.A.Role != WireRole.NetJack && l.B.Role != WireRole.NetJack)) { if (l.Line != null) l.Line.enabled = false; l.RouteFinal = true; l.NextHideCheck = Time.unscaledTime + 1f; continue; }   // Cat6 inside a building is in the walls: not drawn
                if (l.Line == null)
                {
                    var go = new GameObject("Wire_" + l.Kind);
                    go.transform.SetParent(WireTool.Root, false);
                    l.Line = go.AddComponent<LineRenderer>();
                    l.Line.useWorldSpace = true;
                    l.Line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                    l.Line.widthMultiplier = l.Kind == "net" ? 0.012f : l.Kind == "fuel" ? 0.035f : l.Kind == "sewer" ? 0.09f : l.Kind == "water" ? 0.05f : l.Kind == "propane" ? 0.04f : l.Kind == "ac" ? 0.018f : 0.014f;
                    l.Line.numCapVertices = 2;
                    if (s_gasMat == null) s_gasMat = MakeMat(new Color(0.2f, 0.21f, 0.23f));   // propane pipe: charcoal grey
                    if (s_pipeMat == null) s_pipeMat = MakeMat(new Color(0.92f, 0.92f, 0.89f));   // water pipe: white PVC
                    if (s_fuelMat == null) s_fuelMat = MakeMat(new Color(0.09f, 0.09f, 0.1f));    // fuel line: black coated steel
                    if (s_sewerMat == null) s_sewerMat = MakeMat(new Color(0.05f, 0.05f, 0.055f));   // waste pipe: black ABS
                    if (s_netMat == null) s_netMat = MakeMat(new Color(0.1f, 0.3f, 0.72f));   // Cat6: blue
                    l.Line.sharedMaterial = l.Kind == "net" ? s_netMat : l.Kind == "fuel" ? s_fuelMat : l.Kind == "sewer" ? s_sewerMat : l.Kind == "water" ? s_pipeMat : l.Kind == "propane" ? s_gasMat : l.Kind == "ac" ? s_acMat : s_dcMat;
                }
                if (!l.RouteFinal && Time.unscaledTime >= l.NextRouteTry)
                {
                    // tacked to the walls where both ends are on the same side of a building's walls (the building's model may still be loading: tried again a few times)
                    List<Vector3> route = WireRouter.Route(l.A, l.B, out bool outdoors, out bool buried);
                    l.NextRouteTry = Time.unscaledTime + 1.5f;
                    if (route != null) { l.Route = route; l.Conduit = outdoors; l.Heavy = buried; l.RouteFinal = true; ApplyRoute(l); }
                    else if (!IsWallPair(l) || ++l.RouteTries >= 12) l.RouteFinal = true;   // not a wall run, or the model never came
                }
                if (l.Route == null)
                {
                    Vector3 pa = l.A.PortToward(l.B.BasePort), pb = l.B.PortToward(l.A.BasePort);
                    if (l.Drawn && pa == l.DrawnA && pb == l.DrawnB) continue;   // neither end moved: the line is already right
                    l.Drawn = true; l.DrawnA = pa; l.DrawnB = pb;
                    if (l.Kind == "water" || l.Kind == "sewer") { l.Line.positionCount = 2; l.Line.SetPosition(0, pa); l.Line.SetPosition(1, pb); }   // a pipe does not sag
                    else Sag(l.Line, pa, pb);   // a plain hanging wire (until, or unless, it is tacked)
                }
            }
        }

        private static bool IsWallPair(WireLink l)
        {
            AttachedObject x = l.A != null ? l.A.GetComponent<AttachedObject>() : null, y = l.B != null ? l.B.GetComponent<AttachedObject>() : null;
            if (l.A != null && l.B != null && (l.A.Role == WireRole.SolarPanel) != (l.B.Role == WireRole.SolarPanel)) return (x != null || y != null);   // a panel run to a wall device
            if (l.A != null && l.B != null && (l.A.Role == WireRole.WindTurbine || l.B.Role == WireRole.WindTurbine || l.A.Role == WireRole.StandbyGenerator || l.B.Role == WireRole.StandbyGenerator)) return true;   // a turbine run to a panel, a generator to its lockout box
            if (l.Kind == "ac" || l.Kind == "propane" || l.Kind == "fuel" || l.Kind == "net") return true;   // a long AC run, and a propane or fuel line, is buried (tried again while the models load)
            return x != null && y != null && x.Surface == "wall" && y.Surface == "wall" && x.Site != null && x.Site == y.Site;
        }

        private static Mesh s_clipMesh;
        private static Material s_netMat, s_clipMat, s_steelMat, s_pvcMat, s_strapMat, s_gasMat, s_pipeMat, s_sewerMat, s_fuelMat;

        /// <summary>Lays the line along the route with square corners and tacks it with a small clip every half metre and at each corner.</summary>
        private static void ApplyRoute(WireLink l)
        {
            List<Vector3> r = l.Route;
            l.Line.positionCount = r.Count;
            for (int i = 0; i < r.Count; i++) l.Line.SetPosition(i, r[i]);
            l.Line.numCornerVertices = 1;     // square corners
            // made up front: a buried water line is a conduit link too, and its clips used the PVC material before any DC conduit had made it (null: drawn magenta)
            if (s_steelMat == null) { s_steelMat = MakeMat(new Color(0.62f, 0.65f, 0.67f)); s_pvcMat = MakeMat(new Color(0.84f, 0.77f, 0.60f)); s_strapMat = MakeMat(new Color(0.45f, 0.47f, 0.49f)); }
            if (l.Kind == "sewer")   // a sewer line is black waste pipe wherever it runs
            {
                if (s_sewerMat == null) s_sewerMat = MakeMat(new Color(0.05f, 0.05f, 0.055f));
                l.Line.widthMultiplier = 0.09f;
                l.Line.sharedMaterial = s_sewerMat;
            }
            else if (l.Kind == "water")   // a water line is white PVC pipe wherever it runs, along the walls or underground (no conduit round it)
            {
                if (s_pipeMat == null) s_pipeMat = MakeMat(new Color(0.92f, 0.92f, 0.89f));
                l.Line.widthMultiplier = 0.05f;
                l.Line.sharedMaterial = s_pipeMat;
            }
            else if (l.Conduit)
            {
                // outside: the wire runs in conduit, galvanized steel for AC, beige PVC for DC, held by straps
                bool ac = l.Kind == "ac";
                bool windRun = l.Heavy || l.A.Role == WireRole.WindTurbine || l.B.Role == WireRole.WindTurbine || l.A.Role == WireRole.StandbyGenerator || l.B.Role == WireRole.StandbyGenerator;
                l.Line.widthMultiplier = windRun ? 0.07f : ac ? 0.034f : 0.03f;   // the riser from a buried cable is the larger conduit
                l.Line.sharedMaterial = ac ? s_steelMat : s_pvcMat;
                if (l.Kind == "propane") { l.Line.widthMultiplier = 0.045f; l.Line.sharedMaterial = s_gasMat; }
                if (l.Kind == "fuel") { if (s_fuelMat == null) s_fuelMat = MakeMat(new Color(0.09f, 0.09f, 0.1f)); l.Line.widthMultiplier = 0.04f; l.Line.sharedMaterial = s_fuelMat; }
            }
            if (s_clipMesh == null)
            {
                GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
                s_clipMesh = cube.GetComponent<MeshFilter>().sharedMesh;
                Object.Destroy(cube);
                s_clipMat = MakeMat(new Color(0.75f, 0.75f, 0.72f));
            }
            // Every clip of this run is one mesh with one renderer (the clips used to be a GameObject and a renderer each: hundreds of draws for a few wires).
            var clips = new List<CombineInstance>();
            for (int i = 0; i < r.Count - 1; i++)
            {
                Vector3 a = r[i], b = r[i + 1];
                float len = Vector3.Distance(a, b);
                if (len < 0.15f) continue;                       // the stub out of a device is not clipped
                if (Mathf.Abs(b.y - a.y) > len * 0.7f) continue;   // a riser (a run straight up or down, such as where a pipe or conduit goes into the ground) gets no plates: the clip turns into a square collar there
                int n = Mathf.Max(1, Mathf.FloorToInt(len / (l.Conduit ? 0.8f : 0.5f)));
                for (int k = 0; k <= n; k++)
                {
                    if (i == 0 && k == 0) continue;
                    Vector3 p = Vector3.Lerp(a, b, k / (float)n);
                    Vector3 scale = l.Conduit ? (l.Heavy || l.A.Role == WireRole.WindTurbine || l.B.Role == WireRole.WindTurbine ? new Vector3(0.1f, 0.1f, 0.016f) : new Vector3(0.05f, 0.05f, 0.014f)) : new Vector3(0.026f, 0.026f, 0.012f);
                    clips.Add(new CombineInstance { mesh = s_clipMesh, transform = Matrix4x4.TRS(p, Quaternion.LookRotation((b - a).normalized), scale) });
                }
            }
            if (clips.Count == 0) return;
            var clipObj = new GameObject("WireClips");
            clipObj.transform.SetParent(l.Line.transform, false);
            clipObj.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);   // the clip positions are world positions
            var merged = new Mesh { name = "WireClips" };
            if (clips.Count * s_clipMesh.vertexCount > 65000) merged.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            merged.CombineMeshes(clips.ToArray(), true, true);
            clipObj.AddComponent<MeshFilter>().sharedMesh = merged;
            clipObj.AddComponent<WireClipMesh>().Mesh = merged;
            var mr = clipObj.AddComponent<MeshRenderer>();
            mr.sharedMaterial = l.Kind == "water" || l.Kind == "sewer" || l.Kind == "propane" || l.Kind == "fuel" || l.Kind == "ac" ? (l.Conduit ? s_strapMat : s_clipMat) : l.Conduit ? s_pvcMat : s_clipMat;   // a pipe is held by grey metal straps
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        }

        public static void Sag(LineRenderer line, Vector3 a, Vector3 b)
        {
            const int n = 10;
            line.positionCount = n;
            float sag = Mathf.Clamp(Vector3.Distance(a, b) * 0.08f, 0.03f, 0.5f);
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)(n - 1);
                Vector3 p = Vector3.Lerp(a, b, t);
                p.y -= Mathf.Sin(t * Mathf.PI) * sag;
                line.SetPosition(i, p);
            }
        }

        public static Material PendingMaterial { get { if (s_pendMat == null) Redraw(); return s_pendMat; } }

        // ------------------------------------------------------------------ saving

        public static List<GameSave.SavedWire> Capture(Dictionary<GameObject, int> placed, Dictionary<GameObject, int> attached)
        {
            var list = new List<GameSave.SavedWire>();
            foreach (WireLink l in Links)
            {
                if (l.A == null || l.B == null) continue;
                if (l.Auto) continue;   // solar panels side by side join again by themselves
                if (!Ref(l.A, placed, attached, out int ka, out int ia) || !Ref(l.B, placed, attached, out int kb, out int ib)) continue;
                list.Add(new GameSave.SavedWire { aKind = ka, aIndex = ia, bKind = kb, bIndex = ib, kind = l.Kind, length = l.Length, wireItem = l.WireItem });
            }
            return list;
        }

        private static bool Ref(WireNode n, Dictionary<GameObject, int> placed, Dictionary<GameObject, int> attached, out int kind, out int index)
        {
            if (placed.TryGetValue(n.gameObject, out index)) { kind = 0; return true; }
            if (attached.TryGetValue(n.gameObject, out index)) { kind = 1; return true; }
            ConstructionSite cs = n.GetComponent<ConstructionSite>();
            if (cs != null && (index = ConstructionSite.All.IndexOf(cs)) >= 0) { kind = 2; return true; }   // a wind turbine: its work site
            kind = 0;
            index = -1;
            return false;
        }

        public static void Restore(List<GameSave.SavedWire> saved, Dictionary<int, PlacedObject> placed, Dictionary<int, AttachedObject> attached)
        {
            Clear();
            if (saved == null) return;
            foreach (GameSave.SavedWire w in saved)
            {
                WireNode a = Find(w.aKind, w.aIndex, placed, attached), b = Find(w.bKind, w.bIndex, placed, attached);
                if (a == null || b == null) continue;
                Links.Add(new WireLink { A = a, B = b, Kind = w.kind, Length = w.length, WireItem = w.wireItem });
            }
        }

        private static WireNode Find(int kind, int index, Dictionary<int, PlacedObject> placed, Dictionary<int, AttachedObject> attached)
        {
            if (kind == 2) return index >= 0 && index < ConstructionSite.All.Count && ConstructionSite.All[index] != null ? ConstructionSite.All[index].GetComponent<WireNode>() : null;
            if (kind == 0) return placed.TryGetValue(index, out PlacedObject p) && p != null ? p.GetComponent<WireNode>() : null;
            return attached.TryGetValue(index, out AttachedObject a) && a != null ? a.GetComponent<WireNode>() : null;
        }
    }

    /// <summary>
    /// The wire cutters at work. With them in the active slot a right click on a device picks it, a right click on a second device wires the two (or cuts the wire between them), a click on
    /// anything else lets go. While one is picked a line follows the cursor. Draws every wire. Bootstraps itself.
    /// </summary>
    public sealed class WireTool : MonoBehaviour
    {
        private static WireTool s_instance;
        private static WireNode s_first;
        private LineRenderer _pending;

        public static Transform Root { get { return s_instance != null ? s_instance.transform : null; } }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            s_first = null;
            if (FindAnyObjectByType<WireTool>() != null) return;
            var go = new GameObject("WireTool");
            DontDestroyOnLoad(go);
            s_instance = go.AddComponent<WireTool>();
        }

        private void Awake() { s_instance = this; }

        public static void Cancel() { s_first = null; }

        public const string PipeWrenchId = "tool_wrench_pipe";   // propane lines are joined with the pipe wrench, wires with the cutters

        public static bool CuttersHeld() { return ConstructionSite.HeldItem() == WireNetwork.CuttersId; }

        /// <summary>A tool that joins devices is in hand: the cutters (wire) or the pipe wrench (propane pipe).</summary>
        public static bool JoinToolHeld() { return CuttersHeld() || WrenchHeld(); }

        public static bool WrenchHeld() { return ConstructionSite.HeldItem() == PipeWrenchId; }

        /// <summary>The device under the cursor (mounted things are triggers, so the ray asks for them); null when the first thing under the cursor is not a device.</summary>
        public static WireNode NodeUnderCursor(Camera cam, Vector2 pointer, WireNode skip = null)
        {
            if (cam == null || WireNode.All.Count == 0) return null;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(pointer), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            float solid = -1f;   // where the first solid thing (a wall) is along the ray
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                // a device mounted ON a wall sits in the wall's surface: a jack on a log wall is a little behind the nearest bump of a round log, so a device within a hand's width
                // behind the first solid thing still counts (the ray used to stop at that log and the jack could not be picked); anything farther back is behind the wall
                if (solid >= 0f && h.distance - solid > 0.35f) break;
                WireNode n = WireNode.Of(h.collider);
                if (n != null) { if (n == skip) continue; return n; }          // a device (the one already picked is looked past: the one behind or beside it is meant)
                if (h.collider.isTrigger) continue;                              // the click box of something that is not wired (a light): look past it
                if (solid < 0f) solid = h.distance;                              // a solid thing (a wall) is in the way: only what is on its surface can still be picked
            }
            return NodeNear(cam, pointer, skip);
        }

        /// <summary>
        /// When the ray finds no device (a small one behind a bigger click box, a thin one, one a pixel off): the device whose connection point is closest to the cursor on the screen,
        /// within about 45 pixels and 12 m of the camera's target. Makes picking forgiving.
        /// </summary>
        private static bool PanelUnderPointer(Camera cam, WireNode n, Vector2 pointer)
        {
            if (n.GetComponent<MountedPanel>() == null) return false;
            Transform panel = n.transform.Find("FittedPanel");
            if (panel == null) return false;
            bool any = false;
            Rect rect = default;
            foreach (Renderer r in panel.GetComponentsInChildren<Renderer>())
            {
                Bounds b = r.bounds;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 sp = cam.WorldToScreenPoint(new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z));
                    if (sp.z <= 0f) continue;
                    if (!any) { rect = new Rect(sp.x, sp.y, 0f, 0f); any = true; }
                    else rect = Rect.MinMaxRect(Mathf.Min(rect.xMin, sp.x), Mathf.Min(rect.yMin, sp.y), Mathf.Max(rect.xMax, sp.x), Mathf.Max(rect.yMax, sp.y));
                }
            }
            if (!any) return false;
            rect = Rect.MinMaxRect(rect.xMin - 8f, rect.yMin - 8f, rect.xMax + 8f, rect.yMax + 8f);
            return rect.Contains(pointer);
        }

        private static WireNode NodeNear(Camera cam, Vector2 pointer, WireNode skip)
        {
            WireNode best = null;
            float bestD = 45f;
            foreach (WireNode n in WireNode.All)
            {
                if (n == null || n == skip) continue;
                if (PanelUnderPointer(cam, n, pointer)) return n;   // a fitted solar panel: anywhere over it counts, not just its frame
                Vector3 sp = cam.WorldToScreenPoint(n.BasePort);
                if (sp.z <= 0f) continue;
                float d = Vector2.Distance(new Vector2(sp.x, sp.y), pointer);
                if (d < bestD) { bestD = d; best = n; }
            }
            return best;
        }

        /// <summary>A right click with the cutters in hand. True when the click was for the wiring (so nothing else reacts to it).</summary>
        public static bool TryRightClick(Camera cam, Vector2 pointer, Transform player)
        {
            if (!JoinToolHeld()) { s_first = null; return false; }
            WireNode n = NodeUnderCursor(cam, pointer, s_first);
            Dbg.Log("[Wire] right click with the cutters: " + (n != null ? n.ItemId + " (" + n.Role + ")" : "no device") + "; picked first: " + (s_first != null ? s_first.ItemId : "none"));
            if (n == null && s_first != null && NodeUnderCursor(cam, pointer) == s_first)
            {
                s_first = null;                      // a click on the picked device itself lets go of it
                return true;
            }
            if (n == null)
            {
                if (s_first == null) return false;      // nothing picked and nothing aimed at: the click goes on as usual
                s_first = null;                          // let go
                return true;
            }
            // Shift + right click: the cutters cut EVERY wire off this device
            Keyboard kb = Keyboard.current;
            if (kb != null && kb.shiftKey.isPressed)
            {
                s_first = null;
                for (int i = WireNetwork.Links.Count - 1; i >= 0; i--)
                    if (WireNetwork.Links[i].Connects(n) && !WireNetwork.Links[i].Auto) WireNetwork.Remove(WireNetwork.Links[i]);
                return true;
            }
            if (s_first == null || s_first == n) { s_first = s_first == n ? null : n; return true; }
            WireNode first = s_first;
            s_first = null;
            // the right tool for the job: the pipe wrench joins propane pipe, the cutters wire
            bool gas = WireNetwork.IsPropane(first.Role) || WireNetwork.IsPropane(n.Role) || WireNetwork.KindFor(first.Role, n.Role) == "water"
                       || WireNetwork.IsSewer(first.Role) || WireNetwork.IsSewer(n.Role)
                       || WireNetwork.KindFor(first.Role, n.Role) == "fuel";   // propane, water, sewer and fuel lines are pipe
            if (gas != WrenchHeld())
            {
                ToastNotificationSystem.ShowInfo(gas ? "Can't pipe that" : "Can't wire that", gas ? "A propane, water, sewer or fuel line is joined with a pipe wrench in hand." : "Wires are joined with the wire cutters in hand.");
                return true;
            }
            bool done = WireNetwork.Connect(first, n, player, out string reason);
            Dbg.Log("[Wire] " + first.ItemId + " + " + n.ItemId + ": " + (done ? "done" : "not done: " + reason));
            if (!done && reason != null)
                ToastNotificationSystem.ShowInfo(gas ? "Can't pipe that" : "Can't wire that", reason);
            return true;
        }

        private void Update()
        {
            WireNetwork.Redraw();
            WireNetwork.TickSolarGroups();
            WireNetwork.TickCharge();
            if (s_first != null && (!JoinToolHeld() || !s_first.isActiveAndEnabled)) s_first = null;
            if (s_first == null)
            {
                if (_pending != null) _pending.enabled = false;
                return;
            }
            Camera cam = HoverTarget.GameCamera();
            Mouse mouse = Mouse.current;
            if (cam == null || mouse == null) return;
            Ray ray = cam.ScreenPointToRay(mouse.position.ReadValue());
            var plane = new Plane(Vector3.up, s_first.BasePort);
            if (!plane.Raycast(ray, out float enter)) return;
            Vector3 cursor = ray.GetPoint(enter);
            Vector3 from = s_first.PortToward(cursor);   // the connection point the wire would leave from
            if (_pending == null)
            {
                var go = new GameObject("WirePending");
                go.transform.SetParent(transform, false);
                _pending = go.AddComponent<LineRenderer>();
                _pending.useWorldSpace = true;
                _pending.widthMultiplier = 0.012f;
                _pending.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                _pending.sharedMaterial = WireNetwork.PendingMaterial;
            }
            _pending.enabled = true;
            WireNetwork.Sag(_pending, from, cursor);
        }
    }
}
