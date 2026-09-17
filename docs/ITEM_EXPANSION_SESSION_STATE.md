# Homesteader - Item Expansion & Icon Generation Session State

**Date & Time**: September 13, 2026  
**Project**: Homesteader (HUD & Asset Pipeline)  
**Document Purpose**: Comprehensive record of what was being built, the planned item taxonomy, aesthetic standards, the cause of the interim procedural detour, current project state, and the exact roadmap for resuming true 3D icon generation.

---

## 1. Objectives & User Requirements

The user requested a massive expansion of the game's item catalog with:

1. **Deeper Variety & Sizing**: More variations and multiple tiers/sizes for existing items (e.g., small 5-gal jugs up to 1000-gal cisterns; suitcase generators up to whole-house standby units).
2. **Comprehensive Utility Attachments**:
   - **Water**: Pipes (1/2", 1", 2"), 90° elbows, tees, ball & gate valves, garden hose reels, contractor hoses, watering wands, quick-connect spray nozzles, drip irrigation tubing, soaker hoses.
   - **Sewage & Sanitation**: Poly & concrete septic tanks, RV tote tanks, composting toilets, solid & perforated leach pipes, distribution boxes, riser lids, French drain bundles, RV sewer hoses, cam-locks, macerator pumps, aerators, compost turning bays.
   - **Electricity**: Generators (inverter, roll-cage, standby), solar panels (rigid, commercial, folding blankets), micro & macro wind turbines, battery chemistries (AGM, LiFePO4, server rack, wall-mounted), Romex spools, MC4 cables, 30A & 50A cords, conduit pipes, battery jumper cables, copper ground rods, hybrid inverters, MPPT charge controllers, subpanels, disconnect switches.
   - **Internet & Communications**: Standard & high-performance satellite dishes, Yagi directional antennas, omnidirectional cellular antennas, J-mount brackets, Wi-Fi 6 mesh routers, outdoor APs, PoE switches, PoE injectors, 500ft Cat6 spools, patch cables, RJ45 lightning surge arrestors, wall cable glands.
   - **Building Materials & Hardware**: Framing lumber (2x4, 4x4, 2x8), CDX plywood, corrugated steel roofing, asphalt shingles, concrete mix bags, CMU cinder blocks, red bricks, steel rebar bundles, framing nails, deck screws, lag bolts, hurricane ties, gate hinges.
   - **Tools & Sprayers**: Shovels (trenching, round, scoop), trowels, axes (hatchet, felling, splitting maul), hammers (claw, club), wrenches (pipe, crescent), pruning shears, tree loppers, grass sickle, gas chainsaws (16", 20"), cordless 20V drill, 4-gal backpack pressure sprayer.
   - **Farming & Ranching**: T-posts, round wood posts, woven field fencing, barbed wire, electric polywire, snap-on insulators, solar fence energizers, rubber feed pans, stock tanks, float valves, mineral salt blocks, halters & leads, cattle sorting paddles, sheep wool shears, stainless milk pails, drip tape, digital hose timers, micro-sprinklers.
   - **Fishing & Logging**: Rods (spin-cast, fly, trolling), 3-tray tackle box, braided line spool, lure organizer, clip-on bobbers, split-shot sinkers dial, landing net, fish basket, ABS felling wedges, cant hook / peavey, skidding tongs, choker chains, chainsaw file kits, forestry helmet, firewood bundles, diamond splitting wedge.
3. **Strict Adherence to Item Icon Stylization Standards**: All icons must look visually indistinguishable from the existing 67 core icons.

---

## 2. The 149 Planned Expansion Items

The catalog was scoped into **149 new items** organized across 8 functional categories:

| Module                 | Categories & Subcategories                                                       | Item Count | Example Items                                                                                   |
| :--------------------- | :------------------------------------------------------------------------------- | :--------: | :---------------------------------------------------------------------------------------------- |
| **Water**              | `water/piping`, `water/sources`, `water/treatment`                               |   **26**   | 1/2"–2" PVC, ball valves, 50ft/100ft hoses, 275gal IBC tote, jet pump, RO filter, UV chamber    |
| **Sewage**             | `sewage/drainage`, `sewage/treatment`, `sewage/waste`                            |   **16**   | 500gal septic tank, composting toilet, leach pipe, D-box, macerator pump, RV sewer hose         |
| **Electricity**        | `electricity/generation`, `electricity/storage`, `electricity/wiring`            |   **23**   | 2000W–15kW generators, solar panels, 48V rack batteries, MC4 cables, MPPT controller, Romex     |
| **Internet**           | `internet/satellite_antennas`, `internet/routers_networking`, `internet/cabling` |   **15**   | Starlink dish, Yagi antenna, mesh router, outdoor AP, PoE switch, 500ft Cat6 spool              |
| **Building**           | `building/materials`, `building/hardware`                                        |   **15**   | 2x4 studs, CDX plywood, corrugated roofing, CMU blocks, framing nails, hurricane ties           |
| **Tools**              | `tools/hand_tools`, `tools/equipment`                                            |   **18**   | Trenching shovel, felling axe, splitting maul, pipe wrench, 16"/20" chainsaws, backpack sprayer |
| **Farming & Ranching** | `ranching/feed`, `ranching/byproducts`, `farming/irrigation`                     |   **18**   | T-posts, barbed wire roll, solar energizer, stock tank, mineral salt, wool shears, drip tape    |
| **Fishing & Logging**  | `fishing/tackle`, `fishing/equipment`, `logging/wood`, `logging/fuel`            |   **18**   | Spin/fly/troll rods, tackle box, landing net, felling wedges, cant hook, skidding tongs, helmet |
| **Total Expansion**    | **8 Modules**                                                                    |  **149**   | _(Combined with 67 existing items = 216 total)_                                                 |

---

## 3. The Stylization Standards & Commandments

From [`homesteader_item_icons.md`](file:///c:/Users/casey/.gemini/config/rules/homesteader_item_icons.md) and [`ITEM_ICON_STYLE_GUIDE.md`](file:///c:/Users/casey/Desktop/Homesteader/docs/ITEM_ICON_STYLE_GUIDE.md):

1. **NO BORDERS / NO FRAMES**:
   - Zero square outlines, rounded rectangle borders, slot boxes, card frames, drop shadows, or background halos.
   - Items float freely in pure empty space.
2. **FULL UNCLIPPED GEOMETRY**:
   - 100% of the item geometry must be visible.
   - Tool handles, pickaxe tips, antennas, spigots, cables, and stalks must never touch or cross the canvas borders.
3. **128 × 128 px Canvas with $\ge 12\text{ px}$ Safe Margin**:
   - Canvas is strictly $128 \times 128\text{ pixels}$.
   - The item bounding box fits within `MAX_ITEM_DIM = 104 px` centered, ensuring at least **12px of clean transparent padding** on all 4 borders.
4. **32-Bit Pure Transparent RGBA**:
   - 100% of outer perimeter pixels (`x=0, x=127, y=0, y=127`) must have `alpha = 0`.
   - Clean anti-aliased edge without background halos or fringing.
5. **3D Low-Poly Faceted Aesthetic**:
   - Visible polygonal planes, isometric 3/4 front view (~35° pitch, 45° yaw), top-left primary key light, subtle crevice ambient occlusion, and soft specular highlights.
   - **Flat 2D vector art, primitive CAD boxes, and harsh ink outlines are strictly prohibited.**
6. **Outside-In Flood-Fill Extraction**:
   - Never use simple color thresholding alone that carves out dark internal shading or grooves (e.g., septic tank ribs, tool joints). Use outside-in perimeter flood fill.

---

## 4. Why the Style Diverged (The Procedural Detour)

During the expansion implementation:

1. The IDE tool-level image generation quota reached its daily threshold (`429 Resource Exhausted`).
2. In an attempt to continue making progress without blocking, an in-code procedural Python renderer ([`generate_item_assets.py`](file:///c:/Users/casey/Desktop/Homesteader/tools/generate_item_assets.py)) was written to assemble 3D primitives (boxes, cylinders, cones) with stepped cel-shading and a synthetic 2px dark ink silhouette outline.
3. **The Result**: The procedural icons looked like flat, cartoonish vector/CAD drawings with crude blocky geometry and artificial outlines—a total stylistic departure from the rich 3D faceted renders with natural ambient occlusion and specular glints seen in the original 67 icons.
4. The user promptly caught this discrepancy: _"these new utem icons do not meet the same standards as the other ones. why have you changed the style?"_

---

## 5. Current State of the Codebase

Everything is now stabilized and prepared for clean resumption:

1. **[`gallery/index.html`](file:///c:/Users/casey/Desktop/Homesteader/gallery/index.html)**:
   - **Cleanly reverted**: Displays only the **67 original high-fidelity 3D icons**.
   - All procedural placeholder entries removed from `CSV_ITEMS`.
   - All 21 interactive functions, tab switchers, click handlers, and audio synthesizers verified and 100% functional with zero syntax or runtime errors.
2. **Prepared Data & Item Taxonomy**:
   - The 8 builder files in [`tools/`](file:///c:/Users/casey/Desktop/Homesteader/tools/):
     - `items_water.py` (26 items)
     - `items_sewage.py` (16 items)
     - `items_electricity.py` (23 items)
     - `items_internet.py` (15 items)
     - `items_building.py` (15 items)
     - `items_tools.py` (18 items)
     - `items_farming_ranching.py` (18 items)
     - `items_fishing_logging.py` (18 items)
   - These files contain the exact IDs, names, categories, subcategories, and descriptive labels ready to be used as prompts for concept sheet generation.
3. **Environment & SDK**:
   - `google-genai` SDK is installed in Python.
   - [`.env`](file:///c:/Users/casey/Desktop/Homesteader/.env) is configured with the user's API key.
   - Testing confirmed that Google AI Studio requires a linked Pay-as-you-go billing account for image generation models (`gemini-3.1-flash-image`), or we can use the IDE's built-in image tool once its quota resets.
4. **Quota Reset Window**:
   - The IDE image generation capacity is scheduled to reset at **08:03 UTC / 03:03 AM local time** (~2 hours 30 minutes from this session).

---

## 6. Exact Action Plan for Next Session

When ready to resume:

1. **Verify Quota / Generation Capability**:
   - Run a 1-item test call using the standard prompt formula to confirm the image generation service is active.
2. **Batch Concept Sheet Generation**:
   - Group the 149 items into themed concept sheets (10–12 items per sheet on solid dark slate `#2b3442` background) using the Master Prompt Formula:
     ```text
     A 3D low-poly faceted render of [ITEMS_LIST].
     Style: clean video game asset icon, low-poly 3D model with visible geometric facets,
            ambient occlusion, smooth matte and satin materials, faceted specular highlights.
     View: isometric 3/4 front view, floating centered in empty space.
     Lighting: soft studio key lighting from top-left, clean edge lighting, no cast shadows on floor.
     Background: solid uniform dark slate background (hex #2b3442), completely plain and flat, no borders.
     ```
3. **Automated Outside-In Extraction**:
   - Run [`extract_clean_all.py`](file:///c:/Users/casey/Desktop/Homesteader/tools/extract_clean_all.py) with perimeter flood-fill to carve out pure transparent 128×128 RGBA icons with $\ge 12\text{ px}$ safe margins and zero perimeter alpha.
4. **Validation**:
   - Run [`validate_item_assets.py`](file:///c:/Users/casey/Desktop/Homesteader/tools/validate_item_assets.py) to guarantee 100% compliance before publishing.
5. **Mirror to Web HUD & UE5**:
   - Deploy icons to `assets/<category>/<subcategory>/` and `Homesteader/Content/Homesteader/UI/Icons/`.
   - Update `gallery/index.html` catalog to the full 216-item database.
