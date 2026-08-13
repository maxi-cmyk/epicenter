"use client";

import { useReverification } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { confirmBilling } from "@/lib/api";
import type { QueueTicket } from "@epicenter/shared/contracts";
import { Button } from "@epicenter/shared/ui/Button";

import { TaskStepShell } from "./TaskStepShell";
import styles from "./Task.module.css";

export function BillingStep({ ticketId }: { ticketId: string }) {
  return (
    <TaskStepShell step="billing" ticketId={ticketId}>
      {({ ticket, refresh }) => <BillingStepContent refresh={refresh} ticket={ticket} />}
    </TaskStepShell>
  );
}

function BillingStepContent({ ticket, refresh }: { ticket: QueueTicket; refresh: () => Promise<void> }) {
  const [billingCodeEdit, setBillingCodeEdit] = useState<string | null>(null);
  const [uncoveredCostEdit, setUncoveredCostEdit] = useState<string | null>(null);
  const [queueNumberEdit, setQueueNumberEdit] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const reverifiedConfirmBilling = useReverification(confirmBilling);

  const billingCodeValue = billingCodeEdit ?? ticket.billing_code ?? "";
  const uncoveredCostValue = uncoveredCostEdit ?? (ticket.uncovered_cost != null ? String(ticket.uncovered_cost) : "");
  const queueNumberValue = queueNumberEdit ?? ticket.queue_number ?? "";

  const submit = async () => {
    setPending(true);
    setError("");
    try {
      const trimmedCode = billingCodeValue.trim();
      const trimmedQueue = queueNumberValue.trim();
      const parsedCost = uncoveredCostValue.trim() === "" ? undefined : Number(uncoveredCostValue);
      await reverifiedConfirmBilling(ticket.id, ticket.version, {
        billingCode: trimmedCode !== (ticket.billing_code ?? "").trim() ? trimmedCode : undefined,
        uncoveredCost: parsedCost !== undefined && parsedCost !== ticket.uncovered_cost ? parsedCost : undefined,
        queueNumber: trimmedQueue !== (ticket.queue_number ?? "").trim() ? trimmedQueue : undefined,
      });
      setBillingCodeEdit(null);
      setUncoveredCostEdit(null);
      setQueueNumberEdit(null);
      await refresh();
      router.push(`/tasks/${ticket.id}/summary`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not confirm billing and queue information.");
    } finally {
      setPending(false);
    }
  };

  return (
    <section aria-labelledby="billing-title" className={styles.section}>
      <h2 id="billing-title">
        Billing &amp; queue recheck
        {ticket.billing_confirmed ? <span className={styles.tpaConfirmedBadge}>Confirmed</span> : null}
      </h2>
      <p className={styles.hint}>
        The system used all the inputted data to work out the billing code, uncovered cost, and queue number. Check
        these against what the patient should be told and correct any field before confirming.
      </p>
      <div className={styles.tpaFormGrid}>
        <label>
          Billing code
          <input onChange={(event) => setBillingCodeEdit(event.target.value)} value={billingCodeValue} />
        </label>
        <label>
          Uncovered cost ($)
          <input
            min={0}
            onChange={(event) => setUncoveredCostEdit(event.target.value)}
            step="0.01"
            type="number"
            value={uncoveredCostValue}
          />
        </label>
        <label>
          Queue number
          <input onChange={(event) => setQueueNumberEdit(event.target.value)} value={queueNumberValue} />
        </label>
      </div>
      <Button disabled={pending} onClick={() => void submit()}>
        {pending ? "Confirming…" : ticket.billing_confirmed ? "Save & continue" : "Confirm billing & continue"}
      </Button>
      {ticket.billing_confirmed && ticket.billing_confirmed_by ? (
        <p className={styles.hint}>Confirmed by {ticket.billing_confirmed_by}</p>
      ) : null}
      {error ? <p className={styles.error}>{error}</p> : null}
    </section>
  );
}
