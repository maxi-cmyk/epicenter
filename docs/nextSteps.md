# Epicenter delivery roadmap

## Goal

Deliver Epicenter as two independent frontend applications—patient and nurse—using one FastAPI backend and one Supabase source of truth. Complete and verify persistence, authorization, workflow, simulator, and MCP contracts before final visual polish and deployment.

## Current state

| Area | Status | Notes |
| --- | --- | --- |
| Frontend split | Complete | Independent patient and nurse Next.js applications build locally. |
| Supabase foundation | Live and verified | The original raw-data import and first operational migration passed verification. |
| Expanded operational schema | Live and verified | The follow-up migration, operational seed, and expanded verification SQL all passed against the synthetic Supabase project. |
| Shared backend boundary | Live and verified | Supabase repositories, transactional RPC calls, concurrency controls, audit, and protected staff routes passed local tests and the live persistence verifier. |
| Auth | Complete locally | Patient signup/mapping, staff clinic/role authorization, strict Clerk reverification, and the real-session authorization suite pass against the development Clerk and hosted Supabase projects. Production credential handoff remains a deployment concern. |
| Patient panel journey | In progress | Signed-in Home → Coverage → Questionnaire → Queue → Payment → Records is wired for the synthetic Loh Wei Ming / APT-DEMO-014 path, including patient-safe APIs and an appointment-scoped upload link. Kiosk parity and the full journey validation matrix remain. |
| AI and MCP integration | Complete locally | The authenticated nurse assistant, governed document pipeline, and two client-neutral Streamable HTTP MCP endpoints are implemented and independently verified. Copilot Studio remains a deployment check. |
| Analytics presentation | Scoped, not started | Build the native dashboard and simulator from FastAPI/Supabase contracts. Power BI/Fabric is deferred to a future aggregate-only scale option. |
| Deployment | Not started | Everything is still local. Railway and Vercel have not been deployed. |

## Scope

### Included

- Separate patient and nurse frontends with shared, typed contracts.
- FastAPI as the only privileged operational-data boundary.
- Supabase schema, deterministic synthetic seed, private operational access, and verification.
- Separate Clerk patient enrollment and administrator-controlled nurse provisioning.
- Patient registration, readiness outcome, one queue ticket, and counter assignment.
- Simplified nurse workflow, controlled CRUD, simulator, audit, and MCP tools.
- Vercel frontend deployment and Railway API, worker, and MCP deployment.

### Excluded

- Automated clinical urgency or identity/e-card verification.
- Privileged Supabase keys or unrestricted operational queries in a browser.
- Raw SQL in the nurse panel.
- Online learning from live patient documents.
- Live Clinic Assist, NEHR, TPA, or payment integrations.
- Production-scale patient identity and access management.
- Power BI/Fabric implementation during development or as a P0 dependency.
- Copilot Studio as a local runtime or a dependency of the patient/nurse applications; only deployment/publication compatibility is required.

## Tasks

### 1. Split the frontend into two deployable apps

**Status: Complete**

- [x] Create independent `frontend/patient/` and `frontend/nurse/` Next.js workspaces.
- [x] Restrict `frontend/shared/` to typed contracts, global tokens, and safe UI primitives.
- [x] Give each app its own environment example, validation, scripts, route tree, build output, and Vercel root.
- [x] Verify that neither production artifact contains the other panel's routes.
- [x] Point both apps to the same versioned FastAPI API.

### 2. Complete the Supabase operational schema and seed

**Status: Complete — expanded scope applied and verified live**

The original task covered importing the raw fixtures. The operational audit showed that production workflows also require explicit outcomes, import exceptions, coverage reuse, registration validation, notifications, soft deletion, and transactional database functions.

Completed:

- [x] Import and verify the raw dataset: 300 registrations, 60 questionnaires, and 9 documents.
- [x] Record the six unmatched questionnaire imports as explicit exceptions instead of silently dropping them.
- [x] Add clinics, appointments, queue tickets, staff roles, counters, availability, attestations, audit events, configuration versions, simulator snapshots, and simulator runs.
- [x] Add patient-safe `accepted`, `rejected`, and `under_review` outcomes and reasons.
- [x] Add coverage documents, eligibility rules/matches, reuse decisions, submissions, and notifications.
- [x] Add soft deletion and immutable audit/evidence protections.
- [x] Expand the idempotent operational seed with appointments, staff, counters, one-ticket cases, administrative-urgency flags, review cases, outcomes, and simulator runs.
- [x] Add verification for counts, identifier joins, RLS, grants, one-ticket invariants, all three outcomes, and zero false-ready cases.
- [x] Keep browser roles away from operational tables and privileged RPC functions; the service key remains backend-only. This also accommodates Supabase's current opt-in Data API exposure model.

Live verification:

- [x] Apply `supabase/migrations/20260812023811_complete_operational_boundary.sql` to the synthetic Supabase project.
- [x] Run `supabase/operational_seed.sql` successfully.
- [x] Run `supabase/verify_operational.sql` successfully, including counts, joins, RLS/grants, one-ticket invariants, outcomes, and zero false-ready checks.

Supabase advisor review remains part of the broader release gate in Task 11; it does not block completion of the schema-and-seed task.

### 3. Replace demo repositories with the shared persistence/backend boundary

**Status: Complete — local and live persistence verification passed**

The task grew from a repository swap into a full transactional boundary because queue, document, allocation, and CRUD writes require replay safety, conflict detection, audit attribution, and clinic scope.

Completed:

- [x] Add a Supabase Data API client and operational repository adapter.
- [x] Select Supabase automatically when the URL and server secret are configured; retain an explicit in-memory fixture mode for isolated local demos/tests.
- [x] Implement registration validation and pre-arrival submission services.
- [x] Implement document/readiness processing and patient-safe outcomes.
- [x] Preserve one `Q-*` ticket and its original waiting age across review and routing.
- [x] Implement queue transitions, kiosk check-in, counter assignment, and staff dashboard reads.
- [x] Implement allocation decision and simulator snapshot reads.
- [x] Implement allowlisted patient list/detail/create/update/soft-delete and audit reads.
- [x] Add idempotency keys and optimistic-concurrency versions to writes.
- [x] Translate database conflicts into API `409` responses.
- [x] Add server-side Clerk JWT verification plus active staff role/clinic lookup for protected staff endpoints.
- [x] Add backend unit/API/SQL-contract tests and a live-persistence verification script.
- [x] Update patient and nurse clients to send current record versions and unique idempotency keys.

Live verification:

- [x] Complete Task 2's expanded live migration, seed, and SQL verification.
- [x] Run `backend/scripts/verify_live_persistence.py` against Supabase.
- [x] Pass dashboard, replay, stale-write `409`, one-ticket preservation, audit, simulator, patient-search, and browser-denial checks against the expanded live schema.

Local auth note: both development nurse accounts are now mapped, and the ignored local backend environment uses `EPICENTER_DEMO_MODE=false`. Fixture-only tests may explicitly enable demo mode; production must always fail closed with it set to `false`.

### 4. Implement separate Clerk patient enrollment and nurse provisioning

**Status: Complete — development provisioning, authorization boundaries, strict reverification, and live end-to-end verification pass**

- [x] Verify staff Clerk session tokens server-side.
- [x] Map a staff Clerk `sub` to one active `staff_accounts` record and enforce clinic scope.
- [x] Return `403` for unmapped, disabled, or wrong-clinic staff mappings when production auth is enabled.
- [x] Add public account creation only to the patient panel, with no role selector.
- [x] Map each verified patient Clerk `sub` to exactly one configured synthetic `patient_accounts` record.
- [x] Scope production patient registration and pre-arrival requests to the mapped patient and reject other appointments.
- [x] Keep the nurse panel sign-in-only.
- [x] Add unit coverage for valid staff/patient mappings, wrong-clinic staff, unmapped patients, and patient activation.
- [x] Directly create two administrator-controlled Clerk development nurse accounts and attach their Clerk `sub` values to `staff_noor` and `staff_aisyah` without committing provider IDs.
- [x] Document the `+clerk_test` email-code flow and fixed development OTP for the two local nurse fixtures.
- [x] Add role-specific authorization tests for patient, registration nurse, operations administrator, auditor, disabled, unmapped, and wrong-clinic users.
- [x] Require Clerk strict reverification, with a ten-minute freshness window and graceful strongest-available-factor downgrade, for staff mutations.
- [x] Document development judge nurse sign-in and unique patient test-email instructions without committing provider IDs or credentials.
- [x] Test real patient signup, nurse sign-in, cross-panel denial, disablement, audit attribution, and Clerk reverification end to end against the development providers.

Live verification:

- [x] Run `npm run test:auth-live`: seven Playwright checks passed with local demo mode disabled.
- [x] Confirm a temporary patient can sign up with a Clerk test address and access the patient flow while the same session is denied by the nurse panel.
- [x] Confirm both mapped nurse roles reach the real Supabase-backed board and authorization remains role-scoped.
- [x] Confirm a disabled staff mapping is denied immediately and restored after the test.
- [x] Confirm Clerk's verification prompt completes by email code and retries the protected mutation.
- [x] Confirm a real ticket mutation records the authenticated Clerk actor in Supabase audit history, then restore the fixture state.

Production or externally delivered judge credentials are intentionally not repository artifacts. Provisioning and secure handoff for deployed instances remain in Task 12.

See [auth.md](./auth.md) for the identity contract.

## Simplified cross-panel workflow contract

Tasks 5 and 6 implement one connected visit workflow rather than two unrelated feature lists. The patient panel moves document submission and genuinely new questions before arrival; the nurse panel turns the prepared record or remaining exception into one owned next action. Both panels use the same backend visit, readiness, notification, questionnaire, queue, billing, and audit records.

### Patient journey

```text
Sign in or open appointment-scoped link
  → See one upcoming appointment and what is needed
  → Confirm prior coverage or upload a replacement
  → Complete only the appointment-required questionnaire
  → Resolve one patient-safe issue or reminder, when present
  → Receive accepted / rejected / under-review outcome and next step
  → Arrive and retain one Q-* ticket through check-in, review, service, and completion
  → View assigned counter, queue progress, payment state, and visit history
```

### Nurse journey

```text
Sign in
  → Today opens the oldest actionable visit
  → Review compact validated facts and the one unresolved next action
  → Record manual red-flag and identity/e-card attestations at physical contact
  → Confirm, correct, request patient action, or keep under review on the same task
  → Accept / reject with safe reason / retain under review
  → Route the same Q-* ticket without resetting its original waiting age
  → Move to the next visit; use Review, Patients, Simulator, or Audit only when needed
```

### 18-hour bottleneck and target-state fit

The supplied project material reinforces the PRD's quantified problem: approximately 23–32 administrative minutes per patient, or about 1,080 cumulative minutes (18 staff-hours) for 40 morning patients at an illustrative 27-minute average. TPA cases add duplicate entry at registration and again after the visit, while one complex document can delay the serial queue behind it.

| Current bottleneck | Simplified product response | Boundary |
| --- | --- | --- |
| Corporate forms and authorization letters are interpreted only after arrival | Submit before arrival, extract once with source evidence, and present a prepared record for confirmation | Staff confirms the result; extraction never becomes an unreviewed coverage decision |
| Corporate/issuer codes, TPA rules, screening packages, and billing arrangements are resolved separately | Run one versioned deterministic matching/readiness evaluation and return either one prepared result or one explicit exception | Ambiguous, missing, expired, conflicting, or unsupported inputs remain under review |
| Identity, coverage, package, questionnaire, allergy, and billing facts are repeatedly re-entered or re-checked | Reuse one source-aware confirmed record across the visit and ask only genuinely new or mandatory confirmation questions | In-person identity/e-card and clinical safety checks remain human-performed |
| TPA details are entered at registration and re-entered after the visit | Produce one structured clinic record and conceptual TPA payload from the same confirmed facts | Live TPA submission remains deferred and no transport success counts as business acceptance |
| One difficult document blocks everyone behind it | Let prepared visits proceed while staff resolves the exception in Review on the same persistent ticket | Review is an internal worklist, never a second queue or loss of waiting age |

Cross-panel acceptance criteria:

- [ ] A patient can complete the happy path without seeing staff-only reasons, confidence values, audit data, or unrelated records.
- [ ] A nurse can complete the oldest actionable visit from Today without opening the generic Patients database browser.
- [ ] Every patient-facing request becomes a staff-visible state, and every staff request for patient action becomes a patient-safe message with a concrete next step.
- [ ] Loading, empty, permission, validation, stale, offline, retry, duplicate, expired-link, and session-expiry states preserve the user's progress and never fabricate success.
- [ ] The same appointment, readiness record, and `Q-*` ticket reconcile across both panels; review is internal work and never a second patient queue.
- [ ] Timed representative tests compare the complete manual path with the simplified path and report staff time, touches, repeated fields, corrections, and unresolved exceptions without presenting assumptions as observed clinic outcomes.

### 5. Finish the patient panel

**Status: In progress — signed-in journey screens and patient-safe APIs are wired for the synthetic demo path; broader validation and hosted persistence for every journey branch remain**

Completed foundation:

- [x] Add a clearly labelled synthetic registration/pre-arrival flow.
- [x] Add registration-validation, pre-arrival submission, coverage reuse/replace, and patient-safe outcome contracts.
- [x] Represent `accepted`, `rejected`, and `under_review` without exposing internal review details.
- [x] Connect the production-mode patient Clerk account mapping and bearer-token API bridge from Task 4.

Simplified patient experience:

- [x] Make one upcoming-appointment card the signed-in home state, showing appointment time/location, completion summary, one primary next action, and secondary access to queue, payment, and history.
- [x] Support the separate appointment-scoped upload link without turning it into a full account or exposing a public patient lookup.
- [x] Implement the Singpass Login/Myinfo adapter contract and exact field comparison; keep the hackathon response visibly synthetic until a real approved sandbox is connected.
- [x] Implement the check-first coverage branch exactly: show prior issuer/date, then `Yes, same coverage` or `No, upload new document`; reuse the source document but re-run current validity and eligibility rules.
- [x] Complete camera/file upload, preview, replace, progress, processing, timeout, unsupported/oversized file, extraction failure, and retry states without losing the selected file or claiming approval.
- [x] Show only patient-safe accepted, rejected, or under-review outcomes, with one curated reason/next action when the patient can resolve the issue.
- [x] Add the appointment-selected General Health or Occupational Health questionnaire with consented read-only prefill, conditional fields, autosave, resume, review, and explicit submission.
- [x] Persist first-time signup onboarding (Singpass confirm, insurance step, questionnaire answers, completion) to Supabase via `patient_onboarding_states` / `appointment_questionnaire_responses` when `persistence_mode=supabase`.
- [x] Reuse confirmed identity/contact/allergy data across registration, questionnaire, TPA preview, pharmacy confirmation, and billing without silently overwriting source records.
- [x] Ask patients only for genuinely missing, changed, appointment-specific, consent, or acknowledgement fields; show prefilled source/provenance instead of repeating editable entry controls.
- [x] Show one live `Q-*` ticket, assigned counter, current stage, last-updated/stale state, refresh/realtime recovery, and completion; never expose internal ready/review routing as a second queue.
- [x] Add demo payment and visit/coverage history states while clearly labelling mocked payment and preventing edits to immutable evidence/audit history.
- [x] Persist signed-in home / queue / payment / records from Supabase (`epicenter_get_patient_*` RPCs + `payments`), scoped to the Clerk-linked patient account (demo maps to seeded `registration:0107` and stores the Clerk email on `patient_accounts`).

Patient validation:

- [ ] Support the same required questionnaire and coverage capture at the nurse-supervised walk-in kiosk without weakening physical nurse-led red-flag escalation.
- [ ] Verify incomplete prerequisites become actionable `under_review` cases and never block staff-led urgent escalation.
- [ ] Prove a patient cannot access internal reasons, extraction confidence, rules, audit history, full identifiers, or another patient's appointment/ticket.
- [ ] Test first-time, returning, no-appointment, no-prior-coverage, reusable-coverage, rejected, under-review, ready, queue, completed, expired-link, offline, session-expired, and provider-unavailable journeys on mobile and desktop.

### 6. Implement the simplified nurse task flow

**Status: Complete for the approved nurse-panel demo scope — the standalone Assisted Review panel has been retired; administrative exceptions are handled inside the affected visit. Pharmacy queue work remains a separate deferred follow-on below.**

Completed foundation:

- [x] Provide local Today/dashboard, kiosk, ticket-transition, document-result, and counter-assignment flows.
- [x] Preserve the original ticket and waiting age when a case enters review.
- [x] Carry idempotency and expected-version values through nurse mutations.
- [x] Rebuild the single-ticket nurse task screen as an explicit, gated multi-step flow (identity/e-card → forms guidance → forms review → confirm package → billing & queue → summary) matching `docs/nurse-workflow.md`'s System/Patient/Nurse ordering, with per-step persisted confirmation state (`identity_confirmed`, `forms_confirmed`, `package_confirmed`, `billing_confirmed`, `physical_forms_received`) and dedicated backend endpoints for each new gate.
- [x] Restore the needs-review evidence panel as a precursor gate that blocks entry into the step pipeline until the administrative exception is resolved, instead of folding it into one flat page section.
- [x] Skip the package-confirmation step entirely for tickets with no payer documents on file, since there is nothing to recheck against.
- [x] Wire the Incoming → Ongoing visit-phase transition into the summary step (previously a dead navigation-only link with no backend call).

Navigation and daily workflow:

- [x] Make `Today` the default route and group the single persistent visit ticket into Incoming, Ongoing, and Finished columns.
- [x] Limit nurse primary navigation to `Today`, `Database`, and `Audit trail`; keep visit work contextual instead of exposing a second review queue.
- [x] Open each actionable Today card directly into its next incomplete nurse step, with source evidence expanded only when the visit has an administrative exception.
- [x] Keep the original `Q-*` ticket, ordering timestamp, waiting age, readiness state, and visit phase together through the nurse workflow.
- [x] Keep the Audit destination read-only for active nurse and pharmacist demo accounts.

Single visit task:

- [x] Keep appointment context, original `Q-*` ticket, readiness exception evidence, attestations, and permitted intake actions within one visit flow.
- [x] Capture staff-performed manual identity/e-card attestations at physical contact; the system records who/when (`identity_confirmed_by`/`_at`) but never performs or infers the checks. Red-flag/clinical escalation capture (`clinical_escalation`) predates this task and remains a separate field.
- [x] Let staff inspect source evidence and record a resolution method without leaving the visit; keep the visit under review until the established readiness prerequisites pass.
- [x] Require Clerk reverification for the review decision and other protected nurse mutations.
- [x] Present issuer, document facts, screening package, validity, billing code, uncovered cost, and queue number as prepared confirmation steps rather than duplicate entry screens.
- [x] Transition Incoming → Ongoing while preserving the same ticket, ordering timestamp, versioned mutations, and audit history.
- [x] Record the physical identity/e-card, electronic forms, package, billing, and physical-form hand-off confirmations with staff attribution.

Deferred nurse-panel extensions (not required for this demo close-out): date history, staff-set administrative priority and manual kanban reordering, reschedule/cancel/no-show controls, outbound patient messaging, conceptual TPA preview, and the post-consultation Ongoing → Finished action. These require additional lifecycle and audit contracts rather than UI-only controls.

Nurse validation and workload:

- [ ] Verify registration staff, nurse, operations administrator, auditor, billing, and pharmacy roles see only permitted facts/actions and that sensitive reveals/mutations require current reverification. The demo has no doctor role.
- [ ] Test empty/loading/permission/stale/offline/conflict/duplicate/retry/session-expiry states; failed commits must preserve input, queue state, and the patient's original position.
- [ ] Measure end-to-end administrative time, touches, repeated entries, corrections, errors, and perceived workload for representative registration/nurse tasks; compare against the documented 23–32-minute manual baseline without treating the estimate as measured clinic performance.
- [x] Keep physical clinical escalation separate from administrative readiness and never create a second patient queue for review.

Pharmacy queue (incoming/outgoing TPA checklist) — scoped, not started:

- [ ] Split `PharmacyQueueBoard` into two columns: Incoming (consultation finished, medication not yet dispensed) and Outgoing (medication dispensed, TPA portal uploads pending).
- [ ] Move a ticket from Incoming to Outgoing when a medication dispense is recorded on it, but only if it carries coverage documents; a ticket with no coverage documents completes and drops off the board immediately on dispense instead of entering Outgoing.
- [ ] Replace the outgoing ticket's single "Confirm & submit to TPA" action with a checklist: one row per distinct TPA company (`issuer_name`) on the ticket's coverage documents, each linking out to that company's portal via a static `issuer_name -> URL` config table maintained in code.
- [ ] Clear the outgoing ticket once every TPA company row on it is checked off.
- [ ] Track per-ticket dispensed state and per-company checked state as new fields alongside the existing in-memory medication/TPA demo data; this persistence still moves to Supabase only as part of Task 8's deferred follow-on.

### 7. Add intentional staff database access

**Status: Complete for the approved patient-record demo scope — nurse management and pharmacy read access delivered**

- [x] Add allowlisted patient list, detail, create, update, and recoverable soft-delete endpoints through FastAPI.
- [x] Add search, pagination, optimistic concurrency, idempotency, and audit attribution at the backend boundary.
- [x] Add a separate Database tab to both nurse and pharmacy navigation; keep Audit as its own independent, read-only tab.
- [x] Build the patient browser with a top search bar, contact filters, sorting, pagination, loading, empty, error, and responsive states.
- [x] Make a row click expose View, Update, and Delete for authorised nurse/administrator accounts; pharmacists receive View only for patient identity/contact records.
- [x] Allow authenticated nurse/administrator Create and View without an extra password prompt.
- [x] Require password reverification only when committing Update or Delete, using a centered modal with the copy “Enter password to make this change”.
- [x] Submit the password directly to Clerk's session-verification flow, clear it from UI state, refresh the signed session proof, and retain backend freshness enforcement before the mutation.
- [x] Preserve update drafts and deletion reasons when the password modal is cancelled or verification fails.
- [x] Keep hard delete unavailable; deletion remains recoverable, version-checked, idempotent, and audit-attributed.
- [x] Test role permissions, create-without-step-up, update-with-step-up, stale writes, duplicate protection, and the separate Database/Audit route contract.

Deferred beyond this task: a generic medication/TPA/payment data editor. Pharmacists continue to commit those records through the dedicated pharmacy workflow; the Database tab must not become a raw SQL or unrestricted operational-table console.

### 8. Build the immutable, read-only Audit panel

**Status: Complete — synthetic demo scope delivered and verified**

Task 8 is closed against the approved demo boundary. Audit is a separate, read-only accountability surface. It records committed activity without exposing an audit create, edit, delete, restore, annotation, or correction path. Database-owner and migration privileges remain separately governed infrastructure access; the UI does not present immutability as cryptographic tamper proof.

Completed scope:

- [x] Allow nurse (`registration`) and pharmacist demo accounts to open the clinic-scoped Audit panel; the demo has no doctor role.
- [x] Add the Audit destination to both nurse and pharmacy navigation while retaining operations-administrator and auditor API access.
- [x] Keep audit history read-only in both applications and expose no general audit mutation endpoint.
- [x] Store append-only audit records with server-generated identifiers/timestamps, actor reference and event-time demo role, action, target, structured details, and clinic scope.
- [x] Reject `UPDATE` and `DELETE` on `audit_log` and `operational_events` with database triggers, and keep operational tables unavailable to browser database roles.
- [x] Record current registration, pre-arrival, document, readiness, walk-in, counter, allocation, patient, pharmacy, billing, and visit-completion activity supported by the demo workflows.
- [x] Record medication name, quantity, unit cost, total, dispensing actor/time, and visit timestamps.
- [x] Record synthetic TPA mode, status, safe document references, medication reference, external reference, submitting actor/time, and visit timestamps.
- [x] Record synthetic payment amount-due confirmation mode/status, currency, billing code, amount, queue number, confirming actor/time, and visit timestamps without presenting it as a real payment transaction.
- [x] Record scheduled, checked-in, and completed visit timestamps, with idempotent replays producing no duplicate event.
- [x] Apply server-side redaction to identifier hashes, full identity values, raw document text, tokens, secrets, provider identifiers, and unnecessary contact fields.
- [x] Send `Cache-Control: no-store` and fail rather than substituting fixture audit history when retrieval is unavailable.
- [x] Provide a prominent debounced search bar plus date, actor, role, action, outcome, and target filters through the clinic-scoped backend query.
- [x] Provide bounded newest-first pagination, clear/no-results behavior, structured event details, and CSV/JSON export of the visible authorized filtered page.
- [x] Provide distinct loading, empty, permission/API failure, retry, and session-bound states without leaking a prior user's history.
- [x] Make the table and detail view responsive, keyboard accessible, screen-reader labelled, and understandable without colour alone.
- [x] Seed deterministic synthetic nurse, pharmacist, and system history so the demo does not open to an unexplained empty panel.
- [x] Add API role, field-coverage, idempotency, defensive-copy, date-filter, redaction-boundary, and missing-mutation-route tests.
- [x] Regenerate and verify the OpenAPI/TypeScript contract and update both frontend API clients.
- [x] Pass focused backend tests and lint, the non-MCP backend suite, frontend tests/type checks/builds, contract checks, Markdown rendering, desktop/mobile nurse and pharmacy visual QA, design checks, and `git diff --check`.

Production follow-ons, outside Task 8's demo scope:

- Provision a distinct least-privileged audit-read permission instead of granting access from nurse or pharmacist job titles.
- Move medication, TPA, payment, and visit-completion demo persistence to Supabase while preserving the field contract above.
- Add cursor pagination, stable action-taxonomy versioning, retention/backup/restore policy, audit-read/export security telemetry, and a new-event refresh indicator.
- Reconcile the fresh-install schema snapshot, immutable grants/triggers/indexes, query plans, and service-role tamper tests as part of the backend release gate.
- Extend exact-once reconciliation and authenticated browser coverage as each remaining workflow in Tasks 5–7 becomes persistent.

### 9. Build the simulator inside the nurse panel

**Status: Partial — the three initial versioned snapshots/runs and nurse-only read API exist; the engine, animated tab, metric adapters, and comparison controls remain**

The Simulator is a dedicated nurse-panel tab for replaying a clinic day as a controllable animation. It should make operational measures understandable by showing the same queue, wait, throughput, utilisation, bottleneck, and allocation data both as moving clinic flow and as synchronized charts. Queue movement must come from the deterministic simulation event log—not from animation timers or model output—while de-identified aggregates come from the shared FastAPI/Supabase metric adapter.

Seeded starting scenarios, kept first:

1. `serial_baseline` — one serial administrative line using the shared arrivals and sampled service times.
2. `single_ticket` — Epicenter readiness and assisted review while preserving one ticket and its original waiting age.
3. `dynamic_allocation` — the same Epicenter flow with a human-approved counter reallocation.

Completed foundation:

- [x] Store deterministic, versioned, de-identified simulator snapshots and completed runs in Supabase fixtures.
- [x] Seed the serial baseline, single-ticket, and dynamic-allocation scenarios in the order above with the same seed (`20260809`).
- [x] Add a nurse-only read contract for active snapshots.

Simulation engine and data contracts:

- [ ] Expand the minimal seeded payloads into validated scenario fixtures containing arrivals, stage/service-time samples, resources, breaks, routing rules, interventions, assumptions, and a timezone-aware simulation window.
- [ ] Implement a pure deterministic discrete-event engine whose event log is the source of truth for the animation and derived metrics.
- [ ] Freeze the chosen versioned snapshot at run start so database or metric refreshes cannot change an in-progress replay.
- [ ] Keep the simulator in isolated synthetic types/storage and deny it write access to operational patient, queue, staffing, and audit tables.
- [ ] Add one shared de-identified metric contract for queue length, oldest wait, P50/P90 wait, throughput, work in progress, utilisation, readiness, review clearance, fairness gap, and allocation effect.
- [ ] Use the shared FastAPI/Supabase metric adapter for the dashboard, custom Operations MCP, and simulator; label the source, snapshot time, assumptions, and stale/unavailable state.
- [ ] Ensure the normal database-backed dashboard and simulator remain usable when OpenAI or either custom MCP endpoint is unavailable, delayed, or disabled.

Simulator tab and playback:

- [ ] Add a role-scoped `Simulator` route/tab to the nurse navigation without interrupting the Today workflow.
- [ ] Visualize patients moving through arrival, registration, assisted review, consultation/screening, pharmacy, billing, and exit, alongside resource busy/idle/break/reassignment states.
- [ ] Add run, pause, single-step, reset, replay/scrub, and fast-forward controls from `1×` to at least `50×`, with the current simulated date and time always visible.
- [ ] At high speed, aggregate transitions while preserving exact engine results; reduced-motion mode must remain understandable without path animation.
- [ ] Synchronize the clinic animation with queue timelines, live metric cards, bottleneck indicators, recommendation events, and the immutable event log.
- [ ] Allow bounded pre-run resource changes plus labelled walk-in-surge, downstream-bottleneck, and dependency-outage injections.
- [ ] Show an assumptions drawer distinguishing fixture-backed values, illustrative values, selected seed, scenario/policy versions, metric source, and interventions.
- [ ] Export the run summary and event log as JSON/CSV without patient identifiers.

Comparison and allocation behavior:

- [ ] Compare baseline and alternative behavior with identical arrivals, seeds, and sampled service times; flag incompatible comparisons instead of presenting them as evidence.
- [ ] Support side-by-side or overlay comparison of queue movement and key metrics, including where registration improvements move the bottleneck to doctors or pharmacy.
- [ ] Implement allocation recommendation evidence plus approve, modify, reject, expiry, and reversal behavior; only approved simulated changes may affect the replay.
- [ ] Cover known administrative urgency and pending/completed manual identity verification without inferring clinical urgency.

Decisions intentionally left for later:

- [ ] Choose the clinic day/date window to simulate and document why it is representative; do not hard-code that product decision into the engine.
- [ ] Review whether the current seeded `dynamic_allocation` run should remain the labelled ideal-state comparison, be renamed as a recommended-policy scenario, or be replaced after the representative day and assumptions are chosen.
- [ ] Confirm the native Next.js dashboard as the sole analytics presentation layer and select the chart library after accessibility, bundle-size, animation, and testing tradeoffs are evaluated.

Validation and safety:

- [ ] Prove same scenario/version/seed/configuration produces the same event log and metrics after reset or replay.
- [ ] Prove one patient retains exactly one ticket and original waiting age, patient counts are conserved, resources cannot serve two patients, and queues/metrics reconcile exactly with the exported event log.
- [ ] Prove simulation cannot write operational tables, expose identifiers, infer clinical urgency, create a second ticket, reset waiting age, or enact an unapproved/expired allocation.
- [ ] Test empty queues, simultaneous events, midnight/day boundaries, stale or missing metric data, provider outage, invalid fixtures, very high queue volume, pause/reset during activity, and high-speed rendering.
- [ ] Verify keyboard controls, screen-reader labels, non-colour state cues, reduced motion, responsive layout, and readable aggregation at `50×`.

### 10. Deliver the OpenAI assistant and Copilot-compatible MCP layer

**Status: Complete locally — provider-backed live calls and Copilot Studio publication remain deployment checks in Task 12**

- [x] Add the server-side OpenAI Responses API adapter with environment validation, bounded timeouts/retries/output, usage metadata, `store=false`, and safe provider-error handling.
- [x] Expose narrow Epicenter Operations read/explain and synthetic-simulator tools over client-neutral Streamable HTTP for the Responses API remote MCP tool.
- [x] Build the maker/checker Insurance Format Registry MCP using only approved synthetic or formally de-identified templates.
- [x] Stage extracted facts with source evidence and `pending_review`; promote only staff-confirmed facts through the shared backend.
- [x] Prevent OpenAI and every tool/MCP adapter from learning from live patient records, writing canonical tables directly, or deciding eligibility.
- [x] Add queue, de-identified operational-summary, allocation-explanation, and simulator tools using curated FastAPI/Supabase contracts; do not expose arbitrary SQL.
- [x] Build the authenticated nurse assistant UI and FastAPI orchestration route. The browser never receives the OpenAI API key or calls the provider directly.
- [x] Allow only task-relevant tools per request and re-authorize every tool execution against the signed-in actor, role, clinic, and record scope.
- [x] Require a named owner, unique capability, least privilege, data boundary, tests, and removal criteria for every additional AI tool or MCP endpoint.
- [x] Keep tool names, schemas, authentication boundaries, annotations, and errors portable: no OpenAI-only MCP extension is required for discovery or calls.
- [x] Verify initialization, `tools/list`, valid/invalid calls, authorization, timeouts, response bounds, and audit attribution with the independent Python MCP client and backend contract tests before cloud deployment.
- [x] Keep the MCP inventory limited to the custom Operations and Insurance Format Registry servers; no Microsoft-hosted, duplicate, or generic data-access MCP is present.
- [x] Do not build Power BI during development. The native Next.js dashboard remains P0; Power BI/Fabric is only a future de-identified aggregate projection.

**Document classification pipeline (feeds the Insurance Format Registry MCP)**

Before any field extraction runs, an uploaded/scanned document must first be classified into one of the `DocumentCategory` values (`form`, `authorisation_letter`, `benefit_structure`, `coding_scheme`) — extraction logic is category-specific and should never run generically across all document types. This applies to payer paperwork broadly (TPA, CHAS, corporate insurance), not TPA specifically. Proposed four-step triage, cheapest/most-certain checks first:

- [x] **Step 1 — structural triage** (cheap, no content understanding): classify bounded page-count, letterhead, handwriting, and table/grid signals before content rules.
- [x] **Step 2 — keyword/anchor-phrase scan**: use the reviewed consent, payment-authorisation, CHAS, corporate-panel, and issuer anchors.
- [x] **Step 3 — template fingerprint match**: match approved layout fingerprints to a known issuer/family and category after the keyword pass.
- [x] **Step 4 — category-specific extraction**: select a category/family-specific extractor before any OpenAI extraction call; generic unclassified extraction is not callable.

This governs what reaches `QueueTicket.documents`: the nurse and pharmacist screens render only documents present in intake and successfully classified, with no placeholder for an undetected category. The deterministic classifier now implements steps 1–3, and the worker requires its category/family-specific extractor selection before step 4 can call OpenAI. Results are staged with evidence as `pending_review`; the seeded Q-020 records remain pre-classified fixtures so their existing demo presentation is stable.

CHAS and corporate-insurance eligibility-to-package matching is a separate, already-implemented mechanism — see the note under Task 6/cross-panel workflow below; it does not go through this Document/DocumentCategory model at all.

### 11. Pass the backend release gate, then finalise visual design

**Status: Partial — local automated checks pass; live, security, and browser gates remain**

- [x] Run the current backend unit/API/SQL-contract suite.
- [x] Run frontend tests, type checks, lint, contract checks, and production builds for both apps.
- [ ] Verify fresh-install migration parity with `backend/persistence/schema.sql`.
- [x] Complete Task 2's live seed-integrity and RLS/grant checks.
- [ ] Run Supabase security/performance advisors and resolve applicable findings.
- [ ] Complete patient/nurse authorization, step-up CRUD, simulator-invariant, and MCP adversarial tests.
- [ ] Run complete browser journeys for success, failure, retry, and stale states.
- [ ] Finalise palette, typography, status tokens, responsive layouts, WCAG AA contrast, colour-vision checks, and separate patient/nurse visual QA without changing workflow semantics.

### 12. Deploy and verify the complete system

**Status: In progress — Procfile, document_jobs migration, and Railway service config documented; Vercel not yet deployed**

- [ ] Create separate Vercel projects for patient and nurse apps.
- [x] Deploy the FastAPI/MCP service and private worker to Railway. *(Procfile added; two-service config documented: epicenter-api-mcp on web process, epicenter-worker on worker process, both rooted at `backend/`)*
- [ ] Allowlist both exact Vercel origins.
- [ ] Apply production-intended Supabase migrations and synthetic seed. *(document_jobs migration added: `20260812100000_document_jobs_and_worker_rpcs.sql`)*
- [ ] Configure Clerk and the supported Supabase integration.
- [x] Configure the server-side `OPENAI_API_KEY` and evaluated model identifier in Railway secrets without exposing either to the browser. *(env vars documented in .env.example; defaults pinned: OPENAI_MODEL=gpt-4.1-mini, OPENAI_EXTRACTION_MODEL=gpt-4.1)*
- [ ] Deploy and smoke-test the authenticated nurse assistant route against reviewed operations tools.
- [x] Keep Insurance Format Registry tools restricted to the separate maker/reviewer workflow.
- [ ] Add both public Streamable HTTP MCP endpoints to Copilot Studio and verify that only intended tools are discovered.
- [x] Do not add Microsoft-hosted MCPs; integrate future external services only through separately approved application adapters while the two custom MCPs remain the agent tool plane.
- [ ] Reconcile one Copilot Studio read-only synthetic operations call with the native API/dashboard and record the server version, authentication mode, test evidence, and rollback steps.
- [ ] Complete the applicable Copilot Studio publication/licensing gate; if the available trial permits testing but not publishing, report that limitation without claiming the channel is published.
- [ ] Verify that disabling OpenAI or either custom MCP does not affect either web application or the database-backed analytics/simulator path.
- [ ] Run authenticated public-origin smoke tests through Railway to Supabase.
- [ ] Verify health, restart behavior, audit persistence, remote Git refs, and rollback instructions.

## Immediate next actions

1. Continue Tasks 5, 7, and 9 using the persistence and authorization foundations already completed; Tasks 6, 8, and 10 are complete for their approved local demo scope.
2. Run the deployed Copilot Studio compatibility check only after Railway exposes the same two reviewed MCP endpoints over HTTPS.
3. Deploy Railway/Vercel only after the backend release gate passes locally and against the synthetic Supabase project.
4. Provision production nurse identities and distribute judge credentials outside the repository as part of Task 12.

## Open questions

- Will the judged build use a live Singpass/Myinfo sandbox, or the documented synthetic adapter only?
- Which authentication mode and Copilot Studio licence/publication path will be approved for the deployed compatibility check?
- OpenAI model confirmed: OPENAI_EXTRACTION_MODEL=gpt-4.1, OPENAI_MODEL=gpt-4.1-mini — pin after fixture comparison across the nine synthetic document formats.
