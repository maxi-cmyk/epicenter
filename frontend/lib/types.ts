export type ReadinessState = "processing" | "ready" | "needs_review";
export type VisitPhase = "incoming" | "ongoing" | "finished";
export type IntakeType = "booked" | "walk_in";
export type ServiceTarget = "on_track" | "approaching" | "over_target";

export interface Metric {
  label: string;
  value: string;
  detail: string;
  trend?: string;
}

export interface QueueTicket {
  id: string;
  patient_id: string;
  patient_name: string;
  intake_type: IntakeType;
  visit_phase: VisitPhase;
  readiness_state: ReadinessState;
  readiness_reason: string;
  scheduled_at?: string | null;
  checked_in_at?: string | null;
  original_ordering_at: string;
  waiting_minutes: number;
  expected_counter?: string | null;
  actual_counter?: string | null;
  processing_stage: string;
  service_target: ServiceTarget;
  staff_confirmed: boolean;
  clinical_escalation: boolean;
}

export interface ReviewCase {
  id: string;
  ticket_id: string;
  patient_name: string;
  reason_code: string;
  reason_label: string;
  document_name?: string | null;
  evidence_summary: string;
  waiting_minutes: number;
  service_target: ServiceTarget;
  next_action: string;
}

export interface AllocationRecommendation {
  id: string;
  status: string;
  pressured_workstream: string;
  rationale: string;
  qualified_resource: string;
  current_wait_minutes: number;
  expected_wait_minutes: number;
  expires_at: string;
  constraints_checked: string[];
}

export interface ActivityEvent {
  id: string;
  occurred_at: string;
  label: string;
  detail: string;
  tone: string;
}

export interface DashboardSnapshot {
  generated_at: string;
  clinic_name: string;
  synthetic: boolean;
  metrics: Metric[];
  tickets: QueueTicket[];
  review_cases: ReviewCase[];
  recommendation: AllocationRecommendation;
  activity: ActivityEvent[];
}

export interface ActionResult {
  success: boolean;
  message: string;
  ticket?: QueueTicket;
  recommendation?: AllocationRecommendation;
}
