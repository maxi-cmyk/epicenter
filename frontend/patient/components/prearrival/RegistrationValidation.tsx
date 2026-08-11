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
    <table className={styles.validationTable}>
      <caption className="sr-only">Comparison of booking details with consented Myinfo data</caption>
      <thead>
        <tr><th scope="col">Registration field</th><th scope="col">Booking value</th><th scope="col">Validation</th></tr>
      </thead>
      <tbody>
        {fields.map((field) => (
          <tr key={field.label}>
            <th data-label="Field" scope="row">{field.label}</th>
            <td data-label="Booking value">{field.booking}</td>
            <td data-label="Validation" className={field.state === "validated" ? styles.validated : styles.notCompared}>
              {field.state === "validated" ? <Check aria-hidden="true" size={15} /> : <Minus aria-hidden="true" size={15} />}
              {field.state === "validated" ? "Source validated" : "Not compared"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
