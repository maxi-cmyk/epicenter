import pytest
from fastapi import HTTPException

from app.core import auth
from app.core.auth import (
    ClerkIdentity,
    ReverificationRequired,
    _has_fresh_verification,
    _parse_factor_verification_age,
    activate_patient_mapping,
    require_patient,
    require_reverified_staff,
    require_staff,
)
from app.core.config import Settings


def production_settings() -> Settings:
    return Settings(_env_file=None).model_copy(
        update={
            "demo_mode": False,
            "persistence_mode": "supabase",
            "supabase_url": "https://example.supabase.co",
            "supabase_secret_key": "test-secret",
            "clinic_id": "clinic_harbourfront",
            "patient_demo_source_record_key": "registration:0107",
        }
    )


class FakeDataApi:
    responses: dict[str, list[dict[str, object]]] = {}
    inserted: list[tuple[str, dict[str, object]]] = []

    def __init__(self, _url: str, _secret: str) -> None:
        pass

    def close(self) -> None:
        pass

    def select(self, table: str, _fields: str, **_kwargs: object) -> list[dict[str, object]]:
        return self.responses.get(table, [])

    def insert(self, table: str, payload: dict[str, object]) -> dict[str, object]:
        self.inserted.append((table, payload))
        return payload


@pytest.fixture(autouse=True)
def fake_data_api(monkeypatch: pytest.MonkeyPatch):
    FakeDataApi.responses = {}
    FakeDataApi.inserted = []
    monkeypatch.setattr(auth, "SupabaseDataApi", FakeDataApi)


def test_staff_mapping_requires_active_matching_clinic() -> None:
    FakeDataApi.responses["staff_accounts"] = [
        {
            "id": "staff_demo",
            "clerk_user_id": "user_nurse",
            "clinic_id": "clinic_harbourfront",
            "role": "registration",
            "active": True,
        }
    ]

    principal = require_staff(ClerkIdentity(subject="user_nurse", source="clerk"), production_settings())

    assert principal.role == "registration"
    assert principal.clinic_id == "clinic_harbourfront"


def test_wrong_clinic_staff_mapping_is_denied() -> None:
    FakeDataApi.responses["staff_accounts"] = [
        {
            "id": "staff_other",
            "clerk_user_id": "user_nurse",
            "clinic_id": "clinic_other",
            "role": "registration",
            "active": True,
        }
    ]

    with pytest.raises(HTTPException) as caught:
        require_staff(ClerkIdentity(subject="user_nurse", source="clerk"), production_settings())

    assert caught.value.status_code == 403


def test_disabled_staff_mapping_is_denied_even_if_storage_returns_it() -> None:
    FakeDataApi.responses["staff_accounts"] = [
        {
            "id": "staff_disabled",
            "clerk_user_id": "user_disabled",
            "clinic_id": "clinic_harbourfront",
            "role": "registration",
            "active": False,
        }
    ]

    with pytest.raises(HTTPException) as caught:
        require_staff(ClerkIdentity(subject="user_disabled", source="clerk"), production_settings())

    assert caught.value.status_code == 403


@pytest.mark.parametrize("rows", [[], [{"clinic_id": "clinic_harbourfront", "active": True}] * 2])
def test_staff_mapping_must_resolve_exactly_one_row(rows: list[dict[str, object]]) -> None:
    FakeDataApi.responses["staff_accounts"] = rows

    with pytest.raises(HTTPException) as caught:
        require_staff(ClerkIdentity(subject="user_unmapped", source="clerk"), production_settings())

    assert caught.value.status_code == 403


def test_factor_verification_age_is_parsed_fail_closed() -> None:
    assert _parse_factor_verification_age({"fva": [0, -1]}) == (0, -1)
    assert _parse_factor_verification_age({"fva": ["0", -1]}) is None
    assert _parse_factor_verification_age({"fva": [0]}) is None
    assert _parse_factor_verification_age({}) is None


@pytest.mark.parametrize(
    ("ages", "expected"),
    [((0, -1), True), ((9, -1), True), ((10, -1), False), ((0, 9), True), ((0, 10), False), (None, False)],
)
def test_strict_reverification_uses_fresh_strongest_available_factor(
    ages: tuple[int, int] | None,
    expected: bool,
) -> None:
    identity = ClerkIdentity(subject="user_nurse", source="clerk", factor_verification_age=ages)
    assert _has_fresh_verification(identity) is expected


def test_stale_staff_principal_requests_clerk_reverification() -> None:
    principal = auth.StaffPrincipal(
        subject="user_nurse",
        source="clerk",
        factor_verification_age=(10, -1),
        role="registration",
        clinic_id="clinic_harbourfront",
    )

    with pytest.raises(ReverificationRequired) as caught:
        require_reverified_staff(principal)

    assert caught.value.configuration == "strict"


def test_patient_mapping_resolves_exactly_one_active_patient() -> None:
    FakeDataApi.responses = {
        "patient_accounts": [{"patient_id": 107}],
        "patients": [{"id": 107, "source_record_key": "registration:0107"}],
    }

    principal = require_patient(ClerkIdentity(subject="user_patient", source="clerk"), production_settings())

    assert principal.patient_id == 107
    assert principal.source_record_key == "registration:0107"


def test_unmapped_patient_is_denied_until_activation() -> None:
    FakeDataApi.responses["patient_accounts"] = []

    with pytest.raises(HTTPException) as caught:
        require_patient(ClerkIdentity(subject="user_patient", source="clerk"), production_settings())

    assert caught.value.status_code == 403
    assert caught.value.detail == "Patient account activation required."


def test_patient_activation_creates_only_the_configured_synthetic_mapping() -> None:
    FakeDataApi.responses = {
        "patient_accounts": [],
        "patients": [{"id": 107, "source_record_key": "registration:0107"}],
    }

    principal = activate_patient_mapping(
        ClerkIdentity(subject="user_patient", source="clerk"),
        production_settings(),
    )

    assert principal.patient_id == 107
    assert FakeDataApi.inserted == [
        (
            "patient_accounts",
            {"clerk_user_id": "user_patient", "patient_id": 107, "active": True},
        )
    ]
