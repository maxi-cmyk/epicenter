import asyncio
from types import SimpleNamespace

import httpx
from openai import APIConnectionError

from app.ai.assistant import run_nurse_assistant
from app.core.auth import StaffPrincipal
from app.core.config import Settings


class FakeResponses:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.requests: list[dict[str, object]] = []

    async def create(self, **kwargs):
        self.requests.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, responses: FakeResponses) -> None:
        self.responses = responses


def principal(role: str = "registration") -> StaffPrincipal:
    return StaffPrincipal(
        subject="staff-test",
        source="test",
        factor_verification_age=(0, -1),
        role=role,
        clinic_id="clinic_harbourfront",
    )


async def unused_dispatcher(*_args):
    raise AssertionError("No tool call was expected")


def test_assistant_returns_bounded_usage_metadata() -> None:
    response = SimpleNamespace(
        id="resp_test_123",
        output=[],
        output_text="The oldest administrative exception is Q-018.",
        usage=SimpleNamespace(input_tokens=21, output_tokens=9, total_tokens=30),
    )
    responses = FakeResponses(response=response)
    settings = Settings(
        openai_api_key="test-key",
        openai_max_output_tokens=450,
        persistence_mode="demo",
        _env_file=None,
    )

    result = asyncio.run(
        run_nurse_assistant(
            FakeClient(responses),  # type: ignore[arg-type]
            settings=settings,
            principal=principal(),
            user_message="Which administrative exception should I handle first?",
            tool_dispatcher=unused_dispatcher,
        )
    )

    assert result.openai_response_id == "resp_test_123"
    assert result.model == settings.openai_model
    assert result.usage is not None
    assert result.usage.total_tokens == 30
    assert responses.requests[0]["store"] is False
    assert responses.requests[0]["max_output_tokens"] == 450
    assert "api_key" not in responses.requests[0]


def test_assistant_provider_failure_returns_safe_dashboard_fallback() -> None:
    error = APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))
    responses = FakeResponses(error=error)
    settings = Settings(openai_api_key="test-key", persistence_mode="demo", _env_file=None)

    result = asyncio.run(
        run_nurse_assistant(
            FakeClient(responses),  # type: ignore[arg-type]
            settings=settings,
            principal=principal(),
            user_message="Summarize the queue.",
            tool_dispatcher=unused_dispatcher,
        )
    )

    assert result.openai_response_id is None
    assert result.source_labels == []
    assert "dashboard directly" in result.content
