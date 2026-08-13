"use client";

import { Check, FileText, ShieldCheck, TriangleAlert } from "lucide-react";
import { useState } from "react";

import { Button } from "@epicenter/shared/ui/Button";
import type { ReviewCase } from "@epicenter/shared/contracts";

import styles from "./Review.module.css";

const RESOLUTION_METHODS = ["Replacement document provided", "Confirmed self-pay"] as const;

export type ReviewResolution = {
  method: (typeof RESOLUTION_METHODS)[number];
  note: string;
};

export function EvidencePanel({ reviewCase, onConfirm }: { reviewCase: ReviewCase; onConfirm: (resolution: ReviewResolution) => void }) {
  const [confirmed, setConfirmed] = useState(false);
  const [resolutionMethod, setResolutionMethod] = useState("");
  const [resolutionNote, setResolutionNote] = useState("");
  const canConfirm = confirmed && resolutionMethod.length > 0;

  return (
    <section aria-labelledby="evidence-title" className={styles.evidencePanel}>
      <header className={styles.evidenceHeader}>
        <div>
          <h2 id="evidence-title">{reviewCase.reason_label}</h2>
          <p>{reviewCase.ticket_id} · {reviewCase.patient_name}</p>
        </div>
        <TriangleAlert aria-hidden="true" size={28} />
      </header>

      <div className={styles.documentStrip}>
        <FileText aria-hidden="true" size={22} />
        <span><strong>{reviewCase.document_name ?? "No document received"}</strong><small>{reviewCase.evidence_summary}</small></span>
        {reviewCase.document_name ? (
          <details className={styles.sourceDetails}>
            <summary>View source details</summary>
            <p>{reviewCase.evidence_summary}</p>
          </details>
        ) : null}
      </div>

      <div className={styles.evidenceGrid}>
        <div><span>Exception</span><strong>{reviewCase.reason_label}</strong><small>{reviewCase.reason_code.replaceAll("_", " ")}</small></div>
        <div><span>Current evidence</span><strong>{reviewCase.document_name ?? "No document on file"}</strong><small>{reviewCase.evidence_summary}</small></div>
        <div><span>Next safe action</span><strong>{reviewCase.next_action}</strong><small>Staff confirmation required</small></div>
        <div className={styles.failedEvidence}><span>Waiting age</span><strong>{reviewCase.waiting_minutes ? `${reviewCase.waiting_minutes} min` : "Pre-arrival"}</strong><small>Original ticket position is retained</small></div>
      </div>

      <div className={styles.resolutionBand}>
        <h3>Method of resolution</h3>
        <div className={styles.resolutionOptions}>
          {RESOLUTION_METHODS.map((method) => (
            <label key={method}>
              <input
                checked={resolutionMethod === method}
                name="resolution-method"
                onChange={() => setResolutionMethod(method)}
                type="radio"
                value={method}
              />
              <span>{method}</span>
            </label>
          ))}
        </div>
        <textarea
          className={styles.resolutionNote}
          onChange={(event) => setResolutionNote(event.target.value)}
          placeholder="Add resolution notes (optional)"
          value={resolutionNote}
        />
      </div>

      <label className={styles.confirmationCheck}>
        <input checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} type="checkbox" />
        <span><ShieldCheck aria-hidden="true" size={20} /><span><strong>I reviewed the source and confirm this determination.</strong><small>This action is audited. The original ticket and waiting age are preserved.</small></span></span>
      </label>

      <div className={styles.evidenceActions}>
        <Button variant="secondary">Keep in review</Button>
        <Button
          disabled={!canConfirm}
          icon={<Check aria-hidden="true" size={17} />}
          onClick={() => onConfirm({ method: resolutionMethod as ReviewResolution["method"], note: resolutionNote.trim() })}
        >
          Record resolution
        </Button>
      </div>
    </section>
  );
}
