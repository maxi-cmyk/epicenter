"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { confirmForms } from "@/lib/api";
import { hasDocuments } from "@/lib/task-steps";
import type { QueueTicket } from "@epicenter/shared/contracts";
import { Button } from "@epicenter/shared/ui/Button";

import { TaskStepShell } from "./TaskStepShell";
import styles from "./Task.module.css";

export function FormsReviewStep({ ticketId }: { ticketId: string }) {
  return (
    <TaskStepShell step="forms-review" ticketId={ticketId}>
      {({ ticket, refresh }) => <FormsReviewContent refresh={refresh} ticket={ticket} />}
    </TaskStepShell>
  );
}

function FormsReviewContent({ ticket, refresh }: { ticket: QueueTicket; refresh: () => Promise<void> }) {
  const [physicalFormsChecked, setPhysicalFormsChecked] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const electronicDocuments = ticket.documents.filter((clinicDocument) => clinicDocument.category !== "form");
  const allElectronicConfirmed = electronicDocuments.every((clinicDocument) => clinicDocument.confirmed);

  const submit = async () => {
    setPending(true);
    setError("");
    try {
      await confirmForms(ticket.id, ticket.version);
      await refresh();
      router.push(`/tasks/${ticket.id}/${hasDocuments(ticket) ? "package" : "billing"}`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not confirm the forms.");
    } finally {
      setPending(false);
    }
  };

  return (
    <section aria-labelledby="forms-review-title" className={styles.section}>
      <h2 id="forms-review-title">
        Forms review
        {ticket.forms_confirmed ? <span className={styles.tpaConfirmedBadge}>Confirmed</span> : null}
      </h2>
      {electronicDocuments.length > 0 ? (
        <ul className={styles.checklistList}>
          {electronicDocuments.map((clinicDocument) => (
            <li className={styles.checklistItem} key={clinicDocument.id}>
              <span
                className={`${styles.checklistDot} ${clinicDocument.confirmed ? styles.status_pass : styles.status_pending}`}
              />
              <span className={styles.checklistLabel}>{clinicDocument.document_type}</span>
              <span className={clinicDocument.confirmed ? styles.status_pass : styles.status_pending}>
                {clinicDocument.confirmed ? "Confirmed" : "Not yet confirmed"}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className={styles.hint}>No electronic forms were required for this visit.</p>
      )}
      {!allElectronicConfirmed ? (
        <p className={styles.error}>Confirm every electronic form on the previous step before approving.</p>
      ) : null}

      <label className={styles.inlineCheckLabel}>
        <input
          checked={physicalFormsChecked}
          onChange={(event) => setPhysicalFormsChecked(event.target.checked)}
          type="checkbox"
        />
        I checked the physical form filling is correct.
      </label>

      <Button disabled={pending || !allElectronicConfirmed} onClick={() => void submit()}>
        {pending ? "Confirming…" : ticket.forms_confirmed ? "Continue" : "Approve forms & continue"}
      </Button>
      {error ? <p className={styles.error}>{error}</p> : null}
    </section>
  );
}
