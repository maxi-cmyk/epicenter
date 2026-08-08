# Technology Stack

## AI-Assisted Pre-Registration & Eligibility Verification for Parkway Shenton

- **Status:** Recommended implementation baseline
- **Sources:** [PRD.md](./PRD.md) and [design.md](./design.md)
- **Priority:** Hackathon speed, low operational cost, clear security boundaries, and Microsoft Copilot Studio portability

## 1. Architecture Principles

1. **The LLM extracts; deterministic code decides.** The document model converts varied documents into structured fields. Eligibility, package, billing, and queue decisions run through versioned rules and application code.
2. **Identity and e-card checks remain manual.** The application records a staff attestation only. Identity/e-card images or automated verification results must never enter the extraction pipeline.
3. **One backend serves both interfaces.** Staff and patient views use the same records and queue state, with role- and patient-scoped authorization.
4. **Long-running document processing is asynchronous.** Upload returns quickly with a job ID; the UI follows explicit uploading, processing, ready, and failed states.
5. **Realtime is an enhancement, not the only path.** Queue screens subscribe to updates and also expose a manual Refresh action. Initial queue loading uses a fixed-layout skeletal screen.
6. **Provider integrations sit behind adapters.** Document extraction, messaging, mocked payment, and future TPA submission can be replaced without changing core rules.
7. **Clerk is the preferred identity provider.** Staff and seeded demo-patient sign-in, sessions, and sensitive-action reverification use Clerk. Appointment-scoped upload links remain opaque single-use tokens because they are not user accounts.

## 2. Recommended Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Web application | Next.js with TypeScript and App Router | Staff workspace, tokenized upload pages, and demo patient account |
| UI | Tailwind CSS, shadcn/ui primitives, Lucide SVG icons | Accessible responsive components without structural emoji |
| Client data | TanStack Query | Loading/error/retry state, cache invalidation, polling fallback, and manual queue refresh |
| Forms and validation | React Hook Form + Zod | Staff corrections, attestations, questionnaires, and upload validation |
| API | FastAPI + Pydantic | Typed REST endpoints, OpenAPI contract, authorization boundary, and orchestration |
| Core business logic | Plain Python service modules | Eligibility matching, strict queue rules, counter assignment, billing calculations, and audit creation |
| Database | Supabase Postgres | Source of truth for the data model in `design.md` |
| Authentication | Clerk | Staff accounts, seeded demo-patient accounts, sessions, and sensitive-action reverification |
| Authorization | Clerk identity + backend permissions + Postgres RLS | Separates staff roles, patient-owned data, MCP access, and upload-token scope |
| File storage | Private Supabase Storage bucket | Coverage photos/PDFs and generated demo receipts |
| Realtime queue updates | Supabase Realtime | Queue/counter changes shared between staff and patient screens |
| Background processing | Postgres-backed job table + Python worker | Reliable document extraction without adding Redis for the demo |
| Document extraction | OpenAI Responses API with PDF/image inputs and Structured Outputs | Converts the coverage document directly into the validated coverage schema |
| Evidence mapping | Page number + supporting source excerpt | Staff-reviewable evidence without requiring a separate cloud OCR platform |
| Rules engine | Python + versioned Postgres `eligibility_rules` | Deterministic package, eligibility, billing, and queue decisions |
| MCP portability | Python MCP server sharing the core service layer | Exposes extraction, matching, and record lookup to Copilot Studio |
| Deployment | Vercel for Next.js; Railway for API/MCP/worker; managed Supabase | Familiar Git-based deployment without Azure infrastructure |
| Observability | Structured JSON logs + Railway deployment/runtime logs | Request/job tracing without logging raw NRIC or document contents |
| Testing | Vitest, React Testing Library, Playwright, Pytest | Unit, component, API, policy, and end-to-end verification |
| Tooling | pnpm, uv, ESLint, Prettier, Ruff, mypy | Reproducible installs and consistent TypeScript/Python quality checks |

Exact dependency versions should be pinned when the repository is scaffolded rather than embedded in this planning document.

## 3. System Topology

```text
Staff browser                 Patient browser / token link
      │                                   │
      └────────────── Next.js web app ────┘
                           │
                    FastAPI REST API
                      │     │      │
                      │     │      └── MCP server → Copilot Studio
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
```

The API and MCP server call the same service functions. MCP tools must not contain a second implementation of extraction, rules, or authorization logic.

## 4. Frontend

### 4.1 One Next.js Application, Two Surfaces

```text
app/
├── staff/                  # authenticated operational workspace
│   ├── queue/
│   ├── review/
│   ├── upload/
│   ├── records/
│   ├── billing/
│   ├── audit/
│   └── counters/
├── patient/                # seeded demo-account routes
│   ├── queue/
│   ├── payment/
│   └── records/
└── upload/[token]/         # single-use appointment-scoped flow
```

- Server-render the authenticated shell and initial route data where practical.
- Keep staff and patient route layouts separate so internal review data cannot accidentally appear in patient components.
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
- Use text plus semantic icons for PASS, REVIEW, ALERT, FAST, and queue states; color is supplementary.
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

### 5.3 Rules Engine

Rules run after schema validation and never call the LLM. Inputs include:

- issuer/code and requested items;
- validity dates;
- active `eligibility_rules` version;
- appointment and pre-registration state;
- required-document completeness and confidence thresholds.

The strict queue function is:

```text
booked
AND preregistration completed before arrival
AND every required document present, valid, and high-confidence
AND every eligibility/package match clean
    → FAST
otherwise
    → REVIEW
```

Every walk-in is REVIEW. Counter rebalancing may change counters but cannot override this rule.

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
- append-only protections for `audit_log`;
- indexes on queue status/date, patient match fields, document status, and audit timestamp.

### 7.2 Authorization

Clerk authenticates the person; Epicenter authorizes the action. Map each Clerk `sub` to a local `staff_accounts` or `patient_accounts` row. Keep clinic roles and record-level access rules in the application/database so changing identity providers would not rewrite business policy. Clerk Organizations may represent the clinic tenant, but organization membership alone never grants access to a patient record.

| Actor | Access |
| --- | --- |
| Registration staff | Queue, appointment, document review, patient registration, manual-check attestation |
| Pharmacist | Patient identity summary, recorded allergy, manual allergy attestation |
| Billing staff | Confirmed coverage, billing review, demo TPA payload |
| Admin/auditor | Counter allocation, read-only audit, configuration |
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

## 9. MCP and Copilot Studio Portability

Expose narrow tools that call the same authenticated service layer:

```text
extract_coverage_document(document_id)
get_extraction_status(job_id)
match_eligibility(document_id, appointment_reference)
get_patient_record(patient_id)
get_queue_entry(queue_entry_id)
```

MCP tools return typed, minimal payloads and never bypass RLS/role checks or staff confirmation. Destructive/corrective actions should remain in the staff UI unless a future approved Copilot workflow provides equivalent re-authentication and audit guarantees.

## 10. No-Azure Deployment

Use three Git-connected services:

```text
Vercel
└── epicenter-web            Next.js staff/patient application

Railway
├── epicenter-api-mcp        FastAPI REST + HTTPS /mcp + /healthz
└── epicenter-worker         Python document-job worker; no public domain

Supabase                     Postgres + private Storage + Realtime
Clerk                        web sessions + reverification + MCP OAuth
OpenAI                       PDF/image extraction + Structured Outputs
```

Both Railway services use the same repository and Python image but different start commands. Only `epicenter-api-mcp` receives a public Railway domain. The worker communicates through the Postgres job table and does not need an inbound port.

Deployment order:

1. Create Supabase and apply migrations/RLS policies.
2. Configure Clerk, its native Supabase third-party auth integration, and seeded users.
3. Create the OpenAI project/key using synthetic documents only.
4. Deploy `epicenter-api-mcp` from GitHub to Railway, set its variables, configure `/healthz`, and generate a public domain.
5. Deploy `epicenter-worker` from the same repository with the worker start command and no public domain.
6. Deploy the Next.js app to Vercel and set its API base URL to the Railway domain.
7. Register `https://<railway-domain>/mcp` in Copilot Studio.

The initial demo must use synthetic data. Before processing real patient documents, confirm provider terms, retention, residency, access controls, and any required healthcare agreements.

## 11. Mocked and Deferred Integrations

| Capability | Demo implementation | Production adapter |
| --- | --- | --- |
| Payment | Deterministic mock success/failure with `mock_*` status and receipt | PayNow/Stripe-compatible `PaymentProvider` |
| TPA portal | JSON preview/export only | Payer-specific authenticated connector |
| SMS/email | Log/in-app preview | Approved SMS/email provider |
| Clinic Assist/NEHR | Architecture diagram and API contract | Approved institutional integration |
| Patient identity system | Seeded Clerk users mapped to local patient records | Production patient IAM/MFA/recovery program |

The UI and stored status must make mocked behavior visible; it must not imply that money, messages, or insurer submissions were sent externally.

## 12. Suggested Repository Layout

```text
apps/
├── web/                     # Next.js staff + patient application
├── api/                     # FastAPI HTTP service
├── worker/                  # document job worker
└── mcp/                     # MCP transport/tool declarations
packages/
├── api-client/              # generated TypeScript API client
├── ui/                      # shared accessible UI primitives
└── contracts/               # schemas/fixtures where sharing is safe
backend/
└── core/                    # extraction, rules, queue, billing, audit services
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
- Playwright journeys for scheduled-fast, booked-review, walk-in-review, document replacement/reuse, manual-check attestation, counter change/refresh, mocked payment, and read-only history.

### Backend

- Unit tests for extraction-schema validation and every eligibility/queue rule branch.
- Contract tests using all sample chit formats.
- Transaction/idempotency tests for corrections, check-in, billing, and payment.
- Authorization/RLS tests proving patients cannot read review reasons, confidence, rules, audit records, or other patients.
- Clerk session/JWT and reverification tests covering invalid, expired, wrong-audience, wrong-role, and stale-verification cases.
- Tests proving no identity/e-card artifact enters document-extraction jobs.

### Release Gate

```text
pnpm lint + typecheck + test
pnpm playwright test
ruff check + mypy + pytest
Supabase migration/RLS tests
Production builds for web and Python containers
```

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
