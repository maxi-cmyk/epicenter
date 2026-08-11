import { Check } from "lucide-react";

import styles from "./Kiosk.module.css";

const steps = ["Supervised intake", "Processing", "Staff confirmation", "Ready service"];

export function KioskSteps({ activeStep }: { activeStep: number }) {
  return (
    <ol aria-label="Walk-in registration progress" className={styles.steps}>
      {steps.map((step, index) => {
        const current = index + 1 === activeStep;
        const complete = index + 1 < activeStep;
        return (
          <li aria-current={current ? "step" : undefined} className={current ? styles.currentStep : complete ? styles.completeStep : undefined} key={step}>
            <span>{complete ? <Check aria-hidden="true" size={15} /> : index + 1}</span>
            <strong>{step}</strong>
          </li>
        );
      })}
    </ol>
  );
}
