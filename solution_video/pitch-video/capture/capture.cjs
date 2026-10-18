// Production capture: one 1920x1080 still per real UI state (shot list C01–C10 in storyboard.md).
// Needs a throwaway engine, e.g. from the app root:
//   DB_PATH=/tmp/capture.db .venv/bin/python -m uvicorn app.main:app --port 8811
// then from pitch-video/:
//   APP=http://127.0.0.1:8811 NODE_PATH=../../node_modules node capture/capture.cjs
const { chromium } = require("@playwright/test");
const assert = require("assert");
const fs = require("fs");

const APP = process.env.APP || "http://127.0.0.1:8811";
const OUT = __dirname + "/prod";
const KEY = { "X-Approver-Key": "demo-approver" };
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
  const page = await ctx.newPage();
  const req = ctx.request;
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));

  // Toasts are transient; wait for them to leave on their own so stills show the settled page.
  const settle = async () => {
    await page.waitForTimeout(700);
    await page.waitForFunction(() => !document.querySelector(".toast"), null, { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(300);
  };
  const shot = async (name, opts = {}) => { await settle(); await page.screenshot({ path: `${OUT}/${name}.png`, ...opts }); console.log("shot", name); };
  const api = async (p) => (await req.get(`${APP}${p}`)).json();

  const { updates } = await api("/api/supplier-updates");
  for (const u of updates) await req.delete(`${APP}/api/supplier-updates/${u.id}`);
  await req.post(`${APP}/api/demo/reset`, { headers: KEY });
  await req.post(`${APP}/api/data/reset`);

  // C01 overview (before the supplier update)
  await page.goto(`${APP}/#/overview`);
  await shot("c01-overview");
  await shot("c01-overview-full", { fullPage: true });

  // C02 supplier inbox
  await page.goto(`${APP}/#/inbox`); await shot("c02a-inbox-list");
  await page.locator('tr[data-doc="doc-angkor-pl"]').click(); await shot("c02b-review-top");
  await shot("c02b-review-full", { fullPage: true });
  await page.locator('[data-include="a5"]').scrollIntoViewIfNeeded(); await shot("c02c-review-guardrails");
  await page.locator('[data-include="a5"]').uncheck();
  await page.locator('[data-include="a4"]').uncheck(); await shot("c02d-review-ready");
  await page.locator("[data-confirm]").click(); await page.evaluate(() => window.scrollTo(0, 0)); await shot("c02e-verified");
  const cola = (await api("/api/dashboard")).products.find((p) => p.sku === "SKU008");
  assert.strictEqual(cola.unit_cost, 1.36); assert.strictEqual(cola.lead_time_days, 8);

  // C03 forecast, C04 risk
  await page.goto(`${APP}/#/forecasts?sku=SKU008`); await shot("c03-forecast");
  await shot("c03-forecast-full", { fullPage: true });
  await page.goto(`${APP}/#/risk?sku=SKU008`); await shot("c04-risk");

  // C05/C06 cart: plan, why-this-quantity, what-if −30%, apply
  await page.goto(`${APP}/#/cart`);
  await page.locator("[data-load-plan]").click(); await settle(); await page.evaluate(() => window.scrollTo(0, 0)); await shot("c06a-cart-plan");
  await page.locator('[data-why="SKU008"]').click();
  await page.locator('tr[data-line="SKU008"]').scrollIntoViewIfNeeded(); await shot("c05-why-cola");
  await page.locator('[data-why="SKU008"]').click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.locator('[data-sim-pct="-30"]').click(); await shot("c06b-whatif-30");
  await page.locator("[data-sim-apply]").click(); await page.evaluate(() => window.scrollTo(0, 0)); await shot("c06c-applied-8400");
  await page.locator('tr[data-line="SKU008"]').scrollIntoViewIfNeeded(); await shot("c06d-cola-line-8400");
  assert.strictEqual(await page.locator('[data-qty="SKU008"]').inputValue(), "744");

  // C07/C08 purchase order: generate → open → submit → approve (no manual quantity edit)
  await page.locator("[data-generate]").click(); await page.waitForURL(/#\/orders\?created=/);
  await shot("c07a-orders-created");
  const created = page.url().split("created=")[1].split(",").map(Number);
  const { purchase_orders } = await api("/api/pos");
  const angkor = purchase_orders.find((p) => created.includes(p.id) && p.supplier_id === "S2");
  const line = angkor.lines.find((l) => l.sku === "SKU008");
  assert.deepStrictEqual([line.qty, line.unit_cost, line.line_cost], [744, 1.36, 1011.84]);
  await page.locator(`tr[data-po="${angkor.id}"]`).click(); await shot("c07b-po-draft");
  await page.locator('[data-act="submit"]').click(); await shot("c07c-po-pending");
  await page.fill("#ap-key", "demo-approver"); await shot("c07d-po-key");
  await page.locator('[data-act="approve"]').click(); await page.waitForTimeout(500); await shot("c07e-approve-dialog");
  await page.locator("[data-confirm]").click(); await shot("c07f-po-approved");

  // C09 assistant asked about Cola, C10 integrations
  await page.goto(`${APP}/#/forecasts?sku=SKU008`); await settle();
  await page.getByRole("button", { name: "Assistant" }).click(); await page.waitForTimeout(600);
  await page.getByPlaceholder("Ask about a product, the budget or a supplier").fill("Why is Cola 330ml at risk?");
  await page.getByRole("button", { name: "Ask", exact: true }).click(); await page.waitForTimeout(2500); await shot("c09-assistant-cola");
  await page.goto(`${APP}/#/settings`); await shot("c10-settings");

  console.log("page errors:", errors.length ? errors : "none");
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
