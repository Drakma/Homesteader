#!/usr/bin/env node
/**
 * MCP server: ask Google Gemini (gemini.google.com, Lyria) for music and download the MP3.
 *
 * Tools
 *   gemini_music_generate  - send a music prompt, wait for the track, save the MP3 (+ a licence sidecar JSON)
 *   gemini_music_inspect   - open Gemini, dump what is on the page (text, buttons, audio elements) and a screenshot,
 *                            so the selectors below can be tuned when Google changes the page
 *   gemini_music_login     - open the browser so you can sign in once (the session persists)
 *
 * Gemini has no public download API for the web app, so this drives a real browser (Playwright) like the existing
 * gemini image server, but with its OWN profile (~/.codegpt/gemini-music-session): two Chromium instances cannot share
 * one profile, and the image server may be running. Sign in once in this profile.
 *
 * Licence: every track is saved with <name>.json recording the prompt, time, source and file hash. Commercial use
 * needs a paid Gemini plan (see docs/MUSIC_SOURCES.md); keep the sidecars.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import path from 'node:path';
import os from 'node:os';

const GEMINI_URL = 'https://gemini.google.com/app';
const SESSION_DIR = path.join(os.homedir(), '.codegpt', 'gemini-music-session');
const RAW_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), 'raw');   // untouched downloads, outside the Unity project

let _context = null;
let _page = null;

const text = (t) => ({ content: [{ type: 'text', text: t }] });

/** Playwright throws these when the browser we were driving went away (user closed the
 *  window, Chromium crashed, or a leftover process stole the profile). They are always
 *  recoverable: drop the cached context and launch again. */
function isBrowserGone(e) {
  const m = String(e);
  return m.includes('Target page, context or browser has been closed') ||
    m.includes('Target closed') ||
    m.includes('browser has been closed') ||
    m.includes('Browser closed');
}

/** True when another Chromium already holds this profile directory. */
function isProfileBusy(e) {
  const m = String(e);
  return m.includes('Opening in existing browser session') ||
    m.includes('profile is already in use') ||
    m.includes('ProcessSingleton');
}

/** Kill the leftover Playwright Chromium that is holding our profile. It is ours (same
 *  --user-data-dir), not the user's everyday browser, so this is safe. The old commandline
 *  filters were unreliable; matching on the profile path in the command line is not. */
function killStrayChromium() {
  // Only match the Chromium Playwright ships (ms-playwright), never the user's Chrome.
  spawnSync('powershell', ['-NoProfile', '-Command',
    `Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" -ErrorAction SilentlyContinue | ` +
    `Where-Object { $_.CommandLine -and $_.CommandLine -like '*gemini-music-session*' -and $_.CommandLine -like '*ms-playwright*' } | ` +
    `ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }`],
    { stdio: 'ignore' });
}

/** Launch the persistent context, clearing a leftover holder of the profile and retrying
 *  with backoff so we do not race the dying process. */
async function launchContext() {
  const launch = () => chromium.launchPersistentContext(SESSION_DIR, {
    // Use a real visible browser like Claude's connector. Gemini's music UI and
    // download controls are more reliable when the page is rendered normally.
    headless: false,
    channel: 'chromium',
    viewport: { width: 1280, height: 900 },
    acceptDownloads: true,
    args: ['--disable-blink-features=AutomationControlled'],
  });
  const delays = [0, 1500, 3000, 6000];
  let lastErr;
  for (let i = 0; i < delays.length; i++) {
    if (delays[i]) await new Promise((r) => setTimeout(r, delays[i]));
    try {
      return await launch();
    } catch (e) {
      lastErr = e;
      // A second Chromium started on a profile that is already open does not fail with a "busy" message: it hands
      // the launch to the running instance and exits, and Playwright reports that as "Target page, context or browser
      // has been closed" at launch time. That is the same condition, so treat it as busy too - otherwise a leftover
      // Chromium made every launch fail immediately (gen_playlists.log: FAIL ... launchPersistentContext: Target page,
      // context or browser has been closed) and the server never cleared it.
      if (!isProfileBusy(e) && !isBrowserGone(e)) throw e;
      console.error('[gemini-music] profile busy — terminating leftover Chromium using it');
      killStrayChromium();
    }
  }
  throw lastErr;
}

// ── browser ──────────────────────────────────────────────────────────────────

async function getPage() {
  if (_context) {
    try {
      // The user may have closed the window, or Chromium may have crashed.
      if (_page && !_page.isClosed()) return _page;
      _page = await _context.newPage();
      return _page;
    } catch (e) {
      if (!isBrowserGone(e)) throw e;   // a real bug, not a dead browser
      _context = null;
      _page = null;
    }
  }
  // A leftover Chromium holding this profile makes launch fail with
  // "Opening in existing browser session."; launchContext clears it and retries.
  _context = await launchContext();
  _context.on('close', () => { _context = null; _page = null; });
  _page = _context.pages()[0] ?? (await _context.newPage());
  return _page;
}

/** Reset the cached browser after it died, so the next call relaunches cleanly. */
async function resetBrowser() {
  const c = _context;
  _context = null;
  _page = null;
  await c?.close().catch(() => {});
}

/** Gemini opens fine for guests, so "not redirected to accounts.google.com" does NOT mean signed in. Look for the page's own
 *  signed-out controls (a "Sign in" link) and the signed-in account button. */
async function isSignedIn(page) {
  await page.waitForTimeout(2500);   // let the header render
  return page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const signInLink = [...document.querySelectorAll('a, button')].some((e) => {
      if (!vis(e)) return false;
      const t = (e.innerText || e.getAttribute('aria-label') || '').trim().toLowerCase();
      return t === 'sign in' || (e.getAttribute('href') || '').includes('ServiceLogin');
    });
    const account = [...document.querySelectorAll('[aria-label*="Google Account" i], a[href*="SignOutOptions"], img[src*="googleusercontent"][alt*="profile" i]')].some(vis);
    return account || !signInLink;
  });
}

async function openGemini(page) {
  await page.goto(GEMINI_URL, { waitUntil: 'domcontentloaded', timeout: 60_000 });
  if (page.url().includes('accounts.google.com')) return false;
  return isSignedIn(page);
}

const INPUT_SELECTOR = 'rich-textarea .ql-editor, rich-textarea, .ql-editor, [contenteditable="true"], textarea';

async function startFreshChat(page) {
  // Do not inspect the whole document for quota messages: Gemini keeps old
  // conversation titles in the sidebar, including prior limit messages.
  const newChat = page.getByText('New chat', { exact: true }).first();
  if (await newChat.count()) {
    await newChat.click({ timeout: 10_000 });
    await page.waitForTimeout(800);
  }
}

async function sendPrompt(page, prompt) {
  await page.waitForSelector(INPUT_SELECTOR, { timeout: 30_000 });
  const input = await page.$(INPUT_SELECTOR);
  if (!input) throw new Error('could not find the Gemini prompt box');
  await input.click();
  // Typing (not fill) so the rich editor registers it.
  await page.keyboard.type(prompt, { delay: 5 });
  const typed = await input.evaluate((el) => (el.innerText || el.textContent || el.value || '').trim());
  if (!typed || !typed.includes('Generate music.')) {
    throw new Error('Gemini prompt was not visibly entered; refusing to submit');
  }
  await page.waitForTimeout(400);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1000);
  const submitted = await page.evaluate((p) => {
    const text = document.body.innerText || '';
    return text.includes(p.slice(0, 80));
  }, prompt);
  if (!submitted) {
    throw new Error('Gemini prompt was not visibly submitted; refusing to wait for a result');
  }
}

// ── finding and saving the track ─────────────────────────────────────────────

function looksLikeMp3(buf) {
  if (buf.length < 4) return false;
  if (buf[0] === 0x49 && buf[1] === 0x44 && buf[2] === 0x33) return true;          // "ID3"
  return buf[0] === 0xff && (buf[1] & 0xe0) === 0xe0;                               // MPEG frame sync
}

function sniffExt(buf) {
  if (looksLikeMp3(buf)) return 'mp3';
  if (buf.length > 12 && buf.slice(4, 8).toString() === 'ftyp') return 'm4a';
  if (buf.length > 4 && buf.slice(0, 4).toString() === 'RIFF') return 'wav';
  if (buf.length > 4 && buf.slice(0, 4).toString() === 'OggS') return 'ogg';
  return 'bin';
}

/** Try the page's own download control. Returns a Buffer or null. */
async function tryDownloadButton(page) {
  // The newest response is last; look for a download control near an audio player first, then anywhere.
  const candidates = [
    'button[aria-label*="Download" i]',
    '[role="button"][aria-label*="Download" i]',
    'a[download]',
    'button:has-text("Download")',
    '[mattooltip*="Download" i]',
  ];
  for (const sel of candidates) {
    const loc = page.locator(sel);
    const n = await loc.count();
    if (n === 0) continue;
    const btn = loc.nth(n - 1);          // the most recent one
    try {
      const downloadPromise = page.waitForEvent('download', { timeout: 15_000 });
      await btn.click({ timeout: 5_000 });

      // The control may open a menu (Audio / MP3 / Video) instead of downloading at once.
      const menuPick = page
        .locator('[role="menuitem"]:has-text("MP3"), [role="menuitem"]:has-text("Audio"), button:has-text("MP3"), button:has-text("Audio only")')
        .first();
      if (await menuPick.count()) { await menuPick.click({ timeout: 3_000 }).catch(() => {}); }

      const dl = await downloadPromise;
      const tmp = path.join(os.tmpdir(), `gemini_music_${Date.now()}`);
      await dl.saveAs(tmp);
      const { readFileSync, unlinkSync } = await import('node:fs');
      const buf = readFileSync(tmp);
      unlinkSync(tmp);
      if (buf.length > 10_000) return { buf, via: `download button (${sel})`, suggested: dl.suggestedFilename() };
    } catch {
      // try the next strategy
    }
  }
  return null;
}

/** Fall back to fetching the audio element's source inside the page. */
async function tryAudioElement(page) {
  const b64 = await page.evaluate(async () => {
    const els = [...document.querySelectorAll('audio[src], audio source[src], video[src]')];
    for (const el of els.reverse()) {
      const src = el.src || el.getAttribute('src');
      if (!src) continue;
      try {
        const r = await fetch(src);
        const ab = await r.arrayBuffer();
        if (ab.byteLength < 10_000) continue;
        let bin = '';
        const bytes = new Uint8Array(ab);
        for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
        return btoa(bin);
      } catch { /* next */ }
    }
    return null;
  });
  return b64 ? { buf: Buffer.from(b64, 'base64'), via: 'audio element', suggested: null } : null;
}

/** Stop immediately when Gemini reports that music generation is unavailable or rate-limited. */
async function generationLimitReached(page) {
  return page.evaluate(() => {
    const mains = [...document.querySelectorAll('main, [role="main"]')];
    const t = (mains.at(-1)?.innerText || document.body.innerText).toLowerCase();
    return t.includes('i can create more music as soon as your limit resets') ||
      t.includes('music generation limit reached') ||
      t.includes('music generation limit') ||
      t.includes('your limit resets') ||
      t.includes('check your usage in settings');
  });
}

/** True when Gemini itself reported a generation failure (it also says "your track", so it must be
 *  checked BEFORE hasAudioUi, whose text match "your track" would otherwise mask this). */
async function generationFailed(page) {
  return page.evaluate(() => {
    const t = document.body.innerText.toLowerCase();
    return t.includes('something went wrong while generating') ||
      t.includes('i\'m sorry, something went wrong');
  });
}

async function hasAudioUi(page) {
  return page.evaluate(() => {
    // A real audio UI means an element or a download control — NOT page text. The text
    // "Generating your track" and the error "…while generating your track" both contain
    // "your track", which used to make this return true during generation and failure.
    return !!document.querySelector('audio') ||
      !!document.querySelector('[aria-label*="play" i][aria-label*="track" i], [aria-label*="Download" i]');
  });
}

async function generate({ prompt, outputDir, filename, timeoutSeconds, durationSeconds }) {
  mkdirSync(outputDir, { recursive: true });
  const page = await getPage();
  if (!(await openGemini(page))) {
    return text(
      'Not signed in (Gemini is open as a guest). In the open browser window click "Sign in" and use the account with the paid ' +
      'Gemini plan, then call gemini_music_generate again. The session persists.');
  }

  // Two things Gemini must be told every time, or it misbehaves: INSTRUMENTAL ONLY (otherwise it adds vocals), and a fixed
  // duration with a real ending (otherwise the track just stops mid-song).
  const fullPrompt =
    `Generate music. Create an instrumental-only music track: no vocals, no singing, no lyrics. ` +
    `It must start and stop within ${durationSeconds} seconds: a complete piece with a clear beginning and a proper, ` +
    `natural ending (a final resolving chord or gentle fade-out) that finishes by ${durationSeconds} seconds, ` +
    `not cut off mid-song. ${prompt}`;

    // Old quota messages remain in Gemini's sidebar; always submit in a fresh chat.
    await startFreshChat(page);

    const deadline = Date.now() + timeoutSeconds * 1000;
  let got = null;
  let lastNote = '';
  let crashes = 0;
  let page2 = page;
  let sentAt = null;   // when the prompt went in on the current (relaunched) page
  let retries = 0;     // times Gemini itself failed and we started a fresh chat

  // Survive the browser dying mid-generation: relaunch, re-send the prompt and keep
  // waiting, up to a few times, instead of failing the whole request.
  while (Date.now() < deadline) {
    try {
      if (sentAt === null) {
        await sendPrompt(page2, fullPrompt);
        sentAt = Date.now();
      }
      await page2.waitForTimeout(4000);
      if (await generationLimitReached(page2)) {
        const message = 'Gemini music generation limit reached; stopping without retrying. Wait for the limit to reset.';
        console.error(`[gemini-music] ${message}`);
        return text(message);
      }
      if (await generationFailed(page2)) {
        // Gemini's server-side generation failed ("something went wrong"). A manual retry in a
        // fresh chat usually works, so do the same: open a new chat and resend, a few times.
        retries++;
        lastNote = `Gemini failed to generate (attempt ${retries}) — retrying in a fresh chat`;
        console.error(`[gemini-music] ${lastNote}`);
        if (retries > 3) break;
        await page2.goto(GEMINI_URL, { waitUntil: 'domcontentloaded', timeout: 60_000 });
        sentAt = null;
        continue;
      }
      if (!(await hasAudioUi(page2))) {
        // If the browser was relaunched the track is gone from the page; the prompt
        // that produced it was already re-sent, so we just keep waiting.
        lastNote = 'waiting for audio to appear';
        continue;
      }
      got = (await tryDownloadButton(page2)) || (await tryAudioElement(page2));
      if (got) break;
      lastNote = 'audio UI found but no download worked yet';
    } catch (e) {
      if (!isBrowserGone(e)) throw e;
      crashes++;
      console.error(`[gemini-music] browser closed mid-run (${crashes}) — relaunching`);
      if (crashes > 3) break;
      await resetBrowser();
      page2 = await getPage();
      if (!(await openGemini(page2))) {
        return text('The browser closed and Gemini came back signed out. Sign in again in the tool\'s browser and retry.');
      }
      sentAt = null;   // re-send the prompt on the fresh page
      await new Promise((r) => setTimeout(r, 2000));
    }
  }

  if (!got) {
    const shot = path.join(outputDir, `${filename}_failed.png`);
      const note = crashes ? `${lastNote} after ${crashes} browser relaunch(es)` : lastNote;
    await page2.screenshot({ path: shot, fullPage: false }).catch(() => {});
    // Dump the last response's HTML so the selectors can be fixed without guessing.
    try {
      const html = await page2.evaluate(() => {
        const nodes = [...document.querySelectorAll('main, [role="main"]')];
        return (nodes.at(-1) ?? document.body).outerHTML;
      });
      writeFileSync(path.join(outputDir, `${filename}_page.html`), html);
    } catch { /* best effort */ }
    return text(
      `No track was downloaded within ${timeoutSeconds}s (${note}). A screenshot is at ${shot}. ` +
      'Run gemini_music_inspect to see what the page offers, then adjust the selectors in tools/gemini_music_mcp/index.js.');
  }

  let ext = sniffExt(got.buf);
  let file = path.join(outputDir, `${filename}.${ext}`);
  let convertedFrom = null;

  // Gemini's Download control gives an MP4 (a visualiser video with the AAC audio in it). Keep that untouched in raw/ and
  // extract the audio to a high-quality MP3: Unity cannot import m4a/mp4 on Windows, and the video is dead weight.
  if (ext === 'm4a') {
    mkdirSync(RAW_DIR, { recursive: true });
    const raw = path.join(RAW_DIR, `${filename}.mp4`);
    writeFileSync(raw, got.buf);
    const mp3 = path.join(outputDir, `${filename}.mp3`);
    const r = spawnSync('ffmpeg', ['-y', '-v', 'error', '-i', raw, '-vn', '-codec:a', 'libmp3lame', '-q:a', '0', mp3], { encoding: 'utf8' });
    if (r.status === 0) {
      const { readFileSync } = await import('node:fs');
      got.buf = readFileSync(mp3);
      ext = 'mp3';
      file = mp3;
      convertedFrom = `mp4 download kept at ${raw}`;
    } else {
      writeFileSync(file, got.buf);   // no ffmpeg: leave the m4a and say so
    }
  } else {
    writeFileSync(file, got.buf);
  }

  const sha = createHash('sha256').update(got.buf).digest('hex');
  const sidecar = {
    file: path.basename(file),
    source: 'Google Gemini web app (Lyria), via browser automation',
    prompt: fullPrompt,
    requested_prompt: prompt,
    requested_duration_seconds: durationSeconds,
    generated_at: new Date().toISOString(),
    downloaded_via: got.via,
    converted_from: convertedFrom,
    bytes: got.buf.length,
    sha256: sha,
    licence_note:
      'Commercial use requires a paid Gemini plan (AI Plus, Pro or Ultra) at the time of generation. Output carries a SynthID ' +
      'watermark and is likely not copyrightable. Listen for stock-library artifacts ("Purchase your track"). Record the plan here.',
    gemini_plan: 'UNVERIFIED - fill in',
  };
  writeFileSync(path.join(outputDir, `${filename}.json`), JSON.stringify(sidecar, null, 2));

  const warn = ext === 'mp3' ? '' : `\nNote: the file is ${ext}, not MP3; convert it (ffmpeg -i in.${ext} out.mp3).`;
  return text(`Saved ${file} (${Math.round(got.buf.length / 1024)} KB, via ${got.via}).\nLicence log: ${path.join(outputDir, filename + '.json')}${warn}`);
}

// ---- Background job support -------------------------------------------------
// The MCP client can impose a hard request timeout (~2 minutes) shorter than a
// music generation + download can take. In background mode the tool replies at
// once ("job started") and keeps working; progress is mirrored to
// <outputDir>/<filename>.job.json ("running" -> "done"/"failed") so the caller
// can poll the filesystem for the outcome instead of holding the request open.
const _jobs = new Set();   // filenames with a job still in flight

function writeJobState(outputDir, filename, state) {
  try {
    writeFileSync(path.join(outputDir, `${filename}.job.json`),
      JSON.stringify({ filename, ...state, updated_at: new Date().toISOString() }, null, 2));
  } catch { /* best effort */ }
}

async function generateBackground({ prompt, outputDir, filename, timeoutSeconds, durationSeconds }) {
  if (_jobs.has(filename)) {
    return text(`A job for "${filename}" is already running. Poll ${outputDir}\\${filename}.job.json for its state.`);
  }
  _jobs.add(filename);

  // Run synchronously up to the sign-in check so obvious problems surface
  // immediately; the slow part (render + download) continues detached.
  mkdirSync(outputDir, { recursive: true });
  const page = await getPage();
  if (!(await openGemini(page))) {
    _jobs.delete(filename);
    return text(
      'Not signed in (Gemini is open as a guest). In the open browser window click "Sign in" and use the account with the paid ' +
      'Gemini plan, then call gemini_music_generate again. The session persists.');
  }

  writeJobState(outputDir, filename, { state: 'running', note: 'generation started' });
  (async () => {
    try {
      const result = await generate({ prompt, outputDir, filename, timeoutSeconds, durationSeconds });
      const ok = !/^(Error|Not signed in)/.test(result.content?.[0]?.text ?? 'Error');
      writeJobState(outputDir, filename, {
        state: ok ? 'done' : 'failed',
        note: result.content?.[0]?.text ?? 'no result text',
      });
    } catch (e) {
      writeJobState(outputDir, filename, { state: 'failed', note: e.message });
    } finally {
      _jobs.delete(filename);
    }
  })().catch(() => {});

  return text(
    `Background job started for "${filename}" (duration ${durationSeconds}s, wait up to ${timeoutSeconds}s). ` +
    `The ${durationSeconds}-second render usually lands in a couple of minutes; poll ` +
    `${outputDir}\\${filename}.job.json (state: running -> done/failed) and look for ${filename}.mp3.`);
}

async function inspect() {
  const page = await getPage();
  if (!(await openGemini(page))) return text('Not signed in: sign in in the open browser window, then run this again.');
  await page.waitForTimeout(3000);
  const info = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return {
      url: location.href,
      title: document.title,
      buttons: [...document.querySelectorAll('button, [role="button"], a[download]')]
        .filter(vis).slice(-60)
        .map((b) => (b.getAttribute('aria-label') || b.innerText || b.getAttribute('mattooltip') || '').trim().slice(0, 60))
        .filter(Boolean),
      audio: [...document.querySelectorAll('audio, video')].map((a) => ({ tag: a.tagName, src: (a.currentSrc || a.src || '').slice(0, 120) })),
      bodyText: document.body.innerText.slice(-1500),
    };
  });
  const shot = path.join(os.tmpdir(), 'gemini_music_inspect.png');
  await page.screenshot({ path: shot }).catch(() => {});
  return text(JSON.stringify({ ...info, screenshot: shot }, null, 2));
}

async function login() {
  if (!_context) {   // sign-in needs a visible window
    process.env.GEMINI_MUSIC_HEADED = '1';
  }
  const page = await getPage();
  const ok = await openGemini(page);
  return text(ok
    ? 'Already signed in to Gemini in this profile.'
    : 'NOT signed in (Gemini is open as a guest). In the browser window that just opened, click "Sign in" at the top right and ' +
      'sign in with the account that has the paid Gemini plan. When you are at the Gemini chat signed in, tell me and I will ' +
      'call gemini_music_login again to confirm before generating anything.');
}

// ── MCP plumbing ─────────────────────────────────────────────────────────────

const server = new Server({ name: 'gemini-music-server', version: '1.0.0' }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'gemini_music_generate',
      description:
        'Ask Google Gemini (Lyria, via gemini.google.com browser automation) for an instrumental-only music track that starts and stops within duration_seconds, and download ' +
        'the MP3. Writes <filename>.mp3 and a licence sidecar <filename>.json (prompt, time, hash) into output_dir. ' +
        'Takes 30 to 180 seconds. Needs a one-time Google sign-in in this tool\'s own browser profile; commercial use needs a paid Gemini plan.',
      inputSchema: {
        type: 'object',
        properties: {
          prompt: { type: 'string', description: 'Describe the genre, instruments, mood, tempo and structure (no artist names).' },
          output_dir: { type: 'string', description: 'Where to save the file. Defaults to the current directory.' },
          filename: { type: 'string', description: 'File name without extension. Defaults to a timestamp.' },
          duration_seconds: { type: 'number', description: 'The track must start and stop within this many seconds (it is added to the prompt with a request for a proper ending). Default 90, minimum 60, maximum 160.' },
          timeout_seconds: { type: 'number', description: 'How long to wait for the track. Default 240.' },
          background: { type: 'boolean', description: 'Return immediately and keep generating in the background. Poll <output_dir>/<filename>.job.json (state running -> done/failed) for the outcome. Use this when the caller imposes a short request timeout.' },
        },
        required: ['prompt'],
        },
      },
      {
        name: 'gemini_music_inspect',
      description: 'Open Gemini in the tool\'s browser and dump the visible buttons, audio elements and page text plus a screenshot path. Use it to debug or re-tune the selectors.',
      inputSchema: { type: 'object', properties: {} },
    },
    {
      name: 'gemini_music_login',
      description: 'Open the tool\'s browser at Gemini so you can sign in once. The session persists in ~/.codegpt/gemini-music-session.',
      inputSchema: { type: 'object', properties: {} },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    if (name === 'gemini_music_generate') {
      const prompt = String(args?.prompt ?? '').trim();
      if (!prompt) return text('Error: prompt is required.');
      const genArgs = {
        prompt,
        outputDir: args?.output_dir ? String(args.output_dir) : process.cwd(),
        filename: args?.filename ? String(args.filename).replace(/[^\w.-]+/g, '_') : `gemini_music_${Date.now()}`,
        timeoutSeconds: Math.min(Math.max(Number(args?.timeout_seconds) || 240, 30), 900),
        durationSeconds: Math.min(Math.max(Math.round(Number(args?.duration_seconds) || 90), 60), 160),
      };
      if (args?.background) return await generateBackground(genArgs);
      return await generate(genArgs);
    }
    if (name === 'gemini_music_inspect') return await inspect();
    if (name === 'gemini_music_login') return await login();
    return text(`Error: unknown tool: ${name}`);
  } catch (err) {
    return text(`Error in ${name}: ${err.message}`);
  }
});

await server.connect(new StdioServerTransport());
