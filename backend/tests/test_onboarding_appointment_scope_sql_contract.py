from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (ROOT / "supabase/migrations/20260813161000_new_patient_onboarding_appointment_scope.sql").read_text()


def test_new_patient_onboarding_does_not_inherit_demo_appointment() -> None:
    assert "p_appointment_reference text default ''" in MIGRATION
    assert "requested_appointment := coalesce(nullif(trim(p_appointment_reference), ''), '')" in MIGRATION
    assert "appointment.patient_id = p_patient_id" in MIGRATION
    assert "'pending-booking'" in MIGRATION
    assert "'APT-DEMO-014'" not in MIGRATION
    assert "security invoker" in MIGRATION
    assert "set search_path = ''" in MIGRATION
    assert "from public, anon, authenticated" in MIGRATION
    assert "to service_role" in MIGRATION
