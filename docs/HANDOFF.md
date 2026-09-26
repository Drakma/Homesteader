# Handoff (2026-09-26)

## State
Branch main, last commit 2ab0bde9. Uncommitted work: mini-map and its supporting edits. Commit only when the user asks.

## In flight: mini-map (`Homesteader/Assets/Scripts/UI/MiniMap.cs`)
- Lower right, M toggles, flat isometric colour map, drag to move, wheel to zoom, size/position/zoom remembered (PlayerPrefs `Homesteader.MiniMap.`).
- Chunked colour cache (`Prefetch`, 16x16 cell chunks, 1.6x margin), lattice-snapped recentre, sub-pixel plane slide, overlay composed at 2 Hz.
- Dots: faint yellow player, white docile animals, red aggressive (`AnimalBrain.All`, `IsAggressive`). Lights show only a dot of the light colour.
- LAST CHANGE (unverified, not compiled): resize handle removed; 4 faint black shadow layers under the plane (per-layer alpha 0.11, raised from 0.07); resize is now Shift + wheel over the map. `docs/CONTROLS.md` updated.
- NEXT: compile directly (no wait loops, no scheduler; the Unity MCP bridge drops during reload, "Unity not detected" is expected then), then check in game: smooth scroll, fps, dots, shadow, Shift+wheel resize.

## Other uncommitted edits
`AnimalBrain.cs` (registry, IsAggressive), `HudBindings.cs` (wheel gated by `!MiniMap.PointerOver`), `LightEmitter.cs` (Glow), `IsometricLockedCamera.cs` (clipping, zoom gate), `docs/CONTROLS.md`.

## Open items
- Power system: user says the game has one; `LightEmitter.PowerCheck` is unset, class not located.
- Save game does not include animals.
- Dog clips have short strides; farmer run stretch used `--swing 1.45`.
- Older kit labels may still contain emoji (user's "yes" was ambiguous; not acted on).
- Kit server has no no-cache header (stale page until hard refresh).

## Standing rules
No emoji anywhere. Terse replies. Meshy-only, lowpoly, under 5,000 tris, GLB. Spend approvals via kit app `/api/request-approval`. Gait-match rigs with `tools/gait_fix.py`. Check `docs/CONTROLS.md` before assigning keys. New world/player state goes in the save game. Editor/schema/server/template changes stay in sync.
