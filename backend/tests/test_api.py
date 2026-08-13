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


def test_assistant_fails_closed_when_openai_is_not_configured() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("registration")

    response = client.post("/api/v1/assistant", json={"message": "Summarize the queue."})

    assert response.status_code == 503
    assert response.json()["detail"] == "The staff assistant is not configured."


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
    assert "Counter" in body["queue_summary"]
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
    assert queue.json()["queue_number"]
    assert queue.json()["counter_label"]
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


def test_pharmacy_queue_lists_ongoing_and_finished_tickets() -> None:
    response = client.get("/api/v1/pharmacy/queue")

    assert response.status_code == 200
    tickets = response.json()
    assert all(ticket["visit_phase"] in {"ongoing", "finished"} for ticket in tickets)
    assert any(ticket["id"] == "Q-020" for ticket in tickets)


def test_medication_dispense_and_tpa_submission_draft_compose_without_retyping() -> None:
    dispense_response = client.post(
        "/api/v1/tickets/Q-020/medication",
        json={
            "items": [{"name": "Ibuprofen 200mg", "quantity": 10, "unit_cost": 0.2}],
            "idempotency_key": "medication-dispense-test",
        },
    )
    assert dispense_response.status_code == 201
    dispense = dispense_response.json()["medication"]
    assert dispense["ticket_id"] == "Q-020"
    assert dispense["total_cost"] == 2.0

    draft_response = client.get("/api/v1/tickets/Q-020/tpa-submission")
    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert draft["status"] == "draft"
    assert len(draft["documents"]) == 4
    assert {doc["category"] for doc in draft["documents"]} == {
        "form",
        "authorisation_letter",
        "benefit_structure",
        "coding_scheme",
    }
    assert draft["medication"]["ticket_id"] == "Q-020"

    confirm_response = client.post(
        "/api/v1/tickets/Q-020/tpa-submission/confirm",
        json={"expected_version": draft["version"], "idempotency_key": "tpa-confirm-test"},
    )
    assert confirm_response.status_code == 200
    submission = confirm_response.json()["tpa_submission"]
    assert submission["status"] == "submitted"
    assert submission["external_reference"]


def test_registration_confirms_autofilled_tpa_document_without_retyping() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-020")
    benefit_doc = next(doc for doc in ticket["documents"] if doc["category"] == "benefit_structure")
    assert benefit_doc["facts"]["membership_number"] == "MTP-88213045"
    assert benefit_doc["confirmed"] is False

    confirm_response = client.post(
        f"/api/v1/tickets/Q-020/documents/{benefit_doc['id']}/confirm",
        json={"expected_version": ticket["version"], "idempotency_key": "tpa-document-confirm-test"},
    )
    assert confirm_response.status_code == 200
    confirmed_ticket = confirm_response.json()["ticket"]
    confirmed_doc = next(doc for doc in confirmed_ticket["documents"] if doc["id"] == benefit_doc["id"])
    assert confirmed_doc["confirmed"] is True
    assert confirmed_doc["facts"]["membership_number"] == benefit_doc["facts"]["membership_number"]
    assert confirmed_ticket["version"] == ticket["version"] + 1


def test_nurse_explicitly_rechecks_the_matched_package() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-019")
    assert ticket["matched_package"] == "PEE226 — Basic Screen"
    assert ticket["package_confirmed"] is False

    confirm_response = client.post(
        "/api/v1/tickets/Q-019/package/confirm",
        json={"expected_version": ticket["version"], "idempotency_key": "package-confirm-test"},
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["ticket"]
    assert confirmed["package_confirmed"] is True
    assert confirmed["matched_package"] == "PEE226 — Basic Screen"
    assert confirmed["version"] == ticket["version"] + 1


def test_nurse_can_correct_a_wrong_matched_package() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-018")
    assert ticket["matched_package"] == "Executive screening"

    confirm_response = client.post(
        "/api/v1/tickets/Q-018/package/confirm",
        json={
            "corrected_package": "WELL2 — Comprehensive Screen",
            "expected_version": ticket["version"],
            "idempotency_key": "package-correction-test",
        },
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["ticket"]
    assert confirmed["package_confirmed"] is True
    assert confirmed["matched_package"] == "WELL2 — Comprehensive Screen"


def test_nurse_explicitly_rechecks_billing_code_uncovered_cost_and_queue_number() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-019")
    assert ticket["billing_code"] == "PEE226-CHAS"
    assert ticket["uncovered_cost"] == 8.5
    assert ticket["queue_number"] == "Q019"
    assert ticket["billing_confirmed"] is False

    confirm_response = client.post(
        "/api/v1/tickets/Q-019/billing/confirm",
        json={"expected_version": ticket["version"], "idempotency_key": "billing-confirm-test"},
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["ticket"]
    assert confirmed["billing_confirmed"] is True
    assert confirmed["billing_code"] == "PEE226-CHAS"
    assert confirmed["uncovered_cost"] == 8.5
    assert confirmed["queue_number"] == "Q019"
    assert confirmed["version"] == ticket["version"] + 1


def test_nurse_can_correct_wrong_billing_uncovered_cost_or_queue_number() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-018")
    assert ticket["uncovered_cost"] == 45.0

    confirm_response = client.post(
        "/api/v1/tickets/Q-018/billing/confirm",
        json={
            "corrected_uncovered_cost": 30.0,
            "corrected_queue_number": "Q018B",
            "expected_version": ticket["version"],
            "idempotency_key": "billing-correction-test",
        },
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["ticket"]
    assert confirmed["billing_confirmed"] is True
    assert confirmed["uncovered_cost"] == 30.0
    assert confirmed["queue_number"] == "Q018B"
    assert confirmed["billing_code"] == "EXEC-STD"


def test_nurse_confirms_identity_and_ecard() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-014")
    assert ticket["identity_confirmed"] is False

    confirm_response = client.post(
        "/api/v1/tickets/Q-014/identity/confirm",
        json={"expected_version": ticket["version"], "idempotency_key": "identity-confirm-test"},
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["ticket"]
    assert confirmed["identity_confirmed"] is True
    assert confirmed["ecard_verified"] is True
    assert confirmed["ecard_not_applicable"] is False
    assert confirmed["version"] == ticket["version"] + 1


def test_nurse_confirms_identity_with_ecard_not_applicable() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-015")

    confirm_response = client.post(
        "/api/v1/tickets/Q-015/identity/confirm",
        json={
            "ecard_not_applicable": True,
            "ecard_na_reason": "Patient forgot e-card, verified via passport instead.",
            "expected_version": ticket["version"],
            "idempotency_key": "identity-confirm-na-test",
        },
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["ticket"]
    assert confirmed["identity_confirmed"] is True
    assert confirmed["ecard_verified"] is False
    assert confirmed["ecard_not_applicable"] is True
    assert confirmed["ecard_na_reason"] == "Patient forgot e-card, verified via passport instead."


def test_nurse_confirms_forms_when_no_documents_present() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-014")
    assert ticket["documents"] == []

    confirm_response = client.post(
        "/api/v1/tickets/Q-014/forms/confirm",
        json={"expected_version": ticket["version"], "idempotency_key": "forms-confirm-test"},
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["ticket"]
    assert confirmed["forms_confirmed"] is True


def test_forms_confirm_rejects_unconfirmed_electronic_documents() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-020")
    assert any(doc["confirmed"] is False for doc in ticket["documents"])

    confirm_response = client.post(
        "/api/v1/tickets/Q-020/forms/confirm",
        json={"expected_version": ticket["version"], "idempotency_key": "forms-confirm-blocked-test"},
    )
    assert confirm_response.status_code == 409


def test_forms_confirm_succeeds_once_all_electronic_documents_confirmed() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-020")

    version = ticket["version"]
    for index, doc in enumerate(ticket["documents"]):
        confirm_response = client.post(
            f"/api/v1/tickets/Q-020/documents/{doc['id']}/confirm",
            json={"expected_version": version, "idempotency_key": f"forms-confirm-doc-{index}"},
        )
        assert confirm_response.status_code == 200
        version = confirm_response.json()["ticket"]["version"]

    confirm_response = client.post(
        "/api/v1/tickets/Q-020/forms/confirm",
        json={"expected_version": version, "idempotency_key": "forms-confirm-success-test"},
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["ticket"]["forms_confirmed"] is True


def test_nurse_marks_physical_forms_received() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-014")
    assert ticket["physical_forms_received"] is False

    confirm_response = client.post(
        "/api/v1/tickets/Q-014/physical-forms/received",
        json={"expected_version": ticket["version"], "idempotency_key": "physical-forms-received-test"},
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["ticket"]
    assert confirmed["physical_forms_received"] is True
    assert confirmed["physical_forms_received_by"]


def test_kiosk_check_in_can_flag_a_walk_in_as_a_checkup() -> None:
    response = client.post(
        "/api/v1/kiosk/check-in",
        json={
            "patient_name": "Checkup Walk-in",
            "nurse_supervisor": "Test Nurse",
            "is_checkup": True,
            "idempotency_key": "kiosk-checkup-test",
        },
    )
    assert response.status_code == 201
    assert response.json()["ticket"]["is_checkup"] is True


def test_transition_can_move_visit_phase_to_ongoing() -> None:
    ticket_response = client.get("/api/v1/dashboard")
    ticket = next(item for item in ticket_response.json()["tickets"] if item["id"] == "Q-014")
    assert ticket["visit_phase"] == "incoming"

    response = client.post(
        "/api/v1/tickets/Q-014/transition",
        json={
            "readiness_state": ticket["readiness_state"],
            "reason": ticket["readiness_reason"],
            "staff_confirmed": True,
            "visit_phase": "ongoing",
            "expected_version": ticket["version"],
            "idempotency_key": "visit-phase-transition-test",
        },
    )
    assert response.status_code == 200
    assert response.json()["ticket"]["visit_phase"] == "ongoing"


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


def test_pharmacist_can_view_patient_database_but_cannot_create_records() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("pharmacist")

    assert client.get("/api/v1/patients").status_code == 200
    response = client.post(
        "/api/v1/patients",
        json={
            "source_record_key": "api-test:pharmacy-denied",
            "identifier_hash": "d" * 64,
            "identifier_masked": "*****888Y",
            "full_name": "Pharmacy Denied Patient",
            "reason": "Permission test",
            "idempotency_key": "pharmacy-denied-test",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Staff role is not permitted for this action."


def test_patient_filters_and_sort_apply_before_pagination() -> None:
    response = client.get(
        "/api/v1/patients",
        params={"contact_filter": "email", "sort": "reference", "offset": 0, "limit": 1},
    )

    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) <= 1
    assert all(record["email"] for record in records)
    assert response.json()["offset"] == 0
    assert response.json()["limit"] == 1


def test_patient_create_does_not_require_reverification_but_update_does() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("registration", factor_age=(10, -1))

    created = client.post(
        "/api/v1/patients",
        json={
            "source_record_key": "api-test:create-without-step-up",
            "identifier_hash": "e" * 64,
            "identifier_masked": "*****777X",
            "full_name": "Create Without Step Up",
            "reason": "Database policy test",
            "idempotency_key": "create-no-step-up-test",
        },
    )
    assert created.status_code == 201

    response = client.patch(
        f"/api/v1/patients/{created.json()['id']}",
        json={
            "expected_version": created.json()["version"],
            "full_name": "Must Reverify",
            "reason": "Database policy test",
            "idempotency_key": "update-needs-step-up-test",
        },
    )

    assert response.status_code == 403
    assert response.json()["clerk_error"]["reason"] == "reverification-error"


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


@pytest.mark.parametrize("role", ["registration", "pharmacist"])
def test_demo_nurse_and_pharmacist_roles_can_read_audit_but_not_simulator(role: str) -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal(role)

    assert client.get("/api/v1/audit").status_code == 200
    assert client.get("/api/v1/simulator/snapshots").status_code == 403


def test_audit_is_no_store_searchable_filterable_paginated_and_read_only() -> None:
    response = client.get(
        "/api/v1/audit",
        params={"search": "medication", "action_type": "medication_dispensed", "limit": 1, "offset": 0},
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert len(response.json()) == 1
    assert response.json()[0]["action_type"] == "medication_dispensed"
    assert response.json()[0]["actor_role"] == "pharmacist"
    assert client.patch("/api/v1/audit/1", json={"details": {"tampered": True}}).status_code == 404
    assert client.delete("/api/v1/audit/1").status_code == 404

    completed = client.get(
        "/api/v1/audit",
        params={"actor_role": "system", "outcome": "completed", "target_table": "queue_entries"},
    )
    assert completed.status_code == 200
    assert [row["action_type"] for row in completed.json()] == ["visit_completed"]


def test_audit_rejects_an_inverted_date_range() -> None:
    response = client.get(
        "/api/v1/audit",
        params={"occurred_from": "2026-08-13T00:00:00Z", "occurred_to": "2026-08-12T00:00:00Z"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Start date must be before end date."


def test_operations_admin_can_read_audit_and_simulator() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("operations_admin")

    assert client.get("/api/v1/audit").status_code == 200
    assert client.get("/api/v1/simulator/snapshots").status_code == 200


def test_audit_records_medication_tpa_payment_and_visit_times_once() -> None:
    medication_payload = {
        "items": [{"name": "Ibuprofen 200mg", "quantity": 10, "unit_cost": 0.2}],
        "idempotency_key": "audit-medication-test",
    }
    first_medication = client.post("/api/v1/tickets/Q-020/medication", json=medication_payload)
    replayed_medication = client.post("/api/v1/tickets/Q-020/medication", json=medication_payload)
    assert first_medication.status_code == replayed_medication.status_code == 201

    draft = client.get("/api/v1/tickets/Q-020/tpa-submission").json()
    tpa_payload = {"expected_version": draft["version"], "idempotency_key": "audit-tpa-test"}
    first_tpa = client.post("/api/v1/tickets/Q-020/tpa-submission/confirm", json=tpa_payload)
    replayed_tpa = client.post("/api/v1/tickets/Q-020/tpa-submission/confirm", json=tpa_payload)
    assert first_tpa.status_code == replayed_tpa.status_code == 200

    ticket = next(item for item in client.get("/api/v1/dashboard").json()["tickets"] if item["id"] == "Q-019")
    payment_payload = {"expected_version": ticket["version"], "idempotency_key": "audit-payment-test"}
    first_payment = client.post("/api/v1/tickets/Q-019/billing/confirm", json=payment_payload)
    replayed_payment = client.post("/api/v1/tickets/Q-019/billing/confirm", json=payment_payload)
    assert first_payment.status_code == replayed_payment.status_code == 200

    audit_rows = client.get("/api/v1/audit").json()

    medication_rows = [
        row
        for row in audit_rows
        if row["action_type"] == "medication_dispensed" and row["details"]["medication"][0]["name"] == "Ibuprofen 200mg"
    ]
    assert len(medication_rows) == 1
    assert medication_rows[0]["details"]["medication"] == [
        {"name": "Ibuprofen 200mg", "quantity": 10, "unit_cost": 0.2}
    ]
    assert medication_rows[0]["details"]["total_cost"] == 2.0
    assert medication_rows[0]["details"]["dispensed_at"]
    assert medication_rows[0]["details"]["visit_times"]["checked_in_at"] == "2026-08-12T09:20:00+00:00"

    tpa_rows = [row for row in audit_rows if row["action_type"] == "tpa_submission_confirmed"]
    assert len(tpa_rows) == 1
    assert tpa_rows[0]["details"]["mode"] == "synthetic_demo"
    assert tpa_rows[0]["details"]["status"] == "submitted"
    assert tpa_rows[0]["details"]["external_reference"].startswith("CLAIM-")
    assert {document["category"] for document in tpa_rows[0]["details"]["documents"]} == {
        "form",
        "authorisation_letter",
        "benefit_structure",
        "coding_scheme",
    }
    assert tpa_rows[0]["details"]["medication_dispense_id"] == "MED-Q-020"
    assert tpa_rows[0]["details"]["submitted_at"]

    payment_rows = [
        row
        for row in audit_rows
        if row["action_type"] == "payment_details_confirmed" and row["details"]["ticket_id"] == "Q-019"
    ]
    assert len(payment_rows) == 1
    assert payment_rows[0]["details"]["payment"] == {
        "mode": "synthetic_demo",
        "status": "amount_due_confirmed",
        "currency": "SGD",
        "billing_code": "PEE226-CHAS",
        "amount_due": 8.5,
        "queue_number": "Q019",
        "confirmed_at": payment_rows[0]["details"]["payment"]["confirmed_at"],
    }
    assert payment_rows[0]["details"]["visit_times"]["checked_in_at"] == "2026-08-12T09:37:00+00:00"

    visit_rows = [row for row in audit_rows if row["action_type"] == "visit_completed"]
    assert len(visit_rows) == 1
    assert visit_rows[0]["details"]["visit_times"] == {
        "scheduled_at": "2026-08-12T08:30:00+00:00",
        "checked_in_at": "2026-08-12T08:22:00+00:00",
        "completed_at": "2026-08-12T09:08:00+00:00",
    }


def test_demo_audit_reads_cannot_mutate_stored_history() -> None:
    repository = DemoRepository()
    returned = repository.list_audit(limit=50)
    returned[0].details["tampered"] = True

    stored = repository.list_audit(limit=50)
    assert "tampered" not in stored[0].details


def test_stale_factor_allows_manual_confirmation_without_step_up() -> None:
    app.dependency_overrides[require_staff] = lambda: staff_principal("registration", factor_age=(10, -1))

    response = client.post(
        "/api/v1/tickets/Q-017/transition",
        json={
            "readiness_state": "needs_review",
            "reason": "manual-confirmation-test",
            "staff_confirmed": False,
            "expected_version": 1,
            "idempotency_key": "manual-no-step-up-test",
        },
    )

    assert response.status_code == 200


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
