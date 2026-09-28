// Screenshot the old farmer's animated GLB so I can LOOK at the pose rather
// than trusting node names and clip counts.
export default async function run(page, ui) {
  // Wait for the catalog list to render.
  await page.waitForFunction(
    () => document.body.innerText.includes('Peds'),
    { timeout: 40000 }
  ).catch(() => { })

  await page.waitForTimeout(1000)

  // Expand Peds.
  await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('div,span,li,button'))
      .filter(el => /^\s*Peds\s*$/.test((el.textContent || '').trim()) ||
        (el.textContent || '').trim().startsWith('🙍'))
    if (els.length) els[els.length - 1].click()
  })
  await page.waitForTimeout(1800)

  // Click the farmer.
  await page.evaluate(() => {
    const el = Array.from(document.querySelectorAll('div,span,td,li,a,button'))
      .filter(x => x.children.length === 0 && /old farmer/i.test(x.textContent || ''))[0]
    if (!el) return
    let n = el
    for (let i = 0; i < 8 && n; i++) {
      if (n.onclick || n.tagName === 'BUTTON' || n.tagName === 'A' ||
        n.getAttribute('data-id') || /card|row|item/i.test(n.className || '')) {
        n.click(); return
      }
      n = n.parentElement
    }
    el.click()
  })

  // The GLB needs time to load and start animating.
  await page.waitForTimeout(9000)

  const state = await page.evaluate(() => {
    const row = document.getElementById('m-anim-buttons-row')
    const mv = document.getElementById('active-model-viewer')
    const btns = row ? Array.from(row.querySelectorAll('button')) : []
    // Select the Walk clip if present.
    const walk = btns.find(b => /Walk(?!_)/i.test(b.textContent)) || btns[0]
    if (walk) walk.click()
    return {
      buttons: btns.map(b => b.textContent.trim()),
      clicked: walk ? walk.textContent.trim() : null,
      animName: mv ? mv.animationName : null,
      src: mv ? mv.getAttribute('src') : null,
    }
  })

  // Give the walk clip time to reach a mid-stride frame.
  await page.waitForTimeout(2500)

  return { state }
}