"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import { Pill } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useStaffRole } from "@/components/providers/AuthProvider";

import styles from "./AppShell.module.css";

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

type NavItem = { href: string; label: string; icon: typeof Pill };

const NAVIGATION: NavItem[] = [{ href: "/", label: "Pharmacy queue", icon: Pill }];

export function SideNavigation() {
  const pathname = usePathname();
  const { user } = useUser();
  const role = useStaffRole();
  const displayName = user?.fullName || user?.primaryEmailAddress?.emailAddress || "Signed in";

  return (
    <aside className={styles.sidebar}>
      <Link aria-label="Epicenter pharmacy home" className={styles.brand} href="/">
        <span className={styles.brandMark}>E</span>
        <span>
          <strong>Epicenter</strong>
          <small>Pharmacy</small>
        </span>
      </Link>
      <nav aria-label="Primary navigation" className={styles.navigation}>
        {NAVIGATION.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith("/tickets/");
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
