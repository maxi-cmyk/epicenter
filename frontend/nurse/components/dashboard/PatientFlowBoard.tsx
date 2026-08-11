import type { QueueTicket, VisitPhase } from "@epicenter/shared/contracts";

import { TicketRow } from "./TicketRow";
import styles from "./Dashboard.module.css";

const sections: Array<{ phase: VisitPhase; label: string; detail: string }> = [
  { phase: "incoming", label: "Incoming", detail: "Booked patients before check-in" },
  { phase: "ongoing", label: "Ongoing", detail: "Checked in on one persistent ticket" },
  { phase: "finished", label: "Finished", detail: "Completed, cancelled or no-show" },
];

export function PatientFlowBoard({ tickets }: { tickets: QueueTicket[] }) {
  return (
    <section aria-labelledby="patient-flow-title" className={styles.flowBoard}>
      <header className={styles.boardHeader}>
        <div>
          <h2 id="patient-flow-title">Patient readiness board</h2>
          <p>Readiness is administrative. Staff-led clinical escalation always takes precedence.</p>
        </div>
        <div className={styles.boardLegend}>
          <span><i className={styles.readyKey} /> Ready</span>
          <span><i className={styles.reviewKey} /> Review</span>
          <span><i className={styles.processingKey} /> Processing</span>
        </div>
      </header>
      <div className={styles.columnLabels} aria-hidden="true">
        <span>Ticket / patient</span>
        <span>Route</span>
        <span>Stage</span>
        <span>Wait</span>
        <span>Status</span>
      </div>
      {sections.map((section) => {
        const phaseTickets = tickets.filter((ticket) => ticket.visit_phase === section.phase);
        return (
          <div className={styles.phaseSection} key={section.phase}>
            <div className={styles.phaseLabel}>
              <strong>{section.label}</strong>
              <span>{phaseTickets.length}</span>
              <small>{section.detail}</small>
            </div>
            <div className={styles.ticketList}>
              {phaseTickets.map((ticket) => <TicketRow key={ticket.id} ticket={ticket} />)}
            </div>
          </div>
        );
      })}
    </section>
  );
}
