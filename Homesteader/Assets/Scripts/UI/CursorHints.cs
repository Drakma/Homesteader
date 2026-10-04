using Homesteader.Animals;
using Homesteader.Growth;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// Chooses the cursor every frame: the arrow by default, the pointing finger over anything clickable in the HUD, and
    /// the open hand over something in the world that a right click would pick up (a dropped item or log, ripe fruit on a
    /// planted or forest tree, berries on a bush) or a door that is close enough to open, the basket over ripe fruit the tool in hand can pick, the axe over a tree the tool in the active slot can fell, and the hammer over a construction site that has everything its next stage needs.
    ///
    /// UI Toolkit cannot be asked whether an element has a click handler, so elements wired by code carry the
    /// "clickable" class (see <see cref="CursorHintExtensions.Clickable{T}"/>); Buttons, toggles, sliders, dropdowns and
    /// text fields count by type.
    /// </summary>
    public sealed class CursorHints : MonoBehaviour
    {
        public const string ClickableClass = "clickable";

        private void LateUpdate()
        {
            CursorManager cm = CursorManager.Instance;
            if (cm == null || !cm.enabled) return;
            cm.SetCursor(Pick());
        }

        private static string Pick()
        {
            if (!HoverTarget.TryGetPointerPos(out Vector2 screenPos)) return CursorManager.Arrow;

            HudBindings hud = HudBindings.Instance;
            if (hud != null && hud.Root != null && hud.Root.panel != null && hud.IsPointerOverUI(screenPos))
            {
                IPanel panel = hud.Root.panel;
                Vector2 panelPos = RuntimePanelUtils.ScreenToPanel(panel, new Vector2(screenPos.x, Screen.height - screenPos.y));
                return IsClickable(panel.Pick(panelPos)) ? CursorManager.Finger : CursorManager.Arrow;
            }

            if (HudBindings.KeyboardCaptured) return CursorManager.Arrow;
            if (CanShearUnderCursor(screenPos)) return CursorManager.Shears;
            if (ChoppableTreeUnderCursor(screenPos)) return CursorManager.Axe;
            if (FruitPickableUnderCursor(screenPos)) return CursorManager.Basket;
            if (CanPickUpUnderCursor(screenPos) || DoorUnderCursor(screenPos)) return CursorManager.HandOpen;
            return BuildableUnderCursor() ? CursorManager.Hammer : CursorManager.Arrow;
        }

        /// <summary>The picked element or any ancestor is something a click does something to.</summary>
        private static bool IsClickable(VisualElement e)
        {
            for (; e != null; e = e.parent)
            {
                if (e is Button || e is Toggle || e is Scroller || e is BaseSlider<float> || e is BaseSlider<int>
                    || e is TextField || e is DropdownField || e is Foldout || e is RadioButton)
                    return true;
                if (e.ClassListContains(ClickableClass)) return true;
                if (e.ClassListContains("unity-base-popup-field") || e.ClassListContains("unity-base-text-field")) return true;
            }
            return false;
        }

        /// <summary>A tree under the cursor (a forest tree, or one the player planted) that the tool in the active slot can fell: a right click would swing at it.</summary>
        private static bool ChoppableTreeUnderCursor(Vector2 screenPos)
        {
            HudState state = HudState.Active;
            if (state == null || state.SelectedSlot < 0 || state.SelectedSlot >= state.Toolbar.Count) return false;
            ToolbarSlotData slot = state.Toolbar[state.SelectedSlot];
            if (string.IsNullOrEmpty(slot.IconId) || slot.Count <= 0) return false;
            string held = slot.IconId;
            Camera cam = HoverTarget.GameCamera();
            if (cam == null) return false;
            if (Homesteader.World.ForestTrees.CanFell(held)
                && Homesteader.World.ForestTrees.TryPick(cam.ScreenPointToRay(screenPos), out Homesteader.World.ForestTree tree)
                && Homesteader.World.ForestTrees.CanFellTree(tree, held))
                return true;
            // a planted tree that is grown enough to harvest, with the tool its growth group asks for in hand
            Transform hovered = HoverTarget.Find();
            if (hovered == null) return false;
            var plant = hovered.GetComponentInChildren<PlantedGrowth>() ?? hovered.GetComponentInParent<PlantedGrowth>();
            if (plant == null || plant.Group == null || plant.Group.GrowthType != "tree" || !plant.CanHarvest) return false;
            GrowthRules rules = plant.Group.Rules;
            return !string.IsNullOrEmpty(rules.YieldItemId) && rules.YieldAmountMax > 0 && !string.IsNullOrEmpty(rules.YieldTool)
                && GrowthRegistry.ToolMatches(rules.YieldTool, held);
        }

        /// <summary>Ripe fruit under the cursor (a berry bush, a forest tree or a planted plant) and the right picking tool in the active slot: the basket.</summary>
        private static bool FruitPickableUnderCursor(Vector2 screenPos)
        {
            HudState state = HudState.Active;
            string held = null;
            if (state != null && state.SelectedSlot >= 0 && state.SelectedSlot < state.Toolbar.Count)
            {
                ToolbarSlotData slot = state.Toolbar[state.SelectedSlot];
                if (!string.IsNullOrEmpty(slot.IconId) && slot.Count > 0) held = slot.IconId;
            }
            if (held == null) return false;
            Camera cam = HoverTarget.GameCamera();
            if (cam == null) return false;
            Ray ray = cam.ScreenPointToRay(screenPos);
            if (Homesteader.World.BerryBushes.TryPick(ray, out Homesteader.World.BerryBush bush) && Homesteader.World.BerryBushes.CanPickWith(bush, held)) return true;
            if (Homesteader.World.ForestTrees.TryPick(ray, out Homesteader.World.ForestTree tree) && Homesteader.World.ForestTrees.CanPickWith(tree, held)) return true;
            Transform hovered = HoverTarget.Find();
            if (hovered == null) return false;
            var plant = hovered.GetComponentInChildren<PlantedGrowth>() ?? hovered.GetComponentInParent<PlantedGrowth>();
            if (plant == null || !plant.CanPickFruit) return false;
            string need = plant.Group.Rules.FruitTool;
            return string.IsNullOrEmpty(need) || GrowthRegistry.ToolMatches(need, held);
        }

        private static PedController _ped;

        /// <summary>A door of a building under the cursor that a right click would open or shut from where the player stands.</summary>
        private static bool DoorUnderCursor(Vector2 screenPos)
        {
            Camera cam = HoverTarget.GameCamera();
            if (cam == null || ConstructionSite.All.Count == 0) return false;
            if (_ped == null) _ped = Object.FindAnyObjectByType<PedController>();
            if (_ped == null) return false;
            Ray ray = cam.ScreenPointToRay(screenPos);
            foreach (ConstructionSite site in ConstructionSite.All)
                if (site != null && site.DoorUnderCursor(ray, _ped.transform.position)) return true;
            return false;
        }

        /// <summary>A construction site under the cursor whose current stage has everything it needs (materials and tools): a right click builds it.</summary>
        private static bool BuildableUnderCursor()
        {
            Transform hovered = HoverTarget.Find();
            if (hovered == null) return false;
            ConstructionSite site = hovered.GetComponentInParent<ConstructionSite>();
            return site != null && !site.Building && site.Ready;
        }

        /// <summary>The item the sheep shears are (the active toolbar slot must hold it for the shears cursor).</summary>
        public const string SheepShearsId = "tool_shears_sheepwool";

        /// <summary>Sheep shears in the active slot and a sheep that can be sheared under the cursor.</summary>
        private static bool CanShearUnderCursor(Vector2 screenPos)
        {
            HudState state = HudState.Active;
            if (state == null || state.SelectedSlot < 0 || state.SelectedSlot >= state.Toolbar.Count) return false;
            ToolbarSlotData slot = state.Toolbar[state.SelectedSlot];
            if (slot.Count <= 0 || slot.IconId != SheepShearsId) return false;

            Camera cam = HoverTarget.GameCamera();
            if (cam == null) return false;

            // Animals may or may not carry a collider, so take the one nearest the mouse ray (as dropped items are found).
            Ray ray = cam.ScreenPointToRay(screenPos);
            AnimalBrain best = null;
            float bestDist = 0.8f;
            foreach (AnimalBrain a in AnimalBrain.All)
            {
                if (a == null) continue;
                Vector3 p = a.transform.position + Vector3.up * 0.5f;
                float d = Vector3.Cross(ray.direction, p - ray.origin).magnitude;
                if (d < bestDist) { bestDist = d; best = a; }
            }
            return best != null && CanBeSheared(best);
        }

        /// <summary>
        /// Whether this animal can be sheared right now. There is no shearing action or wool regrowth in the game yet, so
        /// today this means "a grown sheep"; when shearing lands, its own check (fleece ready, in reach) replaces the body.
        /// </summary>
        public static bool CanBeSheared(AnimalBrain animal)
        {
            if (animal == null) return false;
            string species = (animal.Species ?? "").ToLowerInvariant();
            string name = animal.gameObject.name.ToLowerInvariant();
            bool sheep = species.Contains("sheep") || name.Contains("sheep");
            bool lamb = species.Contains("lamb") || name.Contains("lamb");
            return sheep && !lamb;
        }

        /// <summary>Mirrors what a plain right click picks up in PlacementController / PlantingController.</summary>
        private static bool CanPickUpUnderCursor(Vector2 screenPos)
        {
            Camera cam = HoverTarget.GameCamera();
            if (cam == null) return false;

            if (WorldItem.UnderCursor(cam, screenPos) != null) return true;

            Ray ray = cam.ScreenPointToRay(screenPos);
            if (Homesteader.World.ForestTrees.TryPick(ray, out Homesteader.World.ForestTree tree) && Homesteader.World.ForestTrees.CanPick(tree)) return true;
            if (Homesteader.World.BerryBushes.TryPick(ray, out Homesteader.World.BerryBush bush) && Homesteader.World.BerryBushes.CanPick(bush)) return true;

            Transform hovered = HoverTarget.Find();
            if (hovered != null)
            {
                var growth = hovered.GetComponentInChildren<PlantedGrowth>() ?? hovered.GetComponentInParent<PlantedGrowth>();
                if (growth != null && growth.CanPickFruit) return true;
            }
            return false;
        }
    }

    public static class CursorHintExtensions
    {
        /// <summary>
        /// Marks an element as something a click acts on, so the cursor shows the finger over it. Returns the element
        /// (null-safe) so it chains in front of RegisterCallback.
        /// </summary>
        public static T Clickable<T>(this T e) where T : VisualElement
        {
            e?.AddToClassList(CursorHints.ClickableClass);
            return e;
        }
    }
}
