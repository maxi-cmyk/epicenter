"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { useDashboard } from "@/hooks/useDashboard";
import { isStepUnlocked, type TaskStep } from "@/lib/task-steps";
import type { QueueTicket } from "@epicenter/shared/contracts";
import { Button } from "@epicenter/shared/ui/Button";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";

import { ReviewGate } from "./ReviewGate";
import { TaskSteps } from "./TaskSteps";
import styles from "./Task.module.css";

export function TaskStepShell({
  ticketId,
  step,
  children,
}: {
  ticketId: string;
  step: TaskStep;
  children: (ctx: { ticket: QueueTicket; refresh: () => Promise<void> }) => ReactNode;
}) {
  const { data, error, loading, refresh, source } = useDashboard();

  if (loading) return <LoadingBoard />;

  if (!data) {
    return (
      <section className={styles.taskRecovery} role="alert">
        <h1>Patient task could not be loaded</h1>
        <p>{error || "Check the clinic API connection, then try again."}</p>
        <div>
          <Button onClick={() => void refresh()}>Retry</Button>
          <Link className={styles.backLink} href="/">Return to board</Link>
        </div>
      </section>
    );
  }

  const ticket = data.tickets.find((item) => item.id === ticketId);

  if (!ticket) {
    return (
      <div className={styles.taskPage}>
        <div className={styles.taskHeader}>
          <PageHeader
            actions={
              <Link className={styles.backLink} href="/">
                Back to board
              </Link>
            }
            description="This ticket could not be found. It may have moved out of today's board or the link may be out of date."
            title="Ticket not found"
          />
        </div>
      </div>
    );
  }

  const pageHeader = (
    <div className={styles.taskHeader}>
      <PageHeader
        actions={
          <Link className={styles.backLink} href="/">
            Back to board
          </Link>
        }
        description={`${ticket.id} · ${ticket.intake_type === "walk_in" ? "Walk-in" : "Booked"}`}
        title={ticket.patient_name}
      />
    </div>
  );

  if (source === "fallback") {
    return (
      <div className={styles.taskPage}>
        {pageHeader}
        <section className={styles.fallbackBlock} role="alert">
          <h2>Confirmations disabled in demo mode</h2>
          <p>
            This ticket came from the local synthetic fallback. Reconnect to live clinic data before recording any
            confirmation.
          </p>
          <div>
            <Button onClick={() => void refresh()}>Try live data again</Button>
            <Link className={styles.backLink} href="/">Return to board</Link>
          </div>
        </section>
      </div>
    );
  }

  // Administrative exceptions must be resolved before the nurse enters the step pipeline at all.
  if (ticket.readiness_state === "needs_review") {
    const reviewCase = data.review_cases.find((item) => item.ticket_id === ticketId);
    return (
      <div className={styles.taskPage}>
        {pageHeader}
        <ReviewGate refresh={refresh} reviewCase={reviewCase} ticket={ticket} />
      </div>
    );
  }

  return (
    <div className={styles.taskPage}>
      {pageHeader}
      <TaskSteps current={step} ticket={ticket} />
      {isStepUnlocked(ticket, step) ? (
        children({ ticket, refresh })
      ) : (
        <section className={styles.section}>
          <p className={styles.hint}>Complete the earlier steps first.</p>
          <Link className={styles.backLink} href={`/tasks/${ticketId}`}>
            Go to the next step
          </Link>
        </section>
      )}
    </div>
  );
}
