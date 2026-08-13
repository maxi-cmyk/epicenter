"use client";

import { useState } from "react";

import { confirmDocument } from "@/lib/api";
import type { ClinicDocument, DocumentCategory } from "@epicenter/shared/contracts";
import { Button } from "@epicenter/shared/ui/Button";

import styles from "./Task.module.css";

const CATEGORY_LABELS: Record<DocumentCategory, string> = {
  form: "Form",
  authorisation_letter: "Authorisation letter",
  benefit_structure: "Benefit structure",
  coding_scheme: "Coding scheme",
};

function factLabel(key: string) {
  return key.replaceAll("_", " ").replace(/^./, (char) => char.toUpperCase());
}

export function DocumentCard({
  document: clinicDocument,
  onConfirmed,
  ticketId,
  ticketVersion,
}: {
  document: ClinicDocument;
  onConfirmed: () => Promise<void>;
  ticketId: string;
  ticketVersion: number;
}) {
  const [facts, setFacts] = useState<Record<string, string>>(clinicDocument.facts);
  const [referenceNumber, setReferenceNumber] = useState(clinicDocument.reference_number ?? "");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const updateFact = (key: string, value: string) => {
    setFacts((current) => ({ ...current, [key]: value }));
  };

  const submit = async () => {
    setPending(true);
    setError("");
    try {
      await confirmDocument(ticketId, clinicDocument.id, ticketVersion, { facts, referenceNumber });
      await onConfirmed();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not confirm this document.");
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={styles.tpaDocCard}>
      <header className={styles.tpaDocHead}>
        <span className={styles.tpaDocCategory}>{CATEGORY_LABELS[clinicDocument.category]}</span>
        {clinicDocument.confirmed ? <span className={styles.tpaConfirmedBadge}>Confirmed</span> : null}
      </header>
      <p className={styles.tpaDocMeta}>
        {clinicDocument.document_type} · {clinicDocument.issuer_name} ({clinicDocument.issuer_code})
      </p>
      <label className={styles.tpaDocRefLabel}>
        Reference number
        <input onChange={(event) => setReferenceNumber(event.target.value)} value={referenceNumber} />
      </label>
      <div className={styles.tpaFormGrid}>
        {Object.entries(facts).map(([key, value]) => (
          <label key={key}>
            {factLabel(key)}
            <input onChange={(event) => updateFact(key, event.target.value)} value={value} />
          </label>
        ))}
      </div>
      <Button disabled={pending} onClick={() => void submit()}>
        {pending ? "Confirming…" : clinicDocument.confirmed ? "Save correction" : "Confirm this document"}
      </Button>
      {error ? <p className={styles.error}>{error}</p> : null}
    </div>
  );
}
