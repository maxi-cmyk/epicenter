import { ShieldCheck } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import styles from "./PatientShell.module.css";

export function PatientShell({ children }: { children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Link aria-label="Epicenter patient registration" className={styles.brand} href="/">
          <span className={styles.brandMark}>E</span>
          <span>
            <strong>Epicenter</strong>
            <small>Patient registration</small>
          </span>
        </Link>
        <span className={styles.environment}><ShieldCheck aria-hidden="true" size={17} /> Synthetic patient journey</span>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  );
}
