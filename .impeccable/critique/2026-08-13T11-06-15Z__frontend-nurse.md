---
target: nurse page
total_score: 23
max_score: 40
na_heuristics:
p0_count: 0
p1_count: 4
timestamp: 2026-08-13T11-06-15Z
slug: frontend-nurse
---
# Epicenter Nurse UI Critique

## Design Health Score

| # | Heuristic | Score | Key issue |
|---|---|---:|---|
| 1 | Visibility of system status | 3 | Loading and authorization are visible, but data freshness and fallback state are understated. |
| 2 | Match system / real world | 3 | Staff language is strong; generic visit-phase lanes underspecify clinic decisions. |
| 3 | User control and freedom | 2 | Task, authorization, and retry paths offer limited escape and recovery. |
| 4 | Consistency and standards | 3 | The visual system is cohesive, but embedded Clerk hierarchy and workspace patterns diverge. |
| 5 | Error prevention | 2 | Confirmation gates help, but synthetic fallback and enrollment boundaries need stronger prevention. |
| 6 | Recognition rather than recall | 3 | Labels and patient details help; mobile hides queue phases off-screen. |
| 7 | Flexibility and efficiency | 1 | No bulk handling, shortcuts, queue filters, or next-exception accelerator. |
| 8 | Aesthetic and minimalist design | 3 | Strong sign-in composition; finished work competes with actionable exceptions. |
| 9 | Error recovery | 2 | Errors identify failure but often lack a precise recovery action. |
| 10 | Help and documentation | 1 | Safety explanations exist, but workspace help is not task-focused or contextual. |
| **Total** | | **23/40** | **Acceptable; meaningful workflow improvements needed** |

## Design Specificity Verdict

**Partially authored.** The split sign-in composition, condensed typography, clinical green, and accountability language are unmistakably Epicenter. The authenticated workspace is less specific: its Incoming / Ongoing / Finished board is a standard Kanban wearing Epicenter colors. It underexpresses the product's real differentiator: administrative exceptions, original waiting age, human confirmation, and the readiness-to-intervention loop.

The deterministic detector returned zero findings across `frontend/nurse`. This means the source avoids the detector's known anti-patterns; it does not mean the workflow hierarchy is solved. The detector missed the information-architecture and situational-awareness problems found in the independent design review.

Live browser evidence was limited to the signed-out surface. Desktop and mobile had no horizontal overflow, axe found zero confirmed violations, focus outlines were visible, and there were no console errors at the exact `localhost` URL. All six visible mobile controls were below the preferred 44px target height, with the main controls at 32px. The authenticated screens were reviewed from source because the isolated browser was not signed in.

## Overall Impression

The visual foundation is more distinctive than most clinical admin tools: calm, accountable, and serious without looking like a generic hospital portal. The interface loses that advantage once work begins. The board emphasizes visit phase when nurses need intervention priority. The single biggest opportunity is to turn the home screen into an exception cockpit that answers, within seconds, which patient needs human action next and why.

## What's Working

- The sign-in surface feels authored for Epicenter. The editorial split, Barlow Condensed headings, dark green palette, and restrained grid create a credible operational identity.
- Safety copy is excellent. Phrases such as “Individual staff accountability,” “Human confirmation remains required,” and “Administrative readiness only” set clear boundaries.
- Accessibility foundations are present: semantic structure, labeled navigation, visible focus styling, reduced-motion support, and authorization loading announcements.

## Priority Issues

### [P1] Intervention priority is visually subordinate to visit phase

The home screen gives Incoming, Ongoing, and Finished equal structural authority. A needs-review ticket is distinguished mainly by a thin amber border, while finished patients retain prime space.

**Why it matters:** A nurse under time pressure must scan multiple cards to infer who needs action. The product's differentiated readiness loop becomes visually secondary to a generic queue board.

**Fix:** Lead with a “Needs confirmation now” worklist ordered by original waiting age, reason, and service target. Preserve the single `Q-*` ticket and visit phase as secondary metadata. Collapse Finished by default.

**Suggested command:** `$impeccable distill`

### [P1] Synthetic fallback can resemble current clinic truth

Fallback data occupies the same shell as live data, while “Local synthetic fallback” is a small context pill and the timestamp is hard-coded.

**Why it matters:** In a clinical operations surface, demo data that resembles live state can cause staff to act on the wrong record set.

**Fix:** Add a persistent, high-salience demo banner, derive freshness from `generated_at`, and disable writes whenever fallback mode is active.

**Suggested command:** `$impeccable harden`

### [P1] Mobile asks for credentials before earning trust

At mobile widths, the sign-in form occupies the first full viewport and safety/accountability context follows below it. The live mobile controls were also only about 32px high rather than the preferred 44px.

**Why it matters:** Nurses see a sensitive credential request before the staff-only and accountability framing, while small controls increase one-handed error risk.

**Fix:** Place a compact brand, staff-only label, data-mode indicator, and human-confirmation reassurance above the form. Increase all interactive targets to at least 44px and retain longer context below.

**Suggested command:** `$impeccable adapt`

### [P1] Staff-only enrollment boundary is visually porous

The rendered Clerk structure exposed a Sign up path even though the custom wrapper attempts to suppress it.

**Why it matters:** A nurse-only clinical surface must never imply self-service staff enrollment.

**Fix:** Remove signup at the Clerk instance and routing level, then verify it is absent from the accessibility tree rather than only visually hidden.

**Suggested command:** `$impeccable harden`

### [P2] The workspace has no expert acceleration or strong recovery path

Tickets are handled one at a time, with no next-exception action, keyboard shortcut, queue filter, or bulk-safe affordance. Authorization and API errors give limited retry guidance.

**Why it matters:** Repetitive clinic work becomes slower as volume grows, and failures force staff to stop and interpret generic messages.

**Fix:** Add a “Next unresolved case” action, keyboard-first navigation, useful filters, and actionable Retry / Return to board / Contact administrator recovery choices.

**Suggested command:** `$impeccable clarify`

## Cognitive Load

The sign-in surface is low-load: two primary choices, clear grouping, and a focused task. The authenticated workspace is moderate-to-high load with three failed checklist items:

- **Single focus:** finished patients compete with active exceptions.
- **Minimal choices:** six openable tickets plus Refresh exceed the four-item working-memory threshold.
- **Working memory:** mobile phase panels sit off-screen in a horizontal carousel.

Grouping and base hierarchy pass, but progressive disclosure is incomplete because similar card metadata appears before the interface identifies the safest next action.

## Emotional Journey

- **Entry:** Serious, calm, and accountable.
- **Peak:** The desktop sign-in composition establishes credibility and human responsibility.
- **Valley:** Mobile postpones the safety rationale until after a full-screen credential form.
- **Operational valley:** Actionable exceptions become visual peers of ready and completed visits, creating scanning pressure.
- **Ending:** Errors and access denial explain the state but do not reliably tell staff what to do next.

## Persona Red Flags

**Alex — impatient power user:** Finished work occupies prime space while Alex hunts for the oldest exception. There is no next-case shortcut, bulk-safe action, keyboard accelerator, or prioritization filter.

**Sam — accessibility-dependent user:** Mobile controls fall below 44px. Readiness relies partly on border color and an alert icon hidden from assistive technology. The embedded sign-in structure may expose a signup path that the visible design intends to suppress.

**Casey — distracted mobile user:** Trust context appears after the first viewport. Horizontal phase swiping hides two-thirds of clinic state, and small controls make one-handed use less reliable.

## Minor Observations

- “Database” is implementation language rather than a nurse task label.
- “Docs” does not distinguish present, verified, expired, or actionable paperwork.
- “Est. arrival —” adds noise when no estimate exists.
- The authenticated dashboard source begins at H2 rather than a page-level H1.
- Development-mode Clerk language weakens the controlled-clinic tone.
- Completed patients should likely be disclosed on demand rather than permanently occupying one-third of the board.

## Questions to Consider

- What if Epicenter's home screen were an exception cockpit rather than a visit-phase Kanban?
- If a nurse has ten seconds, can they identify the single patient whose paperwork most urgently needs human intervention?
- Should completed patients remain visible by default, or move into a collapsed history view?
- If synthetic fallback activates during a real clinic session, what prevents someone from acting on demo data?
