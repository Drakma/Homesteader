export default async function run(page, ui) {
  const r = {};

  await page.waitForFunction(
    () => document.querySelectorAll('.growth-group-card').length > 0,
    { timeout: 60000 }
  ).catch(() => { r.timeout = true; });

  await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.growth-group-card'));
    const c = cards.find(x => /Large Log Cabin/i.test(x.innerText));
    if (c) c.click();
  });
  await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const cs = Array.from(document.querySelectorAll('.gg-stage-card'));
    const c = cs.find(x => /complete/i.test(x.innerText)) || cs[cs.length - 1];
    if (c) c.click();
  });

  // Stop auto-rotation so the measurement is of the settled default view,
  // which is the framing the user actually lands on.
  await page.waitForTimeout(1500);
  await page.evaluate(() => {
    // OrbitControls instance is module-scoped; find it via the renderer's
    // registered listeners is unreliable, so instead just let it run and
    // sample the canvas across several rotation angles.
  });

  // Sample the canvas at several moments across a full rotation and measure the
  // non-background (model) bounding box each time - the worst case is what
  // matters for "is it ever cut off".
  r.samples = [];
  for (let i = 0; i < 6; i++) {
    await page.waitForTimeout(900);
    const s = await page.evaluate(() => {
      const wrap = document.getElementById('viewport-wrap');
      const canvas = wrap ? wrap.querySelector('canvas') : null;
      if (!canvas) return { error: 'no canvas' };
      const cw = canvas.width, ch = canvas.height;
      const ctx = canvas.getContext('webgl2') || canvas.getContext('webgl');
      if (!ctx) return { error: 'no webgl ctx' };
      const px = new Uint8Array(cw * ch * 4);
      ctx.readPixels(0, 0, cw, ch, ctx.RGBA, ctx.UNSIGNED_BYTE, px);
      // Background is 0x080c12; the grid is 0x334863/0x16202e - treat anything
      // clearly brighter/different as model pixels.
      let minX = cw, maxX = -1, minY = ch, maxY = -1, count = 0;
      for (let y = 0; y < ch; y += 2) {
        for (let x = 0; x < cw; x += 2) {
          const o = (y * cw + x) * 4;
          const rr = px[o], gg = px[o + 1], bb = px[o + 2];
          // model pixels (wood/white roof) are far brighter than the grid
          if (rr + gg + bb > 190) {
            count++;
            if (x < minX) minX = x; if (x > maxX) maxX = x;
            if (y < minY) minY = y; if (y > maxY) maxY = y;
          }
        }
      }
      // NOTE: readPixels y is bottom-up; report in canvas coords, edge flags
      // are what matter, not the direction.
      return {
        canvas: [cw, ch],
        modelPixels: count,
        touchedLeft: minX <= 2, touchedRight: maxX >= cw - 3,
        touchedTop: maxY >= ch - 3, touchedBottom: minY <= 2,
        boxNdcish: [minX / cw, maxX / cw, minY / ch, maxY / ch].map(n => +n.toFixed(3))
      };
    });
    r.samples.push(s);
  }

  return r;
}
