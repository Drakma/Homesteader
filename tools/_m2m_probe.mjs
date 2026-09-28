// Drive the real Mesh2Motion app to produce a reference walk pose for the
// human rig, so the headless path has ground truth to match.
export default async function run(page, ui) {
  const out = { steps: [] }

  // 1. Pick the Human rig.
  out.rig = await page.evaluate(() => {
    const el = Array.from(document.querySelectorAll('button,div,span,li'))
      .find(x => (x.textContent || '').trim() === 'Human')
    if (!el) return { found: false }
    el.click()
    return { found: true }
  })
  await page.waitForTimeout(6000)

  // 2. Report the page state and progress through the steps.
  out.afterRig = await page.evaluate(() => ({
    bodyChars: document.body.innerText.length,
    text: document.body.innerText.slice(0, 600),
    buttons: Array.from(document.querySelectorAll('button')).map(b => (b.textContent || '').trim()).filter(Boolean).slice(0, 25),
  }))

  await page.waitForTimeout(3000)

  out.final = await page.evaluate(() => ({
    bodyChars: document.body.innerText.length,
    buttons: Array.from(document.querySelectorAll('button')).map(b => (b.textContent || '').trim()).filter(Boolean).slice(0, 30),
    text: document.body.innerText.slice(0, 500),
  }))

  return out
}