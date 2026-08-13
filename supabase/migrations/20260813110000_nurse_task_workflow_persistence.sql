begin;

-- Task 6 nurse workflow state lives on the existing visit and coverage records.
alter table public.queue_entries
  add column if not exists matched_package text,
  add column if not exists package_confirmed boolean not null default false,
  add column if not exists package_confirmed_by text,
  add column if not exists package_confirmed_at timestamptz,
  add column if not exists billing_code text,
  add column if not exists uncovered_cost numeric(12, 2),
  add column if not exists billing_confirmed boolean not null default false,
  add column if not exists billing_confirmed_by text,
  add column if not exists billing_confirmed_at timestamptz,
  add column if not exists identity_confirmed boolean not null default false,
  add column if not exists identity_confirmed_by text,
  add column if not exists identity_confirmed_at timestamptz,
  add column if not exists ecard_verified boolean not null default false,
  add column if not exists ecard_not_applicable boolean not null default false,
  add column if not exists ecard_na_reason text,
  add column if not exists is_checkup boolean not null default false,
  add column if not exists forms_confirmed boolean not null default false,
  add column if not exists forms_confirmed_by text,
  add column if not exists forms_confirmed_at timestamptz,
  add column if not exists physical_forms_received boolean not null default false,
  add column if not exists physical_forms_received_by text,
  add column if not exists physical_forms_received_at timestamptz;

alter table public.coverage_documents
  add column if not exists document_category text,
  add column if not exists reference_number text;

update public.coverage_documents
set document_category = case
  when lower(document_type) like '%form%' then 'form'
  when lower(document_type) like '%authori%' or lower(document_type) like '%letter%' then 'authorisation_letter'
  when lower(document_type) like '%code%' then 'coding_scheme'
  else 'benefit_structure'
end
where document_category is null;

alter table public.coverage_documents alter column document_category set default 'benefit_structure';
alter table public.coverage_documents alter column document_category set not null;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'queue_entries_uncovered_cost_nonnegative') then
    alter table public.queue_entries add constraint queue_entries_uncovered_cost_nonnegative
      check (uncovered_cost is null or uncovered_cost >= 0);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'queue_entries_ecard_state_valid') then
    alter table public.queue_entries add constraint queue_entries_ecard_state_valid
      check (not (ecard_verified and ecard_not_applicable));
  end if;
  if not exists (select 1 from pg_constraint where conname = 'coverage_documents_category_valid') then
    alter table public.coverage_documents add constraint coverage_documents_category_valid
      check (document_category in ('form', 'authorisation_letter', 'benefit_structure', 'coding_scheme'));
  end if;
end;
$$;

-- Preserve the eligibility result already calculated by the project seed.
with derived as (
  select distinct on (m.appointment_id)
    m.appointment_id, r.package_name, r.package_or_checkup_code as billing_code
  from public.eligibility_matches m
  join public.eligibility_rules r on r.id = m.matched_rule_id
  where m.deleted_at is null and r.deleted_at is null
  order by m.appointment_id, m.updated_at desc
)
update public.queue_entries q
set matched_package = coalesce(q.matched_package, derived.package_name),
    billing_code = coalesce(q.billing_code, derived.billing_code)
from derived
where q.appointment_id = derived.appointment_id
  and (q.matched_package is null or q.billing_code is null);

create or replace function public.epicenter_apply_nurse_step(
  p_operation text,
  p_step text,
  p_ticket_id text,
  p_expected_version integer,
  p_text_value text,
  p_numeric_value numeric,
  p_boolean_value boolean,
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
begin
  perform pg_advisory_xact_lock(hashtextextended(p_operation || ':' || p_idempotency_key, 0));
  select response_payload into existing_response
  from public.idempotency_records
  where operation = p_operation and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;

  select * into current_ticket from public.queue_entries
  where id = p_ticket_id and deleted_at is null for update;
  if not found then raise exception 'ticket_not_found' using errcode = 'PT404'; end if;
  if current_ticket.version <> p_expected_version then
    raise exception 'stale_ticket_version' using errcode = 'PT409';
  end if;
  if p_step not in ('identity', 'forms', 'package', 'billing', 'physical_forms') then
    raise exception 'invalid_nurse_step' using errcode = 'PT422';
  end if;
  if p_step = 'package' and nullif(btrim(coalesce(p_text_value, current_ticket.matched_package)), '') is null then
    raise exception 'package_required' using errcode = 'PT422';
  end if;
  if p_step = 'billing' and p_numeric_value is not null and p_numeric_value < 0 then
    raise exception 'invalid_uncovered_cost' using errcode = 'PT422';
  end if;

  update public.queue_entries set
    identity_confirmed = case when p_step = 'identity' then true else identity_confirmed end,
    identity_confirmed_by = case when p_step = 'identity' then p_actor_reference else identity_confirmed_by end,
    identity_confirmed_at = case when p_step = 'identity' then now() else identity_confirmed_at end,
    ecard_not_applicable = case when p_step = 'identity' then coalesce(p_boolean_value, false) else ecard_not_applicable end,
    ecard_verified = case when p_step = 'identity' then not coalesce(p_boolean_value, false) else ecard_verified end,
    ecard_na_reason = case when p_step = 'identity' then case when p_boolean_value then p_reason else null end else ecard_na_reason end,
    forms_confirmed = case when p_step = 'forms' then true else forms_confirmed end,
    forms_confirmed_by = case when p_step = 'forms' then p_actor_reference else forms_confirmed_by end,
    forms_confirmed_at = case when p_step = 'forms' then now() else forms_confirmed_at end,
    matched_package = case when p_step = 'package' then coalesce(nullif(btrim(p_text_value), ''), matched_package) else matched_package end,
    package_confirmed = case when p_step = 'package' then true else package_confirmed end,
    package_confirmed_by = case when p_step = 'package' then p_actor_reference else package_confirmed_by end,
    package_confirmed_at = case when p_step = 'package' then now() else package_confirmed_at end,
    billing_code = case when p_step = 'billing' then coalesce(nullif(btrim(p_text_value), ''), billing_code) else billing_code end,
    uncovered_cost = case when p_step = 'billing' then coalesce(p_numeric_value, uncovered_cost) else uncovered_cost end,
    queue_number = case when p_step = 'billing' then coalesce(nullif(btrim(p_reason), ''), queue_number) else queue_number end,
    billing_confirmed = case when p_step = 'billing' then true else billing_confirmed end,
    billing_confirmed_by = case when p_step = 'billing' then p_actor_reference else billing_confirmed_by end,
    billing_confirmed_at = case when p_step = 'billing' then now() else billing_confirmed_at end,
    physical_forms_received = case when p_step = 'physical_forms' then true else physical_forms_received end,
    physical_forms_received_by = case when p_step = 'physical_forms' then p_actor_reference else physical_forms_received_by end,
    physical_forms_received_at = case when p_step = 'physical_forms' then now() else physical_forms_received_at end,
    staff_confirmed = true,
    version = version + 1,
    updated_at = now()
  where id = p_ticket_id returning * into updated_ticket;

  insert into public.operational_events (
    clinic_id, queue_entry_id, event_type, staff_touch, actor_reference, metadata
  ) values (
    updated_ticket.clinic_id, updated_ticket.id, p_step || '_confirmed', true, p_actor_reference,
    jsonb_build_object('step', p_step, 'version', updated_ticket.version)
  );
  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    updated_ticket.clinic_id, p_actor_reference, updated_ticket.patient_id,
    'confirm_' || p_step, 'queue_entries', updated_ticket.id,
    jsonb_build_object('step', p_step, 'version', updated_ticket.version)
  );
  existing_response := to_jsonb(updated_ticket);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values (p_operation, p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

create or replace function public.epicenter_confirm_identity(
  p_ticket_id text, p_expected_version integer, p_ecard_not_applicable boolean,
  p_ecard_na_reason text, p_actor_reference text, p_idempotency_key text
) returns jsonb language sql security invoker set search_path = public, pg_temp as $$
  select public.epicenter_apply_nurse_step('nurse_identity_confirm', 'identity', p_ticket_id,
    p_expected_version, null, null, p_ecard_not_applicable, p_ecard_na_reason, p_actor_reference, p_idempotency_key);
$$;

create or replace function public.epicenter_confirm_forms(
  p_ticket_id text, p_expected_version integer, p_actor_reference text, p_idempotency_key text
) returns jsonb language sql security invoker set search_path = public, pg_temp as $$
  select public.epicenter_apply_nurse_step('nurse_forms_confirm', 'forms', p_ticket_id,
    p_expected_version, null, null, null, null, p_actor_reference, p_idempotency_key);
$$;

create or replace function public.epicenter_confirm_package(
  p_ticket_id text, p_expected_version integer, p_corrected_package text,
  p_actor_reference text, p_idempotency_key text
) returns jsonb language sql security invoker set search_path = public, pg_temp as $$
  select public.epicenter_apply_nurse_step('nurse_package_confirm', 'package', p_ticket_id,
    p_expected_version, p_corrected_package, null, null, null, p_actor_reference, p_idempotency_key);
$$;

create or replace function public.epicenter_confirm_billing(
  p_ticket_id text, p_expected_version integer, p_corrected_billing_code text,
  p_corrected_uncovered_cost numeric, p_corrected_queue_number text,
  p_actor_reference text, p_idempotency_key text
) returns jsonb language sql security invoker set search_path = public, pg_temp as $$
  select public.epicenter_apply_nurse_step('nurse_billing_confirm', 'billing', p_ticket_id,
    p_expected_version, p_corrected_billing_code, p_corrected_uncovered_cost, null,
    p_corrected_queue_number, p_actor_reference, p_idempotency_key);
$$;

create or replace function public.epicenter_mark_physical_forms_received(
  p_ticket_id text, p_expected_version integer, p_actor_reference text, p_idempotency_key text
) returns jsonb language sql security invoker set search_path = public, pg_temp as $$
  select public.epicenter_apply_nurse_step('nurse_physical_forms_received', 'physical_forms', p_ticket_id,
    p_expected_version, null, null, null, null, p_actor_reference, p_idempotency_key);
$$;

create or replace function public.epicenter_confirm_document(
  p_ticket_id text, p_document_id text, p_expected_version integer, p_facts jsonb,
  p_reference_number text, p_valid_from date, p_valid_to date,
  p_actor_reference text, p_idempotency_key text
) returns jsonb language plpgsql security invoker set search_path = public, pg_temp as $$
declare
  existing_response jsonb;
  current_ticket public.queue_entries%rowtype;
  updated_ticket public.queue_entries%rowtype;
  updated_document public.coverage_documents%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('nurse_document_confirm:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'nurse_document_confirm' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;
  select * into current_ticket from public.queue_entries
  where id = p_ticket_id and deleted_at is null for update;
  if not found then raise exception 'ticket_not_found' using errcode = 'PT404'; end if;
  if current_ticket.version <> p_expected_version then
    raise exception 'stale_ticket_version' using errcode = 'PT409';
  end if;
  if p_valid_from is not null and p_valid_to is not null and p_valid_to < p_valid_from then
    raise exception 'invalid_document_validity' using errcode = 'PT422';
  end if;
  update public.coverage_documents set
    extracted_facts = coalesce(p_facts, extracted_facts),
    reference_number = coalesce(nullif(btrim(p_reference_number), ''), reference_number),
    validity_start = coalesce(p_valid_from, validity_start),
    validity_end = coalesce(p_valid_to, validity_end),
    review_status = 'confirmed', confirmed_by_reference = p_actor_reference,
    confirmed_at = now(), version = version + 1, updated_at = now()
  where id = p_document_id and clinic_id = current_ticket.clinic_id and deleted_at is null
    and (appointment_id = current_ticket.appointment_id or patient_id = current_ticket.patient_id)
  returning * into updated_document;
  if not found then raise exception 'document_not_found' using errcode = 'PT404'; end if;
  update public.queue_entries set staff_confirmed = true, version = version + 1, updated_at = now()
  where id = p_ticket_id returning * into updated_ticket;
  insert into public.operational_events (clinic_id, queue_entry_id, event_type, staff_touch, actor_reference, metadata)
  values (updated_ticket.clinic_id, updated_ticket.id, 'document_confirmed', true, p_actor_reference,
    jsonb_build_object('document_id', updated_document.id, 'version', updated_document.version));
  insert into public.audit_log (clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details)
  values (updated_ticket.clinic_id, p_actor_reference, updated_ticket.patient_id, 'confirm_document',
    'coverage_documents', updated_document.id,
    jsonb_build_object('queue_entry_id', updated_ticket.id, 'document_version', updated_document.version,
      'ticket_version', updated_ticket.version));
  existing_response := to_jsonb(updated_ticket);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('nurse_document_confirm', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

revoke all on function public.epicenter_apply_nurse_step(text, text, text, integer, text, numeric, boolean, text, text, text) from public, anon, authenticated;
revoke all on function public.epicenter_confirm_identity(text, integer, boolean, text, text, text) from public, anon, authenticated;
revoke all on function public.epicenter_confirm_forms(text, integer, text, text) from public, anon, authenticated;
revoke all on function public.epicenter_confirm_package(text, integer, text, text, text) from public, anon, authenticated;
revoke all on function public.epicenter_confirm_billing(text, integer, text, numeric, text, text, text) from public, anon, authenticated;
revoke all on function public.epicenter_mark_physical_forms_received(text, integer, text, text) from public, anon, authenticated;
revoke all on function public.epicenter_confirm_document(text, text, integer, jsonb, text, date, date, text, text) from public, anon, authenticated;

grant execute on function public.epicenter_apply_nurse_step(text, text, text, integer, text, numeric, boolean, text, text, text) to service_role;
grant execute on function public.epicenter_confirm_identity(text, integer, boolean, text, text, text) to service_role;
grant execute on function public.epicenter_confirm_forms(text, integer, text, text) to service_role;
grant execute on function public.epicenter_confirm_package(text, integer, text, text, text) to service_role;
grant execute on function public.epicenter_confirm_billing(text, integer, text, numeric, text, text, text) to service_role;
grant execute on function public.epicenter_mark_physical_forms_received(text, integer, text, text) to service_role;
grant execute on function public.epicenter_confirm_document(text, text, integer, jsonb, text, date, date, text, text) to service_role;

comment on function public.epicenter_apply_nurse_step(text, text, text, integer, text, numeric, boolean, text, text, text)
  is 'Internal atomic Task 6 mutation helper. Service-role only; every change appends operational and audit records.';

notify pgrst, 'reload schema';

commit;

-- Optional verification after running this file in the Supabase SQL editor:
-- select column_name from information_schema.columns
-- where table_schema = 'public' and table_name = 'queue_entries'
--   and column_name in ('identity_confirmed', 'forms_confirmed', 'package_confirmed', 'billing_confirmed');
-- select routine_name from information_schema.routines
-- where routine_schema = 'public' and routine_name like 'epicenter_%confirm%';
