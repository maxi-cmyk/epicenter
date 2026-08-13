import { projectState } from "./engine.ts";
import type { SimulationRun } from "./types.ts";

export interface InvariantFailure {
  code: string;
  message: string;
}

export function assertRunInvariants(run: SimulationRun): InvariantFailure[] {
  const failures: InvariantFailure[] = [];
  const tickets = new Map<string, string>();
  const busyResource = new Map<string, string>();
  const patientStage = new Map<string, string>();

  for (const patient of run.cohort) {
    if (tickets.has(patient.ticketId)) {
      failures.push({ code: "duplicate_ticket", message: `${patient.ticketId} assigned twice` });
    }
    tickets.set(patient.ticketId, patient.id);
  }
  if (tickets.size !== run.cohort.length) {
    failures.push({ code: "ticket_count", message: "Ticket count does not match cohort size" });
  }

  for (const event of run.events) {
    if (event.type === "service_started" && event.resourceId && event.patientId) {
      if (busyResource.has(event.resourceId)) {
        failures.push({
          code: "resource_double_booked",
          message: `${event.resourceId} started ${event.patientId} while serving ${busyResource.get(event.resourceId)}`,
        });
      }
      if (patientStage.has(event.patientId)) {
        failures.push({ code: "patient_two_stages", message: `${event.patientId} started a second stage while still in service` });
      }
      busyResource.set(event.resourceId, event.patientId);
      patientStage.set(event.patientId, event.stage ?? "unknown");
    }
    if (event.type === "service_completed" && event.resourceId && event.patientId) {
      busyResource.delete(event.resourceId);
      patientStage.delete(event.patientId);
    }
  }

  const arrived = new Set<string>();
  const exited = new Set<string>();
  for (const event of run.events) {
    if (event.type === "patient_arrived" && event.patientId) arrived.add(event.patientId);
    if (event.type === "patient_exited" && event.patientId) exited.add(event.patientId);
  }
  for (const patientId of exited) {
    if (!arrived.has(patientId)) {
      failures.push({ code: "exit_without_arrival", message: `${patientId} exited without arriving` });
    }
  }

  if (
    run.events.some((event) => event.type === "reassignment_completed") &&
    !run.recommendations.some((item) => item.status === "approved")
  ) {
    failures.push({ code: "unapproved_reassignment", message: "A reassignment completed without an approved recommendation" });
  }

  for (const event of run.events.filter(
    (item) => item.type === "service_completed" && (item.nextState === "ready" || item.nextState === "waiting_consult"),
  )) {
    const attested = run.events.some(
      (prior) => prior.patientId === event.patientId && prior.sequence <= event.sequence && prior.type === "identity_attested",
    );
    if (!attested) {
      failures.push({
        code: "false_ready",
        message: `${event.ticketId ?? event.patientId} became ready without identity attestation`,
      });
    }
  }

  const last = run.events.at(-1);
  if (last) {
    const projected = projectState(run, last.time);
    const total = projected.metrics.notArrived + projected.metrics.inClinic + projected.metrics.completed;
    if (total !== run.cohort.length) {
      failures.push({
        code: "count_conservation",
        message: `Patient counts ${total} do not equal cohort ${run.cohort.length}`,
      });
    }
  }

  return failures;
}
