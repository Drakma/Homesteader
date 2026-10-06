using System.Collections;
using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// The honey pot truck (vehicle_septic_pump_truck) and its service in the Tank You phone store, the Septic Pump-Out (waste_service_septic_pumpout, docs/SEPTIC.md).
    /// It comes the morning after the order, like the fuel truck (DeliveryService keeps the order and calls <see cref="Begin"/>), and pumps out one septic tank for
    /// each pump-out ordered, the tanks with the most sludge first: it drives off the road as close to each tank as it gets (the fuel truck's round,
    /// <see cref="FuelDelivery.FuelTruck"/>), takes out the sludge and the liquid, and leaves. A pump-out with no tank to do is refunded.
    /// </summary>
    public static class SepticPumpOut
    {
        public const string TruckItemId = "vehicle_septic_pump_truck";
        public const string ServiceItemId = "waste_service_septic_pumpout";
        private const float SecondsPerTank = 2.5f;

        private static FuelDelivery.FuelTruck s_truck;
        private static bool s_working;

        /// <summary>True while the truck is out (deliveries wait their turn).</summary>
        public static bool Busy { get { return s_truck != null || s_working; } }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { s_truck = null; s_working = false; }

        /// <summary>A new world: no truck on the road.</summary>
        public static void Reset()
        {
            if (s_truck != null) Object.Destroy(s_truck.gameObject);
            s_truck = null;
            s_working = false;
        }

        public static bool IsOrder(string itemId) { return itemId == ServiceItemId; }

        private sealed class Tally { public int Ordered, Done; public float Liters; }

        private static float Price()
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(ServiceItemId);
            return it != null && it.store_listings != null && it.store_listings.Count > 0 ? it.store_listings[0].price : 0f;
        }

        /// <summary>The order is due: sends the truck to the tanks (or, with no road or no truck model, just pumps them). <paramref name="done"/> when it is over.</summary>
        public static void Begin(DeliveryService.Order order, IReadOnlyList<Vector2> road, MonoBehaviour host, System.Action done)
        {
            var tally = new Tally();
            for (int i = 0; i < order.ids.Count; i++) if (IsOrder(order.ids[i])) tally.Ordered += order.counts[i];
            // the tanks that have something in them, the most sludge first
            var tanks = new List<ConstructionSite>();
            foreach (ConstructionSite cs in ConstructionSite.All)
            {
                if (cs == null || !cs.Finished) continue;
                WireNode n = cs.GetComponent<WireNode>();
                if (n != null && n.Role == WireRole.SepticTank && n.SewageL + n.SludgeL > 1f) tanks.Add(cs);
            }
            tanks.Sort((a, b) => Score(b).CompareTo(Score(a)));
            var jobs = new List<FuelDelivery.Job>();
            for (int i = 0; i < tanks.Count && i < tally.Ordered; i++) jobs.Add(new FuelDelivery.Job { Septic = tanks[i] });
            bool truckModel = ItemRegistry.TryGet(TruckItemId, out ItemRegistry.ItemInfo info) && info.Prefab != null;
            if (jobs.Count == 0 || road == null || road.Count < 8 || !truckModel)
            {
                s_working = true;
                host.StartCoroutine(WithoutTruck(jobs, tally, done));
                return;
            }
            ToastNotificationSystem.ShowInfo("Septic truck", "The honey pot truck is on its way.");
            var go = new GameObject("SepticTruck");
            s_truck = go.AddComponent<FuelDelivery.FuelTruck>();
            s_truck.BeginWith(road, info.Prefab, jobs, j => Work(j, tally), () => Report(tally), () => { s_truck = null; done?.Invoke(); });
        }

        private static float Score(ConstructionSite cs)
        {
            WireNode n = cs.GetComponent<WireNode>();
            return n == null ? 0f : Septic.SludgeFill(n) * 10000f + n.SewageL;
        }

        private static void Work(FuelDelivery.Job job, Tally tally)
        {
            if (job.Septic == null) return;   // gone since the truck set off
            WireNode n = job.Septic.GetComponent<WireNode>();
            if (n == null) return;
            tally.Liters += Septic.PumpOut(n);
            tally.Done++;
        }

        private static void Report(Tally tally)
        {
            if (tally.Done > 0)
                ToastNotificationSystem.ShowSuccess("Septic pumped out", tally.Done + (tally.Done == 1 ? " septic tank was" : " septic tanks were") + " pumped out: " + UnitFormat.Volume(tally.Liters) + " taken away.");
            int left = tally.Ordered - tally.Done;
            if (left <= 0) return;
            float back = Price() * left;
            if (back > 0f && HudState.Active != null) HudState.Active.AddMoney(back);
            ToastNotificationSystem.ShowWarning("Septic pump-out", (tally.Done == 0 ? "There was no septic tank to pump out" : "There were not that many tanks to pump out") + (back > 0f ? ": $" + back.ToString("0.00") + " refunded." : "."));
        }

        private static IEnumerator WithoutTruck(List<FuelDelivery.Job> jobs, Tally tally, System.Action done)
        {
            foreach (FuelDelivery.Job j in jobs)
            {
                yield return new WaitForSeconds(SecondsPerTank);
                Work(j, tally);
            }
            Report(tally);
            s_working = false;
            done?.Invoke();
        }
    }
}
