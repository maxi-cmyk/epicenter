# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js frontend and FastAPI backend, selected from the repository's approved technical architecture. Vercel and Railway are the documented deployment targets; the local build uses in-memory synthetic data behind replaceable service adapters.

## Users

- Registration staff managing booked and walk-in administrative readiness.
- Trained nurses supervising clinic walk-in kiosks and applying the clinic's physical red-flag protocol.
- Operations leads reviewing queue pressure and approving or rejecting constrained counter-allocation recommendations.
- Patients completing pre-arrival document submission or supervised walk-in intake.

## Product Purpose

Epicenter turns varied outpatient coverage documents into evidence-backed structured facts, deterministic administrative readiness, and one persistent patient ticket. Success means routine cases move quickly, exceptions remain visible and safe, booked patients can be ready before arrival, and walk-ins receive faster on-site processing without being forced to queue twice.

## Positioning

Epicenter is a focused outpatient administrative-readiness and operations layer, not an EHR. Its differentiator is the closed loop from document evidence to staff-confirmed readiness, targeted intervention, quantified exception workload, constrained human-approved allocation, and measured outcome.

## Operating Context

The product is used at outpatient clinics during busy arrival periods. Scheduled patients complete a conceptual Singpass/Myinfo booking pre-check and submit coverage documents before arrival. Walk-ins register and capture documents at a nurse-supervised clinic kiosk. Staff work from queue, review, records, billing, audit, and counter-allocation views. All demonstrated people, events, documents, metrics, and integrations are synthetic unless explicitly stated otherwise.

## Capabilities and Constraints

- One visit always has one `Q-*` ticket and one original ordering timestamp.
- LLM-style extraction may structure document facts, but deterministic gates and versioned rules decide whether a case can proceed to staff confirmation.
- Staff confirm every determination. Ambiguous, missing, expired, unusual, or failed inputs route to review rather than being guessed.
- Clinical urgency is never inferred by Epicenter. A trained nurse applies the clinic's physical red-flag protocol at first contact and may interrupt administrative intake at any time.
- Identity and e-card checks remain manual and in person. Singpass/Myinfo validation and kiosk intake never replace them.
- Allocation advice is explainable, constrained to qualified resources, expiring, and human-approved.
- Live Singpass, Clerk, Supabase, OpenAI, messaging, payment, EHR, insurer, and TPA integrations are not claimed by the local demo.

## Brand Commitments

- Product name: Epicenter.
- User-specified visual direction: cream foundation with green accents and a hospital/clinic character.
- Voice: calm, precise, operational, conservative, and explicit about human responsibility and synthetic assumptions.
- Impeccable is the required frontend design quality system.

## Evidence on Hand

- Product and workflow requirements: `PRD.md`.
- Staff and patient screen contracts plus data model: `design.md`.
- Approved stack and repository layout: `techStack.md`.
- Simulator behavior and invariants: `simulator.md`.
- Judge-facing prioritization and demo narrative: `pitch.md`.
- No real clinic outcomes, production credentials, live patient data, or approved brand assets are present and none may be fabricated.

## Product Principles

1. Collapse reading into confirmation without hiding the human decision.
2. Fail visibly and conservatively; first-pass automation below 100% is intentional.
3. Preserve one patient journey and the original waiting age.
4. Separate administrative readiness from clinical urgency.
5. Recommend operational action with evidence; never command it silently.

## Accessibility & Inclusion

The staff interface must support desktop and tablet use; patient and kiosk flows must remain usable on touch devices. Status must never rely on colour alone. Controls require visible focus, sufficient targets and contrast, plain-language recovery states, reduced-motion support, keyboard operation, and assistance paths for patients who cannot use a digital channel independently.
