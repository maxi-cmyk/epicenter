from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (ROOT / "supabase/migrations/20260813110000_nurse_task_workflow_persistence.sql").read_text()


def test_nurse_workflow_migration_has_all_task_rpcs() -> None:
    for function_name in (
        "epicenter_confirm_document",
        "epicenter_confirm_package",
        "epicenter_confirm_billing",
        "epicenter_confirm_identity",
        "epicenter_confirm_forms",
        "epicenter_mark_physical_forms_received",
    ):
        assert f"create or replace function public.{function_name}" in MIGRATION
        assert f"revoke all on function public.{function_name}" in MIGRATION


def test_nurse_workflow_mutations_are_atomic_audited_and_idempotent() -> None:
    assert "pg_advisory_xact_lock" in MIGRATION
    assert "for update" in MIGRATION
    assert "public.idempotency_records" in MIGRATION
    assert "public.operational_events" in MIGRATION
    assert "public.audit_log" in MIGRATION
    assert "version = version + 1" in MIGRATION
    assert "security invoker" in MIGRATION
