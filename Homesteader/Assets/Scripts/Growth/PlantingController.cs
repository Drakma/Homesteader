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
            if (FindFirstObjectByType<PlantingController>() != null) return;
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

        private void TryPlant(Vector2 screenPos)
        {
            HudBindings hud = HudBindings.Instance;
            if (hud == null) return;
            // A window/text field owns input, or the click landed on the HUD.
            if (HudBindings.KeyboardCaptured || hud.IsPointerOverUI(screenPos)) return;

            HudState state = HudState.Active;
            if (state.SelectedSlot < 0 || state.SelectedSlot >= state.Toolbar.Count) return;
            ToolbarSlotData slot = state.Toolbar[state.SelectedSlot];
            if (string.IsNullOrEmpty(slot.IconId) || slot.Count <= 0) return;

            if (!GrowthRegistry.TryGetUse(slot.IconId, out UseBehavior use)
                || use.Action != UseBehavior.PlantGrowthGroup)
                return;   // this item has no right-click plant behaviour

            if (!GrowthRegistry.TryGetGroup(use.GroupId, use.Namespace, out GrowthGroup group))
            {
                ToastNotificationSystem.ShowError("Can't plant",
                    $"The growth group '{use.GroupId}' isn't loaded. Is its mod installed?");
                return;
            }

            Camera cam = Camera.main;
            if (cam == null) return;

            if (!TryGroundHit(cam, screenPos, out RaycastHit hit))
            {
                ToastNotificationSystem.ShowWarning("Can't plant", "You can only plant in open ground.");
                return;
            }

            var ped = FindFirstObjectByType<PedController>();
            if (!PlantingValidator.Validate(group, hit, ped != null ? ped.transform : null, out string reason))
            {
                ToastNotificationSystem.ShowWarning("Can't plant here", reason);
                return;
            }

            if (!state.ConsumeFromSelectedSlot(1)) return;
            hud.RefreshToolbar();

            PlantedGrowth.Plant(group, hit.point, PlantedRoot());
            ToastNotificationSystem.ShowSuccess("Planted", $"Planted {group.Name}.");
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
