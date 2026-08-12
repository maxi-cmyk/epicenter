"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { usePharmacyQueue } from "@/hooks/usePharmacyQueue";
import { confirmTpaSubmission, fetchTpaSubmission, recordMedicationDispense } from "@/lib/api";
import type { MedicationItem, TpaSubmission } from "@epicenter/shared/contracts";
import { Button } from "@epicenter/shared/ui/Button";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";

import styles from "./Pharmacy.module.css";

type DraftItem = { name: string; quantity: string; unitCost: string };

const EMPTY_ROW: DraftItem = { name: "", quantity: "1", unitCost: "" };

export function PharmacyWorkspace({ ticketId }: { ticketId: string }) {
  const { tickets, loading, refresh } = usePharmacyQueue();
  const [items, setItems] = useState<DraftItem[]>([{ ...EMPTY_ROW }]);
  const [dispensePending, setDispensePending] = useState(false);
  const [dispenseError, setDispenseError] = useState("");

  const [submission, setSubmission] = useState<TpaSubmission | null>(null);
  const [confirmPending, setConfirmPending] = useState(false);
  const [confirmError, setConfirmError] = useState("");

  const ticket = tickets?.find((item) => item.id === ticketId) ?? null;

  const hasDocuments = Boolean(ticket && ticket.documents.length > 0);

  const loadSubmission = async () => {
    if (!hasDocuments) return;
    try {
      setSubmission(await fetchTpaSubmission(ticketId));
    } catch {
      setSubmission(null);
    }
  };

  useEffect(() => {
    if (!hasDocuments) return;
    let active = true;
    fetchTpaSubmission(ticketId)
      .then((result) => {
        if (active) setSubmission(result);
      })
      .catch(() => {
        if (active) setSubmission(null);
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasDocuments]);

  if (loading || !tickets) return <LoadingBoard />;

  if (!ticket) {
    return (
      <div className={styles.taskPage}>
        <PageHeader
          actions={
            <Link className={styles.backLink} href="/">
              Back to queue
            </Link>
          }
          description="This ticket is not in the current pharmacy queue."
          title="Ticket not found"
        />
      </div>
    );
  }

  const updateItem = (index: number, patch: Partial<DraftItem>) => {
    setItems((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)));
  };

  const addRow = () => setItems((current) => [...current, { ...EMPTY_ROW }]);

  const removeRow = (index: number) =>
    setItems((current) => (current.length > 1 ? current.filter((_, itemIndex) => itemIndex !== index) : current));

  const parsedItems: MedicationItem[] = items
    .filter((item) => item.name.trim().length > 0)
    .map((item) => ({
      name: item.name.trim(),
      quantity: Number(item.quantity) || 0,
      unit_cost: Number(item.unitCost) || 0,
    }));
  const canDispense = parsedItems.length > 0 && parsedItems.every((item) => item.quantity > 0) && !dispensePending;
  const runningTotal = parsedItems.reduce((sum, item) => sum + item.quantity * item.unit_cost, 0);

  const submitDispense = async () => {
    setDispensePending(true);
    setDispenseError("");
    try {
      await recordMedicationDispense(ticketId, parsedItems);
      setItems([{ ...EMPTY_ROW }]);
      await refresh();
      await loadSubmission();
    } catch (error) {
      setDispenseError(error instanceof Error ? error.message : "Could not record the dispense.");
    } finally {
      setDispensePending(false);
    }
  };

  const submitConfirm = async () => {
    if (!submission) return;
    setConfirmPending(true);
    setConfirmError("");
    try {
      await confirmTpaSubmission(ticketId, submission.version);
      await loadSubmission();
    } catch (error) {
      setConfirmError(error instanceof Error ? error.message : "Could not confirm the TPA submission.");
    } finally {
      setConfirmPending(false);
    }
  };

  return (
    <div className={styles.taskPage}>
      <PageHeader
        actions={
          <Link className={styles.backLink} href="/">
            Back to queue
          </Link>
        }
        description={`${ticket.id} · ${ticket.actual_room ?? "Room not assigned"}`}
        title={ticket.patient_name}
      />

      <section aria-labelledby="incoming-title" className={styles.section}>
        <h2 id="incoming-title">Incoming · cost &amp; medication</h2>
        {ticket.documents.length > 0 ? (
          <ul className={styles.tpaDocSummaryList}>
            {ticket.documents.map((clinicDocument) => (
              <li key={clinicDocument.id}>
                <strong>{clinicDocument.category.replaceAll("_", " ")}</strong> — {clinicDocument.document_type} ·{" "}
                {clinicDocument.issuer_name}
                {!clinicDocument.confirmed ? (
                  <span className={styles.hint}> (nurse hasn&apos;t confirmed this yet)</span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className={styles.hint}>No coverage documents on file for this patient — self-pay or other coverage.</p>
        )}

        <div className={styles.medicationList}>
          {items.map((item, index) => (
            <div className={styles.medicationRow} key={index}>
              <input
                onChange={(event) => updateItem(index, { name: event.target.value })}
                placeholder="Medication name"
                value={item.name}
              />
              <input
                min={1}
                onChange={(event) => updateItem(index, { quantity: event.target.value })}
                placeholder="Qty"
                type="number"
                value={item.quantity}
              />
              <input
                min={0}
                onChange={(event) => updateItem(index, { unitCost: event.target.value })}
                placeholder="Unit cost"
                step="0.01"
                type="number"
                value={item.unitCost}
              />
              <Button onClick={() => removeRow(index)} variant="secondary">
                Remove
              </Button>
            </div>
          ))}
        </div>
        <Button onClick={addRow} variant="secondary">
          Add medication
        </Button>
        <p className={styles.medicationTotal}>Running total: ${runningTotal.toFixed(2)}</p>
        <Button disabled={!canDispense} onClick={() => void submitDispense()}>
          {dispensePending ? "Recording…" : "Record dispense"}
        </Button>
        {dispenseError ? <p className={styles.error}>{dispenseError}</p> : null}
      </section>

      {ticket.documents.length > 0 ? (
        <section aria-labelledby="outgoing-title" className={styles.section}>
          <h2 id="outgoing-title">Outgoing · TPA submission</h2>
          {!submission ? (
            <p className={styles.hint}>Loading the TPA submission draft…</p>
          ) : (
            <>
              <span className={`${styles.badge} ${styles[`badge_${submission.status}`]}`}>{submission.status}</span>
              <ul className={styles.tpaDocSummaryList}>
                {submission.documents.map((clinicDocument) => (
                  <li key={clinicDocument.id}>
                    <strong>{clinicDocument.category.replaceAll("_", " ")}</strong> —{" "}
                    {clinicDocument.reference_number ?? "no reference"} ·{" "}
                    {clinicDocument.confirmed ? "confirmed by nurse" : "not yet confirmed by nurse"}
                  </li>
                ))}
              </ul>
              <p className={styles.checkupSummary}>{submission.checkup_summary}</p>
              {submission.medication ? (
                <ul className={styles.medicationList}>
                  {submission.medication.items.map((item) => (
                    <li key={item.name}>
                      {item.name} × {item.quantity} — ${(item.quantity * item.unit_cost).toFixed(2)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className={styles.hint}>No medication recorded yet — record a dispense above first.</p>
              )}
              {submission.status === "submitted" ? (
                <p className={styles.hint}>Submitted · reference {submission.external_reference}</p>
              ) : (
                <Button disabled={!submission.medication || confirmPending} onClick={() => void submitConfirm()}>
                  {confirmPending ? "Confirming…" : "Confirm & submit to TPA"}
                </Button>
              )}
              {confirmError ? <p className={styles.error}>{confirmError}</p> : null}
            </>
          )}
        </section>
      ) : null}

      <div className={styles.done}>
        <Link className={styles.backLink} href="/">
          Done — back to queue
        </Link>
      </div>
    </div>
  );
}
