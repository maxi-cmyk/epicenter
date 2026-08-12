"use client";

import { X } from "lucide-react";
import { useEffect } from "react";

import type { ReviewCase } from "@epicenter/shared/contracts";

import { EvidencePanel } from "../review/EvidencePanel";
import styles from "./Dashboard.module.css";

export function TicketReviewModal({
  onClose,
  onConfirm,
  reviewCase,
}: {
  onClose: () => void;
  onConfirm: () => void;
  reviewCase: ReviewCase;
}) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  return (
    <div aria-modal="true" className={styles.modalOverlay} onClick={onClose} role="dialog">
      <div className={styles.modalDialog} onClick={(event) => event.stopPropagation()}>
        <button aria-label="Close" className={styles.modalClose} onClick={onClose} type="button">
          <X aria-hidden="true" size={18} />
        </button>
        <EvidencePanel onConfirm={onConfirm} reviewCase={reviewCase} />
      </div>
    </div>
  );
}
