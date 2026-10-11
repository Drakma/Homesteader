using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Selling on the Market (docs/MARKET.md). The Market app's Sell tab lists what lies in the pickup zone: the delivery zone (5 tiles from the house toward the road,
    /// where the van drops its goods), out to <see cref="ZoneRadius"/> metres. Placed items (on a pallet too) and loose items count; the player books a pickup
    /// for an item type, and the next morning at 07:00 the cargo truck (vehicle_market_cargo_truck, an open-bed stake truck) drives to the zone, loads those items
    /// (<see cref="Collect"/>) and the player is paid <see cref="Share"/> of each one's base_value. What is no longer in the zone when it comes is not paid for.
    /// </summary>
    public static class MarketPickup
    {
        public const string TruckItemId = "vehicle_market_cargo_truck";
        public const float Share = 0.75f;         // of an item's base_value: never worth more than buying it back
        public const float ZoneRadius = 8f;       // metres from the delivery zone

        /// <summary>What one of this item sells for.</summary>
        public static float PriceOf(string itemId)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            return it != null ? Mathf.Round(it.base_value * Share * 100f) / 100f : 0f;
        }

        /// <summary>Goods the market takes: anything with a value that is not a structure, a blueprint, a vehicle, a pallet or something fixed in place.</summary>
        public static bool Sellable(string itemId)
        {
            if (string.IsNullOrEmpty(itemId)) return false;
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            if (it == null || it.base_value <= 0f || it.category == "vehicles") return false;
            if (Blueprints.IsBlueprint(itemId) || ConstructionSite.IsStructure(itemId) || PalletDeck.IsPallet(itemId)) return false;
            if (WaterTap.IsFixed(itemId) || FuelDelivery.IsFixedTank(itemId)) return false;
            if (itemId == TrashService.BagId) return false;   // trash is for the weekly truck, not the Market
            return true;
        }

        public static bool InZone(Vector3 zone, Vector3 p)
        {
            if (PickupFlag.TryZone(out Rect square, out _)) return square.Contains(new Vector2(p.x, p.z));   // the flag's square, not a radius
            return new Vector2(p.x - zone.x, p.z - zone.z).sqrMagnitude <= ZoneRadius * ZoneRadius;
        }

        /// <summary>A container still holding something is not sold (its contents would be lost): empty it first.</summary>
        private static bool Empty(PlacedObject o)
        {
            if (o.Contents != null && o.Contents.Count > 0) return false;
            return !LiquidRules.IsLiquidContainer(o.ItemId) || LiquidRules.Held(o.ItemId, o.WireUsed) <= 0.01f;
        }

        private sealed class Lot { public PlacedObject Placed; public WorldItem Loose; public float Dist; }

        private static List<Lot> LotsOf(string itemId, Vector3 zone)
        {
            var lots = new List<Lot>();
            foreach (PlacedObject o in PlacedObject.All)
                if (o != null && o.ItemId == itemId && InZone(zone, o.transform.position) && Empty(o))
                    lots.Add(new Lot { Placed = o, Dist = Vector3.Distance(o.transform.position, zone) });
            foreach (WorldItem w in WorldItem.All)
                if (w != null && w.ItemId == itemId && InZone(zone, w.transform.position))
                    lots.Add(new Lot { Loose = w, Dist = Vector3.Distance(w.transform.position, zone) });
            lots.Sort((a, b) => a.Dist.CompareTo(b.Dist));
            return lots;
        }

        /// <summary>The sellable item types in the zone now, each with how many are there and not already booked for the truck.</summary>
        public static List<KeyValuePair<string, int>> InZoneNow()
        {
            Vector3 zone = DeliveryService.ZoneNow();
            var counts = new Dictionary<string, int>();
            foreach (PlacedObject o in PlacedObject.All)
                if (o != null && InZone(zone, o.transform.position) && Sellable(o.ItemId) && Empty(o)) counts[o.ItemId] = (counts.TryGetValue(o.ItemId, out int n) ? n : 0) + 1;
            foreach (WorldItem w in WorldItem.All)
                if (w != null && InZone(zone, w.transform.position) && Sellable(w.ItemId)) counts[w.ItemId] = (counts.TryGetValue(w.ItemId, out int n) ? n : 0) + 1;
            var list = new List<KeyValuePair<string, int>>();
            foreach (var kv in counts)
            {
                int free = kv.Value - DeliveryService.PendingMarket(kv.Key);
                if (free > 0) list.Add(new KeyValuePair<string, int>(kv.Key, free));
            }
            list.Sort((a, b) => string.CompareOrdinal(HudBindings.GetItemName(a.Key), HudBindings.GetItemName(b.Key)));
            return list;
        }

        /// <summary>The truck has stopped at the zone: loads what was booked (as much of it as is still there), and pays for it.</summary>
        public static void Collect(DeliveryService.Order order, Vector3 zone)
        {
            int loaded = 0, short_ = 0;
            float paid = 0f;
            for (int i = 0; i < order.ids.Count; i++)
            {
                string id = order.ids[i];
                List<Lot> lots = LotsOf(id, zone);
                int take = Mathf.Min(order.counts[i], lots.Count);
                for (int k = 0; k < take; k++)
                {
                    if (lots[k].Placed != null) lots[k].Placed.Remove();
                    else if (lots[k].Loose != null) Object.Destroy(lots[k].Loose.gameObject);
                    paid += PriceOf(id) * (lots[k].Placed != null ? PackRules.LeftFraction(lots[k].Placed) : 1f);   // a part-used pack is worth what is left in it
                    loaded++;
                }
                short_ += order.counts[i] - take;
            }
            if (paid > 0f && HudState.Active != null) HudState.Active.AddMoney(paid);
            if (loaded > 0) ToastNotificationSystem.ShowSuccess("Market pickup", loaded + (loaded == 1 ? " item" : " items") + " sold: $" + paid.ToString("0.00") + " paid.");
            if (short_ > 0) ToastNotificationSystem.ShowWarning("Market pickup", short_ + (short_ == 1 ? " item was" : " items were") + " not in the pickup zone when the truck came.");
        }
    }
}
