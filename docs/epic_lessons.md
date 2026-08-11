# Lessons from Epic and Large-Scale EHR Implementations

## Epicenter Safety and Delivery Audit

- **Status:** Design input and risk-control checklist
- **Scope:** Documented Epic-specific failures plus broader EHR implementation failure patterns relevant to Epicenter
- **Related documents:** [PRD.md](./PRD.md), [design.md](./design.md), [techStack.md](./techStack.md), [simulator.md](./simulator.md), and [microsoft_mcp.md](./microsoft_mcp.md)
- **Last reviewed:** 9 August 2026

## 1. Interpretation Boundary

Epic is a large electronic health record platform, while Epicenter is a narrower clinical-operations and administrative system. Epicenter should not claim that every reported EHR problem was caused solely by Epic software: outcomes often reflect local configuration, data migration, training, staffing, governance, and rollout decisions as much as the vendor product.

The useful question is therefore:

> Which documented failure patterns from Epic deployments and EHR systems could recur in Epicenter, and what concrete controls prevent or expose them?

## 2. Evidence-Based Lessons

### 2.1 A model that performs well internally can fail locally

An external validation of the proprietary Epic Sepsis Model reported substantially poorer performance at the evaluating health system than the performance described in vendor materials. The lesson is not limited to sepsis: a model, threshold, or rule must not be trusted because it worked on the developer's data.

**Epicenter implication:**

- The LLM extracts facts but cannot decide eligibility, billing, readiness, staffing, or clinical priority.
- Fixture accuracy is necessary but insufficient. Run new extraction/rule versions in shadow mode against local, clinic-approved examples before they can affect readiness.
- Measure errors by document type and issuer, not only overall accuracy.
- Maintain a zero-tolerance `false_ready` release gate and an immediate rollback path.
- Store model, prompt, schema, and rule versions with every result.

**Source:** [External Validation of a Widely Implemented Proprietary Sepsis Prediction Model in Hospitalized Patients](https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2781307), JAMA Internal Medicine, 2021.

### 2.2 Digitising a poor workflow can increase workload

Studies of Epic and other EHR transitions found that confidence may improve while efficiency, patient flow, after-shift work, and documentation burden remain problematic. Poor usability is associated with cognitive workload and burnout. A system can complete transactions correctly and still fail its users.

**Epicenter implication:**

- Evaluate complete role-based tasks, not screenshots or feature completion.
- Measure task completion time, staff touches, correction rate, navigation steps, after-task cleanup, errors, and perceived workload.
- Test registration, review, pharmacy, billing, operations, and downtime workflows with the actual role that performs them.
- Do not add a field, confirmation, dashboard, or alert unless its owner and operational purpose are explicit.
- Preserve context when staff move between queue, document, billing, and audit views.

**Sources:** [Physician experience with the Epic EHR system after emergency-department implementation](https://pubmed.ncbi.nlm.nih.gov/36006584/) and [EHR usability and workload changes following transition to a new EHR](https://pubmed.ncbi.nlm.nih.gov/33556884/).

### 2.3 Excessive alerts become a safety problem

EHR alert fatigue occurs when excessive, repeated, or low-value warnings make users less likely to notice or act on important alerts. Operational alerts can create the same failure even when they are not clinical.

**Epicenter implication:**

- Use interruptive alerts only when immediate action is required.
- Deduplicate repeated alerts for the same ticket/reason and update the existing alert instead of creating another.
- Send lower-severity events to a worklist or digest.
- Every interruptive alert needs a clear owner, action, severity, expiry, and resolution state.
- Measure alert volume, repeats, acknowledgement, action, expiry, and dismissal by alert type; review alerts with low action rates.
- Allocation advice remains a recommendation card, not a repeated interruptive alarm.

**Sources:** [AHRQ Patient Safety Network: Alert Fatigue](https://psnet.ahrq.gov/primer/alert-fatigue) and [The Elements of Style for Interruptive Electronic Health Record Alerts](https://pubmed.ncbi.nlm.nih.gov/39740769/).

### 2.4 Big-bang implementation magnifies training and workflow defects

A one-day Epic launch study found that satisfaction improved with time but workflow-specific training was perceived as inadequate and efficiency problems persisted. The UK Wachter review also used the Cambridge Epic implementation to illustrate how large digital transformations combine technology, training, workflow, leadership, and implementation risk.

**Epicenter implication:**

- Do not begin with all clinics, payers, roles, and workflows at once.
- Start in observation/shadow mode, then one bounded workflow, counter, shift, and fixture set.
- Use role-specific scenario training rather than generic product tours.
- Identify trained superusers and a staffed stabilization period.
- Publish go/no-go, pause, and rollback criteria before launch.
- Retain the current manual process until reconciliation proves the new path is complete.

**Sources:** [Epic emergency-department implementation study](https://pubmed.ncbi.nlm.nih.gov/36006584/) and the UK Department of Health's [Making IT Work: Wachter Review](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/550866/Wachter_Review_Accessible.pdf).

### 2.5 Downtime is a clinical-operations state, not merely an error screen

EHR unavailability can remove access to patient, workflow, and communication information. The US ONC SAFER Guides treat contingency planning, patient identification, interfaces, system management, and organizational responsibility as explicit safety disciplines.

**Epicenter implication:**

- Define a degraded mode that can continue safe one-time check-in without pretending automated eligibility succeeded.
- Keep manual identity/e-card verification and the clinic's approved fallback process intact.
- Issue one visible downtime ticket that maps to the canonical visit during recovery; the patient never requeues.
- Record the minimum safe fields, creation device/counter, staff actor, and timestamps without copying raw documents into insecure local storage.
- Reconcile every downtime record explicitly after recovery; conflicts never merge silently.
- Drill outage, partial dependency failure, stale data, recovery, and duplicate-event replay in the simulator.

**Source:** [ONC 2025 SAFER Guides](https://healthit.gov/clinical-quality-and-safety/safer-guides/).

### 2.6 Patient identity and copied data need visible provenance

Wrong-patient selection and copied/stale information are persistent EHR hazards. A unified record helps only when staff can distinguish current confirmed data from imported, reused, inferred, corrected, or stale data.

**Epicenter implication:**

- Preserve exact identifier matching and prohibit name-only auto-linking.
- Keep identity verification manual and in person.
- Label every displayed value by source, confirmation state, effective date, and last update where it can affect action.
- Reusing a document never reuses an eligibility decision.
- Corrections append a new value/reason/event; they do not erase the source.
- Downtime reconciliation and imports use the same conflict-safe matching policy.

**Source:** [ONC SAFER Patient Identification Guide](https://healthit.gov/resources/2025-safer-guide-patient-identification/).

### 2.7 Portals can widen access gaps

Studies of Epic MyChart and other portals have found uneven adoption among vulnerable groups and associations with language, age, income, internet/email access, and other factors. A digital pre-registration benefit can become a penalty for patients unable to use it.

**Epicenter implication:**

- Token links and demo accounts remain optional channels, not prerequisites for care.
- Staff-assisted upload and one-time walk-in processing reach the same `ready` state.
- A walk-in keeps the same ticket through processing and review.
- Monitor P50/P90 waiting differences by intake channel and, where lawful and useful, accessibility/language-support cohort using aggregate suppressed reporting.
- Test low-connectivity, no-email, language, disability, camera-denied, and shared-device journeys.

**Sources:** [Patterns of Electronic Portal Use among Vulnerable Patients using Epic MyChart](https://pubmed.ncbi.nlm.nih.gov/27613792/) and [The Digital Divide and Patient Portals](https://pubmed.ncbi.nlm.nih.gov/27314262/).

### 2.8 Integration success requires reconciliation, not only an API call

Large health systems depend on many interfaces. A request returning HTTP success does not prove that the target accepted, interpreted, and committed the intended data. Interface changes and local configuration can create silent inconsistency.

**Epicenter implication:**

- Keep provider adapters behind versioned contracts.
- Validate outgoing and incoming schemas and store the external correlation/reference.
- Model `requested`, `accepted`, `rejected`, `unknown`, and `reconciled` states separately.
- Never convert timeout/unknown into success.
- Use idempotency keys, retry limits, dead-letter review, and end-to-end reconciliation reports.
- Maintain contract fixtures for every conceptual Clinic Assist, TPA, messaging, MCP, or future FHIR-compatible adapter.

**Source:** [ONC SAFER Guides: System Management and interfaces](https://healthit.gov/clinical-quality-and-safety/safer-guides/).

### 2.9 Configuration is part of the safety case

EHR behaviour depends heavily on local rules, thresholds, permissions, mappings, alerts, and templates. Uncontrolled customization can create drift that neither the vendor nor local staff fully understand.

**Epicenter implication:**

- Treat eligibility rules, readiness gates, alert policy, service targets, allocation constraints, prompts, and mappings as versioned configuration.
- Require maker/checker approval for safety- or billing-relevant configuration.
- Run fixture and regression tests before activation.
- Use effective dates and atomic activation; retain the previous version for rollback.
- Record which version governed every decision and simulation.
- Review unused, overridden, noisy, or low-action configuration on a schedule.

## 3. Current Epicenter Coverage

| Failure pattern | Existing coverage | Gap addressed by this audit |
| --- | --- | --- |
| Opaque model drives action | LLM extraction separated from deterministic rules; evidence and staff confirmation required | Shadow validation, segmented error review, release/rollback gate |
| Wrong-patient attachment | Exact identifier matching, no name-only auto-link, manual identity check | Apply same controls to imports and downtime recovery |
| Duplicate/reconstructed data | Unified record, provenance, immutable correction history | Stronger visible freshness/source labels and reconciliation |
| Serial bottleneck | Single-ticket readiness routing and assisted-review worklist | Downtime must preserve the same patient journey |
| Digital exclusion | Walk-ins can become ready; token flow is not mandatory; fairness metrics exist | Add explicit channel-parity and accessibility test matrix |
| Cognitive overload | Role-scoped screens and patient/staff separation | Add task-burden tests and progressive disclosure criteria |
| Alert fatigue | Review worklist and allocation cards are nonclinical | Add alert ownership, deduplication, severity, expiry, and action-rate governance |
| Unsafe automation | Human confirmation and deterministic gates | Add shadow-mode promotion and kill/rollback criteria |
| Big-bang rollout | Not previously defined | Add phased rollout, superusers, stabilization, go/no-go gates |
| Downtime/recovery | Refresh, stale-data, retry, and idempotency states | Add true degraded-mode ticketing and reconciliation drill |
| Interface mismatch | Provider adapters and typed APIs | Add acceptance states, external references, contract tests, and reconciliation |
| Configuration drift | Versioned rules/prompts and audit | Add maker/checker activation, regression gate, and rollback |
| Local optimisation moves bottleneck | Full-clinic simulator and downstream stress scenario | Add outage and degraded-mode scenario |

## 4. Hackathon Application

The main lesson from large EHR programmes is also a scope lesson: Epicenter should not attempt to build a miniature hospital EHR during a hackathon. Apply the safety principles where judges can see and verify them, and represent production controls honestly as contracts or simulations.

### 4.1 Build for P0

| P0 deliverable | Epic lesson applied | Smallest credible implementation |
| --- | --- | --- |
| Fixture validation report | Do not trust internal/model performance claims | Run all nine document fixtures through schema/evidence/readiness checks; show correct fields, review reasons, version, and `false_ready = 0` |
| Versioned decision trace | Configuration and model versions matter | Show document/model/prompt/schema/rule versions plus the exact readiness gates and deterministic rule used on the review screen |
| Three failure-safe cases | Automation must fail visibly | Demonstrate missing identifier, expired/ambiguous document, and extraction failure routing to assisted review without guessing |
| Single-ticket walk-in | Digitisation must not create another queue | Show one walk-in keeping the same `Q-*` ticket from processing through review to ready, with waiting age preserved |
| One restrained operational alert | Avoid alert fatigue | Use one deduplicated, expiring allocation recommendation card with evidence and Approve/Reject UI; repeated pressure updates the card rather than creating notifications |
| Comparable simulator runs | Local optimisation can move bottlenecks | Replay the same seed under serial baseline and Epicenter; show P50/P90, throughput, utilisation, fairness gap, and the new doctor/pharmacy bottleneck |
| Simulated outage injection | Downtime must be designed | Pause automated transitions, create a visible `D-*` recovery reference, then demonstrate idempotent mapping to the same visit plus one visible conflict; do not claim real offline security |
| Short role-task evaluation | Correct software can still burden users | Ask representative users to complete registration review, allocation decision, and patient-status tasks; record time, errors, confusing steps, and one improvement made |
| Channel-parity demo | Portals can widen inequity | Put one pre-registered patient and one walk-in through the system and show that both can reach `ready` without a portal requirement or second ticket |

### 4.2 Show as a contract, not a production build

- phased rollout storyboard: fixtures → shadow → one-counter assisted pilot → measured expansion;
- downtime/reconciliation data contract and simulator state, without claiming secure production offline storage;
- mocked external adapter states: requested, accepted, rejected, unknown, and reconciled;
- configuration release history with seeded draft/shadow/active/rolled-back examples;
- alert-governance metrics using seeded events; and
- go/no-go, pause, and rollback checklist in the pitch.

### 4.3 Explicitly defer

- live Clinic Assist, NEHR, insurer/TPA, payment, messaging, or production identity integration;
- real offline encrypted device storage and multi-device conflict synchronization;
- autonomous staffing changes or predictive clinical-resource allocation;
- hospital-wide, multi-clinic, or big-bang rollout machinery;
- production Power BI/Fabric/Dataverse analytics pipelines;
- independent clinical validation or claims of production/regulatory readiness; and
- comprehensive alert-governance administration UI.

### 4.4 Hackathon release gate

P0 is demo-ready when:

1. the nine-fixture report has no false-ready case;
2. the three exception cases visibly fail safe;
3. the walk-in never receives a second ticket or reset waiting age;
4. baseline and Epicenter simulator runs use the same seed and sampled patients;
5. the outage injection labels itself simulated and reconciles without a duplicate visit;
6. the allocation card cannot apply a real change without human confirmation;
7. one round of role-task testing produces recorded evidence and at least one applied usability improvement; and
8. every mocked, estimated, seeded, or synthetic output is labelled as such.

The strongest hackathon story is not “we solved hospital IT.” It is “we selected a narrow administrative problem, built observable safety boundaries around it, and can show exactly how it behaves when conditions are imperfect.”

## 5. Required Real-Clinic Release Gates

Epicenter is not ready for a real clinic pilot unless:

1. every affected role completes representative usability and downtime tasks;
2. a new extraction/rule version completes shadow validation with no false-ready case;
3. patient/channel parity and accessibility journeys pass;
4. interface reconciliation proves no lost, duplicated, or silently unknown transaction;
5. downtime intake and recovery reconcile every synthetic record without making a patient requeue;
6. interruptive alerts have an owner, action, severity, expiry, and measured baseline;
7. training, superusers, support coverage, pause criteria, and rollback ownership are named; and
8. the simulator and operational dashboard label assumptions, synthetic values, stale data, and small-cohort suppression correctly.

These are product safety gates, not claims of regulatory certification or production readiness.

## 6. Sources

- [External validation of the Epic Sepsis Model](https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2781307)
- [Epic emergency-department implementation experience](https://pubmed.ncbi.nlm.nih.gov/36006584/)
- [EHR usability and workload after transition](https://pubmed.ncbi.nlm.nih.gov/33556884/)
- [AHRQ EHR usability and patient safety](https://digital.ahrq.gov/program-overview/research-stories/improving-electronic-health-record-usability-patient-safety)
- [AHRQ Patient Safety Network: Alert Fatigue](https://psnet.ahrq.gov/primer/alert-fatigue)
- [ONC 2025 SAFER Guides](https://healthit.gov/clinical-quality-and-safety/safer-guides/)
- [UK Wachter Review](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/550866/Wachter_Review_Accessible.pdf)
- [Epic MyChart use among vulnerable patients](https://pubmed.ncbi.nlm.nih.gov/27613792/)
- [Digital divide and patient portals](https://pubmed.ncbi.nlm.nih.gov/27314262/)
