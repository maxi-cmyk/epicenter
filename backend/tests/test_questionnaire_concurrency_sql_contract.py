from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (ROOT / "supabase/migrations/20260813160000_questionnaire_concurrent_load_fix.sql").read_text()


def test_questionnaire_initialization_is_concurrency_safe_and_private() -> None:
    assert "create or replace function public.epicenter_get_questionnaire" in MIGRATION
    assert "on conflict (patient_id) where appointment_id is null do nothing" in MIGRATION
    assert "on conflict (appointment_id, patient_id) where appointment_id is not null do nothing" in MIGRATION
    assert "security invoker" in MIGRATION
    assert "set search_path = ''" in MIGRATION
    assert "from public, anon, authenticated" in MIGRATION
    assert "to service_role" in MIGRATION
