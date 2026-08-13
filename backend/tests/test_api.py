import pytest
from fastapi.testclient import TestClient

from app.core.auth import StaffPrincipal, require_staff
from app.core.config import Settings, get_settings
from app.data.demo_repository import DemoRepository
from app.data.dependencies import get_operations_repository
from app.main import app

client = TestClient(app)


def staff_principal(role: str, *, factor_age: tuple[int, int] | None = (0, -1)) -> StaffPrincipal:
    return StaffPrincipal(
        subject=f"test-{role}",
        source="test",
        factor_verification_age=factor_age,
        role=role,
        clinic_id="clinic_harbourfront",
    )


@pytest.fixture(autouse=True)
def isolated_demo_dependencies():
    repository = DemoRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(
        demo_mode=True,
        persistence_mode="demo",
        _env_file=None,
    )
    app.dependency_overrides[get_operations_repository] = lambda: repository
    try:
        yield
    finally:
        app.dependency_overrides.clear()


def test_healthcheck() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["demo_mode"] is True
    providers = response.json()["providers"]
    assert providers["database"] == "synthetic"
    assert providers["authentication"] == "demo"
    assert "openai" in providers  # new field — present but unconfigured in demo


def test_production_routes_fail_closed_without_clerk_configuration() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        demo_mode=False,
        persistence_mode="demo",
        _env_file=None,
    )
    try:
        response = client.get("/api/v1/dashboard")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "Clerk authentication is not configured."


def test_dashboard_contract() -> None:
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["synthetic"] is True
    assert any(ticket["id"] == "Q-018" for ticket in body["tickets"])


@pytest.mark.parametrize("role", ["registration", "operations_admin", "auditor"])
def test_staff_session_returns_the_authorized_database_role(role: str) -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal(role)

    response = client.get("/api/v1/staff/session")

    assert response.status_code == 200
    assert response.json() == {"role": role, "clinic_id": "clinic_harbourfront"}


def test_simulator_snapshots_are_versioned_and_synthetic() -> None:
    response = client.get("/api/v1/simulator/snapshots")

    assert response.status_code == 200
    snapshots = response.json()
    assert {snapshot["scenario_id"] for snapshot in snapshots} == {
        "dynamic_allocation",
        "serial_baseline",
        "single_ticket",
    }
    assert all(snapshot["synthetic"] and snapshot["snapshot_hash"] for snapshot in snapshots)


def test_patient_pre_arrival_submission_stays_under_review() -> None:
    response = client.post(
        "/api/v1/patient/pre-arrival/submit",
        json={"appointment_id": "APT-DEMO-001", "coverage_action": "reuse"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["synthetic"] is True
    assert body["outcome"] == "under_review"
    assert body["processing_reference"].startswith("PRE-")


def test_patient_account_activation_returns_only_the_configured_synthetic_scenario() -> None:
    response = client.post("/api/v1/patient/account/activate")

    assert response.status_code == 200
    assert response.json() == {
        "patient_id": 1,
        "source_record_key": "registration:0107",
        "synthetic": True,
        "onboarding_completed": False,
        "onboarding_step": "singpass",
    }


def test_fresh_patient_onboarding_wizard_completes_in_order() -> None:
    state = client.get("/api/v1/patient/onboarding")
    assert state.status_code == 200
    assert state.json()["completed"] is False
    assert state.json()["current_step"] == "singpass"

    blocked = client.post(
        "/api/v1/patient/onboarding/advance",
        json={"step": "singpass", "idempotency_key": "onboard-blocked"},
    )
    assert blocked.status_code == 409

    singpass = client.post(
        "/api/v1/patient/onboarding/advance",
        json={
            "step": "singpass",
            "singpass_authenticated": True,
            "idempotency_key": "onboard-singpass",
        },
    )
    assert singpass.status_code == 200
    assert singpass.json()["current_step"] == "singpass"
    assert singpass.json()["singpass_authenticated"] is True
    assert any(field["value"] for field in singpass.json()["singpass_fields"])

    singpass_confirm = client.post(
        "/api/v1/patient/onboarding/advance",
        json={
            "step": "singpass",
            "singpass_authenticated": True,
            "idempotency_key": "onboard-singpass-confirm",
        },
    )
    assert singpass_confirm.status_code == 200
    assert singpass_confirm.json()["current_step"] == "insurance"

    insurance = client.post(
        "/api/v1/patient/onboarding/advance",
        json={
            "step": "insurance",
            "insurance_completed": True,
            "idempotency_key": "onboard-insurance",
        },
    )
    assert insurance.status_code == 200
    assert insurance.json()["current_step"] == "questionnaire"

    questionnaire = client.get(
        "/api/v1/patient/questionnaire",
        params={"appointment_id": "APT-DEMO-014"},
    )
    assert questionnaire.status_code == 200
    assert any(field["field_id"] == "medical_conditions" for field in questionnaire.json()["fields"])

    saved = client.post(
        "/api/v1/patient/questionnaire",
        json={
            "appointment_id": "APT-DEMO-014",
            "answers": {
                "screening_provider": "Parkway Shenton Medical Clinic",
                "screening_location": "Harbourfront Tower One",
                "ethnicity": "Chinese",
                "gender": "Male",
                "medical_conditions": "Asthma",
                "drug_allergies": "No",
                "recent_vaccination": "No",
                "flu_vaccination": "Yes",
                "exercise_frequency": "Less than 100 mins/week",
                "smoking_status": "No",
                "drinks_alcohol": "No",
                "stress_frequency": "Sometimes",
                "chronic_pain": "No",
                "share_sexual_history": "No",
            },
            "declaration_acknowledged": True,
            "submit": True,
            "expected_version": questionnaire.json()["version"],
            "idempotency_key": "onboard-questionnaire-save",
        },
    )
    assert saved.status_code == 200
    assert saved.json()["status"] == "submitted"

    finished = client.post(
        "/api/v1/patient/onboarding/advance",
        json={
            "step": "questionnaire",
            "questionnaire_completed": True,
            "idempotency_key": "onboard-finish",
        },
    )
    assert finished.status_code == 200
    assert finished.json()["completed"] is True
    assert finished.json()["current_step"] == "complete"

    activated = client.post("/api/v1/patient/account/activate")
    assert activated.json()["onboarding_completed"] is True


def test_registration_validation_returns_patient_safe_outcome() -> None:
    response = client.post(
        "/api/v1/patient/registration/validate",
        json={
            "appointment_reference": "APT-DEMO-014",
            "identifier_hash": "4e487c99807bebe1c81bf3cded10ceb92f1c8d3ed0d48cbe822ad578a45854b5",
            "full_name": "Loh Wei Ming",
            "date_of_birth": "1952-07-26",
            "email": "wei.loh43@hotmail.com",
            "idempotency_key": "registration-validation-test",
        },
    )

    assert response.status_code == 200
    assert response.json()["outcome"] == "accepted"
    assert "internal_reason" not in response.json()


def test_patient_home_exposes_one_upcoming_appointment_and_next_action() -> None:
    response = client.get("/api/v1/patient/home")
    assert response.status_code == 200
    body = response.json()
    assert body["patient_display_name"] == "Loh Wei Ming"
    assert body["appointment"]["appointment_id"] == "APT-DEMO-014"
    assert body["primary_action"] == "confirm_coverage"
    assert "confidence" not in body
    assert "readiness_reason" not in body


def test_first_visit_coverage_has_no_prior_policy() -> None:
    prior = client.get(
        "/api/v1/patient/coverage/prior",
        params={"appointment_id": "APT-DEMO-014", "first_visit": True},
    )
    assert prior.status_code == 200
    body = prior.json()
    assert body["has_prior_coverage"] is False
    assert body["force_upload"] is True
    assert body["issuer_name"] is None


def test_patient_coverage_questionnaire_and_queue_journey() -> None:
    prior = client.get("/api/v1/patient/coverage/prior", params={"appointment_id": "APT-DEMO-014"})
    assert prior.status_code == 200
    assert prior.json()["issuer_name"] == "Meridian"

    submit = client.post(
        "/api/v1/patient/pre-arrival/submit",
        json={
            "appointment_id": "APT-DEMO-014",
            "coverage_action": "reuse",
            "idempotency_key": "journey-coverage-1",
        },
    )
    assert submit.status_code == 200
    assert submit.json()["outcome"] == "under_review"

    questionnaire = client.get(
        "/api/v1/patient/questionnaire",
        params={"appointment_id": "APT-DEMO-014"},
    )
    assert questionnaire.status_code == 200
    assert questionnaire.json()["prefill"][0]["editable"] is False
    field_ids = {field["field_id"] for field in questionnaire.json()["fields"]}
    assert "gender" in field_ids
    assert "pregnant" in field_ids
    pregnant = next(field for field in questionnaire.json()["fields"] if field["field_id"] == "pregnant")
    assert pregnant["show_if_field"] == "gender"
    assert pregnant["show_if_value"] == "Female"

    saved = client.post(
        "/api/v1/patient/questionnaire",
        json={
            "appointment_id": "APT-DEMO-014",
            "answers": {
                "screening_provider": "Parkway Shenton Medical Clinic",
                "screening_location": "Harbourfront Tower One",
                "ethnicity": "Chinese",
                "gender": "Male",
                "drug_allergies": "No",
                "recent_vaccination": "No",
                "flu_vaccination": "No",
                "exercise_frequency": "Between 100 to 150 mins/week",
                "smoking_status": "No",
                "drinks_alcohol": "No",
                "stress_frequency": "Rarely",
                "chronic_pain": "No",
                "share_sexual_history": "No",
            },
            "declaration_acknowledged": True,
            "submit": True,
            "expected_version": questionnaire.json()["version"],
            "idempotency_key": "journey-questionnaire-1",
        },
    )
    assert saved.status_code == 200
    assert saved.json()["status"] == "submitted"

    home = client.get("/api/v1/patient/home")
    assert home.json()["outcome"] == "accepted"
    assert home.json()["payment_status"] == "ready"

    queue = client.get("/api/v1/patient/queue")
    assert queue.status_code == 200
    assert queue.json()["ticket_id"] == "Q-014"
    assert "needs_review" not in queue.json()["status_detail"].lower() or "staff member" in queue.json()["status_detail"]

    payment = client.post(
        "/api/v1/patient/payment/mock-pay",
        json={
            "appointment_id": "APT-DEMO-014",
            "expected_version": 1,
            "idempotency_key": "journey-payment-1",
        },
    )
    assert payment.status_code == 200
    assert payment.json()["status"] == "mocked_paid"
    assert payment.json()["mocked"] is True

    records = client.get("/api/v1/patient/records")
    assert records.status_code == 200
    assert len(records.json()["visits"]) >= 1


def test_upload_link_resolves_without_creating_an_account() -> None:
    valid = client.get("/api/v1/patient/upload-links/demo")
    assert valid.status_code == 200
    assert valid.json()["valid"] is True
    assert valid.json()["appointment_id"] == "APT-DEMO-014"

    expired = client.get("/api/v1/patient/upload-links/expired")
    assert expired.status_code == 200
    assert expired.json()["valid"] is False


def test_patient_replacement_requires_a_document_name() -> None:
    response = client.post(
        "/api/v1/patient/pre-arrival/submit",
        json={"appointment_id": "APT-DEMO-001", "coverage_action": "replace"},
    )
    assert response.status_code == 422


def test_patient_fixture_endpoint_fails_closed_outside_demo_mode() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        demo_mode=False,
        persistence_mode="demo",
        _env_file=None,
    )
    try:
        response = client.post(
            "/api/v1/patient/pre-arrival/submit",
            json={"appointment_id": "APT-DEMO-001", "coverage_action": "reuse"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503


def test_ready_transition_rejects_missing_confirmation() -> None:
    response = client.post(
        "/api/v1/tickets/Q-017/transition",
        json={"readiness_state": "ready", "reason": "all_prerequisites_passed", "staff_confirmed": False},
    )
    assert response.status_code == 409


def test_ticket_transition_rejects_stale_version() -> None:
    response = client.post(
        "/api/v1/tickets/Q-017/transition",
        json={
            "readiness_state": "needs_review",
            "reason": "ambiguous_match",
            "staff_confirmed": False,
            "expected_version": 2,
            "idempotency_key": "stale-version-test",
        },
    )
    assert response.status_code == 409


def test_supervised_kiosk_creates_one_processing_ticket() -> None:
    response = client.post(
        "/api/v1/kiosk/check-in",
        json={"patient_name": "Jamie Tan", "nurse_supervisor": "Nurse Noor", "clinical_escalation": False},
    )
    assert response.status_code == 201
    ticket = response.json()["ticket"]
    assert ticket["intake_type"] == "walk_in"
    assert ticket["readiness_state"] == "processing"
    assert ticket["id"].startswith("Q-")


def test_replayed_kiosk_check_in_returns_the_same_ticket() -> None:
    payload = {
        "patient_name": "Jamie Tan",
        "nurse_supervisor": "Nurse Noor",
        "clinical_escalation": False,
        "idempotency_key": "walk-in-retry-test",
    }
    first = client.post("/api/v1/kiosk/check-in", json=payload)
    replay = client.post("/api/v1/kiosk/check-in", json=payload)

    assert first.status_code == replay.status_code == 201
    assert first.json()["ticket"]["id"] == replay.json()["ticket"]["id"]


def test_replayed_transition_returns_the_committed_version() -> None:
    payload = {
        "readiness_state": "needs_review",
        "reason": "ambiguous_match",
        "staff_confirmed": False,
        "expected_version": 1,
        "idempotency_key": "transition-retry-test",
    }
    first = client.post("/api/v1/tickets/Q-017/transition", json=payload)
    replay = client.post("/api/v1/tickets/Q-017/transition", json=payload)

    assert first.status_code == replay.status_code == 200
    assert first.json()["ticket"]["version"] == replay.json()["ticket"]["version"] == 2


def test_recommendation_requires_explicit_decision() -> None:
    response = client.post("/api/v1/recommendations/A-009/decision", json={"decision": "later"})
    assert response.status_code == 422


def test_counter_assignment_preserves_ticket_and_increments_version() -> None:
    response = client.post(
        "/api/v1/tickets/Q-017/counter",
        json={
            "counter_number": "Counter 4",
            "expected_version": 1,
            "idempotency_key": "counter-assignment-test",
        },
    )

    assert response.status_code == 200
    ticket = response.json()["ticket"]
    assert ticket["id"] == "Q-017"
    assert ticket["original_ordering_at"] == "2026-08-12T09:34:00Z"
    assert ticket["actual_counter"] == "Counter 4"
    assert ticket["version"] == 2


def test_patient_crud_uses_versioned_soft_delete() -> None:
    created = client.post(
        "/api/v1/patients",
        json={
            "source_record_key": "api-test:patient",
            "identifier_hash": "b" * 64,
            "identifier_masked": "*****123A",
            "full_name": "API Test Patient",
            "date_of_birth": "1990-01-01",
            "email": "api-test@example.test",
            "contact_mobile": "80000000",
            "reason": "API contract test",
            "idempotency_key": "patient-create-test",
        },
    )
    assert created.status_code == 201
    patient = created.json()

    updated = client.patch(
        f"/api/v1/patients/{patient['id']}",
        json={
            "expected_version": patient["version"],
            "full_name": "Updated API Patient",
            "reason": "Correct synthetic name",
            "idempotency_key": "patient-update-test",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2

    stale = client.patch(
        f"/api/v1/patients/{patient['id']}",
        json={
            "expected_version": 1,
            "full_name": "Must Not Commit",
            "reason": "Stale test",
            "idempotency_key": "patient-stale-test",
        },
    )
    assert stale.status_code == 409

    deleted = client.request(
        "DELETE",
        f"/api/v1/patients/{patient['id']}",
        json={
            "expected_version": 2,
            "reason": "Remove synthetic test fixture",
            "idempotency_key": "patient-delete-test",
        },
    )
    assert deleted.status_code == 200
    assert deleted.json()["deleted_at"] is not None
    assert client.get(f"/api/v1/patients/{patient['id']}").status_code == 404


def test_auditor_role_cannot_mutate_patients() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("auditor")

    response = client.post(
        "/api/v1/patients",
        json={
            "source_record_key": "api-test:denied",
            "identifier_hash": "c" * 64,
            "identifier_masked": "*****999Z",
            "full_name": "Denied Patient",
            "reason": "Permission test",
            "idempotency_key": "auditor-denied-test",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Staff role is not permitted for this action."


def test_registration_role_cannot_decide_operations_recommendations() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("registration")

    response = client.post(
        "/api/v1/recommendations/A-009/decision",
        json={
            "decision": "approved",
            "expected_version": 1,
            "idempotency_key": "registration-role-denied",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Staff role is not permitted for this action."


def test_registration_role_cannot_read_audit_or_simulator() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("registration")

    assert client.get("/api/v1/audit").status_code == 403
    assert client.get("/api/v1/simulator/snapshots").status_code == 403


def test_operations_admin_can_read_audit_and_simulator() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("operations_admin")

    assert client.get("/api/v1/audit").status_code == 200
    assert client.get("/api/v1/simulator/snapshots").status_code == 200


def test_stale_factor_returns_clerk_reverification_hint_before_mutation() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("registration", factor_age=(10, -1))

    response = client.post(
        "/api/v1/tickets/Q-017/transition",
        json={
            "readiness_state": "needs_review",
            "reason": "reverification-test",
            "staff_confirmed": False,
            "expected_version": 1,
            "idempotency_key": "stale-reverification-test",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "clerk_error": {
            "type": "forbidden",
            "reason": "reverification-error",
            "metadata": {"reverification": "strict"},
        }
    }


def test_fresh_factor_allows_registration_mutation() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("registration", factor_age=(0, -1))

    response = client.post(
        "/api/v1/tickets/Q-017/transition",
        json={
            "readiness_state": "needs_review",
            "reason": "fresh-reverification-test",
            "staff_confirmed": False,
            "expected_version": 1,
            "idempotency_key": "fresh-reverification-test",
        },
    )

    assert response.status_code == 200
