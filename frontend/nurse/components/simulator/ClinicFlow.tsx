"use client";

import { Circle, Diamond } from "lucide-react";

import type { PatientSnapshot, ProjectedState, Workstream } from "@/lib/simulation";

import styles from "./Simulator.module.css";

const STAGES: Array<{ id: Workstream; label: string; hint: string }> = [
  { id: "fast_registration", label: "Fast counters", hint: "Complete pre-registration" },
  { id: "slow_registration", label: "Slow counters", hint: "Full registration" },
  { id: "review", label: "Review", hint: "Assisted exceptions" },
  { id: "consult", label: "Doctor", hint: "Consultation" },
  { id: "pharmacy", label: "Pharmacy", hint: "Dispense" },
  { id: "billing", label: "Billing", hint: "Payment" },
];

const STATE_LABEL: Record<string, string> = {
  waiting_check_in: "Waiting",
  checking_in: "Check-in",
  processing: "Processing",
  needs_review: "Review",
  waiting_consult: "Waiting",
  consulting: "Consult",
  waiting_pharmacy: "Waiting",
  dispensing: "Dispensing",
  waiting_billing: "Waiting",
  billing: "Billing",
  completed: "Exit",
};

const QUEUE_STAGES = new Set<Workstream>(["fast_registration", "slow_registration"]);

export type ClinicView = "queue" | "overview";

function Token({ patient, instant }: { patient: PatientSnapshot; instant: boolean }) {
  const inService = Boolean(patient.resourceId);
  return (
    <span
      className={`${styles.token} ${inService ? styles.tokenBusy : styles.tokenWait} ${instant ? styles.instant : ""}`}
      title={`${patient.ticketId} · ${STATE_LABEL[patient.state] ?? patient.state}${patient.fastEligible ? " · fast eligible" : ""}`}
    >
      {inService ? <Diamond aria-hidden="true" size={10} /> : <Circle aria-hidden="true" size={10} />}
      <strong>{patient.ticketId}</strong>
      <small>{STATE_LABEL[patient.state] ?? patient.state}</small>
    </span>
  );
}

export function ClinicFlow({
  instant,
  state,
  view,
}: {
  instant: boolean;
  state: ProjectedState;
  view: ClinicView;
}) {
  const byId = new Map(state.patients.map((patient) => [patient.id, patient]));
  const byTicket = new Map(state.patients.map((patient) => [patient.ticketId, patient]));
  const completed = state.patients.filter((patient) => patient.state === "completed");
  const inClinic = state.patients.filter((patient) => patient.state !== "not_arrived" && patient.state !== "completed").length;
  const stages = view === "queue" ? STAGES.filter((stage) => QUEUE_STAGES.has(stage.id)) : STAGES;

  return (
    <section aria-label="Clinic flow" className={styles.flow}>
      <header>
        <h2>Clinic flow</h2>
      </header>
      <div className={view === "queue" ? styles.stageGridBasic : styles.stageGrid}>
        <article className={styles.stage}>
          <h3>Arrival / Exit</h3>
          <p>
            {state.metrics.notArrived} not arrived · {completed.length} completed
          </p>
          <div className={styles.tokenList}>
            {completed.slice(-4).map((patient) => (
              <Token instant={instant} key={patient.id} patient={patient} />
            ))}
          </div>
        </article>
        {stages.map((stage) => {
          const queued = state.queues[stage.id]
            .map((id) => byId.get(id))
            .filter((patient): patient is PatientSnapshot => Boolean(patient));
          const resources = state.resources.filter((resource) => resource.workstream === stage.id);
          return (
            <article className={styles.stage} key={stage.id}>
              <h3>{stage.label}</h3>
              <p>
                {stage.hint} · queue {queued.length}
                {queued[0] ? ` · oldest ${queued[0].ticketId}` : ""}
              </p>
              <div className={styles.resourceList}>
                {resources.length === 0 ? <p className={styles.more}>No counters in this scenario</p> : null}
                {resources.map((resource) => {
                  const served = resource.ticketId ? byTicket.get(resource.ticketId) : undefined;
                  const overflow = resource.kind === "fast_counter" && served && !served.fastEligible;
                  return (
                    <div className={`${styles.resourceCard} ${overflow ? styles.overflowCard : ""}`} key={resource.id}>
                      <span>{resource.id}</span>
                      <strong>{overflow ? "Overflow" : resource.state.replaceAll("_", " ")}</strong>
                      <small>
                        {resource.ticketId ?? "No ticket"}
                        {resource.remainingMinutes !== null ? ` · ${resource.remainingMinutes}m left` : ""}
                        {overflow ? " · slow duration" : ""}
                      </small>
                    </div>
                  );
                })}
              </div>
              <div className={styles.tokenList}>
                {queued.slice(0, 8).map((patient) => (
                  <Token instant={instant} key={patient.id} patient={patient} />
                ))}
                {queued.length > 8 ? <span className={styles.more}>+{queued.length - 8} more</span> : null}
              </div>
            </article>
          );
        })}
      </div>
      <p className={styles.flowFoot}>
        {inClinic} in clinic · {completed.length} completed
        {view === "overview" ? ` · bottleneck ${state.metrics.longestStage.replaceAll("_", " ")}` : ""}
      </p>
    </section>
  );
}
