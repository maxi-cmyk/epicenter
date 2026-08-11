"use client";

import { Check, ShieldCheck, X } from "lucide-react";
import { useState } from "react";

import { decideRecommendation } from "@/lib/api";
import type { AllocationRecommendation } from "@/lib/types";
import { Button } from "@/components/shared/Button";
import { StatusBadge } from "@/components/shared/StatusBadge";

import styles from "./Dashboard.module.css";

export function AllocationDecision({ initialRecommendation }: { initialRecommendation: AllocationRecommendation }) {
  const [recommendation, setRecommendation] = useState(initialRecommendation);
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);

  async function decide(decision: "approved" | "rejected") {
    setPending(true);
    setMessage("");
    try {
      const result = await decideRecommendation(recommendation.id, decision);
      setRecommendation(result.recommendation ?? { ...recommendation, status: decision });
      setMessage(result.message);
    } catch {
      setRecommendation((current) => ({ ...current, status: decision }));
      setMessage(`Demo fallback: recommendation ${decision}; no change was applied silently.`);
    } finally {
      setPending(false);
    }
  }

  return (
    <section
      aria-labelledby="allocation-title"
      className={`${styles.allocationPanel} ${styles[`allocation_${recommendation.status}`]}`}
      id="allocation-decision"
    >
      <div className={styles.allocationHeading}>
        <div>
          <h2 id="allocation-title">One decision needs attention</h2>
          <p>{recommendation.pressured_workstream}</p>
        </div>
        <StatusBadge state={recommendation.status} />
      </div>
      <p className={styles.rationale}>{recommendation.rationale}</p>
      <div className={styles.waitComparison}>
        <div><span>Without change</span><strong>{recommendation.current_wait_minutes} min</strong></div>
        <span aria-hidden="true" className={styles.routeTrace}><i /></span>
        <div><span>Estimated after approval</span><strong>{recommendation.expected_wait_minutes} min</strong></div>
      </div>
      <div className={styles.resourceLine}>
        <ShieldCheck aria-hidden="true" size={20} />
        <span><strong>{recommendation.qualified_resource}</strong> is qualified and available</span>
      </div>
      <ul className={styles.constraintList}>
        {recommendation.constraints_checked.map((constraint) => <li key={constraint}><Check aria-hidden="true" size={14} />{constraint}</li>)}
      </ul>
      {recommendation.status === "pending" ? (
        <div className={styles.decisionActions}>
          <Button disabled={pending} icon={<Check aria-hidden="true" size={17} />} onClick={() => void decide("approved")}>Approve move</Button>
          <Button disabled={pending} icon={<X aria-hidden="true" size={17} />} onClick={() => void decide("rejected")} variant="quiet">Keep current plan</Button>
        </div>
      ) : null}
      {message ? <p aria-live="polite" className={styles.decisionMessage}>{message}</p> : null}
    </section>
  );
}
