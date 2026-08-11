import { ShieldCheck } from "lucide-react";
import Link from "next/link";

import styles from "./AppShell.module.css";

export function MobileHeader() {
  return (
    <header className={styles.mobileHeader}>
      <Link href="/"><strong>EPICENTER</strong></Link>
      <span><ShieldCheck aria-hidden="true" size={16} /> Nurse · Synthetic</span>
    </header>
  );
}
