# Internet: the phone's signal and the homestead's network

Code: `Assets/Scripts/Growth/Net.cs` (the network, the wall rack), `Assets/Scripts/UI/Phone/Connectivity.cs` (the phone), the wire system (`Wiring.cs`, kind `net`).
Data: `tools/set_net_data.py` (roles, ports, PoE, ranges). Models: `tools/make_internet.py`, `tools/net_pictures.py`.

## The phone

The status bar shows a live signal: four bars and the link in use (`5G`, `Wi-Fi`, `Wi-Fi !` = a Wi-Fi with no internet behind it, `No service`). It is worked out four
times a second from where the player stands (`Connectivity.Refresh`).

**Cellular.** The strength (0 to 1) is the lie of the land (0.55 to 0.8, a slow noise over the world) times:

| | factor |
|---|---|
| Blizzard | 0.35 |
| Thunderstorm | 0.5 |
| Snow / rain / fog / wind | 0.75 / 0.8 / 0.9 / 0.92 |
| Indoors (inside a finished building's walls) | 0.65 |
| A powered cellular antenna within its range (60 m) | 1.3 (a boost of 30%) |

and it wavers a little, more in bad weather. Bars: under 0.18 none, 0.32 one, 0.48 two, 0.64 three, else four. With NO bars there is no internet: a blizzard indoors does
it almost anywhere, a thunderstorm indoors in a weak spot.

**Wi-Fi.** In range of a powered router or access point the phone joins it (full bars beside it, one at the edge of its range). If that network has internet the phone uses
it and the cellular signal no longer matters. A Wi-Fi with no internet behind it leaves the phone on cellular.

**No internet:** the shops, the bank, the market and the gigs do not open (a toast says why). ResView, the grid, the almanac and the radio still work.

## The network

Bandwidth comes only from a satellite dish. Everything else is cabled with Cat6 (wire cutters in hand: right click one, then the next; the same two again unplugs) or
reached over Wi-Fi. The order is

    dish or yagi  >  router  >  switch (optional, PoE or standard)  >  device

| Role (`properties.wire_role`) | Items | Cables to |
|---|---|---|
| `net_dish` | the satellite dishes | a router (its WAN port) |
| `net_yagi` | the yagi antenna (PoE) | a router or a switch, on a PoE port |
| `net_router` | the routers (the rackmount one has no Wi-Fi: cable an access point to it) | dish, switches, devices |
| `net_switch` | the switches, the PoE injector | routers, switches, yagis, devices |
| `net_ap` | the outdoor access point (PoE, Wi-Fi) | a PoE port |
| `net_camera` | the PoE camera (wall mounted) | a PoE port |
| `net_device` | a TV | a standard port, or nothing: it uses Wi-Fi |
| `net_jack` | the Ethernet wall jack (through the wall) | anything: it only passes the cable through |
| `net_rack` | the 8U wall rack | what its contents allow |
| `net_antenna` | the omni cellular antenna | nothing: it only needs power |

- **One dish to a network.** A network (everything joined by cable) takes one dish; a second is refused. A dish gives its `bandwidth_mbps` at most, and the weather takes
  some of it (less than it takes of the cellular signal): blizzard 0.55, thunderstorm 0.7, snow 0.85, rain 0.9, fog 0.95 (`Net.DishWeather`).
- **Ports** (`properties.net_ports`). Every cable takes one port at each end, and a device joins no more cables than it has ports. A router's ports are its LAN ports: the
  dish goes in its WAN port, which is not counted. A network takes as many yagis as it has PoE ports for.
- **PoE and standard ports are separate.** A switch or injector with `properties.poe` has PoE ports (15 W of DC each); every other port is a standard port. A device that
  runs from its cable (`properties.poe_powered`: the camera, the access point, the yagi) is cabled ONLY to a PoE port, and everything else (a TV) ONLY to a standard port.
  A cable between two hubs (router, switch, rack) takes a standard port when one is free and a PoE port otherwise. The look-at panel counts both kinds.
- **Cable.** Cat6 comes as a 15 m and a 30 m patch cable and a 150 m spool (`wire_kind: net`); a run is at most 100 m. A switch may be cabled to another switch.
- **In the walls, routed outside.** A cable between two things INSIDE one building (or from the inside to its wall jack) is in the walls: it is not drawn (`WireRouter.NetInWalls`). OUTSIDE it is run like a wire (`WireRouter.Route`): from a dish or antenna on the roof along the eave and down the wall to the jack (like a solar panel's run), along the outside walls between things mounted there, in conduit, and a long run between buildings buried.
- **The dish and the wall jack.** ONLY the dish needs the **Ethernet wall jack** (`net_jack_wall`, a through-the-wall item with an RJ45 jack on each side): the dish is
  cabled to a jack and the jack to the router (dish, jack, router), wherever the dish stands, on the roof or in the yard. Everything else (a yagi, an access point, a
  camera, a switch in another building) is cabled straight to its router or switch. A jack has two ports, uses no bandwidth and needs no power; the port and pairing rules
  are applied to what is at the two ends of the cable through it. A building is CONNECTED when its jack leads to a working dish (`Net.StructureLink`). A dish cabled straight
  to a router (a cable laid before this rule) is dead until it is run through a jack (`Net.Dead`).
- **Power.** Routers, switches, the rack, a TV and the cellular antenna run on the power of the building they stand in or are mounted on (or a running portable generator
  beside them). PoE devices run from their PoE port. A dish is powered through its cable by the router.
- **What it draws.** The gear is a load on its building (`Net.LoadW`, each item's `power_draw_w`): the routers and switches, every device in a rack, a TV, the
  cellular antenna, plus what the PoE ports there feed down their cables (cameras, access points, yagis) and the dish its router powers. It shows in the grid app as
  "Network (building)".
- **Online.** The internet goes from the powered dish over the cables through powered gear and the jacks. A camera, an access point or a TV passes nothing on.
- **Yagi links.** Two powered yagis within range of each other (1,500 m) carry the network across: each must point at the other (its boom is its forward; R turns it while
  placing). Within 20 degrees the link is full, within 45 half, wider there is none.
- **On the roof.** The dishes, the yagi and the access point (`properties.roof_mount`) stand on the ground or go up on a roof: with one in hand, aim at the roof of a
  finished building (within 6 m of it), R turns it 22.5 degrees a press (Shift + R the other way), left click again mounts it upright. Once it is up, R with the cursor
  on it turns it where it stands, so a yagi is aimed without taking it down.
- **Wi-Fi.** A powered router or access point reaches its `range_m` (router 30 m, mesh router 45 m, indoor access point 25 m, outdoor access point 60 m; the rackmount router and a rack give none: the access points cabled to them do). A TV with no cable is online while it is in
  range of one that has internet.
- **The wall rack** (`properties.rack_capacity_u`, 8 units). Rackmount gear (`properties.rack_units`: the rackmount router, the 16 and 32 port switches, the 16 port PoE
  switch) slides in with a left click and comes out with a right click. The rack is cabled as ONE device: its standard ports and its PoE ports are each the sum of what is
  in it, and it takes a dish when a router is in it. It cannot be taken down, or a device taken out, while that would leave more cables than ports. Its contents are saved
  with it (`SavedAttached.shelfIds`).
- **The rack UPS** (`net_ups_rackmount`, two units, `capacity_wh` 3,000). While the building has power it charges (4 game hours from flat, a load of its own while it
  does). When the power fails the rack runs on from it, with everything the rack feeds over its cables (PoE devices, the dish): `Net.OnUps`. It lasts its charge divided
  by what the rack runs (`Net.RackLoadW`): two hours with the rack fully loaded (six units of PoE switch, 1,500 W), longer with less. The charge is the rack node's
  `ChargeWh`, saved with the rack; the rack's look-at panel shows the charge and the time left. Only the rack is backed up: a router standing on a shelf is not.
- **ResView** shows the bandwidth the dish brings in now (and its rating when the weather takes some), what the online cameras and TVs use, the phone's own link, and every
  piece of gear with its state and ports.

## The subscription

A dish brings nothing in without a plan (`NetPlan.cs`). The bandwidth is the least of the plan and what the dish itself gives in this weather.

| Plan | Allows | A month |
|---|---|---|
| Basic | 25 Mbps | $40 |
| Standard | 100 Mbps | $75 |
| Fast | 250 Mbps | $120 |
| Max | 500 Mbps | $180 |

A plan is taken in ResView (Internet, at the bottom of the list) and paid a month (28 days) ahead: the first month at once, then each renewal as the month runs out (a toast
says so). Changing plan credits the unused days of the old one against the new. A renewal that cannot be paid cancels the plan and the internet goes down. The plan and its
days left are saved (`GameSave.netPlan`, `netPlanDaysLeft`); a new game starts with none.

## Not done yet

The bandwidth is not shared out or throttled (use over the limit and a half yagi link change nothing yet), a PoE port's 15 W is not checked against the device's draw, the
gear's own power draw is not added to its building's load, cameras show no picture, and the TVs have no models yet.
