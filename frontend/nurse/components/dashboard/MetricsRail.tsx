import { ArrowDownRight } from "lucide-react";

import type { AllocationRecommendation, Metric } from "@epicenter/shared/contracts";

import styles from "./Dashboard.module.css";

export function MetricsRail({ metrics, recommendation }: { metrics: Metric[]; recommendation: AllocationRecommendation }) {
  return (
    <section aria-label="Clinic metrics" className={styles.metricsRail}>
      {metrics.map((metric) => (
        <div className={styles.metric} key={metric.label}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          <small>{metric.detail}</small>
          {metric.trend ? <em>{metric.trend}</em> : null}
        </div>
      ))}
      <a className={styles.decisionMetric} href="#allocation-decision">
        <span>Decision needed</span>
        <strong>{recommendation.current_wait_minutes} → {recommendation.expected_wait_minutes}</strong>
        <small>Move {recommendation.qualified_resource.split(" · ")[0]} to assisted review</small>
        <em>Review recommendation <ArrowDownRight aria-hidden="true" size={15} /></em>
      </a>
    </section>
  );
}
