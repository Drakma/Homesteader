using Homesteader.Modding;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// An item lying on the ground (dragged off the toolbar). Shows the item's model; the model is a lazily
    /// loaded GLB, so it appears as soon as the load finishes.
    /// </summary>
    public sealed class WorldItem : MonoBehaviour
    {
        public static readonly System.Collections.Generic.List<WorldItem> All = new System.Collections.Generic.List<WorldItem>();

        public string ItemId { get; private set; }
        /// <summary>The heading the item lies at (degrees about Y).</summary>
        public float Yaw { get; private set; }
        private bool _fixedYaw;
        public bool FixedYaw => _fixedYaw;
        private GameObject prefab;
        private GameObject model;
        private static Transform root;

        private void OnEnable() => All.Add(this);
        private void OnDisable() => All.Remove(this);

        /// <summary>Puts the item on the ground at a point. False when the item has no model to show.</summary>
        public static bool TryDrop(string itemId, Vector3 point) { return TryDrop(itemId, point, null); }

        /// <summary>As above, lying at a given heading (a log along the line a tree fell) instead of a random one.</summary>
        public static bool TryDrop(string itemId, Vector3 point, float? yaw)
        {
            if (!ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info))
            {
                // No model: the icon becomes a thin 3D slab lying on the ground.
                GameObject slab = SpriteSlab.Create(itemId, 0.5f);
                if (slab == null) return false;
                if (root == null) root = new GameObject("WorldItems").transform;
                var holder = new GameObject("Item_" + itemId);
                holder.transform.SetParent(root, false);
                holder.transform.position = Homesteader.Generation.TerrainHeightDetector.PlaceOnGround(point);
                var drop = holder.AddComponent<WorldItem>();
                drop.ItemId = itemId;
                slab.transform.SetParent(holder.transform, false);
                // Face up, with a random heading, resting on the surface.
                slab.transform.localRotation = Quaternion.Euler(90f, Random.Range(0f, 360f), 0f);
                slab.transform.localPosition = Vector3.up * 0.02f;
                drop.model = slab;
                return true;
            }

            if (root == null) root = new GameObject("WorldItems").transform;
            if (!yaw.HasValue) point = Scatter(point, out yaw);
            var go = new GameObject("Item_" + itemId);
            go.transform.SetParent(root, false);
            go.transform.position = Homesteader.Generation.TerrainHeightDetector.PlaceOnGround(point);
            var item = go.AddComponent<WorldItem>();
            item.ItemId = itemId;
            item.prefab = info.Prefab;
            item.Yaw = yaw ?? Random.Range(0f, 360f);
            item._fixedYaw = yaw.HasValue;
            item.TryShow();
            return true;
        }

        /// <summary>
        /// Where and how a loose item lands when it is dropped near others: not on top of them (that piled many logs into a starburst round one
        /// point) but in a free spot within a metre or two, lying at a loosely similar heading to its neighbour, give or take, like things
        /// that were tossed down. Alone it lands where it was dropped at a random heading.
        /// </summary>
        private static Vector3 Scatter(Vector3 point, out float? yaw)
        {
            yaw = null;
            WorldItem nearest = null;
            float nearestD = 2.2f * 2.2f;
            foreach (WorldItem w in All)
            {
                if (w == null) continue;
                float d = (w.transform.position - point).sqrMagnitude;
                if (d < nearestD) { nearestD = d; nearest = w; }
            }
            if (nearest == null) return point;

            Vector3 best = point;
            float bestClear = -1f;
            for (int i = 0; i < 14; i++)
            {
                Vector2 o = Random.insideUnitCircle * Mathf.Lerp(0.5f, 2.0f, i / 13f);
                Vector3 cand = point + new Vector3(o.x, 0f, o.y);
                float clear = float.MaxValue;
                foreach (WorldItem w in All)
                {
                    if (w == null) continue;
                    clear = Mathf.Min(clear, (w.transform.position - cand).magnitude);
                }
                if (clear > bestClear) { bestClear = clear; best = cand; }
                if (clear >= 0.7f) break;
            }
            WorldItem beside = nearest;
            float bd = float.MaxValue;
            foreach (WorldItem w in All)
            {
                if (w == null) continue;
                float d = (w.transform.position - best).sqrMagnitude;
                if (d < bd) { bd = d; beside = w; }
            }
            yaw = beside.Yaw + Random.Range(-70f, 70f);
            return best;
        }

        /// <summary>The dropped item nearest the cursor ray (within 0.7 m of it), or null. Dropped items are walk-through, so no raycast sees them.</summary>
        public static WorldItem UnderCursor(Camera cam, Vector2 screenPos)
        {
            if (cam == null) return null;
            Ray ray = cam.ScreenPointToRay(screenPos);
            WorldItem best = null;
            float bestDist = 0.7f;
            foreach (WorldItem it in All)
            {
                if (it == null) continue;
                Vector3 p = it.transform.position + Vector3.up * 0.1f;
                float d = Vector3.Cross(ray.direction, p - ray.origin).magnitude;   // distance from the point to the ray
                if (d < bestDist) { bestDist = d; best = it; }
            }
            return best;
        }

        /// <summary>Puts one of it into the toolbar and removes it from the ground. False (with a toast) when it cannot.</summary>
        public bool PickUp(Transform player)
        {
            var hud = Homesteader.UI.HudState.Active;
            if (hud == null) return false;
            if (player != null && !PlantingValidator.InReach(player, transform.position, GameRules.Placement.ReachCells + 1))
            {
                Homesteader.UI.ToastNotificationSystem.ShowInfo("Too far", "Move closer to pick that up.");
                return false;
            }
            int added = hud.AddItemToToolbar(ItemId, 1, Homesteader.UI.HudBindings.GetMaxStack(ItemId));
            if (added <= 0)
            {
                Homesteader.UI.ToastNotificationSystem.ShowWarning("Toolbar full", "No room in the toolbar for that.");
                return false;
            }
            Homesteader.UI.HudBindings.Instance?.RefreshToolbar();
            Homesteader.UI.ToastNotificationSystem.ShowCounted("pickup:" + ItemId, "Picked up", "Picked up {0}x " + Homesteader.UI.HudBindings.GetItemName(ItemId).Replace("{", "{{").Replace("}", "}}") + ".", 1);
            Destroy(gameObject);
            return true;
        }

        private void Update()
        {
            if (model == null && prefab != null) TryShow();   // still waiting for the GLB to load
        }

        private void TryShow()
        {
            GlbTemplate glb = prefab.GetComponent<GlbTemplate>();
            if (glb != null)
            {
                glb.EnsureLoading();
                if (glb.Failed) { prefab = null; return; }
                if (!glb.Ready) return;
            }

            model = Instantiate(prefab, transform);
            model.SetActive(true);   // templates live inactive
            model.transform.localPosition = Vector3.zero;
            // Random facing so a pile of dropped items doesn't look like a stamped-out row.
            model.transform.localRotation = Quaternion.Euler(0f, Yaw, 0f);
            // A dropped item is walk-through: the player and clicks pass straight through it.
            foreach (Collider c in model.GetComponentsInChildren<Collider>(true)) c.enabled = false;
        }
    }
}
