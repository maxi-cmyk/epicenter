from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_MIGRATION = (ROOT / "supabase/migrations/20260812023811_complete_operational_boundary.sql").read_text()
ONBOARDING_MIGRATION = (ROOT / "supabase/migrations/20260812120000_patient_onboarding.sql").read_text()
SEED = (ROOT / "supabase/operational_seed.sql").read_text()
VERIFY = (ROOT / "supabase/verify_operational.sql").read_text()


def test_task_two_schema_contract_is_explicitly_secured() -> None:
    tables = {
        "data_import_exceptions",
        "registration_validations",
        "coverage_documents",
        "eligibility_rules",
        "eligibility_matches",
        "coverage_reuse_decisions",
        "patient_submissions",
        "patient_notifications",
    }
    for table in tables:
        assert f"create table public.{table}" in BOUNDARY_MIGRATION
        assert f"alter table public.{table} enable row level security" in BOUNDARY_MIGRATION
        assert f"revoke all on table public.{table} from anon, authenticated" in BOUNDARY_MIGRATION


def test_task_three_writes_are_transactional_idempotent_and_versioned() -> None:
    functions = {
        "epicenter_validate_registration",
        "epicenter_submit_prearrival",
        "epicenter_process_document",
        "epicenter_assign_counter",
        "epicenter_create_patient",
        "epicenter_update_patient",
        "epicenter_soft_delete_patient",
    }
    for function in functions:
        assert f"function public.{function}" in BOUNDARY_MIGRATION
    assert "pg_advisory_xact_lock" in BOUNDARY_MIGRATION
    assert "idempotency_records" in BOUNDARY_MIGRATION
    assert "stale_patient_version" in BOUNDARY_MIGRATION
    assert "stale_ticket_version" in BOUNDARY_MIGRATION
    assert "original_ordering_at" not in BOUNDARY_MIGRATION[BOUNDARY_MIGRATION.index("epicenter_assign_counter") :]


def test_seed_and_verifier_cover_task_two_invariants() -> None:
    assert "'accepted'" in SEED
    assert "'rejected'" in SEED
    assert "'under_review'" in SEED
    assert "administrative_urgency" in SEED
    assert "manual_check_confirmations" in SEED
    assert "simulator_runs" in SEED
    assert "false-ready invariant" in VERIFY
    assert "one-ticket invariant" in VERIFY
    assert "browser database roles retain" in VERIFY


def test_patient_onboarding_persistence_contract() -> None:
    tables = {
        "patient_onboarding_states",
        "appointment_questionnaire_responses",
    }
    for table in tables:
        assert f"create table public.{table}" in ONBOARDING_MIGRATION
        assert f"alter table public.{table} enable row level security" in ONBOARDING_MIGRATION
        assert f"revoke all on table public.{table} from anon, authenticated" in ONBOARDING_MIGRATION
        assert f"grant select, insert, update, delete on table public.{table} to service_role" in ONBOARDING_MIGRATION

    functions = {
        "epicenter_get_onboarding",
        "epicenter_advance_onboarding",
        "epicenter_get_questionnaire",
        "epicenter_save_questionnaire",
    }
    for function in functions:
        assert f"function public.{function}" in ONBOARDING_MIGRATION
        assert f"grant execute on function public.{function}" in ONBOARDING_MIGRATION

    assert "pg_advisory_xact_lock" in ONBOARDING_MIGRATION
    assert "idempotency_records" in ONBOARDING_MIGRATION
    assert "coverage_submission_required" in ONBOARDING_MIGRATION
    assert "questionnaire_submission_required" in ONBOARDING_MIGRATION
    assert "stale_questionnaire_version" in ONBOARDING_MIGRATION


def test_onboarding_coverage_without_appointment_contract() -> None:
    migration = (
        ROOT / "supabase/migrations/20260812143000_onboarding_coverage_without_appointment.sql"
    ).read_text()
    assert "function public.epicenter_submit_onboarding_coverage" in migration
    assert "appointment_id is null" in migration
    assert "grant execute on function public.epicenter_submit_onboarding_coverage" in migration
    assert "Stores first-time patient coverage without requiring an appointment booking." in migration
