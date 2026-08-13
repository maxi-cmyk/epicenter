"use client";

import { RefreshCw } from "lucide-react";
import Link from "next/link";
import { useCallback, useState } from "react";
import { useMountedLoad } from "@/lib/useMountedLoad";

import { Button } from "@epicenter/shared/ui/Button";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";
import type { PatientQueueStatus } from "@epicenter/shared/contracts";

import { getPatientQueue } from "@/lib/api";

import styles from "../home/Journey.module.css";

function formatUpdated(value: string) {
  return new Intl.DateTimeFormat("en-SG", {
    timeStyle: "short",
    timeZone: "Asia/Singapore",
  }).format(new Date(value));
}

export function QueueWorkspace() {
  const [queue, setQueue] = useState<PatientQueueStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stale, setStale] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      setQueue(await getPatientQueue());
      setStale(false);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load queue status.");
      setStale(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useMountedLoad(load);

  if (loading && !queue) {
    return (
      <div aria-busy="true" className={styles.page}>
        <div className={styles.skeletonCard} />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.queueHeader}>
        <PageHeader
          description="Your queue number and counter appear once the clinic assigns them to this visit."
          title="Queue status"
        />
        <Button
          disabled={refreshing}
          onClick={() => void load(true)}
          variant="secondary"
          icon={<RefreshCw aria-hidden="true" size={16} />}
        >
          {refreshing ? "Refreshing…" : "Refresh"}
        </Button>
      </div>

      {queue ? (
        <section className={styles.panel}>
          <div className={styles.statusHero}>
            <strong>{queue.queue_number ?? queue.ticket_id ?? "No appointment has been made"}</strong>
            <p>{queue.status_label === "No active ticket" ? "No appointment has been made" : queue.status_label}</p>
          </div>
          <dl className={styles.summaryList}>
            <div>
              <dt>Queue number</dt>
              <dd>{queue.queue_number ?? queue.ticket_id ?? "Assigned at check-in"}</dd>
            </div>
            <div>
              <dt>Counter</dt>
              <dd>{queue.counter_label ?? "Assigned at check-in"}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{queue.status_detail}</dd>
            </div>
            <div>
              <dt>Patients ahead</dt>
              <dd>{queue.patients_ahead == null ? "—" : queue.patients_ahead}</dd>
            </div>
            <div>
              <dt>{stale ? "Last updated (not current)" : "Updated"}</dt>
              <dd>{formatUpdated(queue.updated_at)}</dd>
            </div>
          </dl>
          {queue.payment_ready ? <Link href="/payment">Continue to payment</Link> : null}
          {stale || error ? (
            <div className={styles.errorBox} role="alert">
              <strong>{stale ? "Showing last known status" : "Queue status unavailable"}</strong>
              <span>{error}</span>
              <Button onClick={() => void load(true)}>Retry</Button>
            </div>
          ) : null}
        </section>
      ) : (
        <div className={styles.errorBox} role="alert">
          <strong>Queue status unavailable</strong>
          <span>{error}</span>
          <Button onClick={() => void load()}>Retry</Button>
        </div>
      )}
    </div>
  );
}
