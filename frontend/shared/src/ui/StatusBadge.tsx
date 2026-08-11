import { CircleCheck, CircleDashed, TriangleAlert } from "lucide-react";

import type { ReadinessState, ServiceTarget } from "@epicenter/shared/contracts";

import styles from "./Shared.module.css";

interface StatusBadgeProps {
  state: ReadinessState | ServiceTarget | string;
  label?: string;
}

const labels: Record<string, string> = {
  ready: "Ready",
  processing: "Processing",
  needs_review: "Needs review",
  on_track: "On track",
  approaching: "Approaching target",
  over_target: "Over target",
  approved: "Approved",
  rejected: "Rejected",
  pending: "Decision needed",
};

export function StatusBadge({ state, label }: StatusBadgeProps) {
  const Icon = state === "ready" || state === "approved" ? CircleCheck : state === "processing" ? CircleDashed : TriangleAlert;
  return (
    <span className={`${styles.badge} ${styles[`badge_${state}`] ?? styles.badge_neutral}`}>
      <Icon aria-hidden="true" size={14} strokeWidth={2.2} />
      {label ?? labels[state] ?? state.replaceAll("_", " ")}
    </span>
  );
}
