-- Patient home / queue / payment / records persistence for signed-in Clerk patients.
begin;

create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  clinic_id text not null references public.clinics(id),
  patient_id bigint not null references public.patients(id) on delete restrict,
  appointment_id text not null references public.appointments(id) on delete restrict,
  appointment_reference text not null,
  package_label text not null default 'WELL2 — Comprehensive Screen',
  amount_covered text not null default '$180.00',
  amount_patient_payable text not null default '$35.00',
  status text not null default 'not_ready'
    check (status in ('not_ready', 'ready', 'mock_processing', 'mocked_paid', 'mock_failed')),
  mock_failure_reason text,
  mock_receipt_reference text,
  paid_at timestamptz,
  version integer not null default 1 check (version > 0),
  is_synthetic boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (appointment_id)
);
create index if not exists payments_patient_id_idx on public.payments (patient_id, created_at desc);
create index if not exists payments_appointment_reference_idx
  on public.payments (appointment_reference);

create trigger payments_set_updated_at
  before update on public.payments
  for each row execute function private.set_updated_at();

alter table public.payments enable row level security;
revoke all on table public.payments from anon, authenticated;
grant select, insert, update, delete on table public.payments to service_role;

-- Historical GP visit for the seeded demo patient (records screen).
insert into public.appointments (
  id, appointment_reference, clinic_id, patient_id, scheduled_at,
  appointment_type, questionnaire_type, administrative_urgency, status
)
values (
  'appointment_history_001',
  'APT-HISTORY-001',
  'clinic_harbourfront',
  (select id from public.patients
    where identifier_hash = '4e487c99807bebe1c81bf3cded10ceb92f1c8d3ed0d48cbe822ad578a45854b5'),
  '2026-02-03 09:30:00+00',
  'gp_consultation',
  'general_health',
  false,
  'completed'
)
on conflict (id) do update set
  appointment_reference = excluded.appointment_reference,
  patient_id = excluded.patient_id,
  scheduled_at = excluded.scheduled_at,
  appointment_type = excluded.appointment_type,
  status = excluded.status,
  deleted_at = null;

insert into public.payments (
  clinic_id, patient_id, appointment_id, appointment_reference,
  package_label, amount_covered, amount_patient_payable, status
)
select
  'clinic_harbourfront',
  a.patient_id,
  a.id,
  a.appointment_reference,
  'WELL2 — Comprehensive Screen',
  '$180.00',
  '$35.00',
  case
    when coalesce(q.patient_outcome, '') = 'accepted' then 'ready'
    else 'not_ready'
  end
from public.appointments a
left join public.queue_entries q
  on q.appointment_id = a.id and q.deleted_at is null
where a.appointment_reference = 'APT-DEMO-014'
  and a.patient_id is not null
  and a.deleted_at is null
on conflict (appointment_id) do update set
  patient_id = excluded.patient_id,
  appointment_reference = excluded.appointment_reference,
  package_label = excluded.package_label,
  amount_covered = excluded.amount_covered,
  amount_patient_payable = excluded.amount_patient_payable,
  status = case
    when public.payments.status in ('mocked_paid', 'mock_failed', 'mock_processing')
      then public.payments.status
    else excluded.status
  end;

create or replace function private.epicenter_payment_payload(p public.payments)
returns jsonb
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select jsonb_build_object(
    'synthetic', true,
    'mocked', true,
    'appointment_id', p.appointment_reference,
    'package_label', p.package_label,
    'amount_covered', p.amount_covered,
    'amount_patient_payable', p.amount_patient_payable,
    'status', p.status,
    'status_detail', case p.status
      when 'not_ready' then 'Staff are still finalising billing for this visit.'
      when 'ready' then 'Demo payment is ready. No live gateway is used.'
      when 'mock_processing' then 'Recording the demo payment…'
      when 'mocked_paid' then 'Demo payment recorded. Download remains local to this demo.'
      when 'mock_failed' then coalesce(
        p.mock_failure_reason,
        'The demo payment could not be recorded. Try again.'
      )
      else 'Payment status unavailable.'
    end,
    'receipt_reference', p.mock_receipt_reference,
    'paid_at', p.paid_at,
    'failure_reason', p.mock_failure_reason,
    'version', p.version
  );
$$;

create or replace function private.epicenter_ensure_payment_for_appointment(
  p_patient_id bigint,
  p_appointment public.appointments
)
returns public.payments
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  payment_row public.payments%rowtype;
  queue_row public.queue_entries%rowtype;
  initial_status text := 'not_ready';
begin
  select * into payment_row from public.payments
  where appointment_id = p_appointment.id
  for update;
  if found then
    return payment_row;
  end if;

  select * into queue_row from public.queue_entries
  where appointment_id = p_appointment.id and deleted_at is null
  limit 1;
  if found and coalesce(queue_row.patient_outcome, '') = 'accepted' then
    initial_status := 'ready';
  end if;

  insert into public.payments (
    clinic_id, patient_id, appointment_id, appointment_reference, status
  ) values (
    p_appointment.clinic_id,
    p_patient_id,
    p_appointment.id,
    p_appointment.appointment_reference,
    initial_status
  )
  on conflict (appointment_id) do update
    set patient_id = excluded.patient_id
  returning * into payment_row;
  return payment_row;
end;
$$;

create or replace function public.epicenter_get_patient_home(p_patient_id bigint)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  patient_row public.patients%rowtype;
  appointment_row public.appointments%rowtype;
  clinic_row public.clinics%rowtype;
  queue_row public.queue_entries%rowtype;
  payment_row public.payments%rowtype;
  onboarding_row public.patient_onboarding_states%rowtype;
  questionnaire_row public.appointment_questionnaire_responses%rowtype;
  notification_row public.patient_notifications%rowtype;
  coverage_count integer := 0;
  coverage_status text := 'not_started';
  coverage_summary text := 'Coverage document still needed';
  questionnaire_status text := 'not_started';
  questionnaire_summary text := 'General health questionnaire not started';
  payment_status text := 'not_ready';
  payment_summary text := 'Not ready — staff still finalising billing';
  primary_action text := 'confirm_coverage';
  primary_label text := 'Confirm coverage for this visit';
  primary_href text := '/coverage';
  queue_summary text := 'Available after staff check-in';
  outcome_value text := null;
  outcome_message text := null;
  recent_visit text := null;
  notification_payload jsonb := null;
  appointment_payload jsonb := null;
begin
  if p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select * into patient_row from public.patients
  where id = p_patient_id and deleted_at is null;
  if not found then
    raise exception 'patient_not_found' using errcode = 'PT404';
  end if;

  select * into appointment_row from public.appointments
  where patient_id = p_patient_id
    and deleted_at is null
    and status in ('booked', 'checked_in')
  order by scheduled_at asc
  limit 1;

  if found then
    select * into clinic_row from public.clinics where id = appointment_row.clinic_id;
    appointment_payload := jsonb_build_object(
      'appointment_id', appointment_row.appointment_reference,
      'scheduled_at', appointment_row.scheduled_at,
      'clinic_name', coalesce(clinic_row.name, appointment_row.clinic_id),
      'location', coalesce(clinic_row.name, 'Clinic'),
      'appointment_type', appointment_row.appointment_type,
      'questionnaire_type', coalesce(appointment_row.questionnaire_type, 'general_health')
    );

    select * into queue_row from public.queue_entries
    where appointment_id = appointment_row.id and deleted_at is null
    limit 1;
    if found then
      outcome_value := queue_row.patient_outcome;
      outcome_message := queue_row.patient_next_action;
      if queue_row.checked_in_at is not null or queue_row.visit_status <> 'incoming' then
        queue_summary := format('Ticket %s · %s', queue_row.id, initcap(queue_row.visit_status));
      else
        queue_summary := format('Ticket %s reserved — status after check-in', queue_row.id);
      end if;
    end if;

    payment_row := private.epicenter_ensure_payment_for_appointment(p_patient_id, appointment_row);
    payment_status := payment_row.status;
    payment_summary := case payment_row.status
      when 'not_ready' then 'Not ready — staff still finalising billing'
      when 'ready' then 'Demo payment ready'
      when 'mock_processing' then 'Demo payment processing'
      when 'mocked_paid' then 'Demo payment recorded'
      when 'mock_failed' then 'Demo payment failed — retry available'
      else 'Payment status unavailable'
    end;

    select * into questionnaire_row from public.appointment_questionnaire_responses
    where appointment_id = appointment_row.id
      and patient_id = p_patient_id
    limit 1;
    if found then
      questionnaire_status := questionnaire_row.status;
    elsif appointment_row.questionnaire_type is null then
      questionnaire_status := 'not_required';
    end if;
  end if;

  select * into onboarding_row from public.patient_onboarding_states
  where patient_id = p_patient_id
  order by updated_at desc
  limit 1;

  select count(*) into coverage_count from public.coverage_documents
  where patient_id = p_patient_id and deleted_at is null;

  select * into notification_row from public.patient_notifications
  where patient_id = p_patient_id
    and patient_action = 'none'
  order by sent_at desc
  limit 1;
  if found then
    coverage_status := 'action_required';
    coverage_summary := case notification_row.category
      when 'document_unclear' then 'Please upload a clearer coverage document'
      when 'document_incomplete' then 'Your coverage document is incomplete'
      when 'document_expired' then 'Your coverage document has expired'
      else 'Please upload a current coverage document'
    end;
    notification_payload := jsonb_build_object(
      'category', notification_row.category,
      'message', coverage_summary,
      'next_action', 'Upload a replacement coverage document'
    );
  elsif coverage_count > 0 or coalesce(onboarding_row.insurance_completed, false) then
    coverage_status := 'submitted';
    coverage_summary := 'Coverage received for staff confirmation';
  elsif coverage_count = 0 and exists (
    select 1 from public.coverage_documents cd
    where cd.patient_id = p_patient_id and cd.deleted_at is null
  ) then
    coverage_status := 'check_first';
    coverage_summary := 'Prior coverage on file — confirm or replace';
  else
    coverage_status := 'not_started';
    coverage_summary := 'Coverage document still needed';
  end if;

  if questionnaire_status = 'not_required' then
    questionnaire_summary := 'No questionnaire required';
  elsif coalesce(onboarding_row.questionnaire_completed, false)
     or questionnaire_status = 'submitted' then
    questionnaire_status := 'submitted';
    questionnaire_summary := 'Questionnaire submitted';
  elsif questionnaire_status = 'draft' then
    questionnaire_summary := 'Questionnaire draft saved — finish and submit';
  else
    questionnaire_status := 'not_started';
    questionnaire_summary := 'General health questionnaire not started';
  end if;

  if coverage_status in ('not_started', 'check_first', 'action_required') then
    primary_action := 'confirm_coverage';
    primary_label := 'Confirm coverage for this visit';
    primary_href := '/coverage';
  elsif questionnaire_status not in ('submitted', 'not_required') then
    primary_action := 'complete_questionnaire';
    primary_label := 'Complete the required questionnaire';
    primary_href := '/questionnaire';
  elsif payment_status in ('ready', 'mock_failed') then
    primary_action := 'pay';
    primary_label := case when payment_status = 'mock_failed'
      then 'Retry demo payment' else 'Complete demo payment' end;
    primary_href := '/payment';
  elsif outcome_value = 'under_review' then
    primary_action := 'wait_for_review';
    primary_label := 'See your current status';
    primary_href := '/queue';
  else
    primary_action := 'view_queue';
    primary_label := 'View queue status';
    primary_href := '/queue';
  end if;

  select format(
    '%s · %s',
    to_char(a.scheduled_at at time zone 'Asia/Singapore', 'DD Mon YYYY'),
    replace(initcap(replace(a.appointment_type, '_', ' ')), 'Gp', 'GP')
  )
  into recent_visit
  from public.appointments a
  where a.patient_id = p_patient_id
    and a.deleted_at is null
    and a.status = 'completed'
  order by a.scheduled_at desc
  limit 1;

  return jsonb_build_object(
    'synthetic', true,
    'patient_display_name', patient_row.full_name,
    'appointment', appointment_payload,
    'coverage_status', coverage_status,
    'coverage_summary', coverage_summary,
    'questionnaire_status', questionnaire_status,
    'queue_summary', queue_summary,
    'payment_status', payment_status,
    'payment_summary', payment_summary,
    'primary_action', primary_action,
    'primary_action_label', primary_label,
    'primary_action_href', primary_href,
    'outcome', outcome_value,
    'outcome_message', outcome_message,
    'notification', notification_payload,
    'recent_visit_summary', recent_visit
  );
end;
$$;

create or replace function public.epicenter_get_patient_queue(p_patient_id bigint)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  queue_row public.queue_entries%rowtype;
  payment_row public.payments%rowtype;
  patients_ahead integer := 0;
  available boolean := false;
  status_label text := 'Before check-in';
  status_detail text := 'Queue status will appear after staff check-in.';
  counter_label text := null;
begin
  if p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select * into queue_row from public.queue_entries
  where patient_id = p_patient_id
    and deleted_at is null
    and visit_status in ('incoming', 'ongoing')
  order by
    case when visit_status = 'ongoing' then 0 else 1 end,
    coalesce(checked_in_at, original_ordering_at) desc
  limit 1;

  if not found then
    select * into queue_row from public.queue_entries
    where patient_id = p_patient_id and deleted_at is null
    order by coalesce(completed_at, updated_at) desc
    limit 1;
  end if;

  if not found then
    return jsonb_build_object(
      'synthetic', true,
      'available', false,
      'ticket_id', null,
      'visit_phase', null,
      'status_label', 'No active ticket',
      'status_detail', 'Your queue ticket will appear once the clinic opens your visit.',
      'counter_label', null,
      'patients_ahead', null,
      'updated_at', now(),
      'stale', false,
      'payment_ready', false
    );
  end if;

  counter_label := coalesce(queue_row.counter_number, queue_row.expected_counter_number);
  available := queue_row.checked_in_at is not null or queue_row.visit_status <> 'incoming';

  if available then
    if queue_row.readiness_state = 'needs_review' then
      status_label := 'Additional review needed';
      status_detail := 'A staff member is reviewing your registration.';
    elsif queue_row.readiness_state = 'processing' then
      status_label := 'Processing';
      status_detail := 'We are checking your registration details.';
    elsif queue_row.visit_status = 'finished' then
      status_label := 'Finished';
      status_detail := 'Your visit is complete.';
    else
      status_label := 'Waiting';
      status_detail := 'Waiting to be called. Keep this ticket — you will not take another number.';
    end if;

    select count(*) into patients_ahead
    from public.queue_entries other
    where other.clinic_id = queue_row.clinic_id
      and other.deleted_at is null
      and other.visit_status = 'ongoing'
      and other.id <> queue_row.id
      and coalesce(other.checked_in_at, other.original_ordering_at)
        < coalesce(queue_row.checked_in_at, queue_row.original_ordering_at);
  end if;

  if queue_row.appointment_id is not null then
    select * into payment_row from public.payments
    where appointment_id = queue_row.appointment_id;
  end if;

  return jsonb_build_object(
    'synthetic', true,
    'available', available,
    'ticket_id', queue_row.id,
    'visit_phase', queue_row.visit_status,
    'status_label', status_label,
    'status_detail', status_detail,
    'counter_label', counter_label,
    'patients_ahead', case when available then patients_ahead else null end,
    'updated_at', queue_row.updated_at,
    'stale', false,
    'payment_ready', coalesce(payment_row.status, 'not_ready')
      in ('ready', 'mocked_paid', 'mock_failed')
  );
end;
$$;

create or replace function public.epicenter_get_patient_payment(p_patient_id bigint)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  appointment_row public.appointments%rowtype;
  payment_row public.payments%rowtype;
begin
  if p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select * into appointment_row from public.appointments
  where patient_id = p_patient_id
    and deleted_at is null
    and status in ('booked', 'checked_in', 'completed')
  order by
    case when status in ('booked', 'checked_in') then 0 else 1 end,
    scheduled_at desc
  limit 1;
  if not found then
    raise exception 'appointment_not_found' using errcode = 'PT404';
  end if;

  payment_row := private.epicenter_ensure_payment_for_appointment(p_patient_id, appointment_row);
  return private.epicenter_payment_payload(payment_row);
end;
$$;

create or replace function public.epicenter_submit_mock_payment(
  p_patient_id bigint,
  p_appointment_reference text,
  p_expected_version integer,
  p_idempotency_key text,
  p_actor_reference text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  appointment_row public.appointments%rowtype;
  payment_row public.payments%rowtype;
  fail_demo boolean;
begin
  perform pg_advisory_xact_lock(hashtextextended('mock_payment:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'mock_payment' and idempotency_key = p_idempotency_key;
  if existing_response is not null then
    return existing_response;
  end if;

  if p_patient_id is null or nullif(trim(p_appointment_reference), '') is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select * into appointment_row from public.appointments
  where appointment_reference = p_appointment_reference
    and patient_id = p_patient_id
    and deleted_at is null;
  if not found then
    raise exception 'appointment_not_found' using errcode = 'PT404';
  end if;

  payment_row := private.epicenter_ensure_payment_for_appointment(p_patient_id, appointment_row);
  select * into payment_row from public.payments where id = payment_row.id for update;

  if payment_row.version <> p_expected_version then
    raise exception 'payment_version_conflict' using errcode = 'PT409';
  end if;
  if payment_row.status = 'mocked_paid' then
    existing_response := private.epicenter_payment_payload(payment_row);
    insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
    values ('mock_payment', p_idempotency_key, p_actor_reference, existing_response);
    return existing_response;
  end if;
  if payment_row.status = 'not_ready' then
    raise exception 'payment_not_ready' using errcode = 'PT409';
  end if;

  fail_demo := lower(p_idempotency_key) like '%fail';
  if fail_demo then
    update public.payments set
      status = 'mock_failed',
      mock_failure_reason = 'Demo payment provider returned a recoverable failure.',
      mock_receipt_reference = null,
      paid_at = null,
      version = version + 1
    where id = payment_row.id
    returning * into payment_row;
  else
    update public.payments set
      status = 'mocked_paid',
      mock_failure_reason = null,
      mock_receipt_reference = 'MOCK-' || upper(substr(md5(p_idempotency_key), 1, 10)),
      paid_at = now(),
      version = version + 1
    where id = payment_row.id
    returning * into payment_row;
  end if;

  existing_response := private.epicenter_payment_payload(payment_row);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('mock_payment', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_get_patient_records(p_patient_id bigint)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  visits jsonb := '[]'::jsonb;
begin
  if p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select coalesce(jsonb_agg(ranked.visit_row order by ranked.sort_at desc), '[]'::jsonb)
  into visits
  from (
    select jsonb_build_object(
      'appointment_id', a.appointment_reference,
      'visited_on', (a.scheduled_at at time zone 'Asia/Singapore')::date,
      'visit_label', replace(initcap(replace(a.appointment_type, '_', ' ')), 'Gp', 'GP'),
      'package_label', pay.package_label,
      'coverage_label', cov.issuer_name,
      'questionnaire_summary', case
        when q.status = 'submitted' then 'General health · Submitted'
        when q.status = 'draft' then 'General health · Draft'
        when a.questionnaire_type is null then null
        else 'General health · Pending'
      end,
      'outcome', coalesce(qe.patient_outcome, sub.outcome)
    ) as visit_row,
    a.scheduled_at as sort_at
    from public.appointments a
    left join lateral (
      select p.package_label from public.payments p
      where p.appointment_id = a.id
      limit 1
    ) pay on true
    left join lateral (
      select cd.issuer_name from public.coverage_documents cd
      where cd.patient_id = a.patient_id
        and cd.deleted_at is null
        and (cd.appointment_id = a.id or cd.appointment_id is null)
      order by cd.created_at desc
      limit 1
    ) cov on true
    left join lateral (
      select aq.status from public.appointment_questionnaire_responses aq
      where aq.appointment_id = a.id
        and aq.patient_id = a.patient_id
      limit 1
    ) q on true
    left join lateral (
      select qe.patient_outcome from public.queue_entries qe
      where qe.appointment_id = a.id and qe.deleted_at is null
      limit 1
    ) qe on true
    left join lateral (
      select ps.outcome from public.patient_submissions ps
      where ps.appointment_id = a.id
        and ps.patient_id = a.patient_id
        and ps.deleted_at is null
      order by ps.created_at desc
      limit 1
    ) sub on true
    where a.patient_id = p_patient_id
      and a.deleted_at is null
  ) ranked;

  return jsonb_build_object(
    'synthetic', true,
    'visits', visits
  );
end;
$$;

revoke all on function public.epicenter_get_patient_home(bigint) from public, anon, authenticated;
revoke all on function public.epicenter_get_patient_queue(bigint) from public, anon, authenticated;
revoke all on function public.epicenter_get_patient_payment(bigint) from public, anon, authenticated;
revoke all on function public.epicenter_submit_mock_payment(bigint, text, integer, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_get_patient_records(bigint) from public, anon, authenticated;

grant execute on function public.epicenter_get_patient_home(bigint) to service_role;
grant execute on function public.epicenter_get_patient_queue(bigint) to service_role;
grant execute on function public.epicenter_get_patient_payment(bigint) to service_role;
grant execute on function public.epicenter_submit_mock_payment(bigint, text, integer, text, text)
  to service_role;
grant execute on function public.epicenter_get_patient_records(bigint) to service_role;

comment on table public.payments is
  'Patient-facing mock payment state for a visit. Status values keep the demo boundary visible.';
comment on function public.epicenter_get_patient_home(bigint) is
  'Patient-safe home summary assembled from appointments, queue, coverage, questionnaire, and payments.';
comment on function public.epicenter_get_patient_queue(bigint) is
  'Patient-safe queue projection for the signed-in patient only.';
comment on function public.epicenter_get_patient_payment(bigint) is
  'Mock payment summary for the patient''s current or latest visit.';
comment on function public.epicenter_submit_mock_payment(bigint, text, integer, text, text) is
  'Idempotent demo payment mutation scoped to the patient appointment.';
comment on function public.epicenter_get_patient_records(bigint) is
  'Visit history for the signed-in patient assembled from appointments and related facts.';

commit;
