"use client";

import { useReverification } from "@clerk/nextjs";
import { useState } from "react";

import { useDashboard } from "@/hooks/useDashboard";
import { transitionTicket } from "@/lib/api";
import type { QueueTicket } from "@epicenter/shared/contracts";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";

import { PatientFlowBoard } from "./PatientFlowBoard";
import { TicketReviewModal } from "./TicketReviewModal";
import styles from "./Dashboard.module.css";

export function DashboardView() {
  const { data, source, loading, refresh } = useDashboard();
  const [reviewTicketId, setReviewTicketId] = useState<string | null>(null);
  const reverifiedTransition = useReverification(transitionTicket);

  const reviewTicket = data?.tickets.find((ticket) => ticket.id === reviewTicketId);
  const reviewCase = data?.review_cases.find((item) => item.ticket_id === reviewTicketId);

  async function confirmReview(ticket: QueueTicket) {
    await reverifiedTransition(ticket.id, ticket.version ?? 1, "ready", "all_prerequisites_passed", true);
    setReviewTicketId(null);
    await refresh();
  }

  return (
    <div className={styles.dashboard}>
      {loading || !data ? (
        <LoadingBoard />
      ) : (
        <PatientFlowBoard
          loading={loading}
          onOpenReview={(ticket) => setReviewTicketId(ticket.id)}
          onRefresh={refresh}
          tickets={data.tickets}
        />
      )}

      <div className={styles.contextBar}>
        <span>{data?.clinic_name ?? "Parkway Shenton · HarbourFront"}</span>
        <span>12 Aug 2026 · 09:42</span>
        <span className={source === "api" ? styles.apiSource : styles.demoSource}>
          {source === "api" ? "API connected" : "Local synthetic fallback"}
        </span>
      </div>

      {reviewCase && reviewTicket ? (
        <TicketReviewModal
          onClose={() => setReviewTicketId(null)}
          onConfirm={() => void confirmReview(reviewTicket)}
          reviewCase={reviewCase}
        />
      ) : null}
    </div>
  );
}
