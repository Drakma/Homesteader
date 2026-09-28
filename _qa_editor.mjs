export default async function run(page, ui) {
  const result = {};

  await page.waitForFunction(
    () => Array.isArray(window.ALL_ITEMS) && window.ALL_ITEMS.length > 0,
    { timeout: 20000 }
  ).catch(() => {});

  const structBtn = page.locator('text=Structures').first();
  if (await structBtn.count()) { await structBtn.click(); await page.waitForTimeout(1200); }

  const cabin = page.locator('text=Large Log Cabin').first();
  result.foundCabin = (await cabin.count()) > 0;
  if (!result.foundCabin) return result;
  await cabin.click();
  await page.waitForTimeout(1500);

  // 1. The redundant header should be gone.
  result.redundantHeaderPresent = await page.evaluate(
    () => document.body.innerText.includes('earliest first')
  );

  // 2. Rail renders icons and its stage count is still visible.
  result.rail = await page.evaluate(() => ({
    cards: document.querySelectorAll('.gg-stage-card').length,
    imgs: Array.from(document.querySelectorAll('.gg-stage-thumb')).filter(t => t.tagName === 'IMG').length,
    decoded: Array.from(document.querySelectorAll('.gg-stage-thumb')).filter(t => t.tagName === 'IMG' && t.naturalWidth > 0).length
  }));

  // 3. The new editable stage table.
  result.editor = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.gg-stage-editor .gg-se-row'));
    return {
      rowCount: rows.length,
      headCols: Array.from(document.querySelectorAll('.gg-se-head > div')).map(d => d.innerText),
      rows: rows.map(r => ({
        stage: r.dataset.stage,
        name: (r.querySelector('.gg-se-name') || {}).value,
        ageMin: (r.querySelector('.gg-se-agemin') || {}).value,
        ageMax: (r.querySelector('.gg-se-agemax') || {}).value,
        model: (r.querySelector('.gg-se-model') || {}).value,
        icon: (r.querySelector('.gg-se-icon') || {}).value
      }))
    };
  });

  return result;
}
