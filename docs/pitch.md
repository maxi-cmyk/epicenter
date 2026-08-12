# Epicenter Hackathon Pitch and Priorities

## 1. Positioning

Epicenter is not a replacement for Epic, Clinic Assist, or another electronic health record. It is a focused outpatient administrative-readiness and operations layer.

It turns unstructured coverage documents into an auditable readiness state, resolves avoidable problems before arrival, and converts the remaining exception workload into explainable operational actions. Every patient keeps one visit and one queue ticket throughout the process.

> **Pitch:** Epicenter finds administrative problems before they become queues. It combines document readiness, targeted intervention, single-ticket routing, and human-approved resource recommendations in one measurable workflow.

The system is deliberately conservative: ambiguous or unusual documents route to staff review rather than being guessed, so the first-pass automation rate will be below 100% by design.

The differentiator is not any individual dashboard, reminder, or allocation algorithm. It is the closed loop connecting them:

```text
Document received
  → readiness problem detected
  → precise patient or staff intervention
  → issue resolved before arrival or retained on one ticket
  → remaining workload quantified
  → constrained allocation recommendation
  → outcome measured
  → rules and reminders improved
```

## 2. What Makes Epicenter Worth Building

Large EHR and command-centre products already provide patient-flow dashboards, capacity forecasting, alerts, and operational analytics. Epicenter should not compete by claiming those capabilities are new.

Epicenter's narrower advantage is that it creates an earlier operational signal from outpatient administrative documents:

- whether a patient is administratively ready before arrival;
- exactly which prerequisite remains unresolved;
- whether a targeted intervention corrected it;
- how much review work remains at the arrival peak;
- whether qualified capacity should be temporarily rebalanced; and
- whether that action improved the patient journey without moving the bottleneck elsewhere.

This makes operational intelligence an extension of the core readiness workflow rather than a disconnected dashboard product.

Staff still confirm every determination. The system's contribution is collapsing 3–5 minutes of document reading into an estimated ~30-second confirmation action; that estimate is a demo assumption to validate with timed staff testing, not a measured clinic result.

For booked patients, processing happens before arrival. For walk-ins, processing still happens at the counter, but document interpretation and rules matching are automated rather than performed manually; walk-ins receive the processing-speed benefit, not the pre-arrival benefit.

## 3. Hackathon Priorities

### P0 — Build and Show

P0 must form one complete, credible vertical slice. If a feature does not strengthen this story, it is not a hackathon priority.

| Priority | Deliverable | What judges must see | Proof |
| --- | --- | --- | --- |
| 1 | Document-to-readiness workflow | A coverage document becomes structured facts with source evidence and deterministic readiness gates | Correct fixture output, explicit review reasons, and zero false-ready cases |
| 2 | Pre-arrival intervention | A missing or invalid prerequisite creates one precise reminder or staff action | The issue is resolved, expires, or remains visibly unresolved; no silent success |
| 3 | Single-ticket routing | Ready work proceeds while an exception is handled without making the patient queue again | One stable `Q-*` ticket, preserved arrival time, and visible state transitions |
| 4 | Operational intelligence | A small dashboard explains current pressure and recurring administrative friction | Readiness rate, P50/P90 wait, oldest-ticket age, staff touches, and exception reasons |
| 5 | Constrained allocation advice | Sustained pressure creates one explainable, expiring recommendation | Evidence, qualified resource, constraints checked, no-change baseline, expected effect, and Approve/Reject action |
| 6 | Comparable simulator | Identical synthetic arrivals are replayed under the baseline and Epicenter | Same seed and sampled patients, assumptions visible, and downstream bottlenecks shown |
| 7 | Safety and trust | Ambiguous, missing, expired, or failed inputs stop safely | Staff confirmation, audit trail, version trace, stale state, and clear synthetic/mock labels |

#### P0 implementation boundaries

- Use deterministic readiness rules after extraction; model confidence never overrides a failed gate.
- Use one actionable, deduplicated operational alert rather than a general notification centre.
- Keep allocation deterministic, explainable, human-approved, and limited to qualified resources.
- Measure workstreams, not individual employee productivity.
- Keep walk-ins on the same ticket while first-pass processing moves them to `ready` or `needs_review`.
- Treat doctor and pharmacist stages as downstream capacity constraints in the simulator, not as an autonomous clinical staffing product.
- Mock message delivery, payment, and external-system acceptance while showing honest sending, failure, retry, and reconciliation states.
- Label every seeded, estimated, mocked, and synthetic value.

### P1 — Extend After the Core Demo Works

| Extension | Why it is P1 |
| --- | --- |
| Additional native analytics charts and OpenAI assistant questions | Useful extensions after the core operational loop is proven |
| Power BI/Fabric aggregate analytics projection | Potential multi-clinic scale option after native metrics are stable; not needed for the core demo and does not require a Power BI MCP |
| Calibrated forecasting across multiple days or clinics | Requires representative historical operational data |
| Multiple allocation policies and confidence intervals | Useful for evaluation after the deterministic policy is validated |
| Rich alert-governance administration | P0 needs only one well-governed alert and visible action-rate evidence |
| Corporate batch-screening workflow | Valuable scale extension, but the existing incoming board can seed grouped appointments for the demo |
| Live SMS or email provider | Adds delivery risk without changing the judged workflow logic |
| Production EHR, Clinic Assist, NEHR, insurer, or TPA adapters | Requires access, governance, reconciliation, security review, and partner participation |
| Multi-clinic command centre | Risks making Epicenter look like a smaller copy of established capacity-management products |

Copilot Studio compatibility is a deployment/publication release gate, not a P1 product feature. Development uses OpenAI and the native dashboard; Copilot Studio connects only to the deployed custom Epicenter MCPs. Microsoft-hosted MCPs are not part of the product architecture.

### Explicitly Deferred

- replacement of an EHR or clinic-management system;
- autonomous staffing or counter changes;
- clinical prioritisation, diagnosis, treatment, or urgency scoring;
- assignment of clinical work across unqualified roles;
- production patient identity, self-registration, recovery, and access administration;
- automated identity or e-card verification;
- real payment processing;
- production offline storage and multi-device reconciliation;
- individual staff rankings or productivity surveillance; and
- claims of production accuracy, regulatory readiness, or real-clinic impact from synthetic data.

## 4. Recommended Demo Narrative

### Scene 1 — Establish the problem

Show a morning arrival peak containing:

- one administratively ready booked patient;
- one booked patient with a missing document;
- one patient with an expired or ambiguous document; and
- one walk-in.

In the serial baseline, document handling blocks the counter and increases the wait for everyone behind the exception.

### Scene 2 — Move work before arrival

Replay the same patients with Epicenter. The system identifies the missing prerequisite before the appointment and sends one targeted reminder. The patient resolves it, and the readiness record records what changed and why.

The ambiguous case is not guessed or marked ready. It remains visible for assisted review, making clear that first-pass automation is intentionally below 100%.

### Scene 3 — Prove there is only one queue journey

The walk-in receives one ticket. First-pass processing updates that ticket to `ready` or `needs_review`; the patient never takes a second number and never loses the original waiting age.

### Scene 4 — Turn workflow events into intelligence

Open the operational view and show only the measures needed to explain the decision:

- readiness before arrival;
- current work by stage;
- P50 and P90 total wait;
- oldest-ticket age;
- staff touches; and
- top reason-coded exceptions.

### Scene 5 — Recommend, do not command

Allow review pressure to persist long enough to trigger one recommendation. Open its evidence and show:

- the pressured workstream;
- estimated staff-minutes;
- the qualified available resource;
- break and minimum-coverage checks;
- reassignment cost;
- expected effect and no-change baseline; and
- expiry time.

The presenter approves or rejects the recommendation. The system records the decision rather than silently changing staffing.

### Scene 6 — Show honest limits

Continue the simulation until consultation or pharmacy becomes the next bottleneck. This proves Epicenter measures the whole visit instead of claiming that faster registration solves the entire clinic.

End with the assumptions and limitations drawer: all outcomes are synthetic, production integrations are conceptual, and a real deployment requires clinic-approved calibration and a shadow pilot.

## 5. Metrics That Support the Pitch

Lead with operational and safety outcomes, not the number of AI features.

| Outcome | Demo measure |
| --- | --- |
| Problems prevented before arrival | Percentage and count of prerequisite issues resolved before check-in |
| First-pass completion | Share reaching `ready` without repeated data entry or another queue ticket |
| Patient experience | Total-visit P50/P90, oldest-ticket age, and status enquiries avoided |
| Staff burden | Staff touches, correction count, and assisted-review clearance time |
| Fair access | Booked-versus-walk-in wait gap and ability to reach `ready` without a portal |
| Readiness safety | False-ready count, with a demo target of zero |
| Alert quality | Action, expiry, and duplicate-suppression outcome for the single reminder or allocation card |
| Allocation value | Result against the same-seed no-change baseline, including reassignment cost |
| System honesty | Visible stale, failed, ambiguous, mocked, estimated, and synthetic states |

Do not claim a percentage improvement unless the comparison uses identical arrivals and sampled service times. Simulator results demonstrate system behaviour under disclosed assumptions; they are not observed clinic outcomes.

## 6. Judge Objections and Responses

| Objection | Response |
| --- | --- |
| “Is this another EHR?” | No. Epicenter does not own the clinical record or replace clinic systems; it resolves a narrow pre-registration and administrative-readiness problem. |
| “Don't existing systems already have dashboards?” | Yes. The dashboard is not the invention. Epicenter's value is the closed loop from document-derived readiness to intervention, remaining workload, action, and measured outcome. |
| “A supervisor can move staff manually.” | Correct. Epicenter supports that decision with sustained-pressure evidence, constraint checks, a no-change baseline, expiry, and an auditable human decision. |
| “Will patients be sent to another queue?” | No. Review is an internal work state on the same visit and ticket; original waiting age and ordering are preserved. |
| “Are the results real?” | The document fixtures test concrete behaviour. Flow improvements are seeded simulations and are labelled as such; a real clinic would require calibration and shadow validation. |
| “Will staff get flooded with alerts?” | P0 demonstrates one owned, actionable, deduplicated, expiring alert and measures what happened to it. |
| “Does AI decide coverage or staffing?” | No. Extraction produces evidence; deterministic rules gate readiness; authorised staff confirm every determination and approve allocation changes. Ambiguous or unusual documents route to review rather than being guessed. |

## 7. Delivery Order and Cut Line

Build in this order:

1. fixture-backed extraction and readiness gates;
2. review workflow and one persistent ticket;
3. pre-arrival reminder lifecycle;
4. deterministic same-seed simulator baseline and Epicenter replay;
5. minimal operational metrics;
6. one constrained allocation recommendation;
7. failure-state and downstream-bottleneck demonstration;
8. the authenticated Epicenter assistant using OpenAI to call one safe, read-only operations tool.
9. deployment evidence that the same MCP contract is discoverable and callable from Copilot Studio, without making Copilot part of the local application path.

If time runs short, cut in this order:

1. Power BI/Fabric implementation and additional assistant tools or analytics visualizations;
2. additional charts and filters;
3. multiple recommendation types;
4. live message delivery;
5. patient payment and records polish;
6. additional simulator scenarios beyond the baseline, Epicenter, downstream-pressure, and downtime injections.

Never cut the deterministic readiness gates, single-ticket invariant, human approval, synthetic-data labels, or comparable baseline. Those are what make the demonstration credible.

## 8. Closing Message

> Epicenter does not try to rebuild hospital infrastructure. It targets the administrative uncertainty that becomes tomorrow's queue. By resolving what it can before arrival, preserving one patient journey when it cannot, and turning the remaining workload into explainable human decisions, Epicenter makes outpatient operations more predictable, auditable, and fair.
