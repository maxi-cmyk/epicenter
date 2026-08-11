from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app

client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["demo_mode"] is True
    assert response.json()["providers"] == {"database": "synthetic", "authentication": "demo"}


def test_production_routes_fail_closed_without_clerk_configuration() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(demo_mode=False, _env_file=None)
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


def test_ready_transition_rejects_missing_confirmation() -> None:
    response = client.post(
        "/api/v1/tickets/Q-017/transition",
        json={"readiness_state": "ready", "reason": "all_prerequisites_passed", "staff_confirmed": False},
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


def test_recommendation_requires_explicit_decision() -> None:
    response = client.post("/api/v1/recommendations/A-009/decision", json={"decision": "later"})
    assert response.status_code == 422
