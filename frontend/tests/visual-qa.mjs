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

async function capture(viewport, filename, url, heading) {
  const page = await browser.newPage({ viewport });
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  await page.goto(url, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: heading }).waitFor();
  await page.screenshot({ fullPage: true, path: resolve(reviewDir, filename) });
  await page.close();
}

await capture({ width: 1440, height: 1000 }, "nurse-desktop.png", "http://localhost:3001", "Today’s clinic flow");
await capture({ width: 390, height: 844 }, "nurse-mobile.png", "http://localhost:3001", "Today’s clinic flow");
await capture({ width: 1440, height: 1000 }, "patient-desktop.png", "http://localhost:3000", "Pre-arrival check");
await capture({ width: 390, height: 844 }, "patient-mobile.png", "http://localhost:3000", "Pre-arrival check");

const interactionPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await interactionPage.goto("http://localhost:3001/review", { waitUntil: "networkidle" });
const checkbox = interactionPage.getByRole("checkbox", { name: /I reviewed the source/ });
await checkbox.check();
assert.equal(await interactionPage.getByRole("button", { name: "Confirm and mark ready" }).isEnabled(), true);

await interactionPage.goto("http://localhost:3001/kiosk", { waitUntil: "networkidle" });
await interactionPage.getByLabel("Patient name").fill("Jamie Tan");
assert.equal(await interactionPage.getByRole("button", { name: "Create one visit ticket" }).isEnabled(), true);

await interactionPage.goto("http://localhost:3000", { waitUntil: "networkidle" });
await interactionPage.getByText("Yes, same coverage", { exact: true }).click();
assert.equal(await interactionPage.getByRole("button", { name: "Run current checks" }).isEnabled(), true);
await interactionPage.getByRole("button", { name: "Run current checks" }).click();
await interactionPage.getByText("Submitted for staff confirmation", { exact: true }).waitFor();

await browser.close();

const unexpectedConsoleErrors = consoleErrors.filter(
  (message) => !message.includes("Failed to load resource: net::ERR_CONNECTION_REFUSED"),
);
assert.deepEqual(unexpectedConsoleErrors, [], `Browser console errors: ${unexpectedConsoleErrors.join("\n")}`);
console.log(`Visual QA passed. Screenshots saved in ${reviewDir}`);
