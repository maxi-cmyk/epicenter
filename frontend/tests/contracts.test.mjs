import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

test("routes stay split into focused workspaces", () => {
  assert.match(read("nurse/app/page.tsx"), /DashboardView/);
  assert.match(read("nurse/app/review/page.tsx"), /ReviewWorkspace/);
  assert.match(read("nurse/app/simulator/page.tsx"), /SimulatorWorkspace/);
  assert.match(read("nurse/app/kiosk/page.tsx"), /KioskWorkspace/);
  assert.match(read("patient/app/page.tsx"), /HomeWorkspace/);
  assert.throws(() => read("patient/app/review/page.tsx"));
  assert.throws(() => read("patient/app/kiosk/page.tsx"));
  assert.throws(() => read("nurse/app/pre-arrival/page.tsx"));
});

test("the walk-in path preserves one ticket and nurse supervision copy", () => {
  const kiosk = read("nurse/components/kiosk/KioskWorkspace.tsx");
  assert.match(kiosk, /One intake\. One ticket\./);
  assert.match(kiosk, /supervising nurse/i);
  assert.match(kiosk, /must not delay care/i);
});

test("the patient pre-check preserves the registration and identity boundary", () => {
  const preArrival = read("patient/components/prearrival/PreArrivalWorkspace.tsx");
  assert.match(preArrival, /Singpass-authenticated booking/);
  assert.match(preArrival, /Myinfo/);
  assert.match(preArrival, /identity and e-card checks physically on arrival/);
  assert.match(preArrival, /submitPreArrival/);
  assert.match(preArrival, /Submitted for staff confirmation/);
  assert.match(read("patient/lib/api.ts"), /\/patient\/pre-arrival\/submit/);
});

test("the dashboard labels all demo data honestly", () => {
  const navigation = read("nurse/components/layout/SideNavigation.tsx");
  const dashboard = read("nurse/components/dashboard/DashboardView.tsx");
  assert.match(navigation, /Nurse panel/);
  assert.match(navigation, /Simulator/);
  assert.match(dashboard, /Local synthetic fallback/);
});

test("each deployable app validates its own environment", () => {
  assert.match(read("patient/app/layout.tsx"), /validatePatientEnvironment/);
  assert.match(read("nurse/app/layout.tsx"), /validateNurseEnvironment/);
  assert.match(read("patient/.env.example"), /NEXT_PUBLIC_API_BASE_URL/);
  assert.match(read("nurse/.env.example"), /NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY/);
  assert.match(read("patient/lib/env.ts"), /parsed\.protocol !== "http:"/);
  assert.match(read("nurse/lib/env.ts"), /parsed\.protocol !== "http:"/);
});

test("the visual QA auth bypass is development-only", () => {
  const nurseAuth = read("nurse/components/providers/AuthProvider.tsx");
  const patientAuth = read("patient/components/providers/PatientAuthProvider.tsx");
  assert.match(nurseAuth, /NODE_ENV === "development"/);
  assert.match(nurseAuth, /NEXT_PUBLIC_E2E_BYPASS_AUTH/);
  assert.match(patientAuth, /NODE_ENV === "development"/);
  assert.match(patientAuth, /NEXT_PUBLIC_E2E_BYPASS_AUTH/);
  assert.doesNotMatch(read("nurse\/.env.example"), /E2E_BYPASS/);
});

test("patient signup and nurse provisioning stay separate", () => {
  const patientAuth = read("patient/components/providers/PatientAuthProvider.tsx");
  const nurseSignIn = read("nurse/components/providers/StaffSignIn.tsx");
  assert.match(patientAuth, /Create patient account/);
  assert.match(patientAuth, /<SignUp/);
  assert.match(patientAuth, /activatePatientAccount/);
  assert.doesNotMatch(patientAuth, /role selector/i);
  assert.match(nurseSignIn, /withSignUp=\{false\}/);
  assert.doesNotMatch(nurseSignIn, /<SignUp/);
});

test("staff authorization and mutation reverification fail closed", () => {
  const provider = read("nurse/components/providers/AuthProvider.tsx");
  const api = read("nurse/lib/api.ts");
  const review = read("nurse/components/review/ReviewWorkspace.tsx");
  const dashboard = read("nurse/components/dashboard/DashboardView.tsx");
  const kiosk = read("nurse/components/kiosk/KioskWorkspace.tsx");

  assert.match(provider, /fetchStaffSession/);
  assert.match(provider, /Nurse access required/);
  assert.match(api, /reverification-error/);
  assert.match(api, /error\.status === 401 \|\| error\.status === 403/);
  assert.match(api, /decideRecommendation/);
  assert.match(review, /useReverification\(transitionTicket\)/);
  assert.match(dashboard, /useReverification\(transitionTicket\)/);
  assert.match(kiosk, /useReverification\(checkInWalkIn\)/);
});

test("the shared workspace contains contracts and presentation primitives only", () => {
  const packageJson = JSON.parse(read("shared/package.json"));
  assert.deepEqual(Object.keys(packageJson.exports).sort(), [
    "./contracts",
    "./contracts/generated",
    "./database",
    "./styles/globals.css",
    "./ui/Button",
    "./ui/LoadingBoard",
    "./ui/PageHeader",
    "./ui/StatusBadge",
  ]);
});
