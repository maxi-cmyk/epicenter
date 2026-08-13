import { generateCohort, SCENARIOS } from "./scenarios.ts";
import {
  ASSUMPTIONS_VERSION,
  POLICY_VERSION,
  SCENARIO_VERSION,
  isFastEligible,
  snapshotHash,
  type LiveMetrics,
  type PatientSnapshot,
  type PatientSpec,
  type PatientState,
  type ProjectedState,
  type Recommendation,
  type ResourceSnapshot,
  type RunOptions,
  type ScenarioConfig,
  type ScenarioId,
  type SimEvent,
  type SimEventType,
  type SimulationRun,
  type Workstream,
} from "./types.ts";

const STAGES: Workstream[] = ["fast_registration", "slow_registration", "review", "consult", "pharmacy", "billing"];

const PRIORITY = {
  complete: 10,
  reassign: 20,
  recover: 25,
  arrive: 30,
  advisor: 40,
  expire: 50,
  outage: 15,
  end: 90,
} as const;

type InternalKind = "arrive" | "complete" | "advisor" | "expire" | "reassign" | "outage" | "recover" | "end";

interface InternalEvent {
  time: number;
  priority: number;
  seq: number;
  kind: InternalKind;
  patientId?: string;
  resourceId?: string;
  stage?: Workstream;
}

interface Resource {
  id: string;
  kind: ResourceSnapshot["kind"];
  workstream: Workstream;
  state: ResourceSnapshot["state"];
  patientId: string | null;
  remainingMinutes: number | null;
  busySince: number | null;
  busyMinutes: number;
  availableMinutes: number;
}

interface PatientRuntime {
  spec: PatientSpec;
  state: PatientState;
  arrivedAt: number | null;
  ticketAssignedAt: number | null;
  stageEnteredAt: number | null;
  resourceId: string | null;
  adminWait: number | null;
  reviewWait: number | null;
  reviewStartedAt: number | null;
  registrationLane: "fast" | "slow" | null;
}

function cloneConfig(id: ScenarioId, options: RunOptions | undefined): ScenarioConfig {
  const base = SCENARIOS[id];
  const resources = { ...base.resources, ...options?.resourceOverrides };
  if (options?.injections?.includes("downstream_bottleneck")) {
    resources.doctors = 1;
  }
  return { ...base, resources };
}

function buildResources(config: ScenarioConfig): Resource[] {
  const resources: Resource[] = [];
  const push = (count: number, kind: Resource["kind"], workstream: Workstream, prefix: string) => {
    for (let index = 0; index < count; index += 1) {
      resources.push({
        id: `${prefix}-${index + 1}`,
        kind,
        workstream,
        state: "idle",
        patientId: null,
        remainingMinutes: null,
        busySince: null,
        busyMinutes: 0,
        availableMinutes: 0,
      });
    }
  };
  push(config.resources.fastCounters, "fast_counter", "fast_registration", "FAST");
  push(config.resources.slowCounters, "slow_counter", "slow_registration", "SLOW");
  push(config.resources.reviewCounters, "review", "review", "REV");
  push(config.resources.flexibleCounters, "flexible", "registration", "FLEX");
  push(config.resources.doctors, "doctor", "consult", "DOC");
  push(config.resources.pharmacists, "pharmacist", "pharmacy", "PHARM");
  push(config.resources.billingCounters, "billing", "billing", "BILL");
  return resources;
}

function percentile(values: number[], ratio: number): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.min(sorted.length - 1, Math.max(0, Math.ceil(ratio * sorted.length) - 1));
  return sorted[index] ?? null;
}

function emptyQueues(): Record<Workstream, string[]> {
  return {
    registration: [],
    fast_registration: [],
    slow_registration: [],
    review: [],
    consult: [],
    pharmacy: [],
    billing: [],
  };
}

function isRegistrationStage(stage: Workstream | undefined): boolean {
  return stage === "registration" || stage === "fast_registration" || stage === "slow_registration";
}

function isRegistrationCounter(resource: Pick<Resource, "kind">): boolean {
  return resource.kind === "fast_counter" || resource.kind === "slow_counter";
}

function serialDuration(spec: PatientSpec): number {
  return spec.checkInMinutes + spec.identityMinutes + spec.documentMinutes;
}

function registrationDuration(spec: PatientSpec, serial: boolean, fastLane: boolean): number {
  if (serial) return serialDuration(spec);
  return fastLane ? spec.fastCheckInMinutes : spec.slowCheckInMinutes;
}

function serviceDuration(spec: PatientSpec, stage: Workstream, serial: boolean): number {
  if (isRegistrationStage(stage)) return registrationDuration(spec, serial, stage === "fast_registration");
  if (stage === "review") return spec.reviewMinutes;
  if (stage === "consult") return spec.consultMinutes;
  if (stage === "pharmacy") return spec.pharmacyMinutes;
  return spec.billingMinutes;
}

function nextAfterAdmin(spec: PatientSpec, serial: boolean): { state: PatientState; stage: Workstream | null } {
  if (!serial && spec.needsReview) return { state: "needs_review", stage: "review" };
  return { state: "waiting_consult", stage: "consult" };
}

function nextAfterConsult(spec: PatientSpec): { state: PatientState; stage: Workstream } {
  if (spec.pharmacyRequired) return { state: "waiting_pharmacy", stage: "pharmacy" };
  return { state: "waiting_billing", stage: "billing" };
}

function arrivalLane(spec: PatientSpec, preRegistrationEnabled: boolean, serial: boolean): "fast_registration" | "slow_registration" {
  if (serial || !isFastEligible(spec, preRegistrationEnabled)) return "slow_registration";
  return "fast_registration";
}

export function computeMetrics(
  patients: PatientRuntime[],
  resources: Resource[],
  queues: Record<Workstream, string[]>,
  time: number,
  recommendations: Recommendation[],
): LiveMetrics {
  const arrived = patients.filter((patient) => patient.arrivedAt !== null && patient.arrivedAt <= time);
  const completed = patients.filter((patient) => patient.state === "completed");
  const inClinic = arrived.filter((patient) => patient.state !== "completed" && patient.state !== "not_arrived");
  const notArrived = patients.filter((patient) => patient.state === "not_arrived").length;
  const adminWaits = patients.map((patient) => patient.adminWait).filter((value): value is number => value !== null);
  const reviewWaits = patients.map((patient) => patient.reviewWait).filter((value): value is number => value !== null);
  const bookedAdmin = patients
    .filter((patient) => patient.spec.intake === "booked" && patient.adminWait !== null)
    .map((patient) => patient.adminWait as number);
  const walkInAdmin = patients
    .filter((patient) => patient.spec.intake === "walk_in" && patient.adminWait !== null)
    .map((patient) => patient.adminWait as number);
  const processed = patients.filter((patient) => patient.adminWait !== null);
  const firstPass = processed.filter((patient) => patient.reviewWait === null);
  const oldest = inClinic.reduce<number | null>((current, patient) => {
    if (patient.arrivedAt === null) return current;
    const wait = time - patient.arrivedAt;
    return current === null || wait > current ? wait : current;
  }, null);
  const queueEntries = STAGES.map((stage) => [stage, queues[stage].length] as const);
  let longestStage: Workstream | "none" = "none";
  let longestCount = -1;
  for (const [stage, count] of queueEntries) {
    if (count > longestCount) {
      longestStage = stage;
      longestCount = count;
    }
  }
  const available = resources.reduce((sum, resource) => sum + Math.max(resource.availableMinutes, 1), 0);
  const busy = resources.reduce((sum, resource) => {
    const current = resource.busySince !== null ? time - resource.busySince : 0;
    return sum + resource.busyMinutes + current;
  }, 0);
  const approvedMoves = recommendations.filter((item) => item.status === "approved").length;
  const hours = Math.max(time / 60, 1 / 60);
  const walkP90 = percentile(walkInAdmin, 0.9);
  const bookedP90 = percentile(bookedAdmin, 0.9);

  return {
    inClinic: inClinic.length,
    completed: completed.length,
    notArrived,
    throughputPerHour: time > 0 ? completed.length / hours : 0,
    adminWaitP50: percentile(adminWaits, 0.5),
    adminWaitP90: percentile(adminWaits, 0.9),
    oldestWaitMinutes: oldest,
    longestStage: longestCount > 0 ? longestStage : "none",
    utilisationPercent: Math.round((100 * busy) / available),
    firstPassReadiness: processed.length === 0 ? null : firstPass.length / processed.length,
    fairnessGapMinutes: walkP90 !== null && bookedP90 !== null ? walkP90 - bookedP90 : null,
    reviewClearanceP90: percentile(reviewWaits, 0.9),
    queueLengthByStage: {
      registration: queues.fast_registration.length + queues.slow_registration.length,
      fast_registration: queues.fast_registration.length,
      slow_registration: queues.slow_registration.length,
      review: queues.review.length,
      consult: queues.consult.length,
      pharmacy: queues.pharmacy.length,
      billing: queues.billing.length,
    },
    reassignmentChurnPerHour: approvedMoves / hours,
    recommendationEffectMinutes: null,
    fastCounterPatients: patients.filter((patient) => patient.registrationLane === "fast").length,
    slowCounterPatients: patients.filter((patient) => patient.registrationLane === "slow").length,
  };
}

export function projectState(run: SimulationRun, time: number): ProjectedState {
  const serial = run.scenario.id === "serial_baseline";
  const patients = new Map<string, PatientRuntime>(
    run.cohort.map((spec) => [
      spec.id,
      {
        spec,
        state: "not_arrived" as const,
        arrivedAt: null,
        ticketAssignedAt: null,
        stageEnteredAt: null,
        resourceId: null,
        adminWait: null,
        reviewWait: null,
        reviewStartedAt: null,
        registrationLane: null,
      },
    ]),
  );
  const resources: Resource[] = run.resources.map((resource) => ({
    id: resource.id,
    kind: resource.kind,
    workstream: resource.workstream,
    state: "idle",
    patientId: null,
    remainingMinutes: null,
    busySince: null,
    busyMinutes: 0,
    availableMinutes: 0,
  }));
  const resourceById = new Map(resources.map((resource) => [resource.id, resource]));
  const queues = emptyQueues();
  const recommendations = run.recommendations.map((item) => ({ ...item, status: "pending" as Recommendation["status"] }));

  for (const event of run.events) {
    if (event.time > time) break;
    if (event.type === "patient_arrived" && event.patientId) {
      const patient = patients.get(event.patientId);
      if (!patient) continue;
      patient.state = "waiting_check_in";
      patient.arrivedAt = event.time;
      patient.ticketAssignedAt = event.time;
      patient.stageEnteredAt = event.time;
    } else if (event.type === "service_started" && event.patientId && event.resourceId && event.stage) {
      const patient = patients.get(event.patientId);
      const resource = resourceById.get(event.resourceId);
      if (!patient || !resource) continue;
      queues[event.stage] = queues[event.stage].filter((id) => id !== patient.spec.id);
      patient.resourceId = resource.id;
      resource.patientId = patient.spec.id;
      resource.state = "busy";
      resource.busySince = event.time;
      resource.remainingMinutes = event.durationMinutes ?? null;
      if (isRegistrationStage(event.stage)) {
        patient.state = serial ? "processing" : "checking_in";
        patient.registrationLane = event.stage === "fast_registration" ? "fast" : "slow";
      }
      if (event.stage === "review") {
        patient.state = "needs_review";
        patient.reviewStartedAt = event.time;
      }
      if (event.stage === "consult") patient.state = "consulting";
      if (event.stage === "pharmacy") patient.state = "dispensing";
      if (event.stage === "billing") patient.state = "billing";
    } else if (event.type === "service_completed" && event.patientId && event.resourceId) {
      const patient = patients.get(event.patientId);
      const resource = resourceById.get(event.resourceId);
      if (!patient || !resource) continue;
      if (resource.busySince !== null) resource.busyMinutes += event.time - resource.busySince;
      resource.state = "idle";
      resource.patientId = null;
      resource.busySince = null;
      resource.remainingMinutes = null;
      patient.resourceId = null;
      if (event.nextState) patient.state = event.nextState;
      if (event.nextState === "completed") patient.stageEnteredAt = event.time;
      if (isRegistrationStage(event.stage) && patient.arrivedAt !== null) {
        patient.adminWait = event.time - patient.arrivedAt;
      }
      if (event.stage === "review" && patient.reviewStartedAt !== null) {
        patient.reviewWait = event.time - patient.reviewStartedAt;
      }
    } else if (event.type === "queued" && event.patientId && event.stage) {
      const patient = patients.get(event.patientId);
      if (!patient) continue;
      patient.stageEnteredAt = event.time;
      if (!queues[event.stage].includes(patient.spec.id)) queues[event.stage].push(patient.spec.id);
      if (event.nextState) patient.state = event.nextState;
    } else if (event.type === "reassignment_completed" && event.resourceId && event.stage) {
      const resource = resourceById.get(event.resourceId);
      if (resource) {
        resource.workstream = event.stage;
        resource.state = "idle";
      }
    } else if (event.type === "dependency_outage_started") {
      for (const resource of resources) {
        if (isRegistrationCounter(resource) && resource.state === "idle") resource.state = "unavailable";
      }
    } else if (event.type === "dependency_outage_recovered") {
      for (const resource of resources) {
        if (resource.state === "unavailable") resource.state = "idle";
      }
    } else if (event.type === "recommendation_approved") {
      const match = recommendations.find((item) => item.status === "pending");
      if (match) match.status = "approved";
    } else if (event.type === "recommendation_rejected") {
      const match = recommendations.find((item) => item.status === "pending");
      if (match) match.status = "rejected";
    } else if (event.type === "recommendation_expired") {
      recommendations.forEach((item) => {
        if (item.status === "pending") item.status = "expired";
      });
    }
  }

  for (const resource of resources) {
    resource.availableMinutes = time;
    if (resource.remainingMinutes !== null && resource.busySince !== null) {
      resource.remainingMinutes = Math.max(0, resource.remainingMinutes - (time - resource.busySince));
    }
  }

  const patientList = [...patients.values()];
  const recs = recommendations.map((item) => {
    const generated = run.recommendations.find((row) => row.id === item.id);
    return generated ? { ...generated, status: item.status } : item;
  });
  const active = recs.find((item) => item.generatedAt <= time && (item.status !== "pending" || item.expiresAt > time)) ?? null;

  return {
    time,
    patients: patientList.map((patient) => ({
      id: patient.spec.id,
      ticketId: patient.spec.ticketId,
      intake: patient.spec.intake,
      state: patient.state,
      arrivedAt: patient.arrivedAt,
      ticketAssignedAt: patient.ticketAssignedAt,
      stageEnteredAt: patient.stageEnteredAt,
      resourceId: patient.resourceId,
      fastEligible: isFastEligible(patient.spec, run.scenario.policies.preRegistrationEnabled),
    })),
    resources: resources.map((resource) => ({
      id: resource.id,
      kind: resource.kind,
      workstream: resource.workstream,
      state: resource.state,
      ticketId: resource.patientId ? patients.get(resource.patientId)?.spec.ticketId ?? null : null,
      remainingMinutes: resource.remainingMinutes,
    })),
    queues,
    metrics: computeMetrics(patientList, resources, queues, time, recs),
    activeRecommendation: active,
  };
}

export function runSimulation(scenarioId: ScenarioId, options: RunOptions = {}): SimulationRun {
  const scenario = cloneConfig(scenarioId, options);
  const serial = scenario.id === "serial_baseline";
  const cohort = (options.cohort ?? generateCohort(scenario.seed, scenario.bookedCount, scenario.walkInCount)).map((spec) => ({
    ...spec,
  }));
  if (options.injections?.includes("walk_in_surge")) {
    const offset = cohort.length;
    const extra = generateCohort(scenario.seed + 17, 0, 4).map((spec, index) => ({
      ...spec,
      id: `P-SURGE${index + 1}`,
      arrivalMinute: 60 + index * 3,
      ticketId: `Q-${String(offset + index + 1).padStart(3, "0")}`,
    }));
    cohort.push(...extra);
  }

  const patients = new Map<string, PatientRuntime>();
  for (const spec of cohort) {
    patients.set(spec.id, {
      spec,
      state: "not_arrived",
      arrivedAt: null,
      ticketAssignedAt: null,
      stageEnteredAt: null,
      resourceId: null,
      adminWait: null,
      reviewWait: null,
      reviewStartedAt: null,
      registrationLane: null,
    });
  }

  const resources = buildResources(scenario);
  const queues = emptyQueues();
  const events: SimEvent[] = [];
  const recommendations: Recommendation[] = [];
  const queue: InternalEvent[] = [];
  let seq = 0;
  let eventSeq = 0;
  let now = 0;
  let pressureMinutes = 0;
  let recommendationIssued = false;

  const push = (event: Omit<InternalEvent, "seq">) => {
    seq += 1;
    queue.push({ ...event, seq });
  };
  const emit = (type: SimEventType, message: string, extra: Partial<SimEvent> = {}) => {
    eventSeq += 1;
    events.push({ time: now, sequence: eventSeq, type, message, ...extra });
  };

  const idleFor = (stage: Workstream): Resource | undefined =>
    resources.find((resource) => resource.state === "idle" && resource.workstream === stage);

  const startService = (resource: Resource, patient: PatientRuntime, stage: Workstream, overflow: boolean) => {
    const fastLane = stage === "fast_registration" && !overflow;
    const duration = isRegistrationStage(stage)
      ? registrationDuration(patient.spec, serial, fastLane)
      : serviceDuration(patient.spec, stage, serial);
    patient.resourceId = resource.id;
    patient.stageEnteredAt = now;
    resource.state = "busy";
    resource.patientId = patient.spec.id;
    resource.busySince = now;
    resource.remainingMinutes = duration;
    if (isRegistrationStage(stage)) {
      patient.state = serial ? "processing" : "checking_in";
      patient.registrationLane = fastLane ? "fast" : "slow";
    }
    if (stage === "review") {
      patient.state = "needs_review";
      patient.reviewStartedAt = now;
      emit("review_started", `Review started for ${patient.spec.ticketId}`, {
        patientId: patient.spec.id,
        ticketId: patient.spec.ticketId,
        resourceId: resource.id,
        stage,
      });
    }
    if (stage === "consult") patient.state = "consulting";
    if (stage === "pharmacy") patient.state = "dispensing";
    if (stage === "billing") patient.state = "billing";
    if (isRegistrationStage(stage)) {
      emit("document_processing_started", `Administrative processing started for ${patient.spec.ticketId}`, {
        patientId: patient.spec.id,
        ticketId: patient.spec.ticketId,
        resourceId: resource.id,
        stage,
      });
      emit("identity_attested", `Manual identity/e-card attestation completed for ${patient.spec.ticketId}`, {
        patientId: patient.spec.id,
        ticketId: patient.spec.ticketId,
      });
      patient.spec.identityState = "completed";
    }
    if (overflow) {
      emit(
        "fast_overflow_started",
        `${patient.spec.ticketId} overflowed onto idle ${resource.id} at slow-counter duration (${duration} min)`,
        {
          patientId: patient.spec.id,
          ticketId: patient.spec.ticketId,
          resourceId: resource.id,
          stage,
          durationMinutes: duration,
        },
      );
    }
    emit("service_started", `${patient.spec.ticketId} started ${stage.replaceAll("_", " ")} at ${resource.id}`, {
      patientId: patient.spec.id,
      ticketId: patient.spec.ticketId,
      resourceId: resource.id,
      stage,
      durationMinutes: duration,
    });
    push({ time: now + duration, priority: PRIORITY.complete, kind: "complete", patientId: patient.spec.id, resourceId: resource.id, stage });
  };

  const tryAssignRegistration = () => {
    for (const resource of resources) {
      if (resource.state !== "idle" || resource.workstream !== "fast_registration") continue;
      if (queues.fast_registration.length > 0) {
        const patientId = queues.fast_registration.shift();
        const patient = patientId ? patients.get(patientId) : undefined;
        if (!patient) continue;
        startService(resource, patient, "fast_registration", false);
        continue;
      }
      if (scenario.policies.fastCounterOverflowEnabled && queues.slow_registration.length > 0) {
        const patientId = queues.slow_registration.shift();
        const patient = patientId ? patients.get(patientId) : undefined;
        if (!patient) continue;
        startService(resource, patient, "slow_registration", true);
      }
    }
    for (const resource of resources) {
      if (resource.state !== "idle" || resource.workstream !== "slow_registration") continue;
      if (queues.slow_registration.length === 0) continue;
      const patientId = queues.slow_registration.shift();
      const patient = patientId ? patients.get(patientId) : undefined;
      if (!patient) continue;
      startService(resource, patient, "slow_registration", false);
    }
  };

  const tryAssign = (stage: Workstream) => {
    if (isRegistrationStage(stage)) {
      tryAssignRegistration();
      return;
    }
    while (queues[stage].length > 0) {
      const resource = idleFor(stage);
      if (!resource) return;
      const patientId = queues[stage].shift();
      if (!patientId) return;
      const patient = patients.get(patientId);
      if (!patient) continue;
      startService(resource, patient, stage, false);
    }
  };

  const enqueue = (patient: PatientRuntime, stage: Workstream, nextState: PatientState) => {
    patient.state = nextState;
    patient.stageEnteredAt = now;
    queues[stage].push(patient.spec.id);
    emit("queued", `${patient.spec.ticketId} queued for ${stage.replaceAll("_", " ")}`, {
      patientId: patient.spec.id,
      ticketId: patient.spec.ticketId,
      stage,
      nextState,
    });
    tryAssign(stage);
  };

  const completeRegistration = (patient: PatientRuntime, resource: Resource, stage: Workstream) => {
    patient.adminWait = patient.arrivedAt === null ? 0 : now - patient.arrivedAt;
    if (serial) {
      emit("document_passed", `Documents interpreted at the serial counter for ${patient.spec.ticketId}`, {
        patientId: patient.spec.id,
        ticketId: patient.spec.ticketId,
      });
      emit("service_completed", `${patient.spec.ticketId} finished registration`, {
        patientId: patient.spec.id,
        ticketId: patient.spec.ticketId,
        resourceId: resource.id,
        stage,
        nextState: "ready",
      });
      enqueue(patient, "consult", "waiting_consult");
      return;
    }
    const routed = nextAfterAdmin(patient.spec, false);
    if (routed.stage === "review") {
      emit("document_required_review", `${patient.spec.ticketId} needs assisted review on the same ticket`, {
        patientId: patient.spec.id,
        ticketId: patient.spec.ticketId,
      });
      emit("service_completed", `${patient.spec.ticketId} finished check-in`, {
        patientId: patient.spec.id,
        ticketId: patient.spec.ticketId,
        resourceId: resource.id,
        stage,
        nextState: routed.state,
      });
      enqueue(patient, "review", routed.state);
      return;
    }
    emit("document_passed", `${patient.spec.ticketId} is ready on the original ticket`, {
      patientId: patient.spec.id,
      ticketId: patient.spec.ticketId,
    });
    emit("service_completed", `${patient.spec.ticketId} finished check-in`, {
      patientId: patient.spec.id,
      ticketId: patient.spec.ticketId,
      resourceId: resource.id,
      stage,
      nextState: "ready",
    });
    enqueue(patient, "consult", "waiting_consult");
  };

  for (const spec of cohort) {
    push({ time: spec.arrivalMinute, priority: PRIORITY.arrive, kind: "arrive", patientId: spec.id });
  }
  if (scenario.policies.allocationAdvisorEnabled) {
    for (let tick = 10; tick < scenario.durationMinutes; tick += 5) {
      push({ time: tick, priority: PRIORITY.advisor, kind: "advisor" });
    }
  }
  if (options.injections?.includes("dependency_outage")) {
    push({ time: 45, priority: PRIORITY.outage, kind: "outage" });
    push({ time: 65, priority: PRIORITY.recover, kind: "recover" });
  }
  push({ time: scenario.durationMinutes, priority: PRIORITY.end, kind: "end" });

  emit("scenario_started", `${scenario.label} started with seed ${scenario.seed}.`);
  const approvals = new Map((options.approvals ?? []).map((item) => [item.recommendationId, item.decision]));

  while (queue.length > 0) {
    queue.sort((left, right) => left.time - right.time || left.priority - right.priority || left.seq - right.seq);
    const event = queue.shift();
    if (!event || event.time > scenario.durationMinutes) break;
    const elapsed = event.time - now;
    if (elapsed > 0) {
      for (const resource of resources) resource.availableMinutes += elapsed;
    }
    now = event.time;

    if (event.kind === "arrive" && event.patientId) {
      const patient = patients.get(event.patientId);
      if (!patient || patient.state !== "not_arrived") continue;
      patient.state = "waiting_check_in";
      patient.arrivedAt = now;
      patient.ticketAssignedAt = now;
      patient.stageEnteredAt = now;
      emit("patient_arrived", `${patient.spec.ticketId} arrived (${patient.spec.intake.replace("_", "-")})`, {
        patientId: patient.spec.id,
        ticketId: patient.spec.ticketId,
      });
      if (isFastEligible(patient.spec, scenario.policies.preRegistrationEnabled)) {
        emit("document_passed", `Pre-arrival documents already processed for ${patient.spec.ticketId}`, {
          patientId: patient.spec.id,
          ticketId: patient.spec.ticketId,
        });
      }
      enqueue(patient, arrivalLane(patient.spec, scenario.policies.preRegistrationEnabled, serial), "waiting_check_in");
    } else if (event.kind === "complete" && event.patientId && event.resourceId && event.stage) {
      const patient = patients.get(event.patientId);
      const resource = resources.find((item) => item.id === event.resourceId);
      if (!patient || !resource) continue;
      if (resource.busySince !== null) resource.busyMinutes += now - resource.busySince;
      resource.state = "idle";
      resource.patientId = null;
      resource.busySince = null;
      resource.remainingMinutes = null;
      patient.resourceId = null;

      if (isRegistrationStage(event.stage)) {
        completeRegistration(patient, resource, event.stage);
      } else if (event.stage === "review") {
        patient.reviewWait = patient.reviewStartedAt === null ? 0 : now - patient.reviewStartedAt;
        emit("review_resolved", `${patient.spec.ticketId} returned to ready on ${patient.spec.ticketId}`, {
          patientId: patient.spec.id,
          ticketId: patient.spec.ticketId,
          resourceId: resource.id,
          stage: event.stage,
        });
        emit("service_completed", `${patient.spec.ticketId} finished review`, {
          patientId: patient.spec.id,
          ticketId: patient.spec.ticketId,
          resourceId: resource.id,
          stage: event.stage,
          nextState: "ready",
        });
        enqueue(patient, "consult", "waiting_consult");
      } else if (event.stage === "consult") {
        const routed = nextAfterConsult(patient.spec);
        emit("service_completed", `${patient.spec.ticketId} finished consultation`, {
          patientId: patient.spec.id,
          ticketId: patient.spec.ticketId,
          resourceId: resource.id,
          stage: event.stage,
          nextState: routed.state,
        });
        enqueue(patient, routed.stage, routed.state);
      } else if (event.stage === "pharmacy") {
        emit("service_completed", `${patient.spec.ticketId} finished pharmacy`, {
          patientId: patient.spec.id,
          ticketId: patient.spec.ticketId,
          resourceId: resource.id,
          stage: event.stage,
          nextState: "waiting_billing",
        });
        enqueue(patient, "billing", "waiting_billing");
      } else if (event.stage === "billing") {
        emit("service_completed", `${patient.spec.ticketId} finished billing`, {
          patientId: patient.spec.id,
          ticketId: patient.spec.ticketId,
          resourceId: resource.id,
          stage: event.stage,
          nextState: "completed",
        });
        patient.state = "completed";
        emit("patient_exited", `${patient.spec.ticketId} completed the visit`, {
          patientId: patient.spec.id,
          ticketId: patient.spec.ticketId,
          nextState: "completed",
        });
      }
      tryAssign(event.stage);
    } else if (event.kind === "advisor") {
      const reviewLoad =
        queues.review.length + resources.filter((resource) => resource.workstream === "review" && resource.state === "busy").length;
      if (reviewLoad >= 2) pressureMinutes += 5;
      else pressureMinutes = 0;
      if (!recommendationIssued && pressureMinutes >= 10) {
        const flexible = resources.find((resource) => resource.kind === "flexible");
        if (flexible && flexible.workstream === "registration") {
          recommendationIssued = true;
          const recommendation: Recommendation = {
            id: "A-SIM-001",
            generatedAt: now,
            expiresAt: now + 20,
            workstream: "review",
            fromResourceId: flexible.id,
            toWorkstream: "review",
            durationMinutes: 30,
            evidence: `Review load held ${reviewLoad} tickets for ${pressureMinutes} minutes. Flexible counter ${flexible.id} is eligible for review work.`,
            expectedP90ReductionMinutes: 6,
            noChangeP90Wait: computeMetrics([...patients.values()], resources, queues, now, recommendations).adminWaitP90 ?? 0,
            status: "pending",
          };
          recommendations.push(recommendation);
          emit(
            "recommendation_generated",
            `Move ${flexible.id} to review for ${recommendation.durationMinutes} min. Expected review P90 −${recommendation.expectedP90ReductionMinutes} min.`,
            { resourceId: flexible.id, stage: "review" },
          );
          const decision = approvals.get(recommendation.id) ?? (scenario.policies.recommendationApproval === "auto" ? "approved" : undefined);
          if (decision === "approved") {
            recommendation.status = "approved";
            emit("recommendation_approved", `Approved ${recommendation.id}`, { resourceId: flexible.id });
            emit("reassignment_started", `${flexible.id} leaving registration`, { resourceId: flexible.id });
            flexible.state = flexible.patientId ? "busy" : "reassignment_pending";
            push({ time: now + 3, priority: PRIORITY.reassign, kind: "reassign", resourceId: flexible.id });
          } else if (decision === "rejected") {
            recommendation.status = "rejected";
            emit("recommendation_rejected", `Rejected ${recommendation.id}`, { resourceId: flexible.id });
          } else {
            push({ time: recommendation.expiresAt, priority: PRIORITY.expire, kind: "expire" });
          }
        }
      }
    } else if (event.kind === "expire") {
      const pending = recommendations.find((item) => item.status === "pending");
      if (pending) {
        pending.status = "expired";
        emit("recommendation_expired", `${pending.id} expired without approval`);
      }
    } else if (event.kind === "reassign" && event.resourceId) {
      const resource = resources.find((item) => item.id === event.resourceId);
      if (!resource || resource.patientId) {
        if (resource) push({ time: now + 1, priority: PRIORITY.reassign, kind: "reassign", resourceId: resource.id });
        continue;
      }
      resource.workstream = "review";
      resource.state = "idle";
      emit("reassignment_completed", `${resource.id} now serving review`, { resourceId: resource.id, stage: "review" });
      tryAssign("review");
    } else if (event.kind === "outage") {
      emit("dependency_outage_started", "Registration dependency unavailable. Automated readiness transitions pause.");
      for (const resource of resources) {
        if (isRegistrationCounter(resource) && !resource.patientId) resource.state = "unavailable";
      }
    } else if (event.kind === "recover") {
      emit("dependency_outage_recovered", "Registration dependency recovered. Existing tickets keep their original waiting age.");
      for (const resource of resources) {
        if (resource.state === "unavailable") resource.state = "idle";
      }
      tryAssignRegistration();
    } else if (event.kind === "end") {
      break;
    }
  }

  emit("scenario_completed", `${scenario.label} reached the simulation window.`);
  const metrics = computeMetrics([...patients.values()], resources, queues, now, recommendations);
  const baselineP90 = recommendations[0]?.noChangeP90Wait ?? null;
  if (baselineP90 !== null && metrics.adminWaitP90 !== null && recommendations.some((item) => item.status === "approved")) {
    metrics.recommendationEffectMinutes = baselineP90 - metrics.adminWaitP90;
  }

  return {
    scenario,
    seed: scenario.seed,
    scenarioVersion: SCENARIO_VERSION,
    assumptionsVersion: ASSUMPTIONS_VERSION,
    policyVersion: POLICY_VERSION,
    snapshotHash: snapshotHash(scenario.id, scenario.seed),
    cohort,
    events,
    recommendations,
    resources: resources.map((resource) => ({
      id: resource.id,
      kind: resource.kind,
      workstream: resource.workstream,
      state: "idle",
      ticketId: null,
      remainingMinutes: null,
    })),
    metrics,
    interventions: [
      ...(options.resourceOverrides ? ["pre_run_resource_override"] : []),
      ...(options.injections ?? []),
      ...(options.approvals ?? []).map((item) => `${item.decision}:${item.recommendationId}`),
    ],
  };
}

export function exportRunJson(run: SimulationRun): string {
  return JSON.stringify(
    {
      scenario: run.scenario.id,
      seed: run.seed,
      scenarioVersion: run.scenarioVersion,
      snapshotHash: run.snapshotHash,
      synthetic: true,
      metrics: run.metrics,
      events: run.events,
    },
    null,
    2,
  );
}

export function exportRunCsv(run: SimulationRun): string {
  const header = "time,sequence,type,ticket_id,resource_id,stage,message";
  const rows = run.events.map((event) =>
    [event.time, event.sequence, event.type, event.ticketId ?? "", event.resourceId ?? "", event.stage ?? "", `"${event.message.replaceAll('"', "'")}"`].join(","),
  );
  return [header, ...rows].join("\n");
}

export function patientSnapshotsAt(run: SimulationRun, time: number): PatientSnapshot[] {
  return projectState(run, time).patients;
}
