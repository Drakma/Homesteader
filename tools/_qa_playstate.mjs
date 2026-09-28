// Is <model-viewer> actually PLAYING the clip, or showing a static default pose?
export default async function run(page, ui) {
  await page.waitForFunction(
    () => document.body.innerText.includes('Peds'), { timeout: 40000 }).catch(() => { })
  await page.waitForTimeout(1000)

  await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('div,span,li,button'))
      .filter(el => /^\s*Peds\s*$/.test((el.textContent || '').trim()) ||
        (el.textContent || '').trim().startsWith('🙍'))
    if (els.length) els[els.length - 1].click()
  })
  await page.waitForTimeout(1800)

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

  await page.waitForTimeout(9000)

  // Sample currentTime twice to prove playback is advancing.
  const sample = async () => page.evaluate(() => {
    const mv = document.getElementById('active-model-viewer')
    if (!mv) return { present: false }
    return {
      present: true,
      loaded: mv.loaded,
      paused: mv.paused,
      currentTime: mv.currentTime,
      duration: mv.duration,
      animationName: mv.animationName,
      availableAnimations: (mv.availableAnimations || []).length,
    }
  })

  const before = await sample()
  await page.waitForTimeout(1500)
  const after = await sample()

  // Also try explicitly selecting + playing Walk.
  const forced = await page.evaluate(async () => {
    const mv = document.getElementById('active-model-viewer')
    if (!mv) return null
    mv.animationName = 'Walk'
    mv.currentTime = 0
    try { mv.play() } catch (e) { /* ignore */ }
    await new Promise(r => setTimeout(r, 1200))
    return {
      animationName: mv.animationName,
      currentTime: mv.currentTime,
      paused: mv.paused,
      duration: mv.duration,
    }
  })

  return { before, after, forced, advanced: after.currentTime !== before.currentTime }
}