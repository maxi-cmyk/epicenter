# Epicenter

Epicenter is a synthetic outpatient administrative-readiness demo. It turns varied coverage documents into evidence-backed readiness states, keeps every patient on one persistent ticket, and presents constrained operational recommendations for staff approval.

## Repository

- `frontend/` — Next.js staff operations, assisted review, supervised kiosk and patient pre-check interfaces, with an optional Clerk provider boundary.
- `backend/` — FastAPI domain services and Clerk JWT-protected HTTP API for readiness, kiosk check-in and allocation decisions.
- `docs/` — PRD, design, architecture, simulator, pitch and supporting research.

## Run locally

The app runs as three processes in three terminals: the patient screen, the
nurse/staff screen, and the backend API. Both frontend processes share one
Next.js codebase — `APP_ROLE` picks which routes each one serves and
redirects any other route, so the patient screen can't reach staff views
and vice versa. Plain `npm run dev` (no role set) still runs everything on
one process for quick local testing.

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
npm run dev:patient
```

Terminal 3 — nurse screen (port 3001, Readiness Board + Assisted Review + Walk-in kiosk):

```bash
cd frontend
npm run dev:nurse
```

Open `http://localhost:3000` for the patient screen and `http://localhost:3001` for the nurse screen. Both frontends use the local API when available and fall back to clearly labelled synthetic data when it is not.

## Provider and deployment boundaries

- **Database:** Supabase is the production persistence target. The initial migration and an idempotent seed now cover 300 synthetic registrations, 60 questionnaire submissions, and 9 synthetic medical documents. The current API still serves its deterministic in-memory workflow until the Supabase repository adapter is enabled.
- **Authentication:** Clerk wraps the frontend when `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is present. Outside demo mode, FastAPI verifies Clerk session tokens with the official Python SDK and `CLERK_SECRET_KEY`; `CLERK_JWT_KEY` is an optional networkless-verification optimization.
- **Frontend deployment:** create a Vercel project with `frontend/` as its root directory and set the frontend environment variables there.
- **Backend deployment:** create a Railway service with `backend/` as its root directory. `backend/railway.toml` defines the start command and health check; set `EPICENTER_DEMO_MODE=false`, provider credentials and the deployed `EPICENTER_FRONTEND_ORIGINS` (comma-separated; both the patient and nurse deployment URLs) in Railway.

The checked-in provider configuration is a deployment contract, not a claim that live Supabase, Clerk, Vercel or Railway resources have already been provisioned.

Sample-data provenance, identity reconciliation results, and local/hosted database commands are documented in [`docs/sample-data.md`](docs/sample-data.md).

## Verify

```bash
cd backend && .venv/bin/pytest -q && .venv/bin/ruff check app tests
cd frontend && npm test && npm run typecheck && npm run lint && npm run build
```

Local `.env` and `.env.local` files contain development-only configuration and are ignored. Copy the checked-in `.env.example` files when setting up another machine. No real patient data or live provider integration is included.
