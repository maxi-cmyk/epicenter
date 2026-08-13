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
    { id: "Q-014", patient_id: "P-0417", patient_name: "Loh Wei Ming", intake_type: "booked", visit_phase: "incoming", readiness_state: "ready", readiness_reason: "all_prerequisites_passed", scheduled_at: "2026-08-12T10:00:00Z", original_ordering_at: "2026-08-12T10:00:00Z", waiting_minutes: 0, processing_stage: "Ready before arrival", service_target: "on_track", staff_confirmed: true, clinical_escalation: false, version: 1, matched_package: "WELL2 — Comprehensive Screen", package_confirmed: false, billing_code: "WELL2-STD", uncovered_cost: 0, queue_number: "Q014", billing_confirmed: false, identity_confirmed: false, ecard_verified: false, ecard_not_applicable: false, forms_confirmed: false, physical_forms_received: false, is_checkup: true, documents: [], record_checklist: { patient: { full_name: "Loh Wei Ming", identifier_masked: "S***946C", date_of_birth: "1988-03-15", contact_mobile: "9**1 234", address: "12 Function Place" }, items: [
      { label: "Patient details", status: "pass", detail: "S***946C" },
      { label: "Coverage document", status: "pass", detail: "Meridian (MRDEB) · voucher" },
      { label: "Eligibility match", status: "pass", detail: "WELL2 — Comprehensive Screen" },
      { label: "General health questionnaire", status: "pass", detail: "Verified" },
      { label: "Occupational health questionnaire", status: "not_required", detail: null },
    ] } },
    { id: "Q-015", patient_id: "P-0398", patient_name: "Tan Kai Xuan", intake_type: "booked", visit_phase: "incoming", readiness_state: "needs_review", readiness_reason: "missing_document", scheduled_at: "2026-08-12T10:15:00Z", original_ordering_at: "2026-08-12T10:15:00Z", waiting_minutes: 0, processing_stage: "Awaiting coverage document", service_target: "approaching", staff_confirmed: false, clinical_escalation: false, version: 1, package_confirmed: false, billing_confirmed: false, identity_confirmed: false, ecard_verified: false, ecard_not_applicable: false, forms_confirmed: false, physical_forms_received: false, is_checkup: false, documents: [], record_checklist: { patient: { full_name: "Tan Kai Xuan", identifier_masked: "S***398D", date_of_birth: "1991-07-02", contact_mobile: "8**4 552", address: "88 Harbour Rise" }, items: [
      { label: "Patient details", status: "pass", detail: "S***398D" },
      { label: "Coverage document", status: "fail", detail: "No coverage document received" },
      { label: "Eligibility match", status: "fail", detail: null },
      { label: "General health questionnaire", status: "pending", detail: "Not yet submitted" },
      { label: "Occupational health questionnaire", status: "not_required", detail: null },
    ] } },
    { id: "Q-017", patient_id: "P-0442", patient_name: "Mei Chen", intake_type: "walk_in", visit_phase: "ongoing", readiness_state: "processing", readiness_reason: "processing", checked_in_at: "2026-08-12T09:34:00Z", original_ordering_at: "2026-08-12T09:34:00Z", waiting_minutes: 8, actual_room: "1", processing_stage: "Document extraction", service_target: "on_track", staff_confirmed: false, clinical_escalation: false, version: 1, package_confirmed: false, billing_confirmed: false, identity_confirmed: false, ecard_verified: false, ecard_not_applicable: false, forms_confirmed: false, physical_forms_received: false, is_checkup: false, documents: [], record_checklist: { patient: { full_name: "Mei Chen", identifier_masked: "S***442F", date_of_birth: "1995-11-20", contact_mobile: "9**7 108", address: "4 Riverwalk Avenue" }, items: [
      { label: "Patient details", status: "pass", detail: "S***442F" },
      { label: "Coverage document", status: "pending", detail: "Extraction in progress" },
      { label: "Eligibility match", status: "pending", detail: null },
      { label: "General health questionnaire", status: "not_required", detail: null },
      { label: "Occupational health questionnaire", status: "not_required", detail: null },
    ] } },
    { id: "Q-018", patient_id: "P-0451", patient_name: "Amir Loh", intake_type: "walk_in", visit_phase: "ongoing", readiness_state: "needs_review", readiness_reason: "expired_document", checked_in_at: "2026-08-12T09:24:00Z", original_ordering_at: "2026-08-12T09:24:00Z", waiting_minutes: 18, actual_room: "2", processing_stage: "Voucher review", service_target: "approaching", staff_confirmed: false, clinical_escalation: false, version: 1, matched_package: "Executive screening", package_confirmed: false, billing_code: "EXEC-STD", uncovered_cost: 45, queue_number: "Q018", billing_confirmed: false, identity_confirmed: false, ecard_verified: false, ecard_not_applicable: false, forms_confirmed: false, physical_forms_received: false, is_checkup: false, documents: [], record_checklist: { patient: { full_name: "Amir Loh", identifier_masked: "S***451A", date_of_birth: "1983-01-09", contact_mobile: "9**3 671", address: "21 Bluepeak Lane" }, items: [
      { label: "Patient details", status: "pass", detail: "S***451A" },
      { label: "Coverage document", status: "fail", detail: "Bluepeak (BLPHS) · voucher — expired 10 Aug 2026" },
      { label: "Eligibility match", status: "pending", detail: "Executive screening" },
      { label: "General health questionnaire", status: "pass", detail: "Verified" },
      { label: "Occupational health questionnaire", status: "not_required", detail: null },
    ] } },
    { id: "Q-019", patient_id: "P-0458", patient_name: "Priya Nair", intake_type: "walk_in", visit_phase: "ongoing", readiness_state: "ready", readiness_reason: "all_prerequisites_passed", checked_in_at: "2026-08-12T09:37:00Z", original_ordering_at: "2026-08-12T09:37:00Z", waiting_minutes: 5, actual_room: "3", processing_stage: "Waiting to be called", service_target: "on_track", staff_confirmed: true, clinical_escalation: false, version: 1, matched_package: "PEE226 — Basic Screen", package_confirmed: false, billing_code: "PEE226-CHAS", uncovered_cost: 8.5, queue_number: "Q019", billing_confirmed: false, identity_confirmed: false, ecard_verified: false, ecard_not_applicable: false, forms_confirmed: false, physical_forms_received: false, is_checkup: false, documents: [], record_checklist: { patient: { full_name: "Priya Nair", identifier_masked: "S***458G", date_of_birth: "1990-05-30", contact_mobile: "8**9 214", address: "17 Coral Drive" }, items: [
      { label: "Patient details", status: "pass", detail: "S***458G" },
      { label: "Coverage document", status: "pass", detail: "CHAS · referral letter" },
      { label: "Eligibility match", status: "pass", detail: "PEE226 — Basic Screen" },
      { label: "General health questionnaire", status: "pass", detail: "Verified" },
      { label: "Occupational health questionnaire", status: "not_required", detail: null },
    ] } },
    { id: "Q-020", patient_id: "P-0463", patient_name: "Marcus Lim", intake_type: "walk_in", visit_phase: "ongoing", readiness_state: "ready", readiness_reason: "all_prerequisites_passed", checked_in_at: "2026-08-12T09:20:00Z", original_ordering_at: "2026-08-12T09:20:00Z", waiting_minutes: 22, actual_room: "Room 2 · Dr Farah", processing_stage: "Consultation in progress", service_target: "on_track", staff_confirmed: true, clinical_escalation: false, version: 1, matched_package: "TPA-GP01 — GP Consultation", package_confirmed: false, billing_code: "TPA-GP01", uncovered_cost: 0, queue_number: "Q020", billing_confirmed: false, identity_confirmed: false, ecard_verified: false, ecard_not_applicable: false, forms_confirmed: false, physical_forms_received: false, is_checkup: false, record_checklist: { patient: { full_name: "Marcus Lim", identifier_masked: "S***463B", date_of_birth: "1985-04-02", contact_mobile: "9**2 640", address: "30 Northshore Drive" }, items: [
      { label: "Patient details", status: "pass", detail: "S***463B" },
      { label: "Coverage document", status: "pass", detail: "Meridian TPA (MRD-TPA) · membership card" },
      { label: "Eligibility match", status: "pass", detail: "TPA-GP01 — GP Consultation" },
      { label: "General health questionnaire", status: "pass", detail: "Verified" },
      { label: "Occupational health questionnaire", status: "not_required", detail: null },
    ] }, documents: [
      { id: "TPADOC-Q020-BEN", category: "benefit_structure", issuer_code: "MRD-TPA", issuer_name: "Meridian TPA", document_type: "Benefit Schedule 2026", reference_number: "BEN-2026-0417", valid_from: "2026-01-01", valid_to: "2026-12-31", facts: { membership_number: "MTP-88213045", plan_tier: "Standard", annual_limit: "2000.00", copay_percentage: "10" }, confirmed: false, version: 1 },
      { id: "TPADOC-Q020-AUTH", category: "authorisation_letter", issuer_code: "MRD-TPA", issuer_name: "Meridian TPA", document_type: "Pre-authorisation letter", reference_number: "AUTH-88213-GP01", valid_from: "2026-08-01", valid_to: "2026-08-31", facts: { authorising_officer: "Grace Lim", approval_number: "AUTH-88213-GP01", scope: "GP Consultation" }, confirmed: false, version: 1 },
      { id: "TPADOC-Q020-CODE", category: "coding_scheme", issuer_code: "MRD-TPA", issuer_name: "Meridian TPA", document_type: "Procedure code reference", reference_number: "TPA-GP01", facts: { procedure_code: "TPA-GP01", code_scheme: "Meridian TPA coding table v3", package_name: "GP Consultation" }, confirmed: false, version: 1 },
      { id: "TPADOC-Q020-FORM", category: "form", issuer_code: "NORTHSHORE-LOGISTICS", issuer_name: "Northshore Logistics", document_type: "Employer claim form", reference_number: "CLAIM-0463", facts: { employer_code: "NORTHSHORE-LOGISTICS", billing_arrangement: "Direct billing to employer" }, confirmed: false, version: 1 },
    ] },
    { id: "Q-011", patient_id: "P-0371", patient_name: "Siti Rahman", intake_type: "booked", visit_phase: "finished", readiness_state: "ready", readiness_reason: "completed", scheduled_at: "2026-08-12T08:30:00Z", checked_in_at: "2026-08-12T08:22:00Z", original_ordering_at: "2026-08-12T08:30:00Z", waiting_minutes: 0, processing_stage: "Completed 09:08", service_target: "on_track", staff_confirmed: true, clinical_escalation: false, version: 1, matched_package: "WELL2 — Comprehensive Screen", package_confirmed: true, package_confirmed_by: "Nurse Aisyah", package_confirmed_at: "2026-08-12T08:25:00Z", billing_code: "WELL2-STD", uncovered_cost: 0, queue_number: "Q011", billing_confirmed: true, billing_confirmed_by: "Nurse Aisyah", billing_confirmed_at: "2026-08-12T08:26:00Z", identity_confirmed: true, identity_confirmed_by: "Nurse Aisyah", ecard_verified: true, ecard_not_applicable: false, forms_confirmed: true, forms_confirmed_by: "Nurse Aisyah", physical_forms_received: true, physical_forms_received_by: "Nurse Aisyah", is_checkup: false, documents: [], record_checklist: { patient: { full_name: "Siti Rahman", identifier_masked: "S***371K", date_of_birth: "1979-09-14", contact_mobile: "9**5 830", address: "6 Meridian Court" }, items: [
      { label: "Patient details", status: "pass", detail: "S***371K" },
      { label: "Coverage document", status: "pass", detail: "Meridian (MRDEB) · voucher" },
      { label: "Eligibility match", status: "pass", detail: "WELL2 — Comprehensive Screen" },
      { label: "General health questionnaire", status: "pass", detail: "Verified" },
      { label: "Occupational health questionnaire", status: "not_required", detail: null },
    ] } },
  ],
  review_cases: [
    { id: "R-015", ticket_id: "Q-015", patient_name: "Tan Kai Xuan", reason_code: "missing_document", reason_label: "Coverage document missing", evidence_summary: "Reminder sent 08:16 · no upload received", waiting_minutes: 0, service_target: "approaching", next_action: "Contact patient" },
    { id: "R-018", ticket_id: "Q-018", patient_name: "Amir Loh", reason_code: "expired_document", reason_label: "Voucher validity expired", document_name: "Bluepeak_voucher.pdf", evidence_summary: "Valid until 10 Aug 2026 · source page 1", waiting_minutes: 18, service_target: "approaching", next_action: "Confirm replacement or self-pay" },
  ],
  recommendation: { id: "A-009", status: "pending", pressured_workstream: "Assisted review", rationale: "Two review cases are approaching the 20-minute service target while Counter 4 has been idle for 7 minutes.", qualified_resource: "Counter 4 · Nur Aisyah", current_wait_minutes: 18, expected_wait_minutes: 9, expires_at: "2026-08-12T09:48:00Z", constraints_checked: ["Registration-trained", "Minimum ready coverage retained", "Break window clear", "No reassignment in last 30 min"], version: 1 },
  activity: [
    { id: "E-1", occurred_at: "2026-08-12T09:41:00Z", label: "Q-019 became ready", detail: "Staff confirmed the rules-matched package; original ticket retained.", tone: "success" },
    { id: "E-2", occurred_at: "2026-08-12T09:38:00Z", label: "Q-017 document received", detail: "Walk-in intake captured at nurse-supervised Kiosk A.", tone: "neutral" },
    { id: "E-3", occurred_at: "2026-08-12T09:35:00Z", label: "Allocation advice created", detail: "Recommendation A-009 expires at 09:48 and requires approval.", tone: "attention" },
  ],
};
