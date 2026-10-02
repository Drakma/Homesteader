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
    /// The fence builder. With a fence item in hand (a manifest with fence_style: wood fence panels, wire fence) each left click puts a post on the
    /// ground; clicking the FIRST post again closes the fence into an enclosure, Enter finishes an open line, Backspace takes the last post back
    /// and Esc (or choosing another slot) throws the plan away. Nothing is used until it is built: then the posts and the panels (as many as the
    /// runs between the posts need) come out of the hotbar and the fencing is filled in between the posts. A gate item (gate_width_m) in hand turns
    /// a left click on a built fence into a gate: the fence there is taken out and the gate stands in the gap (a right click then opens and
    /// closes it). A closed fence built while the player stands inside it with no gate in the hotbar warns first: they would be stuck.
    /// </summary>
    public sealed class FenceBuilder : MonoBehaviour
    {
        private static FenceBuilder s_instance;
        public static bool Building => s_instance != null && s_instance._posts.Count > 0;

        private const float SnapMetres = 0.5f;
        private const float CloseDistance = 0.9f;
        private const int MaxPosts = 200;

        private readonly List<Vector3> _posts = new List<Vector3>();
        private string _panelId;
        private LineRenderer _line;
        private readonly List<GameObject> _markers = new List<GameObject>();
        private VisualElement _panel;
        private Label _title, _l1, _l2, _l3;
        private Material _lineMat;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<FenceBuilder>() != null) return;
            var go = new GameObject("FenceBuilder");
            DontDestroyOnLoad(go);
            s_instance = go.AddComponent<FenceBuilder>();
        }

        private void Awake() { s_instance = this; }

        /// <summary>Esc while a fence is being planned throws the plan away (HudBindings calls this).</summary>
        public static bool CancelPlan()
        {
            if (s_instance == null || s_instance._posts.Count == 0) return false;
            s_instance.Reset();
            return true;
        }

        // ------------------------------------------------------------------ the loop

        private void Update()
        {
            if (WelcomeMenuController.IsLoading) { HidePreview(); return; }
            string held = ConstructionSite.HeldItem();
            AssetCatalogItem item = held != null ? HudBindings.GetCatalogItem(held) : null;
            bool fence = item != null && !string.IsNullOrEmpty(item.fence_style);
            bool gate = item != null && item.gate_width_m > 0f;
            if (_posts.Count > 0 && (!fence || held != _panelId)) Reset();     // another item was chosen: the plan is dropped
            if (!fence && !gate) { HidePreview(); return; }

            Mouse mouse = Mouse.current;
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            HudBindings hud = HudBindings.Instance;
            if (mouse == null || cam == null || hud == null) { HidePreview(); return; }
            Vector2 pointer = mouse.position.ReadValue();
            if (hud.IsPointerOverUI(pointer) || HudBindings.KeyboardCaptured) { HidePreview(); return; }
            Ray ray = cam.ScreenPointToRay(pointer);
            if (!GroundPoint(ray, out Vector3 ground)) { HidePreview(); return; }

            bool click = mouse.leftButton.wasPressedThisFrame;
            if (fence) FenceMode(item, held, ground, click);
            else GateMode(item, ray, click);
        }

        private static bool GroundPoint(Ray ray, out Vector3 point)
        {
            point = default;
            if (Physics.Raycast(ray, out RaycastHit hit, 2000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore)) { point = hit.point; return true; }
            var plane = new Plane(Vector3.up, Vector3.zero);
            if (plane.Raycast(ray, out float t)) { point = ray.GetPoint(t); return true; }
            return false;
        }

        private static Vector3 Snap(Vector3 p)
        {
            float x = Mathf.Round(p.x / SnapMetres) * SnapMetres, z = Mathf.Round(p.z / SnapMetres) * SnapMetres;
            return new Vector3(x, TerrainHeightDetector.GetGroundY(x, z), z);
        }

        // ------------------------------------------------------------------ fence mode

        private void FenceMode(AssetCatalogItem item, string held, Vector3 ground, bool click)
        {
            _panelId = held;
            Vector3 spot = Snap(ground);
            bool nearFirst = _posts.Count >= 3 && Vector2.Distance(new Vector2(spot.x, spot.z), new Vector2(_posts[0].x, _posts[0].z)) < CloseDistance;
            string why = nearFirst ? null : WhyNot(spot);
            bool valid = why == null;

            var keyboard = Keyboard.current;
            if (keyboard != null && keyboard.backspaceKey.wasPressedThisFrame && _posts.Count > 0) _posts.RemoveAt(_posts.Count - 1);
            if (keyboard != null && keyboard.enterKey.wasPressedThisFrame && _posts.Count >= 2) { TryComplete(item, false); return; }

            if (click)
            {
                if (nearFirst) { TryComplete(item, true); return; }
                if (valid && _posts.Count < MaxPosts) _posts.Add(spot);
                else if (why != null) ToastNotificationSystem.ShowInfo("Fence", why);
            }
            DrawPlan(spot, valid || nearFirst, nearFirst);
            ShowPanel(item, spot, nearFirst);
        }

        private string WhyNot(Vector3 spot)
        {
            if (!LandOwnershipSystem.IsOwned(spot.x, spot.z)) return "You can only build a fence on land you own.";
            if (spot.y < TerrainHeightDetector.GetWaterY() + 0.05f) return "You can't put a fence post in water.";
            if (_posts.Count > 0 && Vector2.Distance(new Vector2(spot.x, spot.z), new Vector2(_posts[_posts.Count - 1].x, _posts[_posts.Count - 1].z)) < 0.45f)
                return "That is too close to the last post.";
            if (_posts.Count >= MaxPosts) return "That fence has as many posts as one fence can.";
            return null;
        }

        private void TryComplete(AssetCatalogItem item, bool closed)
        {
            float panelLen = Mathf.Max(0.5f, item.fence_panel_m);
            FenceRun.Needs(_posts, closed, panelLen, out int postsNeeded, out int panelsNeeded);
            string postId = string.IsNullOrEmpty(item.fence_post_item) ? "post_wood_round_6inch" : item.fence_post_item;
            int havePanels = CountInToolbar(_panelId), havePosts = CountInToolbar(postId);
            if (havePanels < panelsNeeded || havePosts < postsNeeded)
            {
                ToastNotificationSystem.ShowWarning("Not enough materials",
                    $"This fence needs {panelsNeeded} x {HudBindings.GetItemName(_panelId)} (you have {havePanels}) and {postsNeeded} x {HudBindings.GetItemName(postId)} (you have {havePosts}).");
                return;
            }
            var ped = FindAnyObjectByType<PedController>();
            bool inside = false;
            if (closed && ped != null)
            {
                var probe = FenceRun.Create(item.fence_style, _panelId, postId, panelLen, item.fence_height_m > 0f ? item.fence_height_m : 1.2f, _posts, true, null);
                inside = probe.Encloses(ped.transform.position);
                Destroy(probe.gameObject);
            }
            if (inside && !HasGateInToolbar())
            {
                string panelId = _panelId;
                var plan = new List<Vector3>(_posts);
                HudBindings.Instance.ShowModal("You would be stuck inside",
                    "You are standing inside this fence and have no gate in your hotbar. Once it is built nothing lets you out. Build it anyway?",
                    () => Build(item, panelId, postId, plan, true, panelsNeeded, postsNeeded),
                    null, "Build it anyway", "Keep editing");
                return;
            }
            Build(item, _panelId, postId, new List<Vector3>(_posts), closed, panelsNeeded, postsNeeded);
        }

        private void Build(AssetCatalogItem item, string panelId, string postId, List<Vector3> posts, bool closed, int panels, int postCount)
        {
            // the plan may have changed while a confirmation was open: check what is there again
            if (CountInToolbar(panelId) < panels || CountInToolbar(postId) < postCount) { ToastNotificationSystem.ShowWarning("Not enough materials", "The materials are no longer in your hotbar."); return; }
            TakeFromToolbar(panelId, panels);
            TakeFromToolbar(postId, postCount);
            FenceRun.Create(item.fence_style, panelId, postId, Mathf.Max(0.5f, item.fence_panel_m), item.fence_height_m > 0f ? item.fence_height_m : 1.2f, posts, closed, null);
            Reset();
            HudBindings.Instance?.RefreshToolbar();
        }

        // ------------------------------------------------------------------ gate mode

        private void GateMode(AssetCatalogItem item, Ray ray, bool click)
        {
            FenceRun best = null;
            int bestSeg = -1;
            float bestS = 0f, bestD = float.MaxValue;
            foreach (FenceRun run in FenceRun.All)
                if (run != null && run.NearestSegment(ray, 0.9f, out int seg, out float s, out float d) && d < bestD) { best = run; bestSeg = seg; bestS = s; bestD = d; }
            if (best == null) { HidePreview(); return; }

            best.SegmentEnds(bestSeg, out Vector3 a, out Vector3 b);
            float len = FenceRun.Flat(a, b);
            float w = item.gate_width_m;
            float s0 = Mathf.Clamp(bestS, w * 0.5f + 0.2f, Mathf.Max(w * 0.5f + 0.2f, len - w * 0.5f - 0.2f));
            bool fits = len >= w + 0.4f;
            foreach (FenceRun.Gate g in best.Gates)
                if (g.Segment == bestSeg && Mathf.Abs(g.S - s0) < (g.Width + w) * 0.5f + 0.1f) fits = false;

            // a bright bar where the gate would stand
            Vector3 from = PointOn(a, b, s0 - w * 0.5f, len), to = PointOn(a, b, s0 + w * 0.5f, len);
            EnsureLine();
            _line.positionCount = 2;
            _line.SetPosition(0, from + Vector3.up * 0.2f);
            _line.SetPosition(1, to + Vector3.up * 0.2f);
            _line.startColor = _line.endColor = fits ? new Color(1f, 0.85f, 0.2f) : new Color(1f, 0.25f, 0.2f);
            _line.enabled = true;
            ClearMarkers();
            if (_panel != null) _panel.style.display = DisplayStyle.None;

            if (!click) return;
            if (!fits) { ToastNotificationSystem.ShowInfo("Gate", "There is not enough room for a gate there."); return; }
            HudState hud = HudState.Active;
            if (hud == null || !hud.ConsumeFromSelectedSlot(1)) return;
            HudBindings.Instance?.RefreshToolbar();
            string held = ConstructionSite.HeldItem();
            best.AddGate(new FenceRun.Gate { Segment = bestSeg, S = s0, Width = w, ItemId = item.id, Style = string.IsNullOrEmpty(item.gate_style) ? "wood" : item.gate_style });
        }

        private static Vector3 PointOn(Vector3 a, Vector3 b, float s, float len)
        {
            float t = len > 0.0001f ? Mathf.Clamp01(s / len) : 0f;
            float x = Mathf.Lerp(a.x, b.x, t), z = Mathf.Lerp(a.z, b.z, t);
            return new Vector3(x, TerrainHeightDetector.GetGroundY(x, z), z);
        }

        /// <summary>A right click on a gate opens or shuts it. True when the ray was on one.</summary>
        public static bool TryToggleGate(Ray ray, Transform player)
        {
            foreach (FenceRun run in FenceRun.All)
            {
                if (run == null || run.Gates.Count == 0) continue;
                if (!run.NearestSegment(ray, 0.9f, out int seg, out float s, out float d)) continue;
                foreach (FenceRun.Gate g in run.Gates)
                {
                    if (g.Segment != seg || Mathf.Abs(g.S - s) > g.Width * 0.5f + 0.35f) continue;
                    run.SegmentEnds(seg, out Vector3 a, out Vector3 b);
                    Vector3 mid = PointOn(a, b, g.S, FenceRun.Flat(a, b));
                    if (player != null && Vector2.Distance(new Vector2(player.position.x, player.position.z), new Vector2(mid.x, mid.z)) > 4f)
                    {
                        ToastNotificationSystem.ShowInfo("Too far", "Move closer to the gate.");
                        return true;
                    }
                    run.ToggleGate(g, player != null ? player.position : mid);
                    return true;
                }
            }
            return false;
        }

        // ------------------------------------------------------------------ the hotbar

        private static int CountInToolbar(string id)
        {
            HudState hud = HudState.Active;
            int n = 0;
            if (hud == null || string.IsNullOrEmpty(id)) return 0;
            hud.EnsureToolbarSlots();
            foreach (ToolbarSlotData s in hud.Toolbar) if (s.IconId == id && s.Count > 0) n += s.Count;
            return n;
        }

        private static bool HasGateInToolbar()
        {
            HudState hud = HudState.Active;
            if (hud == null) return false;
            foreach (ToolbarSlotData s in hud.Toolbar)
            {
                if (string.IsNullOrEmpty(s.IconId) || s.Count <= 0) continue;
                AssetCatalogItem it = HudBindings.GetCatalogItem(s.IconId);
                if (it != null && it.gate_width_m > 0f) return true;
            }
            return false;
        }

        private static void TakeFromToolbar(string id, int count)
        {
            HudState hud = HudState.Active;
            if (hud == null) return;
            for (int i = 0; i < hud.Toolbar.Count && count > 0; i++)
            {
                ToolbarSlotData s = hud.Toolbar[i];
                if (s.IconId != id || s.Count <= 0) continue;
                int take = Mathf.Min(count, s.Count);
                s.Count -= take;
                count -= take;
                hud.Toolbar[i] = s.Count <= 0 ? ToolbarSlotData.Empty() : s;
            }
            hud.SelectSlot(hud.SelectedSlot);
        }

        // ------------------------------------------------------------------ the picture

        private void Reset()
        {
            _posts.Clear();
            _panelId = null;
            HidePreview();
        }

        private void EnsureLine()
        {
            if (_line != null) return;
            var go = new GameObject("FencePlan");
            go.transform.SetParent(transform, false);
            _line = go.AddComponent<LineRenderer>();
            _line.useWorldSpace = true;
            _line.widthMultiplier = 0.14f;
            _line.numCapVertices = 2;
            _lineMat = new Material(Shader.Find("Sprites/Default")) { hideFlags = HideFlags.DontSave };
            _line.sharedMaterial = _lineMat;
            _line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _line.sortingOrder = 10;
        }

        private void DrawPlan(Vector3 cursor, bool valid, bool closing)
        {
            EnsureLine();
            int n = _posts.Count;
            var pts = new List<Vector3>();
            foreach (Vector3 p in _posts) pts.Add(p + Vector3.up * 0.2f);
            if (n > 0) pts.Add(closing ? _posts[0] + Vector3.up * 0.2f : cursor + Vector3.up * 0.2f);
            _line.enabled = pts.Count >= 2;
            _line.positionCount = pts.Count;
            for (int i = 0; i < pts.Count; i++) _line.SetPosition(i, pts[i]);
            Color c = closing ? new Color(0.3f, 1f, 0.5f) : valid ? new Color(0.35f, 0.85f, 1f) : new Color(1f, 0.3f, 0.25f);
            _line.startColor = _line.endColor = c;

            // a marker on every post (and on the spot the next one would go), the first one larger
            ClearMarkers();
            var spots = new List<Vector3>(_posts);
            spots.Add(cursor);
            for (int i = 0; i < spots.Count; i++)
            {
                GameObject m = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                Destroy(m.GetComponent<Collider>());
                m.transform.SetParent(transform, false);
                m.transform.position = spots[i] + Vector3.up * 0.55f;
                float r = (i == 0 && n > 0) ? 0.3f : 0.18f;
                m.transform.localScale = new Vector3(r, 0.55f, r);
                var rend = m.GetComponent<Renderer>();
                rend.sharedMaterial = _lineMat;
                rend.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                rend.material.color = i == spots.Count - 1 ? c : new Color(0.9f, 0.9f, 0.9f, 1f);
                _markers.Add(m);
            }
        }

        private void ClearMarkers()
        {
            foreach (GameObject m in _markers) if (m != null) Destroy(m);
            _markers.Clear();
        }

        private void HidePreview()
        {
            if (_line != null) _line.enabled = false;
            ClearMarkers();
            if (_panel != null) _panel.style.display = DisplayStyle.None;
        }

        private void ShowPanel(AssetCatalogItem item, Vector3 cursor, bool closing)
        {
            UIDocument doc = FindAnyObjectByType<UIDocument>();
            VisualElement root = doc != null ? doc.rootVisualElement : null;
            if (root == null) return;
            if (_panel == null || _panel.parent != root)
            {
                _panel?.RemoveFromHierarchy();
                _panel = new VisualElement { name = "FencePlanCard", pickingMode = PickingMode.Ignore };
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
            var plan = new List<Vector3>(_posts);
            if (!closing && plan.Count > 0) plan.Add(cursor);
            FenceRun.Needs(plan, closing && _posts.Count >= 3, Mathf.Max(0.5f, item.fence_panel_m), out int postsNeeded, out int panelsNeeded);
            string postId = string.IsNullOrEmpty(item.fence_post_item) ? "post_wood_round_6inch" : item.fence_post_item;
            _title.text = item.name;
            _l1.text = $"{HudBindings.GetItemName(_panelId)}: {panelsNeeded} of {CountInToolbar(_panelId)}";
            _l2.text = $"{HudBindings.GetItemName(postId)}: {postsNeeded} of {CountInToolbar(postId)}";
            _l3.text = _posts.Count == 0 ? "Click to place the first post"
                     : closing ? "Click to close the fence"
                     : _posts.Count < 3 ? "Click to add posts, Enter finishes a line, Backspace undoes"
                     : "Click the first post to close it, Enter finishes a line";
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
