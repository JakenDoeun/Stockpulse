// Inspection pass: walks the real Crisis-to-PO journey (mirrors tests/e2e/demo.spec.ts) and
// saves one 1920x1080 still per shot. Run against a throwaway engine:
//   APP=http://127.0.0.1:8811 NODE_PATH=../../node_modules node capture/inspect.cjs
const { chromium } = require("@playwright/test");
const path = require("path");

const APP = process.env.APP || "http://127.0.0.1:8811";
const OUT = path.join(__dirname, "stills");
const KEY = { "X-Approver-Key": "demo-approver" };

(async () => {
  const browser = await chromium.launch();
  // 1600x900 CSS px at 1.2x = 1920x1080 frames with UI text large enough to read on video.
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const req = ctx.request;
  const shot = async (name) => { await page.waitForTimeout(900); await page.screenshot({ path: `${OUT}/${name}.png` }); console.log("shot", name); };

  // fresh engine state
  const { updates } = await (await req.get(`${APP}/api/supplier-updates`)).json();
  for (const u of updates) await req.delete(`${APP}/api/supplier-updates/${u.id}`);
  await req.post(`${APP}/api/demo/reset`, { headers: KEY });
  await req.post(`${APP}/api/data/reset`);

  await page.goto(`${APP}/#/overview`); await shot("01-overview");
  await page.goto(`${APP}/#/inventory`); await shot("02-inventory");

  await page.goto(`${APP}/#/inbox`); await shot("03-inbox-list");
  await page.locator('tr[data-doc="doc-angkor-pl"]').click(); await shot("04-inbox-angkor-review");
  await page.locator('[data-include="a5"]').uncheck();
  await page.locator('[data-include="a4"]').uncheck();
  await shot("05-inbox-ready");
  await page.locator("[data-confirm]").click(); await shot("06-inbox-verified");

  await page.goto(`${APP}/#/forecasts?sku=SKU008`); await shot("07-forecast-cola");
  await page.goto(`${APP}/#/risk?sku=SKU008`); await shot("08-risk-cola");

  await page.goto(`${APP}/#/cart`); await shot("09-cart-empty");
  await page.locator("[data-load-plan]").click(); await shot("10-cart-plan");
  await page.locator('[data-sim-pct="-30"]').click(); await shot("11-cart-whatif-30");
  await page.locator("[data-sim-apply]").click(); await shot("12-cart-budget-8400");
  await page.locator('[data-why="SKU008"]').click(); await shot("13-cart-why-cola");
  await page.keyboard.press("Escape");
  const qty = page.locator('[data-qty="SKU008"]');
  await qty.fill("500"); await qty.press("Enter"); await shot("14-cart-pack-error");
  await page.locator("#iss-SKU008 [data-fix]").first().click(); await shot("15-cart-fixed-480");

  await page.locator("[data-generate]").click(); await page.waitForURL(/#\/orders\?created=/);
  await shot("16-orders-created");
  const created = page.url().split("created=")[1].split(",").map(Number);
  const { purchase_orders } = await (await req.get(`${APP}/api/pos`)).json();
  const angkor = purchase_orders.find((p) => created.includes(p.id) && p.supplier_id === "S2");
  await page.locator(`tr[data-po="${angkor.id}"]`).click(); await shot("17-po-draft");
  await page.locator('[data-act="submit"]').click(); await shot("18-po-pending");
  await page.fill("#ap-key", "demo-approver");
  await page.locator('[data-act="approve"]').click(); await shot("19-po-approve-dialog");
  await page.locator("[data-confirm]").click(); await shot("20-po-approved");
  await page.locator('[data-dispatch="evolus"]').click(); await shot("21-po-dispatch-simulated");
  await page.goto(`${APP}/#/orders/${angkor.id}/preview`); await shot("22-po-preview");
  await page.goto(`${APP}/#/settings`); await shot("23-settings-integrations");

  console.log("page errors:", errors.length ? errors : "none");
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
