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
| AI and MCP integration | Scoped, not started | OpenAI is the development/application LLM; custom Streamable HTTP MCP endpoints will remain client-neutral and be verified in Copilot Studio after deployment. |
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

Supabase advisor review remains part of the broader release gate in Task 10; it does not block completion of the schema-and-seed task.

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

Production or externally delivered judge credentials are intentionally not repository artifacts. Provisioning and secure handoff for deployed instances remain in Task 11.

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

**Status: Partial — core dashboard, review, kiosk, queue mutations, and authorization contracts exist; the one-task Today workflow, contextual tools, and full lifecycle states remain**

Completed foundation:

- [x] Provide local Today/dashboard, review, kiosk, ticket-transition, document-result, and counter-assignment flows.
- [x] Preserve the original ticket and waiting age when a case enters review.
- [x] Carry idempotency and expected-version values through nurse mutations.

Navigation and daily workflow:

- [ ] Limit primary navigation to `Today`, `Review`, `Patients`, `Simulator`, and `Audit`; open upload, extraction correction, billing, notifications, and counter actions contextually from a visit instead of as competing top-level destinations.
- [ ] Make Today the default route with date selection and Incoming, Ongoing, and Finished groups backed by one queue-entry lifecycle.
- [ ] Prioritize the oldest actionable visit while respecting already-called patients, explicit clinic administrative priority, staff role/skill scope, and physical nurse-led clinical escalation.
- [ ] Show one primary next action per visit; keep validated identity, coverage, questionnaire, allergy, billing, and queue facts compact and expand only exceptions, source evidence, or history.
- [ ] Preserve selected date, filters, task state, and intended route across navigation, reverification, session expiry, retry, and back actions.

Single visit task:

- [ ] Put appointment details, original `Q-*` ticket/waiting age, readiness summary, source-backed exceptions, attestations, notifications, and permitted actions on one task screen.
- [ ] Capture staff-performed red-flag escalation and manual identity/e-card attestations at physical contact; the system records who/when but never performs or infers the checks.
- [ ] Let staff confirm extracted facts, correct one evidenced field with a reason, request a missing document, send one curated patient-safe issue message, or retain the case under review without changing screens unnecessarily.
- [ ] Complete accept, reject with a curated safe reason and next step, or keep under review from the same task, with Clerk reverification and an explicit commit summary for mutations.
- [ ] Present corporate/issuer code, TPA, screening package, requested items, validity, and billing arrangement together as one prepared confirmation block instead of separate re-entry screens.
- [ ] Generate a read-only conceptual TPA payload preview from the same confirmed record so the demo proves duplicate-entry removal without claiming a live portal submission.
- [ ] Transition Incoming → Ongoing → Finished and assign actual counters while preserving the same ticket, appointment/check-in ordering timestamp, audit trail, and recoverable failure state.
- [ ] Support reschedule, cancel, no-show, billing confirmation, TPA preview, pharmacy allergy attestation, and visit completion as role-scoped contextual actions.

Nurse validation and workload:

- [ ] Verify registration staff, nurse, operations administrator, auditor, billing, and pharmacy roles see only permitted facts/actions and that sensitive reveals/mutations require current reverification.
- [ ] Test empty/loading/permission/stale/offline/conflict/duplicate/retry/session-expiry states; failed commits must preserve input, queue state, and the patient's original position.
- [ ] Measure end-to-end administrative time, touches, repeated entries, corrections, errors, and perceived workload for representative registration/nurse tasks; compare against the documented 23–32-minute manual baseline without treating the estimate as measured clinic performance.
- [ ] Prove the simplified Today flow completes the oldest actionable visit without requiring the generic Patients browser and never blocks physical urgent escalation or the core visit.

### 7. Add intentional nurse-side database CRUD

**Status: Partial — secured backend CRUD contract and strict step-up auth exist; nurse UI and explicit commit flow remain**

- [x] Add allowlisted patient list, detail, create, update, and recoverable soft-delete endpoints through FastAPI.
- [x] Add search, pagination, optimistic concurrency, idempotency, and audit attribution at the backend boundary.
- [x] Keep audit/evidence records immutable and operational tables unavailable to browser roles.
- [ ] Build the nurse Patients browser with search, filter, sort, and pagination.
- [x] Require fresh Clerk strict reverification for every currently implemented staff mutation (completed in Task 4).
- [ ] Decide whether future sensitive data reveals require password-only reverification instead of Clerk's strongest available factor.
- [ ] Add an explicit commit screen with action, record, before/after values, and reason.
- [ ] Restrict hard delete and test permissions, reverification expiry, retries, duplicates, and stale writes end to end.

### 8. Build the simulator inside the nurse panel

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

### 9. Deliver the OpenAI assistant and Copilot-compatible MCP layer

**Status: Not started — contracts are scoped; implementation follows stable core workflows and dashboard metrics**

- [ ] Add the server-side OpenAI Responses API adapter with environment validation, timeouts, usage metadata, and safe provider-error handling.
- [ ] Expose narrow Epicenter Operations read/explain and synthetic-simulator tools over client-neutral Streamable HTTP for the Responses API remote MCP tool.
- [ ] Build the maker/checker Insurance Format Registry MCP using only approved synthetic or formally de-identified templates.
- [ ] Stage extracted facts with source evidence and `pending_review`; promote only staff-confirmed facts through the shared backend.
- [ ] Prevent OpenAI and every tool/MCP adapter from learning from live patient records, writing canonical tables directly, or deciding eligibility.
- [ ] Add queue, de-identified operational-summary, allocation-explanation, and simulator tools using curated FastAPI/Supabase contracts; do not expose arbitrary SQL.
- [ ] Build the authenticated nurse assistant UI and FastAPI orchestration route; the browser must never receive the OpenAI API key or call the provider directly.
- [ ] Allow only task-relevant tools per request and re-authorize every tool execution against the signed-in actor, role, clinic, and record scope.
- [ ] Require a named owner, unique capability, least privilege, data boundary, tests, and removal criteria for every additional AI tool or MCP endpoint.
- [ ] Keep tool names, schemas, authentication boundaries, annotations, and errors portable: do not rely on an OpenAI-only MCP extension that would prevent Copilot Studio discovery or calls.
- [ ] Verify initialization, `tools/list`, valid/invalid calls, authorization, timeouts, response bounds, and audit attribution with an independent MCP client before cloud deployment.
- [ ] Keep the MCP inventory limited to the custom Operations and Insurance Format Registry servers; reject Microsoft-hosted, duplicate, or generic data-access MCPs.
- [ ] Do not build Power BI during development. Keep the native Next.js dashboard as P0 and document Power BI/Fabric only as a future de-identified aggregate projection for enterprise scale.

### 10. Pass the backend release gate, then finalise visual design

**Status: Partial — local automated checks pass; live, security, and browser gates remain**

- [x] Run the current backend unit/API/SQL-contract suite.
- [x] Run frontend tests, type checks, lint, contract checks, and production builds for both apps.
- [ ] Verify fresh-install migration parity with `backend/persistence/schema.sql`.
- [x] Complete Task 2's live seed-integrity and RLS/grant checks.
- [ ] Run Supabase security/performance advisors and resolve applicable findings.
- [ ] Complete patient/nurse authorization, step-up CRUD, simulator-invariant, and MCP adversarial tests.
- [ ] Run complete browser journeys for success, failure, retry, and stale states.
- [ ] Finalise palette, typography, status tokens, responsive layouts, WCAG AA contrast, colour-vision checks, and separate patient/nurse visual QA without changing workflow semantics.

### 11. Deploy and verify the complete system

**Status: Not started — local only**

- [ ] Create separate Vercel projects for patient and nurse apps.
- [ ] Deploy the FastAPI/MCP service and private worker to Railway.
- [ ] Allowlist both exact Vercel origins.
- [ ] Apply production-intended Supabase migrations and synthetic seed.
- [ ] Configure Clerk and the supported Supabase integration.
- [ ] Configure the server-side `OPENAI_API_KEY` and evaluated model identifier in Railway secrets without exposing either to the browser.
- [ ] Deploy and smoke-test the authenticated nurse assistant route against reviewed operations tools.
- [ ] Keep Insurance Format Registry tools restricted to the separate maker/reviewer workflow.
- [ ] Add both public Streamable HTTP MCP endpoints to Copilot Studio and verify that only intended tools are discovered.
- [ ] Do not add Microsoft-hosted MCPs; integrate future external services only through separately approved application adapters while the two custom MCPs remain the agent tool plane.
- [ ] Reconcile one Copilot Studio read-only synthetic operations call with the native API/dashboard and record the server version, authentication mode, test evidence, and rollback steps.
- [ ] Complete the applicable Copilot Studio publication/licensing gate; if the available trial permits testing but not publishing, report that limitation without claiming the channel is published.
- [ ] Verify that disabling OpenAI or either custom MCP does not affect either web application or the database-backed analytics/simulator path.
- [ ] Run authenticated public-origin smoke tests through Railway to Supabase.
- [ ] Verify health, restart behavior, audit persistence, remote Git refs, and rollback instructions.

## Immediate next actions

1. Continue Task 5 remaining polish (tokenized-upload persistence, Singpass sandbox decision, broader journey matrix) while Task 6 nurse Today workflow proceeds in parallel.
2. Start the client-neutral MCP work only after the protected operational workflows are stable; use OpenAI during development and run the Copilot Studio compatibility check after deployment.
3. Deploy Railway/Vercel only after the backend release gate passes locally and against the synthetic Supabase project.
4. Provision production nurse identities and distribute judge credentials outside the repository as part of Task 11.

## Open questions

- Will the judged build use a live Singpass/Myinfo sandbox, or the documented synthetic adapter only?
- Which evaluated OpenAI model will be pinned separately for document extraction and staff-assistant workloads after fixture, latency, and cost comparisons?
- Which authentication mode and Copilot Studio licence/publication path will be approved for the deployed compatibility check?
- At what multi-clinic scale, if any, would a governed Power BI/Fabric aggregate projection add enough value beyond the native dashboard to justify its tenant, licensing, and reconciliation cost?
