---
name: Epicenter
description: Clinical wayfinding as an operating system for humane outpatient administration.
colors:
  deep-clinic-green: "#12372d"
  clinic-green: "#17473a"
  route-green: "#2d6d58"
  muted-green: "#5d9475"
  green-rule-wash: "#c8dbc9"
  green-surface: "#e0ebdc"
  cream-paper: "#f7f2e3"
  raised-paper: "#fffdf5"
  paper-edge: "#ebe2cb"
  operational-ink: "#17332b"
  muted-ink: "#53665f"
  attention-amber: "#a95816"
  attention-surface: "#f5dfbd"
  critical-red: "#9e3d36"
  critical-surface: "#f3d7d0"
  white: "#ffffff"
  hairline-rule: "rgba(23, 71, 58, 0.2)"
typography:
  display:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "clamp(2.7rem, 6vw, 5.4rem)"
    fontWeight: 700
    lineHeight: 0.86
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.01em"
  body:
    fontFamily: "Source Sans 3, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Source Sans 3, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "normal"
rounded:
  control: "8px"
  choice: "12px"
  surface: "14px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "18px"
  lg: "24px"
  xl: "28px"
  2xl: "36px"
components:
  button-primary:
    backgroundColor: "{colors.clinic-green}"
    textColor: "{colors.raised-paper}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 18px"
    height: "44px"
  button-secondary:
    backgroundColor: "{colors.raised-paper}"
    textColor: "{colors.clinic-green}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 18px"
    height: "44px"
  button-danger:
    backgroundColor: "{colors.critical-red}"
    textColor: "{colors.white}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 18px"
    height: "44px"
  status-ready:
    backgroundColor: "{colors.green-surface}"
    textColor: "{colors.deep-clinic-green}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "7px 10px"
  status-review:
    backgroundColor: "{colors.attention-surface}"
    textColor: "#713807"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "7px 10px"
  input-standard:
    backgroundColor: "{colors.raised-paper}"
    textColor: "{colors.operational-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "48px"
---

# Design System: Epicenter

## Overview

**Creative North Star: "Clinical Wayfinding as Operating System"**

Epicenter presents clinic administration as a legible route through states, evidence, and staff decisions. Warm cream paper and a faint square grid keep the interface humane, while deep clinic-green bands, fixed columns, hairline rules, numbered steps, and explicit status markers make every operational path easy to scan. The patient and nurse experiences are separate application shells over one shared visual foundation: patient work is mobile-first and focused, while nurse work is desktop/tablet-first and operationally dense.

The system is calm rather than sterile and precise rather than decorative. Its strongest visual moments are functional: the persistent navigation rail, condensed room-sign headings, the patient readiness board, the one-ticket route, and the dark allocation decision panel. Administrative automation stays visually subordinate to clear staff confirmation and escalation language.

**Key Characteristics:**

- Cream paper and 32px grid surfaces with deep-green wayfinding bands.
- Condensed uppercase display type paired with a plain, highly legible body face.
- Flat and tonal layouts structured by hairline rules, with selective ambient lift for major work surfaces.
- Explicit route, step, status, ticket, evidence, and human-decision markers.
- Shared tokens and primitives with distinct patient and nurse shell compositions.
- Responsive compositions that preserve operational hierarchy on desktop, tablet, and narrow mobile screens.

## Colors

The palette uses a dark clinical green as the operating frame, cream as the working paper, and amber or red only when an exception needs attention.

### Primary

- **Deep Clinic Green:** The darkest navigation, table-header, and decision-panel field; it establishes the clinic frame and carries high-contrast cream text.
- **Clinic Green:** Primary actions and metric bands use this authoritative mid-dark green.
- **Route Green:** Active route marks, confirmed events, borders, and secondary emphasis use the lighter operational green.

### Secondary

- **Attention Amber:** Review routes, approaching-target events, and exception cues use amber.
- **Critical Red:** Rejected, over-target, danger-action, and stop-state treatments use red.

### Neutral

- **Cream Paper:** The application foundation and grid canvas.
- **Raised Paper:** Workboards, selected navigation, decision summaries, and input fields.
- **Paper Edge:** Processing badges, scrollbar tracks, and soft separators.
- **Operational Ink:** Default text on light surfaces.
- **Muted Ink:** Supporting copy, metadata, and non-primary labels.
- **Hairline Rule:** Tables, stage boundaries, and grouped content rely on the translucent green rule.

### Named Rules

**The Route Color Rule.** Green shows the normal administrative route; amber and red are reserved for states that require attention or intervention.

**The Paper-and-Band Rule.** Use cream for work and deep green for orientation, headers, metrics, and consequential decisions.

## Typography

**Display Font:** Barlow Condensed (with sans-serif fallback)

**Body Font:** Source Sans 3 (with sans-serif fallback)

**Character:** Barlow Condensed behaves like clinic room signage: compact, direct, and visible across a busy floor. Source Sans 3 carries instructions, evidence, metadata, and controls with approachable clarity.

### Hierarchy

- **Display** (700, fluid 2.7rem–5.4rem, 0.86 line-height): Large page titles; uppercase with tightly balanced line breaks.
- **Headline** (700, 2rem, 1 line-height): Workboard, decision, result, and activity headings; usually uppercase.
- **Title** (700, around 1.2rem–1.65rem, compact line-height): Ticket identifiers, phase names, list headers, and local panel titles.
- **Body** (400, 1rem, 1.5 line-height): Operational descriptions and explanatory content; longer blocks are constrained to roughly 68 characters.
- **Label** (700, 0.75rem–0.84rem): Status, source, metric, field, and route labels. Condensed column labels may be uppercase with wider tracking.

### Named Rules

**The Room-Sign Rule.** Use condensed uppercase type for orientation and operational hierarchy, not for paragraphs or recovery instructions.

**The Plain-Language Rule.** Supporting copy remains sentence case, short, and explicit about the person, state, or next action.

## Layout

The shared package owns the cream grid canvas, type, focus treatment, reduced-motion behavior, and reusable buttons, status badges, page headers, and loading boards. Each application owns its shell and workflow compositions; shared visual language does not mean a shared navigation frame.

The patient application is mobile-first. Its focused deep-green header is 82px on wider screens and 68px below 620px; its main canvas uses fluid 18px–72px gutters. The pre-arrival workspace is capped at 1320px, uses an asymmetric two-column composition on wide screens, and becomes one column at 900px. Below 620px, validation remains a semantic table in markup but is visually re-composed into bordered per-field blocks: the row header stays beside stacked booking-value and validation cells, repeated `data-label` text replaces the visually hidden column header, and the state remains explicit text plus icon rather than color alone.

The nurse application is desktop/tablet-first. It uses a fixed 230px deep-green navigation rail and a flexible main canvas with 34px top padding, fluid horizontal gutters, and surface-specific content widths between 1280px and 1480px. The 32px background grid aligns the visual world without forcing every component onto a rigid card grid.

Operational boards use fixed semantic columns and hairline cell divisions. Metric tiles form one continuous band, patient phases remain visibly grouped, and major exception workspaces use asymmetric split panes. Common gaps cluster around 10px, 18px, 24px, and 28px; major surface padding ranges from 24px to 48px.

At 1180px the nurse metric rail wraps and the full patient board can scroll horizontally. At 900px the nurse rail becomes a 72px bottom navigation bar with a 58px mobile header. At 760px and below the nurse queue board is re-composed into ticket, status, stage, wait, and route blocks instead of merely shrinking the desktop table. Nurse split workspaces stack between 860px and 980px, and dense tables retain horizontal scrolling when their column meaning must be preserved.

### Named Rules

**The Route-Before-Decoration Rule.** Grid lines, dividers, columns, and bands must clarify patient or staff movement through the system.

**The Responsive Recomposition Rule.** On narrow screens, preserve state and route hierarchy by changing the grid structure; do not collapse operational data into an undifferentiated card stack.

**The Shell Boundary Rule.** Share tokens and true primitives across applications, but keep patient navigation and mobile validation in the patient shell and staff navigation, authentication framing, and dense operational boards in the nurse shell.

## Elevation & Depth

The system is flat and tonal by default. Depth comes first from the cream hierarchy, dark-green bands, and one-pixel rules. Major workboards and split workspaces receive one restrained ambient surface shadow, while the primary button uses a smaller green-tinted action shadow. Hover lift is limited to actionable controls.

### Shadow Vocabulary

- **Ambient Work Surface** (`0 18px 45px rgba(40, 55, 46, 0.12)`): Patient boards, review workspaces, kiosk workspaces, pre-arrival workspaces, and allocation panels.
- **Primary Action** (`0 8px 18px rgba(23, 71, 58, 0.22)`): Default primary button; strengthens to `0 11px 24px rgba(23, 71, 58, 0.25)` on hover.
- **Outlined Action** (`inset 0 0 0 1px var(--green-700)`): Secondary buttons use an inset route-colored rule instead of ambient lift.

### Named Rules

**The Tonal-First Rule.** Establish hierarchy with fields, bands, and rules before adding shadow.

**The One-Level Lift Rule.** Ambient elevation belongs to complete work surfaces, not to every row, metric, or content fragment.

## Shapes

The overall form language is rectilinear and board-like. Workboards, metric bands, table cells, alert bands, and panels have square corners. Controls use gently rounded 8px corners; large choices use 12px corners; status badges and counters use full pills or circles. The single expressive silhouette is the brand mark, a circular form with one squared-soft corner.

### Named Rules

**The Board-and-Control Rule.** Keep operational surfaces square; reserve rounded geometry for things a person selects, edits, or reads as a compact state.

## Components

### Buttons

- **Shape:** Gently rounded controls (8px) with a 44px minimum height and 18px horizontal padding.
- **Primary:** Clinic green with raised-paper text and a restrained green action shadow.
- **Hover / Focus:** Hover moves upward by 1px and deepens the color or shadow over 180ms ease-out. The global keyboard focus is a 3px amber outline with a 3px offset.
- **Secondary:** Raised paper with an inset route-green border; hover fills with the pale green surface.
- **Quiet:** Transparent green text; used for a lower-emphasis alternative beside a consequential action.
- **Danger:** Critical red with white text.
- **Disabled:** Retains structure at 52% opacity and removes the pointer affordance.

### Chips

- **Style:** Compact 7px-by-10px full pills with a 0.78rem bold label and a 14px state icon.
- **State:** Ready/approved/on-track use pale green, processing/pending use paper edge, review/approaching use pale amber, and rejected/over-target use pale red. Text and icon make state legible without color alone.

### Cards / Containers

- **Corner Style:** Square at the work-surface level; tonal choice controls are the rounded exception.
- **Background:** Raised paper for main boards, pale green for phase bands or supporting result panels, and deep green for metrics or consequential decisions.
- **Shadow Strategy:** Only complete work surfaces receive ambient elevation.
- **Border:** One-pixel translucent green rules divide columns, stages, evidence cells, and grouped records.
- **Internal Padding:** Dense rows use 12px–20px; work surfaces use 24px–48px.

### Inputs / Fields

- **Style:** Raised-paper background, 1px muted-green border, 8px corners, 48px minimum height, and 14px horizontal padding.
- **Focus:** The global amber focus outline remains visible outside the border.
- **Error / Disabled:** Error bands use the critical surface with dark red text; disabled form groups retain their layout and block interaction.
- **Upload fields:** Use a pale-green or cream-paper field, clear file constraints, and a dashed route-green boundary where the whole drop/selection area is represented.

### Navigation

Patient navigation is a focused deep-green registration header with the Epicenter mark, the `Patient registration` destination label, and an explicit synthetic-journey marker. It does not inherit staff routes or a bottom navigation bar.

Nurse navigation is a fixed deep-green rail with a cream active route, green-tinted inactive labels, 19px line icons, and 46px minimum row height. Below 900px it becomes a four-route bottom bar with icon-over-label items, paired with a compact deep-green header that keeps the product and synthetic-data marker visible.

### Registration Validation

The patient registration comparison uses native table markup with a hidden explanatory caption, scoped column and row headers, and plain-language validation states. Below 620px, CSS changes its visual layout: each field becomes a two-column block, the booking value and validation result carry visible generated labels, and the caption and scoped-header markup remain intact.

### Patient Readiness Board

The signature board combines a deep-green column header, pale-green phase labels, square ticket rows, persistent `Q-*` identifiers, route/stage/wait/status columns, and a short colored route mark at each row edge. Mobile layouts preserve the same information as bordered semantic blocks.

### Progress Steps

The kiosk uses a four-stage deep-green route band. Each step has a numbered or checked circular marker; the current step reverses onto raised paper, while completed steps use route green. The route remains textual as well as visual.

### Evidence Grid

Review evidence appears in a two-column hairline grid with source notes under each value. A failed evidence cell uses the attention surface and explicit failure text; at narrow widths the grid becomes a single column.

## Do's and Don'ts

### Do:

- **Do** frame every workflow with an explicit route, stage, state, or next-action marker.
- **Do** preserve cream paper, the 32px grid, and deep-green bands as the dominant material system.
- **Do** use hairline rules and fixed alignment to make dense operational data scannable.
- **Do** pair every colored status with readable text and an icon or shape cue.
- **Do** re-compose dense boards on mobile while keeping ticket, route, stage, wait, and status visible.
- **Do** keep patient and nurse shells separate while importing shared tokens and primitives from the shared package.
- **Do** reserve the strongest deep-green field for orientation and decisions that deserve staff attention.

### Don't:

- **Don't** turn the interface into a generic floating-card dashboard; the implemented system is a connected wayfinding board.
- **Don't** use amber or red as decorative accents; they indicate attention, exception, rejection, or escalation.
- **Don't** round major boards, metric bands, evidence tables, or allocation surfaces.
- **Don't** add shadows to individual rows and content fragments when a tonal field or rule communicates the hierarchy.
- **Don't** turn the patient flow into a scaled-down staff dashboard or expose nurse navigation in the patient shell.
- **Don't** use condensed uppercase typography for long instructions or evidence explanations.
- **Don't** hide human confirmation, administrative-only scope, or the persistent patient ticket behind color-only shorthand.
