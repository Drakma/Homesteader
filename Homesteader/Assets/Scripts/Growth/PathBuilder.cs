using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Land;
using Homesteader.UI;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UIElements;

namespace Homesteader.Growth
{
    /// <summary>
    /// The path and road builder. With a path or road material in hand (a manifest with path_kind: path or road) each left click adds a control
    /// point on the ground and the route is drawn as a smooth curve through the points (Catmull-Rom). Enter lays the route, Backspace or a right
    /// click takes the last point back, Esc (or choosing another slot) throws the plan away. A route of L metres uses ceil(L / path_m_per_item)
    /// items, from the hotbar and the 4 m work site round the first point (same as fences). The ped then walks the route laying it a section at a
    /// time. The material item decides everything: kind (path or road), width and surface (docs/PATHS.md).
    /// </summary>
    public sealed class PathBuilder : MonoBehaviour
    {
        private static PathBuilder s_instance;
        public static bool Building => s_instance != null && s_instance._pts.Count > 0;

        private const float MinSpacing = 1.5f;
        private const int MaxPoints = 60;
        private const string WorkClip = "Fixing_Kneeling_RT";
        private const float SecondsPerSection = 2.4f;

        private readonly List<Vector3> _pts = new List<Vector3>();
        private string _itemId;
        private LineRenderer _ribbon, _centre, _siteLine;
        private readonly List<GameObject> _markers = new List<GameObject>();
        private Material _mat;
        private VisualElement _panel;
        private Label _title, _l1, _l2, _l3;
        private bool _rightDown, _working, _stopWork;
        private Vector2 _rightDownAt;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<PathBuilder>() != null) return;
            var go = new GameObject("PathBuilder");
            DontDestroyOnLoad(go);
            s_instance = go.AddComponent<PathBuilder>();
        }

        private void Awake() { s_instance = this; }

        /// <summary>Esc while a route is being planned throws the plan away (HudBindings calls this).</summary>
        public static bool CancelPlan()
        {
            if (s_instance == null) return false;
            if (s_instance._working) { s_instance._stopWork = true; return true; }
            if (s_instance._pts.Count == 0) return false;
            s_instance.Reset();
            return true;
        }

        private void Update()
        {
            if (WelcomeMenuController.IsLoading || _working || AreaTidy.Active) { HidePreview(); return; }   // (the tidy mode owns the left button)
            string held = ConstructionSite.HeldItem();
            AssetCatalogItem item = held != null ? HudBindings.GetCatalogItem(held) : null;
            bool isPath = item != null && !string.IsNullOrEmpty(item.path_kind);
            if (_pts.Count > 0 && (!isPath || held != _itemId)) Reset();
            if (!isPath) { HidePreview(); return; }

            Mouse mouse = Mouse.current;
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            HudBindings hud = HudBindings.Instance;
            if (mouse == null || cam == null || hud == null) { HidePreview(); return; }
            Vector2 pointer = mouse.position.ReadValue();
            if (hud.IsPointerOverUI(pointer) || HudBindings.KeyboardCaptured) { HidePreview(); return; }
            if (!FenceBuilder.GroundPoint(cam.ScreenPointToRay(pointer), out Vector3 ground)) { HidePreview(); return; }

            _itemId = held;
            Vector3 spot = FenceBuilder.Snap(ground);
            if (PathRun.SnapToRoute(ground, out Vector3 onRoute)) spot = onRoute;   // on another path or road: lock on to its centre line
            string why = WhyNot(spot);

            Keyboard keyboard = Keyboard.current;
            if (keyboard != null && keyboard.backspaceKey.wasPressedThisFrame && _pts.Count > 0) _pts.RemoveAt(_pts.Count - 1);
            if (mouse.rightButton.wasPressedThisFrame) { _rightDown = true; _rightDownAt = pointer; }
            else if (_rightDown && mouse.rightButton.wasReleasedThisFrame)
            {
                _rightDown = false;
                if ((pointer - _rightDownAt).sqrMagnitude <= 36f && _pts.Count > 0) _pts.RemoveAt(_pts.Count - 1);
            }
            if (keyboard != null && keyboard.enterKey.wasPressedThisFrame && _pts.Count >= 2) { TryComplete(item); return; }

            // the route as it would be with the cursor's point on the end (a point on a tree, or a stretch through one, is refused)
            var withCursor = new List<Vector3>(_pts) { spot };
            string problem = why ?? CurveProblem(PathRun.Sample(withCursor), WidthOf(item));
            if (mouse.leftButton.wasPressedThisFrame)
            {
                if (problem == null && _pts.Count < MaxPoints) _pts.Add(spot);
                else if (problem != null) ToastNotificationSystem.ShowInfo(Noun(item), problem);
            }

            var plan = new List<Vector3>(_pts);
            if (why == null || _pts.Count == 0) plan.Add(spot);
            List<Vector3> curve = PathRun.Sample(plan);
            string badCurve = _pts.Count > 0 || why == null ? CurveProblem(curve, WidthOf(item)) : null;
            Draw(item, curve, spot, why == null && badCurve == null);
            ShowPanel(item, curve, why ?? badCurve);
        }

        /// <summary>The material this blueprint lays (the blueprint itself when none is named, so a bare kit still works).</summary>
        private static string MaterialOf(AssetCatalogItem item, string held) { return string.IsNullOrEmpty(item.path_material_item) ? held : item.path_material_item; }

        private static string Noun(AssetCatalogItem item) { return item.path_kind == "road" ? "Road" : "Path"; }

        private string WhyNot(Vector3 spot)
        {
            string noun = Noun(HudBindings.GetCatalogItem(ConstructionSite.HeldItem())).ToLowerInvariant();
            if (!LandOwnershipSystem.IsOwned(spot.x, spot.z)) return "You can only lay a " + noun + " on land you own.";
            if (spot.y < TerrainHeightDetector.GetWaterY() + 0.05f) return "You can't lay a " + noun + " in water.";
            if (_pts.Count > 0 && Vector2.Distance(new Vector2(spot.x, spot.z), new Vector2(_pts[_pts.Count - 1].x, _pts[_pts.Count - 1].z)) < MinSpacing)
                return "That is too close to the last point.";
            return null;
        }

        /// <summary>Anything wrong along the smooth curve itself (it can bow into water or off owned land between two good points).</summary>
        private static string CurveProblem(List<Vector3> curve, float width)
        {
            float water = TerrainHeightDetector.GetWaterY() + 0.05f;
            foreach (Vector3 p in curve)
            {
                if (p.y < water) return "The route would cross water.";
                if (!LandOwnershipSystem.IsOwned(p.x, p.z)) return "The route would leave your land.";
            }
            // Plantables and placed objects are in the way, never cleared.
            float keep = width * 0.5f + 0.5f;
            foreach (PlantedGrowth pg in PlantedGrowth.All)
                if (pg != null && NearRoute(curve, pg.transform.position, keep)) return "Something is growing in the way.";
            foreach (PlacedObject po in PlacedObject.All)
                if (po != null && !WheelbarrowPush.IsPile(po.ItemId) && NearRoute(curve, po.transform.position, keep)) return "Something is in the way.";   // a pile of material (gravel, sand) for the road does not block it
            // Never through a tree: clear of the trunk by half the width plus the margin the laying clears plants in, so no tree is cut down by it.
            if (Homesteader.World.ForestTrees.TreeNearRoute(curve, width * 0.5f + Homesteader.World.SiteClearing.Margin + 0.1f)) return "A tree is in the way. Fell it first, or route around it.";
            return null;
        }

        private static bool NearRoute(List<Vector3> curve, Vector3 p, float distance)
        {
            float d2 = distance * distance;
            foreach (Vector3 c in curve)
            {
                float dx = c.x - p.x, dz = c.z - p.z;
                if (dx * dx + dz * dz <= d2) return true;
            }
            return false;
        }

        private static float WidthOf(AssetCatalogItem item) { return item.path_width_m > 0f ? item.path_width_m : (item.path_kind == "road" ? 4f : 1.2f); }

        // ------------------------------------------------------------------ laying it

        private void TryComplete(AssetCatalogItem item)
        {
            List<Vector3> curve = PathRun.Sample(_pts);
            string bad = CurveProblem(curve, WidthOf(item));
            if (bad != null) { ToastNotificationSystem.ShowInfo(Noun(item), bad); return; }
            float length = PathRun.Length(curve);
            float per = Mathf.Max(0.25f, item.path_m_per_item);
            int items = Mathf.Max(1, Mathf.CeilToInt(length / per - 0.001f));
            string material = MaterialOf(item, _itemId);
            int have = FenceBuilder.Available(material, _pts[0]);
            if (have < items)
            {
                ToastNotificationSystem.ShowWarning("Not enough materials",
                    $"This {Noun(item).ToLowerInvariant()} needs {items} x {HudBindings.GetItemName(material)} (you have {have}).");
                return;
            }
            var points = new List<Vector3>(_pts);
            string id = _itemId;
            Reset();
            StartCoroutine(LayWalk(item, MaterialOf(item, id), points, items, per));
        }

        private System.Collections.IEnumerator LayWalk(AssetCatalogItem item, string id, List<Vector3> points, int items, float per)
        {
            _working = true;
            _stopWork = false;
            var ped = PedController.Current;
            float width = item.path_width_m > 0f ? item.path_width_m : (item.path_kind == "road" ? 4f : 1.2f);
            string style = string.IsNullOrEmpty(item.path_style) ? "gravel" : item.path_style;
            Vector3 site = points[0];
            PathRun run = PathRun.Create(item.path_kind, style, item.id, width, per, points, 0f);
            float total = run.TotalLength;
            bool stopped = false;
            int laid = 0;
            for (int i = 0; i < items && !_stopWork && !stopped; i++)
            {
                if (run == null) break;
                if (FenceBuilder.Available(id, site) < 1)
                {
                    ToastNotificationSystem.ShowWarning("Out of materials", "The rest of the route needs more " + HudBindings.GetItemName(id) + ".");
                    break;
                }
                float from = i * per, to = Mathf.Min(total, (i + 1) * per);
                Vector3 mid = PathRun.PointAt(run.Curve, (from + to) * 0.5f, out Vector3 forward);
                if (ped != null)
                {
                    Vector3 stand = mid + Vector3.Cross(Vector3.up, forward) * (width * 0.5f + 0.5f);
                    stand.y = TerrainHeightDetector.GetGroundY(stand.x, stand.z);
                    bool ok = true;
                    yield return WalkTo(ped, stand, r => ok = r);
                    if (!ok) { stopped = true; break; }
                    bool kneeling = ped.BeginWork(WorkClip, mid);
                    float until = Time.time + SecondsPerSection;
                    while (Time.time < until)
                    {
                        if (ped.ManualInput || _stopWork) { stopped = true; break; }
                        yield return null;
                    }
                    if (kneeling) ped.EndWork(WorkClip);
                    if (stopped) break;
                }
                FenceBuilder.Take(id, 1, site);
                HudBindings.Instance?.RefreshToolbar();
                laid = i + 1;
                run.Built = to;
                run.Rebuild();
                float yaw = Mathf.Atan2(forward.x, forward.z) * Mathf.Rad2Deg;
                Homesteader.World.SiteClearing.ClearFootprint(mid, yaw, new Vector2(width, Mathf.Max(0.5f, to - from)));   // plants and rocks on the route go
            }
            if (ped != null) ped.AutoStop();
            if (run != null)
            {
                if (laid >= items) { run.Built = float.MaxValue; run.Rebuild(); }
                if (laid > 0) PathRun.ReplaceUnder(run.LaidCurve(), width, run);   // an older route under the new one is taken away
            }
            _working = false;
        }

        private System.Collections.IEnumerator WalkTo(PedController ped, Vector3 target, System.Action<bool> done)
        {
            ped.AutoWalkTo(target);
            float giveUp = Time.time + 8f, best = float.MaxValue, mark = Time.time;
            while (true)
            {
                if (ped.AutoCancelled || _stopWork) { ped.AutoStop(); done(false); yield break; }
                Vector3 d = target - ped.transform.position;
                d.y = 0f;
                float dist = d.magnitude;
                if (dist <= 0.5f || Time.time > giveUp) break;
                if (dist < best - 0.3f) { best = dist; mark = Time.time; }
                else if (Time.time - mark > 1.5f) break;   // not getting closer: work from here
                yield return null;
            }
            ped.AutoStop();
            done(true);
        }

        // ------------------------------------------------------------------ the picture

        private void Reset()
        {
            _pts.Clear();
            _itemId = null;
            HidePreview();
        }

        private LineRenderer NewLine(string name, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var lr = go.AddComponent<LineRenderer>();
            lr.useWorldSpace = true;
            lr.numCapVertices = 2;
            lr.numCornerVertices = 3;
            if (_mat == null) _mat = new Material(Shader.Find("Sprites/Default")) { hideFlags = HideFlags.DontSave };
            lr.sharedMaterial = _mat;
            lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            lr.sortingOrder = order;
            return lr;
        }

        private void Draw(AssetCatalogItem item, List<Vector3> curve, Vector3 cursor, bool valid)
        {
            if (_ribbon == null)
            {
                _ribbon = NewLine("PathPlanRibbon", 8);
                _ribbon.alignment = LineAlignment.TransformZ;
                _ribbon.transform.rotation = Quaternion.Euler(90f, 0f, 0f);   // lies flat on the ground
                _centre = NewLine("PathPlanCentre", 10);
                _centre.widthMultiplier = 0.1f;
                _siteLine = NewLine("PathWorkSite", 9);
                _siteLine.loop = true;
                _siteLine.widthMultiplier = 0.08f;
                _siteLine.positionCount = 4;
            }
            Color c = valid ? new Color(0.35f, 0.85f, 1f) : new Color(1f, 0.3f, 0.25f);
            float width = item.path_width_m > 0f ? item.path_width_m : (item.path_kind == "road" ? 4f : 1.2f);
            _ribbon.widthMultiplier = width;
            _ribbon.positionCount = curve.Count;
            _centre.positionCount = curve.Count;
            for (int i = 0; i < curve.Count; i++)
            {
                _ribbon.SetPosition(i, curve[i] + Vector3.up * 0.12f);
                _centre.SetPosition(i, curve[i] + Vector3.up * 0.16f);
            }
            _ribbon.startColor = _ribbon.endColor = new Color(c.r, c.g, c.b, 0.35f);
            _centre.startColor = _centre.endColor = c;
            _ribbon.enabled = _centre.enabled = curve.Count >= 2;

            Vector3 centre = _pts.Count > 0 ? _pts[0] : cursor;
            Vector3[] sq =
            {
                new Vector3(centre.x - FenceBuilder.SiteHalf, 0f, centre.z - FenceBuilder.SiteHalf), new Vector3(centre.x + FenceBuilder.SiteHalf, 0f, centre.z - FenceBuilder.SiteHalf),
                new Vector3(centre.x + FenceBuilder.SiteHalf, 0f, centre.z + FenceBuilder.SiteHalf), new Vector3(centre.x - FenceBuilder.SiteHalf, 0f, centre.z + FenceBuilder.SiteHalf),
            };
            for (int i = 0; i < 4; i++) { sq[i].y = TerrainHeightDetector.GetGroundY(sq[i].x, sq[i].z) + 0.12f; _siteLine.SetPosition(i, sq[i]); }
            _siteLine.startColor = _siteLine.endColor = _pts.Count > 0 ? new Color(1f, 0.75f, 0.25f, 0.9f) : new Color(1f, 0.75f, 0.25f, 0.4f);
            _siteLine.enabled = true;

            foreach (GameObject m in _markers) if (m != null) Destroy(m);
            _markers.Clear();
            var spots = new List<Vector3>(_pts) { cursor };
            for (int i = 0; i < spots.Count; i++)
            {
                GameObject m = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                Destroy(m.GetComponent<Collider>());
                m.transform.SetParent(transform, false);
                m.transform.position = spots[i] + Vector3.up * 0.3f;
                float r = (i == 0 && _pts.Count > 0) ? 0.3f : 0.18f;
                m.transform.localScale = new Vector3(r, 0.3f, r);
                var rend = m.GetComponent<Renderer>();
                rend.sharedMaterial = _mat;
                rend.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                rend.material.color = i == spots.Count - 1 ? c : new Color(0.9f, 0.9f, 0.9f, 1f);
                _markers.Add(m);
            }
        }

        private void HidePreview()
        {
            if (_ribbon != null) _ribbon.enabled = false;
            if (_centre != null) _centre.enabled = false;
            if (_siteLine != null) _siteLine.enabled = false;
            foreach (GameObject m in _markers) if (m != null) Destroy(m);
            _markers.Clear();
            if (_panel != null) _panel.style.display = DisplayStyle.None;
        }

        private void ShowPanel(AssetCatalogItem item, List<Vector3> curve, string problem)
        {
            UIDocument doc = FindAnyObjectByType<UIDocument>();
            VisualElement root = doc != null ? doc.rootVisualElement : null;
            if (root == null) return;
            if (_panel == null || _panel.parent != root)
            {
                _panel?.RemoveFromHierarchy();
                _panel = new VisualElement { name = "PathPlanCard", pickingMode = PickingMode.Ignore };
                _panel.AddToClassList("construction-hover");
                _panel.style.position = Position.Absolute;
                var edge = new VisualElement { pickingMode = PickingMode.Ignore };
                edge.AddToClassList("hs-accent-edge");
                _panel.Add(edge);
                _title = NewLabel("construction-hover-title");
                _l1 = NewLabel("construction-hover-sub");
                _l2 = NewLabel("construction-hover-sub");
                _l3 = NewLabel("construction-hover-hint");
                root.Insert(0, _panel);
            }
            float width = item.path_width_m > 0f ? item.path_width_m : (item.path_kind == "road" ? 4f : 1.2f);
            float length = PathRun.Length(curve);
            float per = Mathf.Max(0.25f, item.path_m_per_item);
            int items = _pts.Count > 0 ? Mathf.Max(1, Mathf.CeilToInt(length / per - 0.001f)) : 0;
            Vector3 first = _pts.Count > 0 ? _pts[0] : curve.Count > 0 ? curve[0] : Vector3.zero;
            _title.text = item.name;
            _l1.text = $"{Noun(item)}: {UnitFormat.Distance(length)} long, {UnitFormat.Distance(width)} wide";
            string material = MaterialOf(item, _itemId);
            _l2.text = $"{HudBindings.GetItemName(material)}: {items} of {FenceBuilder.Available(material, first)}";
            _l3.text = problem != null ? problem
                     : _pts.Count == 0 ? "Click to place the first point (the 4 m square round it is the work site for materials)"
                     : _pts.Count < 2 ? "Click to add points; the route curves smoothly through them"
                     : "Click to add points, Enter lays the route, right click undoes";
            _panel.style.display = DisplayStyle.Flex;
            Mouse mouse = Mouse.current;
            if (mouse != null && _panel.panel != null)
            {
                Vector2 screen = mouse.position.ReadValue();
                Vector2 p = RuntimePanelUtils.ScreenToPanel(_panel.panel, new Vector2(screen.x, Screen.height - screen.y));
                _panel.style.left = p.x + 24f;
                _panel.style.top = p.y + 24f;
            }
        }

        private Label NewLabel(string cls)
        {
            var l = new Label { pickingMode = PickingMode.Ignore };
            l.AddToClassList(cls);
            _panel.Add(l);
            return l;
        }
    }
}
