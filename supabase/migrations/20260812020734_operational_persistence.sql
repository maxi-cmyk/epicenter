begin;

create schema if not exists private;

alter table public.patients
  add column version integer not null default 1 check (version > 0),
  add column updated_at timestamptz not null default now(),
  add column deleted_at timestamptz;

create table public.clinics (
  id text primary key,
  name text not null,
  timezone text not null default 'Asia/Singapore',
  active boolean not null default true,
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.appointments (
  id text primary key,
  appointment_reference text not null unique,
  clinic_id text not null references public.clinics(id),
  patient_id bigint references public.patients(id) on delete restrict,
  scheduled_at timestamptz not null,
  appointment_type text not null,
  questionnaire_type text check (questionnaire_type in ('general_health', 'occupational_health')),
  administrative_urgency boolean not null default false,
  status text not null default 'booked'
    check (status in ('booked', 'checked_in', 'completed', 'cancelled', 'no_show')),
  version integer not null default 1 check (version > 0),
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);
create index appointments_clinic_scheduled_idx on public.appointments (clinic_id, scheduled_at);
create index appointments_patient_id_idx on public.appointments (patient_id);

create table public.staff_accounts (
  id text primary key,
  clerk_user_id text unique,
  clinic_id text not null references public.clinics(id),
  full_name text not null,
  email text,
  role text not null
    check (role in ('registration', 'pharmacist', 'billing', 'operations_admin', 'auditor')),
  active boolean not null default true,
  version integer not null default 1 check (version > 0),
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);
create index staff_accounts_clinic_active_idx on public.staff_accounts (clinic_id, active);

create table public.patient_accounts (
  id bigint generated always as identity primary key,
  clerk_user_id text not null unique,
  patient_id bigint not null references public.patients(id) on delete restrict,
  email text,
  phone text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index patient_accounts_patient_id_idx on public.patient_accounts (patient_id);

create sequence public.queue_ticket_number_seq start with 100;

create table public.queue_entries (
  id text primary key,
  clinic_id text not null references public.clinics(id),
  patient_id bigint references public.patients(id) on delete restrict,
  patient_reference text not null,
  patient_name_snapshot text not null,
  appointment_id text references public.appointments(id) on delete restrict,
  appointment_reference text,
  intake_type text not null check (intake_type in ('booked', 'walk_in')),
  visit_status text not null check (visit_status in ('incoming', 'ongoing', 'finished')),
  visit_outcome text check (visit_outcome in ('completed', 'cancelled', 'no_show')),
  prereg_completed_at timestamptz,
  all_required_documents_present boolean not null default false,
  all_documents_valid boolean not null default false,
  extraction_status text not null default 'needs_review'
    check (extraction_status in ('pass', 'needs_review')),
  match_status text not null default 'no_match'
    check (match_status in ('clean', 'ambiguous', 'no_match')),
  readiness_state text not null check (readiness_state in ('processing', 'ready', 'needs_review')),
  readiness_reason text not null,
  scheduled_at timestamptz,
  checked_in_at timestamptz,
  original_ordering_at timestamptz not null,
  waiting_minutes integer not null default 0 check (waiting_minutes >= 0),
  expected_queue_number text,
  expected_counter_number text,
  queue_number text,
  counter_number text,
  processing_stage text not null,
  service_target text not null default 'on_track'
    check (service_target in ('on_track', 'approaching', 'over_target')),
  staff_confirmed boolean not null default false,
  clinical_escalation boolean not null default false,
  ready_at timestamptz,
  completed_at timestamptz,
  version integer not null default 1 check (version > 0),
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz,
  check (readiness_state <> 'ready' or staff_confirmed),
  check (appointment_id is not null or intake_type = 'walk_in')
);
create unique index queue_entries_appointment_id_unique
  on public.queue_entries (appointment_id) where appointment_id is not null and deleted_at is null;
create index queue_entries_clinic_worklist_idx
  on public.queue_entries (clinic_id, visit_status, readiness_state, original_ordering_at)
  where deleted_at is null;
create index queue_entries_patient_id_idx on public.queue_entries (patient_id);

create table public.review_cases (
  id text primary key,
  queue_entry_id text not null unique references public.queue_entries(id) on delete cascade,
  reason_code text not null,
  reason_label text not null,
  document_name text,
  evidence_summary text not null,
  next_action text not null,
  resolved_at timestamptz,
  version integer not null default 1 check (version > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.manual_check_confirmations (
  id bigint generated always as identity primary key,
  queue_entry_id text not null references public.queue_entries(id) on delete restrict,
  identity_check_status text not null check (identity_check_status = 'manually_confirmed'),
  ecard_check_status text not null check (ecard_check_status in ('manually_confirmed', 'not_applicable')),
  ecard_not_applicable_reason text,
  confirmed_by_staff_id text not null references public.staff_accounts(id),
  attestation_version text not null,
  confirmed_at timestamptz not null default now()
);
create index manual_check_confirmations_queue_entry_idx
  on public.manual_check_confirmations (queue_entry_id, confirmed_at desc);

create table public.counter_allocations (
  id text primary key,
  clinic_id text not null references public.clinics(id),
  service_date date not null,
  counter_number text not null,
  workstream text not null check (workstream in ('ready', 'review')),
  assigned_staff_id text references public.staff_accounts(id),
  effective_from timestamptz,
  effective_to timestamptz,
  active boolean not null default true,
  updated_by_staff_id text references public.staff_accounts(id),
  version integer not null default 1 check (version > 0),
  updated_at timestamptz not null default now()
);
create index counter_allocations_active_idx
  on public.counter_allocations (clinic_id, service_date, active);

create table public.staff_availability (
  id text primary key,
  staff_id text not null references public.staff_accounts(id),
  shift_start timestamptz not null,
  shift_end timestamptz not null,
  eligible_workstreams jsonb not null default '[]'::jsonb,
  planned_breaks jsonb not null default '[]'::jsonb,
  availability_status text not null
    check (availability_status in ('available', 'serving', 'break', 'unavailable')),
  current_workstream text,
  version integer not null default 1 check (version > 0),
  updated_at timestamptz not null default now(),
  check (shift_end > shift_start)
);
create index staff_availability_staff_shift_idx on public.staff_availability (staff_id, shift_start);

create table public.allocation_recommendations (
  id text primary key,
  clinic_id text not null references public.clinics(id),
  generated_at timestamptz not null,
  expires_at timestamptz not null,
  pressured_workstream text not null,
  demand_snapshot jsonb not null default '{}'::jsonb,
  qualified_resource text not null,
  recommended_staff_id text references public.staff_accounts(id),
  recommended_counter_number text,
  constraints_checked jsonb not null default '[]'::jsonb,
  rationale text not null,
  expected_effect jsonb not null default '{}'::jsonb,
  status text not null
    check (status in ('pending', 'approved', 'modified', 'rejected', 'expired', 'reversed')),
  decided_by_reference text,
  decision_reason text,
  decided_at timestamptz,
  version integer not null default 1 check (version > 0),
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index allocation_recommendations_clinic_status_idx
  on public.allocation_recommendations (clinic_id, status, generated_at desc);

create table public.operational_events (
  id bigint generated always as identity primary key,
  clinic_id text not null references public.clinics(id),
  queue_entry_id text references public.queue_entries(id) on delete restrict,
  event_type text not null,
  from_state text,
  to_state text,
  reason_code text,
  staff_touch boolean not null default false,
  actor_reference text,
  occurred_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);
create index operational_events_clinic_occurred_idx
  on public.operational_events (clinic_id, occurred_at desc);
create index operational_events_queue_entry_idx on public.operational_events (queue_entry_id);

create table public.audit_log (
  id bigint generated always as identity primary key,
  clinic_id text references public.clinics(id),
  actor_reference text not null,
  patient_id bigint references public.patients(id) on delete restrict,
  action_type text not null,
  target_table text not null,
  target_id text not null,
  details jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now()
);
create index audit_log_clinic_occurred_idx on public.audit_log (clinic_id, occurred_at desc);
create index audit_log_patient_id_idx on public.audit_log (patient_id);

create table public.idempotency_records (
  operation text not null,
  idempotency_key text not null,
  actor_reference text not null,
  request_hash text,
  response_payload jsonb not null,
  created_at timestamptz not null default now(),
  primary key (operation, idempotency_key)
);

create table public.configuration_releases (
  id text primary key,
  configuration_type text not null,
  version text not null,
  payload_hash text not null,
  status text not null check (status in ('draft', 'shadow', 'approved', 'active', 'rolled_back')),
  validation_summary jsonb not null default '{}'::jsonb,
  effective_from timestamptz,
  effective_to timestamptz,
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  unique (configuration_type, version)
);

create table public.simulator_snapshots (
  id text primary key,
  clinic_id text not null references public.clinics(id),
  scenario_id text not null,
  scenario_version text not null,
  seed bigint not null,
  assumptions_version text not null,
  snapshot_hash text not null,
  snapshot_payload jsonb not null,
  active boolean not null default true,
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  unique (scenario_id, scenario_version, seed)
);

create table public.simulator_runs (
  id text primary key,
  snapshot_id text not null references public.simulator_snapshots(id) on delete restrict,
  configuration_hash text not null,
  status text not null check (status in ('pending', 'running', 'completed', 'failed')),
  interventions jsonb not null default '[]'::jsonb,
  result_payload jsonb,
  version integer not null default 1 check (version > 0),
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  unique (snapshot_id, configuration_hash)
);

create or replace function private.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger patients_set_updated_at before update on public.patients
  for each row execute function private.set_updated_at();
create trigger clinics_set_updated_at before update on public.clinics
  for each row execute function private.set_updated_at();
create trigger appointments_set_updated_at before update on public.appointments
  for each row execute function private.set_updated_at();
create trigger staff_accounts_set_updated_at before update on public.staff_accounts
  for each row execute function private.set_updated_at();
create trigger patient_accounts_set_updated_at before update on public.patient_accounts
  for each row execute function private.set_updated_at();
create trigger queue_entries_set_updated_at before update on public.queue_entries
  for each row execute function private.set_updated_at();
create trigger review_cases_set_updated_at before update on public.review_cases
  for each row execute function private.set_updated_at();
create trigger counter_allocations_set_updated_at before update on public.counter_allocations
  for each row execute function private.set_updated_at();
create trigger staff_availability_set_updated_at before update on public.staff_availability
  for each row execute function private.set_updated_at();
create trigger allocation_recommendations_set_updated_at before update on public.allocation_recommendations
  for each row execute function private.set_updated_at();

create or replace function public.epicenter_transition_ticket(
  p_ticket_id text,
  p_expected_version integer,
  p_readiness_state text,
  p_reason text,
  p_staff_confirmed boolean,
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
  perform pg_advisory_xact_lock(hashtextextended('ticket_transition:' || p_idempotency_key, 0));
  select response_payload into existing_response
  from public.idempotency_records
  where operation = 'ticket_transition' and idempotency_key = p_idempotency_key;
  if existing_response is not null then
    return existing_response;
  end if;

  select * into current_ticket from public.queue_entries
  where id = p_ticket_id and deleted_at is null for update;
  if not found then
    raise exception 'ticket_not_found' using errcode = 'P0002';
  end if;
  if current_ticket.version <> p_expected_version then
    raise exception 'stale_ticket_version' using errcode = 'PT409';
  end if;
  if p_readiness_state not in ('processing', 'ready', 'needs_review') then
    raise exception 'invalid_readiness_state' using errcode = '22023';
  end if;
  if p_readiness_state = 'ready' and (
    not p_staff_confirmed
    or (current_ticket.intake_type = 'booked' and current_ticket.prereg_completed_at is null)
    or not current_ticket.all_required_documents_present
    or not current_ticket.all_documents_valid
    or current_ticket.extraction_status <> 'pass'
    or current_ticket.match_status <> 'clean'
  ) then
    raise exception 'readiness_gates_not_satisfied' using errcode = '23514';
  end if;

  update public.queue_entries
  set readiness_state = p_readiness_state,
      readiness_reason = p_reason,
      staff_confirmed = p_staff_confirmed,
      processing_stage = case p_readiness_state
        when 'ready' then 'Waiting to be called'
        when 'needs_review' then 'Assisted review'
        else 'First-pass processing'
      end,
      ready_at = case when p_readiness_state = 'ready' then now() else null end,
      version = version + 1
  where id = p_ticket_id
  returning * into updated_ticket;

  insert into public.operational_events (
    clinic_id, queue_entry_id, event_type, from_state, to_state, reason_code,
    staff_touch, actor_reference
  ) values (
    updated_ticket.clinic_id, updated_ticket.id, 'readiness_changed',
    current_ticket.readiness_state, updated_ticket.readiness_state, p_reason,
    true, p_actor_reference
  );
  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    updated_ticket.clinic_id, p_actor_reference, updated_ticket.patient_id,
    'transition_readiness', 'queue_entries', updated_ticket.id,
    jsonb_build_object('from', current_ticket.readiness_state, 'to', updated_ticket.readiness_state,
      'reason', p_reason, 'version', updated_ticket.version)
  );
  existing_response := to_jsonb(updated_ticket);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('ticket_transition', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_create_walk_in_ticket(
  p_clinic_id text,
  p_patient_name text,
  p_nurse_supervisor text,
  p_clinical_escalation boolean,
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
  new_ticket public.queue_entries%rowtype;
  new_id text;
begin
  perform pg_advisory_xact_lock(hashtextextended('kiosk_check_in:' || p_idempotency_key, 0));
  select response_payload into existing_response
  from public.idempotency_records
  where operation = 'kiosk_check_in' and idempotency_key = p_idempotency_key;
  if existing_response is not null then
    return existing_response;
  end if;

  new_id := 'Q-' || lpad(nextval('public.queue_ticket_number_seq')::text, 3, '0');
  insert into public.queue_entries (
    id, clinic_id, patient_reference, patient_name_snapshot, intake_type, visit_status,
    extraction_status, match_status, readiness_state, readiness_reason, checked_in_at,
    original_ordering_at, queue_number, counter_number, processing_stage,
    clinical_escalation
  ) values (
    new_id, p_clinic_id, 'P-' || substring(new_id from 3), p_patient_name, 'walk_in', 'ongoing',
    'needs_review', 'no_match', 'processing', 'processing', now(), now(), new_id,
    'Kiosk intake', 'Nurse-supervised registration', p_clinical_escalation
  ) returning * into new_ticket;

  insert into public.operational_events (
    clinic_id, queue_entry_id, event_type, to_state, reason_code, staff_touch, actor_reference,
    metadata
  ) values (
    p_clinic_id, new_id, 'ticket_created', 'processing', 'walk_in_check_in', true,
    p_actor_reference, jsonb_build_object('nurse_supervisor', p_nurse_supervisor,
      'clinical_escalation', p_clinical_escalation)
  );
  insert into public.audit_log (
    clinic_id, actor_reference, action_type, target_table, target_id, details
  ) values (
    p_clinic_id, p_actor_reference, 'check_in', 'queue_entries', new_id,
    jsonb_build_object('source', 'supervised_kiosk', 'nurse_supervisor', p_nurse_supervisor)
  );
  existing_response := to_jsonb(new_ticket);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('kiosk_check_in', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_decide_allocation(
  p_recommendation_id text,
  p_expected_version integer,
  p_decision text,
  p_decided_by text,
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
  current_recommendation public.allocation_recommendations%rowtype;
  updated_recommendation public.allocation_recommendations%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('allocation_decision:' || p_idempotency_key, 0));
  select response_payload into existing_response
  from public.idempotency_records
  where operation = 'allocation_decision' and idempotency_key = p_idempotency_key;
  if existing_response is not null then
    return existing_response;
  end if;

  select * into current_recommendation from public.allocation_recommendations
  where id = p_recommendation_id for update;
  if not found then
    raise exception 'recommendation_not_found' using errcode = 'P0002';
  end if;
  if current_recommendation.version <> p_expected_version then
    raise exception 'stale_recommendation_version' using errcode = 'PT409';
  end if;
  if p_decision not in ('approved', 'rejected') then
    raise exception 'invalid_allocation_decision' using errcode = '22023';
  end if;

  update public.allocation_recommendations
  set status = p_decision, decided_by_reference = p_decided_by, decided_at = now(), version = version + 1
  where id = p_recommendation_id
  returning * into updated_recommendation;

  insert into public.operational_events (
    clinic_id, event_type, from_state, to_state, reason_code, staff_touch, actor_reference,
    metadata
  ) values (
    updated_recommendation.clinic_id, 'allocation_decided', current_recommendation.status,
    updated_recommendation.status, p_decision, true, p_actor_reference,
    jsonb_build_object('recommendation_id', p_recommendation_id)
  );
  insert into public.audit_log (
    clinic_id, actor_reference, action_type, target_table, target_id, details
  ) values (
    updated_recommendation.clinic_id, p_actor_reference, 'allocation_decided',
    'allocation_recommendations', p_recommendation_id,
    jsonb_build_object('decision', p_decision, 'version', updated_recommendation.version)
  );
  existing_response := to_jsonb(updated_recommendation);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('allocation_decision', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

alter table public.clinics enable row level security;
alter table public.appointments enable row level security;
alter table public.staff_accounts enable row level security;
alter table public.patient_accounts enable row level security;
alter table public.queue_entries enable row level security;
alter table public.review_cases enable row level security;
alter table public.manual_check_confirmations enable row level security;
alter table public.counter_allocations enable row level security;
alter table public.staff_availability enable row level security;
alter table public.allocation_recommendations enable row level security;
alter table public.operational_events enable row level security;
alter table public.audit_log enable row level security;
alter table public.idempotency_records enable row level security;
alter table public.configuration_releases enable row level security;
alter table public.simulator_snapshots enable row level security;
alter table public.simulator_runs enable row level security;

revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on function public.epicenter_transition_ticket(text, integer, text, text, boolean, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_create_walk_in_ticket(text, text, text, boolean, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_decide_allocation(text, integer, text, text, text, text)
  from public, anon, authenticated;

grant select, insert, update, delete on all tables in schema public to service_role;
grant usage, select on all sequences in schema public to service_role;
grant execute on function public.epicenter_transition_ticket(text, integer, text, text, boolean, text, text)
  to service_role;
grant execute on function public.epicenter_create_walk_in_ticket(text, text, text, boolean, text, text)
  to service_role;
grant execute on function public.epicenter_decide_allocation(text, integer, text, text, text, text)
  to service_role;

comment on table public.queue_entries is
  'One persistent visit ticket. Readiness changes never replace the ticket or reset original_ordering_at.';
comment on table public.idempotency_records is
  'Server-side replay protection for operational mutations.';
comment on table public.simulator_snapshots is
  'Versioned synthetic copies only; simulator code never writes operational tables.';

commit;
