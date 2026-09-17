# Large Metal Garage - Walls

**ID**: `struct_walls_large_metal_garage`  
**Category**: `structures`  
**Growth Stage**: 3 of 4 (`walls`)  

## Description
Light-gray corrugated aluminum exterior siding panels installed on steel framing with roll-up door opening, open roof trusses awaiting roofing.

## Specifications
- **Dimensions**: 9.0m (W) x 12.0m (D) x 4.5m (H)
- **Weight**: 7800.0 kg
- **Base Value**: $12,000.00

## 4-Stage Construction Lifecycle
1. **Foundation**: `struct_foundation_large_metal_garage` (0-33%)
2. **Framing**: `struct_framing_large_metal_garage` (33-66%)
3. **Walls**: `struct_walls_large_metal_garage` (66-99%)
4. **Complete**: `struct_complete_large_metal_garage` (99-100%)

## ⚠️ Pending: construction_recipe / required_tools

Left as empty arrays (schema-valid but not yet populated) because this is a genuinely all-metal building and the catalog currently has no steel-frame or metal-siding building materials - only `roofing_steel_corrugated` exists. Three new items are queued in `assets/_asset_requests/pending/`: `1789520000_steel_stud_framing`, `1789520001_steel_frame_beam`, `1789520002_steel_siding_corrugated`. Fill in this stage's recipe once those exist, following the barn's per-stage recipe pattern (foundation=concrete/rebar, framing=structural members, walls=siding+rough-in wiring/plumbing, complete=roofing+doors/glass).
