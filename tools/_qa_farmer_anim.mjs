// Expand the Peds category, open the old farmer, and confirm the animation
// selector renders in the 3D preview panel.
export default async function run(page, ui) {
  const out = {}

  // Wait for the category list to render.
  await page.waitForFunction(
    () => document.body.innerText.includes('Peds'),
    { timeout: 40000 }
  ).catch(() => { out.wait = 'timed out waiting for Peds' })
  await page.waitForTimeout(1200)

  // 1. Expand the Peds category by clicking its row.
  out.expand = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('div,span,li,button'))
      .filter(el => (el.textContent || '').trim().startsWith('🙍') ||
                    (el.textContent || '').trim() === 'Peds' ||
                    /^\s*Peds\s*$/.test(el.textContent || ''))
    if (els.length === 0) return { clicked: false, reason: 'no Peds row' }
    // Click the outermost matching element (the category header row).
    const target = els[els.length - 1]
    target.click()
    return { clicked: true, tag: target.tagName, cls: target.className }
  })
  await page.waitForTimeout(2000)

  // 2. Now find the farmer item and click it.
  out.openItem = await page.evaluate(() => {
    const leaves = Array.from(document.querySelectorAll('div,span,td,li,a,button'))
      .filter(el => el.children.length === 0 && /old farmer/i.test(el.textContent || ''))
    if (leaves.length === 0) {
      return { found: false, sample: document.body.innerText.slice(0, 300) }
    }
    const el = leaves[0]
    let node = el
    for (let i = 0; i < 8 && node; i++) {
      if (node.tagName === 'BUTTON' || node.tagName === 'A' || node.onclick ||
          node.getAttribute('data-id') || /card|row|item/i.test(node.className || '')) {
        node.click()
        return { found: true, via: node.tagName, cls: node.className, label: el.textContent.trim() }
      }
      node = node.parentElement
    }
    el.click()
    return { found: true, via: 'leaf', label: el.textContent.trim() }
  })

  // 3. The preview mounts asynchronously (model-viewer loads the GLB).
  await page.waitForTimeout(7000)

  out.panel = await page.evaluate(() => {
    const row = document.getElementById('m-anim-buttons-row')
    const mv = document.getElementById('active-model-viewer')
    const fbx = document.getElementById('three-canvas-container')
    return {
      animRowExists: !!row,
      animRowHidden: row ? row.hidden : null,
      animButtons: row ? Array.from(row.querySelectorAll('button')).map(b => b.textContent.trim()) : [],
      modelViewerPresent: !!mv,
      mvSrc: mv ? mv.getAttribute('src') : null,
      mvLoaded: mv ? mv.loaded : null,
      mvAvailableAnims: mv ? (mv.availableAnimations || null) : null,
      fbxCanvasPresent: !!fbx,
      itemName: (document.getElementById('m-name') || {}).value || null,
    }
  })

  // 4. If buttons rendered, click one to prove it drives playback.
  if (out.panel.animButtons && out.panel.animButtons.length > 0) {
    out.clickTest = await page.evaluate(async () => {
      const row = document.getElementById('m-anim-buttons-row')
      const btns = Array.from(row.querySelectorAll('button'))
      const target = btns.find(b => /Carry/i.test(b.textContent)) || btns[1] || btns[0]
      const before = target.textContent
      target.click()
      await new Promise(r => setTimeout(r, 600))
      const mv = document.getElementById('active-model-viewer')
      return {
        clickedLabel: before.trim(),
        afterLabel: target.textContent.trim(),
        mvAnimationName: mv ? mv.animationName : null,
        mvPaused: mv ? mv.paused : null,
      }
    })
  }

  return out
}