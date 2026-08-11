import { ChevronRight, Clock3 } from "lucide-react";

import { StatusBadge } from "@/components/shared/StatusBadge";
import type { ReviewCase } from "@/lib/types";

import styles from "./Review.module.css";

interface ReviewCaseListProps {
  cases: ReviewCase[];
  selectedId?: string;
  onSelect: (id: string) => void;
}

export function ReviewCaseList({ cases, selectedId, onSelect }: ReviewCaseListProps) {
  return (
    <section aria-label="Review worklist" className={styles.caseList}>
      <header>
        <h2>Review worklist</h2>
        <span>{cases.length} open</span>
      </header>
      {cases.map((reviewCase) => (
        <button
          aria-pressed={selectedId === reviewCase.id}
          className={selectedId === reviewCase.id ? styles.selectedCase : styles.caseButton}
          key={reviewCase.id}
          onClick={() => onSelect(reviewCase.id)}
          type="button"
        >
          <div className={styles.caseIdentity}>
            <strong>{reviewCase.ticket_id}</strong>
            <span>{reviewCase.patient_name}</span>
          </div>
          <p>{reviewCase.reason_label}</p>
          <div className={styles.caseMeta}>
            <span><Clock3 aria-hidden="true" size={14} /> {reviewCase.waiting_minutes ? `${reviewCase.waiting_minutes} min waiting` : "Booked patient"}</span>
            <StatusBadge state={reviewCase.service_target} />
          </div>
          <ChevronRight aria-hidden="true" className={styles.caseArrow} size={20} />
        </button>
      ))}
    </section>
  );
}
