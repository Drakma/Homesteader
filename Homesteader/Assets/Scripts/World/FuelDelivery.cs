using System.Collections;
using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Growth;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// The fuel truck (vehicle_delivery_fuel_truck) and what it is ordered for in the Tank You phone store:
    ///
    ///  - Bulk fuel: propane, diesel and gasoline by the lot (the items fuel_bulk_*: a liquid container sold full, 100 L each, with no model). The truck fills the tanks standing in the
    ///    world: every placed liquid container that takes that liquid and is empty or already holds it.
    ///  - A tank pickup (fuel_service_tank_pickup): the big fuel tanks (fuel_tank_*) cannot be picked up by hand (<see cref="IsFixedTank"/>); the truck takes one away per pickup
    ///    ordered, the emptiest first; half the tank's price is credited, and the fuel still in it is bought back at half what it costs to buy.
    ///
    /// The truck comes the morning after the order, like the van (DeliveryService keeps the order and calls <see cref="Begin"/>). It drives down the road to the point nearest each tank,
    /// leaves the road and drives as close to the tank as it can (it stops short of a building), does its work there, backs out to the road and goes on to the next; then it turns
    /// round and leaves. Fuel that fits in no tank is refunded. With no road, or no truck model, the work is simply done.
    ///
    /// A tank's contents: the liquid in <see cref="PlacedObject.LiquidId"/> and the liters in its WireUsed number (<see cref="LiquidRules.Held"/>).
    /// </summary>
    public static class FuelDelivery
    {
        public const string TruckItemId = "vehicle_delivery_fuel_truck";
        public const string PickupItemId = "fuel_service_tank_pickup";
        private const float SecondsPerTank = 1.5f;
        public const float TankBuyBack = 0.5f;      // a tank taken away is credited at this share of its price
        public const float FuelBuyBack = 0.5f;      // and the fuel still in it at this share of what it costs to buy

        private static FuelTruck s_truck;
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

        /// <summary>The big fuel tanks: too heavy to pick up. The truck takes one away when a tank pickup is ordered.</summary>
        public static bool IsFixedTank(string itemId) { return !string.IsNullOrEmpty(itemId) && itemId.StartsWith("fuel_tank_"); }

        /// <summary>True for a bulk fuel lot, with the liquid it is and the liters in one.</summary>
        public static bool IsBulkFuel(string itemId, out string liquid, out float litersEach)
        {
            liquid = null;
            litersEach = 0f;
            if (string.IsNullOrEmpty(itemId) || !itemId.StartsWith("fuel_bulk_")) return false;
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            if (it == null || string.IsNullOrEmpty(it.liquid_filled_with)) return false;
            liquid = it.liquid_filled_with;
            litersEach = it.liquid_filled_l > 0f ? it.liquid_filled_l : it.liquid_capacity_l;
            return litersEach > 0f;
        }

        /// <summary>Something the fuel truck brings or does (not goods for the van).</summary>
        public static bool IsTruckOrder(string itemId) { return itemId == PickupItemId || IsBulkFuel(itemId, out _, out _); }

        // ------------------------------------------------------------------ the load and the jobs

        /// <summary>What the truck carries and has to do, and what came of it.</summary>
        public sealed class Load
        {
            public readonly Dictionary<string, float> Liters = new Dictionary<string, float>();       // liquid -> liters still on the truck
            public readonly Dictionary<string, float> Ordered = new Dictionary<string, float>();
            public readonly Dictionary<string, float> PricePerLiter = new Dictionary<string, float>();
            public readonly Dictionary<string, int> TanksFilled = new Dictionary<string, int>();
            public int Pickups, PickedUp;
            public float PickupCredit;
            public float FuelCredit, FuelLitersBought;   // the fuel that was in the tanks taken away, bought back at a discount
        }

        public sealed class Job
        {
            public PlacedObject Tank;
            public bool Pickup;
            public ConstructionSite Septic;   // the honey pot truck's job: a septic tank to pump out (SepticPumpOut.cs)
            public Transform Target => Tank != null ? Tank.transform : Septic != null ? Septic.transform : null;
        }

        private static float StorePrice(string itemId)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            return it != null && it.store_listings != null && it.store_listings.Count > 0 ? it.store_listings[0].price : 0f;
        }

        /// <summary>What a liter of this liquid costs to buy: from its bulk lot in the store (fuel_bulk_*), else the liquid's own listed price.</summary>
        private static float BuyPricePerLiter(string liquid)
        {
            string lot = "fuel_bulk_" + liquid.Replace("liquid_", "");
            if (IsBulkFuel(lot, out string of, out float each) && of == liquid && StorePrice(lot) > 0f) return StorePrice(lot) / each;
            return StorePrice(liquid);
        }

        private static Load LoadOf(DeliveryService.Order order)
        {
            var load = new Load();
            for (int i = 0; i < order.ids.Count; i++)
            {
                if (order.ids[i] == PickupItemId) { load.Pickups += order.counts[i]; continue; }
                if (!IsBulkFuel(order.ids[i], out string liquid, out float each)) continue;
                load.Liters.TryGetValue(liquid, out float have);
                load.Liters[liquid] = have + each * order.counts[i];
                load.PricePerLiter[liquid] = StorePrice(order.ids[i]) / each;
            }
            foreach (var kv in load.Liters) { load.Ordered[kv.Key] = kv.Value; load.TanksFilled[kv.Key] = 0; }
            return load;
        }

        /// <summary>The tanks to visit: the ones to take away (the emptiest of the big tanks), then every tank some of the load can go into.</summary>
        private static List<Job> JobsFor(Load load)
        {
            var jobs = new List<Job>();
            var taken = new HashSet<PlacedObject>();
            if (load.Pickups > 0)
            {
                var fixedTanks = new List<PlacedObject>();
                foreach (PlacedObject o in PlacedObject.All) if (o != null && IsFixedTank(o.ItemId)) fixedTanks.Add(o);
                fixedTanks.Sort((a, b) => LiquidRules.Held(a.ItemId, a.WireUsed).CompareTo(LiquidRules.Held(b.ItemId, b.WireUsed)));
                for (int i = 0; i < fixedTanks.Count && i < load.Pickups; i++) { jobs.Add(new Job { Tank = fixedTanks[i], Pickup = true }); taken.Add(fixedTanks[i]); }
            }
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || taken.Contains(o) || !LiquidRules.IsLiquidContainer(o.ItemId)) continue;
                foreach (var kv in load.Liters)
                    if (kv.Value > 0.01f && RoomFor(o, kv.Key) > 0.01f) { jobs.Add(new Job { Tank = o }); break; }
            }
            return jobs;
        }

        /// <summary>Liters of this liquid the tank can still take: none when it does not accept it or holds something else.</summary>
        private static float RoomFor(PlacedObject o, string liquid)
        {
            if (o == null || !LiquidRules.Accepts(o.ItemId, liquid)) return 0f;
            float held = LiquidRules.Held(o.ItemId, o.WireUsed);
            if (held > 0.01f && LiquidRules.LiquidIn(o.ItemId, o.LiquidId) != liquid) return 0f;
            return Mathf.Max(0f, LiquidRules.Capacity(o.ItemId) - held);
        }

        /// <summary>The truck is at the tank: fills it from the load, or takes it away.</summary>
        public static void DoJob(Job job, Load load)
        {
            PlacedObject o = job.Tank;
            if (o == null) return;   // gone since the truck set off
            if (job.Pickup)
            {
                float tankCredit = Mathf.Round(StorePrice(o.ItemId) * TankBuyBack);
                // the fuel in it is bought back too, at a discount on what a liter costs to buy
                float inTank = LiquidRules.Held(o.ItemId, o.WireUsed);
                string held = LiquidRules.LiquidIn(o.ItemId, o.LiquidId);
                float fuelCredit = inTank > 0.01f && !string.IsNullOrEmpty(held) ? Mathf.Round(inTank * BuyPricePerLiter(held) * FuelBuyBack * 100f) / 100f : 0f;
                if (fuelCredit > 0f) load.FuelLitersBought += inTank;
                o.Remove();
                load.PickedUp++;
                load.PickupCredit += tankCredit;
                load.FuelCredit += fuelCredit;
                if (tankCredit + fuelCredit > 0f && HudState.Active != null) HudState.Active.AddMoney(tankCredit + fuelCredit);
                return;
            }
            var liquids = new List<string>(load.Liters.Keys);
            foreach (string liquid in liquids)
            {
                float put = Mathf.Min(load.Liters[liquid], RoomFor(o, liquid));
                if (put <= 0.01f) continue;
                float held = LiquidRules.Held(o.ItemId, o.WireUsed);
                o.LiquidId = liquid;
                o.WireUsed = LiquidRules.StoredFor(o.ItemId, held + put);
                TankSticker.Show(o, liquid);
                load.Liters[liquid] -= put;
                load.TanksFilled[liquid]++;
                break;   // one liquid to a tank
            }
        }

        /// <summary>The truck is done: says what went where, and gives back the price of what fitted nowhere.</summary>
        public static void Finish(Load load)
        {
            foreach (var kv in load.Ordered)
            {
                string name = HudBindings.GetItemName(kv.Key);
                float left = load.Liters[kv.Key], delivered = kv.Value - left;
                int tanks = load.TanksFilled[kv.Key];
                string went = tanks > 0 ? UnitFormat.Volume(delivered) + " of " + name + " into " + tanks + (tanks == 1 ? " tank." : " tanks.") : "No tank had room for " + name + ".";
                if (left <= 0.01f) { ToastNotificationSystem.ShowSuccess("Fuel delivered", went); continue; }
                float refund = Mathf.Round(left * load.PricePerLiter[kv.Key] * 100f) / 100f;
                if (refund > 0f && HudState.Active != null) HudState.Active.AddMoney(refund);
                ToastNotificationSystem.ShowWarning("Fuel delivery", went + " " + UnitFormat.Volume(left) + " did not fit" + (refund > 0f ? " and was refunded ($" + refund.ToString("0.00") + ")." : "."));
            }
            if (load.Pickups > 0)
            {
                if (load.PickedUp > 0)
                    ToastNotificationSystem.ShowSuccess("Tank pickup", load.PickedUp + (load.PickedUp == 1 ? " tank was" : " tanks were") + " taken away" + (load.PickupCredit > 0f ? ": $" + load.PickupCredit.ToString("0.00") + " credited for " + (load.PickedUp == 1 ? "it" : "them") : "")
                        + (load.FuelCredit > 0f ? (load.PickupCredit > 0f ? ", and $" : ": $") + load.FuelCredit.ToString("0.00") + " for the " + UnitFormat.Volume(load.FuelLitersBought) + " of fuel in " + (load.PickedUp == 1 ? "it." : "them.") : "."));
                if (load.PickedUp < load.Pickups)
                {
                    float back = StorePrice(PickupItemId) * (load.Pickups - load.PickedUp);
                    if (back > 0f && HudState.Active != null) HudState.Active.AddMoney(back);
                    ToastNotificationSystem.ShowWarning("Tank pickup", "There was no tank to take" + (back > 0f ? ": $" + back.ToString("0.00") + " refunded." : "."));
                }
            }
        }

        // ------------------------------------------------------------------ setting off

        /// <summary>The order is due: sends the truck (or, with no road or no truck model, just does the work). <paramref name="done"/> is called when the order is finished.</summary>
        public static void Begin(DeliveryService.Order order, IReadOnlyList<Vector2> road, MonoBehaviour host, System.Action done)
        {
            Load load = LoadOf(order);
            List<Job> jobs = JobsFor(load);
            bool truckModel = ItemRegistry.TryGet(TruckItemId, out ItemRegistry.ItemInfo info) && info.Prefab != null;
            if (jobs.Count == 0 || road == null || road.Count < 8 || !truckModel)
            {
                s_working = true;
                host.StartCoroutine(WithoutTruck(jobs, load, done));
                return;
            }
            ToastNotificationSystem.ShowInfo("Fuel truck", "The fuel truck is on its way.");
            var go = new GameObject("FuelTruck");
            s_truck = go.AddComponent<FuelTruck>();
            s_truck.Begin(road, info.Prefab, jobs, load, () => { s_truck = null; done?.Invoke(); });
        }

        private static IEnumerator WithoutTruck(List<Job> jobs, Load load, System.Action done)
        {
            foreach (Job j in jobs)
            {
                yield return new WaitForSeconds(SecondsPerTank);
                DoJob(j, load);
            }
            Finish(load);
            s_working = false;
            done?.Invoke();
        }

        // ------------------------------------------------------------------ the truck

        /// <summary>The truck on its round: along the road, off it to each tank, back out, on to the next, then round and away.</summary>
        public sealed class FuelTruck : MonoBehaviour
        {
            private const float RoadSpeed = 8f, YardSpeed = 3f, BackSpeed = 2.2f, TurnSeconds = 3f;

            private readonly List<Vector3> _pts = new List<Vector3>();      // the whole round, point to point
            private readonly List<bool> _backing = new List<bool>();        // the stretch leaving point i is driven in reverse
            private readonly List<bool> _yard = new List<bool>();           // ... and is off the road
            private readonly Dictionary<int, Job> _stops = new Dictionary<int, Job>();   // a job waits at point i
            private int _turnAt = -1;                                        // the point where it turns round to leave
            private Load _load;
            private System.Action _finished;
            private System.Action<Job> _work;   // what it does at each stop (the fuel truck fills or takes a tank; the septic truck pumps one out)
            private System.Action _done;        // and when the round is over
            private GameObject _prefab;
            private Transform _model;
            private readonly List<Transform> _wheels = new List<Transform>();
            private int _i;                 // the point just passed
            private float _t;               // metres along the stretch to the next
            private float _pause;           // seconds still to wait at a stop
            private bool _turning;
            private float _heading, _turnFrom;
            private Vector3 _smooth;

            public void Begin(IReadOnlyList<Vector2> road, GameObject prefab, List<Job> jobs, Load load, System.Action finished)
            {
                _prefab = prefab; _load = load; _finished = finished;
                _work = j => DoJob(j, load);
                _done = () => Finish(load);
                SetUp(road, jobs);
            }

            /// <summary>Another truck's round (the septic pump truck): its own work at each stop and its own report at the end.</summary>
            public void BeginWith(IReadOnlyList<Vector2> road, GameObject prefab, List<Job> jobs, System.Action<Job> work, System.Action done, System.Action finished)
            {
                _prefab = prefab; _finished = finished; _work = work; _done = done;
                SetUp(road, jobs);
            }

            private void SetUp(IReadOnlyList<Vector2> road, List<Job> jobs)
            {
                Plan(road, jobs);
                transform.position = _smooth = _pts[0];
                _heading = HeadingOf(0);
                transform.rotation = Quaternion.Euler(0f, _heading, 0f);
                StartCoroutine(LoadModel());
            }

            private static Vector3 OnGround(Vector2 p) { return new Vector3(p.x, TerrainHeightDetector.GetSurfaceY(p.x, p.y), p.y); }

            private void Add(Vector2 p, bool backing, bool yard) { _pts.Add(OnGround(p)); _backing.Add(backing); _yard.Add(yard); }

            private static int NearestRoadIndex(IReadOnlyList<Vector2> road, Vector2 p)
            {
                int best = 2;
                float bestD = float.MaxValue;
                for (int i = 2; i < road.Count; i++)
                {
                    float d = (road[i] - p).sqrMagnitude;
                    if (d < bestD) { bestD = d; best = i; }
                }
                return best;
            }

            /// <summary>How far from a tank's middle the truck's middle stops: half the tank, half the truck and room to work.</summary>
            private static float Standoff(Job job)
            {
                float half = 1f;
                if (job.Septic != null) half = Mathf.Max(half, Mathf.Max(job.Septic.Footprint.x, job.Septic.Footprint.y) * 0.5f);   // a buried tank: its footprint
                else foreach (Renderer r in job.Tank.GetComponentsInChildren<Renderer>()) half = Mathf.Max(half, Mathf.Max(r.bounds.extents.x, r.bounds.extents.z));
                return half + 3.8f;
            }

            private void Plan(IReadOnlyList<Vector2> road, List<Job> jobs)
            {
                var order = new List<(int index, Job job)>();
                foreach (Job j in jobs)
                    if (j.Target != null) order.Add((NearestRoadIndex(road, new Vector2(j.Target.position.x, j.Target.position.z)), j));
                order.Sort((a, b) => a.index.CompareTo(b.index));
                int cur = 0;
                Add(road[0], false, false);
                foreach ((int index, Job job) in order)
                {
                    for (int k = cur + 1; k <= index; k++) Add(road[k], false, false);
                    if (index > cur) cur = index;
                    // off the road, straight for the tank, as close as it gets: it stops short of the tank and of any building in the way
                    Vector2 from = road[cur], tank = new Vector2(job.Target.position.x, job.Target.position.z);
                    float dist = Vector2.Distance(from, tank), reach = dist - Standoff(job);
                    Vector2 dir = dist > 0.01f ? (tank - from) / dist : Vector2.up;
                    var approach = new List<Vector2>();
                    for (float d = 1f; d <= reach; d += 1f)
                    {
                        Vector2 q = from + dir * d;
                        bool blocked = false;
                        foreach (ConstructionSite cs in ConstructionSite.All) if (cs != null && cs != job.Septic && cs.DistanceOutside(new Vector3(q.x, 0f, q.y)) < 2.2f) { blocked = true; break; }
                        if (blocked) break;
                        approach.Add(q);
                    }
                    if (approach.Count > 0) { _backing[_backing.Count - 1] = false; _yard[_yard.Count - 1] = true; }
                    for (int k = 0; k < approach.Count; k++) Add(approach[k], false, true);
                    if (_stops.ContainsKey(_pts.Count - 1)) Add(from, false, false);   // two tanks reached from the same spot: a stop each
                    _stops[_pts.Count - 1] = job;                                  // at the end of the approach (or still on the road, when it could not leave it)
                    if (approach.Count > 0)
                    {
                        _backing[_backing.Count - 1] = true;                       // and backs out the way it came
                        for (int k = approach.Count - 2; k >= 0; k--) Add(approach[k], true, true);
                        Add(from, false, false);
                    }
                }
                _turnAt = _pts.Count - 1;                                          // round, and out the way it came in
                for (int k = cur - 1; k >= 0; k--) Add(road[k], false, false);
            }

            private float HeadingOf(int i)
            {
                int a = Mathf.Clamp(i, 0, _pts.Count - 2);
                Vector3 d = _pts[a + 1] - _pts[a];
                d.y = 0f;
                if (d.sqrMagnitude < 0.0001f) return _heading;
                float h = Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
                return _backing[a] ? h + 180f : h;                                 // backing up: the nose still points at the tank
            }

            private IEnumerator LoadModel()
            {
                GlbTemplate glb = _prefab.GetComponent<GlbTemplate>();
                while (glb != null && !glb.Ready)
                {
                    glb.EnsureLoading();
                    if (glb.Failed) { EndRound(); yield break; }
                    yield return null;
                }
                GameObject m = Instantiate(_prefab, transform);
                m.SetActive(true);
                m.transform.localPosition = Vector3.zero;
                foreach (Collider c in m.GetComponentsInChildren<Collider>(true)) c.enabled = false;
                float yaw = 0f;
                foreach (Transform t in m.GetComponentsInChildren<Transform>(true))
                {
                    if (t.name.StartsWith("Wheel_") && !t.name.EndsWith("_hub")) _wheels.Add(t);
                    if (t.name != "FrontMarker") continue;
                    Vector3 d = transform.InverseTransformPoint(t.position);
                    d.y = 0f;
                    if (d.sqrMagnitude > 0.01f) yaw = -Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
                }
                m.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
                _model = m.transform;
            }

            /// <summary>The model never loaded: the work is still done.</summary>
            private void EndRound()
            {
                foreach (var kv in _stops) _work(kv.Value);
                _done();
                _finished?.Invoke();
                Destroy(gameObject);
            }

            private void Update()
            {
                float dt = Time.deltaTime;
                if (dt <= 0f || _model == null) return;
                float travelled = 0f;
                if (_pause > 0f)
                {
                    _pause -= dt;
                    if (_turning)
                    {
                        _heading = _turnFrom + 180f * Mathf.SmoothStep(0f, 1f, 1f - Mathf.Clamp01(_pause / TurnSeconds));
                        if (_pause <= 0f) _turning = false;
                    }
                    else if (_pause <= 0f && _stops.TryGetValue(_i, out Job job))
                    {
                        _work(job);
                        _stops.Remove(_i);
                        if (_i == _turnAt && _i < _pts.Count - 1) { _pause = TurnSeconds; _turning = true; _turnFrom = _heading; }   // the last stop was on the road: it turns round here
                    }
                }
                else if (_i >= _pts.Count - 1)
                {
                    _done();
                    _finished?.Invoke();
                    Destroy(gameObject);
                    return;
                }
                else
                {
                    bool backing = _backing[_i];
                    float len = Vector3.Distance(new Vector3(_pts[_i].x, 0f, _pts[_i].z), new Vector3(_pts[_i + 1].x, 0f, _pts[_i + 1].z));
                    travelled = (backing ? BackSpeed : _yard[_i] ? YardSpeed : RoadSpeed) * dt;
                    _t += travelled;
                    _heading = Mathf.LerpAngle(_heading, HeadingOf(_i), 5f * dt);
                    if (backing) travelled = -travelled;
                    while (_t >= len && _i < _pts.Count - 1)
                    {
                        _t -= len;
                        _i++;
                        if (_stops.ContainsKey(_i)) { _pause = SecondsPerTank; _t = 0f; break; }
                        if (_i == _turnAt && _i < _pts.Count - 1) { _pause = TurnSeconds; _turning = true; _turnFrom = _heading; _t = 0f; break; }
                        if (_i >= _pts.Count - 1) break;
                        len = Vector3.Distance(new Vector3(_pts[_i].x, 0f, _pts[_i].z), new Vector3(_pts[_i + 1].x, 0f, _pts[_i + 1].z));
                    }
                }

                Vector3 pos = _pts[_i];
                if (_i < _pts.Count - 1)
                {
                    float len = Mathf.Max(0.001f, Vector3.Distance(new Vector3(_pts[_i].x, 0f, _pts[_i].z), new Vector3(_pts[_i + 1].x, 0f, _pts[_i + 1].z)));
                    pos = Vector3.Lerp(_pts[_i], _pts[_i + 1], Mathf.Clamp01(_t / len));
                    pos.y = TerrainHeightDetector.GetSurfaceY(pos.x, pos.z);
                }
                _smooth = Vector3.Lerp(_smooth, pos, 14f * dt);
                Quaternion yawRot = Quaternion.Euler(0f, _heading, 0f);
                Vector3 fwd = yawRot * Vector3.forward;                            // pitch with the ground: under the nose against under the tail
                float rise = TerrainHeightDetector.GetSurfaceY(_smooth + fwd * 1.8f) - TerrainHeightDetector.GetSurfaceY(_smooth - fwd * 1.8f);
                transform.SetPositionAndRotation(_smooth, yawRot * Quaternion.Euler(-Mathf.Atan2(rise, 3.6f) * Mathf.Rad2Deg, 0f, 0f));
                if (travelled != 0f)
                {
                    float deg = travelled / 0.42f * Mathf.Rad2Deg;
                    foreach (Transform w in _wheels) if (w != null) w.Rotate(transform.right, deg, Space.World);
                }
            }
        }
    }
}
