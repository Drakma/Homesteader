using System.Collections.Generic;
using System.Text;
using Homesteader.Growth;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// The hover card of a construction site (its own panel, not the look-at panel): beside the cursor while it is over the dirt
    /// area or the structure it shows the structure's name and stage, every material of the stage as have / need (teal when
    /// complete), every tool group as Ready or Missing, and what to do next. Styles: HudUI.uss (construction-hover-*).
    /// The look-at panel (F3) stays quiet over a site.
    /// </summary>
    public sealed class ConstructionHover : MonoBehaviour
    {
        // Two cards share all the filling code: the hover card beside the cursor, and the pinned one (key P over a site) that stays at the
        // right of the viewport and keeps updating while you gather the materials.
        private sealed class Card
        {
            public VisualElement Panel;
            public string Shown;
            public readonly List<Rotation> Rotations = new List<Rotation>();
            public VisualElement BarFill;
            public Label BarValue;
        }
        private readonly Card _hover = new Card();
        private readonly Card _pin = new Card();
        private Card _cur;
        private ConstructionSite _pinned;
        private VisualElement _panel { get { return _cur.Panel; } set { _cur.Panel = value; } }
        private string _shown { get { return _cur.Shown; } set { _cur.Shown = value; } }
        private List<Rotation> _rotations { get { return _cur.Rotations; } }

        // A "#tag" line (any of several items will do) cycles through its member items, name and icon, like the look-at panel does for
        // tools. Holding Shift stops it so one can be read.
        private sealed class Rotation { public Image Icon; public Label Name; public List<string> Items; public string Spec; public int Quantity; public int Shown = -1; }
        private float _rotationClock;
        private const float SecondsPerItem = 1.6f;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<ConstructionHover>() != null) return;
            var go = new GameObject("ConstructionHover");
            DontDestroyOnLoad(go);
            go.AddComponent<ConstructionHover>();
        }

        private void Update()
        {
            ConstructionSite site = WelcomeMenuController.IsLoading ? null : SiteUnderPointer();

            // P over a site pins its list (P again, anywhere, unpins it)
            Keyboard kb = Keyboard.current;
            if (kb != null && kb.pKey.wasPressedThisFrame && !HudBindings.KeyboardCaptured)
            {
                _pinned = _pinned != null ? null : site;
                if (_pinned != null) RememberPin(_pinned); else ForgetPin();
            }
            // The pin outlives the session: it is kept in PlayerPrefs (by the site's spot) and found again whenever the sites exist,
            // however they came back (a load, Continue, a new Play). It is let go only by P, or when its site is finished or removed.
            // It is NOT forgotten when the site object disappears: that also happens when the game stops or a save is loading, and
            // that is exactly when it has to survive. Only P, a finished structure or a removed site (ForgetPinAt) let it go.
            if (_pinned == null && PlayerPrefs.HasKey(PinSiteKey) && !WelcomeMenuController.IsLoading) _pinned = FindSavedPin();
            if (_pinned != null && (_pinned.Finished || !_pinned.isActiveAndEnabled)) _pinned = null;   // gone for now (kept in PlayerPrefs; found again later)

            _cur = _pin;
            EnsureBuilt(true);
            if (_panel != null)
            {
                if (_pinned == null) _panel.style.display = DisplayStyle.None;
                else
                {
                    Fill(_pinned, true);
                    UpdateBar(_pinned);
                    RotateTags();
                    _panel.style.display = DisplayStyle.Flex;
                }
            }

            _cur = _hover;
            if (site == null || site == _pinned) { Hide(); return; }
            EnsureBuilt(false);
            if (_panel == null) return;
            Fill(site, false);
            UpdateBar(site);
            RotateTags();
            _panel.style.display = DisplayStyle.Flex;
            Place();
        }

        private static ConstructionSite SiteUnderPointer()
        {
            HudBindings hud = HudBindings.Instance;
            Mouse mouse = Mouse.current;
            if (hud == null || mouse == null || HudBindings.KeyboardCaptured) return null;
            if (hud.IsPointerOverUI(mouse.position.ReadValue())) return null;
            ConstructionSite site = ConstructionSite.UnderCursor();
            return site != null && site.Finished ? null : site;   // a finished structure is a normal building: the look-at panel names it
        }

        /// <summary>Moves the build progress bar of the current card (if it shows one) to the site's progress.</summary>
        private void UpdateBar(ConstructionSite site)
        {
            if (_cur.BarFill == null || !site.Building) return;
            float p = site.BuildProgress;
            _cur.BarFill.style.width = Length.Percent(p * 100f);
            _cur.BarValue.text = Mathf.RoundToInt(p * 100f) + "%";
        }

        private const string PinXKey = "construction_pin_x", PinYKey = "construction_pin_y";
        private const string PinSiteKey = "construction_pin_site";

        private static void RememberPin(ConstructionSite site)
        {
            Vector3 p = site.transform.position;
            PlayerPrefs.SetString(PinSiteKey, p.x.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture) + "," + p.z.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture));
            PlayerPrefs.Save();
        }

        /// <summary>A pinned site that was finished or removed on purpose: let the pin go (called by ConstructionSite).</summary>
        public static void ForgetPinAt(Vector3 sitePosition)
        {
            string[] f = PlayerPrefs.GetString(PinSiteKey, "").Split(',');
            if (f.Length != 2
                || !float.TryParse(f[0], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float x)
                || !float.TryParse(f[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float z)) return;
            if ((sitePosition.x - x) * (sitePosition.x - x) + (sitePosition.z - z) * (sitePosition.z - z) < 0.25f) ForgetPin();
        }

        private static void ForgetPin()
        {
            if (!PlayerPrefs.HasKey(PinSiteKey)) return;
            PlayerPrefs.DeleteKey(PinSiteKey);
            PlayerPrefs.Save();
        }

        /// <summary>The site standing where the pinned one stood (within half a metre), or null while the sites are not back yet.</summary>
        private static ConstructionSite FindSavedPin()
        {
            string[] f = PlayerPrefs.GetString(PinSiteKey, "").Split(',');
            if (f.Length != 2
                || !float.TryParse(f[0], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float x)
                || !float.TryParse(f[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float z)) return null;
            foreach (ConstructionSite c in ConstructionSite.All)
            {
                if (c == null || c.Finished) continue;
                Vector3 p = c.transform.position;
                if ((p.x - x) * (p.x - x) + (p.z - z) * (p.z - z) < 0.25f) return c;
            }
            return null;
        }

        /// <summary>The pinned card can be dragged anywhere in the window; where it is left is remembered.</summary>
        private static void MakeDraggable(VisualElement panel)
        {
            panel.pickingMode = PickingMode.Position;
            if (PlayerPrefs.HasKey(PinXKey))
            {
                panel.style.right = StyleKeyword.Auto;
                panel.style.left = PlayerPrefs.GetFloat(PinXKey);
                panel.style.top = PlayerPrefs.GetFloat(PinYKey);
            }
            Vector2 grab = Vector2.zero;
            bool dragging = false;
            panel.RegisterCallback<PointerDownEvent>(e =>
            {
                if (e.button != 0) return;
                dragging = true;
                grab = (Vector2)e.position - new Vector2(panel.resolvedStyle.left, panel.resolvedStyle.top);
                if (float.IsNaN(grab.x)) grab = Vector2.zero;
                panel.CapturePointer(e.pointerId);
                e.StopPropagation();
            });
            panel.RegisterCallback<PointerMoveEvent>(e =>
            {
                if (!dragging) return;
                VisualElement root = panel.parent;
                float maxX = root != null ? root.resolvedStyle.width - panel.resolvedStyle.width : 1900f;
                float maxY = root != null ? root.resolvedStyle.height - panel.resolvedStyle.height : 1000f;
                panel.style.right = StyleKeyword.Auto;
                panel.style.left = Mathf.Clamp(e.position.x - grab.x, 0f, Mathf.Max(0f, maxX));
                panel.style.top = Mathf.Clamp(e.position.y - grab.y, 0f, Mathf.Max(0f, maxY));
                e.StopPropagation();
            });
            panel.RegisterCallback<PointerUpEvent>(e =>
            {
                if (!dragging) return;
                dragging = false;
                panel.ReleasePointer(e.pointerId);
                PlayerPrefs.SetFloat(PinXKey, panel.resolvedStyle.left);
                PlayerPrefs.SetFloat(PinYKey, panel.resolvedStyle.top);
                e.StopPropagation();
            });
        }

        private void Hide()
        {
            if (_panel != null) _panel.style.display = DisplayStyle.None;
        }

        private void EnsureBuilt(bool pinned)
        {
            UIDocument doc = FindAnyObjectByType<UIDocument>();
            VisualElement root = doc != null ? doc.rootVisualElement : null;
            if (root == null) return;
            if (_panel != null && _panel.parent == root) return;
            _panel?.RemoveFromHierarchy();
            _panel = new VisualElement { name = "ConstructionHover", pickingMode = PickingMode.Ignore };
            _panel.AddToClassList("construction-hover");
            if (pinned)
            {
                _panel.AddToClassList("construction-hover--pinned");
                MakeDraggable(_panel);
            }
            _panel.style.display = DisplayStyle.None;
            var edge = new VisualElement { pickingMode = PickingMode.Ignore };
            edge.AddToClassList("hs-accent-edge");
            _panel.Add(edge);
            // Index 0: the welcome menu (added later) covers it.
            root.Insert(0, _panel);
            _shown = null;
        }

        private void Fill(ConstructionSite site, bool pinned)
        {
            var key = new StringBuilder();
            key.Append(site.GetHashCode()).Append('|').Append(site.Stage).Append(pinned ? 'P' : 'H');
            if (site.Building) key.Append("|b");
            List<ConstructionSite.LineStatus> lines = site.Lines;
            List<ConstructionSite.ToolStatus> tools = site.Tools;
            foreach (ConstructionSite.LineStatus l in lines)
            {
                key.Append('|').Append(l.Have).Append(l.Chosen);
                if (l.IsChoice) foreach (ConstructionSite.LineStatus o in l.Options) key.Append('/').Append(o.Have);
            }
            foreach (ConstructionSite.ToolStatus t in tools) { key.Append('|').Append(t.Have ? 1 : 0); foreach (string pt in t.Present) key.Append(pt.GetHashCode()); }
            string k = key.ToString();
            if (k == _shown) return;
            _shown = k;

            // keep the accent edge (child 0), rebuild the rest
            while (_panel.childCount > 1) _panel[1].RemoveFromHierarchy();
            _rotations.Clear();

            var title = new Label(site.Name()) { pickingMode = PickingMode.Ignore };
            title.AddToClassList("construction-hover-title");
            _panel.Add(title);

            if (site.Finished)
            {
                _panel.Add(Text("Finished", "construction-hover-sub"));
                return;
            }
            ConstructionStageData stage = site.CurrentStage;
            _panel.Add(Text($"{StageName(stage)}  ({site.Stage + 1} of {site.StageCount})", "construction-hover-sub"));

            if (lines.Count > 0) _panel.Add(Text("Materials", "construction-hover-section"));
            foreach (ConstructionSite.LineStatus l in lines)
            {
                if (!l.IsChoice)
                {
                    _panel.Add(Row(l.Line.item_id, ConstructionSite.LineName(l.Line.item_id), Count(l.Line, l.Have), l.Done, l.Line.quantity));
                    continue;
                }
                // an "or" line: either alternative will do, each listed with its own count
                _panel.Add(Row(null, "Either of these:", l.Done ? "Ready" : "Missing", l.Done));
                for (int oi = 0; oi < l.Options.Count; oi++)
                {
                    ConstructionSite.LineStatus o = l.Options[oi];
                    if (oi > 0) { var orLabel = Text("or", "construction-hover-or"); orLabel.AddToClassList("construction-hover-row--indent"); _panel.Add(orLabel); }
                    VisualElement optRow = Row(o.Line.item_id, ConstructionSite.LineName(o.Line.item_id), Count(o.Line, o.Have), o.Done, o.Line.quantity);
                    optRow.AddToClassList("construction-hover-row--indent");
                    _panel.Add(optRow);
                }
            }

            if (tools.Count > 0) _panel.Add(Text("Tools", "construction-hover-section"));
            int groupNo = 0;
            foreach (ConstructionSite.ToolStatus t in tools)
            {
                groupNo++;
                // the group: "any one of these", met or not, then every tool of it on its own line (ticked when it is there)
                _panel.Add(Row(null, tools.Count > 1 ? $"Group {groupNo}: any one of" : "Any one of", t.Have ? "Ready" : "Missing", t.Have));
                foreach (string tool in t.Group.tools)
                {
                    VisualElement toolRow = Row(tool, ConstructionSite.LineName(tool), t.Present.Contains(tool) ? "Have" : "", t.Present.Contains(tool));
                    toolRow.AddToClassList("construction-hover-row--indent");
                    _panel.Add(toolRow);
                }
            }

            if (site.Building)
            {
                _panel.Add(Text("Building", "construction-hover-go"));
                var bar = new VisualElement { pickingMode = PickingMode.Ignore };
                bar.AddToClassList("construction-hover-bar");
                var track = new VisualElement { pickingMode = PickingMode.Ignore };
                track.AddToClassList("construction-hover-bar-track");
                _cur.BarFill = new VisualElement { pickingMode = PickingMode.Ignore };
                _cur.BarFill.AddToClassList("construction-hover-bar-fill");
                track.Add(_cur.BarFill);
                bar.Add(track);
                _cur.BarValue = new Label("0%") { pickingMode = PickingMode.Ignore };
                _cur.BarValue.AddToClassList("construction-hover-bar-value");
                bar.Add(_cur.BarValue);
                _panel.Add(bar);
                _panel.Add(Text("Move to stop", "construction-hover-hint"));
                return;
            }
            bool ready = site.Ready;
            _panel.Add(Text(ready ? "Right click to build the " + StageName(stage).ToLowerInvariant()
                                  : $"Place the materials within {UnitFormat.Distance(ConstructionSite.YardM)} of the foundation",
                            ready ? "construction-hover-go" : "construction-hover-hint"));
            if (pinned) { _panel.Add(Text("P to unpin this list", "construction-hover-hint")); return; }
            if (_pinned == null) _panel.Add(Text("P to pin this list to the screen", "construction-hover-hint"));
            if (site.Stage == 0)
            {
                _panel.Add(Text("The amber arrow marks the FRONT (the door side)", "construction-hover-hint"));
                _panel.Add(Text("Shift + right click to remove this site", "construction-hover-hint"));
            }
        }

        /// <summary>"3 / 8", or "12 / 20 studs" for a tag with a unit; never more than the quantity (what is over is spare).</summary>
        private static string Count(ConstructionLine line, int have)
        {
            string unit = GrowthRegistry.UnitName(line.item_id);
            return $"{Mathf.Min(have, line.quantity)} / {line.quantity}" + (string.IsNullOrEmpty(unit) ? "" : " " + unit);
        }

        private static string StageName(ConstructionStageData s)
        {
            string n = s != null ? s.name : "";
            return string.IsNullOrEmpty(n) ? "Stage" : char.ToUpperInvariant(n[0]) + n.Substring(1);
        }

        private static Label Text(string text, string cls)
        {
            var l = new Label(text) { pickingMode = PickingMode.Ignore };
            l.AddToClassList(cls);
            return l;
        }

        private static Texture2D _fade;

        /// <summary>A fixed-width box for a name: text that is too long is cut off with a fade into the card's colour (never wraps or widens the card).</summary>
        private static VisualElement NameBox(Label name)
        {
            if (_fade == null)
            {
                _fade = new Texture2D(16, 1, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, hideFlags = HideFlags.DontSave };
                for (int i = 0; i < 16; i++) _fade.SetPixel(i, 0, new Color(43f / 255f, 52f / 255f, 66f / 255f, Mathf.SmoothStep(0f, 1f, i / 15f)));   // --c-panel
                _fade.Apply();
            }
            var box = new VisualElement { pickingMode = PickingMode.Ignore };
            box.AddToClassList("construction-hover-name-box");
            box.Add(name);
            var fade = new VisualElement { pickingMode = PickingMode.Ignore };
            fade.AddToClassList("construction-hover-name-fade");
            fade.style.backgroundImage = _fade;
            box.Add(fade);
            return box;
        }

        private VisualElement Row(string itemId, string name, string value, bool done, int quantity = 0)
        {
            var row = new VisualElement { pickingMode = PickingMode.Ignore };
            row.AddToClassList("construction-hover-row");
            List<string> members = !string.IsNullOrEmpty(itemId) && itemId[0] == '#' ? GrowthRegistry.ToolItems(itemId) : null;
            if (members != null && members.Count > 1)
            {
                // a tag: the icon and name cycle through its members
                var rIcon = new Image { scaleMode = ScaleMode.ScaleToFit, pickingMode = PickingMode.Ignore };
                rIcon.AddToClassList("construction-hover-icon");
                row.Add(rIcon);
                var rName = new Label(name) { pickingMode = PickingMode.Ignore };
                rName.AddToClassList("construction-hover-name");
                row.Add(NameBox(rName));
                _rotations.Add(new Rotation { Icon = rIcon, Name = rName, Items = members, Spec = itemId, Quantity = quantity });
            }
            else if (!string.IsNullOrEmpty(itemId) && itemId[0] != '#')
            {
                Texture2D tex = PhoneController.GetItemIcon(null, itemId);
                if (tex != null)
                {
                    var icon = new Image { image = tex, scaleMode = ScaleMode.ScaleToFit, pickingMode = PickingMode.Ignore };
                    icon.AddToClassList("construction-hover-icon");
                    row.Add(icon);
                }
            }
            if (members == null || members.Count <= 1)
            {
                var n = new Label(name) { pickingMode = PickingMode.Ignore };
                n.AddToClassList("construction-hover-name");
                row.Add(NameBox(n));
            }
            var v = new Label(value) { pickingMode = PickingMode.Ignore };
            v.AddToClassList("construction-hover-value");
            v.EnableInClassList("construction-hover-value--done", done);
            v.EnableInClassList("construction-hover-value--missing", !done);
            row.Add(v);
            return row;
        }

        private void RotateTags()
        {
            if (_rotations.Count == 0) return;
            bool hold = Keyboard.current != null && Keyboard.current.shiftKey.isPressed;
            if (!hold) _rotationClock += Time.unscaledDeltaTime;
            int step = Mathf.FloorToInt(_rotationClock / SecondsPerItem);
            foreach (Rotation r in _rotations)
            {
                int index = step % r.Items.Count;
                if (index == r.Shown) continue;
                r.Shown = index;
                string id = r.Items[index];
                r.Name.text = HudBindings.GetItemName(id);
                if (r.Quantity > 0)
                {
                    // how many of this member alone would cover the quantity (a tag with equivalencies: 200 studs = 10 large bundles)
                    int each = Mathf.CeilToInt(r.Quantity / Mathf.Max(0.0001f, GrowthRegistry.UnitValue(r.Spec, id)) - 0.0001f);
                    r.Name.text = each + " x " + r.Name.text;
                }
                Texture2D tex = PhoneController.GetItemIcon(null, id);
                r.Icon.image = tex;
                r.Icon.style.display = tex != null ? DisplayStyle.Flex : DisplayStyle.None;
            }
        }

        /// <summary>Beside the pointer, kept inside the window.</summary>
        private void Place()
        {
            Mouse mouse = Mouse.current;
            if (mouse == null || _panel.panel == null) return;
            Vector2 screen = mouse.position.ReadValue();
            Vector2 p = RuntimePanelUtils.ScreenToPanel(_panel.panel, new Vector2(screen.x, Screen.height - screen.y));
            float w = Mathf.Max(220f, _panel.resolvedStyle.width), h = Mathf.Max(60f, _panel.resolvedStyle.height);
            VisualElement root = _panel.parent;
            float maxX = root != null ? root.resolvedStyle.width : 1920f, maxY = root != null ? root.resolvedStyle.height : 1080f;
            float x = p.x + 22f, y = p.y + 22f;
            if (x + w > maxX - 6f) x = p.x - 22f - w;
            if (y + h > maxY - 6f) y = maxY - 6f - h;
            _panel.style.left = Mathf.Max(6f, x);
            _panel.style.top = Mathf.Max(6f, y);
        }
    }
}
