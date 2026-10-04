# Music sources and licence log

How music gets into the game, and what to record so it can be used commercially.

## Sources, in order of preference

1. **Our own generative music** (code-built, nothing to license) for the ambient bed.
2. **CC0 / public domain recordings** (Musopen, Internet Archive, OpenGameArt CC0).
3. **CC-BY tracks**, with the credit listed in the credits file.
4. **Gemini (Lyria) tracks** made with the `gemini-music` tool, only while signed in to a PAID Gemini plan (AI Plus, Pro or
   Ultra). Keep the sidecar JSON for each track.

Not allowed: anything from Epidemic Sound (its standard licence does not cover games), or tracks that imitate a named artist.

## The gemini-music tool

`tools/gemini_music_mcp/index.js` (registered as `gemini-music` in `.mcp.json`; restart the session to load it).

- `gemini_music_login`: opens its own browser profile (`~/.codegpt/gemini-music-session`) at Gemini. Sign in once, with the
  account that has the paid plan. It cannot share the image tool's profile (two browsers cannot use one profile).
- `gemini_music_generate(prompt, output_dir, filename, duration_seconds?, timeout_seconds?)`: asks Gemini for an instrumental track
  and saves `<filename>.mp3` plus `<filename>.json` (prompt, time, hash, licence note). Takes 30 to 180 seconds.
  The tool ALWAYS adds two instructions to the prompt, because Gemini needs them: "instrumental only, no vocals" and "starts and
  stops within X seconds, with a definite ending and no fade-out" (X = `duration_seconds`, default 90, minimum 60, maximum 120). Without the second one a track just stops
  mid-song.
- `gemini_music_inspect`: dumps the page's buttons, audio elements and text and a screenshot, for re-tuning the selectors
  when Google changes the page. The download step tries the page's Download control first, then the audio element.

Save tracks under `Homesteader/Assets/Resources/Audio/Music/<PlaylistName>/` (the AudioManager builds one playlist per folder;
folder names are listed in `Resources/Audio/Music/playlists.txt`). Each playlist has a 256x256 cover at
`Resources/Audio/Covers/<PlaylistName>.png`.

## Topping playlists up in bulk

`tools/gemini_music_mcp/bump_playlists.mjs` holds a prompt list per playlist and generates until every folder has 10 tracks.
It talks to the MCP server over stdio (no 2-minute app timeout), skips tracks that already exist and can be re-run safely:

    node tools/gemini_music_mcp/bump_playlists.mjs          # everything
    ONLY=Grunge,Punk node tools/gemini_music_mcp/bump_playlists.mjs
    LIMIT=1 node tools/gemini_music_mcp/bump_playlists.mjs  # smoke test

Gemini has a daily music-generation quota. When Gemini's latest reply says the limit is reached the server stops at once
and the script aborts its run; `retry_bump.ps1` re-runs it every hour (up to 24 hours) until every folder is full.
Progress is in `tools/gemini_music_mcp/bump_playlists.log`.

Two lessons from 2026-10-02: the quota check must read only Gemini's latest reply (the sidebar lists old chat titles such as
"Music Generation Limit Reached", and a whole-page scan matched them and aborted runs that would have worked), and the tool
now drives the installed Google Chrome (`channel: 'chrome'`) because Playwright's bundled Chromium kept closing mid-generation.
`GEMINI_MUSIC_CHANNEL=chromium` switches back. Headless is refused by Gemini ("An error occurred while generating the track")
and an occluded or tiny window stalls the player, so the window opens visible on the left monitor (`GEMINI_MUSIC_WINDOW_POS`).

If Chrome starts crashing the instant the Download button is clicked (Crashpad dumps in the profile's `Crashpad/reports`),
the profile's download database is corrupt from a force-kill mid-download: stop everything and delete
`~/.codegpt/gemini-music-session/Default/History`, `History-journal` and `DownloadMetadata` (sign-in survives). Never
force-kill the tool's Chrome while a download is in flight.

## Loopable beds (menu / intro music)

`gemini_music_generate` takes `loop: true`, which swaps the standing "clear beginning, definite ending" text for a request
for one steady texture with no intro, no ending and no fades. `tools/gemini_music_mcp/gen_loop.mjs` uses it and then makes
the result loop seamlessly: it trims 5 s from each end and crossfades the last 8 s into the first 8 s (equal power), so the
final sample flows into the first one.

    node tools/gemini_music_mcp/gen_loop.mjs Intro_Serene_Dawn "<prompt>" 120

Output is a WAV in `Homesteader/Assets/Resources/Audio/Intro/` with its licence sidecar; the source MP3 stays in
`tools/gemini_music_mcp/raw/`. WAV on purpose: MP3 carries encoder padding that leaves a small gap at the loop point, and
this machine's ffmpeg has no Ogg Vorbis encoder. Unity compresses the WAV on import (set Load Type to Streaming or
Compressed In Memory). The folder is not listed in `playlists.txt`, so these never show up in Steadify.

## Per-track checklist

- Fill `gemini_plan` in the sidecar JSON with the plan that was active when it was generated.
- Listen to the whole track for stock-library artifacts (a spoken "Purchase your track today"); delete the track if present.
- No artist names in the prompt.
- Tracks carry Google's SynthID watermark and are probably not copyrightable: we hold a licence to use them, not exclusivity.
- Keep the sidecar next to the audio file, including in any packaged mod.

Sources for the licence position (secondary, not Google's own text): Rights Docket on Lyria 3 commercial use and Soundstock on
Lyria 3.5 in the Gemini app. Re-read Google's current Terms of Service before shipping.
