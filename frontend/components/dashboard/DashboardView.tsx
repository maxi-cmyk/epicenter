"use client";

import { RefreshCw } from "lucide-react";

import { useDashboard } from "@/hooks/useDashboard";
import { Button } from "@/components/shared/Button";
import { LoadingBoard } from "@/components/shared/LoadingBoard";
import { PageHeader } from "@/components/shared/PageHeader";

import { ActivityRail } from "./ActivityRail";
import { AllocationDecision } from "./AllocationDecision";
import { MetricsRail } from "./MetricsRail";
import { PatientFlowBoard } from "./PatientFlowBoard";
import styles from "./Dashboard.module.css";

export function DashboardView() {
  const { data, source, loading, refresh } = useDashboard();

  return (
    <div className={styles.dashboard}>
      <PageHeader
        actions={
          <Button disabled={loading} icon={<RefreshCw aria-hidden="true" size={17} />} onClick={() => void refresh()} variant="secondary">
            Refresh board
          </Button>
        }
        description="One operational view for booked patients, walk-ins, assisted review and human-approved counter changes."
        title="Today’s clinic flow"
      />

      <div className={styles.contextBar}>
        <span>{data?.clinic_name ?? "Parkway Shenton · HarbourFront"}</span>
        <span>12 Aug 2026 · 09:42</span>
        <span className={source === "api" ? styles.apiSource : styles.demoSource}>
          {source === "api" ? "API connected" : "Local synthetic fallback"}
        </span>
      </div>

      {loading || !data ? (
        <LoadingBoard />
      ) : (
        <>
          <MetricsRail metrics={data.metrics} recommendation={data.recommendation} />
          <PatientFlowBoard tickets={data.tickets} />
          <div className={styles.lowerGrid}>
            <AllocationDecision initialRecommendation={data.recommendation} />
            <ActivityRail activity={data.activity} />
          </div>
        </>
      )}
    </div>
  );
}
