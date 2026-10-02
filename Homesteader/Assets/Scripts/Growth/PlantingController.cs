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
            // Survives the scene reload New Game / Continue does: [RuntimeInitializeOnLoadMethod(AfterSceneLoad)] runs
            // only once at startup, so a controller that is not persistent is gone after the first reload and never comes back.
            var go = new GameObject("PlantingController");
            DontDestroyOnLoad(go);
            go.AddComponent<PlantingController>();
        }

        // Holding the right button on a tree with the felling tool keeps chopping (a click chops once).
        private const float HoldStartSeconds = 0.2f;
        private bool chopStarted;       // this press became a chop: the release must not also be a click
        private float nextSwing;
        private float workUntil;        // a single click plays the chop clip for a moment
        private PedController workPed;
        private Homesteader.World.ForestTree pendingTree;   // a clicked swing waiting for its impact frame
        private string pendingHeld;

        private void Update()
        {
            if (!ReadRightButton(out bool down, out bool up, out Vector2 pos)) return;

            // A clicked swing: the hit lands when the axe does (or when the clip ran out without us seeing it).
            if (pendingTree != null)
            {
                if (workPed == null || ImpactReached(workPed) || Time.unscaledTime > workUntil)
                {
                    Homesteader.World.ForestTrees.TryChop(pendingTree, pendingHeld, workPed != null ? workPed.transform : null);
                    pendingTree = null;
                }
            }

            // A missed release (focus lost, a skipped frame) must not leave the button "held": that kept the axe chopping by itself.
            if (pressed && !down && !up && !RightButtonHeld())
            {
                pressed = false;
                chopStarted = false;
                if (workPed != null) workPed.EndWork(Homesteader.World.ForestTrees.ChopClip);
                workPed = null;
                return;
            }

            // A click's chop clip ends by itself.
            if (workPed != null && !chopStarted && Time.unscaledTime > workUntil)
            {
                workPed.EndWork(Homesteader.World.ForestTrees.ChopClip);
                workPed = null;
            }

            if (down)
            {
                pressed = true;
                chopStarted = false;
                pressPos = pos;
                pressTime = Time.unscaledTime;
                return;
            }

            if (pressed && !up) HoldChop(pos);

            if (!up || !pressed) return;
            pressed = false;

            if (chopStarted)
            {
                // The press was a chop: stop the swing and do not treat the release as a click.
                chopStarted = false;
                if (workPed != null) workPed.EndWork(Homesteader.World.ForestTrees.ChopClip);
                workPed = null;
                return;
            }

            bool isClick = (pos - pressPos).magnitude <= ClickMaxTravelPx
                        && Time.unscaledTime - pressTime <= ClickMaxSeconds;
            if (isClick) TryPlant(pos);
        }

        /// <summary>The button is still down: while the pointer rests on a tree and the felling tool is in the active slot, swing.</summary>
        private void HoldChop(Vector2 pos)
        {
            if ((pos - pressPos).magnitude > ClickMaxTravelPx)
            {
                // Dragging: that is the camera pan, not a chop.
                if (chopStarted && workPed != null) workPed.EndWork(Homesteader.World.ForestTrees.ChopClip);
                chopStarted = false;
                return;
            }
            if (Time.unscaledTime - pressTime < HoldStartSeconds) return;

            if (!TryGetChopTarget(pos, out Homesteader.World.ForestTree tree, out string heldId, out PedController ped))
            {
                if (chopStarted && workPed != null) workPed.EndWork(Homesteader.World.ForestTrees.ChopClip);
                return;
            }

            chopStarted = true;
            workPed = ped;
            if (ped != null) ped.BeginWork(Homesteader.World.ForestTrees.ChopClip, tree.Position);
            // The hit (sound, chips, damage) lands when the axe does: on the clip's impact frame each cycle.
            if (!ImpactReached(ped)) return;

            if (Homesteader.World.ForestTrees.TryChop(tree, heldId, ped != null ? ped.transform : null))
            {
                // It came down.
                if (ped != null) ped.EndWork(Homesteader.World.ForestTrees.ChopClip);
                chopStarted = false;
            }
        }

        private float _prevPhase = -1f;

        /// <summary>True once per cycle, on the frame the chop clip passes its impact point. Without a running clip, falls back to a timer.</summary>
        private bool ImpactReached(PedController ped)
        {
            if (ped != null && ped.WorkPhase(Homesteader.World.ForestTrees.ChopClip, out float phase, out float length))
            {
                float impact = Homesteader.World.ForestTrees.ChopImpact;
                bool hit = _prevPhase >= 0f && _prevPhase < impact && phase >= impact;
                _prevPhase = phase;
                return hit;
            }
            _prevPhase = -1f;
            if (Time.unscaledTime < nextSwing) return false;
            nextSwing = Time.unscaledTime + Homesteader.World.ForestTrees.SwingSeconds;
            return true;
        }

        /// <summary>The tree under the pointer if the item in the active slot fells it (same gates as a click).</summary>
        private bool TryGetChopTarget(Vector2 screenPos, out Homesteader.World.ForestTree tree, out string heldId, out PedController ped)
        {
            tree = null;
            heldId = null;
            ped = null;
            HudBindings hud = HudBindings.Instance;
            if (hud == null || HudBindings.KeyboardCaptured || hud.IsPointerOverUI(screenPos)) return false;
            Camera cam = GameCamera();
            if (cam == null) return false;

            HudState state = HudState.Active;
            if (state.SelectedSlot < 0 || state.SelectedSlot >= state.Toolbar.Count) return false;
            ToolbarSlotData slot = state.Toolbar[state.SelectedSlot];
            if (string.IsNullOrEmpty(slot.IconId) || slot.Count <= 0) return false;
            heldId = slot.IconId;
            if (!Homesteader.World.ForestTrees.CanFell(heldId)) return false;
            if (!Homesteader.World.ForestTrees.TryPick(cam.ScreenPointToRay(screenPos), out tree)) return false;
            if (!Homesteader.World.ForestTrees.CanFellTree(tree, heldId)) { tree = null; return false; }
            ped = FindAnyObjectByType<PedController>();
            return true;
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


            // Holding an axe: a right-click on a forest tree chops it (the trees have no colliders, so pick by ray).
            if (heldId != null && Homesteader.World.ForestTrees.CanFell(heldId)
                && Homesteader.World.ForestTrees.TryPick(cam.ScreenPointToRay(screenPos), out Homesteader.World.ForestTree tree)
                && Homesteader.World.ForestTrees.CanFellTree(tree, heldId))
            {
                var chopper = FindAnyObjectByType<PedController>();
                if (chopper != null && chopper.BeginWork(Homesteader.World.ForestTrees.ChopClip, tree.Position))
                {
                    // One swing: the hit lands on the clip's impact frame (see Update).
                    workPed = chopper;
                    workUntil = Time.unscaledTime + Homesteader.World.ForestTrees.SwingSeconds + 0.3f;
                    pendingTree = tree;
                    pendingHeld = heldId;
                    _prevPhase = -1f;
                }
                else
                {
                    Homesteader.World.ForestTrees.TryChop(tree, heldId, chopper != null ? chopper.transform : null);
                }
                return;
            }

            // A fruiting tree with ripe fruit: right-click picks it by hand (the tree stays).
            if (!canPlant && Homesteader.World.ForestTrees.TryPick(cam.ScreenPointToRay(screenPos), out Homesteader.World.ForestTree fruitTree)
                && Homesteader.World.ForestTrees.CanPick(fruitTree))
            {
                var picker = FindAnyObjectByType<PedController>();
                Homesteader.World.ForestTrees.TryPickFruit(fruitTree, picker != null ? picker.transform : null, heldId);
                return;
            }

            // A berry bush under the cursor: right-click picks ONE berry (kit rules: the bush asset's 'fruiting' schema).
            if (!canPlant && Homesteader.World.BerryBushes.TryPick(cam.ScreenPointToRay(screenPos), out Homesteader.World.BerryBush bush) && Homesteader.World.BerryBushes.HasRules(bush))
            {
                var berryPicker = FindAnyObjectByType<PedController>();
                Homesteader.World.BerryBushes.TryPickBerry(bush, berryPicker != null ? berryPicker.transform : null, heldId);
                return;
            }

            // A forest tree under the cursor and nothing in hand that plants or fells: say what to do.
            if (!canPlant && Homesteader.World.ForestTrees.TryPick(cam.ScreenPointToRay(screenPos), out Homesteader.World.ForestTree hinted)
                && !Homesteader.World.ForestTrees.CanFellTree(hinted, heldId))
            {
                Homesteader.World.ForestTrees.HintTool(hinted, heldId);
                return;
            }

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
                // Ripe fruit is picked by hand, unless the harvest tool (the axe that fells it) is in hand: then the click harvests the tree.
                string tool = existing.Group.Rules.YieldTool;
                bool holdingTool = !string.IsNullOrEmpty(tool) && GrowthRegistry.ToolMatches(tool, heldId);
                if (existing.CanPickFruit && !holdingTool)
                {
                    if (!PlantingValidator.InReach(ped != null ? ped.transform : null, hit.point, GameRules.HarvestReachCells))
                        ToastNotificationSystem.ShowWarning("Too far", "You can only pick the fruit from the squares right next to you.");
                    else
                        existing.PickFruit(heldId, ped != null ? ped.transform : null);
                    return;
                }
                // The tool in hand fits the FRUIT (the basket) but nothing is ripe: that is allowed, there is just nothing to do.
                string fruitTool = existing.Group.Rules.FruitTool;
                if (!string.IsNullOrEmpty(fruitTool) && GrowthRegistry.ToolMatches(fruitTool, heldId))
                {
                    ToastNotificationSystem.ShowInfo(existing.Group.Name, "No ripe fruit right now.");
                    return;
                }
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
            bool extrasFit = rules.YieldExtras.Count == 0 || GrowthDrop.Give(rules.YieldExtras);
            if (added < amount || !extrasFit)
                ToastNotificationSystem.ShowWarning("Toolbar full", "Some of the harvest didn't fit and was lost.");

            plant.Harvested();
        }

        private static string DescribeTool(string spec)
        {
            var names = new System.Collections.Generic.List<string>();
            foreach (string one in spec.Split(','))
            {
                string s = one.Trim();
                if (s.Length == 0) continue;
                names.Add(s.StartsWith("#") ? $"a {s.Substring(1).Replace('_', ' ')}" : HudBindings.GetItemName(s));
            }
            return string.Join(" or ", names);
        }

        /// <summary>
        /// The first thing under the cursor, ignoring the player. It must be
        /// terrain for planting to proceed, so a building or prop in front of the
        /// ground blocks the click rather than being planted through.
        /// </summary>
        private static bool TryGroundHit(Camera cam, Vector2 screenPos, out RaycastHit result)
        {
            result = default;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(screenPos), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
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

        private static bool RightButtonHeld()
        {
#if ENABLE_INPUT_SYSTEM
            Mouse m = Mouse.current;
            return m != null && m.rightButton.isPressed;
#else
            return Input.GetMouseButton(1);
#endif
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
