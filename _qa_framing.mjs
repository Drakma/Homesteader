export default async function run(page, ui) {
  const r = {};

  await page.waitForFunction(
    () => document.querySelectorAll('.growth-group-card').length > 0,
    { timeout: 60000 }
  ).catch(() => { r.timeout = true; });

  // Open a BIG model: Large Log Cabin complete stage.
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
  await page.waitForTimeout(3000);

  // Project the loaded model's world bounding box into screen space and check
  // it sits INSIDE the canvas - that is what "not cut off" means.
  r.framing = await page.evaluate(() => {
    const out = { hasThree: !!(window.threeScene && window.threeCamera) };
    if (!out.hasThree) return out;
    const cam = window.threeCamera, scene = window.threeScene;
    const wrap = document.getElementById('viewport-wrap');
    const canvas = wrap ? wrap.querySelector('canvas') : null;
    if (!canvas) { out.error = 'no canvas'; return out; }

    // Find the model (the loaded Object3D that is not the grid/lights).
    let model = null;
    scene.traverse(o => {
      if (o.type === 'Group' || o.isObject3D) {
        if (o.children && o.children.length && !o.isLight &&
            o.type !== 'GridHelper' && o.name !== 'grid') {
          const b = new THREE.Box3().setFromObject(o);
          if (!b.isEmpty() && (b.max.y - b.min.y) > 0.5) model = o;
        }
      }
    });
    if (!model) { out.error = 'no model found'; return out; }

    const box = new THREE.Box3().setFromObject(model);
    const min = box.min, max = box.max;
    const corners = [];
    for (const x of [min.x, max.x]) for (const y of [min.y, max.y]) for (const z of [min.z, max.z])
      corners.push(new THREE.Vector3(x, y, z));

    const w = canvas.clientWidth, h = canvas.clientHeight;
    let minNdcX = Infinity, maxNdcX = -Infinity, minNdcY = Infinity, maxNdcY = -Infinity;
    for (const c of corners) {
      const p = c.clone().project(cam);
      minNdcX = Math.min(minNdcX, p.x); maxNdcX = Math.max(maxNdcX, p.x);
      minNdcY = Math.min(minNdcY, p.y); maxNdcY = Math.max(maxNdcY, p.y);
    }
    return {
      hasThree: true, canvasW: w, canvasH: h,
      ndc: {
        minX: +minNdcX.toFixed(3), maxX: +maxNdcX.toFixed(3),
        minY: +minNdcY.toFixed(3), maxY: +maxNdcY.toFixed(3)
      },
      fullyInsideFrame: minNdcX > -1 && maxNdcX < 1 && minNdcY > -1 && maxNdcY < 1,
      cameraPos: [cam.position.x, cam.position.y, cam.position.z].map(n => +n.toFixed(2)),
      target: [threeControls.target.x, threeControls.target.y, threeControls.target.z].map(n => +n.toFixed(2))
    };
  });

  return r;
}
