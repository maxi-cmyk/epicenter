"use client";

import { RefreshCw, TriangleAlert } from "lucide-react";
import { useMemo } from "react";

import type { QueueTicket, ReviewCase, VisitPhase } from "@epicenter/shared/contracts";
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
  onRefresh,
  reviewCases,
  tickets,
}: {
  loading: boolean;
  onRefresh: () => void;
  reviewCases: ReviewCase[];
  tickets: QueueTicket[];
}) {
  const reviewByTicket = useMemo(
    () => new Map(reviewCases.map((reviewCase) => [reviewCase.ticket_id, reviewCase])),
    [reviewCases],
  );
  const exceptions = useMemo(
    () =>
      tickets
        .filter((ticket) => ticket.readiness_state === "needs_review" && ticket.visit_phase !== "finished")
        .sort((left, right) => right.waiting_minutes - left.waiting_minutes),
    [tickets],
  );
  const nextException = exceptions[0];

  return (
    <section aria-labelledby="patient-flow-title" className={styles.flowBoard}>
      <header className={styles.boardHeader}>
        <div>
          <h1 id="patient-flow-title">Patient readiness board</h1>
          <p>Three visit phases, ordered around the patients who need staff confirmation first.</p>
        </div>
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
      {nextException ? (
        <div className={styles.exceptionBar} role="status">
          <TriangleAlert aria-hidden="true" size={20} />
          <div>
            <strong>{exceptions.length} {exceptions.length === 1 ? "patient needs" : "patients need"} confirmation</strong>
            <span>
              Next: {nextException.id} · {nextException.patient_name} · waiting {nextException.waiting_minutes} min
            </span>
          </div>
        </div>
      ) : (
        <div className={styles.clearBar} role="status">
          No administrative exceptions need confirmation right now.
        </div>
      )}
      <div className={styles.columns}>
        {columns.map((column) => {
          const columnTickets = tickets
            .filter((ticket) => ticket.visit_phase === column.phase)
            .sort((left, right) => {
              const attentionDifference =
                Number(right.readiness_state === "needs_review") - Number(left.readiness_state === "needs_review");
              return attentionDifference || right.waiting_minutes - left.waiting_minutes;
            });
          return (
            <div className={`${styles.column} ${column.phase === "finished" ? styles.finishedColumn : ""}`} key={column.phase}>
              <div className={styles.columnHead}>
                <strong>{column.label}</strong>
                <span>{columnTickets.length}</span>
              </div>
              <div className={styles.cardStack}>
                {columnTickets.length > 0 ? (
                  columnTickets.map((ticket) => (
                    <TicketRow key={ticket.id} reviewCase={reviewByTicket.get(ticket.id)} ticket={ticket} />
                  ))
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
