"use client";

import { useCallback, useState } from "react";
import { useMountedLoad } from "@/lib/useMountedLoad";

import { Button } from "@epicenter/shared/ui/Button";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";
import type { PatientVisitHistory, PatientVisitRecord } from "@epicenter/shared/contracts";

import { getPatientRecords } from "@/lib/api";

import styles from "../home/Journey.module.css";

export function RecordsWorkspace() {
  const [history, setHistory] = useState<PatientVisitHistory | null>(null);
  const [selected, setSelected] = useState<PatientVisitRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setHistory(await getPatientRecords());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load visit history.");
    } finally {
      setLoading(false);
    }
  }, []);

  useMountedLoad(load);

  if (loading && !history) {
    return (
      <div aria-busy="true" className={styles.page}>
        <div className={styles.skeletonCard} />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader description="Read-only history for visits linked to your account." title="Your visit history" />
      {history && history.visits.length > 0 ? (
        <ul className={styles.recordsList}>
          {history.visits.map((visit) => (
            <li key={visit.appointment_id}>
              <strong>
                {visit.visited_on} · {visit.visit_label}
              </strong>
              <span className={styles.muted}>{visit.coverage_label ?? "Coverage on file"}</span>
              <button onClick={() => setSelected(visit)} type="button">
                Open
              </button>
              {selected?.appointment_id === visit.appointment_id ? (
                <div className={styles.detailCard}>
                  <div>Package: {visit.package_label ?? "—"}</div>
                  <div>Coverage: {visit.coverage_label ?? "—"}</div>
                  <div>Questionnaire: {visit.questionnaire_summary ?? "—"}</div>
                  <div>Outcome: {visit.outcome ?? "—"}</div>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <section className={styles.panel}>
          <p>No appointment has been made yet, so there is no visit history.</p>
          {error ? (
            <div className={styles.errorBox} role="alert">
              {error}
              <Button onClick={() => void load()}>Retry</Button>
            </div>
          ) : null}
        </section>
      )}
    </div>
  );
}
