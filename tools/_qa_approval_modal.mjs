export default async function run(page, ui) {
  // The app polls /api/pending-approvals every 5s on load. Wait for the poll
  // to have run at least once before judging whether the modal opened.
  await page.waitForTimeout(6500);

  const state = await page.evaluate(() => {
    const dlg = document.getElementById("approval-dialog");
    return {
      dialogPresent: !!dlg,
      dialogOpen: dlg ? dlg.open : null,
      title: document.getElementById("approval-title")?.innerText || null,
      planHtmlLen: (document.getElementById("approval-plan-list")?.innerHTML || "").length,
      costHtmlLen: (document.getElementById("approval-cost-box")?.innerHTML || "").length,
      approveBtn: !!document.getElementById("approval-approve-btn"),
      denyBtn: !!document.getElementById("approval-deny-btn"),
    };
  });

  // Ask the server what SHOULD be showing, independently of the DOM.
  const api = await page.evaluate(async () => {
    const r = await fetch("/api/pending-approvals", { cache: "no-store" });
    const d = await r.json();
    return { ok: r.ok, count: (d.approvals || []).length, firstId: (d.approvals || [])[0]?.id || null };
  });

  return { state, api, matches: state.dialogOpen === (api.count > 0) };
}
