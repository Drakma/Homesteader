using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Homesteader.Growth
{
    /// <summary>
    /// Placing structures and props. When the selected toolbar item is placeable (it has a model and its manifest sets
    /// properties.placeable = true; the category does not matter), the first left click brings out a translucent "shadow"
    /// copy of its model that follows the grid square under the cursor. Squares within placement.reach_cells of the player
    /// (default 1) are valid (tinted blue), others are not (tinted red). R turns it by placement.rotate_step_deg
    /// (default 22.5 degrees, Shift+R turns the other way). Enter or a second left click on a valid square consumes one
    /// item (Esc, walking or another slot puts the shadow away); the shadow fades to solid and stays until something removes it (<see cref="PlacedObject.Remove"/>).
    ///
    /// Bootstraps itself after the scene loads, so no scene edit is needed. Keys: docs/CONTROLS.md.
    /// </summary>
    public sealed class PlacementController : MonoBehaviour
    {
        private static readonly Color ValidTint = new Color(0.55f, 0.8f, 1f);
        private static readonly Color InvalidTint = new Color(1f, 0.35f, 0.3f);
        private const float GhostAlpha = 0.45f;

        private string ghostItemId;
        private bool ghostStructureModel;   // the structure shadow is the real foundation model (not the stand-in slab)
        private GameObject ghost;
        private int rotationSteps;
        private bool _mirror;       // T: the shadow is mirrored left to right (a negative x scale), and so is the object placed from it (saved: SavedPlaced.mirrored)
        private bool _runSnapped;   // the shadow of a kitchen piece is snapped to a neighbour or a wall: R then turns it a quarter turn on its snap (KitchenRun.cs)
        private int _runTurns;
        private Transform placedRoot;
        private string lastReason;
        private bool placing;            // the shadow is out: the first click started it, Enter or a second click places it
        private string placingId;
        private int placingStartFrame;
        private Vector3 placingPedPos;   // where the player stood when the shadow came out: walking away puts it back

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<PlacementController>() != null) return;
            // Survives the scene reload New Game / Continue does: [RuntimeInitializeOnLoadMethod(AfterSceneLoad)] runs
            // only once at startup, so a controller that is not persistent is gone after the first reload and never comes back.
            var go = new GameObject("PlacementController");
            DontDestroyOnLoad(go);
            go.AddComponent<PlacementController>();
        }

        private void Update()
        {
            HudBindings hud = HudBindings.Instance;
            if (hud == null || HudBindings.KeyboardCaptured || AreaTidy.Active) { HideGhost(); return; }   // (the tidy mode owns the left button)

            HandlePickupClick(hud);   // right click on a placed object takes it back
            if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.DropItem)) DropHeldItem();
            if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.Consume)) Homesteader.Kitchen.Consumption.TryConsumeHeld();
            // a left click with an uncut log in hand over a sawmill lays it on the track
            if (!placing && PlaceClicked() && !hud.IsPointerOverUI(PointerPosition()) && Sawmill.TryLoadHeld(GameCamera(), PointerPosition())) return;
            // a left click with an item in hand over a wall shelf stands one on it (before anything else takes the click)
            if (!placing && AttachedObject.All.Count > 0 && PlaceClicked() && !hud.IsPointerOverUI(PointerPosition()) && (NetRack.TryPutHeld(GameCamera(), PointerPosition()) || Shelf.TryPutHeld(GameCamera(), PointerPosition()))) return;

            string heldId = HeldItemId();
            string siteId = SiteIdOf(heldId);               // the structure the held item starts: a blueprint itself, or a kit (properties.builds_structure)
            bool structure = siteId != null;
            ItemRegistry.ItemInfo info = null;
            if (!IsPlaceable(heldId) && !string.IsNullOrEmpty(heldId))
            {
                // not placeable on its own, but it may go ON something (a solar panel on a mount): a left click with it over a mount that takes it fits it there
                Camera fitCam = GameCamera();
                if (fitCam != null && PlaceClicked() && !hud.IsPointerOverUI(PointerPosition())) TryFitHeld(heldId, fitCam);
            }
            if (!IsPlaceable(heldId) || (!structure && !ItemRegistry.TryGet(heldId, out info))) { placing = false; HideGhost(); return; }
            if (placing && heldId != placingId) placing = false;            // another item was selected
            if (placing && CancelPressed()) placing = false;
            if (placing)
            {
                var walker = PedController.Current;
                if (walker != null && (walker.transform.position - placingPedPos).sqrMagnitude > 0.0025f) placing = false;   // moved more than 5 cm
            }

            Vector2 pointer = PointerPosition();
            Camera cam = GameCamera();
            if (!hud.IsPointerOverUI(pointer) && AttachController.TakesRoofClick(heldId, cam, pointer)) { placing = false; HideGhost(); return; }   // over a roof it is put up there: the roof preview owns the click and R

            // A window item is never set on the ground: a left click puts it into the wall under the cursor (or swaps the window there), with nothing but a message when the cursor is not on a wall.
            if (StructureWindows.IsWindowItem(heldId) || StructureWindows.IsShutterItem(heldId))
            {
                placing = false;
                HideGhost();
                if (cam != null && !hud.IsPointerOverUI(pointer) && PlaceClicked()) StructureWindows.TryInstallAtCursor(cam, pointer, PedController.Current != null ? PedController.Current.transform : null);
                return;
            }

            // Not placing yet: a placeable item in hand does nothing until it is clicked. That click brings out the shadow.
            if (!placing)
            {
                HideGhost();
                if (cam != null && PlaceClicked() && !hud.IsPointerOverUI(pointer))
                {
                    if (AttachController.TakesRoofClick(heldId, cam, pointer)) return;   // a dish, yagi or access point aimed at a roof: it is put up there (AttachController)
                    if (TryInsertIntoRack(heldId)) return;   // over a battery rack that takes it: it slides into a slot
                    placing = true;
                    placingId = heldId;
                    placingStartFrame = Time.frameCount;
                    var starter = PedController.Current;
                    placingPedPos = starter != null ? starter.transform.position : Vector3.zero;
                }
                if (!placing) return;
            }

            if (RotatePressed(out bool reverse))
                if (KitchenRun.IsRun(heldId)) _runTurns = (_runTurns + (reverse ? 3 : 1)) & 3;   // a kitchen piece: R always turns it a quarter turn (on its snap, and free): kept where you left it
                else rotationSteps += reverse ? -1 : 1;

            if (cam == null || hud.IsPointerOverUI(pointer)) { HideGhost(); return; }

            if (!TryCursorPoint(cam, pointer, out Vector3 hitPoint)) { HideGhost(); return; }
            if (!EnsureGhost(structure ? siteId : heldId, info)) return;   // model still loading

            ghost.SetActive(true);
            // A structure turns in quarter turns so its walls stay on the grid; everything else turns by the usual step.
            ghost.transform.rotation = Quaternion.Euler(0f, rotationSteps * (structure ? 90f : GameRules.Placement.RotateStepDeg) + (!structure && KitchenRun.IsRun(heldId) ? 90f * _runTurns : 0f), 0f);
            if (!structure)
            {
                if (!HudBindings.KeyboardCaptured && Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.MirrorPlacement)) _mirror = !_mirror;
                Vector3 ms = ghost.transform.localScale;
                ms.x = Mathf.Abs(ms.x) * (_mirror ? -1f : 1f);
                ghost.transform.localScale = ms;   // T: mirrored left to right
            }
            else _mirror = false;
            var ped = PedController.Current;
            // Over a pallet's deck the item rests ON the pallet, in the pallet's own turn, packed in its free space.
            PlacedObject pallet = null;
            int deck = 0;
            Vector3 deckHit = hitPoint;
            if (!structure && !PalletDeck.IsPallet(heldId))
            {
                // a shelving unit is found by the ray (and the shelf it comes to), a pallet by the point on the ground
                // a small kitchen item (a cooktop): the counter whose top the ray meets (the ground point behind it would only find the counter at its far edge)
                if (KitchenRun.CountertopItem(heldId, GhostHeight()) && KitchenRun.CounterUnderRay(cam.ScreenPointToRay(pointer), out pallet)) deck = 0;
                else if (!PalletDeck.UnderRay(cam.ScreenPointToRay(pointer), out pallet, out deck, out deckHit)) pallet = PalletDeck.PalletUnder(hitPoint);
            }
            Plan plan;
            if (pallet != null) plan = MakePalletPlan(pallet, heldId, deckHit, ped != null ? ped.transform : null, deck);
            else plan = structure ? MakeSitePlan(siteId, hitPoint, ghost.transform.rotation.eulerAngles.y, ped != null ? ped.transform : null)
                                  : MakePlan(heldId, hitPoint, GhostFootprint(), ped != null ? ped.transform : null);
            lastReason = plan.Reason;
            AssetCatalogItem siteInfo = structure ? HudBindings.GetCatalogItem(siteId) : null;
            WellPreview = siteInfo != null && siteInfo.is_well ? plan.Position : (Vector3?)null;   // a well blueprint: the water under the spot is shown as it is moved
            WellPreviewId = siteId;

            ghost.transform.position = plan.Position;
            if (!structure) Net.Preview(heldId, plan.Position, ghost.transform.forward);   // a yagi: its signal shows while it is aimed
            GhostVisual.Apply(ghost, plan.Valid ? ValidTint : InvalidTint, GhostAlpha);

            // Enter, or a second click, puts it down.
            bool confirm = ConfirmPressed() || (PlaceClicked() && Time.frameCount != placingStartFrame);
            if (confirm && TryInsertIntoRack(heldId)) { placing = false; HideGhost(); return; }
            if (confirm)
            {
                if (!plan.Valid) { ToastNotificationSystem.ShowWarning("Can't place here", plan.Reason); return; }
                if (structure) PlaceSite(heldId, siteId, plan, ghost.transform.rotation.eulerAngles.y);
                else Place(heldId, info, plan, ghost.transform.rotation);
                placing = false;
                HideGhost();
            }
        }

        // ------------------------------------------------------------------ dropping

        /// <summary>
        /// The drop key: puts ONE of the held item on the ground in front of the player (Shift: the whole stack, up to 24). A container that
        /// holds things is placed as itself so its contents stay in it; an item with a model or an icon lies there as a dropped item.
        /// </summary>
        private static void DropHeldItem()
        {
            HudState hud = HudState.Active;
            if (hud == null || HudBindings.KeyboardCaptured) return;
            hud.EnsureToolbarSlots();
            if (hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return;
            ToolbarSlotData slot = hud.Toolbar[hud.SelectedSlot];
            if (string.IsNullOrEmpty(slot.IconId) || slot.Count <= 0) return;
            if (Blueprints.IsBlueprint(slot.IconId)) { ToastNotificationSystem.ShowInfo("Blueprint", "A blueprint is yours for good and cannot be dropped."); return; }
            var ped = PedController.Current;
            if (ped == null) return;

            string id = slot.IconId;
            bool all = Keyboard.current != null && Keyboard.current.shiftKey.isPressed;
            int count = all ? Mathf.Min(slot.Count, 24) : 1;
            Vector3 facing = Quaternion.Euler(0f, ped.transform.eulerAngles.y - ped.modelRotationOffset, 0f) * Vector3.forward;
            Vector3 front = ped.transform.position + facing * 1.2f;

            // a push item (a wheelbarrow) is put down standing, empty or not
            if ((WheelbarrowPush.IsPushItem(id) || WheelbarrowPush.IsPile(id)) && ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo pushInfo) && pushInfo.Prefab != null)
            {
                if (!hud.ConsumeFromSelectedSlot(1)) return;
                PlacedObject set = PlacementController.SpawnPlaced(id, pushInfo, PlantingValidator.SnapToGrid(front), 0f, false, 0, slot.Contents);
                HudBindings.Instance?.RefreshToolbar();
                return;
            }

            if (slot.WireUsed > 0.01f && ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo wireInfo) && wireInfo.Prefab != null)
            {
                // a partly used coil or spool is put down as itself, so the metres used stay with it
                float used = slot.WireUsed;
                int usedSlot = hud.SelectedSlot;
                if (!hud.ConsumeFromSelectedSlot(1)) return;
                ClearWireUsed(hud, usedSlot);
                PlacedObject spool = SpawnPlaced(id, wireInfo, PlantingValidator.SnapToGrid(front), 0f, false, 0, null);
                if (spool != null) spool.WireUsed = used;
                HudBindings.Instance?.RefreshToolbar();
                return;
            }

            bool holdsThings = slot.Contents != null && slot.Contents.Count > 0;
            if (holdsThings)
            {
                // a container with things in it keeps them: it stands on the ground as itself
                if (!ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo info) || info.Prefab == null || !info.PlayerPlaceable)
                {
                    ToastNotificationSystem.ShowInfo("Can't drop", "Empty it first, or place it.");
                    return;
                }
                if (!hud.ConsumeFromSelectedSlot(1)) return;
                SpawnPlaced(id, info, PlantingValidator.SnapToGrid(front), 0f, false, 0, slot.Contents);
                HudBindings.Instance?.RefreshToolbar();
                return;
            }

            int dropped = 0;
            for (int i = 0; i < count; i++)
            {
                if (!hud.ConsumeFromSelectedSlot(1)) break;
                Vector2 jitter = Random.insideUnitCircle * (i == 0 ? 0f : 0.9f);
                if (!WorldItem.TryDrop(id, front + new Vector3(jitter.x, 0f, jitter.y)))
                {
                    hud.AddItemToToolbar(id, 1, HudBindings.GetMaxStack(id));   // nothing to show for it: give it back
                    break;
                }
                dropped++;
            }
            HudBindings.Instance?.RefreshToolbar();
        }

        // ------------------------------------------------------------------ picking up

        private bool _pickDown;
        private Vector2 _pickDownPos;

        /// <summary>
        /// A right CLICK (not a drag: dragging with the right button pans the camera) on a placed object takes the top
        /// one of its stack back into the toolbar, with whatever it holds. Trees, plants and the tool in hand are not
        /// touched: only a direct hit on a placed object counts.
        /// </summary>
        private void HandlePickupClick(HudBindings hud)
        {
            Mouse mouse = Mouse.current;
            if (mouse == null) { _pickDown = false; return; }
            Vector2 pointer = mouse.position.ReadValue();
            if (mouse.rightButton.wasPressedThisFrame)
            {
                _pickDown = !hud.IsPointerOverUI(pointer);
                _pickDownPos = pointer;
                return;
            }
            if (!_pickDown || !mouse.rightButton.wasReleasedThisFrame) return;
            _pickDown = false;
            if ((pointer - _pickDownPos).sqrMagnitude > 36f) return;   // a camera drag, not a click

            // A right click on a breaker box or light mounted on a building takes it down.
            {
                Camera mountCam = GameCamera();
                var mountPed = PedController.Current;
                if (mountCam != null && LightEmitter.TryRightClick(mountCam, pointer, mountPed != null ? mountPed.transform : null)) return;   // a light: switches it off or on (a wrench takes it down)
                if (mountCam != null && StructureWindows.TryRightClick(mountCam, pointer, mountPed != null ? mountPed.transform : null)) return;   // a wrench on a window: it is picked up and slides along its wall
                if (mountCam != null && Sawmill.TryRightClick(mountCam, pointer)) return;   // a sawmill: asks what to cut (Shift: the log off again)
                if (mountCam != null && NetRack.TryTake(mountCam, pointer)) return;   // a router or switch in a wall rack: back into the toolbar
                if (mountCam != null && Shelf.TryTake(mountCam, pointer)) return;   // a thing on a wall shelf: back into the toolbar
                if (mountCam != null && PropaneFill.TryRightClick(mountCam, pointer, mountPed != null ? mountPed.transform : null)) return;
                if (mountCam != null && WaterTap.TryRightClick(mountCam, pointer, mountPed != null ? mountPed.transform : null)) return;   // a water container in hand, on a spigot or faucet: fills it   // a portable propane tank in hand, on a fill post: fills it
                if (mountCam != null && FuelNozzle.TryRightClick(mountCam, pointer, mountPed != null ? mountPed.transform : null)) return;   // a fuel pump: take or hang up the nozzle; with it in hand, fill a container
                if (Fixtures.TryRightClick(mountPed != null ? mountPed.transform : null)) return;
                if (mountCam != null && Disconnect.TryRightClick(mountCam, pointer, mountPed != null ? mountPed.transform : null)) return;   // a safety disconnect: throws it on or off   // a sink, toilet, shower or washer in a building: uses it (Shift + right click picks it up)
                if (mountCam != null && WireTool.TryRightClick(mountCam, pointer, mountPed != null ? mountPed.transform : null)) return;   // wire cutters in hand: wire two devices (or cut the wire)
                if (mountCam != null && AttachedObject.TryFitAtRay(mountCam.ScreenPointToRay(pointer), mountPed != null ? mountPed.transform.position : Vector3.zero)) return;   // a panel in hand on a roof rack
                if (mountCam != null && PlacedChimney.TryPickUpAtRay(mountCam.ScreenPointToRay(pointer), mountPed != null ? mountPed.transform.position : Vector3.zero)) return;   // a chimney: Shift + right click with a wrench takes it down
                if (mountCam != null && AttachedObject.TryPickUpAtRay(mountCam.ScreenPointToRay(pointer), mountPed != null ? mountPed.transform.position : Vector3.zero)) return;
            }

            // A right click on a fence post with an axe (or on a wire fence with wire cutters) takes that section down; on a gate it opens or shuts it.
            {
                Camera gateCam = GameCamera();
                if (gateCam != null && FenceBuilder.TryChopPost(gateCam.ScreenPointToRay(pointer), ConstructionSite.HeldItem())) return;
                var gatePed = PedController.Current;
                if (gateCam != null && FenceBuilder.TryToggleGate(gateCam.ScreenPointToRay(pointer), gatePed != null ? gatePed.transform : null)) return;
            }
            if (WireTool.CuttersHeld())
            {
                // a door still opens with the cutters in hand (they are in hand most of the time while a building is wired and cabled)
                Camera cutCam = GameCamera();
                var cutPed = PedController.Current;
                if (cutCam != null)
                {
                    Ray cutRay = cutCam.ScreenPointToRay(pointer);
                    foreach (ConstructionSite cs in new List<ConstructionSite>(ConstructionSite.All))
                        if (cs != null && cs.TryDoorAtCursor(cutRay, cutPed != null ? cutPed.transform : null)) return;
                }
            }
            if (WireTool.CuttersHeld()) return;   // the cutters only cut wire (and wire fences): a click that found nothing must not go on to move or take things (they went into a container under the cursor)

            // Pushing a wheelbarrow: Shift + right click empties it on the ground (and keeps pushing), any other right click puts it down.
            if (WheelbarrowPush.Active != null)
            {
                // the wheelbarrow has to be DOWN to be filled: while it is pushed, a right click puts it down (Shift + right click empties it)
                if (Keyboard.current != null && Keyboard.current.shiftKey.isPressed) WheelbarrowPush.Active.Dump();
                else WheelbarrowPush.Active.PutDown();
                return;
            }

            // A right click with a paint can in the active slot paints the wall under the cursor (one wall, the side that was clicked).
            {
                string held = ConstructionSite.HeldItem();
                Camera paintCam = GameCamera();
                if (held != null && held.StartsWith("building_paint_") && paintCam != null)
                {
                    var paintPed = PedController.Current;
                    if (ConstructionSite.TryPaintAtRay(paintCam.ScreenPointToRay(pointer), held, paintPed != null ? paintPed.transform : null)) return;
                    if (PlacedObject.TryPaintAtRay(paintCam.ScreenPointToRay(pointer), held, paintPed != null ? paintPed.transform : null)) return;   // a placed door
                }
            }

            // A right click with a straw bale in the active slot on the floor of a building spreads bedding over that room; with a shovel on the
            // bedding it is mucked out again.
            {
                string beddingHeld = ConstructionSite.HeldItem();
                Camera beddingCam = GameCamera();
                if (beddingHeld != null && beddingCam != null)
                {
                    var beddingPed = PedController.Current;
                    Ray beddingRay = beddingCam.ScreenPointToRay(pointer);
                    if (StrawBedding.TrySpreadAtRay(beddingRay, beddingHeld, beddingPed != null ? beddingPed.transform : null)) return;
                    if (StrawBedding.TryMuckOutAtRay(beddingRay, beddingHeld, beddingPed != null ? beddingPed.transform : null)) return;
                }
            }

            // A right click with a pickaxe on a stone (a rock of the world, a stone item on the ground) breaks it into aggregate.
            {
                Camera stoneCam = GameCamera();
                var stonePed = PedController.Current;
                if (stoneCam != null && StoneBreaker.TryBreak(stoneCam, pointer, stonePed != null ? stonePed.transform : null)) return;
            }

            // A right click aimed at an interior door of a building swings it (before anything else reads the click as "build").
            {
                Camera doorCam = GameCamera();
                var doorPed = PedController.Current;
                if (doorCam != null)
                {
                    Ray doorRay = doorCam.ScreenPointToRay(pointer);
                    foreach (ConstructionSite cs in new List<ConstructionSite>(ConstructionSite.All))
                        if (cs != null && cs.TryDoorAtCursor(doorRay, doorPed != null ? doorPed.transform : null)) return;
                }
            }

            // An item lying on the floor of a building: the click that reaches it is for the item, not for the building it lies in (the floor is part of
            // the site, so the site branch below would take the click). Only when nothing of the building stands between the camera and the item:
            // a roof or a wall in front of it (the cutaway hides them while the player is inside) means it is not the item that was clicked.
            {
                Camera floorCam = GameCamera();
                WorldItem onFloor = floorCam != null ? WorldItem.UnderCursor(floorCam, pointer) : null;
                if (onFloor != null && onFloor.TryBounds(out Bounds floorBounds))
                {
                    Ray floorRay = floorCam.ScreenPointToRay(pointer);
                    float toItem = Vector3.Dot(floorBounds.center - floorRay.origin, floorRay.direction);
                    if (!ConstructionSite.SolidBefore(floorRay, toItem))
                    {
                        var floorPed = PedController.Current;
                        onFloor.PickUp(floorPed != null ? floorPed.transform : null);
                        return;
                    }
                }
            }

            // A right click on a construction site itself (its dirt area or structure) builds the next stage when it is ready.
            ConstructionSite site = ConstructionSite.UnderCursor();
            if (site != null)
            {
                var builder = PedController.Current;
                // Admin: Alt + right click with a hammer in hand removes the structure entirely, at any stage (and everything mounted on it).
                if (Keyboard.current != null && Keyboard.current.altKey.isPressed && (ConstructionSite.HeldItem() ?? "").StartsWith("tool_hammer"))
                {
                    site.AdminRemove();
                    return;
                }
                // TEMPORARY test shortcut: Alt + right click builds the next stage at once, without materials (see ConstructionSite.TryBuildFree).
                if (Keyboard.current != null && Keyboard.current.altKey.isPressed && !site.Finished)
                {
                    site.TryBuildFree();
                    return;
                }
                // The chimney of a finished building: firewood goes into its fireplace, a lighter lights it.
                PlacedChimney chim = PlacedChimney.UnderCursor();
                if (chim != null && chim.Fire != null && chim.Fire.Use(ConstructionSite.HeldItem(), builder != null ? builder.transform : null))
                    return;
                // A finished storage structure (a grain silo): with something in the active slot items move in or out like a container; with an empty slot it says what is in it.
                if (site.IsStorage)
                {
                    HudState sh = HudState.Active;
                    bool slotEmpty = sh == null || sh.SelectedSlot < 0 || sh.SelectedSlot >= sh.Toolbar.Count || sh.Toolbar[sh.SelectedSlot].Count <= 0 || string.IsNullOrEmpty(sh.Toolbar[sh.SelectedSlot].IconId);
                    if (slotEmpty) ToastNotificationSystem.ShowInfo(site.Name(), site.StorageSummary());
                    else TransferWithContainer(site.StructureId, site.Contents, site.transform.position, null);
                    return;
                }
                bool shiftHeld = Keyboard.current != null && Keyboard.current.shiftKey.isPressed;
                // Shift + right click takes back a site that has not been started; a plain right click builds the stage.
                if (shiftHeld && site.Stage == 0) site.TryCancel(builder != null ? builder.transform : null);
                else site.TryBuild(builder != null ? builder.transform : null);
                return;
            }

            // A right click with a hoe on open ground (nothing standing on it) tills a square of farmland.
            if (PlacedUnderCursor() == null && Tiller.HoeHeld())
            {
                Camera hoeCam = GameCamera();
                var hoePed = PedController.Current;
                if (hoeCam != null && WorldItem.UnderCursor(hoeCam, pointer) == null && Tiller.TryTill(hoeCam, pointer, hoePed != null ? hoePed.transform : null)) return;
            }

            // A right click with a loaded shovel on open ground empties it there: onto a pile of that material, or as a new tiny pile that grows.
            if (PlacedUnderCursor() == null && PileService.LoadedBulkShovel())
            {
                Camera pourCam = GameCamera();
                var pourPed = PedController.Current;
                if (pourCam != null && WorldItem.UnderCursor(pourCam, pointer) == null && PileService.TryPourOnGround(pourCam, pointer, pourPed != null ? pourPed.transform : null)) return;
            }

            // A right click with a shovel on sandy ground (nothing standing on it) digs a shovelful of sand.
            if (PlacedUnderCursor() == null && SandDigger.ShovelHeld())
            {
                Camera sandCam = GameCamera();
                var sandPed = PedController.Current;
                if (sandCam != null && WorldItem.UnderCursor(sandCam, pointer) == null && SandDigger.TryDig(sandCam, pointer, sandPed != null ? sandPed.transform : null)) return;
            }

            PlacedObject target = PlacedUnderCursor();
            if (target == null)
            {
                // an item lying on the ground (a dropped item, a felled tree's log): right click picks it up
                WorldItem lying = WorldItem.UnderCursor(GameCamera(), pointer);
                if (lying != null && WheelbarrowPush.TryStandUp(lying, out PlacedObject standing)) target = standing;   // a wheelbarrow lying there stands up to be pushed
                else
                {
                    if (lying != null)
                    {
                        var collector = PedController.Current;
                        lying.PickUp(collector != null ? collector.transform : null);
                    }
                    return;
                }
            }
            // A big fuel tank is not picked up: the fuel truck takes it away (a Tank Pickup, ordered in the Tank You phone store).
            if (Homesteader.World.FuelDelivery.IsFixedTank(target.ItemId))
            {
                ToastNotificationSystem.ShowInfo("Too heavy to move", "A fuel tank stays where it is. Order a Tank Pickup in the Tank You app and the fuel truck takes it away.");
                return;
            }
            // A spigot post (set in the ground) and a macerator pump (plumbed in) are not picked up (WaterTap.IsFixed).
            if (WaterTap.IsFixed(target.ItemId))
            {
                if (WaterTap.IsStandbyGenerator(target.ItemId)) ToastNotificationSystem.ShowInfo("Set on its pad", "A standby generator stays where it is.");
                else ToastNotificationSystem.ShowInfo("Plumbed in", target.ItemId == WaterTap.Macerator ? "A macerator pump stays where it is." : "A spigot post is set in the ground: it stays where it is.");
                return;
            }
            // A mount on the ground (a solar rack) and the item it takes in hand (its panel): a right click fits it.
            if (ItemRegistry.TryGet(target.ItemId, out ItemRegistry.ItemInfo mountInfo) && !string.IsNullOrEmpty(mountInfo.AttachItem) && ConstructionSite.HeldItem() == mountInfo.AttachItem)
            {
                if (TryFitOnMount(target, mountInfo)) return;
            }
            // Any object in a kitchen (a cabinet, a fridge, the stove ...): a right click without a wrench opens the Meals List for that kitchen (docs/COOKING.md).
            if (Homesteader.Kitchen.MealsPanel.IsKitchenObject(target.ItemId) && !AttachedObject.WrenchInHand() && !(Keyboard.current != null && Keyboard.current.shiftKey.isPressed))   // (Shift + right click picks the board up)
            {
                Homesteader.Kitchen.MealsPanel.Open(target.transform.position, target.ItemId);
                return;
            }
            // A bolted-down piece (properties.wrench_remove: kitchen, living room, lighting and bathroom fittings): a right click with a wrench takes it up.
            if (ItemRegistry.NeedsWrench(target.ItemId) && !AttachedObject.WrenchRemoval())
            {
                ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(target.ItemId), "Take it up with a wrench: Shift + right click.");
                return;
            }
            // A solar panel or mount is bolted down: a wrench with Shift + right click takes it up.
            if (WaterTap.IsBoltedSolar(target.ItemId) && !AttachedObject.WrenchRemoval())
            {
                ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(target.ItemId), "Take it up with a wrench: Shift + right click.");
                return;
            }
            // A placed container: with something in the active slot a right click moves items between the two; with an empty
            // active slot it picks the container up like anything else.
            HudState state = HudState.Active;
            bool activeSlotEmpty = state == null || state.SelectedSlot < 0 || state.SelectedSlot >= state.Toolbar.Count
                || state.Toolbar[state.SelectedSlot].Count <= 0 || string.IsNullOrEmpty(state.Toolbar[state.SelectedSlot].IconId);
            // A push item (a wheelbarrow): Shift + right click empties it onto the ground; with an empty slot a right click takes the handles.
            if (WheelbarrowPush.IsPushItem(target.ItemId))
            {
                if (Keyboard.current != null && Keyboard.current.shiftKey.isPressed) { WheelbarrowPush.DumpPlaced(target); return; }
                if (activeSlotEmpty) { WheelbarrowPush.Grab(target); return; }
            }
            // A heap of bulk material (sand, gravel ...): a shovel in hand scoops from it; otherwise it can only be lifted whole while it is untouched.
            if (WheelbarrowPush.IsPile(target.ItemId))
            {
                if (PileService.TryPourOnto(target)) return;     // a loaded shovel adds to the pile
                if (WheelbarrowPush.TryScoop(target)) return;    // an empty one takes from it
                if (target.Contents != null && target.Contents.Count > 0) { ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(target.ItemId), "Use a shovel to move it."); return; }
            }
            if (ContainerRules.IsContainer(target.ItemId) && !activeSlotEmpty && !AttachedObject.WrenchInHand()) { TransferWithContainer(target); return; }   // (a wrench in hand picks the container up: it is the tool for taking things up)
            // A bundle, stack or case: a right click takes ONE piece out of it, Shift + right click the whole pack (what is left stays on it and goes with it)
            // A PLACED thing is only taken up with a wrench and Shift (a right click with Shift held, a wrench in the active slot); only a DROPPED item is picked up by a plain right click.
            if (!AttachedObject.WrenchRemoval())
            {
                ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(target.ItemId), "Take it up with a wrench: Shift + right click.");
                return;
            }
            if (PackRules.TryTakeOne(target)) return;
            PickUp(target);
        }

        /// <summary>
        /// Right click on a placed container while the active slot holds something. Items the container accepts go IN (as
        /// many as fit by weight; the rest stays in the slot). Otherwise, when the slot holds an item the container also has
        /// and is not full, items come OUT into the slot (as many as it takes; the rest stays in the container).
        /// </summary>
        private static void TransferWithContainer(PlacedObject box)
        {
            if (box.Contents == null) box.Contents = new List<ContainerStack>();
            TransferWithContainer(box.ItemId, box.Contents, box.transform.position, box);
        }

        /// <summary>The same for any container-like thing: a placed container (box != null) or a storage structure (a silo: box == null, boxId its structure id).</summary>
        private static void TransferWithContainer(string boxId, List<ContainerStack> contents, Vector3 position, PlacedObject box)
        {
            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, position, GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to reach that.");
                return;
            }
            HudState hud = HudState.Active;
            if (hud == null) return;
            hud.EnsureToolbarSlots();
            int index = hud.SelectedSlot;
            if (index < 0 || index >= hud.Toolbar.Count) return;
            ToolbarSlotData slot = hud.Toolbar[index];
            string boxName = HudBindings.GetItemName(boxId);
            bool slotHasItems = slot.Count > 0 && !string.IsNullOrEmpty(slot.IconId);

            // A container in the active slot (a basket in hand): it is its CONTENTS that move, not the basket itself.
            if (slotHasItems && ContainerRules.IsContainer(slot.IconId))
            {
                if (box != null) TransferBetweenContainers(box, slot, index, hud, boxName);
                else ToastNotificationSystem.ShowInfo(boxName, "Put the items straight in: pick them out of the basket first.");
                return;
            }

            // IN: a filled or part-used liquid container (a jar of jam) goes in with what it holds.
            if (slotHasItems && LiquidRules.IsLiquidContainer(slot.IconId) && (!string.IsNullOrEmpty(slot.LiquidId) || Mathf.Abs(slot.WireUsed) > 0.0001f) && ContainerRules.Accepts(boxId, slot.IconId, contents))
            {
                if (ContainerRules.AddWithState(boxId, contents, slot.IconId, slot.LiquidId, slot.WireUsed) > 0)
                {
                    slot.Count--;
                    slot.WireUsed = 0f;
                    slot.LiquidId = "";
                    hud.Toolbar[index] = slot.Count > 0 ? slot : ToolbarSlotData.Empty();
                    FinishTransfer(hud);
                }
                else ToastNotificationSystem.ShowInfo(boxName, "It is full.");
                return;
            }

            // IN: the slot's items go into the container.
            if (slotHasItems && ContainerRules.Accepts(boxId, slot.IconId, contents))
            {
                int moved = ContainerRules.Add(boxId, contents, slot.IconId, slot.Count);
                if (moved > 0)
                {
                    slot.Count -= moved;
                    hud.Toolbar[index] = slot.Count > 0 ? slot : ToolbarSlotData.Empty();
                    FinishTransfer(hud);
                    return;
                }
                // Full of that: fall through and try to take some out instead.
            }

            // OUT: the container's items go into the slot.
            string item = null;
            int room = 0;
            int maxStack = 0;
            if (slotHasItems && contents.Exists(c => c.ItemId == slot.IconId) && !ContainerRules.IsContainer(slot.IconId))
            {
                item = slot.IconId;
                maxStack = Mathf.Max(1, HudBindings.GetMaxStack(item));
                room = maxStack - slot.Count;
            }

            if (item == null || room <= 0)
            {
                if (slotHasItems && !ContainerRules.Accepts(boxId, slot.IconId, contents))
                    ToastNotificationSystem.ShowInfo(boxName, boxName + " does not take " + HudBindings.GetItemName(slot.IconId) + ".");
                else if (slotHasItems && ContainerRules.RoomFor(boxId, contents, slot.IconId) <= 0)
                    ToastNotificationSystem.ShowInfo(boxName, boxName + " is full.");
                else if (contents.Count == 0)
                    ToastNotificationSystem.ShowInfo(boxName, boxName + " is empty.");
                else
                    ToastNotificationSystem.ShowInfo(boxName, "Your active slot is full.");
                return;
            }

            ContainerStack stack = contents.Find(c => c.ItemId == item);
            int take = Mathf.Min(room, stack != null ? stack.Count : 0);
            if (take <= 0) return;
            ContainerRules.Remove(contents, item, take);
            slot = slotHasItems ? slot : new ToolbarSlotData { IconId = item, Count = 0 };
            slot.Count += take;
            hud.Toolbar[index] = slot;
            FinishTransfer(hud);
            if (box != null && box.Contents.Count == 0 && ContainerRules.IsDisposable(box.ItemId)) box.Remove();   // an emptied cardboard box goes away
        }

        /// <summary>
        /// The held container (its contents) and a placed container. What the held one carries goes into the placed one (what
        /// it accepts, as many as fit by weight; the rest stays in the held one). If nothing can go in, the placed one's
        /// contents go into the held one the same way (as many as it accepts and has room for; the rest stays).
        /// </summary>
        private static void TransferBetweenContainers(PlacedObject box, ToolbarSlotData held, int slotIndex, HudState hud, string boxName)
        {
            if (held.Contents == null) held.Contents = new List<ContainerStack>();
            string heldName = HudBindings.GetItemName(held.IconId);

            int movedIn = 0;
            foreach (ContainerStack st in new List<ContainerStack>(held.Contents))
            {
                if (st.HasState) { movedIn += ContainerRules.MoveStateful(st, box.ItemId, box.Contents, held.Contents); continue; }
                int n = ContainerRules.Add(box.ItemId, box.Contents, st.ItemId, st.Count);
                if (n <= 0) continue;
                ContainerRules.Remove(held.Contents, st.ItemId, n);
                movedIn += n;
            }
            if (movedIn > 0)
            {
                hud.Toolbar[slotIndex] = held;
                FinishTransfer(hud);
                return;
            }

            int movedOut = 0;
            foreach (ContainerStack st in new List<ContainerStack>(box.Contents))
            {
                if (st.HasState) { movedOut += ContainerRules.MoveStateful(st, held.IconId, held.Contents, box.Contents); continue; }
                int n = ContainerRules.Add(held.IconId, held.Contents, st.ItemId, st.Count);
                if (n <= 0) continue;
                ContainerRules.Remove(box.Contents, st.ItemId, n);
                movedOut += n;
            }
            if (movedOut > 0)
            {
                hud.Toolbar[slotIndex] = held;
                FinishTransfer(hud);
                return;
            }

            if (held.Contents.Count == 0 && box.Contents.Count == 0) ToastNotificationSystem.ShowInfo(boxName, "Both are empty.");
            else if (held.Contents.Count == 0) ToastNotificationSystem.ShowInfo(heldName, heldName + " does not take what is in " + boxName + ", or is full.");
            else ToastNotificationSystem.ShowInfo(boxName, boxName + " does not take what " + heldName + " holds, or is full.");
        }

        private static void FinishTransfer(HudState hud)
        {
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
        }

        private static string Brace(string text) { return text.Replace("{", "{{").Replace("}", "}}"); }

        /// <summary>Puts the top object of this object's stack into the toolbar (a container keeps its contents). False with a toast when it cannot.</summary>
        /// <summary>Fits the held item (a solar panel) onto a placed mount: the mount becomes its attach_result where it stands. True when the click was for that.</summary>
        private static bool TryFitOnMount(PlacedObject mount, ItemRegistry.ItemInfo mountInfo)
        {
            if (mount.GetComponent<MountedPanel>() != null) return false;   // it has its panel
            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, mount.NearestPointTo(ped.transform.position), GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to fit it.");
                return true;
            }
            HudState hud = HudState.Active;
            if (hud == null || !hud.ConsumeFromSelectedSlot(1)) return true;
            MountedPanel.Fit(mount.gameObject, mount.ItemId, mountInfo.AttachItem);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        public static bool PickUp(PlacedObject any)
        {
            if (any == null) return false;
            PlacedObject top = any;
            foreach (List<PlacedObject> col in PlacedObject.ColumnsAt(any.transform.position))
                if (col.Contains(any)) { top = col[col.Count - 1]; break; }

            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, top.NearestPointTo(ped.transform.position), GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to pick that up.");
                return false;
            }

            if (PalletDeck.IsPallet(top.ItemId) && PalletDeck.Carried(top).Count > 0)
            {
                ToastNotificationSystem.ShowInfo("Pallet", "Take what is on the pallet off first.");
                return false;
            }

            HudState hud = HudState.Active;
            if (hud == null) return false;
            hud.EnsureToolbarSlots();
            string id = top.ItemId;
            bool holdsThings = top.Contents != null && top.Contents.Count > 0;
            if (ContainerRules.IsContainer(id) || holdsThings)
            {
                // A container goes into a slot of its own so its contents stay with it.
                int free = -1;
                for (int i = 0; i < hud.Toolbar.Count; i++)
                    if (hud.Toolbar[i].Count <= 0 || string.IsNullOrEmpty(hud.Toolbar[i].IconId)) { free = i; break; }
                if (free < 0) { ToastNotificationSystem.ShowWarning("Toolbar full", "No free toolbar slot for that."); return false; }
                hud.Toolbar[free] = new ToolbarSlotData { IconId = id, Count = 1, Contents = ContainerRules.Clone(top.Contents) };
            }
            else if (top.WireUsed > 0.01f || !string.IsNullOrEmpty(top.LiquidId))
            {
                // a partly used coil or spool of wire goes into a slot of its own, so the metres already used go with it
                int free = -1;
                for (int i = 0; i < hud.Toolbar.Count; i++)
                    if (hud.Toolbar[i].Count <= 0 || string.IsNullOrEmpty(hud.Toolbar[i].IconId)) { free = i; break; }
                if (free < 0) { ToastNotificationSystem.ShowWarning("Toolbar full", "No free toolbar slot for that."); return false; }
                hud.Toolbar[free] = new ToolbarSlotData { IconId = id, Count = 1, WireUsed = top.WireUsed, LiquidId = top.LiquidId ?? "" };   // (a glass of juice: the liquid goes with it)
            }
            else
            {
                AssetCatalogItem cat = HudBindings.GetCatalogItem(id);
                int added = hud.AddItemToToolbar(id, 1, cat != null ? Mathf.Max(1, cat.max_stack) : 64);
                if (added <= 0) { ToastNotificationSystem.ShowWarning("Toolbar full", "No room in the toolbar for that."); return false; }
            }
            string panelOn = MountedPanel.PanelOn(top.gameObject);
            if (panelOn != null) hud.AddItemToToolbar(panelOn, 1, HudBindings.GetMaxStack(panelOn));   // the panel comes up with its rack
            top.Remove();
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        // ------------------------------------------------------------------ placing

        private void Place(string itemId, ItemRegistry.ItemInfo info, Plan plan, Quaternion rotation)
        {
            HudState state = HudState.Active;
            // A container keeps what is in it when it is put down.
            List<ContainerStack> contents = state.SelectedSlot >= 0 && state.SelectedSlot < state.Toolbar.Count ? state.Toolbar[state.SelectedSlot].Contents : null;
            float wireUsed = state.SelectedSlot >= 0 && state.SelectedSlot < state.Toolbar.Count ? state.Toolbar[state.SelectedSlot].WireUsed : 0f;   // a used coil or spool keeps its metres
            int wireSlot = state.SelectedSlot;
            string slotLiquid = state.SelectedSlot >= 0 && state.SelectedSlot < state.Toolbar.Count ? state.Toolbar[state.SelectedSlot].LiquidId : null;   // a filled glass keeps its liquid
            if (!state.ConsumeFromSelectedSlot(1)) return;
            ClearWireUsed(state, wireSlot);
            HudBindings.Instance.RefreshToolbar();

            // Stacks that had to make room slide over first (the terrain height under each is re-read).
            foreach (var shift in plan.Shifts)
                foreach (PlacedObject o in shift.Key)
                {
                    if (o == null) continue;
                    Vector3 from = o.transform.position;
                    Vector3 to = new Vector3(from.x + shift.Value.x, from.y, from.z + shift.Value.y);
                    to.y += Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(to) - Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(from);
                    o.transform.position = to;
                }

            PlacedObject placedNow = SpawnPlaced(itemId, info, plan.Position, rotation.eulerAngles.y, true, plan.Level, contents, _mirror);
            _mirror = false;
            if (placedNow != null) { placedNow.WireUsed = wireUsed; if (!string.IsNullOrEmpty(slotLiquid)) placedNow.LiquidId = slotLiquid; }
        }

        /// <summary>The used spool was the one that left the slot: what is still in it is whole spools.</summary>
        private static void ClearWireUsed(HudState state, int slotIndex)
        {
            if (slotIndex < 0 || slotIndex >= state.Toolbar.Count) return;
            ToolbarSlotData s = state.Toolbar[slotIndex];
            if (s.Count <= 0 || s.WireUsed <= 0f) return;
            s.WireUsed = 0f;
            state.Toolbar[slotIndex] = s;
        }

        private static Transform s_placedRoot;

        /// <summary>
        /// Creates a placed object from a loaded model template. fade = true starts as the translucent shadow and
        /// fades to solid (a fresh placement); false is a solid object at once (restoring a save).
        /// </summary>
        public static PlacedObject SpawnPlaced(string itemId, ItemRegistry.ItemInfo info, Vector3 cell, float yawDeg, bool fade, int level = 0, List<ContainerStack> contents = null, bool mirrored = false)
        {
            if (s_placedRoot == null) s_placedRoot = new GameObject("PlacedObjects").transform;
            // Snap to the terrain surface (just above, not 3 m above) when it is below it; a container stacked on another, or a thing standing on a
            // floor, foundation or deck, keeps the height it was given (the plan and the save already hold the right one).
            if (level <= 0 && cell.y < Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(cell) + 0.02f)
                cell = Homesteader.Generation.TerrainHeightDetector.PlaceOnGround(cell);
            GameObject obj = Instantiate(info.Prefab, s_placedRoot);
            obj.SetActive(true);                       // templates live inactive
            obj.transform.SetPositionAndRotation(cell, Quaternion.Euler(0f, yawDeg, 0f));
            if (mirrored) { Vector3 sc = obj.transform.localScale; sc.x = -Mathf.Abs(sc.x); obj.transform.localScale = sc; }   // mirrored left to right
            var placed = obj.AddComponent<PlacedObject>();
            placed.Mirrored = mirrored;
            placed.Init(itemId, cell, yawDeg, level);
            if (contents != null) placed.Contents = ContainerRules.Clone(contents);
            WireNode.Attach(placed.gameObject, itemId);     // a device the solar chain wires together
            NoClimb.AttachIfGroundRack(placed);             // the player does not walk up a panel on a ground rack
            PortableGenerator.Attach(placed.gameObject, itemId);   // a portable generator powers what is round it
            WindTurbine.AttachIfTurbine(placed);            // a wind turbine turns into the wind and its blades spin
            ContainerFillView.AttachIfContainer(placed);   // what is inside shows as blocks that fill the container
            DishView.AttachIfDish(placed);                 // a served plate, bowl or glass shows its food or drink
            KitchenRunFiller.AttachIfRun(placed);          // a kitchen run piece: a filler strip closes a gap between its end and a wall
            StrawBedding.AttachIfBedding(placed);          // straw bedding finds its room and lays the straw over the floor
            TankSticker.AttachIfTank(placed);              // a fuel tank's sticker names what is in it
            Homesteader.World.PickupFlag.AttachIfFlag(placed);   // a pickup flag: it marks the market pickup zone
            Sawmill.AttachIfSawmill(placed);               // a sawmill: logs on its track are cut into lumber
            WheelbarrowPush.AttachPileVisual(placed);       // a heap shrinks as it is shovelled
            LightEmitter.Attach(obj, itemId, info.Lights);   // its lights come on with the game clock
            if (fade)
            {
                GhostVisual.Apply(obj, ValidTint, GhostAlpha);
                placed.StartCoroutine(placed.FadeToSolid(ValidTint, GhostAlpha, 0.4f));
            }
            return placed;
        }

        /// <summary>An identical stackable container can be put on top of this one while the stack is under its limit.</summary>
        public static bool CanStack(PlacedObject below, string itemId)
        {
            return below != null && !string.IsNullOrEmpty(itemId) && below.ItemId == itemId && ContainerRules.StackingLimit(itemId) > below.Level + 1;
        }

        /// <summary>
        /// With an item in hand and the cursor over a container with SLOTS (a battery rack) that takes it, a left click slides one into the rack instead of putting it on the ground
        /// (the rack's square is taken, so it could not be placed there anyway). True when the click was for that.
        /// </summary>
        private static bool TryInsertIntoRack(string heldId)
        {
            PlacedObject rack = PlacedUnderCursor();
            if (rack == null || string.IsNullOrEmpty(heldId)) return false;
            AssetCatalogItem info = HudBindings.GetCatalogItem(rack.ItemId);
            if (info == null || info.container_slot_pitch_m <= 0f || !ContainerRules.Accepts(rack.ItemId, heldId, rack.Contents)) return false;
            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, rack.NearestPointTo(ped.transform.position), GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to reach that.");
                return true;
            }
            if (rack.Contents == null) rack.Contents = new List<ContainerStack>();
            if (ContainerRules.RoomFor(rack.ItemId, rack.Contents, heldId) <= 0)
            {
                ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(rack.ItemId), HudBindings.GetItemName(rack.ItemId) + " is full.");
                return true;
            }
            HudState hud = HudState.Active;
            if (hud == null || hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return true;
            if (ContainerRules.Add(rack.ItemId, rack.Contents, heldId, 1) <= 0) return true;
            hud.ConsumeFromSelectedSlot(1);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        /// <summary>A left click with an item in hand over a mount (a roof or ground solar rack) whose attach_item it is: fits it. True when the click was for that.</summary>
        private static bool TryFitHeld(string heldId, Camera cam)
        {
            ConstructionSite wellSite = ConstructionSite.UnderCursor();
            if (wellSite != null && wellSite.TryFitPanel(heldId)) return true;   // a well's sub panel
            PlacedObject target = PlacedUnderCursor();
            if (target != null && ItemRegistry.TryGet(target.ItemId, out ItemRegistry.ItemInfo mi) && !string.IsNullOrEmpty(mi.AttachItem) && mi.AttachItem == heldId)
                return TryFitOnMount(target, mi);
            var ped = PedController.Current;
            return AttachedObject.TryFitAtRay(cam.ScreenPointToRay(PointerPosition()), ped != null ? ped.transform.position : Vector3.zero);
        }

        /// <summary>The placed object under the mouse pointer (a direct hit on its collider), or null.</summary>
        public static PlacedObject PlacedUnderCursor()
        {
            Camera cam = GameCamera();
            if (cam == null) return null;
            RaycastHit[] hits = Homesteader.UI.HoverTarget.SortedHits(cam, PointerPosition());
            foreach (RaycastHit h in hits)
            {
                if (h.collider == null) continue;   // the hits are shared for the frame: a collider destroyed since (a panel fitted, a stack settled) is gone
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                PlacedObject p = h.collider.GetComponentInParent<PlacedObject>();
                if (p != null) return p;
                return null;   // something else is in front
            }
            return null;
        }

        /// <summary>Where a structure's dirt area would go (on the grid), and whether the ground allows it.</summary>
        private Plan MakeSitePlan(string structureId, Vector3 hit, float yawDeg, Transform player)
        {
            var plan = new Plan();
            Vector2 foot = ConstructionSite.FootprintOf(structureId);
            // The foundation sits in a block of WHOLE grid squares (as many as its width and depth need, measured as turned: a quarter turn
            // swaps them), centred in it, so its edges run parallel to the grid lines with the same small margin on both sides and its
            // centre lands on a square corner or a square centre like the squares themselves do.
            float g = PlantingValidator.GridSizeM;
            bool quarter = Mathf.Abs(Mathf.Sin(yawDeg * Mathf.Deg2Rad)) > 0.7f;
            Vector2 turned = quarter ? new Vector2(foot.y, foot.x) : foot;
            float blockX = Mathf.Max(1f, Mathf.Ceil(turned.x / g - 0.001f)) * g;
            float blockZ = Mathf.Max(1f, Mathf.Ceil(turned.y / g - 0.001f)) * g;
            float minX = Mathf.Round((hit.x - blockX * 0.5f) / g) * g;
            float minZ = Mathf.Round((hit.z - blockZ * 0.5f) / g) * g;
            Vector3 center = new Vector3(minX + blockX * 0.5f, 0f, minZ + blockZ * 0.5f);
            center.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(center);
            plan.Position = center;
            float reach = foot.magnitude * 0.5f + 2f;
            if (player != null && new Vector2(player.position.x - center.x, player.position.z - center.z).magnitude > reach + GameRules.Placement.ReachCells)
            {
                plan.Reason = "You can only start a structure close to you.";
                return plan;
            }
            Quaternion rot = Quaternion.Euler(0f, yawDeg, 0f);
            // water and slope at the middle and the four corners
            for (int i = 0; i < 5; i++)
            {
                Vector3 local = i == 0 ? Vector3.zero : new Vector3((i & 1) == 0 ? -foot.x : foot.x, 0f, (i & 2) == 0 ? -foot.y : foot.y) * 0.5f;
                Vector3 p = center + rot * local;
                if (Homesteader.Generation.TerrainHeightDetector.GetGroundY(p) < WaterY() + 0.05f) { plan.Reason = "You can't build in water."; return plan; }
            }
            if (SlopeAt(center) > GameRules.Planting.MaxSlopeDeg) { plan.Reason = "The ground is too steep here."; return plan; }
            // not on top of another site, a plant or a placed object
            foreach (ConstructionSite other in ConstructionSite.All)
            {
                if (other == null) continue;
                float apart = new Vector2(other.transform.position.x - center.x, other.transform.position.z - center.z).magnitude;
                if (apart < (other.Footprint.magnitude + foot.magnitude) * 0.5f)
                {
                    WireNode buried = other.GetComponent<WireNode>();   // nothing is built over a septic tank or a leach field (docs/SEPTIC.md)
                    plan.Reason = buried != null && (buried.Role == WireRole.SepticTank || buried.Role == WireRole.LeachField) ? "Nothing can be built over a " + WireNode.RoleName(buried.Role) + "." : "Another structure is in the way.";
                    return plan;
                }
            }
            foreach (PlantedGrowth pg in PlantedGrowth.All)
            {
                if (pg == null) continue;
                Vector3 local = Quaternion.Inverse(rot) * (pg.transform.position - center);
                if (Mathf.Abs(local.x) < foot.x * 0.5f && Mathf.Abs(local.z) < foot.y * 0.5f) { plan.Reason = "Something is growing there."; return plan; }
            }
            foreach (PlacedObject po in PlacedObject.All)
            {
                if (po == null) continue;
                Vector3 local = Quaternion.Inverse(rot) * (po.transform.position - center);
                if (Mathf.Abs(local.x) < foot.x * 0.5f && Mathf.Abs(local.z) < foot.y * 0.5f) { plan.Reason = "Something is in the way."; return plan; }
            }
            plan.Valid = true;
            return plan;
        }

        private Plan MakePalletPlan(PlacedObject pallet, string itemId, Vector3 hit, Transform player, int deck = 0)
        {
            var plan = new Plan { Position = hit };
            bool onCounter = KitchenRun.IsRun(pallet.ItemId) && !PalletDeck.IsShelving(pallet.ItemId);
            // aligned with the pallet; on a kitchen counter the R turns of the appliance (a toaster, a mixer) are added to the counter's own
            ghost.transform.rotation = Quaternion.Euler(0f, pallet.transform.eulerAngles.y + (onCounter ? rotationSteps * GameRules.Placement.RotateStepDeg : 0f), 0f);
            if (!PalletDeck.LocalRect(pallet.transform, ghost, out Rect mine)) { plan.Reason = "Loading..."; return plan; }
            if (player != null && !PlantingValidator.InReach(player, new Vector3(hit.x, pallet.transform.position.y, hit.z), GameRules.Placement.ReachCells))   // reach is to the spot being placed, not to the middle of the pallet (a 1.6 m island is not out of reach at its ends)
            {
                plan.Reason = $"You can only place things within {GameRules.Placement.ReachCells} squares of you.";
                return plan;
            }
            float itemHeight = 0f;
            bool anyRenderer = false;
            Bounds gb = default;
            foreach (Renderer r in ghost.GetComponentsInChildren<Renderer>()) { if (!anyRenderer) { gb = r.bounds; anyRenderer = true; } else gb.Encapsulate(r.bounds); }
            if (anyRenderer) itemHeight = gb.size.y;
            if (KitchenRun.IsRun(pallet.ItemId) && !PalletDeck.IsShelving(pallet.ItemId))
            {
                // a kitchen counter: free placement under the cursor, in the counter's own turn, across any counters side by side (a cooktop spans two cabinets)
                Camera counterCam = GameCamera();
                Ray counterRay = counterCam != null ? counterCam.ScreenPointToRay(PointerPosition()) : new Ray(hit + Vector3.up, Vector3.down);
                plan.Valid = KitchenRun.PlanOnCounter(pallet, ghost, counterRay, hit, itemHeight, out Vector3 counterPos, out string counterReason);
                plan.Position = counterPos;
                plan.Reason = counterReason;
                plan.Level = 0;
                return plan;
            }
            if (!PalletDeck.FindSpot(pallet, itemId, new Vector2(mine.width, mine.height), hit, null, out Vector3 pos, out int level, out string reason, deck, itemHeight))
            {
                plan.Reason = reason;
                return plan;
            }
            plan.Position = pos;
            plan.Level = level;
            plan.Valid = true;
            return plan;
        }

        private void PlaceSite(string heldId, string structureId, Plan plan, float yawDeg)
        {
            HudState state = HudState.Active;
            // a blueprint starts the site and stays with the player; a KIT is used up by it (the work site then has the kit's parts)
            if (!Blueprints.IsBlueprint(heldId) && !state.ConsumeFromSelectedSlot(1)) return;
            HudBindings.Instance.RefreshToolbar();
            ConstructionSite.Create(structureId, plan.Position, yawDeg);
        }

        private bool ValidateGround(Vector3 cell, Transform player, out string reason)
        {
            reason = null;
            if (!PlantingValidator.InReach(player, cell, GameRules.Placement.ReachCells))
            {
                reason = $"You can only place things within {GameRules.Placement.ReachCells} squares of you.";
                return false;
            }
            if (cell.y < WaterY() + 0.05f)
            {
                reason = "You can't build in water.";
                return false;
            }
            if (SlopeAt(cell) > GameRules.Planting.MaxSlopeDeg)
            {
                reason = "The ground is too steep here.";
                return false;
            }
            foreach (PlantedGrowth p in PlantedGrowth.All)
            {
                if (p == null) continue;
                Vector3 c = p.transform.position;
                float g = PlantingValidator.GridSizeM;
                if (Mathf.Floor(c.x / g) == Mathf.Floor(cell.x / g) && Mathf.Floor(c.z / g) == Mathf.Floor(cell.z / g))
                {
                    reason = "Something is growing in that square.";
                    return false;
                }
            }
            return true;
        }

        // ------------------------------------------------------------------ packing a square

        /// <summary>Where a new object goes in its grid square, which stacks have to slide over to make room, and whether it fits at all.</summary>
        private sealed class Plan
        {
            public bool Valid;
            public string Reason;
            public Vector3 Position;
            public int Level;
            public readonly List<KeyValuePair<List<PlacedObject>, Vector2>> Shifts = new List<KeyValuePair<List<PlacedObject>, Vector2>>();
        }

        private const float PackGap = 0.01f;

        /// <summary>
        /// 1) An identical stackable item standing under the cursor and under its limit: stack on it.
        /// 2) Else the free spot in the square nearest the cursor that the footprint fits in without touching anything.
        /// 3) Else re-pack the whole square (the stacks already there and the new item) into rows; if everything fits the
        ///    stacks slide over to their new places. 4) Else there is no room.
        /// </summary>
        private Plan MakePlan(string heldId, Vector3 hit, Vector2 size, Transform player)
        {
            var plan = new Plan();
            float g = PlantingValidator.GridSizeM;
            Vector3 center = PlantingValidator.SnapToGrid(hit);
            center.y = RestY(center, hit.y);
            float restY = center.y;
            bool onTop = restY > Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(center) + 0.04f;   // on a floor, foundation or deck
            plan.Position = center;
            if (!ValidateGround(center, player, out string reason)) { plan.Reason = reason; return plan; }

            if (TrySnapMount(heldId, hit, size, restY, onTop, player, plan)) return plan;   // a solar rack next to another one snaps to it
            _runSnapped = KitchenRun.TrySnap(heldId, ghost, hit, _runTurns, out Vector3 runPos, out float runYaw, out string runReason);
            if (_runSnapped)   // a kitchen cabinet or appliance: against its neighbour, else backed onto the wall
            {
                ghost.transform.rotation = Quaternion.Euler(0f, runYaw, 0f);
                plan.Position = GroundAt(new Vector2(runPos.x, runPos.z), restY, onTop);
                plan.Reason = runReason;
                plan.Valid = runReason == null;
                plan.Level = 0;
                return plan;
            }
            if (TryFreePlace(hit, size, plan)) return plan;   // inside a building: exactly where the cursor is, not on the outdoor grid

            Vector2 min = new Vector2(center.x - g * 0.5f, center.z - g * 0.5f);
            size = new Vector2(Mathf.Min(size.x, g - 0.02f), Mathf.Min(size.y, g - 0.02f));
            Vector2 hit2 = new Vector2(hit.x, hit.z);
            List<List<PlacedObject>> columns = PlacedObject.ColumnsAt(center);

            // 1) stack on the column under the cursor
            bool fullStackHere = false;
            foreach (List<PlacedObject> col in columns)
            {
                if (!ExpandRect(PlacedObject.ColumnRect(col), 0.03f).Contains(hit2)) continue;
                PlacedObject top = col[col.Count - 1];
                if (CanStack(top, heldId))
                {
                    Vector3 tp = top.transform.position;
                    plan.Position = new Vector3(tp.x, tp.y + top.Height, tp.z);
                    plan.Level = top.Level + 1;
                    plan.Valid = true;
                    return plan;
                }
                fullStackHere = top.ItemId == heldId && ContainerRules.StackingLimit(heldId) > 1;
                break;   // a full stack or a different item: look for room beside it
            }

            // 2) a free spot, nearest the cursor
            float hw = size.x * 0.5f, hd = size.y * 0.5f, half = PackGap * 0.5f;
            bool found = false;
            Vector2 best = default;
            float bestD = float.MaxValue;
            for (float x = min.x + hw + half; x <= min.x + g - hw - half + 1e-4f; x += 0.05f)
            {
                for (float z = min.y + hd + half; z <= min.y + g - hd - half + 1e-4f; z += 0.05f)
                {
                    var cand = new Rect(x - hw, z - hd, size.x, size.y);
                    bool free = true;
                    foreach (List<PlacedObject> col in columns)
                        if (cand.Overlaps(ExpandRect(PlacedObject.ColumnRect(col), half))) { free = false; break; }
                    if (!free) continue;
                    float d = (x - hit.x) * (x - hit.x) + (z - hit.z) * (z - hit.z);
                    if (d < bestD) { bestD = d; best = new Vector2(x, z); found = true; }
                }
            }
            if (found)
            {
                plan.Position = GroundAt(best, restY, onTop);
                plan.Valid = true;
                return plan;
            }

            // 3) re-pack the square: the stacks already here keep their size, the new item goes last
            if (columns.Count > 0)
            {
                var sizes = new List<Vector2>();
                foreach (List<PlacedObject> col in columns) sizes.Add(PlacedObject.ColumnRect(col).size);
                sizes.Add(size);
                Vector2[] centers = Pack(sizes, g, min);
                if (centers != null)
                {
                    for (int i = 0; i < columns.Count; i++)
                    {
                        Vector2 from = PlacedObject.ColumnRect(columns[i]).center;
                        plan.Shifts.Add(new KeyValuePair<List<PlacedObject>, Vector2>(columns[i], centers[i] - from));
                    }
                    plan.Position = GroundAt(centers[centers.Length - 1], restY, onTop);
                    plan.Valid = true;
                    return plan;
                }
            }

            plan.Reason = fullStackHere ? "That stack is as high as it goes and there is no room beside it." : "There is no room left on that square.";
            return plan;
        }

        /// <summary>The plan-view size of the panel a mount takes (its manifest's panel_width_m and panel_depth_m), turned with the mount: zero when it does not say.</summary>
        private static Vector2 PanelSpan(string mountId, float yawDeg)
        {
            AssetCatalogItem m = HudBindings.GetCatalogItem(mountId);
            if (m == null || m.panel_width_m <= 0f) return Vector2.zero;
            bool quarter = Mathf.Abs(Mathf.Sin(yawDeg * Mathf.Deg2Rad)) > 0.7f;
            return quarter ? new Vector2(m.panel_depth_m, m.panel_width_m) : new Vector2(m.panel_width_m, m.panel_depth_m);
        }

        /// <summary>
        /// Inside a finished building things go EXACTLY where the cursor is (the ground grid does not fit a room: a 1 m square straddles the walls and pushed things against
        /// them), kept inside the walls, on the floor. Over a stack it leaves the choice to the stacking rules. False when the cursor is not on a building's floor.
        /// </summary>
        private bool TryFreePlace(Vector3 hit, Vector2 size, Plan plan)
        {
            if (!s_cursorOnStructure) return false;
            ConstructionSite site = null;
            foreach (ConstructionSite s in ConstructionSite.All)
                if (s != null && s.Finished && s.IsInsideWalls(hit)) { site = s; break; }
            if (site == null) return false;
            Vector2 hit2 = new Vector2(hit.x, hit.z);
            foreach (List<PlacedObject> col in PlacedObject.ColumnsAt(PlantingValidator.SnapToGrid(hit)))
                if (ExpandRect(PlacedObject.ColumnRect(col), 0.03f).Contains(hit2)) return false;   // over a stack: stack on it (the usual rules)
            // inside the walls: the walls' rectangle less their thickness, less half the item
            Quaternion rot = site.transform.rotation;
            Vector3 l = Quaternion.Inverse(rot) * (hit - site.transform.position);
            Rect r = site.WingRectNear(l.x, l.z);   // the wing the cursor is in (an L-shaped house has two)
            float wall = AttachedObject.DefaultWall + 0.02f;
            float half = Mathf.Max(size.x, size.y) * 0.5f;
            l.x = Mathf.Clamp(l.x, r.xMin + wall + half, Mathf.Max(r.xMin + wall + half, r.xMax - wall - half));
            l.z = Mathf.Clamp(l.z, r.yMin + wall + half, Mathf.Max(r.yMin + wall + half, r.yMax - wall - half));
            Vector3 at = site.transform.position + rot * new Vector3(l.x, 0f, l.z);
            var mine = new Rect(at.x - size.x * 0.5f, at.z - size.y * 0.5f, size.x, size.y);
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null) continue;
                if (mine.Overlaps(ExpandRect(PlacedObject.ColumnRect(new List<PlacedObject> { o }), -0.01f)))
                {
                    plan.Position = new Vector3(at.x, RestY(at, hit.y), at.z);
                    plan.Reason = "Something is in the way.";
                    return true;
                }
            }
            plan.Position = new Vector3(at.x, RestY(at, hit.y), at.z);
            plan.Level = 0;
            plan.Valid = true;
            return true;
        }

        private const float MountGap = 0.05f;   // between two racks: their panels sit edge to edge with this much air

        /// <summary>
        /// A mount (a solar rack, an item with an attach_item) held near another mount snaps edge to edge to it, on any of its four sides, a hair apart, so the panels
        /// fitted on them sit in a neat row or block. Crosses the grid lines. False when no mount is near or the snapped spot is blocked.
        /// </summary>
        private bool TrySnapMount(string heldId, Vector3 hit, Vector2 size, float restY, bool onTop, Transform player, Plan plan)
        {
            if (!ItemRegistry.TryGet(heldId, out ItemRegistry.ItemInfo hi) || string.IsNullOrEmpty(hi.AttachItem)) return false;
            Vector2 hit2 = new Vector2(hit.x, hit.z);
            float ghostYaw = ghost != null ? ghost.transform.eulerAngles.y : 0f;
            Vector2 mine = Vector2.Max(size, PanelSpan(heldId, ghostYaw));   // the panel is wider than the rack under it: space by the panel
            float best = 1.6f * 1.6f;
            Vector2 bestC = default;
            bool any = false;
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !ItemRegistry.TryGet(o.ItemId, out ItemRegistry.ItemInfo oi) || string.IsNullOrEmpty(oi.AttachItem)) continue;
                Rect r = PlacedObject.ColumnRect(new List<PlacedObject> { o });
                Vector2 theirs = Vector2.Max(r.size, PanelSpan(o.ItemId, o.YawDeg));
                Vector2 c0 = r.center;
                float dx = theirs.x * 0.5f + mine.x * 0.5f + MountGap, dz = theirs.y * 0.5f + mine.y * 0.5f + MountGap;
                Vector2[] cands = { new Vector2(c0.x + dx, c0.y), new Vector2(c0.x - dx, c0.y), new Vector2(c0.x, c0.y + dz), new Vector2(c0.x, c0.y - dz) };
                foreach (Vector2 c in cands)
                {
                    float d = (c - hit2).sqrMagnitude;
                    if (d >= best) continue;
                    var cand = new Rect(c.x - mine.x * 0.5f, c.y - mine.y * 0.5f, mine.x, mine.y);
                    bool free = true;
                    foreach (PlacedObject other in PlacedObject.All)
                    {
                        if (other == null) continue;
                        Rect orect = PlacedObject.ColumnRect(new List<PlacedObject> { other });
                        if (ItemRegistry.TryGet(other.ItemId, out ItemRegistry.ItemInfo oinfo) && !string.IsNullOrEmpty(oinfo.AttachItem))
                        {
                            Vector2 sp = Vector2.Max(orect.size, PanelSpan(other.ItemId, other.YawDeg));
                            orect = new Rect(orect.center.x - sp.x * 0.5f, orect.center.y - sp.y * 0.5f, sp.x, sp.y);
                        }
                        if (cand.Overlaps(ExpandRect(orect, -0.005f))) { free = false; break; }
                    }
                    if (!free) continue;
                    best = d;
                    bestC = c;
                    any = true;
                }
            }
            if (!any) return false;
            var at = new Vector3(bestC.x, 0f, bestC.y);
            if (!ValidateGround(PlantingValidator.SnapToGrid(at), player, out string reason)) return false;
            float y = RestY(at, hit.y);
            plan.Position = GroundAt(bestC, y, onTop);
            plan.Valid = true;
            return true;
        }

        private static Vector3 GroundAt(Vector2 xz, float restY, bool onTop)
        {
            var p = new Vector3(xz.x, 0f, xz.y);
            p.y = onTop ? restY : Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(p);   // on a floor the whole square rests at its height
            return p;
        }

        private static Rect ExpandRect(Rect r, float by) { return new Rect(r.x - by, r.y - by, r.width + 2f * by, r.height + 2f * by); }

        /// <summary>
        /// Fits every footprint into a square of side g (corner at min) in rows, tallest first, trying rows along x and
        /// rows along z. Returns the centre of each in the input order, or null when they do not all fit.
        /// </summary>
        private static Vector2[] Pack(List<Vector2> sizes, float g, Vector2 min)
        {
            for (int orientation = 0; orientation < 2; orientation++)
            {
                var s2 = new List<Vector2>();
                foreach (Vector2 v in sizes) s2.Add(orientation == 0 ? v : new Vector2(v.y, v.x));
                var order = new List<int>();
                for (int i = 0; i < s2.Count; i++) order.Add(i);
                order.Sort((a, b) => s2[b].y.CompareTo(s2[a].y));

                var result = new Vector2[s2.Count];
                float x = PackGap * 0.5f, rowZ = PackGap * 0.5f, rowH = 0f;
                bool ok = true;
                foreach (int i in order)
                {
                    Vector2 v = s2[i];
                    if (x + v.x > g - PackGap * 0.5f + 1e-4f) { x = PackGap * 0.5f; rowZ += rowH + PackGap; rowH = 0f; }
                    if (x + v.x > g - PackGap * 0.5f + 1e-4f || rowZ + v.y > g - PackGap * 0.5f + 1e-4f) { ok = false; break; }
                    result[i] = new Vector2(x + v.x * 0.5f, rowZ + v.y * 0.5f);
                    x += v.x + PackGap;
                    rowH = Mathf.Max(rowH, v.y);
                }
                if (!ok) continue;
                for (int i = 0; i < result.Length; i++)
                {
                    Vector2 c = orientation == 0 ? result[i] : new Vector2(result[i].y, result[i].x);
                    result[i] = new Vector2(min.x + c.x, min.y + c.y);
                }
                return result;
            }
            return null;
        }

        /// <summary>The height of the shadow in metres (0 until its model has loaded).</summary>
        private float GhostHeight()
        {
            Renderer[] rs = ghost != null ? ghost.GetComponentsInChildren<Renderer>() : null;
            if (rs == null || rs.Length == 0) return 0f;
            Bounds b = rs[0].bounds;
            for (int i = 1; i < rs.Length; i++) b.Encapsulate(rs[i].bounds);
            return b.size.y;
        }

        /// <summary>World footprint (x, z) of the shadow at its current turn.</summary>
        private Vector2 GhostFootprint()
        {
            Renderer[] rs = ghost != null ? ghost.GetComponentsInChildren<Renderer>() : null;
            if (rs == null || rs.Length == 0) return new Vector2(0.8f, 0.8f);
            Bounds b = rs[0].bounds;
            for (int i = 1; i < rs.Length; i++) b.Encapsulate(rs[i].bounds);
            return new Vector2(b.size.x, b.size.z);
        }

        // ------------------------------------------------------------------ ghost

        /// <summary>Makes sure the shadow for this item exists; false while its GLB is still loading.</summary>
        private bool EnsureGhost(string itemId, ItemRegistry.ItemInfo info)
        {
            if (ghost != null && ghostItemId == itemId)
            {
                if (info != null || ghostStructureModel) return true;
                // a structure's stand-in slab: swap for the foundation model as soon as it is ready
                List<ConstructionStageData> st = ConstructionSite.StagesOf(itemId);
                bool ready = false;
                if (st != null && ItemRegistry.TryGet(st[0].item_id, out ItemRegistry.ItemInfo fi) && fi.Prefab != null)
                {
                    GlbTemplate g = fi.Prefab.GetComponent<GlbTemplate>();
                    ready = g == null || g.Ready;
                }
                if (!ready) return true;
            }
            DestroyGhost();

            if (info == null)
            {
                // A structure: the shadow is its foundation (the stage-1 model, which has the door step), with an arrow marking the FRONT.
                // While that model is still loading the shadow is a flat slab of the footprint.
                Vector2 foot = ConstructionSite.FootprintOf(itemId);
                var holder = new GameObject("PlacementGhost_" + itemId);
                List<ConstructionStageData> stages = ConstructionSite.StagesOf(itemId);
                ItemRegistry.ItemInfo foundation = null;
                if (stages != null && ItemRegistry.TryGet(stages[0].item_id, out foundation) && foundation.Prefab != null)
                {
                    GlbTemplate fglb = foundation.Prefab.GetComponent<GlbTemplate>();
                    if (fglb != null) fglb.EnsureLoading();
                    if (fglb == null || fglb.Ready)
                    {
                        ConstructionSite.LearnFront(foundation.Prefab);
                        GameObject model = Instantiate(foundation.Prefab, holder.transform);
                        model.SetActive(true);
                        model.transform.localPosition = Vector3.zero;
                        model.transform.localRotation = Quaternion.identity;
                        foreach (Collider c in model.GetComponentsInChildren<Collider>(true)) Destroy(c);
                        ghostStructureModel = true;
                    }
                }
                if (!ghostStructureModel)
                {
                    GameObject slab = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    slab.transform.SetParent(holder.transform, false);
                    slab.transform.localScale = new Vector3(foot.x, 0.12f, foot.y);
                    slab.transform.localPosition = new Vector3(0f, 0.06f, 0f);
                    Destroy(slab.GetComponent<Collider>());
                }
                ConstructionSite.MakeFrontArrow(holder.transform, foot, ConstructionSite.FrontLocal);
                ghost = holder;
                ghostItemId = itemId;
                return true;
            }

            GlbTemplate glb = info.Prefab.GetComponent<GlbTemplate>();
            if (glb != null)
            {
                glb.EnsureLoading();
                if (glb.Failed) return false;
                if (!glb.Ready) return false;
            }

            ghost = Instantiate(info.Prefab);
            ghost.name = "PlacementGhost_" + itemId;
            ghost.SetActive(true);
            // The shadow is walk-through and never blocks the cursor ray.
            foreach (Collider c in ghost.GetComponentsInChildren<Collider>(true)) Destroy(c);
            ghostItemId = itemId;
            return true;
        }

        private void HideGhost()
        {
            if (ghost != null) ghost.SetActive(false);
            WellPreview = null;
        }

        /// <summary>Where a WELL blueprint is being held over the ground (the look-at panel shows the depth and the most it can give there), or null.</summary>
        public static Vector3? WellPreview;
        public static string WellPreviewId;

        private void DestroyGhost()
        {
            if (ghost != null) Destroy(ghost);
            ghost = null;
            ghostItemId = null;
            ghostStructureModel = false;
        }

        private void OnDisable() => DestroyGhost();

        // ------------------------------------------------------------------ helpers

        private static string HeldItemId()
        {
            HudState state = HudState.Active;
            if (state == null || state.SelectedSlot < 0 || state.SelectedSlot >= state.Toolbar.Count) return null;
            ToolbarSlotData slot = state.Toolbar[state.SelectedSlot];
            return !string.IsNullOrEmpty(slot.IconId) && slot.Count > 0 ? slot.IconId : null;
        }

        /// <summary>
        /// Placeable or not: an item with a model whose manifest says properties.placeable = true (opt in; the category
        /// does not matter), and that is not a seed that plants a growth group.
        /// </summary>
        /// <summary>The structure an item starts when it is placed: the item itself for a blueprint, the kit's structure for a kit (properties.builds_structure); null for anything else.</summary>
        public static string SiteIdOf(string itemId)
        {
            if (string.IsNullOrEmpty(itemId)) return null;
            if (ConstructionSite.IsStructure(itemId)) return itemId;
            return ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo kit) && !string.IsNullOrEmpty(kit.BuildsStructure) && ConstructionSite.IsStructure(kit.BuildsStructure) ? kit.BuildsStructure : null;
        }

        public static bool IsPlaceable(string itemId)
        {
            if (string.IsNullOrEmpty(itemId)) return false;
            if (SiteIdOf(itemId) != null) return true;   // a structure (or a kit that builds one) starts as a construction site (a dirt area), no model needed
            if (!ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info) || info.Prefab == null || !info.PlayerPlaceable) return false;
            return !GrowthRegistry.TryGetGroupPlantedBy(itemId, out _);
        }

        private Transform PlacedRoot()
        {
            if (placedRoot == null) placedRoot = new GameObject("PlacedObjects").transform;
            return placedRoot;
        }

        /// <summary>The ground point under the cursor, ignoring the player and the shadow itself.</summary>
        private static bool TryCursorPoint(Camera cam, Vector2 screenPos, out Vector3 point)
        {
            point = default;
            RaycastHit[] hits = Homesteader.UI.HoverTarget.SortedHits(cam, screenPos);
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                // Aim at the ground behind a placed object so its square (not the object's top) is picked.
                if (h.collider.GetComponentInParent<PlacedObject>() != null) continue;
                point = h.point;
                // pointing at the top of a building's floor, foundation or deck: things go on it, not on the terrain under it
                s_cursorOnStructure = h.normal.y > 0.5f && h.collider.GetComponentInParent<ConstructionSite>() != null;
                return true;
            }
            return false;
        }

        private static bool s_cursorOnStructure;

        /// <summary>
        /// The height a thing rests at on a spot: the top of the floor, foundation or deck of the building the cursor is on (the ray goes down
        /// from just above the cursor, at the spot's own x and z), else the terrain.
        /// </summary>
        private static float RestY(Vector3 p, float cursorY)
        {
            float terrain = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(p);
            if (!s_cursorOnStructure || cursorY <= terrain + 0.05f) return terrain;
            float offset = terrain - Homesteader.Generation.TerrainHeightDetector.GetGroundY(p);
            RaycastHit[] hits = Physics.RaycastAll(new Vector3(p.x, cursorY + 0.4f, p.z), Vector3.down, 2f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null || h.collider.GetComponentInParent<PlacedObject>() != null) continue;
                if (h.normal.y < 0.5f || h.collider.GetComponentInParent<ConstructionSite>() == null) continue;
                return Mathf.Max(terrain, h.point.y + offset);
            }
            return terrain;   // no floor of a building under the square (the cursor was on a wall, a roof or something tall beside it): on the ground, never up at the height the cursor hit
        }

        private static float GroundY(Vector3 p)
        {
            return Homesteader.Generation.TerrainHeightDetector.GetGroundY(p);
        }

        private static float SlopeAt(Vector3 p)
        {
            float h = GroundY(p);
            float dx = GroundY(p + Vector3.right) - h;
            float dz = GroundY(p + Vector3.forward) - h;
            return Mathf.Atan(Mathf.Sqrt(dx * dx + dz * dz)) * Mathf.Rad2Deg;
        }

        private static float WaterY()
        {
            return Homesteader.Generation.TerrainHeightDetector.GetWaterY();
        }

        private static Camera GameCamera()
        {
            Camera cam = Camera.main;
            if (cam != null) return cam;
            var iso = IsometricLockedCamera.Current;
            if (iso != null && iso.TryGetComponent(out cam)) return cam;
            return FindAnyObjectByType<Camera>();
        }

        private static Vector2 PointerPosition()
        {
#if ENABLE_INPUT_SYSTEM
            return Mouse.current != null ? Mouse.current.position.ReadValue() : (Vector2)Input.mousePosition;
#else
            return Input.mousePosition;
#endif
        }

        private static bool PlaceClicked()
        {
#if ENABLE_INPUT_SYSTEM
            return Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame;
#else
            return Input.GetMouseButtonDown(0);
#endif
        }

        private static bool ConfirmPressed()
        {
#if ENABLE_INPUT_SYSTEM
            Keyboard kb = Keyboard.current;
            return kb != null && (kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame);
#else
            return Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter);
#endif
        }

        private static bool CancelPressed()
        {
#if ENABLE_INPUT_SYSTEM
            return Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame;
#else
            return Input.GetKeyDown(KeyCode.Escape);
#endif
        }

        private static bool RotatePressed(out bool reverse)
        {
#if ENABLE_INPUT_SYSTEM
            Keyboard kb = Keyboard.current;
            reverse = kb != null && kb.shiftKey.isPressed;
            return Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.PlaceRotate);
#else
            reverse = Input.GetKey(KeyCode.LeftShift);
            return Input.GetKeyDown(KeyCode.R);
#endif
        }
    }

    /// <summary>A structure or prop the player placed. Permanent: it stays until something calls <see cref="Remove"/>.</summary>
    public sealed class PlacedObject : MonoBehaviour
    {
        // Each grid square holds a stack of placed objects, bottom first (one object unless it is a stackable container).
        private static readonly Dictionary<Vector2Int, List<PlacedObject>> stacks = new Dictionary<Vector2Int, List<PlacedObject>>();
        public static IEnumerable<PlacedObject> All
        {
            get
            {
                var all = new List<PlacedObject>();
                foreach (List<PlacedObject> l in stacks.Values) all.AddRange(l);
                return all;
            }
        }

        public string ItemId { get; private set; }
        public float YawDeg { get; private set; }
        public int Level { get; private set; }         // 0 = on the ground, 1 = on top of one box, ...
        public float Height { get; private set; }      // the model's height in metres (what the next one in a stack sits on)
        public List<ContainerStack> Contents = new List<ContainerStack>();   // what a placed container holds
        private Vector2Int cell;

        /// <summary>How many objects are in this one's stack (itself included).</summary>
        public int StackCount
        {
            get
            {
                foreach (List<PlacedObject> col in ColumnsAt(transform.position))
                    if (col.Contains(this)) return col.Count;
                return 1;
            }
        }

        public bool IsTopOfStack
        {
            get
            {
                foreach (List<PlacedObject> col in ColumnsAt(transform.position))
                    if (col.Contains(this)) return col[col.Count - 1] == this;
                return false;
            }
        }

        /// <summary>
        /// Puts every placed object that stands on the GROUND back on the ground as it is now. The ground under a building site is graded (cut
        /// or filled) as its foundation goes in, which on a restart happens after the objects were put back at their saved heights, so a box
        /// placed before the grading was left floating (or buried). A stack moves as one; anything standing on a floor, foundation or deck is left alone.
        /// </summary>
        public static void SettleOnGround()
        {
            SettleColumns(All);
        }

        /// <summary>
        /// THE rule that keeps placed things from hovering, one rule for every case: the lowest piece of every stack rests on what is physically under it. That is found by looking straight down
        /// from it past its own stack, the player and a roof: the ground, a floor, a foundation, a deck, a pallet, a table, whatever is first. It comes down to that (or up, when the ground came up)
        /// and the pieces above follow it, levels renumbered from 0. Nothing is trusted to be "on a structure" or "on a pallet" by name: it has to actually touch it.
        /// </summary>
        public static void SettleColumns(IEnumerable<PlacedObject> candidates)
        {
            var done = new HashSet<PlacedObject>();
            var closed = new HashSet<PlacedObject>();
            foreach (PlacedObject o in new List<PlacedObject>(candidates))
            {
                if (o == null || done.Contains(o)) continue;
                foreach (List<PlacedObject> col in ColumnsAt(o.transform.position))
                {
                    if (!col.Contains(o)) continue;
                    bool busy = false;
                    foreach (PlacedObject c in col)
                    {
                        if (c == null) continue;
                        done.Add(c);
                        if (c.GetComponent<StackSettle>() != null || (WheelbarrowPush.Active != null && WheelbarrowPush.Active.Placed == c)) busy = true;   // falling already, or being pushed
                    }
                    if (busy) break;
                    PlacedObject bottom = col[0];
                    if (bottom == null) break;
                    float support = SupportY(col, bottom);
                    float delta = support - bottom.transform.position.y;
                    if (Mathf.Abs(delta) >= 0.02f || bottom.Level != 0)
                    {
                        float y = support;
                        int level = 0;
                        foreach (PlacedObject c in col)
                        {
                            if (c == null) continue;
                            Vector3 q = c.transform.position;
                            c.Relocate(new Vector3(q.x, y, q.z), level++);
                            y += c.Height;
                        }
                    }
                    else CloseGaps(col, closed);
                    break;
                }
            }
        }

        /// <summary>The height of the first thing under a stack's bottom piece: not the stack itself, the player or a roof (a roof is never a floor), else the ground.</summary>
        private static float SupportY(List<PlacedObject> col, PlacedObject bottom)
        {
            Vector3 p = bottom.transform.position;
            RaycastHit[] hits = Physics.RaycastAll(p + Vector3.up * 0.08f, Vector3.down, 8f, ~0, QueryTriggerInteraction.Ignore);   // (low: a thing on a shelf must not start above the shelf over it)
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider == null) continue;
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                PlacedObject po = h.collider.GetComponentInParent<PlacedObject>();
                if (po != null && col.Contains(po)) continue;                       // its own stack
                if (h.normal.y < 0.5f) continue;                                    // a side, not a top
                bool roof = false;
                for (Transform t = h.collider.transform; t != null; t = t.parent) if (t.name == "Roof") { roof = true; break; }
                if (roof) continue;
                return h.point.y;
            }
            return Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(p);
        }

        /// <summary>A piece of a stack that floats above the one under it (a gap in the column) comes down onto it.</summary>
        private static void CloseGaps(List<PlacedObject> col, HashSet<PlacedObject> done)
        {
            if (col.Count < 2 || done.Contains(col[0])) return;
            done.Add(col[0]);
            for (int i = 1; i < col.Count; i++)
            {
                PlacedObject below = col[i - 1], o = col[i];
                if (below == null || o == null || below.Height <= 0.001f) continue;
                float expected = below.transform.position.y + below.Height;
                float y = o.transform.position.y;
                if (y > expected + 0.03f) { Vector3 q = o.transform.position; q.y = expected; o.transform.position = q; }
            }
        }

        // ------------------------------------------------------------------ never left hovering

        /// <summary>
        /// Keeps placed things from hovering, for good: every few seconds, once the world is up, everything that is not held by something (the ground, a floor or a deck of a building, a
        /// pallet, the piece under it in its stack) comes down onto what is under it (<see cref="SettleOnGround"/>). It catches every way a thing was left up in the air: grading under a new
        /// building, a building taken away, the thing under a stack removed, a save from an older version.
        /// </summary>
        private sealed class Settler : MonoBehaviour
        {
            private float _next;

            [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
            private static void Bootstrap()
            {
                if (FindAnyObjectByType<Settler>() != null) return;
                var go = new GameObject("PlacedSettler");
                DontDestroyOnLoad(go);
                go.AddComponent<Settler>();
            }

            private readonly Queue<PlacedObject> _queue = new Queue<PlacedObject>();
            private readonly List<PlacedObject> _batch = new List<PlacedObject>();

            private void Update()
            {
                if (Time.unscaledTime < _next) return;
                _next = Time.unscaledTime + 0.2f;
                if (WelcomeMenuController.IsLoading) return;
                // the whole world is checked, a handful of stacks at a time (every check is a ray): a pass takes a few seconds and never costs a frame much
                if (_queue.Count == 0) foreach (PlacedObject o in All) if (o != null) _queue.Enqueue(o);
                _batch.Clear();
                for (int i = 0; i < 6 && _queue.Count > 0; i++) _batch.Add(_queue.Dequeue());
                SettleColumns(_batch);
            }
        }

        /// <summary>
        /// Stacks whose bottom is above the ground with NOTHING under it (the pallet they stood on is gone, or the piece under them was taken without
        /// the stack coming down) are lowered onto the ground, bottom first, levels renumbered. Stacks on a pallet, a floor or a deck stay.
        /// </summary>
        public static void GroundUnsupported(IEnumerable<PlacedObject> candidates)
        {
            SettleColumns(candidates);
        }

        /// <summary>Records the yaw it now faces (a wheelbarrow being pushed turns), so a save keeps it.</summary>
        public void SetYaw(float yawDeg) { YawDeg = yawDeg; }

        public void Init(string itemId, Vector3 position, float yawDeg, int level = 0)
        {
            ItemId = itemId;
            YawDeg = yawDeg;
            Level = level;
            cell = CellOf(position);
            if (!stacks.TryGetValue(cell, out List<PlacedObject> list)) { list = new List<PlacedObject>(); stacks[cell] = list; }
            list.Add(this);
            list.Sort((a, b) => a.Level.CompareTo(b.Level));

            var renderers = GetComponentsInChildren<Renderer>();
            if (renderers.Length > 0)
            {
                Bounds b = renderers[0].bounds;
                for (int i = 1; i < renderers.Length; i++) b.Encapsulate(renderers[i].bounds);
                Height = b.size.y;
            }
        }

        /// <summary>
        /// The columns (stacks) standing in the grid square containing the point. Objects that share the same spot on
        /// the ground are one column, bottom first; a square holds several columns when they were packed side by side.
        /// </summary>
        public static List<List<PlacedObject>> ColumnsAt(Vector3 point)
        {
            var result = new List<List<PlacedObject>>();
            if (!stacks.TryGetValue(CellOf(point), out List<PlacedObject> all)) return result;
            foreach (PlacedObject o in all)
            {
                if (o == null) continue;
                Vector3 p = o.transform.position;
                List<PlacedObject> col = null;
                foreach (List<PlacedObject> c in result)
                {
                    Vector3 q = c[0].transform.position;
                    if (Mathf.Abs(q.x - p.x) < 0.08f && Mathf.Abs(q.z - p.z) < 0.08f) { col = c; break; }
                }
                if (col == null) { col = new List<PlacedObject>(); result.Add(col); }
                col.Add(o);
            }
            // Things at the same x, z but at different heights are not one stack when there is air between them: one on each shelf of a shelving unit is a column per shelf.
            var split = new List<List<PlacedObject>>();
            foreach (List<PlacedObject> c in result)
            {
                c.Sort((a, b) => a.transform.position.y.CompareTo(b.transform.position.y));
                List<PlacedObject> cur = null;
                PlacedObject prev = null;
                foreach (PlacedObject o in c)
                {
                    bool apart = prev != null && prev.Height > 0.001f && o.transform.position.y > prev.transform.position.y + prev.Height + ShelfGapM;
                    if (cur == null || apart) { cur = new List<PlacedObject>(); split.Add(cur); }
                    cur.Add(o);
                    prev = o;
                }
            }
            foreach (List<PlacedObject> c in split) c.Sort((a, b) => a.Level.CompareTo(b.Level));
            return split;
        }

        private const float ShelfGapM = 0.12f;   // more air than this between two things at one spot and the upper one rests on something else (a shelf): it is not on the lower one

        /// <summary>The ground footprint (x, z in world metres) of a column: the union of its objects' bounds.</summary>
        public static Rect ColumnRect(List<PlacedObject> column)
        {
            bool any = false;
            Bounds b = default;
            foreach (PlacedObject o in column)
            {
                if (o == null) continue;
                foreach (Renderer r in o.GetComponentsInChildren<Renderer>())
                {
                    if (!any) { b = r.bounds; any = true; }
                    else b.Encapsulate(r.bounds);
                }
            }
            if (!any)
            {
                Vector3 p = column[0].transform.position;
                return new Rect(p.x - 0.4f, p.z - 0.4f, 0.8f, 0.8f);   // the model has not loaded: a generous footprint
            }
            return new Rect(b.min.x, b.min.z, b.size.x, b.size.z);
        }

        /// <summary>The placed object on top of the column that covers the point, if any.</summary>
        public static PlacedObject At(Vector3 point)
        {
            var p2 = new Vector2(point.x, point.z);
            foreach (List<PlacedObject> col in ColumnsAt(point))
            {
                Rect r = ColumnRect(col);
                if (new Rect(r.x - 0.03f, r.y - 0.03f, r.width + 0.06f, r.height + 0.06f).Contains(p2)) return col[col.Count - 1];
            }
            return null;
        }

        /// <summary>The point of the object nearest to a position (its model's bounds, not its middle): a long plank or log is reached from its end.</summary>
        public Vector3 NearestPointTo(Vector3 from)
        {
            bool any = false;
            Bounds b = default;
            foreach (Renderer r in GetComponentsInChildren<Renderer>())
            {
                if (!any) { b = r.bounds; any = true; }
                else b.Encapsulate(r.bounds);
            }
            return any ? b.ClosestPoint(from) : transform.position;
        }

        /// <summary>Moves it to another spot and files it under the grid square it now stands in.</summary>
        public void Relocate(Vector3 position, int level)
        {
            Unregister();
            transform.position = position;
            Level = level;
            cell = CellOf(position);
            if (!stacks.TryGetValue(cell, out List<PlacedObject> list)) { list = new List<PlacedObject>(); stacks[cell] = list; }
            list.Add(this);
            list.Sort((a, b) => a.Level.CompareTo(b.Level));
        }

        /// <summary>Takes it out of the world and frees its square (call from a demolish tool / any gameplay rule).</summary>
        public void Remove()
        {
            // what was stacked above it (same spot on the ground) comes down to fill the gap
            var above = new List<PlacedObject>();
            foreach (List<PlacedObject> col in ColumnsAt(transform.position))
            {
                if (!col.Contains(this)) continue;
                foreach (PlacedObject o in col) if (o != null && o != this && o.Level > Level) above.Add(o);
                break;
            }
            float cursor = transform.position.y;
            int level = Level;
            List<PlacedObject> carried = PalletDeck.IsPallet(ItemId) ? PalletDeck.Carried(this) : null;   // a pallet's load comes down with it
            Unregister();
            Destroy(gameObject);
            if (carried != null && carried.Count > 0) GroundUnsupported(carried);
            above.Sort((x, y) => x.Level.CompareTo(y.Level));
            foreach (PlacedObject o in above)
            {
                o.Level = level++;
                var settle = o.GetComponent<StackSettle>();
                if (settle == null) settle = o.gameObject.AddComponent<StackSettle>();
                settle.TargetY = cursor;
                cursor += o.Height;
            }
        }

        /// <summary>A placed object falling to its new spot after what was under it was taken (it stops at TargetY).</summary>
        private sealed class StackSettle : MonoBehaviour
        {
            public float TargetY;
            private float _speed;

            private void Update()
            {
                _speed += 9.81f * Time.deltaTime;
                Vector3 p = transform.position;
                p.y = Mathf.Max(TargetY, p.y - _speed * Time.deltaTime);
                transform.position = p;
                if (p.y <= TargetY + 0.0001f) Destroy(this);
            }
        }

        private void OnDestroy() => Unregister();

        private void Unregister()
        {
            if (!stacks.TryGetValue(cell, out List<PlacedObject> list)) return;
            list.Remove(this);
            list.RemoveAll(p => p == null);
            if (list.Count == 0) stacks.Remove(cell);
        }

        private static Vector2Int CellOf(Vector3 p)
        {
            float g = PlantingValidator.GridSizeM;
            return new Vector2Int(Mathf.FloorToInt(p.x / g), Mathf.FloorToInt(p.z / g));
        }

        /// <summary>Raises the shadow's opacity to solid, then puts the real materials back.</summary>
        public System.Collections.IEnumerator FadeToSolid(Color tint, float fromAlpha, float seconds)
        {
            for (float t = 0f; t < seconds; t += Time.deltaTime)
            {
                GhostVisual.Apply(gameObject, Color.Lerp(tint, Color.white, t / seconds), Mathf.Lerp(fromAlpha, 1f, t / seconds));
                yield return null;
            }
            GhostVisual.Restore(gameObject);
            if (!string.IsNullOrEmpty(PaintId)) ApplyPaint(PaintId);   // painted while it was still fading in
        }

        // A placed DOOR (any item whose model has "Door..." materials: the door styles of tools/make_doors.py and the plain panel doors) takes paint
        // like a building's door does: a right click with a paint can recolours its slab, panels and trim; the knob, hinges and glass keep their own.
        // Saved with the placed object (SavedPlaced.paintId). Picking the door up gives back the plain item.

        /// <summary>The paint can (item id) this placed door was painted with, or null.</summary>
        public bool Mirrored { get; set; }              // placed mirrored left to right (T while placing)
        public string PaintId { get; private set; }
        public float WireUsed;                          // a placed coil or spool of wire: the metres used from it (see Wiring.cs); a liquid container: its liters (LiquidRules.Held)
        public string SawLog;                           // a sawmill: the uncut log lying on its track (Sawmill.cs)
        public string LiquidId;                         // a placed liquid container: the liquid in it (a tank that takes several; null = its default)

        /// <summary>True when the model has something a paint can recolours.</summary>
        public bool Paintable { get { return StructureLook.HasMaterial(GetComponentsInChildren<Renderer>(true), StructureLook.DoorPaintable); } }

        /// <summary>Paints it with a paint item (also used when a save is restored). False when the item is unknown or nothing on it takes paint.</summary>
        public bool ApplyPaint(string paintItemId)
        {
            AssetCatalogItem paint = HudBindings.GetCatalogItem(paintItemId);
            if (paint == null || !Paintable) return false;
            PaintId = paintItemId;
            StructureLook.Paint(GetComponentsInChildren<Renderer>(true), StructureLook.DoorPaintable, paint);
            return true;
        }

        /// <summary>A right click with a paint can: paints the placed door under the cursor. False when the first thing hit is not a paintable placed object.</summary>
        public static bool TryPaintAtRay(Ray ray, string paintItemId, Transform player)
        {
            AssetCatalogItem paint = HudBindings.GetCatalogItem(paintItemId);
            if (paint == null) return false;
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                PlacedObject p = h.collider.GetComponentInParent<PlacedObject>();
                if (p == null || !p.Paintable) return false;      // the first thing hit decides
                AssetCatalogItem item = HudBindings.GetCatalogItem(p.ItemId);
                string title = item != null ? item.name : "Door";
                if (player != null && Vector3.Distance(player.position, p.transform.position) > 8f)
                {
                    ToastNotificationSystem.ShowInfo("Too far", "Move closer to paint it.");
                    return true;
                }
                p.ApplyPaint(paintItemId);
                return true;
            }
            return false;
        }
    }

    /// <summary>Turns a model translucent and tinted (an unlit copy of each material keeping its texture), and back.</summary>
    public static class GhostVisual
    {
        private sealed class Originals : MonoBehaviour
        {
            public readonly Dictionary<Renderer, Material[]> Shared = new Dictionary<Renderer, Material[]>();
            public readonly List<Material> Made = new List<Material>();
        }

        public static void Apply(GameObject go, Color tint, float alpha)
        {
            Originals o = go.GetComponent<Originals>();
            if (o == null)
            {
                o = go.AddComponent<Originals>();
                Shader sh = Shader.Find("Universal Render Pipeline/Lit");   // shaded, in ONE colour: the model's own texture is not used (a red sofa under a blue tint read as an invalid red)
                foreach (Renderer r in go.GetComponentsInChildren<Renderer>(true))
                {
                    if (r is ParticleSystemRenderer) continue;
                    Material[] src = r.sharedMaterials;
                    o.Shared[r] = src;
                    var made = new Material[src.Length];
                    for (int i = 0; i < src.Length; i++)
                    {
                        var m = new Material(sh) { name = "Ghost" };
                        m.SetFloat("_Metallic", 0f);
                        m.SetFloat("_Smoothness", 0.15f);
                        m.SetFloat("_Surface", 1f);
                        m.SetFloat("_Blend", 0f);
                        m.SetFloat("_ZWrite", 0f);
                        m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                        m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                        m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                        m.SetOverrideTag("RenderType", "Transparent");
                        m.renderQueue = 3000;
                        made[i] = m;
                        o.Made.Add(m);
                    }
                    r.sharedMaterials = made;
                    r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                }
            }
            var c = new Color(tint.r, tint.g, tint.b, alpha);
            foreach (Material m in o.Made) m.SetColor("_BaseColor", c);
        }

        public static void Restore(GameObject go)
        {
            Originals o = go.GetComponent<Originals>();
            if (o == null) return;
            foreach (var kv in o.Shared)
            {
                if (kv.Key == null) continue;
                kv.Key.sharedMaterials = kv.Value;
                kv.Key.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            }
            foreach (Material m in o.Made) if (m != null) Object.Destroy(m);
            Object.Destroy(o);
        }
    }
}
