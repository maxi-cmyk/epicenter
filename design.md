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
[All pre-registration gates passed before arrival?]
  Required documents present + valid + high-confidence + every match clean
     ├── YES → FAST QUEUE
     └── NO  → REVIEW QUEUE (SLOW PATH)
     ↓
[Pre-Arrival Record Ready, queue pre-assigned]
  Registration + questionnaire data pre-filled, package/billing pre-matched
  Any low-confidence field flagged for staff review
     ↓
[Patient Arrives]
     ↓
[Staff manually verifies identity/e-card in person using approved process]
     ↓
[System records staff confirmation only (§2.3)]
     ↓
[FAST QUEUE]                             [REVIEW QUEUE]
Staff confirms pre-processed record        Staff resolves flagged fields,
in seconds, patient proceeds                then confirms — patient's extra
                                             time does not block fast-queue
                                             patients behind them
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
[Assign REVIEW QUEUE]  ← all walk-ins use the slow path
  reason: walk_in
     ↓
[Staff uploads/scans coverage document at review counter]
     ↓
[Document Extraction Layer] → [Eligibility & Package Matching Engine]
     ↓
[Staff resolves any flags and confirms]
     ↓
[Queue / Consultation or Screening]
```

### Flow notes

- Fast-queue admission uses an all-gates rule: the patient must have a booked appointment, complete pre-registration before arrival, provide every required valid document, receive high-confidence extraction for every required field, and produce clean eligibility/package matches. If any gate fails, the patient enters the review queue.
- Walk-ins always enter the review queue, regardless of eventual extraction confidence. Because walk-ins are less common, they share the staffed slow path with incomplete and uncertain cases rather than creating a third queue.
- **Queue assignment solves the compounding-delay problem named in the brief** by structurally protecting booked, fully pre-cleared patients from variable-time cases.
- Identity/e-card checking always happens manually, in person, and outside system decision logic. The product only records the responsible staff member's confirmation after the manual process; it never scans, validates, or suggests a result.
- Staff confirmation is always required before a record is treated as final in either queue.

### 1.3 Shared Check-First Upload Entry

This branch runs when a patient opens either a tokenized appointment link or the upload screen in a seeded demo account:

```text
[Patient reaches coverage screen]
     ↓
[Resolve patient within the current scope]
  Tokenized link: appointment-bound patient, matched by normalized NRIC/email
  Demo account: authenticated patient record, matched by normalized NRIC/email
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
- Matching requires one unambiguous exact match after normalisation. NRIC is preferred and email is the fallback; conflicting or multiple matches reveal no prior coverage and fall back to upload plus staff review.
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
- Read-only navigation uses the active staff session. Re-authentication is required immediately before confirming/correcting extracted data, revealing NRIC, overriding a match, confirming billing, or recording a manual identity/e-card check.
- Sensitive actions use Clerk reverification. The backend validates that the signed session reflects sufficiently recent verification before committing the action; a frontend-only modal is not sufficient authorization.
- Invalid credentials show an inline error without clearing the email. Repeated failure preserves the uncommitted action and offers Cancel; session expiry returns to sign-in and restores the intended route after success.

### 2.2 Queue Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Queue Overview     Date: [12 Aug 2026]    [Search] [Filters]             │
├───────────┬──────────────────────────────────────────────────────────────┤
│ Incoming  │ 09:00 Loh Wei Ming  FAST   F-014  Expected Counter 2 [Open]│
│ 8         │ 09:15 Tan Kai Xuan  REVIEW R-006  Expected Counter 4 [Open]│
├───────────┼──────────────────────────────────────────────────────────────┤
│ Ongoing   │ F-012 Mei Chen    Counter 2  Manual check recorded [Open]  │
│ 3         │ R-004 Priya Nair  Counter 4  Document review       [Open]  │
├───────────┼──────────────────────────────────────────────────────────────┤
│ Finished  │ F-010 Siti Rahman Counter 2  Completed 08:52        [Open]  │
│ 21        │ R-002 John Lim    —          No-show 08:45          [Open]  │
└───────────┴──────────────────────────────────────────────────────────────┘
```

- **Incoming** retains scheduled date/time, fast/review label, expected queue number, and expected counter. Opening a row leads to §2.9.
- **Ongoing** begins after staff records the manual check-in confirmation (§2.3) and shows actual queue/counter plus current stage.
- **Finished** includes completed, cancelled, and no-show outcomes; rescheduled appointments remain Incoming on the new date with an audit link to the old slot.
- Empty groups say what happened (for example, “No incoming appointments for this date”). Loading uses fixed-height skeleton rows; load failure provides Retry. Color is never the only status cue.

### 2.3 Check-In and Manual Verification Confirmation

```text
┌─────────────────────────────────────────────────────────────┐
│ Check in: Loh Wei Ming — 12 Aug 2026, 09:00                 │
│ Planned: FAST / F-014 / Expected Counter 2                  │
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

### 2.4 Review Queue Worklist

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Review Queue  [Today] [Reason: All] [Oldest first] [Search]            │
├──────┬───────────────┬───────────────┬──────────────────┬─────────────┤
│ R-006│ Tan Kai Xuan  │ 09:15 booked │ Missing document │ [Open]      │
│ R-007│ Amir Loh      │ 10:00 booked │ Expired voucher  │ [Open]      │
│ R-008│ Priya Nair    │ Walk-in 09:22│ Walk-in          │ [Open]      │
└──────┴───────────────┴───────────────┴──────────────────┴─────────────┘
```

- Each row shows appointment/walk-in time, queue reason, document status, age in queue, assigned counter, and next action. Opening a document issue leads to §2.6; missing documents lead to §2.5.
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
│ Review: Meridian_chit.pdf        Reason: AMBIGUOUS PACKAGE           │
├──────────────────────────────┬───────────────────────────────────────┤
│ Source document              │ Extracted fields                      │
│ [highlighted source region]  │ Issuer      Meridian (MRDEB)  PASS   │
│                              │ Policy no.  MRD707314         PASS   │
│                              │ Valid until 10 Aug 2026       REVIEW │
│                              │ Package     Cardiac Add-on    REVIEW │
│                              │                                       │
│                              │ [Edit selected field] [View rule]     │
├──────────────────────────────┴───────────────────────────────────────┤
│ [Back to worklist]             [Confirm corrected record]           │
└──────────────────────────────────────────────────────────────────────┘
```

- Selecting a field highlights its source. Edit mode shows the original value, corrected value, required correction reason, and Cancel/Save; Save requires re-authentication and creates an immutable audit entry.
- Expired documents, unknown issuers, ambiguous matches, OCR failure, and no-match states each explain the cause and next action. Staff may correct extracted facts or choose a rules-table result, but cannot make an LLM-generated coverage decision final.
- Confirmation is unavailable until every required field is resolved. Failed save preserves edits and offers Retry.

### 2.7 Records Search

```text
┌──────────────────────────────────────────────────────────────────┐
│ Patient Records                                                  │
│ Search [ Name, patient ID, masked NRIC, email ________________ ] │
│ Filters [Last visit] [Coverage] [Queue]                          │
├─────────────┬────────────────┬───────────────┬───────────────────┤
│ PS-REG-0417 │ Loh Wei Ming   │ 12 Aug 2026   │ Meridian  [Open] │
│ PS-REG-0398 │ Tan Kai Xuan   │ 03 Aug 2026   │ CHAS      [Open] │
└─────────────┴────────────────┴───────────────┴───────────────────┘
```

- Search is debounced, keyboard operable, and never displays full NRIC in results. Empty, loading, permission-denied, and error states are explicit.

### 2.8 Patient Record

```text
┌──────────────────────────────────────────────────────────────────┐
│ Back to records                                                  │
│ PS-REG-0417 · Loh Wei Ming · NRIC S***946C             │
│ Current visit: 12 Aug 2026 · Queue FAST · F-014 · Counter 2     │
│ Coverage: Meridian (MRDEB) · Cardiac Add-on · Confirmed         │
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
│ REVIEW · R-006 · Expected Counter 4 · Missing document          │
│                                                                  │
│ Pre-registration checklist                                      │
│ PASS  Patient details       PASS  Questionnaire                 │
│ FAIL  Coverage document     —     Eligibility match             │
│                                                                  │
│ [Send upload reminder] [Upload for patient] [Open review]       │
│ [Reschedule] [Cancel appointment] [Record no-show]              │
└──────────────────────────────────────────────────────────────────┘
```

- This replaces the duplicate pre-arrival list: §2.2 owns list-level status; this screen owns one appointment's prerequisites and actions.
- Reminder delivery shows sending/sent/failed states and retry. Reschedule retains an audit link to the old date; cancel/no-show require confirmation and move the row into Finished with its outcome.

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
│ Coverage source: Meridian document · confirmed 08 Aug 2026      │
│ Package: Executive Health Screening — Cardiac Add-on            │
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
│ FAST counters:   [1] [2]         REVIEW counters: [3] [4]       │
│ Expected load:    8 incoming      Expected load:   5 incoming    │
│                                                                  │
│ R-006 Tan Kai Xuan · Expected 4 · Actual —  [Assign counter ▾]  │
│ [Preview changes]                         [Apply allocation]      │
└──────────────────────────────────────────────────────────────────┘
```

- Rebalancing may change expected/actual counters but cannot move a patient into FAST unless all fast-queue prerequisites pass. Changes require confirmation, announce affected patients/staff, and are audited.

### 2.15 Staff-Wide States and Accessibility

- Staff tables provide search, filters, sorting, pagination/virtualisation for large lists, skeleton loading, actionable errors, and meaningful empty states.
- Desktop is primary; tablet collapses the sidebar; narrow layouts turn tables into labelled cards without horizontal scrolling. A skip-to-main link bypasses the persistent navigation, visible focus follows visual order, and returning from detail restores list state.
- Production icons use one SVG icon set. Status always includes text plus icon/shape; wireframe words such as PASS, REVIEW, ALERT, and FAIL are the accessible labels, not color-dependent decoration.

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
│ FAST QUEUE · F-014                      │
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
| Review queue | REVIEW QUEUE, `R-*`, counter/position; no internal confidence details |
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
│ Cardiac Add-on                          │
│ Covered by Meridian: $XXX.XX            │
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
│ 12 Aug 2026 · Executive Health [Open]   │
│ 03 Feb 2026 · GP Consultation   [Open]  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Visit: 12 Aug 2026                      │
│ Package: Cardiac Add-on                 │
│ Coverage: Meridian                      │
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

```text
patients
├── id (uuid, PK)
├── patient_id_display        -- e.g. "PS-REG-0417"
├── full_name
├── nric_masked
├── nric_full (encrypted)       -- reveal is a logged action
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

staff_accounts
├── id (uuid, PK)
├── clerk_user_id (text, UNIQUE)
├── full_name
├── email
├── role                         -- registration / pharmacist / billing / admin
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
├── file_reference             -- stored upload (image/PDF)
├── raw_extracted_text (text)    -- full OCR/LLM-read output, for audit
├── issuer_name                    -- e.g. "Meridian Life Assurance"
├── issuer_code                       -- e.g. "MRDEB"
├── policy_or_voucher_no
├── requested_items (jsonb)             -- e.g. ["Chest X-Ray", "HIV Antibody Test", "Treadmill ECG"]
├── validity_start / validity_end
├── extraction_confidence (jsonb)          -- per-field confidence scores
├── processing_status                     -- uploading / processing / ready / failed
├── processing_error_code (nullable)       -- unsupported / too_large / unreadable / timeout / extraction_failed
├── status                                    -- pending_review / confirmed / rejected
├── confirmed_by_staff_id (FK, nullable)
└── confirmed_at

coverage_reuse_decisions
├── id (uuid, PK)
├── patient_id (FK → patients)
├── appointment_reference
├── prior_coverage_document_id (FK → coverage_documents)
├── entry_source                    -- "tokenized_link" / "demo_account"
├── match_method                    -- "nric" / "email"; stores method, not raw value
├── decision                        -- "reuse" / "replace"
├── replacement_document_id (FK → coverage_documents, nullable)
└── created_at
    -- records the check-first choice without modifying the prior document;
    -- "reuse" still creates a new eligibility match for this appointment

eligibility_rules
├── id (uuid, PK)
├── issuer_code                -- e.g. "MRDEB", "EVWPA"
├── issuer_name
├── package_name                  -- e.g. "Executive Health Screening — Cardiac Add-on"
├── included_items (jsonb)
├── billing_arrangement
└── active (boolean)
    -- this table is the rules-based matching engine referenced in PRD §6.2 —
    -- deliberately separate from LLM extraction, so coverage/billing decisions
    -- are never an LLM inference, only a structured lookup

eligibility_matches
├── id (uuid, PK)
├── coverage_document_id (FK → coverage_documents)
├── appointment_reference                -- eligibility is re-evaluated per visit
├── matched_rule_id (FK → eligibility_rules, nullable)   -- null if no clean match
├── match_confidence                -- high / needs_review / no_match
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
├── extraction_status                    -- "high_confidence" / "needs_review"
├── match_status                         -- "clean" / "ambiguous" / "no_match"
├── queue                                -- "fast" / "review"
├── queue_reason                         -- "all_prerequisites_passed" / "walk_in" /
│                                            "prereg_incomplete" / "missing_document" /
│                                            "expired_document" / "low_confidence" /
│                                            "ambiguous_match"
├── visit_status                         -- "incoming" / "ongoing" / "finished"
├── visit_outcome (nullable)              -- "completed" / "cancelled" / "no_show"
├── rescheduled_from_queue_entry_id (FK, nullable)
├── expected_queue_number (nullable)     -- e.g. "F-014" / "R-006" for Incoming
├── expected_counter_number (nullable)   -- planning assignment shown before arrival
├── queue_number (nullable)              -- active/final number once checked in
├── counter_number (nullable)            -- actual assigned counter
├── processing_stage (nullable)          -- e.g. "manual_check_confirmation" / "document_review"
├── assigned_at
├── checked_in_at (nullable)             -- transition: Incoming → Ongoing
└── completed_at (nullable)              -- transition: Ongoing → Finished
    -- database/service constraint: queue="fast" only when intake_type="booked",
    -- prereg_completed_at is set, every document gate is true/high-confidence,
    -- and match_status="clean"; every walk-in is queue="review" and starts Ongoing

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
├── queue_type                         -- "fast" / "review"
├── active (boolean)
├── updated_by_staff_id (FK → staff_accounts)
└── updated_at

questionnaire_responses
├── id (uuid, PK)
├── patient_id (FK → patients)
├── appointment_reference
├── questionnaire_type          -- "general_health" / "occupational_health"
├── responses (jsonb)              -- fields specific to each questionnaire type,
│                                       per general_health_questionnaire_mock_patients.csv
│                                       and occupational_health_questionnaire_mock_patients.csv
├── shared_fields_reused (boolean)   -- true if patient/contact fields were pulled
│                                         from `patients` rather than re-entered
├── consent_status                    -- pending / recorded
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
│                                "reveal_nric" / "override_match" / "assign_queue" /
│                                "confirm_allergy_check" / "check_prior_coverage" /
│                                "reuse_coverage" / "request_coverage_replacement" /
│                                "assign_expected_counter" / "record_manual_checks" /
│                                "check_in" / "reassign_counter" / "confirm_billing" /
│                                "reschedule_visit" / "cancel_visit" / "record_no_show" /
│                                "complete_visit"
├── target_table
├── target_id
├── details (jsonb)
└── timestamp
```

### Design notes

- `patients` fields are deliberately a direct mirror of `patient_registration_synthetic.csv`'s columns, so the provided dataset loads with no schema-translation guesswork — this matters for a hackathon timeline.
- `coverage_documents` and `eligibility_rules`/`eligibility_matches` are kept as separate concerns on purpose: the first is "what did the LLM read off this document," the second is "what does that map to under our rules." This split is what makes the hallucination-mitigation claim in PRD §6.2/§8 concretely true rather than just asserted — the LLM's output never directly becomes a billing decision; it always passes through a deterministic lookup table first.
- `queue_entries` makes the strict queue rule (PRD §4.2) queryable at the visit level. Queue status does not live on a coverage document because booking type and pre-registration completion are also required inputs. The same row drives the Queue Overview (§2.2), Appointment Detail (§2.9), and patient Queue Status (§3.4).
- `queue_entries.scheduled_at` preserves the appointment date across all three lifecycle views. `expected_queue_number` and `expected_counter_number` are generated for Incoming booked patients after routing; `queue_number` and `counter_number` hold the actual assignments after check-in. `checked_in_at` and `completed_at` drive the Incoming → Ongoing → Finished transitions without moving data between tables.
- `manual_check_confirmations` is deliberately an attestation record, not a verification engine. It proves which staff member recorded completion of the clinic's manual identity/e-card process and cannot store or infer an automated verification result.
- `visit_outcome`, `rescheduled_from_queue_entry_id`, and `counter_allocations` support the cancelled, no-show, rescheduled, and counter-rebalancing states shown in staff views without weakening the strict fast-queue rule.
- `coverage_reuse_decisions` records the check-first branch independently of the source document. Reuse points to the prior document but creates a fresh appointment-scoped `eligibility_matches` row, so an old coverage decision is never silently carried forward.
- `touchpoint_reuse_log` is the mechanism that makes "we eliminated duplicate entry across all five touchpoints" a provable, queryable fact in the demo — not just the questionnaire-only claim an earlier draft of this system could support.
- `upload_links` and `patient_accounts` are two intentionally different mechanisms for two intentionally different needs: a one-time, unauthenticated, appointment-scoped token for the common case (submit a document ahead of a visit), versus a real but small, fixed-pool account for anything requiring returning access (queue status, payment, records history). Collapsing these into one "patient login" table would overstate what's actually been designed — keeping them separate keeps that honest.
- `billing_reviews` separates staff-confirmed billing from patient payment. `payments.status` uses explicit `mock_*` values so success/failure/receipt states remain visibly demo-only in data, not only in prose that a reader might skip.

---

## 5. Auth & Review Flow Summary

```text
Staff logs in through Clerk (individual account)
   ↓
Read-only actions (view queue, view records, view audit log) → no re-auth required
   ↓
Any confirmation or correction action (record a manually completed identity/e-card
check, confirm extracted data/billing, override a match, reveal NRIC, edit a field)
→ Clerk reverification before the change commits
   ↓ (on success)
Action commits → audit_log entry created automatically → record status updates
```

This mirrors the accountability pattern established earlier in this project's design work (credential/factor reverification on any sensitive edit, automatic audit logging via the data layer) — carried forward because it directly serves the Governance & Safety judging criterion (human oversight, audit trail) in the new brief.

**Note on patient-side auth:** Clerk authenticates the small demo patient account (§3.1–§3.6), while the tokenized upload flow (§3.2–§3.3) remains a separate appointment-scoped capability rather than a Clerk user session. See the `upload_links` vs. `patient_accounts` design note in §4 for why these are kept distinct. A patient may record a reuse/replacement choice within either authorized scope without staff re-authentication, but the resulting eligibility match is not final until a staff member reviews and confirms it.

---

## 6. Open Items for Next Pass

- Exact visual/interactive wireframe (colors, type, layout polish) — not yet built; this document covers structure and flow only.
- Build out the full `eligibility_rules` table content from all insurer/TPA samples in the provided Medical Chit Letters document, not just the two illustrated here (Meridian, Everwell).
- Define staffing targets and service-time expectations for the review queue now that its membership is fixed: all walk-ins plus every incomplete, invalid, low-confidence, or ambiguous pre-registration.
- Decide how a corporate batch pre-registration scenario (multiple employees processed ahead of one screening day) would extend Queue Overview (§2.2) and Appointment Detail (§2.9), if built, to support the scalability judging criterion.
- Confirm exact confidence-threshold logic for what triggers REVIEW vs. PASS on an extracted field.
- Decide whether the demo shows a live mixed-queue simulation: a booked, fully pre-cleared patient enters the fast queue while a walk-in and a booked patient with a failed prerequisite both enter the review queue.
- Decide how many seeded demo patient accounts (PRD §4.6/`patient_accounts`) to prepare for judges, and what visit history each should have pre-populated so Medical Records (§3.6) has something meaningful to show.
