# Design Document

## AI-Assisted Pre-Registration & Eligibility Verification for Parkway Shenton

- **Companion to:** [PRD.md](./PRD.md)
- **Supersedes:** prior `design.md` (CDMP trend monitoring — see PRD §0 for why)
- **Scope:** User flow, screen structure, and backend data model

---

## 1. User Flow

### 1.1 Scheduled appointment (pre-arrival path)

```text
[Patient books appointment / is registered for corporate screening]
     ↓
[Patient opens tokenized link or demo-account upload screen]
     ↓
[Check-first coverage step (§1.3)]
  Reuse prior document, or upload a new chit/voucher/referral letter
     ↓
[Document Extraction Layer]
  New upload: LLM parses the document into structured fields
  Reuse: load the prior document's staff-confirmed structured fields
  issuer/TPA code, policy/voucher no., patient ID, requested package, validity
     ↓
[Eligibility & Package Matching Engine]
  Rules-based lookup: structured fields → confirmed package + billing arrangement
     ↓
[All readiness gates passed before arrival?]
  Required documents present + valid + readiness PASS + every match clean
     ├── YES → READY BEFORE ARRIVAL
     └── NO  → NEEDS ASSISTED REVIEW
     ↓
[One visit ticket prepared; readiness state recorded]
  Registration + questionnaire data pre-filled, package/billing pre-matched
  Any failed readiness gate flagged for staff review
     ↓
[Patient Arrives]
     ↓
[Staff manually verifies identity/e-card in person using approved process]
     ↓
[System records staff confirmation only (§2.3)]
     ↓
[READY SERVICE]                         [ASSISTED REVIEW WORKLIST]
Staff confirms pre-processed record       Staff resolves flagged fields on
and calls the existing ticket             the same ticket; original waiting
                                            age continues throughout
     ↓                                          ↓
[Queue / Consultation or Screening]  ←──────────┘
```

### 1.2 Walk-in patient (at-counter path)

```text
[Patient arrives with document, or no document if self-pay]
     ↓
[Staff manually verifies identity/e-card in person using approved process]
     ↓
[System records staff confirmation only (§2.3)]
     ↓
[Create one visit ticket; state = PROCESSING]
     ↓
[Staff uploads/scans coverage document once]
     ↓
[Document Extraction Layer] → [Eligibility & Package Matching Engine]
     ↓
[All readiness gates pass and staff confirms?]
     ├── YES → same ticket becomes READY
     └── NO  → same ticket becomes NEEDS REVIEW
                    ↓
              [Staff resolves flags; same ticket becomes READY]
     ↓
[Queue / Consultation or Screening]
```

### Flow notes

- Every visit has exactly one patient-facing ticket. `processing`, `ready`, and `needs_review` are states on that ticket, not separate queues the patient must join.
- Readiness uses an all-gates rule: every required document must be present and valid, each document must receive `readiness_status = pass`, eligibility/package matches must be clean, and required staff confirmation must be complete.
- Walk-ins begin in `processing` and can become `ready` after first-pass processing. A failed gate moves the same ticket to `needs_review`; resolving it never issues a new number or resets `checked_in_at`.
- **Internal workstream routing solves the compounding-delay problem named in the brief** by letting ready cases proceed while staff resolve variable-time exceptions in parallel.
- A ticket cleared after review retains its original appointment/check-in ordering key. It does not displace someone already called, but it is not treated as a new arrival. Review-age alerts and flexible counter reallocation prevent unresolved cases from being starved.
- Identity/e-card checking always happens manually, in person, and outside system decision logic. The product only records the responsible staff member's confirmation after the manual process; it never scans, validates, or suggests a result.
- Staff confirmation is always required before a record is treated as final or `ready`.

### 1.3 Shared Check-First Upload Entry

This branch runs when a patient opens either a tokenized appointment link or the upload screen in a seeded demo account:

```text
[Patient reaches coverage screen]
     ↓
[Resolve patient within the current scope]
  Tokenized link: appointment-bound patient, resolved by normalized identifier
  Demo account: authenticated patient record; no public identity search
     ↓
[Prior coverage document on file?]
     ├── NO ──→ [Standard photo/file upload flow (§3.3)]
     │
     └── YES ─→ [Show prior issuer + document date]
                   "We have your Meridian coverage on file from [date].
                    Still the same?"
                       ├── [Yes, same coverage]
                       │      ↓
                       │   [Reuse document for this appointment]
                       │   [Re-run validity + eligibility rules]
                       │   [Route to staff review/confirmation]
                       │
                       └── [No, upload new document]
                              ↓
                           [Standard photo/file upload flow (§3.3)]
```

- This is a scoped lookup, not a public NRIC/email search. The token or authenticated account first establishes which patient may be checked.
- Matching requires one unambiguous exact match after normalisation. NRIC/FIN/passport is preferred and email is a scoped fallback only; the supplied questionnaire audit shows that emails frequently differ even when names and identifiers match. Conflicting, multiple, or name-only matches reveal no prior coverage and fall back to upload plus staff review.
- "Yes, same coverage" reuses the prior source document, not its old eligibility decision. Current validity and eligibility checks still run, and staff still confirms the result.
- Both choices are logged so staff can see whether the patient reused a prior document or supplied a replacement.

---

## 2. Staff Views

Staff views use a persistent desktop/tablet sidebar: **Queue**, **Review**, **Upload**, **Records**, **Billing**, **Audit**, and **Counters**. Every route keeps the selected date, filters, and scroll position when staff navigate back.

### 2.1 Staff Sign-In and Re-Authentication

```text
┌───────────────────────────────────────────────┐
│ Staff sign in                                  │
│ Email      [_______________________________]   │
│ Password   [________________________] [Show]   │
│                                               │
│                     [ Sign in ]               │
└───────────────────────────────────────────────┘

```

- Clerk supplies the sign-in/session flow. The wireframe may use Clerk's prebuilt component or a Clerk-backed custom form while preserving the same states and project styling.
- Read-only navigation uses the active staff session. Re-authentication is required immediately before confirming/correcting extracted data, revealing a full NRIC/FIN/passport identifier, overriding a match, confirming billing, or recording a manual identity/e-card check.
- Sensitive actions use Clerk reverification. The backend validates that the signed session reflects sufficiently recent verification before committing the action; a frontend-only modal is not sufficient authorization.
- Invalid credentials show an inline error without clearing the email. Repeated failure preserves the uncommitted action and offers Cancel; session expiry returns to sign-in and restores the intended route after success.

### 2.2 Queue Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Queue Overview     Date: [12 Aug 2026]    [Search] [Filters]             │
├───────────┬──────────────────────────────────────────────────────────────┤
│ Incoming  │ 09:00 Loh Wei Ming  READY  Q-014  Expected Counter 2 [Open]│
│ 8         │ 09:15 Tan Kai Xuan  REVIEW Q-015  Expected Counter 4 [Open]│
├───────────┼──────────────────────────────────────────────────────────────┤
│ Ongoing   │ Q-012 Mei Chen    Counter 2  Manual check recorded [Open]  │
│ 3         │ Q-013 Priya Nair  Counter 4  Document review       [Open]  │
├───────────┼──────────────────────────────────────────────────────────────┤
│ Finished  │ Q-010 Siti Rahman Counter 2  Completed 08:52        [Open]  │
│ 21        │ Q-011 John Lim    —          No-show 08:45          [Open]  │
└───────────┴──────────────────────────────────────────────────────────────┘
```

- **Incoming** retains scheduled date/time, readiness state, one expected queue number, and expected counter. Opening a row leads to §2.9.
- **Ongoing** begins after staff records the manual check-in confirmation (§2.3) and shows actual queue/counter plus current stage.
- **Finished** includes completed, cancelled, and no-show outcomes; rescheduled appointments remain Incoming on the new date with an audit link to the old slot.
- Empty groups say what happened (for example, “No incoming appointments for this date”). Loading uses fixed-height skeleton rows; load failure provides Retry. Color is never the only status cue.

### 2.3 Check-In and Manual Verification Confirmation

```text
┌─────────────────────────────────────────────────────────────┐
│ Check in: Loh Wei Ming — 12 Aug 2026, 09:00                 │
│ Planned: READY / Q-014 / Expected Counter 2                 │
│                                                             │
│ Record checks completed manually outside this system:       │
│ [ ] I manually verified the patient's identity in person.   │
│ [ ] I manually validated the e-card using the approved       │
│     in-person process.  [ Not applicable — reason required ]│
│                                                             │
│ [ Cancel ]              [ Record confirmation and check in ]│
└─────────────────────────────────────────────────────────────┘
```

- The controls are attestations only. Staff performs the real identity and e-card checks manually using the clinic's approved process; the product stores who confirmed them and when.
- The primary action stays disabled until identity is confirmed and e-card is either manually confirmed or marked not applicable with a reason. Re-authentication (§2.1) occurs before commit.
- A successful commit assigns the actual counter, transitions Incoming → Ongoing, and writes an audit entry. Failure leaves the patient Incoming and offers Retry; it never assumes the checks passed.

### 2.4 Assisted Review Worklist

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Assisted Review  [Today] [Reason: All] [Oldest first] [Search]         │
├──────┬───────────────┬───────────────┬──────────────────┬─────────────┤
│ Q-015│ Tan Kai Xuan  │ 09:15 booked │ Missing document │ [Open]      │
│ Q-018│ Amir Loh      │ 10:00 booked │ Expired voucher  │ [Open]      │
│ Q-019│ Priya Nair    │ Walk-in 09:22│ Ambiguous match  │ [Open]      │
└──────┴───────────────┴───────────────┴──────────────────┴─────────────┘
```

- This is an internal staff worklist, not another patient queue. Each row shows the visit's original ticket, appointment/check-in time, review reason, document status, total waiting age, service-target state, assigned counter, and next action. Opening a document issue leads to §2.6; missing documents lead to §2.5.
- Approaching/over-target rows are labelled and announced without relying on color. Staff may reassign a flexible counter; the system never silently changes clinical priority or auto-marks the ticket ready.
- An empty worklist says “No patients need review.” Loading, permission failure, and network failure are explicit and recoverable.

### 2.5 Staff Document Capture

```text
┌─────────────────────────────────────────────────────────────┐
│ Upload coverage document                                    │
│ Patient* [ Search patients ______________________________ ]  │
│                                                             │
│ [ Choose file ] [ Take photo ]                              │
│ Meridian_chit.pdf  PDF · 1.8 MB  [Preview] [Remove]         │
│ Supported: PDF, JPG, PNG · Maximum 10 MB                    │
│                                                             │
│ [ Cancel ]                          [ Process document ]     │
└─────────────────────────────────────────────────────────────┘
```

- Walk-ins must first have a minimal patient/visit record; upload never creates an unmatched clinical record silently.
- States: camera permission denied, unsupported type, oversized file, unreadable preview, upload progress, processing progress, timeout, extraction failure, success, and Replace/Retry. Buttons are disabled while a request is active.

### 2.6 Extraction Review and Exception Correction

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Review: Meridian_chit.pdf        Reason: VALIDITY NOT STATED         │
├──────────────────────────────┬───────────────────────────────────────┤
│ Source document · Page 1     │ Extracted fields                      │
│ [selected page/excerpt]      │ Issuer      Meridian (MRDEB)  PASS   │
│                              │ Policy no.  MRD707314         PASS   │
│                              │ Patient ID  S***946C          PASS   │
│                              │ Requests    3 medical tests   PASS   │
│ Evidence: “Chest X-Ray...”   │ Valid until Not stated       REVIEW │
│                              │                                       │
│                              │ [Edit selected field] [View rule]     │
├──────────────────────────────┴───────────────────────────────────────┤
│ [Back to worklist]             [Confirm corrected record]           │
└──────────────────────────────────────────────────────────────────────┘
```

- Selecting a field opens its source page and supporting excerpt. A bounding-box highlight appears only when reliable coordinates exist; the no-Azure baseline does not invent one. Edit mode shows the original value, corrected value, required correction reason, and Cancel/Save; Save requires re-authentication and creates an immutable audit entry.
- Checked forms show selected and unselected options separately. Only selected options feed `requested_items` or package matching.
- Expired documents, unknown issuers, missing patient identifiers, identifier conflicts, ambiguous selections, extraction failure, and no-match states each explain the cause and next action. Staff may correct extracted facts or choose a rules-table result, but cannot make an LLM-generated coverage decision final.
- PASS is a deterministic readiness state, not an LLM probability threshold. Confirmation is unavailable until the schema is valid, every required field for the detected document type has evidence, patient matching is resolved, validity is resolved, and exactly one rules result remains. Failed save preserves edits and offers Retry.

### 2.7 Records Search

```text
┌──────────────────────────────────────────────────────────────────┐
│ Patient Records                                                  │
│ Search [ Name, patient ID, masked NRIC/FIN/passport, email ____ ] │
│ Filters [Last visit] [Coverage] [Queue]                          │
├─────────────┬────────────────┬───────────────┬───────────────────┤
│ PS-REG-0417 │ Loh Wei Ming   │ 12 Aug 2026   │ Meridian  [Open] │
│ PS-REG-0398 │ Tan Kai Xuan   │ 03 Aug 2026   │ CHAS      [Open] │
└─────────────┴────────────────┴───────────────┴───────────────────┘
```

- Search is debounced, keyboard operable, and never displays a full NRIC/FIN/passport identifier in results. Empty, loading, permission-denied, and error states are explicit.

### 2.8 Patient Record

```text
┌──────────────────────────────────────────────────────────────────┐
│ Back to records                                                  │
│ PS-REG-0417 · Loh Wei Ming · NRIC S***946C             │
│ Current visit: 12 Aug 2026 · READY · Q-014 · Counter 2          │
│ Coverage: Meridian (MRDEB) · 3 requested tests · Confirmed      │
│                                                                  │
│ Record reuse                                                     │
│ TPA form PASS · Eligibility PASS · General questionnaire PASS   │
│ Occupational questionnaire PENDING · Pharmacy PASS · Billing —  │
│                                                                  │
│ [Open appointment] [Questionnaires] [Billing] [Audit history]   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.9 Appointment and Pre-Registration Detail

```text
┌──────────────────────────────────────────────────────────────────┐
│ 12 Aug 2026 · 09:15 · Tan Kai Xuan                  INCOMING    │
│ NEEDS REVIEW · Q-015 · Expected Counter 4 · Missing document    │
│                                                                  │
│ Pre-registration checklist                                      │
│ PASS  Patient details       PASS  Questionnaire                 │
│ FAIL  Coverage document     —     Eligibility match             │
│                                                                  │
│ [Send upload reminder] [Notify patient of issue ▾] [Open review]│
│ [Upload for patient]                                             │
│ [Reschedule] [Cancel appointment] [Record no-show]              │
│                                                                  │
│ Notifications sent                                               │
│ 09 Aug 08:02 · document_expired · SMS · Delivered · No action yet│
└──────────────────────────────────────────────────────────────────┘
```

- This replaces the duplicate pre-arrival list: §2.2 owns list-level status; this screen owns one appointment's prerequisites and actions.
- Reminder delivery shows sending/sent/failed states and retry. Reschedule retains an audit link to the old date; cancel/no-show require confirmation and move the row into Finished with its outcome.
- **Notify patient of issue** opens a picker limited to the curated, versioned category list (PRD §4.4: `document_unclear`, `document_incomplete`, `document_expired`, `document_type_mismatch`). Staff cannot type a free-text message into this channel — only select a category, so the patient never receives a raw internal review reason, source excerpt, or confidence value. Sending writes a `patient_notifications` row (§4) and an `audit_log` entry (`action_type = send_patient_notification`); the "Notifications sent" list on this screen reads that same table, so staff can see exactly what a patient was told before calling them to a counter.

### 2.10 Questionnaire and Consent Prefill

```text
┌──────────────────────────────────────────────────────────────────┐
│ General Health Questionnaire · Loh Wei Ming                     │
│ Prefilled from patient record (read-only)                        │
│ Name: Loh Wei Ming · DOB: 15 Mar 1988 · Contact: •••• 1234     │
│                                                                  │
│ New information                                                  │
│ Medical history* [___________________________________________]   │
│ Lifestyle*       [___________________________________________]   │
│                                                                  │
│ Consent and disclosure                                           │
│ [ ] Patient completed the required consent outside/within the    │
│     approved clinic process.                                    │
│ [Save draft]                              [Submit questionnaire] │
└──────────────────────────────────────────────────────────────────┘
```

- Prefilled identity/contact fields are visibly read-only, not disabled-looking. Only genuinely new answers are editable; long forms autosave drafts.
- Required-field errors appear beside fields with a summary linking to each error. Submission records the consent event but does not invent or bypass consent.

### 2.11 Pharmacy Allergy Confirmation

```text
┌─────────────────────────────────────────────────────────────┐
│ Dispensing: Loh Wei Ming · PS-REG-0417                      │
│ ALERT · Recorded allergy: Sulfa drugs · confirmed 12 Aug    │
│                                                             │
│ Pharmacist must verbally check with the patient manually.   │
│ [ ] I completed the verbal allergy check with the patient.  │
│                                                             │
│ [Cancel]                         [Record manual confirmation]│
└─────────────────────────────────────────────────────────────┘
```

- The system only displays the recorded allergy and logs the pharmacist's attestation. It does not perform or replace the clinical safety check.

### 2.12 Billing and TPA Confirmation

```text
┌──────────────────────────────────────────────────────────────────┐
│ Billing review · Loh Wei Ming · 12 Aug 2026                     │
│ Coverage source: Bluepeak BLPHS voucher · staff-confirmed        │
│ Selected package: WELL2 — Comprehensive Screen                   │
│ Covered amount: $XXX.XX        Patient payable: $XX.XX           │
│ TPA status: Ready for conceptual export                          │
│                                                                  │
│ [View source] [Correct billing] [Generate demo TPA payload]      │
│                                [Confirm billing]                 │
└──────────────────────────────────────────────────────────────────┘
```

- Billing confirmation requires re-authentication. Corrections require a reason and never overwrite the source extraction or prior audit history.
- TPA submission remains conceptual/demo-only: the screen previews or exports structured data and never claims a live insurer portal connection.

### 2.13 Audit Log

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Audit  [Date] [Actor] [Action] [Patient] [Export demo CSV]          │
├─────────┬──────────────┬───────────────────────┬─────────────────────┤
│ 09:02:11│ Staff A      │ manual_check_recorded │ PS-REG-0417 [View] │
│ 08:58:04│ Staff B      │ field_corrected       │ PS-REG-0398 [View] │
└─────────┴──────────────┴───────────────────────┴─────────────────────┘
```

- Detail shows before/after values, reason, actor, timestamp, source IP/session metadata where appropriate, and related record links. The log is read-only, paginated, sortable, and has empty/loading/error states.

### 2.14 Counter Allocation and Rebalancing

```text
┌──────────────────────────────────────────────────────────────────┐
│ Counter allocation · 12 Aug 2026                                │
│ READY work:     [1] [2]         REVIEW work:     [3] [4]         │
│ Expected load:  8 tickets       Expected load:   5 tickets       │
│                                                                  │
│ Recommendation · Review pressure rising                          │
│ Move Counter 2 to REVIEW for 30 min after Q-014                  │
│ Checks: qualified staff · minimum ready coverage · break clear   │
│ Expected: review P90 −6 min · Expires 09:35                      │
│ [Reject] [Modify] [Preview and approve]                          │
│                                                                  │
│ Q-015 Tan Kai Xuan · Expected 4 · Actual —  [Assign counter ▾]  │
│ [Preview changes]                         [Apply allocation]      │
└──────────────────────────────────────────────────────────────────┘
```

- Rebalancing may change expected/actual counters but cannot mark a ticket `ready` unless every readiness prerequisite passes. It never creates a replacement ticket or resets the original waiting age. Changes require confirmation, announce affected patients/staff, and are audited.
- Recommendations use current workload, near-term arrivals, historical stage handling times, eligible staff availability, planned breaks, and minimum coverage. Each shows its rationale, constraints, expected effect, and expiry.
- Only an authorised operations lead may accept or modify a recommendation. Rejection, modification, approval, reversal, and the observed outcome are audited. Recommendations never move staff automatically.
- A stability window and maximum reassignment frequency suppress short-lived oscillations; an approved move cannot begin until the staff member's current patient interaction safely ends.

### 2.15 Staff-Wide States and Accessibility

- Staff tables provide search, filters, sorting, pagination/virtualisation for large lists, skeleton loading, actionable errors, and meaningful empty states.
- Desktop is primary; tablet collapses the sidebar; narrow layouts turn tables into labelled cards without horizontal scrolling. A skip-to-main link bypasses the persistent navigation, visible focus follows visual order, and returning from detail restores list state.
- Production icons use one SVG icon set. Status always includes text plus icon/shape; wireframe words such as PASS, REVIEW, ALERT, and FAIL are the accessible labels, not color-dependent decoration.
- Interruptive alerts are reserved for conditions requiring immediate action. Every alert has an owner, severity, action, deduplication key, expiry, and resolution state; a repeated event updates the existing alert rather than stacking another modal/banner.
- Nonurgent conditions appear in their owning worklist or digest. Alert-governance views report volume, repeats, acknowledgement, action, dismissal, and expiry by alert type without ranking individual staff.

### 2.16 Operational Intelligence and Allocation Advisor (Product Extension)

```text
┌──────────────────────────────────────────────────────────────────┐
│ Operations · This week             [Booked/Walk-in] [Date range] │
├──────────────────┬──────────────────┬────────────────────────────┤
│ Ready pre-arrival│ First-pass ready │ Admin wait P50 / P90       │
│ 64%              │ 81%              │ 7 min / 19 min             │
├──────────────────┴──────────────────┴────────────────────────────┤
│ Top review reasons         Review clearance       Staff touches │
│ Missing document     18    Median 6 min            1.4 / visit   │
│ Expired voucher       9    P90 17 min                            │
│ Ambiguous match       5                                          │
├──────────────────────────────────────────────────────────────────┤
│ Booked P90: 15 min · Walk-in P90: 21 min · Difference: 6 min    │
├──────────────────────────────────────────────────────────────────┤
│ Forecast · next 30 min: REVIEW pressure likely                  │
│ Suggested: +1 qualified counter for 30 min · Expected P90 −6 min│
│ Constraints: minimum READY coverage PASS · breaks PASS           │
│ [View evidence] [Reject] [Modify] [Approve]                      │
└──────────────────────────────────────────────────────────────────┘
```

- The dashboard aggregates append-only `operational_events`; it does not query or display raw source documents, direct identifiers, or clinical information.
- Filters compare intake type, issuer/document category, reason, and time period. Small cohorts are suppressed where necessary to avoid exposing individuals.
- P50/P90 waiting time, first-pass readiness, review clearance, staff touches, corrections, and false-ready counts use explicit definitions and retain the selected period for reproducibility.
- Forecast workload is expressed in estimated staff-minutes, not ticket count alone, using scheduled arrivals, recent walk-in rate, and historical stage/reason handling times.
- The advisor considers only active staff/counters that satisfy role, skill, availability, break, minimum-coverage, stability-window, and reassignment-frequency constraints. It never treats all staff as interchangeable.
- Recommendations include their evidence, expected impact, expiry, and a no-change baseline. Approval, modification, rejection, reversal, and observed outcome are append-only events.
- The dashboard supports operational decisions but never ranks clinical urgency, scores individual productivity, automatically changes rules, or reallocates resources without authorised approval.
- P0 may use seeded events and deterministic recommendation rules. Loading, no-data, suppressed-data, stale, expired-recommendation, conflict, approval-failure, and recoverable error states are explicit.

### 2.17 Downtime and Recovery

```text
┌──────────────────────────────────────────────────────────────────┐
│ DEGRADED MODE · Last confirmed connection 09:12 · [Retry]       │
│ Automated eligibility and readiness updates are unavailable.    │
├──────────────────────────────────────────────────────────────────┤
│ Minimum-safe intake                                              │
│ Downtime ticket D-0042 · Created 09:16 · Counter 2              │
│ Manual identity check: [Record local attestation]                │
│ E-card check: [Confirmed manually] [Not applicable + reason]     │
│ Coverage document: [Hold securely for recovery workflow]         │
│ [Print/show ticket] [Save local encrypted downtime record]       │
├──────────────────────────────────────────────────────────────────┤
│ Pending recovery: 4 · Conflicts: 1 · [Open reconciliation]      │
└──────────────────────────────────────────────────────────────────┘
```

- Degraded mode is entered only for a verified dependency/service failure, not a single slow request. The banner identifies unavailable capabilities, last confirmed connection, local record count, and recovery owner.
- The fallback follows the clinic-approved manual process. It never claims extraction, eligibility, coverage, billing, or readiness passed while those services are unavailable.
- A downtime record contains the minimum safe data, local device/counter ID, staff actor, manual-check attestation, timestamps, and a locally unique `D-*` reference. Raw coverage files are not copied into unapproved browser storage.
- `D-*` is a recovery reference, not a second patient queue number. The patient retains it throughout the outage; recovery maps it to one canonical `Q-*` visit without restarting waiting age or requiring the patient to requeue.
- When service returns, staff review exact match, possible match, conflict, and failed-upload groups. Nothing auto-merges on name alone. Each record reaches `reconciled`, `conflict_review`, or `failed_retryable` with actor/time/audit evidence.
- Replayed writes use idempotency keys. Recovery reports prove counts across locally created, accepted, conflicted, failed, and reconciled records before degraded mode is closed.
- The simulator exercises full outage, partial dependency failure, stale reads, recovery, duplicate replay, and conflict resolution.

---

## 3. Patient Views

Patient screens are mobile-first and expose only the signed-in/token-scoped patient's data. The demo account uses four labelled destinations: **Home**, **Queue**, **Payment**, and **Records**; coverage upload is the primary action from Home. Tokenized links open only the scoped coverage flow and do not expose account navigation.

### 3.1 Demo Account Sign-In and Home

```text
┌─────────────────────────────────────────┐
│ Patient demo sign in                    │
│ Email    [___________________________]   │
│ Password [____________________] [Show]   │
│                         [ Sign in ]      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Hi Loh Wei Ming                         │
│ Upcoming: 12 Aug 2026 · 09:00           │
│ Coverage: Action required [Open upload]  │
│ Queue: Available after check-in          │
│ Payment: Not ready                       │
│ Recent visit: 03 Feb 2026 [View]         │
│                                         │
│ [Home] [Queue] [Payment] [Records]       │
└─────────────────────────────────────────┘
```

- Invalid sign-in, expired session, loading, no-upcoming-appointment, and service-error states have clear recovery. This remains a small seeded demo pool, not production patient identity design.

### 3.2 Coverage Check-First Entry

```text
┌─────────────────────────────────────────┐
│ Confirm your coverage                   │
│ Appointment: 12 Aug 2026 · 09:00        │
│ We have Meridian coverage on file       │
│ from 12 Feb 2026. Is it still the same? │
│                                         │
│ [Yes, use it] [No, upload a new one]    │
└─────────────────────────────────────────┘
```

- The initial state says “Checking for previous coverage…” without exposing data. No prior match proceeds to §3.3; an ambiguous match reveals nothing and also proceeds to upload while flagging staff review.
- Expired/used/invalid token states explain that the link no longer works and direct the patient to contact the clinic. Reuse success confirms receipt but does not claim eligibility approval.
- **Reopening a link with an unresolved issue notification** shows a banner above the normal check-first content instead of the usual coverage question, using only the curated category's patient-safe text — e.g. "The photo of your document wasn't clear enough for us to read. Please retake and reupload." — sourced from `patient_notifications` (§4), never the internal `readiness_reasons` value. The banner routes straight to §3.3 upload; there is no "still the same?" reuse question in this state, since the prior upload is the thing that needs replacing. Categories that map to a staff-side issue (e.g. an identifier conflict) never reach this screen as a banner — those stay in the Assisted Review worklist (§2.4) and the patient instead sees the ordinary "under review" outcome with no action prompt.

### 3.3 Coverage Upload and Outcomes

```text
┌─────────────────────────────────────────┐
│ Upload coverage document                │
│ [Take photo] [Choose file]              │
│ Meridian_chit.pdf · 1.8 MB              │
│ [Preview] [Remove]                      │
│ PDF, JPG or PNG · Maximum 10 MB         │
│                                         │
│                           [Submit]      │
└─────────────────────────────────────────┘
```

| State | Patient-facing behavior |
| --- | --- |
| Uploading/processing | Progress indicator, disabled duplicate submit, safe Back warning |
| Unsupported/too large/unreadable | Inline cause plus Replace file |
| Network/processing failure | Preserve selection where safe and offer Retry |
| Success | “Document received for staff review”; no confidence score or queue promise |
| Token expires mid-flow | Preserve no sensitive data, explain expiry, provide clinic contact path |

### 3.4 Queue Status

```text
┌─────────────────────────────────────────┐
│ Queue status                  [Refresh] │
│ Queue Q-014 · Ready                     │
│ Counter 2 · 2 patients ahead            │
│ Status: Waiting                         │
│ Updated: 09:18                          │
└─────────────────────────────────────────┘
```

| State | Message/content |
| --- | --- |
| Initial loading | Show a fixed-layout skeletal loading screen matching the final queue card, including placeholder lines for queue, counter, position, status, and updated time; avoid layout shift |
| Refreshing | Keep the current queue information visible, change the button label to “Refreshing…”, disable repeat taps, and update the timestamp when complete |
| Before check-in | “Queue status will appear after staff check-in.” |
| Processing | Keep the same `Q-*` ticket and say “We are checking your registration details.” |
| Additional review needed | Keep the same `Q-*` ticket and original waiting age; say “A staff member is reviewing your registration.” Do not expose internal confidence details or ask the patient to take another number. |
| Ready | Keep the same `Q-*` ticket and show counter/position when assigned. |
| Called | “Please proceed to Counter 2 now.” with text and accessible alert |
| Counter changed | New counter plus “Your counter changed” announcement |
| Delayed | Plain-language delay message; do not promise an exact wait time |
| Finished | Completion state with link to payment when ready |
| Load failure | Last-updated time plus Retry; never show stale data as current silently |

- This reads the same `queue_entries` row as staff views. Patients never see review reasons, source documents, or other patients.
- **Refresh** is a labelled top-right button with a minimum 44×44 px target. Refresh failure keeps the last known data visible, marks it as not current, and offers Retry. Skeleton shimmer is disabled when reduced motion is requested.

### 3.5 Payment and Receipt (Mocked)

```text
┌─────────────────────────────────────────┐
│ Payment summary                         │
│ WELL2 — Comprehensive Screen            │
│ Covered by Bluepeak: $XXX.XX            │
│ You pay: $XX.XX                         │
│                                         │
│ [Pay now — demo]                        │
└─────────────────────────────────────────┘
```

| State | Behavior |
| --- | --- |
| Not ready | Explain that staff is finalising billing; payment disabled |
| Processing | Disable repeat submission and show progress |
| Success | Receipt reference, timestamp, amount, and Download/View receipt |
| Failure | No receipt created; explain failure and offer Retry |
| Already paid | Show receipt, never offer Pay again |

- The judge-facing/demo chrome labels this as mocked. Patient-facing confirmation remains realistic but never triggers a live gateway.

### 3.6 Medical Records and Visit Detail (Read-Only)

```text
┌─────────────────────────────────────────┐
│ Your visit history                      │
│ 12 Aug 2026 · Health Screening [Open]   │
│ 03 Feb 2026 · GP Consultation   [Open]  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Visit: 12 Aug 2026                      │
│ Package: WELL2 — Comprehensive Screen   │
│ Coverage: Bluepeak BLPHS                 │
│ Questionnaire responses [Expand]        │
│ General health · Submitted 08 Aug       │
│ Occupational health · Not required      │
└─────────────────────────────────────────┘
```

- History has loading, error/Retry, and “No past visits yet” states. Long histories paginate. Detail includes coverage/package history and past questionnaire responses promised by the PRD, but remains read-only.

### 3.7 Patient-Wide Accessibility and Responsive Behavior

- Minimum 44×44 px controls, visible focus, labelled inputs with appropriate email/number/tel keyboards, inline errors, screen-reader announcements for queue/counter changes, and no status communicated by color alone.
- Layout supports 375 px width through tablet without horizontal scroll, respects browser zoom/dynamic text, safe areas, reduced motion, and light/dark contrast. Navigation labels remain visible; structural emoji are replaced with consistent SVG icons in implementation.

---

## 4. Backend Data Model (Supabase / Postgres)

### 4.1 Demo Data Contract

The supplied archive is treated as the complete demo-data input, not as a production schema:

| Fixture | Audited shape | Design consequence |
| --- | --- | --- |
| Registration CSV | 300 rows; 12 columns; 300 unique nonblank identifiers | Canonical patient seed and contact record |
| General-health CSV | 30 rows; 41 columns | Reduced response projection; conditional blanks remain `null` |
| Occupational-health CSV | 30 rows; 27 columns | Reduced response projection; disclosure consent remains a distinct field |
| Questionnaire field reference | Full general/occupational live-field catalogue | Schema/UI reference only; fields or signatures absent from CSV data are not invented |
| Medical chit DOCX | Nine synthetic one-page documents across seven issuer/code families | Preprocess into nine individual PDF/image fixtures with fixture IDs and expected outputs |

Reconciliation results and rules:

- Across both questionnaire CSVs there are 57 unique people. Fifty-one join to registration by normalized NRIC/FIN/passport; six stay in `data_import_exceptions` and do not create patients silently.
- Three matched people have both questionnaire types; each response remains a separate record.
- For matched rows, names agree but questionnaire emails frequently differ. Registration remains canonical; source questionnaire contact values remain in the response payload with provenance and never overwrite `patients.email` automatically.
- Registration DOB is `DD/MM/YY`; questionnaire DOB is `DD/MM/YYYY`. Matching four-digit DOB resolves the century where available. For remaining demo rows, `00`–`26` maps to 2000–2026 and `27`–`99` maps to 1927–1999; resulting ages below 16 or above 100 become import warnings. Production migration must not rely on this demo pivot.
- Six medical fixtures contain an explicit patient identifier and match a registration row. Three have no explicit identifier and must demonstrate `patient_match_status = needs_review`; name-only matching is prohibited.
- The combined DOCX is a source bundle, not an accepted upload type. Fixture preparation splits/renders its nine pages; patient/staff uploads remain PDF, JPG, or PNG.

```text
patients
├── id (uuid, PK)
├── patient_id_display        -- e.g. "PS-REG-0417"
├── source_dataset
├── source_row_number
├── full_name
├── identity_type                -- NRIC_FIN / passport / other
├── identity_masked
├── identity_encrypted           -- reveal is a re-authenticated, logged action
├── identity_hash                -- normalized exact-match lookup
├── sex
├── nationality
├── date_of_birth
├── address
├── postal_code
├── contact_home
├── contact_office
├── contact_mobile
├── email
├── drug_allergy
└── created_at
    -- fields mirror patient_registration_synthetic.csv exactly, so the
    -- synthetic dataset can be loaded directly with no field-mapping guesswork

data_import_exceptions
├── id (uuid, PK)
├── source_file / source_row_number
├── source_record_type          -- registration / general_health / occupational_health
├── normalized_identifier_hash (nullable)
├── reason_code                 -- unmatched_patient / duplicate_identifier /
│                                  invalid_date / conflicting_identity
├── details (jsonb)             -- masked/non-sensitive diagnostic fields only
├── resolution_status           -- unresolved / linked / intentionally_ignored
├── resolved_patient_id (FK → patients, nullable)
├── created_at
└── resolved_at (nullable)
    -- the six unmatched questionnaire people are visible import exceptions;
    -- questionnaire rows never create patient records implicitly

staff_accounts
├── id (uuid, PK)
├── clerk_user_id (text, UNIQUE)
├── full_name
├── email
├── role                         -- registration / pharmacist / billing /
│                                  operations_admin / auditor
├── active (boolean)
└── created_at
    -- Clerk stores credentials; this table supplies app role/audit identity

upload_links
├── id (uuid, PK)
├── token_hash               -- hash of opaque, single-use, unguessable token
├── patient_id (FK → patients, nullable until identity is known at booking)
├── appointment_reference       -- links to the specific scheduled visit
├── expires_at                     -- appointment date, or first use, whichever first
├── used_at (nullable)
└── created_at
    -- backs the patient-facing upload link (design §3.2) — deliberately NOT an
    -- account/session table; a token scopes access to exactly one appointment's
    -- upload action and nothing else, keeping the internet-facing surface minimal

patient_accounts
├── id (uuid, PK)
├── clerk_user_id (text, UNIQUE)
├── patient_id (FK → patients)
├── email / phone              -- cached display/contact value; Clerk owns login identity
└── created_at
    -- DELIBERATELY SEPARATE from upload_links above. This table backs the small,
    -- fixed demo pool of patient logins (PRD §4.6) — e.g. a handful of seeded
    -- accounts given to judges — NOT a production-scale, self-service patient
    -- identity system. Keeping this as its own table (rather than quietly
    -- extending upload_links into a full account system) is what keeps the
    -- "this is a demo-scoped account, not a solved production auth design"
    -- distinction honest and visible in the schema itself, not just in prose.

payments
├── id (uuid, PK)
├── patient_id (FK → patients)
├── coverage_document_id (FK → coverage_documents)
├── billing_review_id (FK → billing_reviews)
├── amount_covered
├── amount_patient_payable
├── status                  -- not_ready / mock_processing / mocked_paid / mock_failed
├── mock_failure_reason (nullable)
├── mock_receipt_reference (nullable)
└── paid_at (nullable)
    -- status value is deliberately named "mocked_paid" rather than "paid", so
    -- the mocked nature of this flow is visible in the data itself, not just
    -- in documentation that could go stale or get skipped over in a demo

coverage_documents
├── id (uuid, PK)
├── patient_id (FK → patients, nullable until matched/created)
├── source_fixture_id (nullable)        -- e.g. fixture page from the supplied DOCX bundle
├── file_reference                      -- private stored upload (image/PDF)
├── document_type                       -- referral_letter / voucher / underwriting_request /
│                                          authorisation_form / appointment_notice / other
├── issued_on (nullable)
├── issuer_name / issuer_code
├── employer_policyholder_or_agency (nullable)
├── extracted_patient_name (nullable)
├── extracted_id_type (nullable)        -- NRIC_FIN / passport / other
├── extracted_id_encrypted (nullable)
├── extracted_id_hash (nullable)
├── extracted_id_masked (nullable)
├── patient_match_status                -- exact_identifier / needs_review / conflict
├── reference_numbers (jsonb)           -- policy, voucher, proposal, contract, certificate, etc.
├── package_or_checkup_code (nullable)  -- e.g. WELL2 / PEE226
├── selected_options (jsonb)            -- checked and unchecked options kept distinctly
├── requested_items (jsonb)             -- selected medical tests/services only
├── administrative_requirements (jsonb) -- non-medical requirements retained separately
├── appointment_at (nullable)
├── fulfil_by (nullable)
├── venue (nullable)
├── validity_start / validity_end (nullable)
├── validity_basis (nullable)            -- explicit / relative_to_issue / fulfil_by / not_stated
├── special_instructions (jsonb)
├── billing_instructions (jsonb)
├── field_evidence (jsonb)               -- field → page + source excerpt + optional bbox
├── extraction_confidence (jsonb)        -- advisory per-field signal; never routes alone
├── readiness_status                     -- pass / needs_review
├── readiness_reasons (jsonb)            -- missing_identifier / missing_required_field /
│                                          ambiguous_selection / invalid_or_unknown_validity / etc.
├── extraction_model / prompt_version / schema_version
├── processing_status                    -- uploading / processing / ready / failed
├── processing_error_code (nullable)     -- unsupported / too_large / unreadable / timeout / extraction_failed
├── status                               -- pending_review / confirmed / rejected
├── confirmed_by_staff_id (FK, nullable)
└── confirmed_at

patient_notifications
├── id (uuid, PK)
├── patient_id (FK → patients)
├── queue_entry_id (FK → queue_entries, nullable)
├── coverage_document_id (FK → coverage_documents, nullable)
├── upload_link_id (FK → upload_links, nullable)
├── category                     -- one of the fixed, versioned patient-safe categories:
│                                    "document_unclear" / "document_incomplete" /
│                                    "document_expired" / "document_type_mismatch"
├── category_map_version          -- points at the approved configuration_releases row
│                                     for configuration_type = "patient_notification_category_map"
├── channel                      -- "sms" / "email"
├── sent_by_staff_id (FK → staff_accounts, nullable)  -- null when system-triggered
├── delivery_status              -- queued / sent / delivered / failed
├── delivery_failure_reason (nullable)
├── patient_action               -- none / reopened_link / resubmitted / expired_unactioned
├── resulting_coverage_document_id (FK → coverage_documents, nullable)
├── sent_at
└── actioned_at (nullable)
    -- backs the "Notify patient of issue" action (design §2.9) and the reopened-link
    -- banner (design §3.2). `category` is deliberately a closed enum, never free text,
    -- so a patient can never receive a raw internal readiness_reason, source excerpt,
    -- or confidence value (PRD §4.4/§7). Every row also produces an audit_log entry.

coverage_reuse_decisions
├── id (uuid, PK)
├── patient_id (FK → patients)
├── appointment_reference
├── prior_coverage_document_id (FK → coverage_documents)
├── entry_source                    -- "tokenized_link" / "demo_account"
├── match_method                    -- "identifier" / "email"; stores method, not raw value
├── decision                        -- "reuse" / "replace"
├── replacement_document_id (FK → coverage_documents, nullable)
└── created_at
    -- records the check-first choice without modifying the prior document;
    -- "reuse" still creates a new eligibility match for this appointment

eligibility_rules
├── id (uuid, PK)
├── issuer_code                -- one of seven supplied demo code families
├── issuer_name
├── document_type
├── package_or_checkup_code (nullable)
├── required_selected_items (jsonb)
├── disallowed_or_conflicting_items (jsonb)
├── package_name                  -- clinic-approved label; e.g. fixture-selected WELL2
├── included_items (jsonb)
├── billing_arrangement
├── rule_version
├── effective_from
├── effective_to (nullable)
├── priority
└── active (boolean)
    -- this table is the rules-based matching engine referenced in PRD §6.2 —
    -- issuer_code alone is not unique enough; document type and selected
    -- package/check-up/items participate in a deterministic lookup

eligibility_matches
├── id (uuid, PK)
├── coverage_document_id (FK → coverage_documents)
├── appointment_reference                -- eligibility is re-evaluated per visit
├── matched_rule_id (FK → eligibility_rules, nullable)   -- null if no clean match
├── match_status                    -- clean / ambiguous / no_match
├── match_basis (jsonb)             -- rule version + exact inputs used
├── review_reasons (jsonb)
├── status                             -- pending_review / confirmed / overridden
├── confirmed_by_staff_id (FK, nullable)
└── confirmed_at

queue_entries
├── id (uuid, PK)
├── patient_id (FK → patients)
├── appointment_reference (nullable)     -- null for walk-ins
├── scheduled_at (timestamptz, nullable)  -- booked appointment date/time; null for walk-ins
├── intake_type                          -- "booked" / "walk_in"
├── prereg_completed_at (nullable)
├── all_required_documents_present (boolean)
├── all_documents_valid (boolean)
├── extraction_status                    -- "pass" / "needs_review"
├── match_status                         -- "clean" / "ambiguous" / "no_match"
├── readiness_state                      -- "processing" / "ready" / "needs_review"
├── readiness_reason                     -- "all_prerequisites_passed" /
│                                            "prereg_incomplete" / "missing_document" /
│                                            "expired_document" / "extraction_needs_review" /
│                                            "ambiguous_match"
├── visit_status                         -- "incoming" / "ongoing" / "finished"
├── visit_outcome (nullable)              -- "completed" / "cancelled" / "no_show"
├── rescheduled_from_queue_entry_id (FK, nullable)
├── expected_queue_number (nullable)     -- e.g. "Q-014" for Incoming
├── expected_counter_number (nullable)   -- planning assignment shown before arrival
├── queue_number (nullable)              -- active/final number once checked in
├── counter_number (nullable)            -- actual assigned counter
├── processing_stage (nullable)          -- e.g. "manual_check_confirmation" / "document_review"
├── assigned_at
├── checked_in_at (nullable)             -- transition: Incoming → Ongoing
├── ready_at (nullable)
└── completed_at (nullable)              -- transition: Ongoing → Finished
    -- database/service constraint: one row/ticket per visit. readiness_state="ready"
    -- only when every document readiness gate is PASS, match_status="clean", and
    -- required staff confirmation exists. Walk-ins start "processing" and retain
    -- this row plus checked_in_at through review and eventual readiness.

manual_check_confirmations
├── id (uuid, PK)
├── queue_entry_id (FK → queue_entries)
├── identity_check_status              -- "manually_confirmed"
├── ecard_check_status                 -- "manually_confirmed" / "not_applicable"
├── ecard_not_applicable_reason (nullable)
├── confirmed_by_staff_id (FK → staff_accounts)
├── attestation_version
└── confirmed_at
    -- stores staff attestation only; no identity/e-card image, automated result,
    -- or system-generated verification decision is captured

counter_allocations
├── id (uuid, PK)
├── service_date
├── counter_number
├── workstream                         -- "ready" / "review"
├── assigned_staff_id (FK → staff_accounts, nullable)
├── effective_from / effective_to (nullable)
├── active (boolean)
├── updated_by_staff_id (FK → staff_accounts)
└── updated_at

staff_availability
├── id (uuid, PK)
├── staff_id (FK → staff_accounts)
├── shift_start / shift_end
├── eligible_workstreams (jsonb)       -- derived from approved role/training
├── planned_breaks (jsonb)
├── availability_status               -- available / serving / break / unavailable
├── current_workstream (nullable)
└── updated_at
    -- operational availability only; not an individual productivity score

allocation_recommendations
├── id (uuid, PK)
├── generated_at / expires_at
├── pressured_workstream
├── demand_snapshot (jsonb)            -- counts, waiting age, estimated staff-minutes
├── recommended_staff_id (FK, nullable)
├── recommended_counter_number (nullable)
├── recommended_from / recommended_to
├── constraints_checked (jsonb)        -- skills, coverage, breaks, stability, frequency
├── rationale / expected_effect (jsonb)
├── status                             -- pending / accepted / modified / rejected /
│                                        expired / reversed
├── decided_by_staff_id (FK, nullable)
├── decision_reason (nullable)
└── decided_at (nullable)
    -- advisory only; a recommendation never changes an allocation by itself

operational_events
├── id (uuid, PK)
├── queue_entry_id (FK → queue_entries)
├── event_type                       -- ticket_created / readiness_changed /
│                                       review_started / review_resolved /
│                                       counter_assigned / allocation_recommended /
│                                       allocation_decided / allocation_reversed /
│                                       visit_completed
├── from_state (nullable)
├── to_state (nullable)
├── reason_code (nullable)
├── staff_touch (boolean)
├── occurred_at
└── metadata (jsonb)                 -- masked operational attributes only
    -- append-only event stream for PRD §4.7 metrics. It contains no raw document
    -- content or direct identifier and never drives clinical priority.

operational_alerts
├── id (uuid, PK)
├── alert_type / severity
├── owner_role
├── related_queue_entry_id (FK, nullable)
├── deduplication_key
├── required_action
├── status                         -- active / acknowledged / resolved /
│                                    dismissed / expired
├── occurrence_count
├── first_seen_at / last_seen_at / expires_at
├── acknowledged_by / acknowledged_at (nullable)
└── resolved_by / resolved_at (nullable)
    -- repeated conditions update occurrence_count/last_seen_at rather than
    -- creating duplicate interruptions; aggregate action metrics support review

downtime_intake_records
├── id (uuid, PK)                  -- generated locally with collision-safe UUID
├── downtime_reference            -- D-* recovery/display reference
├── encrypted_minimum_safe_payload
├── identifier_hash / identifier_masked (nullable)
├── local_device_id / counter_reference
├── created_by_staff_reference
├── manual_check_snapshot (jsonb)
├── original_waiting_since
├── idempotency_key
├── recovery_status               -- pending / reconciled / conflict_review /
│                                    failed_retryable
├── canonical_queue_entry_id (FK, nullable)
├── created_at / recovery_attempted_at (nullable)
└── reconciled_at (nullable)
    -- temporary recovery record, never a second patient journey. Plaintext/raw
    -- source documents are excluded from unapproved browser/local storage.

configuration_releases
├── id (uuid, PK)
├── configuration_type            -- eligibility_rule / readiness_gate / prompt /
│                                    schema / alert_policy / allocation_constraint /
│                                    integration_mapping
├── version / payload_hash
├── status                        -- draft / shadow / approved / active / rolled_back
├── effective_from / effective_to (nullable)
├── validation_summary (jsonb)
├── created_by_staff_id / approved_by_staff_id (nullable)
├── activated_at / rolled_back_at (nullable)
└── supersedes_release_id (FK, nullable)
    -- maker/checker constraint: creator cannot approve safety- or billing-relevant
    -- configuration; each decision stores the governing release/version

questionnaire_responses
├── id (uuid, PK)
├── patient_id (FK → patients)
├── appointment_reference
├── questionnaire_type          -- "general_health" / "occupational_health"
├── source_file / source_row_number (nullable)
├── source_schema_version
├── source_identity_snapshot (jsonb) -- source name, ID type, identifier hash/mask,
│                                        DOB, and email for provenance; no plaintext ID
├── responses (jsonb)              -- non-identity fields actually supplied by the CSV/UI;
│                                      conditional blanks are null, not false
├── shared_fields_reused (boolean)   -- true if patient/contact fields were pulled
│                                         from `patients` rather than re-entered
├── declaration_acknowledged (boolean)
├── disclosure_consent (nullable)     -- occupational employer/insurer consent kept separate
├── source_date_signed (nullable)
├── consent_status                    -- pending / recorded; never inferred from missing fields
├── consent_recorded_by_staff_id (FK, nullable)
├── draft_saved_at (nullable)
└── submitted_at

billing_reviews
├── id (uuid, PK)
├── patient_id (FK → patients)
├── appointment_reference
├── coverage_document_id (FK → coverage_documents)
├── eligibility_match_id (FK → eligibility_matches)
├── amount_covered
├── amount_patient_payable
├── tpa_payload (jsonb, nullable)       -- demo preview/export only; no live submission claim
├── status                              -- pending / confirmed / corrected
├── correction_reason (nullable)
├── confirmed_by_staff_id (FK, nullable)
└── confirmed_at (nullable)

touchpoint_reuse_log
├── id (uuid, PK)
├── patient_id (FK → patients)
├── touchpoint                  -- "tpa_form" / "eligibility_check" / "general_health_questionnaire" /
│                                     "occupational_health_questionnaire" / "pharmacy_allergy_check" /
│                                     "billing_tpa_portal"
├── reused_from_record (boolean)   -- true if this touchpoint drew from the shared patient record
│                                        rather than requiring fresh manual entry
├── timestamp
└── notes
    -- this table is what makes §4.3's "all five touchpoints" claim provable across the FULL
    -- visit, not just the two questionnaire types tracked by shared_fields_reused above —
    -- it's the source of truth for the Record Reuse checklist shown in the Patient Record
    -- View (design §2.8) and for the duplicate-entry success metric in PRD §9

audit_log
├── id (uuid, PK)
├── staff_id (FK, nullable)
├── patient_id (FK, nullable)
├── action_type            -- "extract_document" / "confirm_match" / "correct_field" /
│                                "reveal_identifier" / "override_match" / "assign_queue" /
│                                "confirm_allergy_check" / "check_prior_coverage" /
│                                "reuse_coverage" / "request_coverage_replacement" /
│                                "assign_expected_counter" / "record_manual_checks" /
│                                "check_in" / "reassign_counter" / "confirm_billing" /
│                                "reschedule_visit" / "cancel_visit" / "record_no_show" /
│                                "complete_visit" / "send_patient_notification"
├── target_table
├── target_id
├── details (jsonb)
└── timestamp
```

### Design notes

- `patients` mirrors the 12 registration CSV fields plus source provenance. DOB is normalized to a database date; the original source row remains traceable so two-digit-year decisions can be audited.
- `data_import_exceptions` makes the six unmatched questionnaire people and any future conflicts visible without treating a questionnaire as authority to create or overwrite a patient.
- `coverage_documents` and `eligibility_rules`/`eligibility_matches` are kept as separate concerns on purpose: the first is "what did the model read off this document," the second is "what does that map to under our rules." This split makes the hallucination-mitigation claim in PRD §6.2/§8 concrete. Model output never directly becomes a billing decision, and advisory confidence never grants `ready` status.
- `field_evidence` uses page plus excerpt as the required no-Azure evidence contract. A bounding box is nullable and shown only if an added OCR adapter produces reliable coordinates.
- `selected_options` prevents checkbox forms from collapsing selected and unselected services together. Administrative requirements remain separate from medical `requested_items`.
- `queue_entries` makes single-ticket readiness routing (PRD §4.2) queryable at the visit level. Readiness does not live on a coverage document because staff confirmation and visit state are also required inputs. The same row persists through processing, review, readiness, and completion and drives the Queue Overview (§2.2), Appointment Detail (§2.9), and patient Queue Status (§3.4).
- `queue_entries.scheduled_at` preserves the appointment date across all three lifecycle views. `expected_queue_number` and `expected_counter_number` are generated for Incoming booked patients after routing; `queue_number` and `counter_number` hold the actual assignments after check-in. `checked_in_at` and `completed_at` drive the Incoming → Ongoing → Finished transitions without moving data between tables.
- `manual_check_confirmations` is deliberately an attestation record, not a verification engine. It proves which staff member recorded completion of the clinic's manual identity/e-card process and cannot store or infer an automated verification result.
- `visit_outcome`, `rescheduled_from_queue_entry_id`, and `counter_allocations` support the cancelled, no-show, rescheduled, and counter-rebalancing states shown in staff views without weakening readiness gates or replacing a patient's ticket.
- `operational_events` provides the privacy-safe stage transitions and reason codes needed for the Operational Intelligence dashboard. It is append-only analytics evidence, not a second workflow state store.
- `staff_availability` and `allocation_recommendations` keep resource advice explicit and auditable. Eligibility and availability are constraints, while the recommendation status proves that a human—not the advisor—made the allocation decision.
- `operational_alerts` makes alert deduplication, ownership, expiry, and action-rate review queryable instead of relying on transient UI banners.
- `downtime_intake_records` is a bounded recovery store, not a parallel queue database. Its original waiting time survives reconciliation into one canonical `queue_entries` row.
- `configuration_releases` applies shadow validation, maker/checker approval, effective dates, governing-version attribution, and rollback consistently across rules, prompts, mappings, alerts, and allocation constraints.
- `coverage_reuse_decisions` records the check-first branch independently of the source document. Reuse points to the prior document but creates a fresh appointment-scoped `eligibility_matches` row, so an old coverage decision is never silently carried forward.
- `patient_notifications` keeps the patient-facing issue message on a closed, versioned category enum rather than free text, so the same `configuration_releases` maker/checker/rollback pattern used for eligibility rules and readiness gates also governs what wording a patient can ever receive (`configuration_type = "patient_notification_category_map"`). Every row is both the delivery record (§2.9, §3.2) and an audit trail entry — staff can see what was sent, when, and whether the patient acted, without that record ever containing the internal `readiness_reasons` value it was derived from.
- `touchpoint_reuse_log` is the mechanism that makes "we eliminated duplicate entry across all five touchpoints" a provable, queryable fact in the demo — not just the questionnaire-only claim an earlier draft of this system could support.
- `upload_links` and `patient_accounts` are two intentionally different mechanisms for two intentionally different needs: a one-time, unauthenticated, appointment-scoped token for the common case (submit a document ahead of a visit), versus a real but small, fixed-pool account for anything requiring returning access (queue status, payment, records history). Collapsing these into one "patient login" table would overstate what's actually been designed — keeping them separate keeps that honest.
- `billing_reviews` separates staff-confirmed billing from patient payment. `payments.status` uses explicit `mock_*` values so success/failure/receipt states remain visibly demo-only in data, not only in prose that a reader might skip.
- `questionnaire_responses.source_identity_snapshot` preserves what each source file said without overwriting the canonical registration record. Consent/declaration fields remain explicit because the reduced CSVs do not contain every field or signature from the full questionnaire reference.

---

## 5. Auth & Review Flow Summary

```text
Staff logs in through Clerk (individual account)
   ↓
Read-only actions (view queue, view records, view audit log) → no re-auth required
   ↓
Any confirmation or correction action (record a manually completed identity/e-card
check, confirm extracted data/billing, override a match, reveal a full identifier, edit a field)
→ Clerk reverification before the change commits
   ↓ (on success)
Action commits → audit_log entry created automatically → record status updates
```

This mirrors the accountability pattern established earlier in this project's design work (credential/factor reverification on any sensitive edit, automatic audit logging via the data layer) — carried forward because it directly serves the Governance & Safety judging criterion (human oversight, audit trail) in the new brief.

**Note on patient-side auth:** Clerk authenticates the small demo patient account (§3.1–§3.6), while the tokenized upload flow (§3.2–§3.3) remains a separate appointment-scoped capability rather than a Clerk user session. See the `upload_links` vs. `patient_accounts` design note in §4 for why these are kept distinct. A patient may record a reuse/replacement choice within either authorized scope without staff re-authentication, but the resulting eligibility match is not final until a staff member reviews and confirms it.

---

## 6. Resolved Decisions and Remaining Open Items

### 6.1 Resolved from the supplied data

#### Eligibility fixture coverage

All nine document pages become individual extraction fixtures. The initial rules fixture set covers all seven code families, using a compound match rather than `issuer_code` alone:

| Code | Supplied document variants | Deterministic demo behavior |
| --- | --- | --- |
| `MRDEB` | Medical referral letter; employer appointment email | Referral requested tests feed matching. Appointment email contributes appointment/instruction facts but does not independently prove a package; missing paired coverage facts require review. |
| `EVWPA` | Health check-up voucher | Match the explicit selected test list and stated expiry. |
| `EVWME` | Group-insurance medical invitation | Match Adult Medical Examination plus the letter's completion window; retain certificate/coverage metadata. |
| `BLPDE` | Underwriting follow-up | Separate Full Medical Examination and HIV test from non-medical administrative requirements; non-medical items never become clinic tests. |
| `BLPHS` | Wellness voucher with `WELL1`/`WELL2`/`WELL3` options | Use only the checked package (`WELL2` in the fixture), its included tests, and explicit validity date. Transfer fields do not change the patient unless completed and staff-reviewed. |
| `NSTNBU` | Further-requirements letter | Preserve the requirement for two urine examinations on different days and the fulfil-by date; route unsupported multi-visit scheduling details to review. |
| `MOL0199VME` | Two government authorisation-form variants | Use checked purpose/check-up/add-on/test options. The fixture with `PEE226`, MMR Dose 1, and ECG can match those selections; the variant without a selected examination code remains review-required. |

The rules table stores fixture expectations, but final package names, billing arrangements, and production eligibility meaning still require clinic approval. Synthetic issuer wording is not treated as authoritative real-payer policy.

#### PASS versus REVIEW

There is no arbitrary numeric confidence threshold in P0. `readiness_status = pass` only when all of these gates pass:

1. detected document type has a valid schema;
2. every required field for that type is present;
3. every required fact has page/source-excerpt evidence;
4. selected versus unselected options are unambiguous;
5. an explicit patient identifier matches exactly within the authorized scope;
6. validity is current and can be established from an explicit or rule-supported date basis;
7. exactly one active deterministic eligibility rule matches.

Any failed gate sets `needs_review` with reason codes. Model confidence may prioritize the review UI but can never independently produce PASS or `ready`.

#### Demo scenarios and accounts

- The judged demo includes one booked patient ready before arrival, one booked patient needing review, and one walk-in whose single ticket visibly transitions from `processing` to `ready` or `needs_review` without changing number or check-in time.
- Seed four Clerk patient accounts chosen from the 51 questionnaire people that match registration: an Incoming ready case, an Incoming needs-review case, an Ongoing/counter-change case, and a Finished case with questionnaire, coverage, mocked payment, and visit history. The three dual-questionnaire people are preferred for at least one history-rich account.
- Do not seed judge accounts from the six unmatched questionnaire people. Keep those rows as visible import exceptions for an admin/test fixture.
- A dedicated corporate-batch screen is not P0. Demonstrate scale by seeding multiple booked patients with the same employer/screening date and using the existing date-filtered Incoming board.

### 6.2 Still open

- Exact visual system and interactive polish: colors, typography, production icons, and final responsive compositions.
- Clinic-approved package names, billing arrangements, and interpretation of each synthetic rule fixture.
- Staffing targets and service-time expectations for ready and review workstreams.
- The operational cost estimate for OpenAI document processing, Railway, Supabase, Clerk, and Vercel at the expected demo/production volume.
- Whether precise source bounding boxes justify adding a local/specialized OCR adapter after the page/excerpt baseline works.
- Final policy for resolving the six unmatched questionnaire people and any future conflicting source identities in a production import.
