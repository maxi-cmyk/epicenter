"use client";

import { ClipboardCheck, LayoutDashboard, ScanLine, Stethoscope } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "./AppShell.module.css";

const navigation = [
  { href: "/", label: "Operations", icon: LayoutDashboard },
  { href: "/review", label: "Assisted review", icon: ClipboardCheck },
  { href: "/kiosk", label: "Walk-in kiosk", icon: ScanLine },
  { href: "/pre-arrival", label: "Patient pre-check", icon: Stethoscope },
];

export function SideNavigation() {
  const pathname = usePathname();
  return (
    <aside className={styles.sidebar}>
      <Link aria-label="Epicenter operations home" className={styles.brand} href="/">
        <span className={styles.brandMark}>E</span>
        <span>
          <strong>Epicenter</strong>
          <small>Clinic readiness</small>
        </span>
      </Link>
      <nav aria-label="Primary navigation" className={styles.navigation}>
        {navigation.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link aria-current={active ? "page" : undefined} className={active ? styles.activeLink : styles.navLink} href={href} key={href}>
              <Icon aria-hidden="true" size={19} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className={styles.sidebarFoot}>
        <span className={styles.liveDot} />
        <span>
          <strong>Synthetic demo</strong>
          <small>No live patient data</small>
        </span>
      </div>
    </aside>
  );
}
