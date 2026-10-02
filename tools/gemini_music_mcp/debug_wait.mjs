// Debug: reproduce gemini-music's sendPrompt step and capture what the page does.
import { chromium } from 'playwright';
import path from 'node:path';
import os from 'node:os';

const SESSION_DIR = path.join(os.homedir(), '.codegpt', 'gemini-music-session');
const GEMINI_URL = 'https://gemini.google.com/app';
const OUT = 'C:/Users/casey/Desktop/Homesteader/tools/gemini_music_mcp/debug';

const context = await chromium.launchPersistentContext(SESSION_DIR, {
  headless: false,
  channel: 'chrome',
  viewport: { width: 1280, height: 900 },
  acceptDownloads: true,
  args: ['--disable-blink-features=AutomationControlled'],
});
const page = context.pages()[0] ?? await context.newPage();
await page.goto(GEMINI_URL, { waitUntil: 'domcontentloaded', timeout: 60_000 });
await page.waitForTimeout(3000);

const INPUT_SELECTOR = 'rich-textarea .ql-editor, rich-textarea, .ql-editor, [contenteditable="true"], textarea';
await page.waitForSelector(INPUT_SELECTOR, { timeout: 30_000 });
const matches = await page.$$(INPUT_SELECTOR);
console.log('selector matched', matches.length, 'element(s)');
for (let i = 0; i < matches.length; i++) {
  const box = await matches[i].boundingBox();
  const tag = await matches[i].evaluate((e) => `${e.tagName}.${e.className}`.slice(0, 90));
  console.log(`  [${i}] ${tag} box=${JSON.stringify(box)}`);
}

const input = await page.$(INPUT_SELECTOR);
await input.click();
await page.keyboard.type('Create an instrumental-only music track: warm acoustic guitar, soft piano, calm', { delay: 5 });
await page.waitForTimeout(400);
// what is in the editor right before submit?
const editorText = await page.evaluate(() => {
  const ed = document.querySelector('.ql-editor, [contenteditable="true"]');
  return ed ? ed.innerText : '(none)';
});
console.log('editor text before Enter:', JSON.stringify(editorText));

await page.keyboard.press('Enter');
await page.waitForTimeout(90_000);

const after = await page.evaluate(() => ({
  url: location.href,
  body: document.body.innerText.slice(0, 2500),
  audioCount: document.querySelectorAll('audio').length,
}));
console.log('URL after:', after.url);
console.log('audio elements:', after.audioCount);
console.log('--- body text after send ---');
console.log(after.body);
await page.screenshot({ path: path.join(OUT, 'debug_after_send.png'), fullPage: false });
console.log('screenshot saved to', path.join(OUT, 'debug_after_send.png'));

await context.close();

