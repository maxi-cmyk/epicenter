"use client";

import { Check, FileText, ShieldCheck, TriangleAlert } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/shared/Button";
import type { ReviewCase } from "@/lib/types";

import styles from "./Review.module.css";

export function EvidencePanel({ reviewCase, onConfirm }: { reviewCase: ReviewCase; onConfirm: () => void }) {
  const [confirmed, setConfirmed] = useState(false);

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
        <button type="button">View source page</button>
      </div>

      <div className={styles.evidenceGrid}>
        <div><span>Issuer</span><strong>Bluepeak</strong><small>Source page 1 · exact match</small></div>
        <div><span>Patient ID</span><strong>S••••451A</strong><small>Registration match</small></div>
        <div><span>Package</span><strong>Executive screening</strong><small>Rule BLPHS-04</small></div>
        <div className={styles.failedEvidence}><span>Valid until</span><strong>10 Aug 2026</strong><small>Expired · staff action required</small></div>
      </div>

      <div className={styles.resolutionBand}>
        <h3>Resolution recorded by staff</h3>
        <p>Patient supplied a replacement voucher valid until 31 December 2026. Current rules were re-run and produced one clean package match.</p>
      </div>

      <label className={styles.confirmationCheck}>
        <input checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} type="checkbox" />
        <span><ShieldCheck aria-hidden="true" size={20} /><span><strong>I reviewed the source and confirm this determination.</strong><small>This action is audited. The original ticket and waiting age are preserved.</small></span></span>
      </label>

      <div className={styles.evidenceActions}>
        <Button variant="secondary">Keep in review</Button>
        <Button disabled={!confirmed} icon={<Check aria-hidden="true" size={17} />} onClick={onConfirm}>Confirm and mark ready</Button>
      </div>
    </section>
  );
}
