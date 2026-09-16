const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
  const filePath = 'file://' + path.resolve(__dirname, 'badge_v2.html');
  await page.goto(filePath);
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.resolve(__dirname, 'badge_v2_screenshot.png'), fullPage: true });
  await browser.close();
})();
