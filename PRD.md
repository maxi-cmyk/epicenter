# Product Requirements Document

## AI-Assisted Pre-Registration & Eligibility Verification for Parkway Shenton

- **Status:** Draft v1 (supersedes prior CDMP trend-monitoring PRD — see §0)
- **Track:** Hack4Health 2026, Technical Track
- **Constraint alignment:** Microsoft Copilot Studio portability (per official constraints)

## 1. Problem Statement

### 1.1 Current Workflow

Every patient — whether a GP consultation or a corporate health screening — currently requires front-desk staff to manually determine identity, employer/insurer, applicable benefits, screening package, and billing arrangement after the patient has already reached the counter. This is complicated by a lack of standardisation: the supplied synthetic bundle contains nine distinct medical-document examples across seven issuer/code families, including referral letters, vouchers, underwriting requests, government authorisation forms, and an employer appointment email. The same issuer code can also appear on different document types. Staff must interpret the selected tests, packages, dates, and instructions in context, cross-reference the right coverage rules, and manually key the result into one or more systems — sometimes twice, once into the clinic's own system and again into a separate TPA portal after the visit.

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

Excluding the clinical encounter itself, this totals approximately 23–32 minutes of administrative work per patient. For a clinic processing 40 patients in a morning, that is roughly 1,080 minutes (18 hours) of cumulative administrative effort — and because most of this happens sequentially at a single registration counter, delay for one patient compounds waiting time for every patient behind them, including those who may need more urgent attention.

### 1.3 Root Cause

The problem is explicitly not identity verification itself — that must and will remain an in-person, secure step. There are two distinct root causes, and most solutions to this brief will only address the first:

**(a)** Document interpretation and eligibility determination only happen after the patient physically arrives, and that interpretation is manual, repetitive, and error-prone due to the lack of standardisation across payers.

**(b)** The same small set of source data — patient identity, the coverage document, and clinical/allergy information — is independently re-derived at five separate points across a single visit, rather than captured once and reused. Tracing the as-is workflow step by step:

| Touchpoint | What's re-entered or re-checked | Already captured at |
| --- | --- | --- |
| Step 4 — TPA form | Patient identity, written onto a second paper record | Step 3 (registration) |
| Step 5–6 — Eligibility & package verification | Coverage/package details, re-checked against the original document | Step 4 (document interpretation) |
| Step 6 — On-site consent/disclosure forms (×2) | Name, NRIC, DOB, contact, address | Step 3 (registration) |
| Step 11 — Medication dispensed | Drug allergy information, asked again verbally | Step 3 registration and/or Step 6 questionnaires |
| Step 12 — Payment | The original coverage document, re-checked a third time; then re-entered a second time into the TPA portal | Step 4 (document interpretation) and Steps 3–11 (visit data) |

Most solutions to this brief will only notice two of these five touchpoints — typically registration-to-questionnaire duplication, since it's the most visible. The allergy re-ask at step 11 in particular is easy to miss because it's mid-workflow and framed as a routine safety check rather than a data problem — but it is the same underlying redundancy, and it is patient-safety-relevant, not just an efficiency loss.

### 1.4 Why It Matters

This bottleneck affects every patient passing through registration, not a narrow subgroup — it is a high-frequency, high-cumulative-cost workflow problem. Because most of this happens sequentially at a single registration counter, a single patient whose document needs extra handling (illegible chit, unfamiliar TPA format, missing information) doesn't just cost that patient time — it compounds directly onto the wait of every patient behind them, including those who may need more urgent attention. This is a structural property of a single-queue, single-counter design, not something that can be fixed by making any one patient's processing faster on average.

## 2. Constraints (from Official Brief — Non-Negotiable)

- **Copilot Studio portability required.** The solution does not need to be built entirely in Copilot Studio during the hackathon, but must demonstrably be portable/integrable into it.
- **Identity verification and e-card validation must remain in-person** and are explicitly out of scope for automation. This PRD does not propose automating these steps under any circumstance.
- **Operational cost must be realistic.** The solution should be economically viable to deploy, not merely technically impressive.
- Everything else may be automated: document interpretation, eligibility checks, package matching, and registration data entry.

## 3. Goals

| Goal | Success signal |
| --- | --- |
| Retrieve and process patient/coverage information before the patient reaches the front desk | Pre-registration data (identity, coverage, package) is resolved ahead of arrival for scheduled appointments, and rapidly on arrival for walk-ins |
| Eliminate manual document interpretation | Chit/voucher/referral-letter content is extracted and structured automatically, not read and re-typed by staff |
| Capture the patient's core data once and reuse it across every touchpoint that needs it | All five re-entry/re-check points identified in §1.3(b) — not just registration-to-questionnaire — draw from a single record |
| Prevent one patient's processing time from delaying every patient behind them | Patients needing manual review are routed off the main line rather than serialising against straightforward cases |
| Reduce TPA double-entry | Structured eligibility/package data is available for both clinic system and (conceptually) TPA portal submission from a single source |
| Preserve mandatory in-person steps | Identity verification and e-card validation remain explicitly untouched, staff-performed steps |
| Keep staff and patients in control | Every automated determination is reviewable and correctable by staff before being finalised |

### Non-Goals (Explicitly Out of Scope)

- Automating identity verification or e-card validation (constraint #2 — hard boundary)
- Clinical decision-making, diagnosis, or treatment recommendation
- Chronic disease trend monitoring (prior direction — superseded, see §0)
- Real integration with Parkway Shenton's production Clinic Assist system or live NEHR (conceptual integration only, per judging criteria §5)

## 4. Core Product Scope

### 4.1 Primary Feature — Automated Document Interpretation & Eligibility Matching

**What it does:** Ingests a patient's medical-administration document (medical chit, insurer voucher, corporate referral/underwriting letter, TPA/government authorisation form, or employer appointment notice) — via photo/scan/upload — and automatically extracts the fields staff currently read manually: document type; issuer/employer/TPA and code; patient name and identifier when present; policy, voucher, proposal, contract, certificate, package, or check-up references; selected tests/package contents; issue, appointment, fulfil-by, and validity dates; venue; billing/policyholder details; and special instructions. Fields are nullable because the samples do not all contain the same facts. The extracted facts are matched against a versioned rules table to determine the applicable package and billing arrangement or to produce a staff-review reason.

**Why this is the highest-value target:** This is the single most time-consuming, most error-prone, and most duplicated step in the current workflow (document interpretation ~3–5 min + eligibility check ~3–5 min + package verification ~2–4 min = up to ~14 of the ~23–32 total administrative minutes per patient, before even reaching billing). It is also the step most directly caused by lack of standardisation across payers — exactly the kind of unstructured-document variation an LLM-based extraction layer is well suited to normalise, since the underlying documents (as seen in the sample chit letters) vary in layout and wording but contain a consistent underlying set of facts (who, what coverage, what's requested, what's valid).

**Design requirements:**

- **Extraction only, not judgment.** The system extracts and structures what the document says; a hard-coded/rules-based eligibility table (not LLM inference) determines what package/coverage that maps to, to avoid hallucinated coverage decisions. The LLM's job is parsing messy input into structured fields — the same "reliable backbone + LLM for parsing unstructured input" pattern used successfully in earlier research on this project.
- **Readiness-gated, not self-confidence-driven.** A document passes extraction only when its schema is valid, every required field for that document type is present, each required fact has source evidence, any patient identifier matches exactly within the authorized scope, validity can be established, and the rules engine produces one clean result. Model-provided confidence is advisory only. Any failed gate routes the case to staff review rather than being guessed.
- **Always staff-reviewable before finalising.** Extracted/matched data is presented to staff for confirmation, not silently auto-committed — consistent with the human-in-the-loop principle carried through this project's design.
- **Explainable.** Staff can see the page and supporting source excerpt for every extracted field. Precise bounding-box highlighting is shown only when a future OCR adapter supplies reliable coordinates; it is not required for the no-Azure demo baseline.
- **Checkbox-aware.** For forms and vouchers, checked and unchecked options are preserved separately. Only explicitly selected options may become requested tests or package inputs.
- **Patient-match-safe.** Documents without an explicit patient identifier, or with a conflicting identifier, always require staff review. Name-only matching never silently attaches a document to a patient.
- **Recoverable capture and processing.** Staff/patient upload flows show file preview, supported type/size, upload and processing progress, success, and actionable camera/file/network/timeout/extraction errors without duplicate submission.
- **Controlled correction.** Editing an extracted fact displays the original and corrected values, requires a reason and staff re-authentication, preserves failed edits for retry, and writes an immutable audit entry.

### 4.2 Core Add-On Feature — Pre-Cleared Fast Queue and Review Queue

**What it does:** Rather than a single serial line, the system uses a strict two-queue rule. The **fast queue** is reserved for booked patients who completed pre-registration before arrival and whose required documents pass every extraction/validity gate and match cleanly. Everyone else enters the **review queue (slow path)**: all walk-ins, booked patients who did not complete pre-registration, and any case with a missing, expired, incomplete, unfamiliar, unsupported, or ambiguous document or eligibility match.

**Routing rule:**

```text
IF appointment is booked
   AND pre-registration is complete before arrival
   AND every required document is present, valid, and readiness_status = pass
   AND every eligibility/package match is clean
THEN → FAST QUEUE
ELSE → REVIEW QUEUE (SLOW PATH)
```

**Why this is a core feature, not an optimization:** The brief's own numbers describe a structural failure, not an average-speed problem: because most administrative tasks occur sequentially at a single registration counter, one patient's extra time directly compounds onto the wait of everyone behind them — including patients needing more urgent attention. Making the average patient faster (§4.1) reduces this but does not eliminate it, because the slowest cases still serialise against everyone else. Only decoupling fast and slow cases into separate queues actually removes the compounding effect at its source. This is a genuinely different kind of fix from "process each document faster" — it is a systems/queueing-design decision, not a per-patient feature, and it directly targets the compounding-delay mechanism named explicitly in the brief's Administrative Impact section.

**Design requirements:**

- A booked patient's routing decision is made during pre-registration, before arrival. Fast-queue status is granted only after every prerequisite passes; it is never inferred from booking status alone.
- Walk-ins always enter the review queue, even if their document later extracts cleanly. Walk-ins are less common and are intentionally grouped with cases needing more staff handling rather than given a separate queue.
- The review queue is not a penalty state. Patients routed there still receive full staff attention; the point is to protect the predictable pre-cleared path, not deprioritise anyone's care.
- Queue assignment is visible to staff with a machine-readable reason such as `walk_in`, `prereg_incomplete`, `missing_document`, `extraction_needs_review`, `expired_document`, or `ambiguous_match`.
- Staff can see queue composition to manage counter allocation in real time, but manually moving a patient into the fast queue requires all fast-queue prerequisites to be satisfied.
- The staff queue board tracks appointment date/time and separates patients into **Incoming**, **Ongoing**, and **Finished** views:
  - **Incoming:** booked patients who have not checked in. Shows scheduled date/time, expected queue number, fast/review assignment, and expected counter number.
  - **Ongoing:** checked-in patients who have not completed the visit. Shows current queue number, assigned counter, and current processing stage.
  - **Finished:** completed visits. Shows appointment date, completion time, final queue/counter, and completion status for operational review.
- Expected queue and counter numbers are generated once a booked patient's pre-registration route is known. They are planning assignments, not guarantees; the actual counter may change at check-in or when staff rebalance capacity, and the change is logged.
- Check-in records staff confirmation that identity verification and, where applicable, e-card validation were completed manually using the approved in-person process. The system does not perform, assist with, scan for, or decide either check; it stores only the staff attestation, timestamp, and allowed not-applicable reason.
- The Review workspace lists every slow-path case with its appointment/walk-in time, review reason, document state, time waiting, counter, and next action. It has explicit empty, loading, permission, and recoverable error states.
- Appointment lifecycle also records rescheduled, cancelled, and no-show outcomes. A rescheduled booking keeps an audit link to its prior slot; cancelled/no-show visits appear under Finished with their outcome.
- Counter-allocation controls may rebalance expected or actual counters but cannot promote a patient to the fast queue unless every fast-queue prerequisite passes.

### 4.3 Core Add-On Feature — Unified Patient Record Across All Touchpoints

**What it does:** A single structured patient record — identity, contact details, coverage/eligibility, and clinical/allergy information — captured once and reused everywhere it is needed across the visit, rather than re-derived at each step. This directly addresses all five re-entry/re-check touchpoints identified in §1.3(b), not only the registration-to-questionnaire duplication that is the most visible instance of the pattern:

| Touchpoint addressed | How |
| --- | --- |
| TPA form re-entry (step 4) | Identity pulled from the registration record, not re-keyed onto a second paper form |
| Eligibility/package re-checking (steps 5–6) | Reuses the structured extraction from §4.1 rather than staff re-reading the source document |
| On-site consent/disclosure forms (step 6) | Name, NRIC, DOB, contact, and address pre-filled from the registration record; patient/staff only complete genuinely new fields (medical history, lifestyle) |
| Allergy re-ask at medication dispensing (step 11) | Drug allergy information already captured at registration and/or questionnaire is surfaced to the pharmacist directly, rather than re-asked verbally from scratch |
| Payment / TPA portal re-entry (step 12) | The same structured coverage and visit record feeds billing determination and (conceptually) TPA portal submission, rather than staff re-checking the original document a third time |

**Why this is scoped as a core feature, not a stretch:** Treating this as "reduce duplicate entry" and stopping at the questionnaire step (as an earlier draft of this PRD did) understates the actual pattern in the brief. The allergy re-ask at step 11 in particular is a patient-safety-relevant instance of the same redundancy that is easy to miss because it doesn't look like a paperwork problem on the surface — but it is the identical mechanism (data already known, re-derived anyway) as the more visible form-filling redundancy.

**Design requirement:** The pharmacist-facing allergy surface (step 11) is display-only in this system's scope — it presents already-recorded allergy information to support the pharmacist's own verbal check, it does not replace or automate the clinical safety check itself.

The questionnaire/consent surface visibly separates read-only prefilled identity/contact data from genuinely new answers, autosaves long-form drafts, and records the approved consent event without inventing consent. The billing/TPA surface shows the confirmed source, package, covered/patient amounts, correction reason, and demo payload preview; it requires staff confirmation and never claims a live TPA submission.

### 4.4 Secondary Feature — Pre-Arrival Processing for Scheduled Appointments

**What it does:** For scheduled (non-walk-in) appointments, the system processes the patient's coverage document and pre-fills registration and questionnaire data before the patient arrives. On arrival, front-desk staff only need to perform identity verification and confirm the pre-processed information, rather than starting document interpretation from zero. This pre-registration stage is the only route into the fast queue: a booked patient enters it only when every required document and match passes before arrival; otherwise they enter the review queue.

**Submission mechanism — patient upload link, not a full patient account.** Rather than building a full patient-facing account system (separate login, credential management, its own auth surface), a scheduled patient receives a tokenized, single-use upload link tied to their specific appointment — e.g., sent by SMS/email at booking. The link opens a minimal, unauthenticated-but-scoped page: upload the coverage document, done. No password, no account, no persistent session. For corporate batch screening, the same mechanism extends naturally — each employee gets their own tokenized link ahead of the scheduled screening day, rather than staff manually collecting documents from a group.

**Check-first coverage reuse.** Before showing the upload control, the system resolves the appointment-bound patient by normalized NRIC/FIN/passport, using email only as an unambiguous fallback inside the already authorized scope, and checks for a prior coverage document. A new patient, a conflicting/name-only match, or a patient with no prior document proceeds directly to the standard upload flow. A returning patient sees only the prior issuer and document date — for example, "We have your Meridian coverage on file from 12 February 2026. Still the same?" — with two choices:

- **Yes, same coverage:** reuse the prior document as the input for this appointment, then re-run validity and eligibility rules and place the result through the normal staff-review gate. This confirms reuse of the document; it does not guarantee that coverage is still valid.
- **No, upload new document:** continue to the existing photo/file upload flow and process the new document through the standard extraction pipeline.

The check is server-side and scoped to the patient already associated with the single-use appointment link; it is not a public NRIC/email search endpoint. The reuse decision and the matching method are logged for audit.

The patient flow includes checking/loading, no-prior-match, ambiguous-match-without-disclosure, invalid/used/expired-token, upload progress, validation failure, retry, and receipt-confirmation states. A successful upload/reuse message confirms only that the item was received for staff review; it never promises fast-queue or eligibility approval.

### 4.5 Staff and Patient View Boundaries

The product has two deliberately separate interface surfaces.

**Staff workspace:** authenticated operational views for queue lifecycle, appointment prerequisites, manual check-in attestations, review worklists, document extraction/correction, records search, questionnaires/consent prefill, pharmacy allergy attestation, billing/TPA confirmation, audit history, and counter allocation. Staff may see operational reasons and source-document evidence appropriate to their role.

**Patient surface:** a minimal token-scoped upload flow plus a small seeded demo account with Home, Queue, Payment, and Records. Patients see only their own appointment, document-submission outcome, queue/counter status, mocked payment/receipt, and read-only visit/questionnaire history. They never see extraction confidence, review reasons, internal rules, audit data, or other patients.

Both surfaces require explicit loading, empty, validation, failure, retry, and success states. Status is communicated through text and accessible semantics, not color alone; staff tables remain keyboard-operable and patient views are mobile-first.

### 4.6 Demo-Scoped Feature — Patient Account (Small, Fixed Demo Pool)

**What it does:** A small set of demo patient accounts (a handful of seeded logins, e.g. for judges to explore) providing: document/detail upload for an upcoming visit, a live queue number and station once checked in, a mocked payment step, and read access to past visit records (coverage/package history, past questionnaire responses).

**Design requirements:**

- Clerk provides sign-in and session management for the seeded demo accounts. Each Clerk user is mapped to one local patient record; this does not turn the separate single-use upload link into a user account.
- Upload reuses the same extraction pipeline as §4.1/§4.4 — no separate logic, just an authenticated entry point instead of a tokenized one.
- The authenticated upload screen uses the same check-first coverage-reuse step as the tokenized link. The account's patient record is used for the lookup; the patient can reuse the prior document or upload a replacement.
- Queue number/station is a read view onto the same queue assignment staff already see (§4.2) — the patient sees their own queue position, not a parallel system.
- The demo account has a small Home/Queue/Payment/Records shell. Queue states cover skeletal initial loading, manual refresh, before check-in, fast/review waiting, called, counter changed, delayed, finished, stale/load failure, and retry without exposing internal review reasons. The Queue screen has a labelled Refresh control at the top right.
- Payment is mocked, not a live gateway integration — consistent with the mocked-delivery approach used elsewhere in this project's design (SMS/email). Shows a realistic confirmation flow with no real transaction, and is built so a real gateway (e.g. PayNow, Stripe) could be substituted behind the same interface later, without being a live dependency risk during judging.
- Mocked payment covers not-ready, processing, success/receipt, failure/retry, and already-paid states; duplicate submission cannot create a second receipt.
- Medical records view is read-only — the patient sees their own coverage/package history and past questionnaire responses, including visit detail and empty/loading/error states; nothing here allows editing clinical or coverage data, which remains a staff-confirmed action per §7.
- Explicitly not production-scoped. This is not a claim that a full self-service patient identity/authentication system has been designed or secured to production standard — it is a demo-scale illustration of the pattern, clearly distinguished from that larger undertaking in the pitch.

### 4.7 Explicitly Deferred / Future Work

- Full production-scale patient identity and authentication system (self-registration, password recovery, MFA, etc.) — §4.6 is a small, fixed demo pool, not this
- Real payment gateway integration (PayNow, Stripe, or similar) — mocked for the hackathon (§4.6)
- Conceptual TPA portal auto-submission (structured eligibility data could, in production, be submitted to insurer/TPA portals automatically — described as an architecture point per judging criteria §5, not built as a live integration)
- Full corporate batch-screening scheduling workflows
- Any automation of identity verification or e-card validation (permanently out of scope, not just deferred — see §2)

## 5. User Stories

### Front-Desk / Registration Staff

- As registration staff, I want a patient's coverage document to already be interpreted before they reach my counter, so that I only need to verify identity and confirm details rather than read and decode the document myself.
- As registration staff, I want the system to flag which fields it's unsure about, so that I know exactly what to double-check rather than re-verifying everything from scratch.
- As registration staff, I want to see which part of the source document produced each extracted field, so that I can quickly confirm accuracy without re-reading the whole document.
- As registration staff handling a TPA patient, I want the structured coverage data to be reusable for the TPA portal entry, so that I'm not manually typing the same information twice.
- As registration staff, I want appointments grouped by incoming, ongoing, and finished status with their dates and expected or actual counters, so that I can plan arrivals and track the day's flow.
- As registration staff, I want to record that I completed the required identity and e-card checks manually, without the system attempting to perform or decide those checks.
- As registration staff, I want one review worklist with the reason and next action for every slow-path patient, so that exceptions do not disappear between screens.
- As registration staff, I want missing-document reminders, reschedule/cancel/no-show actions, and counter rebalancing to be auditable from the appointment view.
- As billing staff, I want to confirm or correct the reused coverage/billing record and preview the demo TPA payload from one screen.

### GP / Clinical Staff

- As a GP, I want confirmed patient and coverage information available before or at the start of the consultation, so that administrative delay upstream doesn't cut into consultation time or delay care for other patients.
- As a GP, I want to trust that identity has been properly verified in person regardless of how much of the paperwork was automated, so that clinical safety isn't compromised for administrative speed.
- As a pharmacist, I want the recorded allergy surfaced while I perform the verbal check myself, then record that the manual check occurred.

### Patient

- As a patient with a scheduled appointment, I want to submit my coverage document ahead of time, so that I spend less time at the counter before being seen.
- As a patient filling in screening questionnaires, I want my basic details to carry over automatically, so that I'm not re-typing my name, NRIC, and contact information on every form.
- As a patient who has checked in, I want to see my queue number and assigned counter, so that I know what to expect without repeatedly asking staff.
- As a patient, I want to pay for my visit through the app, so that I don't need to queue separately at a payment counter.
- As a returning patient, I want to view my past visit and coverage history, so that I don't need to ask staff to look it up for me.
- As a returning patient, I want to confirm that my previous coverage is still the same instead of uploading the same document again, while still being able to replace it when my coverage has changed.
- As a patient, I want clear upload, queue, payment, and records states—including errors and retries—without seeing internal confidence scores or operational review reasons.

## 6. System Architecture

### 6.1 High-Level Flow

```text
Patient's coverage document (chit/voucher/referral letter)
   → captured via upload/scan (pre-arrival) or at check-in (walk-in)
   → Document Extraction Layer (schema-constrained parsing of varied layouts)
   → Typed facts + selected options + page/source-excerpt evidence
   → Readiness gates: required fields, identifier, validity, and evidence
   → Eligibility & Package Matching Engine (rules-based lookup, not LLM judgment)
   → Queue Assignment: booked + pre-registration complete + all readiness gates/matches clean
     → fast queue; every other case (including all walk-ins) → review queue
   → Staff review/confirmation screen
   → Confirmed record feeds: registration system, questionnaire pre-fill,
     billing determination, (conceptually) TPA portal submission
   → [In-person, untouched] Staff manually perform identity verification
     and e-card validation using the approved clinic process
   → System records staff attestation only; it does not perform either check
   → Patient proceeds to queue / consultation
```

### 6.2 Components

| Layer | Function | Notes |
| --- | --- | --- |
| Document Extraction Layer | Schema-constrained parsing of PDFs/images into typed facts, selected options, and page/source-excerpt evidence | Handles the nine supplied document variants without assuming every field exists |
| Eligibility & Package Matching Engine | Versioned rules lookup using issuer code plus document type, package/check-up code, and requested items | Issuer code alone is insufficient because one code can occur on different document types; decisions remain deterministic, not LLM inference |
| Patient/Registration Record Store | Single structured record per patient, reused across registration and questionnaire steps | Eliminates the duplicate-entry problem named in §1.1/§4.3 |
| Staff Review Interface | Presents extracted + matched data for confirmation before finalising | Human-in-the-loop; each field shows page/excerpt evidence, with region highlighting only when coordinates exist |
| Pre-Arrival Intake Channel | Where scheduled patients submit documents ahead of arrival, via a tokenized single-use upload link (no patient account/login) tied to their appointment | Directly addresses the "before they reach the front desk" requirement in the brief, without the added auth/security surface of a full patient account (see §4.4) |
| Coverage Reuse Check | Resolves the appointment-bound/authenticated patient by normalized identifier, with unambiguous scoped email fallback, then records reuse or replacement | Avoids duplicate uploads without exposing a public patient lookup or bypassing validity, eligibility, and staff review |
| Queue Operations Board | Tracks scheduled date/time, Incoming/Ongoing/Finished status, fast/review routing, and expected vs. actual queue/counter numbers | Gives staff one date-aware operational view from pre-arrival planning through visit completion |
| Manual Check Attestation | Records which staff member confirmed completion of the approved manual identity/e-card process and when | Stores no automated verification decision; check-in fails safely if the attestation cannot be saved |
| Review and Exception Workspace | Lists slow-path cases and supports reasoned, re-authenticated corrections with source evidence | Keeps original/corrected values and immutable audit history |
| Questionnaire, Pharmacy, and Billing Surfaces | Reuse confirmed patient/coverage data while recording approved consent, manual allergy-check attestation, and staff billing confirmation | Demonstrates the remaining repeated-data touchpoints without automating clinical checks or live TPA submission |
| Counter Allocation and Audit | Assigns fast/review counter pools, records rebalancing, and exposes a read-only event log | Counter changes cannot bypass fast-queue prerequisites |

### 6.3 Data Sources (Demo)

The supplied archive is the complete demo-data contract:

| Source | Contents | Import/use decision |
| --- | --- | --- |
| `patient_registration_synthetic.csv` | 300 rows, 12 identity/contact/allergy columns, 300 unique nonblank identifiers | Canonical patient seed. Normalize DOB from `DD/MM/YY` to a database date and retain an import warning where the century required a pivot rule. |
| `general_health_questionnaire_mock_patients.csv` | 30 rows, 41 columns | Reduced mock export for demo history/prefill. Blank conditional fields remain `null`, not `false`. |
| `occupational_health_questionnaire_mock_patients.csv` | 30 rows, 27 columns | Reduced mock export for demo history/prefill. Preserve the employer/insurer disclosure-consent field independently. |
| `Parkway_Shenton_Questionnaires_Field_Reference.docx` | Full live-field reference for both questionnaire types | UI/schema reference. It contains more conditional fields, matrices, screening/vaccination details, and signatures than the mock CSVs; absent CSV fields must not be fabricated. |
| `Sample Medical Chit Letters (v2).docx` | Nine synthetic one-page documents across seven code families | Split/render into nine individual PDF/image fixtures before extraction tests. The combined DOCX itself is not a patient upload fixture. |

Dataset reconciliation rules:

- Normalize and join questionnaires to patients by exact NRIC/FIN/passport first. Across both questionnaire files there are 57 unique people: 51 match the registration dataset and six do not. Unmatched responses enter an import-exception list and do not silently create patient records.
- Three people have both questionnaire types; preserve both appointment/questionnaire records.
- Names agree for matched rows, but questionnaire emails frequently differ from registration emails. Questionnaire email is retained as source data but never overwrites the canonical registration email automatically. Email remains an unambiguous, scoped fallback only when no identifier is available.
- Registration DOB uses `DD/MM/YY`; questionnaire DOB uses `DD/MM/YYYY`. Four-digit questionnaire DOB disambiguates matching rows. Remaining two-digit years use a documented import pivot and are flagged if they produce an implausible age.
- Six medical-document fixtures contain explicit patient identifiers and all six match registration records. The three fixtures without an identifier must exercise the staff-review path; they may not be attached automatically by name.
- Because the questionnaire CSVs are reduced exports, demo completeness is measured against the columns actually supplied. The fuller field-reference document guides future UI expansion but does not turn absent answers or signatures into completed consent.

### 6.4 Copilot Studio / Microsoft Ecosystem Portability

Per the official constraint (Copilot Studio use not required during the hackathon, but portability must be demonstrated):

- Document extraction and eligibility-matching logic exposed as clean API endpoints with defined input/output schemas.
- Wrapped as MCP tool(s) — e.g., `extract_coverage_document(file)`, `match_eligibility(extracted_fields)`, `get_patient_record(patient_id)` — so a Copilot Studio agent could consume the same capabilities via "Add an action → MCP server."
- Submission includes a diagram mapping this architecture to Copilot Studio's action/knowledge-source model, and conceptually to Clinic Assist/NEHR integration points, per judging criteria §5.

## 7. Guardrails & Human-in-the-Loop Requirements

- Identity verification and e-card validation are never automated, under any configuration. This is a hard constraint, not a design preference.
- The interface only records a staff attestation after those checks are completed manually. It does not capture evidence, scan identity/e-card data, suggest a result, or treat a failed save as a successful check.
- No eligibility/coverage/billing determination is finalised without staff confirmation.
- Every extracted field is explainable — traceable to the specific part of the source document that produced it.
- Any failed extraction-readiness gate is flagged with a reason rather than guessed; model confidence is advisory only.
- Reusing a prior coverage document never reuses an old eligibility decision. Validity and eligibility rules run again for the new appointment, followed by staff confirmation.
- All actions are logged, supporting both audit and the ability to correct systematic extraction errors over time.
- Patient views expose only patient-scoped outcomes; extraction confidence, review reasons, internal eligibility rules, staff audit data, and other patients are never shown.
- Loading, empty, error, retry, disabled, and success states are explicit. Status never relies on color alone, and critical controls are keyboard/touch accessible.

## 8. Regulatory & Compliance Posture (Singapore Context)

- **PDPA:** Patient identity and health data are involved throughout. The demo uses only the supplied synthetic data. Any real deployment must minimise retained fields, encrypt direct identifiers, disclose only the minimum necessary content to approved processors, configure retention/deletion, and complete the required provider and cross-border/data-residency review before OpenAI or any external service processes a patient document. A conceptual TPA/insurer submission remains a separate disclosure event. The occupational questionnaire's employer/insurer disclosure consent is stored independently and never inferred from the general declaration or a missing field.
- **AIHGle 2.0 (MOH/HSA):** This is squarely a "Clinical-Ops" administrative automation tool — it does not diagnose, treat, or make clinical judgments, which is a favourable regulatory posture. The constraint that identity verification stays in-person further limits risk exposure.
- **Governance & Safety (judging criterion):** Hallucination mitigation is addressed structurally (§6.2) by separating LLM-based extraction from rules-based eligibility determination — the LLM never decides coverage, it only reads documents.

## 9. Success Metrics (Demo-Scoped)

| Metric | Target |
| --- | --- |
| Document extraction accuracy | All nine split document fixtures produce schema-valid output or an explicit review reason; required extracted facts and selected checkboxes are correct against fixture expectations |
| Patient matching safety | All six identifier-bearing document fixtures match the intended registration record; all three identifier-free fixtures require staff review rather than name-only auto-linking |
| Dataset import integrity | 300 registration rows load once; 51 uniquely matched questionnaire people link by normalized identifier; six unmatched people are reported without silent patient creation; three dual-questionnaire patients retain both records |
| Time saved (demo comparison) | Visibly faster path from "document received" to "package/eligibility confirmed" vs. the ~14-minute manual baseline (interpretation + eligibility + package verification) stated in the brief |
| Queue-splitting impact (demo comparison) | Simulated queue visibly shows a booked, fully pre-cleared patient entering the fast queue while walk-ins and any incomplete or uncertain cases enter the review queue, vs. a single-line baseline |
| Queue lifecycle traceability | Every demo visit retains its appointment date and visibly transitions from Incoming to Ongoing to Finished, with expected counter shown before arrival and actual counter recorded after check-in |
| Duplicate entry eliminated | Patient details entered once, demonstrably reused across all five touchpoints identified in §1.3(b) — not only registration-to-questionnaire — in the demo |
| Human-in-the-loop integrity | 100% of extracted/matched records shown for staff confirmation before being treated as final in the demo |
| Manual-check boundary | 100% of identity/e-card records are staff attestations of a manually completed process; the demo contains no automated verification result or simulated scan |
| Screen-state completeness | Demo covers loading, empty, validation/error, retry, and success for upload/reuse, review, queue, payment, and records flows |
| Patient/staff separation | Patient demo routes expose only the signed-in/token-scoped patient's outcomes and never expose confidence, review reasons, rules, or audit records |
| Copilot Studio portability | A working (or clearly diagrammed) MCP tool wrapping at least one core function |

## 10. Key Risks & Mitigations

| Risk | Mitigation |
| --- | --- |
| LLM misreads a chit and assigns wrong coverage | Rules-based eligibility engine separated from extraction (§6.2); mandatory staff confirmation (§7) |
| Extraction fails silently on an unusual document format | Schema, evidence, identifier, validity, and unique-rule readiness gates (§4.1) route unresolved cases to staff rather than guessing |
| Issuer code maps to the wrong rule because one code appears on multiple document types | Rule lookup keys on issuer code plus document type and, where present, package/check-up code and selected requested items; ambiguous results route to review |
| Checked and unchecked form options are flattened into one test list | Extraction preserves option state and only selected options feed matching; contract tests cover every checkbox-style fixture |
| A document without an identifier attaches to the wrong same-name patient | Auto-linking requires an exact identifier within the authorized scope; identifier-free/conflicting documents always require staff review |
| Questionnaire email overwrites the canonical patient email | Registration remains canonical; questionnaire contact values retain source provenance and mismatches are reviewable rather than auto-merged |
| Two-digit and four-digit DOB formats are interpreted inconsistently | Import normalizes both formats, uses four-digit questionnaire DOB where available, documents the remaining century pivot, and flags implausible ages |
| Queue-splitting creates a two-tier experience that feels unfair to review-queue patients | Explicit design requirement (§4.2) that the review queue is an operational routing decision, not a deprioritisation — patient-facing UX should call it the "review queue," not the "slow queue," and explain when more processing is needed |
| A booked patient is incorrectly placed in the fast queue before all prerequisites pass | Fast-queue eligibility is a strict all-gates rule: booked appointment, pre-registration completed before arrival, every required document valid with `readiness_status = pass`, and every match clean |
| Overclaiming feasibility of real Clinic Assist/NEHR integration | Judging criteria explicitly ask for conceptual integration only — PRD and pitch should describe the integration pattern honestly, not claim a working live connection |
| Identity verification scope creep | Treated as an explicit, permanent hard constraint (§2, §7) reinforced throughout, not just stated once |
| A confirmation screen is mistaken for automated identity/e-card checking | Copy explicitly says staff completed the checks manually; the stored record is an attestation only, contains no automated result/evidence, and fails safely if it cannot be saved |
| Staff correction silently overwrites extracted evidence | Original/corrected values and a required reason are stored through re-authenticated, immutable audit events |
| Queue or payment data is stale or submitted twice | Screens show last-updated/processing states, disable duplicate actions, and provide idempotent retry behavior |
| Status is inaccessible or understood only through color | Every state has a text label and semantic status; production icons are consistent vectors and controls meet keyboard/touch requirements |
| Operational cost realism (judging criterion) | Architecture favours a lean extraction + rules-matching pipeline over a heavier, more expensive full clinical-AI stack, consistent with constraint #3 |
| Demo patient account (§4.6) mistaken for a production-ready patient identity system | Stated explicitly in the pitch as a small, fixed demo pool distinct from the tokenized single-visit upload link (§4.4) — not presented as a solved production patient-authentication design |
| A returning patient reuses stale or expired coverage | "Yes, same coverage" reuses only the source document; the system re-runs document validity and current eligibility rules and still requires staff confirmation before finalising |

## 11. Remaining Decisions

- Exact package/billing outcomes still require clinic-approved interpretation, but the demo rules fixture set is fixed at all seven supplied code families: `MRDEB`, `EVWPA`, `EVWME`, `BLPDE`, `BLPHS`, `NSTNBU`, and `MOL0199VME`. Rules use document type and selected package/check-up/requested items in addition to issuer code.
- A dedicated corporate-batch workflow remains deferred. For the demo, scalability is shown by seeding multiple booked patients on one screening date/employer and using the existing date-filtered Incoming board rather than building a separate batch UI.
- What specific operational cost estimate will be included to satisfy constraint #3 (e.g., API/inference cost per document processed)?
