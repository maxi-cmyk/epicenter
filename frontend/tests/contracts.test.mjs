import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

test("routes stay split into focused workspaces", () => {
  assert.match(read("app/page.tsx"), /DashboardView/);
  assert.match(read("app/review/page.tsx"), /ReviewWorkspace/);
  assert.match(read("app/kiosk/page.tsx"), /KioskWorkspace/);
  assert.match(read("app/pre-arrival/page.tsx"), /PreArrivalWorkspace/);
});

test("the walk-in path preserves one ticket and nurse supervision copy", () => {
  const kiosk = read("components/kiosk/KioskWorkspace.tsx");
  assert.match(kiosk, /One intake\. One ticket\./);
  assert.match(kiosk, /supervising nurse/i);
  assert.match(kiosk, /must not delay care/i);
});

test("the patient pre-check preserves the registration and identity boundary", () => {
  const preArrival = read("components/prearrival/PreArrivalWorkspace.tsx");
  assert.match(preArrival, /Singpass-authenticated booking/);
  assert.match(preArrival, /Myinfo/);
  assert.match(preArrival, /identity and e-card checks physically on arrival/);
});

test("the dashboard labels all demo data honestly", () => {
  const navigation = read("components/layout/SideNavigation.tsx");
  const dashboard = read("components/dashboard/DashboardView.tsx");
  assert.match(navigation, /Synthetic demo/);
  assert.match(dashboard, /Local synthetic fallback/);
});
