import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

const here = dirname(fileURLToPath(import.meta.url));
const reviewDir = resolve(here, "../../.impeccable/review");
await mkdir(reviewDir, { recursive: true });

const auditRows = [
  { id: 2, actor_reference: "synthetic-staff", actor_role: "nurse", action_type: "payment_details_confirmed", target_table: "queue_entries", target_id: "Q-019", details: { payment: { mode: "synthetic_demo", status: "amount_due_confirmed", currency: "SGD", billing_code: "PEE226-CHAS", amount_due: 8.5, confirmed_at: "2026-08-12T09:37:00Z" } }, occurred_at: "2026-08-12T09:37:00Z" },
  { id: 1, actor_reference: "synthetic-system", actor_role: "system", action_type: "visit_completed", target_table: "queue_entries", target_id: "Q-016", details: { outcome: "completed", visit_times: { scheduled_at: "2026-08-12T08:30:00Z", checked_in_at: "2026-08-12T08:22:00Z", completed_at: "2026-08-12T09:08:00Z" } }, occurred_at: "2026-08-12T09:08:00Z" },
];

const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });

async function inspect(baseUrl, app, viewport, filename) {
  const page = await browser.newPage({ viewport });
  const errors = [];
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  await page.route("**/api/v1/audit**", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(auditRows) }));
  await page.goto(`${baseUrl}/audit`, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "Audit trail" }).waitFor();
  assert.equal(await page.getByPlaceholder("Search actor, action, ticket, or safe event detail").isVisible(), true);
  assert.equal(await page.getByRole("button", { name: "CSV" }).isEnabled(), true);
  await page.getByPlaceholder("Search actor, action, ticket, or safe event detail").fill("payment");
  await page.locator("tbody strong").filter({ hasText: "Payment details confirmed" }).waitFor();
  await page.screenshot({ fullPage: true, path: resolve(reviewDir, filename) });
  assert.deepEqual(errors, [], `${app} console errors: ${errors.join("\n")}`);
  await page.close();
}

await inspect("http://localhost:3001", "nurse", { width: 1440, height: 1000 }, "audit-nurse-desktop.png");
await inspect("http://localhost:3001", "nurse", { width: 390, height: 844 }, "audit-nurse-mobile.png");

await browser.close();
console.log(`Audit visual QA passed. Screenshots saved in ${reviewDir}`);
