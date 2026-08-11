"use client";

import { useMemo, useState } from "react";

import { useDashboard } from "@/hooks/useDashboard";
import { transitionTicket } from "@/lib/api";
import type { ReviewCase } from "@epicenter/shared/contracts";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";

import { EvidencePanel } from "./EvidencePanel";
import { ReviewCaseList } from "./ReviewCaseList";
import styles from "./Review.module.css";

export function ReviewWorkspace() {
  const { data, loading } = useDashboard();
  const [selectedId, setSelectedId] = useState("R-018");
  const [resolvedIds, setResolvedIds] = useState<string[]>([]);

  const cases = useMemo(() => data?.review_cases.filter((item) => !resolvedIds.includes(item.id)) ?? [], [data, resolvedIds]);
  const selected = cases.find((item) => item.id === selectedId) ?? cases[0];

  async function confirmReview(reviewCase: ReviewCase) {
    try {
      await transitionTicket(reviewCase.ticket_id, "ready", "all_prerequisites_passed", true);
    } finally {
      setResolvedIds((current) => [...current, reviewCase.id]);
    }
  }

  return (
    <div className={styles.reviewPage}>
      <PageHeader
        description="Resolve administrative exceptions with source evidence. Patients retain their original ticket and waiting age throughout."
        title="Assisted review"
      />
      {loading || !data ? (
        <LoadingBoard />
      ) : cases.length === 0 ? (
        <section className={styles.emptyState}>
          <h2>No patients need review</h2>
          <p>All current administrative exceptions have been resolved or returned to processing.</p>
        </section>
      ) : (
        <div className={styles.reviewWorkspace}>
          <ReviewCaseList cases={cases} onSelect={setSelectedId} selectedId={selected?.id} />
          {selected ? <EvidencePanel onConfirm={() => void confirmReview(selected)} reviewCase={selected} /> : null}
        </div>
      )}
    </div>
  );
}
