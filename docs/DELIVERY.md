# Deliveries

A phone store checkout (Nail It, Homestead Depot and the other stores) charges the player and schedules the order for **the next
day**. Code: `Assets/Scripts/World/DeliveryService.cs`.

1. **Order.** `HandleCheckout` calls `DeliveryService.Schedule(cart)`: the order is due the day after (day of year + 1), saved in
   `GameSave.deliveries`.
2. **Dispatch.** From **07:00** on the due day (or at once when a save is loaded late) the toast **"A Delivery is on the way"**
   shows and the delivery van enters.
3. **The van.** `vehicle_delivery_boxvan` (`tools/make_boxvan.py`) appears at the map-edge end of the starter road and drives
   along `HomesteaderTerrainGenerator.RoadPoints` at 9 m/s (it follows the ground, pitches with it and spins its `Wheel_*`
   objects, easing to a stop at the end), unloads, turns around and drives back out. The model's `FrontMarker` empty tells the
   game which way it faces.
4. **The delivery zone.** Before any house is placed it is beside the road end. Once ANY house or cabin (an id containing "cabin" or "house", not a greenhouse) has been placed, even only its dirt area, the zone moves to **5 tiles from the FIRST house placed**, toward the road (a second house never moves it): a
   point 5 grid squares out from its foundation toward the road. The van drives to the road point closest to that zone and the
   goods are set down at the zone, clear of the foundation. (`DeliveryService.TryHouseZone`)
5. **Pallets.** When the pallet asset exists, the goods are set down ON PALLETS (`building_pallet_wood`), one pallet per load, in a row
   from the zone on a 2 m pitch. Like items are grouped and stacked up to their stacking limit, packed side by side on the deck; a
   full pallet starts the next one. (`PalletDeck.cs`; the same packing is what placing things on a pallet by hand uses.)
6. **The goods.** At the zone. An item with a placeable model (a crate, a barrel, a tool with a placeable model) is **set down as itself**.
   Every other item (no model, or not placeable: seeds, food, liquids, structure kits) goes **into cardboard boxes**
   (`box_large_brown`, filled by weight; pick a box up and take the items out as usual). Only something too heavy for any box lies on the
   ground by itself. The toast **"Delivery arrived"** shows.
7. **No road or no van model:** the goods turn up at the delivery zone at once, without the van.

Only one van runs at a time; later orders wait their turn. A van that is mid-trip when the game is saved is not saved: its order
stays pending and the van starts again on the next load.
