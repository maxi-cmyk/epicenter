from app.data.operations_repository import SupabaseOperationsRepository
from app.domain.models import KioskCheckInRequest, ReadinessState, TicketTransitionRequest


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
