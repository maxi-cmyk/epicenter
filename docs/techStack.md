# Technology Stack

## AI-Assisted Pre-Registration & Eligibility Verification for Parkway Shenton

- **Status:** Recommended implementation baseline
- **Sources:** [PRD.md](./PRD.md), [design.md](./design.md), and [simulator.md](./simulator.md)
- **Priority:** Hackathon speed, low operational cost, clear security boundaries, a server-side OpenAI integration, and portable MCP publication

## 1. Architecture Principles

1. **The LLM extracts; deterministic code decides.** The document model converts varied documents into structured fields. Eligibility, package, billing, and queue decisions run through versioned rules and application code.
2. **Identity and e-card checks remain manual.** The application records a staff attestation only. Identity/e-card images or automated verification results must never enter the extraction pipeline.
3. **One backend serves both interfaces.** Staff and patient views use the same records and queue state, with role- and patient-scoped authorization.
4. **Long-running document processing is asynchronous.** Upload returns quickly with a job ID; the UI follows explicit uploading, processing, ready, and failed states.
5. **Realtime is an enhancement, not the only path.** Queue screens subscribe to updates and also expose a manual Refresh action. Initial queue loading uses a fixed-layout skeletal screen.
6. **Provider integrations sit behind adapters.** Document extraction, messaging, mocked payment, and future TPA submission can be replaced without changing core rules.
7. **Clerk is the preferred identity provider.** Staff and seeded demo-patient sign-in, sessions, and sensitive-action reverification use Clerk. Appointment-scoped upload links remain opaque single-use tokens because they are not user accounts.
8. **One visit means one ticket.** Processing, readiness, review, and counter changes update one persistent queue row; no transition issues a second number or resets the patient's original check-in time.
9. **Shadow before authority.** New model, prompt, schema, rule, alert, and allocation-policy versions must prove themselves without changing live readiness before controlled activation.
10. **Downtime is a workflow.** Degraded mode, minimum-safe intake, recovery ownership, idempotent replay, and conflict reconciliation are designed and tested—not reduced to a generic error page.
11. **Alerts consume attention.** Interruptive alerts require immediate actionable conditions; ownership, deduplication, expiry, resolution, and action-rate review are part of the data contract.
12. **Integrations require acknowledgement and reconciliation.** HTTP success is transport evidence, not proof that another system accepted the intended business record.

## 2. Recommended Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Web applications | Two Next.js applications with TypeScript and App Router | Separate patient and nurse panels with shared generated API contracts only |
| UI | Tailwind CSS, shadcn/ui primitives, Lucide SVG icons | Accessible responsive components without structural emoji |
| Client data | TanStack Query | Loading/error/retry state, cache invalidation, polling fallback, and manual queue refresh |
| Forms and validation | React Hook Form + Zod | Staff corrections, attestations, questionnaires, and upload validation |
| API | FastAPI + Pydantic | Typed REST endpoints, OpenAPI contract, authorization boundary, and orchestration |
| Core business logic | Plain Python service modules | Eligibility matching, single-ticket readiness transitions, counter assignment, billing calculations, and audit creation |
| Database | Supabase Postgres | Source of truth for the data model in `design.md` |
| Authentication | Clerk | Staff accounts, seeded demo-patient accounts, sessions, and sensitive-action reverification |
| Authorization | Clerk identity + backend permissions + Postgres RLS | Separates staff roles, patient-owned data, MCP access, and upload-token scope |
| File storage | Private Supabase Storage bucket | Coverage photos/PDFs and generated demo receipts |
| Realtime queue updates | Supabase Realtime | Queue/counter changes shared between staff and patient screens |
| Background processing | Postgres-backed job table + Python worker | Reliable document extraction without adding Redis for the demo |
| Application LLM and document extraction | OpenAI Responses API with PDF/image inputs and Structured Outputs | Powers approved server-side language-model tasks and converts coverage documents into the validated extraction schema |
| Evidence mapping | Page number + supporting source excerpt | Staff-reviewable evidence without requiring a separate cloud OCR platform |
| Rules engine | Python + versioned Postgres `eligibility_rules` | Deterministic package, eligibility, billing, and queue decisions |
| Operational analytics and allocation advisor | Postgres views + plain Python rules | P50/P90 waits, near-term staff-minute demand, constraint-aware resource recommendations, and outcome measurement without a separate ML platform |
| Agent tools | Custom Epicenter Operations MCP and Insurance Format Registry MCP | Own all agent-facing domain workflows while remaining client-neutral and compatible with Copilot Studio |
| Analytics presentation | Native Next.js dashboard over FastAPI/Supabase metrics | P0 implementation; Power BI/Fabric is deferred to an optional aggregate-only scale projection |
| Deployment | Two Vercel projects; Railway for shared API/MCP/worker; managed Supabase | Independent patient/nurse releases against one backend and source of truth |
| Observability | Structured JSON logs + Railway deployment/runtime logs | Request/job tracing without logging raw NRIC or document contents |
| Testing | Vitest, React Testing Library, Playwright, Pytest | Unit, component, API, policy, and end-to-end verification |
| Tooling | pnpm, uv, ESLint, Prettier, Ruff, mypy | Reproducible installs and consistent TypeScript/Python quality checks |

Exact dependency versions should be pinned when the repository is scaffolded rather than embedded in this planning document.

## 3. System Topology

```text
Nurse browser                    Patient browser / token link
      │                                      │
Nurse Next.js app                  Patient Next.js app
      │                                      │
      └─────────────── FastAPI REST API ─────┘
                      │     │      │
                      │     │      └── OpenAI Responses API
                      │     │                 │
                      │     │                 └── reviewed Epicenter MCP tools
                      │     │
                      │     └── Postgres job queue → Python worker
                      │                                │
                      │                         OpenAI document adapter
                      │                    PDF/image → structured output
                      │                                │
                      └──────── Supabase ──────────────┘
                                ├── Postgres + RLS
                                ├── Clerk third-party auth
                                ├── Private Storage
                                └── Realtime

Copilot Studio (deployment/publication only)
      └── same public HTTPS Streamable HTTP Epicenter MCP tools

Future scale only
      └── de-identified aggregates → optional Power BI/Fabric model
```

The API and MCP server call the same service functions. MCP tools must not contain a second implementation of extraction, rules, or authorization logic.

## 4. Frontend

### 4.1 Two Next.js Applications, One Backend

```text
frontend/
├── nurse/app/              # Today, Review, Patients, Simulator, Audit
├── patient/app/            # Registration, Queue, Payment, Records, upload token
└── shared/                 # generated API types and safe primitives only
```

- Build and deploy each panel independently, with a distinct origin allowlisted by the shared backend.
- Server-render each authenticated shell and initial route data where practical.
- Keep nurse and patient routes in different applications so internal review data cannot accidentally appear in patient bundles or navigation.
- Use Clerk middleware for coarse route protection and enforce authorization again in the API/database.
- Pass the Clerk session token to Supabase through its native Clerk third-party auth integration; write RLS policies against `auth.jwt()->>'sub'`, because Clerk user IDs are strings rather than Supabase UUIDs.
- Never expose a Supabase service-role key, Clerk secret, OpenAI key, or raw document-storage path to the browser.

### 4.2 Queue Behavior

- Subscribe to the patient/staff `queue_entries` row through Supabase Realtime.
- The patient Queue screen's top-right **Refresh** button invalidates the TanStack Query cache and requests fresh API data.
- Initial loading renders a fixed-layout skeletal queue card to avoid layout shift.
- During refresh, keep the last known information visible, change the action to **Refreshing…**, and disable repeated requests.
- On failure, label the displayed data as stale, retain its last-updated time, and offer Retry.

### 4.3 Accessibility and Responsive Baseline

- Staff tables become labelled cards on narrow screens rather than horizontally scrolling.
- Patient routes are mobile-first from 375 px upward.
- Use text plus semantic icons for PASS, PROCESSING, READY, REVIEW, ALERT, and visit states; color is supplementary.
- Provide visible focus, a skip-to-main link, keyboard-operable tables/forms, screen-reader live regions, and minimum 44×44 px controls.
- Respect browser zoom, dynamic text, dark/light contrast, safe areas, and reduced motion. Skeleton shimmer becomes static when reduced motion is enabled.

## 5. Backend Services

### 5.1 FastAPI

FastAPI owns:

- Clerk JWT validation and role/patient-scope enforcement;
- opaque upload-token validation;
- signed upload/download URL creation;
- document-job creation and status retrieval;
- staff corrections and re-authenticated confirmations;
- manual identity/e-card attestation recording;
- deterministic eligibility, queue, counter, and billing operations;
- idempotency for upload, check-in, refresh-sensitive writes, and mocked payment;
- audit events committed in the same database transaction as each mutation.

Pydantic request/response models are the canonical API contract. Generate the frontend API types from the OpenAPI document or validate them against shared Zod schemas in CI.

### 5.2 Background Worker

Use a small Postgres-backed `document_jobs` table for the demo:

```text
queued → processing → ready
                  └→ failed (retryable or final)
```

The worker claims jobs transactionally, downloads from private storage, invokes the OpenAI document adapter, validates the Structured Output, and writes per-field confidence plus page/excerpt evidence. Retries must be bounded and idempotent.

This avoids operating Redis during the hackathon. If production throughput requires it, the job adapter can later move to a dedicated managed queue without changing extraction or rules services.

### 5.3 Rules Engine and Readiness State Machine

Rules run after schema validation and never call the LLM. Inputs include:

- issuer/code and requested items;
- validity dates;
- active `eligibility_rules` version;
- appointment and pre-registration state;
- required-document completeness and deterministic readiness gates.

Every visit owns one persistent `queue_entries` row and one `Q-*` ticket. The readiness transition is:

```text
while required checks are running
    → PROCESSING on the existing ticket

every required document present and valid
AND every required extraction fact has source evidence
AND every eligibility/package match clean
AND required staff confirmation complete
    → READY on the existing ticket

any readiness gate fails
    → NEEDS_REVIEW on the existing ticket
```

Booked patients may satisfy the gates before arrival. Walk-ins start `processing` and can reach `ready` after first-pass processing. Review resolution updates the same row and never changes its queue number or original `checked_in_at`. Counter rebalancing may change counters but cannot override readiness gates.

Service ordering uses a clinic-configured ordering key derived from the original scheduled/check-in time. Readiness transitions never replace that key. A scheduled job or query flags review tickets approaching the configured service target so staff can reassign flexible counter capacity; it does not make clinical-priority decisions.

### 5.4 Load Balancing and Allocation Advisor

The advisor runs on a short interval and remains deterministic for P0:

1. Read current tickets, waiting ages, scheduled arrivals, and recent walk-in rate.
2. Convert demand into estimated staff-minutes using aggregate median/P90 handling times by stage and reason.
3. Read active counters and `staff_availability`, including eligible workstreams, breaks, and current assignment.
4. Evaluate candidate changes against minimum coverage, stability-window, maximum-reassignment, role/skill, and safe-handoff constraints.
5. Persist an expiring recommendation with its input snapshot, no-change baseline, rationale, constraints, and expected effect.
6. Apply a change only after an authorised operations lead accepts or modifies it; write the allocation and audit event transactionally.
7. Compare the resulting workstream waits with the recorded baseline after the recommendation window closes.

Use hysteresis: pressure must persist across a configured stability window before recommending a move, and the reverse move must meet a separate threshold. This prevents oscillation. The advisor operates on workstream aggregates and must not expose or rank individual productivity.

## 6. Document Extraction Pipeline

```text
Private upload
   → malware/type/size validation
   → OpenAI Responses API with PDF/image input
   → strict JSON Schema Structured Output
   → Pydantic schema validation
   → per-field confidence + page/source-excerpt evidence
   → deterministic eligibility/package match
   → staff review and confirmation
```

Recommended safeguards:

- Permit PDF, JPG, and PNG only, with the documented 10 MB limit.
- Reject unreadable or unsupported files before LLM invocation where possible.
- Require structured JSON matching the coverage schema; reject extra/unknown fields.
- Store prompt/template/model version with the job for reproducibility.
- Use `store=false` where supported. If the implementation uploads a temporary OpenAI file, set an expiry and delete it as soon as processing completes.
- Keep the original document only in private Supabase Storage. Never place a long-lived signed URL in a model request or log.
- Page number and source excerpt are the hackathon evidence baseline. Precise bounding-box highlighting requires a later local or specialized OCR adapter and must not be implied when unavailable.
- Store original and corrected values separately in immutable audit events.
- Do not send identity/e-card checks through the document model. The system stores staff attestation only.

## 7. Data and Security

### 7.1 Supabase

Use SQL migrations through the Supabase CLI for every table, enum, function, index, and RLS policy described in `design.md`.

Recommended database additions needed by this stack:

- `document_jobs` for asynchronous processing;
- `idempotency_keys` for write deduplication;
- `prompt_versions` for extraction reproducibility;
- `operational_events` as an append-only, privacy-safe source for readiness and flow metrics;
- `staff_availability` for role/skill eligibility, shifts, breaks, and current administrative assignment;
- `allocation_recommendations` for expiring advice, constraints, decisions, and measured outcomes;
- `operational_alerts` for severity, ownership, deduplication, expiry, acknowledgement, action, and alert-burden review;
- `downtime_intake_records` for encrypted minimum-safe local capture and conflict-safe recovery into one canonical visit;
- `configuration_releases` for shadow validation, maker/checker approval, effective dates, decision-version attribution, and rollback;
- append-only protections for `audit_log`;
- aggregate views for P50/P90 waits, first-pass readiness, review clearance, reason frequency, estimated staff-minute demand, staff touches, and booked/walk-in comparisons;
- indexes on readiness/visit status/date, patient match fields, document status, operational-event time, and audit timestamp.

### 7.2 Authorization

Clerk authenticates the person; Epicenter authorizes the action. Map each Clerk `sub` to a local `staff_accounts` or `patient_accounts` row. Keep clinic roles and record-level access rules in the application/database so changing identity providers would not rewrite business policy. Clerk Organizations may represent the clinic tenant, but organization membership alone never grants access to a patient record.

| Actor | Access |
| --- | --- |
| Registration staff | Queue, appointment, document review, patient registration, manual-check attestation |
| Pharmacist | Patient identity summary, recorded allergy, manual allergy attestation |
| Billing staff | Confirmed coverage, billing review, demo TPA payload |
| Operations admin | Allocation recommendations, counter/staff assignments, configuration, and read-only audit |
| Auditor | Read-only operational metrics, recommendation decisions, and audit history |
| Demo patient | Own queue, payment, records, and coverage upload only |
| Token-link visitor | One upload/reuse decision for one appointment only |

- Store upload tokens as hashes, not plaintext; expire after submission or appointment cutoff.
- Use Clerk reverification before sensitive staff actions such as confirming/correcting extracted data, revealing NRIC, overriding a match, confirming billing, or recording a manual-check attestation. The backend must validate the fresh-verification claim before committing.
- Prefer exact normalized NRIC match, then email fallback, only inside an already scoped appointment/account flow.
- Encrypt full NRIC and mask it by default. Reveal requires re-authentication and an audit event.
- Private storage uses short-lived signed URLs and server-checked ownership.
- Do not log raw NRIC, document content, access tokens, signed URLs, or medical answers.

### 7.3 Manual Check Boundary

`manual_check_confirmations` stores only:

- queue/visit reference;
- `identity_check_status = manually_confirmed`;
- e-card status or allowed not-applicable reason;
- staff ID, attestation version, and timestamp.

It stores no scan, image, biometric, automated score, or generated verification outcome. If the attestation write fails, the patient remains Incoming and the interface offers Retry.

## 8. Realtime, Refresh, and Notifications

- Realtime events are scoped by RLS and contain only identifiers/status fields needed by the active screen.
- REST endpoints remain the source for a full refresh and recovery after a dropped subscription.
- Queue updates include `updated_at` so stale data is never presented as current silently.
- SMS/email delivery is mocked for the demo behind a `NotificationProvider` interface. A real provider can later implement upload links, reminders, counter changes, and called notifications.

### 8.1 Degraded Mode and Recovery

- Detect dependency health separately for API, database, storage, authentication, extraction, realtime, and external adapters; partial failure must not be presented as total success or total outage.
- A verified outage activates the minimum-safe intake defined in `design.md`. Store only an encrypted bounded payload with a collision-safe local ID/idempotency key; do not cache raw documents in ordinary browser storage.
- Use an approved device-keystore/encrypted local-store adapter for any production offline implementation. P0 may simulate the contract without claiming production offline security.
- On recovery, upload through an idempotent reconciliation endpoint. Exact match, possible match, conflict, rejected, and retryable failure remain distinct.
- Close degraded mode only when created, reconciled, conflicted, and failed counts balance and an authorized recovery owner signs off.

### 8.2 Alert Governance

- Centralize operational alert policy instead of allowing each screen/service to invent interrupts.
- Deduplicate by alert type + owning record/workstream; a recurrence increments count and updates `last_seen_at`.
- Interrupt only for immediate actionable conditions. Route lower-severity information to an owning worklist/digest.
- Track acknowledgement, action, dismissal, expiry, repeats, and time-to-resolution by alert type. Do not publish individual staff rankings.
- Alert-policy changes follow the same shadow, maker/checker, effective-date, regression, and rollback controls as eligibility/readiness rules.

## 9. OpenAI Runtime and Copilot-Compatible MCP Transport

The custom Epicenter MCP exposes only narrow domain tools that call the same authenticated service layer:

```text
epicenter_start_document_extraction(document_id)
epicenter_get_extraction_status(job_id)
epicenter_preview_eligibility(document_id, appointment_reference)
epicenter_get_visit_ticket(ticket_id)
epicenter_get_operational_summary(clinic_id, date_range)
epicenter_get_allocation_recommendation(recommendation_id)
epicenter_run_simulation(scenario_id, seed, bounded_overrides)
epicenter_compare_simulation_runs(baseline_run_id, epicenter_run_id)
```

MCP tools return typed, minimal payloads and never bypass RLS/role checks or staff confirmation. Real readiness, correction, billing, identity/e-card, and allocation-approval writes remain in the staff UI. Simulation tools operate only on synthetic isolated state and label every result with scenario, seed, assumptions version, and `synthetic=true`.

The authenticated nurse application contains the Epicenter assistant. During development and normal application use, FastAPI calls the OpenAI Responses API with the reviewed Epicenter Operations MCP and, only for the maker/reviewer workflow, the Insurance Format Registry MCP. The Operations MCP serves curated queue, aggregate analytics, allocation, and simulator contracts from existing FastAPI/Supabase services. The Registry MCP serves only approved synthetic or formally de-identified fixtures.

The same public HTTPS Streamable HTTP servers must remain compatible with Copilot Studio at deployment/publication time. OpenAI and Copilot Studio are alternative clients of one tool contract; neither MCP exposes an unrestricted prompt, model proxy, or database console. The complete compatibility profile and verification gate are in [openai_integration.md](./openai_integration.md).

No Microsoft-hosted MCP is required. Live operational queue and simulator data use the custom Operations MCP; document-format maker/checker logic uses the custom Registry MCP. Copilot Studio connects to those same custom servers after deployment.

The native Next.js dashboard is the P0 analytics presentation. Power BI/Fabric is not built during development; it remains an optional future projection over reconciled de-identified aggregates for multi-clinic scale and never replaces the operational source of truth.

## 10. No-Azure Deployment

Use three Git-connected services:

```text
Vercel
└── epicenter-web            Next.js staff/patient application

Railway
├── epicenter-api-mcp        FastAPI REST + HTTPS /mcp + /healthz
└── epicenter-worker         Python document-job worker; no public domain

Supabase                     Postgres + private Storage + Realtime
Clerk                        web sessions + reverification; MCP auth adapter
OpenAI                       PDF/image extraction + Structured Outputs
Copilot Studio               deployment/publication compatibility client only
Power BI/Fabric              optional future aggregate analytics projection
```

Both Railway services use the same repository and Python image but different start commands. Only `epicenter-api-mcp` receives a public Railway domain. The worker communicates through the Postgres job table and does not need an inbound port.

Deployment order:

1. Create Supabase and apply migrations/RLS policies.
2. Configure Clerk, its native Supabase third-party auth integration, and seeded users.
3. Create the OpenAI project/key using synthetic documents only.
4. Deploy `epicenter-api-mcp` from GitHub to Railway, set its variables, configure `/healthz`, and generate a public domain.
5. Deploy `epicenter-worker` from the same repository with the worker start command and no public domain.
6. Deploy the patient and nurse Next.js applications as separate Vercel projects and set both API base URLs to the same Railway domain.
7. After the core product is stable, deploy `/mcp/operations` and `/mcp/insurance-registry`, then enable the authenticated nurse assistant through the OpenAI Responses API.
8. Verify both endpoints as Streamable HTTP MCP servers and connect at least one safe read-only synthetic tool in the Copilot Studio test panel; treat publishing/licensing as a manual release gate.

Power BI/Fabric is deliberately absent from this deployment sequence. Revisit it only if enterprise/multi-clinic reporting justifies a governed aggregate projection beyond the native dashboard.

The initial demo must use synthetic data. Before processing real patient documents, confirm provider terms, retention, residency, access controls, and any required healthcare agreements.

## 11. Mocked and Deferred Integrations

| Capability | Demo implementation | Production adapter |
| --- | --- | --- |
| Payment | Deterministic mock success/failure with `mock_*` status and receipt | PayNow/Stripe-compatible `PaymentProvider` |
| TPA portal | JSON preview/export only | Payer-specific authenticated connector |
| SMS/email | Log/in-app preview | Approved SMS/email provider |
| Clinic Assist/NEHR | Architecture diagram and API contract | Approved institutional integration |
| Patient identity system | Seeded Clerk users mapped to local patient records | Production patient IAM/MFA/recovery program |

Every adapter uses a versioned request/response contract plus `requested`, `accepted`, `rejected`, `unknown`, and `reconciled` business states. Store idempotency and external correlation references, cap retries, route unresolved/unknown results to an exception worklist, and test end-to-end acknowledgement. A 2xx response alone never advances the business record to accepted.

The UI and stored status must make mocked behavior visible; it must not imply that money, messages, or insurer submissions were sent externally.

## 12. Suggested Repository Layout

```text
frontend/
├── patient/                 # separate patient Next.js app / Vercel project
├── nurse/                   # separate nurse Next.js app / Vercel project
└── shared/                  # generated API client + safe shared UI primitives
backend/
├── app/                     # one FastAPI API/MCP service for both panels
├── worker/                  # document-processing worker
└── persistence/             # matching SQL Editor schema snapshot
supabase/
├── migrations/
├── seed.sql
└── tests/
tests/
├── e2e/
├── fixtures/
└── security/
```

Keep MCP and FastAPI transports thin; business logic belongs in `backend/core` so there is one implementation to test.

## 13. Testing Strategy

### Frontend

- Component tests for skeleton, empty, error, retry, stale, and success states.
- Keyboard and accessibility checks for every staff/patient route.
- Playwright journeys for scheduled-ready, booked-review, walk-in processing-to-ready, walk-in processing-to-review-to-ready on the same ticket, explainable allocation recommendation/approval/rejection, document replacement/reuse, manual-check attestation, counter change/refresh, mocked payment, and read-only history.
- Role-based usability journeys capture task time, staff touches, navigation steps, corrections, errors, recovery, and a short perceived-workload measure for registration, review, pharmacy, billing, operations, and downtime roles.
- Downtime journeys cover verified outage entry, minimum-safe intake, one visible recovery reference, reconnection, exact/conflict reconciliation, duplicate replay, and proof that waiting age is not reset.

### Backend

- Unit tests for extraction-schema validation and every eligibility/queue rule branch.
- Contract tests using all sample chit formats.
- Transaction/idempotency tests for corrections, check-in, billing, and payment.
- Authorization/RLS tests proving patients cannot read review reasons, confidence, rules, audit records, or other patients.
- Clerk session/JWT and reverification tests covering invalid, expired, wrong-audience, wrong-role, and stale-verification cases.
- Tests proving no identity/e-card artifact enters document-extraction jobs.
- Allocation-advisor tests for demand estimation, role/skill eligibility, minimum coverage, breaks, stability/hysteresis, reassignment limits, expiry, conflict, audit, and a no-change result for short-lived spikes.
- Shadow-release tests prove draft model/prompt/schema/rule versions cannot change readiness, billing, alerts, or allocations; activation requires maker/checker approval and rollback restores the prior version atomically.
- Alert-governance tests cover deduplication, severity, ownership, expiry, recurrence count, acknowledgement/action metrics, and noninterruptive worklist routing.
- Adapter contract/reconciliation tests separate transport success from accepted/rejected/unknown/reconciled business outcomes and prove bounded idempotent replay.

### Release Gate

```text
pnpm lint + typecheck + test
pnpm playwright test
ruff check + mypy + pytest
Supabase migration/RLS tests
Production builds for patient, nurse, and Python containers
```

Automated checks are necessary but not sufficient. A clinic pilot also requires the human and operational release gates in [epic_lessons.md](./epic_lessons.md): representative role-task validation, zero-false-ready shadow results, alert ownership, channel parity, interface reconciliation, downtime drill, trained superusers, stabilization support, pause criteria, and named rollback ownership.

Roll out in controlled stages:

1. **Offline fixture validation:** no operational users or live state.
2. **Shadow observation:** process approved inputs but do not change readiness, billing, allocation, or alerts.
3. **Assisted bounded pilot:** one workflow/shift/counter and approved rule set, with staff confirming every action and the manual fallback retained.
4. **Stabilization:** daily error/burden/alert/reconciliation review with trained superusers and pause authority.
5. **Measured expansion:** add roles, issuers, shifts, or sites one at a time only after the preceding gate passes.

## 14. Environment Configuration

Use secret managers in deployed environments and checked-in `.env.example` files with names only.

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
SUPABASE_SERVICE_ROLE_KEY          # server only
SUPABASE_DATABASE_URL              # server only
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY                   # server only
CLERK_JWT_KEY                      # optional networkless backend verification
CLERK_ISSUER_URL
OPENAI_API_KEY                     # server/worker only
OPENAI_DOCUMENT_MODEL
UPLOAD_TOKEN_SIGNING_SECRET
APP_BASE_URL
NEXT_PUBLIC_API_BASE_URL
```

No server secret may use a `NEXT_PUBLIC_` prefix.

## 15. Decisions to Confirm Before Scaffolding

The architecture can proceed with the defaults above. Confirm these only when provider accounts are being configured:

1. OpenAI document-capable model and project limits available to the team.
2. Whether page/source-excerpt evidence is sufficient for the judged demo or local bounding-box OCR is worth the added complexity.
3. Which real messaging provider, if any, should replace the demo notification adapter.
4. Required data residency, retention, and deletion rules for uploaded documents and extracted text.
5. Clerk production domain, allowed sign-in factors, clinic organization/role setup, and reverification policy.

## 16. Platform References

- [Deploy FastAPI on Railway](https://docs.railway.com/guides/fastapi)
- [Map multiple services onto Railway](https://docs.railway.com/guides/docker-compose)
- [Deploy Next.js on Vercel](https://vercel.com/docs/frameworks/full-stack/nextjs)
- [Analyze images and PDF files with the OpenAI API](https://platform.openai.com/docs/quickstart/make-your-first-api-request)
- [OpenAI API data controls](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint)
