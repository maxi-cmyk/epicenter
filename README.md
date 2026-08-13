# Epicenter

Epicenter is a synthetic outpatient administrative-readiness demo. It turns varied coverage documents into evidence-backed readiness states, keeps every patient on one persistent ticket, and routes that ticket to a labelled registration counter. OpenAI is the application LLM during development and is accessed only through the backend; the deployed custom MCP endpoints remain compatible with Copilot Studio as required by the publication brief.

## What the demo shows

Two independently built Next.js applications share one FastAPI contract:

| App | Port | What it covers |
| --- | --- | --- |
| Patient | 3000 | Home, coverage upload, questionnaire, queue (number + assigned counter), payment, records |
| Nurse | 3001 | Today board (Incoming / Ongoing / Finished), gated registration tasks, walk-in kiosk, Database, Audit, Simulator |

**Registration routing.** Walk-ins always go to slow counters (`S1`–`S4`). Only booked patients with no outstanding issues (`intake_type` `booked` and `readiness_state` `ready`) go to fast counters (`F1`–`F2`). The assigned queue number and counter are visible on both the patient queue screen and the nurse dashboard.

**Nurse task flow.** Opening a ticket walks through gated steps: Identity & e-card → Forms guidance → Forms review → Confirm package (when documents are on file) → Billing & queue → Summary. Exceptions stay on the same ticket. See [`docs/workflow.md`](docs/workflow.md).

**Simulator.** The nurse Simulator tab replays a deterministic clinic-day model (`serial_baseline`, `single_ticket`, `dynamic_allocation`) with playback controls. The engine lives in `frontend/nurse/lib/simulation/` and must not write operational patient or queue tables.

## Repository

- `frontend/patient/` — independently built Next.js patient registration and pre-arrival experience with public patient-only Clerk enrollment.
- `frontend/nurse/` — independently built Next.js staff operations, gated task flow, walk-in kiosk, Database, Audit, and Simulator, with Clerk authentication.
- `frontend/shared/` — generated data contracts, design tokens and safe presentation primitives shared by both apps.
- `backend/` — FastAPI domain services, Clerk JWT-protected HTTP API, and the server-side OpenAI integration for document intelligence and reviewed assistant tools.
- `docs/` — product, requirements, stack, and clinic workflow.

See [`docs/PRODUCT.md`](docs/PRODUCT.md), [`docs/PRD.md`](docs/PRD.md), [`docs/techStack.md`](docs/techStack.md), and [`docs/workflow.md`](docs/workflow.md).

## OpenAI configuration

OpenAI requests originate from FastAPI or the private worker, never from either browser application. Supply the API key only through an ignored local backend environment file or the Railway secret manager:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

Do not create a `NEXT_PUBLIC_OPENAI_API_KEY` variable, commit the key, paste it into documentation, or return it through an API/tool response. The exact model is pinned only after the document fixtures and assistant tasks are evaluated for correctness, latency, and cost. Normal patient/nurse workflows, the native dashboard, and the deterministic simulator must continue to work when OpenAI is unavailable.

Copilot Studio and Power BI are not required for local development. Epicenter uses only its custom Operations and Insurance Format Registry MCP servers. Their Railway endpoints use client-neutral Streamable HTTP so the same reviewed tools can be connected to Copilot Studio at deployment/publication time without forking the business logic. Microsoft-hosted MCPs are not dependencies. The built-in Next.js dashboard remains the P0 analytics surface.

## Run locally

The app runs as three processes in three terminals: the patient app, the
nurse app, and the backend API. The two Next.js apps are separate workspace
packages with separate route trees, builds, environment validation and Vercel
roots. They share only the backend contract and safe presentation primitives;
patient routes are not compiled into the nurse deployment and nurse routes are
not compiled into the patient deployment.

Terminal 1 — backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\uvicorn app.main:app --reload
```

With `EPICENTER_SUPABASE_URL` and `EPICENTER_SUPABASE_SECRET_KEY` present,
`EPICENTER_PERSISTENCE_MODE=auto` makes the local FastAPI process use the
hosted Supabase project. Set `EPICENTER_PERSISTENCE_MODE=demo` when you want an
isolated in-memory run. Set it to `supabase` to fail closed if the server
credentials are missing.

Terminal 2 — patient screen (port 3000):

```bash
cd frontend
npm install
npm run patient
```

Terminal 3 — nurse screen (port 3001):

```bash
cd frontend
npm run nurse
```

Open `http://localhost:3000` for the patient screen and `http://localhost:3001` for the nurse screen. Both frontends use the same local API. The nurse board can show its clearly labelled synthetic fallback when the API is unavailable; patient submissions fail visibly, preserve the selection, and offer retry rather than pretending the action completed.

The two commands are independent: either app can run by itself, and starting one does not start or require the other frontend process.

Walk-in kiosk (nurse app): `http://localhost:3001/kiosk`.

## Sign-in and account roles

Clerk proves who is signed in; FastAPI and Supabase decide what that identity may access. Patient and nurse accounts use separate enrollment paths even when both panels use the same Clerk application.

| Flow | Where | How access is granted |
| --- | --- | --- |
| Patient | `http://localhost:3000` | The patient may create an account or sign in. FastAPI verifies the Clerk session and maps its immutable `sub` to one configured synthetic `patient_accounts` record. There is no role selector. |
| Nurse/staff | `http://localhost:3001` | Sign-in only. A clinic administrator creates the Clerk user and attaches its Clerk User ID to one active `staff_accounts` record with the required clinic and role. Public nurse enrollment is never enabled. |
| Local demo bypass | FastAPI with `EPICENTER_DEMO_MODE=true` | Uses synthetic principals so local fixture workflows and automated tests can run without provider sessions. This does not prove real patient/nurse isolation. |
| Clerk CLI developer | Terminal | `clerk auth login` authenticates a developer to manage Clerk applications. It does not sign a patient or nurse into Epicenter. |

### Patient sign-up and sign-in

1. Open the patient panel and choose **Create patient account** or **Sign in**.
2. The frontend sends the Clerk session token to `POST /api/v1/patient/account/activate`.
3. FastAPI creates or resolves exactly one mapping to `EPICENTER_PATIENT_DEMO_SOURCE_RECORD_KEY`.
4. Registration and pre-arrival requests are restricted to appointments belonging to that mapped patient.

Email verifies the Clerk identity but never grants a staff role. Browser metadata, URL parameters, and editable Clerk metadata are not authorization sources.

### Nurse sign-in

The nurse panel never offers public sign-up. The hosted development environment has two directly provisioned test nurses:

| Staff fixture | Clerk development email | Role |
| --- | --- | --- |
| Nurse Noor (`staff_noor`) | `nurse.noor+clerk_test@example.com` | Registration nurse |
| Nur Aisyah (`staff_aisyah`) | `nurse.aisyah+clerk_test@example.com` | Operations administrator |

To sign in locally:

1. Open `http://localhost:3001` and enter one of the test emails above.
2. Request the email verification code. Clerk does not send mail for a `+clerk_test` address.
3. Enter the development test code `424242`.
4. Clerk issues the browser session; FastAPI then resolves the Clerk User ID to the mapped staff row and applies its clinic and role.

These addresses and the fixed code work only with Clerk test mode and are for local/development use. They are fake inboxes, so do not use an invitation flow that depends on receiving mail. The users were created directly with generated initial passwords; normal local sign-in uses the email-code flow above. Use real, administrator-controlled addresses and separately delivered credentials for production or judging.

For another staff user, create the user through the Clerk Dashboard or CLI, then copy its Clerk User ID (`user_...`) into the intended staff record:

```sql
update public.staff_accounts
set clerk_user_id = 'user_REPLACE_ME',
    active = true
where id = 'staff_noor';
```

Keep provider-specific Clerk User IDs out of the seed SQL and repository. Re-running `supabase/operational_seed.sql` preserves existing mappings because its staff upsert does not overwrite `clerk_user_id`.

On every protected request, FastAPI requires a valid Clerk session and exactly one active staff mapping for `EPICENTER_CLINIC_ID`. Patient, unmapped, disabled, and wrong-clinic identities receive `403` instead of staff access. An email address alone never grants a nurse role.

Every currently implemented staff mutation also requires a recent Clerk verification. If the strongest configured factor is older than ten minutes, Clerk opens its verification prompt and automatically retries the action after verification succeeds. Database Update and Delete require password reverification in the UI. In the development instance, choose **Use another method → Email code** when needed and enter `424242` for a `+clerk_test` account.

### Switching from demo to real local sessions

Use `EPICENTER_DEMO_MODE=true` only for fixture-only flows and automated tests that intentionally bypass provider sessions. The ignored local `backend/.env` now uses `EPICENTER_DEMO_MODE=false` because the development nurse mappings exist. In real-session mode:

1. Keep both local frontend origins in `EPICENTER_FRONTEND_ORIGINS`.
2. Start all three processes again after changing authentication settings.
3. A patient signs up publicly and is attached to the configured synthetic patient only after FastAPI verifies the Clerk session.
4. A nurse signs in with a pre-provisioned identity and receives only the clinic-scoped role stored in `staff_accounts`.
5. Test patient-to-nurse denial, nurse sign-in, unmapped/disabled staff denial, and audit attribution before deployment.

The repeatable development-provider check covers those paths, the Clerk verification prompt, and a real audited Supabase mutation:

```bash
cd frontend
npm run test:auth-live
```

It creates and removes a temporary patient, temporarily disables and restores a nurse mapping, and restores the ticket used for its mutation check. It requires the ignored local Clerk and backend environment files and must not be run against production.

The browser receives only `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`. `CLERK_SECRET_KEY`, the optional `CLERK_JWT_KEY`, and the Supabase secret remain backend-only.

### Clerk CLI login

The Clerk CLI is optional developer tooling:

```bash
clerk --version
clerk doctor --json
clerk users list --instance dev --email-address nurse.noor+clerk_test@example.com --json
```

`clerk doctor --json` verifies the developer login and linked Clerk application. CLI login is separate from both application sign-in flows: it authorizes account administration, not access to either Epicenter panel. Preview user mutations with `--dry-run`, target `--instance dev` explicitly, and do not commit CLI sessions, patient credentials, nurse credentials, Clerk User IDs, generated passwords, or provider secrets.

FastAPI is the contract authority for both apps. After changing backend request or response models, regenerate and verify the checked-in TypeScript contracts:

```bash
cd frontend
npm run contracts:generate
npm run contracts:check
```

## Provider and deployment boundaries

- **Database:** Supabase is the shared persistence target. The migrations and idempotent seeds cover the raw fixtures plus clinics, appointments, the one-ticket queue, review cases, counters, staff availability, human-approved allocation, operational/audit events, configuration releases, and simulator snapshots. The local FastAPI process automatically selects the server-only Supabase adapter when its URL and secret key are configured; Railway is not required for local use.
- **Authentication:** Clerk wraps both frontends when `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is present. Outside demo mode, FastAPI verifies Clerk session tokens with the official Python SDK, maps patients through `patient_accounts`, and maps staff through active clinic-scoped `staff_accounts`. `CLERK_JWT_KEY` is an optional networkless-verification optimization.
- **Patient demo boundary:** each verified patient account is attached only to the configured synthetic scenario. Pre-arrival submissions return a patient-safe outcome pending any required staff confirmation; privileged operational data remains behind FastAPI.
- **Frontend deployment:** create one Vercel project rooted at `frontend/patient/` and another rooted at `frontend/nurse/`. Set each app's browser-safe environment variables independently; both use the same Railway API URL.
- **Backend deployment:** create a Railway service with `backend/` as its root directory. `backend/railway.toml` defines the start command and health check; set `EPICENTER_DEMO_MODE=false`, provider credentials and the deployed `EPICENTER_FRONTEND_ORIGINS` (comma-separated; both the patient and nurse deployment URLs) in Railway.
- **MCP publication compatibility:** expose the reviewed Operations and Insurance Format Registry servers over public HTTPS Streamable HTTP, verify tool discovery and a read-only synthetic call in Copilot Studio, and keep licensing/publication as an explicit manual release gate.
- **Analytics scaling:** use the native dashboard for development and the core demo. Consider Power BI/Fabric only later through a reconciled de-identified aggregate projection; it is never the operational source of truth.

The checked-in provider configuration is a deployment contract, not a claim that live Supabase, Clerk, Vercel or Railway resources have already been provisioned.

## Verify

```bash
cd backend && .venv/bin/pytest -q && .venv/bin/ruff check app tests
cd frontend && npm test && npm run typecheck && npm run lint && npm run build
```

On Windows PowerShell:

```powershell
cd backend; .\.venv\Scripts\pytest -q; .\.venv\Scripts\ruff check app tests
cd frontend; npm test; npm run typecheck; npm run lint; npm run build
```

Local `.env` and `.env.local` files contain development-only configuration and are ignored. Copy `frontend/patient/.env.example` and `frontend/nurse/.env.example` into each app when setting up another machine. No real patient data or live provider integration is included.
