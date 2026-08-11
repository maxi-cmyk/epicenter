"use client";

import { Check, FileCheck2, LockKeyhole, Upload } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/shared/Button";
import { PageHeader } from "@/components/shared/PageHeader";

import { RegistrationValidation } from "./RegistrationValidation";
import styles from "./PreArrival.module.css";

type CoverageChoice = "reuse" | "replace" | null;

export function PreArrivalWorkspace() {
  const [choice, setChoice] = useState<CoverageChoice>(null);

  return (
    <div className={styles.preArrivalPage}>
      <PageHeader
        description="A scheduled-patient flow showing how consented Myinfo data validates registration fields before the clinic visit."
        title="Pre-arrival check"
      />
      <div className={styles.preArrivalGrid}>
        <section className={styles.identityPanel}>
          <div className={styles.singpassBand}>
            <LockKeyhole aria-hidden="true" size={28} />
            <div><strong>Singpass-authenticated booking</strong><span>Myinfo fields shared with patient consent</span></div>
            <span className={styles.verifiedMark}><Check aria-hidden="true" size={15} /> Authenticated</span>
          </div>
          <RegistrationValidation />
          <p className={styles.boundaryNote}>This validates registration data only. Clinic staff still perform the mandatory identity and e-card checks physically on arrival.</p>
        </section>

        <section className={styles.coveragePanel}>
          <FileCheck2 aria-hidden="true" size={30} />
          <h2>We have your Meridian coverage on file from 12 February 2026. Still the same?</h2>
          <p>Choose one option for this appointment. Current validity and eligibility rules will run again, followed by staff confirmation.</p>
          <div className={styles.coverageChoices}>
            <button aria-pressed={choice === "reuse"} className={choice === "reuse" ? styles.selectedChoice : undefined} onClick={() => setChoice("reuse")} type="button">
              <Check aria-hidden="true" size={20} />
              <span><strong>Yes, same coverage</strong><small>Reuse the source document and run today’s checks again.</small></span>
            </button>
            <button aria-pressed={choice === "replace"} className={choice === "replace" ? styles.selectedChoice : undefined} onClick={() => setChoice("replace")} type="button">
              <Upload aria-hidden="true" size={20} />
              <span><strong>No, upload new document</strong><small>Replace the prior source for this appointment.</small></span>
            </button>
          </div>
          {choice === "replace" ? (
            <label className={styles.uploadField}>
              New coverage document
              <input accept=".pdf,.jpg,.jpeg,.png" type="file" />
              <small>PDF, JPG or PNG · maximum 10 MB</small>
            </label>
          ) : null}
          {choice ? <Button>{choice === "reuse" ? "Run current checks" : "Upload and process"}</Button> : null}
        </section>
      </div>
    </div>
  );
}
