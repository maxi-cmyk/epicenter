# Epicenter release and deployment runbook

This is the execution checklist for Tasks 11 and 12. Complete it in order. Commands labelled **local** are safe repository checks; steps labelled **manual** change a hosted provider.

## 1. Local release gate

1. **Manual prerequisite:** install the [Supabase CLI](https://supabase.com/docs/guides/local-development/cli/getting-started) and start Docker Desktop. The CLI and a running Docker daemon are not currently available on this machine.
2. From the repository root, rebuild an empty local database from migrations and seeds:

   ```bash
   supabase start
   supabase db reset
   ```

3. Run the complete local gate:

   ```bash
   cd backend
   .venv/bin/pytest -q
   .venv/bin/ruff check app tests scripts
   cd ../frontend
   npm test
   npm run typecheck
   npm run lint
   npm run contracts:check
   npm run build
   ```

4. Run the desktop browser journeys and visual capture while the backend and all three frontends are running:

   ```bash
   cd frontend
   npm run qa:visual
   ```

Do not run `npm run test:auth-live` against production. It creates a temporary Clerk patient, disables and restores a nurse mapping, and mutates then restores a ticket. Run it only against the development Clerk and synthetic Supabase project.

## 2. Reconcile and deploy Supabase

These steps are **manual** because they authenticate to and modify the hosted Supabase project.

1. Log in and link the intended project:

   ```bash
   supabase login
   supabase link --project-ref YOUR_PROJECT_REF
   supabase migration list
   ```

2. Stop if local and remote migration histories do not agree. Some SQL was previously run through the SQL editor, which can change the schema without recording a CLI migration. Compare the remote schema with each matching migration before using `supabase migration repair`; never mark an unapplied migration as applied merely to clear the warning.
3. Preview, review, and then push migrations using the options shown by the installed CLI:

   ```bash
   supabase db push --dry-run
   supabase db push
   ```

4. Load `supabase/seed.sql` and `supabase/operational_seed.sql` only into the approved synthetic demo project. Never seed a real patient project.
5. Run `supabase/verify_operational.sql` in the SQL editor and save the output as release evidence.
6. Open **Database → Security Advisor** and **Database → Performance Advisor** in the Supabase Dashboard. Resolve applicable errors and document any accepted demo-only warnings. Confirm RLS on exposed tables, SSL enforcement, MFA for the organization, and appropriate network restrictions before public deployment. See Supabase's [production checklist](https://supabase.com/docs/guides/deployment/going-into-prod).

## 3. Configure Clerk

These steps are **manual** because they manage external identities and production credentials.

1. Verify the local CLI session:

   ```bash
   clerk doctor --json
   ```

   This could not be completed automatically because the privileged CLI check was blocked by the current tool usage limit.
2. Decide whether judging uses the Clerk development instance or a production instance. Production is recommended for public URLs; development-only `+clerk_test` addresses and code `424242` must not be treated as production credentials.
3. In Clerk, add the two exact Vercel origins and the deployed domains. Store `CLERK_SECRET_KEY` only in Railway and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` only in the relevant Vercel projects.
4. Provision nurse demo identities administratively, then map their immutable Clerk User IDs to active, clinic-scoped `staff_accounts` rows. Do not enable public staff signup or place those IDs in committed seed files.
5. Distribute judge credentials outside Git, Vercel logs, screenshots, and project documentation.

## 4. Deploy Railway

Create two services from the same repository. This is **manual**.

| Service | Root directory | Config/start command | Public domain |
| --- | --- | --- | --- |
| API + MCP | `/backend` | Config file `/backend/railway.toml` | Yes |
| Worker | `/backend` | Override start command with `python -m worker` | No |

Configure the required Railway variables without committing their values:

- `EPICENTER_ENVIRONMENT=production`
- `EPICENTER_DEMO_MODE=false`
- `EPICENTER_PERSISTENCE_MODE=supabase`
- `EPICENTER_FRONTEND_ORIGINS` containing the exact patient and nurse Vercel origins
- Supabase URL, publishable key, and backend-only secret key
- Clerk secret key and optional JWT key
- server-only OpenAI key and reviewed model identifiers
- a long, random, revocable `EPICENTER_MCP_API_KEY`

The API service must pass `/healthz`. The worker should remain private. After deployment, confirm that Railway's displayed source commit matches `git rev-parse HEAD`.

OpenAI calls already use `store=False`; keep the key server-side and confirm the deployed model names rather than relying on defaults. Current OpenAI retention behavior is documented in the [API data controls guide](https://developers.openai.com/api/docs/guides/your-data#default-usage-policies-by-endpoint).

## 5. Deploy three Vercel projects

Create one project per app, as recommended for a [Vercel monorepo](https://vercel.com/docs/monorepos). This is **manual**.

| Project | Root directory | Required browser variables |
| --- | --- | --- |
| Patient | `frontend/patient` | API base URL, Clerk publishable key, browser-safe Supabase values |
| Nurse | `frontend/nurse` | API base URL, Clerk publishable key, browser-safe Supabase values |

Set `NEXT_PUBLIC_API_BASE_URL` to `https://YOUR_RAILWAY_DOMAIN/api/v1`. Never put a Clerk secret, Supabase secret/service-role key, OpenAI key, or MCP key in a `NEXT_PUBLIC_*` variable. Redeploy after changing environment variables, then copy the exact production origins back into Railway's `EPICENTER_FRONTEND_ORIGINS` and redeploy the API.

## 6. Verify the public deployment

Run these read-only checks locally against the public services:

```bash
cd backend
.venv/bin/python scripts/verify_deployment.py \
  --base-url https://YOUR_RAILWAY_DOMAIN \
  --frontend-origin https://YOUR_PATIENT_DOMAIN \
  --frontend-origin https://YOUR_NURSE_DOMAIN \
  --expected-commit YOUR_SHORT_GIT_SHA \
  --require-production

.venv/bin/python scripts/verify_mcp_client.py \
  --base-url https://YOUR_RAILWAY_DOMAIN
```

Before the MCP check, load the key without echoing it or placing it in shell history:

```bash
read -s "EPICENTER_MCP_API_KEY?MCP key: "
export EPICENTER_MCP_API_KEY
# run verify_mcp_client.py, then:
unset EPICENTER_MCP_API_KEY
```

Manually verify patient onboarding, coverage editing, questionnaire draft/submission, nurse queue and exception handling, step-up update/delete, audit immutability, and failure/retry states. Restart both Railway services and confirm persisted data and audit entries remain intact.

## 7. Add the custom MCP servers to Copilot Studio

This is a **manual Microsoft configuration and licensing gate**.

1. Add two existing MCP servers using Streamable HTTP:
   - `https://YOUR_RAILWAY_DOMAIN/mcp/operations`
   - `https://YOUR_RAILWAY_DOMAIN/mcp/insurance-registry`
2. Select API-key authentication and configure the `X-MCP-API-Key` secret if the connector permits the required header. If the tenant cannot supply that header, stop and record the limitation; do not disable authentication.
3. Verify that only the intended `epicenter_*` and `registry_*` tools are discovered.
4. Run one read-only synthetic operations call and reconcile its result with the native dashboard/API.
5. Record the Git SHA, endpoint, authentication mode, tool inventory, result, screenshots, tenant/licence state, and rollback procedure. Do not claim publication if the tenant only permits testing.

Copilot Studio's current MCP flow uses Streamable HTTP; legacy SSE is not supported. Follow Microsoft's [add an existing MCP server](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent) guide.

## 8. Release evidence and rollback

Record, without secrets:

- Git SHA and remote branch
- Supabase project ref, migration-list output, seed verification, and advisor results
- Clerk instance type and role-mapping verification
- Railway API/worker deployment IDs and health results
- all three Vercel deployment URLs and CORS smoke result
- MCP inventories and Copilot Studio result/licensing state
- desktop browser/visual QA result

Rollback by redeploying the last known-good Railway/Vercel Git SHA. Database migrations require a reviewed forward migration; do not delete migration files, rewrite applied migration history, or manually erase audit records.
