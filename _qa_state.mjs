export default async function run(page, ui) {
  const r = {};

  // Long, explicit render wait - the catalog is ~1.8MB and cold render is slow.
  try {
    await page.waitForFunction(
      () => document.querySelectorAll('.folder-card, .item-card').length > 0,
      { timeout: 120000 }
    );
  } catch (e) {
    r.renderTimeout = true;
  }

  r.state = await page.evaluate(() => ({
    sidebarBtns: document.querySelectorAll('#cat-sidebar .cat-btn').length,
    gridChildren: document.getElementById('item-grid') ? document.getElementById('item-grid').children.length : -1,
    folderCards: document.querySelectorAll('.folder-card').length,
    growthGroupCards: document.querySelectorAll('.growth-group-card').length,
    allItemsLen: (typeof ALL_ITEMS !== 'undefined') ? ALL_ITEMS.length : 'ALL_ITEMS undefined',
    growthGroupsKeys: (typeof GROWTH_GROUPS !== 'undefined') ? Object.keys(GROWTH_GROUPS) : 'GG undefined',
    gridClass: (document.getElementById('item-grid') || {}).className,
    bannerTitle: (document.getElementById('banner-title') || {}).innerText,
  }));

  return r;
}
