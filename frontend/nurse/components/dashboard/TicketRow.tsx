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
    <article className={`${styles.ticketRow} ${styles[`ticket_${ticket.readiness_state}`]}`}>
      <div className={styles.patientCell}>
        <strong>{ticket.id}</strong>
        <span>{ticket.patient_name}</span>
        <small>{ticket.intake_type === "walk_in" ? "Walk-in" : `${timeLabel(ticket)} booked`}</small>
      </div>
      <div className={styles.routeCell}>
        <span>{ticket.actual_counter ?? ticket.expected_counter ?? "Unassigned"}</span>
        <small>{ticket.actual_counter ? "Actual route" : "Expected route"}</small>
      </div>
      <div className={styles.stageCell}>
        <span>{ticket.processing_stage}</span>
        <small>{ticket.staff_confirmed ? "Staff confirmed" : "Confirmation pending"}</small>
      </div>
      <div className={styles.waitCell}>
        <Clock3 aria-hidden="true" size={15} />
        <span>{ticket.waiting_minutes ? `${ticket.waiting_minutes} min` : "Not arrived"}</span>
      </div>
      <div className={styles.statusCell}>
        <StatusBadge state={ticket.readiness_state} />
        {ticket.readiness_state === "needs_review" ? (
          <Link aria-label={`Open review for ${ticket.patient_name}`} href="/review"><ArrowRight aria-hidden="true" size={18} /></Link>
        ) : null}
      </div>
    </article>
  );
}
