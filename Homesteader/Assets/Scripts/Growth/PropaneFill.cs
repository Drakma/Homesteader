using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Filling a portable propane tank at a fill post. The post (manifest wire_role: propane_filler) stands in the ground and is piped to a big propane tank with propane pipe
    /// (Wiring.cs, the "propane" kind). A right click on it with a portable tank in the active slot (a liquid container that takes liquid_propane) fills that tank.
    /// How full a carried tank is rides in the slot's WireUsed number (see <see cref="LiquidRules.Held"/>): it is already saved with the toolbar and with a tank set down in the world.
    /// docs/WIRING.md, "Propane lines".
    /// </summary>
    public static class PropaneFill
    {
        public const string Propane = "liquid_propane";
        private const float Reach = 4f;

        /// <summary>True when the held item is a portable tank that takes propane (and is not itself an end of a propane line).</summary>
        public static bool IsPortableTank(string itemId)
        {
            if (string.IsNullOrEmpty(itemId) || !LiquidRules.Accepts(itemId, Propane)) return false;
            AssetCatalogItem info = HudBindings.GetCatalogItem(itemId);
            return info != null && WireNode.ParseRole(info.wire_role) == WireRole.None;
        }

        /// <summary>A right click with a portable propane tank in hand. True when the click was on a fill post (so nothing else reacts to it).</summary>
        public static bool TryRightClick(Camera cam, Vector2 pointer, Transform player)
        {
            string held = ConstructionSite.HeldItem();
            if (!IsPortableTank(held)) return false;
            WireNode post = WireTool.NodeUnderCursor(cam, pointer);
            if (post == null || post.Role != WireRole.PropaneFiller) return false;
            if (player != null && Vector3.Distance(player.position, post.transform.position) > Reach)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the fill post.");
                return true;
            }
            if (!WireNetwork.PropaneSupplied(post, out bool piped))
            {
                ToastNotificationSystem.ShowInfo("No propane", piped ? "The tank this post is piped to is empty. Order propane in the Tank You app." : "The fill post is not piped to a propane tank.");
                return true;
            }
            HudState hud = HudState.Active;
            if (hud == null || hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return true;
            ToolbarSlotData slot = hud.Toolbar[hud.SelectedSlot];
            if (slot.Count != 1)
            {
                ToastNotificationSystem.ShowInfo("One at a time", "Hold a single tank to fill it.");
                return true;
            }
            float capacity = LiquidRules.Capacity(held);
            if (LiquidRules.Held(held, slot.WireUsed) >= capacity - 0.01f)
            {
                ToastNotificationSystem.ShowInfo("Full", "That tank is already full.");
                return true;
            }
            slot.WireUsed = LiquidRules.StoredFor(held, capacity);
            hud.Toolbar[hud.SelectedSlot] = slot;
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            // the tank looks the same full or empty, so this is said (nothing on screen shows it)
            ToastNotificationSystem.ShowInfo("Filled", HudBindings.GetItemName(held) + ": " + UnitFormat.Volume(capacity) + " of propane.");
            return true;
        }
    }
}
