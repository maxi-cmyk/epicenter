"use client";

import { AlertCircle, ArrowRight, CalendarDays, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useCallback, useState } from "react";
import { useMountedLoad } from "@/lib/useMountedLoad";

import { Button } from "@epicenter/shared/ui/Button";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";
import type { PatientHome } from "@epicenter/shared/contracts";

import { getPatientHome } from "@/lib/api";

import styles from "./Journey.module.css";

function formatWhen(value: string) {
  return new Intl.DateTimeFormat("en-SG", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Singapore",
  }).format(new Date(value));
}

export function HomeWorkspace() {
  const [home, setHome] = useState<PatientHome | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setHome(await getPatientHome());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to open your booking.");
    } finally {
      setLoading(false);
    }
  }, []);

  useMountedLoad(load);

  if (loading && !home) {
    return (
      <div aria-busy="true" className={styles.page}>
        <div className={styles.skeletonCard} />
      </div>
    );
  }

  if (error && !home) {
    return (
      <div className={styles.page} role="alert">
        <PageHeader description={error} title="Booking unavailable" />
        <Button onClick={() => void load()}>Retry</Button>
      </div>
    );
  }

  if (!home?.appointment) {
    return (
      <div className={styles.page}>
        <PageHeader
          description="No appointment has been made yet. Complete onboarding if needed, then book with the clinic."
          title={home ? `Hi ${home.patient_display_name}` : "No appointment has been made"}
        />
        {home ? (
          <section className={styles.panel}>
            <p className={styles.muted}>Coverage: {home.coverage_summary}</p>
            <p className={styles.muted}>Questionnaire: {home.questionnaire_status}</p>
            <p className={styles.muted}>Queue: {home.queue_summary}</p>
          </section>
        ) : null}
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader
        description="One upcoming visit, one ticket, and only the next step you can complete now."
        title={`Hi ${home.patient_display_name}`}
      />

      {home.notification ? (
        <div className={styles.banner} role="status">
          <AlertCircle aria-hidden="true" size={20} />
          <div>
            <strong>Action needed</strong>
            <p>{home.notification.message}</p>
            <Link href="/coverage">{home.notification.next_action}</Link>
          </div>
        </div>
      ) : null}

      <section className={styles.homeCard}>
        <div className={styles.homeMeta}>
          <CalendarDays aria-hidden="true" size={22} />
          <div>
            <strong>Upcoming appointment</strong>
            <p>{formatWhen(home.appointment.scheduled_at)}</p>
            <small>
              {home.appointment.clinic_name} · {home.appointment.location}
            </small>
          </div>
        </div>

        <dl className={styles.summaryList}>
          <div>
            <dt>Coverage</dt>
            <dd>{home.coverage_summary}</dd>
          </div>
          <div>
            <dt>Questionnaire</dt>
            <dd>
              {home.questionnaire_status === "submitted"
                ? "Submitted"
                : home.questionnaire_status === "draft"
                  ? "Draft saved"
                  : "Not started"}
            </dd>
          </div>
          <div>
            <dt>Queue</dt>
            <dd>{home.queue_summary}</dd>
          </div>
          <div>
            <dt>Payment</dt>
            <dd>{home.payment_summary}</dd>
          </div>
          {home.recent_visit_summary ? (
            <div>
              <dt>Recent visit</dt>
              <dd>
                {home.recent_visit_summary}{" "}
                <Link href="/records">View</Link>
              </dd>
            </div>
          ) : null}
        </dl>

        {home.outcome_message ? (
          <div className={styles.outcome} data-outcome={home.outcome ?? undefined}>
            <strong>
              {home.outcome === "accepted"
                ? "Accepted for staff confirmation"
                : home.outcome === "rejected"
                  ? "Needs your attention"
                  : "Under review"}
            </strong>
            <p>{home.outcome_message}</p>
          </div>
        ) : null}

        <Link className={styles.primaryLink} href={home.primary_action_href}>
          {home.primary_action_label}
          <ArrowRight aria-hidden="true" size={18} />
        </Link>

        <button className={styles.refreshLink} onClick={() => void load()} type="button">
          <RefreshCw aria-hidden="true" size={16} />
          {loading ? "Refreshing…" : "Refresh status"}
        </button>
      </section>
    </div>
  );
}
