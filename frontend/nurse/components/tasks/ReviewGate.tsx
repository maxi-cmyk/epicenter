"use client";

import { useState } from "react";

import { transitionTicket } from "@/lib/api";
import type { QueueTicket, ReviewCase } from "@epicenter/shared/contracts";

import { EvidencePanel, type ReviewResolution } from "../review/EvidencePanel";
import styles from "./Task.module.css";

export function ReviewGate({
  ticket,
  reviewCase,
  refresh,
}: {
  ticket: QueueTicket;
  reviewCase: ReviewCase | undefined;
  refresh: () => Promise<void>;
}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [confirmation, setConfirmation] = useState("");

  const confirmReview = async (resolution: ReviewResolution) => {
    setPending(true);
    setError("");
    setConfirmation("");
    try {
      const reason = `review_resolved:${resolution.method.toLowerCase().replaceAll(" ", "_")}${
        resolution.note ? `:${resolution.note}` : ""
      }`;
      await transitionTicket(ticket.id, ticket.version, "needs_review", reason, true);
      await refresh();
      setConfirmation("Resolution recorded. This visit stays in review until its readiness prerequisites pass.");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not confirm the record.");
    } finally {
      setPending(false);
    }
  };

  return (
    <section aria-labelledby="record-title" className={styles.section}>
      <h2 id="record-title">Needs review before starting</h2>
      <p className={styles.hint}>
        This ticket has an administrative exception that must be resolved before the nurse workflow can begin.
      </p>
      {reviewCase ? (
        <EvidencePanel onConfirm={(resolution) => void confirmReview(resolution)} reviewCase={reviewCase} />
      ) : (
        <div className={styles.notice}>
          <p>No review evidence found for this ticket.</p>
          <p>Return to Dashboard and refresh the visit before trying again.</p>
        </div>
      )}
      {pending ? <p className={styles.hint}>Confirming…</p> : null}
      {confirmation ? <p className={styles.success}>{confirmation}</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}
    </section>
  );
}
