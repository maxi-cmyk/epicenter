import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

const here = dirname(fileURLToPath(import.meta.url));
const reviewDir = resolve(here, "../../.impeccable/review");
await mkdir(reviewDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true,
});

const consoleErrors = [];

async function captureDashboard(viewport, filename) {
  const page = await browser.newPage({ viewport });
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
  await page.getByText("API connected", { exact: true }).waitFor();
  await page.screenshot({ fullPage: true, path: resolve(reviewDir, filename) });
  await page.close();
}

await captureDashboard({ width: 1440, height: 1000 }, "desktop.png");
await captureDashboard({ width: 390, height: 844 }, "mobile.png");

const interactionPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await interactionPage.goto("http://localhost:3000/review", { waitUntil: "networkidle" });
const checkbox = interactionPage.getByRole("checkbox", { name: /I reviewed the source/ });
await checkbox.check();
assert.equal(await interactionPage.getByRole("button", { name: "Confirm and mark ready" }).isEnabled(), true);

await interactionPage.goto("http://localhost:3000/kiosk", { waitUntil: "networkidle" });
await interactionPage.getByLabel("Patient name").fill("Jamie Tan");
await interactionPage.getByRole("button", { name: "Create one visit ticket" }).click();
await interactionPage.getByText("Visit ticket created", { exact: true }).waitFor();

await browser.close();

assert.deepEqual(consoleErrors, [], `Browser console errors: ${consoleErrors.join("\n")}`);
console.log(`Visual QA passed. Screenshots: ${reviewDir}/desktop.png, ${reviewDir}/mobile.png`);
