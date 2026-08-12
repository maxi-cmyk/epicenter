"use client";

import { CreditCard, FileText, Home, Ticket } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import styles from "./PatientShell.module.css";

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/queue", label: "Queue", icon: Ticket },
  { href: "/payment", label: "Payment", icon: CreditCard },
  { href: "/records", label: "Records", icon: FileText },
];

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
      <nav aria-label="Patient destinations" className={styles.nav}>
        {navItems.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              aria-current={active ? "page" : undefined}
              className={active ? styles.navActive : undefined}
              href={item.href}
              key={item.href}
            >
              <Icon aria-hidden="true" size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
