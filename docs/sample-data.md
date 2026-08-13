# Synthetic sample data

The supplied sample files are checked into `data/raw/` unchanged so the demo database can be reproduced. Every record and document is synthetic or fictional; none may be relabelled as real clinical evidence.

## Imported scope

| Source | Records used | Supabase target |
|---|---:|---|
| Patient registration CSV | 300 | `patients` |
| General health questionnaire CSV | 30 | `questionnaire_submissions` |
| Occupational health questionnaire CSV | 30 | `questionnaire_submissions` |
| Sample medical chit DOCX | 9 documents | `medical_document_samples` |
| Questionnaire field-reference DOCX | Schema reference | Generator and validation rules |
| Deterministic clinic workflow | 1 clinic, 3 appointments, 6 tickets, 2 review cases | Operational tables |
| Deterministic simulator fixtures | 3 scenario snapshots | `simulator_snapshots` |

Government identifiers are normalized only long enough to calculate a SHA-256 match key. Supabase stores the hash and a masked display value, not the raw identifier. The unmodified raw fixtures remain development-only source material.

## Identity gate

The registration file contains 300 unique normalized identifiers. Across the questionnaires there are 57 unique people: 51 identifiers occur in registration data and 6 do not. The 54 individual questionnaire submissions with a registration candidate have the same identifier and name but a conflicting date of birth. They are therefore stored with `verification_status = 'conflict'`, a candidate patient reference, and no verified `patient_id`. The other 6 are stored as `no_registration`.

This is deliberate. An identifier hit is candidate evidence, not permission to silently overwrite or merge conflicting patient facts. Staff must resolve those records. The system is deliberately conservative: ambiguous, conflicting, or unusual documents route to staff review rather than guess, so first-pass automation is below 100% by design.

## Generate and load

Generate the idempotent seed after changing any raw fixture or the derived chit manifest:

```bash
python3 backend/scripts/generate_supabase_seed.py
```

For a local Supabase stack with Docker running:

```bash
npx supabase start
npx supabase db reset
```

For the hosted project, authenticate the CLI locally, link the project, and then apply both migration and seed:

```bash
npx supabase login
npx supabase link --project-ref YOUR_PROJECT_REF
npx supabase db push --include-seed
```

`db push --include-seed` applies pending migrations and the idempotent seed without resetting the linked database. Always inspect the project reference and the CLI dry run before applying it to a shared environment.

Patient first-time signup persistence lives in `supabase/migrations/20260812120000_patient_onboarding.sql` (`patient_onboarding_states`, `appointment_questionnaire_responses`, and the `epicenter_*_onboarding` / `epicenter_*_questionnaire` RPCs). Apply it with the same `npx supabase db push` flow before enabling `EPICENTER_PERSISTENCE_MODE=supabase` for onboarding.

Signed-in home / queue / payment / records use `supabase/migrations/20260813010000_patient_journey_persistence.sql` (`payments` plus `epicenter_get_patient_*` / `epicenter_submit_mock_payment`). Clerk sign-in links through `patient_accounts` (email cached when available); demo mode still resolves the seeded `registration:0107` patient for the journey fixture.

The Supabase URL and API keys used by the running FastAPI service cannot apply
DDL. A linked CLI session (or the SQL Editor) must apply the migration before
the local API can select `EPICENTER_PERSISTENCE_MODE=supabase`. Railway is a
later deployment step and is not involved in this local verification path.

The browser publishable key cannot create tables or perform this privileged import. Keep `EPICENTER_SUPABASE_SECRET_KEY`, the CLI access token, and the database password out of both `frontend/patient/.env.local` and `frontend/nurse/.env.local`, and out of Git.

## Access boundary

All raw and operational tables have row-level security enabled and grant no direct access to `anon` or `authenticated`. Transactional mutation functions are executable only by `service_role`. The FastAPI backend uses the server-only Supabase secret; neither frontend receives it. A Clerk-aware browser client is prepared for future narrowly scoped Realtime/RLS use, but no patient-data policy is opened by this seed.

Before enabling that browser path, connect Clerk under Supabase **Authentication → Third-Party Auth** and add restrictive role/clinic policies. The current browser client passes the active Clerk session token through Supabase's supported `accessToken` callback; it does not use the deprecated shared-JWT-secret integration.
