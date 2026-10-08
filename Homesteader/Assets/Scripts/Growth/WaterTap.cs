using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Water out of a building (docs/WELLS.md, "Into the building"): a building has water while a water inlet mounted on it is piped to tanks that hold some. A
    /// right click on one of its spigots or faucets with a liquid container that takes water in hand (a bucket, a jug, a watering can) fills that container from
    /// those tanks. Every tap gives whatever water the building is supplied with, raw or filtered. A spigot post (water_spigot_post) stands in the yard and is
    /// piped to a tank, a filter or a well itself: it gives the water of the tanks its pipe reaches.
    /// </summary>
    public static class WaterTap
    {
        public const string Water = "liquid_water";
        public const string RawWater = "liquid_water_raw";   // untreated well water: not safe to drink
        private const float Reach = 4f;
        public const string SpigotPost = "water_spigot_post";

        public const string Macerator = "waste_pump_macerator";

        /// <summary>Fixed in place for good: a spigot post (set in the ground), a macerator pump (plumbed in) and a standby generator (on its pad) are not picked up
        /// or moved by tidying (a sawmill is too: it is 6 m long and stands where it is).</summary>
        public static bool IsFixed(string itemId) { return itemId == SpigotPost || itemId == Macerator || IsStandbyGenerator(itemId) || Sawmill.IsSawmill(itemId) || Homesteader.World.PickupFlag.IsFlag(itemId); }

        /// <summary>A solar panel or its mount is bolted down: only a wrench with Shift + right click takes it up (AttachedObject.WrenchRemoval).</summary>
        public static bool IsBoltedSolar(string itemId) { return !string.IsNullOrEmpty(itemId) && (itemId.StartsWith("electricity_solar_panel_") || itemId.StartsWith("electricity_solar_mount_")); }

        public static bool IsStandbyGenerator(string itemId) { return !string.IsNullOrEmpty(itemId) && itemId.StartsWith("electricity_generator_standby_"); }

        /// <summary>A right click with a water container in hand. True when the click was on a spigot or faucet (so nothing else reacts to it).</summary>
        public static bool TryRightClick(Camera cam, Vector2 pointer, Transform player)
        {
            string held = ConstructionSite.HeldItem();
            if (string.IsNullOrEmpty(held) || !LiquidRules.Accepts(held, Water)) return false;
            WireNode tap = WireTool.NodeUnderCursor(cam, pointer);
            if (tap == null || tap.Role != WireRole.WaterSpigot) return false;
            AttachedObject mount = tap.GetComponent<AttachedObject>();
            bool post = mount == null;                           // a spigot post out in the yard: its water comes down its own pipe, not from a building
            if (!post && mount.Site == null) return false;
            if (player != null && Vector3.Distance(player.position, tap.transform.position) > Reach)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the tap.");
                return true;
            }
            HudState hud = HudState.Active;
            if (hud == null || hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return true;
            ToolbarSlotData slot = hud.Toolbar[hud.SelectedSlot];
            if (slot.Count != 1) { ToastNotificationSystem.ShowInfo("One at a time", "Hold a single container to fill it."); return true; }
            float capacity = LiquidRules.Capacity(held);
            float have = LiquidRules.Held(held, slot.WireUsed);
            float room = capacity - have;
            if (room <= 0.01f) { ToastNotificationSystem.ShowInfo("Full", "That is already full."); return true; }
            string why;
            float raw;
            // a tap gives at most its flow for one fill: a narrow pipe, a small filter or a small faucet makes it slow, and a big container takes several
            string slowBy;
            float flow = post ? WireNetwork.SupplyFlowLph(tap, out slowBy) : WireNetwork.TapFlowLph(tap, mount.Site, out slowBy);
            float fill = Mathf.Min(room, flow * WireNetwork.TapFillHours);
            float got = post ? WireNetwork.DrawWaterAt(tap, fill, out why, out raw) : WireNetwork.DrawWater(mount.Site, fill, false, out why, out raw);   // every tap gives whatever water it is supplied with, raw or clean (raw water will make the player sick)
            if (got <= 0.01f) { ToastNotificationSystem.ShowInfo("No water", why); return true; }
            if (fill < room - 0.01f && got >= fill - 0.01f)
                ToastNotificationSystem.ShowInfo("Slow tap", "Only " + UnitFormat.Volume(flow) + " an hour reaches it" + (string.IsNullOrEmpty(slowBy) ? "" : ": " + slowBy + " limits it") + ". Fill again for more.");
            // any raw water in it makes the whole container raw
            bool wasRaw = have > 0.01f && slot.LiquidId == RawWater;
            string liquid = raw > 0.01f || wasRaw ? RawWater : Water;
            if (!LiquidRules.Accepts(held, liquid)) liquid = Water;   // (a container that takes no raw water keeps it as water)
            slot.LiquidId = liquid;
            slot.WireUsed = LiquidRules.StoredFor(held, have + got);
            hud.Toolbar[hud.SelectedSlot] = slot;
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }
    }
}
