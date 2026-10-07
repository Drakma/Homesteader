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
    /// The lot builder. With a lot blueprint in hand (a manifest with lot_style: dirt, gravel, asphalt or concrete) left clicks lay the corners of the lot on your land. One corner, then
    /// the opposite one, makes a RECTANGLE of any size (the preview follows the cursor); three or more corners make any other shape. Enter lays it; Backspace or a right click takes the
    /// last corner back; Esc (or another slot) throws the plan away. A lot of A square metres uses ceil(A / lot_m2_per_item) of the blueprint's material, from the hotbar and the 4 m work
    /// site round the first corner (as for paths and fences); the ped walks over and works kneeling while it is laid. Shift + right click on a lot with a pickaxe or a shovel breaks it up.
    /// docs/LOTS.md.
    /// </summary>
    public sealed class LotBuilder : MonoBehaviour
    {
        private static LotBuilder s_instance;
        public static bool Building => s_instance != null && s_instance._pts.Count > 0;

        private const float MinArea = 4f, MaxArea = 2500f, MinSide = 1f;
        private const int MaxPoints = 24;
        private const string WorkClip = "Fixing_Kneeling_RT";
        private const float PreviewEdge = 3f;

        private readonly List<Vector3> _pts = new List<Vector3>();
        private string _itemId;
        private LineRenderer _outline, _siteLine;
        private MeshFilter _fill;
        private readonly List<GameObject> _markers = new List<GameObject>();
        private Material _mat, _fillMat;
        private VisualElement _panel;
        private Label _title, _l1, _l2, _l3;
        private bool _rightDown, _working, _stopWork;
        private Vector2 _rightDownAt;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<LotBuilder>() != null) return;
            var go = new GameObject("LotBuilder");
            DontDestroyOnLoad(go);
            s_instance = go.AddComponent<LotBuilder>();
        }

        private void Awake() { s_instance = this; }

        /// <summary>Esc while a lot is being planned throws the plan away (HudBindings calls this).</summary>
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
            if (WelcomeMenuController.IsLoading || _working || AreaTidy.Active) { HidePreview(); return; }
            string held = ConstructionSite.HeldItem();
            AssetCatalogItem item = held != null ? HudBindings.GetCatalogItem(held) : null;
            bool isLot = item != null && !string.IsNullOrEmpty(item.lot_style);
            if (_pts.Count > 0 && (!isLot || held != _itemId)) Reset();
            TryBreakUp(held);
            if (!isLot) { HidePreview(); return; }

            Mouse mouse = Mouse.current;
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            HudBindings hud = HudBindings.Instance;
            if (mouse == null || cam == null || hud == null) { HidePreview(); return; }
            Vector2 pointer = mouse.position.ReadValue();
            if (hud.IsPointerOverUI(pointer) || HudBindings.KeyboardCaptured) { HidePreview(); return; }
            if (!FenceBuilder.GroundPoint(cam.ScreenPointToRay(pointer), out Vector3 ground)) { HidePreview(); return; }

            _itemId = held;
            Vector3 spot = FenceBuilder.Snap(ground);
            Keyboard keyboard = Keyboard.current;
            if (keyboard != null && keyboard.backspaceKey.wasPressedThisFrame && _pts.Count > 0) _pts.RemoveAt(_pts.Count - 1);
            if (mouse.rightButton.wasPressedThisFrame) { _rightDown = true; _rightDownAt = pointer; }
            else if (_rightDown && mouse.rightButton.wasReleasedThisFrame)
            {
                _rightDown = false;
                bool shift = keyboard != null && keyboard.shiftKey.isPressed;
                if (!shift && (pointer - _rightDownAt).sqrMagnitude <= 36f && _pts.Count > 0) _pts.RemoveAt(_pts.Count - 1);
            }

            if (keyboard != null && keyboard.enterKey.wasPressedThisFrame && _pts.Count >= 2) { TryComplete(item); return; }

            // the shape as it would be with the cursor's corner added: a rectangle from the first corner while only one is down
            List<Vector3> shape = ShapeWith(spot);
            string why = ProblemAt(spot);
            string problem = why ?? ShapeProblem(shape, false);
            if (mouse.leftButton.wasPressedThisFrame)
            {
                if (why != null) ToastNotificationSystem.ShowInfo("Lot", why);
                else if (_pts.Count < MaxPoints)
                {
                    List<Vector3> with = new List<Vector3>(_pts) { spot };
                    string bad = with.Count >= 3 ? ShapeProblem(Corners(with), false) : null;
                    if (bad != null) ToastNotificationSystem.ShowInfo("Lot", bad); else _pts.Add(spot);
                }
            }
            shape = ShapeWith(spot);
            problem = why ?? (_pts.Count >= 1 ? ShapeProblem(shape, false) : null);
            Draw(shape, spot, problem == null);
            ShowPanel(item, shape, problem);
        }

        // ------------------------------------------------------------------ the shape

        /// <summary>The corners as a polygon: two points are the opposite corners of a rectangle.</summary>
        private static List<Vector3> Corners(List<Vector3> pts)
        {
            if (pts.Count != 2) return new List<Vector3>(pts);
            Vector3 a = pts[0], b = pts[1];
            return new List<Vector3>
            {
                new Vector3(a.x, a.y, a.z), new Vector3(b.x, a.y, a.z), new Vector3(b.x, b.y, b.z), new Vector3(a.x, b.y, b.z),
            };
        }

        private List<Vector3> ShapeWith(Vector3 cursor)
        {
            var with = new List<Vector3>(_pts);
            if (with.Count == 0) return with;
            if (with.Count == 1) with.Add(cursor);                                   // a rectangle from the first corner to the cursor
            else if (with.Count >= 3) with.Add(cursor);                              // another shape: the cursor is its next corner
            return Corners(with);                                                    // (two corners placed: that rectangle, a third click bends it)
        }

        private string ProblemAt(Vector3 spot)
        {
            if (!LandOwnershipSystem.IsOwned(spot.x, spot.z)) return "You can only lay a lot on land you own.";
            if (spot.y < TerrainHeightDetector.GetWaterY() + 0.05f) return "You can't lay a lot in water.";
            return null;
        }

        /// <summary>What is wrong with the whole shape (null when it can be laid). `full` also looks for trees, plants and objects in the way (a little dearer: done when it is laid).</summary>
        private static string ShapeProblem(List<Vector3> poly, bool full)
        {
            if (poly.Count < 3) return null;
            float area = LotRun.PolygonArea(poly);
            if (area < 0.5f) return null;                     // still being drawn
            if (LotRun.SelfIntersects(poly)) return "The edges cross each other.";
            if (area > MaxArea) return "That lot is too big (at most " + UnitFormat.Area(MaxArea) + ").";
            float water = TerrainHeightDetector.GetWaterY() + 0.05f;
            float x0 = float.MaxValue, x1 = float.MinValue, z0 = float.MaxValue, z1 = float.MinValue;
            foreach (Vector3 p in poly) { x0 = Mathf.Min(x0, p.x); x1 = Mathf.Max(x1, p.x); z0 = Mathf.Min(z0, p.z); z1 = Mathf.Max(z1, p.z); }
            float step = Mathf.Max(2f, Mathf.Sqrt(area / 400f));   // at most about 400 samples
            for (float z = z0; z <= z1 + 0.01f; z += step)
                for (float x = x0; x <= x1 + 0.01f; x += step)
                {
                    if (!LotRun.Inside(poly, x, z)) continue;
                    if (!LandOwnershipSystem.IsOwned(x, z)) return "The lot would leave your land.";
                    if (TerrainHeightDetector.GetGroundY(x, z) < water) return "The lot would reach into water.";
                }
            foreach (Vector3 p in poly)
            {
                if (!LandOwnershipSystem.IsOwned(p.x, p.z)) return "The lot would leave your land.";
                if (TerrainHeightDetector.GetGroundY(p.x, p.z) < water) return "The lot would reach into water.";
            }
            if (!full) return null;
            foreach (PlantedGrowth pg in PlantedGrowth.All)
                if (pg != null && LotRun.Inside(poly, pg.transform.position.x, pg.transform.position.z)) return "Something is growing in the way.";
            foreach (PlacedObject po in PlacedObject.All)
                if (po != null && !WheelbarrowPush.IsPile(po.ItemId) && LotRun.Inside(poly, po.transform.position.x, po.transform.position.z)) return "Something is in the way.";
            // never through a tree: sample the inside on a metre grid (and the edges) for a trunk
            var samples = new List<Vector3>();
            for (float z = z0; z <= z1 + 0.01f; z += 1.5f)
                for (float x = x0; x <= x1 + 0.01f; x += 1.5f)
                    if (LotRun.Inside(poly, x, z)) samples.Add(new Vector3(x, 0f, z));
            for (int i = 0; i < poly.Count; i++)
            {
                Vector3 a = poly[i], b = poly[(i + 1) % poly.Count];
                int n = Mathf.Max(1, Mathf.CeilToInt(Vector3.Distance(a, b) / 1.5f));
                for (int k = 0; k <= n; k++) samples.Add(Vector3.Lerp(a, b, k / (float)n));
            }
            if (Homesteader.World.ForestTrees.TreeNearRoute(samples, 1.0f)) return "A tree is in the way. Fell it first, or make the lot around it.";
            return null;
        }

        // ------------------------------------------------------------------ laying it

        private void TryComplete(AssetCatalogItem item)
        {
            List<Vector3> poly = Corners(_pts);
            if (poly.Count < 3) { ToastNotificationSystem.ShowInfo("Lot", "A lot needs a second corner (or more) first."); return; }
            float area = LotRun.PolygonArea(poly);
            if (area < MinArea) { ToastNotificationSystem.ShowInfo("Lot", "That lot is too small (at least " + UnitFormat.Area(MinArea) + ")."); return; }
            string bad = ShapeProblem(poly, true);
            if (bad != null) { ToastNotificationSystem.ShowInfo("Lot", bad); return; }
            float per = Mathf.Max(0.5f, item.lot_m2_per_item);
            int items = Mathf.Max(1, Mathf.CeilToInt(area / per - 0.001f));
            string material = string.IsNullOrEmpty(item.lot_material_item) ? _itemId : item.lot_material_item;
            int have = FenceBuilder.Available(material, _pts[0]);
            if (have < items)
            {
                ToastNotificationSystem.ShowWarning("Not enough materials", $"This lot needs {items} x {HudBindings.GetItemName(material)} (you have {have} in the toolbar and at the work site).");
                return;
            }
            string id = _itemId;
            Vector3 first = _pts[0];
            Reset();
            StartCoroutine(LayWalk(item, material, poly, items, first));
        }

        private System.Collections.IEnumerator LayWalk(AssetCatalogItem item, string material, List<Vector3> poly, int items, Vector3 site)
        {
            _working = true;
            _stopWork = false;
            var ped = PedController.Current;
            bool stopped = false;
            if (ped != null)
            {
                Vector3 stand = site;
                float best = float.MaxValue;
                foreach (Vector3 p in poly) { float d = (p - ped.transform.position).sqrMagnitude; if (d < best) { best = d; stand = p; } }
                bool ok = true;
                yield return WalkTo(ped, stand, r => ok = r);
                if (!ok) stopped = true;
                else
                {
                    bool kneeling = ped.BeginWork(WorkClip, stand);
                    float seconds = Mathf.Clamp(2f + items * 0.25f, 2f, 14f);
                    float until = Time.time + seconds;
                    while (Time.time < until)
                    {
                        if (ped.ManualInput || _stopWork) { stopped = true; break; }
                        yield return null;
                    }
                    if (kneeling) ped.EndWork(WorkClip);
                }
                ped.AutoStop();
            }
            if (!stopped)
            {
                if (FenceBuilder.Available(material, site) < items)
                    ToastNotificationSystem.ShowWarning("Out of materials", "The lot needs " + items + " x " + HudBindings.GetItemName(material) + ".");
                else
                {
                    FenceBuilder.Take(material, items, site);
                    HudBindings.Instance?.RefreshToolbar();
                    LotRun.Create(item.lot_style, item.id, poly);
                    Homesteader.World.SiteClearing.ClearPolygon(poly);   // plants and rocks on the lot go
                }
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
                if (dist <= 0.8f || Time.time > giveUp) break;
                if (dist < best - 0.3f) { best = dist; mark = Time.time; }
                else if (Time.time - mark > 1.5f) break;
                yield return null;
            }
            ped.AutoStop();
            done(true);
        }

        // ------------------------------------------------------------------ breaking one up

        private static float s_breakDownAt = -1f;

        /// <summary>Shift + right click on a lot with a pickaxe or a shovel in hand breaks the lot up (no material comes back).</summary>
        private void TryBreakUp(string held)
        {
            if (held != "tool_pickaxe" && held != "tool_shovel" && held != "tool_shovel_round_point" && held != "tool_shovel_trenching") return;
            Mouse mouse = Mouse.current;
            Keyboard keyboard = Keyboard.current;
            if (mouse == null || keyboard == null || !keyboard.shiftKey.isPressed || !mouse.rightButton.wasPressedThisFrame) return;
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            HudBindings hud = HudBindings.Instance;
            Vector2 pointer = mouse.position.ReadValue();
            if (cam == null || hud == null || hud.IsPointerOverUI(pointer)) return;
            if (!FenceBuilder.GroundPoint(cam.ScreenPointToRay(pointer), out Vector3 ground)) return;
            LotRun lot = LotRun.At(ground.x, ground.z);
            if (lot == null) return;
            var ped = PedController.Current;
            if (ped != null && Vector2.Distance(new Vector2(ped.transform.position.x, ped.transform.position.z), new Vector2(ground.x, ground.z)) > 6f)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to break up the lot.");
                return;
            }
            Destroy(lot.gameObject);
        }

        // ------------------------------------------------------------------ the picture

        private void Reset()
        {
            _pts.Clear();
            _itemId = null;
            HidePreview();
        }

        private void EnsureParts()
        {
            if (_mat == null) _mat = new Material(Shader.Find("Sprites/Default")) { hideFlags = HideFlags.DontSave };
            if (_fillMat == null) _fillMat = new Material(Shader.Find("Sprites/Default")) { hideFlags = HideFlags.DontSave };
            if (_outline == null)
            {
                var go = new GameObject("LotPlanOutline");
                go.transform.SetParent(transform, false);
                _outline = go.AddComponent<LineRenderer>();
                _outline.useWorldSpace = true;
                _outline.loop = true;
                _outline.numCornerVertices = 2;
                _outline.widthMultiplier = 0.12f;
                _outline.sharedMaterial = _mat;
                _outline.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                _outline.sortingOrder = 10;
                var sg = new GameObject("LotWorkSite");
                sg.transform.SetParent(transform, false);
                _siteLine = sg.AddComponent<LineRenderer>();
                _siteLine.useWorldSpace = true;
                _siteLine.loop = true;
                _siteLine.positionCount = 4;
                _siteLine.widthMultiplier = 0.08f;
                _siteLine.sharedMaterial = _mat;
                _siteLine.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                _siteLine.sortingOrder = 9;
                var fg = new GameObject("LotPlanFill");
                fg.transform.SetParent(transform, false);
                _fill = fg.AddComponent<MeshFilter>();
                var fr = fg.AddComponent<MeshRenderer>();
                fr.sharedMaterial = _fillMat;
                fr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                fr.receiveShadows = false;
            }
        }

        private void Draw(List<Vector3> shape, Vector3 cursor, bool valid)
        {
            EnsureParts();
            Color c = valid ? new Color(0.35f, 0.85f, 1f) : new Color(1f, 0.3f, 0.25f);
            _outline.startColor = _outline.endColor = c;
            _outline.positionCount = shape.Count;
            for (int i = 0; i < shape.Count; i++) _outline.SetPosition(i, new Vector3(shape[i].x, TerrainHeightDetector.GetGroundY(shape[i].x, shape[i].z) + 0.18f, shape[i].z));
            _outline.enabled = shape.Count >= 2;
            _fillMat.color = new Color(c.r, c.g, c.b, 0.3f);
            if (shape.Count >= 3 && LotRun.PolygonArea(shape) > 0.5f && !LotRun.SelfIntersects(shape))
            {
                _fill.sharedMesh = LotRun.BuildMesh(shape, PreviewEdge, 0.14f, _fill.sharedMesh);
                _fill.gameObject.SetActive(true);
            }
            else _fill.gameObject.SetActive(false);

            Vector3 centre = _pts.Count > 0 ? _pts[0] : cursor;
            Vector3[] sq =
            {
                new Vector3(centre.x - FenceBuilder.SiteHalf, 0f, centre.z - FenceBuilder.SiteHalf), new Vector3(centre.x + FenceBuilder.SiteHalf, 0f, centre.z - FenceBuilder.SiteHalf),
                new Vector3(centre.x + FenceBuilder.SiteHalf, 0f, centre.z + FenceBuilder.SiteHalf), new Vector3(centre.x - FenceBuilder.SiteHalf, 0f, centre.z + FenceBuilder.SiteHalf),
            };
            for (int i = 0; i < 4; i++) { sq[i].y = TerrainHeightDetector.GetGroundY(sq[i].x, sq[i].z) + 0.16f; _siteLine.SetPosition(i, sq[i]); }
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
            if (_outline != null) _outline.enabled = false;
            if (_siteLine != null) _siteLine.enabled = false;
            if (_fill != null) _fill.gameObject.SetActive(false);
            foreach (GameObject m in _markers) if (m != null) Destroy(m);
            _markers.Clear();
            if (_panel != null) _panel.style.display = DisplayStyle.None;
        }

        private void ShowPanel(AssetCatalogItem item, List<Vector3> shape, string problem)
        {
            UIDocument doc = FindAnyObjectByType<UIDocument>();
            VisualElement root = doc != null ? doc.rootVisualElement : null;
            if (root == null) return;
            if (_panel == null || _panel.parent != root)
            {
                _panel?.RemoveFromHierarchy();
                _panel = new VisualElement { name = "LotPlanCard", pickingMode = PickingMode.Ignore };
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
            float area = shape.Count >= 3 ? LotRun.PolygonArea(shape) : 0f;
            float per = Mathf.Max(0.5f, item.lot_m2_per_item);
            int items = area > 0f ? Mathf.Max(1, Mathf.CeilToInt(area / per - 0.001f)) : 0;
            string material = string.IsNullOrEmpty(item.lot_material_item) ? _itemId : item.lot_material_item;
            Vector3 first = _pts.Count > 0 ? _pts[0] : Vector3.zero;
            _title.text = item.name;
            _l1.text = area > 0f ? "Lot: " + UnitFormat.Area(area) + " of " + item.lot_style : "Lot of " + item.lot_style;
            _l2.text = _pts.Count > 0 ? $"{HudBindings.GetItemName(material)}: {items} of {FenceBuilder.Available(material, first)}" : HudBindings.GetItemName(material) + ": one per " + UnitFormat.Area(per);
            _l3.text = problem != null ? problem
                     : _pts.Count == 0 ? "Click a corner of the lot (the 4 m square round it is the work site for materials)"
                     : _pts.Count == 1 ? "Click the opposite corner for a rectangle, or keep clicking corners for another shape"
                     : _pts.Count == 2 ? "Enter lays this rectangle; click again to bend it into another shape; right click undoes"
                     : "Enter lays the lot, click adds a corner, right click undoes";
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
