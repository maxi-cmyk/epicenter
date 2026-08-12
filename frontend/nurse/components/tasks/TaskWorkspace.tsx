"use client";

import { useReverification } from "@clerk/nextjs";
import { IdCard } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useDashboard } from "@/hooks/useDashboard";
import { confirmBilling, confirmPackage, transitionTicket } from "@/lib/api";
import { Button } from "@epicenter/shared/ui/Button";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";

import { EvidencePanel } from "../review/EvidencePanel";
import styles from "./Task.module.css";
import { DocumentCard } from "./DocumentCard";

export function TaskWorkspace({ ticketId }: { ticketId: string }) {
  const { data, loading, refresh } = useDashboard();
  const [identityConfirmed, setIdentityConfirmed] = useState(false);
  const [ecardConfirmed, setEcardConfirmed] = useState(false);
  const [ecardNotApplicable, setEcardNotApplicable] = useState(false);
  const [ecardReason, setEcardReason] = useState("");
  const [recordPending, setRecordPending] = useState(false);
  const [recordError, setRecordError] = useState("");
  const [packageEdit, setPackageEdit] = useState<string | null>(null);
  const [packagePending, setPackagePending] = useState(false);
  const [packageError, setPackageError] = useState("");
  const [billingCodeEdit, setBillingCodeEdit] = useState<string | null>(null);
  const [uncoveredCostEdit, setUncoveredCostEdit] = useState<string | null>(null);
  const [queueNumberEdit, setQueueNumberEdit] = useState<string | null>(null);
  const [billingPending, setBillingPending] = useState(false);
  const [billingError, setBillingError] = useState("");

  const reverifiedTransition = useReverification(transitionTicket);
  const reverifiedConfirmPackage = useReverification(confirmPackage);
  const reverifiedConfirmBilling = useReverification(confirmBilling);

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

  const reviewCase = data.review_cases.find((item) => item.ticket_id === ticketId);

  const confirmReview = async (ticketId: string, expectedVersion: number) => {
    setRecordPending(true);
    setRecordError("");
    try {
      await reverifiedTransition(ticketId, expectedVersion, "ready", "all_prerequisites_passed", true);
      await refresh();
    } catch (error) {
      setRecordError(error instanceof Error ? error.message : "Could not confirm the record.");
    } finally {
      setRecordPending(false);
    }
  };

  const packageValue = packageEdit ?? ticket.matched_package ?? "";

  const submitPackageConfirm = async (ticketId: string, expectedVersion: number) => {
    setPackagePending(true);
    setPackageError("");
    try {
      const trimmed = packageValue.trim();
      const corrected = trimmed !== (ticket.matched_package ?? "").trim() ? trimmed : undefined;
      await reverifiedConfirmPackage(ticketId, expectedVersion, corrected);
      setPackageEdit(null);
      await refresh();
    } catch (error) {
      setPackageError(error instanceof Error ? error.message : "Could not confirm the package.");
    } finally {
      setPackagePending(false);
    }
  };

  const billingCodeValue = billingCodeEdit ?? ticket.billing_code ?? "";
  const uncoveredCostValue = uncoveredCostEdit ?? (ticket.uncovered_cost != null ? String(ticket.uncovered_cost) : "");
  const queueNumberValue = queueNumberEdit ?? ticket.queue_number ?? "";
  const hasBillingInfo = ticket.billing_code != null || ticket.uncovered_cost != null || ticket.queue_number != null;

  const submitBillingConfirm = async (ticketId: string, expectedVersion: number) => {
    setBillingPending(true);
    setBillingError("");
    try {
      const trimmedCode = billingCodeValue.trim();
      const trimmedQueue = queueNumberValue.trim();
      const parsedCost = uncoveredCostValue.trim() === "" ? undefined : Number(uncoveredCostValue);
      await reverifiedConfirmBilling(ticketId, expectedVersion, {
        billingCode: trimmedCode !== (ticket.billing_code ?? "").trim() ? trimmedCode : undefined,
        uncoveredCost: parsedCost !== undefined && parsedCost !== ticket.uncovered_cost ? parsedCost : undefined,
        queueNumber: trimmedQueue !== (ticket.queue_number ?? "").trim() ? trimmedQueue : undefined,
      });
      setBillingCodeEdit(null);
      setUncoveredCostEdit(null);
      setQueueNumberEdit(null);
      await refresh();
    } catch (error) {
      setBillingError(error instanceof Error ? error.message : "Could not confirm billing and queue information.");
    } finally {
      setBillingPending(false);
    }
  };

  return (
    <div className={styles.taskPage}>
      <PageHeader
        actions={
          <Link className={styles.backLink} href="/">
            Back to board
          </Link>
        }
        description={`${ticket.id} · ${ticket.intake_type === "walk_in" ? "Walk-in" : "Booked"}`}
        title={ticket.patient_name}
      />

      <section aria-labelledby="record-title" className={styles.section}>
        <h2 id="record-title">Prepared record</h2>
        {ticket.record_checklist ? (
          <div className={styles.checklist}>
            {ticket.record_checklist.patient ? (
              <div className={styles.patientSummary}>
                <strong>{ticket.record_checklist.patient.full_name}</strong>
                <span>{ticket.record_checklist.patient.identifier_masked}</span>
                {ticket.record_checklist.patient.date_of_birth ? (
                  <span>DOB {ticket.record_checklist.patient.date_of_birth}</span>
                ) : null}
                {ticket.record_checklist.patient.contact_mobile ? (
                  <span>{ticket.record_checklist.patient.contact_mobile}</span>
                ) : null}
              </div>
            ) : null}
            <ul className={styles.checklistList}>
              {ticket.record_checklist.items.map((item) => (
                <li className={styles.checklistItem} key={item.label}>
                  <span className={`${styles.checklistDot} ${styles[`status_${item.status}`]}`} />
                  <span className={styles.checklistLabel}>{item.label}</span>
                  <span className={`${styles.checklistStatus} ${styles[`status_${item.status}`]}`}>
                    {item.status.replaceAll("_", " ")}
                  </span>
                  {item.detail ? <span className={styles.checklistDetail}>{item.detail}</span> : null}
                </li>
              ))}
            </ul>
            <p className={styles.hint}>Pharmacy dispensing and TPA claim submission are handled on the pharmacist screen.</p>
          </div>
        ) : null}

        {ticket.readiness_state === "needs_review" ? (
          reviewCase ? (
            <EvidencePanel onConfirm={() => void confirmReview(ticket.id, ticket.version)} reviewCase={reviewCase} />
          ) : (
            <div className={styles.notice}>
              <p>No review evidence found for this ticket.</p>
              <Link href="/review">Open the review worklist</Link>
            </div>
          )
        ) : null}

        {recordPending ? <p className={styles.hint}>Confirming…</p> : null}
        {recordError ? <p className={styles.error}>{recordError}</p> : null}
      </section>

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
              <input
                checked={identityConfirmed}
                onChange={(event) => setIdentityConfirmed(event.target.checked)}
                type="checkbox"
              />
              I manually verified the patient&apos;s identity in person.
            </label>
            <label>
              <input
                checked={ecardConfirmed}
                disabled={ecardNotApplicable}
                onChange={(event) => setEcardConfirmed(event.target.checked)}
                type="checkbox"
              />
              I manually validated the e-card using the approved in-person process.
            </label>
            <label>
              <input
                checked={ecardNotApplicable}
                onChange={(event) => {
                  setEcardNotApplicable(event.target.checked);
                  if (event.target.checked) setEcardConfirmed(false);
                }}
                type="checkbox"
              />
              Not applicable
            </label>
            {ecardNotApplicable ? (
              <input
                className={styles.reasonInput}
                onChange={(event) => setEcardReason(event.target.value)}
                placeholder="Reason e-card check is not applicable"
                value={ecardReason}
              />
            ) : null}
          </div>
        </div>
      </section>

      {ticket.documents.length > 0 ? (
        <section aria-labelledby="documents-title" className={styles.section}>
          <h2 id="documents-title">Autofilled documents</h2>
          <p className={styles.hint}>
            Coverage paperwork splits into several distinct kinds — the system autofilled each of these from what
            was captured at registration. Check each one against the physical document and correct any field before
            confirming.
          </p>
          <div className={styles.tpaDocList}>
            {ticket.documents.map((clinicDocument) => (
              <DocumentCard
                document={clinicDocument}
                key={clinicDocument.id}
                onConfirmed={refresh}
                ticketId={ticket.id}
                ticketVersion={ticket.version}
              />
            ))}
          </div>
        </section>
      ) : null}

      {ticket.matched_package ? (
        <section aria-labelledby="package-title" className={styles.section}>
          <h2 id="package-title">
            Package recheck
            {ticket.package_confirmed ? <span className={styles.tpaConfirmedBadge}>Confirmed</span> : null}
          </h2>
          <p className={styles.hint}>
            The system matched this patient&apos;s coverage to a package automatically. Recheck it against the
            eligibility rule and correct it here if it&apos;s wrong before confirming.
          </p>
          <label className={styles.tpaDocRefLabel}>
            Matched package
            <input onChange={(event) => setPackageEdit(event.target.value)} value={packageValue} />
          </label>
          <Button disabled={packagePending} onClick={() => void submitPackageConfirm(ticket.id, ticket.version)}>
            {packagePending ? "Confirming…" : ticket.package_confirmed ? "Save correction" : "Confirm package is correct"}
          </Button>
          {ticket.package_confirmed && ticket.package_confirmed_by ? (
            <p className={styles.hint}>Confirmed by {ticket.package_confirmed_by}</p>
          ) : null}
          {packageError ? <p className={styles.error}>{packageError}</p> : null}
        </section>
      ) : null}

      {hasBillingInfo ? (
        <section aria-labelledby="billing-title" className={styles.section}>
          <h2 id="billing-title">
            Billing &amp; queue recheck
            {ticket.billing_confirmed ? <span className={styles.tpaConfirmedBadge}>Confirmed</span> : null}
          </h2>
          <p className={styles.hint}>
            The system worked out the billing code, uncovered cost, and queue number automatically. Check these
            against what the patient should be told and correct any field before confirming.
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
          <Button disabled={billingPending} onClick={() => void submitBillingConfirm(ticket.id, ticket.version)}>
            {billingPending ? "Confirming…" : ticket.billing_confirmed ? "Save correction" : "Confirm billing & queue number"}
          </Button>
          {ticket.billing_confirmed && ticket.billing_confirmed_by ? (
            <p className={styles.hint}>Confirmed by {ticket.billing_confirmed_by}</p>
          ) : null}
          {billingError ? <p className={styles.error}>{billingError}</p> : null}
        </section>
      ) : null}

      <div className={styles.done}>
        {/* Incoming -> Ongoing visit-phase transition has no backend endpoint yet; this is navigation only. */}
        <Link className={styles.backLink} href="/">
          Done — back to board
        </Link>
      </div>
    </div>
  );
}
