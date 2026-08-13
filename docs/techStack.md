# Technology Stack

## AI-Assisted Pre-Registration & Eligibility Verification for Parkway Shenton

- **Status:** As-built implementation baseline
- **Sources:** [PRD.md](./PRD.md), [PRODUCT.md](./PRODUCT.md), and [workflow.md](./workflow.md)
- **Priority:** Hackathon speed, low operational cost, clear security boundaries, a server-side OpenAI integration, and portable MCP publication

## 1. Architecture Principles

1. **The LLM extracts; deterministic code decides.** The document model converts varied documents into structured fields. Eligibility, package, billing, and queue decisions run through versioned rules and application code.
2. **Identity and e-card checks remain manual.** The application records a staff attestation only. Identity/e-card images or automated verification results must never enter the extraction pipeline.
3. **One backend serves both interfaces.** Staff and patient views use the same records and queue state, with role- and patient-scoped authorization.
4. **Long-running document processing is asynchronous.** Upload returns quickly with a job ID; the UI follows explicit uploading, processing, ready, and failed states.
5. **Provider integrations sit behind adapters.** Document extraction, messaging, mocked payment, and future TPA submission can be replaced without changing core rules.
6. **Clerk is the identity provider.** Staff and seeded demo-patient sign-in, sessions, and sensitive-action reverification use Clerk. Appointment-scoped upload links remain opaque single-use tokens because they are not user accounts.
7. **One visit means one ticket.** Processing, readiness, review, and counter changes update one persistent queue row; no transition issues a second number or resets the patient's original check-in time.
8. **Walk-ins are always slow-counter.** Only booked patients with no outstanding issues use fast counters (`F1`–`F2`). Walk-ins and booked cases that need review use slow counters (`S1`–`S4`).
9. **FastAPI is the privileged data boundary.** Browsers never receive a Supabase service-role key. Operational reads and writes go through versioned REST contracts.
10. **The simulator is isolated.** The nurse Simulator engine lives in `frontend/nurse/lib/simulation/` and must not write operational patient, queue, staffing, or audit tables.
11. **Downtime is a workflow.** Degraded mode, minimum-safe intake, recovery ownership, idempotent replay, and conflict reconciliation are designed and tested—not reduced to a generic error page.

## 2. Implemented Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Web applications | Two Next.js 16 apps (App Router, TypeScript, npm workspaces) | Separate patient (`:3000`) and nurse (`:3001`) panels |
| Shared UI | `@epicenter/shared` CSS modules, design tokens, Lucide icons | Typed contracts and safe presentation primitives only |
| API | FastAPI + Pydantic | Typed REST, OpenAPI contract, Clerk JWT authorization, orchestration |
| Core business logic | Python service modules in `backend/app/` | Eligibility, single-ticket readiness, kiosk check-in, counter assignment, billing, audit |
| Persistence | Supabase Postgres, or in-memory demo fixture | `EPICENTER_PERSISTENCE_MODE` `auto` / `demo` / `supabase` |
| Authentication | Clerk | Patient public enrollment; administrator-provisioned staff; reverification for mutations |
| Authorization | Clerk identity + FastAPI role/clinic mapping + Postgres RLS | Patients cannot read staff review data; staff cannot act outside clinic scope |
| File storage | Private Supabase Storage | Coverage photos/PDFs for the extraction pipeline |
| Background processing | `backend/worker.py` + Postgres-backed jobs | Document classification and OpenAI extraction |
| Application LLM | OpenAI Responses API (`store=false`) | Server-side document extraction and the nurse assistant |
| Agent tools | Custom Operations MCP and Insurance Format Registry MCP | Streamable HTTP; Copilot Studio-compatible at deploy time |
| Simulator | Deterministic TypeScript engine in the nurse app | `serial_baseline`, `single_ticket`, `dynamic_allocation` |
| Analytics presentation | Native Next.js dashboard over FastAPI metrics | Power BI/Fabric is deferred |
| Deployment | Two Vercel projects; Railway API/worker; managed Supabase | Independent patient/nurse releases against one backend |
| Testing | Node test runner, Playwright, Pytest, Ruff | Frontend contracts/simulation, auth journeys, API and SQL contracts |
| Tooling | npm workspaces, Python venv, ESLint, Ruff | Reproducible installs |

## 3. System Topology

```text
Nurse browser                         Patient browser / token link
      │                                          │
Nurse Next.js app (:3001)              Patient Next.js app (:3000)
      │                                          │
      └──────────────── FastAPI REST API ────────┘
                         │     │      │
                         │     │      └── OpenAI Responses API
                         │     │                 │
                         │     │                 └── reviewed Epicenter MCP tools
                         │     │
                         │     └── document worker
                         │
                         └──────── Supabase (when configured)
                                   ├── Postgres + RLS
                                   └── Private Storage

Copilot Studio (deployment/publication only)
      └── same public HTTPS Streamable HTTP Epicenter MCP tools
```

The API and MCP transports call the same service functions. MCP tools must not contain a second implementation of extraction, rules, or authorization logic. The nurse Simulator runs entirely in the nurse frontend against synthetic fixtures and does not write through FastAPI operational repositories.

## 4. Frontend

### 4.1 Two Next.js Applications, One Backend

```text
frontend/
├── patient/app/            # Home, coverage, questionnaire, queue, payment, records
├── nurse/app/              # Today, tasks, kiosk, Database, Audit, Simulator
└── shared/                 # generated API types and safe primitives only
```

- Build and deploy each panel independently, with a distinct origin allowlisted by `EPICENTER_FRONTEND_ORIGINS`.
- Keep nurse and patient routes in different applications so internal review data cannot appear in patient bundles or navigation.
- Use Clerk middleware for coarse route protection and enforce authorization again in FastAPI.
- Never expose a Supabase service-role key, Clerk secret, OpenAI key, or raw document-storage path to the browser.
- Generate TypeScript contracts from the FastAPI OpenAPI document (`npm run contracts:generate` / `contracts:check`).

Nurse primary navigation: Dashboard (Today), Database, Audit trail, Simulator. The gated task flow lives under `/tasks/[ticketId]/…`. Walk-in kiosk is `/kiosk`. `/review` is not a staff destination.

Patient primary journey: Home → Coverage → Questionnaire → Queue (queue number + counter) → Payment → Records.

### 4.2 Queue Behavior

- Patient and nurse screens read the same ticket, queue number, and assigned counter from FastAPI.
- Walk-ins always map to slow counters `S1`–`S4`.
- Booked + ready maps to fast counters `F1`–`F2`.
- Queue screens expose loading, empty, stale, and retry states. Status never relies on colour alone.

### 4.3 Accessibility and Responsive Baseline

- Staff tables become labelled cards on narrow screens rather than horizontally scrolling.
- Patient routes are mobile-first from 375 px upward.
- Use text plus semantic icons for readiness and visit states; color is supplementary.
- Provide visible focus, keyboard-operable tables/forms, and minimum 44×44 px controls.
- Respect reduced motion.

## 5. Backend Services

### 5.1 FastAPI

FastAPI owns:

- Clerk JWT validation and role/patient-scope enforcement;
- opaque upload-token validation;
- document-job creation and status retrieval;
- staff corrections and re-authenticated confirmations;
- manual identity/e-card attestation recording;
- gated nurse task mutations (`identity_confirmed`, `forms_confirmed`, `package_confirmed`, `billing_confirmed`);
- deterministic eligibility, queue, counter, and billing operations;
- kiosk walk-in check-in and slow-counter assignment;
- patient home/queue payloads including `queue_number` and assigned counter;
- idempotency for upload, check-in, and mocked payment;
- audit events committed with each mutation;
- MCP Streamable HTTP at `/mcp/operations` and `/mcp/insurance-registry`.

Pydantic request/response models are the canonical API contract.

### 5.2 Background Worker

`backend/worker.py` claims document jobs, classifies the upload into a `DocumentCategory` (`form`, `authorisation_letter`, `benefit_structure`, `coding_scheme`), then runs a category-specific extractor. Generic unclassified extraction is not callable.

```text
queued → processing → ready
                  └→ failed (retryable or final)
```

### 5.3 Rules Engine and Readiness State Machine

Rules run after schema validation and never call the LLM. Every visit owns one persistent queue row and one `Q-*` ticket:

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

Counter assignment is independent of the patient's place in line:

```text
walk-in                                → slow counter S1–S4
booked AND readiness_state = ready     → fast counter F1–F2
booked AND any outstanding issue       → slow counter S1–S4
```

Review resolution updates the same row and never changes its queue number or original ordering timestamp.

### 5.4 Load Balancing and Allocation Advisor

The advisor remains deterministic for the demo: estimate demand, respect role/skill/break/coverage constraints, persist an expiring recommendation, and apply a change only after an authorised operations lead accepts or modifies it. The Simulator's `dynamic_allocation` scenario is the visual proof of that policy; it does not mutate operational tables.

## 6. Document Extraction Pipeline

```text
Private upload
   → malware/type/size validation
   → structural / keyword / fingerprint classification
   → category-specific OpenAI Structured Output
   → Pydantic schema validation
   → per-field confidence + page/source-excerpt evidence
   → deterministic eligibility/package match
   → staff review and confirmation
```

Safeguards: PDF/JPG/PNG only; `store=false`; original files stay in private storage; identity/e-card artifacts never enter the model; staged facts remain `pending_review` until staff confirm.

## 7. Data and Security

### 7.1 Persistence

`EPICENTER_PERSISTENCE_MODE=auto` uses Supabase when `EPICENTER_SUPABASE_URL` and `EPICENTER_SUPABASE_SECRET_KEY` are set, otherwise the in-memory fixture. `demo` forces isolation. `supabase` fails closed if credentials are missing.

Migrations and the operational seed live in `supabase/`. Browser roles do not receive operational-table grants. Audit and operational-event tables reject `UPDATE`/`DELETE`.

### 7.2 Authorization

Clerk authenticates the person; Epicenter authorizes the action. Map each Clerk `sub` to a local `staff_accounts` or `patient_accounts` row. Clinic roles and record-level access live in the application/database.

| Actor | Access |
| --- | --- |
| Registration staff | Today board, gated tasks, kiosk, patient Database CRUD (update/delete step-up), Audit |
| Operations admin | Same as registration, plus allocation recommendations |
| Auditor | Read-only Audit |
| Demo patient | Own home, coverage, questionnaire, queue, payment, and records |
| Token-link visitor | One upload/reuse decision for one appointment only |

- Database Update and Delete require fresh Clerk password verification. Create and View do not add a second prompt.
- Do not log raw NRIC, document content, access tokens, signed URLs, or medical answers.
- The browser receives only `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `NEXT_PUBLIC_API_BASE_URL`.

### 7.3 Manual Check Boundary

Identity/e-card confirmation stores only the queue/visit reference, staff attestation, timestamp, and allowed not-applicable reason. It stores no scan, image, biometric, or automated score. If the attestation write fails, the patient remains Incoming and the interface offers Retry.

## 8. OpenAI Runtime and Copilot-Compatible MCP Transport

During development, FastAPI calls the OpenAI Responses API with the reviewed Epicenter Operations MCP and, for maker/reviewer format work, the Insurance Format Registry MCP. The browser never receives the OpenAI key.

MCP tools return typed, minimal payloads and never bypass role checks or staff confirmation. Real readiness, correction, billing, identity/e-card, and allocation-approval writes remain in the staff UI. Simulation tools, when exposed, operate only on synthetic isolated state and label every result `synthetic=true`.

The same public HTTPS Streamable HTTP servers must remain compatible with Copilot Studio at deployment/publication time. Microsoft-hosted MCPs are not dependencies. The product remains usable when OpenAI or either MCP endpoint is unavailable.

## 9. Deployment

```text
Vercel
├── frontend/patient     patient Next.js app
└── frontend/nurse       nurse Next.js app

Railway
├── epicenter-api        FastAPI REST + /mcp + /healthz
└── epicenter-worker     document-job worker; no public domain

Supabase                 Postgres + private Storage
Clerk                    web sessions + reverification
OpenAI                   PDF/image extraction + nurse assistant
```

Set `EPICENTER_DEMO_MODE=false` and comma-separated patient/nurse origins in `EPICENTER_FRONTEND_ORIGINS` on Railway. The initial demo uses synthetic data only.

## 10. Mocked and Deferred Integrations

| Capability | Demo implementation | Production adapter |
| --- | --- | --- |
| Payment | Deterministic mock success/failure | PayNow/Stripe-compatible provider |
| TPA portal | Structured record / preview only | Payer-specific authenticated connector |
| SMS/email | Log/in-app preview | Approved messaging provider |
| Clinic Assist/NEHR | Architecture contract | Approved institutional integration |
| Singpass/Myinfo | Labelled synthetic booking pre-check | Production Singpass Login + Myinfo |

A 2xx HTTP response alone never advances a business record to accepted.

## 11. Repository Layout

```text
frontend/
├── patient/                 # patient Next.js app / Vercel project
├── nurse/                   # nurse Next.js app / Vercel project
└── shared/                  # generated API client + safe shared UI primitives
backend/
├── app/                     # FastAPI API + MCP
└── worker.py                # document-processing worker
supabase/
├── migrations/
└── operational_seed.sql
docs/
├── PRODUCT.md
├── PRD.md
├── techStack.md
└── workflow.md
```

## 12. Testing and Verify

```bash
cd backend && .venv/bin/pytest -q && .venv/bin/ruff check app tests
cd frontend && npm test && npm run typecheck && npm run lint && npm run build
```

Windows PowerShell uses `.\.venv\Scripts\pytest` and `.\.venv\Scripts\ruff`. `npm run test:auth-live` covers Clerk session, reverification, and a real audited mutation against development credentials only.

## 13. Environment Configuration

Use secret managers in deployed environments and checked-in `.env.example` files with names only.

```text
NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY                   # server only
CLERK_JWT_KEY                      # optional
EPICENTER_FRONTEND_ORIGINS
EPICENTER_DEMO_MODE
EPICENTER_PERSISTENCE_MODE
EPICENTER_SUPABASE_URL
EPICENTER_SUPABASE_SECRET_KEY      # server only
OPENAI_API_KEY                     # server/worker only
OPENAI_MODEL
```

No server secret may use a `NEXT_PUBLIC_` prefix.

## 14. Platform References

- [Deploy FastAPI on Railway](https://docs.railway.com/guides/fastapi)
- [Deploy Next.js on Vercel](https://vercel.com/docs/frameworks/full-stack/nextjs)
- [Analyze images and PDF files with the OpenAI API](https://platform.openai.com/docs/quickstart/make-your-first-api-request)
- [OpenAI API data controls](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint)
