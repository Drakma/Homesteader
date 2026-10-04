# HUD Root / Visual Tree (`Resources/HUDTree/`)

The entire in-game HUD is a single Unity UI Toolkit `UIDocument` driven by one
UXML layout (`HudUI.uxml`) and wired to C# via `HudBindings.cs`. This document
describes the visual tree hierarchy, the C# scripts that power it, and the
asset folders that feed it.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  UIDocument (on the "HUD" GameObject in scene)               │
│  └─ rootVisualElement  ←  HudBindings._root                  │
│     └─ TemplateContainer                                      │
│        └─ ScreenRoot  (.screen-root)                          │
│           ├─ ToastContainer                                   │
│           ├─ Header                                           │
│           │   ├─ VitalsWell → Vitals (4 vital chips)          │
│           │   ├─ WeatherTimelineGroup                         │
│           │   ├─ TimeAndDateCell → TimeAndDate                 │
│           │   ├─ CelestialTimelineGroup                       │
│           │   │   └─ SeasonCell → SeasonIcon                  │
│           │   ├─ ResourcesCell → ResourcesBar (5 resources)   │
│           │   └─ SettingsBtn (⚙)                              │
│           ├─ ToolbarSlots (10 slots, bottom center)           │
│           ├─ PhoneWrapper (slide-in smartphone, Tab)          │
│           │   └─ phone-chassis → phone-screen                 │
│           │      ├─ phone-status-bar                          │
│           │      ├─ phone-content (paginated app launcher)    │
│           │      │   ├─ PhoneHome (weather widget + app grid) │
│           │      │   ├─ ViewVolt (Grid OS)                    │
│           │      │   ├─ ViewRes (ResView)                     │
│           │      │   ├─ ViewStore (3 stores)                  │
│           │      │   ├─ ViewBank                             │
│           │      │   ├─ ViewMarket                           │
│           │      │   ├─ ViewAlmanac                           │
│           │      │   ├─ ViewAdmin (season/time/vitals/res)   │
│           │      │   ├─ ViewMods (mod manager)                │
│           │      │   └─ ViewGigs (job board)                 │
│           │      └─ phone-bottom-bar (home pill)             │
│           ├─ WindowShade (modal overlay)                     │
│           │   ├─ SettingsWindow                              │
│           │   └─ ConfirmModal                                │
│           └─ AssetSpawnerWindow (item catalog, draggable)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Visual Tree Elements (`HudUI.uxml`)

### 2.1 ScreenRoot

`<ui:VisualElement name="ScreenRoot" class="screen-root" picking-mode="Ignore">`

The top-level container. `picking-mode="Ignore"` means it never intercepts
clicks — only its children do. All HUD elements are children of this root.

### 2.2 ToastContainer

`name="ToastContainer" class="toast-container" picking-mode="Ignore"`

Mounted directly below `ScreenRoot` so toasts render underneath the `Header`
band in draw order. Populated at runtime by `ToastNotificationSystem`, which
binds to this container in `HudBindings.ResolveReferences()`.

### 2.3 Header

`name="Header" class="header"` — full-width top band, flex-row layout.

| Child | name | Purpose |
|---|---|---|
| VitalsWell | `VitalsWell` | Left cluster: 4 vital chips (Wellness, Stamina, Thirst, Hunger) |
| WeatherTimelineGroup | `WeatherTimelineGroup` | Moving weather timeline tape + current temp cell |
| TimeAndDateCell | `TimeAndDateCell` | Center: season + date + wall clock + speed state |
| CelestialTimelineGroup | `CelestialTimelineGroup` | Moving sun/moon timeline + season icon |
| ResourcesCell | `ResourcesCell` | Right cluster: 5 resource rows (Water, Electricity, Bandwidth, Fuel, Money) |
| SettingsBtn | `SettingsBtn` | Gear icon button (opens Settings window) |

#### Vitals (`VitalsWell` → `Vitals`)

Four `vital-row` elements, each containing:
- `vital-icon` (icon art element with category-specific class)
- `vital-meter` → `vital-meter-fill` (the bar that fills/empties)
- `vital-meter-center` (center marker for the signed -100..+100 scale)

Named fill elements: `VitalWellnessFill`, `VitalStaminaFill`,
`VitalThirstFill`, `VitalHungerFill`.

Separator labels (`text="|"`, class `hud-sep`) are placed between vital rows.

#### Weather Timeline (`WeatherTimelineGroup`)

A horizontally scrolling tape showing weather icons at 4-hour intervals
(-32h to +32h, 17 nodes). The track translates left as time advances.

| Element | name | Purpose |
|---|---|---|
| WeatherTimelineWell | `WeatherTimelineWell` | Clipping viewport |
| WeatherTimelineViewport | `WeatherTimelineViewport` | Overflow-hidden viewport |
| WeatherTimelineTrack | `WeatherTimelineTrack` | Moving track (translated by C#) |
| CurrentTempCell | `CurrentTempCell` | Live temperature display |
| CurrentTempLabel | `CurrentTempLabel` | "72°F" label |

Built dynamically by `HudBindings.BuildWeatherTimelineTrack()` and updated
each frame by `UpdateWeatherTimelineTape()`.

#### Time & Date (`TimeAndDateCell` → `TimeAndDate`)

| Element | name | Purpose |
|---|---|---|
| TimeDisplayRow | `TimeDisplayRow` | Row containing the time line label |
| TimeLineLabel | `TimeLineLabel` | "Winter January 1 8:00" |
| SpeedStateLabel | `SpeedStateLabel` | "1x" / "3x" / "5x" / "10x" / "Paused" |

#### Celestial Timeline (`CelestialTimelineGroup`)

Mirrors the weather timeline but shows sun/moon phase icons. The season
icon is attached to the left side.

| Element | name | Purpose |
|---|---|---|
| SeasonCell | `SeasonCell` | Container for the season tree icon |
| SeasonIcon | `SeasonIcon` | Season tree icon (spring/summer/autumn/winter) |
| TimelineWell | `TimelineWell` | Clipping viewport |
| TimelineViewport | `TimelineViewport` | Overflow-hidden viewport |
| TimelineTrack | `TimelineTrack` | Moving track (translated by C#) |

Built by `HudBindings.BuildTimelineTrack()` and updated by
`UpdateTimelineTape()`.

#### Resources (`ResourcesCell` → `ResourcesBar`)

Five `resource-row` elements, each with a `resource-icon` (category-specific
class) and a `resource-amount` label:

| Label name | Resource | Default text |
|---|---|---|
| `ResourceWaterLabel` | Water | "0 L" |
| `ResourceElectricityLabel` | Electricity | "0.00 MJ" |
| `ResourceBandwidthLabel` | Bandwidth | "0 Mbps" |
| `ResourceFuelLabel` | Fuel | "0 L" |
| `ResourceMoneyLabel` | Money | "0" |

Separator labels between rows, same `hud-sep` class as vitals.

### 2.4 ToolbarSlots

`name="ToolbarSlots" class="toolbar-slots"` — absolutely positioned at bottom
center. Contains 10 `tool-slot` elements (`ToolbarSlot0` through
`ToolbarSlot9`), each with:

- `tool-slot-icon` (icon art, picking-mode Ignore)
- `tool-slot-num` (keyboard number label: 1-9, 0)
- `ToolSlotLabelN` (stack count label, e.g. "x3")
- `tool-slot-underline` (selection indicator)

Slot 0 starts with class `tool-slot--selected`. Click events on each slot
call `HudBindings.SelectToolbarSlot(index)`.

### 2.5 PhoneWrapper

`name="PhoneWrapper" class="phone-wrapper phone-wrapper--hidden"` — an
in-game smartphone, slide-in animated, toggled with **Tab**.

Structure:
- `phone-chassis` → `phone-screen`
  - `phone-notch-bar` (speaker pill)
  - `phone-status-bar` (clock, celestial icon, 5G, battery)
  - `phone-content` (paginated app launcher + 9 app views)
  - `phone-bottom-bar` (home pill button)

#### Phone App Launcher (paginated, 2 pages)

**Page 1 (12 apps):**

| Tile name | App | View |
|---|---|---|
| `AppTileVolt` | Grid OS | ViewVolt |
| `AppTileRes` | ResView | ViewRes |
| `AppTileAlmanac` | Good Almanac | ViewAlmanac |
| `AppTileDepot` | Homestead Depot | ViewStore (Depot) |
| `AppTileGrocer` | Pantry & Grocer | ViewStore (Grocer) |
| `AppTileFeed` | Valley Feed & Seed | ViewStore (Feed) |
| `AppTileBank` | First Homestead Bank | ViewBank |
| `AppTileMarket` | Valley Market | ViewMarket |
| `AppTileMods` | Mod Manager | ViewMods |
| `AppTileAdmin` | Admin Tools | ViewAdmin |
| `AppTileGigs` | Gigs | ViewGigs |
| `AppTileLumber` | (placeholder) | — |

**Page 2 (8 apps):**

| Tile name | App |
|---|---|
| `AppTileVehicles` | Wheel Deal (vehicles) |
| `AppTileWater` | Tank You (water) |
| `AppTileLivestock` | Tractor Beam (livestock) |
| `AppTileEquipment` | Nail It (equipment) |
| `AppTileDealership` | Shift Happens (dealership) |
| `AppTileTrailerShack` | Trailer Shack (housing) |
| `AppTileVoltvision` | VoltVision (electrical) |
| `AppTileFurniture` | Sofa So Good (furniture) |

Page dots: `PageDot0`, `PageDot1` (in `PhonePageDotsRow`).

#### Phone App Views

Each view is a `phone-app-view` with `phone-app-view--hidden` toggled by
`PhoneController.ShowView()`. Each has a header with a back button and a
scrollable content area.

| View | name | Key features |
|---|---|---|
| Volt (Grid OS) | `ViewVolt` | Solar wattage, battery %, load |
| Res (ResView) | `ViewRes` | Water, fuel, internet telemetry |
| Store | `ViewStore` | 3 stores (Depot, Grocer, Feed) with cart + checkout |
| Bank | `ViewBank` | Balance, loan debt, take/repay loans |
| Market | `ViewMarket` | Buy/sell tabs |
| Almanac | `ViewAlmanac` | Daily/weekly forecast, astronomy |
| Admin | `ViewAdmin` | Season, time, vitals, resources, weather controls |
| Mods | `ViewMods` | Category cards, mod enable/disable |
| Gigs | `ViewGigs` | Job board, take a shift, daily pay |

### 2.6 WindowShade

`name="WindowShade" class="window-shade window-shade--hidden"` — a
full-screen dimming overlay that sits behind modal windows. Click on the
shade background (not on a window) dismisses the topmost window.

Contains:

#### SettingsWindow

`name="SettingsWindow" class="window window--hidden"` — draggable by
header. Contains:
- Master Volume slider, Music Volume slider
- Fullscreen toggle, V-Sync toggle
- "Test Confirm Dialog" button, "Apply & Close" button

#### ConfirmModal

`name="ConfirmModal" class="modal modal--hidden"` — draggable by header.
A generic 3-button modal (Cancel, optional Third, Confirm) with dynamic
title and message. Used by `HudBindings.ShowModal()`.

### 2.7 AssetSpawnerWindow

`name="AssetSpawnerWindow" class="window asset-spawner-window
asset-spawner-window--hidden"` — a draggable, resizable item catalog
window opened from the Admin app. Contains:
- Category dropdown, search field, shortcut hint
- Scrollable asset grid (populated from `AssetCatalog.json`)
- Status bar with item count and resize handle

---

## 3. C# Scripts (`Assets/Scripts/UI/`)

### 3.1 HudBindings.cs

**File**: `Assets/Scripts/UI/HudBindings.cs` (~1658 lines)

The central MonoBehaviour that drives the entire HUD. Annotated with
`[DefaultExecutionOrder(-80)]` and `[RequireComponent(typeof(UIDocument))]`.

**Responsibilities:**
- Resolves all UXML elements by name via `Q<T>(name)` queries
- Ticks `TimeSystem` each frame (`_ownsTimeSystem` flag)
- Writes state to the live UIDocument: time, vitals, resources, toolbar
- Handles keyboard shortcuts (Esc, Tab, Space, `[`/`]`, 1-0, scroll wheel)
- Manages Settings window, Confirm modal, Asset Spawner window
- Builds and updates the celestial and weather timeline tapes
- Creates and owns the `PhoneController` instance
- Provides static `KeyboardCaptured` flag for gameplay input gating
- Provides `IsPointerOverUI()` for click-through detection

**Key static properties:**
- `HudBindings.Instance` — singleton accessor
- `HudBindings.KeyboardCaptured` — true when any modal/settings/text field has keyboard focus

**Key methods:**
| Method | Purpose |
|---|---|
| `ResolveReferences()` | Q() all UXML elements, wire callbacks, build timelines |
| `Update()` | Tick time, handle shortcuts, write all widgets |
| `WriteTime()` | Update time label, speed label, season icon, timeline tapes |
| `WriteVitals(HudState)` | Update 4 vital bar fills + percent labels |
| `WriteResources(HudState)` | Update 5 resource amount labels |
| `WriteToolbar(HudState)` | Update 10 toolbar slot icons + counts + selection |
| `ShowModal(...)` | Open confirm modal with title, message, callbacks |
| `OpenSettings()` / `CloseSettings()` | Toggle settings window |
| `OpenAssetSpawner()` / `CloseAssetSpawner()` | Toggle item catalog |
| `SelectToolbarSlot(int)` | Select a toolbar slot by index |
| `MakeDraggable(...)` / `MakeResizable(...)` | Window drag/resize helpers |
| `IsPointerOverUI(Vector2)` | Check if screen position is over a pickable HUD element |

### 3.2 HudState.cs

**File**: `Assets/Scripts/UI/HudState.cs` (~547 lines)

Plain C# data class (not a MonoBehaviour) holding all runtime HUD state.
Accessed via `HudState.Active` singleton.

**Data held:**
- `Vitals` — `Dictionary<VitalId, Vital>` (Wellness, Stamina, Thirst, Hunger; signed -100..+100)
- `Resources` — `Dictionary<ResourceId, Resource>` (Water, Electricity, Bandwidth, Fuel, Money)
- `Fuel` has subspecies: gasoline, diesel, kerosene, propane
- `Toolbar` — `List<ToolbarSlotData>` (10 slots, each with IconId + Count)
- `SelectedSlot` — int (0..9)
- `HeldAssetId` — string (the item in the selected slot)
- `Units` — `UnitSystem` (Metric or Imperial)
- `LoanDebt` — float (bank loan principal, 3.5% APR)

**Key methods:**
- `AddItemToToolbar(itemId, count, maxStack)` — stack-aware item insertion
- `ConsumeFromSelectedSlot(count)` — remove items from selected slot
- `SelectSlot(idx)` — set selected slot + HeldAssetId
- `SpendMoney(amount)` / `AddMoney(amount)` / `TakeLoan(principal)` / `RepayLoan(amount)`
- `SetVitalValue(id, value)` / `SetVitalPercent(id, percent)`
- `SetResourceAmount(id, amount)`
- `ResetToNewGameDefaults()` — zero resources, max vitals, empty toolbar
- `FormatWater()` / `FormatElectricity()` / `FormatFuel()` / `FormatBandwidth()` / `FormatMoney()`
- `FormatLength(meters, system)` — metric/imperial length formatting

### 3.3 TimeSystem.cs

**File**: `Assets/Scripts/UI/TimeSystem.cs`

The game clock. Ported from `assets/hud_kit/runtime/time_system.py`.

**Constants:**
- 7 days/week, 4 weeks/month, 3 months/season, 12 months/year, 336 days/year
- 1 real-second = 1 game-minute at 1x speed
- 12-hour Day phase, 12-hour Night phase

**Speeds:** Pause, 1x, 3x, 5x, 10x

**Seasons:** Spring, Summer, Autumn, Winter

**Weather:** Sunny, PartlyCloudy, Cloudy, Rain, Thunderstorm, Snow, Blizzard, Wind, Fog

**Key API:**
- `TimeSystem.Instance` — singleton
- `Tick(deltaTime)` — advance the clock
- `SetSpeed(HomesteaderSpeed)` — change simulation speed
- `Snapshot()` — returns `HudTimeState` struct with all current time data
- `GetWallClock()` — returns "HH:MM" string
- `GetCelestialIconId(minuteOfDay)` — sun/moon icon for a given time
- `FormatTemperature(celsius, units)` — metric/imperial temperature formatting

### 3.4 PhoneController.cs

**File**: `Assets/Scripts/UI/Phone/PhoneController.cs`

Pure C# class (not a MonoBehaviour) that manages the in-game smartphone.
Instantiated by `HudBindings` in `ResolveReferences()`.

**App views** (`AppView` enum): Home, Volt, Res, StoreDepot, StoreGrocer,
StoreFeed, Bank, Market, Almanac, Mods, Admin, Gigs.

**Key features:**
- Slide-in/out animation (Tab to toggle)
- Status bar: real-time clock, celestial icon, battery, weather
- Paginated app launcher (2 pages, swipeable)
- Store engine: 3 stores with live item cards, cart, checkout
- Bank: balance, loan debt, take/repay loans
- Market: buy/sell tabs
- Admin: season/time/vitals/resources/weather controls
- Mods: category cards, mod enable/disable
- Gigs: job board (delegated to `GigsApp.cs`)

**Static helpers:**
- `GetItemIcon(iconPath, itemId)` — loads a Texture2D from `Resources/HUDTree/PhoneIcons/`

### 3.5 GigsApp.cs

**File**: `Assets/Scripts/UI/Phone/GigsApp.cs`

Job board for the phone's Gigs app. 15 job offers (on-site and remote),
each with hourly wage, hours/day, shift start time, and daily pay.
`JobBoard.Tick()` is called from `HudBindings.Update()` to advance
active shifts.

### 3.6 ToastNotificationSystem.cs

**File**: `Assets/Scripts/UI/ToastNotificationSystem.cs`

Dropdown toast notifications mounted in `ToastContainer`. Features:
- Newer toasts insert at top, pushing older ones down
- Duration: 5s base + ~0.045s per character (reading time)
- Timers freeze when game is paused
- 5 types: Info (blue), Success (green), Warning (amber), Error (red), Severe
- Click to dismiss
- Static API: `ToastNotificationSystem.Show(title, message, type)`

### 3.7 WailaPanel.cs

**File**: `Assets/Scripts/UI/WailaPanel.cs`

"What Am I Looking At" panel, toggled with **F3**. Shows the name and
details of whatever `HoverTarget` finds under the cursor (or the grid
cell + biome under bare ground). Built entirely in C# (not in
`HudUI.uxml`) — it finds the existing HUD root and `ToastContainer` by
name and attaches itself.

Bootstraps via `[RuntimeInitializeOnLoadMethod]` — auto-creates a
`DontDestroyOnLoad` GameObject on scene load.

### 3.8 MiniMap.cs

**File**: `Assets/Scripts/UI/MiniMap.cs`

Flat isometric minimap in the lower-right corner, toggled with **M**.
A 128×128 color texture where each pixel represents a biome color.
Follows the game camera's yaw and is squashed to the isometric angle.
Player is a white dot. Mouse wheel zooms, drag to move, Shift+scroll
to resize. Position/size/zoom/on-off persisted in `PlayerPrefs`.

Bootstraps itself and attaches to `HudBindings.Root` once the HUD exists.
Exposes `MiniMap.PointerOver` so scroll-wheel events can defer to it.

### 3.9 AlmanacSystem.cs

**File**: `Assets/Scripts/UI/AlmanacSystem.cs`

Astronomical and weather forecasting engine. Generates:
- Ground-truth weather for any calendar day (336 days/year)
- Rolling 32-week forecast (8 weeks daily + 24 weeks weekly)
- Astronomical data: sunrise, sunset, daylight, solstices, equinoxes, moon phases

Confidence tiers: 95% (days 1-21), 70% (days 22-42), 50% (days 43-56),
40% (weekly outlooks weeks 9-32).

### 3.10 CursorManager.cs

**File**: `Assets/Scripts/UI/CursorManager.cs`

Applies custom cursor textures from `cursors.json` (the kit set in
`assets/hud_kit/cursors/`, copied to `StreamingAssets/HudKit/cursors/`).
Each cursor has a hotspot authored per-image (a tool cursor clicks at its
blade, not its center). Variants: Mono (black outline, white interior),
Color (category-coloured interiors) and Amber (the HUD accent as a gradient
with a bevel, lit from the upper left, so the cursor looks raised; the
default). It bootstraps
itself at startup (no scene object) and scales the 128 px art down to
`displaySize` (40 px) on load, hotspots included.

### 3.11 CursorHints.cs

**File**: `Assets/Scripts/UI/CursorHints.cs`

Picks the cursor every frame:

| Cursor | When |
|---|---|
| `cursor_arrow` | Default |
| `cursor_finger_point` | Over a clickable HUD element: a Button, Toggle, slider, dropdown, text field, or any element carrying the `clickable` USS class |
| `cursor_shears` | Sheep shears (`tool_shears_sheepwool`) in the active slot and a sheep that can be sheared under the cursor (`CursorHints.CanBeSheared`; today "a grown sheep", since shearing itself is not in the game yet) |
| `cursor_hand_open` | Over something in the world a right click picks up: a dropped item or log (`WorldItem`), ripe fruit on a planted or forest tree, berries on a bush |

Elements wired with `RegisterCallback<ClickEvent>` are tagged by calling
`.Clickable()` on them first (an extension that adds the `clickable` class);
UI Toolkit cannot be asked whether an element has a click handler. Do the
same for any new clickable element that is not a Button.

---

## 4. Style Sheets (USS)

| File | Scope |
|---|---|
| `HudUI.uss` | Main HUD styles: header, vitals, resources, toolbar, phone, windows, toasts, timelines |
| `HudUI_kit.uss` | Kit overlay styles (hand-designed chrome, enabled via `_enableKitOverlay` flag) |
| `PhoneUI.uss` | Phone-specific styles: chassis, screen, app tiles, app views, status bar |
| `ResourcesBar.uss` | Resource bar styles |
| `SpeedControls.uss` | Speed control chip styles |
| `TimeAndDate.uss` | Time and date widget styles |
| `ToolbarSlots.uss` | Toolbar slot styles |
| `Vitals.uss` | Vitals bar styles |

All USS files live in `Assets/Resources/HUDTree/` alongside the UXML.

---

## 5. Asset Folders (`Resources/HUDTree/`)

### 5.1 KitSprites/

Sprite PNGs loaded at runtime by `HudBindings` via
`Resources.Load<Texture2D>("HUDTree/KitSprites/...")`:

| Subfolder | Contents |
|---|---|
| `celestial/` | Sun/moon phase icons (loaded by `GetCelestialTexture()`) |
| `weather/` | Weather icons (loaded by `GetWeatherTexture()`) |
| `seasons/` | Season tree icons (`season_spring.png`, etc.) |
| `vitals/` | Vital icons (wellness, stamina, thirst, hunger) |
| `resources/` | Resource icons (water, electricity, bandwidth, fuel) |
| `buttons/` | Button sprites |
| `speed_controls/` | Speed chip sprites (pause, 1x, 3x, 5x, 9x) |
| `panels/` | Panel sprites (dialog, drawer, modal, toast) |
| `status_windows/` | Window divider/corner sprites |
| `toolbar_slots/` | Toolbar slot sprites |
| `decor/` | Decorative sprites (close_x, glow, separators) |

### 5.2 Atlases/

Procedurally painted atlases (from `Assets/UI/bake_atlases.py`):
- `button_atlas.png`, `checkbox_atlas.png`, `radio_atlas.png`
- `slider_track_*.png`, `slider_knob.png`
- `vital_fill_positive.png`, `vital_fill_negative.png` (gradient bars)
- `vital_gradient.png`, `header_strip.png`, `well.png`, `window_frame.png`, `modal_frame.png`

### 5.3 Atlases/Kit/

Hand-designed kit chrome (from `assets/hud_kit/sprites/`):
- `button_atlas_kit.png`, `vital_atlas_kit.png`, `resource_atlas_kit.png`
- `slot_atlas_kit.png`, `decor_atlas_kit.png`
- Re-baked via `python tools/bake_kit_atlases.py`

### 5.4 PhoneIcons/

18 app icon PNGs for the phone launcher (e.g. `app_grid_os.png`,
`app_resview_levels.png`, `app_gigs.png`, etc.).

### 5.5 Fonts/

The Homesteader HUD typeface — hand-drawn on a 16×24 design grid:
- `HomesteaderHUD.ttf` (Regular 400)
- `HomesteaderHUD_Medium.ttf` (Medium 500)
- `HomesteaderHUD_Bold.ttf` (Bold 700)
- `HomesteaderHUD_Italic.ttf` (Italic 400, -10° shear)
- `HomesteaderHUD_BoldItalic.ttf` (Bold Italic 700, -10° shear)
- `HomesteaderHUD_Bold_Mono.ttf` (Bold Monospace)

87 glyphs per file. Re-baked via `python tools/bake_kit_fonts.py`.

---

## 6. Reusable UXML Components

These UXML files exist as reusable templates (referenced by the main
`HudUI.uxml` or used standalone):

| File | Purpose |
|---|---|
| `Vitals.uxml` | Reusable vital bar component |
| `Toolbar.uxml` | Reusable toolbar component |
| `TimeAndDate.uxml` | Reusable time/date widget |
| `ResourcesBar.uxml` | Reusable resource bar |
| `SpeedControls.uxml` | Reusable speed control chips |
| `ToolbarSlots.uxml` | Reusable toolbar slots |
| `WindowPanel.uxml` | Reusable window panel template |
| `FormPanel.uxml` | Reusable form panel template |
| `PhoneUI.uxml` | Phone UI template |
| `HUDOverlay_kit.uxml` | Kit chrome overlay tree (KitVitals, KitResources, KitDecor) |

---

## 7. Keyboard Shortcuts

| Key | Action | Context |
|---|---|---|
| `Esc` | Open Settings / close topmost window / close phone | Always |
| `Tab` | Toggle phone | When keyboard not captured |
| `Space` | Toggle pause/play | When keyboard not captured |
| `[` / `]` | Decrease / increase speed | When keyboard not captured |
| `1`-`0` | Select toolbar slot 0-9 | When phone/spawner closed |
| Scroll wheel | Cycle toolbar slots | When not over minimap, not Ctrl |
| `F3` | Toggle WailaPanel | Always |
| `M` | Toggle MiniMap | Always |

`KeyboardCaptured` is true when any modal, settings window, asset spawner,
or text field has focus — gameplay input (movement, camera, hotkeys) is
suppressed while this is true.

---

## 8. Data Flow

```
TimeSystem.Instance
    │
    ▼
HudBindings.Update()
    │
    ├── Tick(Time.deltaTime)  →  TimeSystem advances
    ├── HandleShortcuts()     →  keyboard/mouse input
    ├── _phone.Tick()         →  PhoneController updates
    ├── JobBoard.Tick()       →  Gigs shifts advance
    │
    ├── WriteTime()           →  TimeLineLabel, SpeedStateLabel, SeasonIcon,
    │                            TimelineTrack, WeatherTimelineTrack, CurrentTempLabel
    ├── WriteResources(state) →  ResourceWaterLabel, ResourceElectricityLabel,
    │                            ResourceBandwidthLabel, ResourceFuelLabel, ResourceMoneyLabel
    ├── WriteVitals(state)    →  VitalWellnessFill, VitalStaminaFill,
    │                            VitalThirstFill, VitalHungerFill + percent labels
    └── WriteToolbar(state)   →  ToolbarSlot0-9 icons, counts, selection
```

`HudState.Active` is the singleton data store. `GameSaveManager` serializes
and deserializes it (vitals, resources, toolbar, loan debt, selected slot)
to/from save files.

---

## 9. Save Integration

`GameSaveManager.cs` waits for mods, terrain, player, and HUD to initialize
before loading. It serializes:

- `HudState.Toolbar` (10 slots: IconId + Count)
- `HudState.SelectedSlot`
- `HudState.Vitals` (4 vitals: id + value)
- `HudState.Resources` (5 resources: id + amount)
- `HudState.LoanDebt`

On load, it restores these into `HudState.Active`, which `HudBindings`
then renders on the next `Update()` tick.

---

## 10. Kit Overlay (Optional)

The kit overlay is an optional chrome layer that sits on top of the
existing HUD. Enabled via the `_enableKitOverlay` flag on `HudUIBuilder`
or `HudSceneBootstrap`.

When enabled:
1. `HUDOverlay_kit.uxml` is added as a full-overlay sibling on the
   `UIDocument` root.
2. `HudUI_kit.uss` is added as a sibling style sheet.
3. The existing `HudUI` tree continues to render unchanged below.

The kit brings hand-designed chrome with palette discipline from
`assets/hud_kit/palette.json` and a 16×24 design grid. See
`Resources/HUDTree/Kits/KIT_README.md` for full details.
