// In the live Mesh2Motion app: load the farmer into the human rig, pick a walk
// animation, and screenshot the result. This is the ground-truth pose the
// headless export must match.
export default async function run(page, ui) {
  const out = {}

  // 1. Human rig.
  await page.evaluate(() => {
    const el = Array.from(document.querySelectorAll('button,div,span,li'))
      .find(x => (x.textContent || '').trim() === 'Human')
    if (el) el.click()
  })
  await page.waitForTimeout(7000)

  // 2. Search the animation list for a Walk entry and click it.
  out.walk = await page.evaluate(async () => {
    // Find the search box if present.
    const search = Array.from(document.querySelectorAll('input'))
      .find(i => /search|filter/i.test(i.placeholder || '') || i.type === 'text')
    if (search) {
      search.value = 'walk'
      search.dispatchEvent(new Event('input', { bubbles: true }))
      await new Promise(r => setTimeout(r, 800))
    }
    // Click the first list entry that is exactly Walk.
    const cands = Array.from(document.querySelectorAll('*'))
      .filter(el => el.children.length === 0 && /^\s*Walk\s*$/.test(el.textContent || ''))
    if (cands.length) { cands[0].click(); return { clicked: true, how: 'exact Walk' } }
    // Otherwise whatever matches /walk/i but not Crouch/Carry.
    const alt = Array.from(document.querySelectorAll('*'))
      .filter(el => el.children.length === 0 &&
        /walk/i.test(el.textContent || '') &&
        !/crouch|carry|backward|fast|slow/i.test(el.textContent || ''))[0]
    if (alt) { alt.click(); return { clicked: true, how: alt.textContent.trim() } }
    return { clicked: false }
  })

  await page.waitForTimeout(6000)

  out.state = await page.evaluate(() => ({
    bodyChars: document.body.innerText.length,
    hasCanvas: !!document.querySelector('canvas'),
    canvasCount: document.querySelectorAll('canvas').length,
  }))

  return out
}