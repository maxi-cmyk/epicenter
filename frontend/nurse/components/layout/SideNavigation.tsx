"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import { Database, LayoutDashboard, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useStaffRole } from "@/components/providers/AuthProvider";

import styles from "./AppShell.module.css";

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

type NavItem = { href: string; label: string; icon: typeof LayoutDashboard };

const NAVIGATION: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/database", label: "Database", icon: Database },
  { href: "/audit", label: "Audit trail", icon: ShieldCheck },
];

export function SideNavigation() {
  const visualQaBypass =
    process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_E2E_BYPASS_AUTH === "true";
  return visualQaBypass ? <NavigationView displayName="Synthetic nurse" role="registration" /> : <AuthenticatedNavigation />;
}

function AuthenticatedNavigation() {
  const { user } = useUser();
  const role = useStaffRole();
  return <NavigationView displayName={user?.fullName || user?.primaryEmailAddress?.emailAddress || "Signed in"} role={role} userButton />;
}

function NavigationView({ displayName, role, userButton = false }: { displayName: string; role: string | null; userButton?: boolean }) {
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
        <div className={styles.profileText}>
          <strong>{displayName}</strong>
          {role ? <small>{capitalize(role)}</small> : null}
        </div>
        {userButton ? <UserButton
          appearance={{
            elements: {
              userButtonAvatarBox: styles.userButtonAvatar,
              userButtonTrigger: styles.userButtonTrigger,
            },
          }}
        /> : null}
      </div>
    </aside>
  );
}
