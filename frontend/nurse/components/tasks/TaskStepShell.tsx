"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { useDashboard } from "@/hooks/useDashboard";
import { isStepUnlocked, type TaskStep } from "@/lib/task-steps";
import type { QueueTicket } from "@epicenter/shared/contracts";
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
  const { data, loading, refresh } = useDashboard();

  if (loading || !data) return <LoadingBoard />;

  const ticket = data.tickets.find((item) => item.id === ticketId);

  if (!ticket) {
    return (
      <div className={styles.taskPage}>
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
    );
  }

  const pageHeader = (
    <PageHeader
      actions={
        <Link className={styles.backLink} href="/">
          Back to board
        </Link>
      }
      description={`${ticket.id} · ${ticket.intake_type === "walk_in" ? "Walk-in" : "Booked"}`}
      title={ticket.patient_name}
    />
  );

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
