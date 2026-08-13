"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import { ClipboardCheck, LayoutDashboard, Waypoints } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useStaffRole } from "@/components/providers/AuthProvider";

import styles from "./AppShell.module.css";

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

type NavItem = { href: string; label: string; icon: typeof LayoutDashboard };

const NAVIGATION: NavItem[] = [
  { href: "/", label: "Readiness board", icon: LayoutDashboard },
  { href: "/review", label: "Assisted review", icon: ClipboardCheck },
  { href: "/simulator", label: "Simulator", icon: Waypoints },
];

export function SideNavigation() {
  const pathname = usePathname();
  const { user } = useUser();
  const role = useStaffRole();
  const displayName = user?.fullName || user?.primaryEmailAddress?.emailAddress || "Signed in";

  return (
    <aside className={styles.sidebar}>
      <Link aria-label="Epicenter nurse home" className={styles.brand} href="/">
        <span className={styles.brandMark}>E</span>
        <span>
          <strong>Epicenter</strong>
          <small>Clinic readiness</small>
        </span>
      </Link>
      <nav aria-label="Nurse panel" className={styles.navigation}>
        {NAVIGATION.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link aria-current={active ? "page" : undefined} className={active ? styles.activeLink : styles.navLink} href={href} key={href}>
              <Icon aria-hidden="true" size={19} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className={styles.sidebarFoot}>
        <div className={styles.profileText}>
          <strong>{displayName}</strong>
          {role ? <small>{capitalize(role)}</small> : null}
        </div>
        <UserButton
          appearance={{
            elements: {
              userButtonAvatarBox: styles.userButtonAvatar,
              userButtonTrigger: styles.userButtonTrigger,
            },
          }}
        />
      </div>
    </aside>
  );
}
