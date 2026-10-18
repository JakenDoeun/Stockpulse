// Extra inspection stills: the assistant answering about Cola, and the PO document preview.
const { chromium } = require("@playwright/test");
const APP = process.env.APP || "http://127.0.0.1:8811", OUT = __dirname + "/stills";
(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 })).newPage();
  await page.goto(`${APP}/#/forecasts?sku=SKU008`); await page.waitForTimeout(1200);
  await page.getByRole("button", { name: "Assistant" }).click(); await page.waitForTimeout(600);
  await page.locator("[data-as-suggest]").first().click(); await page.waitForTimeout(2500);
  await page.screenshot({ path: `${OUT}/24-assistant-cola.png` });
  const { purchase_orders } = await (await page.request.get(`${APP}/api/pos`)).json();
  const po = purchase_orders.find((p) => p.supplier_id === "S2");
  await page.goto(`${APP}/#/orders/${po.id}/preview`); await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/22-po-preview.png` });
  await b.close();
})();
