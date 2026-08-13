"use client";

import { ClipboardList } from "lucide-react";
import Link from "next/link";

import type { QueueTicket } from "@epicenter/shared/contracts";

import { DocumentCard } from "./DocumentCard";
import { TaskStepShell } from "./TaskStepShell";
import styles from "./Task.module.css";

export function FormsGuidanceStep({ ticketId }: { ticketId: string }) {
  return (
    <TaskStepShell step="forms" ticketId={ticketId}>
      {({ ticket, refresh }) => <FormsGuidanceContent refresh={refresh} ticket={ticket} />}
    </TaskStepShell>
  );
}

function FormsGuidanceContent({ ticket, refresh }: { ticket: QueueTicket; refresh: () => Promise<void> }) {
  const tpaInvolved = ticket.documents.length > 0;
  const paperForms = ticket.documents.filter((clinicDocument) => clinicDocument.category === "form");
  const electronicDocuments = ticket.documents.filter((clinicDocument) => clinicDocument.category !== "form");

  return (
    <section aria-labelledby="forms-title" className={styles.section}>
      <h2 id="forms-title">Forms to fill</h2>
      {tpaInvolved ? (
        <p className={styles.hint}>
          <ClipboardList aria-hidden="true" size={16} /> This visit involves TPA/payer paperwork — fill in the
          forms below.
        </p>
      ) : (
        <p className={styles.hint}>No TPA or payer paperwork is on file for this visit — no forms required here.</p>
      )}

      {ticket.is_checkup ? (
        <div className={styles.notice}>
          <p>
            This patient preregistered for a checkup. Hand over the 2 physical checkup forms for the patient to
            fill in first.
          </p>
        </div>
      ) : null}

      {paperForms.length > 0 ? (
        <div className={styles.notice}>
          <p>Refer to the following forms and fill them out on paper:</p>
          <ul className={styles.checklistList}>
            {paperForms.map((clinicDocument) => (
              <li className={styles.checklistItem} key={clinicDocument.id}>
                <span className={styles.checklistLabel}>{clinicDocument.document_type}</span>
                <span className={styles.checklistDetail}>
                  {clinicDocument.issuer_name} ({clinicDocument.issuer_code})
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {electronicDocuments.length > 0 ? (
        <div className={styles.tpaDocList}>
          {electronicDocuments.map((clinicDocument) => (
            <DocumentCard
              document={clinicDocument}
              key={clinicDocument.id}
              onConfirmed={refresh}
              ticketId={ticket.id}
              ticketVersion={ticket.version}
            />
          ))}
        </div>
      ) : null}

      <div className={styles.done}>
        <Link className={styles.backLink} href={`/tasks/${ticket.id}/forms-review`}>
          Continue to forms review →
        </Link>
      </div>
    </section>
  );
}
