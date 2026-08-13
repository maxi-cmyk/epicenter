"""Document extraction orchestration.

Sends a coverage document (PDF or image) to the configured extraction model
with a strict Structured Output schema. Validates the response and returns
an ExtractionResult with per-field source evidence.

Constraints from openai_integration.md / techStack.md:
- Uses store=False so documents are not retained on OpenAI's servers.
- If a temporary file upload is needed, it is deleted immediately after the request.
- Identity/e-card images must NEVER enter this pipeline.
- The result is advisory: deterministic eligibility rules make coverage decisions.
"""

from __future__ import annotations

import logging

from openai import AsyncOpenAI, OpenAIError

from app.ai.client import create_response
from app.ai.schemas import ApprovedDocumentDataClass, DocumentClassification, ExtractedCoverage, ExtractionResult
from app.core.config import Settings

logger = logging.getLogger(__name__)

# Prompt version tracked with every extraction job for reproducibility.
PROMPT_VERSION = "v1.0.0"

_SYSTEM_PROMPT = """
You are a medical document extraction assistant for Epicenter, a clinic pre-registration system.

Your task is to extract structured coverage information from the provided document.
Follow these rules strictly:
1. Extract only what is explicitly present in the document — never invent or infer values.
2. Leave a field null/None if the information is absent or unreadable.
3. For every non-null field, provide page number and a verbatim or near-verbatim excerpt as evidence.
4. Set confidence to "high" only when the text is clear and unambiguous.
5. Do NOT extract identity, NRIC, passport numbers, biometrics, or any personal identifiers.
6. Do NOT make eligibility decisions. Only extract facts from the document.
7. List all regions you could not read reliably in unreadable_regions.
""".strip()


def _build_extraction_schema() -> dict:
    """Return the JSON Schema for ExtractedCoverage as a Structured Output spec."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "extracted_coverage",
            "strict": True,
            "schema": ExtractedCoverage.model_json_schema(),
        },
    }


async def extract_document(
    client: AsyncOpenAI,
    *,
    settings: Settings,
    document_id: str,
    job_id: str,
    file_bytes: bytes,
    file_name: str,
    mime_type: str = "application/pdf",
    classification: DocumentClassification,
    data_classification: ApprovedDocumentDataClass,
) -> ExtractionResult:
    """Send a document to OpenAI and return a validated ExtractionResult.

    Args:
        client: Shared AsyncOpenAI client.
        settings: Application settings (provides extraction model name).
        document_id: Epicenter document record ID (for audit, not sent to OpenAI).
        job_id: Epicenter job ID (for audit).
        file_bytes: Raw document bytes (PDF, JPG, or PNG).
        file_name: Original file name — used only for logging (no PII).
        mime_type: MIME type of the document.

    Returns:
        ExtractionResult with validated ExtractedCoverage and metadata.

    Raises:
        ExtractionError: On OpenAI failure, schema validation failure, or unsupported input.
    """
    if mime_type not in ("application/pdf", "image/jpeg", "image/png"):
        raise ExtractionError(f"Unsupported MIME type for extraction: {mime_type}")
    if data_classification not in {
        ApprovedDocumentDataClass.SYNTHETIC,
        ApprovedDocumentDataClass.FORMALLY_DEIDENTIFIED,
    }:
        raise ExtractionError("Only synthetic or formally de-identified documents may be sent to OpenAI.")

    model = settings.openai_extraction_model
    logger.info(
        "Starting document extraction",
        extra={"job_id": job_id, "model": model, "mime_type": mime_type},
    )

    # Build the input message with the document inline as a base64 data URI.
    # This avoids a separate file upload step and ensures no retained artifact.
    import base64
    data_uri = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode()}"

    input_messages: list[dict] = [
        {
            "role": "system",
            "content": (
                _SYSTEM_PROMPT
                + f"\nUse only the category-specific extractor for category '{classification.category}' "
                + f"and family '{classification.document_family or 'unknown'}'."
            ),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_file",
                    "filename": "document",
                    "file_data": data_uri,
                },
                {
                    "type": "input_text",
                    "text": (
                        "Extract all coverage information from this document. "
                        "Set every absent field to null. Provide source evidence for every non-null field."
                    ),
                },
            ],
        },
    ]

    try:
        response = await create_response(
            client,
            model=model,
            input_messages=input_messages,
            text_format=_build_extraction_schema(),
            store=False,
            metadata={
                "job_id": job_id,
                "prompt_version": PROMPT_VERSION,
                "epicenter_data_classification": data_classification.value,
                "epicenter_document_category": classification.category,
            },
        )
    except OpenAIError as exc:
        raise ExtractionError(f"OpenAI API error during extraction: {type(exc).__name__}") from exc

    # Extract the text output from the response
    try:
        raw_text = response.output_text
    except AttributeError:
        # Fallback for different response shapes
        try:
            raw_text = response.output[0].content[0].text
        except (AttributeError, IndexError, KeyError) as exc:
            raise ExtractionError("Could not read output text from OpenAI response.") from exc

    # Validate against strict schema
    try:
        import json
        coverage_data = json.loads(raw_text)
        coverage = ExtractedCoverage.model_validate(coverage_data)
    except Exception as exc:
        raise ExtractionError(f"Extraction schema validation failed: {exc}") from exc

    return ExtractionResult(
        job_id=job_id,
        document_id=document_id,
        model_used=model,
        prompt_version=PROMPT_VERSION,
        classification=classification,
        review_status="pending_review",
        synthetic=data_classification == ApprovedDocumentDataClass.SYNTHETIC,
        coverage=coverage,
        raw_response_id=getattr(response, "id", None),
    )


class ExtractionError(Exception):
    """Raised when document extraction fails at any stage."""
