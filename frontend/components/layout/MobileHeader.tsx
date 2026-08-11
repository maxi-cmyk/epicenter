import { ShieldCheck } from "lucide-react";
import Link from "next/link";

import type { AppRole } from "@/lib/app-role";

import styles from "./AppShell.module.css";

const HOME_HREF_BY_ROLE: Record<AppRole, string> = {
  patient: "/pre-arrival",
  nurse: "/",
  combined: "/",
};

export function MobileHeader({ role }: { role: AppRole }) {
  return (
    <header className={styles.mobileHeader}>
      <Link href={HOME_HREF_BY_ROLE[role]}><strong>EPICENTER</strong></Link>
      <span><ShieldCheck aria-hidden="true" size={16} /> Synthetic</span>
    </header>
  );
}
