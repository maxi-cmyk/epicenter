import { TriangleAlert } from "lucide-react";
import Link from "next/link";

import type { QueueTicket, ReviewCase } from "@epicenter/shared/contracts";

import styles from "./Dashboard.module.css";

function roomValue(room: string | null | undefined) {
  if (!room) return room;
  const match = /^(?:Room|Counter|Review)\s+(\d+)/i.exec(room);
  return match ? match[1] : room;
}

export function TicketRow({ reviewCase, ticket }: { reviewCase?: ReviewCase; ticket: QueueTicket }) {
  const room = roomValue(ticket.actual_room ?? ticket.expected_room);
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
      {room || secondStat ? (
        <dl className={styles.cardStats}>
          {room ? (
            <div>
              <dt>Room</dt>
              <dd>{room}</dd>
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
