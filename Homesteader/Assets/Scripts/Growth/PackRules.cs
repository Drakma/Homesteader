using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Homesteader.Growth
{
    /// <summary>
    /// A pack is a placed bundle, stack or case that holds N of a single item (a bundle of 20 studs, a case of 10 elbows: the equivalencies, GrowthRegistry.PackContent).
    /// A right click on a placed pack takes ONE piece out of it into the toolbar; Shift + right click takes the whole pack (the normal pick up). The pack remembers how
    /// many are left: PlacedObject.WireUsed counts the pieces taken (saved with the world, like the metres used from a coil), a part-used pack picked up keeps it in its own
    /// toolbar slot and puts it down again with it, and the look-at panel shows "Left: 13 of 20". The last piece taken takes the empty pack away.
    /// </summary>
    public static class PackRules
    {
        public static bool IsPack(string itemId) { return GrowthRegistry.PackContent(itemId, out _, out _); }

        /// <summary>How many pieces are left in a placed pack (0 for something that is not a pack).</summary>
        public static int Left(PlacedObject p)
        {
            if (p == null || !GrowthRegistry.PackContent(p.ItemId, out _, out int count)) return 0;
            return Mathf.Clamp(count - Mathf.RoundToInt(p.WireUsed), 0, count);
        }

        /// <summary>What share of a full pack is left (1 for something that is not a pack, or a whole one): what it is worth.</summary>
        public static float LeftFraction(PlacedObject p)
        {
            if (p == null || !GrowthRegistry.PackContent(p.ItemId, out _, out int count) || count <= 0) return 1f;
            return Mathf.Clamp01(Left(p) / (float)count);
        }

        private static bool ShiftHeld()
        {
#if ENABLE_INPUT_SYSTEM
            return Keyboard.current != null && Keyboard.current.shiftKey.isPressed;
#else
            return false;
#endif
        }

        /// <summary>
        /// A right click on a placed pack: takes one piece (true when the click was dealt with). Shift + right click, or anything that is not a pack, returns false so the whole thing is picked up.
        /// </summary>
        public static bool TryTakeOne(PlacedObject target)
        {
            if (target == null || ShiftHeld()) return false;
            if (!GrowthRegistry.PackContent(target.ItemId, out string single, out int count) || count < 2) return false;
            PlacedObject top = target;
            foreach (List<PlacedObject> col in PlacedObject.ColumnsAt(target.transform.position))
                if (col.Contains(target)) { top = col[col.Count - 1]; break; }   // (the top of a stack is the one that comes off)
            if (!GrowthRegistry.PackContent(top.ItemId, out single, out count)) top = target;
            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, top.NearestPointTo(ped.transform.position), GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to take one.");
                return true;
            }
            HudState hud = HudState.Active;
            if (hud == null) return true;
            hud.EnsureToolbarSlots();
            string name = HudBindings.GetItemName(single);
            if (hud.AddItemToToolbar(single, 1, HudBindings.GetMaxStack(single)) <= 0)
            {
                ToastNotificationSystem.ShowWarning("Toolbar full", "No room in the toolbar for " + name + ".");
                return true;
            }
            top.WireUsed += 1f;
            if (Left(top) <= 0) top.Remove();   // the last one: the empty pack goes
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }
    }
}
