"use client";

import { useReverification } from "@clerk/nextjs";
import Link from "next/link";
import { useState } from "react";

import { transitionTicket } from "@/lib/api";
import type { QueueTicket, ReviewCase } from "@epicenter/shared/contracts";

import { EvidencePanel } from "../review/EvidencePanel";
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

  const reverifiedTransition = useReverification(transitionTicket);

  const confirmReview = async () => {
    setPending(true);
    setError("");
    try {
      await reverifiedTransition(ticket.id, ticket.version, "ready", "all_prerequisites_passed", true);
      await refresh();
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
        <EvidencePanel onConfirm={() => void confirmReview()} reviewCase={reviewCase} />
      ) : (
        <div className={styles.notice}>
          <p>No review evidence found for this ticket.</p>
          <Link className={styles.backLink} href="/review">
            Open the review worklist
          </Link>
        </div>
      )}
      {pending ? <p className={styles.hint}>Confirming…</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}
    </section>
  );
}
