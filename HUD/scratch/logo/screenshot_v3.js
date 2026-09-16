const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1100, height: 700 } });
  await page.goto('file://' + path.resolve(__dirname, 'badge_v3.html'));
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.resolve(__dirname, 'badge_v3_screenshot.png'), fullPage: true });
  await browser.close();
})();
