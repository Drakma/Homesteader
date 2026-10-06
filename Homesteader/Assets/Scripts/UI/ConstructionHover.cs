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
            public ConstructionSite LastSite;
            public object LastLines;   // the evaluation the card was last checked against (it is a new list a few times a second)
            public readonly List<Rotation> Rotations = new List<Rotation>();
            public VisualElement BarFill;
            public Label BarValue;
        }
        private readonly Card _hover = new Card();
        private readonly Card _pin = new Card();
        private Card _cur;
        private ConstructionSite _pinned;
        private ConstructionSite _site;   // the site the card is showing (the choice buttons talk to it)
        private VisualElement _body;   // where the rows go (a scroll view on the pinned card)
        private ScrollView _scroll;    // the pinned card's list, when there is one
        private VisualElement _panel { get { return _cur.Panel; } set { _cur.Panel = value; } }
        private string _shown { get { return _cur.Shown; } set { _cur.Shown = value; if (value == null) _cur.LastLines = null; } }
        private List<Rotation> _rotations { get { return _cur.Rotations; } }

        // A "#tag" line (any of several items will do) cycles through its member items, name and icon, like the look-at panel does for
        // tools. Holding Shift stops it so one can be read.
        private sealed class Rotation { public Image Icon; public Label Name; public List<string> Items; public string Spec; public float Quantity; public int Shown = -1; public bool Struck; }
        private float _rotationClock;
        private const float SecondsPerItem = 1.6f;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            // the saved position of the pinned list is reset once per layout version (an old or off-screen position broke the card)
            if (PlayerPrefs.GetInt(LayoutVersionKey, 0) < LayoutVersion)
            {
                PlayerPrefs.DeleteKey(PinXKey);
                PlayerPrefs.DeleteKey(PinYKey);
                PlayerPrefs.SetInt(LayoutVersionKey, LayoutVersion);
                PlayerPrefs.Save();
            }
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
        private const string LayoutVersionKey = "construction_pin_layout";
        private const int LayoutVersion = 2;   // bump to reset every player's saved position of the pinned list
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
            if (PlayerPrefs.HasKey(PinXKey) && PlayerPrefs.GetFloat(PinXKey) >= 0f && PlayerPrefs.GetFloat(PinYKey) >= 0f && PlayerPrefs.GetFloat(PinXKey) < 3000f && PlayerPrefs.GetFloat(PinYKey) < 2000f)
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
                if (e.target is Button || (e.target is VisualElement tv && tv.GetFirstAncestorOfType<Button>() != null)) return;   // a button is clicked, not dragged by
                dragging = true;
                grab = (Vector2)e.position - new Vector2(panel.resolvedStyle.left, panel.resolvedStyle.top);
                if (float.IsNaN(grab.x)) grab = Vector2.zero;
                panel.CapturePointer(e.pointerId);
                e.StopPropagation();
            });
            panel.RegisterCallback<PointerCaptureOutEvent>(e => { dragging = false; });
            panel.RegisterCallback<PointerMoveEvent>(e =>
            {
                if (!dragging) return;
                if ((e.pressedButtons & 1) == 0) { dragging = false; panel.ReleasePointer(e.pointerId); return; }   // the button was let go outside the window: stop, never stay stuck
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
            List<ConstructionSite.LineStatus> evaluated = site.Lines;
            if (_shown != null && ReferenceEquals(_cur.LastLines, evaluated) && _cur.LastSite == site) return;   // nothing re-counted since: same card
            _cur.LastLines = evaluated;
            _cur.LastSite = site;
            var key = new StringBuilder();
            key.Append(site.GetHashCode()).Append('|').Append(site.Stage).Append(pinned ? 'P' : 'H');
            if (site.Building) key.Append("|b");
            key.Append("|s").Append(Mathf.RoundToInt(site.EstimatedBuildSeconds));
            List<ConstructionSite.LineStatus> lines = site.Lines;
            List<ConstructionSite.ToolStatus> tools = site.Tools;
            foreach (ConstructionSite.LineStatus l in lines) KeyNode(key, l);
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
            _site = site;
            _panel.Add(Text($"{StageName(stage)}  ({site.Stage + 1} of {site.StageCount})", "construction-hover-sub"));
            // the reset button, up top: forget the choices of this stage so the questions are asked again
            if (pinned && !site.Building && site.HasChoices())
            {
                var reset = new Button(() => { site.ResetChoices(); _shown = null; }) { text = "Reset choices" };
                reset.AddToClassList("construction-hover-reset");
                _panel.Add(reset);
            }

            // the build progress bar sits at the top, under the title
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
            }

            // the list: a pinned card scrolls when it is long (the title, the bar and the hints stay put)
            _pinnedNow = pinned;
            VisualElement body;
            if (pinned)
            {
                var scroll = new ScrollView(ScrollViewMode.Vertical) { pickingMode = PickingMode.Position };
                scroll.horizontalScrollerVisibility = ScrollerVisibility.Hidden;
                scroll.RegisterCallback<PointerDownEvent>(e => e.StopPropagation());   // the card is dragged by its title, not by the list
                VisualElement rootEl = _panel.parent;
                float rootH = rootEl != null && !float.IsNaN(rootEl.resolvedStyle.height) && rootEl.resolvedStyle.height > 200f ? rootEl.resolvedStyle.height : 900f;
                scroll.style.maxHeight = rootH * 0.6f;
                scroll.style.flexShrink = 1;
                scroll.contentContainer.style.flexShrink = 0;
                body = scroll;
                _scroll = scroll;
            }
            else { body = new VisualElement { pickingMode = PickingMode.Ignore }; _scroll = null; }
            body.AddToClassList("construction-hover-scroll");
            _body = body;
            _panel.Add(body);

            if (lines.Count > 0) _body.Add(Text("Materials", "construction-hover-section"));
            foreach (ConstructionSite.LineStatus l in lines) AddNode(l, 0);

            if (tools.Count > 0) _body.Add(Text("Tools", "construction-hover-section"));
            int groupNo = 0;
            foreach (ConstructionSite.ToolStatus t in tools)
            {
                groupNo++;
                // the group: "any one of these", met or not, then every tool of it on its own line (ticked when it is there)
                _body.Add(Row(null, tools.Count > 1 ? $"Group {groupNo}: any one of" : "Any one of", t.Have ? "Ready" : "Missing", t.Have));
                foreach (string tool in t.Group.tools)
                {
                    VisualElement toolRow = Row(tool, ConstructionSite.LineName(tool), t.Present.Contains(tool) ? "Have" : t.Unpowered.Contains(tool) ? "No power" : "", t.Present.Contains(tool));
                    toolRow.AddToClassList("construction-hover-row--indent");
                    _body.Add(toolRow);
                }
            }

            if (site.Building)
            {
                _panel.Add(Text("Move to stop", "construction-hover-hint"));
                if (pinned) KeepOnScreen();
                return;
            }
            bool ready = site.Ready;
            if (tools.Count > 0) _panel.Add(Text("Build time with these tools: " + BuildTimeText(site.EstimatedBuildSeconds), "construction-hover-hint"));
            _panel.Add(Text(ready ? "Right click to build the " + StageName(stage).ToLowerInvariant()
                                  : $"Place the materials within {UnitFormat.Distance(ConstructionSite.YardM)} of the foundation",
                            ready ? "construction-hover-go" : "construction-hover-hint"));
            if (pinned) { _panel.Add(Text("P to unpin this list", "construction-hover-hint")); KeepOnScreen(); return; }
            if (_pinned == null) _panel.Add(Text("P to pin this list to the screen", "construction-hover-hint"));
            if (site.Stage == 0)
            {
                _panel.Add(Text("The amber arrow marks the FRONT (the door side)", "construction-hover-hint"));
                _panel.Add(Text("Shift + right click to remove this site", "construction-hover-hint"));
            }
        }

        private static string BuildTimeText(float seconds)
        {
            int s = Mathf.RoundToInt(seconds);
            return s >= 60 ? (s / 60) + " min" + (s % 60 > 0 ? " " + (s % 60) + " s" : "") : s + " s";
        }

        private static void KeyNode(StringBuilder key, ConstructionSite.LineStatus l)
        {
            key.Append('|').Append(l.Have).Append(l.Chosen).Append(l.PickedIndex).Append(l.Unresolved ? 'u' : 'r').Append(l.Active ? 'a' : 'i');
            if (l.Children != null) foreach (ConstructionSite.LineStatus c in l.Children) KeyNode(key, c);
        }

        private static string SpecText(string spec) => ConstructionSite.LineName(spec);

        /// <summary>One node of the materials tree: a line as a row, a section as a header (its mode, its condition) with its children indented under it.</summary>
        private void AddNode(ConstructionSite.LineStatus n, int depth)
        {
            if (n.Children == null)
            {
                VisualElement row = Row(n.Line.item_id, ConstructionSite.LineName(n.Line.item_id), Count(n.Line, n.Have, n.Needed), n.Done, n.Needed);
                Indent(row, depth);
                _body.Add(row);
                return;
            }
            ConstructionLine sec = n.Line;
            if (n.Any && n.Active)
            {
                if (n.Unresolved) { AddQuestion(n, depth); return; }
                // a chosen option: only that option is on the list
                if (n.Children.Count > 0) AddNode(n.Children[0], depth);
                return;
            }
            string title = string.IsNullOrEmpty(sec.section) ? null : sec.section;
            string cond = null;
            if (!string.IsNullOrEmpty(sec.uses)) cond = "If using " + SpecText(sec.uses);
            if (!string.IsNullOrEmpty(sec.not_uses)) cond = (cond == null ? "" : cond + ", and ") + "If not using " + SpecText(sec.not_uses);
            string head = cond != null ? (title != null ? title + ": " + cond : cond + ":") : (n.Any ? (title != null ? title + ": either of these" : "Either of these:") : title);
            if (head != null)
            {
                VisualElement hr = Row(null, head, !n.Active ? "Not needed" : (n.Done ? "Ready" : "Missing"), n.Done);
                Indent(hr, depth);
                if (!n.Active) hr.style.opacity = 0.5f;
                _body.Add(hr);
            }
            int childDepth = head != null ? depth + 1 : depth;
            for (int i = 0; i < n.Children.Count; i++)
            {
                if (n.Any && i > 0)
                {
                    Label orLabel = Text("or", "construction-hover-or");
                    Indent(orLabel, childDepth);
                    _body.Add(orLabel);
                }
                int before = _body.childCount;
                AddNode(n.Children[i], childDepth);
                if (!n.Active) for (int c = before; c < _body.childCount; c++) _body[c].style.opacity = 0.5f;
            }
        }

        /// <summary>A question: an "any" section the player has not chosen an option of yet. The pinned card shows one button per option; the hover card says to pin.</summary>
        private void AddQuestion(ConstructionSite.LineStatus n, int depth)
        {
            ConstructionLine sec = n.Line;
            string title = string.IsNullOrEmpty(sec.section) ? "Choose one" : sec.section;
            Label q = Text(title + "?", "construction-hover-section");
            Indent(q, depth);
            _body.Add(q);
            for (int i = 0; i < sec.items.Count; i++)
            {
                int option = i;
                string label = ConstructionSite.OptionLabel(sec.items[i]);
                if (_pinnedNow && _site != null)
                {
                    string path = n.Path;
                    ConstructionSite site = _site;
                    var b = new Button(() => { site.Choose(path, option); _shown = null; }) { text = label };
                    b.AddToClassList("construction-hover-choice");
                    Indent(b, depth);
                    _body.Add(b);
                }
                else
                {
                    Label l = Text("  " + label, "construction-hover-name");
                    Indent(l, depth);
                    _body.Add(l);
                }
            }
            if (!_pinnedNow)
            {
                Label hint = Text("Press P to pin this list, then choose", "construction-hover-hint");
                Indent(hint, depth);
                _body.Add(hint);
            }
        }

        private bool _pinnedNow;   // the card being filled is the pinned one (its buttons can be clicked)

        /// <summary>Strikes the text of a row through and dims it (an alternative that is no longer needed).</summary>
        private static void Strike(VisualElement e)
        {
            e.style.opacity = 0.5f;
            foreach (Label l in e.Query<Label>().ToList())
                if (!string.IsNullOrEmpty(l.text) && !l.text.StartsWith("<s>")) l.text = "<s>" + l.text + "</s>";
        }

        /// <summary>After the layout settles, moves the pinned card back inside the window when it was left (or has grown) past an edge.</summary>
        private void KeepOnScreen()
        {
            VisualElement panel = _panel;   // captured: the field can be cleared before this runs
            ScrollView scroll = _scroll;
            if (panel == null) return;
            // 1. once the layout has settled, a list taller than 60% of the window gets exactly that height and scrolls (max-height alone did not hold)
            panel.schedule.Execute(() =>
            {
                if (panel == null || panel.panel == null || scroll == null || scroll.panel == null) return;
                VisualElement root = panel.parent;
                float rootH = root != null && root.worldBound.height > 200f ? root.worldBound.height : 900f;
                float limit = rootH * 0.6f;
                float content = scroll.contentContainer.layout.height;
                if (float.IsNaN(content)) return;
                scroll.style.height = content > limit ? new StyleLength(limit) : new StyleLength(StyleKeyword.Auto);
            }).StartingIn(30);
            // 2. then the card is moved back inside the window when it was left (or has grown) past an edge
            panel.schedule.Execute(() =>
            {
                if (panel == null || panel.panel == null) return;
                VisualElement root = panel.parent;
                if (root == null) return;
                Rect wb = panel.worldBound, rb = root.worldBound;
                if (float.IsNaN(wb.x) || wb.width <= 0f) return;
                float dx = 0f, dy = 0f;
                if (wb.yMin < rb.yMin) dy = rb.yMin - wb.yMin; else if (wb.yMax > rb.yMax) dy = Mathf.Max(rb.yMin - wb.yMin, rb.yMax - wb.yMax);
                if (wb.xMin < rb.xMin) dx = rb.xMin - wb.xMin; else if (wb.xMax > rb.xMax) dx = Mathf.Max(rb.xMin - wb.xMin, rb.xMax - wb.xMax);
                if (dx == 0f && dy == 0f) return;
                float l = panel.resolvedStyle.left, t = panel.resolvedStyle.top;
                if (float.IsNaN(l) || float.IsNaN(t)) return;
                panel.style.right = StyleKeyword.Auto;
                panel.style.left = l + dx;
                panel.style.top = t + dy;
            }).StartingIn(90);
        }

        private static void Indent(VisualElement e, int depth)
        {
            if (depth > 0) e.style.marginLeft = depth * 12;
        }

        /// <summary>"3 / 8", or "12 / 20 studs" for a tag with a unit; never more than the quantity (what is over is spare).</summary>
        private static string Count(ConstructionLine line, float have, float need)
        {
            string unit = GrowthRegistry.UnitName(line.item_id);
            float shown = Mathf.Min(have, need);
            if (unit == "m3") return UnitFormat.BulkVolume(shown) + " / " + UnitFormat.BulkVolume(need);   // bulk piles: counted in cubic metres, shown in the player's units
            if (unit == "m") return UnitFormat.Distance(shown) + " / " + UnitFormat.Distance(need);         // cable: counted in metres, shown in the player's units
            return $"{ConstructionSite.Num(shown)} / {ConstructionSite.Num(need)}" + (string.IsNullOrEmpty(unit) ? "" : " " + unit);
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

        private VisualElement Row(string itemId, string name, string value, bool done, float quantity = 0f)
        {
            var row = new VisualElement { pickingMode = PickingMode.Ignore };
            row.AddToClassList("construction-hover-row");
            List<string> members = GrowthRegistry.IsGroupSpec(itemId) ? GrowthRegistry.ToolItems(itemId) : null;
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
            else if (!string.IsNullOrEmpty(itemId) && !GrowthRegistry.IsGroupSpec(itemId))
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
                r.Name.text = HudBindings.GetDisplayName(id);
                if (r.Quantity > 0)
                {
                    // how many of this member alone would cover the quantity (a tag with equivalencies: 200 studs = 10 large bundles)
                    int each = Mathf.CeilToInt(r.Quantity / Mathf.Max(0.0001f, GrowthRegistry.UnitValue(r.Spec, id)) - 0.0001f);
                    r.Name.text = each + " x " + r.Name.text;
                }
                if (r.Struck) r.Name.text = "<s>" + r.Name.text + "</s>";
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
