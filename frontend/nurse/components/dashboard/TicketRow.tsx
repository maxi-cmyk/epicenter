import { TriangleAlert } from "lucide-react";
import Link from "next/link";

import type { QueueTicket } from "@epicenter/shared/contracts";

import styles from "./Dashboard.module.css";

function roomValue(room: string | null | undefined) {
  if (!room) return room;
  const match = /^(?:Room|Counter|Review)\s+(\d+)/i.exec(room);
  return match ? match[1] : room;
}

function timeLabel(value: string | null | undefined) {
  if (!value) return null;
  return new Intl.DateTimeFormat("en-SG", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "UTC" }).format(
    new Date(value),
  );
}

export function TicketRow({ ticket }: { ticket: QueueTicket }) {
  const room = roomValue(ticket.actual_room ?? ticket.expected_room);
  const needsAttention = ticket.readiness_state === "needs_review";
  const stateClass = needsAttention
    ? styles.card_flagged
    : ticket.readiness_state === "processing"
      ? styles.card_processing
      : "";
  const isFinished = ticket.visit_phase === "finished";
  const statusLabel = ticket.processing_stage.replace(/\s+\d{1,2}:\d{2}$/, "");
  const secondStat = isFinished
    ? { label: "Est. completion", value: ticket.processing_stage.replace(/^Completed\s+/i, "") }
    : ticket.visit_phase === "incoming"
      ? { label: "Est. arrival", value: "-" }
      : ticket.waiting_minutes
        ? { label: "Est. finish", value: `${ticket.waiting_minutes} min` }
        : null;

  const cardBody = (
    <>
      <header className={styles.cardHead}>
        <span className={styles.cardId}>{ticket.id}</span>
        <span className={styles.cardHeadRight}>
          {ticket.documents.length > 0 ? <span className={styles.tpaBadge}>Docs</span> : null}
          {needsAttention ? <TriangleAlert aria-hidden="true" className={styles.attentionFlag} size={16} strokeWidth={2.4} /> : null}
        </span>
      </header>
      <h3 className={styles.cardName}>{ticket.patient_name}</h3>
      <span className={styles.cardStatus}>Status: {statusLabel}</span>
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
    return <article className={`${styles.card} ${stateClass}`}>{cardBody}</article>;
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
