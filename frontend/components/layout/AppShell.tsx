import type { ReactNode } from "react";

import type { AppRole } from "@/lib/app-role";

import { MobileHeader } from "./MobileHeader";
import { SideNavigation } from "./SideNavigation";
import styles from "./AppShell.module.css";

export function AppShell({ children, role }: { children: ReactNode; role: AppRole }) {
  return (
    <div className={styles.shell}>
      <SideNavigation role={role} />
      <MobileHeader role={role} />
      <main className={styles.main}>{children}</main>
    </div>
  );
}
