from app.data.operations_repository import SupabaseOperationsRepository
from app.domain.models import (
    IdentityConfirmRequest,
    KioskCheckInRequest,
    OnboardingAdvanceRequest,
    OnboardingStep,
    QuestionnaireSaveRequest,
    ReadinessState,
    TicketTransitionRequest,
)


class FakeApi:
    def __init__(self) -> None:
        self.rpc_calls: list[tuple[str, dict[str, object]]] = []

    def select(self, table, fields="*", *, filters=None, order=None, limit=None):
        if table == "queue_entries":
            return [
                {
                    "id": "Q-017",
                    "patient_reference": "P-0442",
                    "patient_name_snapshot": "Mei Chen",
                    "intake_type": "walk_in",
                    "visit_status": "ongoing",
                    "readiness_state": "processing",
                    "readiness_reason": "processing",
                    "scheduled_at": None,
                    "checked_in_at": "2026-08-12T09:34:00+00:00",
                    "original_ordering_at": "2026-08-12T09:34:00+00:00",
                    "waiting_minutes": 8,
                    "expected_counter_number": None,
                    "counter_number": "Kiosk A",
                    "processing_stage": "Document extraction",
                    "service_target": "on_track",
                    "staff_confirmed": False,
                    "clinical_escalation": False,
                    "version": 1,
                }
            ]
        return []

    def rpc(self, function_name, parameters):
        self.rpc_calls.append((function_name, parameters))
        if function_name == "epicenter_transition_ticket":
            row = self.select("queue_entries")[0]
            return {
                **row,
                "readiness_state": parameters["p_readiness_state"],
                "readiness_reason": parameters["p_reason"],
                "processing_stage": "Assisted review",
                "version": 2,
            }
        if function_name == "epicenter_create_walk_in_ticket":
            row = self.select("queue_entries")[0]
            return {**row, "id": "Q-100", "patient_name_snapshot": parameters["p_patient_name"]}
        if function_name == "epicenter_get_onboarding":
            return {
                "clerk_user_id": parameters["p_clerk_user_id"],
                "patient_id": parameters["p_patient_id"],
                "appointment_id": parameters.get("p_appointment_reference") or "",
                "current_step": "singpass",
                "completed": False,
                "singpass_authenticated": False,
                "insurance_completed": False,
                "questionnaire_completed": False,
                "singpass_profile": [],
                "version": 1,
            }
        if function_name == "epicenter_advance_onboarding":
            return {
                "clerk_user_id": parameters["p_clerk_user_id"],
                "patient_id": parameters["p_patient_id"],
                "appointment_id": "APT-DEMO-014",
                "current_step": "insurance",
                "completed": False,
                "singpass_authenticated": True,
                "insurance_completed": False,
                "questionnaire_completed": False,
                "singpass_profile": parameters["p_singpass_profile"],
                "version": 2,
            }
        if function_name == "epicenter_get_questionnaire":
            return {
                "appointment_id": parameters["p_appointment_reference"],
                "appointment_db_id": "appointment_014",
                "patient_id": parameters["p_patient_id"],
                "answers": {"gender": "Male"},
                "declaration_acknowledged": False,
                "status": "draft",
                "version": 1,
            }
        if function_name == "epicenter_save_questionnaire":
            return {
                "appointment_id": parameters["p_appointment_reference"],
                "appointment_db_id": "appointment_014",
                "patient_id": parameters["p_patient_id"],
                "answers": parameters["p_answers"],
                "declaration_acknowledged": parameters["p_declaration_acknowledged"],
                "status": "submitted" if parameters["p_submit"] else "draft",
                "version": int(parameters["p_expected_version"]) + 1,
            }
        if function_name == "epicenter_confirm_identity":
            row = self.select("queue_entries")[0]
            return {**row, "identity_confirmed": True, "ecard_verified": True, "version": 2}
        raise AssertionError(function_name)


def test_transition_uses_transactional_rpc_with_concurrency_and_idempotency() -> None:
    api = FakeApi()
    repository = SupabaseOperationsRepository(api)  # type: ignore[arg-type]
    ticket = repository.find_ticket("Q-017")
    assert ticket is not None
    request = TicketTransitionRequest(
        readiness_state=ReadinessState.NEEDS_REVIEW,
        reason="ambiguous_match",
        expected_version=1,
        idempotency_key="transition-017-test",
    )

    updated = repository.transition_ticket(ticket.id, request, "synthetic-staff")

    assert updated.version == 2
    assert api.rpc_calls == [
        (
            "epicenter_transition_ticket",
            {
                "p_ticket_id": "Q-017",
                "p_expected_version": 1,
                "p_readiness_state": "needs_review",
                "p_reason": "ambiguous_match",
                "p_staff_confirmed": False,
                "p_actor_reference": "synthetic-staff",
                "p_idempotency_key": "transition-017-test",
            },
        )
    ]


def test_walk_in_uses_transactional_rpc_and_preserves_one_ticket() -> None:
    api = FakeApi()
    repository = SupabaseOperationsRepository(api)  # type: ignore[arg-type]
    request = KioskCheckInRequest(
        patient_name="Jamie Tan",
        nurse_supervisor="Nurse Noor",
        idempotency_key="walk-in-jamie-test",
    )

    ticket = repository.add_walk_in(request, "synthetic-staff")

    assert ticket.id == "Q-100"
    assert len(api.rpc_calls) == 1
    assert api.rpc_calls[0][0] == "epicenter_create_walk_in_ticket"


def test_onboarding_state_uses_supabase_rpc() -> None:
    api = FakeApi()
    repository = SupabaseOperationsRepository(api)  # type: ignore[arg-type]

    state = repository.get_onboarding_state("clerk_user_abc", patient_id=14)
    assert state.current_step is OnboardingStep.SINGPASS
    assert state.completed is False
    assert state.appointment_id == "pending-booking"

    advanced = repository.advance_onboarding(
        OnboardingAdvanceRequest(
            step=OnboardingStep.SINGPASS,
            singpass_authenticated=True,
            idempotency_key="onboard-singpass-supabase",
        ),
        "clerk_user_abc",
        patient_id=14,
    )
    assert advanced.current_step is OnboardingStep.INSURANCE
    assert advanced.singpass_authenticated is True
    assert api.rpc_calls[-1][0] == "epicenter_advance_onboarding"
    assert api.rpc_calls[-1][1]["p_clerk_user_id"] == "clerk_user_abc"


def test_questionnaire_save_uses_supabase_rpc_after_local_validation() -> None:
    api = FakeApi()
    repository = SupabaseOperationsRepository(api)  # type: ignore[arg-type]

    draft = repository.get_patient_questionnaire("APT-DEMO-014", patient_id=14)
    assert draft.status.value == "draft"
    assert any(field.field_id == "gender" for field in draft.fields)

    saved = repository.save_patient_questionnaire(
        QuestionnaireSaveRequest(
            appointment_id="APT-DEMO-014",
            answers={
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
            declaration_acknowledged=True,
            submit=True,
            expected_version=1,
            idempotency_key="questionnaire-supabase-1",
        ),
        "clerk_user_abc",
        patient_id=14,
    )
    assert saved.status.value == "submitted"
    assert api.rpc_calls[-1][0] == "epicenter_save_questionnaire"


def test_identity_confirmation_uses_supabase_rpc() -> None:
    api = FakeApi()
    repository = SupabaseOperationsRepository(api)  # type: ignore[arg-type]
    request = IdentityConfirmRequest(
        expected_version=1,
        idempotency_key="identity-017-test",
    )

    ticket = repository.confirm_identity("Q-017", request, "nurse-demo")

    assert ticket.identity_confirmed is True
    assert ticket.ecard_verified is True
    assert ticket.version == 2
    assert api.rpc_calls == [
        (
            "epicenter_confirm_identity",
            {
                "p_ticket_id": "Q-017",
                "p_expected_version": 1,
                "p_ecard_not_applicable": False,
                "p_ecard_na_reason": None,
                "p_actor_reference": "nurse-demo",
                "p_idempotency_key": "identity-017-test",
            },
        )
    ]
