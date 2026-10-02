// Generates the three Homesteader playlists by talking to the gemini-music MCP
// server directly over stdio (avoids the app's ~2-minute MCP call timeout).
// Run: node gen_playlists.mjs
import { spawn } from 'node:child_process';
import { existsSync, writeFileSync, appendFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const AUDIO = 'C:/Users/casey/Desktop/Homesteader/Homesteader/Assets/Audio/Playlists';
const LOG = path.join(here, 'gen_playlists.log');

const playlists = {
  HomesteaderChill: [
    ['hc_01_sunrise_porch', 'Lo-fi hip hop instrumental, mellow and warm: dusty vinyl crackle, soft electric piano chords, laid-back boom-bap drums around 75 BPM, gentle upright bass. Peaceful early-morning farm feeling.'],
    ['hc_02_hammock_grove', 'Relaxed lo-fi instrumental: mellow Rhodes piano, soft brushed drums, warm tape saturation, light acoustic guitar plucks, lazy summer afternoon under the trees mood, 70 BPM.'],
    ['hc_03_rain_on_tin', 'Cozy lo-fi instrumental with a rainy-day mood: rain ambience, soft muted piano, jazzy minor-7th chords, slow head-nodding drums, gentle double bass, umbrella-on-porch feeling.'],
    ['hc_04_greenhouse_hum', 'Dreamy lo-fi instrumental: lush warm pads, soft tape-warped keys, slow swing drums, mellow flute melody, humid green greenhouse atmosphere, peaceful and floating.'],
    ['hc_05_evening_harvest', 'Warm nostalgic lo-fi instrumental: wistful electric piano, soft vinyl noise, dusty drum loop around 72 BPM, mellow synth lead, golden-hour end-of-day satisfaction mood.'],
    ['hc_06_cider_and_blankets', 'Hygge lo-fi instrumental: crackling fireplace texture, soft felt piano, gentle lo-fi drums, warm bass, mellow clarinet touches, cozy autumn evening indoors feeling.'],
  ],
  ModernHomesteading: [
    ['mh_01_golden_hour_drive', 'Lo-fi instrumental remix styled like a modern synth-pop radio hit: dreamy synth arpeggios, punchy soft drums around 100 BPM, glossy electric piano chords, airy pads, catchy melancholic lead melody, nostalgic sunset drive feeling.'],
    ['mh_02_city_to_country', 'Chill lo-fi take on a modern dance-pop track: four-on-the-floor soft kick, bright plucky synths, warm sub bass, sparkly hats around 110 BPM, hopeful uplifting mood, fresh-start morning energy.'],
    ['mh_03_neon_barn_lights', 'Lo-fi instrumental in the style of a moody modern alt-pop song: dark rounded synth bass, hazy pads, crisp minimal drums at 95 BPM, wistful piano hook, night-time neon glow over fields feeling.'],
    ['mh_04_sunroom_dance', 'Bouncy lo-fi pop instrumental: playful marimba-like synth plucks, snapping fingers, soft claps, groovy bassline around 105 BPM, sunny joyful vibe, modern pop chorus energy without vocals.'],
    ['mh_05_late_night_stream', 'Smooth lo-fi future-pop instrumental: velvet pads, muted trumpet melody, deep soft sub bass, laid-back trap-influenced hats at 85 BPM, intimate late-night headphones mood.'],
    ['mh_06_graptopia', 'Feel-good lo-fi pop instrumental: shimmering guitar arpeggios, airy synth swells, crisp modern drums around 98 BPM, singalong-style wordless lead melody (instrumental only), bright festival-on-the-farm energy.'],
  ],
  FarmCountry: [
    ['fc_01_dirt_road_dawn', 'Lo-fi country-style instrumental: laid-back acoustic guitar strumming, gentle banjo rolls, soft lo-fi drums with a country shuffle around 80 BPM, warm pedal steel-like slide guitar, sunrise over the pasture mood.'],
    ['fc_02_old_truck_radio', 'Nostalgic lo-fi country instrumental: warm twangy electric guitar, soft tape warble, relaxed mid-tempo drums, mellow harmonica licks, windows-down dirt-road cruising feeling.'],
    ['fc_03_hay_bale_harmony', 'Feel-good lo-fi country folk instrumental: fingerpicked acoustic guitar, soft mandolin, brushed drums at 85 BPM, gentle fiddle melody, golden hay-field afternoon warmth.'],
    ['fc_04_front_porch_pickin', 'Cozy lo-fi bluegrass-flavored instrumental: upright bass, relaxed banjo, warm acoustic guitar, soft handclaps, easy porch-sitting tempo, firefly evening atmosphere.'],
    ['fc_05_moonshine_mellow', 'Moody lo-fi country instrumental: slow bluesy slide guitar, dusty drums around 70 BPM, deep warm bass, lonesome pedal-steel melody, quiet night under stars feeling.'],
    ['fc_06_wildflower_waltz', 'Gentle lo-fi country waltz instrumental: soft 3/4 feel around 85 BPM, sweet violin melody, plucked acoustic guitar, warm tape hiss, tender wildflower-meadow romance mood.'],
  ],
};

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  appendFileSync(LOG, line + '\n');
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
proc.stderr.on('data', (d) => log('server stderr: ' + d));
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
  await call('initialize', { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'playlist-gen', version: '1.0' } }, 20000);
  proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  await call('notifications/initialized', undefined, 1000).catch(() => {});

  let done = 0, total = 0;
  const retryQueue = [];
  for (const [pl, tracks] of Object.entries(playlists)) total += tracks.length;
  const pass = async (tracksList, isRetry) => {
    for (const { playlist, filename, prompt } of tracksList) {
      const dir = path.join(AUDIO, playlist);
      if (existsSync(path.join(dir, filename + '.mp3'))) { log(`SKIP ${playlist}/${filename}`); done++; continue; }
      log(`GEN ${playlist}/${filename} (${done + 1}/${total})`);
      try {
        const res = await call('tools/call', {
          name: 'gemini_music_generate',
          arguments: { prompt, output_dir: dir, filename, duration_seconds: 120, timeout_seconds: 400 },
        }, 480000);
        const txt = String(res?.result?.content?.[0]?.text ?? JSON.stringify(res));
        const errMatch = txt.match(/^Error in \w+:\s*(.{0,240})/);
        if (errMatch) {
          log(`FAIL ${playlist}/${filename}: ${errMatch[1].replace(/\n/g, ' ')}`);
          if (!isRetry) retryQueue.push({ playlist, filename, prompt });
        } else {
          log(`OK ${playlist}/${filename}: ${txt.slice(0, 160).replace(/\n/g, ' ')}`);
        }
      } catch (e) {
        log(`FAIL ${playlist}/${filename}: ${e.message}`);
        if (!isRetry) retryQueue.push({ playlist, filename, prompt });
      }
      done++;
      const limit = Number(process.env.LIMIT || 0);
      if (limit && done >= limit) { log(`LIMIT reached (${done}) — stopping`); break; }
    }
  };

  const initial = [];
  for (const [playlist, tracks] of Object.entries(playlists)) {
    for (const [filename, prompt] of tracks) initial.push({ playlist, filename, prompt });
  }
  await pass(initial, false);
  if (retryQueue.length) {
    log(`RETRY pass: ${retryQueue.length} track(s)`);
    await pass([...retryQueue], true);
  }
  log(`ALL DONE ${done}/${total}`);
  proc.kill();
  process.exit(0);
}

main().catch((e) => { log('FATAL ' + e.message); process.exit(1); });
