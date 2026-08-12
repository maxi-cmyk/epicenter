-- Deterministic synthetic operational state for the local nurse workflow.
begin;

insert into public.clinics (id, name)
values ('clinic_harbourfront', 'Parkway Shenton · HarbourFront')
on conflict (id) do update set name = excluded.name;

insert into public.staff_accounts (id, clinic_id, full_name, email, role)
values
  ('staff_noor', 'clinic_harbourfront', 'Nurse Noor', 'nurse.noor@example.test', 'registration'),
  ('staff_aisyah', 'clinic_harbourfront', 'Nur Aisyah', 'nur.aisyah@example.test', 'operations_admin')
on conflict (id) do update set
  clinic_id = excluded.clinic_id,
  full_name = excluded.full_name,
  email = excluded.email,
  role = excluded.role,
  active = true,
  deleted_at = null;

insert into public.appointments (
  id, appointment_reference, clinic_id, patient_id, scheduled_at,
  appointment_type, questionnaire_type, administrative_urgency, status
)
values
  (
    'appointment_014', 'APT-DEMO-014', 'clinic_harbourfront',
    (select id from public.patients where identifier_hash = '4e487c99807bebe1c81bf3cded10ceb92f1c8d3ed0d48cbe822ad578a45854b5'),
    '2026-08-12 10:00:00+00', 'insurance_medical', 'general_health', false, 'booked'
  ),
  (
    'appointment_015', 'APT-DEMO-015', 'clinic_harbourfront',
    (select id from public.patients where source_record_key = 'registration:0001'),
    '2026-08-12 10:15:00+00', 'health_screening', 'general_health', true, 'booked'
  ),
  (
    'appointment_011', 'APT-DEMO-011', 'clinic_harbourfront', null,
    '2026-08-12 08:30:00+00', 'health_screening', 'occupational_health', false, 'completed'
  )
on conflict (id) do update set
  appointment_reference = excluded.appointment_reference,
  clinic_id = excluded.clinic_id,
  patient_id = excluded.patient_id,
  scheduled_at = excluded.scheduled_at,
  appointment_type = excluded.appointment_type,
  questionnaire_type = excluded.questionnaire_type,
  administrative_urgency = excluded.administrative_urgency,
  status = excluded.status,
  deleted_at = null;

insert into public.queue_entries (
  id, clinic_id, patient_id, patient_reference, patient_name_snapshot,
  appointment_id, appointment_reference, intake_type, visit_status,
  prereg_completed_at, all_required_documents_present, all_documents_valid,
  extraction_status, match_status, readiness_state, readiness_reason,
  scheduled_at, checked_in_at, original_ordering_at, waiting_minutes, expected_queue_number,
  expected_counter_number, queue_number, counter_number, processing_stage,
  service_target, staff_confirmed, clinical_escalation, ready_at, completed_at,
  patient_outcome, patient_reason_code, patient_next_action, assigned_at
)
values
  (
    'Q-014', 'clinic_harbourfront',
    (select id from public.patients where identifier_hash = '4e487c99807bebe1c81bf3cded10ceb92f1c8d3ed0d48cbe822ad578a45854b5'),
    'P-0417', 'Loh Wei Ming', 'appointment_014', 'APT-DEMO-014', 'booked', 'incoming',
    '2026-08-11 08:00:00+00', true, true, 'pass', 'clean', 'ready',
    'all_prerequisites_passed', '2026-08-12 10:00:00+00', null,
    '2026-08-12 10:00:00+00', 0, 'Q-014', 'Counter 2', null, null,
    'Ready before arrival', 'on_track', true, false, '2026-08-12 09:10:00+00', null,
    'accepted', 'administrative_checks_complete', 'Keep your queue ticket for arrival.', '2026-08-12 09:10:00+00'
  ),
  (
    'Q-015', 'clinic_harbourfront',
    (select id from public.patients where source_record_key = 'registration:0001'),
    'P-0398', 'Tan Kai Xuan', 'appointment_015', 'APT-DEMO-015', 'booked', 'incoming',
    '2026-08-11 08:05:00+00', false, false, 'needs_review', 'no_match', 'needs_review',
    'missing_document', '2026-08-12 10:15:00+00', null,
    '2026-08-12 10:15:00+00', 0, 'Q-015', 'Review 1', null, null,
    'Awaiting coverage document', 'approaching', false, false, null, null,
    'under_review', 'coverage_document_required', 'Upload a current coverage document.', null
  ),
  (
    'Q-017', 'clinic_harbourfront', null, 'P-0442', 'Mei Chen', null, null,
    'walk_in', 'ongoing', null, true, true, 'needs_review', 'no_match', 'processing',
    'processing', null, '2026-08-12 09:34:00+00', '2026-08-12 09:34:00+00',
    8, null, null, 'Q-017', 'Kiosk A', 'Document extraction', 'on_track', false, false, null, null,
    'under_review', 'clinic_review_required', 'Continue with the nurse-supervised check-in.', '2026-08-12 09:34:00+00'
  ),
  (
    'Q-018', 'clinic_harbourfront',
    (select id from public.patients where source_record_key = 'registration:0002'),
    'P-0451', 'Amir Loh', null, null, 'walk_in', 'ongoing', null, true, false,
    'needs_review', 'no_match', 'needs_review', 'expired_document', null,
    '2026-08-12 09:24:00+00', '2026-08-12 09:24:00+00', 18, null, null, 'Q-018',
    'Review 2', 'Voucher review', 'approaching', false, false, null, null,
    'under_review', 'coverage_document_expired', 'Clinic staff are reviewing your coverage.', '2026-08-12 09:24:00+00'
  ),
  (
    'Q-019', 'clinic_harbourfront', null, 'P-0458', 'Priya Nair', null, null,
    'walk_in', 'ongoing', null, true, true, 'pass', 'clean', 'ready',
    'all_prerequisites_passed', null, '2026-08-12 09:37:00+00',
    '2026-08-12 09:37:00+00', 5, null, null, 'Q-019', 'Counter 3',
    'Waiting to be called', 'on_track', true, false, '2026-08-12 09:39:00+00', null,
    'accepted', 'administrative_checks_complete', 'Wait for your counter to be called.', '2026-08-12 09:39:00+00'
  ),
  (
    'Q-011', 'clinic_harbourfront', null, 'P-0371', 'Siti Rahman', 'appointment_011',
    'APT-DEMO-011', 'booked', 'finished', '2026-08-10 08:00:00+00', true, true,
    'pass', 'clean', 'ready', 'completed', '2026-08-12 08:30:00+00',
    '2026-08-12 08:22:00+00', '2026-08-12 08:30:00+00', 0, 'Q-011', 'Counter 1',
    'Q-011', 'Counter 1', 'Completed 09:08', 'on_track', true, false,
    '2026-08-12 08:25:00+00', '2026-08-12 09:08:00+00',
    'accepted', 'visit_completed', 'No further action is needed.', '2026-08-12 08:25:00+00'
  )
on conflict (id) do update set
  clinic_id = excluded.clinic_id,
  patient_id = excluded.patient_id,
  patient_reference = excluded.patient_reference,
  patient_name_snapshot = excluded.patient_name_snapshot,
  appointment_id = excluded.appointment_id,
  appointment_reference = excluded.appointment_reference,
  intake_type = excluded.intake_type,
  visit_status = excluded.visit_status,
  prereg_completed_at = excluded.prereg_completed_at,
  all_required_documents_present = excluded.all_required_documents_present,
  all_documents_valid = excluded.all_documents_valid,
  extraction_status = excluded.extraction_status,
  match_status = excluded.match_status,
  readiness_state = excluded.readiness_state,
  readiness_reason = excluded.readiness_reason,
  scheduled_at = excluded.scheduled_at,
  checked_in_at = excluded.checked_in_at,
  original_ordering_at = excluded.original_ordering_at,
  waiting_minutes = excluded.waiting_minutes,
  expected_queue_number = excluded.expected_queue_number,
  expected_counter_number = excluded.expected_counter_number,
  queue_number = excluded.queue_number,
  counter_number = excluded.counter_number,
  processing_stage = excluded.processing_stage,
  service_target = excluded.service_target,
  staff_confirmed = excluded.staff_confirmed,
  clinical_escalation = excluded.clinical_escalation,
  ready_at = excluded.ready_at,
  completed_at = excluded.completed_at,
  patient_outcome = excluded.patient_outcome,
  patient_reason_code = excluded.patient_reason_code,
  patient_next_action = excluded.patient_next_action,
  assigned_at = excluded.assigned_at,
  deleted_at = null;

insert into public.registration_validations (
  id, clinic_id, appointment_id, patient_id, field_results, outcome,
  patient_reason_code, patient_next_action, actor_reference
)
select
  'VAL-015', appointment.clinic_id, appointment.id, appointment.patient_id,
  '{"identifier":"source_validated","full_name":"conflict","date_of_birth":"source_validated","email":"conflict"}',
  'rejected', 'registration_details_mismatch',
  'Review your booking details or ask clinic staff for help.', 'synthetic-seed'
from public.appointments appointment where appointment.id = 'appointment_015'
on conflict (id) do update set
  field_results = excluded.field_results,
  outcome = excluded.outcome,
  patient_reason_code = excluded.patient_reason_code,
  patient_next_action = excluded.patient_next_action,
  deleted_at = null;

insert into public.review_cases (
  id, queue_entry_id, reason_code, reason_label, document_name,
  evidence_summary, next_action
)
values
  ('R-015', 'Q-015', 'missing_document', 'Coverage document missing', null,
    'Reminder sent 08:16 · no upload received', 'Contact patient'),
  ('R-018', 'Q-018', 'expired_document', 'Voucher validity expired', 'Bluepeak_voucher.pdf',
    'Valid until 10 Aug 2026 · source page 1', 'Confirm replacement or self-pay')
on conflict (id) do update set
  queue_entry_id = excluded.queue_entry_id,
  reason_code = excluded.reason_code,
  reason_label = excluded.reason_label,
  document_name = excluded.document_name,
  evidence_summary = excluded.evidence_summary,
  next_action = excluded.next_action,
  resolved_at = null;

insert into public.data_import_exceptions (
  source_record_key, source_record_type, normalized_identifier_hash,
  reason_code, details, resolution_status
)
select
  submission.source_record_key,
  submission.questionnaire_type,
  submission.subject_identifier_hash,
  'unmatched_patient',
  jsonb_build_object(
    'subject_identifier_masked', submission.subject_identifier_masked,
    'subject_name', submission.subject_name
  ),
  'unresolved'
from public.questionnaire_submissions submission
where submission.verification_status = 'no_registration'
on conflict (source_record_key) do update set
  normalized_identifier_hash = excluded.normalized_identifier_hash,
  reason_code = excluded.reason_code,
  details = excluded.details,
  resolution_status = excluded.resolution_status;

insert into public.coverage_documents (
  id, clinic_id, patient_id, appointment_id, source_fixture_id, file_reference,
  document_type, issuer_code, issuer_name, issued_on, validity_end,
  extracted_identifier_hash, extracted_identifier_masked, patient_match_status,
  extracted_facts, field_evidence, extraction_confidence, readiness_status,
  readiness_reasons, processing_status, review_status,
  confirmed_by_reference, confirmed_at
)
values
  (
    'DOC-014', 'clinic_harbourfront',
    (select patient_id from public.appointments where id = 'appointment_014'),
    'appointment_014',
    (select id from public.medical_document_samples where source_record_key = 'medical_chit:01_mrdeb_referral'),
    'synthetic://medical_chit/01_mrdeb_referral', 'medical_referral_letter',
    'MRDEB', 'Meridian Life Assurance Pte Ltd', '2026-08-04', '2026-09-30',
    '4e487c99807bebe1c81bf3cded10ceb92f1c8d3ed0d48cbe822ad578a45854b5',
    '*****946C', 'exact_identifier',
    '{"policy_number":"MRD707314","requirements":["Chest X-Ray","HIV Antibody Test","Treadmill ECG"]}',
    '{"policy_number":{"page":1,"excerpt":"Policy No. MRD707314"}}',
    '{"policy_number":0.99}', 'pass', '[]', 'ready', 'confirmed',
    'synthetic-seed', '2026-08-12 09:10:00+00'
  ),
  (
    'DOC-018', 'clinic_harbourfront',
    (select id from public.patients where source_record_key = 'registration:0002'),
    null,
    (select id from public.medical_document_samples where source_record_key = 'medical_chit:05_blphs_wellness'),
    'synthetic://medical_chit/05_blphs_wellness', 'wellness_package_voucher',
    'BLPHS', 'Bluepeak Prosperity Life', null, '2026-08-10', null, null,
    'needs_review', '{"package_code":"WELL2"}',
    '{"validity_end":{"page":1,"excerpt":"Valid until 10 Aug 2026"}}',
    '{"validity_end":0.98}', 'needs_review', '["expired_document"]',
    'ready', 'pending_review', null, null
  )
on conflict (id) do update set
  patient_id = excluded.patient_id,
  appointment_id = excluded.appointment_id,
  source_fixture_id = excluded.source_fixture_id,
  file_reference = excluded.file_reference,
  extracted_facts = excluded.extracted_facts,
  field_evidence = excluded.field_evidence,
  extraction_confidence = excluded.extraction_confidence,
  readiness_status = excluded.readiness_status,
  readiness_reasons = excluded.readiness_reasons,
  processing_status = excluded.processing_status,
  review_status = excluded.review_status,
  confirmed_by_reference = excluded.confirmed_by_reference,
  confirmed_at = excluded.confirmed_at,
  deleted_at = null;

insert into public.eligibility_rules (
  id, issuer_code, document_type, package_or_checkup_code,
  required_selected_items, disallowed_or_conflicting_items, package_name,
  included_items, billing_arrangement, rule_version, effective_from,
  priority, active
)
values
  (
    'RULE-MRDEB-REFERRAL-V1', 'MRDEB', 'medical_referral_letter', null,
    '["Chest X-Ray","HIV Antibody Test","Treadmill ECG"]', '[]',
    'Meridian referral requirements',
    '["Chest X-Ray","HIV Antibody Test","Treadmill ECG"]',
    'insurer_authorisation', 'demo-v1', '2026-08-01 00:00:00+00', 10, true
  ),
  (
    'RULE-BLPHS-WELL2-V1', 'BLPHS', 'wellness_package_voucher', 'WELL2',
    '["Complete History Taking","Complete Physical Examination"]', '[]',
    'Executive screening WELL2',
    '["History","Physical examination","Screening panel"]',
    'voucher', 'demo-v1', '2026-08-01 00:00:00+00', 10, true
  )
on conflict (id) do update set
  required_selected_items = excluded.required_selected_items,
  included_items = excluded.included_items,
  billing_arrangement = excluded.billing_arrangement,
  active = true,
  deleted_at = null;

insert into public.eligibility_matches (
  id, coverage_document_id, appointment_id, matched_rule_id, match_status,
  match_basis, review_reasons, status, confirmed_by_reference, confirmed_at
)
values (
    'MATCH-014', 'DOC-014', 'appointment_014', 'RULE-MRDEB-REFERRAL-V1',
    'clean',
    '{"rule_version":"demo-v1","issuer_code":"MRDEB","document_type":"medical_referral_letter"}',
    '[]', 'confirmed', 'synthetic-seed', '2026-08-12 09:10:00+00'
  )
on conflict (id) do update set
  matched_rule_id = excluded.matched_rule_id,
  match_status = excluded.match_status,
  match_basis = excluded.match_basis,
  review_reasons = excluded.review_reasons,
  status = excluded.status,
  confirmed_by_reference = excluded.confirmed_by_reference,
  confirmed_at = excluded.confirmed_at,
  deleted_at = null;

insert into public.registration_validations (
  id, clinic_id, appointment_id, patient_id, field_results, outcome,
  patient_reason_code, patient_next_action, actor_reference
)
select
  'VAL-014', appointment.clinic_id, appointment.id, appointment.patient_id,
  '{"identifier":"source_validated","full_name":"source_validated","date_of_birth":"source_validated","email":"source_validated"}',
  'accepted', 'registration_confirmed', 'Continue to the required pre-arrival steps.', 'synthetic-seed'
from public.appointments appointment where appointment.id = 'appointment_014'
on conflict (id) do update set
  field_results = excluded.field_results,
  outcome = excluded.outcome,
  patient_reason_code = excluded.patient_reason_code,
  patient_next_action = excluded.patient_next_action,
  deleted_at = null;

insert into public.coverage_reuse_decisions (
  id, clinic_id, patient_id, appointment_id, prior_coverage_document_id,
  entry_source, match_method, decision, actor_reference
)
select
  'CRD-014', appointment.clinic_id, appointment.patient_id, appointment.id,
  'DOC-014', 'demo_account', 'identifier', 'reuse', 'synthetic-seed'
from public.appointments appointment where appointment.id = 'appointment_014'
on conflict (id) do update set
  prior_coverage_document_id = excluded.prior_coverage_document_id,
  match_method = excluded.match_method,
  decision = excluded.decision;

insert into public.patient_submissions (
  id, clinic_id, appointment_id, queue_entry_id, patient_id,
  registration_validation_id, coverage_reuse_decision_id, outcome,
  patient_reason_code, patient_next_action, internal_reason_code, actor_reference
)
values
  (
    'PRE-014', 'clinic_harbourfront', 'appointment_014', 'Q-014',
    (select patient_id from public.appointments where id = 'appointment_014'),
    'VAL-014', 'CRD-014', 'accepted', 'administrative_checks_complete',
    'Keep your queue ticket for arrival.', 'all_prerequisites_passed', 'synthetic-seed'
  ),
  (
    'PRE-015', 'clinic_harbourfront', 'appointment_015', 'Q-015',
    (select patient_id from public.appointments where id = 'appointment_015'),
    null, null, 'under_review', 'coverage_document_required',
    'Upload a current coverage document.', 'missing_document', 'synthetic-seed'
  ),
  (
    'PRE-015-REJECTED', 'clinic_harbourfront', 'appointment_015', 'Q-015',
    (select patient_id from public.appointments where id = 'appointment_015'),
    'VAL-015', null, 'rejected', 'registration_details_mismatch',
    'Review your booking details or ask clinic staff for help.',
    'registration_identity_conflict', 'synthetic-seed'
  )
on conflict (id) do update set
  outcome = excluded.outcome,
  patient_reason_code = excluded.patient_reason_code,
  patient_next_action = excluded.patient_next_action,
  internal_reason_code = excluded.internal_reason_code,
  deleted_at = null;

insert into public.manual_check_confirmations (
  queue_entry_id, identity_check_status, ecard_check_status,
  ecard_not_applicable_reason, confirmed_by_staff_id, attestation_version, confirmed_at
)
select
  'Q-019', 'manually_confirmed', 'not_applicable',
  'Synthetic walk-in has no insurer e-card fixture.', 'staff_noor', 'demo-v1',
  '2026-08-12 09:39:00+00'
where not exists (
  select 1 from public.manual_check_confirmations
  where queue_entry_id = 'Q-019' and attestation_version = 'demo-v1'
);

insert into public.patient_notifications (
  id, clinic_id, patient_id, queue_entry_id, coverage_document_id,
  category, category_map_version, channel, sent_by_reference,
  delivery_status, patient_action, sent_at
)
values (
  'NOTICE-018', 'clinic_harbourfront',
  (select id from public.patients where source_record_key = 'registration:0002'),
  'Q-018', 'DOC-018', 'document_expired', 'demo-v1', 'sms',
  'synthetic-seed', 'delivered', 'none', '2026-08-12 09:30:00+00'
)
on conflict (id) do update set
  category = excluded.category,
  category_map_version = excluded.category_map_version,
  delivery_status = excluded.delivery_status,
  patient_action = excluded.patient_action;

insert into public.counter_allocations (
  id, clinic_id, service_date, counter_number, workstream,
  assigned_staff_id, active, updated_by_staff_id
)
values
  ('counter_1', 'clinic_harbourfront', '2026-08-12', 'Counter 1', 'ready', 'staff_noor', true, 'staff_aisyah'),
  ('counter_2', 'clinic_harbourfront', '2026-08-12', 'Counter 2', 'ready', 'staff_aisyah', true, 'staff_aisyah'),
  ('counter_4', 'clinic_harbourfront', '2026-08-12', 'Counter 4', 'review', null, true, 'staff_aisyah')
on conflict (id) do update set
  workstream = excluded.workstream,
  assigned_staff_id = excluded.assigned_staff_id,
  active = excluded.active,
  updated_by_staff_id = excluded.updated_by_staff_id;

insert into public.staff_availability (
  id, staff_id, shift_start, shift_end, eligible_workstreams,
  planned_breaks, availability_status, current_workstream
)
values
  ('availability_noor', 'staff_noor', '2026-08-12 08:00:00+00', '2026-08-12 17:00:00+00',
    '["ready","review"]', '[]', 'serving', 'ready'),
  ('availability_aisyah', 'staff_aisyah', '2026-08-12 08:00:00+00', '2026-08-12 17:00:00+00',
    '["ready","review"]', '[]', 'available', null)
on conflict (id) do update set
  eligible_workstreams = excluded.eligible_workstreams,
  planned_breaks = excluded.planned_breaks,
  availability_status = excluded.availability_status,
  current_workstream = excluded.current_workstream;

insert into public.allocation_recommendations (
  id, clinic_id, generated_at, expires_at, pressured_workstream,
  demand_snapshot, qualified_resource, recommended_staff_id,
  recommended_counter_number, constraints_checked, rationale,
  expected_effect, status, decided_by_reference, decision_reason, decided_at
)
values
  (
    'A-008', 'clinic_harbourfront', '2026-08-12 08:55:00+00', '2026-08-12 09:10:00+00',
    'Ready arrivals', '{"current_wait_minutes":12,"estimated_staff_minutes":24}',
    'Counter 2 · Nurse Noor', 'staff_noor', 'Counter 2',
    '["Registration-trained","Minimum review coverage retained","Break window clear"]',
    'A short ready-arrival increase can be covered without removing review capacity.',
    '{"expected_wait_minutes":7,"ready_p90_delta_seconds":-240}', 'approved',
    'synthetic-operations-lead', 'Seeded human approval example', '2026-08-12 08:57:00+00'
  ),
  (
    'A-009', 'clinic_harbourfront', '2026-08-12 09:35:00+00', '2026-08-12 09:48:00+00',
    'Assisted review', '{"current_wait_minutes":18,"estimated_staff_minutes":42}',
    'Counter 4 · Nur Aisyah', 'staff_aisyah', 'Counter 4',
    '["Registration-trained","Minimum ready coverage retained","Break window clear","No reassignment in last 30 min"]',
    'Two review cases are approaching the 20-minute service target while Counter 4 has been idle for 7 minutes.',
    '{"expected_wait_minutes":9,"review_p90_delta_seconds":-360}', 'pending', null, null, null
  )
on conflict (id) do update set
  demand_snapshot = excluded.demand_snapshot,
  constraints_checked = excluded.constraints_checked,
  rationale = excluded.rationale,
  expected_effect = excluded.expected_effect,
  status = excluded.status,
  decided_by_reference = case when excluded.status = 'approved' then 'synthetic-operations-lead' else null end,
  decision_reason = case when excluded.status = 'approved' then 'Seeded human approval example' else null end,
  decided_at = case when excluded.status = 'approved' then '2026-08-12 08:57:00+00'::timestamptz else null end,
  deleted_at = null;

insert into public.operational_events (
  clinic_id, queue_entry_id, event_type, to_state, reason_code,
  staff_touch, actor_reference, occurred_at, metadata
)
select * from (values
  ('clinic_harbourfront', 'Q-019', 'readiness_changed', 'ready', 'all_prerequisites_passed', true,
    'synthetic-seed', '2026-08-12 09:41:00+00'::timestamptz,
    '{"label":"Q-019 became ready","detail":"Staff confirmed the rules-matched package; original ticket retained.","tone":"success"}'::jsonb),
  ('clinic_harbourfront', 'Q-017', 'document_received', 'processing', 'walk_in_upload', false,
    'synthetic-seed', '2026-08-12 09:38:00+00'::timestamptz,
    '{"label":"Q-017 document received","detail":"Walk-in intake captured at nurse-supervised Kiosk A.","tone":"neutral"}'::jsonb),
  ('clinic_harbourfront', null, 'allocation_recommended', 'pending', 'review_pressure', false,
    'synthetic-seed', '2026-08-12 09:35:00+00'::timestamptz,
    '{"label":"Allocation advice created","detail":"Recommendation A-009 expires at 09:48 and requires approval.","tone":"attention"}'::jsonb)
) as seed(clinic_id, queue_entry_id, event_type, to_state, reason_code, staff_touch, actor_reference, occurred_at, metadata)
where not exists (
  select 1 from public.operational_events existing
  where existing.actor_reference = 'synthetic-seed'
    and existing.event_type = seed.event_type
    and existing.occurred_at = seed.occurred_at
);

insert into public.configuration_releases (
  id, configuration_type, version, payload_hash, status,
  validation_summary, effective_from
)
values
  ('config_readiness_v1', 'readiness_gate', 'demo-v1', 'synthetic-readiness-demo-v1', 'active',
    '{"zero_false_ready":true}', '2026-08-12 00:00:00+00'),
  ('config_allocation_v1', 'allocation_constraint', 'demo-v1', 'synthetic-allocation-demo-v1', 'active',
    '{"role_skill_break_and_stability_checked":true}', '2026-08-12 00:00:00+00'),
  ('config_patient_messages_v1', 'patient_notification_category_map', 'demo-v1',
    'synthetic-patient-messages-demo-v1', 'active',
    '{"closed_categories":4,"free_text_disabled":true}', '2026-08-12 00:00:00+00')
on conflict (id) do update set
  status = excluded.status,
  validation_summary = excluded.validation_summary,
  effective_from = excluded.effective_from;

insert into public.simulator_snapshots (
  id, clinic_id, scenario_id, scenario_version, seed, assumptions_version,
  snapshot_hash, snapshot_payload
)
values
  ('snapshot_serial', 'clinic_harbourfront', 'serial_baseline', 'demo-v1', 20260809, 'demo-v1',
    'serial-baseline-20260809-demo-v1',
    '{"synthetic":true,"description":"Serial baseline with shared arrivals and sampled service times"}'),
  ('snapshot_single_ticket', 'clinic_harbourfront', 'single_ticket', 'demo-v1', 20260809, 'demo-v1',
    'single-ticket-20260809-demo-v1',
    '{"synthetic":true,"description":"Epicenter single-ticket readiness workflow"}'),
  ('snapshot_dynamic', 'clinic_harbourfront', 'dynamic_allocation', 'demo-v1', 20260809, 'demo-v1',
    'dynamic-allocation-20260809-demo-v1',
    '{"synthetic":true,"description":"Single-ticket flow with human-approved dynamic allocation"}')
on conflict (id) do update set
  snapshot_hash = excluded.snapshot_hash,
  snapshot_payload = excluded.snapshot_payload,
  active = true;

insert into public.simulator_runs (
  id, snapshot_id, configuration_hash, status, interventions,
  result_payload, version, completed_at
)
values
  (
    'run_serial_demo', 'snapshot_serial', 'serial-demo-v1', 'completed', '[]',
    '{"median_admin_wait_minutes":14,"p90_admin_wait_minutes":27,"second_ticket_count":0}',
    1, '2026-08-12 09:30:00+00'
  ),
  (
    'run_single_ticket_demo', 'snapshot_single_ticket', 'single-ticket-demo-v1', 'completed',
    '[{"type":"parallel_review_worklist"}]',
    '{"median_admin_wait_minutes":8,"p90_admin_wait_minutes":18,"second_ticket_count":0}',
    1, '2026-08-12 09:30:00+00'
  ),
  (
    'run_dynamic_demo', 'snapshot_dynamic', 'dynamic-demo-v1', 'completed',
    '[{"type":"approved_counter_reallocation","recommendation_id":"A-008"}]',
    '{"median_admin_wait_minutes":7,"p90_admin_wait_minutes":15,"second_ticket_count":0}',
    1, '2026-08-12 09:30:00+00'
  )
on conflict (id) do update set
  status = excluded.status,
  interventions = excluded.interventions,
  result_payload = excluded.result_payload,
  completed_at = excluded.completed_at;

commit;
