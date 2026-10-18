/**
 * UI sound cues: played only for real outcomes, once, and never when muted.
 * Web Audio is observed (every oscillator the page starts is recorded), not mocked.
 */
import { test, expect, type Page } from "@playwright/test";
import { resetEngine, watchErrors } from "./helpers.js";

// Base note of each cue (each note also starts a quiet octave above it).
const SELECT = [880, 1318.5], REVIEW = [587.33, 587.33], ERROR = [523.25, 392], SUCCESS = [659.25, 830.61, 987.77];
const voices = (notes: number[]) => notes.flatMap((f) => [f, f * 2]).map(Math.round).sort((a, b) => a - b);

async function listen(page: Page) {
  await page.addInitScript(() => {
    const w = window as unknown as { __tones: number[] };
    w.__tones = [];
    const start = OscillatorNode.prototype.start;
    OscillatorNode.prototype.start = function (this: OscillatorNode, ...a: [number?]) {
      w.__tones.push(Math.round(this.frequency.value));
      return start.apply(this, a);
    };
  });
}
const heard = (page: Page) => page.evaluate(() => (window as unknown as { __tones: number[] }).__tones.slice().sort((a, b) => a - b));
const clear = (page: Page) => page.evaluate(() => { (window as unknown as { __tones: number[] }).__tones.length = 0; });
const csv = (name: string, text: string) => ({ name, mimeType: "text/csv", buffer: Buffer.from(text) });

test.beforeAll(async ({ request }) => { await resetEngine(request); });

test("import: a soft cue when files are picked, then a review cue when the engine rejects them", async ({ page }) => {
  const errors = watchErrors(page);
  await listen(page);
  await page.goto("/#/overview");
  await page.getByRole("button", { name: "Import Data" }).click(); // the user gesture that unlocks audio
  const input = page.locator("dialog [data-file]");

  await input.setInputFiles(csv("sales.csv", "date,sku,units\n2026-10-01,SKU008,40\n")); // one day of sales: the engine's check refuses it
  await expect(page.getByText("Can't import yet:")).toBeVisible();
  await expect.poll(() => heard(page)).toEqual(voices([...SELECT, ...REVIEW]));

  await page.waitForTimeout(1600); // past the repeat window
  await clear(page);
  await input.setInputFiles(csv("notes.csv", "colour,size\nred,4\n"));
  await expect(page.getByText("Header doesn't match sales, inventory or suppliers.")).toBeVisible(); // the visible status stays the source of truth
  await expect.poll(() => heard(page)).toEqual(voices(REVIEW));
  expect(errors).toEqual([]);
});

test("supplier inbox: a refused file gets the error cue", async ({ page }) => {
  await listen(page);
  await page.goto("/#/inbox");
  await page.getByRole("heading", { name: "Supplier Inbox" }).click();
  const input = page.locator("[data-file]").first();

  await input.setInputFiles({ name: "archive.zip", mimeType: "application/zip", buffer: Buffer.from("PK") });
  await expect(page.getByText("isn't supported")).toBeVisible();
  await expect.poll(() => heard(page)).toEqual(voices(ERROR));
});

test("muted: the setting persists and nothing plays", async ({ page }) => {
  await listen(page);
  await page.goto("/#/settings");
  const toggle = page.locator("#set-sfx");
  await expect(toggle).toBeChecked();
  await toggle.uncheck();
  await expect(page.locator("#set-sfx-vol")).toBeDisabled();
  await page.reload();
  await expect(page.locator("#set-sfx")).not.toBeChecked();

  await page.getByRole("button", { name: "Import Data" }).click();
  await page.locator("dialog [data-file]").setInputFiles(csv("sales.csv", "date,sku,units\n2026-10-01,SKU008,40\n"));
  await expect(page.getByText(/sales\.csv · 1 rows/)).toBeVisible();
  await page.waitForTimeout(500);
  expect(await heard(page)).toEqual([]);
});

test("a repeated trigger plays once", async ({ page }) => {
  await listen(page);
  await page.goto("/#/settings");
  const sample = page.getByRole("button", { name: "Play a sample" });
  await sample.click();
  await sample.click();
  await sample.click();
  await expect.poll(() => heard(page)).toEqual(voices(SUCCESS));
  await page.waitForTimeout(400);
  expect(await heard(page)).toEqual(voices(SUCCESS));
});
