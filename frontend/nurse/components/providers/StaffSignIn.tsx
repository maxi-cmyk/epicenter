"use client";

import { SignIn } from "@clerk/nextjs";
import { ClipboardCheck, ShieldCheck, Stethoscope } from "lucide-react";

import styles from "./AuthProvider.module.css";

const assurances = [
  { icon: ShieldCheck, label: "Individual staff accountability" },
  { icon: ClipboardCheck, label: "Human confirmation remains required" },
  { icon: Stethoscope, label: "Administrative readiness only" },
];

export function StaffSignIn() {
  return (
    <main className={styles.signInPage}>
      <section className={styles.signInContext}>
        <div className={styles.signInBrand}>
          <span aria-hidden="true">E</span>
          <strong>Epicenter</strong>
        </div>
        <div>
          <h1>Staff access to today&apos;s clinic flow</h1>
          <p>
            Sign in with your assigned clinic account. Every confirmation and operational decision remains attributable
            to the staff member who made it.
          </p>
        </div>
        <ul className={styles.assuranceList}>
          {assurances.map(({ icon: Icon, label }) => (
            <li key={label}>
              <Icon aria-hidden="true" size={18} />
              <span>{label}</span>
            </li>
          ))}
        </ul>
        <small>Synthetic demonstration · no live patient data</small>
      </section>
      <section aria-label="Staff sign in" className={styles.signInControl}>
        <div className={styles.signInTask}>
          <h2>Open the operations workspace</h2>
          <p>Use the staff account issued by your clinic administrator.</p>
          <p className={styles.provisioningNote}>Staff accounts are provisioned by the clinic. Self-service sign-up is unavailable.</p>
          <SignIn
            appearance={{
              elements: {
                footerAction: { display: "none" },
                headerSubtitle: { display: "none" },
                headerTitle: { display: "none" },
              },
            }}
            routing="hash"
            withSignUp={false}
          />
        </div>
      </section>
    </main>
  );
}
