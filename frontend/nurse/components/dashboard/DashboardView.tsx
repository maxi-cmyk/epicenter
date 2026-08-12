"use client";

import { useDashboard } from "@/hooks/useDashboard";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";

import { PatientFlowBoard } from "./PatientFlowBoard";
import styles from "./Dashboard.module.css";

export function DashboardView() {
  const { data, source, loading, refresh } = useDashboard();

  return (
    <div className={styles.dashboard}>
      {loading || !data ? (
        <LoadingBoard />
      ) : (
        <PatientFlowBoard loading={loading} onRefresh={refresh} tickets={data.tickets} />
      )}

      <div className={styles.contextBar}>
        <span>{data?.clinic_name ?? "Parkway Shenton · HarbourFront"}</span>
        <span>12 Aug 2026 · 09:42</span>
        <span className={source === "api" ? styles.apiSource : styles.demoSource}>
          {source === "api" ? "API connected" : "Local synthetic fallback"}
        </span>
      </div>
    </div>
  );
}
