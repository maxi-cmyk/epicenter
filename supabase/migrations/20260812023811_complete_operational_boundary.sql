begin;

alter table public.clinics add column if not exists deleted_at timestamptz;
alter table public.review_cases add column if not exists deleted_at timestamptz;
alter table public.counter_allocations add column if not exists deleted_at timestamptz;
alter table public.staff_availability add column if not exists deleted_at timestamptz;
alter table public.allocation_recommendations add column if not exists deleted_at timestamptz;
alter table public.configuration_releases add column if not exists deleted_at timestamptz;
alter table public.queue_entries
  add column if not exists patient_outcome text
    check (patient_outcome in ('accepted', 'rejected', 'under_review')),
  add column if not exists patient_reason_code text,
  add column if not exists patient_next_action text,
  add column if not exists assigned_at timestamptz,
  add column if not exists rescheduled_from_queue_entry_id text
    references public.queue_entries(id) on delete restrict;

create index if not exists queue_entries_rescheduled_from_idx
  on public.queue_entries (rescheduled_from_queue_entry_id)
  where rescheduled_from_queue_entry_id is not null;

create table public.data_import_exceptions (
  id bigint generated always as identity primary key,
  source_record_key text not null unique,
  source_record_type text not null
    check (source_record_type in ('registration', 'general_health', 'occupational_health', 'document')),
  normalized_identifier_hash text,
  reason_code text not null
    check (reason_code in ('unmatched_patient', 'duplicate_identifier', 'invalid_date', 'conflicting_identity')),
  details jsonb not null default '{}'::jsonb,
  resolution_status text not null default 'unresolved'
    check (resolution_status in ('unresolved', 'linked', 'intentionally_ignored')),
  resolved_patient_id bigint references public.patients(id) on delete restrict,
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);
create index data_import_exceptions_status_idx
  on public.data_import_exceptions (resolution_status, created_at)
  where resolution_status = 'unresolved';
create index data_import_exceptions_resolved_patient_idx
  on public.data_import_exceptions (resolved_patient_id)
  where resolved_patient_id is not null;

create table public.registration_validations (
  id text primary key,
  clinic_id text not null references public.clinics(id),
  appointment_id text not null references public.appointments(id) on delete restrict,
  patient_id bigint not null references public.patients(id) on delete restrict,
  field_results jsonb not null,
  outcome text not null check (outcome in ('accepted', 'rejected', 'under_review')),
  patient_reason_code text not null,
  patient_next_action text not null,
  actor_reference text not null,
  version integer not null default 1 check (version > 0),
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);
create index registration_validations_appointment_idx
  on public.registration_validations (appointment_id, created_at desc)
  where deleted_at is null;
create index registration_validations_patient_idx
  on public.registration_validations (patient_id, created_at desc)
  where deleted_at is null;

create table public.coverage_documents (
  id text primary key,
  clinic_id text not null references public.clinics(id),
  patient_id bigint references public.patients(id) on delete restrict,
  appointment_id text references public.appointments(id) on delete restrict,
  source_fixture_id bigint references public.medical_document_samples(id) on delete set null,
  file_reference text not null,
  document_type text not null,
  issuer_code text,
  issuer_name text,
  issued_on date,
  validity_start date,
  validity_end date,
  extracted_identifier_hash text,
  extracted_identifier_masked text,
  patient_match_status text not null default 'needs_review'
    check (patient_match_status in ('exact_identifier', 'needs_review', 'conflict')),
  extracted_facts jsonb not null default '{}'::jsonb,
  field_evidence jsonb not null default '{}'::jsonb,
  extraction_confidence jsonb not null default '{}'::jsonb,
  readiness_status text not null default 'needs_review'
    check (readiness_status in ('pass', 'needs_review')),
  readiness_reasons jsonb not null default '[]'::jsonb,
  processing_status text not null default 'processing'
    check (processing_status in ('uploading', 'processing', 'ready', 'failed')),
  processing_error_code text,
  review_status text not null default 'pending_review'
    check (review_status in ('pending_review', 'confirmed', 'rejected')),
  confirmed_by_reference text,
  confirmed_at timestamptz,
  version integer not null default 1 check (version > 0),
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);
create index coverage_documents_patient_idx
  on public.coverage_documents (patient_id, created_at desc)
  where deleted_at is null;
create index coverage_documents_appointment_idx
  on public.coverage_documents (appointment_id, created_at desc)
  where deleted_at is null;
create index coverage_documents_source_fixture_idx
  on public.coverage_documents (source_fixture_id)
  where source_fixture_id is not null;
create index coverage_documents_review_worklist_idx
  on public.coverage_documents (clinic_id, review_status, created_at)
  where deleted_at is null and review_status = 'pending_review';

create table public.eligibility_rules (
  id text primary key,
  issuer_code text not null,
  document_type text not null,
  package_or_checkup_code text,
  required_selected_items jsonb not null default '[]'::jsonb,
  disallowed_or_conflicting_items jsonb not null default '[]'::jsonb,
  package_name text not null,
  included_items jsonb not null default '[]'::jsonb,
  billing_arrangement text not null,
  rule_version text not null,
  effective_from timestamptz not null,
  effective_to timestamptz,
  priority integer not null default 100,
  active boolean not null default true,
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  deleted_at timestamptz,
  unique (issuer_code, document_type, package_or_checkup_code, rule_version)
);
create index eligibility_rules_lookup_idx
  on public.eligibility_rules (issuer_code, document_type, package_or_checkup_code, priority)
  where active and deleted_at is null;

create table public.eligibility_matches (
  id text primary key,
  coverage_document_id text not null references public.coverage_documents(id) on delete restrict,
  appointment_id text not null references public.appointments(id) on delete restrict,
  matched_rule_id text references public.eligibility_rules(id) on delete restrict,
  match_status text not null check (match_status in ('clean', 'ambiguous', 'no_match')),
  match_basis jsonb not null default '{}'::jsonb,
  review_reasons jsonb not null default '[]'::jsonb,
  status text not null default 'pending_review'
    check (status in ('pending_review', 'confirmed', 'overridden')),
  confirmed_by_reference text,
  confirmed_at timestamptz,
  version integer not null default 1 check (version > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz,
  unique (coverage_document_id, appointment_id)
);
create index eligibility_matches_appointment_idx
  on public.eligibility_matches (appointment_id, match_status)
  where deleted_at is null;
create index eligibility_matches_rule_idx
  on public.eligibility_matches (matched_rule_id)
  where matched_rule_id is not null;

create table public.coverage_reuse_decisions (
  id text primary key,
  clinic_id text not null references public.clinics(id),
  patient_id bigint not null references public.patients(id) on delete restrict,
  appointment_id text not null references public.appointments(id) on delete restrict,
  prior_coverage_document_id text references public.coverage_documents(id) on delete restrict,
  entry_source text not null check (entry_source in ('tokenized_link', 'demo_account')),
  match_method text check (match_method in ('identifier', 'email')),
  decision text not null check (decision in ('reuse', 'replace')),
  replacement_document_id text references public.coverage_documents(id) on delete restrict,
  actor_reference text not null,
  created_at timestamptz not null default now()
);
create index coverage_reuse_decisions_patient_idx
  on public.coverage_reuse_decisions (patient_id, created_at desc);
create index coverage_reuse_decisions_appointment_idx
  on public.coverage_reuse_decisions (appointment_id, created_at desc);
create index coverage_reuse_decisions_prior_document_idx
  on public.coverage_reuse_decisions (prior_coverage_document_id)
  where prior_coverage_document_id is not null;
create index coverage_reuse_decisions_replacement_idx
  on public.coverage_reuse_decisions (replacement_document_id)
  where replacement_document_id is not null;

create table public.patient_submissions (
  id text primary key,
  clinic_id text not null references public.clinics(id),
  appointment_id text not null references public.appointments(id) on delete restrict,
  queue_entry_id text not null references public.queue_entries(id) on delete restrict,
  patient_id bigint not null references public.patients(id) on delete restrict,
  registration_validation_id text references public.registration_validations(id) on delete restrict,
  coverage_reuse_decision_id text references public.coverage_reuse_decisions(id) on delete restrict,
  outcome text not null check (outcome in ('accepted', 'rejected', 'under_review')),
  patient_reason_code text not null,
  patient_next_action text not null,
  internal_reason_code text not null,
  actor_reference text not null,
  version integer not null default 1 check (version > 0),
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);
create index patient_submissions_appointment_idx
  on public.patient_submissions (appointment_id, created_at desc)
  where deleted_at is null;
create index patient_submissions_queue_idx
  on public.patient_submissions (queue_entry_id, created_at desc)
  where deleted_at is null;
create index patient_submissions_patient_idx
  on public.patient_submissions (patient_id, created_at desc)
  where deleted_at is null;

create table public.patient_notifications (
  id text primary key,
  clinic_id text not null references public.clinics(id),
  patient_id bigint not null references public.patients(id) on delete restrict,
  queue_entry_id text references public.queue_entries(id) on delete restrict,
  coverage_document_id text references public.coverage_documents(id) on delete restrict,
  category text not null
    check (category in ('document_unclear', 'document_incomplete', 'document_expired', 'document_type_mismatch')),
  category_map_version text not null,
  channel text not null check (channel in ('sms', 'email')),
  sent_by_reference text,
  delivery_status text not null check (delivery_status in ('queued', 'sent', 'delivered', 'failed')),
  delivery_failure_reason text,
  patient_action text not null default 'none'
    check (patient_action in ('none', 'reopened_link', 'resubmitted', 'expired_unactioned')),
  sent_at timestamptz not null default now(),
  actioned_at timestamptz
);
create index patient_notifications_patient_idx
  on public.patient_notifications (patient_id, sent_at desc);
create index patient_notifications_queue_idx
  on public.patient_notifications (queue_entry_id)
  where queue_entry_id is not null;
create index patient_notifications_document_idx
  on public.patient_notifications (coverage_document_id)
  where coverage_document_id is not null;

create or replace function private.reject_immutable_mutation()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
begin
  raise exception 'immutable_record' using errcode = 'PT409';
end;
$$;

create trigger operational_events_immutable
  before update or delete on public.operational_events
  for each row execute function private.reject_immutable_mutation();
create trigger audit_log_immutable
  before update or delete on public.audit_log
  for each row execute function private.reject_immutable_mutation();

create trigger registration_validations_set_updated_at before update on public.registration_validations
  for each row execute function private.set_updated_at();
create trigger coverage_documents_set_updated_at before update on public.coverage_documents
  for each row execute function private.set_updated_at();
create trigger eligibility_matches_set_updated_at before update on public.eligibility_matches
  for each row execute function private.set_updated_at();
create trigger patient_submissions_set_updated_at before update on public.patient_submissions
  for each row execute function private.set_updated_at();

create or replace function public.epicenter_validate_registration(
  p_appointment_reference text,
  p_identifier_hash text,
  p_full_name text,
  p_date_of_birth date,
  p_email text,
  p_actor_reference text,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  current_appointment public.appointments%rowtype;
  current_patient public.patients%rowtype;
  validation_row public.registration_validations%rowtype;
  identifier_result text;
  name_result text;
  dob_result text;
  email_result text;
  outcome_value text;
  safe_reason text;
  next_action text;
begin
  perform pg_advisory_xact_lock(hashtextextended('registration_validation:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'registration_validation' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;

  select * into current_appointment from public.appointments
  where appointment_reference = p_appointment_reference and deleted_at is null for update;
  if not found or current_appointment.patient_id is null then
    raise exception 'appointment_not_found' using errcode = 'PT404';
  end if;
  select * into current_patient from public.patients
  where id = current_appointment.patient_id and deleted_at is null;

  identifier_result := case
    when coalesce(p_identifier_hash, '') !~ '^[0-9a-f]{64}$' then 'malformed'
    when p_identifier_hash = current_patient.identifier_hash then 'source_validated'
    else 'conflict' end;
  name_result := case
    when nullif(trim(p_full_name), '') is null then 'missing'
    when lower(trim(p_full_name)) = lower(trim(current_patient.full_name)) then 'source_validated'
    else 'conflict' end;
  dob_result := case
    when p_date_of_birth is null then 'missing'
    when p_date_of_birth = current_patient.date_of_birth then 'source_validated'
    else 'conflict' end;
  email_result := case
    when nullif(trim(p_email), '') is null then 'missing'
    when lower(trim(p_email)) = lower(trim(coalesce(current_patient.email, ''))) then 'source_validated'
    else 'conflict' end;

  if 'conflict' in (identifier_result, name_result, dob_result, email_result)
    or 'malformed' in (identifier_result, name_result, dob_result, email_result) then
    outcome_value := 'rejected';
    safe_reason := 'registration_details_mismatch';
    next_action := 'Review your booking details or ask clinic staff for help.';
  elsif 'missing' in (identifier_result, name_result, dob_result, email_result) then
    outcome_value := 'under_review';
    safe_reason := 'registration_details_incomplete';
    next_action := 'Complete the missing booking details before arrival.';
  else
    outcome_value := 'accepted';
    safe_reason := 'registration_confirmed';
    next_action := 'Continue to the required pre-arrival steps.';
  end if;

  insert into public.registration_validations (
    id, clinic_id, appointment_id, patient_id, field_results, outcome,
    patient_reason_code, patient_next_action, actor_reference
  ) values (
    'VAL-' || upper(substr(md5(p_idempotency_key), 1, 12)),
    current_appointment.clinic_id, current_appointment.id, current_patient.id,
    jsonb_build_object('identifier', identifier_result, 'full_name', name_result,
      'date_of_birth', dob_result, 'email', email_result),
    outcome_value, safe_reason, next_action, p_actor_reference
  ) returning * into validation_row;

  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    current_appointment.clinic_id, p_actor_reference, current_patient.id,
    'validate_registration', 'registration_validations', validation_row.id,
    jsonb_build_object('outcome', outcome_value, 'appointment_id', current_appointment.id)
  );
  existing_response := to_jsonb(validation_row);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('registration_validation', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_submit_prearrival(
  p_appointment_reference text,
  p_coverage_action text,
  p_file_name text,
  p_expected_ticket_version integer,
  p_actor_reference text,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  current_appointment public.appointments%rowtype;
  current_ticket public.queue_entries%rowtype;
  prior_document public.coverage_documents%rowtype;
  replacement_document public.coverage_documents%rowtype;
  decision_row public.coverage_reuse_decisions%rowtype;
  submission_row public.patient_submissions%rowtype;
  outcome_value text := 'under_review';
  safe_reason text := 'checks_in_progress';
  next_action text := 'Clinic staff will confirm the result before it becomes final.';
begin
  perform pg_advisory_xact_lock(hashtextextended('prearrival_submission:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'prearrival_submission' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;
  if p_coverage_action not in ('reuse', 'replace') then
    raise exception 'invalid_coverage_action' using errcode = 'PT422';
  end if;
  if p_coverage_action = 'replace' and nullif(trim(p_file_name), '') is null then
    raise exception 'replacement_document_required' using errcode = 'PT422';
  end if;

  select * into current_appointment from public.appointments
  where appointment_reference = p_appointment_reference and deleted_at is null for update;
  if not found or current_appointment.patient_id is null then
    raise exception 'appointment_not_found' using errcode = 'PT404';
  end if;
  select * into current_ticket from public.queue_entries
  where appointment_id = current_appointment.id and deleted_at is null for update;
  if not found then raise exception 'ticket_not_found' using errcode = 'PT404'; end if;
  if current_ticket.version <> p_expected_ticket_version then
    raise exception 'stale_ticket_version' using errcode = 'PT409';
  end if;

  if p_coverage_action = 'reuse' then
    select * into prior_document from public.coverage_documents
    where patient_id = current_appointment.patient_id
      and review_status = 'confirmed' and deleted_at is null
    order by confirmed_at desc nulls last, created_at desc limit 1;
    if not found then
      safe_reason := 'coverage_document_required';
      next_action := 'Upload a current coverage document for clinic review.';
    end if;
  else
    insert into public.coverage_documents (
      id, clinic_id, patient_id, appointment_id, file_reference, document_type,
      patient_match_status, readiness_status, readiness_reasons, processing_status, review_status
    ) values (
      'DOC-' || upper(substr(md5(p_idempotency_key), 1, 12)), current_appointment.clinic_id,
      current_appointment.patient_id, current_appointment.id, trim(p_file_name), 'other',
      'needs_review', 'needs_review', '["awaiting_extraction"]'::jsonb, 'processing', 'pending_review'
    ) returning * into replacement_document;
  end if;

  insert into public.coverage_reuse_decisions (
    id, clinic_id, patient_id, appointment_id, prior_coverage_document_id,
    entry_source, match_method, decision, replacement_document_id, actor_reference
  ) values (
    'CRD-' || upper(substr(md5(p_idempotency_key), 1, 12)), current_appointment.clinic_id,
    current_appointment.patient_id, current_appointment.id, prior_document.id,
    'demo_account', case when prior_document.id is null then null else 'identifier' end,
    p_coverage_action, replacement_document.id, p_actor_reference
  ) returning * into decision_row;

  update public.queue_entries set
    readiness_state = case when prior_document.id is null and replacement_document.id is null
      then 'needs_review' else 'processing' end,
    readiness_reason = case when prior_document.id is null and replacement_document.id is null
      then 'missing_document' else 'processing' end,
    patient_outcome = outcome_value,
    patient_reason_code = safe_reason,
    patient_next_action = next_action,
    processing_stage = case when prior_document.id is null and replacement_document.id is null
      then 'Awaiting coverage document' else 'Document processing' end,
    version = version + 1
  where id = current_ticket.id;

  insert into public.patient_submissions (
    id, clinic_id, appointment_id, queue_entry_id, patient_id,
    coverage_reuse_decision_id, outcome, patient_reason_code, patient_next_action,
    internal_reason_code, actor_reference
  ) values (
    'PRE-' || upper(substr(md5(p_idempotency_key), 1, 12)), current_appointment.clinic_id,
    current_appointment.id, current_ticket.id, current_appointment.patient_id, decision_row.id,
    outcome_value, safe_reason, next_action,
    case when prior_document.id is null and replacement_document.id is null
      then 'no_confirmed_prior_document' else 'pending_current_checks' end,
    p_actor_reference
  ) returning * into submission_row;

  insert into public.operational_events (
    clinic_id, queue_entry_id, event_type, to_state, reason_code, staff_touch,
    actor_reference, metadata
  ) values (
    current_appointment.clinic_id, current_ticket.id, 'prearrival_submitted', 'under_review',
    safe_reason, false, p_actor_reference,
    jsonb_build_object('coverage_action', p_coverage_action, 'submission_id', submission_row.id)
  );
  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    current_appointment.clinic_id, p_actor_reference, current_appointment.patient_id,
    'submit_prearrival', 'patient_submissions', submission_row.id,
    jsonb_build_object('coverage_action', p_coverage_action, 'queue_entry_id', current_ticket.id)
  );
  existing_response := to_jsonb(submission_row);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('prearrival_submission', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_process_document(
  p_ticket_id text,
  p_document_id text,
  p_expected_version integer,
  p_readiness_status text,
  p_match_status text,
  p_all_required_documents_present boolean,
  p_all_documents_valid boolean,
  p_staff_confirmed boolean,
  p_reason text,
  p_actor_reference text,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  current_ticket public.queue_entries%rowtype;
  updated_ticket public.queue_entries%rowtype;
  final_state text;
begin
  perform pg_advisory_xact_lock(hashtextextended('document_processing:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'document_processing' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;
  select * into current_ticket from public.queue_entries
  where id = p_ticket_id and deleted_at is null for update;
  if not found then raise exception 'ticket_not_found' using errcode = 'PT404'; end if;
  if current_ticket.version <> p_expected_version then
    raise exception 'stale_ticket_version' using errcode = 'PT409';
  end if;
  if p_readiness_status not in ('pass', 'needs_review')
    or p_match_status not in ('clean', 'ambiguous', 'no_match') then
    raise exception 'invalid_document_result' using errcode = 'PT422';
  end if;

  update public.coverage_documents set
    readiness_status = p_readiness_status,
    patient_match_status = case p_match_status when 'clean' then 'exact_identifier'
      when 'ambiguous' then 'needs_review' else 'conflict' end,
    readiness_reasons = case when p_readiness_status = 'pass' then '[]'::jsonb
      else jsonb_build_array(p_reason) end,
    processing_status = 'ready',
    review_status = case when p_staff_confirmed then 'confirmed' else 'pending_review' end,
    confirmed_by_reference = case when p_staff_confirmed then p_actor_reference else null end,
    confirmed_at = case when p_staff_confirmed then now() else null end,
    version = version + 1
  where id = p_document_id
    and clinic_id = current_ticket.clinic_id
    and deleted_at is null
    and (
      appointment_id = current_ticket.appointment_id
      or (patient_id is not null and patient_id = current_ticket.patient_id)
    );
  if not found then raise exception 'document_not_found' using errcode = 'PT404'; end if;

  final_state := case when p_staff_confirmed
    and p_all_required_documents_present and p_all_documents_valid
    and p_readiness_status = 'pass' and p_match_status = 'clean'
    and (current_ticket.intake_type = 'walk_in' or current_ticket.prereg_completed_at is not null)
    then 'ready' else 'needs_review' end;

  update public.queue_entries set
    all_required_documents_present = p_all_required_documents_present,
    all_documents_valid = p_all_documents_valid,
    extraction_status = p_readiness_status,
    match_status = p_match_status,
    readiness_state = final_state,
    readiness_reason = case when final_state = 'ready' then 'all_prerequisites_passed' else p_reason end,
    patient_outcome = case when final_state = 'ready' then 'accepted' else 'under_review' end,
    patient_reason_code = case when final_state = 'ready' then 'administrative_checks_complete'
      else 'clinic_review_required' end,
    patient_next_action = case when final_state = 'ready' then 'Keep your queue ticket for arrival.'
      else 'Clinic staff are reviewing your submission.' end,
    staff_confirmed = p_staff_confirmed,
    ready_at = case when final_state = 'ready' then now() else null end,
    processing_stage = case when final_state = 'ready' then 'Waiting to be called' else 'Assisted review' end,
    version = version + 1
  where id = p_ticket_id returning * into updated_ticket;

  insert into public.operational_events (
    clinic_id, queue_entry_id, event_type, from_state, to_state, reason_code,
    staff_touch, actor_reference, metadata
  ) values (
    updated_ticket.clinic_id, updated_ticket.id, 'document_processed',
    current_ticket.readiness_state, final_state, p_reason, true, p_actor_reference,
    jsonb_build_object('document_id', p_document_id, 'match_status', p_match_status)
  );
  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    updated_ticket.clinic_id, p_actor_reference, updated_ticket.patient_id,
    'process_document', 'coverage_documents', p_document_id,
    jsonb_build_object('queue_entry_id', p_ticket_id, 'outcome', final_state,
      'version', updated_ticket.version)
  );
  existing_response := to_jsonb(updated_ticket);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('document_processing', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_assign_counter(
  p_ticket_id text,
  p_expected_version integer,
  p_counter_number text,
  p_actor_reference text,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  current_ticket public.queue_entries%rowtype;
  updated_ticket public.queue_entries%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('counter_assignment:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'counter_assignment' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;
  if nullif(trim(p_counter_number), '') is null then
    raise exception 'counter_required' using errcode = 'PT422';
  end if;
  select * into current_ticket from public.queue_entries
  where id = p_ticket_id and deleted_at is null for update;
  if not found then raise exception 'ticket_not_found' using errcode = 'PT404'; end if;
  if current_ticket.version <> p_expected_version then
    raise exception 'stale_ticket_version' using errcode = 'PT409';
  end if;
  update public.queue_entries set
    expected_counter_number = case when visit_status = 'incoming' then trim(p_counter_number)
      else expected_counter_number end,
    counter_number = case when visit_status <> 'incoming' then trim(p_counter_number)
      else counter_number end,
    assigned_at = now(), version = version + 1
  where id = p_ticket_id returning * into updated_ticket;
  insert into public.operational_events (
    clinic_id, queue_entry_id, event_type, from_state, to_state, reason_code,
    staff_touch, actor_reference, metadata
  ) values (
    updated_ticket.clinic_id, updated_ticket.id, 'counter_assigned',
    coalesce(current_ticket.counter_number, current_ticket.expected_counter_number),
    trim(p_counter_number), 'staff_assignment', true, p_actor_reference,
    jsonb_build_object('visit_status', updated_ticket.visit_status)
  );
  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    updated_ticket.clinic_id, p_actor_reference, updated_ticket.patient_id,
    'assign_counter', 'queue_entries', updated_ticket.id,
    jsonb_build_object('counter_number', trim(p_counter_number), 'version', updated_ticket.version)
  );
  existing_response := to_jsonb(updated_ticket);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('counter_assignment', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_create_patient(
  p_clinic_id text,
  p_source_record_key text,
  p_identifier_hash text,
  p_identifier_masked text,
  p_full_name text,
  p_date_of_birth date,
  p_email text,
  p_contact_mobile text,
  p_reason text,
  p_actor_reference text,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  patient_row public.patients%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('patient_create:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'patient_create' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;
  if p_identifier_hash !~ '^[0-9a-f]{64}$' or nullif(trim(p_full_name), '') is null
    or nullif(trim(p_reason), '') is null then
    raise exception 'invalid_patient_create' using errcode = 'PT422';
  end if;
  insert into public.patients (
    source_record_key, identifier_hash, identifier_masked, full_name,
    date_of_birth, email, contact_mobile
  ) values (
    p_source_record_key, p_identifier_hash, p_identifier_masked, trim(p_full_name),
    p_date_of_birth, nullif(trim(p_email), ''), nullif(trim(p_contact_mobile), '')
  ) returning * into patient_row;
  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    p_clinic_id, p_actor_reference, patient_row.id, 'create_patient', 'patients',
    patient_row.id::text, jsonb_build_object('reason', p_reason, 'after', to_jsonb(patient_row))
  );
  existing_response := to_jsonb(patient_row);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('patient_create', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_update_patient(
  p_patient_id bigint,
  p_clinic_id text,
  p_expected_version integer,
  p_full_name text,
  p_email text,
  p_contact_mobile text,
  p_reason text,
  p_actor_reference text,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  current_patient public.patients%rowtype;
  patient_row public.patients%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('patient_update:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'patient_update' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;
  if nullif(trim(p_reason), '') is null then
    raise exception 'mutation_reason_required' using errcode = 'PT422';
  end if;
  select * into current_patient from public.patients
  where id = p_patient_id and deleted_at is null for update;
  if not found then raise exception 'patient_not_found' using errcode = 'PT404'; end if;
  if current_patient.version <> p_expected_version then
    raise exception 'stale_patient_version' using errcode = 'PT409';
  end if;
  update public.patients set
    full_name = coalesce(nullif(trim(p_full_name), ''), full_name),
    email = coalesce(nullif(trim(p_email), ''), email),
    contact_mobile = coalesce(nullif(trim(p_contact_mobile), ''), contact_mobile),
    version = version + 1
  where id = p_patient_id returning * into patient_row;
  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    p_clinic_id, p_actor_reference, patient_row.id, 'update_patient', 'patients',
    patient_row.id::text, jsonb_build_object('reason', p_reason,
      'before', to_jsonb(current_patient), 'after', to_jsonb(patient_row))
  );
  existing_response := to_jsonb(patient_row);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('patient_update', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_soft_delete_patient(
  p_patient_id bigint,
  p_clinic_id text,
  p_expected_version integer,
  p_reason text,
  p_actor_reference text,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  current_patient public.patients%rowtype;
  patient_row public.patients%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('patient_delete:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'patient_delete' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;
  if nullif(trim(p_reason), '') is null then
    raise exception 'mutation_reason_required' using errcode = 'PT422';
  end if;
  select * into current_patient from public.patients
  where id = p_patient_id and deleted_at is null for update;
  if not found then raise exception 'patient_not_found' using errcode = 'PT404'; end if;
  if current_patient.version <> p_expected_version then
    raise exception 'stale_patient_version' using errcode = 'PT409';
  end if;
  update public.patients set deleted_at = now(), version = version + 1
  where id = p_patient_id returning * into patient_row;
  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    p_clinic_id, p_actor_reference, patient_row.id, 'soft_delete_patient', 'patients',
    patient_row.id::text, jsonb_build_object('reason', p_reason,
      'before', to_jsonb(current_patient), 'after', to_jsonb(patient_row))
  );
  existing_response := to_jsonb(patient_row);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('patient_delete', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

alter table public.data_import_exceptions enable row level security;
alter table public.registration_validations enable row level security;
alter table public.coverage_documents enable row level security;
alter table public.eligibility_rules enable row level security;
alter table public.eligibility_matches enable row level security;
alter table public.coverage_reuse_decisions enable row level security;
alter table public.patient_submissions enable row level security;
alter table public.patient_notifications enable row level security;

revoke all on table public.data_import_exceptions from anon, authenticated;
revoke all on table public.registration_validations from anon, authenticated;
revoke all on table public.coverage_documents from anon, authenticated;
revoke all on table public.eligibility_rules from anon, authenticated;
revoke all on table public.eligibility_matches from anon, authenticated;
revoke all on table public.coverage_reuse_decisions from anon, authenticated;
revoke all on table public.patient_submissions from anon, authenticated;
revoke all on table public.patient_notifications from anon, authenticated;
revoke all on sequence public.data_import_exceptions_id_seq from anon, authenticated;
revoke all on function public.epicenter_validate_registration(text, text, text, date, text, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_submit_prearrival(text, text, text, integer, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_process_document(text, text, integer, text, text, boolean, boolean, boolean, text, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_assign_counter(text, integer, text, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_create_patient(text, text, text, text, text, date, text, text, text, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_update_patient(bigint, text, integer, text, text, text, text, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_soft_delete_patient(bigint, text, integer, text, text, text)
  from public, anon, authenticated;

grant select, insert, update, delete on table public.data_import_exceptions to service_role;
grant select, insert, update, delete on table public.registration_validations to service_role;
grant select, insert, update, delete on table public.coverage_documents to service_role;
grant select, insert, update, delete on table public.eligibility_rules to service_role;
grant select, insert, update, delete on table public.eligibility_matches to service_role;
grant select, insert, update, delete on table public.coverage_reuse_decisions to service_role;
grant select, insert, update, delete on table public.patient_submissions to service_role;
grant select, insert, update, delete on table public.patient_notifications to service_role;
grant usage, select on sequence public.data_import_exceptions_id_seq to service_role;
grant execute on function public.epicenter_validate_registration(text, text, text, date, text, text, text)
  to service_role;
grant execute on function public.epicenter_submit_prearrival(text, text, text, integer, text, text)
  to service_role;
grant execute on function public.epicenter_process_document(text, text, integer, text, text, boolean, boolean, boolean, text, text, text)
  to service_role;
grant execute on function public.epicenter_assign_counter(text, integer, text, text, text)
  to service_role;
grant execute on function public.epicenter_create_patient(text, text, text, text, text, date, text, text, text, text, text)
  to service_role;
grant execute on function public.epicenter_update_patient(bigint, text, integer, text, text, text, text, text, text)
  to service_role;
grant execute on function public.epicenter_soft_delete_patient(bigint, text, integer, text, text, text)
  to service_role;

comment on table public.registration_validations is
  'Appointment-scoped comparison evidence. Conflicts never overwrite canonical registration data.';
comment on table public.patient_submissions is
  'Patient-safe accepted, rejected, or under-review result, separated from internal reason evidence.';
comment on table public.coverage_reuse_decisions is
  'Reuses only a source document; current appointment validity and eligibility must be recalculated.';

commit;
