import { ArrowRight, Clock3 } from "lucide-react";
import Link from "next/link";

import { StatusBadge } from "@epicenter/shared/ui/StatusBadge";
import type { QueueTicket } from "@epicenter/shared/contracts";

import styles from "./Dashboard.module.css";

function timeLabel(ticket: QueueTicket) {
  const value = ticket.scheduled_at ?? ticket.checked_in_at;
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-SG", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "UTC" }).format(new Date(value));
}

export function TicketRow({ ticket }: { ticket: QueueTicket }) {
  return (
    <article className={`${styles.card} ${styles[`card_${ticket.readiness_state}`]}`}>
      <header className={styles.cardHead}>
        <span className={styles.cardId}>{ticket.id}</span>
        <StatusBadge state={ticket.readiness_state} />
      </header>
      <h3 className={styles.cardName}>{ticket.patient_name}</h3>
      <p className={styles.cardMeta}>{ticket.intake_type === "walk_in" ? "Walk-in" : `${timeLabel(ticket)} booked`}</p>
      <dl className={styles.cardStats}>
        <div>
          <dt>Route</dt>
          <dd>{ticket.actual_counter ?? ticket.expected_counter ?? "Unassigned"}</dd>
        </div>
        <div>
          <dt>Stage</dt>
          <dd>{ticket.processing_stage}</dd>
        </div>
        <div>
          <dt><Clock3 aria-hidden="true" size={12} /> Wait</dt>
          <dd>{ticket.waiting_minutes ? `${ticket.waiting_minutes} min` : "Not arrived"}</dd>
        </div>
      </dl>
      <footer className={styles.cardFoot}>
        <span>{ticket.staff_confirmed ? "Staff confirmed" : "Confirmation pending"}</span>
        {ticket.readiness_state === "needs_review" ? (
          <Link aria-label={`Open review for ${ticket.patient_name}`} className={styles.cardReviewLink} href="/review">
            Review <ArrowRight aria-hidden="true" size={14} />
          </Link>
        ) : null}
      </footer>
    </article>
  );
}
