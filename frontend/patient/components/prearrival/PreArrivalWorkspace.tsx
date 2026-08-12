"use client";

import { Check, FileCheck2, LockKeyhole, Upload } from "lucide-react";
import { useState } from "react";

import { Button } from "@epicenter/shared/ui/Button";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";
import type { PreArrivalSubmissionResult } from "@epicenter/shared/contracts";

import { submitPreArrival } from "@/lib/api";

import { RegistrationValidation } from "./RegistrationValidation";
import styles from "./PreArrival.module.css";

type CoverageChoice = "reuse" | "replace" | null;

export function PreArrivalWorkspace() {
  const [choice, setChoice] = useState<CoverageChoice>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<PreArrivalSubmissionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function chooseCoverage(nextChoice: Exclude<CoverageChoice, null>) {
    setChoice(nextChoice);
    setSelectedFile(null);
    setResult(null);
    setError(null);
  }

  async function handleSubmit() {
    if (!choice || (choice === "replace" && !selectedFile)) return;

    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const submission = await submitPreArrival({
        appointment_id: "APT-DEMO-014",
        coverage_action: choice,
        file_name: selectedFile?.name,
        expected_ticket_version: 1,
        idempotency_key: crypto.randomUUID(),
      });
      setResult(submission);
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "The clinic service could not process this submission. Try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

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
            <button aria-pressed={choice === "reuse"} className={choice === "reuse" ? styles.selectedChoice : undefined} onClick={() => chooseCoverage("reuse")} type="button">
              <Check aria-hidden="true" size={20} />
              <span><strong>Yes, same coverage</strong><small>Reuse the source document and run today’s checks again.</small></span>
            </button>
            <button aria-pressed={choice === "replace"} className={choice === "replace" ? styles.selectedChoice : undefined} onClick={() => chooseCoverage("replace")} type="button">
              <Upload aria-hidden="true" size={20} />
              <span><strong>No, upload new document</strong><small>Replace the prior source for this appointment.</small></span>
            </button>
          </div>
          {choice === "replace" ? (
            <label className={styles.uploadField}>
              New coverage document
              <input
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(event) => {
                  setSelectedFile(event.target.files?.[0] ?? null);
                  setError(null);
                  setResult(null);
                }}
                type="file"
              />
              <small>PDF, JPG or PNG · maximum 10 MB</small>
            </label>
          ) : null}
          {choice ? (
            <Button
              disabled={submitting || (choice === "replace" && !selectedFile)}
              onClick={() => void handleSubmit()}
            >
              {submitting ? "Submitting…" : choice === "reuse" ? "Run current checks" : "Upload and process"}
            </Button>
          ) : null}
          {result ? (
            <div aria-live="polite" className={styles.submissionSuccess} role="status">
              <strong>Submitted for staff confirmation</strong>
              <span>{result.message}</span>
              <small>{result.next_action} Reference: {result.processing_reference}</small>
            </div>
          ) : null}
          {error ? (
            <div aria-live="assertive" className={styles.submissionError} role="alert">
              <strong>Submission not completed</strong>
              <span>{error}</span>
              <small>Your selection is still here. Check your connection and try again.</small>
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}
