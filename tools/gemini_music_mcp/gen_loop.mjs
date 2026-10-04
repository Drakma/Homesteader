// Generates one loopable bed with the gemini-music server (loop mode) and turns it into a SEAMLESS loop:
// trims the first/last few seconds, then crossfades the tail into the head, so the last sample flows into the first.
// Output is WAV (Unity loops WAV without the gap MP3 leaves at the loop point, and compresses it on import).
// The raw MP3 stays in tools/gemini_music_mcp/raw (outside the Unity project); the licence sidecar is copied next to the WAV.
//
// Run: node gen_loop.mjs <FileName> "<prompt>" [durationSeconds=120] [outDir=Resources/Audio/Intro]
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const RAW = path.join(here, 'raw');
const [name, prompt, durArg, outArg] = process.argv.slice(2);
if (!name || !prompt) { console.error('usage: node gen_loop.mjs <FileName> "<prompt>" [duration] [outDir]'); process.exit(2); }
const duration = Number(durArg) || 120;
const OUT = outArg || 'C:/Users/casey/Desktop/Homesteader/Homesteader/Assets/Resources/Audio/Intro';
// Env overrides: SHAPE=arc (soft -> lift -> soft; default is a steady bed), TRIM and XFADE in seconds.
const SHAPE = process.env.SHAPE === 'arc' ? 'arc' : true;
const TRIM = Number(process.env.TRIM ?? 5);    // seconds dropped from each end (any intro swell or ending tail Gemini adds anyway)
const XFADE = Number(process.env.XFADE ?? 8);  // seconds of tail crossfaded into the head

mkdirSync(RAW, { recursive: true }); mkdirSync(OUT, { recursive: true });
const rawMp3 = path.join(RAW, name + '.mp3');

if (!existsSync(rawMp3)) {
  const proc = spawn('node', [path.join(here, 'index.js')]);
  let buf = ''; const pending = new Map(); let idc = 0;
  proc.stdout.on('data', (d) => { buf += d; let i; while ((i = buf.indexOf('\n')) >= 0) { const line = buf.slice(0, i); buf = buf.slice(i + 1); try { const m = JSON.parse(line); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } } catch {} } });
  proc.stderr.on('data', (d) => console.error(String(d).trim().slice(0, 200)));
  const call = (method, params, ms) => new Promise((res, rej) => { const id = ++idc; const t = setTimeout(() => rej(new Error('rpc timeout')), ms); pending.set(id, (m) => { clearTimeout(t); res(m); }); proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n'); });
  await call('initialize', { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'gen-loop', version: '1.0' } }, 20000);
  proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  const res = await call('tools/call', { name: 'gemini_music_generate', arguments: { prompt, output_dir: RAW, filename: name, duration_seconds: duration, timeout_seconds: 600, loop: SHAPE } }, 720000);
  const txt = String(res?.result?.content?.[0]?.text ?? '');
  proc.kill();
  console.log(txt.slice(0, 200));
  if (!existsSync(rawMp3)) { console.error('GENERATION FAILED'); process.exit(1); }
}

const D = Number(spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', rawMp3], { encoding: 'utf8' }).stdout.trim());
const wav = path.join(OUT, name + '.wav');
const filter =
  `[0:a]atrim=start=${TRIM}:end=${(D - TRIM).toFixed(3)},asetpts=PTS-STARTPTS,asplit[a][b];` +
  `[a]atrim=start=${XFADE},asetpts=PTS-STARTPTS[main];` +
  `[b]atrim=end=${XFADE},asetpts=PTS-STARTPTS[head];` +
  `[main][head]acrossfade=d=${XFADE}:c1=qsin:c2=qsin[out]`;
const r = spawnSync('ffmpeg', ['-y', '-v', 'error', '-i', rawMp3, '-filter_complex', filter, '-map', '[out]', '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', wav], { encoding: 'utf8' });
if (r.status !== 0) { console.error('ffmpeg failed: ' + r.stderr); process.exit(1); }
const loopLen = Number(spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav], { encoding: 'utf8' }).stdout.trim());

const side = path.join(RAW, name + '.json');
if (existsSync(side)) {
  const j = JSON.parse(readFileSync(side, 'utf8'));
  j.file = name + '.wav';
  j.loop_processing = `seamless loop: ${TRIM}s trimmed from each end of the ${D.toFixed(1)}s source, last ${XFADE}s crossfaded (equal power) into the first ${XFADE}s; loop length ${loopLen.toFixed(2)}s; source MP3 kept at tools/gemini_music_mcp/raw/${name}.mp3`;
  writeFileSync(path.join(OUT, name + '.json'), JSON.stringify(j, null, 2));
}
console.log(`LOOP ${wav} source=${D.toFixed(1)}s loop=${loopLen.toFixed(2)}s`);
