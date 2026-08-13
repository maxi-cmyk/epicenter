"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { markPhysicalFormsReceived, transitionTicket } from "@/lib/api";
import type { QueueTicket } from "@epicenter/shared/contracts";
import { Button } from "@epicenter/shared/ui/Button";

import { TaskStepShell } from "./TaskStepShell";
import styles from "./Task.module.css";

export function SummaryStep({ ticketId }: { ticketId: string }) {
  return (
    <TaskStepShell step="summary" ticketId={ticketId}>
      {({ ticket, refresh }) => <SummaryStepContent refresh={refresh} ticket={ticket} />}
    </TaskStepShell>
  );
}

function SummaryStepContent({ ticket, refresh }: { ticket: QueueTicket; refresh: () => Promise<void> }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const finish = async () => {
    setPending(true);
    setError("");
    try {
      const afterForms = await markPhysicalFormsReceived(ticket.id, ticket.version);
      const updatedVersion = afterForms.ticket?.version ?? ticket.version;
      await transitionTicket(ticket.id, updatedVersion, ticket.readiness_state, ticket.readiness_reason, true, "ongoing");
      await refresh();
      router.push("/");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not complete the visit hand-off.");
    } finally {
      setPending(false);
    }
  };

  return (
    <section aria-labelledby="summary-title" className={styles.section}>
      <h2 id="summary-title">Queue number &amp; billing summary</h2>
      <dl className={styles.counterSummary}>
        <div>
          <dt>Queue number</dt>
          <dd>{ticket.queue_number ?? "—"}</dd>
        </div>
        <div>
          <dt>Billing code</dt>
          <dd>{ticket.billing_code ?? "—"}</dd>
        </div>
        <div>
          <dt>Uncovered cost</dt>
          <dd>{ticket.uncovered_cost != null ? `$${ticket.uncovered_cost.toFixed(2)}` : "—"}</dd>
        </div>
      </dl>
      {ticket.is_checkup ? (
        <p className={styles.hint}>
          By now the patient should have finished the 2 physical checkup forms. Collect them, tell the patient
          about the uncovered cost, and hand over the queue number.
        </p>
      ) : (
        <p className={styles.hint}>Tell the patient about the uncovered cost and hand over the queue number.</p>
      )}
      {ticket.physical_forms_received ? (
        <p className={styles.hint}>Physical forms received by {ticket.physical_forms_received_by}.</p>
      ) : null}
      <Button disabled={pending} onClick={() => void finish()}>
        {pending ? "Completing…" : "Forms received — mark visit ongoing"}
      </Button>
      {error ? <p className={styles.error}>{error}</p> : null}
    </section>
  );
}
