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
    /// (default 12.5 degrees, Shift+R turns the other way). Enter or a second left click on a valid square consumes one
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
            if (hud == null || HudBindings.KeyboardCaptured) { HideGhost(); return; }

            HandlePickupClick(hud);   // right click on a placed object takes it back
            if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.DropItem)) DropHeldItem();

            string heldId = HeldItemId();
            bool structure = ConstructionSite.IsStructure(heldId);
            ItemRegistry.ItemInfo info = null;
            if (!IsPlaceable(heldId) || (!structure && !ItemRegistry.TryGet(heldId, out info))) { placing = false; HideGhost(); return; }
            if (placing && heldId != placingId) placing = false;            // another item was selected
            if (placing && CancelPressed()) placing = false;
            if (placing)
            {
                var walker = FindAnyObjectByType<PedController>();
                if (walker != null && (walker.transform.position - placingPedPos).sqrMagnitude > 0.0025f) placing = false;   // moved more than 5 cm
            }

            Vector2 pointer = PointerPosition();
            Camera cam = GameCamera();

            // Not placing yet: a placeable item in hand does nothing until it is clicked. That click brings out the shadow.
            if (!placing)
            {
                HideGhost();
                if (cam != null && PlaceClicked() && !hud.IsPointerOverUI(pointer))
                {
                    placing = true;
                    placingId = heldId;
                    placingStartFrame = Time.frameCount;
                    var starter = FindAnyObjectByType<PedController>();
                    placingPedPos = starter != null ? starter.transform.position : Vector3.zero;
                }
                if (!placing) return;
            }

            if (RotatePressed(out bool reverse))
                rotationSteps += reverse ? -1 : 1;

            if (cam == null || hud.IsPointerOverUI(pointer)) { HideGhost(); return; }

            if (!TryCursorPoint(cam, pointer, out Vector3 hitPoint)) { HideGhost(); return; }
            if (!EnsureGhost(heldId, info)) return;   // model still loading

            ghost.SetActive(true);
            // A structure turns in quarter turns so its walls stay on the grid; everything else turns by the usual step.
            ghost.transform.rotation = Quaternion.Euler(0f, rotationSteps * (structure ? 90f : GameRules.Placement.RotateStepDeg), 0f);
            var ped = FindAnyObjectByType<PedController>();
            // Over a pallet's deck the item rests ON the pallet, in the pallet's own turn, packed in its free space.
            PlacedObject pallet = !structure && !PalletDeck.IsPallet(heldId) ? PalletDeck.PalletUnder(hitPoint) : null;
            Plan plan;
            if (pallet != null) plan = MakePalletPlan(pallet, heldId, hitPoint, ped != null ? ped.transform : null);
            else plan = structure ? MakeSitePlan(heldId, hitPoint, ghost.transform.rotation.eulerAngles.y, ped != null ? ped.transform : null)
                                  : MakePlan(heldId, hitPoint, GhostFootprint(), ped != null ? ped.transform : null);
            lastReason = plan.Reason;

            ghost.transform.position = plan.Position;
            GhostVisual.Apply(ghost, plan.Valid ? ValidTint : InvalidTint, GhostAlpha);

            // Enter, or a second click, puts it down.
            bool confirm = ConfirmPressed() || (PlaceClicked() && Time.frameCount != placingStartFrame);
            if (confirm)
            {
                if (!plan.Valid) { ToastNotificationSystem.ShowWarning("Can't place here", plan.Reason); return; }
                if (structure) PlaceSite(heldId, plan, ghost.transform.rotation.eulerAngles.y);
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
            var ped = FindAnyObjectByType<PedController>();
            if (ped == null) return;

            string id = slot.IconId;
            bool all = Keyboard.current != null && Keyboard.current.shiftKey.isPressed;
            int count = all ? Mathf.Min(slot.Count, 24) : 1;
            Vector3 facing = Quaternion.Euler(0f, ped.transform.eulerAngles.y - ped.modelRotationOffset, 0f) * Vector3.forward;
            Vector3 front = ped.transform.position + facing * 1.2f;

            bool holdsThings = slot.Contents != null && slot.Contents.Count > 0;
            if (holdsThings)
            {
                // a container with things in it keeps them: it stands on the ground as itself
                if (!ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo info) || info.Prefab == null || !info.Placeable)
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
            if (dropped > 0) ToastNotificationSystem.ShowCounted("drop:" + id, "Dropped", "Dropped {0}x " + HudBindings.GetItemName(id).Replace("{", "{{").Replace("}", "}}") + ".", dropped);
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

            // A right click on a construction site itself (its dirt area or structure) builds the next stage when it is ready.
            ConstructionSite site = ConstructionSite.UnderCursor();
            if (site != null)
            {
                var builder = FindAnyObjectByType<PedController>();
                // The chimney of a finished building: firewood goes into its fireplace, a lighter lights it.
                if (site.Fireplace != null && site.Fireplace.CursorOnChimney() && site.Fireplace.Use(ConstructionSite.HeldItem(), builder != null ? builder.transform : null))
                    return;
                bool shiftHeld = Keyboard.current != null && Keyboard.current.shiftKey.isPressed;
                // Shift + right click takes back a site that has not been started; a plain right click builds the stage.
                if (shiftHeld && site.Stage == 0) site.TryCancel(builder != null ? builder.transform : null);
                else site.TryBuild(builder != null ? builder.transform : null);
                return;
            }

            PlacedObject target = PlacedUnderCursor();
            if (target == null)
            {
                // an item lying on the ground (a dropped item, a felled tree's log): right click picks it up
                WorldItem lying = WorldItem.UnderCursor(GameCamera(), pointer);
                if (lying != null)
                {
                    var collector = FindAnyObjectByType<PedController>();
                    lying.PickUp(collector != null ? collector.transform : null);
                }
                return;
            }
            // A placed container: with something in the active slot a right click moves items between the two; with an empty
            // active slot it picks the container up like anything else.
            HudState state = HudState.Active;
            bool activeSlotEmpty = state == null || state.SelectedSlot < 0 || state.SelectedSlot >= state.Toolbar.Count
                || state.Toolbar[state.SelectedSlot].Count <= 0 || string.IsNullOrEmpty(state.Toolbar[state.SelectedSlot].IconId);
            if (ContainerRules.IsContainer(target.ItemId) && !activeSlotEmpty) { TransferWithContainer(target); return; }
            PickUp(target);
        }

        /// <summary>
        /// Right click on a placed container while the active slot holds something. Items the container accepts go IN (as
        /// many as fit by weight; the rest stays in the slot). Otherwise, when the slot holds an item the container also has
        /// and is not full, items come OUT into the slot (as many as it takes; the rest stays in the container).
        /// </summary>
        private static void TransferWithContainer(PlacedObject box)
        {
            var ped = FindAnyObjectByType<PedController>();
            if (ped != null && !PlantingValidator.InReach(ped.transform, box.transform.position, GameRules.Placement.ReachCells))
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
            string boxName = HudBindings.GetItemName(box.ItemId);
            if (box.Contents == null) box.Contents = new List<ContainerStack>();
            bool slotHasItems = slot.Count > 0 && !string.IsNullOrEmpty(slot.IconId);

            // A container in the active slot (a basket in hand): it is its CONTENTS that move, not the basket itself.
            if (slotHasItems && ContainerRules.IsContainer(slot.IconId))
            {
                TransferBetweenContainers(box, slot, index, hud, boxName);
                return;
            }

            // IN: the slot's items go into the container.
            if (slotHasItems && ContainerRules.Accepts(box.ItemId, slot.IconId, box.Contents))
            {
                int moved = ContainerRules.Add(box.ItemId, box.Contents, slot.IconId, slot.Count);
                if (moved > 0)
                {
                    slot.Count -= moved;
                    hud.Toolbar[index] = slot.Count > 0 ? slot : ToolbarSlotData.Empty();
                    FinishTransfer(hud);
                    ToastNotificationSystem.ShowCounted("transfer_in:" + slot.IconId, boxName, "Put {0}x " + Brace(HudBindings.GetItemName(slot.IconId)) + " in.", moved);
                    return;
                }
                // Full of that: fall through and try to take some out instead.
            }

            // OUT: the container's items go into the slot.
            string item = null;
            int room = 0;
            int maxStack = 0;
            if (slotHasItems && box.Contents.Exists(c => c.ItemId == slot.IconId) && !ContainerRules.IsContainer(slot.IconId))
            {
                item = slot.IconId;
                maxStack = Mathf.Max(1, HudBindings.GetMaxStack(item));
                room = maxStack - slot.Count;
            }

            if (item == null || room <= 0)
            {
                if (slotHasItems && !ContainerRules.Accepts(box.ItemId, slot.IconId, box.Contents))
                    ToastNotificationSystem.ShowInfo(boxName, boxName + " does not take " + HudBindings.GetItemName(slot.IconId) + ".");
                else if (slotHasItems && ContainerRules.RoomFor(box.ItemId, box.Contents, slot.IconId) <= 0)
                    ToastNotificationSystem.ShowInfo(boxName, boxName + " is full.");
                else if (box.Contents.Count == 0)
                    ToastNotificationSystem.ShowInfo(boxName, boxName + " is empty.");
                else
                    ToastNotificationSystem.ShowInfo(boxName, "Your active slot is full.");
                return;
            }

            ContainerStack stack = box.Contents.Find(c => c.ItemId == item);
            int take = Mathf.Min(room, stack != null ? stack.Count : 0);
            if (take <= 0) return;
            ContainerRules.Remove(box.Contents, item, take);
            slot = slotHasItems ? slot : new ToolbarSlotData { IconId = item, Count = 0 };
            slot.Count += take;
            hud.Toolbar[index] = slot;
            FinishTransfer(hud);
            if (box.Contents.Count == 0 && ContainerRules.IsDisposable(box.ItemId)) box.Remove();   // an emptied cardboard box goes away
            ToastNotificationSystem.ShowCounted("transfer_out:" + item, boxName, "Took {0}x " + Brace(HudBindings.GetItemName(item)) + " out.", take);
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
                int n = ContainerRules.Add(box.ItemId, box.Contents, st.ItemId, st.Count);
                if (n <= 0) continue;
                ContainerRules.Remove(held.Contents, st.ItemId, n);
                movedIn += n;
            }
            if (movedIn > 0)
            {
                hud.Toolbar[slotIndex] = held;
                FinishTransfer(hud);
                ToastNotificationSystem.ShowCounted("transfer_in:" + box.GetHashCode(), boxName, "Moved {0} items in from " + Brace(heldName) + ".", movedIn);
                return;
            }

            int movedOut = 0;
            foreach (ContainerStack st in new List<ContainerStack>(box.Contents))
            {
                int n = ContainerRules.Add(held.IconId, held.Contents, st.ItemId, st.Count);
                if (n <= 0) continue;
                ContainerRules.Remove(box.Contents, st.ItemId, n);
                movedOut += n;
            }
            if (movedOut > 0)
            {
                hud.Toolbar[slotIndex] = held;
                FinishTransfer(hud);
                ToastNotificationSystem.ShowCounted("transfer_out:" + box.GetHashCode(), boxName, "Moved {0} items out to " + Brace(heldName) + ".", movedOut);
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
        public static bool PickUp(PlacedObject any)
        {
            if (any == null) return false;
            PlacedObject top = any;
            foreach (List<PlacedObject> col in PlacedObject.ColumnsAt(any.transform.position))
                if (col.Contains(any)) { top = col[col.Count - 1]; break; }

            var ped = FindAnyObjectByType<PedController>();
            if (ped != null && !PlantingValidator.InReach(ped.transform, top.transform.position, GameRules.Placement.ReachCells))
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
            else
            {
                AssetCatalogItem cat = HudBindings.GetCatalogItem(id);
                int added = hud.AddItemToToolbar(id, 1, cat != null ? Mathf.Max(1, cat.max_stack) : 64);
                if (added <= 0) { ToastNotificationSystem.ShowWarning("Toolbar full", "No room in the toolbar for that."); return false; }
            }
            top.Remove();
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            ToastNotificationSystem.ShowCounted("pickup:" + id, "Picked up", "Picked up {0}x " + HudBindings.GetItemName(id).Replace("{", "{{").Replace("}", "}}") + ".", 1);
            return true;
        }

        // ------------------------------------------------------------------ placing

        private void Place(string itemId, ItemRegistry.ItemInfo info, Plan plan, Quaternion rotation)
        {
            HudState state = HudState.Active;
            // A container keeps what is in it when it is put down.
            List<ContainerStack> contents = state.SelectedSlot >= 0 && state.SelectedSlot < state.Toolbar.Count ? state.Toolbar[state.SelectedSlot].Contents : null;
            if (!state.ConsumeFromSelectedSlot(1)) return;
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

            SpawnPlaced(itemId, info, plan.Position, rotation.eulerAngles.y, true, plan.Level, contents);
        }

        private static Transform s_placedRoot;

        /// <summary>
        /// Creates a placed object from a loaded model template. fade = true starts as the translucent shadow and
        /// fades to solid (a fresh placement); false is a solid object at once (restoring a save).
        /// </summary>
        public static PlacedObject SpawnPlaced(string itemId, ItemRegistry.ItemInfo info, Vector3 cell, float yawDeg, bool fade, int level = 0, List<ContainerStack> contents = null)
        {
            if (s_placedRoot == null) s_placedRoot = new GameObject("PlacedObjects").transform;
            // Snap to the terrain surface (just above, not 3 m above); a container stacked on another keeps the height it was given.
            if (level <= 0) cell = Homesteader.Generation.TerrainHeightDetector.PlaceOnGround(cell);
            GameObject obj = Instantiate(info.Prefab, s_placedRoot);
            obj.SetActive(true);                       // templates live inactive
            obj.transform.SetPositionAndRotation(cell, Quaternion.Euler(0f, yawDeg, 0f));
            var placed = obj.AddComponent<PlacedObject>();
            placed.Init(itemId, cell, yawDeg, level);
            if (contents != null) placed.Contents = ContainerRules.Clone(contents);
            ContainerFillView.AttachIfContainer(placed);   // what is inside shows as blocks that fill the container
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

        /// <summary>The placed object under the mouse pointer (a direct hit on its collider), or null.</summary>
        public static PlacedObject PlacedUnderCursor()
        {
            Camera cam = GameCamera();
            if (cam == null) return null;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(PointerPosition()), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
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
                if (apart < (other.Footprint.magnitude + foot.magnitude) * 0.5f) { plan.Reason = "Another structure is in the way."; return plan; }
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

        private Plan MakePalletPlan(PlacedObject pallet, string itemId, Vector3 hit, Transform player)
        {
            var plan = new Plan { Position = hit };
            ghost.transform.rotation = Quaternion.Euler(0f, pallet.transform.eulerAngles.y, 0f);   // aligned with the pallet
            if (!PalletDeck.LocalRect(pallet.transform, ghost, out Rect mine)) { plan.Reason = "Loading..."; return plan; }
            if (player != null && !PlantingValidator.InReach(player, pallet.transform.position, GameRules.Placement.ReachCells))
            {
                plan.Reason = $"You can only place things within {GameRules.Placement.ReachCells} squares of you.";
                return plan;
            }
            if (!PalletDeck.FindSpot(pallet, itemId, new Vector2(mine.width, mine.height), hit, null, out Vector3 pos, out int level, out string reason))
            {
                plan.Reason = reason;
                return plan;
            }
            plan.Position = pos;
            plan.Level = level;
            plan.Valid = true;
            return plan;
        }

        private void PlaceSite(string structureId, Plan plan, float yawDeg)
        {
            HudState state = HudState.Active;
            if (!state.ConsumeFromSelectedSlot(1)) return;
            HudBindings.Instance.RefreshToolbar();
            ConstructionSite.Create(structureId, plan.Position, yawDeg);
            ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(structureId), "Site marked. Hover it to see what the foundation needs.");
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
            center.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(center);
            plan.Position = center;
            if (!ValidateGround(center, player, out string reason)) { plan.Reason = reason; return plan; }

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
                plan.Position = GroundAt(best);
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
                    plan.Position = GroundAt(centers[centers.Length - 1]);
                    plan.Valid = true;
                    return plan;
                }
            }

            plan.Reason = fullStackHere ? "That stack is as high as it goes and there is no room beside it." : "There is no room left on that square.";
            return plan;
        }

        private static Vector3 GroundAt(Vector2 xz)
        {
            var p = new Vector3(xz.x, 0f, xz.y);
            p.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(p);
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
        }

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
        public static bool IsPlaceable(string itemId)
        {
            if (string.IsNullOrEmpty(itemId)) return false;
            if (ConstructionSite.IsStructure(itemId)) return true;   // a structure starts as a construction site (a dirt area), no model needed
            if (!ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info) || info.Prefab == null || !info.Placeable) return false;
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
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(screenPos), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                // Aim at the ground behind a placed object so its square (not the object's top) is picked.
                if (h.collider.GetComponentInParent<PlacedObject>() != null) continue;
                point = h.point;
                return true;
            }
            return false;
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
            var iso = FindAnyObjectByType<IsometricLockedCamera>();
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
            foreach (List<PlacedObject> c in result) c.Sort((a, b) => a.Level.CompareTo(b.Level));
            return result;
        }

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
            Unregister();
            Destroy(gameObject);
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
                Shader sh = Shader.Find("Universal Render Pipeline/Unlit");
                foreach (Renderer r in go.GetComponentsInChildren<Renderer>(true))
                {
                    if (r is ParticleSystemRenderer) continue;
                    Material[] src = r.sharedMaterials;
                    o.Shared[r] = src;
                    var made = new Material[src.Length];
                    for (int i = 0; i < src.Length; i++)
                    {
                        var m = new Material(sh) { name = "Ghost" };
                        Texture tex = src[i] != null && src[i].HasProperty("_BaseMap") ? src[i].GetTexture("_BaseMap")
                                    : src[i] != null ? src[i].mainTexture : null;
                        if (tex != null) m.SetTexture("_BaseMap", tex);
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
