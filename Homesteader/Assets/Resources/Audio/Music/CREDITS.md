# Music Track Credits

## LoFiBeats Playlist

| File | Title | Source | Licence |
|---|---|---|---|
| `LoFiBeats/Music_HomesteadMorning.mp3` | Homestead Morning | Generated with Google Gemini (Lyria) | Generated on a paid Gemini plan; see `Music_HomesteadMorning.json` for the prompt, date and licence notes. Contains Google's SynthID watermark. |

## All other playlists (LoFiMeadow, LoFiHarvest, LoFiNeon, ModernPop, ModernCountry, SmoothJazz, ClassicRock, Grunge, Punk)

Every track in these folders was generated with Google Gemini (Lyria) on a paid Gemini plan, via `tools/gemini_music_mcp`
(`bump_playlists.mjs` holds the prompts). The `.json` sidecar next to each `.mp3` is its licence record. Tracks without a
sidecar predate the sidecar step and were generated the same way.

Each generated track keeps its `.json` sidecar (prompt, time, hash, licence note). See `docs/MUSIC_SOURCES.md`.
Any CC-BY track added later must be credited here and in the game's credits screen.
