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
    /// cell, showing whatever HoverOutline is currently hovering (or, over bare ground,
    /// the grid cell + biome under the cursor). Built entirely in C#, not HudUI.uxml -
    /// it only needs to find the existing HUD's root and the "ToastContainer" element
    /// by name to push toasts down while open, so it doesn't need to touch the already
    /// large HudBindings.cs wiring.
    /// Bootstraps itself on scene load, same pattern as FpsCounter/HoverOutline.
    /// </summary>
    public sealed class WailaPanel : MonoBehaviour
    {
        private static readonly Color Slate = new Color32(43, 52, 66, 255);
        private static readonly Color SlateEdge = new Color32(61, 74, 92, 255);
        private static readonly Color Copper = new Color32(224, 138, 60, 255);
        private static readonly Color TextColor = new Color32(238, 242, 246, 255);
        private static readonly Color TextDim = new Color32(139, 150, 165, 255);

        private bool _visible;
        private VisualElement _root;
        private VisualElement _toastContainer;
        private VisualElement _panel;
        private VisualElement _headerRow;
        private Image _iconImage;
        private Label _titleLabel;
        private VisualElement _rows;
        private string _lastContentKey;

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
            }

            UpdateToastPush();
        }

        private void EnsureBuilt()
        {
            if (_panel != null) return;

            var doc = FindAnyObjectByType<UIDocument>();
            if (doc == null) return;
            _root = doc.rootVisualElement;
            if (_root == null) return;

            _toastContainer = _root.Q<VisualElement>("ToastContainer");

            _panel = new VisualElement { name = "WailaPanel" };
            _panel.style.position = Position.Absolute;
            _panel.style.left = new Length(50, LengthUnit.Percent);
            _panel.style.top = 67f; // header height (64) + 3px padding
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

            _root.Add(_panel);
        }

        private void RefreshContent()
        {
            Transform hovered = HoverOutline.Current;
            string title;
            Texture2D icon;
            var details = new List<(string, string)>();

            if (hovered != null)
            {
                DescribeObject(hovered, out title, out icon, details);
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
            string key = title + "|" + details.Count;
            foreach (var (label, value) in details) key += "|" + label + "=" + value;
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
            foreach (var (label, value) in details)
            {
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

        private static void DescribeObject(Transform hovered, out string title, out Texture2D icon, List<(string, string)> details)
        {
            var growth = hovered.GetComponentInChildren<PlantedGrowth>() ?? hovered.GetComponentInParent<PlantedGrowth>();
            if (growth != null)
            {
                string itemId = growth.Group != null ? growth.Group.Id : null;
                title = !string.IsNullOrEmpty(itemId) ? Homesteader.UI.HudBindings.GetItemName(itemId) : NiceNameFromGameObject(hovered.name);
                icon = Homesteader.UI.PhoneController.GetItemIcon(null, itemId);

                details.Add(("Age", $"{growth.AgeDays:F1} days"));
                string stageName = growth.CurrentStage != null && !string.IsNullOrEmpty(growth.CurrentStage.Name)
                    ? growth.CurrentStage.Name
                    : growth.CurrentStage?.Stage.ToString();
                if (stageName != null) details.Add(("Stage", stageName));
                details.Add(("State", growth.State.ToString()));
                details.Add(("Ready to harvest", growth.CanHarvest ? "Yes" : "No"));
                return;
            }

            var item = hovered.GetComponentInChildren<WorldItem>() ?? hovered.GetComponentInParent<WorldItem>();
            if (item != null)
            {
                title = Homesteader.UI.HudBindings.GetItemName(item.ItemId);
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
            foreach (string prefix in new[] { "Planted_", "Item_" })
                if (s.StartsWith(prefix)) s = s.Substring(prefix.Length);
            s = s.Replace('_', ' ');
            return s.Length > 0 ? char.ToUpperInvariant(s[0]) + s.Substring(1) : rawName;
        }

        /// <summary>
        /// Crops and dropped items disable their own colliders (they're walk-through by
        /// design - PlantedGrowth.ShowModel / WorldItem.TryShow both turn theirs off), so
        /// HoverOutline's physics raycast can never find them. This raycasts the mouse
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

        private static bool TryGroundHit(out Vector3 hit)
        {
            hit = default;
            var cam = Camera.main;
            if (cam == null)
            {
                var iso = FindAnyObjectByType<IsometricLockedCamera>();
                if (iso != null) cam = iso.GetComponent<Camera>();
            }
            if (cam == null) return false;

            Vector2 mousePos = Mouse.current != null ? Mouse.current.position.ReadValue() : (Vector2)Input.mousePosition;
            Ray ray = cam.ScreenPointToRay(mousePos);

            // Prefer the real (rolling) terrain surface over a flat y=0 plane - otherwise the
            // reported grid cell/biome drifts from what's actually under the cursor on hills.
            if (Physics.Raycast(ray, out RaycastHit rayHit, 2000f))
            {
                hit = rayHit.point;
                return true;
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
            int cellX = Mathf.FloorToInt(hit.x);
            int cellZ = Mathf.FloorToInt(hit.z);

            title = "Ground";
            details.Add(("Grid cell", $"({cellX}, {cellZ})"));

            // A planting zone on the ground wins; otherwise fall back to the generated terrain's
            // own biome map (same order PlantingValidator uses), so this doesn't just say "none"
            // everywhere outside a hand-placed zone.
            string biome = PlantingZone.BiomeAt(hit);
            string biomeLabel = biome;
            if (biome == null)
            {
                var generator = FindAnyObjectByType<HomesteaderTerrainGenerator>();
                if (generator != null && generator.GetComponent<Terrain>() != null)
                {
                    Vector3 origin = generator.transform.position;
                    BiomeData data = generator.EvaluateBiomeAt(hit.x - origin.x, hit.z - origin.z);
                    if (data != null) biomeLabel = data.name;
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
                _toastContainer.style.top = 67f + panelHeight + 8f;
            }
            else
            {
                _toastContainer.style.top = StyleKeyword.Null; // back to the USS default (64px)
            }
        }
    }
}
