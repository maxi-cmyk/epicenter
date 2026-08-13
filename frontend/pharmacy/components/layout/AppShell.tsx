import type { ReactNode } from "react";

import { MobileHeader } from "./MobileHeader";
import { SideNavigation } from "./SideNavigation";
import styles from "./AppShell.module.css";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <SideNavigation />
      <MobileHeader />
      <main className={styles.main}>{children}</main>
    </div>
  );
}
