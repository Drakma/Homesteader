using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Keeps the player off a solar panel on a ground rack: its tilted surface is a ramp the character controller would walk up. A solid invisible box from the
    /// ground up over the rack and its panel (on the Ignore Raycast layer, so the mouse still reaches the rack and the panel) is a wall the player bumps into.
    /// </summary>
    public static class NoClimb
    {
        private const int IgnoreRaycastLayer = 2;
        private const float Height = 2.2f;

        public static bool IsGroundRack(string itemId) { return !string.IsNullOrEmpty(itemId) && itemId.StartsWith("electricity_solar_mount_") && itemId.EndsWith("_ground"); }

        public static void AttachIfGroundRack(PlacedObject placed)
        {
            if (placed == null || !IsGroundRack(placed.ItemId)) return;
            Transform t = placed.transform;
            Transform old = t.Find("NoClimb");
            if (old != null) { old.SetParent(null); Object.Destroy(old.gameObject); }   // rebuilt once the panel is on, so the box covers it
            // the rack's own size, in its own space, and the panel it takes (panel_width_m / panel_depth_m) over it
            bool any = false;
            Bounds local = new Bounds(Vector3.up * 0.5f, Vector3.one);
            foreach (Renderer r in placed.GetComponentsInChildren<Renderer>(true))
            {
                Bounds b = r.bounds;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 c = t.InverseTransformPoint(new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z));
                    if (!any) { local = new Bounds(c, Vector3.zero); any = true; } else local.Encapsulate(c);
                }
            }
            AssetCatalogItem it = HudBindings.GetCatalogItem(placed.ItemId);
            if (it != null && it.panel_width_m > 0f && it.panel_depth_m > 0f)
                local.Encapsulate(new Bounds(new Vector3(local.center.x, local.center.y, local.center.z), new Vector3(it.panel_width_m, 0.1f, it.panel_depth_m)));
            var go = new GameObject("NoClimb");
            go.layer = IgnoreRaycastLayer;
            go.transform.SetParent(t, false);
            var box = go.AddComponent<BoxCollider>();
            box.center = new Vector3(local.center.x, Height * 0.5f, local.center.z);
            box.size = new Vector3(Mathf.Max(0.3f, local.size.x), Height, Mathf.Max(0.3f, local.size.z));
        }
    }
}
