using System.Collections;
using System.Collections.Generic;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// A wall shelf (a mounted item whose manifest says properties.shelf): things are stood on it in a row. A left click on it with an item in hand
    /// puts ONE on the shelf where the cursor is (slid along to the nearest free place); a right click on a thing on the shelf takes it back. What is
    /// on it stays the item it was (a part-used coil keeps its metres, a jug its liquid), is saved with the shelf (GameSave.SavedAttached.shelf*) and
    /// shows in the look-at panel. The shelf must be emptied before a wrench takes it down. docs/ATTACHED_ITEMS.md.
    /// </summary>
    public sealed class Shelf : MonoBehaviour
    {
        public const float Gap = 0.015f;          // air between two things
        public const float Overhang = 0.06f;      // how far a thing may stick out over the front edge
        public const float MaxHeight = 0.9f;      // nothing taller stands on a shelf
        public const float Reach = 3.5f;

        public sealed class Held
        {
            public string ItemId;
            public float X;              // its middle along the shelf, in the shelf's own space
            public float WireUsed;
            public string LiquidId;
            public float HalfWidth = 0.05f;
            public GameObject View;
        }

        public readonly List<Held> Items = new List<Held>();

        private float _x0, _x1, _z0, _z1, _top;   // the board's top face, in the shelf's own space
        public AttachedObject Mount { get; private set; }

        public static bool IsShelf(string itemId)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            return it != null && it.shelf;
        }

        /// <summary>Makes a mounted item a shelf when its manifest says so (called as it is mounted, after its click box is made).</summary>
        public static Shelf AttachIfShelf(AttachedObject mount)
        {
            if (mount == null || !IsShelf(mount.ItemId)) return null;
            var s = mount.gameObject.AddComponent<Shelf>();
            s.Mount = mount;
            var box = mount.GetComponent<BoxCollider>();
            Vector3 c = box != null ? box.center : Vector3.zero, e = box != null ? box.size * 0.5f : new Vector3(0.4f, 0.1f, 0.12f);
            s._x0 = c.x - e.x; s._x1 = c.x + e.x;
            s._z0 = c.z - e.z; s._z1 = c.z + e.z;
            s._top = c.y + e.y;
            return s;
        }

        /// <summary>The item (shelf and thing on it) a collider belongs to, for the look-at panel and the clicks.</summary>
        public static bool Find(Collider col, out Shelf shelf, out Held held)
        {
            shelf = col != null ? col.GetComponentInParent<Shelf>() : null;
            held = null;
            if (shelf == null) return false;
            foreach (Held h in shelf.Items)
                if (h.View != null && col.transform.IsChildOf(h.View.transform)) { held = h; break; }
            return true;
        }

        private static bool UnderCursor(Camera cam, Vector2 pointer, out Shelf shelf, out Held held, out Vector3 point)
        {
            shelf = null; held = null; point = default;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(pointer), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (Find(h.collider, out shelf, out held)) { point = h.point; return true; }
                if (h.collider.isTrigger) continue;   // a click box or zone of something else: look past it
                if (Blocks(h.collider)) break;         // something solid is in front
            }
            if (s_any > 0 && Time.unscaledTime >= s_nextLog)
            {
                s_nextLog = Time.unscaledTime + 0.5f;
                var sb = new System.Text.StringBuilder("[Shelf] click found no shelf; under the cursor: ");
                int n = 0;
                foreach (RaycastHit h in hits)
                {
                    Transform t = h.collider.transform;
                    sb.Append(t.parent != null ? t.parent.name + "/" : "").Append(t.name).Append(h.collider.isTrigger ? " (trigger)" : "").Append(" layer ").Append(t.gameObject.layer).Append(" at ").Append(h.distance.ToString("0.0")).Append("; ");
                    if (++n >= 8) break;
                }
                Dbg.Log(sb.ToString());
            }
            return false;
        }

        private static int s_any;         // how many shelves exist
        private static float s_nextLog;
        private void OnEnable() { s_any++; }
        private void OnDisable() { s_any--; }

        /// <summary>A solid thing that hides what is behind it from a click: not the ground, and not the invisible walls along the land's edge.</summary>
        private static bool Blocks(Collider c)
        {
            if (c is TerrainCollider || c.gameObject.name == "Ground") return false;
            if (c.GetComponent<Renderer>() == null && c.GetComponentInParent<Renderer>() == null && c.GetComponentInChildren<Renderer>() == null) return false;   // nothing to see: an invisible wall or zone
            return true;
        }

        // ------------------------------------------------------------------ putting on, taking off

        /// <summary>A left click with an item in hand over a shelf: one of it goes on the shelf. True when the click was for a shelf (whether or not it fitted).</summary>
        public static bool TryPutHeld(Camera cam, Vector2 pointer)
        {
            if (cam == null || AttachedObject.All.Count == 0) return false;
            HudState hud = HudState.Active;
            if (hud == null || hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return false;
            ToolbarSlotData slot = hud.Toolbar[hud.SelectedSlot];
            if (string.IsNullOrEmpty(slot.IconId) || slot.Count <= 0) return false;
            if (!UnderCursor(cam, pointer, out Shelf shelf, out _, out Vector3 point)) return false;
            string id = slot.IconId, name = HudBindings.GetItemName(shelf.Mount.ItemId);
            Dbg.Log("[Shelf] left click on " + shelf.Mount.ItemId + " with " + id);
            if (IsShelf(id)) return false;   // a shelf in hand is being mounted, not shelved
            var ped = PedController.Current;
            if (ped != null && Flat(ped.transform.position, shelf.transform.position) > Reach) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to reach that."); return true; }
            if (slot.Contents != null && slot.Contents.Count > 0) { ToastNotificationSystem.ShowInfo(name, "Empty it first: a container goes on a shelf empty."); return true; }
            if (!ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo info) || info.Prefab == null) { ToastNotificationSystem.ShowInfo(name, HudBindings.GetItemName(id) + " cannot stand on a shelf."); return true; }
            GlbTemplate glb = info.Prefab.GetComponent<GlbTemplate>();
            if (glb != null && !glb.Ready) { glb.EnsureLoading(); Dbg.Log("[Shelf] the model of " + id + " is still loading"); return true; }   // its model is still coming: the next click does it
            var held = new Held { ItemId = id, WireUsed = slot.WireUsed, LiquidId = slot.LiquidId };
            if (!shelf.MakeView(held, info, out Vector3 size)) { ToastNotificationSystem.ShowInfo(name, HudBindings.GetItemName(id) + " cannot stand on a shelf."); return true; }
            string why = size.y > MaxHeight ? "It is too tall for a shelf." : size.z > (shelf._z1 - shelf._z0) + Overhang ? "It is too deep for this shelf." : null;
            float x = shelf.transform.InverseTransformPoint(point).x;
            if (why == null && !shelf.FreeSpot(held.HalfWidth, ref x)) why = size.x > shelf._x1 - shelf._x0 ? "It is too wide for this shelf." : "There is no room left on the shelf.";
            if (why != null) { Destroy(held.View); Dbg.Log("[Shelf] " + id + " not put on: " + why + " size " + size.ToString("0.00") + ", board " + (shelf._x1 - shelf._x0).ToString("0.00") + " x " + (shelf._z1 - shelf._z0).ToString("0.00")); ToastNotificationSystem.ShowInfo(name, why); return true; }
            held.X = x;
            shelf.Seat(held);
            shelf.Items.Add(held);
            hud.ConsumeFromSelectedSlot(1);
            if (slot.Count <= 1) { }   // the slot is empty now: its metres and liquid went with the item
            else { ToolbarSlotData rest = hud.Toolbar[hud.SelectedSlot]; rest.WireUsed = 0f; hud.Toolbar[hud.SelectedSlot] = rest; }   // the used one was on top
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        /// <summary>A right click on a thing on a shelf takes it back into the toolbar. True when the click was for one.</summary>
        public static bool TryTake(Camera cam, Vector2 pointer)
        {
            if (cam == null || AttachedObject.All.Count == 0 || AttachedObject.WrenchRemoval()) return false;
            if (!UnderCursor(cam, pointer, out Shelf shelf, out Held held, out _) || held == null) return false;
            var ped = PedController.Current;
            if (ped != null && Flat(ped.transform.position, shelf.transform.position) > Reach) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to reach that."); return true; }
            HudState hud = HudState.Active;
            if (hud == null) return true;
            hud.EnsureToolbarSlots();
            if (held.WireUsed > 0.01f || !string.IsNullOrEmpty(held.LiquidId))
            {
                // a part-used coil, a filled can: a slot of its own, so what is in it goes with it
                int free = -1;
                for (int i = 0; i < hud.Toolbar.Count; i++)
                    if (hud.Toolbar[i].Count <= 0 || string.IsNullOrEmpty(hud.Toolbar[i].IconId)) { free = i; break; }
                if (free < 0) { ToastNotificationSystem.ShowWarning("Toolbar full", "No free toolbar slot for that."); return true; }
                hud.Toolbar[free] = new ToolbarSlotData { IconId = held.ItemId, Count = 1, WireUsed = held.WireUsed, LiquidId = held.LiquidId };
            }
            else if (hud.AddItemToToolbar(held.ItemId, 1, HudBindings.GetMaxStack(held.ItemId)) < 1) { ToastNotificationSystem.ShowWarning("Toolbar full", "No room in the toolbar for that."); return true; }
            shelf.Items.Remove(held);
            if (held.View != null) Destroy(held.View);
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        private static float Flat(Vector3 a, Vector3 b) { return new Vector2(a.x - b.x, a.z - b.z).magnitude; }

        /// <summary>The free place nearest <paramref name="x"/> for a thing this wide (half its width): false when none is left.</summary>
        private bool FreeSpot(float half, ref float x)
        {
            float lo = _x0 + half, hi = _x1 - half;
            if (hi < lo - 0.001f) return false;
            var taken = new List<Vector2>();
            foreach (Held h in Items) taken.Add(new Vector2(h.X - h.HalfWidth - Gap - half, h.X + h.HalfWidth + Gap + half));
            taken.Sort((a, b) => a.x.CompareTo(b.x));
            float want = Mathf.Clamp(x, lo, hi), best = float.MaxValue, at = 0f, from = lo;
            bool any = false;
            for (int i = 0; i <= taken.Count; i++)
            {
                float to = i < taken.Count ? Mathf.Min(hi, taken[i].x) : hi;
                if (to >= from - 0.0005f)
                {
                    float c = Mathf.Clamp(want, from, Mathf.Max(from, to)), d = Mathf.Abs(c - want);
                    if (d < best) { best = d; at = c; any = true; }
                }
                if (i < taken.Count) from = Mathf.Max(from, taken[i].y);
            }
            if (any) x = at;
            return any;
        }

        // ------------------------------------------------------------------ the things as they stand

        /// <summary>Makes the model of a thing for the shelf (no physics of its own: one click box) and measures it. False when it has nothing to show.</summary>
        private bool MakeView(Held held, ItemRegistry.ItemInfo info, out Vector3 size)
        {
            size = Vector3.zero;
            GameObject view = Instantiate(info.Prefab, transform);
            view.name = "Shelved_" + held.ItemId;
            view.SetActive(true);
            view.transform.localPosition = Vector3.zero;
            view.transform.localRotation = Quaternion.identity;
            foreach (Collider c in view.GetComponentsInChildren<Collider>(true)) Destroy(c);
            foreach (MonoBehaviour m in view.GetComponentsInChildren<MonoBehaviour>(true)) if (!(m is GlbTemplate)) Destroy(m);
            Renderer[] rs = view.GetComponentsInChildren<Renderer>(true);
            if (rs.Length == 0) { Destroy(view); return false; }
            bool any = false;
            Bounds lb = default;
            foreach (Renderer r in rs)
            {
                Bounds wb = r.bounds;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = wb.center + new Vector3((i & 1) == 0 ? -wb.extents.x : wb.extents.x, (i & 2) == 0 ? -wb.extents.y : wb.extents.y, (i & 4) == 0 ? -wb.extents.z : wb.extents.z);
                    Vector3 local = view.transform.InverseTransformPoint(corner);
                    if (!any) { lb = new Bounds(local, Vector3.zero); any = true; } else lb.Encapsulate(local);
                }
            }
            // a long thing lies along the shelf
            if (lb.size.z > lb.size.x + 0.01f)
            {
                view.transform.localRotation = Quaternion.Euler(0f, 90f, 0f);
                lb = new Bounds(new Vector3(lb.center.z, lb.center.y, -lb.center.x), new Vector3(lb.size.z, lb.size.y, lb.size.x));
            }
            var box = view.AddComponent<BoxCollider>();   // on the view's own (unturned) axes
            box.isTrigger = true;
            Quaternion inv = Quaternion.Inverse(view.transform.localRotation);
            Vector3 bs = inv * lb.size;
            box.center = inv * lb.center;
            box.size = Vector3.Max(new Vector3(Mathf.Abs(bs.x), Mathf.Abs(bs.y), Mathf.Abs(bs.z)), new Vector3(0.03f, 0.03f, 0.03f));
            held.View = view;
            held.HalfWidth = lb.size.x * 0.5f;
            _viewBounds[view] = lb;
            size = lb.size;
            return true;
        }

        private readonly Dictionary<GameObject, Bounds> _viewBounds = new Dictionary<GameObject, Bounds>();

        /// <summary>Stands a thing on the board at its place: its foot on the top face, its back towards the wall.</summary>
        private void Seat(Held held)
        {
            if (held.View == null || !_viewBounds.TryGetValue(held.View, out Bounds lb)) return;
            float depth = _z1 - _z0;
            float z = lb.size.z <= depth ? _z0 + depth * 0.5f : _z0 + lb.size.z * 0.5f;   // a deep thing sits back against the wall and sticks out in front
            held.View.transform.localPosition = new Vector3(held.X - lb.center.x, _top - (lb.center.y - lb.size.y * 0.5f), z - lb.center.z);
        }

        // ------------------------------------------------------------------ the look-at panel, saving

        /// <summary>What stands on the shelf, as "3 x Wood Glue, Hammer", for the look-at panel.</summary>
        public string Describe()
        {
            if (Items.Count == 0) return "Empty";
            var counts = new Dictionary<string, int>();
            var order = new List<string>();
            foreach (Held h in Items) { if (!counts.ContainsKey(h.ItemId)) { counts[h.ItemId] = 0; order.Add(h.ItemId); } counts[h.ItemId]++; }
            var sb = new System.Text.StringBuilder();
            foreach (string id in order) sb.Append(sb.Length > 0 ? ", " : "").Append(counts[id] > 1 ? counts[id] + " x " : "").Append(HudBindings.GetItemName(id));
            return sb.ToString();
        }

        /// <summary>Metres of the board still free.</summary>
        public float FreeLength()
        {
            float used = 0f;
            foreach (Held h in Items) used += h.HalfWidth * 2f + Gap;
            return Mathf.Max(0f, _x1 - _x0 - used);
        }

        /// <summary>Puts back what a save says stood on the shelf (the models may still be loading: each appears when its own is ready).</summary>
        public void Restore(List<string> ids, List<float> xs, List<float> used, List<string> liquids)
        {
            if (ids == null) return;
            for (int i = 0; i < ids.Count; i++)
            {
                var held = new Held { ItemId = ids[i], X = xs != null && i < xs.Count ? xs[i] : 0f, WireUsed = used != null && i < used.Count ? used[i] : 0f,
                                      LiquidId = liquids != null && i < liquids.Count && !string.IsNullOrEmpty(liquids[i]) ? liquids[i] : null };
                Items.Add(held);
                StartCoroutine(Show(held));
            }
        }

        private IEnumerator Show(Held held)
        {
            if (!ItemRegistry.TryGet(held.ItemId, out ItemRegistry.ItemInfo info) || info.Prefab == null) yield break;   // (the item is gone from the game: it stays listed, unseen)
            GlbTemplate glb = info.Prefab.GetComponent<GlbTemplate>();
            if (glb != null)
            {
                glb.EnsureLoading();
                float until = Time.realtimeSinceStartup + 30f;
                while (!glb.Ready && !glb.Failed && Time.realtimeSinceStartup < until) yield return null;
                if (!glb.Ready) yield break;
            }
            if (!Items.Contains(held)) yield break;   // taken meanwhile
            if (MakeView(held, info, out _)) Seat(held);
        }
    }
}
