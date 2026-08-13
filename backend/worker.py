"""Postgres-backed document job worker.

Runs as a separate process on Railway (epicenter-worker). Polls the
document_jobs table, claims jobs transactionally, downloads from private
Supabase Storage, invokes the OpenAI extraction adapter, validates the
Structured Output, and writes per-field confidence plus page/excerpt evidence.

Constraints from techStack.md / openai_integration.md:
- store=False: documents are not retained on OpenAI's servers.
- Identity/e-card images must NEVER enter this pipeline.
- Retries are bounded and idempotent.
- The original document stays only in private Supabase Storage.
- No long-lived signed URL is placed in a model request or log.

Usage (Railway epicenter-worker start command):
    python -m backend.worker
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

# Maximum retries per job before marking final_failed
MAX_RETRIES = 3
# Poll interval in seconds
POLL_INTERVAL = 5
# Download timeout (seconds)
DOWNLOAD_TIMEOUT = 30


async def _process_one_job(settings: "Settings", client: "AsyncOpenAI") -> bool:  # type: ignore[name-defined]
    """Claim and process one pending document job. Returns True if a job was found."""
    from app.core.config import get_settings
    from app.data.supabase_client import SupabaseDataApi, SupabaseDataError

    if not settings.supabase_configured:
        logger.warning("Supabase not configured — worker idle.")
        return False

    api = SupabaseDataApi(settings.supabase_url, settings.supabase_secret_key)
    try:
        # Claim one queued job transactionally using Supabase RPC
        # This calls a stored procedure that atomically sets status='processing'
        # and returns the claimed row — preventing double-processing.
        rows = api.rpc(
            "claim_document_job",
            {"worker_id": f"worker-{os.getpid()}"},
        )
    except SupabaseDataError as exc:
        logger.error("Failed to claim document job: %s", exc)
        api.close()
        return False

    if not rows:
        api.close()
        return False

    # rpc may return a list (SETOF) or a single dict
    job = rows[0] if isinstance(rows, list) else rows
    job_id = str(job["id"])
    document_id = str(job["document_id"])
    retry_count = int(job.get("retry_count", 0))
    file_path = str(job.get("storage_path", ""))

    logger.info("Claimed job %s for document %s", job_id, document_id)

    try:
        # Download the document from private Supabase Storage
        # We use a short-lived signed URL that is not logged
        import httpx

        try:
            signed = api.rpc(
                "create_signed_document_url",
                {"storage_path": file_path, "expires_in": 120},
            )
            # rpc may return dict or list
            signed_row = signed[0] if isinstance(signed, list) else signed
            signed_url = signed_row["signed_url"]
        except (SupabaseDataError, KeyError, IndexError, TypeError) as exc:
            raise WorkerError(f"Could not create signed URL: {exc}") from exc

        async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT) as http:
            resp = await http.get(signed_url)
            resp.raise_for_status()
            file_bytes = resp.content

        # Determine MIME type from storage_path
        if file_path.lower().endswith(".pdf"):
            mime_type = "application/pdf"
        elif file_path.lower().endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        elif file_path.lower().endswith(".png"):
            mime_type = "image/png"
        else:
            raise WorkerError(f"Unsupported file extension in storage path: {file_path}")

        # Run extraction
        from app.ai.extraction import extract_document, ExtractionError
        from app.ai.schemas import ApprovedDocumentDataClass, ClassificationInput
        from app.services.document_classification import classify_document

        data_classification = ApprovedDocumentDataClass(str(job.get("data_classification") or "synthetic"))
        classification = classify_document(
            ClassificationInput(
                page_count=int(job.get("page_count") or 1),
                has_letterhead=bool(job.get("has_letterhead")),
                handwritten=bool(job.get("handwritten")),
                has_table_grid=bool(job.get("has_table_grid")),
                top_text=str(job.get("classification_text") or ""),
                field_labels=list(job.get("field_labels") or []),
                layout_fingerprint=job.get("layout_fingerprint"),
                data_classification=data_classification,
            )
        )

        result = await extract_document(
            client,
            settings=settings,
            document_id=document_id,
            job_id=job_id,
            file_bytes=file_bytes,
            file_name=file_path.split("/")[-1],
            mime_type=mime_type,
            classification=classification,
            data_classification=data_classification,
        )

        ticket_id = job.get("ticket_id")
        if ticket_id:
            classification_payload = result.classification.model_dump()
            classification_payload["data_classification"] = data_classification.value
            coverage_payload = result.coverage.model_dump()
            source_evidence = {
                key: value
                for key, value in coverage_payload.items()
                if key.endswith("_evidence") and value is not None
            }
            facts = {
                key: value
                for key, value in coverage_payload.items()
                if not key.endswith("_evidence")
            }
            api.rpc(
                "epicenter_stage_document_extraction",
                {
                    "p_ticket_id": str(ticket_id),
                    "p_document_id": document_id,
                    "p_classification": classification_payload,
                    "p_facts": facts,
                    "p_source_evidence": source_evidence,
                    "p_actor_reference": f"worker:{os.getpid()}",
                    "p_idempotency_key": f"stage-extraction:{job_id}",
                },
            )
        # Mark ready only after pending-review staging succeeds.
        api.patch(
            "document_jobs",
            {
                "status": "ready",
                "model_used": result.model_used,
                "prompt_version": result.prompt_version,
                "extraction_result": {
                    "facts": result.coverage.model_dump(),
                    "classification": result.classification.model_dump(),
                    "review_status": result.review_status,
                },
                "overall_confidence": result.coverage.overall_confidence,
                "raw_response_id": result.raw_response_id,
                "completed_at": datetime.now(UTC).isoformat(),
            },
            filters={"id": f"eq.{job_id}"},
        )
        logger.info("Job %s completed successfully.", job_id)
        return True

    except WorkerError as exc:
        logger.error("Worker error on job %s: %s", job_id, exc)
        _mark_failed(api, job_id, str(exc), retry_count)
        return True
    except Exception as exc:
        logger.exception("Unexpected error on job %s: %s", job_id, exc)
        _mark_failed(api, job_id, f"Unexpected: {type(exc).__name__}", retry_count)
        return True
    finally:
        api.close()


def _mark_failed(
    api: "SupabaseDataApi",  # type: ignore[name-defined]
    job_id: str,
    reason: str,
    retry_count: int,
) -> None:
    is_final = retry_count >= MAX_RETRIES - 1
    api.patch(
        "document_jobs",
        {
            "status": "failed_final" if is_final else "failed_retryable",
            "failure_reason": reason[:500],
            "retry_count": retry_count + 1,
            "failed_at": datetime.now(UTC).isoformat(),
        },
        filters={"id": f"eq.{job_id}"},
    )
    if is_final:
        logger.error("Job %s marked final_failed after %d attempts.", job_id, retry_count + 1)
    else:
        logger.warning("Job %s marked retryable (attempt %d).", job_id, retry_count + 1)


async def run_worker() -> None:
    """Main worker loop. Runs until interrupted."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Epicenter document worker starting.")

    from app.core.config import get_settings
    settings = get_settings()

    if not settings.openai_configured:
        logger.error("OPENAI_API_KEY is not configured. Worker cannot process documents.")
        sys.exit(1)

    from app.ai.client import get_openai_client
    client = get_openai_client(settings)

    logger.info(
        "Worker ready. model=%s poll_interval=%ds",
        settings.openai_extraction_model,
        POLL_INTERVAL,
    )

    while True:
        try:
            found = await _process_one_job(settings, client)
            if not found:
                await asyncio.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Worker interrupted — shutting down.")
            break
        except Exception as exc:
            logger.exception("Worker loop error: %s", exc)
            await asyncio.sleep(POLL_INTERVAL)


class WorkerError(Exception):
    """Raised for recoverable worker errors (wrong MIME, download failure, etc.)."""


if __name__ == "__main__":
    asyncio.run(run_worker())
