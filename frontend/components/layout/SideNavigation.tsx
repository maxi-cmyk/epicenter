"use client";

import { ClipboardCheck, LayoutDashboard, ScanLine, Stethoscope } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import type { AppRole } from "@/lib/app-role";

import styles from "./AppShell.module.css";

type NavItem = { href: string; label: string; icon: typeof LayoutDashboard };

const NAV_BY_ROLE: Record<AppRole, NavItem[]> = {
  patient: [{ href: "/pre-arrival", label: "Patient pre-check", icon: Stethoscope }],
  nurse: [
    { href: "/", label: "Readiness board", icon: LayoutDashboard },
    { href: "/review", label: "Assisted review", icon: ClipboardCheck },
    { href: "/kiosk", label: "Walk-in kiosk", icon: ScanLine },
  ],
  combined: [
    { href: "/", label: "Operations", icon: LayoutDashboard },
    { href: "/review", label: "Assisted review", icon: ClipboardCheck },
    { href: "/kiosk", label: "Walk-in kiosk", icon: ScanLine },
    { href: "/pre-arrival", label: "Patient pre-check", icon: Stethoscope },
  ],
};

const HOME_HREF_BY_ROLE: Record<AppRole, string> = {
  patient: "/pre-arrival",
  nurse: "/",
  combined: "/",
};

const FOOT_LABEL_BY_ROLE: Record<AppRole, string> = {
  patient: "Patient screen",
  nurse: "Nurse screen",
  combined: "Synthetic demo",
};

export function SideNavigation({ role }: { role: AppRole }) {
  const pathname = usePathname();
  const navigation = NAV_BY_ROLE[role];
  return (
    <aside className={styles.sidebar}>
      <Link aria-label="Epicenter home" className={styles.brand} href={HOME_HREF_BY_ROLE[role]}>
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
          <strong>{FOOT_LABEL_BY_ROLE[role]}</strong>
          <small>No live patient data</small>
        </span>
      </div>
    </aside>
  );
}
