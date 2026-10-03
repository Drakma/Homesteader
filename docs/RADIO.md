# Steadify Radio

Steadify (the phone's music app) has a second mode: **Radio**. A station is a short daily programme written from the
game's own facts and read aloud by a text-to-speech voice that runs on the player's machine. The first station is
**Almanac Weather** (88.3 FM): today's weather and temperatures, the three-day outlook, the week ahead, sunrise and
sunset, the moon, and notes on the player's own crops, animals and money.

Everything here is modular: stations are mod data, scripts come from one of two writers, and the voice is a swappable
engine behind one interface.

## How an episode is made

1. **Facts** - `RadioScriptContext.Gather()` (`Assets/Scripts/Radio/RadioScriptContext.cs`) reads the day, the
   almanac's 56-day forecast, the sky, the player's plantings, animals, money and loan, and the unit setting. Both
   writers see only this object; nothing else from the game or the save reaches a script.
2. **Script** - one of two writers produces a `RadioEpisode` (a list of `{speaker, text}` lines):
   - **Almanac writer** (`RadioScriptWriter.cs`, default). Fills the station's sentence banks from the facts. Free,
     offline, deterministic for (world seed, day, station).
   - **Claude writer** (`ClaudeScriptWriter.cs`, Settings > Audio > Radio > Script Writer = Claude). Sends the fact
     sheet and the station's persona to the Claude API (`POST /v1/messages`, model from Settings, default
     `claude-opus-5-5`, low effort, server-side refusal fallbacks on) and parses the JSON dialogue it returns. Needs an
     API key (Settings, or the `ANTHROPIC_API_KEY` environment variable). Any failure falls back to the almanac writer
     for that episode and shows a toast. An episode is a few thousand input tokens and under a thousand output tokens.
3. **Voice** - `RadioPlayer` (`RadioPlayer.cs`) synthesises lines a few ahead of playback on a worker thread through
   `ITtsEngine`. The engine is **Kokoro** via sherpa-onnx (`Tts/KokoroTtsEngine.cs`, P/Invoke in
   `Tts/SherpaOnnxNative.cs`): 24 kHz, 11 English voices, faster than real time on CPU. Without the voice pack the
   transcript still scrolls at reading speed.
4. **Cache** - `<persistentDataPath>/Radio/<station>/<seed>_<day>_<writer>_<units>/` keeps `episode.json` and one WAV
   per line, so a replay, a reload or the next day's rebroadcast is instant and a Claude episode is paid for once.
   "Rewrite" in the Radio tab deletes today's cache and writes again.

When the episode ends the station takes a short break and starts again: the same episode, or a new one once the game
day has turned. Starting a music track turns the radio off and tuning the radio pauses the music.

## Installing the voice pack (once per machine)

```bash
python tools/fetch_tts_runtime.py
```

Downloads the sherpa-onnx Windows libraries (`sherpa-onnx-c-api.dll`, `onnxruntime.dll`, about 7 MB) into
`Assets/Plugins/x86_64/` with plugin-importer meta files, and the `kokoro-multi-lang-v1_0` model (about 350 MB) into
`Assets/StreamingAssets/Tts/`. Both locations are git-ignored. Restart the editor afterwards so it imports the plugins.
`--check` reports what is installed. The struct layout in `SherpaOnnxNative.cs` matches sherpa-onnx v1.13.8; bump the
version in both places together.

Voice ids for the station data (`speakers[].voice`), kokoro-multi-lang-v1_0: 0 af_alloy, 1 af_aoede, 2 af_bella,
3 af_heart, 4 af_jessica, 5 af_kore, 6 af_nicole, 7 af_nova, 8 af_river, 9 af_sarah, 10 af_sky, 11 am_adam, 12 am_echo,
13 am_eric, 14 am_fenrir, 15 am_liam, 16 am_michael, 17 am_onyx, 18 am_puck, 19 am_santa, 20 bf_alice, 21 bf_emma,
22 bf_isabella, 23 bf_lily, 24 bm_daniel, 25 bm_fable, 26 bm_george, 27 bm_lewis (28..52 are Chinese voices). The engine
uses the first installed folder in `KokoroTtsEngine.KnownModelFolders`; `--model` on the fetch script picks another build
(the int8 v0.19 build is small but sounds thin, and v1.1-zh has only three English voices).

## Stations as mod data

A station is a JSON file loaded as mod content type `radio` (core: `assets/_radio/*.json`, packaged to
`mods/homesteader/radio/` by `tools/package_catalog_as_mods.py`). Schema: `assets/_schemas/radio_station.schema.json`.

```json
{ "contents": [ { "type": "radio", "path": "radio/*.json" } ] }
```

Fields: `id`, `name`, `tagline`, `frequency`, `format`, `episode_minutes`, `speakers[]` (`id`, `name`, `voice`,
`speed`, `style`), `persona` (for the Claude writer), `segments[]` (in order) and `lines{}` (sentence banks keyed by
segment). A line starting `{host}:` is spoken by that speaker. Placeholders are filled from the facts; the ones the
almanac writer provides:

| Placeholder | Meaning |
|---|---|
| `{host}`, `{host_name}` (and every speaker id) | speaker tag / display name |
| `{frequency}`, `{station}` | station data |
| `{part_of_day}`, `{weekday}`, `{month}`, `{day_of_month}`, `{ordinal_day}`, `{day_of_year}`, `{season}`, `{season_phrase}` | the day |
| `{weather_now}`, `{weather_now_lower}`, `{high_today}`, `{low_today}` | today |
| `{outlook_phrase}` | the next three days in one sentence |
| `{week_dominant_lower}`, `{week_high}`, `{week_low}`, `{wet_days}`, `{week_note}` | days 1..7 |
| `{frost_day}`, `{frost_low}` | first frost in the coming week (bank `frost` is only used when present) |
| `{sunrise}`, `{sunset}`, `{daylight_hours}`, `{daylight_trend}`, `{moon_phrase}`, `{astro_badge}` | the sky |
| `{crop_count}`, `{crop_word}`, `{crop_top}`, `{crop_nearest_phrase}`, `{planting_hint}` | crops |
| `{animal_phrase}` | "three chickens and a cow" |
| `{money}`, `{loan_phrase}` | the ledger |

Conditional banks the writer looks for: `today_<weather>` (`today_rain`, `today_snow`, ...), `frost`, `moon`, `astro`,
`farm_crops` / `farm_no_crops`, `farm_animals`, `farm_money`, `week_note_wet` / `week_note_dry` / `week_note_cold`.
Temperatures follow the Metric / Imperial setting and are spoken as plain degrees.

## Save game

`GameSave.radioStation` (empty = off), `radioLine`, `radioPaused`; captured and restored through
`RadioPlayer.Capture` / `Restore` (`GameSaveManager`). The episode itself is rebuilt from the cache or the writer.

## Settings

Settings > Audio > Radio: Script Writer (Almanac / Claude), Claude API Key (stored in PlayerPrefs on this machine only;
never written to a save or a mod), Claude Model, and a line reporting whether the voice pack is installed. Radio plays
at the Music level times Master. Reset All Settings resets the writer and model but keeps the key.

## Files

- `Assets/Scripts/Radio/` - `RadioStationDefinition.cs` (+ `RadioRegistry`), `RadioScriptContext.cs`,
  `RadioScriptWriter.cs` (+ `RadioEpisode`, `RadioLine`), `ClaudeScriptWriter.cs`, `RadioPlayer.cs` (+ `RadioWav`),
  `RadioSettings.cs`, `RadioSettingsPanel.cs`, `Tts/ITtsEngine.cs`, `Tts/SherpaOnnxNative.cs`, `Tts/KokoroTtsEngine.cs`
- `Assets/Scripts/UI/Phone/SteadifyRadioPanel.cs`, hooks in `SteadifyApp.cs`
- `Assets/Resources/HUDTree/PhoneUI.uxml` / `.uss` (`SteadifyRadioPane`, `.steadify-mode-*`, `.steadify-radio-*`)
- `Assets/Resources/HUDTree/WelcomeMenu.uxml` (Radio section of the Audio page)
- `Assets/Scripts/Modding/ModManifest.cs`, `ModLoader.cs` (`LoadRadio`), `ModManager.cs` (registry reset)
- `assets/_radio/`, `assets/_schemas/radio_station.schema.json`, `tools/package_catalog_as_mods.py`
- `tools/fetch_tts_runtime.py`

## Known limits

- English voices only are used; the v1.0 model also carries Chinese voices if a station ever wants them.
- One native synthesis at a time; a long line can take a second or two before the first episode starts. Lines are
  cached, so only a first listen waits.
- The Claude writer trusts the model to stay inside the fact sheet; the system prompt forbids invention and the
  transcript is shown so the player can see what was said.
