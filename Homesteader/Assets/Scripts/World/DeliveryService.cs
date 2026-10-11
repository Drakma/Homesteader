using System.Collections;
using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Growth;
using Homesteader.Modding;
using Homesteader.Save;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Bulk fuel (the fuel_bulk_* lots) and tank pickups are an order of their own: the fuel truck's, which drives to each tank (FuelDelivery.cs).
    /// Phone orders arrive the NEXT DAY. An order made at checkout waits until 07:00 the day after; then a delivery box van
    /// (vehicle_delivery_boxvan) enters from the map edge, drives down the starter road to the grass area, unloads the goods
    /// beside the road end in cardboard boxes, turns around and drives back out. Pending orders are saved (GameSave.deliveries).
    ///
    /// The goods go into the kit's delivery boxes (box_large_brown and the like) by weight, with their contents; a heavy item
    /// that fits no box is set down by itself. If the world has no road, the goods appear at once without the van.
    /// </summary>
    public sealed class DeliveryService : MonoBehaviour
    {
        public const string VanItemId = "vehicle_delivery_boxvan";
        private const float ArriveMinute = 7f * 60f;     // the van sets off at 07:00 the next day
        private const float VanSpeed = 9f;                // metres per second on the road
        private const string BoxId = "box_large_brown";
        private const string PalletId = "building_pallet_wood";

        [System.Serializable]
        public sealed class Order
        {
            public int dueDay;                       // day of year it is due (the day after the order)
            public List<string> ids = new List<string>();
            public List<int> counts = new List<int>();
            public bool fuel;                        // bulk fuel (FuelDelivery.cs): the fuel truck brings it and fills the tanks, nothing is unloaded
            public bool septic;                      // septic pump-outs (SepticPumpOut.cs): the honey pot truck comes and pumps the tanks out
            public bool market;                      // goods sold in the Market app (MarketPickup.cs): the cargo truck collects them from the delivery zone
            public bool trash;                       // the weekly trash round (TrashService.cs): the trash truck empties the bins in the pickup zone
        }

        private static readonly List<Order> Pending = new List<Order>();
        private static DeliveryVan _van;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { Pending.Clear(); _van = null; }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<DeliveryService>() != null) return;
            var go = new GameObject("DeliveryService");
            DontDestroyOnLoad(go);
            go.AddComponent<DeliveryService>();
        }

        // ------------------------------------------------------------------ orders

        /// <summary>An order from the phone store: it arrives tomorrow morning.</summary>
        public static void Schedule(IDictionary<string, int> items)
        {
            TimeSystem time = TimeSystem.Instance;
            if (time == null) return;
            int due = time.DayOfYear % TimeConstants.DaysPerYear + 1;
            var o = new Order { dueDay = due };
            var fuel = new Order { dueDay = due, fuel = true };   // bulk fuel and tank pickups are an order of their own: the fuel truck's
            var septic = new Order { dueDay = due, septic = true };   // and septic pump-outs the honey pot truck's
            foreach (var kv in items)
            {
                if (kv.Value <= 0) continue;
                Order to = SepticPumpOut.IsOrder(kv.Key) ? septic : FuelDelivery.IsTruckOrder(kv.Key) ? fuel : o;
                to.ids.Add(kv.Key);
                to.counts.Add(kv.Value);
            }
            if (o.ids.Count > 0) Pending.Add(o);
            if (fuel.ids.Count > 0) Pending.Add(fuel);
            if (septic.ids.Count > 0) Pending.Add(septic);
        }

        /// <summary>The Market's sell orders: the goods the cargo truck collects tomorrow morning from the delivery zone, paid for when it has loaded them.</summary>
        public static void ScheduleMarket(IDictionary<string, int> items)
        {
            TimeSystem time = TimeSystem.Instance;
            if (time == null) return;
            var o = new Order { dueDay = time.DayOfYear % TimeConstants.DaysPerYear + 1, market = true };
            foreach (var kv in items) if (kv.Value > 0) { o.ids.Add(kv.Key); o.counts.Add(kv.Value); }
            if (o.ids.Count > 0) Pending.Add(o);
        }

        /// <summary>How many of an item are already booked for the cargo truck (so the Sell tab does not offer them twice).</summary>
        public static int PendingMarket(string itemId)
        {
            int n = 0;
            foreach (Order o in Pending)
                if (o.market) for (int i = 0; i < o.ids.Count; i++) if (o.ids[i] == itemId) n += o.counts[i];
            return n;
        }

        public static List<Order> SavedOrders() { return new List<Order>(Pending); }

        /// <summary>A new world: no orders waiting and no van on the road.</summary>
        public static void Reset()
        {
            Pending.Clear();
            if (_van != null) Destroy(_van.gameObject);
            _van = null;
            FuelDelivery.Reset();
            SepticPumpOut.Reset();
            TrashService.Reset();
        }

        public static void RestoreOrders(List<Order> orders)
        {
            Pending.Clear();
            if (orders != null) Pending.AddRange(orders);
        }

        private static bool Due(Order o, TimeSystem t)
        {
            int ahead = (t.DayOfYear - o.dueDay + TimeConstants.DaysPerYear) % TimeConstants.DaysPerYear;   // 0 = the due day itself
            if (ahead == 0) return t.MinuteOfDay >= ArriveMinute;
            return ahead < TimeConstants.DaysPerYear / 2;   // a day or more past due (a save loaded late)
        }

        private float _next;

        private void Update()
        {
            if (Time.unscaledTime < _next) return;
            _next = Time.unscaledTime + 1f;
            if (_van != null || FuelDelivery.Busy || SepticPumpOut.Busy) return;
            if (WelcomeMenuController.IsLoading || !GameSaveManager.Restored) return;
            TimeSystem time = TimeSystem.Instance;
            if (time == null) return;
            Order weekly = TrashService.Tick(time);   // once a week: the trash truck's round
            if (weekly != null) Pending.Add(weekly);
            if (Pending.Count == 0) return;
            foreach (Order o in Pending)
                if (Due(o, time)) { Dispatch(o); return; }
        }

        private void Dispatch(Order order)
        {
            HomesteaderTerrainGenerator gen = FindAnyObjectByType<HomesteaderTerrainGenerator>();
            IReadOnlyList<Vector2> road = gen != null ? gen.RoadPoints : null;
            if (order.septic)
            {
                SepticPumpOut.Begin(order, road, this, () => { Pending.Remove(order); });   // the honey pot truck's round (SepticPumpOut.cs)
                return;
            }
            if (order.fuel)
            {
                // the fuel truck's round: it drives to each tank (FuelDelivery.cs); the order stays pending until it is done
                FuelDelivery.Begin(order, road, this, () => { Pending.Remove(order); });
                return;
            }
            if (order.market)
            {
                // every pickup booked for the same day goes on ONE trip (each booking is its own order: they used to come one truck after another)
                TimeSystem now = TimeSystem.Instance;
                foreach (Order other in new List<Order>(Pending))
                {
                    if (other == order || !other.market || (now != null && !Due(other, now))) continue;
                    order.ids.AddRange(other.ids);
                    order.counts.AddRange(other.counts);
                    Pending.Remove(other);
                }
            }
            ToastNotificationSystem.ShowInfo(order.trash ? "Trash pickup" : order.market ? "Market pickup" : "Delivery", order.trash ? "The trash truck is on its way." : order.market ? "The cargo truck is on its way." : "A Delivery is on the way");

            // Where the goods go (and are collected from): see ResolveZone.
            ResolveZone(gen, road, out Vector3 zone, out int stopIndex);
            System.Action<Order, Vector3> work = order.trash ? (System.Action<Order, Vector3>)TrashService.Collect : order.market ? MarketPickup.Collect : Deliver;   // the cargo truck loads up instead of unloading; the trash truck empties the bins
            string truckId = order.trash ? TrashService.TruckItemId : order.market ? MarketPickup.TruckItemId : VanItemId;

            if (road == null || road.Count < 8 || !ItemRegistry.TryGet(truckId, out ItemRegistry.ItemInfo vanInfo) || vanInfo.Prefab == null)
            {
                // No road or no van model: the goods just turn up at the delivery zone (or are just collected from it).
                Pending.Remove(order);
                work(order, zone);
                return;
            }
            var go = new GameObject(order.trash ? "TrashTruck" : order.market ? "CargoTruck" : "DeliveryVan");
            _van = go.AddComponent<DeliveryVan>();
            _van.Begin(order, road, vanInfo.Prefab, zone, stopIndex, o => { Pending.Remove(o); }, () => { _van = null; }, work);
        }

        /// <summary>
        /// Where the goods go: once a house has been placed (even only its dirt area) the delivery zone is 5 tiles from the house nearest the road; the van drives
        /// to the road point closest to that zone. Before any house: the end of the road. The cargo truck collects from the same spot.
        /// </summary>
        public static void ResolveZone(HomesteaderTerrainGenerator gen, IReadOnlyList<Vector2> road, out Vector3 zone, out int stopIndex)
        {
            if (PickupFlag.TryZone(out Rect flagZone, out int flagStop))
            {
                zone = PickupFlag.CentreOf(flagZone);   // a planted pickup flag: the square it marks
                stopIndex = flagStop;
            }
            else if (road == null || road.Count < 8)
            {
                zone = DropPointNear(StarterCentre(gen));
                stopIndex = 0;
            }
            else if (!TryHouseZone(road, out zone, out stopIndex))
            {
                zone = DropPointBesideRoadEnd(road);
                stopIndex = road.Count - 1;
            }
        }

        /// <summary>The delivery zone now (for the Market's sell tab).</summary>
        public static Vector3 ZoneNow()
        {
            HomesteaderTerrainGenerator gen = FindAnyObjectByType<HomesteaderTerrainGenerator>();
            ResolveZone(gen, gen != null ? gen.RoadPoints : null, out Vector3 zone, out _);
            return zone;
        }

        /// <summary>The distance, in tiles (1 m grid squares), between a house and its delivery zone.</summary>
        public const float HouseZoneTiles = 5f;

        public static bool IsHouse(string structureId)
        {
            if (string.IsNullOrEmpty(structureId)) return false;
            // Any cabin or house, whatever it is called (small_cabin, large_log_cabin, farmhouse, starter_house, ...); a greenhouse is not a home.
            return (structureId.Contains("cabin") || structureId.Contains("house")) && !structureId.Contains("greenhouse");
        }

        /// <summary>
        /// The delivery zone around the house (a construction site of a house structure, at any stage) that is nearest the road: a
        /// point <see cref="HouseZoneTiles"/> tiles out from its foundation toward the road, and the road point the van drives
        /// to for it. False when no house has been placed.
        /// </summary>
        public static bool TryHouseZone(IReadOnlyList<Vector2> road, out Vector3 zone, out int stopIndex)
        {
            zone = default;
            stopIndex = 0;
            ConstructionSite best = null;
            float bestDist = float.MaxValue;
            int bestIdx = 0;
            foreach (ConstructionSite site in ConstructionSite.All)
            {
                if (site == null || !IsHouse(site.StructureId)) continue;
                Vector2 hp = new Vector2(site.transform.position.x, site.transform.position.z);
                for (int i = 0; i < road.Count; i++)
                {
                    float d = (road[i] - hp).sqrMagnitude;
                    if (d < bestDist) { bestDist = d; best = site; bestIdx = i; }
                }
                if (best != null) break;   // the FIRST house placed keeps the zone: a second house never moves it (it used to jump to whichever was nearer the road)
            }
            if (best == null) return false;

            Vector2 house = new Vector2(best.transform.position.x, best.transform.position.z);
            Vector2 toRoad = road[bestIdx] - house;
            float toRoadLen = toRoad.magnitude;
            Vector2 dir = toRoadLen > 0.01f ? toRoad / toRoadLen : Vector2.up;
            // walk out from the house centre until the point is 5 tiles beyond the foundation's edge (or the road is reached first)
            float t = 0f;
            while (t < toRoadLen)
            {
                Vector2 q = house + dir * t;
                if (best.DistanceOutside(new Vector3(q.x, 0f, q.y)) >= HouseZoneTiles) break;
                t += 0.5f;
            }
            Vector2 z2 = house + dir * Mathf.Min(t, toRoadLen);
            zone = PlantingValidator.SnapToGrid(new Vector3(z2.x, 0f, z2.y));
            zone.y = TerrainHeightDetector.GetSurfaceY(zone.x, zone.z);
            // the road point closest to the zone is where the van stops
            float bestStop = float.MaxValue;
            for (int i = 0; i < road.Count; i++)
            {
                float d = (road[i] - z2).sqrMagnitude;
                if (d < bestStop) { bestStop = d; stopIndex = i; }
            }
            stopIndex = Mathf.Max(2, stopIndex);
            return true;
        }

        private static Vector3 StarterCentre(HomesteaderTerrainGenerator gen)
        {
            Vector2 c = Homesteader.Land.LandOwnershipSystem.TileCenter(Homesteader.Land.LandOwnershipSystem.StarterX, Homesteader.Land.LandOwnershipSystem.StarterZ);
            return new Vector3(c.x, TerrainHeightDetector.GetSurfaceY(c.x, c.y), c.y);
        }

        private static Vector3 DropPointNear(Vector3 p) { return PlantingValidator.SnapToGrid(p); }

        // ------------------------------------------------------------------ the goods

        private static DeliveryService _instance;

        private void Awake() { _instance = this; }

        private sealed class Unit
        {
            public string Id;
            public ItemRegistry.ItemInfo Info;
            public List<ContainerStack> Contents;
        }

        /// <summary>
        /// Sets the order down at <paramref name="centre"/>, neatly: an item with a placeable model is placed as itself, every other
        /// item (no model, or not placeable) goes into boxes by weight, and only what is too heavy for any box lies on the ground.
        /// Like things are stacked (a box or crate on another, up to its stacking limit) and the stacks stand in tidy rows on the grid,
        /// all facing the same way. The models load lazily, so it waits for them before placing anything (a box placed before its
        /// model had loaded was invisible).
        /// </summary>
        /// <summary>The van or the truck has arrived: goods are unloaded at the delivery zone, bulk fuel is pumped into the tanks.</summary>
        public static void Deliver(Order order, Vector3 centre) { Unload(order, centre, Vector3.forward); }

        public static void Unload(Order order, Vector3 centre, Vector3 roadDir)
        {
            if (_instance != null) _instance.StartCoroutine(UnloadRoutine(order, centre));
        }

        private static IEnumerator UnloadRoutine(Order order, Vector3 centre)
        {
            ItemRegistry.TryGet(BoxId, out ItemRegistry.ItemInfo boxInfo);
            bool boxes = boxInfo != null && boxInfo.Prefab != null && ContainerRules.Capacity(BoxId) > 0f;
            var units = new List<Unit>();
            var loose = new List<string>();
            List<ContainerStack> current = null;

            void CloseBox()
            {
                if (current != null && current.Count > 0) units.Add(new Unit { Id = BoxId, Info = boxInfo, Contents = current });
                current = null;
            }

            for (int i = 0; i < order.ids.Count; i++)
            {
                string id = order.ids[i];
                int left = order.counts[i];

                // An item with a placeable model is set down as itself, one by one.
                if (ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo info) && info.Prefab != null && info.Placeable && !ConstructionSite.IsStructure(id))
                {
                    for (; left > 0; left--) units.Add(new Unit { Id = id, Info = info });
                    continue;
                }

                // Everything else goes into a box, by weight.
                while (left > 0)
                {
                    int put = 0;
                    if (boxes)
                    {
                        if (current == null) current = new List<ContainerStack>();
                        put = ContainerRules.Add(BoxId, current, id, left);
                        if (put <= 0 && current.Count > 0) { CloseBox(); current = new List<ContainerStack>(); put = ContainerRules.Add(BoxId, current, id, left); }
                        if (put <= 0) current = null;
                    }
                    if (put > 0) { left -= put; continue; }
                    loose.Add(id);   // too heavy for any box (or no box asset): it lies on the ground by itself
                    left--;
                }
            }
            CloseBox();

            // Goods go onto pallets when there is a pallet asset: one pallet per load, filled in tidy stacks.
            ItemRegistry.TryGet(PalletId, out ItemRegistry.ItemInfo palletInfo);
            bool pallets = palletInfo != null && palletInfo.Prefab != null && units.Count > 0;

            // The models are loaded on demand: wait for each one used before placing (a placed copy of an unloaded template is empty).
            var waited = new HashSet<string>();
            if (pallets)
            {
                GlbTemplate pg = palletInfo.Prefab.GetComponent<GlbTemplate>();
                if (pg != null)
                {
                    pg.EnsureLoading();
                    float until = Time.realtimeSinceStartup + 20f;
                    while (!pg.Ready && !pg.Failed && Time.realtimeSinceStartup < until) yield return null;
                    if (!pg.Ready) pallets = false;
                }
            }
            foreach (Unit u in units)
            {
                if (!waited.Add(u.Id)) continue;
                GlbTemplate glb = u.Info.Prefab != null ? u.Info.Prefab.GetComponent<GlbTemplate>() : null;
                if (glb == null) continue;
                glb.EnsureLoading();
                float until = Time.realtimeSinceStartup + 20f;
                while (!glb.Ready && !glb.Failed && Time.realtimeSinceStartup < until) yield return null;
            }

            if (pallets)
            {
                PlaceOnPallets(units, palletInfo, centre, loose);
                Dbg.Log($"[Delivery] unloaded at ({centre.x:F1}, {centre.z:F1}) onto pallets: {units.Count} object(s), {loose.Count} loose item(s).");
                ToastNotificationSystem.ShowSuccess("Delivery arrived", "Your order is waiting at the delivery zone.");
                yield break;
            }

            // Group like with like (first appearance first), then pack each group into stacks.
            var groupIds = new List<string>();
            var groups = new Dictionary<string, List<Unit>>();
            foreach (Unit u in units)
            {
                if (!groups.TryGetValue(u.Id, out List<Unit> g)) { g = new List<Unit>(); groups[u.Id] = g; groupIds.Add(u.Id); }
                g.Add(u);
            }
            int cellsNeeded = loose.Count;
            foreach (string gid in groupIds) cellsNeeded += Mathf.CeilToInt(groups[gid].Count / (float)Mathf.Max(1, ContainerRules.StackingLimit(gid)));

            // Free grid squares in tidy rows starting at the delivery zone, clear of any foundation.
            int cols = Mathf.Clamp(Mathf.CeilToInt(Mathf.Sqrt(cellsNeeded * 1.5f)), 2, 8);
            var cells = new List<Vector3>();
            Vector3 origin = DropOrigin(centre);
            for (int row = 0; cells.Count < cellsNeeded && row < 40; row++)
                for (int col = 0; col < cols && cells.Count < cellsNeeded; col++)
                {
                    Vector3 p = PlantingValidator.SnapToGrid(origin + new Vector3(col, 0f, row));
                    p.y = TerrainHeightDetector.GetSurfaceY(p);
                    bool blocked = PlacedObject.ColumnsAt(p).Count > 0;
                    foreach (ConstructionSite cs in ConstructionSite.All) if (cs != null && cs.DistanceOutside(p) < 1.5f) { blocked = true; break; }
                    if (!blocked) cells.Add(p);
                }

            int cell = 0;
            foreach (string gid in groupIds)
            {
                List<Unit> g = groups[gid];
                int limit = Mathf.Max(1, ContainerRules.StackingLimit(gid));
                for (int k = 0; k < g.Count; k += limit)
                {
                    if (cell >= cells.Count) break;
                    Vector3 pos = cells[cell++];
                    float y = pos.y;
                    for (int level = 0; level < limit && k + level < g.Count; level++)
                    {
                        Unit u = g[k + level];
                        Vector3 at = new Vector3(pos.x, y, pos.z);
                        PlacedObject placed = PlacementController.SpawnPlaced(u.Id, u.Info, at, 0f, false, level, u.Contents);
                        if (placed != null) y += placed.Height;
                    }
                }
            }
            foreach (string id in loose) WorldItem.TryDrop(id, cell < cells.Count ? cells[cell++] : centre);

            Dbg.Log($"[Delivery] unloaded at ({centre.x:F1}, {centre.z:F1}): {units.Count} placed object(s) in {Mathf.Min(cell, cells.Count)} stack(s), {loose.Count} loose item(s), box asset {(boxes ? "ok" : "MISSING")}.");
            ToastNotificationSystem.ShowSuccess("Delivery arrived", "Your order is waiting at the delivery zone.");
        }

        /// <summary>
        /// Puts the goods on pallets: like with like in a row of units, each placed on the current pallet in its free space or
        /// stacked on an identical stack (PalletDeck), a new pallet when it is full. Pallets stand in rows on a 2 m pitch from the zone.
        /// </summary>
        private static void PlaceOnPallets(List<Unit> units, ItemRegistry.ItemInfo palletInfo, Vector3 centre, List<string> loose)
        {
            // like with like
            var order = new List<Unit>();
            var seen = new HashSet<string>();
            foreach (Unit u in units)
            {
                if (!seen.Add(u.Id)) continue;
                foreach (Unit v in units) if (v.Id == u.Id) order.Add(v);
            }

            Vector3 origin = DropOrigin(centre);
            int palletCount = 0;
            const int perRow = 3;
            PlacedObject pallet = null;
            PlacedObject lastPlaced = null;

            PlacedObject NewPallet()
            {
                for (int tries = 0; tries < 60; tries++)
                {
                    int n = palletCount++;
                    Vector3 p = PlantingValidator.SnapToGrid(origin + new Vector3((n % perRow) * 2f, 0f, (n / perRow) * 2f));
                    p.y = TerrainHeightDetector.GetSurfaceY(p);
                    bool blocked = PlacedObject.ColumnsAt(p).Count > 0;
                    foreach (ConstructionSite cs in ConstructionSite.All) if (cs != null && cs.DistanceOutside(p) < 1.5f) { blocked = true; break; }
                    if (blocked) continue;
                    return PlacementController.SpawnPlaced(PalletId, palletInfo, p, 0f, false);
                }
                return null;
            }

            bool TryPlace(PlacedObject onto, Unit u, Vector3 want)
            {
                if (onto == null) return false;
                float deckY = PalletDeck.DeckY(onto);
                Vector3 start = onto.transform.position + Vector3.up * (deckY - onto.transform.position.y);
                PlacedObject obj = PlacementController.SpawnPlaced(u.Id, u.Info, start, onto.transform.eulerAngles.y, false, 1, u.Contents);
                if (obj == null) return false;
                Vector2 size = PalletDeck.LocalRect(onto.transform, obj.gameObject, out Rect r) ? new Vector2(r.width, r.height) : new Vector2(0.5f, 0.5f);
                if (!PalletDeck.FindSpot(onto, u.Id, size, want, obj, out Vector3 pos, out int level, out _)) { obj.Remove(); return false; }
                obj.Relocate(pos, level);
                lastPlaced = obj;
                return true;
            }

            string lastId = null;
            foreach (Unit u in order)
            {
                if (pallet == null) pallet = NewPallet();
                Vector3 want = lastPlaced != null && lastId == u.Id ? lastPlaced.transform.position : (pallet != null ? pallet.transform.position : centre);
                if (TryPlace(pallet, u, want)) { lastId = u.Id; continue; }
                pallet = NewPallet();                       // that one is full
                if (TryPlace(pallet, u, pallet != null ? pallet.transform.position : centre)) { lastId = u.Id; continue; }
                loose.Add(u.Id);                            // it does not fit even on a pallet of its own
            }
        }

        /// <summary>Where the rows of goods start: the middle of the zone, or, with a pickup flag, the square's own corner (the rows run +x and +z, so they stay inside the square).</summary>
        private static Vector3 DropOrigin(Vector3 centre)
        {
            if (PickupFlag.TryZone(out Rect r, out _))
            {
                Vector3 c = PlantingValidator.SnapToGrid(new Vector3(r.xMin + 0.5f, 0f, r.yMin + 0.5f));
                c.y = TerrainHeightDetector.GetSurfaceY(c.x, c.z);
                return c;
            }
            return PlantingValidator.SnapToGrid(centre);
        }

        public static Vector3 DropPointBesideRoadEnd(IReadOnlyList<Vector2> road)
        {
            int n = road.Count;
            Vector2 end = road[n - 1];
            Vector2 dir = (road[n - 1] - road[Mathf.Max(0, n - 8)]).normalized;
            Vector2 side = new Vector2(-dir.y, dir.x);
            Vector2 p = end + dir * 6f + side * 4.5f;
            return new Vector3(p.x, TerrainHeightDetector.GetSurfaceY(p.x, p.y), p.y);
        }

        // ------------------------------------------------------------------ the van

        private sealed class DeliveryVan : MonoBehaviour
        {
            private Order _order;
            private IReadOnlyList<Vector2> _road;
            private GameObject _prefab;
            private System.Action<Order> _delivered;
            private System.Action _finished;
            private Vector3 _dropPoint;
            private Transform _model;
            private readonly List<Transform> _wheels = new List<Transform>();
            private float _modelYaw;          // turns the model so its nose follows the van's forward
            private float _s;                 // distance along the road, metres
            private float _length;
            private int _phase;               // 0 in, 1 unload, 2 turn, 3 out
            private float _timer;
            private float _heading;           // degrees about Y (world)
            private float _turnFrom;
            private Vector3 _smoothPos;

            private System.Action<Order, Vector3> _work = Deliver;   // what it does when it stops (the van unloads; the cargo truck loads)

            public void Begin(Order order, IReadOnlyList<Vector2> road, GameObject prefab, Vector3 dropPoint, int stopIndex, System.Action<Order> delivered, System.Action finished,
                              System.Action<Order, Vector3> work = null)
            {
                _order = order; _road = road; _prefab = prefab; _dropPoint = dropPoint; _delivered = delivered; _finished = finished;
                if (work != null) _work = work;
                _length = Mathf.Clamp(stopIndex, 2, road.Count - 1);
                _road = BuildPath(road, (int)_length);   // the road up to its stop, then (with a pickup flag) off the road into the flag's square
                _length = _road.Count - 1;
                _s = 0f;
                Vector3 p = PointAt(0f);
                transform.position = p;
                _heading = HeadingAt(0f);
                transform.rotation = Quaternion.Euler(0f, _heading, 0f);
                _smoothPos = p;
                StartCoroutine(LoadModel());
            }

            /// <summary>The road from its start to the stop; with a pickup flag the path goes on, straight across the ground, to the edge of the flag's square (a little inside it).</summary>
            private static List<Vector2> BuildPath(IReadOnlyList<Vector2> road, int stop)
            {
                var path = new List<Vector2>();
                for (int i = 0; i <= stop; i++) path.Add(road[i]);
                if (!PickupFlag.TryZone(out Rect r, out _)) return path;
                Vector2 from = road[stop];
                Vector2 inside = new Vector2(Mathf.Clamp(from.x, r.xMin + 2f, r.xMax - 2f), Mathf.Clamp(from.y, r.yMin + 2f, r.yMax - 2f));
                float leg = Vector2.Distance(from, inside);
                if (leg < 1f) return path;
                float step = 0f;
                for (int i = 1; i <= stop; i++) step += Vector2.Distance(road[i - 1], road[i]);
                step = Mathf.Max(0.5f, step / Mathf.Max(1, stop));   // the road's own spacing, so the van keeps its speed on the leg
                int n = Mathf.Max(1, Mathf.CeilToInt(leg / step));
                for (int k = 1; k <= n; k++) path.Add(Vector2.Lerp(from, inside, k / (float)n));
                return path;
            }

            private IEnumerator LoadModel()
            {
                GlbTemplate glb = _prefab.GetComponent<GlbTemplate>();
                while (glb != null && !glb.Ready)
                {
                    glb.EnsureLoading();
                    if (glb.Failed) { Finish(true); yield break; }
                    yield return null;
                }
                GameObject m = Instantiate(_prefab, transform);
                m.SetActive(true);
                m.transform.localPosition = Vector3.zero;
                m.transform.localRotation = Quaternion.identity;
                foreach (Collider c in m.GetComponentsInChildren<Collider>(true)) c.enabled = false;   // it drives past; nothing to bump into
                _model = m.transform;
                foreach (Transform t in m.GetComponentsInChildren<Transform>(true))
                    if (t.name.StartsWith("Wheel_") && !t.name.EndsWith("_hub")) _wheels.Add(t);
                // Which way does the model face? The nose marker tells (its direction from the model's origin, on the ground plane).
                Transform marker = null;
                foreach (Transform t in m.GetComponentsInChildren<Transform>(true)) if (t.name == "FrontMarker") { marker = t; break; }
                if (marker != null)
                {
                    Vector3 d = transform.InverseTransformPoint(marker.position);
                    d.y = 0f;
                    if (d.sqrMagnitude > 0.01f) _modelYaw = -Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
                }
                m.transform.localRotation = Quaternion.Euler(0f, _modelYaw, 0f);
            }

            private Vector3 PointAt(float s)
            {
                s = Mathf.Clamp(s, 0f, _length);
                int i = Mathf.Min(_road.Count - 2, Mathf.FloorToInt(s));
                Vector2 a = _road[i], b = _road[i + 1];
                Vector2 p = Vector2.Lerp(a, b, s - i);
                return new Vector3(p.x, TerrainHeightDetector.GetSurfaceY(p.x, p.y), p.y);
            }

            private float HeadingAt(float s)
            {
                Vector3 a = PointAt(s - 2f), b = PointAt(s + 3f);
                Vector3 d = b - a;
                d.y = 0f;
                if (d.sqrMagnitude < 0.0001f) return _heading;
                return Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
            }

            private void Update()
            {
                float dt = Time.deltaTime;
                if (dt <= 0f) return;
                float travelled = 0f;
                switch (_phase)
                {
                    case 0:
                    {
                        float remaining = _length - _s;
                        float speed = VanSpeed * Mathf.Clamp01(remaining / 14f + 0.15f);   // eases to a stop at the end
                        travelled = speed * dt;
                        _s += travelled;
                        if (_s >= _length - 0.2f) { _s = _length; _phase = 1; _timer = 0f; }
                        _heading = Mathf.LerpAngle(_heading, HeadingAt(_s), 6f * dt);
                        break;
                    }
                    case 1:
                        _timer += dt;
                        if (_timer > 0.8f && _order != null)
                        {
                            Order o = _order;
                            _order = null;
                            _work(o, _dropPoint);
                            _delivered?.Invoke(o);
                        }
                        if (_timer > 3.5f) { _phase = 2; _timer = 0f; _turnFrom = _heading; }
                        break;
                    case 2:
                        _timer += dt;
                        _heading = _turnFrom + 180f * Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(_timer / 3f));
                        travelled = 1.2f * dt;   // creeps through the turn
                        if (_timer >= 3f) _phase = 3;
                        break;
                    case 3:
                    {
                        float speed = VanSpeed * Mathf.Clamp01(_s / 6f + 0.3f);
                        travelled = speed * dt;
                        _s -= travelled;
                        float back = HeadingAt(_s) + 180f;
                        _heading = Mathf.LerpAngle(_heading, back, 6f * dt);
                        if (_s <= 0.5f) { Finish(false); return; }
                        break;
                    }
                }

                Vector3 pos = PointAt(_s);
                _smoothPos = Vector3.Lerp(_smoothPos, pos, 18f * dt);
                Quaternion yaw = Quaternion.Euler(0f, _heading, 0f);
                // pitch with the road: the ground under the nose against the ground under the tail
                Vector3 fwd = yaw * Vector3.forward;
                float rise = TerrainHeightDetector.GetSurfaceY(_smoothPos + fwd * 1.8f) - TerrainHeightDetector.GetSurfaceY(_smoothPos - fwd * 1.8f);
                float pitch = -Mathf.Atan2(rise, 3.6f) * Mathf.Rad2Deg;
                transform.SetPositionAndRotation(_smoothPos, yaw * Quaternion.Euler(pitch, 0f, 0f));

                // wheels turn with the distance covered (reversing turns them back)
                if (travelled != 0f)
                {
                    float deg = travelled / 0.42f * Mathf.Rad2Deg * (_phase == 3 ? -1f : 1f);
                    foreach (Transform w in _wheels) if (w != null) w.Rotate(transform.right, deg, Space.World);
                }
            }

            private void Finish(bool failed)
            {
                if (_order != null)
                {
                    // the model never loaded: still bring the goods
                    Order o = _order;
                    _order = null;
                    _work(o, _dropPoint);
                    _delivered?.Invoke(o);
                }
                _finished?.Invoke();
                Destroy(gameObject);
            }
        }
    }
}
