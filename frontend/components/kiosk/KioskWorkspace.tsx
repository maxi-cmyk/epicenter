"use client";

import { ArrowRight, ShieldAlert } from "lucide-react";
import { FormEvent, useState } from "react";

import { checkInWalkIn } from "@/lib/api";
import type { QueueTicket } from "@/lib/types";
import { Button } from "@/components/shared/Button";
import { PageHeader } from "@/components/shared/PageHeader";
import { StatusBadge } from "@/components/shared/StatusBadge";

import { KioskSteps } from "./KioskSteps";
import styles from "./Kiosk.module.css";

export function KioskWorkspace() {
  const [patientName, setPatientName] = useState("");
  const [nurseSupervisor, setNurseSupervisor] = useState("Nurse Noor");
  const [clinicalEscalation, setClinicalEscalation] = useState(false);
  const [ticket, setTicket] = useState<QueueTicket | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const result = await checkInWalkIn(patientName, nurseSupervisor, clinicalEscalation);
      setTicket(result.ticket ?? null);
    } catch {
      const now = new Date().toISOString();
      setTicket({ id: "Q-020", patient_id: "P-020", patient_name: patientName, intake_type: "walk_in", visit_phase: "ongoing", readiness_state: "processing", readiness_reason: "processing", checked_in_at: now, original_ordering_at: now, waiting_minutes: 0, actual_counter: "Kiosk intake", processing_stage: "Nurse-supervised registration", service_target: "on_track", staff_confirmed: false, clinical_escalation: clinicalEscalation });
    } finally {
      setPending(false);
    }
  }

  return (
    <div className={styles.kioskPage}>
      <PageHeader
        description="A supervised intake channel for walk-ins. The kiosk creates one visit ticket; a trained nurse remains physically present throughout."
        title="Walk-in registration"
      />
      <KioskSteps activeStep={ticket ? 2 : 1} />
      <div className={styles.kioskGrid}>
        <form className={styles.kioskForm} onSubmit={submit}>
          <fieldset disabled={pending || Boolean(ticket)}>
            <legend>Patient and supervisor</legend>
            <label>
              Patient name
              <input autoComplete="name" onChange={(event) => setPatientName(event.target.value)} placeholder="Enter the patient’s full name" required value={patientName} />
            </label>
            <label>
              Supervising nurse
              <input onChange={(event) => setNurseSupervisor(event.target.value)} required value={nurseSupervisor} />
            </label>
            <label className={styles.fileField}>
              Coverage document
              <span><strong>Choose PDF or image</strong><small>Maximum 10 MB · preview before processing</small></span>
              <input accept=".pdf,.jpg,.jpeg,.png" type="file" />
            </label>
          </fieldset>

          <div className={styles.urgencyGate}>
            <ShieldAlert aria-hidden="true" size={24} />
            <div>
              <strong>Physical red-flag check</strong>
              <p>The supervising nurse applies the clinic’s existing protocol before normal administrative routing.</p>
              <label><input checked={clinicalEscalation} disabled={Boolean(ticket)} onChange={(event) => setClinicalEscalation(event.target.checked)} type="checkbox" /> Clinical escalation identified</label>
            </div>
          </div>

          {clinicalEscalation ? <p className={styles.escalationNotice}>Stop kiosk intake and follow the clinic’s approved urgent-care pathway. Administrative processing must not delay care.</p> : null}
          {error ? <p className={styles.error}>{error}</p> : null}
          {!ticket ? <Button disabled={pending || patientName.trim().length < 2} icon={<ArrowRight aria-hidden="true" size={18} />} type="submit">{pending ? "Creating ticket…" : "Create one visit ticket"}</Button> : null}
        </form>

        <aside className={styles.kioskResult}>
          {ticket ? (
            <>
              <span className={styles.ticketLabel}>Visit ticket created</span>
              <strong className={styles.ticketNumber}>{ticket.id}</strong>
              <h2>{ticket.patient_name}</h2>
              <StatusBadge state={ticket.readiness_state} />
              <dl>
                <div><dt>Original check-in</dt><dd>Just now</dd></div>
                <div><dt>Current route</dt><dd>{ticket.actual_counter}</dd></div>
                <div><dt>Next step</dt><dd>{ticket.clinical_escalation ? "Urgent-care pathway" : "Document processing"}</dd></div>
              </dl>
              <p>This number remains with the patient through processing, review and readiness.</p>
            </>
          ) : (
            <>
              <span className={styles.ticketLabel}>What happens next</span>
              <h2>One intake. One ticket.</h2>
              <ol>
                <li>The nurse checks for physical red flags.</li>
                <li>The kiosk captures registration and coverage documents.</li>
                <li>Epicenter processes the case without making the patient queue again.</li>
                <li>Staff confirm every determination.</li>
              </ol>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
