using System.Collections;
using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Homesteader.Growth
{
    /// <summary>
    /// The stationary sawmill (docs/SAWMILL.md). A placed item whose manifest says properties.sawmill. A left click on it with an UNCUT LOG in hand lays the log on the track
    /// (one at a time; Shift + right click takes it back); a right click on it asks what lumber to cut. The saw carriage then makes three passes along the log (it is brought
    /// back after each), the log is gone, and the lumber is stacked beside the sawmill: on a stack of the same lumber while it has room, else in the next place along. The
    /// model has three parts found by name: "SawCarriage" (it travels along its x), "SawBlade" (spins about its own z) and "Frame".
    /// </summary>
    public sealed class Sawmill : MonoBehaviour
    {
        public const float Reach = 3.5f;          // metres from the machine
        public const float PassSeconds = 2.8f, ReturnSeconds = 1.1f;
        public const int Passes = 3;
        public const float LogBaseY = 0.40f;      // the height of the log's underside above the machine's foot (the cradles)
        public const float FirstRowZ = 1.3f;      // the first row of lumber, from the machine's middle, on its front
        public const float RowPitch = 0.26f;      // the next beside it
        public const int MaxRows = 12;
        public const string Fuel = "liquid_gasoline";
        public const float FuelPerCutL = 0.5f;    // liters of gasoline a cut (three passes) burns
        public const float SpanX = 2.6f;          // lumber lies within this of the middle of the track

        public sealed class LumberType
        {
            public string Id;
            public int PerLongLog;     // pieces a long (4 m) uncut log gives
            public float MinLogM;      // the shortest log that gives a piece (its length)
            public KeyValuePair<string, int>[] Bundles;   // the strapped bundles (item, pieces in it) the pieces are made up into, the biggest first
        }

        private static KeyValuePair<string, int> B(string id, int pieces) { return new KeyValuePair<string, int>(id, pieces); }

        /// <summary>What a log can be cut into: a piece is no longer than the log, and a log gives pieces in proportion to its volume.</summary>
        public static readonly LumberType[] Types =
        {
            new LumberType { Id = "lumber_stud_2x4", PerLongLog = 20, MinLogM = 2.4f, Bundles = new[] { B("lumber_bundle_2x4_large", 40), B("lumber_bundle_2x4_small", 20) } },
            new LumberType { Id = "lumber_board_2x6", PerLongLog = 14, MinLogM = 2.4f, Bundles = new[] { B("lumber_bundle_2x6_large", 25), B("lumber_bundle_2x6_small", 10) } },
            new LumberType { Id = "lumber_post_4x4", PerLongLog = 10, MinLogM = 2.4f, Bundles = new[] { B("lumber_post_4x4_stack_20", 20), B("lumber_post_4x4_stack_10", 10) } },
            new LumberType { Id = "lumber_joist_2x8", PerLongLog = 10, MinLogM = 3.6f, Bundles = new[] { B("lumber_joist_2x8_stack_20", 20), B("lumber_joist_2x8_stack_10", 10) } },
            new LumberType { Id = "building_lumber_joist_2x10", PerLongLog = 8, MinLogM = 4.0f, Bundles = new[] { B("lumber_bundle_2x10_large", 15), B("lumber_bundle_2x10_small", 6) } },
        };

        private PlacedObject _placed;
        private Transform _carriage, _blade;
        private Vector3 _home;
        private GameObject _logView;
        private bool _busy, _spinning, _menu;

        public bool Busy { get { return _busy; } }
        public string LogId { get { return _placed != null ? _placed.SawLog : null; } }

        /// <summary>Liters of gasoline in its tank (the sawmill is a liquid container for gasoline: the number is kept in the placed object like any tank's).</summary>
        public float FuelL { get { return _placed != null ? LiquidRules.Held(_placed.ItemId, _placed.WireUsed) : 0f; } }
        public float TankL { get { return _placed != null ? LiquidRules.Capacity(_placed.ItemId) : 0f; } }

        private void SetFuel(float liters) { _placed.WireUsed = LiquidRules.StoredFor(_placed.ItemId, liters); }

        // ------------------------------------------------------------------ knowing one

        public static bool IsSawmill(string itemId)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            return it != null && it.sawmill;
        }

        public static Sawmill AttachIfSawmill(PlacedObject placed)
        {
            if (placed == null || !IsSawmill(placed.ItemId)) return null;
            var s = placed.gameObject.AddComponent<Sawmill>();
            s._placed = placed;
            s.StartCoroutine(s.FindParts());
            return s;
        }

        /// <summary>The model loads lazily: the carriage and the blade are found when it has.</summary>
        private IEnumerator FindParts()
        {
            float until = Time.realtimeSinceStartup + 40f;
            while (_carriage == null && Time.realtimeSinceStartup < until)
            {
                foreach (Transform t in GetComponentsInChildren<Transform>(true))
                {
                    // glTFast splits a part with several materials into child nodes carrying the same name: the part itself is the OUTERMOST one (moving a child alone moved nothing:
                    // its home was its own zero, and the carriage never left its end)
                    bool childOfSame = t.parent != null && t.parent.name.StartsWith(t.name.Length >= 9 && t.name.StartsWith("SawCarriage") ? "SawCarriage" : "SawBlade");
                    if (t.name.StartsWith("SawCarriage") && !childOfSame) _carriage = t;
                    else if (t.name.StartsWith("SawBlade") && !childOfSame) _blade = t;
                }
                if (_carriage == null) yield return new WaitForSeconds(0.25f);
            }
            if (_carriage == null) yield break;
            _home = _carriage.localPosition;
            Dbg.Log("[Sawmill] parts: carriage '" + _carriage.name + "' at local " + _home.ToString("0.00") + " (parent '" + (_carriage.parent != null ? _carriage.parent.name : "none") + "'), blade '" + (_blade != null ? _blade.name : "none") + "'");
            if (!string.IsNullOrEmpty(LogId)) StartCoroutine(ShowLog(LogId));
        }

        public static bool IsUncutLog(string itemId) { return !string.IsNullOrEmpty(itemId) && itemId.StartsWith("mat_log_") && itemId.Contains("_uncut_"); }

        /// <summary>The length of an uncut log (long 4 m, medium 2.4 m, small 1.3 m).</summary>
        public static float LogLengthM(string logId)
        {
            return logId == null ? 0f : logId.EndsWith("_long") ? 4.0f : logId.EndsWith("_medium") ? 2.4f : logId.EndsWith("_small") ? 1.3f : 0f;
        }

        /// <summary>How many pieces of a lumber type a log gives (0 when the log is too short for it).</summary>
        public static int Yield(string logId, LumberType type)
        {
            float len = LogLengthM(logId);
            if (len + 0.01f < type.MinLogM) return 0;
            float volume = len / 4f * Mathf.Pow(len >= 4f ? 1f : len >= 2.4f ? 0.8f : 0.63f, 2f);   // length times the girth squared, against a long log
            return Mathf.Max(1, Mathf.FloorToInt(type.PerLongLog * volume));
        }

        // ------------------------------------------------------------------ the clicks

        private static Sawmill UnderCursor(Camera cam, Vector2 pointer)
        {
            if (cam == null) return null;
            PlacedObject p = PlacementController.PlacedUnderCursor();
            return p != null ? p.GetComponent<Sawmill>() : null;
        }

        private bool InReach()
        {
            PedController ped = PedController.Current;
            if (ped == null || _placed == null) return true;
            Vector3 np = _placed.NearestPointTo(ped.transform.position);
            return new Vector2(np.x - ped.transform.position.x, np.z - ped.transform.position.z).magnitude <= Reach;
        }

        /// <summary>A left click with an uncut log in the active slot over a sawmill: lays it on the track. True when the click was for a sawmill.</summary>
        public static bool TryLoadHeld(Camera cam, Vector2 pointer)
        {
            HudState hud = HudState.Active;
            if (hud == null || hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return false;
            string held = hud.Toolbar[hud.SelectedSlot].IconId;
            if (!IsUncutLog(held) || hud.Toolbar[hud.SelectedSlot].Count <= 0) return false;
            Sawmill s = UnderCursor(cam, pointer);
            if (s == null) return false;
            string name = HudBindings.GetItemName(s._placed.ItemId);
            if (!s.InReach()) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to the sawmill."); return true; }
            if (s._busy) { ToastNotificationSystem.ShowInfo(name, "It is cutting."); return true; }
            if (!string.IsNullOrEmpty(s.LogId)) { ToastNotificationSystem.ShowInfo(name, "There is a log on the track already: right click the sawmill to cut it."); return true; }
            if (!hud.ConsumeFromSelectedSlot(1)) return true;
            s._placed.SawLog = held;
            s.StartCoroutine(s.ShowLog(held));
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        /// <summary>
        /// A right click on a sawmill: asks what lumber to cut from the log on the track. Shift + right click takes the log off again, and with nothing on the track lets the click
        /// go on (the sawmill is picked up like any placed thing). True when the click was for the sawmill.
        /// </summary>
        public static bool TryRightClick(Camera cam, Vector2 pointer)
        {
            Sawmill s = UnderCursor(cam, pointer);
            if (s == null) return false;
            string name = HudBindings.GetItemName(s._placed.ItemId);
            if (s.TryPourHeld(name)) return true;   // a can of gasoline in hand: it is poured into the tank
            bool shift = Keyboard.current != null && Keyboard.current.shiftKey.isPressed;
            if (shift)
            {
                if (string.IsNullOrEmpty(s.LogId)) return false;   // nothing on it: Shift + right click picks the machine up as before
                if (s._busy) { ToastNotificationSystem.ShowInfo(name, "It is cutting."); return true; }
                if (!s.InReach()) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to the sawmill."); return true; }
                HudState hud = HudState.Active;
                string id = s._placed.SawLog;
                if (hud == null || hud.AddItemToToolbar(id, 1, HudBindings.GetMaxStack(id)) < 1) { ToastNotificationSystem.ShowWarning("Toolbar full", "No room in the toolbar for the log."); return true; }
                s.ClearLog();
                HudBindings.Instance?.RefreshToolbar();
                return true;
            }
            if (!s.InReach()) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to the sawmill."); return true; }
            if (s._busy) { ToastNotificationSystem.ShowInfo(name, "It is cutting."); return true; }
            if (s.FuelL < FuelPerCutL - 0.001f) { ToastNotificationSystem.ShowInfo(name, "It is out of gasoline: pour a can into it (right click the sawmill with the can in hand)."); return true; }
            if (string.IsNullOrEmpty(s.LogId)) { ToastNotificationSystem.ShowInfo(name, "Put an uncut log on the track first: left click the sawmill with one in hand."); return true; }
            s.OpenMenu();
            return true;
        }

        /// <summary>
        /// A right click with a container holding gasoline in the active slot: pours what fits into the sawmill's tank. True when the click was for that (a full tank or a can that
        /// does not hold gasoline is said, not ignored).
        /// </summary>
        private bool TryPourHeld(string name)
        {
            HudState hud = HudState.Active;
            if (hud == null || hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return false;
            ToolbarSlotData slot = hud.Toolbar[hud.SelectedSlot];
            string held = slot.IconId;
            if (string.IsNullOrEmpty(held) || slot.Count <= 0 || !LiquidRules.IsLiquidContainer(held)) return false;
            if (LiquidRules.LiquidIn(held, slot.LiquidId) != Fuel) return false;   // only a container of gasoline: anything else goes on to the menu
            if (!InReach()) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to the sawmill."); return true; }
            if (slot.Count != 1) { ToastNotificationSystem.ShowInfo("One at a time", "Hold a single can to pour it."); return true; }
            float have = LiquidRules.Held(held, slot.WireUsed);
            if (have <= 0.01f) { ToastNotificationSystem.ShowInfo("Empty", "That can is empty."); return true; }
            float room = TankL - FuelL;
            if (room <= 0.01f) { ToastNotificationSystem.ShowInfo(name, "The tank is full."); return true; }
            float pour = Mathf.Min(have, room);
            SetFuel(FuelL + pour);
            slot.WireUsed = LiquidRules.StoredFor(held, have - pour);
            hud.Toolbar[hud.SelectedSlot] = slot;
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        // ------------------------------------------------------------------ the menu

        private void OpenMenu()
        {
            string log = LogId;
            var options = new List<HudBindings.ChoiceOption>();
            var shown = new List<LumberType>();
            foreach (LumberType t in Types)
            {
                int n = Yield(log, t);
                if (n <= 0) continue;
                options.Add(new HudBindings.ChoiceOption(HudBindings.GetItemName(t.Id) + "  x" + n + Summary(t, n), t.Id, "Cut", FuelL >= FuelPerCutL - 0.001f, "Out of gasoline: right click the sawmill with a can of gasoline in hand."));
                shown.Add(t);
            }
            if (shown.Count == 0) { ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(_placed.ItemId), "That log is too short to saw into lumber."); return; }
            HudBindings hud = HudBindings.Instance;
            if (hud == null) return;
            _menu = true;
            string gauge = "Gasoline  " + UnitFormat.Volume(FuelL) + " / " + UnitFormat.Volume(TankL);
            string hint = "On the track: " + HudBindings.GetItemName(log) + ". A cut burns " + UnitFormat.Volume(FuelPerCutL) + " of gasoline.";
            hud.ShowChoiceMenu("Sawmill", gauge, TankL > 0f ? FuelL / TankL : 0f, hint, "CUT THE LOG INTO", options, i => { _menu = false; Begin(shown[i]); });
        }

        private float _nextSweep;

        /// <summary>Every few seconds: stacks of loose lumber at the machine that make a bundle are bundled (no cut needed).</summary>
        private IEnumerator Sweep()
        {
            _busy = true;
            foreach (LumberType t in Types)
            {
                List<PlacedObject> loose = LoosePieces(t.Id);
                if (loose.Count == 0 || BundlesFor(t, loose.Count, out _).Count == 0) continue;
                yield return Deposit(t, 0);
            }
            _busy = false;
        }

        private void Update()
        {
            if (!_busy && _placed != null && Time.time >= _nextSweep)
            {
                _nextSweep = Time.time + 3f;
                StartCoroutine(Sweep());
            }
            if (_spinning && _blade != null) _blade.Rotate(0f, 0f, 900f * Time.deltaTime, Space.Self);
            if (_menu)
            {
                HudBindings hud = HudBindings.Instance;
                bool escape = Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame;
                if (hud == null || !hud.ChoiceMenuOpen) _menu = false;
                else if (escape || !InReach()) { hud.CloseChoiceMenu(); _menu = false; }
            }
        }

        // ------------------------------------------------------------------ the log on the track

        private void ClearLog()
        {
            if (_placed != null) _placed.SawLog = null;
            if (_logView != null) Destroy(_logView);
            _logView = null;
        }

        /// <summary>Shows the log lying on the cradles (its model, no colliders), once the machine's own model and the log's are there.</summary>
        private IEnumerator ShowLog(string logId)
        {
            while (_carriage == null) yield return null;
            if (!ItemRegistry.TryGet(logId, out ItemRegistry.ItemInfo info) || info.Prefab == null) yield break;
            GlbTemplate glb = info.Prefab.GetComponent<GlbTemplate>();
            if (glb != null)
            {
                glb.EnsureLoading();
                float until = Time.realtimeSinceStartup + 30f;
                while (!glb.Ready && !glb.Failed && Time.realtimeSinceStartup < until) yield return null;
                if (!glb.Ready) yield break;
            }
            if (_placed == null || _placed.SawLog != logId) yield break;   // taken off again meanwhile
            if (_logView != null) Destroy(_logView);
            _logView = Instantiate(info.Prefab, transform);
            _logView.name = "SawLog";
            _logView.SetActive(true);
            foreach (Collider c in _logView.GetComponentsInChildren<Collider>(true)) Destroy(c);
            foreach (MonoBehaviour m in _logView.GetComponentsInChildren<MonoBehaviour>(true)) if (!(m is GlbTemplate)) Destroy(m);
            _logView.transform.localRotation = Quaternion.identity;
            _logView.transform.localScale = Vector3.one;
            _logView.transform.localPosition = Vector3.zero;
            // centred on the track, its underside on the cradles
            Bounds b = default;
            bool any = false;
            foreach (Renderer r in _logView.GetComponentsInChildren<Renderer>(true)) { if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds); }
            if (any)
            {
                Vector3 centre = transform.InverseTransformPoint(b.center), min = transform.InverseTransformPoint(new Vector3(b.center.x, b.min.y, b.center.z));
                _logView.transform.localPosition = new Vector3(-centre.x, LogBaseY - min.y, -centre.z);
            }
        }

        // ------------------------------------------------------------------ cutting

        public const float BackZ = -1.25f;        // where the player pushes from: the BACK side, opposite the front where the lumber comes out (the machine's local z)

        private void Begin(LumberType type)
        {
            if (_busy || string.IsNullOrEmpty(LogId) || _carriage == null) return;
            int count = Yield(LogId, type);
            if (count <= 0) return;
            if (FuelL < FuelPerCutL - 0.001f) { ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(_placed.ItemId), "It is out of gasoline."); return; }
            if (!Fits(type, count))
            {
                ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(_placed.ItemId), "There is no room for the lumber beside the sawmill: take some away first.");
                return;
            }
            SetFuel(FuelL - FuelPerCutL);   // the cut burns its fuel when it starts
            StartCoroutine(Cut(type, count));
        }

        private float LocalX(Vector3 world) { return transform.InverseTransformPoint(world).x; }

        /// <summary>The spot on the back side, level with a place along the track: where the player stands to push.</summary>
        private Vector3 PushSpot(float localX) { return transform.TransformPoint(new Vector3(localX, 0f, BackZ)); }

        /// <summary>The player walks round to the back of the machine (by the end of the track, never through it) and to the carriage.</summary>
        private IEnumerator WalkToCarriage(PedController ped)
        {
            Vector3 lp = transform.InverseTransformPoint(ped.transform.position);
            float carriageX = LocalX(_carriage.position);
            var way = new List<Vector3>();
            if (lp.z > BackZ + 0.8f)                                      // on the front side or beside it: round the nearer end first
            {
                float endX = (lp.x >= 0f ? 1f : -1f) * (Mathf.Abs(_home.x) + 1.8f);
                way.Add(transform.TransformPoint(new Vector3(endX, 0f, Mathf.Max(lp.z, 1.6f))));
                way.Add(transform.TransformPoint(new Vector3(endX, 0f, BackZ)));
            }
            way.Add(PushSpot(carriageX));
            foreach (Vector3 target in way)
            {
                float until = Time.realtimeSinceStartup + 7f;   // (a player who cannot get there does not hold the cut up: it goes on)
                while (Time.realtimeSinceStartup < until)
                {
                    Vector3 d = target - ped.transform.position;
                    d.y = 0f;
                    if (d.sqrMagnitude < 0.12f) break;
                    ped.AutoWalkTo(target);
                    yield return null;
                }
                if (Time.realtimeSinceStartup >= until) Dbg.Log("[Sawmill] the player did not reach " + target.ToString("0.0") + ": it is at " + ped.transform.position.ToString("0.0") + " (blocked?)");
            }
            ped.AutoStop();
        }

        /// <summary>One push or pull of the carriage along the track: it moves while the player keeps up with it, and the player walks beside it on the back side.</summary>
        private IEnumerator Push(PedController ped, Vector3 from, Vector3 to, float scaleFrom, float scaleTo)
        {
            float seconds = Mathf.Max(0.5f, Vector3.Distance(from, to) / 2.2f);   // metres a second
            float t = 0f;
            while (t < seconds)
            {
                float k = Mathf.SmoothStep(0f, 1f, t / seconds);
                _carriage.localPosition = Vector3.Lerp(from, to, k);
                if (_logView != null && scaleFrom != scaleTo) _logView.transform.localScale = new Vector3(1f, Mathf.Lerp(scaleFrom, scaleTo, k), 1f);
                t += Time.deltaTime;
                yield return null;
            }
            _carriage.localPosition = to;
        }

        private IEnumerator Cut(LumberType type, int count)
        {
            _busy = true;
            PedController ped = PedController.Current;
            Dbg.Log("[Sawmill] cutting " + LogId + " into " + count + " x " + type.Id + "; the player is at " + (ped != null ? ped.transform.position.ToString("0.0") : "none") + ", the carriage at " + _carriage.position.ToString("0.0"));
            if (ItemRegistry.TryGet(type.Id, out ItemRegistry.ItemInfo outInfo) && outInfo.Prefab != null)
            {
                GlbTemplate og = outInfo.Prefab.GetComponent<GlbTemplate>();
                if (og != null) og.EnsureLoading();   // the lumber's own model loads while the saw is at work
            }
            if (ped != null) yield return WalkToCarriage(ped);
            if (ped != null) Dbg.Log("[Sawmill] the player stands at " + ped.transform.position.ToString("0.0") + " (the push spot is " + PushSpot(LocalX(_carriage.position)).ToString("0.0") + ")");
            if (ped != null) ped.AutoStop();   // the player stands at the start of the track, on the back side, while the carriage runs
            Vector3 end = new Vector3(-_home.x, _home.y, _home.z);
            _spinning = true;
            for (int pass = 0; pass < Passes; pass++)
            {
                float a = 1f - pass / (float)Passes, b = Mathf.Max(0.04f, 1f - (pass + 1) / (float)Passes);
                yield return Push(ped, _home, end, a, b);     // pushed along the log, the blade cutting
                yield return Push(ped, end, _home, b, b);     // and brought back
            }
            _spinning = false;
            if (ped != null) ped.AutoStop();
            ClearLog();   // the uncut log is gone
            yield return Deposit(type, count);
            foreach (LumberType other in Types)       // loose stacks of any lumber at the machine that now make a bundle are bundled too
                if (other != type) yield return Deposit(other, 0);
            _busy = false;
        }

        // ------------------------------------------------------------------ the bundles beside it

        public const float Gap = 0.04f;                                   // between two things in the lumber area
        private const float ZEnd = FirstRowZ + MaxRows * RowPitch;        // how far out the lumber area goes

        /// <summary>The pieces are made up into strapped bundles (the biggest first); what does not make a bundle is left as loose pieces.</summary>
        private static List<string> BundlesFor(LumberType t, int count, out int loose)
        {
            var list = new List<string>();
            int left = count;
            foreach (KeyValuePair<string, int> b in GrowthRegistry.PacksOf(t.Id)) while (left >= b.Value) { list.Add(b.Key); left -= b.Value; }   // the packs of the lumber, biggest first (the equivalencies)
            loose = left;
            return list;
        }

        /// <summary>What a cut comes out as, for the menu: "  : 1 bundle and 3 loose".</summary>
        private static string Summary(LumberType t, int count)
        {
            int loose;
            int bundles = BundlesFor(t, count, out loose).Count;
            if (bundles == 0) return "  : loose";
            return "  : " + bundles + (bundles == 1 ? " bundle" : " bundles") + (loose > 0 ? " + " + loose + " loose" : "");
        }

        private static readonly Dictionary<string, float> s_depth = new Dictionary<string, float>();

        /// <summary>How deep an item lies across the track (its model's z, measured once its model is loaded; a guess until then: a bundle is wide, a piece is narrow).</summary>
        private static float DepthOf(string itemId)
        {
            if (s_depth.TryGetValue(itemId, out float known)) return known;
            float guess = itemId.Contains("bundle") || itemId.Contains("_stack_") ? 0.6f : 0.3f;
            if (!ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info) || info.Prefab == null) return guess;
            GlbTemplate glb = info.Prefab.GetComponent<GlbTemplate>();
            if (glb != null) { glb.EnsureLoading(); if (!glb.Ready) return guess; }
            Transform root = info.Prefab.transform;
            bool any = false;
            Bounds b = default;
            foreach (MeshFilter mf in info.Prefab.GetComponentsInChildren<MeshFilter>(true))
            {
                if (mf.sharedMesh == null) continue;
                Bounds mb = mf.sharedMesh.bounds;
                for (int k = 0; k < 8; k++)
                {
                    Vector3 corner = mb.center + new Vector3((k & 1) == 0 ? -mb.extents.x : mb.extents.x, (k & 2) == 0 ? -mb.extents.y : mb.extents.y, (k & 4) == 0 ? -mb.extents.z : mb.extents.z);
                    Vector3 w = root.InverseTransformPoint(mf.transform.TransformPoint(corner));
                    if (!any) { b = new Bounds(w, Vector3.zero); any = true; } else b.Encapsulate(w);
                }
            }
            if (!any) return guess;
            float depth = Mathf.Max(0.05f, b.size.z);
            s_depth[itemId] = depth;
            return depth;
        }

        /// <summary>Whether a place in the machine's local space is in the lumber area: along the track, and on the front side from the first row out.</summary>
        private static bool InZone(Vector3 local) { return Mathf.Abs(local.x) <= SpanX && local.z >= FirstRowZ - RowPitch * 0.5f && local.z <= ZEnd; }

        public const float NearM = 5f;   // a stack of the loose lumber within this of the machine (its rectangle) counts as "already there", wherever it is round it

        private static bool NearMachine(Vector3 local)
        {
            float dx = Mathf.Max(0f, Mathf.Abs(local.x) - 3.3f), dz = Mathf.Max(0f, Mathf.Abs(local.z) - 0.8f);
            return Mathf.Sqrt(dx * dx + dz * dz) <= NearM;
        }

        private bool LocalBounds(PlacedObject o, out Vector3 min, out Vector3 max)
        {
            min = max = Vector3.zero;
            bool any = false;
            foreach (Renderer r in o.GetComponentsInChildren<Renderer>())
            {
                Bounds b = r.bounds;
                for (int k = 0; k < 8; k++)
                {
                    Vector3 c = b.center + new Vector3((k & 1) == 0 ? -b.extents.x : b.extents.x, (k & 2) == 0 ? -b.extents.y : b.extents.y, (k & 4) == 0 ? -b.extents.z : b.extents.z);
                    Vector3 l = transform.InverseTransformPoint(c);
                    if (!any) { min = max = l; any = true; } else { min = Vector3.Min(min, l); max = Vector3.Max(max, l); }
                }
            }
            return any;
        }

        /// <summary>The stretches across the track (the machine's local z) that things already take in the lumber area, nearest first.</summary>
        private List<Vector2> Occupied()
        {
            var list = new List<Vector2>();
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || o == _placed || !LocalBounds(o, out Vector3 lo, out Vector3 hi)) continue;
                if (hi.z < FirstRowZ - 0.3f || lo.z > ZEnd + 0.5f) continue;
                if (lo.x > SpanX + 1.5f || hi.x < -SpanX - 1.5f) continue;
                list.Add(new Vector2(lo.z, hi.z));
            }
            list.Sort((a, b) => a.x.CompareTo(b.x));
            return list;
        }

        /// <summary>The first place along the lumber area that a thing this deep fits in, clear of what is there. False when there is none.</summary>
        private static bool FindZ(List<Vector2> occupied, float depth, out float centre)
        {
            float lo = FirstRowZ;
            foreach (Vector2 iv in occupied)
            {
                if (iv.y + Gap <= lo) continue;               // wholly before it
                if (iv.x - Gap >= lo + depth) break;           // it fits before this one
                lo = Mathf.Max(lo, iv.y + Gap);
            }
            centre = lo + depth * 0.5f;
            return lo + depth <= ZEnd;
        }

        private static void Take(List<Vector2> occupied, float centre, float depth)
        {
            occupied.Add(new Vector2(centre - depth * 0.5f, centre + depth * 0.5f));
            occupied.Sort((a, b) => a.x.CompareTo(b.x));
        }

        /// <summary>
        /// The stacks of LOOSE pieces of an item near the machine, whoever made them: the placed pieces of that item standing on the same spot are one stack, each with its top piece (the
        /// highest level) and its count. The stack nearest the machine first.
        /// </summary>
        private List<KeyValuePair<PlacedObject, int>> StacksOf(string itemId)
        {
            var seen = new List<Vector2>();
            var tops = new List<PlacedObject>();
            var counts = new List<int>();
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || o == _placed || o.ItemId != itemId) continue;
                Vector3 l = transform.InverseTransformPoint(o.transform.position);
                if (!InZone(l) && !NearMachine(l)) continue;
                Vector2 spot = new Vector2(l.x, l.z);
                int at = -1;
                for (int k = 0; k < seen.Count; k++) if ((seen[k] - spot).sqrMagnitude < 0.04f) { at = k; break; }   // within 20 cm: the same stack
                if (at < 0) { seen.Add(spot); tops.Add(o); counts.Add(1); }
                else { counts[at]++; if (o.Level > tops[at].Level) tops[at] = o; }
            }
            var stacks = new List<KeyValuePair<PlacedObject, int>>();
            for (int k = 0; k < tops.Count; k++) stacks.Add(new KeyValuePair<PlacedObject, int>(tops[k], counts[k]));
            stacks.Sort((x, y) => transform.InverseTransformPoint(x.Key.transform.position).z.CompareTo(transform.InverseTransformPoint(y.Key.transform.position).z));
            return stacks;
        }

        /// <summary>Every loose piece of an item lying at the machine (the pieces StacksOf counts).</summary>
        private List<PlacedObject> LoosePieces(string itemId)
        {
            var list = new List<PlacedObject>();
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || o == _placed || o.ItemId != itemId) continue;
                Vector3 l = transform.InverseTransformPoint(o.transform.position);
                if (InZone(l) || NearMachine(l)) list.Add(o);
            }
            return list;
        }

        /// <summary>Whether a cut fits: every bundle finds a place in the lumber area, and so do the loose pieces (on the stacks of them already there, or on new ones).</summary>
        private bool Fits(LumberType t, int count)
        {
            List<Vector2> occ = Occupied();
            List<string> bundles = BundlesFor(t, count, out int loose);
            foreach (string bundle in bundles)
            {
                float depth = DepthOf(bundle);
                if (!FindZ(occ, depth, out float c)) return false;
                Take(occ, c, depth);
            }
            if (loose <= 0) return true;
            int limit = Mathf.Max(1, ContainerRules.StackingLimit(t.Id)), room = 0;
            foreach (var st in StacksOf(t.Id)) room += Mathf.Max(0, limit - st.Value);
            int more = loose - room;
            while (more > 0)
            {
                float depth = DepthOf(t.Id);
                if (!FindZ(occ, depth, out float c)) return false;
                Take(occ, c, depth);
                more -= limit;
            }
            return true;
        }

        private Vector3 PlaceAt(float z)
        {
            Vector3 world = transform.TransformPoint(new Vector3(0f, 0f, z));
            return TerrainHeightDetector.PlaceOnGround(new Vector3(world.x, world.y - 2f, world.z));
        }

        private static IEnumerator Ready(ItemRegistry.ItemInfo info)
        {
            GlbTemplate glb = info.Prefab != null ? info.Prefab.GetComponent<GlbTemplate>() : null;
            if (glb == null) yield break;
            glb.EnsureLoading();
            float until = Time.realtimeSinceStartup + 20f;
            while (!glb.Ready && !glb.Failed && Time.realtimeSinceStartup < until) yield return null;
        }

        /// <summary>
        /// The cut comes out as strapped bundles (the biggest the pieces make, then the next size), each in the next free place along the front of the sawmill. What does not make a bundle is
        /// loose pieces: they fill the stacks of that lumber that are already there, and what is left starts a new stack.
        /// </summary>
        private IEnumerator Deposit(LumberType type, int count)
        {
            List<string> bundles = BundlesFor(type, count, out int loose);
            {
                // loose pieces already lying there count too: when they and the new ones make another bundle, they are all bundled together
                List<PlacedObject> old = LoosePieces(type.Id);
                if (old.Count > 0 && BundlesFor(type, count + old.Count, out _).Count > bundles.Count)
                {
                    foreach (PlacedObject o in old) o.Remove();
                    count += old.Count;
                    bundles = BundlesFor(type, count, out loose);
                }
            }
            var wanted = new List<string>(bundles);
            if (loose > 0) wanted.Add(type.Id);
            foreach (string id in wanted) if (ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo want) && want.Prefab != null) yield return Ready(want);
            List<Vector2> occ = Occupied();
            Dbg.Log("[Sawmill] putting out " + count + " x " + type.Id + " as " + bundles.Count + " bundle(s) and " + loose + " loose");
            foreach (string bundle in bundles)
            {
                if (!ItemRegistry.TryGet(bundle, out ItemRegistry.ItemInfo info) || info.Prefab == null) { loose += BundleSize(type, bundle); continue; }   // (no model: they come out loose)
                int bundleLimit = Mathf.Max(1, ContainerRules.StackingLimit(bundle));
                PlacedObject under = null;
                foreach (var st in StacksOf(bundle)) if (st.Value < bundleLimit) { under = st.Key; break; }   // a stack of that bundle with room: it goes on top
                if (under != null)
                {
                    Vector3 up = under.transform.position;
                    PlacementController.SpawnPlaced(bundle, info, new Vector3(up.x, up.y + under.Height, up.z), under.YawDeg, true, under.Level + 1);
                    yield return null;
                    continue;
                }
                float depth = DepthOf(bundle);
                if (!FindZ(occ, depth, out float centre)) { loose += BundleSize(type, bundle); continue; }
                Take(occ, centre, depth);
                PlacementController.SpawnPlaced(bundle, info, PlaceAt(centre), _placed.YawDeg, true, 0);
                yield return null;
            }
            if (loose <= 0) yield break;
            if (!ItemRegistry.TryGet(type.Id, out ItemRegistry.ItemInfo pieceInfo) || pieceInfo.Prefab == null) yield break;
            int limit = Mathf.Max(1, ContainerRules.StackingLimit(type.Id));
            int left = loose;
            foreach (var st in StacksOf(type.Id))        // the loose pieces fill the stacks already there first
            {
                PlacedObject top = st.Key;
                int have = st.Value;
                while (left > 0 && have < limit)
                {
                    Vector3 tp = top.transform.position;
                    top = PlacementController.SpawnPlaced(type.Id, pieceInfo, new Vector3(tp.x, tp.y + top.Height, tp.z), top.YawDeg, true, top.Level + 1);   // turned like the stack it joins
                    have++;
                    left--;
                }
                if (left <= 0) break;
            }
            while (left > 0)                              // and the rest starts new stacks
            {
                float depth = DepthOf(type.Id);
                if (!FindZ(occ, depth, out float centre)) break;
                Take(occ, centre, depth);
                PlacedObject top = PlacementController.SpawnPlaced(type.Id, pieceInfo, PlaceAt(centre), _placed.YawDeg, true, 0);
                left--;
                for (int n = 1; n < limit && left > 0; n++)
                {
                    Vector3 tp = top.transform.position;
                    top = PlacementController.SpawnPlaced(type.Id, pieceInfo, new Vector3(tp.x, tp.y + top.Height, tp.z), _placed.YawDeg, true, top.Level + 1);
                    left--;
                }
                yield return null;
            }
        }

        private static int BundleSize(LumberType t, string bundleId)
        {
            foreach (KeyValuePair<string, int> b in GrowthRegistry.PacksOf(t.Id)) if (b.Key == bundleId) return b.Value;
            return 0;
        }
    }
}
