"use client";

import { RotateCcw, TriangleAlert } from "lucide-react";

import { useDashboard } from "@/hooks/useDashboard";
import { Button } from "@epicenter/shared/ui/Button";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";

import { PatientFlowBoard } from "./PatientFlowBoard";
import { AssistantPanel } from "@/components/assistant/AssistantPanel";
import styles from "./Dashboard.module.css";

export function DashboardView() {
  const { data, error, source, loading, refreshing, refresh } = useDashboard();
  const generatedAt = data
    ? new Intl.DateTimeFormat("en-SG", { dateStyle: "medium", timeStyle: "short" }).format(new Date(data.generated_at))
    : null;

  return (
    <div className={styles.dashboard}>
      <div className={styles.contextBar}>
        <span>{data?.clinic_name ?? "Parkway Shenton · HarbourFront"}</span>
        <span>{generatedAt ? `Updated ${generatedAt}` : "Waiting for clinic data"}</span>
      </div>

      {loading ? (
        <LoadingBoard />
      ) : !data ? (
        <section className={styles.loadError} role="alert">
          <TriangleAlert aria-hidden="true" size={24} />
          <div>
            <h1>Clinic data could not be loaded</h1>
            <p>{error || "Check the clinic API connection, then try again."}</p>
          </div>
          <Button icon={<RotateCcw aria-hidden="true" size={15} />} onClick={() => void refresh()}>
            Retry
          </Button>
        </section>
      ) : (
        <>
          {source === "fallback" ? (
            <div className={styles.fallbackBanner} role="alert">
              <TriangleAlert aria-hidden="true" size={22} />
              <div>
                <strong>Demo data only — confirmations are disabled</strong>
                <span>The live clinic API could not be reached. Reconnect before acting on a patient record.</span>
              </div>
              <Button icon={<RotateCcw aria-hidden="true" size={15} />} onClick={() => void refresh()} variant="secondary">
                Try live data again
              </Button>
            </div>
          ) : null}
          {error ? <p className={styles.refreshError}>{error}</p> : null}
          <AssistantPanel available={source === "api"} />
          <PatientFlowBoard
            loading={refreshing}
            onRefresh={refresh}
            reviewCases={data.review_cases}
            tickets={data.tickets}
          />
        </>
      )}

    </div>
  );
}
