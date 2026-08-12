import { createClerkClient } from "@clerk/backend";
import { clerk, setupClerkTestingToken } from "@clerk/testing/playwright";
import { expect, test } from "@playwright/test";
import { randomUUID } from "node:crypto";

const nurseEmail = "nurse.noor+clerk_test@example.com";
const adminEmail = "nurse.aisyah+clerk_test@example.com";
const patientEmail = "task4.patient+clerk_test@example.com";
const apiBaseUrl = "http://localhost:8000/api/v1";

const clerkSecretKey = process.env.CLERK_SECRET_KEY;
const supabaseUrl = process.env.EPICENTER_SUPABASE_URL;
const supabaseSecretKey = process.env.EPICENTER_SUPABASE_SECRET_KEY;

if (!clerkSecretKey || !supabaseUrl || !supabaseSecretKey) {
  throw new Error("Live auth tests require Clerk and Supabase server credentials from the ignored backend environment.");
}

const clerkClient = createClerkClient({ secretKey: clerkSecretKey });
let patientFixtureTouched = false;

async function findUser(email: string) {
  const response = await clerkClient.users.getUserList({ emailAddress: [email], limit: 2 });
  if (response.data.length !== 1) throw new Error(`Expected exactly one Clerk user for ${email}.`);
  return response.data[0];
}

async function deletePatientFixture() {
  const response = await clerkClient.users.getUserList({ emailAddress: [patientEmail], limit: 10 });
  for (const user of response.data) {
    await deletePatientMapping(user.id);
    await clerkClient.users.deleteUser(user.id);
  }
}

async function supabaseRequest(path: string, init: RequestInit) {
  const response = await fetch(`${supabaseUrl}/rest/v1/${path}`, {
    ...init,
    headers: {
      apikey: supabaseSecretKey,
      "Content-Type": "application/json",
      Prefer: "return=representation",
      ...init.headers,
    },
  });
  if (!response.ok) throw new Error(`Supabase test setup failed with status ${response.status}.`);
  return response.json() as Promise<unknown>;
}

async function setStaffActive(clerkUserId: string, active: boolean) {
  const rows = await supabaseRequest(`staff_accounts?clerk_user_id=eq.${encodeURIComponent(clerkUserId)}`, {
    method: "PATCH",
    body: JSON.stringify({ active }),
  });
  if (!Array.isArray(rows) || rows.length !== 1) throw new Error("Expected exactly one staff mapping update.");
}

async function deletePatientMapping(clerkUserId: string) {
  await supabaseRequest(`patient_accounts?clerk_user_id=eq.${encodeURIComponent(clerkUserId)}`, {
    method: "DELETE",
  });
}

async function signInWithTestEmail(page: Parameters<typeof clerk.signIn>[0]["page"], email: string) {
  await page.goto("/");
  await clerk.signIn({
    page,
    signInParams: { strategy: "email_code", identifier: email },
  });
}

test.describe.serial("live Clerk authorization", () => {
  test.afterAll(async () => {
    if (patientFixtureTouched) await deletePatientFixture();
  });

  test("a patient can sign up and activate only the configured synthetic booking", async ({ page }) => {
    await deletePatientFixture();
    patientFixtureTouched = true;
    await setupClerkTestingToken({ page });
    await page.goto("http://localhost:3000");
    await page.locator(".cl-signUp-root").waitFor({ state: "attached" });

    const firstName = page.locator('input[name="firstName"]');
    if (await firstName.isVisible()) await firstName.fill("Task Four");
    const lastName = page.locator('input[name="lastName"]');
    if (await lastName.isVisible()) await lastName.fill("Patient");
    await page.locator('input[name="emailAddress"]').fill(patientEmail);
    await page.locator('input[name="password"]').fill(`T4!${randomUUID()}aA1`);
    await page.getByRole("button", { name: "Continue", exact: true }).click();
    await page.getByRole("textbox", { name: "Enter verification code" }).pressSequentially("424242");

    await expect(page.getByRole("heading", { name: "Pre-arrival check" })).toBeVisible();
    await expect(page.getByText("Singpass-authenticated booking", { exact: true })).toBeVisible();
  });

  test("a patient Clerk session is denied by the nurse panel", async ({ page }) => {
    await page.goto("http://localhost:3001");
    await clerk.signIn({ page, signInParams: { strategy: "email_code", identifier: patientEmail } });
    await page.reload();

    await expect(page.getByRole("heading", { name: "Nurse access required" })).toBeVisible();
    await expect(page.getByText("not mapped to an active staff role", { exact: false })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Today’s clinic flow" })).toHaveCount(0);
  });

  test("a provisioned nurse can sign in and reach the clinic workspace", async ({ page }) => {
    await signInWithTestEmail(page, nurseEmail);
    await page.reload();

    await expect(page.getByRole("heading", { name: "Today’s clinic flow" })).toBeVisible();
    await expect(page.getByText("Local synthetic fallback", { exact: true })).toHaveCount(0);
  });

  test("a stale-factor response opens Clerk reverification and retries the mutation", async ({ page }) => {
    await signInWithTestEmail(page, nurseEmail);
    await page.goto("http://localhost:3001/review");
    await expect(page.getByRole("heading", { name: "Assisted review" })).toBeVisible();

    let attempts = 0;
    await page.route("**/api/v1/tickets/*/transition", async (route) => {
      attempts += 1;
      if (attempts === 1) {
        await route.fulfill({
          status: 403,
          contentType: "application/json",
          body: JSON.stringify({
            clerk_error: {
              type: "forbidden",
              reason: "reverification-error",
              metadata: { reverification: "strict" },
            },
          }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true, message: "Reverification retry accepted." }),
      });
    });

    await page.locator('input[type="checkbox"]').check();
    await page.getByRole("button", { name: "Confirm and mark ready" }).click();
    await expect(page.getByRole("heading", { name: "Verification required" })).toBeVisible();
    await page.getByRole("link", { name: "Use another method" }).click();
    await Promise.all([
      page.waitForResponse(
        (response) => response.url().includes("/verify/prepare_first_factor") && response.ok(),
      ),
      page.getByRole("button", { name: "Email code" }).click(),
    ]);
    await page.getByRole("textbox", { name: "Enter verification code" }).pressSequentially("424242");

    await expect.poll(() => attempts).toBe(2);
  });

  test("disabling the staff mapping removes access immediately", async ({ page }) => {
    const nurse = await findUser(nurseEmail);
    await setStaffActive(nurse.id, false);
    try {
      await signInWithTestEmail(page, nurseEmail);
      await page.reload();
      await expect(page.getByRole("heading", { name: "Nurse access required" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Today’s clinic flow" })).toHaveCount(0);
    } finally {
      await setStaffActive(nurse.id, true);
    }
  });

  test("a fresh administrator factor can mutate and the audit identifies that Clerk user", async ({ page, request }) => {
    const administrator = await findUser(adminEmail);
    await signInWithTestEmail(page, adminEmail);
    const token = await page.evaluate(() => window.Clerk.session?.getToken());
    if (!token) throw new Error("Clerk did not issue a session token.");
    const headers = { Authorization: `Bearer ${token}` };

    const dashboardResponse = await request.get(`${apiBaseUrl}/dashboard`, { headers });
    expect(dashboardResponse.ok()).toBeTruthy();
    const dashboard = await dashboardResponse.json();
    const original = dashboard.tickets.find((ticket: { id: string }) => ticket.id === "Q-017");
    if (!original) throw new Error("Seeded ticket Q-017 is unavailable.");

    let committedVersion: number | null = null;
    try {
      const transition = await request.post(`${apiBaseUrl}/tickets/Q-017/transition`, {
        headers,
        data: {
          readiness_state: "needs_review",
          reason: "task4_live_auth_audit",
          staff_confirmed: false,
          expected_version: original.version,
          idempotency_key: `task4-auth-${randomUUID()}`,
        },
      });
      expect(transition.ok()).toBeTruthy();
      const transitionBody = await transition.json();
      committedVersion = transitionBody.ticket.version;

      const auditResponse = await request.get(`${apiBaseUrl}/audit?limit=20`, { headers });
      expect(auditResponse.ok()).toBeTruthy();
      const auditRows = await auditResponse.json();
      expect(
        auditRows.some(
          (row: { actor_reference: string; action_type: string; target_id: string }) =>
            row.actor_reference === administrator.id &&
            row.action_type === "transition_readiness" &&
            row.target_id === "Q-017",
        ),
      ).toBeTruthy();
    } finally {
      if (committedVersion !== null) {
        const restore = await request.post(`${apiBaseUrl}/tickets/Q-017/transition`, {
          headers,
          data: {
            readiness_state: original.readiness_state,
            reason: original.readiness_reason,
            staff_confirmed: original.staff_confirmed,
            expected_version: committedVersion,
            idempotency_key: `task4-restore-${randomUUID()}`,
          },
        });
        expect(restore.ok()).toBeTruthy();
      }
    }
  });
});
