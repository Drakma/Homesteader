using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Growth;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// F3 toggles a "what am I looking at" panel directly under the header's date/time
    /// cell, showing whatever HoverTarget finds under the cursor (or, over bare ground,
    /// the grid cell + biome under the cursor). Built entirely in C#, not HudUI.uxml -
    /// it only needs to find the existing HUD's root and the "ToastContainer" element
    /// by name to push toasts down while open, so it doesn't need to touch the already
    /// large HudBindings.cs wiring.
    /// Bootstraps itself on scene load, same pattern as FpsCounter.
    /// </summary>
    public sealed class WailaPanel : MonoBehaviour
    {
        private static readonly Color Slate = new Color32(43, 52, 66, 255);
        private static readonly Color SlateEdge = new Color32(61, 74, 92, 255);
        private static readonly Color Copper = new Color32(224, 138, 60, 255);
        private static readonly Color TextColor = new Color32(238, 242, 246, 255);
        private static readonly Color TextDim = new Color32(139, 150, 165, 255);

        private bool _visible = true;
        private VisualElement _root;
        private VisualElement _toastContainer;
        private VisualElement _panel;
        private VisualElement _headerRow;
        private Image _iconImage;
        private Label _titleLabel;

        // Rows that rotate through the tools able to do a job (icon and name); Shift holds the rotation.
        private sealed class ToolRotation { public Image Icon; public Label Name; public List<string> Items; public int Shown = -1; }
        private readonly List<ToolRotation> _rotations = new List<ToolRotation>();
        private float _rotationClock;
        private const float SecondsPerTool = 1.6f;
        private VisualElement _rows;
        private string _lastContentKey;
        private static HomesteaderTerrainGenerator _cachedGenerator;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<WailaPanel>() != null) return;
            var go = new GameObject("WailaPanel");
            DontDestroyOnLoad(go);
            go.AddComponent<WailaPanel>();
        }

        private void Update()
        {
            // Block while loading
            if (WelcomeMenuController.IsLoading) return;

            bool pressed = Keyboard.current != null
                ? Keyboard.current.f3Key.wasPressedThisFrame
                : Input.GetKeyDown(KeyCode.F3);

            if (pressed)
            {
                _visible = !_visible;
                if (_visible) EnsureBuilt();
                if (_panel != null) _panel.style.display = _visible ? DisplayStyle.Flex : DisplayStyle.None;

            }

            if (_visible)
            {
                EnsureBuilt();
                RefreshContent();
                UpdateToolRotation();
            }

            UpdateToastPush();
        }

        private Transform _lastHovered;
        private float _nextDescribe;
        private float _nextStaleCheck;
        private float _lastToastTop = -1f;

        private void EnsureBuilt()
        {
            // If we have a panel but it's detached or in a stale root (e.g. after scene reload), rebuild
            if (_panel != null && Time.unscaledTime >= _nextStaleCheck)   // a scene scan: about once a second, not every frame
            {
                _nextStaleCheck = Time.unscaledTime + 1f;
                var doc = FindAnyObjectByType<UIDocument>();
                var currentRoot = doc != null ? doc.rootVisualElement : null;
                if (_panel.parent == null || (currentRoot != null && _panel.parent != currentRoot))
                {
                    _panel = null;
                }
            }

            if (_panel != null) return;

            var d = FindAnyObjectByType<UIDocument>();
            if (d == null) return;
            _root = d.rootVisualElement;
            if (_root == null) return;

            _toastContainer = _root.Q<VisualElement>("ToastContainer");

            _panel = new VisualElement { name = "WailaPanel" };
            _panel.style.position = Position.Absolute;
            _panel.style.left = new Length(50, LengthUnit.Percent);
            _panel.style.top = 70f; // header height (64) + 6px gap
            _panel.style.translate = new Translate(new Length(-50, LengthUnit.Percent), 0);
            _panel.style.minWidth = 260f;
            _panel.style.maxWidth = 380f;
            _panel.style.backgroundColor = Slate;
            _panel.style.borderTopWidth = _panel.style.borderRightWidth = _panel.style.borderBottomWidth = 1;
            _panel.style.borderLeftWidth = 2;
            _panel.style.borderTopColor = _panel.style.borderRightColor = _panel.style.borderBottomColor = SlateEdge;
            _panel.style.borderLeftColor = Copper;
            _panel.style.paddingTop = _panel.style.paddingBottom = 10f;
            _panel.style.paddingLeft = _panel.style.paddingRight = 14f;
            _panel.style.display = DisplayStyle.None;
            _panel.pickingMode = PickingMode.Ignore;

            _headerRow = new VisualElement { name = "WailaHeaderRow" };
            _headerRow.style.flexDirection = FlexDirection.Row;
            _headerRow.style.alignItems = Align.Center;
            _headerRow.style.marginBottom = 6f;
            _panel.Add(_headerRow);

            _iconImage = new Image { name = "WailaIcon" };
            _iconImage.style.width = 28f;
            _iconImage.style.height = 28f;
            _iconImage.style.marginRight = 8f;
            _iconImage.style.display = DisplayStyle.None;
            _headerRow.Add(_iconImage);

            _titleLabel = new Label { name = "WailaTitle" };
            _titleLabel.style.color = TextColor;
            _titleLabel.style.fontSize = 18f;
            _titleLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            _headerRow.Add(_titleLabel);

            _rows = new VisualElement { name = "WailaRows" };
            _panel.Add(_rows);

            // Insert at index 0 so the welcome menu (added later by WelcomeMenuController)
            // and its wallpaper sit on top of the WAILA panel, hiding it while the menu is open.
            _root.Insert(0, _panel);
        }

        private readonly List<(string, string)> _details = new List<(string, string)>();
        private readonly System.Text.StringBuilder _key = new System.Text.StringBuilder();

        private void RefreshContent()
        {
            if (HudVisibility.Hidden) { if (_panel != null) _panel.style.display = DisplayStyle.None; return; }   // F11 hides the whole HUD, this panel too
            Transform hovered = HoverTarget.Find();
            // The card is rebuilt once a second while the same object stays under the cursor (a new target shows at once); between rebuilds it stays as it is.
            // Describing a well, a wired device or a building walks wires, water and power every time, which is far too much for every frame.
            if (hovered != null && hovered == _lastHovered && _panel != null && _panel.style.display == DisplayStyle.Flex && Time.unscaledTime < _nextDescribe) return;
            _lastHovered = hovered;
            _nextDescribe = Time.unscaledTime + (hovered != null ? 1f : 0.15f);
            string title;
            Texture2D icon;
            var details = _details;   // reused: this runs every frame
            details.Clear();

            ConstructionSite site = hovered != null && hovered.GetComponentInParent<AttachedObject>() == null && hovered.GetComponentInParent<Homesteader.Growth.PlacedChimney>() == null ? hovered.GetComponentInParent<ConstructionSite>() : null;   // a mounted item on the building is its own target
            if (Homesteader.Growth.Net.PreviewFrame >= Time.frameCount - 1)
            {
                // a yagi being placed: how it lines up with the other yagis, connected or not, so the two can be aimed at each other
                title = Homesteader.UI.HudBindings.GetDisplayName(Homesteader.Growth.Net.PreviewItem);
                icon = Homesteader.UI.PhoneController.GetItemIcon(null, Homesteader.Growth.Net.PreviewItem);
                Homesteader.UI.AssetCatalogItem yagi = Homesteader.UI.HudBindings.GetCatalogItem(Homesteader.Growth.Net.PreviewItem);
                Homesteader.Growth.Net.SignalRows(Homesteader.Growth.Net.PreviewPos, Homesteader.Growth.Net.PreviewForward, yagi != null ? yagi.range_m : 0f, null, details);
                details.Add(("Turn it", "R (Shift + R the other way)"));
            }
            else if (PlacementController.WellPreview.HasValue)
            {
                // a well blueprint held over the ground: what is under this spot
                Vector3 at = PlacementController.WellPreview.Value;
                title = "Well here";
                icon = Homesteader.UI.PhoneController.GetItemIcon(null, PlacementController.WellPreviewId);
                float depth = WaterTable.DepthM(at);
                details.Add(("Water at", UnitFormat.Distance(depth) + " down"));
                details.Add(("Max flow", UnitFormat.Volume(WaterTable.YieldLph(at)) + " an hour"));
                WellNeeds(PlacementController.WellPreviewId, depth, details);
            }
            else if (site != null)
            {
                // The what-and-how-far is on the site's own hover card (ConstructionHover); this just names it.
                title = site.Finished ? site.Name() : site.Name() + " Build Site";
                icon = Homesteader.UI.PhoneController.GetItemIcon(null, site.StructureId);
                if (!site.Finished) details.Add(("Stage", site.CurrentStage != null ? site.CurrentStage.name + $"  ({site.Stage + 1} of {site.StageCount})" : ""));
                if (site.Finished) WireNetwork.Describe(site.GetComponent<WireNode>(), details);   // a wind turbine: its output and what it is wired to
                if (site.Finished && !site.IsWell)
                {
                    // a utility is listed only when something is wrong with it, and the row says what (a tripped breaker, an empty tank, the first break in the network ...)
                    string powerWhy = WireNetwork.PowerProblem(site);
                    if (powerWhy != null) details.Add(("Electricity", powerWhy));
                    string waterWhy = WireNetwork.WaterProblem(site);
                    if (waterWhy != null) details.Add(("Water", waterWhy));
                    string netWhy = WireNetwork.InternetProblem(site);
                    if (netWhy != null) details.Add(("Internet", netWhy));
                }
                if (site.IsStorage) details.Add(("Stored", site.StorageSummary()));
                if (site.IsWell)
                {
                    details.Add(("Water at", UnitFormat.Distance(site.WellDepthM) + " down"));
                    details.Add(("Max flow", UnitFormat.Volume(WaterTable.YieldLph(site.transform.position)) + " an hour"));
                    details.Add(("Pump", string.IsNullOrEmpty(site.PumpId) ? "None yet" : Homesteader.UI.HudBindings.GetItemName(site.PumpId)));
                    if (site.Finished && string.IsNullOrEmpty(site.FittedPanel)) details.Add(("Sub panel", "None"));
                }
            }
            else if (hovered != null)
            {
                DescribeObject(hovered, out title, out icon, details);
                PlacedObject tank = hovered.GetComponentInParent<PlacedObject>();   // a tank, a drum, a can: what is in it
                if (tank != null && LiquidRules.IsLiquidContainer(tank.ItemId)) details.Add(("Holds", LiquidRules.Describe(tank.ItemId, tank.LiquidId, tank.WireUsed)));
                WireNetwork.Describe(WireNode.Of(hovered), details);   // what a wired device is connected to
            }
            else if (TryDescribeForestTree(out title, out icon, details))
            {
                // a procedural forest tree under the cursor
            }
            else if (TryDescribeBerryBush(out title, out icon, details))
            {
                // a berry bush under the cursor
            }
            else if (TryFindNearbyPlantOrItem(out title, out icon, details))
            {
                // handled
            }
            else if (!TryDescribeGroundCell(out title, out icon, details))
            {
                _panel.style.display = DisplayStyle.None;
                return;
            }

            _panel.style.display = DisplayStyle.Flex;

            // Cheap dedupe so we're not tearing down/rebuilding the row list every frame.
            _key.Clear().Append(title).Append('|').Append(details.Count);
            foreach (var (label, value) in details) _key.Append('|').Append(label).Append('=').Append(value);
            string key = _key.ToString();
            if (key == _lastContentKey) return;
            _lastContentKey = key;

            _titleLabel.text = title;
            if (icon != null)
            {
                _iconImage.image = icon;
                _iconImage.style.display = DisplayStyle.Flex;
            }
            else
            {
                _iconImage.style.display = DisplayStyle.None;
            }
            _rows.Clear();
            _rotations.Clear();
            foreach (var (label, value) in details)
            {
                if (label.StartsWith("@item|"))
                {
                    AddItemRow(label.Substring("@item|".Length), value);
                    continue;
                }
                if (label.StartsWith("@tools|"))
                {
                    AddToolRow(label.Substring("@tools|".Length), value);
                    continue;
                }
                var row = new VisualElement();
                row.style.flexDirection = FlexDirection.Row;
                row.style.justifyContent = Justify.SpaceBetween;
                row.style.marginTop = 3f;

                var labelEl = new Label(label) { style = { color = TextDim, fontSize = 14f } };
                var valueEl = new Label(value) { style = { color = TextColor, fontSize = 14f } };
                row.Add(labelEl);
                row.Add(valueEl);
                _rows.Add(row);
            }
        }

        /// <summary>A row "[icon] Item name ... xN": one item held in a container.</summary>
        private void AddItemRow(string itemId, string count)
        {
            var row = new VisualElement();
            row.style.flexDirection = FlexDirection.Row;
            row.style.justifyContent = Justify.SpaceBetween;
            row.style.alignItems = Align.Center;
            row.style.marginTop = 3f;
            var left = new VisualElement();
            left.style.flexDirection = FlexDirection.Row;
            left.style.alignItems = Align.Center;
            Texture2D tex = Homesteader.UI.PhoneController.GetItemIcon(null, itemId);
            if (tex != null)
            {
                var icon = new Image { image = tex, scaleMode = ScaleMode.ScaleToFit };
                icon.style.width = 22f; icon.style.height = 22f; icon.style.marginRight = 6f;
                left.Add(icon);
            }
            left.Add(new Label(Homesteader.UI.HudBindings.GetDisplayName(itemId)) { style = { color = TextColor, fontSize = 14f } });
            row.Add(left);
            row.Add(new Label(count.StartsWith("=") ? count.Substring(1) : "x" + count) { style = { color = TextDim, fontSize = 14f } });   // ("=text": shown as it is, not as a count)
            _rows.Add(row);
        }

        /// <summary>A row "label ... [icon] Tool name" that cycles through every item the tool spec accepts.</summary>
        private void AddToolRow(string label, string spec)
        {
            List<string> items = GrowthRegistry.ToolItems(spec);
            var row = new VisualElement();
            row.style.flexDirection = FlexDirection.Row;
            row.style.justifyContent = Justify.SpaceBetween;
            row.style.alignItems = Align.Center;
            row.style.marginTop = 3f;
            row.Add(new Label(label) { style = { color = TextDim, fontSize = 14f } });
            var right = new VisualElement();
            right.style.flexDirection = FlexDirection.Row;
            right.style.alignItems = Align.Center;
            var icon = new Image { scaleMode = ScaleMode.ScaleToFit };
            icon.style.width = 22f; icon.style.height = 22f; icon.style.marginRight = 6f;
            var name = new Label(items.Count == 0 ? "Any matching tool" : "") { style = { color = TextColor, fontSize = 14f } };
            right.Add(icon); right.Add(name);
            row.Add(right);
            _rows.Add(row);
            if (items.Count == 0) { icon.style.display = DisplayStyle.None; return; }
            _rotations.Add(new ToolRotation { Icon = icon, Name = name, Items = items });
        }

        /// <summary>Advances the clock (held while Shift is down) and shows the current tool in every rotating row.</summary>
        private void UpdateToolRotation()
        {
            if (_rotations.Count == 0) return;
            bool hold = Keyboard.current != null && Keyboard.current.shiftKey.isPressed;
            if (!hold) _rotationClock += Time.unscaledDeltaTime;
            int step = Mathf.FloorToInt(_rotationClock / SecondsPerTool);
            foreach (ToolRotation r in _rotations)
            {
                int index = step % r.Items.Count;
                if (index == r.Shown) continue;
                r.Shown = index;
                string id = r.Items[index];
                r.Name.text = Homesteader.UI.HudBindings.GetDisplayName(id);
                Texture2D tex = Homesteader.UI.PhoneController.GetItemIcon(null, id);
                r.Icon.image = tex;
                r.Icon.style.display = tex != null ? DisplayStyle.Flex : DisplayStyle.None;
            }
        }

        /// <summary>What a well's depth-scaled lines need at that depth (the pipe and the cable).</summary>
        private static void WellNeeds(string wellId, float depth, List<(string, string)> details)
        {
            List<ConstructionStageData> stages = ConstructionSite.StagesOf(wellId);
            if (stages == null) return;
            foreach (ConstructionStageData st in stages)
                foreach (ConstructionLine l in st.recipe)
                {
                    if (l == null || l.per_depth_m <= 0f) continue;
                    float n = Mathf.Ceil(l.quantity + l.per_depth_m * depth);
                    string unit = GrowthRegistry.UnitName(l.item_id);
                    details.Add((ConstructionSite.LineName(l.item_id), unit == "m" ? UnitFormat.Distance(n) : ConstructionSite.Num(n) + (string.IsNullOrEmpty(unit) ? "" : " " + unit)));
                }
        }

        private static void DescribeObject(Transform hovered, out string title, out Texture2D icon, List<(string, string)> details)
        {
            var growth = hovered.GetComponentInChildren<PlantedGrowth>() ?? hovered.GetComponentInParent<PlantedGrowth>();
            if (growth != null)
            {
                string itemId = growth.Group != null ? growth.Group.Id : null;
                title = !string.IsNullOrEmpty(itemId) ? Homesteader.UI.HudBindings.GetDisplayName(itemId) : NiceNameFromGameObject(hovered.name);
                icon = Homesteader.UI.PhoneController.GetItemIcon(null, itemId);

                details.Add(("Age", $"{growth.AgeDays:F1} days"));
                string stageName = growth.CurrentStage != null && !string.IsNullOrEmpty(growth.CurrentStage.Name)
                    ? growth.CurrentStage.Name
                    : growth.CurrentStage?.Stage.ToString();
                if (stageName != null) details.Add(("Stage", stageName));
                details.Add(("State", growth.State.ToString()));
                details.Add(("Ready to harvest", growth.CanHarvest ? "Yes" : "No"));
                string harvestTools = growth.Group?.Rules?.YieldTool;
                if (!string.IsNullOrEmpty(harvestTools)) details.Add(("@tools|Harvest with", harvestTools));
                return;
            }

            var chimney = hovered.GetComponentInParent<Homesteader.Growth.PlacedChimney>();
            if (chimney != null)
            {
                title = Homesteader.UI.HudBindings.GetDisplayName(chimney.KitId);
                icon = Homesteader.UI.PhoneController.GetItemIcon(null, chimney.KitId);
                details.Add(("Height", UnitFormat.Length(chimney.Spec.Top)));
                details.Add(("Fireplace", chimney.FireLit ? "Burning" : chimney.FuelMinutes > 0f ? "Wood laid, not lit" : "Empty"));
                if (chimney.FuelMinutes > 0f) details.Add(("Wood", Mathf.RoundToInt(chimney.FuelMinutes) + " game minutes"));
                return;
            }

            var mounted = hovered.GetComponentInParent<AttachedObject>();
            if (mounted != null)
            {
                title = Homesteader.UI.HudBindings.GetDisplayName(mounted.ItemId);
                icon = Homesteader.UI.PhoneController.GetItemIcon(null, mounted.ItemId);
                var shelf = mounted.GetComponent<Homesteader.Growth.Shelf>();
                if (shelf != null)
                {
                    details.Add(("On it", shelf.Describe()));
                    details.Add(("Free", UnitFormat.Length(shelf.FreeLength())));
                }
                return;
            }

            var placed = hovered.GetComponentInParent<PlacedObject>() ?? hovered.GetComponentInChildren<PlacedObject>();
            if (placed != null)
            {
                int stackCount = placed.StackCount;
                title = Homesteader.UI.HudBindings.GetDisplayName(placed.ItemId) + (stackCount > 1 ? "  x" + stackCount : "");
                icon = Homesteader.UI.PhoneController.GetItemIcon(null, placed.ItemId);
                if (stackCount > 1) details.Add(("Stacked", stackCount + " high"));
                if (Homesteader.Growth.GrowthRegistry.PackContent(placed.ItemId, out string packSingle, out int packCount))
                {
                    details.Add(("Left", Homesteader.Growth.PackRules.Left(placed) + " of " + packCount + " " + Homesteader.UI.HudBindings.GetItemName(packSingle)));
                }
                PortableGenerator gen = placed.GetComponent<PortableGenerator>();
                if (gen != null)
                {
                    details.Add(("Output", SolarSun.Power(Mathf.Min(gen.DemandW, gen.RatedW)) + " of " + SolarSun.Power(gen.RatedW)));
                    details.Add(("Range", Mathf.RoundToInt(gen.RadiusTiles) + " tiles, and any build site it reaches"));
                    if (gen.RatedA > 0f) details.Add(("Current", gen.LoadA.ToString("0.#") + " A of " + gen.RatedA.ToString("0.#") + " A"));
                    if (gen.Tripped) details.Add(("State", "Tripped: overload"));
                    else if (gen.DemandW > gen.RatedW) details.Add(("Overloaded", "More is wanted than it makes"));
                }
                Homesteader.UI.AssetCatalogItem spool = Homesteader.UI.HudBindings.GetCatalogItem(placed.ItemId);
                if (spool != null && spool.wire_length_m > 0f) details.Add(("Wire left", UnitFormat.Distance(Mathf.Max(0f, spool.wire_length_m - placed.WireUsed)) + " of " + UnitFormat.Distance(spool.wire_length_m)));
                if (Homesteader.UI.ContainerRules.IsContainer(placed.ItemId))
                {
                    details.Add(("Holds", UnitFormat.WeightPair(Homesteader.UI.ContainerRules.Used(placed.Contents), Homesteader.UI.ContainerRules.Capacity(placed.ItemId))));
                    if (placed.Contents != null && placed.Contents.Count > 0)
                        foreach (ContainerStack c in placed.Contents) details.Add(("@item|" + c.ItemId, c.Count.ToString()));   // an icon row
                    else details.Add(("Contents", "Empty"));
                }
                var sawmill = placed.GetComponent<Homesteader.Growth.Sawmill>();
                if (sawmill != null)
                {
                    if (sawmill.FuelL < Homesteader.Growth.Sawmill.FuelPerCutL - 0.001f) details.Add(("Fuel", "Out of gasoline"));
                    if (sawmill.Busy) details.Add(("Status", "Cutting"));
                    else if (!string.IsNullOrEmpty(sawmill.LogId)) { details.Add(("@item|" + sawmill.LogId, "=On the track")); }
                    else { details.Add(("Track", "Empty")); }
                    return;
                }
                return;
            }

            var item = hovered.GetComponentInChildren<WorldItem>() ?? hovered.GetComponentInParent<WorldItem>();
            if (item != null)
            {
                title = Homesteader.UI.HudBindings.GetDisplayName(item.ItemId);
                icon = Homesteader.UI.PhoneController.GetItemIcon(null, item.ItemId);
                details.Add(("Type", "Dropped item"));
                return;
            }

            title = NiceNameFromGameObject(hovered.name);
            icon = null;
        }

        /// <summary>Last-resort display name when there's no catalog entry to ask: strips a
        /// "Planted_"/"Item_" prefix and underscores instead of showing the raw internal name.</summary>
        private static string NiceNameFromGameObject(string rawName)
        {
            string s = rawName;
            // Model clones are named "GLB_<item id>(Clone)": drop the decoration and use the catalog's real name when the id is an item.
            if (s.EndsWith("(Clone)")) s = s.Substring(0, s.Length - "(Clone)".Length).TrimEnd();
            foreach (string prefix in new[] { "Planted_", "Item_", "GLB_" })
                if (s.StartsWith(prefix)) s = s.Substring(prefix.Length);
            string catalogName = Homesteader.UI.HudBindings.GetItemName(s);
            if (!string.IsNullOrEmpty(catalogName) && catalogName != s) return Homesteader.UI.HudBindings.GetDisplayName(s);
            s = s.Replace('_', ' ');
            return s.Length > 0 ? char.ToUpperInvariant(s[0]) + s.Substring(1) : rawName;
        }

        /// <summary>
        /// Crops and dropped items disable their own colliders (they're walk-through by
        /// design - PlantedGrowth.ShowModel / WorldItem.TryShow both turn theirs off), so
        /// HoverTarget's physics raycast can never find them. This raycasts the mouse
        /// onto the ground plane instead and picks whichever tracked crop/item is
        /// closest to that point, within a small radius.
        /// </summary>
        private static bool TryFindNearbyPlantOrItem(out string title, out Texture2D icon, List<(string, string)> details)
        {
            title = null;
            icon = null;
            details.Clear();

            if (!TryGroundHit(out Vector3 hit)) return false;

            const float radius = 0.6f;
            float bestDistSq = radius * radius;
            PlantedGrowth bestGrowth = null;
            foreach (PlantedGrowth g in PlantedGrowth.All)
            {
                if (g == null) continue;
                float d = (g.transform.position - hit).sqrMagnitude;
                if (d < bestDistSq) { bestDistSq = d; bestGrowth = g; }
            }
            if (bestGrowth != null)
            {
                DescribeObject(bestGrowth.transform, out title, out icon, details);
                return true;
            }

            bestDistSq = radius * radius;
            WorldItem bestItem = null;
            foreach (WorldItem it in WorldItem.All)
            {
                if (it == null) continue;
                float d = (it.transform.position - hit).sqrMagnitude;
                if (d < bestDistSq) { bestDistSq = d; bestItem = it; }
            }
            if (bestItem != null)
            {
                DescribeObject(bestItem.transform, out title, out icon, details);
                return true;
            }

            return false;
        }

        /// <summary>The forest trees have no colliders, so the hover is found by ray against the tree registry.</summary>
        private static bool TryDescribeForestTree(out string title, out Texture2D icon, List<(string, string)> details)
        {
            title = null;
            icon = null;
            details.Clear();
            if (Homesteader.World.ForestTrees.Count == 0) return false;

            var cam = Camera.main;
            if (cam == null)
            {
                var iso = IsometricLockedCamera.Current;
                if (iso != null) cam = iso.GetComponent<Camera>();
            }
            if (cam == null) return false;

            Vector2 mousePos = Mouse.current != null ? Mouse.current.position.ReadValue() : (Vector2)Input.mousePosition;
            if (!Homesteader.World.ForestTrees.TryPick(cam.ScreenPointToRay(mousePos), out Homesteader.World.ForestTree tree)) return false;

            Homesteader.World.ForestTrees.Describe(tree, out title, details);
            return true;
        }

        private static bool TryDescribeBerryBush(out string title, out Texture2D icon, List<(string, string)> details)
        {
            title = null;
            icon = null;
            details.Clear();
            if (Homesteader.World.BerryBushes.Count == 0) return false;
            var cam = Camera.main;
            if (cam == null)
            {
                var iso = IsometricLockedCamera.Current;
                if (iso != null) cam = iso.GetComponent<Camera>();
            }
            if (cam == null) return false;
            Vector2 mousePos = Mouse.current != null ? Mouse.current.position.ReadValue() : (Vector2)Input.mousePosition;
            if (!Homesteader.World.BerryBushes.TryPick(cam.ScreenPointToRay(mousePos), out Homesteader.World.BerryBush bush)) return false;
            Homesteader.World.BerryBushes.Describe(bush, out title, details);
            icon = PhoneController.GetItemIcon(bush.AssetId + ".png", bush.AssetId);
            return true;
        }

        private static bool TryGroundHit(out Vector3 hit)
        {
            hit = default;
            var cam = Camera.main;
            if (cam == null)
            {
                var iso = IsometricLockedCamera.Current;
                if (iso != null) cam = iso.GetComponent<Camera>();
            }
            if (cam == null) return false;

            Vector2 mousePos = Mouse.current != null ? Mouse.current.position.ReadValue() : (Vector2)Input.mousePosition;
            Ray ray = cam.ScreenPointToRay(mousePos);

            // Prefer the real (rolling) terrain surface over a flat y=0 plane - otherwise the
            // reported grid cell/biome drifts from what's actually under the cursor on hills.
            // This runs every frame WAILA is open over bare ground, so keep the common case a single
            // cheap Raycast; only pay for RaycastAll+sort on the rare frame that actually hits an
            // invisible LandWall border collider (see LandBoundaryController), which a plain Raycast
            // would otherwise stop dead on well short of the real ground.
            if (Physics.Raycast(ray, out RaycastHit rayHit, 2000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
            {
                if (!rayHit.collider.gameObject.name.StartsWith("LandWall_"))
                {
                    hit = rayHit.point;
                    return true;
                }

                RaycastHit[] rayHits = Physics.RaycastAll(ray, 2000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
                System.Array.Sort(rayHits, (a, b) => a.distance.CompareTo(b.distance));
                foreach (RaycastHit rh in rayHits)
                {
                    if (rh.collider.gameObject.name.StartsWith("LandWall_")) continue;
                    hit = rh.point;
                    return true;
                }
            }

            var groundPlane = new Plane(Vector3.up, Vector3.zero);
            if (!groundPlane.Raycast(ray, out float enter)) return false;
            hit = ray.GetPoint(enter);
            return true;
        }

        private static bool TryDescribeGroundCell(out string title, out Texture2D icon, List<(string, string)> details)
        {
            title = null;
            icon = null;
            details.Clear();

            if (!TryGroundHit(out Vector3 hit)) return false;
            title = "Ground";

            // A planting zone on the ground wins; otherwise fall back to the generated terrain's
            // own biome map (same order PlantingValidator uses), so this doesn't just say "none"
            // everywhere outside a hand-placed zone.
            string biome = PlantingZone.BiomeAt(hit);
            string biomeLabel = biome;
            if (biome == null)
            {
                // Cached: this runs every frame WAILA is showing bare, unzoned ground, and the
                // generator is a single persistent object for the whole session.
                if (_cachedGenerator == null) _cachedGenerator = FindAnyObjectByType<HomesteaderTerrainGenerator>();
                var generator = _cachedGenerator;
                if (generator != null && generator.GetComponent<Terrain>() != null)
                {
                    Vector3 origin = generator.transform.position;
                    float localX = hit.x - origin.x;
                    float localZ = hit.z - origin.z;

                    // Only evaluate biome if the hit point is within the terrain bounds
                    if (localX >= 0f && localX <= generator.terrainSizeX &&
                        localZ >= 0f && localZ <= generator.terrainSizeZ)
                    {
                        BiomeData data = generator.EvaluateBiomeAt(localX, localZ);
                        if (data != null) biomeLabel = data.name;
                    }
                }
            }
            details.Add(("Biome", biomeLabel ?? "none"));
            return true;
        }

        private void UpdateToastPush()
        {
            if (_toastContainer == null) return;

            if (_visible && _panel != null)
            {
                float panelHeight = _panel.resolvedStyle.height;
                if (panelHeight <= 0f) panelHeight = 70f; // not laid out yet this frame; reasonable default
                float top = 70f + panelHeight + 8f;
                if (!Mathf.Approximately(top, _lastToastTop)) { _lastToastTop = top; _toastContainer.style.top = top; }   // only when it changes: a style write dirties the layout
            }
            else
            {
                if (_lastToastTop >= 0f) { _lastToastTop = -1f; _toastContainer.style.top = StyleKeyword.Null; } // back to the USS default (64px)
            }
        }
    }
}
