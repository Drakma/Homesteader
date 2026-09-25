using Homesteader.UI;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Homesteader.Growth
{
    /// <summary>
    /// Right-click to plant. When the selected toolbar item declares a
    /// use.right_click action of "plant_growth_group" (in its mod manifest),
    /// right-clicking the ground validates the spot against the growth group's
    /// planting rules and, if valid, plants stage 1 and consumes one item.
    ///
    /// Right-drag pans the camera, so a plant only fires on a right-CLICK: the
    /// button is released without the pointer having travelled (and quickly).
    ///
    /// Bootstraps itself after the scene loads, so no scene edit is needed.
    /// </summary>
    public sealed class PlantingController : MonoBehaviour
    {
        private const float ClickMaxTravelPx = 8f;
        private const float ClickMaxSeconds = 0.4f;

        private Vector2 pressPos;
        private float pressTime;
        private bool pressed;
        private Transform plantedRoot;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<PlantingController>() != null) return;
            new GameObject("PlantingController").AddComponent<PlantingController>();
        }

        private void Update()
        {
            if (!ReadRightButton(out bool down, out bool up, out Vector2 pos)) return;

            if (down)
            {
                pressed = true;
                pressPos = pos;
                pressTime = Time.unscaledTime;
                return;
            }

            if (!up || !pressed) return;
            pressed = false;

            bool isClick = (pos - pressPos).magnitude <= ClickMaxTravelPx
                        && Time.unscaledTime - pressTime <= ClickMaxSeconds;
            if (isClick) TryPlant(pos);
        }

        public void TryPlant(Vector2 screenPos)
        {
            HudBindings hud = HudBindings.Instance;
            if (hud == null) return;
            // A window/text field owns input, or the click landed on the HUD.
            if (HudBindings.KeyboardCaptured || hud.IsPointerOverUI(screenPos)) return;

            Camera cam = GameCamera();
            if (cam == null) return;

            HudState state = HudState.Active;
            string heldId = null;
            GrowthGroup group = null;
            if (state.SelectedSlot >= 0 && state.SelectedSlot < state.Toolbar.Count)
            {
                ToolbarSlotData slot = state.Toolbar[state.SelectedSlot];
                if (!string.IsNullOrEmpty(slot.IconId) && slot.Count > 0) heldId = slot.IconId;
            }
            // The GROUP owns what plants it: the held item plants whichever group names it.
            bool canPlant = heldId != null && GrowthRegistry.TryGetGroupPlantedBy(heldId, out group);

            if (!TryGroundHit(cam, screenPos, out RaycastHit hit))
            {
                if (canPlant) ToastNotificationSystem.ShowWarning("Can't plant", "You can only plant in open ground.");
                return;
            }

            // Lock to the ground grid: everything below (zone, biome, spacing, reach) is
            // checked at, and the plant is placed on, the centre of the clicked cell.
            hit.point = PlantingValidator.SnapToGrid(hit.point);
            var ped = FindAnyObjectByType<PedController>();

            // Something already growing in that square: this click tries to harvest it.
            PlantedGrowth existing = PlantedAt(hit.point);
            if (existing != null)
            {
                TryHarvest(existing, heldId, ped != null ? ped.transform : null, hit.point);
                return;
            }

            if (!canPlant) return;   // nothing to plant with this item

            if (!PlantingValidator.Validate(group, hit, ped != null ? ped.transform : null, out string reason))
            {
                ToastNotificationSystem.ShowWarning("Can't plant here", reason);
                return;
            }

            if (!state.ConsumeFromSelectedSlot(1)) return;
            hud.RefreshToolbar();

            PlantedGrowth.Plant(group, hit.point, PlantedRoot());
        }

        /// <summary>The plant standing in the grid square containing the point, if any.</summary>
        private static PlantedGrowth PlantedAt(Vector3 point)
        {
            foreach (PlantedGrowth p in PlantedGrowth.All)
            {
                if (p == null) continue;
                Vector3 c = p.transform.position;
                if (Mathf.Floor(c.x / PlantingValidator.GridSizeM) == Mathf.Floor(point.x / PlantingValidator.GridSizeM)
                    && Mathf.Floor(c.z / PlantingValidator.GridSizeM) == Mathf.Floor(point.z / PlantingValidator.GridSizeM))
                    return p;
            }
            return null;
        }

        /// <summary>
        /// Harvests a ready plant if the player is in reach and (when the group needs one) holding the
        /// right tool. A success is silent; the yield just appears on the toolbar. Only failures the
        /// player can act on get a message, and only when the click was clearly a harvest attempt.
        /// </summary>
        private static void TryHarvest(PlantedGrowth plant, string heldId, Transform player, Vector3 point)
        {
            GrowthRules rules = plant.Group.Rules;
            if (string.IsNullOrEmpty(rules.YieldItemId) || rules.YieldAmountMax <= 0) return;   // nothing to harvest

            bool needsTool = !string.IsNullOrEmpty(rules.YieldTool);
            bool holdingTool = needsTool && GrowthRegistry.ToolMatches(rules.YieldTool, heldId);

            if (!plant.CanHarvest)
            {
                // A withered or dead plant just can't be harvested; a young one gets a hint if the right tool is in hand.
                if (holdingTool && plant.State == PlantedGrowth.PlantState.Alive)
                    ToastNotificationSystem.ShowWarning("Not ready", $"{plant.Group.Name} isn't ready to harvest yet.");
                return;
            }

            if (!PlantingValidator.InReach(player, point, GameRules.HarvestReachCells))
            {
                ToastNotificationSystem.ShowWarning("Too far", "You can only harvest the squares right next to you.");
                return;
            }

            if (needsTool && !holdingTool)
            {
                ToastNotificationSystem.ShowWarning("Need a tool", $"You need {DescribeTool(rules.YieldTool)} to harvest this.");
                return;
            }

            int amount = rules.RollYield();
            int added = HudState.Active.AddItemToToolbar(rules.YieldItemId, amount, HudBindings.GetMaxStack(rules.YieldItemId));
            if (added <= 0)
            {
                ToastNotificationSystem.ShowWarning("Toolbar full", "Make room on the toolbar to harvest this.");
                return;
            }
            HudBindings.Instance.RefreshToolbar();
            if (added < amount)
                ToastNotificationSystem.ShowWarning("Toolbar full", "Some of the harvest didn't fit and was lost.");

            plant.Harvested();
        }

        private static string DescribeTool(string spec)
        {
            return spec.StartsWith("#") ? $"a {spec.Substring(1).Replace('_', ' ')}" : HudBindings.GetItemName(spec);
        }

        /// <summary>
        /// The first thing under the cursor, ignoring the player. It must be
        /// terrain for planting to proceed, so a building or prop in front of the
        /// ground blocks the click rather than being planted through.
        /// </summary>
        private static bool TryGroundHit(Camera cam, Vector2 screenPos, out RaycastHit result)
        {
            result = default;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(screenPos), 1000f, ~0, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));

            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                result = h;
                return true;
            }
            return false;
        }

        /// <summary>
        /// The gameplay camera. Camera.main needs the MainCamera tag, which this scene's
        /// camera does not carry, so fall back to the isometric camera, then any camera.
        /// </summary>
        private static Camera GameCamera()
        {
            Camera cam = Camera.main;
            if (cam != null) return cam;

            var iso = FindAnyObjectByType<IsometricLockedCamera>();
            if (iso != null && iso.TryGetComponent(out cam)) return cam;

            return FindAnyObjectByType<Camera>();
        }

        private Transform PlantedRoot()
        {
            if (plantedRoot == null)
            {
                var root = new GameObject("PlantedGrowth");
                plantedRoot = root.transform;
            }
            return plantedRoot;
        }

        private static bool ReadRightButton(out bool down, out bool up, out Vector2 pos)
        {
#if ENABLE_INPUT_SYSTEM
            Mouse m = Mouse.current;
            if (m == null) { down = up = false; pos = default; return false; }
            down = m.rightButton.wasPressedThisFrame;
            up = m.rightButton.wasReleasedThisFrame;
            pos = m.position.ReadValue();
            return true;
#else
            down = Input.GetMouseButtonDown(1);
            up = Input.GetMouseButtonUp(1);
            pos = Input.mousePosition;
            return true;
#endif
        }
    }
}
