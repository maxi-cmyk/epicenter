begin;

-- Task 6 follow-up: let staff undo a document confirmation made in error, mirroring
-- epicenter_confirm_document but resetting the document back to pending review.
create or replace function public.epicenter_unconfirm_document(
  p_ticket_id text, p_document_id text, p_expected_version integer,
  p_actor_reference text, p_idempotency_key text
) returns jsonb language plpgsql security invoker set search_path = public, pg_temp as $$
declare
  existing_response jsonb;
  current_ticket public.queue_entries%rowtype;
  updated_ticket public.queue_entries%rowtype;
  updated_document public.coverage_documents%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('nurse_document_unconfirm:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'nurse_document_unconfirm' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;
  select * into current_ticket from public.queue_entries
  where id = p_ticket_id and deleted_at is null for update;
  if not found then raise exception 'ticket_not_found' using errcode = 'PT404'; end if;
  if current_ticket.version <> p_expected_version then
    raise exception 'stale_ticket_version' using errcode = 'PT409';
  end if;
  update public.coverage_documents set
    review_status = 'pending_review', confirmed_by_reference = null,
    confirmed_at = null, version = version + 1, updated_at = now()
  where id = p_document_id and clinic_id = current_ticket.clinic_id and deleted_at is null
    and (appointment_id = current_ticket.appointment_id or patient_id = current_ticket.patient_id)
  returning * into updated_document;
  if not found then raise exception 'document_not_found' using errcode = 'PT404'; end if;
  update public.queue_entries set staff_confirmed = true, version = version + 1, updated_at = now()
  where id = p_ticket_id returning * into updated_ticket;
  insert into public.operational_events (clinic_id, queue_entry_id, event_type, staff_touch, actor_reference, metadata)
  values (updated_ticket.clinic_id, updated_ticket.id, 'document_unconfirmed', true, p_actor_reference,
    jsonb_build_object('document_id', updated_document.id, 'version', updated_document.version));
  insert into public.audit_log (clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details)
  values (updated_ticket.clinic_id, p_actor_reference, updated_ticket.patient_id, 'unconfirm_document',
    'coverage_documents', updated_document.id,
    jsonb_build_object('queue_entry_id', updated_ticket.id, 'document_version', updated_document.version,
      'ticket_version', updated_ticket.version));
  existing_response := to_jsonb(updated_ticket);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('nurse_document_unconfirm', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

revoke all on function public.epicenter_unconfirm_document(text, text, integer, text, text) from public, anon, authenticated;
grant execute on function public.epicenter_unconfirm_document(text, text, integer, text, text) to service_role;

notify pgrst, 'reload schema';

commit;
