-- Fast/slow registration counters are labelled F1–F2 and S1–S4.
-- Walk-ins and incomplete pre-registration go to a slow counter.

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
  assigned_counter text;
  lane_pool text[];
begin
  perform pg_advisory_xact_lock(hashtextextended('kiosk_check_in:' || p_idempotency_key, 0));
  select response_payload into existing_response
  from public.idempotency_records
  where operation = 'kiosk_check_in' and idempotency_key = p_idempotency_key;
  if existing_response is not null then
    return existing_response;
  end if;

  lane_pool := array['S1', 'S2', 'S3', 'S4'];
  select lane into assigned_counter
  from unnest(lane_pool) as lane
  left join public.queue_entries q
    on q.clinic_id = p_clinic_id
    and q.deleted_at is null
    and q.visit_status = 'ongoing'
    and coalesce(q.counter_number, q.expected_counter_number) = lane
  group by lane
  order by count(q.id), lane
  limit 1;
  assigned_counter := coalesce(assigned_counter, lane_pool[1]);

  new_id := 'Q-' || lpad(nextval('public.queue_ticket_number_seq')::text, 3, '0');
  insert into public.queue_entries (
    id, clinic_id, patient_reference, patient_name_snapshot, intake_type, visit_status,
    extraction_status, match_status, readiness_state, readiness_reason, checked_in_at,
    original_ordering_at, queue_number, counter_number, processing_stage,
    clinical_escalation
  ) values (
    new_id, p_clinic_id, 'P-' || substring(new_id from 3), p_patient_name, 'walk_in', 'ongoing',
    'needs_review', 'no_match', 'processing', 'processing', now(), now(), new_id,
    assigned_counter, 'Nurse-supervised registration', p_clinical_escalation
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
    jsonb_build_object('source', 'supervised_kiosk', 'nurse_supervisor', p_nurse_supervisor,
      'counter_number', assigned_counter)
  );
  existing_response := to_jsonb(new_ticket);
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('kiosk_check_in', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

update public.queue_entries
set expected_counter_number = case id
  when 'Q-014' then 'S2'
  when 'Q-015' then 'S1'
  when 'Q-011' then 'F1'
  else expected_counter_number
end,
counter_number = case id
  when 'Q-017' then 'S2'
  when 'Q-018' then 'S3'
  when 'Q-019' then 'S4'
  when 'Q-011' then 'F1'
  else counter_number
end
where id in ('Q-011', 'Q-014', 'Q-015', 'Q-017', 'Q-018', 'Q-019');

update public.counter_allocations
set counter_number = case id
  when 'counter_1' then 'F1'
  when 'counter_2' then 'F2'
  when 'counter_4' then 'S1'
  else counter_number
end
where id in ('counter_1', 'counter_2', 'counter_4');
