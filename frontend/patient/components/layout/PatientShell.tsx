"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import styles from "./PatientShell.module.css";

export function PatientShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const hideChrome = pathname?.startsWith("/upload/") || pathname === "/onboarding";

  if (hideChrome) {
    return <main className={styles.mainBare}>{children}</main>;
  }

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Link aria-label="Epicenter patient home" className={styles.brand} href="/">
          <span className={styles.brandMark}>E</span>
          <span>
            <strong>Epicenter</strong>
            <small>Patient journey</small>
          </span>
        </Link>
        <span className={styles.environment}>Synthetic demonstration</span>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  );
}
