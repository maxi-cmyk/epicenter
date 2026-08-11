import type { DashboardSnapshot } from "@epicenter/shared/contracts";

export const demoSnapshot: DashboardSnapshot = {
  generated_at: "2026-08-12T09:42:00Z",
  clinic_name: "Parkway Shenton · HarbourFront",
  synthetic: true,
  metrics: [
    { label: "Ready before arrival", value: "78%", detail: "18 of 23 booked patients", trend: "+9% vs baseline" },
    { label: "Oldest review", value: "18 min", detail: "Q-018 · expired voucher", trend: "Approaching target" },
    { label: "Median admin wait", value: "6 min", detail: "P90 14 minutes", trend: "−4 min vs baseline" },
    { label: "Staff confirmations", value: "31", detail: "Estimated 30 sec each", trend: "100% human confirmed" },
  ],
  tickets: [
    { id: "Q-014", patient_id: "P-0417", patient_name: "Loh Wei Ming", intake_type: "booked", visit_phase: "incoming", readiness_state: "ready", readiness_reason: "all_prerequisites_passed", scheduled_at: "2026-08-12T10:00:00Z", original_ordering_at: "2026-08-12T10:00:00Z", waiting_minutes: 0, expected_counter: "Counter 2", processing_stage: "Ready before arrival", service_target: "on_track", staff_confirmed: true, clinical_escalation: false },
    { id: "Q-015", patient_id: "P-0398", patient_name: "Tan Kai Xuan", intake_type: "booked", visit_phase: "incoming", readiness_state: "needs_review", readiness_reason: "missing_document", scheduled_at: "2026-08-12T10:15:00Z", original_ordering_at: "2026-08-12T10:15:00Z", waiting_minutes: 0, expected_counter: "Review 1", processing_stage: "Awaiting coverage document", service_target: "approaching", staff_confirmed: false, clinical_escalation: false },
    { id: "Q-017", patient_id: "P-0442", patient_name: "Mei Chen", intake_type: "walk_in", visit_phase: "ongoing", readiness_state: "processing", readiness_reason: "processing", checked_in_at: "2026-08-12T09:34:00Z", original_ordering_at: "2026-08-12T09:34:00Z", waiting_minutes: 8, actual_counter: "Kiosk A", processing_stage: "Document extraction", service_target: "on_track", staff_confirmed: false, clinical_escalation: false },
    { id: "Q-018", patient_id: "P-0451", patient_name: "Amir Loh", intake_type: "walk_in", visit_phase: "ongoing", readiness_state: "needs_review", readiness_reason: "expired_document", checked_in_at: "2026-08-12T09:24:00Z", original_ordering_at: "2026-08-12T09:24:00Z", waiting_minutes: 18, actual_counter: "Review 2", processing_stage: "Voucher review", service_target: "approaching", staff_confirmed: false, clinical_escalation: false },
    { id: "Q-019", patient_id: "P-0458", patient_name: "Priya Nair", intake_type: "walk_in", visit_phase: "ongoing", readiness_state: "ready", readiness_reason: "all_prerequisites_passed", checked_in_at: "2026-08-12T09:37:00Z", original_ordering_at: "2026-08-12T09:37:00Z", waiting_minutes: 5, actual_counter: "Counter 3", processing_stage: "Waiting to be called", service_target: "on_track", staff_confirmed: true, clinical_escalation: false },
    { id: "Q-011", patient_id: "P-0371", patient_name: "Siti Rahman", intake_type: "booked", visit_phase: "finished", readiness_state: "ready", readiness_reason: "completed", scheduled_at: "2026-08-12T08:30:00Z", checked_in_at: "2026-08-12T08:22:00Z", original_ordering_at: "2026-08-12T08:30:00Z", waiting_minutes: 0, actual_counter: "Counter 1", processing_stage: "Completed 09:08", service_target: "on_track", staff_confirmed: true, clinical_escalation: false },
  ],
  review_cases: [
    { id: "R-015", ticket_id: "Q-015", patient_name: "Tan Kai Xuan", reason_code: "missing_document", reason_label: "Coverage document missing", evidence_summary: "Reminder sent 08:16 · no upload received", waiting_minutes: 0, service_target: "approaching", next_action: "Contact patient" },
    { id: "R-018", ticket_id: "Q-018", patient_name: "Amir Loh", reason_code: "expired_document", reason_label: "Voucher validity expired", document_name: "Bluepeak_voucher.pdf", evidence_summary: "Valid until 10 Aug 2026 · source page 1", waiting_minutes: 18, service_target: "approaching", next_action: "Confirm replacement or self-pay" },
  ],
  recommendation: { id: "A-009", status: "pending", pressured_workstream: "Assisted review", rationale: "Two review cases are approaching the 20-minute service target while Counter 4 has been idle for 7 minutes.", qualified_resource: "Counter 4 · Nur Aisyah", current_wait_minutes: 18, expected_wait_minutes: 9, expires_at: "2026-08-12T09:48:00Z", constraints_checked: ["Registration-trained", "Minimum ready coverage retained", "Break window clear", "No reassignment in last 30 min"] },
  activity: [
    { id: "E-1", occurred_at: "2026-08-12T09:41:00Z", label: "Q-019 became ready", detail: "Staff confirmed the rules-matched package; original ticket retained.", tone: "success" },
    { id: "E-2", occurred_at: "2026-08-12T09:38:00Z", label: "Q-017 document received", detail: "Walk-in intake captured at nurse-supervised Kiosk A.", tone: "neutral" },
    { id: "E-3", occurred_at: "2026-08-12T09:35:00Z", label: "Allocation advice created", detail: "Recommendation A-009 expires at 09:48 and requires approval.", tone: "attention" },
  ],
};
