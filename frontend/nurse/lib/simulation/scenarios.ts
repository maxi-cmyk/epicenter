import { createRng, sampleInt } from "./rng.ts";
import {
  ASSUMPTIONS_VERSION,
  SIMULATION_SEED,
  type Assumption,
  type PatientSpec,
  type ScenarioConfig,
  type ScenarioId,
} from "./types.ts";

const SHARED_ASSUMPTIONS: Assumption[] = [
  { key: "seed", label: "Shared seed", value: String(SIMULATION_SEED), source: "fixture" },
  { key: "assumptions_version", label: "Assumptions version", value: ASSUMPTIONS_VERSION, source: "fixture" },
  { key: "clinic", label: "Clinic window", value: "HarbourFront synthetic morning (08:00 start)", source: "fixture" },
  { key: "counters", label: "Registration counters", value: "Always 2 fast counters and 4 slow counters", source: "illustrative" },
  { key: "fast_time", label: "Fast-counter service", value: "2 minutes — presence check and cursory file review", source: "illustrative" },
  { key: "slow_time", label: "Slow-counter service", value: "6–8 minutes (3–4× fast) — full registration after arrival", source: "illustrative" },
  { key: "booked", label: "Booked arrivals", value: "24 patients; about 20 complete pre-registration and use the fast counters", source: "illustrative" },
  { key: "walk_ins", label: "Walk-in arrivals", value: "6 patients in a morning-peak cluster; never pre-registered", source: "illustrative" },
  { key: "consult", label: "Consultation", value: "8–12 minutes sampled per patient", source: "illustrative" },
  { key: "pharmacy", label: "Pharmacy", value: "Required for about half of visits, 5–8 minutes", source: "illustrative" },
  { key: "billing", label: "Billing", value: "3–5 minutes sampled per patient", source: "illustrative" },
  {
    key: "manual_baseline",
    label: "Manual administrative baseline (brief)",
    value: "23–32 minutes cited for comparison only; not used as an engine input",
    source: "fixture",
  },
];

function withShared(extra: Assumption[]): Assumption[] {
  return [...SHARED_ASSUMPTIONS, ...extra];
}

const EPICENTER_RESOURCES = {
  fastCounters: 2,
  slowCounters: 4,
  reviewCounters: 1,
  flexibleCounters: 0,
  doctors: 3,
  pharmacists: 1,
  billingCounters: 1,
};

export const SCENARIOS: Record<ScenarioId, ScenarioConfig> = {
  serial_baseline: {
    id: "serial_baseline",
    label: "Serial baseline",
    description: "Same 2 fast / 4 slow desks, but pre-registration is ignored. Every arrival does full registration at a slow counter.",
    seed: SIMULATION_SEED,
    durationMinutes: 240,
    bookedCount: 24,
    walkInCount: 6,
    resources: EPICENTER_RESOURCES,
    policies: {
      preRegistrationEnabled: false,
      singleTicketRoutingEnabled: false,
      fastCounterOverflowEnabled: false,
      allocationAdvisorEnabled: false,
      recommendationApproval: "manual",
    },
    assumptions: withShared([
      {
        key: "serial_admin",
        label: "Serial administration",
        value: "Fast counters stay in the layout but unused; every arrival queues for a slow counter",
        source: "illustrative",
      },
    ]),
  },
  single_ticket: {
    id: "single_ticket",
    label: "Epicenter single-ticket",
    description: "Two fast counters for complete pre-registration; four slow counters for everyone else. Lanes stay strict.",
    seed: SIMULATION_SEED,
    durationMinutes: 240,
    bookedCount: 24,
    walkInCount: 6,
    resources: EPICENTER_RESOURCES,
    policies: {
      preRegistrationEnabled: true,
      singleTicketRoutingEnabled: true,
      fastCounterOverflowEnabled: false,
      allocationAdvisorEnabled: false,
      recommendationApproval: "manual",
    },
    assumptions: withShared([
      {
        key: "strict_lanes",
        label: "Strict lanes",
        value: "Fast counters stay idle rather than taking incomplete registrations",
        source: "illustrative",
      },
      {
        key: "review_workstream",
        label: "Assisted review",
        value: "Exceptions leave the registration line without taking a second ticket",
        source: "fixture",
      },
    ]),
  },
  dynamic_allocation: {
    id: "dynamic_allocation",
    label: "Epicenter + allocation",
    description: "Same 2 fast / 4 slow layout. Idle fast counters take slow-queue patients until a pre-registered patient arrives.",
    seed: SIMULATION_SEED,
    durationMinutes: 240,
    bookedCount: 24,
    walkInCount: 6,
    resources: EPICENTER_RESOURCES,
    policies: {
      preRegistrationEnabled: true,
      singleTicketRoutingEnabled: true,
      fastCounterOverflowEnabled: true,
      allocationAdvisorEnabled: false,
      recommendationApproval: "manual",
    },
    assumptions: withShared([
      {
        key: "overflow",
        label: "Fast-counter overflow",
        value: "If the fast queue is empty, idle fast counters serve the oldest slow-queue patient at slow-counter duration",
        source: "illustrative",
      },
      {
        key: "recall",
        label: "Fast-lane recall",
        value: "A waiting pre-registered patient always takes the next freed fast counter; overflow is not started while they wait",
        source: "illustrative",
      },
    ]),
  },
};

export const SCENARIO_ORDER: ScenarioId[] = ["serial_baseline", "single_ticket", "dynamic_allocation"];

export function generateCohort(seed: number, bookedCount: number, walkInCount: number): PatientSpec[] {
  const rng = createRng(seed);
  const specs: Omit<PatientSpec, "ticketId">[] = [];

  for (let index = 0; index < bookedCount; index += 1) {
    const scheduledMinute = index < 8 ? index : 20 + (index - 8) * 4;
    const arrivalMinute = Math.max(0, scheduledMinute + sampleInt(rng, -1, 1));
    const needsReview = index === 11 || index === 19;
    const fastCheckInMinutes = 2;
    specs.push({
      id: `P-B${String(index + 1).padStart(2, "0")}`,
      intake: "booked",
      adminPriority: index === 11 ? "administratively_urgent" : "standard",
      scheduledMinute,
      arrivalMinute,
      preRegistered: index % 6 !== 5,
      needsReview,
      pharmacyRequired: rng() < 0.48,
      identityState: "pending",
      checkInMinutes: sampleInt(rng, 2, 3),
      identityMinutes: sampleInt(rng, 1, 2),
      documentMinutes: needsReview ? sampleInt(rng, 10, 14) : sampleInt(rng, 3, 6),
      fastCheckInMinutes,
      slowCheckInMinutes: sampleInt(rng, fastCheckInMinutes * 3, fastCheckInMinutes * 4),
      reviewMinutes: needsReview ? sampleInt(rng, 8, 12) : 0,
      consultMinutes: sampleInt(rng, 8, 12),
      pharmacyMinutes: sampleInt(rng, 5, 8),
      billingMinutes: sampleInt(rng, 3, 5),
    });
  }

  const walkInTimes = [18, 22, 26, 30, 58, 76];
  for (let index = 0; index < walkInCount; index += 1) {
    const isComplexBlocker = index === 0;
    const needsReview = index <= 1;
    const fastCheckInMinutes = 2;
    specs.push({
      id: `P-W${String(index + 1).padStart(2, "0")}`,
      intake: "walk_in",
      adminPriority: "standard",
      scheduledMinute: null,
      arrivalMinute: walkInTimes[index] ?? 20 + index * 12,
      preRegistered: false,
      needsReview,
      pharmacyRequired: rng() < 0.45,
      identityState: "pending",
      checkInMinutes: sampleInt(rng, 2, 4),
      identityMinutes: sampleInt(rng, 1, 2),
      documentMinutes: isComplexBlocker ? 24 : needsReview ? 12 : sampleInt(rng, 4, 7),
      fastCheckInMinutes,
      slowCheckInMinutes: sampleInt(rng, fastCheckInMinutes * 3, fastCheckInMinutes * 4),
      reviewMinutes: needsReview ? (isComplexBlocker ? 20 : 16) : 0,
      consultMinutes: sampleInt(rng, 8, 12),
      pharmacyMinutes: sampleInt(rng, 5, 8),
      billingMinutes: sampleInt(rng, 3, 5),
    });
  }

  return specs
    .sort((left, right) => left.arrivalMinute - right.arrivalMinute || left.id.localeCompare(right.id))
    .map((spec, index) => ({
      ...spec,
      ticketId: `Q-${String(index + 1).padStart(3, "0")}`,
    }));
}
