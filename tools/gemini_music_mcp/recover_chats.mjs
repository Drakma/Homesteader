// Walks the Gemini sidebar, opens every music chat and downloads any finished track that was
// never saved (the browser crashed on the Download click for a while on 2026-10-02). Tracks whose
// prompt matches one in bump_playlists.mjs / gen_playlists.mjs land in that playlist folder under
// that filename; anything else goes to tools/gemini_music_mcp/recovered/<slug>.mp3 (OUTSIDE the Unity project) to be sorted
// by hand. Every file gets the usual licence sidecar, plus the chat URL.
//
// Run: node recover_chats.mjs            (DRY=1 lists what it would do without downloading)
import { chromium } from 'playwright';
import { existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const SESSION_DIR = path.join(os.homedir(), '.codegpt', 'gemini-music-session');
const MUSIC = 'C:/Users/casey/Desktop/Homesteader/Homesteader/Assets/Resources/Audio/Music';
const RAW_DIR = path.join(here, 'raw');
const LOG = path.join(here, 'recover_chats.log');
const DRY = process.env.DRY === '1';

function log(m) { const l = `[${new Date().toISOString()}] ${m}`; console.log(l); appendFileSync(LOG, l + '\n'); }

// prompt -> { playlist, filename } from both generator scripts
const promptMap = new Map();
for (const f of ['bump_playlists.mjs', 'gen_playlists.mjs']) {
  const src = readFileSync(path.join(here, f), 'utf8');
  const re = /^\s*(\w+): \[\s*$|^\s*\['([\w-]+)',\s*'((?:[^'\\]|\\.)*)'\],?\s*$/gm;
  let pl = null, m;
  while ((m = re.exec(src))) {
    if (m[1]) { pl = m[1]; continue; }
    if (pl && m[2]) promptMap.set(norm(m[3].replace(/\\'/g, "'")), { playlist: pl, filename: m[2] });
  }
}
function norm(s) { return s.toLowerCase().replace(/\s+/g, ' ').replace(/[^\w ]/g, '').trim(); }
log(`known prompts: ${promptMap.size}`);

const UNSORTED = '(unsorted)';   // not a playlist: see where `dir` is chosen
function guessPlaylist(t) {
  if (/grunge/i.test(t)) return 'Grunge';
  if (/punk/i.test(t)) return 'Punk';
  if (/jazz|blues|lounge|sax|bossa/i.test(t)) return 'SmoothJazz';
  if (/country|ballad|banjo|pedal steel/i.test(t)) return 'ModernCountry';
  if (/classic rock|arena rock|hard rock|rock/i.test(t)) return 'ClassicRock';
  if (/pop|synth|electro|anthem|dance/i.test(t)) return 'ModernPop';
  if (/lo-?fi|chill|homestead|farm|cozy|mellow/i.test(t)) return 'LoFiBeats';
  return UNSORTED;
}
const MUSIC_TITLE = /instrumental|track|music|lo-?fi|grunge|jazz|country|pop|beat|punk|rock|synth|anthem|lounge|piano|sax|blues|folk|bossa|funk|chill/i;
const SKIP_TITLE = /^(failed|denied|music generation (usage )?limit)/i;

const ctx = await chromium.launchPersistentContext(SESSION_DIR, {
  headless: false, channel: 'chrome', colorScheme: 'dark', viewport: { width: 1280, height: 900 }, acceptDownloads: true,
  args: ['--disable-blink-features=AutomationControlled', '--window-position=-1900,40', '--window-size=1300,960', '--force-dark-mode'],
});
const page = ctx.pages()[0] ?? await ctx.newPage();
await page.goto('https://gemini.google.com/app', { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(4000);

// Load the whole conversation list: scroll the sidebar's scrolling ancestor until the count stops growing.
let stable = 0, last = -1;
for (let i = 0; i < 80 && stable < 4; i++) {
  const n = await page.evaluate(() => {
    const items = document.querySelectorAll('a.gem-nav-list-item[href*="/app/"]');
    let el = items[items.length - 1];
    while (el && !(el.scrollHeight > el.clientHeight + 4 && getComputedStyle(el).overflowY !== 'visible')) el = el.parentElement;
    if (el) el.scrollTop = el.scrollHeight;
    const more = [...document.querySelectorAll('button, [role="button"]')].find((b) => /^(show more|more|load more)$/i.test((b.innerText || '').trim()));
    if (more) more.click();
    return items.length;
  });
  if (n === last) stable++; else { stable = 0; last = n; }
  await page.waitForTimeout(900);
}
const chats = await page.evaluate(() => [...document.querySelectorAll('a.gem-nav-list-item[href*="/app/"]')]
  .map((a) => ({ href: a.getAttribute('href'), title: (a.innerText || '').trim().split('\n')[0] })));
const seen = new Set();
const targets = chats.filter((c) => { if (seen.has(c.href)) return false; seen.add(c.href); return MUSIC_TITLE.test(c.title) && !SKIP_TITLE.test(c.title); });
log(`sidebar chats: ${chats.length}, music chats to inspect: ${targets.length}`);

let saved = 0, skipped = 0, none = 0, failed = 0;
for (const c of targets) {
  try {
    try { await page.goto('https://gemini.google.com' + c.href, { waitUntil: 'domcontentloaded', timeout: 60000 }); }
    catch (e) { if (!/ERR_ABORTED/.test(String(e))) throw e; await page.waitForTimeout(1500); await page.goto('https://gemini.google.com' + c.href, { waitUntil: 'domcontentloaded', timeout: 60000 }); }
    await page.waitForTimeout(3500);
    const info = await page.evaluate(() => {
      const q = [...document.querySelectorAll('user-query, .user-query, .query-text, [class*="query-text"]')];
      const prompt = q.length ? (q[0].innerText || '').trim() : '';
      // Only Gemini's music player control; image results have their own "Download" buttons.
      const btns = [...document.querySelectorAll('button[aria-label="Download track" i], button[aria-label*="download track" i]')];
      return { prompt, downloads: btns.length };
    });
    if (!info.downloads) { none++; log(`NONE  ${c.title} (${c.href}) - no finished track`); continue; }
    const requested = info.prompt.replace(/^.*?not cut off mid-song\.\s*/s, '').trim();
    const hit = promptMap.get(norm(requested));
    let playlist, filename;
    if (hit) {
      ({ playlist, filename } = hit);
      // The retired Assets/Audio/Playlists names map onto the live Resources playlists.
      playlist = { HomesteaderChill: 'LoFiBeats', FarmCountry: 'ModernCountry', ModernHomesteading: 'ModernPop' }[playlist] || playlist;
      filename = filename.replace(/^[a-z]{2}_\d\d_/, '').split('_').map((w) => w[0].toUpperCase() + w.slice(1)).join('_');
    } else {
      playlist = guessPlaylist(c.title + ' ' + requested);
      filename = c.title.replace(/(instrumental|track|generation|creation|request|production|blueprint|prompt|script|the|a|an|for|of)/gi, ' ')
        .replace(/[^\w]+/g, '_').replace(/^_+|_+$/g, '').replace(/_+/g, '_').slice(0, 48) || 'Track';
    }
    // Unsorted tracks must never land under Resources/Audio/Music: in the editor every folder there that holds audio
    // becomes a Steadify playlist, and in a build its clips fall into the "Default" playlist.
    const dir = playlist === UNSORTED ? path.join(here, 'recovered') : path.join(MUSIC, playlist);
    // Several chats can share one prompt (retries): keep up to three takes as _v2/_v3.
    let mp3 = path.join(dir, filename + '.mp3');
    if (existsSync(mp3)) {
      let v = 2;
      while (v <= 3 && existsSync(path.join(dir, `${filename}_v${v}.mp3`))) v++;
      if (v > 3) { skipped++; log(`SKIP  ${playlist}/${filename} already has 3 takes`); continue; }
      filename = `${filename}_v${v}`; mp3 = path.join(dir, filename + '.mp3');
    }
    log(`FOUND ${playlist}/${filename} <- "${c.title}"${hit ? '' : ' (prompt not in generator tables)'}`);
    if (DRY) continue;

    mkdirSync(dir, { recursive: true });
    // Fetch the player's media URL with the browser context's cookies instead of clicking Download
    // (Chrome crashes in its download path on this profile; the media URL is a plain https link).
    const src = await page.evaluate(() => {
      const m = [...document.querySelectorAll('video, audio')].at(-1);
      return m ? (m.currentSrc || m.src || '') : '';
    });
    if (!/^https?:/.test(src)) throw new Error('player has no media URL');
    const resp = await ctx.request.get(src, { timeout: 120000 });
    if (!resp.ok()) throw new Error(`media fetch ${resp.status()}`);
    let buf = Buffer.from(await resp.body());
    if (buf.length < 10000) throw new Error('media fetch too small');
    let convertedFrom = null;
    const isMp3 = buf[0] === 0x49 && buf[1] === 0x44 && buf[2] === 0x33 || (buf[0] === 0xff && (buf[1] & 0xe0) === 0xe0);
    if (!isMp3) {
      mkdirSync(RAW_DIR, { recursive: true });
      const raw = path.join(RAW_DIR, filename + '.mp4');
      writeFileSync(raw, buf);
      const r = spawnSync('ffmpeg', ['-y', '-v', 'error', '-i', raw, '-vn', '-codec:a', 'libmp3lame', '-q:a', '0', mp3], { encoding: 'utf8' });
      if (r.status !== 0) throw new Error('ffmpeg failed: ' + r.stderr.slice(0, 200));
      buf = readFileSync(mp3);
      convertedFrom = `mp4 download kept at ${raw}`;
    } else {
      writeFileSync(mp3, buf);
    }
    writeFileSync(path.join(dir, filename + '.json'), JSON.stringify({
      file: filename + '.mp3',
      source: 'Google Gemini web app (Lyria), recovered from chat history via browser automation',
      chat_url: 'https://gemini.google.com' + c.href,
      chat_title: c.title,
      prompt: info.prompt,
      requested_prompt: requested,
      generated_at: new Date().toISOString() + ' (recovered; chat is earlier)',
      downloaded_via: 'media URL fetched with context cookies',
      converted_from: convertedFrom,
      bytes: buf.length,
      sha256: createHash('sha256').update(buf).digest('hex'),
      licence_note: 'Commercial use requires a paid Gemini plan (AI Plus, Pro or Ultra) at the time of generation. Output carries a SynthID watermark and is likely not copyrightable. Listen for stock-library artifacts ("Purchase your track"). Record the plan here.',
      gemini_plan: 'Google AI Plus (account shows Plus badge on 2026-10-02)',
    }, null, 2));
    saved++;
    log(`SAVED ${playlist}/${filename} (${Math.round(buf.length / 1024)} KB)`);
  } catch (e) {
    failed++;
    log(`FAIL  ${c.title} (${c.href}): ${String(e.message || e).slice(0, 160)}`);
    if (/Target page, context or browser has been closed/.test(String(e))) break;
  }
}
log(`DONE saved=${saved} skipped=${skipped} none=${none} failed=${failed}`);
await ctx.close().catch(() => {});
