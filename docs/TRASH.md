# Trash: bins, bags and the weekly truck

Three items (`tools/make_trash_assets.py`, procedural models, no Meshy):

| Item | What it is |
|---|---|
| `waste_garbage_bag_full` (Full Garbage Bag) | A full, tied bag, 9 kg. Not for sale: the game makes the bags. The Market does not buy it. |
| `waste_trash_bin_wheeled` (Wheeled Trash Bin) | The big bin with a hinged lid, a handle and two wheels at the back, $65 at the Depot. A container that holds FOUR full bags (`container.max_items` 4, accepts only the bag, 40 kg). It is a push item (`container.pushable`, like a wheelbarrow): right click it with an empty slot to take the handle and push it, right click again to put it down. |
| `vehicle_trash_truck` (Trash Truck) | The refuse truck: the fuel truck's chassis, cab and four separate wheels (`Wheel_FL/FR/RL/RR`) and a `FrontMarker`, with a rear-loading body. Not for sale. |

## The weekly pickup (`Assets/Scripts/World/TrashService.cs`)

- Every seventh day of the year, at 07:00, the trash truck drives to the PICKUP ZONE: the square of the pickup flag (docs/DELIVERY.md, docs/MARKET.md), the same spot the delivery van and the cargo truck use.
- It empties every wheeled trash bin standing in the zone: the bags in them are gone. Bags that are not in a bin are NOT collected. A bin that was not moved into the zone is not emptied ("N bins were not in the pickup zone").
- The pickup costs **$50 a week** (`TrashService.WeeklyFee`), taken when the truck reaches the zone, whether or not a bin was out. If you cannot pay, the truck leaves without emptying anything. There is no round, and no fee, until a bin has been placed.
- The round is an order of the delivery service (`DeliveryService.Order.trash`), so it shares the road and the truck driving with the other trucks. The day of the last round is saved (`GameSave.trashLastDay`) so loading on pickup day never sends the truck twice.
