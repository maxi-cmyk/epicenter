"""Strict Pydantic schemas for OpenAI document extraction and nurse assistant.

All schemas use model_config = ConfigDict(extra='forbid') so unexpected fields
from the model are rejected rather than silently ignored.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Extraction schemas — used as the Structured Output JSON Schema
# ---------------------------------------------------------------------------


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ABSENT = "absent"


class ApprovedDocumentDataClass(StrEnum):
    SYNTHETIC = "synthetic"
    FORMALLY_DEIDENTIFIED = "formally_deidentified"


class ClassificationInput(BaseModel):
    """Bounded OCR/layout signals; never accepts raw live-patient identifiers."""

    model_config = ConfigDict(extra="forbid")
    page_count: int = Field(ge=1, le=100)
    has_letterhead: bool = False
    handwritten: bool = False
    has_table_grid: bool = False
    top_text: str = Field(default="", max_length=2_000)
    field_labels: list[Annotated[str, Field(max_length=120)]] = Field(default_factory=list, max_length=40)
    layout_fingerprint: str | None = Field(default=None, max_length=160)
    data_classification: ApprovedDocumentDataClass


class DocumentClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: str
    document_family: str | None = None
    structural_signals: list[str]
    keyword_hits: list[str]
    template_fingerprint: str | None = None
    extractor: str
    review_status: str = "pending_review"
    synthetic: bool = True


class FieldEvidence(BaseModel):
    """Source evidence for one extracted field."""

    model_config = ConfigDict(extra="forbid")

    page: int | None = Field(
        default=None,
        description="1-indexed page number where the value was found. Null if not applicable.",
    )
    excerpt: str | None = Field(
        default=None,
        max_length=400,
        description="Verbatim or near-verbatim text fragment supporting the extracted value.",
    )
    confidence: ConfidenceLevel = Field(
        description="Model confidence in this extracted value.",
    )


class ExtractedCoverage(BaseModel):
    """Strict extraction schema for coverage/insurance documents.

    All optional fields are None when absent in the source document — the model
    must NOT invent plausible values. Evidence is required for every non-None field.
    """

    model_config = ConfigDict(extra="forbid")

    document_family: Annotated[str | None, Field(max_length=120)] = None
    issuer_code: Annotated[str | None, Field(max_length=80)] = None
    issuer_name: Annotated[str | None, Field(max_length=200)] = None
    document_type: Annotated[str | None, Field(max_length=120)] = None
    insured_name: Annotated[str | None, Field(max_length=200)] = None
    valid_from: Annotated[str | None, Field(max_length=30)] = None
    valid_to: Annotated[str | None, Field(max_length=30)] = None
    screening_package: Annotated[str | None, Field(max_length=400)] = None
    requested_items: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list,
        description="Individual line-item tests or services listed on the document.",
    )
    billing_arrangement: Annotated[str | None, Field(max_length=400)] = None
    tpa_reference: Annotated[str | None, Field(max_length=200)] = None
    corporate_code: Annotated[str | None, Field(max_length=120)] = None
    authorization_number: Annotated[str | None, Field(max_length=120)] = None
    notes: Annotated[str | None, Field(max_length=600)] = None

    # Per-field evidence — keyed to the field names above
    document_family_evidence: FieldEvidence | None = None
    issuer_code_evidence: FieldEvidence | None = None
    issuer_name_evidence: FieldEvidence | None = None
    document_type_evidence: FieldEvidence | None = None
    insured_name_evidence: FieldEvidence | None = None
    valid_from_evidence: FieldEvidence | None = None
    valid_to_evidence: FieldEvidence | None = None
    screening_package_evidence: FieldEvidence | None = None
    requested_items_evidence: FieldEvidence | None = None
    billing_arrangement_evidence: FieldEvidence | None = None
    tpa_reference_evidence: FieldEvidence | None = None
    corporate_code_evidence: FieldEvidence | None = None
    authorization_number_evidence: FieldEvidence | None = None

    # Overall extraction metadata
    overall_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    extraction_notes: Annotated[str | None, Field(max_length=600)] = None
    unreadable_regions: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list,
        description="Descriptions of regions the model could not read reliably.",
    )


class ExtractionResult(BaseModel):
    """Wrapper returned by the extraction service, including job metadata."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    document_id: str
    model_used: str
    prompt_version: str
    classification: DocumentClassification
    review_status: str = "pending_review"
    synthetic: bool = True
    coverage: ExtractedCoverage
    raw_response_id: str | None = None  # OpenAI response ID for audit


# ---------------------------------------------------------------------------
# Nurse assistant schemas
# ---------------------------------------------------------------------------


class AssistantRequest(BaseModel):
    """One bounded staff question sent to the server-side assistant."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=2, max_length=1_500)


class AssistantUsage(BaseModel):
    """Provider usage returned without exposing prompts, tool payloads, or credentials."""

    model_config = ConfigDict(extra="forbid")

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class AssistantMessage(BaseModel):
    """A single grounded assistant reply returned to the nurse panel."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(description="Grounded, plain-language reply from the assistant.")
    source_labels: list[str] = Field(
        default_factory=list,
        description="Human-readable labels identifying the tool results used (e.g. 'queue snapshot 09:42').",
    )
    snapshot_time: str | None = Field(
        default=None,
        description="ISO timestamp of the most recent data snapshot used.",
    )
    synthetic: bool = True
    openai_response_id: str | None = None
    model: str | None = None
    usage: AssistantUsage | None = None
