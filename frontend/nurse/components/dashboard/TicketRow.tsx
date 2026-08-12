import { TriangleAlert } from "lucide-react";

import type { QueueTicket } from "@epicenter/shared/contracts";

import styles from "./Dashboard.module.css";

function counterValue(counter: string | null | undefined) {
  if (!counter) return counter;
  const match = /^(?:Counter|Review)\s+(\d+)$/i.exec(counter);
  return match ? match[1] : counter;
}

function timeLabel(value: string | null | undefined) {
  if (!value) return null;
  return new Intl.DateTimeFormat("en-SG", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "UTC" }).format(
    new Date(value),
  );
}

export function TicketRow({ ticket, onOpenReview }: { ticket: QueueTicket; onOpenReview: (ticket: QueueTicket) => void }) {
  const counter = counterValue(ticket.actual_counter ?? ticket.expected_counter);
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

  return (
    <article
      aria-label={needsAttention ? `Resolve issue for ${ticket.patient_name}` : undefined}
      className={`${styles.card} ${stateClass} ${needsAttention ? styles.card_clickable : ""}`}
      onClick={needsAttention ? () => onOpenReview(ticket) : undefined}
      onKeyDown={
        needsAttention
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onOpenReview(ticket);
              }
            }
          : undefined
      }
      role={needsAttention ? "button" : undefined}
      tabIndex={needsAttention ? 0 : undefined}
    >
      <header className={styles.cardHead}>
        <span className={styles.cardId}>{ticket.id}</span>
        {needsAttention ? <TriangleAlert aria-hidden="true" className={styles.attentionFlag} size={16} strokeWidth={2.4} /> : null}
      </header>
      <h3 className={styles.cardName}>{ticket.patient_name}</h3>
      <span className={styles.cardStatus}>Status: {statusLabel}</span>
      {counter || secondStat ? (
        <dl className={styles.cardStats}>
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
    </article>
  );
}
