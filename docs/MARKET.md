# Selling on the Market

The Market app's **Sell** tab books a pickup; the **cargo truck** (`vehicle_market_cargo_truck`, an open-bed stake truck, `tools/make_cargo_truck.py`) comes for it.
Code: `World/MarketPickup.cs` (what can be sold, the collection), `World/DeliveryService.cs` (the order and the drive), `UI/Phone/PhoneController.cs` (`PopulateMarketSell`).

- **The pickup zone** is the delivery zone (5 tiles from the first house placed, toward the road, where the van drops its goods; `DeliveryService.ZoneNow`), out to
  8 m (`MarketPickup.ZoneRadius`). Placed items (on a pallet too) and loose items in it count.
- **The Sell tab** lists the sellable item types in the zone with how many there are and what they pay. Items already booked are not offered twice. "Sell all" asks for a
  confirmation and books a pickup for that item type (`DeliveryService.ScheduleMarket`, an `Order` with `market` set, saved with the other orders).
- **The truck** sets off at 07:00 the next day, like the van (one truck out at a time), drives to the road point nearest the zone, stops, loads what was booked
  (the items nearest the zone's centre first; placed items are removed, stacks above them come down) and leaves. It pays then: `base_value` x `MarketPickup.Share` (75 %) per
  item, so buying and selling can never be looped for profit. What is no longer in the zone when it comes is not paid for (a toast says how many).
- **What sells:** anything with a `base_value` that is not a structure, a blueprint, a vehicle, a pallet, a spigot post, a macerator, a standby generator or a fuel tank.
  A container still holding something is not sold (empty it first). The price comes from the manifest's `properties.base_value` (catalog field `base_value`).
- With no road or no truck model the pickup is simply done at once. The Market still needs the internet.

## The pickup flag

Plant a **Pickup Flag** (`building_pickup_flag`, bought at the depot, `Scripts/World/PickupFlag.cs`) to choose the pickup zone yourself. The flag stands on one corner tile of a 10 by 10 tile square that reaches from the flag toward the road (the road point nearest the flag), along each axis: a square, not a radius. Hover the flag to draw the square on the ground. The Market Sell tab counts what lies in the square, deliveries are dropped at its middle and the cargo truck collects from it. The first flag planted rules; with no flag the zone is the old one beside the first house (a radius of 8 m).
