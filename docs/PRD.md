# Product Requirements Document

## AI-Assisted Pre-Registration & Eligibility Verification for Parkway Shenton

- **Status:** As-built hackathon demo (patient + nurse panels against one FastAPI backend)
- **Track:** Hack4Health 2026, Technical Track
- **How to read this document:** §1–2 state the official clinic problem and brief constraints. §3 onward describes **what the repository actually ships**, not earlier planning ideas (tokenized SMS links, live Singpass, a staff allocation console, outbound patient messaging).
- **Workflow:** [workflow.md](./workflow.md) · **Stack:** [techStack.md](./techStack.md) · **Product:** [PRODUCT.md](./PRODUCT.md)

## 1. Problem Statement

How might we automate pre-registration and eligibility verification for both scheduled appointments and walk-in patients, so the necessary information is retrieved and processed before they reach the front desk, eliminating the need for staff to manually determine coverage, benefits, and screening packages while ensuring identity verification is still completed securely in person?

### 1.1 Current Workflow

Every patient — whether a GP consultation or a corporate health screening — currently requires front-desk staff to manually determine identity, employer/insurer, applicable benefits, screening package, and billing arrangement after the patient has already reached the counter.

This is complicated by a lack of standardisation: the supplied synthetic bundle contains nine distinct medical-document examples across seven issuer/code families, including referral letters, vouchers, underwriting requests, government authorisation forms, and an employer appointment email.

The same issuer code can also appear on different document types. Staff must interpret the selected tests, packages, dates, and instructions in context, cross-reference the right coverage rules, and manually key the result into one or more systems — sometimes twice, once into the clinic's own system and again into a separate TPA portal after the visit.

### 1.2 Quantified Pain Point (from the Official Problem Statement)

| Stage | Estimated time |
| --- | ---: |
| Identity verification | ~1 min |
| Patient registration (manual entry) | ~2–3 min |
| Document interpretation (+ separate TPA form if applicable) | ~3–5 min |
| Eligibility check (CHAS/corporate insurance matching) | ~3–5 min |
| Screening package verification (+ 2 on-site consent/disclosure forms, re-asking for details already captured) | ~2–4 min |
| Billing determination | ~2 min |
| Queue issuance | ~1 min |
| Consultation/screening itself (out of scope for automation) | 10–20 min |
| Medication dispensed (allergy re-check) | ~2–3 min |
| Payment (+ manual TPA portal entry for insured patients) | ~5–8 min |

Excluding the clinical encounter itself, this totals approximately 23–32 minutes of administrative work per patient. For a clinic processing 40 patients in a morning, that is roughly 1,080 minutes (18 hours) of cumulative administrative effort — and because most of this happens sequentially at a single registration counter, delay for one patient compounds waiting time for every patient behind them.

### 1.3 Root Cause

The problem is explicitly not identity verification itself — that must and will remain an in-person, secure step. There are two distinct root causes:

**(a)** Document interpretation and eligibility determination only happen after the patient physically arrives, and that interpretation is manual, repetitive, and error-prone due to the lack of standardisation across payers.

**(b)** The same small set of source data — patient identity, the coverage document, and clinical/allergy information — is independently re-derived at several points across a single visit, rather than captured once and reused.

| Touchpoint | What's re-entered or re-checked | Already captured at |
| --- | --- | --- |
| TPA form | Patient identity, written onto a second paper record | Registration |
| Eligibility & package verification | Coverage/package details, re-checked against the original document | Document interpretation |
| On-site consent/disclosure forms | Name, NRIC, DOB, contact, address | Registration |
| Medication dispensed | Drug allergy information, asked again verbally | Registration and/or questionnaires |
| Payment | The original coverage document, re-checked again; then re-entered into the TPA portal | Document interpretation and visit data |

### 1.4 Why It Matters

This bottleneck affects every patient passing through registration. Because most of it happens sequentially at a single registration counter, one unusual document does not only delay that patient — it compounds onto everyone behind them. That is a structural property of a serial counter, not something fixed by making the average case slightly faster.

### 1.5 Simplification Rule

**Capture once, interpret once, confirm exceptions, and reuse the confirmed result.** Scheduled patients should submit coverage and questionnaire answers before they reach the desk. Walk-ins should go through supervised intake once. Staff keep in-person identity/e-card checks and final confirmation. Live TPA portal submission is not claimed.

## 2. Constraints (from Official Brief — Non-Negotiable)

- **Copilot Studio publication portability is required.** Development does not run in Copilot Studio. Deployed MCP endpoints must remain compatible with it.
- **OpenAI is the development and application LLM.** All model access is server-side through the Responses API. The P0 analytics surface is Epicenter's native UI, not Power BI.
- **Identity verification and e-card validation must remain in-person** and are out of scope for automation.
- **Operational cost must be realistic.**
- Document interpretation, eligibility checks, package matching, and registration data entry may be automated; staff still confirm them.

### 2.1 Demo vs production concept

| Topic | Production concept | What the demo actually does |
| --- | --- | --- |
| Booking identity | Singpass Login + consented Myinfo | Onboarding step labelled **“Synthetic adapter — no live Singpass sandbox is connected.”** Dummy fields are filled; if demo mode is off, the same fields are editable by the patient. |
| Coverage capture | SMS/email tokenized upload link, no patient account | **Clerk patient account** + onboarding Insurance step. A `/upload/[token]` route exists only for a few hardcoded demo tokens (`demo`, `apt-demo-014`, `valid`). Nothing sends SMS or email. |
| Patient issue notices | Outbound SMS/email with patient-safe categories | Optional **in-app banner** from seeded data. No message sender. |
| Payment | PayNow / card gateway | Explicit **mocked payment**. Copy states no money moves. |
| TPA portal | Authenticated insurer connector | Structured billing record and staff confirmation only. |
| Allocation advisor | Approve/modify/reject on the operations board | Recommendation **decide API exists**; the Dashboard does **not** render it. Allocation behaviour is shown in the Simulator. |

## 3. What the Demo Delivers

Two Next.js apps and one FastAPI service:

| App | Port | What a user can do |
| --- | --- | --- |
| Patient | 3000 | Create/sign in with Clerk, complete onboarding, open Home, see queue number and counter, mock-pay, read visit records |
| Nurse | 3001 | Dashboard (Incoming / Ongoing / Finished), gated registration tasks, walk-in kiosk, Database, Audit, Simulator, operations assistant |

Persistence is `EPICENTER_PERSISTENCE_MODE` `auto` / `demo` / `supabase`. Browsers never receive the Supabase secret. Generated TypeScript contracts live in `frontend/shared/`.

```text
frontend/
├── patient/             # Next.js patient app
├── nurse/               # Next.js nurse app
└── shared/              # generated API types and safe UI primitives
backend/                 # FastAPI + MCP + document worker
supabase/                # migrations and operational seed
docs/                    # PRODUCT, PRD, techStack, workflow, deployment-runbook
```

## 4. Core Product Scope (As Built)

### 4.1 Patient account and onboarding

The judged patient path is a **Clerk account**, not an unauthenticated SMS link.

1. Patient creates an account or signs in on the patient app.
2. FastAPI `POST /api/v1/patient/account/activate` maps the Clerk `sub` to one synthetic patient (`EPICENTER_PATIENT_DEMO_SOURCE_RECORD_KEY`, typically Loh Wei Ming / `APT-DEMO-014`).
3. Incomplete onboarding is forced to `/onboarding`:
   - **Singpass profile** — synthetic adapter, then continue.
   - **Insurance** — check-first coverage reuse (“Yes, same coverage” / “No, upload new document”) or a new document name. Success copy is “received for staff review”, not “approved”.
   - **Questionnaire** — General Health Screening Questionnaire with read-only identity/contact prefill and draft save on section actions (not keystroke autosave).
4. Home then shows the upcoming visit, coverage/questionnaire/queue/payment summaries, and the next action.

There is no in-app appointment booking. Patients without a mapped booking see a Parkway pre-registration link and Records/Payment shortcuts.

Occupational-health questionnaires exist in the catalog/schema; the patient UI only runs **general health**.

### 4.2 Patient destinations after onboarding

| Route | Behaviour |
| --- | --- |
| `/` Home | Visit card, outcome banner when present, next-step CTA |
| `/questionnaire` | Edit/resume the general-health questionnaire for the appointment |
| `/queue` | Queue number, assigned counter, status, patients ahead (after check-in), manual **Refresh** |
| `/payment` | Mocked package / covered / payable amounts; `POST /patient/payment/mock-pay` |
| `/records` | Read-only past visits (coverage, package, questionnaire summary, outcome) |
| `/upload/[token]` | Unauthenticated coverage UI for hardcoded demo tokens only |

Queue assignment is visible once the clinic has a planned or actual counter, **including before physical check-in** (“Ticket reserved”). After check-in the status is waiting. Internal review reasons and confidence scores are not shown to the patient.

Coverage reuse and upload also run inside onboarding. Home may still point at `/coverage`; that route is not a patient page — coverage is the Insurance onboarding step.

### 4.3 Document interpretation and eligibility

**Intent:** collapse manual chit-reading into structured facts plus staff confirmation.

**What ships:**

- Server-side classification and OpenAI Structured Output extraction (`backend/worker.py`, `backend/app/ai/extraction.py`) for PDF/JPG/PNG. Identity/e-card images must not enter this pipeline.
- Deterministic eligibility/package matching in Python services and versioned rules — the model does not decide coverage.
- Nurse **Forms** step: `DocumentCard` shows extracted facts, lets staff edit them, and confirm or unconfirm (`POST /tickets/{id}/documents/{doc}/confirm` and `/unconfirm`).
- Nurse **Package** and **Billing** steps confirm matched package, billing code, uncovered cost, and queue number.
- Demo tickets are seeded with documents and review cases (for example Q-014 ambiguous match, Q-015 missing document, Q-018 expired voucher).

**Honest limits:** the patient client submits a **file name**, not a binary upload to Storage. The kiosk file picker is not wired to extraction. Staff still confirm every determination before it is treated as final.

### 4.4 Single-ticket readiness and counter routing

Every visit keeps one `Q-*` ticket and its original ordering timestamp. Readiness (`processing` / `ready` / `needs_review`) is an internal staff state on that ticket. The patient does not take a second number.

```text
walk-in at kiosk                         → slow counter S1–S4  (enforced at ticket create)
booked AND readiness_state = ready       → fast counter F1–F2  (board display + seeded examples)
booked with any outstanding issue        → slow counter S1–S4
```

Walk-in → slow is enforced in `backend/app/services/kiosk.py` and `epicenter_create_walk_in_ticket`. Booked + ready → fast is the product rule used by the nurse board (`TicketRow`) and seeds (for example finished Siti Rahman on F1). There is no separate HTTP assigner that re-checks F/S eligibility on every write.

`/review` is not a staff destination; it redirects home. Exceptions stay on the same ticket. When `readiness_state` is `needs_review`, the task flow opens **ReviewGate** first (reason, evidence, next action; resolution methods such as replacement document or confirmed self-pay).

### 4.5 Nurse Dashboard and gated tasks

Primary navigation: **Dashboard**, **Database**, **Audit trail**, **Simulator**.

Dashboard (not labelled “Today” in the UI) is a three-column **Incoming / Ongoing / Finished** board. Cards show ticket id, name, processing stage, document confirm count, queue number, counter, and a “Needs confirmation” flag when the ticket is in review. Unfinished cards open `/tasks/{ticketId}`.

Gated steps (`frontend/nurse/lib/task-steps.ts`):

| Step | Gate |
| --- | --- |
| Identity & e-card | Staff attest in-person checks (`identity_confirmed`). Epicenter does not scan or decide identity. |
| Forms guidance | Unlocked after identity. Shows which forms apply; electronic documents are confirmed here. |
| Forms review | `forms_confirmed`, including a physical-forms checkbox when required. |
| Confirm package | Only if the ticket has documents (`package_confirmed`). |
| Billing & queue | `billing_confirmed` (billing code, uncovered cost, queue number). |
| Summary | Ticket stays the same; nurse can mark physical forms received and move the visit to ongoing. |

The Dashboard also hosts the **Operations assistant** (`POST /api/v1/assistant`) when OpenAI is configured. It may explain queue/metrics via reviewed tools; it cannot approve readiness, attest identity, confirm billing, or decide allocations.

### 4.6 Walk-in kiosk

`/kiosk` is a supervised intake form (patient name, supervising nurse, optional clinical-escalation checkbox) that calls `POST /kiosk/check-in`. It creates one slow-counter ticket. It is **not** in the side navigation.

The kiosk does not infer clinical urgency. Escalation copy tells the nurse to use the clinic pathway; ticket creation is not blocked by the checkbox. Coverage file input on the kiosk is UI-only.

### 4.7 Database and Audit

**Database** is an allowlisted patient-record browser (search, filter, sort, pagination, detail). It is not SQL.

- Create and view use the signed-in staff role (`registration` / `operations_admin`).
- Update and recoverable soft-delete require Clerk password reverification in a modal; FastAPI also checks freshness. Hard delete is unavailable.

**Audit** is a separate read-only clinic event browser (search, filters, pagination, row detail, CSV/JSON export of the visible page). `audit_log` / operational events reject update/delete. Sensitive detail keys are redacted.

### 4.8 Simulator

`/simulator` runs a deterministic discrete-event engine in `frontend/nurse/lib/simulation/`. It does not write operational patient, queue, or audit tables.

The UI currently plays **`single_ticket`** (play/pause, step, reset, 1–50×, scrub, JSON/CSV export). `serial_baseline` and `dynamic_allocation` exist in the engine and tests but are not selectable in the workspace. `GET /simulator/snapshots` returns labelled metadata for MCP/assistant; it is not the playback engine.

Fast eligibility inside the engine is pre-registered and not needing review. Walk-in arrivals in the cohort are never pre-registered, so they stay on the slow path.

### 4.9 MCP

FastAPI mounts two Streamable HTTP servers:

- **Operations** (`/mcp/operations`) — ticket, queue snapshot, operational summary, allocation read. Extraction-status, eligibility-preview, run-simulation, and compare-runs tools are **synthetic stubs**.
- **Insurance Format Registry** (`/mcp/insurance-registry`) — approved synthetic format schemas and maker/checker mapping proposals. It does not write canonical patient tables or decide eligibility.

Copilot Studio is not required locally. The patient and nurse apps remain usable when OpenAI or MCP is down.

### 4.10 Explicitly not built

- SMS/email of upload links, reminders, or document-issue notices
- Live Singpass / Myinfo
- Live payment or TPA portal submission
- A staff allocation approve/reject card on the Dashboard
- A dedicated Review worklist page
- Occupational-health questionnaire in the patient app
- Binary coverage upload from the patient or kiosk clients
- Clinic Assist / NEHR
- Automating identity or e-card checks (permanent non-goal)

## 5. User Stories (Covered by the Demo)

### Nurse

- As registration staff, I want Incoming / Ongoing / Finished cards with queue number and counter, so I can see the day’s flow without opening another system.
- As registration staff, I want to attest identity and e-card checks myself, so the system never pretends it verified the patient.
- As registration staff, I want gated forms, package, and billing steps on the same ticket, so exceptions do not issue a second queue number.
- As registration staff, I want extracted document facts on the Forms step so I confirm or correct them instead of retyping the chit.
- As registration staff, I want a supervised kiosk check-in that always assigns a slow counter.
- As an authorised nurse, I want Database create/view without a password prompt, and password reverification only for update/delete.
- As staff, I want a read-only Audit trail I can search and export.
- As a nurse running the demo, I want a Simulator that replays clinic flow without touching live tickets.
- As a nurse, I want an optional operations assistant that explains queue state and cannot approve clinical or billing actions.

### Patient

- As a scheduled demo patient, I want to sign in, complete synthetic Singpass / coverage / questionnaire onboarding, and see my visit on Home.
- As a returning patient in onboarding, I want to reuse coverage on file or upload a replacement, without being told that means eligibility is approved.
- As a patient, I want my queue number and counter in the app, including after they are reserved and before I reach the desk.
- As a patient, I want a clearly labelled demo payment that does not charge a card.
- As a patient, I want read-only records of past synthetic visits.

## 6. System Architecture (As Built)

```text
Patient Next.js (:3000) ─┐
                         ├── FastAPI /api/v1 ── Clerk JWT
Nurse Next.js (:3001) ───┘         ├── domain services (readiness, kiosk, billing)
                                   ├── DemoRepository or SupabaseOperationsRepository
                                   ├── OpenAI assistant + document worker
                                   └── /mcp/operations and /mcp/insurance-registry

Nurse Simulator ── frontend-only engine (no operational writes)
```

High-level visit path:

```text
Clerk patient account
  → synthetic Singpass onboarding
  → coverage reuse or document name + staff review
  → general-health questionnaire
  → one Q-* ticket with queue number and F/S counter
  → nurse identity / forms / package / billing confirmations
  → mocked payment and records
Walk-in: supervised kiosk → same ticket model on S1–S4
```

## 7. Guardrails

- Identity and e-card checks are staff attestations only. No scan, biometric, or automated pass/fail.
- Eligibility, package, and billing are not final without a nurse confirmation step.
- Extraction is advisory; rules and staff decide.
- Patient UI does not expose confidence, internal `needs_review` reasons, rules, or other patients.
- Staff mutations go through FastAPI. Database update/delete require backend-checked Clerk reverification.
- Audit history is append-only.
- The Simulator cannot write operational repositories.
- OpenAI and MCP are optional adapters. Dashboard, kiosk, tasks, queue, and payment work without them.

## 8. Regulatory & Compliance Posture (Singapore Context)

- **PDPA:** The demo uses synthetic data only. A real deployment must minimise fields, encrypt identifiers, and complete processor/residency review before any live document reaches OpenAI.
- **AIHGle 2.0:** This is clinical-ops administrative automation. It does not diagnose or treat. Keeping identity in-person further limits risk.
- **Hallucination:** LLM extraction is separated from rules-based matching; staff confirm before finalising.

## 9. Demo Success Criteria

| Criterion | Evidence in this repo |
| --- | --- |
| Separate panels | Patient `:3000` and nurse `:3001` with distinct route trees |
| One ticket | Queue number and counter on both apps; walk-in does not issue a second id |
| Counter policy | Kiosk always S1–S4; board treats booked+ready as fast |
| Pre-arrival work | Clerk onboarding (synthetic Singpass, coverage, questionnaire) before the desk |
| Staff confirmation | Gated identity / forms / package / billing steps |
| Exceptions stay put | ReviewGate on the same ticket; `/review` redirects home |
| Mocked payment | Labelled demo pay; no gateway |
| Intentional CRUD | Password step-up on patient update/delete |
| Immutable audit | Read-only Audit panel |
| Isolated simulator | Client engine; no operational writes |
| Optional AI | Assistant + MCP; apps usable without the key |

Timed “30-second confirmation vs 3–5 minute reading” remains a **demo assumption**, not a measured clinic result.

## 10. Key Risks & Mitigations

| Risk | Mitigation in the demo |
| --- | --- |
| PRD overclaims unbuilt channels | This document lists SMS tokens, live Singpass, allocation UI, and outbound notices as **not built** |
| LLM assigns wrong coverage | Rules engine + mandatory staff confirmation |
| Unusual document is guessed | Failed gates → `needs_review` on the same ticket |
| Second queue number after review | One `Q-*` row; ReviewGate does not mint a new id |
| Walk-in takes a fast counter | Kiosk create only assigns S1–S4 |
| Identity UI mistaken for automated KYC | Copy and stored record are attestations only |
| Simulator corrupts the board | Engine is frontend-only |
| Assistant approves a move | Tools are read/explain; writes stay in the staff UI |
| Mock pay mistaken for a real charge | “No card is charged and no money moves.” |
| Demo patient account mistaken for production IAM | One mapped synthetic booking; not a full patient IAM design |

## 11. Remaining Decisions and Deferred Work

Deferred on purpose:

- Live Singpass/Myinfo, SMS/email upload links, and outbound document-issue notices
- Binary Storage uploads from patient and kiosk UIs
- Dashboard allocation approve/reject UI (API already exists for operations admin)
- Simulator scenario picker for `serial_baseline` and `dynamic_allocation`
- Occupational-health questionnaire in the patient app
- Live TPA submission, PayNow/Stripe, Clinic Assist/NEHR

Still clinic-owned rather than product-owned:

- Exact package/billing outcomes for the seven fixture code families (`MRDEB`, `EVWPA`, `EVWME`, `BLPDE`, `BLPHS`, `NSTNBU`, `MOL0199VME`)
- Operational cost per extracted document for the brief’s cost-realism criterion
