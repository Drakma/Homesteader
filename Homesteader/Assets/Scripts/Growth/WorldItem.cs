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
        private GameObject prefab;
        private GameObject model;
        private static Transform root;

        private void OnEnable() => All.Add(this);
        private void OnDisable() => All.Remove(this);

        /// <summary>Puts the item on the ground at a point. False when the item has no model to show.</summary>
        public static bool TryDrop(string itemId, Vector3 point)
        {
            if (!ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info)) return false;

            if (root == null) root = new GameObject("WorldItems").transform;
            var go = new GameObject("Item_" + itemId);
            go.transform.SetParent(root, false);
            go.transform.position = Homesteader.Generation.TerrainHeightDetector.PlaceOnGround(point);
            var item = go.AddComponent<WorldItem>();
            item.ItemId = itemId;
            item.prefab = info.Prefab;
            item.TryShow();
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
            model.transform.localRotation = Quaternion.Euler(0f, Random.Range(0f, 360f), 0f);
            // A dropped item is walk-through: the player and clicks pass straight through it.
            foreach (Collider c in model.GetComponentsInChildren<Collider>(true)) c.enabled = false;
        }
    }
}
