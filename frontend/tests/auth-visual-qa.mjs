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

async function captureSignedOut(viewport, filename) {
  const page = await browser.newPage({ viewport });
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  await page.goto("http://127.0.0.1:3001", { waitUntil: "networkidle" });
  const signInHeading = page.getByRole("heading", { name: "Open the operations workspace" });
  await signInHeading.waitFor();
  await page.getByRole("heading", { name: "Staff access to today's clinic flow" }).waitFor();
  await page.getByText("Individual staff accountability", { exact: true }).waitFor();
  assert.equal(await page.getByRole("link", { name: "Sign up" }).count(), 0, "Staff sign-in must not offer self-registration");
  const headingBox = await signInHeading.boundingBox();
  assert.ok(headingBox && headingBox.y < viewport.height, "The sign-in task must begin within the first viewport");
  await page.screenshot({ fullPage: true, path: resolve(reviewDir, filename) });
  await page.close();
}

await captureSignedOut({ width: 1440, height: 1000 }, "auth-desktop.png");
await captureSignedOut({ width: 390, height: 844 }, "auth-mobile.png");

await browser.close();

assert.deepEqual(consoleErrors, [], `Browser console errors: ${consoleErrors.join("\n")}`);
console.log(`Clerk signed-out QA passed. Screenshots: ${reviewDir}/auth-desktop.png, ${reviewDir}/auth-mobile.png`);
