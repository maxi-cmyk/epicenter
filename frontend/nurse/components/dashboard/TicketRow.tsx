import { TriangleAlert } from "lucide-react";
import Link from "next/link";

import type { QueueTicket, ReviewCase } from "@epicenter/shared/contracts";

import styles from "./Dashboard.module.css";

function isFastLane(ticket: QueueTicket) {
  return ticket.intake_type === "booked" && ticket.readiness_state === "ready";
}

function assignedCounter(ticket: QueueTicket) {
  const raw = ticket.actual_room ?? ticket.expected_room;
  if (raw && /^[FS]\d+$/i.test(raw)) return raw.toUpperCase();

  const fast = isFastLane(ticket);
  const numbered = raw ? /(?:Room|Counter|Review)\s+(\d+)/i.exec(raw) : null;
  if (numbered) {
    const index = Number(numbered[1]);
    return fast ? `F${Math.min(Math.max(index, 1), 2)}` : `S${Math.min(Math.max(index, 1), 4)}`;
  }
  if (raw && /kiosk/i.test(raw)) return "S1";

  const serial = Number(ticket.id.replace(/\D/g, "")) || 1;
  return fast ? `F${((serial - 1) % 2) + 1}` : `S${((serial - 1) % 4) + 1}`;
}

export function TicketRow({ reviewCase, ticket }: { reviewCase?: ReviewCase; ticket: QueueTicket }) {
  const counter = assignedCounter(ticket);
  const queueNumber = ticket.queue_number || ticket.id;
  const needsAttention = ticket.readiness_state === "needs_review";
  const stateClass = needsAttention
    ? styles.card_flagged
    : ticket.readiness_state === "processing"
      ? styles.card_processing
      : "";
  const isFinished = ticket.visit_phase === "finished";
  const confirmedDocuments = ticket.documents.filter((document) => document.confirmed).length;
  const statusLabel = ticket.processing_stage.replace(/\s+\d{1,2}:\d{2}$/, "");
  const secondStat = isFinished
    ? { label: "Est. completion", value: ticket.processing_stage.replace(/^Completed\s+/i, "") }
      : ticket.visit_phase === "incoming"
      ? null
      : ticket.waiting_minutes
        ? { label: "Est. finish", value: `${ticket.waiting_minutes} min` }
        : null;

  const cardBody = (
    <>
      <header className={styles.cardHead}>
        <span className={styles.cardId}>{ticket.id}</span>
        <span className={styles.cardHeadRight}>
          {ticket.documents.length > 0 ? (
            <span className={styles.tpaBadge}>{confirmedDocuments}/{ticket.documents.length} verified</span>
          ) : null}
          {needsAttention ? (
            <span className={styles.attentionFlag}>
              <TriangleAlert aria-hidden="true" size={15} strokeWidth={2.4} />
              Needs confirmation
            </span>
          ) : null}
        </span>
      </header>
      <h3 className={styles.cardName}>{ticket.patient_name}</h3>
      <span className={styles.cardStatus}>Status: {statusLabel}</span>
      {needsAttention && reviewCase ? (
        <div className={styles.exceptionDetail}>
          <strong>{reviewCase.reason_label}</strong>
          <span>{reviewCase.next_action}</span>
        </div>
      ) : null}
      {queueNumber || counter || secondStat ? (
        <dl className={styles.cardStats}>
          {queueNumber ? (
            <div>
              <dt>Queue</dt>
              <dd>{queueNumber}</dd>
            </div>
          ) : null}
          {counter ? (
            <div>
              <dt>Counter</dt>
              <dd>{counter}</dd>
            </div>
          ) : null}
          {secondStat ? (
            <div>
              <dt>{secondStat.label}</dt>
              <dd>{secondStat.value}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
    </>
  );

  if (isFinished) {
    return <article className={`${styles.card} ${styles.card_finished} ${stateClass}`}>{cardBody}</article>;
  }

  return (
    <Link
      aria-label={`Open task for ${ticket.patient_name}`}
      className={`${styles.card} ${stateClass} ${styles.card_clickable}`}
      href={`/tasks/${ticket.id}`}
    >
      {cardBody}
    </Link>
  );
}
