export const SIMULATION_SEED = 20260809;
export const SCENARIO_VERSION = "demo-v1";
export const ASSUMPTIONS_VERSION = "demo-v1";
export const POLICY_VERSION = "demo-v1";
export const CLOCK_START_HOUR = 8;

export type ScenarioId = "serial_baseline" | "single_ticket" | "dynamic_allocation";
export type IntakeType = "booked" | "walk_in";
export type AdminPriority = "standard" | "administratively_urgent";
export type IdentityState = "pending" | "completed" | "unable_to_confirm";
export type ResourceKind = "fast_counter" | "slow_counter" | "review" | "flexible" | "doctor" | "pharmacist" | "billing";
export type ResourceState = "closed" | "idle" | "busy" | "break" | "reassignment_pending" | "unavailable";
export type Workstream =
  | "registration"
  | "fast_registration"
  | "slow_registration"
  | "review"
  | "consult"
  | "pharmacy"
  | "billing";
export type AssumptionSource = "fixture" | "illustrative";
export type Injection = "walk_in_surge" | "downstream_bottleneck" | "dependency_outage";

export type PatientState =
  | "not_arrived"
  | "waiting_check_in"
  | "checking_in"
  | "processing"
  | "needs_review"
  | "ready"
  | "waiting_consult"
  | "consulting"
  | "waiting_pharmacy"
  | "dispensing"
  | "waiting_billing"
  | "billing"
  | "completed";

export type SimEventType =
  | "scenario_started"
  | "scenario_completed"
  | "patient_arrived"
  | "queued"
  | "service_started"
  | "service_completed"
  | "patient_exited"
  | "document_processing_started"
  | "document_passed"
  | "document_required_review"
  | "identity_attested"
  | "review_started"
  | "review_resolved"
  | "recommendation_generated"
  | "recommendation_approved"
  | "recommendation_rejected"
  | "recommendation_expired"
  | "reassignment_started"
  | "reassignment_completed"
  | "fast_overflow_started"
  | "dependency_outage_started"
  | "dependency_outage_recovered";

export interface ResourceCounts {
  fastCounters: number;
  slowCounters: number;
  reviewCounters: number;
  flexibleCounters: number;
  doctors: number;
  pharmacists: number;
  billingCounters: number;
}

export interface ScenarioPolicies {
  preRegistrationEnabled: boolean;
  singleTicketRoutingEnabled: boolean;
  fastCounterOverflowEnabled: boolean;
  allocationAdvisorEnabled: boolean;
  recommendationApproval: "manual" | "auto";
}

export interface Assumption {
  key: string;
  label: string;
  value: string;
  source: AssumptionSource;
}

export interface ScenarioConfig {
  id: ScenarioId;
  label: string;
  description: string;
  seed: number;
  durationMinutes: number;
  bookedCount: number;
  walkInCount: number;
  resources: ResourceCounts;
  policies: ScenarioPolicies;
  assumptions: Assumption[];
}

export interface PatientSpec {
  id: string;
  ticketId: string;
  intake: IntakeType;
  adminPriority: AdminPriority;
  scheduledMinute: number | null;
  arrivalMinute: number;
  preRegistered: boolean;
  needsReview: boolean;
  pharmacyRequired: boolean;
  identityState: IdentityState;
  checkInMinutes: number;
  identityMinutes: number;
  documentMinutes: number;
  fastCheckInMinutes: number;
  slowCheckInMinutes: number;
  reviewMinutes: number;
  consultMinutes: number;
  pharmacyMinutes: number;
  billingMinutes: number;
}

export interface SimEvent {
  time: number;
  sequence: number;
  type: SimEventType;
  patientId?: string;
  ticketId?: string;
  resourceId?: string;
  stage?: Workstream;
  durationMinutes?: number;
  nextState?: PatientState;
  message: string;
}

export interface Recommendation {
  id: string;
  generatedAt: number;
  expiresAt: number;
  workstream: Workstream;
  fromResourceId: string;
  toWorkstream: Workstream;
  durationMinutes: number;
  evidence: string;
  expectedP90ReductionMinutes: number;
  noChangeP90Wait: number;
  status: "pending" | "approved" | "rejected" | "expired" | "reversed";
}

export interface ResourceSnapshot {
  id: string;
  kind: ResourceKind;
  workstream: Workstream;
  state: ResourceState;
  ticketId: string | null;
  remainingMinutes: number | null;
}

export interface PatientSnapshot {
  id: string;
  ticketId: string;
  intake: IntakeType;
  state: PatientState;
  arrivedAt: number | null;
  ticketAssignedAt: number | null;
  stageEnteredAt: number | null;
  resourceId: string | null;
  fastEligible: boolean;
}

export interface LiveMetrics {
  inClinic: number;
  completed: number;
  notArrived: number;
  throughputPerHour: number;
  adminWaitP50: number | null;
  adminWaitP90: number | null;
  oldestWaitMinutes: number | null;
  longestStage: Workstream | "none";
  utilisationPercent: number;
  firstPassReadiness: number | null;
  fairnessGapMinutes: number | null;
  reviewClearanceP90: number | null;
  queueLengthByStage: Record<Workstream, number>;
  reassignmentChurnPerHour: number;
  recommendationEffectMinutes: number | null;
  fastCounterPatients: number;
  slowCounterPatients: number;
}

export interface SimulationRun {
  scenario: ScenarioConfig;
  seed: number;
  scenarioVersion: string;
  assumptionsVersion: string;
  policyVersion: string;
  snapshotHash: string;
  cohort: PatientSpec[];
  events: SimEvent[];
  recommendations: Recommendation[];
  resources: ResourceSnapshot[];
  metrics: LiveMetrics;
  interventions: string[];
}

export interface ProjectedState {
  time: number;
  patients: PatientSnapshot[];
  resources: ResourceSnapshot[];
  queues: Record<Workstream, string[]>;
  metrics: LiveMetrics;
  activeRecommendation: Recommendation | null;
}

export interface RunOptions {
  approvals?: Array<{ recommendationId: string; decision: "approved" | "rejected" }>;
  resourceOverrides?: Partial<ResourceCounts>;
  injections?: Injection[];
  cohort?: PatientSpec[];
}

export function formatSimClock(minute: number): string {
  const total = CLOCK_START_HOUR * 60 + minute;
  const hours = Math.floor(total / 60) % 24;
  const minutes = total % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

export function snapshotHash(scenarioId: ScenarioId, seed: number): string {
  return `${scenarioId}-${seed}-${ASSUMPTIONS_VERSION}`;
}

export function isFastEligible(spec: Pick<PatientSpec, "preRegistered" | "needsReview">, preRegistrationEnabled: boolean): boolean {
  return preRegistrationEnabled && spec.preRegistered && !spec.needsReview;
}
