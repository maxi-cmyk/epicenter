# Epicenter

Epicenter is a synthetic outpatient administrative-readiness demo. It turns varied coverage documents into evidence-backed readiness states, keeps every patient on one persistent ticket, and presents constrained operational recommendations for staff approval.

## Repository

- `frontend/patient/` — independently built Next.js patient registration and pre-arrival experience.
- `frontend/nurse/` — independently built Next.js staff operations, assisted review and supervised kiosk experience with Clerk authentication.
- `frontend/shared/` — generated data contracts, design tokens and safe presentation primitives shared by both apps.
- `backend/` — FastAPI domain services and Clerk JWT-protected HTTP API for readiness, kiosk check-in and allocation decisions.
- `docs/` — PRD, design, architecture, simulator, pitch and supporting research.

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

Terminal 2 — patient screen (port 3000, Patient Pre-check only):

```bash
cd frontend
npm install
npm run patient
```

Terminal 3 — nurse screen (port 3001, Readiness Board + Assisted Review + Walk-in kiosk):

```bash
cd frontend
npm run nurse
```

Open `http://localhost:3000` for the patient screen and `http://localhost:3001` for the nurse screen. Both frontends use the same local API. The nurse board can show its clearly labelled synthetic fallback when the API is unavailable; patient submissions fail visibly, preserve the selection, and offer retry rather than pretending the action completed.

The two commands are independent: either app can run by itself, and starting one does not start or require the other frontend process.

FastAPI is the contract authority for both apps. After changing backend request or response models, regenerate and verify the checked-in TypeScript contracts:

```bash
cd frontend
npm run contracts:generate
npm run contracts:check
```

## Provider and deployment boundaries

- **Database:** Supabase is the production persistence target. The initial migration and an idempotent seed now cover 300 synthetic registrations, 60 questionnaire submissions, and 9 synthetic medical documents. The current API still serves its deterministic in-memory workflow until the Supabase repository adapter is enabled.
- **Authentication:** Clerk wraps the frontend when `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is present. Outside demo mode, FastAPI verifies Clerk session tokens with the official Python SDK and `CLERK_SECRET_KEY`; `CLERK_JWT_KEY` is an optional networkless-verification optimization.
- **Patient demo boundary:** the synthetic pre-arrival action posts to the same FastAPI service and returns `under_review` pending staff confirmation. Its unauthenticated fixture endpoint is available only in demo mode and fails closed until a production patient-token adapter is configured.
- **Frontend deployment:** create one Vercel project rooted at `frontend/patient/` and another rooted at `frontend/nurse/`. Set each app's browser-safe environment variables independently; both use the same Railway API URL.
- **Backend deployment:** create a Railway service with `backend/` as its root directory. `backend/railway.toml` defines the start command and health check; set `EPICENTER_DEMO_MODE=false`, provider credentials and the deployed `EPICENTER_FRONTEND_ORIGINS` (comma-separated; both the patient and nurse deployment URLs) in Railway.

The checked-in provider configuration is a deployment contract, not a claim that live Supabase, Clerk, Vercel or Railway resources have already been provisioned.

Sample-data provenance, identity reconciliation results, and local/hosted database commands are documented in [`docs/sample-data.md`](docs/sample-data.md).

## Verify

```bash
cd backend && .venv/bin/pytest -q && .venv/bin/ruff check app tests
cd frontend && npm test && npm run typecheck && npm run lint && npm run build
```

Local `.env` and `.env.local` files contain development-only configuration and are ignored. Copy `frontend/patient/.env.example` and `frontend/nurse/.env.example` into each app when setting up another machine. No real patient data or live provider integration is included.
