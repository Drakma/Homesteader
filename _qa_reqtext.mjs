export default async function run(page, ui) {
  const r = {};
  await page.waitForSelector('#status-requests', { timeout: 60000 });
  await page.waitForFunction(
    () => document.querySelectorAll('#cat-sidebar .cat-btn').length > 5,
    { timeout: 40000 }
  );
  // The request poller runs on an interval; give it time to finish a cycle.
  await page.waitForTimeout(3000);

  r.idle = await page.evaluate(() => {
    const v = document.getElementById('status-requests-value');
    const item = document.getElementById('status-requests');
    return {
      value: v ? v.textContent.trim() : null,
      color: v ? v.style.color : null,
      title: item ? item.getAttribute('title') : null,
    };
  });

  return r;
}
