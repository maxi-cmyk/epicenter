"use client";

import { ClipboardCheck, LayoutDashboard, ScanLine } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "./AppShell.module.css";

type NavItem = { href: string; label: string; icon: typeof LayoutDashboard };

const NAVIGATION: NavItem[] = [
  { href: "/", label: "Readiness board", icon: LayoutDashboard },
  { href: "/review", label: "Assisted review", icon: ClipboardCheck },
  { href: "/kiosk", label: "Walk-in kiosk", icon: ScanLine },
];

export function SideNavigation() {
  const pathname = usePathname();
  return (
    <aside className={styles.sidebar}>
      <Link aria-label="Epicenter nurse home" className={styles.brand} href="/">
        <span className={styles.brandMark}>E</span>
        <span>
          <strong>Epicenter</strong>
          <small>Clinic readiness</small>
        </span>
      </Link>
      <nav aria-label="Primary navigation" className={styles.navigation}>
        {NAVIGATION.map(({ href, label, icon: Icon }) => {
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
          <strong>Nurse panel</strong>
          <small>No live patient data</small>
        </span>
      </div>
    </aside>
  );
}
