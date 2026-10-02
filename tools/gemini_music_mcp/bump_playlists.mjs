// Tops every Steadify playlist up to TARGET tracks by talking to the gemini-music MCP
// server directly over stdio (avoids the app's ~2-minute MCP call timeout).
// Output goes straight into Resources/Audio/Music/<Playlist>/ (the folders the
// AudioManager reads). A playlist that already has TARGET .mp3 files is skipped;
// a track whose .mp3 already exists is skipped, so the script is safe to re-run.
//
// Run: node bump_playlists.mjs            (all playlists)
//      LIMIT=1 node bump_playlists.mjs    (smoke test: stop after one track)
//      ONLY=Grunge,Punk node bump_playlists.mjs
import { spawn } from 'node:child_process';
import { existsSync, readdirSync, mkdirSync, appendFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const MUSIC = 'C:/Users/casey/Desktop/Homesteader/Homesteader/Assets/Resources/Audio/Music';
const LOG = path.join(here, 'bump_playlists.log');
const TARGET = 10;
const DURATION = 120;

// No artist or band names anywhere in these prompts (docs/MUSIC_SOURCES.md).
const playlists = {
  LoFiBeats: [
    ['Dusty_Window_Light', 'Lo-fi hip hop instrumental, 74 BPM: dusty vinyl crackle, warm Rhodes chords, soft boom-bap drums, round upright bass, slow sunlit morning in a farmhouse kitchen mood.'],
    ['Coffee_Steam', 'Mellow lo-fi beat, 72 BPM: muted felt piano, tape hiss, lazy swung drums, gentle sub bass, a short wistful melodica line, quiet first-cup-of-coffee feeling.'],
    ['Porch_Swing_Loop', 'Chillhop instrumental, 78 BPM: warm electric piano, soft brushed snare, plucked nylon guitar, light vinyl noise, slow creaking porch swing in the afternoon mood.'],
    ['Woodstove_Warmth', 'Cozy lo-fi hip hop, 70 BPM: crackling fire texture, soft jazzy minor-seventh chords, head-nodding drums, warm bass, mellow clarinet touches, winter cabin evening.'],
    ['Seed_Catalog', 'Dreamy lo-fi instrumental, 76 BPM: tape-warped keys, soft pads, slow swing drums, gentle flute melody, hopeful planning-the-garden-in-spring mood.'],
    ['Laundry_Line', 'Breezy lo-fi beat, 80 BPM: bright clean guitar plucks, soft shaker, warm Rhodes, relaxed drums, white sheets drying in the summer wind feeling.'],
    ['Attic_Rain', 'Rainy-day lo-fi instrumental, 68 BPM: soft rain ambience, muted piano, slow drums, deep double bass, nostalgic and still, rain on an attic roof.'],
    ['Barn_Cat_Nap', 'Playful mellow lo-fi, 74 BPM: bouncy muted keys, soft vinyl crackle, light boom-bap, warm bass, sleepy afternoon in the hay loft mood.'],
    ['Lantern_Walk', 'Night-time lo-fi hip hop, 70 BPM: dark warm pads, soft piano, slow dusty drums, round bass, crickets very quiet in the background, lantern walk to the barn mood.'],
    ['Last_Light_Fence', 'Golden-hour lo-fi instrumental, 73 BPM: wistful electric piano, soft tape saturation, gentle drums, mellow synth lead, end-of-day satisfaction leaning on a fence.'],
  ],
  LoFiMeadow: [
    ['Clover_Hum', 'Soft pastoral lo-fi instrumental, 72 BPM: airy pads, gentle fingerpicked acoustic guitar, brushed drums, warm bass, bees and summer meadow calm.'],
    ['Creekside_Stones', 'Mellow lo-fi beat, 70 BPM: light running-water ambience, soft felt piano, slow drums, round bass, peaceful creekside afternoon.'],
    ['Wildflower_Breeze', 'Bright gentle lo-fi, 78 BPM: shimmering Rhodes, plucked nylon guitar, soft shaker and brushed snare, open wildflower meadow in the wind mood.'],
    ['Butterfly_Path', 'Light dreamy lo-fi instrumental, 76 BPM: music-box style keys, soft pads, slow swing drums, warm sub bass, drifting lazily across a meadow feeling.'],
    ['Tall_Grass_Drowse', 'Sleepy lo-fi beat, 66 BPM: hazy tape-warped piano, slow heavy drums, deep warm bass, cicada hum very quiet, lying in tall grass at noon.'],
    ['Dandelion_Clock', 'Gentle lo-fi instrumental, 74 BPM: soft glockenspiel touches, warm electric piano, relaxed drums, light vinyl crackle, blowing dandelion seeds mood.'],
  ],
  LoFiHarvest: [
    ['Orchard_Ladder', 'Warm autumn lo-fi hip hop, 76 BPM: mellow Rhodes, soft acoustic guitar, dusty drums, round bass, crisp apple-picking afternoon feeling.'],
    ['Pumpkin_Rows', 'Cozy lo-fi beat, 72 BPM: warm felt piano, soft clarinet melody, slow boom-bap, tape hiss, October pumpkin patch mood.'],
    ['Corn_Crib_Dusk', 'Golden lo-fi instrumental, 74 BPM: wistful electric piano, soft slide guitar touches, relaxed drums, warm bass, harvest sunset over the fields.'],
    ['Root_Cellar', 'Dark mellow lo-fi, 68 BPM: muted piano in a minor key, slow drums, deep bass, soft vinyl noise, cool quiet root cellar atmosphere.'],
    ['Threshing_Floor', 'Rhythmic lo-fi beat, 82 BPM: woody percussion, warm Rhodes stabs, soft bass, light acoustic guitar, steady satisfying harvest-work groove.'],
    ['Pie_Cooling', 'Sweet lo-fi instrumental, 70 BPM: soft music-box keys, warm pads, gentle drums, round bass, pie cooling on the windowsill feeling.'],
    ['Hayride_Home', 'Gentle lo-fi hip hop, 75 BPM: plucked banjo-like tones kept soft, mellow keys, slow drums, warm bass, hay wagon ride home at dusk.'],
  ],
  LoFiNeon: [
    ['Vending_Machine_Glow', 'Lo-fi instrumental with a synthwave tint, 84 BPM: hazy analog pads, soft retro drum machine, warm sub bass, glowing arpeggio, late-night neon city feeling.'],
    ['Rain_On_Glass', 'Night lo-fi beat, 80 BPM: rain ambience, dark Rhodes chords, soft trap-influenced hats, deep bass, neon reflections in wet streets mood.'],
    ['After_Hours_Diner', 'Smooth lo-fi instrumental, 78 BPM: muted trumpet melody, velvet synth pads, soft drums, warm bass, empty diner under neon lights.'],
    ['Pink_Static', 'Dreamy chillwave lo-fi, 86 BPM: detuned synth chords, tape wobble, soft clap, warm bass, pink and purple haze mood.'],
    ['Subway_Hum', 'Moody lo-fi hip hop, 82 BPM: dark minor keys, low synth drone, crisp minimal drums, deep bass, last train home feeling.'],
    ['Arcade_Carpet', 'Playful retro lo-fi, 90 BPM: chiptune-flavoured lead kept soft, warm pads, relaxed drums, bouncy bass, nostalgic arcade at night.'],
    ['Rooftop_Signal', 'Atmospheric lo-fi instrumental, 76 BPM: wide pads, soft piano, slow drums, sub bass, city skyline from a rooftop at midnight.'],
    ['Taxi_Light_Drift', 'Laid-back lo-fi beat, 84 BPM: hazy electric piano, soft 808-style bass, gentle hats, slow neon taxi ride mood.'],
    ['Blue_Hour_Mall', 'Vaporwave-tinted lo-fi, 72 BPM: slowed dreamy synth chords, soft reverb drums, warm bass, empty mall at blue hour atmosphere.'],
    ['Last_Call_Lights', 'Mellow night lo-fi, 78 BPM: smoky saxophone touches, soft Rhodes, slow drums, deep bass, neon sign flickering off at closing time.'],
  ],
  ModernPop: [
    ['Summer_Chrome', 'Modern pop instrumental, 118 BPM: bright plucky synths, punchy drums, glossy electric piano, airy pads, big catchy chorus hook, sunny road-trip energy, radio-ready mix.'],
    ['Skyline_Heartbeat', 'Modern synth-pop instrumental, 112 BPM: pulsing sidechained pads, crisp claps, deep sub bass, soaring lead melody, nostalgic city-at-night mood.'],
    ['City_Lights', 'Upbeat modern dance-pop instrumental, 124 BPM: four-on-the-floor kick, sparkling arpeggios, warm bass, bright hook, euphoric night-out feeling.'],
    ['Paper_Planes', 'Feel-good modern pop instrumental, 110 BPM: strummed acoustic guitar with synth layers, snapping fingers, punchy drums, big uplifting chorus.'],
    ['Golden_Filter', 'Dreamy modern pop instrumental, 100 BPM: glossy piano chords, soft trap-pop hats, warm bass, airy vocal-style synth lead without words, sunset selfie mood.'],
    ['Weekend_Static', 'Energetic modern electro-pop instrumental, 126 BPM: gritty synth bass, bright stabs, driving drums, anthemic drop, Friday night energy.'],
    ['Soft_Launch', 'Mid-tempo modern pop ballad instrumental, 92 BPM: warm piano, lush pads, deep 808 bass, crisp snare, emotional building chorus.'],
    ['Neon_Confetti', 'Bubbly modern pop instrumental, 120 BPM: playful marimba synths, claps, bouncy bass, bright brass stabs, celebration mood.'],
  ],
  ModernCountry: [
    ['Tailgate_Sunset', 'Modern country instrumental, 104 BPM: twangy electric guitar hooks, acoustic rhythm guitar, live drums with a solid backbeat, warm bass, pedal steel swells, feel-good summer evening mood.'],
    ['Gravel_And_Gold', 'Modern country rock instrumental, 112 BPM: crunchy guitar riff, driving drums, banjo accents, big anthemic chorus, dirt-road energy.'],
    ['Porch_Light_On', 'Mid-tempo modern country ballad instrumental, 84 BPM: fingerpicked acoustic guitar, soft piano, pedal steel, brushed drums, heartfelt and warm.'],
    ['Small_Town_Saturday', 'Upbeat modern country pop instrumental, 120 BPM: bright acoustic strumming, clapping, fiddle hook, punchy drums, hometown festival feeling.'],
    ['Fence_Line_Fire', 'Modern country rock anthem instrumental, 108 BPM: layered electric guitars, stomping drums, warm bass, mandolin flourishes, stadium singalong section.'],
    ['Creek_Water_Cold', 'Laid-back modern country instrumental, 96 BPM: slide guitar, acoustic guitar, easy groove drums, harmonica licks, lazy river afternoon.'],
    ['Diesel_And_Daisies', 'Modern country instrumental with a southern rock edge, 100 BPM: bluesy electric guitar, Hammond organ, live drums, big chorus, highway feeling.'],
    ['Harvest_Moon_Two_Step', 'Modern country two-step instrumental, 116 BPM: walking bass, fiddle and pedal steel trading melodies, snappy drums, barn dance mood.'],
  ],
  SmoothJazz: [
    ['Amber_Guitar_Night', 'Smooth jazz instrumental, 88 BPM: clean warm electric guitar lead, Rhodes comping, soft brushed drums, fretless-style bass, late evening lounge mood.'],
    ['Moonlit_Piano_Lounge', 'Smooth jazz instrumental, 80 BPM: mellow grand piano lead, light drums, upright bass, soft string pads, moonlit hotel lounge feeling.'],
    ['Velvet_Evening', 'Smooth jazz instrumental, 84 BPM: soprano saxophone melody, lush electric piano, gentle groove drums, warm bass, velvet-smooth evening.'],
    ['Harbor_Lights_Bossa', 'Smooth jazz bossa nova instrumental, 110 BPM: nylon guitar, soft flute lead, brushed drums, warm bass, harbor at sunset.'],
    ['Rooftop_Flugelhorn', 'Smooth jazz instrumental, 86 BPM: warm flugelhorn melody, Rhodes chords, light funky drums, round bass, rooftop at dusk.'],
    ['Silk_Road_Groove', 'Mid-tempo smooth jazz funk instrumental, 96 BPM: slap-free fingerstyle bass groove, clean guitar, alto sax lead, tight drums, polished and upbeat.'],
    ['Rainy_Vibraphone', 'Smooth jazz instrumental, 78 BPM: vibraphone lead, soft piano, brushed drums, upright bass, rainy afternoon calm.'],
    ['Candlelight_Tenor', 'Slow smooth jazz instrumental, 72 BPM: breathy tenor saxophone, warm piano, soft drums, deep bass, candlelit dinner mood.'],
  ],
  ClassicRock: [
    ['Highway_Thunder', 'Classic rock instrumental in a 1970s style, 128 BPM: driving overdriven electric guitar riff, live drums with big toms, punchy bass, Hammond organ, guitar solo section, open highway energy.'],
    ['Barnburner_Boogie', 'Classic rock boogie instrumental, 140 BPM: shuffling electric guitars, honky-tonk piano, driving drums, walking bass, barn-party energy.'],
    ['Smoke_On_The_Ridge', 'Heavy classic rock instrumental, 116 BPM: thick fuzz guitar riff, pounding drums, growling bass, organ swells, extended guitar solo.'],
    ['Silver_Pickup', 'Upbeat classic rock instrumental, 132 BPM: jangly rhythm guitar, bright lead guitar hooks, crisp drums, melodic bass, windows-down road trip mood.'],
    ['Thunderhead_Blues', 'Blues rock instrumental, 100 BPM: bluesy bending lead guitar, slow heavy drums, warm bass, Hammond organ, storm rolling in mood.'],
    ['Steel_Town_Anthem', 'Arena classic rock instrumental, 120 BPM: big power chords, stomping drums, soaring guitar melody, piano accents, anthemic chorus.'],
    ['Backwoods_Rambler', 'Southern classic rock instrumental, 110 BPM: twin lead guitars in harmony, slide guitar, driving drums, piano, swampy swagger.'],
    ['Midnight_Freight', 'Dark classic rock instrumental, 124 BPM: chugging palm-muted guitar riff, train-beat drums, deep bass, wailing lead guitar, night train mood.'],
    ['Copper_Sunrise', 'Melodic classic rock ballad instrumental, 76 BPM: clean arpeggiated guitar intro, building drums, warm bass, emotional guitar solo climax.'],
    ['Last_Exit_Riff', 'Hard-driving classic rock instrumental, 136 BPM: fast riffing guitars, cowbell groove, pounding drums, bass locked to the kick, triumphant ending.'],
  ],
  Grunge: [
    ['Flannel_Fog', 'Grunge rock instrumental in a 1990s style, 100 BPM: heavy fuzz-distorted guitar riff, quiet clean verse section then loud distorted chorus, sludgy bass, hard-hitting drums, rainy overcast mood.'],
    ['Rust_And_Static', 'Dark grunge instrumental, 92 BPM: detuned heavy guitars, feedback swells, pounding drums, thick bass, brooding and raw.'],
    ['Basement_Amp', 'Raw grunge rock instrumental, 112 BPM: crunchy power chords, dirty bass, loose energetic drums, garage-recorded feel, loud-quiet-loud dynamics.'],
    ['Grey_Sky_Garage', 'Mid-tempo grunge instrumental, 96 BPM: chorus-effect clean guitar verse, massive distorted chorus, melodic bass line, heavy drums, melancholic.'],
    ['Sludge_Creek', 'Slow heavy grunge instrumental, 80 BPM: downtuned sludgy guitar riff, dragging heavy drums, rumbling bass, feedback-soaked ending.'],
    ['Thrift_Store_Halo', 'Melodic grunge instrumental, 104 BPM: jangly distorted guitars, driving bass, big drums, bittersweet chord progression, anthemic chorus riff.'],
    ['Powerline_Hum', 'Noisy grunge instrumental, 108 BPM: dissonant guitar riff, feedback, punchy bass, aggressive drums, tense and restless.'],
    ['Cold_Coffee_Riot', 'Energetic grunge punk crossover instrumental, 128 BPM: fast fuzzy riffs, driving drums, shouting-style guitar hooks without vocals, raw energy.'],
    ['Overcast_Anthem', 'Big grunge rock anthem instrumental, 98 BPM: wall of distorted guitars, slow heavy groove, melodic lead guitar line, thunderous drums.'],
    ['Wet_Leaves', 'Moody acoustic-to-electric grunge instrumental, 88 BPM: dark acoustic guitar intro building into heavy distorted full-band section, melancholic and raw.'],
  ],
  Punk: [
    ['Three_Chord_Sunrise', 'Fast punk rock instrumental, 180 BPM: buzzsaw distorted power chords, relentless eighth-note bass, driving fast drums, short catchy riff hooks, raw and energetic.'],
    ['Skate_The_Silo', 'Skate punk instrumental, 190 BPM: fast palm-muted guitar riffs, melodic lead guitar hooks, rapid drums with fills, bouncing bass, sunny high energy.'],
    ['Chicken_Wire_Fence', 'Garage punk instrumental, 170 BPM: trashy distorted guitars, pounding simple drums, driving bass, shout-along style riff energy, raw lo-fi production.'],
    ['Mohawk_Mower', 'Hardcore punk instrumental, 200 BPM: fast aggressive power chords, blasting drums, thick bass, breakdown section, loud and tight.'],
    ['Pogo_In_The_Pasture', 'Pop punk instrumental, 175 BPM: bright crunchy guitars, melodic hooks, punchy drums, octave guitar lead, upbeat and fun.'],
    ['Spray_Paint_Barn', 'Street punk instrumental, 165 BPM: chunky distorted guitars, gang-chant style guitar stabs, stomping drums, driving bass, defiant energy.'],
    ['Safety_Pin_Sky', 'Classic 1977-style punk rock instrumental, 160 BPM: raw jangly distorted guitars, simple fast drums, melodic bass, short sharp riffs.'],
    ['Combat_Boots_Mud', 'Oi-style punk instrumental, 150 BPM: big marching power chords, stomping drums, singalong-style guitar melody, thick bass.'],
    ['Duct_Tape_Dreams', 'Melodic punk instrumental, 185 BPM: fast skate-punk riffs, soaring twin-guitar harmony, rapid drums, bouncy bass, triumphant chorus riff.'],
    ['Last_Bus_Riot', 'Fast punk rock instrumental, 178 BPM: driving buzzsaw guitars, pounding drums, rolling bass, breakneck energy, abrupt tight ending.'],
  ],
};

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  appendFileSync(LOG, line + '\n');
}

function mp3Count(dir) {
  if (!existsSync(dir)) return 0;
  return readdirSync(dir).filter((f) => f.toLowerCase().endsWith('.mp3')).length;
}

let idc = 0;
const pending = new Map();
const proc = spawn('node', [path.join(here, 'index.js')]);
let buf = '';
proc.stdout.on('data', (d) => {
  buf += d;
  let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i); buf = buf.slice(i + 1);
    if (!line.trim()) continue;
    let msg; try { msg = JSON.parse(line); } catch { continue; }
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  }
});
proc.stderr.on('data', (d) => log('server stderr: ' + String(d).trim().slice(0, 300)));
proc.on('exit', (c) => log('server exited ' + c));

function call(method, params, timeoutMs) {
  return new Promise((resolve, reject) => {
    const id = ++idc;
    const t = setTimeout(() => { pending.delete(id); reject(new Error('rpc timeout')); }, timeoutMs);
    pending.set(id, (msg) => { clearTimeout(t); resolve(msg); });
    proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
  });
}

async function main() {
  await call('initialize', { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'playlist-bump', version: '1.0' } }, 20000);
  proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');

  const only = (process.env.ONLY || '').split(',').map((s) => s.trim()).filter(Boolean);
  const limit = Number(process.env.LIMIT || 0);
  let generated = 0, failed = 0, quotaHit = false;
  const failures = [];

  const genOne = async (playlist, filename, prompt) => {
    const dir = path.join(MUSIC, playlist);
    mkdirSync(dir, { recursive: true });
    log(`GEN ${playlist}/${filename} (${mp3Count(dir)}/${TARGET} in folder)`);
    try {
      const res = await call('tools/call', {
        name: 'gemini_music_generate',
        arguments: { prompt, output_dir: dir, filename, duration_seconds: DURATION, timeout_seconds: 400 },
      }, 480000);
      const txt = String(res?.result?.content?.[0]?.text ?? JSON.stringify(res));
      if (/^(Error|Not signed in|No track)/.test(txt) || !existsSync(path.join(dir, filename + '.mp3'))) {
        log(`FAIL ${playlist}/${filename}: ${txt.slice(0, 240).replace(/\n/g, ' ')}`);
        return false;
      }
      log(`OK ${playlist}/${filename}: ${txt.slice(0, 120).replace(/\n/g, ' ')}`);
      return true;
    } catch (e) {
      log(`FAIL ${playlist}/${filename}: ${e.message}`);
      return false;
    }
  };

  outer:
  for (let attempt = 0; attempt < 2; attempt++) {
    for (const [playlist, tracks] of Object.entries(playlists)) {
      if (only.length && !only.includes(playlist)) continue;
      const dir = path.join(MUSIC, playlist);
      for (const [filename, prompt] of tracks) {
        if (mp3Count(dir) >= TARGET) break;
        if (existsSync(path.join(dir, filename + '.mp3'))) continue;
        const ok = await genOne(playlist, filename, prompt);
        if (ok) generated++; else { failed++; failures.push(`${playlist}/${filename}`); }
        if (quotaHit) break outer;
        if (limit && generated + failed >= limit) { log(`LIMIT reached (${limit}) - stopping`); break outer; }
      }
    }
    if (attempt === 0) log('PASS 1 done - second pass picks up anything still short');
  }

  const summary = Object.keys(playlists)
    .map((p) => `${p}=${mp3Count(path.join(MUSIC, p))}`).join(' ');
  log(`ALL DONE generated=${generated} failed=${failed}${quotaHit ? ' quota-limit-reached' : ''} counts: ${summary}`);
  if (failures.length) log('Unresolved: ' + failures.join(', '));
  proc.kill();
  process.exit(0);
}

main().catch((e) => { log('FATAL ' + e.message); proc.kill(); process.exit(1); });
