export default async function run(page, ui) {
  const result = {};

  // Wait for the app to finish initializing: the degenerate signal is the
  // sidebar tab row existing at all (it is built by buildCategorySidebar).
  try {
    await page.waitForSelector('#tab-btn-biomes', { timeout: 60000 });
    result.tabFound = true;
  } catch (e) {
    result.tabFound = false;
    result.waitError = String(e).slice(0, 200);
  }

  result.tabs = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.sidebar-tab-btn')).map(b => b.innerText.trim())
  );
  result.biomeCount = await page.evaluate(() => (window.BIOMES || []).length);
  result.sidebarText = await page.evaluate(() =>
    (document.getElementById('cat-sidebar')?.innerText || '').slice(0, 200)
  );

  if (result.tabFound) {
    // Switch to the Biomes tab and confirm the biome list renders in the sidebar.
    await page.click('#tab-btn-biomes');
    await page.waitForTimeout(400);
    result.biomeRowsAfterTab = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#cat-sidebar button[data-biome]')).map(b => ({
        id: b.dataset.biome,
        label: b.innerText.replace(/\s+/g, ' ').trim()
      }))
    );

    // Click the first biome -> editor should open in the collection view.
    const firstId = await page.evaluate(() => {
      const b = document.querySelector('#cat-sidebar button[data-biome]');
      return b ? b.dataset.biome : null;
    });
    result.firstBiomeId = firstId;
    if (firstId) {
      await page.click(`#cat-sidebar button[data-biome="${firstId}"]`);
      // Monaco loads lazily from CDN; give it room.
      await page.waitForTimeout(6000);
      result.editorMounted = await page.evaluate(() =>
        !!document.querySelector('#biome-monaco-host .monaco-editor')
      );
      result.monacoHostText = await page.evaluate(() =>
        (document.getElementById('biome-monaco-host')?.innerText || '').slice(0, 120)
      );
      result.saveBtn = await page.evaluate(() => !!document.getElementById('biome-save-btn'));
      result.bannerTitle = await page.evaluate(() =>
        (document.getElementById('banner-title')?.innerText || '').replace(/\s+/g, ' ').trim()
      );
      // Read a sample of the JSON currently in Monaco.
      result.editorValueHead = await page.evaluate(() => {
        const ta = document.querySelector('#biome-monaco-host textarea');
        return ta ? ta.value.slice(0, 80) : null;
      });
    }
  }

  return result;
}
