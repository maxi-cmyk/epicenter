"use client";

import {
  AlertCircle,
  ArrowRight,
  CalendarDays,
  ClipboardList,
  CreditCard,
  FileText,
  RefreshCw,
  ShieldCheck,
  Ticket,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useState } from "react";

import { Button } from "@epicenter/shared/ui/Button";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";
import type { PatientHome } from "@epicenter/shared/contracts";

import { getPatientHome } from "@/lib/api";
import { useMountedLoad } from "@/lib/useMountedLoad";

import styles from "./Journey.module.css";

function formatWhen(value: string) {
  return new Intl.DateTimeFormat("en-SG", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Singapore",
  }).format(new Date(value));
}

function firstName(fullName: string) {
  const part = fullName.trim().split(/\s+/)[0];
  return part || fullName;
}

function questionnaireLabel(status: PatientHome["questionnaire_status"]) {
  if (status === "submitted") return "Submitted";
  if (status === "draft") return "Draft saved";
  if (status === "not_required") return "Not required";
  return "Not started";
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
        <header className={styles.homeIntro}>
          <p className={styles.homeEyebrow}>Patient home</p>
          <h1>Hi {home ? firstName(home.patient_display_name) : "there"}</h1>
          <p>
            No appointment has been made yet. Your preparation progress stays here until the clinic books your
            visit.
          </p>
        </header>

        <section className={styles.emptyHero} aria-labelledby="empty-appointment-title">
          <div className={styles.emptyHeroIcon}>
            <CalendarDays aria-hidden="true" size={28} />
          </div>
          <div>
            <h2 id="empty-appointment-title">No appointment has been made</h2>
            <p>
              When HarbourFront or another clinic books you in, the time, location, queue ticket, and payment
              step will appear on this page.
            </p>
          </div>
        </section>

        {home ? (
          <section className={styles.prepPanel} aria-label="Preparation status">
            <div className={styles.prepHeading}>
              <strong>Preparation</strong>
              <span>Ready when you book</span>
            </div>
            <ul className={styles.prepList}>
              <li>
                <span className={styles.prepIcon}>
                  <ShieldCheck aria-hidden="true" size={18} />
                </span>
                <div>
                  <strong>Coverage</strong>
                  <p>{home.coverage_summary}</p>
                </div>
              </li>
              <li>
                <span className={styles.prepIcon}>
                  <ClipboardList aria-hidden="true" size={18} />
                </span>
                <div>
                  <strong>Questionnaire</strong>
                  <p>{questionnaireLabel(home.questionnaire_status)}</p>
                </div>
              </li>
              <li>
                <span className={styles.prepIcon}>
                  <Ticket aria-hidden="true" size={18} />
                </span>
                <div>
                  <strong>Queue</strong>
                  <p>{home.queue_summary}</p>
                </div>
              </li>
            </ul>
          </section>
        ) : null}

        <nav aria-label="Other patient pages" className={styles.homeShortcuts}>
          <Link href="/records">
            <FileText aria-hidden="true" size={18} />
            Records
          </Link>
          <Link href="/queue">
            <Ticket aria-hidden="true" size={18} />
            Queue
          </Link>
          <Link href="/payment">
            <CreditCard aria-hidden="true" size={18} />
            Payment
          </Link>
        </nav>

        <button className={styles.refreshLink} onClick={() => void load()} type="button">
          <RefreshCw aria-hidden="true" size={16} />
          {loading ? "Refreshing…" : "Refresh status"}
        </button>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.homeIntro}>
        <p className={styles.homeEyebrow}>Upcoming visit</p>
        <h1>Hi {firstName(home.patient_display_name)}</h1>
        <p>One appointment, one ticket, and only the next step you can complete now.</p>
      </header>

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
          <span className={styles.appointmentIcon}>
            <CalendarDays aria-hidden="true" size={22} />
          </span>
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
            <dd>{questionnaireLabel(home.questionnaire_status)}</dd>
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
                {home.recent_visit_summary} <Link href="/records">View</Link>
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

        {home.primary_action !== "none" ? (
          <Link className={styles.primaryLink} href={home.primary_action_href}>
            {home.primary_action_label}
            <ArrowRight aria-hidden="true" size={18} />
          </Link>
        ) : null}

        <button className={styles.refreshLink} onClick={() => void load()} type="button">
          <RefreshCw aria-hidden="true" size={16} />
          {loading ? "Refreshing…" : "Refresh status"}
        </button>
      </section>
    </div>
  );
}
