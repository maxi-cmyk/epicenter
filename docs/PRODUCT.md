# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Two Next.js applications (patient on port 3000, nurse on port 3001) and one FastAPI backend. Clerk authenticates both panels; FastAPI authorizes every request. Supabase Postgres is the persistence target when credentials are present (`EPICENTER_PERSISTENCE_MODE=auto`); otherwise the API uses an in-memory synthetic fixture. Vercel and Railway remain the documented deployment targets.

## Users

- Registration staff managing booked and walk-in administrative readiness from the nurse Today board.
- Trained nurses supervising clinic walk-in kiosks and applying the clinic's physical red-flag protocol.
- Operations leads reviewing queue pressure and approving or rejecting constrained counter-allocation recommendations.
- Patients completing pre-arrival document submission, questionnaire, queue, mocked payment, and records on the patient panel.

## Product Purpose

Epicenter turns varied outpatient coverage documents into evidence-backed structured facts, deterministic administrative readiness, and one persistent patient ticket. Success means routine cases move quickly, exceptions remain visible and safe, booked patients can be ready before arrival, and walk-ins receive faster on-site processing without being forced to queue twice.

## Positioning

Epicenter is a focused outpatient administrative-readiness and operations layer, not an EHR. Its differentiator is the closed loop from document evidence to staff-confirmed readiness, targeted intervention, quantified exception workload, constrained human-approved allocation, and measured outcome.

## Operating Context

The product is used at outpatient clinics during busy arrival periods. Scheduled patients complete a conceptual Singpass/Myinfo booking pre-check and submit coverage documents before arrival. Walk-ins register and capture documents at a nurse-supervised clinic kiosk. Staff work from the Today board (Incoming / Ongoing / Finished), a gated per-ticket task flow, kiosk, Database, Audit, and Simulator. All demonstrated people, events, documents, metrics, and integrations are synthetic unless explicitly stated otherwise.

## Capabilities and Constraints

- One visit always has one `Q-*` ticket and one original ordering timestamp.
- Walk-ins always go to slow counters (`S1`–`S4`). Only booked patients with no outstanding issues (`intake_type` booked and `readiness_state` ready) go to fast counters (`F1`–`F2`).
- The assigned queue number and counter are visible on both the patient queue screen and the nurse dashboard.
- LLM-style extraction may structure document facts, but deterministic gates and versioned rules decide whether a case can proceed to staff confirmation.
- Staff confirm every determination through gated task steps. Ambiguous, missing, expired, unusual, or failed inputs stay on the same ticket rather than being guessed.
- Clinical urgency is never inferred by Epicenter. A trained nurse applies the clinic's physical red-flag protocol at first contact and may interrupt administrative intake at any time.
- Identity and e-card checks remain manual and in person. Singpass/Myinfo validation and kiosk intake never replace them.
- Allocation advice is explainable, constrained to qualified resources, expiring, and human-approved.
- The nurse Simulator replays synthetic clinic-day scenarios in `frontend/nurse/lib/simulation/` and must not write operational patient or queue tables.
- Live Singpass, payment, EHR, insurer, and TPA integrations are not claimed by the local demo.
- OpenAI is the development/application LLM; the deployed custom MCP contract must remain compatible with Copilot Studio without making Copilot a local runtime dependency.
- Only the custom Operations and Insurance Format Registry MCPs are used. They must run from OpenAI during development and remain connectable from Copilot Studio after deployment.
- The native dashboard is the P0 analytics surface. Power BI/Fabric is a deferred, aggregate-only scalability option without a Power BI MCP dependency, not a source of truth or core-demo dependency.

## Brand Commitments

- Product name: Epicenter.
- User-specified visual direction: cream foundation with green accents and a hospital/clinic character.
- Voice: calm, precise, operational, conservative, and explicit about human responsibility and synthetic assumptions.
- Impeccable is the required frontend design quality system.

## Evidence on Hand

- Product and workflow requirements: `PRD.md`.
- Approved stack and repository layout: `techStack.md`.
- Clinic as-is process and implemented Epicenter path: `workflow.md`.
- Local run, Clerk test accounts, and verification: repository `README.md`.
- No real clinic outcomes, production credentials, live patient data, or approved brand assets are present and none may be fabricated.

## Product Principles

1. Collapse reading into confirmation without hiding the human decision.
2. Fail visibly and conservatively; first-pass automation below 100% is intentional.
3. Preserve one patient journey and the original waiting age.
4. Separate administrative readiness from clinical urgency.
5. Recommend operational action with evidence; never command it silently.

## Accessibility & Inclusion

The staff interface must support desktop and tablet use; patient and kiosk flows must remain usable on touch devices. Status must never rely on colour alone. Controls require visible focus, sufficient targets and contrast, plain-language recovery states, reduced-motion support, keyboard operation, and assistance paths for patients who cannot use a digital channel independently.
