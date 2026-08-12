from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (ROOT / "supabase/migrations/20260812023811_complete_operational_boundary.sql").read_text()
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
        assert f"create table public.{table}" in MIGRATION
        assert f"alter table public.{table} enable row level security" in MIGRATION
        assert f"revoke all on table public.{table} from anon, authenticated" in MIGRATION


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
        assert f"function public.{function}" in MIGRATION
    assert "pg_advisory_xact_lock" in MIGRATION
    assert "idempotency_records" in MIGRATION
    assert "stale_patient_version" in MIGRATION
    assert "stale_ticket_version" in MIGRATION
    assert "original_ordering_at" not in MIGRATION[MIGRATION.index("epicenter_assign_counter") :]


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
