import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

const here = dirname(fileURLToPath(import.meta.url));
const reviewDir = resolve(here, "../../.impeccable/review");
await mkdir(reviewDir, { recursive: true });

const patients = [
  { id: 1, source_record_key: "registration:0001", identifier_masked: "*****854C", full_name: "Tan Kai Xuan", date_of_birth: "1993-12-18", email: "kai.tan@example.test", contact_mobile: "8947 8454", version: 1, deleted_at: null },
  { id: 2, source_record_key: "registration:0042", identifier_masked: "*****946C", full_name: "Loh Wei Ming", date_of_birth: "1986-05-09", email: "wei.loh@example.test", contact_mobile: "8123 4409", version: 3, deleted_at: null },
  { id: 3, source_record_key: "registration:0107", identifier_masked: "*****369H", full_name: "Wong Siti", date_of_birth: "1990-09-25", email: null, contact_mobile: "9234 1188", version: 2, deleted_at: null },
];

const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });

async function preparePage(baseUrl, viewport) {
  const page = await browser.newPage({ viewport });
  const errors = [];
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  await page.route("**/api/v1/patients**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ records: patients, offset: 0, limit: 21 }) });
      return;
    }
    const patient = patients[0];
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...patient, version: patient.version + 1 }) });
  });
  await page.goto(`${baseUrl}/database`, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "Database" }).waitFor();
  return { page, errors };
}

const desktop = await preparePage("http://localhost:3001", { width: 1440, height: 1000 });
assert.equal(await desktop.page.getByPlaceholder("Search patient name").isVisible(), true);
await desktop.page.screenshot({ fullPage: true, path: resolve(reviewDir, "database-desktop.png") });
await desktop.page.getByText("Tan Kai Xuan", { exact: true }).click();
await desktop.page.getByRole("menuitem", { name: "Update" }).click();
await desktop.page.getByRole("heading", { name: "Enter password to make this change" }).waitFor();
await desktop.page.getByLabel("Reason for change").fill("Correct synthetic contact details");
assert.equal(await desktop.page.getByRole("textbox", { name: "Password" }).getAttribute("type"), "password");
await desktop.page.screenshot({ fullPage: true, path: resolve(reviewDir, "database-modal-desktop.png") });
assert.deepEqual(desktop.errors, []);
await desktop.page.close();

const mobile = await preparePage("http://localhost:3001", { width: 390, height: 844 });
await mobile.page.screenshot({ fullPage: true, path: resolve(reviewDir, "database-mobile.png") });
assert.deepEqual(mobile.errors, []);
await mobile.page.close();

await browser.close();
console.log(`Database visual QA passed. Screenshots saved in ${reviewDir}`);
