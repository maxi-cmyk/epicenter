"""OpenAI Responses API adapter.

Single shared entry point for all OpenAI interactions. Reads credentials from
Settings. Never logs the API key, raw document content, or patient identifiers.
"""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Module-level client — created once per process, shared across requests.
_client: AsyncOpenAI | None = None
_client_configuration: tuple[str, float, int] | None = None


def get_openai_client(settings: Settings) -> AsyncOpenAI:
    """Return the module-level AsyncOpenAI client, initialising it on first call."""
    global _client, _client_configuration
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. "
            "Set it as a server-side environment variable."
        )
    configuration = (
        settings.openai_api_key,
        settings.openai_timeout_seconds,
        settings.openai_max_retries,
    )
    if _client is None or _client_configuration != configuration:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
        _client_configuration = configuration
    return _client


async def create_response(
    client: AsyncOpenAI,
    *,
    model: str,
    input_messages: list[dict[str, Any]],
    text_format: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    store: bool = False,
    metadata: dict[str, str] | None = None,
    max_output_tokens: int | None = None,
) -> Any:
    """Thin wrapper around the OpenAI Responses API.

    Uses store=False by default so document content is not retained on OpenAI's
    servers beyond the request lifetime.

    Raises OpenAIError on provider failure — callers are responsible for
    catching and converting this into an appropriate HTTP or job error.
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "input": input_messages,
        "store": store,
    }
    if text_format is not None:
        kwargs["text"] = {"format": text_format}
    if tools is not None:
        kwargs["tools"] = tools
    if metadata is not None:
        kwargs["metadata"] = metadata
    if max_output_tokens is not None:
        kwargs["max_output_tokens"] = max_output_tokens

    try:
        response = await client.responses.create(**kwargs)
        logger.info(
            "OpenAI response received",
            extra={
                "model": model,
                "response_id": getattr(response, "id", None),
                "usage_input": getattr(getattr(response, "usage", None), "input_tokens", None),
                "usage_output": getattr(getattr(response, "usage", None), "output_tokens", None),
            },
        )
        return response
    except OpenAIError as exc:
        logger.error("OpenAI API error: %s", type(exc).__name__)
        raise
