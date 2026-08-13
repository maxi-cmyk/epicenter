import type { QueueTicket } from "@epicenter/shared/contracts";

export const TASK_STEPS = ["identity", "forms", "forms-review", "package", "billing", "summary"] as const;

export type TaskStep = (typeof TASK_STEPS)[number];

export const TASK_STEP_LABELS: Record<TaskStep, string> = {
  identity: "Identity & e-card",
  forms: "Forms guidance",
  "forms-review": "Forms review",
  package: "Package recheck",
  billing: "Billing & queue",
  summary: "Summary",
};

/** Whether the nurse is allowed to open this step's page yet, given what's confirmed so far. */
export function isStepUnlocked(ticket: QueueTicket, step: TaskStep): boolean {
  switch (step) {
    case "identity":
      return true;
    case "forms":
    case "forms-review":
      return ticket.identity_confirmed;
    case "package":
      return ticket.forms_confirmed;
    case "billing":
      return ticket.package_confirmed;
    case "summary":
      return ticket.billing_confirmed;
  }
}

/** Whether this step's own gating action has already been done (used for the stepper's checkmarks). */
export function isStepComplete(ticket: QueueTicket, step: TaskStep): boolean {
  switch (step) {
    case "identity":
      return ticket.identity_confirmed;
    case "forms":
      // The forms-guidance page has no confirm action of its own; it rides on the identity gate.
      return ticket.identity_confirmed;
    case "forms-review":
      return ticket.forms_confirmed;
    case "package":
      return ticket.package_confirmed;
    case "billing":
      return ticket.billing_confirmed;
    case "summary":
      return false;
  }
}

export function nextIncompleteStep(ticket: QueueTicket): TaskStep {
  if (!ticket.identity_confirmed) return "identity";
  if (!ticket.forms_confirmed) return "forms-review";
  if (!ticket.package_confirmed) return "package";
  if (!ticket.billing_confirmed) return "billing";
  return "summary";
}
