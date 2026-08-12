import type { QueueTicket, VisitPhase } from "@epicenter/shared/contracts";

import { TicketRow } from "./TicketRow";
import styles from "./Dashboard.module.css";

const columns: Array<{ phase: VisitPhase; label: string; detail: string }> = [
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
      <div className={styles.columns}>
        {columns.map((column) => {
          const columnTickets = tickets.filter((ticket) => ticket.visit_phase === column.phase);
          return (
            <div className={styles.column} key={column.phase}>
              <div className={styles.columnHead}>
                <strong>{column.label}</strong>
                <span>{columnTickets.length}</span>
                <small>{column.detail}</small>
              </div>
              <div className={styles.cardStack}>
                {columnTickets.length > 0 ? (
                  columnTickets.map((ticket) => <TicketRow key={ticket.id} ticket={ticket} />)
                ) : (
                  <p className={styles.columnEmpty}>No patients here right now.</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
