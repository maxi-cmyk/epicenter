import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  assertRunInvariants,
  generateCohort,
  isFastEligible,
  projectState,
  runSimulation,
  SIMULATION_SEED,
} from "../nurse/lib/simulation/index.ts";
import type { PatientSpec } from "../nurse/lib/simulation/types.ts";

const read = (path: string) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

function makeSpec(overrides: Partial<PatientSpec> & Pick<PatientSpec, "id" | "ticketId" | "arrivalMinute">): PatientSpec {
  return {
    intake: "walk_in",
    adminPriority: "standard",
    scheduledMinute: null,
    preRegistered: false,
    needsReview: false,
    pharmacyRequired: false,
    identityState: "pending",
    checkInMinutes: 2,
    identityMinutes: 1,
    documentMinutes: 4,
    fastCheckInMinutes: 2,
    slowCheckInMinutes: 8,
    reviewMinutes: 0,
    consultMinutes: 8,
    pharmacyMinutes: 5,
    billingMinutes: 3,
    ...overrides,
  };
}

test("the same scenario and seed reproduce the event log", () => {
  const first = runSimulation("single_ticket");
  const second = runSimulation("single_ticket");
  assert.equal(first.seed, SIMULATION_SEED);
  assert.deepEqual(
    first.events.map((event) => [event.time, event.type, event.ticketId, event.resourceId]),
    second.events.map((event) => [event.time, event.type, event.ticketId, event.resourceId]),
  );
  assert.equal(assertRunInvariants(first).length, 0);
});

test("baseline and epicenter reuse identical arrivals and tickets", () => {
  const cohort = generateCohort(SIMULATION_SEED, 24, 6);
  const baseline = runSimulation("serial_baseline", { cohort });
  const epicenter = runSimulation("single_ticket", { cohort });
  assert.deepEqual(
    baseline.cohort.map((patient) => [patient.ticketId, patient.arrivalMinute, patient.consultMinutes]),
    epicenter.cohort.map((patient) => [patient.ticketId, patient.arrivalMinute, patient.consultMinutes]),
  );
  assert.equal(new Set(baseline.cohort.map((patient) => patient.ticketId)).size, baseline.cohort.length);
  for (const run of [baseline, epicenter, runSimulation("dynamic_allocation", { cohort })]) {
    assert.equal(run.resources.filter((resource) => resource.kind === "fast_counter").length, 2);
    assert.equal(run.resources.filter((resource) => resource.kind === "slow_counter").length, 4);
    assert.deepEqual(
      run.resources.filter((resource) => resource.kind === "fast_counter").map((resource) => resource.id),
      ["F1", "F2"],
    );
    assert.deepEqual(
      run.resources.filter((resource) => resource.kind === "slow_counter").map((resource) => resource.id),
      ["S1", "S2", "S3", "S4"],
    );
  }
  assert.equal(assertRunInvariants(baseline).length, 0);
});

test("complete pre-registration starts at a fast counter", () => {
  const run = runSimulation("single_ticket");
  const eligible = run.cohort.filter((patient) => isFastEligible(patient, true));
  assert.ok(eligible.length >= 16, `expected a busy fast lane, got ${eligible.length} eligible patients`);
  for (const patient of eligible) {
    const start = run.events.find(
      (event) => event.type === "service_started" && event.patientId === patient.id && event.stage === "fast_registration",
    );
    assert.ok(/^F\d+$/.test(start?.resourceId ?? ""), `${patient.ticketId} should start at a fast counter`);
    assert.equal(start?.durationMinutes, patient.fastCheckInMinutes);
  }
  assert.equal(run.metrics.fastCounterPatients, eligible.length);
  assert.ok(run.metrics.slowCounterPatients > 0);
  assert.equal(assertRunInvariants(run).length, 0);
});

test("strict lanes keep incomplete registrations on slow counters", () => {
  const run = runSimulation("single_ticket");
  const incomplete = run.cohort.filter((patient) => !isFastEligible(patient, true));
  assert.ok(incomplete.length > 0);
  for (const patient of incomplete) {
    const start = run.events.find(
      (event) =>
        event.type === "service_started" &&
        event.patientId === patient.id &&
        (event.stage === "fast_registration" || event.stage === "slow_registration"),
    );
    assert.ok(/^S\d+$/.test(start?.resourceId ?? ""), `${patient.ticketId} should stay on a slow counter`);
    assert.equal(start?.stage, "slow_registration");
  }
  assert.equal(
    run.events.some((event) => event.type === "fast_overflow_started"),
    false,
  );
  assert.equal(assertRunInvariants(run).length, 0);
});

test("idle fast counters take slow-queue patients at slow duration", () => {
  const run = runSimulation("dynamic_allocation");
  const overflow = run.events.find((event) => event.type === "fast_overflow_started");
  assert.ok(overflow, "dynamic allocation should overflow onto an idle fast counter");
  assert.ok(/^F\d+$/.test(overflow.resourceId ?? ""));
  const start = run.events.find(
    (event) =>
      event.type === "service_started" &&
      event.patientId === overflow.patientId &&
      event.resourceId === overflow.resourceId,
  );
  const patient = run.cohort.find((item) => item.id === overflow.patientId);
  assert.equal(start?.stage, "slow_registration");
  assert.equal(start?.durationMinutes, patient?.slowCheckInMinutes);
  assert.equal(isFastEligible(patient!, true), false);
  assert.equal(assertRunInvariants(run).length, 0);
});

test("a waiting fast-lane patient takes the next freed fast counter", () => {
  const slowPatients = Array.from({ length: 8 }, (_, index) =>
    makeSpec({
      id: `P-SLOW${index + 1}`,
      ticketId: `Q-S${String(index + 1).padStart(2, "0")}`,
      arrivalMinute: 0,
    }),
  );
  const fastPatient = makeSpec({
    id: "P-FAST",
    ticketId: "Q-FAST",
    intake: "booked",
    scheduledMinute: 1,
    arrivalMinute: 1,
    preRegistered: true,
  });
  const cohort = [...slowPatients, fastPatient];
  const run = runSimulation("dynamic_allocation", { cohort });

  const overflowAtStart = run.events.filter((event) => event.type === "fast_overflow_started" && event.time === 0);
  assert.equal(overflowAtStart.length, 2);

  const fastQueued = run.events.find((event) => event.type === "queued" && event.patientId === "P-FAST");
  const nextFastStart = run.events.find(
    (event) => event.type === "service_started" && event.patientId === "P-FAST" && event.stage === "fast_registration",
  );
  assert.ok(fastQueued);
  assert.equal(/^F\d+$/.test(nextFastStart?.resourceId ?? ""), true);
  assert.equal(nextFastStart?.durationMinutes, 2);
  assert.equal(
    run.events.some(
      (event) =>
        event.type === "fast_overflow_started" &&
        event.sequence > (fastQueued?.sequence ?? 0) &&
        event.sequence < (nextFastStart?.sequence ?? 0),
    ),
    false,
  );
  assert.equal(assertRunInvariants(run).length, 0);
});

test("every patient keeps one ticket through review", () => {
  const run = runSimulation("single_ticket");
  const reviews = run.events.filter((event) => event.type === "review_started" || event.type === "review_resolved");
  assert.ok(reviews.length > 0);
  for (const event of reviews) {
    const patient = run.cohort.find((item) => item.id === event.patientId);
    assert.equal(event.ticketId, patient?.ticketId);
  }
});

test("projected queues follow queued events rather than dumping arrivals onto one counter", () => {
  const run = runSimulation("dynamic_allocation");
  const firstArrival = run.events.find((event) => event.type === "patient_arrived");
  assert.ok(firstArrival);
  const state = projectState(run, firstArrival.time);
  assert.equal(state.queues.registration.length, 0);
  const inRegistration =
    state.queues.fast_registration.length +
    state.queues.slow_registration.length +
    state.resources.filter((resource) => resource.kind === "fast_counter" || resource.kind === "slow_counter").filter((resource) => resource.ticketId).length;
  assert.ok(inRegistration >= 1);
});

test("the simulator stays isolated from operational nurse writes", () => {
  const engine = read("nurse/lib/simulation/engine.ts");
  const workspace = read("nurse/components/simulator/SimulatorWorkspace.tsx");
  assert.doesNotMatch(engine, /\/patients|\/tickets|queue_entries/);
  assert.doesNotMatch(workspace, /transitionTicket|decideRecommendation/);
  assert.match(workspace, /Recent events/);
  assert.match(workspace, /value="queue"/);
  assert.match(workspace, /Whole Overview/);
});
