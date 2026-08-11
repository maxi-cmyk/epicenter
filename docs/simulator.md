# Clinic Operations Simulator

## Epicenter Demo Specification

- **Status:** Proposed demo extension
- **Purpose:** Make patient flow, bottlenecks, and resource-allocation effects visible and measurable
- **Related documents:** [PRD.md](./PRD.md), [design.md](./design.md), and [techStack.md](./techStack.md)

## 1. Product Question

How does Epicenter change the movement of patients and administrative work through a clinic when arrival demand, document complexity, and available staff vary over time?

The simulator should let judges see patients arrive, receive one persistent ticket, move through registration, consultation, pharmacy, billing, and exit, while counters and qualified staff become busy, idle, or reassigned. It should compare a serial baseline with Epicenter's pre-arrival processing, single-ticket readiness routing, and human-approved dynamic resource allocation.

The simulator is an explanatory and testing tool. It is not a production scheduler, a clinical digital twin, or evidence that the configured assumptions match a real Parkway Shenton clinic.

## 2. Demo Outcomes

The demo must make these claims visible:

1. One complex administrative case can block patients behind it in a serial baseline.
2. Pre-arrival processing reduces work performed during the arrival peak.
3. Ready work can continue while an exception is resolved without making that patient take another ticket.
4. A downstream resource—such as doctors or pharmacists—can become the new bottleneck after registration improves.
5. Adding resources everywhere is not necessarily efficient; reallocating qualified capacity at the right time can be more effective.
6. The Operational Intelligence Loop can identify sustained pressure and recommend a constrained allocation change.
7. The effect of an accepted recommendation can be compared with a no-change baseline.

## 3. Simulation Model

Use a deterministic, seeded discrete-event simulation. The animation must replay engine events rather than move patients using unrelated visual timers.

### 3.1 Patient Journey

```text
Scheduled arrival or walk-in
   → one ticket created/activated
   → manual identity/e-card confirmation
   → administrative processing
        ├── ready
        └── assisted review → ready on the same ticket
   → consultation / screening
   → pharmacy, when required
   → billing/payment
   → completed visit and exit
```

Each simulated patient retains one ID, one `Q-*` ticket, and one original ordering timestamp. A readiness or counter change must never create a second ticket or reset waiting age.

### 3.2 Patient Attributes

Use synthetic attributes only:

- booked or walk-in intake;
- explicit administrative-priority class supplied by the appointment source (`standard` or `administratively_urgent`), never inferred from symptoms or demographics;
- scheduled time and actual arrival time;
- pre-registration completed or incomplete;
- manual identity/e-card attestation state (`pending`, `completed`, or `unable_to_confirm`) and event time;
- document readiness result and review reason;
- consultation/screening pathway;
- pharmacy required or not required;
- covered billing or self-pay;
- service-time samples by stage; and
- current stage, ticket, waiting age, and timestamps.

No name, NRIC/FIN/passport, medical answer, real document, or other direct identifier is needed.

### 3.3 Resource Pools

| Resource | Configurable properties | Work performed |
| --- | --- | --- |
| Registration counters | Count, opening time, assigned staff | Manual check-in and identity/e-card attestation |
| Assisted-review counters | Count, qualified staff, reason-specific handling rates | Missing, expired, ambiguous, or extraction-review cases |
| Flexible counters | Count, eligible workstreams, reassignment delay | Temporarily support ready registration, review, or billing |
| Doctors | Count, shift/break windows, consultation-time distribution | Consultation only; never perform administrative review by default |
| Screening stations | Optional count and service distribution | Corporate/health-screening pathway |
| Pharmacists | Count, shift/break windows, dispensing-time distribution | Allergy confirmation and medication dispensing |
| Billing counters | Count, covered/self-pay service distributions | Billing confirmation and payment |
| Document-processing workers | Concurrency and processing-time distribution | Simulated asynchronous extraction; not represented as clinic staff |

Resources are not interchangeable. Every assignment and recommendation must satisfy configured role and skill eligibility.

### 3.4 Patient and Resource States

Patient states:

```text
not_arrived → waiting_check_in → checking_in
            → processing → needs_review → ready
            → waiting_consult → consulting
            → waiting_pharmacy → dispensing
            → waiting_billing → billing
            → completed
```

`processing` may transition directly to `ready`. `needs_review` returns to `ready` on the same ticket.

Resource states:

```text
closed / idle / busy / break / reassignment_pending / unavailable
```

### 3.5 Event Types

- scenario started, paused, resumed, reset, and completed;
- patient scheduled, arrived, queued, service started, service completed, and exited;
- document processing started, passed, or required review;
- administrative-priority appointment injected or arrived;
- manual identity/e-card attestation completed or remained unresolved;
- review started and resolved;
- resource opened, became idle/busy, started/ended break, or became unavailable;
- allocation recommendation generated, accepted, modified, rejected, expired, or reversed; and
- counter/staff reassignment started and completed.

The engine processes simultaneous events using an explicit stable priority order so the same scenario and seed always produce the same result.

## 4. Scenario Configuration

Each scenario is a versioned JSON fixture validated before a run. A fixture contains:

```json
{
  "id": "morning_peak_epicenter",
  "seed": 20260809,
  "durationMinutes": 240,
  "arrivals": {
    "booked": { "count": 32, "pattern": "appointment_schedule" },
    "walkIns": { "count": 8, "pattern": "morning_peak" }
  },
  "resources": {
    "registrationCounters": 2,
    "reviewCounters": 1,
    "flexibleCounters": 1,
    "doctors": 3,
    "screeningStations": 1,
    "pharmacists": 1,
    "billingCounters": 1,
    "documentWorkerConcurrency": 2
  },
  "policies": {
    "preRegistrationEnabled": true,
    "singleTicketRoutingEnabled": true,
    "allocationAdvisorEnabled": true,
    "recommendationApproval": "manual"
  }
}
```

All service-time distributions, routing probabilities, staffing assumptions, and thresholds must be visible in an **Assumptions** drawer. Values derived from the official brief should be labelled separately from illustrative demo assumptions.

## 5. Demo Scenarios and Stress Injections

P0 needs three primary replayable scenarios (§5.1–§5.3). The downstream and downtime cases (§5.4–§5.5) are predefined injections using the same engine and UI, not separate simulator products.

### 5.1 Serial Baseline

- One administrative line.
- Documents are interpreted after arrival.
- Complex cases block patients behind them.
- No pre-arrival readiness, exception workstream, or allocation advisor.

### 5.2 Epicenter Single-Ticket Flow

- Booked patients may be ready before arrival.
- Walk-ins begin processing at check-in.
- Exceptions are handled in the assisted-review worklist.
- Every patient keeps the same ticket and original waiting age.

### 5.3 Epicenter with Dynamic Allocation

- Same arrivals and random seed as §5.2.
- A sustained review or billing spike generates a recommendation.
- The presenter can inspect evidence and accept, modify, or reject it.
- The result is compared with the recorded no-change estimate.

### 5.4 Downstream Bottleneck Injection

- Registration capacity is improved while doctor or pharmacy capacity remains constrained.
- The visualisation demonstrates that local optimisation can move, rather than eliminate, a bottleneck.
- The dashboard identifies the constrained downstream stage without recommending clinically inappropriate staff substitution.

### 5.5 Downtime and Recovery Injection

- API/database or another configured dependency becomes unavailable during an arrival peak.
- Existing displayed data becomes visibly stale and automated readiness/eligibility transitions stop.
- Minimum-safe intake issues a stable `D-*` recovery reference without creating a second patient journey.
- Recovery replays records idempotently into canonical `Q-*` visits while preserving original waiting age.
- The scenario includes one exact reconciliation, one duplicate replay, and one identity conflict that requires staff review.
- Completion requires all generated downtime records to reconcile, conflict, or fail explicitly; no record disappears into an unknown state.

## 6. Dynamic Allocation Policy

The P0 advisor is deterministic and explainable. It runs at a configurable interval:

1. Calculate current waiting count, total waiting age, oldest waiting age, and estimated staff-minutes by workstream.
2. Add near-term demand from scheduled arrivals and the recent walk-in rate.
3. Estimate capacity from qualified available staff, active counters, current work, and planned breaks.
4. Require pressure to persist for a stability window before proposing a change.
5. Evaluate candidate moves against role/skill permissions, minimum coverage, break protection, safe handoff, and maximum reassignment frequency. Clinical capacity may move only within the same qualified role; the engine never substitutes administrative staff for doctors or pharmacists.
6. Rank valid moves by expected reduction in P90 administrative waiting time, with reassignment cost shown separately.
7. Persist the recommendation with its evidence, constraints, expiry, and no-change baseline.
8. Change the simulated allocation only after presenter approval, unless the scenario is explicitly running in policy-test mode.

Policy-test mode is for simulation experiments only and must be visibly labelled. It does not change the production requirement for human approval.

## 7. Simulator Interface

### 7.1 Main Layout

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Scenario [Epicenter + allocation ▾] Seed [20260809] Speed [10×]    │
│ [Run] [Pause] [Step] [Reset] [Compare baseline] [Assumptions]       │
├──────────────────────────────────────────────┬───────────────────────┤
│ CLINIC FLOW                                  │ LIVE METRICS          │
│                                              │ In clinic        18   │
│ Arrival → Registration → Doctor → Pharmacy  │ Completed        27   │
│                ↘ Review       ↘ Billing     │ Admin wait P90  19m   │
│                                              │ Longest stage  Doctor │
│ moving Q-* patient tokens and resource cards│ Utilisation      82%  │
├──────────────────────────────────────────────┴───────────────────────┤
│ Timeline: arrivals · queue length · utilisation · recommendations   │
├──────────────────────────────────────────────────────────────────────┤
│ Advisor: REVIEW pressure sustained for 10 min                       │
│ Move Flexible Counter 2 for 30 min · Expected review P90 −6 min     │
│ [Evidence] [Reject] [Modify] [Approve]                               │
└──────────────────────────────────────────────────────────────────────┘
```

### 7.2 Visual Rules

- Patient tokens show ticket and state, never a real identity.
- Movement occurs only when the simulation emits a stage-transition event.
- Queues show count, oldest waiting age, and service-target state.
- Resource cards show role, current state, assigned workstream, current ticket, and time remaining where known.
- Color is supplementary; every state has text and a consistent icon/shape.
- Animation respects reduced-motion settings. Reduced motion uses state changes and subtle position updates without path animation.
- At high speed, aggregate transitions rather than attempting to animate every movement.

### 7.3 Controls

- select scenario and seed;
- run, pause, single-step, reset, and speed from 1× to 50×;
- change resource counts before a run;
- inject a walk-in surge or resource outage during a run;
- inspect or act on an allocation recommendation;
- toggle baseline/Epicenter comparison; and
- export event log and summary metrics as JSON/CSV.

Changing structural assumptions during a run creates a labelled intervention event. Resetting with the same configuration and seed must reproduce the original result.

## 8. Metrics and Definitions

| Metric | Definition |
| --- | --- |
| Throughput | Patients completing the simulated visit per hour |
| Stage wait | `service_started_at - stage_queue_entered_at` |
| End-to-end time | `visit_completed_at - arrived_at` |
| P50/P90 wait | Median/90th percentile across the selected cohort and stage |
| Queue length | Patients waiting for a stage at a simulation timestamp |
| Work in progress | Arrived patients not yet completed |
| Resource utilisation | Busy eligible minutes divided by available scheduled minutes |
| First-pass readiness | Patients reaching ready without assisted review divided by processed patients |
| Review clearance time | `review_resolved_at - review_started_at` |
| Fairness gap | Walk-in P90 administrative wait minus booked P90 administrative wait |
| Reassignment churn | Approved staff/counter moves per simulated hour |
| Recommendation effect | Observed metric change versus recorded no-change baseline |
| False-ready count | Tickets reaching ready without every configured readiness gate; target zero |
| Recovery integrity | Lost, duplicated, silently merged, requeued, and unresolved-unknown downtime records; target zero for the first four and explicit ownership for every unresolved record |

Counts and averages must not conceal tail waits. The primary comparison should show throughput plus P50/P90 time, oldest waiting age, and utilisation.

## 9. Technical Design

### 9.1 Suggested Structure

```text
frontend/nurse/app/simulator/       # nurse-panel visual demo route
frontend/nurse/features/simulator/  # controls, clinic map, charts, replay
frontend/shared/simulation-core/    # pure deterministic engine, imported by nurse only
tests/fixtures/simulation/          # versioned scenario JSON
tests/simulation/                   # engine and policy tests
```

The engine should be a pure TypeScript package with no React or network dependency. The Next.js interface consumes its event stream and renders the replay. This keeps the demo self-contained, fast to reset, and deployable on Vercel without running a separate simulation service.

Use a seeded pseudo-random-number generator and a priority queue ordered by `(simulation_time, event_priority, sequence_number)`. Store the selected seed, scenario version, policy version, and interventions with every run.

### 9.2 State Separation

- Engine state is the source of truth for patients, resources, queues, and simulated time.
- UI state contains only playback position, selected panels, and presenter controls.
- Analytics derive from the immutable event log rather than reading animation positions.
- Production queue records and synthetic simulation records must use separate stores and types; the simulator never writes to operational tables.
- A run may read only a versioned de-identified Supabase seed/snapshot through the backend. The snapshot is copied into simulation state before the run, its hash/version is stored with results, and live database changes cannot alter an in-progress replay.
- Administrative priority affects only the configured appointment-ordering policy. Clinical urgency remains a physical nurse-led escalation outside the engine and is never predicted or ranked.

## 10. Validation

### Engine invariants

- the same scenario and seed produce the same event log and metrics;
- one patient has exactly one ticket;
- no patient occupies two service stages simultaneously;
- no resource serves two patients simultaneously;
- a resource performs only eligible work;
- breaks, unavailable periods, minimum coverage, and reassignment delays are respected;
- queue waiting age never resets during readiness/review transitions;
- patient counts are conserved: not-arrived + in-clinic + completed equals generated patients;
- no ticket becomes ready without all configured readiness gates; and
- an unapproved or expired recommendation cannot change resources.

### Scenario acceptance criteria

- Baseline and Epicenter comparisons reuse identical arrivals and sampled service times.
- The serial baseline visibly demonstrates blocking from one complex case.
- The single-ticket scenario shows a walk-in transition through review without a new ticket.
- The allocation scenario generates a reproducible recommendation and supports approve, modify, reject, expiry, and reversal.
- The downstream stress test correctly identifies a doctor or pharmacy bottleneck after administrative improvement.
- The downtime drill preserves a single patient journey, blocks false readiness, replays idempotently, and balances created/reconciled/conflicted/failed record counts.
- Summary metrics exactly reconcile with the exported event log.
- The interface remains understandable at 375 px and keyboard-operable at desktop sizes.

## 11. Delivery Scope

### P0 — Judged demo

- deterministic engine with three primary scenarios plus downstream-bottleneck and downtime injections;
- animated clinic-flow view with configurable resource counts;
- run/pause/step/reset/speed controls;
- live queue, wait, throughput, and utilisation metrics;
- one explainable dynamic-allocation recommendation flow;
- baseline comparison using the same seed and sampled patients;
- assumptions drawer and JSON/CSV export; and
- invariant, policy, and scenario tests.

### P1 — Calibration and experimentation

- import anonymised aggregate arrival/service distributions when clinic-approved data becomes available;
- scenario editor and saved custom scenarios;
- confidence intervals across multiple seeds;
- richer staff shifts, outages, and corporate-screening patterns; and
- comparison report suitable for operational review.

## 12. Demo Narrative

1. Run the serial baseline and pause when a complex document blocks registration.
2. Replay the identical patients with Epicenter and show pre-cleared patients proceeding while the same ticket receives assisted review.
3. Continue until review or billing pressure persists and the advisor generates a recommendation.
4. Open the evidence, show the skill/break/minimum-coverage checks, and approve the temporary move.
5. Show the effect on P90 wait, oldest-ticket age, utilisation, and reassignment churn.
6. Run the downstream stress test to show that Epicenter identifies the next bottleneck rather than claiming that registration optimisation solves the entire clinic.
7. Trigger the downtime drill and show one recovery reference reconciling without a second queue, a duplicate replay being ignored, and a conflict staying visible for staff review.
8. End on the assumptions drawer: official figures are distinguished from illustrative values, and real deployment requires calibration with clinic-approved aggregate data.
