---
target: patient screen
total_score: 24
max_score: 40
na_heuristics:
p0_count: 0
p1_count: 4
timestamp: 2026-08-13T12-48-42Z
slug: frontend-patient
---
Method: dual-agent (A: impeccable_ui_review · B: impeccable_detector)

## Design Health Score

| # | Heuristic | Score | Key issue |
|---|---|---:|---|
| 1 | Visibility of system status | 3 | Loading, saving, stale-data, and submission states are visible; activation and long-form completion progress are vague. |
| 2 | Match system / real world | 3 | Mostly patient-friendly, but terms such as activation, coverage, Singpass, and Myinfo need plainer context. |
| 3 | User control and freedom | 2 | Onboarding has no visible Back or save-and-exit path; invalid upload links are dead ends. |
| 4 | Consistency and standards | 3 | Tokens, cards, navigation, and focus styling are cohesive; embedded Clerk introduces a second hierarchy. |
| 5 | Error prevention | 2 | Disabled actions and saved drafts help, but the journey does not clearly redirect urgent symptoms away from administrative processing. |
| 6 | Recognition rather than recall | 3 | Stepper, summaries, sources, and next-step framing help; the long questionnaire still demands memory. |
| 7 | Flexibility and efficiency | 2 | Prefill, drafts, coverage reuse, and persistent destinations help; onboarding remains rigidly linear. |
| 8 | Aesthetic and minimalist design | 3 | Entry is focused and polished; the questionnaire becomes dense and repetitive. |
| 9 | Error recovery | 2 | Retry states preserve work, but invalid links and activation errors lack actionable recovery. |
| 10 | Help and documentation | 1 | Explanatory copy exists, but there is no persistent clinic-contact or contextual-help path. |
| **Total** |  | **24/40** | **Acceptable; significant journey improvements remain** |

## Design Specificity Verdict

**Strong visual specificity; moderate journey specificity.** The clinical green and warm cream palette, condensed editorial headings, synthetic-data disclosure, single-ticket language, coverage-reuse branch, and explicit staff confirmation feel authored for Epicenter. The product becomes more generic in the questionnaire and utility destinations, where conventional stacked cards do not express the safety model strongly enough.

The deterministic detector returned zero findings across `frontend/patient`. This confirms that the source avoids the detector's known anti-patterns; it does not invalidate the human findings around information architecture, recovery, or trust sequencing. Live browser checks also found no confirmed axe violations, horizontal overflow, console errors, page errors, or failed requests.

No reliable user-visible overlay is available. Browser mutation tooling was unavailable, so the evidence pass used isolated desktop/mobile screenshots, DOM metrics, focus traversal, axe, console capture, and request capture.

## Overall Impression

The patient app looks calm, credible, and unusually honest about synthetic data and human confirmation. Its largest opportunity is to make the whole journey as reassuring and focused as the account screen: establish trust before asking for credentials, break the medical form into understandable progress, and turn every failure into a clear next action.

## What's Working

- The sign-up surface is visually confident and clearly separates patient signup from separately provisioned staff access.
- The journey model is strong: one appointment, one ticket, and one currently available next action. Coverage reuse is rechecked rather than silently trusted.
- System states are honest. Staff confirmation remains explicit, stale queue data is labelled, and synthetic payment/data copy avoids overclaiming.
- Accessibility foundations are solid: native controls, semantic landmarks, visible focus styling, keyboard reachability, reduced-motion support, and zero confirmed axe violations.

## Priority Issues

### [P1] Urgent clinical escalation is absent from the patient journey

**Why it matters:** The questionnaire collects pregnancy, pain, medical history, and medication information, but the administrative flow does not state clearly that urgent symptoms must be raised with clinic staff immediately and that paperwork never delays care. Patients could mistake questionnaire completion or readiness status for clinical triage.

**Fix:** Add a concise safety notice before the questionnaire and near relevant conditional sections: this form does not assess urgency; tell clinic staff immediately about urgent symptoms; clinical escalation overrides queue and administrative readiness.

**Suggested command:** `$impeccable clarify`

### [P1] The questionnaire turns guided onboarding into a wall of fields

**Why it matters:** Every section renders sequentially in one panel. Several decision points exceed four choices, including a ten-option pain scale, six ethnicity choices, five smoking choices, five medication choices, and a large condition multiselect. Patients cannot estimate effort or see how much remains.

**Fix:** Split the questionnaire into section-level steps, show progress and required-field counts, reveal conditional follow-ups only when triggered, preserve drafts between sections, and add an answer review before submission.

**Suggested command:** `$impeccable distill`

### [P1] Mobile requests credentials before establishing trust

**Why it matters:** At 780px and below, the account form is ordered first with a full viewport minimum height. The synthetic-data disclosure, patient/staff boundary, and visit-preparation explanation appear only after scrolling past the credential request.

**Fix:** Keep a compact brand, “Patient account” label, synthetic-data disclosure, and staff-access boundary above the mobile form. Move only the longer explanatory content below it.

**Suggested command:** `$impeccable adapt`

### [P1] Invalid upload links end without recovery

**Why it matters:** The error screen tells the patient to contact the clinic but provides no button, contact detail, return destination, or link-request action. A patient who followed an expired message has no path forward.

**Fix:** Add “Request a new link,” clinic contact details, and “Return to patient sign in.” Explain whether previously entered or uploaded information remains saved.

**Suggested command:** `$impeccable harden`

### [P2] Onboarding is linear without enough control

**Why it matters:** The three-step indicator communicates progress, but completed steps are not reviewable and there is no Back, Save and leave, or explicit autosave explanation. Interrupted patients cannot confidently exit.

**Fix:** Add “Save and leave,” allow safe review of completed steps, and state what is saved automatically. Keep forward progression gated where clinical or identity integrity requires it.

**Suggested command:** `$impeccable onboard`

## Cognitive Load

The entry screen is low-load, with two account modes and two authentication methods. The questionnaire fails 4 of 8 checks: chunking, one-thing-at-a-time, minimal choices, and working-memory support. Its full medical form is shown without persistent section progress or a visible completion summary. Bottom navigation remains manageable at four destinations.

## Emotional Journey

- **Entry:** Calm, credible, and concrete: “Prepare before your clinic visit.”
- **Mobile trust valley:** Identity credentials appear before the product explains the synthetic-data and staff-access boundaries.
- **Onboarding:** The three-step indicator creates momentum, but institutional terms arrive before the patient benefit is fully explained.
- **Questionnaire valley:** Form density, medical uncertainty, and unknown remaining effort create the highest abandonment risk.
- **Coverage peak:** “Use same coverage” versus “upload new document” is a clear, low-risk decision, and staff confirmation remains explicit.
- **Failure ending:** The invalid-link state is visually clean but emotionally abrupt because it offers no next action.

## Persona Red Flags

**Jordan — first-time patient:** Singpass, Myinfo, coverage, and activation arrive quickly without one plain-language overview. A failed upload link offers no next click. The questionnaire does not communicate remaining effort.

**Sam — accessibility-dependent patient:** Core semantics, labels, native controls, and focus styling are strong. However, the public account page has two visible H1 elements, seven of nine visible interactive elements measure below the preferred 44px height, and mobile source order places safety context after the whole form. Axe left contrast as a manual-review item for five nodes rather than confirming a failure.

**Casey — distracted mobile patient:** The first viewport prioritizes authentication over reassurance. The questionnaire lacks section progress, interruption guidance, and a prominent resume state. Onboarding hides the thumb-friendly bottom navigation and provides no visible save-and-exit action.

## Minor Observations

- Desktop account creation is balanced and polished, but the custom account-mode switch duplicates Clerk's own sign-in link.
- “Create patient account” wraps in the mobile segmented control and feels cramped.
- “Welcome! Please fill in the details to get started” is generic compared with the otherwise product-specific copy.
- The public account surface has two visible H1s: “Prepare before your clinic visit” and “Create your account.”
- Most Clerk controls are 32px high; seven of nine visible interactive elements fall below the preferred 44px target size.
- The invalid-link heading is oversized for a recovery state and leaves excessive empty space.
- “Accepted for staff confirmation” is accurate but awkward; “Checks complete — awaiting staff confirmation” is clearer.
- “Pay now — demo” is honest, but a confirmation step should reinforce that no money moves.

## Questions to Consider

- What must patients see before trusting the product with identity and health information on a phone?
- Could onboarding promise a time estimate and show section-level completion?
- Should clinical-safety guidance remain visible throughout the questionnaire rather than appearing once?
- When a token fails, can Epicenter recover the patient without making them understand appointment-link infrastructure?
- Can every journey state answer: “What happened?”, “Does staff still need to confirm?”, and “What should I do next?”
