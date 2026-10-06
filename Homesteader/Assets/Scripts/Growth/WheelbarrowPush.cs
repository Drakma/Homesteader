using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Push items (a wheelbarrow: container.pushable) and heaps of bulk material.
    /// Right click on a placed wheelbarrow with an empty active slot takes the handles: it follows the player (slower, no running) until a
    /// right click puts it down. Shift + right click empties it onto the ground as piles (the pile items of the material, fewest piles that
    /// hold it; anything else drops as loose items). A shovel (a container that accepts the #bulk shovelfuls) in the active slot scoops from a
    /// pile and moves shovelfuls to and from a placed wheelbarrow through the ordinary container transfer.
    /// A pile is a placed pile item whose contents are shovelfuls: untouched (no contents) it is a whole pile; once scooped its contents are what
    /// is left, and it shrinks to match (<see cref="PileVisual"/>).
    /// </summary>
    public sealed class WheelbarrowPush : MonoBehaviour
    {
        private const float HandleOffsetM = 0.62f;   // from the player to the middle of the wheelbarrow (the handles are at the near end)

        public static WheelbarrowPush Active { get; private set; }

        /// <summary>The wheelbarrow being pushed, or null.</summary>
        public PlacedObject Placed => _placed;

        private PlacedObject _placed;
        private PedController _ped;
        private Collider[] _colliders;
        private bool[] _colliderWas;
        private Vector3 _lastFiled;

        public static bool IsPushItem(string itemId)
        {
            AssetCatalogItem info = HudBindings.GetCatalogItem(itemId);
            return info != null && info.container_pushable;
        }

        /// <summary>A push item lying loose on the ground (dropped, or from the asset spawner) stands up as a placed object, so it can be pushed. False for anything else.</summary>
        public static bool TryStandUp(WorldItem lying, out PlacedObject standing)
        {
            standing = null;
            if (lying == null || !(IsPushItem(lying.ItemId) || IsPile(lying.ItemId))) return false;
            if (!ItemRegistry.TryGet(lying.ItemId, out ItemRegistry.ItemInfo info) || info.Prefab == null) return false;
            Vector3 at = lying.transform.position;
            Object.Destroy(lying.gameObject);
            standing = PlacementController.SpawnPlaced(lying.ItemId, info, at, Random.Range(0f, 360f), false);
            return standing != null;
        }

        /// <summary>Drops a push item on the ground as a placed object (it is meant to be pushed, not picked at). False when the item is not one or has no model.</summary>
        public static bool TryDropPlaced(string itemId, Vector3 at)
        {
            if (!(IsPushItem(itemId) || IsPile(itemId)) || !ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info) || info.Prefab == null) return false;
            at.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(at);
            PlacementController.SpawnPlaced(itemId, info, at, Random.Range(0f, 360f), false);
            return true;
        }

        public static bool IsPile(string itemId) => GrowthRegistry.BulkOf(itemId, out _, out _);

        private static bool IsScoop(string itemId) => GrowthRegistry.ToolMatches("#bulk", itemId);

        // ------------------------------------------------------------------ pushing

        public static void Grab(PlacedObject wheelbarrow)
        {
            if (wheelbarrow == null || Active != null) return;
            var ped = PedController.Current;
            if (ped == null) return;
            if (!PlantingValidator.InReach(ped.transform, wheelbarrow.transform.position, GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to take the handles.");
                return;
            }
            var push = wheelbarrow.gameObject.AddComponent<WheelbarrowPush>();
            push._placed = wheelbarrow;
            push._ped = ped;
            push._colliders = wheelbarrow.GetComponentsInChildren<Collider>();
            push._colliderWas = new bool[push._colliders.Length];
            for (int i = 0; i < push._colliders.Length; i++) { push._colliderWas[i] = push._colliders[i].enabled; push._colliders[i].enabled = false; }   // it must not block the player pushing it
            push._lastFiled = wheelbarrow.transform.position;
            ped.NoRun = true;
            ped.Carrying = true;
            Active = push;
            push.Follow(1f);
        }

        private void LateUpdate()
        {
            if (_placed == null || _ped == null) { Cleanup(); Destroy(this); return; }
            Follow(Mathf.Clamp01(Time.deltaTime * 14f));
        }

        private void Follow(float turn)
        {
            Vector3 dir = Quaternion.Euler(0f, _ped.transform.eulerAngles.y - _ped.modelRotationOffset, 0f) * Vector3.forward;
            Vector3 pos = _ped.transform.position + dir * HandleOffsetM;
            pos.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(pos);
            // the wheel is at the model's -x end, the handles at +x: the wheelbarrow points the way the player faces
            Quaternion want = Quaternion.FromToRotation(Vector3.right, dir);   // turned round: the wheel leads
            Quaternion rot = Quaternion.Slerp(_placed.transform.rotation, want, turn);
            _placed.transform.rotation = rot;
            if ((pos - _lastFiled).sqrMagnitude > 0.0025f)
            {
                _placed.Relocate(pos, 0);          // filed under the grid square it is in now (a save while pushing keeps it)
                _lastFiled = pos;
            }
            else _placed.transform.position = pos;
            _placed.SetYaw(rot.eulerAngles.y);

            float cap = Mathf.Max(1f, ContainerRules.Capacity(_placed.ItemId));
            float load = Mathf.Clamp01(ContainerRules.Used(_placed.Contents) / cap);
            _ped.PushSpeedFactor = 1f;   // a pushed wheelbarrow adds no encumbrance and no slowdown: the player walks at the normal speed (running is off)
        }

        /// <summary>Puts the wheelbarrow down where it is.</summary>
        public void PutDown()
        {
            if (_placed != null) _placed.Relocate(_placed.transform.position, 0);
            Cleanup();
            Destroy(this);
        }

        private void Cleanup()
        {
            if (_colliders != null)
                for (int i = 0; i < _colliders.Length; i++) if (_colliders[i] != null) _colliders[i].enabled = _colliderWas[i];
            if (_ped != null) { _ped.PushSpeedFactor = 1f; _ped.NoRun = false; _ped.Carrying = false; }
            if (Active == this) Active = null;
            _colliders = null;
        }

        private void OnDestroy() { if (Active == this) Cleanup(); }

        /// <summary>Shift + right click while pushing: empty it in front.</summary>
        public void Dump()
        {
            if (_placed == null) return;
            DumpContents(_placed, _placed.transform.position + _placed.transform.right * 1.3f);
        }

        /// <summary>Shift + right click on a standing wheelbarrow.</summary>
        public static void DumpPlaced(PlacedObject wheelbarrow)
        {
            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, wheelbarrow.transform.position, GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to reach that.");
                return;
            }
            DumpContents(wheelbarrow, wheelbarrow.transform.position + wheelbarrow.transform.right * 1.3f);
        }

        // ------------------------------------------------------------------ dumping

        private static void DumpContents(PlacedObject from, Vector3 front)
        {
            string name = HudBindings.GetItemName(from.ItemId);
            if (from.Contents == null || from.Contents.Count == 0) { ToastNotificationSystem.ShowInfo(name, name + " is empty."); return; }
            Vector3 right = Vector3.Cross(Vector3.up, (front - from.transform.position).normalized);
            Vector3 along = (front - from.transform.position).normalized;
            int spot = 0, piles = 0, loose = 0;
            foreach (ContainerStack st in new List<ContainerStack>(from.Contents))
            {
                if (IsScoop(st.ItemId))
                {
                    // onto a pile of this material close by (growing it), else a new pile; what a full pile cannot take starts the next one beside it
                    Vector3 at = front + right * (((spot % 3) - 1) * 1.3f) + along * ((spot / 3) * 1.3f);
                    spot++;
                    int placed = PileService.AddAt(st.ItemId, st.Count, at, Random.Range(0f, 360f));
                    if (placed > 0) piles++;
                    ContainerRules.Remove(from.Contents, st.ItemId, placed);
                    if (placed < st.Count && GrowthRegistry.PilesOfScoop(st.ItemId).Count == 0) loose += DropLoose(st.ItemId, st.Count - placed, front);
                }
                else
                {
                    int n = DropLoose(st.ItemId, Mathf.Min(st.Count, 24), front);
                    ContainerRules.Remove(from.Contents, st.ItemId, n);
                    loose += n;
                }
            }
            if (piles + loose <= 0) ToastNotificationSystem.ShowInfo(name, "There is no room to empty it here.");
        }

        /// <summary>Drops shovelfuls of a bulk material as the fewest piles that hold them (small / medium / large), laid out in a row round the point. Returns the piles made.</summary>
        public static int DropAsPiles(string scoopId, int scoops, Vector3 front, Vector3 along)
        {
            int spot = 0;
            return DropAsPiles(scoopId, scoops, front, along, ref spot, out _);
        }

        private static int DropAsPiles(string scoopId, int scoops, Vector3 front, Vector3 along, ref int spot, out int remaining)
        {
            Vector3 right = Vector3.Cross(Vector3.up, along.normalized);
            along = along.normalized;
            List<KeyValuePair<string, int>> sizes = GrowthRegistry.PilesOfScoop(scoopId);
            remaining = scoops;
            int piles = 0;
            while (remaining > 0 && sizes.Count > 0)
            {
                // the smallest pile that holds what is left; when none does, the biggest one and go round again
                KeyValuePair<string, int> pick = sizes[sizes.Count - 1];
                foreach (var s in sizes) if (s.Value >= remaining) { pick = s; break; }
                int take = Mathf.Min(remaining, pick.Value);
                Vector3 at = front + right * (((spot % 3) - 1) * 1.3f) + along * ((spot / 3) * 1.3f);
                if (!SpawnPile(pick.Key, scoopId, take, pick.Value, at)) break;
                remaining -= take;
                spot++;
                piles++;
            }
            return piles;
        }

        private static int DropLoose(string itemId, int count, Vector3 around)
        {
            int dropped = 0;
            for (int i = 0; i < count; i++)
            {
                Vector2 jitter = Random.insideUnitCircle * 0.8f;
                if (!WorldItem.TryDrop(itemId, around + new Vector3(jitter.x, 0f, jitter.y))) break;
                dropped++;
            }
            return dropped;
        }

        /// <summary>The fewest piles that hold this many shovelfuls: (pile item id, shovelfuls in it), the last one possibly part of a pile.</summary>
        public static List<KeyValuePair<string, int>> PlanPiles(string scoopId, int scoops)
        {
            var plan = new List<KeyValuePair<string, int>>();
            List<KeyValuePair<string, int>> sizes = GrowthRegistry.PilesOfScoop(scoopId);
            int remaining = scoops;
            while (remaining > 0 && sizes.Count > 0)
            {
                KeyValuePair<string, int> pick = sizes[sizes.Count - 1];
                foreach (var s in sizes) if (s.Value >= remaining) { pick = s; break; }
                int take = Mathf.Min(remaining, pick.Value);
                plan.Add(new KeyValuePair<string, int>(pick.Key, take));
                remaining -= take;
            }
            return plan;
        }

        /// <summary>Puts one pile (whole, or part of one holding the given shovelfuls) at a spot, turned to the given heading. Null when the pile has no model.</summary>
        public static PlacedObject SpawnPileAt(string pileId, string scoopId, int scoops, Vector3 at, float yawDeg)
        {
            if (!ItemRegistry.TryGet(pileId, out ItemRegistry.ItemInfo info) || info.Prefab == null) return null;
            GrowthRegistry.BulkOf(pileId, out _, out int full);
            at.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(at);
            List<ContainerStack> contents = scoops >= full ? null : new List<ContainerStack> { new ContainerStack { ItemId = scoopId, Count = scoops } };
            return PlacementController.SpawnPlaced(pileId, info, at, yawDeg, false, 0, contents);
        }

        private static bool SpawnPile(string pileId, string scoopId, int scoops, int fullScoops, Vector3 at)
        {
            if (!ItemRegistry.TryGet(pileId, out ItemRegistry.ItemInfo info) || info.Prefab == null) return false;
            at.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(at);
            // a whole pile has no contents; a part of one holds the shovelfuls that are left
            List<ContainerStack> contents = scoops >= fullScoops ? null : new List<ContainerStack> { new ContainerStack { ItemId = scoopId, Count = scoops } };
            PlacementController.SpawnPlaced(pileId, info, at, Random.Range(0f, 360f), false, 0, contents);
            return true;
        }

        // ------------------------------------------------------------------ shovelling

        /// <summary>
        /// Right click on a pile with a shovel (a container that takes the pile's shovelfuls) in the active slot: one shovelful goes onto the
        /// shovel. False when the active slot is not such a shovel, so the click carries on as usual.
        /// </summary>
        public static bool TryScoop(PlacedObject pile)
        {
            if (!GrowthRegistry.BulkOf(pile.ItemId, out string scoopId, out int total)) return false;
            HudState hud = HudState.Active;
            if (hud == null) return false;
            hud.EnsureToolbarSlots();
            int index = hud.SelectedSlot;
            if (index < 0 || index >= hud.Toolbar.Count) return false;
            ToolbarSlotData slot = hud.Toolbar[index];
            if (slot.Count <= 0 || string.IsNullOrEmpty(slot.IconId) || !ContainerRules.IsContainer(slot.IconId)) return false;
            if (slot.Contents == null) slot.Contents = new List<ContainerStack>();
            if (!ContainerRules.Accepts(slot.IconId, scoopId, slot.Contents)) return false;

            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, pile.transform.position, GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the pile.");
                return true;
            }
            string pileName = HudBindings.GetItemName(pile.ItemId);
            // one scoop fills the shovel: as many shovelfuls as it has room for, and the pile has
            int onPile = PileService.ScoopsIn(pile, out _);
            int room = ContainerRules.RoomFor(slot.IconId, slot.Contents, scoopId);
            int taken = room > 0 ? ContainerRules.Add(slot.IconId, slot.Contents, scoopId, Mathf.Min(room, onPile)) : 0;
            if (taken <= 0)
            {
                ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(slot.IconId), HudBindings.GetItemName(slot.IconId) + " is full.");
                return true;
            }
            int leftOnPile = onPile - taken;
            hud.Toolbar[index] = slot;
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            PileService.SetScoops(pile, leftOnPile);    // the pile shrinks (and goes down a stage when it should); none left: it is gone
            return true;
        }

        public static void AttachPileVisual(PlacedObject placed)
        {
            if (placed != null && IsPile(placed.ItemId) && placed.GetComponent<PileVisual>() == null) placed.gameObject.AddComponent<PileVisual>();
        }
    }

    /// <summary>Scales a heap to how full its stage is (the cube root of the share, never below about half: the stage below takes over).</summary>
    public sealed class PileVisual : MonoBehaviour
    {
        private PlacedObject _placed;
        private float _scale = -1f;

        private void Awake() { _placed = GetComponent<PlacedObject>(); }

        private void Update()
        {
            if (_placed == null || Time.frameCount % 15 != 0) return;
            float s = PileService.ScaleOf(_placed);
            if (Mathf.Approximately(s, _scale)) return;
            _scale = s;
            transform.localScale = Vector3.one * s;
        }
    }
}
