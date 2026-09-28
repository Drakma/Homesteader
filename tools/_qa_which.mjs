// Find WHICH library reports false and WHY. Loads the real page over the real
// network with nothing blocked.
export default async function run(page, ui) {
  const out = { libs: {}, consoleLib: [], reqFail: [] };

  page.on('console', m => {
    const t = m.text();
    if (t.includes('[libs]')) out.consoleLib.push(t.slice(0, 180));
  });
  page.on('requestfailed', r => {
    if (/cdn|googleapis/.test(r.url())) {
      out.reqFail.push({ url: r.url().slice(0, 90), err: r.failure()?.errorText });
    }
  });

  await page.goto('http://127.0.0.1:8088/', { waitUntil: 'load' });
  // Wait past every timeout in the loader.
  await page.waitForTimeout(18000);

  out.libs = await page.evaluate(() => window.__LIB_STATE || 'ABSENT');
  out.globals = await page.evaluate(() => ({
    THREE: typeof THREE,
    fflate: typeof fflate,
    marked: typeof marked,
    modelViewer: !!customElements.get('model-viewer'),
  }));
  out.failures = await page.evaluate(() =>
    (window.LIB_READY?.failures) ? window.LIB_READY.failures() : 'no fn');
  out.pending = await page.evaluate(() =>
    (window.LIB_READY?.anyPending) ? window.LIB_READY.anyPending() : 'no fn');

  return out;
}
