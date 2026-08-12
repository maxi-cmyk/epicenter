import { RefreshCw } from "lucide-react";

import type { QueueTicket, VisitPhase } from "@epicenter/shared/contracts";
import { Button } from "@epicenter/shared/ui/Button";

import { TicketRow } from "./TicketRow";
import styles from "./Dashboard.module.css";

const columns: Array<{ phase: VisitPhase; label: string }> = [
  { phase: "incoming", label: "Incoming" },
  { phase: "ongoing", label: "Ongoing" },
  { phase: "finished", label: "Finished" },
];

export function PatientFlowBoard({
  loading,
  onOpenReview,
  onRefresh,
  tickets,
}: {
  loading: boolean;
  onOpenReview: (ticket: QueueTicket) => void;
  onRefresh: () => void;
  tickets: QueueTicket[];
}) {
  return (
    <section aria-labelledby="patient-flow-title" className={styles.flowBoard}>
      <header className={styles.boardHeader}>
        <h2 id="patient-flow-title">Patient readiness board</h2>
        <div className={styles.boardHeaderRight}>
          <Button
            className={styles.boardRefresh}
            disabled={loading}
            icon={<RefreshCw aria-hidden="true" size={13} />}
            onClick={() => void onRefresh()}
            variant="secondary"
          >
            Refresh
          </Button>
          <div className={styles.boardLegend}>
            <span><i className={styles.readyKey} /> Ready</span>
            <span><i className={styles.reviewKey} /> Review</span>
            <span><i className={styles.processingKey} /> Processing</span>
          </div>
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
              </div>
              <div className={styles.cardStack}>
                {columnTickets.length > 0 ? (
                  columnTickets.map((ticket) => <TicketRow key={ticket.id} onOpenReview={onOpenReview} ticket={ticket} />)
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
