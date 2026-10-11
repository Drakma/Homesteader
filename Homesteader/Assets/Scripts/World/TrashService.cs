using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// The weekly trash pickup (docs/TRASH.md). Every seventh day, at 07:00, the trash truck (vehicle_trash_truck) drives to the pickup zone (the flag's square, as the delivery van and the cargo
    /// truck do) and empties every wheeled trash bin (waste_trash_bin_wheeled: it holds four full garbage bags) standing in it. Bags that are not in a bin are left, and so is a bin that was not
    /// moved to the zone. The pickup costs <see cref="WeeklyFee"/> a week whether or not a bin was out; there is no round while no bin has been placed.
    /// </summary>
    public static class TrashService
    {
        public const string TruckItemId = "vehicle_trash_truck";
        public const string BinId = "waste_trash_bin_wheeled";
        public const string BagId = "waste_garbage_bag_full";
        public const float WeeklyFee = 50f;
        private const float RoundMinute = 7f * 60f;        // the truck sets off at 07:00 on pickup day

        /// <summary>The day of the year of the last round (0 = none yet): saved, so loading on pickup day does not send the truck twice.</summary>
        public static int LastDay { get; private set; }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        public static void Reset() { LastDay = 0; }

        public static void Restore(int lastDay) { LastDay = lastDay; }

        /// <summary>True on the day of the week the truck comes (every seventh day of the year).</summary>
        public static bool IsPickupDay(int dayOfYear) { return dayOfYear % TimeConstants.DaysPerWeek == 0; }

        private static bool AnyBin()
        {
            foreach (PlacedObject o in PlacedObject.All) if (o != null && o.ItemId == BinId) return true;
            return false;
        }

        /// <summary>Called by the delivery service about once a second: the round of this week when it is time (the truck's order), else null.</summary>
        public static DeliveryService.Order Tick(TimeSystem time)
        {
            if (time == null || !IsPickupDay(time.DayOfYear) || LastDay == time.DayOfYear || time.MinuteOfDay < RoundMinute) return null;
            LastDay = time.DayOfYear;
            if (!AnyBin()) return null;                                     // nobody has a bin: no truck, no fee
            return new DeliveryService.Order { dueDay = time.DayOfYear, trash = true };
        }

        /// <summary>The truck has stopped at the pickup zone: the fee is taken and the bins standing in the zone are emptied.</summary>
        public static void Collect(DeliveryService.Order order, Vector3 zone)
        {
            HudState hud = HudState.Active;
            if (hud != null && !hud.SpendMoney(WeeklyFee))
            {
                ToastNotificationSystem.ShowWarning("Trash pickup", "You could not pay the $" + WeeklyFee.ToString("0") + " weekly fee: the truck left without emptying anything.");
                return;
            }
            int emptied = 0, bags = 0, outside = 0;
            foreach (PlacedObject o in new List<PlacedObject>(PlacedObject.All))
            {
                if (o == null || o.ItemId != BinId) continue;
                if (!MarketPickup.InZone(zone, o.transform.position)) { outside++; continue; }
                if (o.Contents != null)
                {
                    foreach (ContainerStack s in o.Contents) if (s.ItemId == BagId) bags += s.Count;
                    o.Contents.RemoveAll(s => s.ItemId == BagId);
                }
                emptied++;
            }
            string fee = "$" + WeeklyFee.ToString("0") + " charged.";
            if (emptied > 0) ToastNotificationSystem.ShowSuccess("Trash pickup", emptied + (emptied == 1 ? " bin" : " bins") + " emptied (" + bags + (bags == 1 ? " bag" : " bags") + "). " + fee);
            else ToastNotificationSystem.ShowWarning("Trash pickup", "No bin was in the pickup zone. " + fee);
            if (outside > 0) ToastNotificationSystem.ShowWarning("Trash pickup", outside + (outside == 1 ? " bin was" : " bins were") + " not in the pickup zone: not emptied.");
        }
    }
}
