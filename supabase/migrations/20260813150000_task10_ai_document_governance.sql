-- Task 10: bounded document classification metadata and pending-review staging.
-- Apply after 20260813110000_nurse_task_workflow_persistence.sql.

begin;

alter table public.document_jobs
  add column if not exists ticket_id text references public.queue_entries(id),
  add column if not exists data_classification text not null default 'synthetic'
    check (data_classification in ('synthetic', 'formally_deidentified')),
  add column if not exists page_count integer not null default 1 check (page_count between 1 and 100),
  add column if not exists has_letterhead boolean not null default false,
  add column if not exists handwritten boolean not null default false,
  add column if not exists has_table_grid boolean not null default false,
  add column if not exists classification_text text not null default '' check (length(classification_text) <= 2000),
  add column if not exists field_labels jsonb not null default '[]'::jsonb check (jsonb_typeof(field_labels) = 'array'),
  add column if not exists layout_fingerprint text check (length(layout_fingerprint) <= 160);

create index if not exists document_jobs_ticket_id_idx on public.document_jobs (ticket_id)
  where ticket_id is not null;

alter table public.coverage_documents
  add column if not exists classification_metadata jsonb not null default '{}'::jsonb
    check (jsonb_typeof(classification_metadata) = 'object');

create or replace function public.epicenter_stage_document_extraction(
  p_ticket_id text,
  p_document_id text,
  p_classification jsonb,
  p_facts jsonb,
  p_source_evidence jsonb,
  p_actor_reference text,
  p_idempotency_key text
) returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  existing_response jsonb;
  current_ticket public.queue_entries%rowtype;
  updated_document public.coverage_documents%rowtype;
begin
  if coalesce(p_classification->>'review_status', '') <> 'pending_review' then
    raise exception 'classification_must_be_pending_review' using errcode = 'PT422';
  end if;
  if coalesce(p_classification->>'category', '') not in
    ('form', 'authorisation_letter', 'benefit_structure', 'coding_scheme') then
    raise exception 'invalid_document_category' using errcode = 'PT422';
  end if;
  if coalesce(p_classification->>'data_classification', '') not in
    ('synthetic', 'formally_deidentified') then
    raise exception 'unapproved_document_data_classification' using errcode = 'PT422';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('stage_document_extraction:' || p_idempotency_key, 0));
  select response_payload into existing_response
  from public.idempotency_records
  where operation = 'stage_document_extraction' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;

  select * into current_ticket from public.queue_entries
  where id = p_ticket_id and deleted_at is null;
  if not found then raise exception 'ticket_not_found' using errcode = 'PT404'; end if;

  update public.coverage_documents set
    document_category = p_classification->>'category',
    extracted_facts = coalesce(p_facts, '{}'::jsonb),
    field_evidence = coalesce(p_source_evidence, '{}'::jsonb),
    classification_metadata = p_classification,
    review_status = 'pending_review',
    confirmed_by_reference = null,
    confirmed_at = null,
    version = version + 1,
    updated_at = now()
  where id = p_document_id
    and clinic_id = current_ticket.clinic_id
    and deleted_at is null
    and (appointment_id = current_ticket.appointment_id or patient_id = current_ticket.patient_id)
  returning * into updated_document;
  if not found then raise exception 'document_not_found' using errcode = 'PT404'; end if;

  insert into public.operational_events
    (clinic_id, queue_entry_id, event_type, staff_touch, actor_reference, metadata)
  values
    (current_ticket.clinic_id, current_ticket.id, 'document_extraction_staged', false,
     p_actor_reference, jsonb_build_object('document_id', updated_document.id, 'review_status', 'pending_review'));

  insert into public.audit_log
    (clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details)
  values
    (current_ticket.clinic_id, p_actor_reference, current_ticket.patient_id,
     'stage_document_extraction', 'coverage_documents', updated_document.id,
     jsonb_build_object('queue_entry_id', current_ticket.id, 'document_version', updated_document.version,
       'category', p_classification->>'category', 'review_status', 'pending_review'));

  existing_response := to_jsonb(updated_document);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('stage_document_extraction', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

revoke all on function public.epicenter_stage_document_extraction(text, text, jsonb, jsonb, jsonb, text, text)
  from public, anon, authenticated;
grant execute on function public.epicenter_stage_document_extraction(text, text, jsonb, jsonb, jsonb, text, text)
  to service_role;

comment on function public.epicenter_stage_document_extraction(text, text, jsonb, jsonb, jsonb, text, text)
  is 'Stages approved synthetic or formally de-identified extraction facts with evidence as pending_review. Staff confirmation is a separate RPC.';

notify pgrst, 'reload schema';
commit;
