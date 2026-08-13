"""Deterministic, cheapest-first payer-document classification."""

from __future__ import annotations

from app.ai.schemas import ClassificationInput, DocumentClassification
from app.domain.models import DocumentCategory

_FINGERPRINTS: dict[str, tuple[str, DocumentCategory]] = {
    "ge-authorisation-v1": ("GE", DocumentCategory.AUTHORISATION_LETTER),
    "ghs-corp-grid-v1": ("GHS-CORP", DocumentCategory.BENEFIT_STRUCTURE),
    "chas-card-v1": ("CHAS", DocumentCategory.CODING_SCHEME),
    "mhc-panel-v1": ("MHC", DocumentCategory.BENEFIT_STRUCTURE),
}


def classify_document(signals: ClassificationInput) -> DocumentClassification:
    """Apply structural, keyword, fingerprint, then extractor selection in order."""
    structural: list[str] = []
    if signals.page_count > 1:
        structural.append("multi_page")
    else:
        structural.append("single_page")
    if signals.has_letterhead:
        structural.append("letterhead")
    if signals.handwritten:
        structural.append("handwritten")
    if signals.has_table_grid:
        structural.append("table_grid")

    text = " ".join([signals.top_text, *signals.field_labels]).casefold()
    hits: list[str] = []
    family: str | None = None
    category: DocumentCategory | None = None

    keyword_rules = [
        (("i hereby consent", "declaration"), DocumentCategory.FORM, None),
        (("guarantee of payment", "authorises", "please bill to"), DocumentCategory.AUTHORISATION_LETTER, None),
        (("chas blue", "chas orange", "chas green"), DocumentCategory.CODING_SCHEME, "CHAS"),
        (("screening package", " panel"), DocumentCategory.BENEFIT_STRUCTURE, "CORPORATE"),
    ]
    for anchors, matched_category, matched_family in keyword_rules:
        found = [anchor.strip() for anchor in anchors if anchor in text]
        if found and category is None:
            hits.extend(found)
            category = matched_category
            family = matched_family

    for issuer in ("AIA", "GE", "IHP", "MHC"):
        if issuer.casefold() in text:
            hits.append(issuer)
            family = issuer
            if category is None:
                category = (
                    DocumentCategory.AUTHORISATION_LETTER
                    if signals.has_letterhead
                    else DocumentCategory.BENEFIT_STRUCTURE
                )
            break

    fingerprint = signals.layout_fingerprint
    if fingerprint and fingerprint in _FINGERPRINTS:
        fp_family, fp_category = _FINGERPRINTS[fingerprint]
        family = fp_family
        category = fp_category

    if category is None:
        if signals.has_table_grid:
            category = DocumentCategory.BENEFIT_STRUCTURE
        elif signals.has_letterhead:
            category = DocumentCategory.AUTHORISATION_LETTER
        elif signals.page_count > 1 or signals.handwritten:
            category = DocumentCategory.FORM
        else:
            category = DocumentCategory.CODING_SCHEME

    extractor_family = (family or "unknown").lower().replace(" ", "_")
    return DocumentClassification(
        category=category.value,
        document_family=family,
        structural_signals=structural,
        keyword_hits=hits,
        template_fingerprint=fingerprint if fingerprint in _FINGERPRINTS else None,
        extractor=f"{extractor_family}_{category.value}_extractor",
        review_status="pending_review",
        synthetic=signals.data_classification.value == "synthetic",
    )
