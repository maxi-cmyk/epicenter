from app.domain.models import RecommendationDecisionRequest


class InvalidDecision(ValueError):
    pass


def normalize_decision(request: RecommendationDecisionRequest) -> str:
    decision = request.decision.strip().lower()
    if decision not in {"approved", "rejected"}:
        raise InvalidDecision("Decision must be approved or rejected.")
    return decision
