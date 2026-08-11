import { Check, Minus } from "lucide-react";

import styles from "./PreArrival.module.css";

const fields = [
  { label: "Full name", booking: "Loh Wei Ming", source: "Myinfo", state: "validated" },
  { label: "Date of birth", booking: "14 May 1988", source: "Myinfo", state: "validated" },
  { label: "Mobile number", booking: "+65 •••• 8124", source: "Myinfo", state: "validated" },
  { label: "Email", booking: "wei.ming@example.sg", source: "Patient entry", state: "not_compared" },
];

export function RegistrationValidation() {
  return (
    <div className={styles.validationTable}>
      <header><span>Registration field</span><span>Booking value</span><span>Validation</span></header>
      {fields.map((field) => (
        <div key={field.label}>
          <strong>{field.label}</strong>
          <span>{field.booking}</span>
          <span className={field.state === "validated" ? styles.validated : styles.notCompared}>
            {field.state === "validated" ? <Check aria-hidden="true" size={15} /> : <Minus aria-hidden="true" size={15} />}
            {field.state === "validated" ? "Source validated" : "Not compared"}
          </span>
        </div>
      ))}
    </div>
  );
}
