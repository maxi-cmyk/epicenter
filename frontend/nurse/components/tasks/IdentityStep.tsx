"use client";

import { useReverification } from "@clerk/nextjs";
import { IdCard } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { confirmIdentity } from "@/lib/api";
import type { QueueTicket } from "@epicenter/shared/contracts";
import { Button } from "@epicenter/shared/ui/Button";

import { TaskStepShell } from "./TaskStepShell";
import styles from "./Task.module.css";

export function IdentityStep({ ticketId }: { ticketId: string }) {
  return (
    <TaskStepShell step="identity" ticketId={ticketId}>
      {({ ticket, refresh }) => <IdentityStepContent refresh={refresh} ticket={ticket} />}
    </TaskStepShell>
  );
}

function IdentityStepContent({ ticket, refresh }: { ticket: QueueTicket; refresh: () => Promise<void> }) {
  const [identityChecked, setIdentityChecked] = useState(ticket.identity_confirmed);
  const [ecardChecked, setEcardChecked] = useState(ticket.ecard_verified);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const reverifiedConfirmIdentity = useReverification(confirmIdentity);

  const canSubmit = identityChecked && ecardChecked;

  const submit = async () => {
    setPending(true);
    setError("");
    try {
      await reverifiedConfirmIdentity(ticket.id, ticket.version);
      await refresh();
      router.push(`/tasks/${ticket.id}/forms`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not confirm identity verification.");
    } finally {
      setPending(false);
    }
  };

  return (
    <section aria-labelledby="attestation-title" className={styles.section}>
      <h2 id="attestation-title">Manual identity &amp; e-card verification</h2>
      <div className={styles.attestationGate}>
        <IdCard aria-hidden="true" size={24} />
        <div>
          <p>
            Record checks completed manually outside this system. Staff performs the real identity and e-card
            checks in person; the system only stores who confirmed them and when.
          </p>
          <label>
            <input checked={identityChecked} onChange={(event) => setIdentityChecked(event.target.checked)} type="checkbox" />
            I manually verified the patient&apos;s identity in person.
          </label>
          <label>
            <input
              checked={ecardChecked}
              onChange={(event) => setEcardChecked(event.target.checked)}
              type="checkbox"
            />
            I manually validated the e-card using the approved in-person process.
          </label>
        </div>
      </div>
      {ticket.identity_confirmed && ticket.identity_confirmed_by ? (
        <p className={styles.hint}>Confirmed by {ticket.identity_confirmed_by}</p>
      ) : null}
      <Button disabled={pending || !canSubmit} onClick={() => void submit()}>
        {pending ? "Confirming…" : "Confirm identity & continue"}
      </Button>
      {error ? <p className={styles.error}>{error}</p> : null}
    </section>
  );
}
