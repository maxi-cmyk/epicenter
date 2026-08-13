import { Check } from "lucide-react";
import Link from "next/link";

import type { QueueTicket } from "@epicenter/shared/contracts";
import { isStepComplete, isStepUnlocked, TASK_STEP_LABELS, type TaskStep, visibleSteps } from "@/lib/task-steps";

import styles from "./Task.module.css";

export function TaskSteps({ current, ticket }: { current: TaskStep; ticket: QueueTicket }) {
  return (
    <ol aria-label="Ticket workflow progress" className={styles.steps}>
      {visibleSteps(ticket).map((step, index) => {
        const unlocked = isStepUnlocked(ticket, step);
        const complete = isStepComplete(ticket, step);
        const isCurrent = step === current;
        const itemClassName = isCurrent ? styles.currentStep : complete ? styles.completeStep : undefined;
        const label = TASK_STEP_LABELS[step];
        return (
          <li aria-current={isCurrent ? "step" : undefined} className={itemClassName} key={step}>
            {unlocked ? (
              <Link href={`/tasks/${ticket.id}/${step}`}>
                <span>{complete ? <Check aria-hidden="true" size={15} /> : index + 1}</span>
                <strong>{label}</strong>
              </Link>
            ) : (
              <span className={styles.lockedStep}>
                <span>{index + 1}</span>
                <strong>{label}</strong>
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
