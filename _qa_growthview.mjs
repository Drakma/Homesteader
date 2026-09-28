export default async function run(page, ui) {
  const r = {};

  // Wait for the catalog to mount (the app fetches /api/catalog first, which
  // takes ~30s cold on this box - wait on the DOM, not a fixed delay).
  await page.waitForFunction(
    () => document.querySelectorAll('#cat-sidebar .cat-btn').length > 5,
    { timeout: 120000 }
  );
  await page.waitForFunction(
    () => document.querySelectorAll('.item-card, .folder-card').length > 0,
    { timeout: 120000 }
  );

  // Find a growth-group folder card and click it.
  r.groupCardTitle = await page.evaluate(() => {
    const c = document.querySelector('.growth-group-card');
    return c ? c.title : null;
  });

  if (!r.groupCardTitle) return { error: 'no growth-group-card found', ...r };

  await page.click('.growth-group-card');
  await page.waitForTimeout(700);

  r.dom = await page.evaluate(() => {
    const grid = document.getElementById('item-grid');
    const rail = document.querySelector('.gg-stage-rail');
    const scheme = document.querySelector('.gg-scheme');
    const cards = Array.from(document.querySelectorAll('.gg-stage-card'));
    return {
      bodyHasClass: document.body.classList.contains('growth-group-mode'),
      gridCols: grid ? getComputedStyle(grid).gridTemplateColumns : null,
      railPresent: !!rail,
      schemePresent: !!scheme,
      stageOrder: cards.map(c => (c.querySelector('.gg-stage-num') || {}).innerText),
      stageNames: cards.map(c => (c.querySelector('.gg-stage-name') || {}).innerText),
      clickable: cards.map(c => c.classList.contains('gg-no-mesh') ? 'inert' : 'clickable'),
      schemeTitle: scheme ? (scheme.querySelector('.gg-scheme-title') || {}).innerText : null,
      kvPairs: scheme ? Array.from(scheme.querySelectorAll('.kv-box')).map(b => [
        b.querySelector('.kv-key').innerText, b.querySelector('.kv-val').innerText
      ]) : null,
      warnings: scheme ? Array.from(scheme.querySelectorAll('.gg-warn')).map(w => w.innerText) : null,
      lifespanSegs: scheme ? scheme.querySelectorAll('.gg-lifespan-seg').length : 0,
    };
  });

  // Click the first clickable stage and confirm the modal opens on just it.
  r.modal = await page.evaluate(() => {
    const c = Array.from(document.querySelectorAll('.gg-stage-card'))
      .find(x => !x.classList.contains('gg-no-mesh'));
    if (!c) return { skipped: 'no clickable stage card' };
    c.click();
    return { clicked: true };
  });

  await page.waitForTimeout(900);

  r.afterClick = await page.evaluate(() => {
    const m = document.getElementById('item-modal');
    return {
      modalOpen: !!(m && m.open),
      modalName: (document.getElementById('m-name') || {}).innerText || null,
      hasViewport: !!document.querySelector('#viewport-wrap model-viewer, #viewport-wrap canvas'),
    };
  });

  return r;
}
